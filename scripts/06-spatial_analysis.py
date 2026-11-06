#### Preamble ####
# Purpose: Spatial autocorrelation (Global Moran's I, LISA) and regional
#   comparison of the question 10 vote, by electoral division.
# Author: Joseph and TheZarif (adapted from a collaborator notebook)
# Date: 6 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas, numpy, matplotlib and geopandas must be installed
#   - scripts/03-clean_data.py must have been run
#   - data/01-raw_data/ab_electoral_divisions_2017.geojson and
#     data/01-raw_data/ed_regions.csv must exist
# Notes:
#   - Boundaries are the 2017 Government of Alberta electoral divisions
#     (simplified). Region labels in ed_regions.csv came from a collaborator
#     notebook and are not independently verified.
#   - There is no regression. The notebook this came from used randomly
#     generated covariates, which were dropped. Add real covariates before
#     fitting any spatial lag model.


#### Workspace setup ####
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[1] / ".mplconfig"),
)

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import ANALYSIS, EXPECTED_2026, RAW, SKETCHES

K_NEIGHBOURS = 5
N_PERMUTATIONS = 9999
SEED = 42

REGION_COLOURS = {
    "Edmonton": "#4575b4",
    "Calgary": "#74add1",
    "Central": "#fdae61",
    "North": "#f46d43",
    "South": "#d73027",
}
LISA_COLOURS = {
    "High-High": "#d73027",
    "Low-Low": "#4575b4",
    "High-Low": "#fdae61",
    "Low-High": "#abd9e9",
}


#### Load question 10 and riding locations ####
results = pd.read_csv(ANALYSIS / "ed_results_2026.csv", dtype={"ed_code": str})
q10 = results[results["question_number"] == 10].copy()
# Option 1 is the first choice; the province-wide check below ties it to
# the published totals.
q10["total"] = q10["choice_1_votes"] + q10["choice_2_votes"]
q10["option2_pct"] = 100 * q10["choice_2_votes"] / q10["total"]

regions = pd.read_csv(RAW / "ed_regions.csv", dtype={"ed_code": str})[["ed_code", "region"]]
shapes = gpd.read_file(RAW / "ab_electoral_divisions_2017.geojson")
shapes["ed_code"] = shapes["EDNUMBER"].astype(int).map("{:02d}".format)

gdf = (shapes[["ed_code", "geometry"]].merge(q10, on="ed_code", how="right")
       .merge(regions, on="ed_code", how="left"))
gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=shapes.crs)

assert len(gdf) == 87 and gdf.geometry.notna().all() and gdf["region"].notna().all()
assert gdf["choice_1_votes"].sum() == EXPECTED_2026[10]["choice_1"]
assert gdf["choice_2_votes"].sum() == EXPECTED_2026[10]["choice_2"]

# Centroids in NAD83 / Alberta 10-TM Forest (metres); lon/lat for plotting
metric = gdf.to_crs(3400)
gdf["x"], gdf["y"] = metric.centroid.x, metric.centroid.y
cent = metric.centroid.to_crs(4326)
gdf["lon"], gdf["lat"] = cent.x, cent.y
df = pd.DataFrame(gdf.drop(columns="geometry"))

y = df["option2_pct"].to_numpy()
print(f"Option 2 share, provincial: {100 * df['choice_2_votes'].sum() / df['total'].sum():.2f}%")
print(f"Divisions above 50%: {(y > 50).sum()}")
print(df.loc[y > 50, ["ed_name", "option2_pct"]].to_string(index=False))


#### Spatial weights ####
def knn_weights(xy: np.ndarray, k: int) -> np.ndarray:
    """Row-standardised k-nearest-neighbour weights on projected centroids."""
    d = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    w = np.zeros_like(d)
    for i, cols in enumerate(np.argsort(d, axis=1)[:, :k]):
        w[i, cols] = 1.0
    return w / w.sum(axis=1, keepdims=True)


def queen_weights(geoms: gpd.GeoSeries, tol: float = 500) -> np.ndarray:
    """Contiguity weights: divisions within tol metres count as neighbours,
    which absorbs small gaps left by boundary simplification."""
    buf = geoms.buffer(tol)
    w = np.array([[float(i != j and buf.iloc[i].intersects(geoms.iloc[j]))
                   for j in range(len(geoms))] for i in range(len(geoms))])
    assert (w.sum(axis=1) > 0).all(), "a division has no neighbours"
    return w / w.sum(axis=1, keepdims=True)


