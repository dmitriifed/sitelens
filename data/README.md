# Data layer — attribution and documentation

This directory holds Layer-0 (data fetching and preparation) scripts for SiteLens AI.

## Sources and attribution

All data ingested by scripts in this directory is openly available and attribution is preserved in derived outputs.

**Building damage labels:** Vescovo, R. et al. (2025). *Noto Peninsula 2024 earthquake building damage assessment.* Zenodo. https://doi.org/10.5281/zenodo.11055711. Licensed CC-BY 4.0. n = 140,208 buildings, F1 = 0.94 (human ground-survey validation).

**Aerial imagery:** Geospatial Information Authority of Japan (GSI). Post-event orthophoto tiles, captured 11 January 2024, ~0.47 m/pixel at zoom 18 (Wajima Asaichi fire district). Required attribution on any derived imagery: 「地理院タイル」 (Map tiles by GSI). Source: https://maps.gsi.go.jp/

## Scripts

- **fetch_gsi_tiles.py** — GSI tile fetcher and stitcher. Downloads post-event orthophoto tiles covering a bounding box, stitches them into a georeferenced GeoTIFF, exports quick-look PNG.
- **overlay_damage.py** — Polygon overlay validator. Loads Vescovo et al. building polygons, overlays on orthophoto, produces three visualisations (all-damage, destroyed-only, multihazard).

## Notes

Layer-0 scripts are validated and do not require further refinement before feeding into Layer-1 (per-building crop extraction, Week 11).

Both scripts require the Noto Peninsula damage dataset (GPKG) and GSI orthophoto layer access. Configuration is in the CONFIG block at the top of each script.
