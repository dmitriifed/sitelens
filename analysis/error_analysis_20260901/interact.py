import pandas as pd, numpy as np
from math import sqrt

pred = pd.read_csv("data/noto_crops/predictions.csv")
test = pd.read_csv("model/weights/test_split.csv")
lab  = pd.read_csv("data/noto_crops/labels.csv").drop_duplicates(subset="s_fid")
t = pred.merge(test[["s_fid"]], on="s_fid").merge(lab, on="s_fid", how="left")
t["yhat"] = (t.pred_prob >= 0.5).astype(int)
t["win_px"] = t[["window_width","window_height"]].max(axis=1)
t["fire"] = (t.gsi_fire == 1)

def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    ph = k/n; den = 1 + z*z/n
    c = (ph + z*z/(2*n))/den
    h = z*sqrt(ph*(1-ph)/n + z*z/(4*n*n))/den
    return (max(0,c-h), min(1,c+h))

d = t[t.true_label == 1].copy()
q = t.win_px.quantile([0,.25,.5,.75,1.0]).values
d["szq"] = pd.cut(d.win_px, bins=q, include_lowest=True,
                  labels=["Q1 <=28px","Q2 <=35px","Q3 <=44px","Q4 <=155px"])

print("=== THE CONFOUND CHECK: is size an effect, or is it hazard in disguise? ===\n")
for lbl, sub in [("FIRE-ZONE destroyed", d[d.fire]), ("NON-FIRE destroyed", d[~d.fire])]:
    print(f"--- {lbl} (n={len(sub)}) ---")
    rows=[]
    for g, s in sub.groupby("szq", observed=True):
        if len(s)==0: continue
        hit=int((s.yhat==1).sum()); lo,hi=wilson(hit,len(s))
        rows.append([str(g), len(s), hit, round(hit/len(s),3), f"[{lo:.2f},{hi:.2f}]"])
    print(pd.DataFrame(rows, columns=["size quartile","n","caught","recall","95% CI"]).to_string(index=False))
    print()

print("=== SIZE DISTRIBUTION: fire vs non-fire destroyed ===")
print(d.groupby("fire", observed=True).win_px.describe(percentiles=[.25,.5,.75]).round(1).to_string())

print("\n=== MEAN PREDICTED PROBABILITY by hazard, destroyed only ===")
print(d.groupby("fire", observed=True).pred_prob.describe(percentiles=[.25,.5,.75]).round(3).to_string())

print("\n=== SAME SPLIT ACROSS THE WHOLE 1,967 (train+val+test; NOT held out) ===")
a = pred.merge(lab, on="s_fid", how="left")
a["yhat"]=(a.pred_prob>=0.5).astype(int); a["fire"]=(a.gsi_fire==1)
ad = a[a.true_label==1]
rows=[]
for f, s in ad.groupby("fire", observed=True):
    hit=int((s.yhat==1).sum()); lo,hi=wilson(hit,len(s))
    rows.append(["fire" if f else "non-fire", len(s), hit, round(hit/len(s),3), f"[{lo:.2f},{hi:.2f}]"])
print(pd.DataFrame(rows, columns=["hazard","n_destroyed","caught","recall","95% CI"]).to_string(index=False))
print("\n(train rows included -> optimistic; pattern only, not a generalisation estimate)")

print("\n=== CLASS COMPOSITION ===")
print("test destroyed:  fire", int(d.fire.sum()), "| non-fire", int((~d.fire).sum()))
print("all  destroyed:  fire", int(ad.fire.sum()), "| non-fire", int((~ad.fire).sum()))
print("test survived :  fire", int((t[t.true_label==0].gsi_fire==1).sum()),
      "| non-fire", int((t[t.true_label==0].gsi_fire!=1).sum()))
