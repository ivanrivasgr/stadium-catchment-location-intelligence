"""Load venue tables and turn them into clean GeoDataFrames.

Validation happens here so the rest of the pipeline can assume well-formed
inputs: required columns present, coordinates parseable and in range.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from . import config


def load_venues(path: str | Path) -> pd.DataFrame:
    """Read a venue CSV and validate its structure.

    Raises FileNotFoundError if the path is missing and ValueError if
    required columns are absent or coordinates are unusable.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Venue file not found: {path}")

    df = pd.read_csv(path)

    missing = [c for c in config.REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Input is missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )

    # Coordinates must be numeric and non-null.
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    bad_coords = df[df["latitude"].isna() | df["longitude"].isna()]
    if not bad_coords.empty:
        ids = bad_coords.get("venue_id", bad_coords.index).tolist()
        raise ValueError(f"Rows have missing/unparseable coordinates: {ids}")

    out_of_range = df[
        (df["latitude"].abs() > 90) | (df["longitude"].abs() > 180)
    ]
    if not out_of_range.empty:
        ids = out_of_range.get("venue_id", out_of_range.index).tolist()
        raise ValueError(f"Rows have out-of-range coordinates: {ids}")

    return df


def to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Convert a validated venue DataFrame to a GeoDataFrame in WGS84."""
    geometry = gpd.points_from_xy(df["longitude"], df["latitude"])
    return gpd.GeoDataFrame(df.copy(), geometry=geometry, crs=config.CRS_GEOGRAPHIC)
