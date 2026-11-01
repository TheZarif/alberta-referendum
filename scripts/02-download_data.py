#### Preamble ####
# Purpose: Downloads the official Elections Alberta referendum workbooks.
# Author: TheZarif
# Date: 1 November 2026
# Contact: https://github.com/TheZarif
# License: MIT
# Pre-requisites:
#   - requests must be installed
# Any other information needed? Saves Excel files under data/01-raw_data.
#   Re-run with --force to download files that are already on disk.
#   Re-run with --skip-polls to keep the division workbooks only.

from __future__ import annotations

import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import OFFICIAL_BASE, QUESTIONS_2021, QUESTIONS_2026, RAW, ROOT

USER_AGENT = "ab-referendum-research/0.1 (public election-results archive)"
MANIFEST_PATH = RAW / "manifest.json"
_THREAD = threading.local()


def session() -> requests.Session:
    retry = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    http = requests.Session()
    http.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=8)
    http.mount("https://", adapter)
    return http


def ed_url(event_id: int) -> str:
    return (
        f"{OFFICIAL_BASE}/orEDResultsReferendum2026.cfm"
        f"?EventId={event_id}&MODE=exED"
    )


def poll_url(event_id: int, ed: int) -> str:
    return (
        f"{OFFICIAL_BASE}/orPollResultsReferendum2026.cfm"
        f"?EventID={event_id}&ED={ed:02d}&MODE=exED"
    )


def referendum_2021_url(question_number: int) -> str:
    return (
        f"{OFFICIAL_BASE}/orResultsReferendum2021.cfm"
        f"?MODE=exProv&EventId=68&QUESTIONNO={question_number}"
    )


def _thread_session() -> requests.Session:
    http = getattr(_THREAD, "session", None)
    if http is None:
        http = session()
        _THREAD.session = http
    return http


def _write_xlsx(url: str, dest: Path, force: bool) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        content = dest.read_bytes()
    else:
        response = _thread_session().get(url, timeout=90)
        response.raise_for_status()
        content = response.content
        if content[:2] != b"PK":
            raise RuntimeError(f"Response was not an Excel workbook: {url}")
        partial = dest.with_suffix(dest.suffix + ".part")
        partial.write_bytes(content)
        partial.replace(dest)
    return {
        "path": str(dest.relative_to(ROOT)),
        "url": url,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def planned_downloads() -> list[tuple[str, Path]]:
    """Every official workbook this project archives, as (url, destination)."""
    jobs: list[tuple[str, Path]] = []
    for number in QUESTIONS_2026:
        event_id = 202600 + number
        jobs.append((ed_url(event_id), RAW / "official" / "2026" / "ed" / f"q{number:02d}.xlsx"))
        for ed in range(1, 88):
            jobs.append(
                (
                    poll_url(event_id, ed),
                    RAW / "official" / "2026" / "polls" / f"q{number:02d}" / f"ed-{ed:02d}.xlsx",
                )
            )
    for key, meta in QUESTIONS_2021.items():
        jobs.append(
            (
                referendum_2021_url(meta["question_number"]),
                RAW / "official" / "2021" / f"{key}.xlsx",
            )
        )
    return jobs


def download(force: bool = False, skip_polls: bool = False, workers: int = 4) -> Path:
    jobs = planned_downloads()
    if skip_polls:
        jobs = [(url, path) for url, path in jobs if "/polls/" not in path.as_posix()]

    print(f"Downloading {len(jobs)} workbooks into {RAW}")
    records = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_write_xlsx, url, path, force): (url, path) for url, path in jobs}
        for future in as_completed(futures):
            url, path = futures[future]
            try:
                records.append(future.result())
            except Exception as exc:
                raise RuntimeError(f"Failed to download {url}") from exc
            done += 1
            if done % 100 == 0 or done == len(jobs):
                print(f"  {done}/{len(jobs)}")

    records.sort(key=lambda item: item["path"])
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": OFFICIAL_BASE,
        "files": records,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {MANIFEST_PATH}")
    return MANIFEST_PATH


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download official referendum workbooks")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-polls", action="store_true")
    args = parser.parse_args()
    download(force=args.force, skip_polls=args.skip_polls)
