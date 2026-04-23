import os
import calendar
import subprocess
from datetime import date, timedelta
from string import Template


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def last_chunk_bounds(year, chunk_days):
    """Return (start, end) dates of the final chunk for a given year."""
    ndays = 366 if calendar.isleap(year) else 365
    r = ndays % chunk_days
    last_len = chunk_days if r == 0 else r
    end = date(year, 12, 31)
    start = end - timedelta(days=last_len - 1)
    return start, end


def final_name_for_year(year, chunk_days):
    s, e = last_chunk_bounds(year, chunk_days)
    return f"final_{s:%Y%m%d}_{e:%Y%m%d}.nc"


def render_template(template_name, d):
    """Load a template file and substitute dict d."""
    path = os.path.join(TEMPLATE_DIR, template_name)
    with open(path) as f:
        return Template(f.read()).substitute(d)


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def submit_job(job_script, job_dir):
    subprocess.run(["sbatch", job_script], cwd=job_dir)
