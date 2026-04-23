import os
import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree


def get_latlon_2d(ncfile):
    """
    Extract 2D latitude and longitude arrays from a forcing dataset.
    Handles 1D (regular grid) and 2D (curvilinear) lat/lon coordinates.
    Longitudes normalized to [-180, 180].
    """
    ds = xr.open_dataset(ncfile)
    ds.close()

    lat_name = next((n for n in ("latitude", "lat", "XLAT") if n in ds.coords), None)
    lon_name = next((n for n in ("longitude", "lon", "XLONG") if n in ds.coords), None)
    if lat_name is None or lon_name is None:
        raise RuntimeError(f"Could not find lat/lon coords. Found: {list(ds.coords)}")

    lat = ds[lat_name].values
    lon = ((ds[lon_name].values + 180) % 360) - 180

    if lat.ndim == 1 and lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    elif lat.ndim == 2 and lon.ndim == 2:
        lat2d, lon2d = lat, lon
    else:
        raise RuntimeError(f"Unsupported lat/lon shapes: lat {lat.shape}, lon {lon.shape}")

    return lat2d, lon2d


def build_lookup(params_csv, lat2d, lon2d, out_csv, flip_dims=False):
    """
    For each runoff element centroid, find the nearest forcing grid cell using
    a KD-tree and write a stream -> (lat_index, lon_index) lookup CSV.

    flip_dims: set True for products like IMERG where lat/lon array dims are transposed.
    """
    df = pd.read_csv(params_csv)

    need = {"stream", "centroid_lat", "centroid_lon"}
    if not need.issubset(df.columns):
        raise ValueError(f"{params_csv} must have columns {need}. Got {df.columns.tolist()}")

    lon_adj = ((df["centroid_lon"].to_numpy() + 180) % 360) - 180
    pts = np.column_stack([df["centroid_lat"].to_numpy(), lon_adj])

    tree = cKDTree(np.c_[lat2d.ravel(), lon2d.ravel()])
    _, flat = tree.query(pts)
    iy, ix = np.unravel_index(flat, lat2d.shape)

    out = df[["stream"]].copy()
    if flip_dims:
        out["lat_index"] = ix
        out["lon_index"] = iy
    else:
        out["lat_index"] = iy
        out["lon_index"] = ix
    out.to_csv(out_csv, index=False)

    return out


def get_forcing_characteristics(ncfile):
    """
    Inspect a forcing NetCDF and return (var_name, dims_string, time_resolution).
    dims_string is comma-joined, e.g. "time,lat,lon".
    """
    ds = xr.open_dataset(ncfile)
    ds.close()

    chars = ["p", "r", "t2m", "tmp"]
    var_name = next((v for v in ds.data_vars if any(c in v.lower() for c in chars)), None)
    if var_name is None:
        raise RuntimeError(f"Could not detect forcing variable in {ncfile}. Vars: {list(ds.data_vars)}")

    dims = ",".join(ds[var_name].dims)

    time_var = next((c for c in ds.coords if c.lower() == "time"), None)
    if time_var is None:
        raise RuntimeError(f"No time coordinate found in {ncfile}")
    resolution = f"{(ds[time_var].diff(time_var).median() / pd.Timedelta(hours=1)):g}h"

    return var_name, dims, resolution


def generate_lookup(ncfile, params_csv, out_csv, flip_dims=False):
    """Build and save a forcing lookup table for a given product/region."""
    try:
        lat2d, lon2d = get_latlon_2d(ncfile)
        build_lookup(params_csv, lat2d, lon2d, out_csv, flip_dims=flip_dims)
        print(f"Lookup complete: {os.path.basename(out_csv)}")
    except Exception as e:
        print(f"Error generating lookup for {os.path.basename(out_csv)}: {e}")
