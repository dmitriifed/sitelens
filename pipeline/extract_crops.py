"""
extract_crops.py — Per-building image crop extractor.

Part of SiteLens AI. Layer-1 data preparation. Week 11 deliverable.

Concept taught here (one per section):
  1. Geo stack + CRS alignment
  2. Spatial filter — bbox pushed to the file driver, not a Python loop
  3. World ->pixel conversion via rasterio.windows.from_bounds
  4. Context padding — 25% of larger side around each polygon
  5. Square-pad in pixel space — cos(lat) means degree-square != pixel-square
  6. Per-building extract loop — windowed read, PIL save, labels CSV

Inputs:
    data/raw/Noto_Peninsula_Damage_2_5.gpkg
    pipeline/gsi_output/mosaic_20240102noto_wazimanaka_0111do_z18.tif

Outputs:
    data/noto_crops/all/<id>.png    — one PNG per building
    data/noto_crops/labels.csv      — filename, damage_val, split columns

Usage (from repo root):
    python pipeline/extract_crops.py
"""

from pathlib import Path
import datetime
import json
import subprocess
import rasterio
from rasterio.windows import from_bounds, Window
import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent          # repo root
PIPELINE = Path(__file__).parent             # pipeline/

GPKG_PATH = ROOT / "data/raw/Noto_Peninsula_Damage_2_5.gpkg"
TIFF_PATH = PIPELINE / "gsi_output/mosaic_20240102noto_wazimanaka_0111do_z18.tif"
OUT_DIR   = ROOT / "data/noto_crops"
OUT_IMG   = OUT_DIR / "all"
OUT_CSV         = OUT_DIR / "labels.csv"
OUT_SKIPPED_CSV = OUT_DIR / "extraction_skipped.csv"

TARGET_SIZE  = 64    # pixels per side of final crop
CONTEXT_PAD  = 0.25  # extra background around bbox (fraction of larger side)

OUT_IMG.mkdir(parents=True, exist_ok=True)


def git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT
        ).decode().strip()
    except Exception:
        return None


def pad_bbox(minx, miny, maxx, maxy, pad_ratio=CONTEXT_PAD):
    """Expand a bbox by pad_ratio of its larger dimension on all four sides."""
    width  = maxx - minx
    height = maxy - miny
    pad    = pad_ratio * max(width, height)
    return (minx - pad, miny - pad, maxx + pad, maxy + pad)



# ---------------------------------------------------------------------------
# Concept 1: open the raster and assert CRS
# ---------------------------------------------------------------------------
src = rasterio.open(TIFF_PATH)
tiff_crs = src.crs
tiff_bounds = src.bounds   # (left, bottom, right, top) in world coords

print(f"Raster CRS:    {tiff_crs}")
print(f"Raster bounds: {tiff_bounds}")
print(f"Raster shape:  {src.height} x {src.width} pixels")

# ---------------------------------------------------------------------------
# Concept 2: spatial filter at read time — push bbox down to the file driver
# ---------------------------------------------------------------------------
# The GPKG has 140k polygons across the full peninsula; our raster covers a
# few city blocks. bbox= tells the driver to return only polygons whose
# bounding boxes intersect the raster extent — no Python-side loop needed.
gdf = gpd.read_file(
    GPKG_PATH,
    layer="v2.5",
    bbox=(tiff_bounds.left, tiff_bounds.bottom, tiff_bounds.right, tiff_bounds.top),
)
print(f"Buildings in raster extent: {len(gdf)}")
print(gdf["damage_val"].value_counts())

# Assert CRS match before any geometry math — same principle as the raster check.
assert gdf.crs == tiff_crs, f"CRS mismatch: {gdf.crs} vs {tiff_crs}"

# Capture pre-filter counts for the summary before dropping ambiguous labels.
n_in_extent   = len(gdf)
damage_counts = gdf["damage_val"].value_counts().to_dict()

# Drop ambiguous labels (9 = obstructed, 99 = inconsistent footprint).
gdf = gdf[gdf["damage_val"].isin([0, 1])].copy()
gdf["label"] = gdf["damage_val"].map({0: "survived", 1: "destroyed"})
print(f"\nValid buildings: {len(gdf)}")
print(gdf["label"].value_counts())

# ---------------------------------------------------------------------------
# Concept 6: per-building extract loop
# Concepts 3, 4, 5 applied at scale
# ---------------------------------------------------------------------------
rows_out    = []
skipped_rows = []

