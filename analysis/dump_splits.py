"""
dump_splits.py — reproduce train.py's exact train/val/test split and dump the
val-set id list for the disciplined manual sample review.

Read-only. Touches only tracked files:
    data/noto_crops/labels.csv      (via model/train.py's load_labeled_frame)
    data/noto_crops/predictions.csv
    model/weights/test_split.csv    (reconstruction check only)

Outputs (untracked working artefacts):
    analysis/splits/train_ids.csv
    analysis/splits/val_ids.csv
    analysis/splits/val_misses.csv  <- tomorrow's eyeball list

The reconstruction is verified against model/weights/test_split.csv before any
output is written. If the 296 test s_fids do not match exactly the script
raises and writes nothing — a mismatch means the split logic drifted and the
val list would be untrustworthy.

Run from anywhere:  python analysis/dump_splits.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Split reproduction
#
# model/train.py is imported directly rather than re-implemented so the loader
# and the two split calls cannot drift from the training script. Importing it
# is side-effect-free: module level is imports + CONFIG constants + a read-only
# torch.cuda.is_available() check (model/train.py:24-66); main() is guarded by
# `if __name__ == "__main__"` (model/train.py:219-220) and is not run here.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "model"))
import train  # noqa: E402  (model/train.py)

# labels.csv -> binary label `y`, on-disk existence filter, drop_duplicates on
# s_fid keeping first, reset_index.  (model/train.py:72-99, load_labeled_frame)
df = train.load_labeled_frame()

# Two stratified splits, identical args to model/train.py:155-159.
train_val, test = train_test_split(
    df, test_size=train.TEST_FRAC, stratify=df["y"], random_state=train.SEED
)
val_rel = train.VAL_FRAC / (1 - train.TEST_FRAC)
train_df, val_df = train_test_split(
    train_val, test_size=val_rel, stratify=train_val["y"], random_state=train.SEED
)

print(
    f"Reconstructed split: train={len(train_df)}  val={len(val_df)}  test={len(test)}"
)

# ---------------------------------------------------------------------------
# Verify the reconstructed test set against the locked file BEFORE writing.
# ---------------------------------------------------------------------------
locked = pd.read_csv(REPO_ROOT / "model" / "weights" / "test_split.csv",
                     dtype={"s_fid": str})
locked_ids = set(locked["s_fid"])
recon_ids = set(test["s_fid"].astype(str))

if recon_ids != locked_ids:
    only_locked = sorted(locked_ids - recon_ids)
    only_recon = sorted(recon_ids - locked_ids)
    raise SystemExit(
        "TEST-SPLIT RECONSTRUCTION MISMATCH — not writing any output.\n"
        f"  locked test_split.csv: {len(locked_ids)} s_fids\n"
        f"  reconstructed test   : {len(recon_ids)} s_fids\n"
        f"  in locked only ({len(only_locked)}): {only_locked[:10]}\n"
        f"  in reconstructed only ({len(only_recon)}): {only_recon[:10]}"
    )
print(f"Test-split reconstruction MATCHES model/weights/test_split.csv "
      f"({len(recon_ids)} s_fids).")

# ---------------------------------------------------------------------------
# Write the id lists.
# ---------------------------------------------------------------------------
out_dir = REPO_ROOT / "analysis" / "splits"
out_dir.mkdir(parents=True, exist_ok=True)

train_df[["s_fid", "y"]].to_csv(out_dir / "train_ids.csv", index=False)
val_df[["s_fid", "y"]].to_csv(out_dir / "val_ids.csv", index=False)
print(f"Wrote {out_dir / 'train_ids.csv'}  ({len(train_df)} rows)")
print(f"Wrote {out_dir / 'val_ids.csv'}  ({len(val_df)} rows)")

# ---------------------------------------------------------------------------
# val_misses.csv — val rows whose TRUE label is destroyed (y == 1) that the
# model called survived (pred_prob < 0.5). Joined to labels.csv context.
# This is the manual review list; the test set stays untouched for selection.
# ---------------------------------------------------------------------------
preds = pd.read_csv(REPO_ROOT / "data" / "noto_crops" / "predictions.csv",
                    dtype={"s_fid": str})
labels = pd.read_csv(REPO_ROOT / "data" / "noto_crops" / "labels.csv",
                     dtype={"s_fid": str})

val_ids = val_df["s_fid"].astype(str)
val_destroyed = val_df[val_df["y"] == 1]["s_fid"].astype(str)

misses = (
    preds[preds["s_fid"].isin(set(val_destroyed)) & (preds["pred_prob"] < 0.5)]
    .merge(
        labels[["s_fid", "window_width", "gsi_fire", "municipality"]],
        on="s_fid", how="left",
    )
    [["s_fid", "pred_prob", "window_width", "gsi_fire", "municipality"]]
    .sort_values("pred_prob")
    .reset_index(drop=True)
)
misses.to_csv(out_dir / "val_misses.csv", index=False)
print(f"Wrote {out_dir / 'val_misses.csv'}  ({len(misses)} rows) — "
      f"val destroyed-but-called-survived")
