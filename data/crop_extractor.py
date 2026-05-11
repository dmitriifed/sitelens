"""
crop_extractor.py — Per-building crop extractor.

Part of SiteLens AI. Layer-1 data preparation. Week 11 deliverable.

Extracts per-building crops from the orthophoto GeoTIFF at a fixed size
(256x256 px) centred on each Vescovo et al. damage polygon.

Inputs:
    - GeoTIFF from fetch_gsi_tiles.py
    - Damage polygon GeoPackage (Vescovo et al. 2025)

Outputs:
    - crops/ directory with numbered PNG files
    - crops/metadata.csv  (polygon ID, damage_val, hazard class, crop path)
"""

# TODO: implement in Week 11
