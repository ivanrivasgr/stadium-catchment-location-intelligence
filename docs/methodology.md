# Methodology

This document explains the analytical decisions behind the catchment and
opportunity scoring, and where the model can break down.

## Why CRS matters

Source coordinates are latitude/longitude in WGS84 (EPSG:4326). That frame is
fine for storing and displaying points, but it is a geographic CRS measured in
degrees. A degree of latitude is roughly constant on the ground, but a degree
of longitude shrinks as you move away from the equator. Computing distances or
buffer areas directly in degrees mixes two different real-world units and
produces numbers that do not correspond to miles or square miles.

## Why a projected CRS for distance and area

Before any buffering or distance work, the points are reprojected to
**EPSG:5070 (NAD83 / Conus Albers)**, an equal-area projection covering the
continental US measured in meters. In a projected CRS:

- buffers are true circles of a fixed ground radius,
- areas come out in consistent units (converted here to square miles),
- nearest-neighbor distances are real ground distances.

EPSG:5070 is a reasonable single-CRS choice for a CONUS-wide dataset. It
preserves area well and keeps distance error modest across the lower 48. For a
study confined to one metro area, a local UTM zone would be marginally more
accurate. For data outside the US, this CRS should be swapped for an
appropriate regional one in `src/config.py`.

## Catchment buffers

For each venue the pipeline builds circular buffers at 5, 10, and 25 miles.
These approximate drive-time bands in a simple, transparent way. They do not
account for road networks, water barriers, or travel time, so a 25-mile circle
over a bay or mountain range overstates the reachable population. A true
isochrone (drive-time) analysis would refine this, at the cost of needing a
routing service.

## Features

For each venue:

- **buffer_area_sq_mi** — area of the largest catchment band, a sanity-check
  reference value.
- **n_competitors** — count of other venues within the competitor radius
  (default 25 miles). A proxy for how saturated the local market is.
- **dist_to_nearest_competitor_mi** — straight-line distance to the closest
  other venue. Higher means more local exclusivity.
- **metro_population** — illustrative addressable-market figure carried from
  the input. In the sample data this is a synthetic placeholder; replace it
  with real ACS / census block-group population intersected against the
  buffers for a defensible result.

## Opportunity score

The score is a weighted blend of three min-max normalized terms, scaled to
0-100:

```
score = 100 * (
      w_pop        * normalized(population)
    + w_comp       * (1 - normalized(n_competitors))
    + w_isolation  * normalized(distance_to_nearest_competitor)
)
```

Default weights (in `config.SCORE_WEIGHTS`): population 0.50, competition 0.30,
isolation 0.20. The logic: a strong expansion or market-reach target has a
large addressable population, few competing venues nearby, and sits some
distance from the closest competitor.

Normalization is relative to the venues in the current dataset, so scores are
**comparative within a run**, not absolute. Adding or removing venues shifts
the min/max and therefore the scores. This is intentional for ranking sites
against each other, but it means a score of 60 in one dataset is not directly
comparable to a 60 in another.

## Limitations

- Population in the sample data is synthetic and labeled as such. Real
  conclusions require real demographic data clipped to the buffers.
- Buffers are straight-line, not drive-time.
- "Competitor" is any other venue in the file; it does not distinguish league,
  sport, capacity, or whether two venues actually compete for the same
  audience.
- Scores are relative to the current dataset, not an absolute scale.
- Single-CRS reprojection introduces small distortion at the edges of CONUS.

These are all addressable with richer inputs; the pipeline structure stays the
same.
