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


def fetch_page(offset):
    """Request one page of up to PAGE_SIZE rows starting at `offset`; return a list of dicts.

    Hint: requests.get(API_URL, params={...}, timeout=120) with these params:
        "$select": the column names joined by commas
        "$limit":  PAGE_SIZE
        "$offset": offset
        "$order":  ":id"      (keeps the row order stable between pages)
    Then response.raise_for_status() and return response.json().
    """
    pass


def save_page(rows, page_number):
    """Write one page to data/raw/page_000.json (3-digit page number). Return the path."""
    pass


def main():
    # Step 1: make sure RAW_DIR exists

    # Step 2: loop: fetch a page, stop if it's empty, otherwise save it,
    #         print progress, and move the offset forward by PAGE_SIZE
    #         (a short time.sleep(1) between pages is polite to the City's server)

    # Step 3: print the total number of rows downloaded
    pass


if __name__ == "__main__":
    main()
