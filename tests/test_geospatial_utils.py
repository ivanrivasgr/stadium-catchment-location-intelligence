"""Tests for CRS handling, buffering, and competitor metrics."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from src import config, load_data
from src import geospatial_utils as geo


@pytest.fixture
def sample_gdf():
    df = pd.DataFrame(
        {
            "venue_id": ["A", "B", "C"],
            "venue_name": ["A", "B", "C"],
            # A and B are close (~5 mi); C is far away.
            "latitude": [32.7473, 32.7473, 47.5914],
            "longitude": [-97.0838, -97.0945, -122.3325],
        }
    )
    return load_data.to_geodataframe(df)


def test_to_geodataframe_sets_geographic_crs(sample_gdf):
    assert sample_gdf.crs is not None
    assert sample_gdf.crs.to_string() == config.CRS_GEOGRAPHIC


def test_reprojection_changes_crs(sample_gdf):
    projected = geo.to_projected(sample_gdf)
    assert projected.crs.to_string() == config.CRS_PROJECTED
    # Projected coordinates should be in meters, not degrees.
    assert abs(projected.geometry.iloc[0].x) > 180


def test_to_projected_without_crs_raises():
    gdf = gpd.GeoDataFrame({"geometry": [Point(0, 0)]})
    with pytest.raises(ValueError):
        geo.to_projected(gdf)


def test_miles_to_meters():
    assert geo.miles_to_meters(1) == pytest.approx(1609.344)


def test_buffer_creates_polygons_with_expected_area(sample_gdf):
    projected = geo.to_projected(sample_gdf)
    buffers = geo.create_buffers(projected, miles=10)
    assert (buffers.geometry.geom_type == "Polygon").all()
    # Area of a 10-mile-radius circle is pi * 10^2 ~= 314 sq mi.
    assert buffers["buffer_area_sq_mi"].iloc[0] == pytest.approx(314, rel=0.05)


def test_nearest_competitor_distance_is_symmetric_for_pair(sample_gdf):
    projected = geo.to_projected(sample_gdf)
    dists = geo.distance_to_nearest_competitor(projected)
    # A and B are each other's nearest neighbor -> same distance.
    assert dists[0] == pytest.approx(dists[1], rel=1e-6)
    # That distance should be well under 10 miles.
    assert dists[0] < 10


def test_count_competitors_within_radius(sample_gdf):
    projected = geo.to_projected(sample_gdf)
    counts = geo.count_competitors_within(projected, radius_miles=25)
    # A and B see each other; C is isolated.
    assert counts == [1, 1, 0]
