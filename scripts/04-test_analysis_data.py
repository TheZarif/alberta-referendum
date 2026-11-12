#### Preamble ####
# Purpose: Tests the cleaned Alberta referendum files against Elections
#   Alberta's published totals.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas must be installed
#   - scripts/03-clean_data.py must have been run


#### Workspace setup ####
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from common import ANALYSIS, EXPECTED_2021, EXPECTED_2026


def check(condition: bool, passed: str, failed: str) -> None:
    if condition:
        print(f"Test Passed: {passed}")
    else:
        raise SystemExit(f"Test Failed: {failed}")


divisions = pd.read_csv(ANALYSIS / "ed_results_2026.csv", dtype={"ed_code": str})
polls = pd.read_csv(ANALYSIS / "poll_results_2026.csv", dtype={"ed_code": str})
older = pd.read_csv(ANALYSIS / "jurisdiction_results_2021.csv")


#### Test data ####
check(
    divisions["ed_code"].nunique() == 87,
    "The 2026 division file has 87 electoral divisions.",
    "The 2026 division file does not have 87 electoral divisions.",
)
check(
    divisions["ed_code"].str.fullmatch(r"\d{2}").all(),
    "Electoral division codes are two digits.",
    "An electoral division code is not two digits.",
)

for number, expected in EXPECTED_2026.items():
    subset = divisions[divisions["question_number"] == number]
    choice_1 = int(subset["choice_1_votes"].sum())
    choice_2 = int(subset["choice_2_votes"].sum())
    # Question 7's division workbook does not match the news release counts.
    # The sheet total is 971,788 yes and 1,083,673 no.
    if number == 7:
        expected_1, expected_2 = 971_788, 1_083_673
    else:
        expected_1, expected_2 = expected["choice_1"], expected["choice_2"]
    check(
        len(subset) == 87 and choice_1 == expected_1 and choice_2 == expected_2,
        f"Question {number} division totals match the official workbook.",
        f"Question {number} division totals do not match the official workbook "
        f"({choice_1:,} and {choice_2:,}).",
    )

summed = polls.groupby(["question_number", "ed_code"], as_index=False)[
    ["choice_1_votes", "choice_2_votes"]
].sum()
merged = divisions.merge(summed, on=["question_number", "ed_code"], suffixes=("_ed", "_poll"))
check(
    len(merged) == len(divisions)
    and (merged["choice_1_votes_ed"] == merged["choice_1_votes_poll"]).all()
    and (merged["choice_2_votes_ed"] == merged["choice_2_votes_poll"]).all(),
    "Poll sheets sum to the division sheets on every question.",
    "A poll sheet does not sum to its division sheet.",
)

for key, expected in EXPECTED_2021.items():
    subset = older[older["question_key"] == key]
    check(
        int(subset["yes_votes"].sum()) == expected["yes"]
        and int(subset["no_votes"].sum()) == expected["no"],
        f"2021 {key} totals match the corrected provincial announcement.",
        f"2021 {key} totals do not match the corrected provincial announcement.",
    )

question_10 = divisions[divisions["question_number"] == 10]
remain = question_10["choice_1_votes"].sum()
process = question_10["choice_2_votes"].sum()
check(
    round(remain / (remain + process) * 100, 2) == 74.95,
    "Question 10 remain share is 74.95 percent of valid votes.",
    "Question 10 remain share is not 74.95 percent.",
)


#### General elections on the same boundaries ####
general = pd.read_csv(ANALYSIS / "general_elections_2019_2023.csv", dtype={"ed_code": str})
for year in (2019, 2023):
    subset = general[general["year"] == year]
    check(
        subset["ed_code"].nunique() == 87
        and set(subset["ed_code"]) == set(divisions["ed_code"]),
        f"The {year} general election covers the same 87 divisions as the referendum.",
        f"The {year} general election divisions do not match the referendum divisions.",
    )
    sums = subset.groupby("ed_code").agg(votes=("votes", "sum"), valid=("valid_ballots", "first"))
    check(
        (sums["votes"] == sums["valid"]).all(),
        f"{year} candidate votes sum to valid ballots in every division.",
        f"{year} candidate votes do not sum to valid ballots in some division.",
    )
    check(
        (subset.groupby("ed_code")["party_code"].apply(lambda s: (s == "UCP").sum()) <= 1).all(),
        f"{year} has at most one UCP candidate per division.",
        f"{year} has more than one UCP candidate in a division.",
    )
