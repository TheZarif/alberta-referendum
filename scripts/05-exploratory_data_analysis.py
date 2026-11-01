#### Preamble ####
# Purpose: Summarises the cleaned 2026 results and compares question 10
#   with the public separation polls.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas and matplotlib must be installed
#   - scripts/03-clean_data.py must have been run


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
import pandas as pd

from common import ANALYSIS, RAW, SKETCHES


def region(ed_name: str) -> str:
    name = ed_name.upper()
    if name.startswith("CALGARY"):
        return "Calgary"
    if name.startswith("EDMONTON"):
        return "Edmonton"
    return "Rest of Alberta"


#### Read data ####
divisions = pd.read_csv(ANALYSIS / "ed_results_2026.csv", dtype={"ed_code": str})
polls = pd.read_csv(RAW / "polls_separation.csv", parse_dates=["fieldwork_end"])


#### Explore ####
summary = divisions.groupby(
    ["question_number", "short_name", "choice_1_label"], as_index=False
)[["choice_1_votes", "choice_2_votes"]].sum()
valid = summary["choice_1_votes"] + summary["choice_2_votes"]
summary["choice_1_pct"] = summary["choice_1_votes"] / valid * 100
print(summary.to_string(index=False))

SKETCHES.mkdir(parents=True, exist_ok=True)

yes = summary[summary["question_number"] < 10].sort_values("question_number")
labels = yes["question_number"].astype(str) + ". " + yes["short_name"].str.replace("_", " ")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(labels, yes["choice_1_pct"], color="#2c5f2d")
ax.axvline(50, color="#888888", linewidth=1)
ax.set_xlabel("Yes, percent of valid votes")
ax.set_xlim(0, 100)
ax.invert_yaxis()
ax.set_title("Questions 1 to 9")
fig.tight_layout()
fig.savefig(SKETCHES / "yes_share_2026.png", dpi=150)
plt.close(fig)

question_10 = divisions[divisions["question_number"] == 10].copy()
question_10["region"] = question_10["ed_name"].map(region)
regional = question_10.groupby("region", as_index=False)[
    ["choice_1_votes", "choice_2_votes"]
].sum()
regional["remain_pct"] = (
    regional["choice_1_votes"]
    / (regional["choice_1_votes"] + regional["choice_2_votes"])
    * 100
)
order = ["Calgary", "Edmonton", "Rest of Alberta"]
regional = regional.set_index("region").loc[order].reset_index()
print(regional.to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(regional["region"], regional["remain_pct"], color="#1f4e79")
ax.axhline(74.95, color="#888888", linewidth=1)
ax.set_ylabel("Remain, percent of valid votes")
ax.set_ylim(0, 100)
ax.set_title("Question 10")
fig.tight_layout()
fig.savefig(SKETCHES / "q10_remain_by_region.png", dpi=150)
plt.close(fig)

decided = polls["remain_pct"] + polls["separation_pct"]
polls = polls.sort_values("fieldwork_end")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(
    polls["fieldwork_end"],
    polls["remain_pct"] / decided * 100,
    s=30,
    color="#1f4e79",
)
ax.axhline(74.95, color="#2c5f2d", linewidth=1)
ax.set_ylabel("Remain, percent of decided respondents")
ax.set_ylim(50, 100)
ax.set_title("Separation polls and the official result")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(SKETCHES / "polls_vs_result.png", dpi=150)
plt.close(fig)
print(f"Wrote sketches to {SKETCHES}")
