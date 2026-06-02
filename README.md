# Stadium Catchment & Market Opportunity Analysis

Catchment and market-opportunity analysis around sports venues. Given a list of
venues with coordinates, the pipeline builds distance-band catchments, computes
competition and reach features, and ranks each venue with a 0-100 opportunity
score. Results export to CSV, GeoJSON, and a QGIS-ready GeoPackage.

## Problem

A sports organization deciding where to invest in fan development, ticketing
pushes, or a future venue needs to understand the local market around each
site: how large is the addressable population, how many competing venues sit
nearby, and how isolated (or crowded) is the catchment. This project turns a
plain venue list into those answers.

## Why it matters

The same pattern shows up well beyond stadiums: retail site selection,
territory planning, and service-area analysis all ask "what does the area
around this point look like, and how does it compare to others?" The workflow
here, source points to projected buffers to scored, comparable areas, transfers
directly to those problems and to QGIS/ArcGIS-based location intelligence work.

## Skills demonstrated

- Geospatial data handling with GeoPandas / Shapely / pyproj
- Correct CRS management: geographic source, projected CRS for distance/area
- Buffer (catchment) construction and nearest-neighbor / proximity metrics
- A transparent, documented scoring model
- Reproducible CLI pipeline with input validation and error handling
- Exports built for downstream GIS tools (GeoPackage, GeoJSON)
- Static (Matplotlib) and interactive (Folium) mapping
- Lightweight test coverage with pytest

## Repository structure

```
stadium-catchment-location-intelligence/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── data/
│   ├── raw/                 # bulky source pulls (gitignored)
│   ├── processed/           # intermediate data (gitignored)
│   └── sample/              # bundled demo dataset
├── notebooks/
│   └── 01_exploratory_geospatial_analysis.ipynb
├── src/
│   ├── config.py            # paths, CRS, buffer bands, scoring weights
│   ├── load_data.py         # load + validate venues, build GeoDataFrame
│   ├── geospatial_utils.py  # reprojection, buffers, proximity metrics
│   ├── scoring.py           # normalization + opportunity score
│   └── build_outputs.py     # pipeline entry point + maps + exports
├── outputs/
│   ├── maps/                # static PNG + interactive HTML
│   ├── tables/              # CSV summary
│   └── qgis/                # GeoJSON + GeoPackage
├── tests/
└── docs/
    ├── methodology.md
    ├── data_dictionary.md
    └── qgis_workflow.md
```

## Quickstart

```bash
git clone <your-fork-url>
cd stadium-catchment-location-intelligence

python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt

# Run on the bundled sample data
python -m src.build_outputs --input data/sample/venues_sample.csv

# Run the tests
pytest -q
```

Point `--input` at your own CSV to analyze a different venue set; it just needs
`venue_id`, `venue_name`, `latitude`, and `longitude` columns (see
`docs/data_dictionary.md`).

## Example outputs

Top venues from the sample run, ranked by opportunity score:

| Venue                 | Metro pop (illustrative) | Competitors ≤25mi | Nearest competitor (mi) | Score |
|-----------------------|--------------------------|-------------------|-------------------------|-------|
| Angel Stadium         | 12.9M                    | 0                 | 27.7                    | 62.5  |
| T-Mobile Park         | 4.0M                     | 0                 | 680.4                   | 55.8  |
| Daikin Park           | 7.3M                     | 0                 | 230.5                   | 52.2  |
| Coors Field           | 3.0M                     | 0                 | 654.3                   | 52.0  |
| Madison Square Garden | 19.2M                    | 3                 | 6.0                     | 50.2  |

Also generated:

- `outputs/maps/catchment_static_map.png` — venues colored by score over the
  25-mile catchment band.
- `outputs/maps/catchment_interactive_map.html` — Folium map with toggleable
  buffer bands and venue popups.
- `outputs/qgis/catchment.gpkg` — multi-layer GeoPackage for QGIS.

## Methodology summary

Source points come in as WGS84 lat/lon and are reprojected to EPSG:5070
(Conus Albers, equal-area, meters) before any distance or area math, because
computing distances in degrees is meaningless. Each venue gets 5/10/25-mile
catchment buffers, a count of competing venues within 25 miles, and a
straight-line distance to its nearest competitor. The opportunity score is a
weighted, min-max-normalized blend of addressable population (favored),
competition (penalized), and isolation from competitors (favored), scaled to
0-100. Full detail and the reasoning behind each choice is in
[`docs/methodology.md`](docs/methodology.md).

## QGIS compatibility

The GeoPackage (`outputs/qgis/catchment.gpkg`) carries the venue points and
each buffer band as separate layers, ready to open and style in QGIS.
[`docs/qgis_workflow.md`](docs/qgis_workflow.md) covers loading the layers,
styling venues by opportunity score, styling nested buffer bands, verifying
values against the CSV, and composing a print layout.

## Limitations

- The sample dataset uses real, publicly known venue coordinates, but
  `metro_population` is a **synthetic, illustrative** placeholder, not official
  data. It is labeled as such and is meant to be replaced with real ACS/census
  population for production use.
- Catchments are straight-line buffers, not drive-time isochrones.
- "Competitor" means any other venue in the dataset, with no distinction by
  sport, league, or capacity.
- Scores are normalized within a single run, so they are comparative rankings,
  not an absolute scale.

## Next steps

- Swap the illustrative population field for real census block-group data
  clipped to the buffers.
- Replace circular buffers with drive-time isochrones from a routing service.
- Add demographic and income layers to enrich the market read.
- Weight competitors by capacity, sport, or shared audience rather than a flat
  count.
- Parameterize the scoring weights via the CLI for scenario comparison.
