#### Preamble ####
# Purpose: Tests the structure of the simulated Alberta referendum file.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas must be installed
#   - scripts/00-simulate_data.py must have been run


#### Workspace setup ####
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from common import DIVISIONS, QUESTIONS_2026, SIMULATED


def check(condition: bool, passed: str, failed: str) -> None:
    if condition:
        print(f"Test Passed: {passed}")
    else:
        raise SystemExit(f"Test Failed: {failed}")


simulated = pd.read_csv(SIMULATED / "simulated_data.csv", dtype={"ed_code": str})


#### Test data ####
check(
    simulated.shape[0] == 87 * 10,
    "The dataset has 870 rows, one for each division and question.",
    f"The dataset has {len(simulated)} rows, not 870.",
)
check(
    list(simulated.columns)
    == [
        "ed_code",
        "ed_name",
        "question_number",
        "short_name",
        "electors",
        "choice_1_votes",
        "choice_2_votes",
    ],
    "The dataset has the expected columns.",
    "The dataset columns do not match the simulated schema.",
)
check(
    not simulated.isna().any().any(),
    "The dataset contains no missing values.",
    "The dataset contains missing values.",
)
check(
    set(simulated["ed_code"]) == {code for code, _ in DIVISIONS},
    "Every electoral division code is present.",
    "The electoral division codes do not match the simulated list.",
)
check(
    set(simulated["question_number"]) == set(QUESTIONS_2026),
    "All 10 questions are present.",
    "The question numbers are not 1 through 10.",
)
check(
    (simulated["choice_1_votes"] >= 0).all() and (simulated["choice_2_votes"] >= 0).all(),
    "Vote counts are non-negative.",
    "A vote count is negative.",
)
check(
    (
        simulated["choice_1_votes"] + simulated["choice_2_votes"] == simulated["electors"]
    ).all(),
    "Choice 1 and choice 2 sum to the simulated electorate.",
    "Choice 1 and choice 2 do not sum to the simulated electorate.",
)
