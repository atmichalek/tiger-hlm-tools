from .defaults import (
    REQUIRED,
    SLURM_DEFAULTS,
    runoff_yaml_defaults,
    routing_yaml_defaults,
    runoff_slurm_defaults,
    routing_slurm_defaults,
)
from .lookup import generate_lookup, get_forcing_characteristics
from .setup import setup_longterm, setup_forecast, setup_spinup


def describe_setup_options():
    """Return a defaults-driven description of the setup options users can change."""
    descriptions = {
        "year": "Year being generated; required for each run.",
        "initial_mode": "Runoff initialization mode; defaults to from_file.",
        "init_file": "Runoff initial-condition file; required unless a default is supplied by the caller.",
        "params_dir": "Directory containing runoff parameters.",
        "params_csv": "CSV file with spatially varying runoff parameters.",
        "forcings_dir": "Directory containing forcing files.",
        "pr_file_pattern": "Filename pattern for precipitation forcing files.",
        "pr_varname": "Variable name for precipitation forcing data.",
        "pr_resolution": "Temporal resolution of precipitation forcing data.",
        "pr_dims": "Dimension names for precipitation forcing data.",
        "t2_file_pattern": "Filename pattern for temperature forcing files.",
        "t2_varname": "Variable name for temperature forcing data.",
        "t2_resolution": "Temporal resolution of temperature forcing data; defaults to 24h.",
        "t2_dims": "Dimension names for temperature forcing data.",
        "chunk_days": "Number of days per time chunk for forcings; defaults to 4.",
        "lookup_dir": "Directory containing forcing lookup tables.",
        "lookup_pr_csv": "Lookup CSV for precipitation forcing mappings.",
        "lookup_t2m_csv": "Lookup CSV for temperature forcing mappings.",
        "print_interval": "How often runoff output is printed.",
        "query_dt": "Time step used for query operations.",
        "final_interval_minutes": "Interval for final output writing.",
        "states": "List of runoff state indices included in output.",
        "output_dir": "Directory where runoff output files are written.",
        "runoff_output": "Runoff output file path relative to the output directory.",
        "final_per_year": "Whether to write a final file once per year.",
        "start_date": "Routing start date; required for each run.",
        "params": "Routing parameter path or configuration.",
        "runoff_path": "Path to runoff files used by routing.",
        "series_filepath": "File path for routing series output.",
        "snapshot_filepath": "File path for routing snapshot output.",
        "max_output_filepath": "File path for routing max-output data.",
        "chunk_size": "Routing chunk size; defaults to 0 (no chunking).",
        "ini_flag": "Routing initialization mode flag; 0 for constant, 1 for netcdf restart file.",
        "ival": "Initial routing state value used for constant initialization.",
        "ini_file": "Routing restart file path used when ini_flag is 1.",
        "out_flag": "Routing output flag.",
        "out_level": "Routing output level.",
        "out_resolution": "Routing output resolution.",
        "max_output_flag": "Routing max-output flag.",
        "sav_path": "Path to the SAV file used by routing.",
        "account": "SLURM account to use.",
        "partition": "SLURM partition to use.",
        "email": "Email address for SLURM notifications.",
        "runoff_version": "Tiger HLM runoff module version to load.",
        "routing_version": "Tiger HLM routing module version to load.",
        "runoff_time": "SLURM wall time for runoff jobs.",
        "routing_time": "SLURM wall time for routing jobs.",
        "runoff_mem": "Memory request for runoff jobs.",
        "routing_cpus": "CPU count requested for routing jobs.",
        "remove_runoff": "Whether to remove runoff files after routing completes.",
    }

    defaults = {}
    defaults.update(runoff_yaml_defaults(""))
    defaults.update(routing_yaml_defaults())
    defaults.update({k: v for k, v in SLURM_DEFAULTS.items() if k in {"account", "partition", "email", "runoff_version", "routing_version", "runoff_time", "routing_time", "runoff_mem", "routing_cpus"}})
    defaults.update(runoff_slurm_defaults({}))
    defaults.update(routing_slurm_defaults({}))

    result = {}
    for key, value in sorted(defaults.items()):
        if key in {"name", "yaml", "out", "routing_slurm_dir", "routing_script", "runoff_path", "remove_runoff"}:
            continue
        required = value is REQUIRED
        if isinstance(value, dict):
            default_repr = "<dict>"
        elif isinstance(value, list):
            default_repr = repr(value)
        elif value is REQUIRED:
            default_repr = "required"
        else:
            default_repr = repr(value)
        result[key] = {
            "default": default_repr,
            "required": required,
            "description": descriptions.get(key, "User-configurable option."),
        }
    return result
