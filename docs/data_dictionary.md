# Data dictionary

## Input: `data/sample/venues_sample.csv`

| Column            | Type    | Required | Description |
|-------------------|---------|----------|-------------|
| `venue_id`        | string  | yes      | Stable unique identifier for the venue. |
| `venue_name`      | string  | yes      | Display name. |
| `city`            | string  | no       | City. |
| `state`           | string  | no       | Two-letter state code. |
| `latitude`        | float   | yes      | Decimal degrees, WGS84. Range -90 to 90. |
| `longitude`       | float   | yes      | Decimal degrees, WGS84. Range -180 to 180. |
| `metro_population`| integer | no       | **Illustrative / synthetic** addressable-market figure for the sample. Not official. Replace with real demographic data for production use. |

Required columns are enforced in `src/load_data.py`; missing or out-of-range
coordinates raise a `ValueError`.

## Output: `outputs/tables/venue_opportunity_summary.csv`

One row per venue, sorted by opportunity score descending.

| Column                          | Type    | Description |
|---------------------------------|---------|-------------|
| `venue_id`                      | string  | From input. |
| `venue_name`                    | string  | From input. |
| `city`, `state`                 | string  | From input (if present). |
| `latitude`, `longitude`         | float   | From input. |
| `metro_population`              | integer | From input (illustrative). |
| `n_competitors`                 | integer | Other venues within the competitor radius (default 25 mi). |
| `dist_to_nearest_competitor_mi` | float   | Straight-line miles to the closest other venue. |
| `catchment_25mi_area_sq_mi`     | float   | Area of the 25-mile catchment, square miles. |
| `opportunity_score`             | float   | 0-100, higher = stronger opportunity. Relative to the current dataset. |

## Output: spatial layers (`outputs/qgis/`)

- `venues_scored.geojson` / `catchment.gpkg :: venues_scored` — venue points
  with `n_competitors`, `dist_to_nearest_competitor_mi`, and
  `opportunity_score` attributes, in EPSG:4326.
- `catchment.gpkg :: catchment_5mi` / `catchment_10mi` / `catchment_25mi` —
  buffer polygons per band, in EPSG:4326, each carrying `buffer_miles` and
  `buffer_area_sq_mi`.
