#### Preamble ####
# Purpose: Spatial autocorrelation (Global Moran's I, LISA) and regional
#   comparison of the question 10 vote, by electoral division.
# Author: Joseph and TheZarif (adapted from a collaborator notebook)
# Date: 6 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas, numpy and matplotlib must be installed
#   - scripts/03-clean_data.py must have been run
#   - data/01-raw_data/riding_centroids.csv must exist
# Notes:
#   - Locations are approximate riding centres, not boundaries. Moran's I
#     and the neighbour weights depend on them, so treat results as
#     provisional until the Elections Alberta boundary file is used.
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

centroids = pd.read_csv(RAW / "riding_centroids.csv", dtype={"ed_code": str})
df = q10.merge(centroids[["ed_code", "region", "lat", "lon"]], on="ed_code", how="left")

assert len(df) == 87 and df["lat"].notna().all()
assert df["choice_1_votes"].sum() == EXPECTED_2026[10]["choice_1"]
assert df["choice_2_votes"].sum() == EXPECTED_2026[10]["choice_2"]

y = df["option2_pct"].to_numpy()
print(f"Option 2 share, provincial: {100 * df['choice_2_votes'].sum() / df['total'].sum():.2f}%")
print(f"Divisions above 50%: {(y > 50).sum()}")
print(df.loc[y > 50, ["ed_name", "option2_pct"]].to_string(index=False))


#### Spatial weights ####
def knn_weights(coords: np.ndarray, k: int) -> np.ndarray:
    """Row-standardised k-nearest-neighbour weights. Distance is planar in
    degrees with longitude scaled by cos(latitude)."""
    scaled = coords.copy()
    scaled[:, 0] *= np.cos(np.radians(coords[:, 1].mean()))
    d = np.linalg.norm(scaled[:, None, :] - scaled[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    w = np.zeros_like(d)
    nearest = np.argsort(d, axis=1)[:, :k]
    for i, cols in enumerate(nearest):
        w[i, cols] = 1.0
    return w / w.sum(axis=1, keepdims=True)


def morans_i(values: np.ndarray, w: np.ndarray) -> float:
    dev = values - values.mean()
    return (len(values) / w.sum()) * (dev @ w @ dev) / (dev @ dev)


coords = df[["lon", "lat"]].to_numpy()
W = knn_weights(coords, K_NEIGHBOURS)


#### Global Moran's I with a permutation p-value ####
rng = np.random.default_rng(SEED)
i_obs = morans_i(y, W)
i_perm = np.array([morans_i(rng.permutation(y), W) for _ in range(N_PERMUTATIONS)])
p_value = (1 + np.sum(i_perm >= i_obs)) / (N_PERMUTATIONS + 1)
print(f"\nGlobal Moran's I (k={K_NEIGHBOURS}): {i_obs:.4f}, "
      f"pseudo p = {p_value:.4f} ({N_PERMUTATIONS} permutations)")

# Sensitivity to k
for k in (3, 5, 7, 10):
    print(f"  k={k:>2}: I = {morans_i(y, knn_weights(coords, k)):.4f}")


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
sc = ax.scatter(df["lon"], df["lat"], c=df["option2_pct"], cmap="YlOrRd",
                s=df["electors"] / 250, edgecolor="#333333", linewidth=0.5)
fig.colorbar(sc, ax=ax, orientation="horizontal", shrink=0.7, pad=0.08,
             label="Question 10, Option 2 share (%)")
ax.set_title("Question 10 by electoral division (approximate centres)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect(1 / np.cos(np.radians(df["lat"].mean())))
fig.tight_layout()
fig.savefig(SKETCHES / "q10_map_points.png", dpi=150)
plt.close(fig)

fig, (ax_map, ax_sc) = plt.subplots(1, 2, figsize=(13, 7))
for name, colour in LISA_COLOURS.items():
    sub = df[df["lisa"] == name]
    ax_map.scatter(sub["lon"], sub["lat"], c=colour, s=60, edgecolor="#333333",
                   label=f"{name} (n={len(sub)})")
    ax_sc.scatter(sub["z"], sub["lag"], c=colour, s=45, edgecolor="#333333")
ax_map.legend(loc="lower left", fontsize=8)
ax_map.set_title("LISA quadrants")
ax_map.set_aspect(1 / np.cos(np.radians(df["lat"].mean())))
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
