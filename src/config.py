"""Central configuration: paths, coordinate systems, analysis parameters.

Keeping these in one place makes the pipeline easy to retarget at a new
dataset or a different region without hunting through the codebase.
"""

from __future__ import annotations

from pathlib import Path

# --- Paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DATA = DATA_DIR / "sample" / "venues_sample.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
MAPS_DIR = OUTPUTS_DIR / "maps"
QGIS_DIR = OUTPUTS_DIR / "qgis"

# --- Coordinate reference systems ------------------------------------------
# Source data is lat/lon in WGS84.
CRS_GEOGRAPHIC = "EPSG:4326"
# Projected CRS for distance/area work. Albers Equal Area (CONUS) keeps area
# and distance reasonable across the continental US. Swap this if you move
# the analysis to another region (e.g. a local UTM zone or national grid).
CRS_PROJECTED = "EPSG:5070"

# --- Analysis parameters ---------------------------------------------------
# Catchment bands in miles.
BUFFER_MILES = [5, 10, 25]
# Radius used to count competing venues around each site.
COMPETITOR_RADIUS_MILES = 25
METERS_PER_MILE = 1609.344

# --- Scoring weights -------------------------------------------------------
# Opportunity favors large addressable population, few nearby competitors,
# and distance from the closest competing venue. Weights sum to 1.0.
SCORE_WEIGHTS = {
    "population": 0.50,
    "competition": 0.30,  # applied to an inverted (less-competition-is-better) term
    "isolation": 0.20,
}

# Required columns in any input venue file.
REQUIRED_COLUMNS = ["venue_id", "venue_name", "latitude", "longitude"]
