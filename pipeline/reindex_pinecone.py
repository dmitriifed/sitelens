"""
reindex_pinecone.py — Re-index Pinecone from labels.csv using real s_fid IDs.

Replaces the old sample_records index (bldg_XXXX synthetic IDs, ~26 vectors)
with all buildings from labels.csv (real Vescovo s_fid IDs, ~1,967 vectors).
This closes the two-corpus seam: Pinecone IDs now match predictions.csv and
hit_to_record() so the popup model line and lat/lon map rendering work.

Run from repo root:
    python pipeline/reindex_pinecone.py

Safe to re-run: upsert is idempotent by ID.
"""

from __future__ import annotations
from pathlib import Path
import os, sys

import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

LABELS_CSV  = REPO_ROOT / "data" / "noto_crops" / "labels.csv"
MODEL_NAME  = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE  = 100

MMI_LABELS = [
    (9, "violent"), (8, "severe"), (7, "very strong"),
    (6, "strong"),  (4, "moderate"), (0, "light"),
]

def mmi_label(mmi: float) -> str:
    for threshold, label in MMI_LABELS:
        if mmi >= threshold:
            return label
    return "light"

def row_to_text(row) -> str:
    outcome = "destroyed" if int(row.damage_val) > 0 else "survived"
    hazards = [h for h, flag in [
        ("fire",          row.gsi_fire),
        ("tsunami",       row.gsi_tsunami),
        ("slope failure", row.gsi_slope_failure),
    ] if int(flag) == 1]
    haz_str = ", ".join(hazards) if hazards else "seismic only"
    mmi     = float(row.usgs_mmi)
    conf    = str(row.conf).strip()
    return (
        f"Building {outcome}. Hazard: {haz_str}. "
        f"MMI {mmi:.1f} ({mmi_label(mmi)} shaking). "
        f"Evidence: {conf}-source assessment."
    )


def main():
    # --- Load labels ---
    df = pd.read_csv(LABELS_CSV)
    if "s_fid" not in df.columns:
        df = df.reset_index().rename(columns={df.columns[0]: "s_fid"})
    df = df.drop_duplicates(subset="s_fid").reset_index(drop=True)
    print(f"Loaded {len(df)} buildings from labels.csv")

    # --- Build records ---
    records = []
    for _, row in df.iterrows():
        records.append({
            "id":   str(row.s_fid),
            "text": row_to_text(row),
            "lat":  float(row.centroid_lat),
            "lon":  float(row.centroid_lon),
        })

    # --- Embed ---
    print(f"Embedding {len(records)} texts with {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    texts = [r["text"] for r in records]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True).tolist()

    # --- Pinecone upsert ---
    api_key    = os.environ["PINECONE_API_KEY"]
    index_name = os.environ.get("PINECONE_INDEX", "sitelens")
    pc    = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    print(f"Upserting to Pinecone index '{index_name}' in batches of {BATCH_SIZE} ...")
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch_r = records[i : i + BATCH_SIZE]
        batch_e = embeddings[i : i + BATCH_SIZE]
        vectors = [
            {
                "id":     r["id"],
                "values": e,
                "metadata": {
                    "text": r["text"],
                    "lat":  r["lat"],
                    "lon":  r["lon"],
                },
            }
            for r, e in zip(batch_r, batch_e)
        ]
        index.upsert(vectors=vectors)
        total += len(vectors)
        print(f"  {total}/{len(records)}")

    stats = index.describe_index_stats()
    print(f"\nDone. Index now contains {stats['total_vector_count']} vectors.")
    print("Sample IDs in this batch:", [r["id"] for r in records[:3]])


if __name__ == "__main__":
    main()
