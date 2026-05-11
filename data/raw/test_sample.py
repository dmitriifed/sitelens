

import geopandas as gpd
import pandas as pd

gdf = gpd.read_file("data/raw/Noto_Peninsula_Damage_2_5.gpkg", layer="v2.5", rows=5)
print("=== COLUMNS ===")
print(gdf.dtypes.to_string())
print("\n=== SAMPLE ROWS ===")
print(gdf.drop(columns="geometry").head(3).to_string())
print("\n=== CRS ===")
print(gdf.crs)


# Load a stratified sample: some survived, some destroyed, some obstructed
gdf_destroyed = gpd.read_file("data/raw/Noto_Peninsula_Damage_2_5.gpkg", layer="v2.5",
                               where="damage_val = 1").head(12)
gdf_survived  = gpd.read_file("data/raw/Noto_Peninsula_Damage_2_5.gpkg", layer="v2.5",
                               where="damage_val = 0").head(6)
gdf_obs       = gpd.read_file("data/raw/Noto_Peninsula_Damage_2_5.gpkg", layer="v2.5",
                               where="damage_val = 9").head(2)

gdf = pd.concat([gdf_destroyed, gdf_survived, gdf_obs], ignore_index=True)
print(gdf["damage_val"].value_counts())  # should show 12 / 6 / 2
