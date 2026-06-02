"""Geospatial helpers: reprojection, buffering, and competitor metrics.

All distance and area math runs in a projected CRS (see config.CRS_PROJECTED).
Doing it in lat/lon degrees would give meaningless results because a degree
of longitude is not a fixed ground distance.
"""

from __future__ import annotations

import geopandas as gpd

from . import config


def miles_to_meters(miles: float) -> float:
    """Convert miles to meters."""
    return miles * config.METERS_PER_MILE


def to_projected(gdf: gpd.GeoDataFrame, crs: str = config.CRS_PROJECTED) -> gpd.GeoDataFrame:
    """Reproject to a projected CRS for distance/area calculations.

    Errors early if the input has no CRS, since reprojecting without a known
    source frame silently produces garbage.
    """
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS; set one before reprojecting.")
    return gdf.to_crs(crs)


def create_buffers(
    gdf_projected: gpd.GeoDataFrame, miles: float
) -> gpd.GeoDataFrame:
    """Return a copy of the venues with circular buffers of the given radius.

    The input must already be in a projected CRS measured in meters.
    """
    radius_m = miles_to_meters(miles)
    buffered = gdf_projected.copy()
    buffered["geometry"] = gdf_projected.geometry.buffer(radius_m)
    buffered["buffer_miles"] = miles
    buffered["buffer_area_sq_mi"] = buffered.geometry.area / (config.METERS_PER_MILE ** 2)
    return buffered


def distance_to_nearest_competitor(gdf_projected: gpd.GeoDataFrame) -> list[float]:
    """Distance in miles from each venue to its closest neighbor.

    Returns NaN-free positive distances; a lone venue would return inf, but
    real inputs are expected to have at least two points.
    """
    points = gdf_projected.geometry
    distances = []
    for i, geom in enumerate(points):
        others = points.drop(points.index[i])
        nearest_m = others.distance(geom).min()
        distances.append(nearest_m / config.METERS_PER_MILE)
    return distances


def count_competitors_within(
    gdf_projected: gpd.GeoDataFrame, radius_miles: float
) -> list[int]:
    """Count other venues within radius_miles of each venue."""
    radius_m = miles_to_meters(radius_miles)
    points = gdf_projected.geometry
    counts = []
    for i, geom in enumerate(points):
        others = points.drop(points.index[i])
        counts.append(int((others.distance(geom) <= radius_m).sum()))
    return counts
