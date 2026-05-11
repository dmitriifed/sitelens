"""
fetch_gsi_tiles.py — GSI Noto Peninsula orthophoto tile fetcher and stitcher.

Part of SiteLens AI. Layer-0 data preparation.

Data sources:
- GSI post-event orthophoto tiles, captured 11 January 2024.
  Required attribution: 「地理院タイル」 (Map tiles by GSI).
- Vescovo, R. et al. (2025). Noto Peninsula 2024 earthquake building 
  damage assessment. Zenodo. https://doi.org/10.5281/zenodo.11055711. 
  Licensed CC-BY 4.0.

Downloads GSI post-event orthophoto tiles covering a specified bounding box,
stitches them into a single georeferenced GeoTIFF, and exports a quick-look PNG.

Attribution: GSI tiles (地理院タイル) are published by the Geospatial
Information Authority of Japan. Cite as "Map tiles by GSI" with source URL
https://maps.gsi.go.jp/ when using in any deliverable.

Usage:
    python fetch_gsi_tiles.py

Edit the CONFIG block below to change layer/bbox/zoom.

Last used coordinates (layer: 20240102noto_wazimanaka_0111do):
  HERO — tight Asaichi fire zone (current):
    BBOX = (136.895, 37.394, 136.903, 37.399), ZOOM = 18
    42 tiles, 1792x1536 px — burnt Asaichi market district, south-shifted framing

  CONTEXT — wider Wajima overview:
    BBOX = (136.870, 37.380, 136.920, 37.410), ZOOM = 17
    300 tiles, 5120x3840 px — full Wajima central area, ~1 m/pixel
"""

import os
import time
from io import BytesIO
from pathlib import Path

import mercantile
import rasterio
import requests
from PIL import Image
from rasterio.transform import from_bounds

# ============================================================================
# CONFIG — edit these
# ============================================================================

# Layer name from GSI (from the ls= parameter in the viewer URL)
# Strong picks:
#   20240102noto_wazimanaka_0111do  - Wajima Central, Jan 11 flight (clearer)
#   20240102noto_wazimahigashi_0114do  - Wajima East, Jan 14 (later, cleaner)
#   20240102noto_suzu_0114do  - Suzu, Jan 14
LAYER = "20240102noto_wazimanaka_0111do"

# Bounding box: (min_lon, min_lat, max_lon, max_lat) in WGS84
# Asaichi fire district + central Wajima (~1.5 km × 1.5 km)
BBOX = (136.895, 37.394, 136.903, 37.399)

# Zoom level: 17 = ~1 m/pixel, 18 = ~0.6 m/pixel at this latitude
# Use 18 for hero close-ups, 17 for wider context
ZOOM = 18

# Output directory (relative to this script)
OUT_DIR = Path("gsi_output")
TILE_CACHE = OUT_DIR / f"tiles_{LAYER}_z{ZOOM}"

# Polite rate limiting — GSI is a government server, do not hammer it
REQUEST_DELAY_S = 0.1  # 10 requests/second max
REQUEST_TIMEOUT_S = 15

# User-Agent — identify yourself honestly
USER_AGENT = "SensingRisk-prototype/0.1 (research, contact: Dmitrii Fedorov)"

# ============================================================================
# END CONFIG
# ============================================================================


def fetch_tile(z: int, x: int, y: int, layer: str, cache_dir: Path,
               session: requests.Session) -> Path | None:
    """Fetch a single tile, cache it locally. Returns path to cached file or None if tile is empty/404."""
    cache_path = cache_dir / f"{z}_{x}_{y}.png"
    if cache_path.exists():
        return cache_path if cache_path.stat().st_size > 0 else None

    url = f"https://cyberjapandata.gsi.go.jp/xyz/{layer}/{z}/{x}/{y}.png"
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT_S)
        if r.status_code == 200 and len(r.content) > 200:
            # Tile has real content (not a blank/error response)
            cache_path.write_bytes(r.content)
            return cache_path
        else:
            # Mark as known-empty with zero-byte file so we don't retry
            cache_path.touch()
            return None
    except requests.RequestException as e:
        print(f"  ! tile {z}/{x}/{y} failed: {e}")
        return None


