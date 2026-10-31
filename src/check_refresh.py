"""Safety check: make sure freshly built dashboard files look sane before they go live.

Run from the project root (after src.build_dashboard_data):
    python -m src.check_refresh

It compares the new summary files in app/data/ with the row counts saved by the last
successful refresh (app/data/last_refresh.json). If the new data looks broken, it
stops with an error, so the weekly workflow never commits bad numbers.
If everything looks fine, it writes a new last_refresh.json with today's date and
the new row counts (the dashboard reads the date to show "Data last updated").

Input:  app/data/*.parquet, app/data/last_refresh.json (missing on the very first run)
Output: app/data/last_refresh.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path("app/data")
REFRESH_PATH = DATA_DIR / "last_refresh.json"

# The summary files the dashboard needs (same names build_dashboard_data writes)
SUMMARY_FILES = ["monthly_counts", "ward_times", "neighbourhoods", "channel_times"]

# How far a file's row count may FALL compared with last time before we stop.
# 0.20 = a drop of more than 20% is treated as a broken download.
MAX_DROP = 0.20


def count_rows():
    """Return {file name: number of rows} for every file in SUMMARY_FILES.

    Hint: pd.read_parquet(DATA_DIR / f"{name}.parquet") then len(...).
    A missing file should count as 0 rows (check_counts will then stop the run).
    """
    file_counts = {}
    for filename in SUMMARY_FILES:
        path = DATA_DIR / f"{filename}.parquet"
        if not path.exists():
            file_counts[filename] = 0   # missing file: check_counts will report it
            continue
        table = pd.read_parquet(path)
        file_counts[filename] = len(table)
    return file_counts


def load_previous():
    """Return the row counts saved by the last refresh, or None on the very first run.

    Hint: if REFRESH_PATH doesn't exist, return None; otherwise json.load it and
    return its "row_counts" part.
    """
    if not REFRESH_PATH.exists():
        return None

    with open(REFRESH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["row_counts"]


def check_counts(new, previous):
    """Return a list of problems (empty list = all good).

    Problems to catch:
      - any file with 0 rows
      - any file whose count fell by more than MAX_DROP compared with `previous`
        (skip this comparison when `previous` is None: there is nothing to compare with)
    Example problem text: "ward_times: 120,000 rows, was 160,000 (-25%)"
    """
    problems = []
    for file, count in new.items():
        if count == 0:
            problems.append(f"{file}: 0 rows")
        elif previous is not None and file in previous:
            prev_count = previous[file]
            if prev_count > 0:
                drop_percentage = (prev_count - count) / prev_count
                if drop_percentage > MAX_DROP:
                    problems.append(f"{file}: {count:,} rows, was {prev_count:,} (-{drop_percentage:.0%})")
    return problems


def save_refresh(new):
    """Write REFRESH_PATH with today's date (UTC, YYYY-MM-DD) and the new row counts.

    Shape: {"refreshed_on": "2026-11-02", "row_counts": {"monthly_counts": 9876, ...}}
    """
    record = {
        "refreshed_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "row_counts": new,
    }
    REFRESH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REFRESH_PATH, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return record


def main():
    # Step 1: count rows in the new files and load last time's counts
    new = count_rows()
    previous = load_previous()

    # Step 2: check them; if there are problems, print each one and stop
    problems = check_counts(new, previous)
    if problems:
        print("Refresh stopped: the new data looks wrong, so nothing will be committed.")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)

    # Step 3: save the new refresh record and print a one-line summary
    record = save_refresh(new)
    counts = ", ".join(f"{name} {count:,}" for name, count in new.items())
    print(f"Refresh OK ({record['refreshed_on']}): {counts}")


if __name__ == "__main__":
    main()
