"""
overlay_damage.py — Polygon-orthophoto overlay validation.

Part of SiteLens AI. Layer-0 data preparation.

Data sources:
- GSI post-event orthophoto tiles, captured 11 January 2024.
  Required attribution: 「地理院タイル」 (Map tiles by GSI).
- Vescovo, R. et al. (2025). Noto Peninsula 2024 earthquake building 
  damage assessment. Zenodo. https://doi.org/10.5281/zenodo.11055711. 
  Licensed CC-BY 4.0.

Produces three outputs in overlay_output/:
  1. quicklook_with_polygons.png  - polygon overlay on dimmed orthophoto
  2. damage_only.png              - only destroyed (damage_val=1) buildings highlighted
  3. multihazard.png              - polygons coloured by hazard mode (fire/tsunami/slope/seismic)

Also prints alignment statistics to stdout so you can verify CRS match.

Attribution required when using outputs:
  - Map tiles by GSI (地理院タイル) https://maps.gsi.go.jp/
  - Building damage data: Vescovo et al. 2025, doi:10.5281/zenodo.11055711 (CC-BY 4.0)

Usage:
    Edit TIFF_PATH and GPKG_PATH below, then:
    pip install geopandas rasterio matplotlib pillow
    python overlay_damage.py
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from PIL import Image, ImageEnhance
from rasterio.plot import reshape_as_image
from shapely.geometry import box

# ============================================================================
# CONFIG
# ============================================================================
TIFF_PATH = Path("pipeline/gsi_output/mosaic_20240102noto_wazimanaka_0111do_z18.tif")
GPKG_PATH = Path("data/raw/Noto_Peninsula_Damage_2_5.gpkg")
OUT_DIR = Path("pipeline/overlay_output")

# Image enhancement (GSI Noto orthos are dim; brighten before overlay)
BRIGHTNESS = 1.3
CONTRAST = 1.2

# Damage colour scheme (Vescovo et al. binary: 0=survived, 1=destroyed, 9=obstructed, 99=missing)
DAMAGE_COLORS = {
    0: "#3388ff",   # survived — blue
    1: "#ff3333",   # destroyed — red
    9: "#888888",   # obstructed — grey
    99: "#cccc00",  # missing/inconsistent — yellow (rarely shown)
}
DAMAGE_LABELS = {
    0: "Survived",
    1: "Destroyed",
    9: "Obstructed view",
    99: "Inconsistent footprint",
}
# ============================================================================


def load_image(tiff_path):
    """Load and enhance the orthophoto for visualisation."""
    with rasterio.open(tiff_path) as src:
        rgb = src.read([1, 2, 3])  # (3, H, W)
        bounds = src.bounds
        crs = src.crs
        transform = src.transform

    # Convert to PIL for enhancement
    arr = reshape_as_image(rgb)  # (H, W, 3)
    pil = Image.fromarray(arr)
    pil = ImageEnhance.Brightness(pil).enhance(BRIGHTNESS)
    pil = ImageEnhance.Contrast(pil).enhance(CONTRAST)
    enhanced = np.array(pil)

    return enhanced, bounds, crs, transform


def load_polygons(gpkg_path, bounds, crs):
    """Load Vescovo damage polygons, filter to TIFF bbox."""
    # Use spatial filter to read only what we need (much faster on 140k features)
    bbox_tuple = (bounds.left, bounds.bottom, bounds.right, bounds.top)
    gdf = gpd.read_file(gpkg_path, layer="v2.5", bbox=bbox_tuple)

    # Verify CRS match
    if gdf.crs != crs:
        print(f"  ! CRS mismatch — reprojecting from {gdf.crs} to {crs}")
        gdf = gdf.to_crs(crs)

    return gdf


def make_axes(image, bounds, figsize=(14, 14)):
    """Create a figure with the orthophoto as background, axes in WGS84 coordinates."""
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)
    ax.imshow(image, extent=extent, origin="upper")
    ax.set_xlim(bounds.left, bounds.right)
    ax.set_ylim(bounds.bottom, bounds.top)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.tick_params(labelsize=8)
    return fig, ax


def add_attribution(ax):
    """Add required attribution text in lower-right corner."""
    ax.text(
        0.99, 0.01,
        "Imagery: GSI (地理院タイル)  |  Damage labels: Vescovo et al. 2025 (CC-BY 4.0)",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=7, color="white",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.6, edgecolor="none"),
    )


def render_quicklook(image, bounds, gdf, out_path):
    """All polygons coloured by damage_val."""
    fig, ax = make_axes(image, bounds)

    # Plot each damage class
    for dv, color in DAMAGE_COLORS.items():
        subset = gdf[gdf["damage_val"] == dv]
        if len(subset) == 0:
            continue
        # Skip 99 in the main quicklook — it's not damage information
        if dv == 99:
            continue
        subset.plot(ax=ax, facecolor=color, edgecolor="white",
                    linewidth=0.3, alpha=0.6)

    # Legend
    legend_handles = [
        Patch(facecolor=DAMAGE_COLORS[k], edgecolor="white",
              label=f"{DAMAGE_LABELS[k]} (n={len(gdf[gdf['damage_val']==k])})")
        for k in [0, 1, 9] if len(gdf[gdf["damage_val"] == k]) > 0
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=10,
              framealpha=0.9, title="Building condition")

    ax.set_title(
        "Wajima · Asaichi District — Post-event damage assessment\n"
        "Building footprints classified per Vescovo et al. (2025)",
        fontsize=12, pad=10,
    )
    add_attribution(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> {out_path}")


def render_destroyed_only(image, bounds, gdf, out_path):
    """Only destroyed buildings highlighted (cleaner for hero slide)."""
    fig, ax = make_axes(image, bounds)
    destroyed = gdf[gdf["damage_val"] == 1]
    destroyed.plot(ax=ax, facecolor="#ff2222", edgecolor="white",
                   linewidth=0.4, alpha=0.75)

    ax.set_title(
        f"Wajima · Asaichi District — {len(destroyed)} destroyed buildings\n"
        "Vescovo et al. (2025) ground truth · 2024 Noto Peninsula earthquake",
        fontsize=12, pad=10,
    )
    add_attribution(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> {out_path}")


def render_multihazard(image, bounds, gdf, out_path):
    """Buildings coloured by hazard mode (fire / tsunami / slope failure / seismic-only)."""
    fig, ax = make_axes(image, bounds)

    # Categorise destroyed buildings by hazard
    destroyed = gdf[gdf["damage_val"] == 1].copy()

    fire = destroyed[destroyed["GSI_fire"] == 1]
    tsunami = destroyed[(destroyed["GSI_tsunami"] == 1) & (destroyed["GSI_fire"] != 1)]
    slope = destroyed[
        (destroyed["GSI_slope_failure"] == 1)
        & (destroyed["GSI_fire"] != 1)
        & (destroyed["GSI_tsunami"] != 1)
    ]
    seismic_only = destroyed[
        (destroyed["GSI_fire"] != 1)
        & (destroyed["GSI_tsunami"] != 1)
        & (destroyed["GSI_slope_failure"] != 1)
    ]

    if len(seismic_only) > 0:
        seismic_only.plot(ax=ax, facecolor="#ff8800", edgecolor="white",
                          linewidth=0.4, alpha=0.8, label=f"Seismic ({len(seismic_only)})")
    if len(fire) > 0:
        fire.plot(ax=ax, facecolor="#cc0000", edgecolor="white",
                  linewidth=0.4, alpha=0.85, label=f"Fire ({len(fire)})")
    if len(tsunami) > 0:
        tsunami.plot(ax=ax, facecolor="#0088ff", edgecolor="white",
                     linewidth=0.4, alpha=0.8, label=f"Tsunami ({len(tsunami)})")
    if len(slope) > 0:
        slope.plot(ax=ax, facecolor="#88dd00", edgecolor="white",
                   linewidth=0.4, alpha=0.8, label=f"Slope failure ({len(slope)})")

    legend_handles = [
        Patch(facecolor="#ff8800", edgecolor="white", label=f"Seismic only (n={len(seismic_only)})"),
        Patch(facecolor="#cc0000", edgecolor="white", label=f"Fire (n={len(fire)})"),
    ]
    if len(tsunami) > 0:
        legend_handles.append(Patch(facecolor="#0088ff", edgecolor="white",
                                    label=f"Tsunami (n={len(tsunami)})"))
    if len(slope) > 0:
        legend_handles.append(Patch(facecolor="#88dd00", edgecolor="white",
                                    label=f"Slope failure (n={len(slope)})"))
    ax.legend(handles=legend_handles, loc="upper left", fontsize=10,
              framealpha=0.9, title="Destroyed buildings — peril")

    ax.set_title(
        "Multi-hazard damage attribution — Wajima\n"
        "Per-building hazard layer intersection from GPKG metadata",
        fontsize=12, pad=10,
    )
    add_attribution(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> {out_path}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    print("Loading orthophoto...")
    image, bounds, crs, transform = load_image(TIFF_PATH)
    print(f"  Image: {image.shape[1]}×{image.shape[0]} px")
    print(f"  Bounds (WGS84): W={bounds.left:.5f}, S={bounds.bottom:.5f}, "
          f"E={bounds.right:.5f}, N={bounds.top:.5f}")
    print(f"  CRS: {crs}")

    print("\nLoading damage polygons (spatially filtered to bbox)...")
    gdf = load_polygons(GPKG_PATH, bounds, crs)
    print(f"  Buildings in view: {len(gdf)}")
    print(f"  Damage distribution: {gdf['damage_val'].value_counts().to_dict()}")

    if len(gdf) == 0:
        print("\nERROR: No polygons found in TIFF bbox.")
        print("  Check TIFF and GPKG CRS match, and that bbox is within Noto Peninsula.")
        return

    # Sanity check: are any polygons outside the TIFF bbox?
    tif_box = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
    fully_in = gdf[gdf.geometry.within(tif_box)]
    print(f"  Fully inside bbox: {len(fully_in)} ({100 * len(fully_in)/len(gdf):.0f}%)")

    print("\nRendering overlays...")
    render_quicklook(image, bounds, gdf, OUT_DIR / "quicklook_with_polygons.png")
    render_destroyed_only(image, bounds, gdf, OUT_DIR / "destroyed_only.png")
    render_multihazard(image, bounds, gdf, OUT_DIR / "multihazard.png")

    print("\nDone.")
    print("\nIf alignment looks correct in the rendered PNGs, the GPKG and TIFF agree.")
    print("If polygons appear shifted, check that both are EPSG:4326 (WGS84).")


if __name__ == "__main__":
    main()