def main():
    print(f"GSI tile fetcher")
    print(f"Layer: {LAYER}")
    print(f"BBox:  {BBOX}")
    print(f"Zoom:  {ZOOM}")

    # Create output directories
    OUT_DIR.mkdir(exist_ok=True)
    TILE_CACHE.mkdir(parents=True, exist_ok=True)

    # Compute tile grid for bbox
    tiles = list(mercantile.tiles(*BBOX, zooms=ZOOM))
    if not tiles:
        print("No tiles in bbox — check coordinates (minlon, minlat, maxlon, maxlat)")
        return

    xs = [t.x for t in tiles]
    ys = [t.y for t in tiles]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    cols = x_max - x_min + 1
    rows = y_max - y_min + 1

    print(f"\nTile grid: {cols} cols x {rows} rows = {len(tiles)} tiles")
    est_seconds = len(tiles) * REQUEST_DELAY_S
    print(f"Est. download time: {est_seconds:.0f}s")
    print()

    # Download
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    fetched, empty = 0, 0
    for i, tile in enumerate(tiles, 1):
        result = fetch_tile(tile.z, tile.x, tile.y, LAYER, TILE_CACHE, session)
        if result:
            fetched += 1
        else:
            empty += 1

        if i % 20 == 0 or i == len(tiles):
            print(f"  {i}/{len(tiles)}  fetched={fetched}  empty={empty}")
        time.sleep(REQUEST_DELAY_S)

    if fetched == 0:
        print("\nERROR: No tiles returned content. Possible causes:")
        print(f"  1. Layer name wrong. Confirm: {LAYER}")
        print(f"  2. Bbox outside layer coverage area")
        print(f"  3. Zoom too high (layer may not have z={ZOOM} tiles)")
        print(f"\nTry opening this URL in browser to test:")
        sample = tiles[len(tiles) // 2]
        print(f"  https://cyberjapandata.gsi.go.jp/xyz/{LAYER}/{sample.z}/{sample.x}/{sample.y}.png")
        return

    print(f"\nStitching {fetched} tiles into mosaic...")

    # Stitch into a big image
    tile_size = 256
    mosaic = Image.new("RGBA", (cols * tile_size, rows * tile_size), (0, 0, 0, 0))

    for tile in tiles:
        cache_path = TILE_CACHE / f"{tile.z}_{tile.x}_{tile.y}.png"
        if not cache_path.exists() or cache_path.stat().st_size == 0:
            continue
        try:
            img = Image.open(cache_path).convert("RGBA")
            px = (tile.x - x_min) * tile_size
            py = (tile.y - y_min) * tile_size
            mosaic.paste(img, (px, py))
        except Exception as e:
            print(f"  ! couldn't paste {cache_path.name}: {e}")

    # Compute geographic bounds of the mosaic (may be slightly larger than input bbox
    # because it's aligned to tile boundaries)
    ul_bounds = mercantile.bounds(mercantile.Tile(x_min, y_min, ZOOM))
    lr_bounds = mercantile.bounds(mercantile.Tile(x_max, y_max, ZOOM))
    mosaic_bbox = (ul_bounds.west, lr_bounds.south, lr_bounds.east, ul_bounds.north)

    # Save quick-look PNG (RGB, dropping alpha) with visual enhancement
    png_path = OUT_DIR / f"quicklook_{LAYER}_z{ZOOM}.png"
    mosaic_rgb = mosaic.convert("RGB")
    from PIL import ImageEnhance
    import numpy as np
    mosaic_rgb = ImageEnhance.Brightness(mosaic_rgb).enhance(1 + 30 / 255)
    mosaic_rgb = ImageEnhance.Contrast(mosaic_rgb).enhance(1.5)
    arr = np.array(mosaic_rgb).astype(np.float32) / 255.0
    arr = np.clip(arr ** 0.7, 0, 1)
    mosaic_rgb = Image.fromarray((arr * 255).astype(np.uint8))
    mosaic_rgb.save(png_path, "PNG", optimize=True)
    print(f"  -> {png_path}  ({mosaic_rgb.size[0]}x{mosaic_rgb.size[1]}px)")

    # Save georeferenced GeoTIFF
    tiff_path = OUT_DIR / f"mosaic_{LAYER}_z{ZOOM}.tif"
    width, height = mosaic_rgb.size
    import numpy as np
    arr = np.array(mosaic_rgb).transpose(2, 0, 1)  # (bands, rows, cols)

    transform = from_bounds(
        mosaic_bbox[0], mosaic_bbox[1],
        mosaic_bbox[2], mosaic_bbox[3],
        width, height
    )

    with rasterio.open(
        tiff_path, "w",
        driver="GTiff",
        height=height, width=width,
        count=3, dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
        compress="lzw",
        tiled=True,
    ) as dst:
        dst.write(arr)
        dst.update_tags(
            source="GSI (Geospatial Information Authority of Japan)",
            source_url="https://maps.gsi.go.jp/",
            layer=LAYER,
            attribution="Map tiles by GSI (地理院タイル)",
        )
    print(f"  -> {tiff_path}  (georeferenced, EPSG:4326)")

    print(f"\nDone.")
    print(f"Mosaic bbox (WGS84): {mosaic_bbox}")
    print(f"\nATTRIBUTION REQUIRED:")
    print(f'  "Map tiles by GSI (Chiriin Tile)" - source: https://maps.gsi.go.jp/')
    print(f"  See: https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html")


if __name__ == "__main__":
    main()
