from datetime import date

# Sentinel for fields that must be provided by the caller
REQUIRED = object()


# --- SLURM cluster settings ---
SLURM_DEFAULTS = {
    "account":         "my_account",
    "partition":       "my_partition",
    "email":           "user@university.edu",
    "runoff_version":  "1.0.0",
    "routing_version": "1.0.0",
    "runoff_time":     "24:00:00",
    "routing_time":    "08:00:00",
    "runoff_mem":      "128G",
    "routing_cpus":    112,
}


# --- Runoff solver presets by region ---
SOLVER_PRESETS = {
    "West": {
        "rtol": 1e-4, "atol": 1e-7,
        "safety": 0.92, "min_scale": 0.2, "max_scale": 12.0,
        "initial_step": 0.1,
        "override_tolerances": "true", "override_initial_step": "true",
    },
    "default": {
        "rtol": 1e-6, "atol": 1e-9,
        "safety": 0.9, "min_scale": 0.2, "max_scale": 10.0,
        "initial_step": 0.05,
        "override_tolerances": "true", "override_initial_step": "true",
    },
}


def get_solver_settings(region):
    return SOLVER_PRESETS.get(region, SOLVER_PRESETS["default"])


def runoff_yaml_defaults(region, solver_overrides=None):
    solver = get_solver_settings(region)
    if solver_overrides:
        solver.update(solver_overrides)
    return {
        "Description":          "Runoff Generation",
        "region_title":         region,
        "year":                 REQUIRED,
        "today":                date.today().isoformat(),
        "init_file":            REQUIRED,
        "params_dir":           REQUIRED,
        "params_csv":           REQUIRED,
        "forcings_dir":         REQUIRED,
        "pr_file_pattern":      REQUIRED,
        "pr_varname":           REQUIRED,
        "pr_resolution":        REQUIRED,
        "pr_dims":              REQUIRED,
        "t2_file_pattern":      REQUIRED,
        "t2_varname":           REQUIRED,
        "t2_resolution":        "24h",
        "t2_dims":              REQUIRED,
        "chunk_days":           4,
        "lookup_dir":           REQUIRED,
        "lookup_pr_csv":        REQUIRED,
        "lookup_t2m_csv":       REQUIRED,
        "print_interval":       1,
        "query_dt":             60.0,
        "final_interval_minutes": 0,
        "states":               [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "output_dir":           REQUIRED,
        "final_per_year":       True,
        **solver,
    }


def routing_yaml_defaults():
    return {
        "start_date":          REQUIRED,
        "params":              REQUIRED,
        "runoff_path":         REQUIRED,
        "series_filepath":     REQUIRED,
        "snapshot_filepath":   REQUIRED,
        "max_output_filepath": REQUIRED,
        "chunk_size":          0,
        "ini_flag":            REQUIRED,
        "ival":                0.1,
        "ini_file":            REQUIRED,
        "out_flag":            2,
        "out_level":           2,
        "out_resolution":      15,
        "sav_path":            REQUIRED,
    }


def runoff_slurm_defaults(slurm_cfg):
    return {
        "name":              "runoff",
        "account":           slurm_cfg.get("account",         SLURM_DEFAULTS["account"]),
        "partition":         slurm_cfg.get("partition",        SLURM_DEFAULTS["partition"]),
        "mem":               slurm_cfg.get("runoff_mem",       SLURM_DEFAULTS["runoff_mem"]),
        "time":              slurm_cfg.get("runoff_time",      SLURM_DEFAULTS["runoff_time"]),
        "email":             slurm_cfg.get("email",            SLURM_DEFAULTS["email"]),
        "runoff_version":    slurm_cfg.get("runoff_version",   SLURM_DEFAULTS["runoff_version"]),
        "yaml":              REQUIRED,
        "out":               "out.txt",
        "routing_slurm_dir": REQUIRED,
        "routing_script":    REQUIRED,
    }


def routing_slurm_defaults(slurm_cfg):
    return {
        "name":             "routing",
        "account":          slurm_cfg.get("account",          SLURM_DEFAULTS["account"]),
        "cpus":             slurm_cfg.get("routing_cpus",     SLURM_DEFAULTS["routing_cpus"]),
        "time":             slurm_cfg.get("routing_time",     SLURM_DEFAULTS["routing_time"]),
        "email":            slurm_cfg.get("email",            SLURM_DEFAULTS["email"]),
        "routing_version":  slurm_cfg.get("routing_version",  SLURM_DEFAULTS["routing_version"]),
        "yaml":             REQUIRED,
        "out":              "out.txt",
        "runoff_path":      REQUIRED,
        "remove_runoff":    slurm_cfg.get("remove_runoff",    False),
    }
