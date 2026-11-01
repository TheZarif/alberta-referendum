#### Preamble ####
# Purpose: Simulates division-level results for the 10 questions on the
#   19 October 2026 Alberta referendum, so the pipeline can be tested
#   before the official workbooks are downloaded.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - numpy and pandas must be installed
# Any other information needed? Run from any directory. These votes are
#   simulated. They are not the official results.


#### Workspace setup ####
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from common import DIVISIONS, QUESTIONS_2026, SIMULATED


#### Simulate data ####
# Province-wide chance that a ballot is choice 1. Choice 1 is "yes" on
# questions 1 to 9 and "remain" on question 10. The draw is binomial within
# each division. Seed 853 matches the starter folder.
rng = np.random.default_rng(853)
choice_1_probability = {
    1: 0.55,
    2: 0.52,
    3: 0.53,
    4: 0.52,
    5: 0.58,
    6: 0.45,
    7: 0.47,
    8: 0.42,
    9: 0.44,
    10: 0.75,
}
electors = rng.integers(20_000, 55_000, size=len(DIVISIONS))

rows = []
for question_number, meta in QUESTIONS_2026.items():
    choice_1 = rng.binomial(electors, choice_1_probability[question_number])
    for (ed_code, ed_name), electorate, votes_1 in zip(DIVISIONS, electors, choice_1):
        rows.append(
            {
                "ed_code": ed_code,
                "ed_name": ed_name,
                "question_number": question_number,
                "short_name": meta["short_name"],
                "electors": int(electorate),
                "choice_1_votes": int(votes_1),
                "choice_2_votes": int(electorate - votes_1),
            }
        )

simulated = pd.DataFrame(rows)


#### Save data ####
SIMULATED.mkdir(parents=True, exist_ok=True)
out = SIMULATED / "simulated_data.csv"
simulated.to_csv(out, index=False)
print(f"Wrote {len(simulated):,} rows to {out}")
