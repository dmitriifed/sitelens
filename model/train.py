"""
train.py — CNN damage classifier training (PyTorch).

Part of SiteLens AI. Layer-1 model training. Week 11 deliverable.

Transfer-learning binary classifier (survived=0 / destroyed=1) on the
per-building crops in data/noto_crops/. Frozen MobileNetV2 backbone +
retrained single-logit head. Class imbalance handled with
BCEWithLogitsLoss pos_weight computed from the TRAINING split (so it can
never drift from the data). Best checkpoint is saved by validation
macro-F1. The held-out test split is written to a file and never seen
during training; evaluate.py reads the same split back.

Honesty discipline: the F1 this produces is image-only MODEL F1. It is
reported separately from the Vescovo et al. 2025 ground-survey F1 = 0.94
(human-on-human, n = 140,208). evaluate.py prints both, never conflated.

Run from repo root:  python model/train.py

(scikit-learn arrives via sentence-transformers; if `import sklearn`
fails, `pip install scikit-learn`.)
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

# ---------------------------------------------------------------------------
# CONFIG  —  verify the two CROP-PATH lines (1) and (2) against your files
# ---------------------------------------------------------------------------
REPO_ROOT  = Path(__file__).resolve().parents[1]
DATA_DIR   = REPO_ROOT / "data" / "noto_crops"
LABELS_CSV = DATA_DIR / "labels.csv"
CROPS_DIR  = DATA_DIR / "all"                   # <-- (1) folder holding the PNGs

def crop_path(s_fid) -> Path:                   # <-- (2) filename pattern
    return CROPS_DIR / f"bldg_{int(s_fid):06d}.png"

WEIGHTS_OUT = REPO_ROOT / "model" / "weights" / "mobilenetv2_noto.pt"
SPLIT_OUT   = REPO_ROOT / "model" / "weights" / "test_split.csv"   # locked test set

IMG_SIZE    = 224
BATCH_SIZE  = 32
EPOCHS      = 30
PATIENCE    = 6
LR          = 1e-3
SEED        = 42
VAL_FRAC    = 0.15
TEST_FRAC   = 0.15
NUM_WORKERS = 0          # 0 is safest on Windows; bump on Linux/Colab

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_labeled_frame() -> pd.DataFrame:
    """Read labels.csv, resolve a binary label, drop rows whose crop is missing."""
    df = pd.read_csv(LABELS_CSV)
    if "s_fid" not in df.columns:
        df = df.reset_index().rename(columns={df.columns[0]: "s_fid"})

    if "label" in df.columns:                       # prefer an explicit string label
        y = (df["label"].astype(str).str.lower() == "destroyed").astype(int)
    elif "damage_val" in df.columns:                # else derive: 0 = survived, >0 = destroyed
        y = (df["damage_val"].astype(int) > 0).astype(int)
    else:
        raise ValueError("labels.csv has neither a 'label' nor a 'damage_val' column.")

    df = df.assign(y=y)
    if "filepath" in df.columns:
        df["path"] = df["filepath"].map(Path)
    else:
        df["path"] = df["s_fid"].map(crop_path)
    exists = df["path"].map(lambda p: p.exists())
    if exists.sum() == 0:
        raise FileNotFoundError(
            f"No crops found. Check CONFIG lines (1) CROPS_DIR and (2) crop_path()."
        )
    if (~exists).any():
        print(f"[warn] {(~exists).sum()} crops in labels.csv are missing on disk; dropping them.")
    df = df[exists].reset_index(drop=True)
    df = df.drop_duplicates(subset="s_fid").reset_index(drop=True)
    return df


class CropDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, train: bool):
        self.frame = frame.reset_index(drop=True)
        common = [transforms.Resize((IMG_SIZE, IMG_SIZE))]
        aug = ([transforms.RandomHorizontalFlip(),
                transforms.RandomVerticalFlip(),        # aerial roofs: vertical flip is valid
                transforms.RandomRotation(20),
                transforms.ColorJitter(0.1, 0.1, 0.1)] if train else [])
        tail = [transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
        self.tf = transforms.Compose(common + aug + tail)

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, i):
        row = self.frame.iloc[i]
        img = Image.open(row["path"]).convert("RGB")
        return self.tf(img), torch.tensor([row["y"]], dtype=torch.float32)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def build_model() -> nn.Module:
    model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
    for p in model.features.parameters():
        p.requires_grad = False                          # freeze backbone
    in_feats = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_feats, 1)         # single-logit head
    return model.to(DEVICE)


@torch.no_grad()
def predict_probs(model, loader):
    model.eval()
    ys, ps = [], []
    for x, y in loader:
        prob = torch.sigmoid(model(x.to(DEVICE)).squeeze(1)).cpu().numpy()
        ps.append(prob)
        ys.append(y.squeeze(1).numpy())
    return np.concatenate(ys), np.concatenate(ps)


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    df = load_labeled_frame()

    train_val, test = train_test_split(
        df, test_size=TEST_FRAC, stratify=df["y"], random_state=SEED)
    val_rel = VAL_FRAC / (1 - TEST_FRAC)
    train, val = train_test_split(
        train_val, test_size=val_rel, stratify=train_val["y"], random_state=SEED)

    SPLIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    test[["s_fid", "y"]].to_csv(SPLIT_OUT, index=False)        # lock the test set
    print(f"Split: train={len(train)}  val={len(val)}  test={len(test)}  "
          f"(test locked -> {SPLIT_OUT.name})")

    n_pos = int((train["y"] == 1).sum())
    n_neg = int((train["y"] == 0).sum())
    pos_weight = torch.tensor([n_neg / max(n_pos, 1)], device=DEVICE)
    print(f"Train balance: survived={n_neg}  destroyed={n_pos}  "
          f"-> pos_weight={pos_weight.item():.2f}")

    train_loader = DataLoader(CropDataset(train, True),  batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=NUM_WORKERS)
    val_loader   = DataLoader(CropDataset(val, False),   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=NUM_WORKERS)

    model = build_model()
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(
        (p for p in model.parameters() if p.requires_grad), lr=LR)

    best_f1, best_epoch, wait = -1.0, -1, 0
    WEIGHTS_OUT.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        running = 0.0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running += loss.item() * x.size(0)
        running /= len(train_loader.dataset)

        y_true, y_prob = predict_probs(model, val_loader)
        y_pred = (y_prob >= 0.5).astype(int)
        macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
        dest  = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
        print(f"epoch {epoch:02d}  train_loss={running:.4f}  "
              f"val_macroF1={macro:.3f}  val_destroyedF1={dest:.3f}")

        if macro > best_f1:
            best_f1, best_epoch, wait = macro, epoch, 0
            torch.save(model.state_dict(), WEIGHTS_OUT)      # best-only checkpoint
        else:
            wait += 1
            if wait >= PATIENCE:
                print(f"Early stop at epoch {epoch} "
                      f"(best val_macroF1={best_f1:.3f} @ epoch {best_epoch}).")
                break

    print(f"\nBest val macro-F1 = {best_f1:.3f} (epoch {best_epoch}).")
    print(f"Best weights -> {WEIGHTS_OUT}")
    print("Now run:  python model/evaluate.py")


if __name__ == "__main__":
    main()
