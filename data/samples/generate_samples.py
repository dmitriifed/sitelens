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

from src.data.load_vescovo import load_sample
from src.data.records_to_text import gdf_to_records

OUT_PATH = Path("data/samples/sample_records.json")


def main():
    print("Loading stratified sample from GPKG...")
    gdf = load_sample(n_destroyed=12, n_survived=6, n_obstructed=2)
    print(f"  {len(gdf)} records loaded  ({gdf['damage_val'].value_counts().to_dict()})")

    records = gdf_to_records(gdf)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records -> {OUT_PATH}")


if __name__ == "__main__":
    main()
