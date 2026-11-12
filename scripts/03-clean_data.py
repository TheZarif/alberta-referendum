#### Preamble ####
# Purpose: Cleans the official referendum workbooks, and the 2019 and 2023
#   general election workbooks, into analysis files.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - pandas and openpyxl must be installed
#   - scripts/02-download_data.py must have been run

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

warnings.filterwarnings("ignore", message="Workbook contains no default style")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (
    ANALYSIS,
    EXPECTED_2021,
    EXPECTED_2026,
    QUESTIONS_2021,
    QUESTIONS_2026,
    RAW,
    VOTE_DATE_2026,
)


def _norm(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split())


def _rows(path: Path) -> list[tuple]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        return [tuple(row) for row in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def _blank(value) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text in {"", "-", "—", "–", "n/a", "N/A", "NA"}


def _as_int(value):
    if _blank(value):
        return None
    if isinstance(value, str):
        text = value.replace(",", "").strip()
        if text.endswith("%"):
            return None
        value = float(text)
    number = float(value)
    if not number.is_integer():
        raise ValueError(f"Expected a whole number, got {value!r}")
    return int(number)


def _as_float(value):
    if _blank(value):
        return None
    if isinstance(value, str):
        text = value.replace(",", "").replace("%", "").strip()
        if _blank(text):
            return None
        return float(text)
    return float(value)


def _ed_code(value) -> str:
    text = _norm(value)
    if text.isdigit():
        return f"{int(text):02d}"
    return text


def _preamble(rows: list[tuple]) -> dict:
    question_text = ""
    choice_text = {}
    for row in rows[:12]:
        for cell in row:
            text = _norm(cell)
            if text.startswith("Question "):
                question_text = text.split(":", 1)[-1].strip()
            for label in ("Option 1", "Option 2"):
                if text.startswith(label):
                    choice_text[label] = text.split("-", 1)[-1].strip() if "-" in text else text
    return {"question_text": question_text, "choice_text": choice_text}


def _header_index(rows: list[tuple], marker: str) -> tuple[int, dict[str, int]]:
    for index, row in enumerate(rows):
        labels = {_norm(cell): position for position, cell in enumerate(row) if _norm(cell)}
        if any(label.startswith(marker) for label in labels):
            return index, labels
    raise ValueError(f"No header containing {marker!r}")


def _choice_columns(labels: dict[str, int]) -> tuple[tuple[str, int], tuple[str, int]]:
    pairs = []
    for name in ("Option 1", "Yes", "Option 2", "No"):
        if name in labels:
            pairs.append((name, labels[name]))
    if len(pairs) != 2:
        raise ValueError(f"Expected two choice columns, found {pairs}")
    return pairs[0], pairs[1]


def _is_total_label(value) -> bool:
    text = _norm(value).lower()
    return text.startswith("total") or text == "count percentage" or text.endswith("subtotal")


def parse_ed_2026(path: Path, question_number: int) -> list[dict]:
    rows = _rows(path)
    meta = QUESTIONS_2026[question_number]
    preamble = _preamble(rows)
    header_at, labels = _header_index(rows, "ELECTORAL DIVISION")
    first, second = _choice_columns(labels)
    places_col = labels["Voting Place / Voting Area"]
    electors_col = labels["Number of Electors"]
    turnout_col = labels["Voter Turnout (%)"]
    choice_text = preamble["choice_text"]

    records = []
    for row in rows[header_at + 1 :]:
        if not row or _is_total_label(row[0]) or _norm(row[0]) == "":
            continue
        records.append(
            {
                "vote_date": VOTE_DATE_2026,
                "question_number": question_number,
                "short_name": meta["short_name"],
                "topic_group": meta["topic_group"],
                "legal_status": meta["legal_status"],
                "order_in_council": meta["order_in_council"],
                "question_text": preamble["question_text"],
                "choice_1_label": first[0],
                "choice_2_label": second[0],
                "choice_1_text": choice_text.get(first[0], first[0]),
                "choice_2_text": choice_text.get(second[0], second[0]),
                "ed_code": _ed_code(row[0]),
                "ed_name": _norm(row[1]),
                "voting_place_count": _as_int(row[places_col]),
                "electors": _as_int(row[electors_col]),
                "choice_1_votes": _as_int(row[first[1]]),
                "choice_2_votes": _as_int(row[second[1]]),
                "turnout_pct": _as_float(row[turnout_col]),
            }
        )
    if len(records) != 87:
        raise ValueError(f"{path.name}: expected 87 divisions, found {len(records)}")
    return records


def parse_poll_2026(path: Path, question_number: int) -> list[dict]:
    rows = _rows(path)
    meta = QUESTIONS_2026[question_number]
    division = ""
    for row in rows[:8]:
        for cell in row:
            text = _norm(cell)
            if len(text) > 4 and text[:2].isdigit() and text[2:5] == " - ":
                division = text
    if " - " not in division:
        raise ValueError(f"{path}: could not read the division title")
    ed_code, ed_name = division.split(" - ", 1)
    ed_code = _ed_code(ed_code)
    expected_code = path.stem.split("-", 1)[1]
    if ed_code != expected_code:
        raise ValueError(f"{path.name} contains division {ed_code}, expected {expected_code}")

    header_at, labels = _header_index(rows, "Voting Place")
    first, second = _choice_columns(labels)
    records = []
    for row in rows[header_at + 1 :]:
        if not row or _is_total_label(row[0]):
            continue
        ballot_type = _norm(row[labels["Type"]]) if "Type" in labels else ""
        if ballot_type not in {"Election Day", "Advance", "Mobile", "Special Ballot"}:
            continue
        voting_area = row[0]
        if isinstance(voting_area, float) and voting_area.is_integer():
            voting_area = f"{int(voting_area):03d}"
        elif isinstance(voting_area, int):
            voting_area = f"{voting_area:03d}"
        else:
            voting_area = _norm(voting_area) or None
        records.append(
            {
                "vote_date": VOTE_DATE_2026,
                "question_number": question_number,
                "short_name": meta["short_name"],
                "ed_code": ed_code,
                "ed_name": ed_name,
                "voting_area": voting_area,
                "location": _norm(row[1]) or None,
                "ballot_type": ballot_type,
                "electors": _as_int(row[labels["Number of Electors"]]),
                "choice_1_votes": _as_int(row[first[1]]),
                "choice_2_votes": _as_int(row[second[1]]),
                "valid_ballots": _as_int(row[labels["Valid Ballots Cast"]]),
                "spoiled_ballots": _as_int(row[labels["Spoiled Ballots"]]),
                "declined_ballots": _as_int(row[labels["Declined Ballots"]]),
                "rejected_ballots": _as_int(row[labels["Rejected Ballots"]]),
                "turnout_pct": _as_float(row[labels["Voter Turnout (%)"]]),
            }
        )
    if not records:
        raise ValueError(f"{path}: no poll rows")
    return records


def parse_2021(path: Path, key: str) -> list[dict]:
    rows = _rows(path)
    meta = QUESTIONS_2021[key]
    question_text = ""
    for row in rows[:5]:
        for cell in row:
            text = _norm(cell)
            if text and not text.startswith("Referendum Election") and "Jurisdiction" not in text:
                question_text = text
                break
        if question_text:
            break
    header_at, labels = _header_index(rows, "Jurisdiction")
    records = []
    for row in rows[header_at + 1 :]:
        jurisdiction = _norm(row[0]) if row else ""
        if not jurisdiction or _is_total_label(jurisdiction):
            continue
        records.append(
            {
                "vote_date": meta["vote_date"],
                "question_key": key,
                "question_number": meta["question_number"],
                "question_text": question_text,
                "jurisdiction": jurisdiction,
                "includes_results_from": _norm(row[labels["Includes results from"]]) or None,
                "electors_who_voted": _as_int(row[labels["Number of Electors Who Voted"]]),
                "yes_votes": _as_int(row[labels["Yes"]]),
                "no_votes": _as_int(row[labels["No"]]),
                "declined_ballots": _as_int(row[labels["Rejected as Blank (Declined)"]]),
                "rejected_other": _as_int(row[labels["Rejected for Other Reasons"]]),
            }
        )
    if not records:
        raise ValueError(f"{path}: no jurisdiction rows")
    return records


# Party codes printed in the 2019 and 2023 general election workbooks.
PARTY_NAMES = {
    "AAP": "Alberta Advantage Party",
    "AIP": "Alberta Independence Party",
    "AP": "Alberta Party",
    "APA": "Advantage Party of Alberta",
    "BPA": "Buffalo Party of Alberta",
    "CP-A": "Communist Party - Alberta",
    "FCP": "Freedom Conservative Party",
    "GPA": "Green Party of Alberta",
    "IND": "Independent",
    "LIB": "Alberta Liberal Party",
    "NDP": "Alberta New Democratic Party",
    "PAPA": "Pro-Life Alberta Political Association",
    "PC": "Progressive Conservative",
    "REF": "Reform Party of Alberta",
    "SM": "Solidarity Movement of Alberta",
    "TIP": "The Independence Party of Alberta",
    "UCP": "United Conservative Party",
    "WIPA": "Wildrose Independence Party of Alberta",
    "WLC": "Wildrose Loyalty Coalition",
    "WRP": "Wildrose Party",
}


def parse_general_election(path: Path, year: int) -> list[dict]:
    """Candidate totals for one division from a general election poll workbook.

    The 2019 and 2023 workbooks lay out the same information slightly
    differently, so columns are found by their header labels and the total
    row by its 'Total (All ...' label.
    """
    rows = _rows(path)
    title = _norm(rows[0][0])  # "Official Poll Results - 01 - CALGARY-ACADIA"
    _, code, name = [part.strip() for part in title.split(" - ", 2)]
    header_row, labels = _header_index(rows, "Valid Ballots Cast")
    header = rows[header_row]
    first = labels["Names on List"] + 1
    last = labels["Valid Ballots Cast"]
    total = next(row for row in rows[header_row + 1:]
                 if any(_norm(cell).startswith("Total (All") for cell in row))
    electors = _as_int(total[labels["Names on List"]])
    valid = _as_int(total[last])
    records = []
    for position in range(first, last):
        candidate, _, party = str(header[position]).rpartition("\n")
        party = party.strip()
        if party not in PARTY_NAMES:
            raise ValueError(f"{path}: unknown party code {party!r}")
        records.append({
            "year": year,
            "ed_code": _ed_code(code),
            "ed_name": name,
            "candidate": _norm(candidate),
            "party_code": party,
            "party": PARTY_NAMES[party],
            "votes": _as_int(total[position]),
            "valid_ballots": valid,
            "electors": electors,
        })
    if sum(r["votes"] for r in records) != valid:
        raise ValueError(f"{path}: candidate votes do not sum to valid ballots")
    return records


def parse_general_elections() -> pd.DataFrame:
    records = []
    for year in (2019, 2023):
        paths = sorted((RAW / "official" / str(year) / "ge").glob("ed-*.xlsx"))
        if len(paths) != 87:
            raise FileNotFoundError(f"{year} has {len(paths)} division workbooks; expected 87")
        for path in paths:
            records.extend(parse_general_election(path, year))
    return pd.DataFrame(records)


def _check(name: str, actual: int, expected: int, problems: list[str]) -> None:
    if actual != expected:
        problems.append(f"{name}: parsed {actual:,} but the official total is {expected:,}")


def parse() -> None:
    ed_dir = RAW / "official" / "2026" / "ed"
    poll_dir = RAW / "official" / "2026" / "polls"
    if not ed_dir.exists():
        raise FileNotFoundError(
            "Missing official workbooks. Run: python scripts/02-download_data.py"
        )

    ed_records = []
    poll_records = []
    for number in QUESTIONS_2026:
        ed_records.extend(parse_ed_2026(ed_dir / f"q{number:02d}.xlsx", number))
        question_polls = sorted((poll_dir / f"q{number:02d}").glob("ed-*.xlsx"))
        if len(question_polls) != 87:
            raise FileNotFoundError(
                f"Question {number} has {len(question_polls)} poll workbooks; expected 87"
            )
        for path in question_polls:
            poll_records.extend(parse_poll_2026(path, number))

    historical = []
    for key in QUESTIONS_2021:
        historical.extend(parse_2021(RAW / "official" / "2021" / f"{key}.xlsx", key))

    ed = pd.DataFrame(ed_records)
    polls = pd.DataFrame(poll_records)
    older = pd.DataFrame(historical)
    problems: list[str] = []

    elector_totals = ed.groupby("question_number")["electors"].sum()
    if elector_totals.nunique() != 1 or int(elector_totals.iloc[0]) != 3_286_778:
        problems.append(
            "Division elector totals are not 3,286,778 on every question. "
            "That is the elector count printed on the official results table, "
            "which is not the same figure as the 3,148,205 eligible electors "
            "in the news release."
        )

    notes: list[str] = []
    for number, expected in EXPECTED_2026.items():
        subset = ed[ed["question_number"] == number]
        for label, column, expected_value in (
            ("choice 1", "choice_1_votes", expected["choice_1"]),
            ("choice 2", "choice_2_votes", expected["choice_2"]),
        ):
            actual = int(subset[column].sum())
            if actual != expected_value:
                notes.append(
                    f"2026 Q{number} {label}: workbook {actual:,}, "
                    f"news release {expected_value:,}"
                )
        polled = polls[polls["question_number"] == number]
        ballots = int(
            polled[["valid_ballots", "declined_ballots", "rejected_ballots"]].fillna(0).sum().sum()
        )
        if ballots != expected["ballots_cast"]:
            notes.append(
                f"2026 Q{number} ballots cast: workbook {ballots:,}, "
                f"news release {expected['ballots_cast']:,}"
            )

    merged = ed.merge(
        polls.groupby(["question_number", "ed_code"], as_index=False)[
            ["choice_1_votes", "choice_2_votes"]
        ].sum(),
        on=["question_number", "ed_code"],
        suffixes=("_ed", "_poll"),
    )
    mismatch = merged[
        (merged["choice_1_votes_ed"] != merged["choice_1_votes_poll"])
        | (merged["choice_2_votes_ed"] != merged["choice_2_votes_poll"])
    ]
    if not mismatch.empty:
        problems.append(f"{len(mismatch)} division totals disagree with their poll sheets")

    for key, expected in EXPECTED_2021.items():
        subset = older[older["question_key"] == key]
        _check(f"2021 {key} yes", int(subset["yes_votes"].sum()), expected["yes"], problems)
        _check(f"2021 {key} no", int(subset["no_votes"].sum()), expected["no"], problems)

    if problems:
        raise SystemExit("Official totals did not match:\n- " + "\n- ".join(problems))
    if notes:
        print("Workbook totals differ from the 29 October 2026 news release:")
        for note in notes:
            print(f"- {note}")

    questions = (
        ed[
            [
                "question_number",
                "short_name",
                "topic_group",
                "legal_status",
                "order_in_council",
                "question_text",
                "choice_1_label",
                "choice_2_label",
                "choice_1_text",
                "choice_2_text",
            ]
        ]
        .drop_duplicates()
        .sort_values("question_number")
    )

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    ed.sort_values(["question_number", "ed_code"]).to_csv(
        ANALYSIS / "ed_results_2026.csv", index=False
    )
    polls.sort_values(["question_number", "ed_code", "ballot_type", "voting_area"]).to_csv(
        ANALYSIS / "poll_results_2026.csv", index=False
    )
    questions.to_csv(ANALYSIS / "questions_2026.csv", index=False)
    older.sort_values(["question_number", "jurisdiction"]).to_csv(
        ANALYSIS / "jurisdiction_results_2021.csv", index=False
    )
    general = parse_general_elections()
    general.sort_values(["year", "ed_code", "votes"], ascending=[True, True, False]).to_csv(
        ANALYSIS / "general_elections_2019_2023.csv", index=False
    )
    print(
        "Wrote "
        f"{len(ed):,} division rows, {len(polls):,} poll rows, "
        f"{len(older):,} 2021 jurisdiction rows, "
        f"and {len(general):,} 2019 and 2023 candidate rows"
    )


if __name__ == "__main__":
    parse()
