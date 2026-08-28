"""
evaluate.py — Model evaluation + demo-prediction export (PyTorch).

Part of SiteLens AI. Layer-1 evaluation. Week 11 deliverable.

Loads the best checkpoint from train.py and evaluates it on the
held-out test split recorded in model/weights/test_split.csv. Reports
confusion matrix + per-class precision/recall/F1 + macro-F1 + ROC-AUC.
Prints the image-only MODEL F1 next to the Vescovo et al. 2025
label-validation F1 = 0.94 (agreement between their multi-source visual
assessment and independent ground-survey photographs, on an
independently surveyed validation subset; dataset n = 140,208) with an
explicit note that they are different kinds of number — the build-log
§4 framing enforced in the output, not just in discipline.

Vescovo et al. 2025: Earth System Science Data 17, 5259; dataset Zenodo
DOI 10.5281/zenodo.11055711.

Also scores every crop and writes data/noto_crops/predictions.csv
(s_fid, true_label, pred_prob, pred_label) so the Streamlit demo shows
predicted-vs-actual from a pre-computed file with NO model loaded live.

Run from repo root (after train.py):  python model/evaluate.py
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import (confusion_matrix, classification_report,
                             f1_score, roc_auc_score)

from train import (load_labeled_frame, build_model, CropDataset, predict_probs,
                   WEIGHTS_OUT, SPLIT_OUT, DATA_DIR, BATCH_SIZE, NUM_WORKERS, DEVICE)

VESCOVO_F1 = 0.94                     # label-validation F1, independently surveyed subset; dataset n=140,208 — NOT the model
PRED_OUT   = DATA_DIR / "predictions.csv"


def main():
    df = load_labeled_frame()
    test_ids = pd.read_csv(SPLIT_OUT)["s_fid"].tolist()
    test = df[df["s_fid"].isin(test_ids)].reset_index(drop=True)

    model = build_model()
    model.load_state_dict(torch.load(WEIGHTS_OUT, map_location=DEVICE))

    test_loader = DataLoader(CropDataset(test, False), batch_size=BATCH_SIZE,
                             shuffle=False, num_workers=NUM_WORKERS)
    y_true, y_prob = predict_probs(model, test_loader)
    y_pred = (y_prob >= 0.5).astype(int)

    names = ["survived", "destroyed"]
    print("\nConfusion matrix (rows=true, cols=pred) [survived, destroyed]:")
    print(confusion_matrix(y_true, y_pred))
    print("\nPer-class report:")
    print(classification_report(y_true, y_pred, target_names=names,
                                digits=3, zero_division=0))

    macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    dest  = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auc = float("nan")

    print("=" * 68)
    print("HONEST F1 FRAMING — report these two numbers separately:")
    print(f"  SiteLens model (image-only, held-out test, n={len(test)}):")
    print(f"      macro F1     = {macro:.3f}")
    print(f"      destroyed F1 = {dest:.3f}")
    print(f"      ROC-AUC      = {auc:.3f}")
    print(f"  Vescovo et al. 2025 ground truth: F1 = {VESCOVO_F1:.2f} "
          "on an independently surveyed validation subset; dataset n=140,208.")
    print("  Different kinds of number. Never quote 0.94 as the model's score.")
    print("=" * 68)

    # full-dataset predictions for the demo (pre-computed; the app loads no model)
    full_loader = DataLoader(CropDataset(df, False), batch_size=BATCH_SIZE,
                             shuffle=False, num_workers=NUM_WORKERS)
    _, all_prob = predict_probs(model, full_loader)
    out = pd.DataFrame({
        "s_fid":      df["s_fid"].values,
        "true_label": df["y"].values,
        "pred_prob":  np.round(all_prob, 4),
        "pred_label": (all_prob >= 0.5).astype(int),
    })
    out.to_csv(PRED_OUT, index=False)
    print(f"\nWrote demo predictions -> {PRED_OUT}  ({len(out)} rows)")


if __name__ == "__main__":
    main()
