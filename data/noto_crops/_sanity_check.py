import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

df = pd.read_csv(Path(__file__).parent / "labels.csv")
sample = df.sample(12, random_state=42)

fig, axes = plt.subplots(3, 4, figsize=(12, 9))
for ax, (_, r) in zip(axes.flat, sample.iterrows()):
    img = Image.open(r["filepath"])
    ax.imshow(img)
    title = (
        f"{r['label']}  .  s_fid {r['s_fid']}\n"
        f"{r['centroid_lat']:.4f}, {r['centroid_lon']:.4f}  .  mmi {r['usgs_mmi']:.1f}"
    )
    ax.set_title(title, fontsize=7)
    ax.axis("off")
plt.tight_layout()
out = Path(__file__).parent / "sanity_grid.png"
plt.savefig(out, dpi=120)
print(f"Saved {out}")
