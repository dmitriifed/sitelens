"""Load and spatially filter the Vescovo et al. 2025 GPKG damage dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

DEFAULT_GPKG = Path("data/raw/Noto_Peninsula_Damage_2_5.gpkg")
LAYER = "v2.5"

WAJIMA_BBOX = (136.870, 37.380, 136.920, 37.410)
ASAICHI_BBOX = (136.895, 37.394, 136.903, 37.399)


def load_sample(gpkg_path=DEFAULT_GPKG, n_destroyed=12, n_survived=6, n_obstructed=2):
    """Stratified sample: n_destroyed destroyed + n_survived survived + n_obstructed obstructed."""
    gdf_d = gpd.read_file(gpkg_path, layer=LAYER, where="damage_val = 1").head(n_destroyed)
    gdf_s = gpd.read_file(gpkg_path, layer=LAYER, where="damage_val = 0").head(n_survived)
    gdf_o = gpd.read_file(gpkg_path, layer=LAYER, where="damage_val = 9").head(n_obstructed)
    return pd.concat([gdf_d, gdf_s, gdf_o], ignore_index=True)


def load_bbox(gpkg_path=DEFAULT_GPKG, bbox=WAJIMA_BBOX):
    """All records within a (west, south, east, north) bounding box."""
    return gpd.read_file(gpkg_path, layer=LAYER, bbox=bbox)


def load_fire_zone(gpkg_path=DEFAULT_GPKG):
    """Destroyed buildings in the Wajima Asaichi fire zone (GSI_fire=1)."""
    gdf = load_bbox(gpkg_path=gpkg_path, bbox=ASAICHI_BBOX)
    return gdf[(gdf["damage_val"] == 1) & (gdf["GSI_fire"] == 1)]
