"""End-to-end pipeline: load venues, build catchments, score, export.

Run from the repo root:

    python -m src.build_outputs --input data/sample/venues_sample.csv

Outputs land in outputs/{tables,qgis,maps}. The GeoPackage is the QGIS entry
point; see docs/qgis_workflow.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from . import config, load_data, scoring
from . import geospatial_utils as geo


def build_feature_table(gdf_geo: gpd.GeoDataFrame) -> pd.DataFrame:
    """Compute per-venue features and the opportunity score."""
    gdf_proj = geo.to_projected(gdf_geo)

    df = pd.DataFrame(gdf_geo.drop(columns="geometry"))
    df["n_competitors"] = geo.count_competitors_within(
        gdf_proj, config.COMPETITOR_RADIUS_MILES
    )
    df["dist_to_nearest_competitor_mi"] = [
        round(d, 2) for d in geo.distance_to_nearest_competitor(gdf_proj)
    ]
    # Area of the largest catchment band, as a reference figure.
    largest = max(config.BUFFER_MILES)
    buffers = geo.create_buffers(gdf_proj, largest)
    df[f"catchment_{largest}mi_area_sq_mi"] = buffers["buffer_area_sq_mi"].round(1)

    df["opportunity_score"] = scoring.compute_opportunity_score(df)
    return df.sort_values("opportunity_score", ascending=False).reset_index(drop=True)


def build_buffer_layers(gdf_geo: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    """Build one buffer GeoDataFrame per band, reprojected back to WGS84."""
    gdf_proj = geo.to_projected(gdf_geo)
    layers: dict[str, gpd.GeoDataFrame] = {}
    for miles in config.BUFFER_MILES:
        band = geo.create_buffers(gdf_proj, miles).to_crs(config.CRS_GEOGRAPHIC)
        layers[f"catchment_{miles}mi"] = band
    return layers


def export_outputs(
    feature_df: pd.DataFrame,
    gdf_geo: gpd.GeoDataFrame,
    buffer_layers: dict[str, gpd.GeoDataFrame],
) -> None:
    """Write CSV, GeoJSON, and a multi-layer GeoPackage for QGIS."""
    for d in (config.TABLES_DIR, config.QGIS_DIR, config.MAPS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # CSV summary.
    csv_path = config.TABLES_DIR / "venue_opportunity_summary.csv"
    feature_df.to_csv(csv_path, index=False)

    # Scored venue points carry the features into the spatial outputs.
    venues_scored = gdf_geo.merge(
        feature_df[["venue_id", "n_competitors",
                    "dist_to_nearest_competitor_mi", "opportunity_score"]],
        on="venue_id",
        how="left",
    )

    # GeoJSON (points only; widely supported and easy to inspect).
    venues_scored.to_file(config.QGIS_DIR / "venues_scored.geojson", driver="GeoJSON")

    # GeoPackage with separate layers for QGIS.
    gpkg = config.QGIS_DIR / "catchment.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    venues_scored.to_file(gpkg, layer="venues_scored", driver="GPKG")
    for name, layer in buffer_layers.items():
        layer.to_file(gpkg, layer=name, driver="GPKG")

    print(f"Wrote {csv_path}")
    print(f"Wrote {config.QGIS_DIR / 'venues_scored.geojson'}")
    print(f"Wrote {gpkg} (layers: venues_scored, {', '.join(buffer_layers)})")


def make_static_map(
    gdf_geo: gpd.GeoDataFrame, buffer_layers: dict[str, gpd.GeoDataFrame]
) -> Path:
    """Render a static PNG: largest buffer band plus scored venue points."""
    fig, ax = plt.subplots(figsize=(11, 8))
    largest = f"catchment_{max(config.BUFFER_MILES)}mi"
    buffer_layers[largest].plot(
        ax=ax, color="#1b6ec2", alpha=0.12, edgecolor="#1b6ec2", linewidth=0.6
    )
    gdf_geo.plot(
        ax=ax,
        column="opportunity_score",
        cmap="viridis",
        markersize=55,
        legend=True,
        legend_kwds={"label": "Opportunity score (0-100)", "shrink": 0.6},
    )
    ax.set_title(
        f"Stadium catchment ({max(config.BUFFER_MILES)} mi) and opportunity score",
        fontsize=13,
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.tight_layout()
    out = config.MAPS_DIR / "catchment_static_map.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")
    return out


def make_interactive_map(
    gdf_geo: gpd.GeoDataFrame, buffer_layers: dict[str, gpd.GeoDataFrame]
) -> Path | None:
    """Render a Folium HTML map if Folium is available."""
    try:
        import folium
    except ImportError:
        print("folium not installed; skipping interactive map.")
        return None

    center = [gdf_geo["latitude"].mean(), gdf_geo["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=4, tiles="cartodbpositron")

    colors = {5: "#2c7fb8", 10: "#41b6c4", 25: "#a1dab4"}
    for miles in config.BUFFER_MILES:
        layer = buffer_layers[f"catchment_{miles}mi"]
        fg = folium.FeatureGroup(name=f"{miles}-mile catchment")
        folium.GeoJson(
            layer.to_json(),
            style_function=lambda _f, c=colors[miles]: {
                "fillColor": c, "color": c, "weight": 1, "fillOpacity": 0.08
            },
        ).add_to(fg)
        fg.add_to(fmap)

    venue_fg = folium.FeatureGroup(name="Venues")
    for _, row in gdf_geo.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color="#253494",
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>{row['venue_name']}</b><br>"
                f"Score: {row.get('opportunity_score', 'n/a')}",
                max_width=250,
            ),
        ).add_to(venue_fg)
    venue_fg.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    out = config.MAPS_DIR / "catchment_interactive_map.html"
    fmap.save(str(out))
    print(f"Wrote {out}")
    return out


def run(input_path: str | Path) -> pd.DataFrame:
    """Run the full pipeline and return the feature table."""
    df = load_data.load_venues(input_path)
    gdf_geo = load_data.to_geodataframe(df)

    feature_df = build_feature_table(gdf_geo)
    # Attach the score back onto the points for mapping.
    gdf_geo = gdf_geo.merge(
        feature_df[["venue_id", "opportunity_score"]], on="venue_id", how="left"
    )
    buffer_layers = build_buffer_layers(gdf_geo)

    export_outputs(feature_df, gdf_geo, buffer_layers)
    make_static_map(gdf_geo, buffer_layers)
    make_interactive_map(gdf_geo, buffer_layers)
    return feature_df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(config.SAMPLE_DATA),
        help="Path to a venue CSV (default: bundled sample dataset).",
    )
    args = parser.parse_args()

    try:
        feature_df = run(args.input)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc

    print("\nTop venues by opportunity score:")
    cols = ["venue_name", "n_competitors",
            "dist_to_nearest_competitor_mi", "opportunity_score"]
    print(feature_df[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