for idx, row in gdf.iterrows():
    poly = row.geometry
    if poly is None or poly.is_empty:
        continue

    # Concept 4: pad for context (pad_bbox is correct in degrees — symmetric)
    minx, miny, maxx, maxy = poly.bounds
    minx, miny, maxx, maxy = pad_bbox(minx, miny, maxx, maxy)

    # Concept 3: world bbox ->pixel window (un-squared)
    w_raw = from_bounds(minx, miny, maxx, maxy, transform=src.transform)

    # Concept 5 (corrected): squarify in PIXEL space, not world space.
    # At 37.4N, 1 deg lon ~88.7 km vs 1 deg lat ~111 km, so "square in
    # degrees" is a 0.80:1 rectangle in pixels — squarifying in degrees
    # stretches horizontal features. Fix: squarify after world->pixel.
    size = max(w_raw.width, w_raw.height)
    col_off = w_raw.col_off - (size - w_raw.width) / 2
    row_off = w_raw.row_off - (size - w_raw.height) / 2
    window = Window(col_off, row_off, size, size)

    # boundless=True: buildings at the raster edge read fine; out-of-bounds
    # pixels come back as fill_value=0 (black) rather than raising an error.
    # out_shape resizes at read time — bilinear from source pixels, no
    # intermediate array, faster and slightly higher quality than PIL resize.
    arr = src.read(
        window=window,
        boundless=True,
        fill_value=0,
        out_shape=(src.count, TARGET_SIZE, TARGET_SIZE),
        resampling=rasterio.enums.Resampling.bilinear,
    )

    # Quality filters — flag rather than silently include bad crops.
    arr_rgb     = arr[:3]
    total_px    = arr_rgb.shape[1] * arr_rgb.shape[2]
    zero_frac   = float((arr_rgb.sum(axis=0) == 0).sum() / total_px)
    pixel_std   = float(arr_rgb.std())

    s_fid = row["s_fid"]
    if zero_frac > 0.20 or pixel_std < 10:
        skipped_rows.append({
            "s_fid":      s_fid,
            "idx":        idx,
            "reason":     "edge_fill" if zero_frac > 0.20 else "low_variance",
            "zero_frac":  zero_frac,
            "pixel_std":  pixel_std,
            "damage_val": int(row["damage_val"]),
            "label":      row["label"],
        })
        continue

    # Rasterio: (bands, H, W) uint16/uint8 ->PIL wants (H, W, bands) uint8
    if arr.shape[0] == 1:
        img = Image.fromarray(arr[0].astype(np.uint8), mode="L")
    else:
        rgb = np.transpose(arr[:3], (1, 2, 0)).astype(np.uint8)
        img = Image.fromarray(rgb, mode="RGB")

    out_name = f"bldg_{int(s_fid):06d}.png" if str(s_fid).isdigit() else f"bldg_{idx:06d}.png"
    img.save(OUT_IMG / out_name)

    rows_out.append({
        "filepath":          str(OUT_IMG / out_name),
        "s_fid":             row["s_fid"],
        "label":             row["label"],
        "damage_val":        int(row["damage_val"]),
        # location traceability
        "centroid_lon":      float(poly.centroid.x),
        "centroid_lat":      float(poly.centroid.y),
        "polygon_wkt":       poly.wkt,
        # pixel-space traceability — reproduce this exact crop from the raster
        "window_col_off":    float(window.col_off),
        "window_row_off":    float(window.row_off),
        "window_width":      float(window.width),
        "window_height":     float(window.height),
        # damage metadata
        "municipality":      row["municipality"],
        "gsi_fire":          int(row["GSI_fire"]),
        "gsi_tsunami":       int(row["GSI_tsunami"]),
        "gsi_slope_failure": int(row["GSI_slope_failure"]),
        "usgs_mmi":          float(row["USGS_MMI"]),
        "conf":              row["conf"],
    })

src.close()

# Concept 6 cont.: write the labels CSV in flow_from_dataframe shape.
# Extra hazard columns (gsi_fire, usgs_mmi, …) are free to carry now —
# they're needed for multi-peril attribution later without re-running the extractor.
labels_df = pd.DataFrame(rows_out)
labels_df.to_csv(OUT_CSV, index=False)

skipped_df = pd.DataFrame(skipped_rows)
skipped_df.to_csv(OUT_SKIPPED_CSV, index=False)

print(f"\nSaved {len(labels_df)} crops ->{OUT_IMG}")
print(f"Skipped    {len(skipped_df)} crops ->{OUT_SKIPPED_CSV}")
if not skipped_df.empty:
    print(skipped_df["reason"].value_counts().to_string())
print(f"\nLabels CSV ->{OUT_CSV}")
print(labels_df["label"].value_counts())

summary = {
    "run_timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    "git_commit":        git_hash(),
    "script":            "pipeline/extract_crops.py",
    "inputs": {
        "gpkg":          str(GPKG_PATH),
        "raster":        str(TIFF_PATH),
        "raster_crs":    str(tiff_crs),
        "raster_bounds": list(tiff_bounds),
    },
    "parameters": {
        "target_size":   TARGET_SIZE,
        "context_pad":   CONTEXT_PAD,
        "resampling":    "bilinear",
        "squarify_mode": "pixel_space",
    },
    "counts": {
        "polygons_in_extent":     n_in_extent,
        "dropped_damage_val_9":   int(damage_counts.get(9,  0)),
        "dropped_damage_val_99":  int(damage_counts.get(99, 0)),
        "skipped_edge_or_lowvar": len(skipped_rows),
        "crops_written":          len(labels_df),
    },
    "class_balance": labels_df["label"].value_counts().to_dict(),
}
(OUT_DIR / "extraction_summary.json").write_text(json.dumps(summary, indent=2))
print(f"\nSummary    ->{OUT_DIR / 'extraction_summary.json'}")
