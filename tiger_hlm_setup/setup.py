"""
tiger_hlm_setup: generate YAML and SLURM files for Tiger HLM runs.

Three modes
-----------
longterm   : multi-year simulation, chained via initial conditions
forecast   : single run from a user-specified start date and input files
spinup     : repeat the first year of a longterm run N times to spin up state
"""

import os
from datetime import date

from .defaults import (
    REQUIRED, runoff_yaml_defaults, routing_yaml_defaults,
    runoff_slurm_defaults, routing_slurm_defaults,
)
from .utils import (
    ensure_dir, final_name_for_year, is_leap_year,
    render_template, write_file, submit_job,
)


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _validate(d, label):
    missing = [k for k, v in d.items() if v is REQUIRED]
    if missing:
        raise ValueError(f"[{label}] required fields not set: {missing}")


def _merge(defaults, overrides):
    out = dict(defaults)
    out.update({k: v for k, v in overrides.items() if v is not None})
    return out


def _join_path(*parts):
    segments = []
    for part in parts:
        if part is None:
            continue
        for seg in str(part).split("/"):
            if seg.strip():
                segments.append(seg.strip())
    if not segments:
        return ""
    prefix = "/" if parts and str(parts[0]).startswith("/") else ""
    return prefix + "/".join(segments)


def _build_paths(proj_root, product, region):
    runoff_root = _join_path(proj_root, "runoff", product)
    routing_root = _join_path(proj_root, "routing", product)
    return {
        "runoff_outputs":  _join_path(runoff_root, "outputs", region),
        "runoff_slurm":    _join_path(runoff_root, "slurm", region),
        "routing_outputs": _join_path(routing_root, "outputs", region),
        "routing_slurm":   _join_path(routing_root, "slurm", region),
    }


def _build_job_name(prefix, region, product):
    tag_parts = [str(part).strip().lower() for part in [region, product] if str(part).strip()]
    if not tag_parts:
        return prefix
    return f"{prefix}_{'_'.join(tag_parts)}"


def _write_year(
    year, paths, region, product, runoff_inputs, routing_inputs,
    init_file, ini_flag, ini_file, ival,
    slurm_cfg, submit,
):
    """Generate all four files (runoff yaml, runoff slurm, routing yaml, routing slurm) for one year."""

    runoff_out_dir = f"{paths['runoff_outputs']}/{year}"
    runoff_path    = f"{runoff_out_dir}/runoff"
    ensure_dir(f"{runoff_out_dir}/final")
    ensure_dir(runoff_path)

    series_fp      = f"{paths['routing_outputs']}/hydro"
    snapshot_fp    = f"{paths['routing_outputs']}/snapshot"
    max_output_fp  = f"{paths['routing_outputs']}/max_output"

    runoff_yaml_f  = f"{paths['runoff_slurm']}/runoff_{year}.yaml"
    runoff_slurm_f = f"{paths['runoff_slurm']}/runoff_{year}.slurm"
    routing_yaml_f = f"{paths['routing_slurm']}/routing_{year}.yaml"
    routing_slurm_f = f"{paths['routing_slurm']}/routing_{year}.slurm"

    # --- runoff yaml ---
    ry = _merge(runoff_yaml_defaults(region), {
        "year":       year,
        "init_file":  init_file,
        "output_dir": runoff_out_dir,
        **runoff_inputs,
    })
    _validate(ry, f"runoff_yaml year={year}")
    write_file(runoff_yaml_f, render_template("runoff.yaml", ry))

    # --- routing yaml ---
    rt = _merge(routing_yaml_defaults(), {
        "start_date":          f"{year}-01-01 00:00:00",
        "runoff_path":         runoff_path,
        "series_filepath":     series_fp,
        "snapshot_filepath":   snapshot_fp,
        "max_output_filepath": max_output_fp,
        "ini_flag":            ini_flag,
        "ini_file":            ini_file,
        "ival":                ival,
        **routing_inputs,
    })
    _validate(rt, f"routing_yaml year={year}")
    write_file(routing_yaml_f, render_template("routing.yaml", rt))

    # --- runoff slurm ---
    rs = _merge(runoff_slurm_defaults(slurm_cfg), {
        "name":              _build_job_name("runoff", region, product),
        "yaml":              os.path.basename(runoff_yaml_f),
        "out":               f"out_{year}.txt",
        "routing_slurm_dir": paths["routing_slurm"],
        "routing_script":    os.path.basename(routing_slurm_f),
    })
    _validate(rs, f"runoff_slurm year={year}")
    write_file(runoff_slurm_f, render_template("runoff.slurm", rs))

    # --- routing slurm ---
    rts_defaults = routing_slurm_defaults(slurm_cfg)
    remove_cmd = "#remove runoff\nrm -f " + f"{runoff_path}/*.nc" if rts_defaults.get("remove_runoff") else "#remove runoff: disabled"
    rts = _merge(rts_defaults, {
        "name":               _build_job_name("routing", region, product),
        "yaml":               os.path.basename(routing_yaml_f),
        "out":                f"out_{year}.txt",
        "runoff_path":        f"{runoff_path}/*.nc",
        "remove_runoff_cmd":  remove_cmd,
    })
    _validate(rts, f"routing_slurm year={year}")
    write_file(routing_slurm_f, render_template("routing.slurm", rts))

    print(f"  [{year}] files written")

    if submit:
        submit_job(runoff_slurm_f, paths["runoff_slurm"])

    return snapshot_fp   # caller may need this for chaining


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def setup_longterm(
    proj_root,
    start_year,
    end_year,
    runoff_inputs,        # dict: params_dir, params_csv, forcings_dir, pr_*, t2_*, lookup_*
    routing_inputs,       # dict: params, sav_path
    region="",
    product="",
    runoff_spinup_file=None,
    routing_initial_value=0.1,
    routing_initial_file=None,
    slurm_cfg=None,
    submit=False,
):
    """Multi-year simulation chained year-by-year."""
    slurm_cfg = slurm_cfg or {}
    paths = _build_paths(proj_root, product, region)
    for d in paths.values():
        ensure_dir(d)

    for year in range(start_year, end_year + 1):
        chunk_days = runoff_inputs.get("chunk_days", 4)

        # runoff initial condition
        if year == start_year:
            init_file = runoff_spinup_file
        else:
            prev_final = final_name_for_year(year - 1, chunk_days)
            init_file = f"{paths['runoff_outputs']}/{year - 1}/final/{prev_final}"

        # routing initial condition
        snapshot_fp = f"{paths['routing_outputs']}/snapshot"
        if year == start_year:
            if routing_initial_file:
                ini_flag, ini_file, ival = 1, routing_initial_file, 0.1
            else:
                ini_flag, ini_file, ival = 0, "", routing_initial_value
        else:
            ini_flag = 1
            ival = 0.1
            suffix = "12-30" if is_leap_year(year - 1) else "12-31"
            ini_file = f"{snapshot_fp}_{year - 1}-{suffix}_00_00_00.nc"

        _write_year(
            year, paths, region, product,
            runoff_inputs, routing_inputs,
            init_file, ini_flag, ini_file, ival,
            slurm_cfg, submit,
        )


