import pandas as pd, numpy as np
from math import sqrt

pred = pd.read_csv("data/noto_crops/predictions.csv")
test = pd.read_csv("model/weights/test_split.csv")
lab  = pd.read_csv("data/noto_crops/labels.csv").drop_duplicates(subset="s_fid")

t = pred.merge(test[["s_fid"]], on="s_fid").merge(lab, on="s_fid", how="left")
t["yhat"] = (t.pred_prob >= 0.5).astype(int)
t["correct"] = (t.yhat == t.true_label)
t["win_px"] = t[["window_width", "window_height"]].max(axis=1)

d = t[t.true_label == 1]          # destroyed only
fn = d[d.yhat == 0]

print("=== 1. WHERE THE 20 MISSES SIT IN PROBABILITY SPACE ===")
print("missed destroyed (n=%d) pred_prob:" % len(fn))
print(fn.pred_prob.describe(percentiles=[.25,.5,.75]).round(4).to_string())
print("\ncaught destroyed (n=%d) pred_prob:" % (len(d)-len(fn)))
print(d[d.yhat==1].pred_prob.describe(percentiles=[.25,.5,.75]).round(4).to_string())
print("\nmiss probabilities sorted:", sorted(fn.pred_prob.round(3).tolist()))

def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'), float('nan'))
    ph = k/n
    den = 1 + z*z/n
    c = (ph + z*z/(2*n))/den
    h = z*sqrt(ph*(1-ph)/n + z*z/(4*n*n))/den
    return (max(0, c-h), min(1, c+h))

def slice_report(df, col, title, bins=None, labels=None):
    x = df.copy()
    if bins is not None:
        x["_g"] = pd.cut(x[col], bins=bins, labels=labels, include_lowest=True)
    else:
        x["_g"] = x[col]
    print(f"\n=== {title} — destroyed-class recall by group (test, n={len(df)}) ===")
    out = []
    for g, sub in x.groupby("_g", observed=True):
        dd = sub[sub.true_label == 1]
        if len(dd) == 0:
            out.append([str(g), len(sub), 0, None, None, None]); continue
        hit = int((dd.yhat == 1).sum())
        lo, hi = wilson(hit, len(dd))
        out.append([str(g), len(sub), len(dd), round(hit/len(dd), 3),
                    f"[{lo:.2f},{hi:.2f}]", len(dd)-hit])
    print(pd.DataFrame(out, columns=["group","n_all","n_destroyed","recall","95% CI","missed"]).to_string(index=False))

q = t.win_px.quantile([0, .25, .5, .75, 1.0]).values
slice_report(t, "win_px", "A. PIXELS ON BUILDING (native window, max dim)",
             bins=q, labels=[f"Q1 <={q[1]:.0f}px", f"Q2 <={q[2]:.0f}px",
                             f"Q3 <={q[3]:.0f}px", f"Q4 <={q[4]:.0f}px"])

t["hazard"] = np.select(
    [ (t.gsi_fire==1) & (t.gsi_slope_failure==1), t.gsi_fire==1,
      t.gsi_slope_failure==1, t.gsi_tsunami==1 ],
    ["fire+slope","fire","slope","tsunami"], default="none/seismic")
slice_report(t, "hazard", "B. HAZARD CLASS")

slice_report(t, "municipality", "C. MUNICIPALITY")

if t.conf.notna().any():
    slice_report(t, "conf", "D. VESCOVO LABEL CONFIDENCE")

print("\n=== E. FALSE POSITIVES (survived predicted destroyed) ===")
fp = t[(t.true_label==0) & (t.yhat==1)]
print(fp[["s_fid","pred_prob","win_px","municipality","hazard","conf"]].to_string(index=False))

print("\n=== F. THE 20 MISSES, LISTED ===")
print(fn[["s_fid","pred_prob","win_px","municipality","hazard","conf"]]
      .sort_values("pred_prob").to_string(index=False))

print("\n=== G. win_px distribution overall vs misses ===")
print("all test :", t.win_px.describe(percentiles=[.1,.25,.5,.75,.9]).round(1).to_string())
print("\nmisses   :", fn.win_px.describe(percentiles=[.1,.25,.5,.75,.9]).round(1).to_string())
