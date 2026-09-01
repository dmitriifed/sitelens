import pandas as pd, numpy as np
from sklearn.metrics import f1_score, classification_report

pred = pd.read_csv("data/noto_crops/predictions.csv")
lab  = pd.read_csv("data/noto_crops/labels.csv").drop_duplicates(subset="s_fid")
a = pred.merge(lab, on="s_fid", how="left")
a["yhat"] = (a.pred_prob >= 0.5).astype(int)
a["fire"] = (a.gsi_fire == 1).astype(int)

# metres, local tangent plane at 37.4N
LAT0 = a.centroid_lat.mean()
mx = 111320*np.cos(np.radians(LAT0)); my = 110540
a["x"] = a.centroid_lon*mx; a["y"] = a.centroid_lat*my

fire_pts = a.loc[a.fire==1, ["x","y"]].to_numpy()
nf = a[a.fire==0].copy()
d = np.sqrt(((nf[["x","y"]].to_numpy()[:,None,:] - fire_pts[None,:,:])**2).sum(-1)).min(1)
nf["dist_to_fire_m"] = d

print("=== MECHANISM: do non-fire FALSE POSITIVES cluster near the fire zone? ===")
print("(if yes -> the model reads burn-scar CONTEXT, not the building)\n")
grp = nf.assign(kind=np.where(nf.yhat==1,
        np.where(nf.true_label==1,"non-fire TP (real find)","non-fire FALSE POSITIVE"),
        np.where(nf.true_label==1,"non-fire MISS","non-fire true negative")))
print(grp.groupby("kind").dist_to_fire_m.describe(percentiles=[.25,.5,.75]).round(1).to_string())

print("\nmedian distance to nearest fire-zone building:")
for k, s in grp.groupby("kind"):
    print(f"  {k:28s} n={len(s):5d}  median {s.dist_to_fire_m.median():7.1f} m")

print("\n=== FP RATE BY DISTANCE BAND (non-fire, true survivors only) ===")
sv = grp[grp.true_label==0].copy()
sv["band"] = pd.cut(sv.dist_to_fire_m, [0,50,100,200,400,1e9],
                    labels=["<50m","50-100m","100-200m","200-400m",">400m"])
r = sv.groupby("band", observed=True).agg(n=("yhat","size"), false_pos=("yhat","sum"))
r["fp_rate"] = (r.false_pos/r.n).round(4)
print(r.to_string())

print("\n\n=== COMBINING RULE + MODEL (all 1967 rows) ===")
y = a.true_label.values
combo = ((a.fire==1) | (a.yhat==1)).astype(int).values
for name, yh in [("rule only  (fire flag)", a.fire.values),
                 ("model only (CNN @0.5) ", a.yhat.values),
                 ("rule OR model         ", combo)]:
    print(f"{name}: destroyed-F1 {f1_score(y,yh,pos_label=1,zero_division=0):.3f}"
          f"  macro {f1_score(y,yh,average='macro',zero_division=0):.3f}"
          f"  recall {(yh[y==1]==1).mean():.3f}"
          f"  precision {(y[yh==1]==1).mean():.3f}")

print("\n=== WHAT THE MODEL ADDS THAT THE RULE CANNOT ===")
add = a[(a.fire==0)&(a.true_label==1)&(a.yhat==1)]
print(f"non-fire destroyed buildings the model finds and the rule cannot: {len(add)}")
print(f"non-fire destroyed total: {int(((a.fire==0)&(a.true_label==1)).sum())}"
      f"  -> model recovers {len(add)/((a.fire==0)&(a.true_label==1)).sum():.1%} of them")
print(f"cost: {int(((a.fire==0)&(a.true_label==0)&(a.yhat==1)).sum())} false positives among non-fire survivors")