def setup_forecast(
    proj_root,
    start_date,           # "YYYY-MM-DD"
    end_date,             # "YYYY-MM-DD"
    runoff_inputs,        # must include init_file for runoff
    routing_inputs,       # must include params, sav_path, ini_flag, ini_file (or ival)
    region="",
    product="",
    slurm_cfg=None,
    submit=False,
):
    """Single forecast run from a specified date window."""
    slurm_cfg = slurm_cfg or {}
    year = int(start_date[:4])
    paths = _build_paths(proj_root, product, region)
    for d in paths.values():
        ensure_dir(d)

    init_file = runoff_inputs.pop("init_file")
    ini_flag  = routing_inputs.pop("ini_flag",  0)
    ini_file  = routing_inputs.pop("ini_file",  "")
    ival      = routing_inputs.pop("ival",       0.1)

    # Override time period in runoff yaml via a special key
    runoff_inputs["_start_date"] = start_date
    runoff_inputs["_end_date"]   = end_date

    _write_year(
        year, paths, region, product,
        runoff_inputs, routing_inputs,
        init_file, ini_flag, ini_file, ival,
        slurm_cfg, submit,
    )


def setup_spinup(
    proj_root,
    spinup_year,          # the year to repeat
    n_cycles,             # how many times to repeat it
    runoff_inputs,
    routing_inputs,
    region="",
    product="",
    runoff_spinup_file=None,
    routing_initial_value=0.1,
    slurm_cfg=None,
    submit=False,
):
    """
    Repeat spinup_year N times.  Each cycle feeds its final state into the next.
    Output dirs are labelled spinup_1, spinup_2, …
    """
    slurm_cfg = slurm_cfg or {}
    chunk_days = runoff_inputs.get("chunk_days", 4)

    #turn off runoff/routing output for spinup since it can consume a lot of space and isn't usually needed for diagnostics
    routing_inputs['out_flag'] = 0    
    routing_inputs['max_output_flag'] = 0
    slurm_cfg['remove_runoff'] = True  # add flag to remove runoff files after routing to save space during spinup

    for cycle in range(1, n_cycles + 1):
        cycle_root = f"{proj_root}spinup_{cycle}"
        paths = _build_paths(cycle_root, product, region)
        for d in paths.values():
            ensure_dir(d)

        if cycle == 1:
            init_file = runoff_spinup_file
            ini_flag, ini_file, ival = 0, "", routing_initial_value
            runoff_inputs['initial_mode'] = 'constant'
        else:
            prev_root    = f"{proj_root}spinup_{cycle - 1}"
            prev_paths   = _build_paths(prev_root, product, region)
            prev_final   = final_name_for_year(spinup_year, chunk_days)
            init_file    = f"{prev_paths['runoff_outputs']}/{spinup_year}/final/{prev_final}"
            prev_snap    = f"{prev_paths['routing_outputs']}/snapshot"
            suffix       = "12-30" if is_leap_year(spinup_year) else "12-31"
            ini_flag     = 1
            ini_file     = f"{prev_snap}_{spinup_year}-{suffix}_00_00_00.nc"
            ival         = 0.1
            runoff_inputs['initial_mode'] = 'from_file'

        print(f"Spinup cycle {cycle}/{n_cycles}")
        _write_year(
            spinup_year, paths, region, product,
            runoff_inputs, routing_inputs,
            init_file, ini_flag, ini_file, ival,
            slurm_cfg, submit,
        )
