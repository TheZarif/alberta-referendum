#### Preamble ####
# Purpose: Shared loading and spatial statistics for the question 10 spatial
#   analysis, used by scripts/06-spatial_analysis.py and
#   notebooks/06-spatial_analysis.ipynb.
# Author: Joseph and TheZarif
# Date: 6 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - numpy, pandas and geopandas must be installed
#   - scripts/03-clean_data.py must have been run

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from common import ANALYSIS, EXPECTED_2026, RAW

# NAD83 / Alberta 10-TM (Forest): metres, used for areas, centroids and distances.
METRIC_CRS = 3400

REGION_ORDER = ["Edmonton", "Calgary", "Central", "North", "South"]
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
    "Not significant": "#eeeeee",
}


def load_q10() -> gpd.GeoDataFrame:
    """Question 10 results joined to 2017 division boundaries and regions.

    Adds option2_pct (Option 2 share of valid votes), area_km2, projected
    centroids (x, y in metres) and lon/lat centroids for labels. Checks the
    totals against the 29 October 2026 news release.
    """
    results = pd.read_csv(ANALYSIS / "ed_results_2026.csv", dtype={"ed_code": str})
    q10 = results[results["question_number"] == 10].copy()
    q10["total"] = q10["choice_1_votes"] + q10["choice_2_votes"]
    q10["option2_pct"] = 100 * q10["choice_2_votes"] / q10["total"]

    regions = pd.read_csv(RAW / "ed_regions.csv", dtype={"ed_code": str})
    shapes = gpd.read_file(RAW / "ab_electoral_divisions_2017.geojson")
    # Simplification on download leaves a few self-intersections; repair them.
    shapes["geometry"] = shapes.geometry.buffer(0)
    # One division is Calgary-McCall in the boundary file and
    # Calgary-Bhullar-McCall in the results, so join on number, not name.
    shapes["ed_code"] = shapes["EDNUMBER"].astype(int).map("{:02d}".format)

    gdf = shapes[["ed_code", "geometry"]].merge(q10, on="ed_code", how="right")
    gdf = gdf.merge(regions[["ed_code", "region"]], on="ed_code", how="left")
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=shapes.crs)

    assert len(gdf) == 87, "expected 87 divisions"
    assert gdf.geometry.notna().all(), "a division has no boundary"
    assert gdf["region"].notna().all(), "a division has no region"
    assert gdf["choice_1_votes"].sum() == EXPECTED_2026[10]["choice_1"]
    assert gdf["choice_2_votes"].sum() == EXPECTED_2026[10]["choice_2"]

    metric = gdf.geometry.to_crs(METRIC_CRS)
    gdf["area_km2"] = metric.area / 1e6
    gdf["x"], gdf["y"] = metric.centroid.x, metric.centroid.y
    lonlat = metric.centroid.to_crs(4326)
    gdf["lon"], gdf["lat"] = lonlat.x, lonlat.y
    return gdf.sort_values("ed_code").reset_index(drop=True)


#### Spatial weights (row-standardised) ####
def knn_weights(xy: np.ndarray, k: int) -> np.ndarray:
    """Each division's k nearest divisions by centroid distance."""
    d = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    w = np.zeros_like(d)
    for i, cols in enumerate(np.argsort(d, axis=1)[:, :k]):
        w[i, cols] = 1.0
    return w / w.sum(axis=1, keepdims=True)


def queen_weights(gdf: gpd.GeoDataFrame, tol_m: float = 500) -> np.ndarray:
    """Divisions that share a border or corner. The tolerance (metres)
    closes small gaps left by simplifying the boundary file."""
    geoms = gdf.geometry.to_crs(METRIC_CRS).reset_index(drop=True)
    buffered = geoms.buffer(tol_m)
    w = np.zeros((len(geoms), len(geoms)))
    for i, poly in enumerate(buffered):
        for j in geoms.sindex.query(poly, predicate="intersects"):
            if i != j:
                w[i, j] = 1.0
    assert (w.sum(axis=1) > 0).all(), "a division has no neighbours"
    return w / w.sum(axis=1, keepdims=True)


#### Moran's I ####
def morans_i(values: np.ndarray, w: np.ndarray) -> float:
    dev = values - values.mean()
    return float((len(values) / w.sum()) * (dev @ w @ dev) / (dev @ dev))


def moran_test(values: np.ndarray, w: np.ndarray, n_perm: int = 9999, seed: int = 42):
    """Global Moran's I with a one-sided permutation p-value (clustering)."""
    rng = np.random.default_rng(seed)
    observed = morans_i(values, w)
    perms = np.array([morans_i(rng.permutation(values), w) for _ in range(n_perm)])
    p = (1 + np.sum(perms >= observed)) / (n_perm + 1)
    return observed, float(p), perms


def local_moran(values: np.ndarray, w: np.ndarray, n_perm: int = 9999, seed: int = 42):
    """Local Moran's I with conditional-permutation pseudo p-values.

    For each division, its own value is held fixed and its neighbours are
    replaced by random draws from the other divisions. The p-value is the
    share of draws at least as extreme as observed, in the observed
    direction (as in PySAL's esda.Moran_Local).
    """
    rng = np.random.default_rng(seed)
    n = len(values)
    z = (values - values.mean()) / values.std()
    lag = w @ z
    local_i = z * lag
    p = np.empty(n)
    for i in range(n):
        nbr = np.flatnonzero(w[i])
        others = np.delete(np.arange(n), i)
        draws = np.array([rng.choice(others, size=len(nbr), replace=False) for _ in range(n_perm)])
        sim = z[i] * (z[draws] @ w[i, nbr])
        if local_i[i] >= 0:
            larger = np.sum(sim >= local_i[i])
        else:
            larger = np.sum(sim <= local_i[i])
        p[i] = (larger + 1) / (n_perm + 1)
    quadrant = np.select(
        [(z > 0) & (lag > 0), (z < 0) & (lag < 0), (z > 0) & (lag < 0)],
        ["High-High", "Low-Low", "High-Low"],
        default="Low-High",
    )
    return pd.DataFrame({"z": z, "lag": lag, "local_i": local_i, "p": p, "quadrant": quadrant})
