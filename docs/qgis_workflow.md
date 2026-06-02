# QGIS workflow

The pipeline writes a GeoPackage at `outputs/qgis/catchment.gpkg` with four
layers: `venues_scored`, `catchment_5mi`, `catchment_10mi`, and
`catchment_25mi`. A standalone `venues_scored.geojson` is also written for
quick inspection or tools that prefer GeoJSON.

These steps assume QGIS 3.28 LTR or newer.

## 1. Load the data

1. **Layer → Add Layer → Add Vector Layer**, or drag `catchment.gpkg` onto the
   canvas.
2. When the layer-selection dialog appears, add all four layers.
3. Drag the layers in the panel so `venues_scored` sits on top, with the
   buffer bands beneath it (largest at the bottom).

All layers are EPSG:4326. If you plan to measure on the map, set the project
CRS to a projected one: **Project → Properties → CRS → EPSG:5070** so the QGIS
measure tools report meters/feet rather than degrees.

## 2. Style the buffer bands

For each catchment layer:

1. Right-click → **Properties → Symbology**.
2. Set a single-fill symbol with a low opacity (around 10-15%) and a thin
   outline. Use a lighter shade for the 25-mile band and progressively
   stronger shades inward so overlapping bands read clearly.

Tip: a graduated nested look comes from drawing 25mi (lightest) at the bottom,
then 10mi, then 5mi (strongest) on top.

## 3. Style venues by opportunity score

1. Select `venues_scored` → **Properties → Symbology**.
2. Switch the renderer to **Graduated**.
3. Set **Value** to `opportunity_score`, choose a sequential color ramp
   (e.g. Viridis), and classify with 5 classes using Natural Breaks (Jenks).
4. Increase marker size so high-score venues stand out.

To label points: **Properties → Labels → Single Labels**, label with
`venue_name`, and optionally add `opportunity_score` on a second line.

## 4. Inspect and verify

- Use **Identify Features** to click a venue and read its attributes.
- Open the attribute table (F6) on `venues_scored` to sort by
  `opportunity_score` and confirm it matches the CSV summary.
- Use the **Measure** tool (with the project CRS set to EPSG:5070) to spot
  check a buffer radius against its band.

## 5. Compose a map

1. **Project → New Print Layout**.
2. Add the map frame, a title, a legend (which picks up the graduated score
   classes), a scale bar, and a north arrow.
3. Export to PDF or PNG via **Layout → Export**.

## Refreshing after a new run

The pipeline overwrites `catchment.gpkg` on each run. In QGIS, right-click a
layer → **Reload** (or close and re-add the GeoPackage) to pull updated
geometry and scores without rebuilding your styling from scratch — saved style
files (`.qml`) can be re-applied via **Properties → Style → Load Style**.
