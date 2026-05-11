"""
Generate data/samples/sample_records.json from the full GPKG.

Run once from the project root after the GPKG is in data/raw/:
    python data/samples/generate_samples.py

Produces a committed 20-record JSON for hello-world notebooks and tests,
so those can run without the full 140k-record GPKG.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.data.load_vescovo import load_bbox, ASAICHI_BBOX
from src.data.records_to_text import gdf_to_records

OUT_PATH = Path("data/samples/sample_records.json")


def main():
    print("Loading fire-zone sample from GPKG (Wajima Asaichi bbox)...")
    gdf_all = load_bbox(bbox=ASAICHI_BBOX)
    gdf_fire = gdf_all[(gdf_all["damage_val"] == 1) & (gdf_all["GSI_fire"] == 1)].head(12)
    gdf_surv = gdf_all[gdf_all["damage_val"] == 0].head(6)
    gdf_obs  = gdf_all[gdf_all["damage_val"] == 9].head(2)
    gdf = pd.concat([gdf_fire, gdf_surv, gdf_obs], ignore_index=True)
    print(f"  {len(gdf)} records loaded  ({gdf['damage_val'].value_counts().to_dict()})")

    records = gdf_to_records(gdf)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records -> {OUT_PATH}")


if __name__ == "__main__":
    main()
