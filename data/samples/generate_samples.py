"""
Generate data/samples/sample_records.json from the full GPKG.

Run once from the project root after the GPKG is in data/raw/:
    python data/samples/generate_samples.py

Produces a ~26-record JSON for hello-world notebooks and tests:
  - Fire zone (Wajima Asaichi): 12 destroyed, 6 survived, 2 obstructed
  - Tsunami zone: 4 destroyed, 2 survived
Mixed hazard types enable the multi-area inspector demo in 03_summarisation.ipynb.

Note: GSI hazard zones are mutually exclusive in this dataset (no building carries
more than one hazard flag). Mixed-hazard summaries arise when an inspector is
assigned to multiple disconnected areas, not from individual multi-hazard buildings.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.data.load_vescovo import load_bbox, load_tsunami_zone, ASAICHI_BBOX
from src.data.records_to_text import gdf_to_records

OUT_PATH = Path("data/samples/sample_records.json")


def main():
    print("Loading fire-zone sample (Wajima Asaichi bbox)...")
    gdf_all = load_bbox(bbox=ASAICHI_BBOX)
    gdf_fire = gdf_all[(gdf_all["damage_val"] == 1) & (gdf_all["GSI_fire"] == 1)].head(12)
    gdf_surv = gdf_all[gdf_all["damage_val"] == 0].head(6)
    gdf_obs  = gdf_all[gdf_all["damage_val"] == 9].head(2)

    print("Loading tsunami-zone sample...")
    gdf_tsunami = load_tsunami_zone()

    gdf = pd.concat([gdf_fire, gdf_surv, gdf_obs, gdf_tsunami], ignore_index=True)
    print(f"  {len(gdf)} records total  ({gdf['damage_val'].value_counts().to_dict()})")
    print(f"  Hazard flags: fire={int((gdf.GSI_fire==1).sum())}  tsunami={int((gdf.GSI_tsunami==1).sum())}  slope={int((gdf.GSI_slope_failure==1).sum())}")

    records = gdf_to_records(gdf)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records -> {OUT_PATH}")


if __name__ == "__main__":
    main()
