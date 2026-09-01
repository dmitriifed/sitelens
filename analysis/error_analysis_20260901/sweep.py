import pandas as pd, numpy as np
from sklearn.metrics import precision_recall_curve, f1_score

pred = pd.read_csv("data/noto_crops/predictions.csv")
test = pd.read_csv("model/weights/test_split.csv")
t = pred.merge(test[["s_fid"]], on="s_fid", how="inner")
y, p = t.true_label.values, t.pred_prob.values

rows = []
for th in np.arange(0.05, 0.96, 0.01):
    yhat = (p >= th).astype(int)
    tp = int(((yhat == 1) & (y == 1)).sum())
    fp = int(((yhat == 1) & (y == 0)).sum())
    fn = int(((yhat == 0) & (y == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    macro = f1_score(y, yhat, average="macro", zero_division=0)
    rows.append(dict(th=round(th, 2), tp=tp, fp=fp, fn=fn,
                     prec=round(prec, 3), rec=round(rec, 3),
                     f1=round(f1, 3), macro=round(macro, 3)))
sw = pd.DataFrame(rows)

best_f1 = sw.loc[sw.f1.idxmax()]
best_macro = sw.loc[sw.macro.idxmax()]

print("=== DESTROYED-CLASS THRESHOLD SWEEP (held-out test, n=296, 65 destroyed) ===\n")
print("At the shipped threshold 0.50:")
print(sw[sw.th == 0.50].to_string(index=False))

print("\nBest destroyed-F1:")
print(sw.loc[[sw.f1.idxmax()]].to_string(index=False))
print("\nBest macro-F1:")
print(sw.loc[[sw.macro.idxmax()]].to_string(index=False))

print("\n--- selected operating points ---")
show = sw[sw.th.isin([0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60,0.70,0.80,0.90])]
print(show.to_string(index=False))

print("\n--- recall targets: cheapest threshold reaching each ---")
for target in [0.75, 0.80, 0.85, 0.90, 0.95]:
    ok = sw[sw.rec >= target]
    if len(ok):
        r = ok.loc[ok.th.idxmax()]   # highest threshold that still hits the target
        print(f"recall >= {target:.2f}  ->  th {r.th:.2f}  "
              f"prec {r.prec:.3f}  rec {r.rec:.3f}  F1 {r.f1:.3f}  "
              f"(TP {int(r.tp)}, FP {int(r.fp)}, FN {int(r.fn)})")
    else:
        print(f"recall >= {target:.2f}  ->  unreachable")

sw.to_csv("/home/claude/sweep_results.csv", index=False)
