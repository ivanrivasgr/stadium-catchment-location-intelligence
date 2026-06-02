"""Tests for normalization, opportunity scoring, and input validation."""

import pandas as pd
import pytest

from src import load_data, scoring


def test_normalize_maps_to_unit_range():
    s = pd.Series([10, 20, 30])
    out = scoring.normalize(s)
    assert out.min() == 0.0
    assert out.max() == 1.0
    assert out.iloc[1] == pytest.approx(0.5)


def test_normalize_flat_series_is_neutral():
    s = pd.Series([5, 5, 5])
    out = scoring.normalize(s)
    assert (out == 0.0).all()


def test_opportunity_score_within_bounds():
    df = pd.DataFrame(
        {
            "metro_population": [1_000_000, 5_000_000, 9_000_000],
            "n_competitors": [0, 3, 8],
            "dist_to_nearest_competitor_mi": [120.0, 15.0, 2.0],
        }
    )
    scores = scoring.compute_opportunity_score(df)
    assert scores.between(0, 100).all()


def test_score_runs_without_population_column():
    df = pd.DataFrame(
        {
            "n_competitors": [0, 5],
            "dist_to_nearest_competitor_mi": [50.0, 3.0],
        }
    )
    scores = scoring.compute_opportunity_score(df)
    assert scores.between(0, 100).all()


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_data.load_venues(tmp_path / "does_not_exist.csv")


def test_load_missing_columns_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("venue_id,latitude\nV1,40.0\n")
    with pytest.raises(ValueError):
        load_data.load_venues(p)


def test_load_rejects_missing_coordinates(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(
        "venue_id,venue_name,latitude,longitude\nV1,Test,,-97.0\n"
    )
    with pytest.raises(ValueError):
        load_data.load_venues(p)


def test_load_rejects_out_of_range_coordinates(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(
        "venue_id,venue_name,latitude,longitude\nV1,Test,200.0,-97.0\n"
    )
    with pytest.raises(ValueError):
        load_data.load_venues(p)
