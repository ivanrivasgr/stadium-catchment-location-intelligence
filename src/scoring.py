"""Opportunity scoring.

The score combines three normalized signals into a 0-100 value:
  - population: larger addressable market is better
  - competition: fewer nearby venues is better (inverted)
  - isolation: more distance to the nearest competitor is better

Weights live in config.SCORE_WEIGHTS. The model is intentionally simple and
transparent; see docs/methodology.md for assumptions and limitations.
"""

from __future__ import annotations

import pandas as pd

from . import config


def normalize(series: pd.Series) -> pd.Series:
    """Min-max scale a series to [0, 1].

    A flat series (no spread) maps to all zeros, which keeps that signal
    neutral rather than blowing up on a divide-by-zero.
    """
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def compute_opportunity_score(df: pd.DataFrame) -> pd.Series:
    """Return a 0-100 opportunity score per row.

    Expects columns: metro_population (optional), n_competitors,
    dist_to_nearest_competitor_mi. Missing population is treated as a
    neutral 0 contribution so the model still runs on minimal inputs.
    """
    w = config.SCORE_WEIGHTS

    if "metro_population" in df.columns:
        population_term = normalize(df["metro_population"].fillna(0))
    else:
        population_term = pd.Series(0.0, index=df.index)

    # Fewer competitors is better, so invert the normalized competition term.
    competition_term = 1.0 - normalize(df["n_competitors"])
    isolation_term = normalize(df["dist_to_nearest_competitor_mi"])

    score = (
        w["population"] * population_term
        + w["competition"] * competition_term
        + w["isolation"] * isolation_term
    )
    return (score * 100).round(1)