def morans_i(values: np.ndarray, w: np.ndarray) -> float:
    dev = values - values.mean()
    return (len(values) / w.sum()) * (dev @ w @ dev) / (dev @ dev)


coords = df[["x", "y"]].to_numpy()
W = knn_weights(coords, K_NEIGHBOURS)


#### Global Moran's I with a permutation p-value ####
rng = np.random.default_rng(SEED)
i_obs = morans_i(y, W)
i_perm = np.array([morans_i(rng.permutation(y), W) for _ in range(N_PERMUTATIONS)])
p_value = (1 + np.sum(i_perm >= i_obs)) / (N_PERMUTATIONS + 1)
print(f"\nGlobal Moran's I (k={K_NEIGHBOURS}): {i_obs:.4f}, "
      f"pseudo p = {p_value:.4f} ({N_PERMUTATIONS} permutations)")

# Sensitivity to the weights
for k in (3, 5, 7, 10):
    print(f"  k={k:>2} nearest: I = {morans_i(y, knn_weights(coords, k)):.4f}")
print(f"  queen contiguity: I = {morans_i(y, queen_weights(metric.geometry)):.4f}")


#### LISA quadrants (descriptive; no local significance test) ####
z = (y - y.mean()) / y.std()
lag = W @ z
df["z"], df["lag"] = z, lag
df["lisa"] = np.select(
    [(z > 0) & (lag > 0), (z < 0) & (lag < 0), (z > 0) & (lag < 0)],
    ["High-High", "Low-Low", "High-Low"],
    default="Low-High",
)
print("\nLISA quadrant counts (not significance-tested):")
print(df["lisa"].value_counts().to_string())


#### Regional summary ####
summary = (
    df.groupby("region")["option2_pct"]
    .agg(n="count", median="median", mean="mean", min="min", max="max")
    .round(2)
)
print("\nOption 2 share by region:")
print(summary.to_string())


#### Figures ####
SKETCHES.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 9))
gdf.plot(column="option2_pct", cmap="YlOrRd", edgecolor="#333333", linewidth=0.4, legend=True, ax=ax,
         legend_kwds={"label": "Question 10, Option 2 share (%)", "orientation": "horizontal",
                      "shrink": 0.7, "pad": 0.05})
ax.set_title("Question 10 by electoral division")
fig.tight_layout()
fig.savefig(SKETCHES / "q10_map.png", dpi=150)
plt.close(fig)

fig, (ax_map, ax_sc) = plt.subplots(1, 2, figsize=(13, 7))
for name, colour in LISA_COLOURS.items():
    sub = df[df["lisa"] == name]
    if len(sub):
        gdf[df["lisa"] == name].plot(color=colour, edgecolor="#333333", linewidth=0.4, ax=ax_map)
    ax_map.scatter([], [], c=colour, label=f"{name} (n={len(sub)})")
    ax_sc.scatter(sub["z"], sub["lag"], c=colour, s=45, edgecolor="#333333")
ax_map.legend(loc="lower left", fontsize=8)
ax_map.set_title("LISA quadrants")
xs = np.linspace(z.min(), z.max(), 20)
ax_sc.plot(xs, i_obs * xs, color="black", label=f"slope = I = {i_obs:.3f}")
ax_sc.axhline(0, color="grey", linestyle="--")
ax_sc.axvline(0, color="grey", linestyle="--")
ax_sc.set_xlabel("Standardised Option 2 share")
ax_sc.set_ylabel("Spatial lag")
ax_sc.set_title(f"Moran scatterplot (pseudo p = {p_value:.4f})")
ax_sc.legend()
fig.tight_layout()
fig.savefig(SKETCHES / "q10_lisa.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))
order = ["Edmonton", "Calgary", "North", "Central", "South"]
bp = ax.boxplot([df.loc[df["region"] == r, "option2_pct"] for r in order],
                tick_labels=order, patch_artist=True)
for patch, r in zip(bp["boxes"], order):
    patch.set_facecolor(REGION_COLOURS[r])
ax.axhline(50, color="red", linestyle="--", linewidth=1)
ax.set_ylabel("Question 10, Option 2 share (%)")
ax.set_title("Question 10 by region")
fig.tight_layout()
fig.savefig(SKETCHES / "q10_region_boxplot.png", dpi=150)
plt.close(fig)

print(f"\nSaved figures to {SKETCHES}")
