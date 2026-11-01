#### Preamble ####
# Purpose: Shared paths and question metadata for the Alberta referendum scripts.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites: none

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMULATED = ROOT / "data" / "00-simulated_data"
RAW = ROOT / "data" / "01-raw_data"
ANALYSIS = ROOT / "data" / "02-analysis_data"
SKETCHES = ROOT / "other" / "sketches"

OFFICIAL_BASE = "https://officialresults.elections.ab.ca"
VOTE_DATE_2026 = "2026-10-19"

# Choice sums and ballots cast (valid + declined + rejected) from the
# Elections Alberta news release of 29 October 2026.
EXPECTED_2026 = {
    1: {"choice_1": 1_127_729, "choice_2": 927_783, "ballots_cast": 2_202_613},
    2: {"choice_1": 1_078_681, "choice_2": 977_384, "ballots_cast": 2_205_405},
    3: {"choice_1": 1_096_546, "choice_2": 967_754, "ballots_cast": 2_214_060},
    4: {"choice_1": 1_067_383, "choice_2": 994_065, "ballots_cast": 2_210_909},
    5: {"choice_1": 1_200_838, "choice_2": 867_525, "ballots_cast": 2_217_074},
    6: {"choice_1": 933_310, "choice_2": 1_124_131, "ballots_cast": 2_213_649},
    7: {"choice_1": 971_837, "choice_2": 1_083_780, "ballots_cast": 2_214_706},
    8: {"choice_1": 873_059, "choice_2": 1_183_982, "ballots_cast": 2_211_700},
    9: {"choice_1": 908_729, "choice_2": 1_148_744, "ballots_cast": 2_213_520},
    10: {"choice_1": 1_556_316, "choice_2": 520_233, "ballots_cast": 2_216_505},
}

# Corrected provincial totals announced 26 October 2021.
EXPECTED_2021 = {
    "equalization": {"yes": 642_501, "no": 399_169},
    "daylight_saving": {"yes": 531_782, "no": 536_874},
}

QUESTIONS_2026 = {
    1: {
        "short_name": "immigration_control",
        "topic_group": "immigration",
        "legal_status": "not binding",
        "order_in_council": "O.C. 110/2026",
    },
    2: {
        "short_name": "program_eligibility",
        "topic_group": "immigration",
        "legal_status": "not binding",
        "order_in_council": "O.C. 110/2026",
    },
    3: {
        "short_name": "residency_wait",
        "topic_group": "immigration",
        "legal_status": "not binding",
        "order_in_council": "O.C. 110/2026",
    },
    4: {
        "short_name": "health_education_fee",
        "topic_group": "immigration",
        "legal_status": "not binding",
        "order_in_council": "O.C. 110/2026",
    },
    5: {
        "short_name": "citizenship_to_vote",
        "topic_group": "immigration",
        "legal_status": "not binding",
        "order_in_council": "O.C. 110/2026",
    },
    6: {
        "short_name": "judicial_appointments",
        "topic_group": "constitution",
        "legal_status": "constitutional",
        "order_in_council": "O.C. 109/2026",
    },
    7: {
        "short_name": "abolish_senate",
        "topic_group": "constitution",
        "legal_status": "constitutional",
        "order_in_council": "O.C. 109/2026",
    },
    8: {
        "short_name": "opt_out_with_funding",
        "topic_group": "constitution",
        "legal_status": "constitutional",
        "order_in_council": "O.C. 109/2026",
    },
    9: {
        "short_name": "provincial_paramountcy",
        "topic_group": "constitution",
        "legal_status": "constitutional",
        "order_in_council": "O.C. 109/2026",
    },
    10: {
        "short_name": "remain_or_process",
        "topic_group": "separation",
        "legal_status": "not binding",
        "order_in_council": "O.C. 160/2026",
    },
}

QUESTIONS_2021 = {
    "equalization": {
        "question_number": 1,
        "event_id": "68RQ1",
        "short_name": "equalization",
        "vote_date": "2021-10-18",
    },
    "daylight_saving": {
        "question_number": 2,
        "event_id": "68RQ2",
        "short_name": "daylight_saving",
        "vote_date": "2021-10-18",
    },
}

