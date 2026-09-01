import pandas as pd, numpy as np
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

pred = pd.read_csv("data/noto_crops/predictions.csv")
test = pd.read_csv("model/weights/test_split.csv")
lab  = pd.read_csv("data/noto_crops/labels.csv")

print("predictions rows:", len(pred), "| unique s_fid:", pred.s_fid.nunique())
print("test_split rows :", len(test), "| unique s_fid:", test.s_fid.nunique())
print("labels rows     :", len(lab),  "| unique s_fid:", lab.s_fid.nunique())

t = pred.merge(test[["s_fid"]], on="s_fid", how="inner")
print("\njoined test rows:", len(t))
print("label agreement :", (t.true_label.values == test.set_index('s_fid').loc[t.s_fid,'y'].values).all())

y, p = t.true_label.values, t.pred_prob.values
yhat = (p >= 0.5).astype(int)

print("\n--- REPRODUCTION at threshold 0.5, n =", len(t), "---")
print(classification_report(y, yhat, target_names=["survived","destroyed"], digits=3, zero_division=0))
print("ROC-AUC:", round(roc_auc_score(y, p), 4))
print("confusion (rows=true, cols=pred):\n", confusion_matrix(y, yhat))
print("\nclass balance in test: destroyed =", int(y.sum()), "/", len(y), "=", round(y.mean(), 4))

# published figures for comparison
print("\npublished: destroyed-F1 0.789 | macro-F1 0.870 | ROC-AUC 0.918")
