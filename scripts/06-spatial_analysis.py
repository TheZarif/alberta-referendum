#### Preamble ####
# Purpose: Spatial analysis of the 2026 referendum by electoral division.
#   For question 10: Global Moran's I, region-adjusted Moran's I, local
#   Moran's I (LISA) with significance, and regional summaries. For all ten
#   questions: support, clustering and how closely the questions agree. The notebook
#   notebooks/06-spatial_analysis.ipynb (and .qmd) has the full write-up.
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
#     generated covariates, which were dropped.


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

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import SKETCHES
from spatial import (LISA_COLOURS, QUESTION_LABELS, REGION_COLOURS, REGION_ORDER, knn_weights,
                     load_q10, load_support, local_moran, moran_test, morans_i, queen_weights)

N_PERMUTATIONS = 9999
ALPHA = 0.05


#### Load ####
gdf = load_q10()
y = gdf["option2_pct"].to_numpy()
prov_share = 100 * gdf["choice_2_votes"].sum() / gdf["total"].sum()
print(f"Option 2 share, provincial: {prov_share:.2f}%")
print(f"Divisions above 50%: {(y > 50).sum()}")
print(gdf.loc[y > 50, ["ed_name", "option2_pct"]].to_string(index=False))


#### Global Moran's I (shared-border neighbours) ####
W = queen_weights(gdf)
i_obs, p_obs, _ = moran_test(y, W, N_PERMUTATIONS)
print(f"\nGlobal Moran's I (queen contiguity): {i_obs:.4f}, pseudo p = {p_obs:.4f}")

xy = gdf[["x", "y"]].to_numpy()
for k in (3, 5, 7, 10):
    print(f"  k={k:>2} nearest: I = {morans_i(y, knn_weights(xy, k)):.4f}")

# Clustering left after removing each region's mean
resid = y - gdf.groupby("region")["option2_pct"].transform("mean").to_numpy()
i_res, p_res, _ = moran_test(resid, W, N_PERMUTATIONS)
print(f"Region-adjusted Moran's I: {i_res:.4f}, pseudo p = {p_res:.4f}")


#### Local Moran's I ####
lisa = local_moran(y, W, N_PERMUTATIONS)
gdf["lisa"] = np.where(lisa["p"] < ALPHA, lisa["quadrant"], "Not significant")
print(f"\nLISA clusters (conditional permutation, p < {ALPHA}):")
print(gdf["lisa"].value_counts().to_string())


#### Regional summary ####
summary = gdf.groupby("region").agg(
    ridings=("ed_code", "size"),
    area_km2=("area_km2", "sum"),
    valid_votes=("total", "sum"),
    option2_votes=("choice_2_votes", "sum"),
    median_option2_pct=("option2_pct", "median"),
    median_turnout_pct=("turnout_pct", "median"),
).reindex(REGION_ORDER)
summary["option2_pct"] = 100 * summary["option2_votes"] / summary["valid_votes"]
print("\nBy region:")
print(summary.round(1).to_string())


#### All ten questions ####
# Support is Yes for questions 1 to 9 and Option 2 for question 10.
support, votes = load_support()
support = support.loc[gdf["ed_code"]].reset_index(drop=True)
prov = votes.groupby("question_number")[["support_votes", "total"]].sum()
regions = gdf["region"].to_numpy()
rows = []
for q in support.columns:
    yq = support[q].to_numpy()
    iq, pq, _ = moran_test(yq, W, N_PERMUTATIONS)
    rq = yq - pd.Series(yq).groupby(regions).transform("mean").to_numpy()
    irq, prq, _ = moran_test(rq, W, N_PERMUTATIONS)
    rows.append({"question": QUESTION_LABELS[q],
                 "support_pct": 100 * prov.loc[q, "support_votes"] / prov.loc[q, "total"],
                 "ridings_majority": int((yq > 50).sum()),
                 "morans_i": iq, "p": pq, "morans_i_within_regions": irq, "p_within": prq})
print("\nAll ten questions (support = Yes, or Option 2 for question 10):")
print(pd.DataFrame(rows).set_index("question").round(4).to_string())

corr = support.corr().to_numpy()
eig = np.linalg.eigvalsh(corr)
print(f"Lowest correlation between two questions across ridings: {corr[~np.eye(len(corr), dtype=bool)].min():.3f}")
print(f"Share of riding differences captured by one shared pattern: {100 * eig[-1] / eig.sum():.1f}%")


#### Figures ####
SKETCHES.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 9))
gdf.plot(column="option2_pct", cmap="YlOrRd", vmin=5, vmax=55, edgecolor="#333333", linewidth=0.4,
         legend=True, ax=ax, legend_kwds={"label": "Question 10, Option 2 share (%)",
                                          "orientation": "horizontal", "shrink": 0.7, "pad": 0.02})
ax.set_title("Question 10 by electoral division")
ax.set_axis_off()
fig.tight_layout()
fig.savefig(SKETCHES / "q10_map.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 9))
present = [n for n in LISA_COLOURS if (gdf["lisa"] == n).any()]
for name in present:
    gdf[gdf["lisa"] == name].plot(color=LISA_COLOURS[name], edgecolor="#555555", linewidth=0.4, ax=ax)
ax.legend(handles=[mpatches.Patch(color=LISA_COLOURS[n], label=f"{n} ({(gdf['lisa'] == n).sum()})")
                   for n in present], loc="lower left", frameon=False)
ax.set_title(f"Question 10 LISA clusters (p < {ALPHA})")
ax.set_axis_off()
fig.tight_layout()
fig.savefig(SKETCHES / "q10_lisa.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))
bp = ax.boxplot([gdf.loc[gdf["region"] == r, "option2_pct"] for r in REGION_ORDER],
                tick_labels=REGION_ORDER, patch_artist=True)
for patch, r in zip(bp["boxes"], REGION_ORDER):
    patch.set_facecolor(REGION_COLOURS[r])
ax.axhline(50, color="red", linestyle="--", linewidth=1)
ax.axhline(prov_share, color="black", linestyle=":", linewidth=1)
ax.set_ylabel("Question 10, Option 2 share (%)")
ax.set_title("Question 10 by region")
fig.tight_layout()
fig.savefig(SKETCHES / "q10_region_boxplot.png", dpi=150)
plt.close(fig)

print(f"\nSaved figures to {SKETCHES}")