# Names as printed on the official 2026 division table. Used only to label
# the simulated file. The real names and codes come from the workbooks.
DIVISIONS = [
    ("01", "CALGARY-ACADIA"),
    ("02", "CALGARY-BEDDINGTON"),
    ("03", "CALGARY-BOW"),
    ("04", "CALGARY-BUFFALO"),
    ("05", "CALGARY-CROSS"),
    ("06", "CALGARY-CURRIE"),
    ("07", "CALGARY-EAST"),
    ("08", "CALGARY-EDGEMONT"),
    ("09", "CALGARY-ELBOW"),
    ("10", "CALGARY-FALCONRIDGE"),
    ("11", "CALGARY-FISH CREEK"),
    ("12", "CALGARY-FOOTHILLS"),
    ("13", "CALGARY-GLENMORE"),
    ("14", "CALGARY-HAYS"),
    ("15", "CALGARY-KLEIN"),
    ("16", "CALGARY-LOUGHEED"),
    ("17", "CALGARY-BHULLAR-MCCALL"),
    ("18", "CALGARY-MOUNTAIN VIEW"),
    ("19", "CALGARY-NORTH"),
    ("20", "CALGARY-NORTH EAST"),
    ("21", "CALGARY-NORTH WEST"),
    ("22", "CALGARY-PEIGAN"),
    ("23", "CALGARY-SHAW"),
    ("24", "CALGARY-SOUTH EAST"),
    ("25", "CALGARY-VARSITY"),
    ("26", "CALGARY-WEST"),
    ("27", "EDMONTON-BEVERLY-CLAREVIEW"),
    ("28", "EDMONTON-CASTLE DOWNS"),
    ("29", "EDMONTON-CITY CENTRE"),
    ("30", "EDMONTON-DECORE"),
    ("31", "EDMONTON-ELLERSLIE"),
    ("32", "EDMONTON-GLENORA"),
    ("33", "EDMONTON-GOLD BAR"),
    ("34", "EDMONTON-HIGHLANDS-NORWOOD"),
    ("35", "EDMONTON-MANNING"),
    ("36", "EDMONTON-MCCLUNG"),
    ("37", "EDMONTON-MEADOWS"),
    ("38", "EDMONTON-MILL WOODS"),
    ("39", "EDMONTON-NORTH WEST"),
    ("40", "EDMONTON-RIVERVIEW"),
    ("41", "EDMONTON-RUTHERFORD"),
    ("42", "EDMONTON-SOUTH"),
    ("43", "EDMONTON-SOUTH WEST"),
    ("44", "EDMONTON-STRATHCONA"),
    ("45", "EDMONTON-WEST HENDAY"),
    ("46", "EDMONTON-WHITEMUD"),
    ("47", "AIRDRIE-COCHRANE"),
    ("48", "AIRDRIE-EAST"),
    ("49", "ATHABASCA-BARRHEAD-WESTLOCK"),
    ("50", "BANFF-KANANASKIS"),
    ("51", "BONNYVILLE-COLD LAKE-ST. PAUL"),
    ("52", "BROOKS-MEDICINE HAT"),
    ("53", "CAMROSE"),
    ("54", "CARDSTON-SIKSIKA"),
    ("55", "CENTRAL PEACE-NOTLEY"),
    ("56", "CHESTERMERE-STRATHMORE"),
    ("57", "CYPRESS-MEDICINE HAT"),
    ("58", "DRAYTON VALLEY-DEVON"),
    ("59", "DRUMHELLER-STETTLER"),
    ("60", "FORT MCMURRAY-LAC LA BICHE"),
    ("61", "FORT MCMURRAY-WOOD BUFFALO"),
    ("62", "FORT SASKATCHEWAN-VEGREVILLE"),
    ("63", "GRANDE PRAIRIE"),
    ("64", "GRANDE PRAIRIE-WAPITI"),
    ("65", "HIGHWOOD"),
    ("66", "INNISFAIL-SYLVAN LAKE"),
    ("67", "LAC STE. ANNE-PARKLAND"),
    ("68", "LACOMBE-PONOKA"),
    ("69", "LEDUC-BEAUMONT"),
    ("70", "LESSER SLAVE LAKE"),
    ("71", "LETHBRIDGE-EAST"),
    ("72", "LETHBRIDGE-WEST"),
    ("73", "LIVINGSTONE-MACLEOD"),
    ("74", "MASKWACIS-WETASKIWIN"),
    ("75", "MORINVILLE-ST. ALBERT"),
    ("76", "OLDS-DIDSBURY-THREE HILLS"),
    ("77", "PEACE RIVER"),
    ("78", "RED DEER-NORTH"),
    ("79", "RED DEER-SOUTH"),
    ("80", "RIMBEY-ROCKY MOUNTAIN HOUSE-SUNDRE"),
    ("81", "SHERWOOD PARK"),
    ("82", "SPRUCE GROVE-STONY PLAIN"),
    ("83", "ST. ALBERT"),
    ("84", "STRATHCONA-SHERWOOD PARK"),
    ("85", "TABER-WARNER"),
    ("86", "VERMILION-LLOYDMINSTER-WAINWRIGHT"),
    ("87", "WEST YELLOWHEAD"),
]
