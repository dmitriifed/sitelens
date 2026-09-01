import pandas as pd, numpy as np
from sklearn.metrics import classification_report, f1_score, confusion_matrix

pred = pd.read_csv("data/noto_crops/predictions.csv")
test = pd.read_csv("model/weights/test_split.csv")
lab  = pd.read_csv("data/noto_crops/labels.csv").drop_duplicates(subset="s_fid")
t = pred.merge(test[["s_fid"]], on="s_fid").merge(lab, on="s_fid", how="left")
t["yhat"] = (t.pred_prob >= 0.5).astype(int)
t["fire"] = (t.gsi_fire == 1).astype(int)

a = pred.merge(lab, on="s_fid", how="left")
a["yhat"] = (a.pred_prob >= 0.5).astype(int); a["fire"] = (a.gsi_fire == 1).astype(int)

print("=== IS THE FIRE FLAG SEPARABLE FROM THE LABEL? ===")
for name, df in [("TEST (n=296)", t), ("ALL  (n=1967)", a)]:
    ct = pd.crosstab(df.fire, df.true_label, rownames=["gsi_fire"], colnames=["destroyed"])
    print(f"\n{name}\n{ct.to_string()}")

print("\n\n=== TRIVIAL BASELINE: predict destroyed iff gsi_fire == 1 ===")
for name, df in [("TEST held-out (n=296)", t), ("ALL rows (n=1967)", a)]:
    y = df.true_label.values
    print(f"\n--- {name} ---")
    print("  RULE  (destroyed = in fire zone):")
    print(classification_report(y, df.fire.values, target_names=["survived","destroyed"],
                                digits=3, zero_division=0))
    print("  MODEL (MobileNetV2 @ 0.5):")
    print(classification_report(y, df.yhat.values, target_names=["survived","destroyed"],
                                digits=3, zero_division=0))
    print(f"  destroyed-F1  rule {f1_score(y, df.fire, pos_label=1, zero_division=0):.3f}"
          f"   model {f1_score(y, df.yhat, pos_label=1, zero_division=0):.3f}")
    print(f"  macro-F1      rule {f1_score(y, df.fire, average='macro', zero_division=0):.3f}"
          f"   model {f1_score(y, df.yhat, average='macro', zero_division=0):.3f}")

print("\n\n=== HOW OFTEN DOES THE MODEL SIMPLY AGREE WITH THE FIRE FLAG? ===")
for name, df in [("TEST", t), ("ALL", a)]:
    agree = (df.yhat == df.fire).mean()
    print(f"{name}: model prediction == fire flag on {agree*100:.1f}% of rows")
    print(pd.crosstab(df.fire, df.yhat, rownames=["gsi_fire"], colnames=["model pred"]).to_string())
    print()
