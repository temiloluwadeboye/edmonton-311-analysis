"""Extract: download City of Edmonton 311 requests from the open data API, page by page.

Run from the project root:
    python -m src.extract

Output: data/raw/page_000.json, page_001.json, ... (one file per page of 50,000 rows)
"""

import json
import time
from pathlib import Path

import requests

API_URL = "https://data.edmonton.ca/resource/ukww-xkmj.json"
RAW_DIR = Path("data/raw")
PAGE_SIZE = 50_000

# Only the columns we need (the API names, which we'll rename in the Transform step)
COLUMNS = [
    "ticket_id",
    "ticket_created_date_time",
    "ticket_closed_date_time",
    "ticket_status",
    "status_detail",
    "issue_type",
    "issue_description",
    "agency_responsible",
    "display_name",           # = neighbourhood
    "neighborhood_district",  # = ward
    "lat",
    "long",
    "ticket_source",
]


def fetch_page(offset, retries=3):
    """Request one page of up to PAGE_SIZE rows starting at `offset`; return a list of dicts.

    If the server is slow or briefly unavailable, wait and try again (up to `retries` times).
    """
    params = {
        "$select": ",".join(COLUMNS),
        "$limit": PAGE_SIZE,
        "$offset": offset,   # how many rows to skip before this page starts
        "$order": ":id",     # same order every time, so pages never overlap or leave gaps
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=120)
            response.raise_for_status()   # turn an HTTP error (e.g. 500) into a Python error
            return response.json()
        except requests.RequestException as error:
            if attempt == retries:
                raise
            wait = 5 * attempt
            print(f"  request failed ({error}); retrying in {wait}s...")
            time.sleep(wait)


def save_page(rows, page_number):
    """Write one page to data/raw/page_000.json (3-digit page number). Return the path."""
    path = RAW_DIR / f"page_{page_number:03d}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f)
    return path


def main():
    # Step 1: make sure RAW_DIR exists, and clear out pages from any earlier run
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for old_page in RAW_DIR.glob("page_*.json"):
        old_page.unlink()

    # Step 2: keep asking for the next page until one comes back empty
    offset, page_number, total = 0, 0, 0
    while True:
        rows = fetch_page(offset)
        if not rows:
            break
        path = save_page(rows, page_number)
        total += len(rows)
        print(f"page {page_number:>3}: {len(rows):>6,} rows   ({total:>9,} total)  -> {path}")

        offset += PAGE_SIZE
        page_number += 1
        time.sleep(1)   # be polite to the City's server

    # Step 3: summary
    print(f"\nDone: {total:,} rows in {page_number} pages.")


if __name__ == "__main__":
    main()
