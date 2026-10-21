"""Transform: clean the raw 311 pages into one analysis-ready table.

Run from the project root (after src.extract):
    python -m src.transform

Input:  data/raw/page_*.json
Output: data/processed/requests.parquet
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/processed/requests.parquet")

# A generous box around Edmonton. Coordinates outside it are data errors
# (e.g. two 2018 tickets with longitude 30741.0) and would break a map.
LAT_RANGE = (53.0, 54.0)
LON_RANGE = (-114.0, -113.0)

# API column name -> clear name
RENAME = {
    "ticket_id": "ticket_id",
    "ticket_created_date_time": "created_date",
    "ticket_closed_date_time": "closed_date",
    "ticket_status": "status",
    "status_detail": "status_detail",
    "issue_type": "category",
    "issue_description": "description",
    "agency_responsible": "department",
    "display_name": "neighbourhood",
    "neighborhood_district": "ward",
    "lat": "latitude",
    "long": "longitude",
    "ticket_source": "source",
}

# Categories that were renamed over the years -> one standard name.
# Found by checking which years each category name was used. Only clear renames are
# merged: categories the City SPLIT into several new ones around 2020-2021 (e.g.
# "Tree Maintenance" -> Trees / Pruning / Broken Branch) are left alone, because
# merging them would mean guessing which new category each old request belongs to.
CATEGORY_MAP = {
    "Pothole": "Potholes",
    "Snow & Ice Maintenance": "Maintenance - Snow & Ice",
    "Parking Enforcement": "Public Parking Complaints",
    "Litter & Waste": "Litter",
    "Vandalism/Graffiti": "Graffiti",
}

# Edmonton seasons by month number
SEASONS = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}


def load_raw():
    """Read every data/raw/page_*.json file and stack them into one DataFrame.
    Hint: sorted(RAW_DIR.glob("page_*.json")), pd.read_json(path, dtype=False) for each,
    then pd.concat([...], ignore_index=True). dtype=False keeps everything as text
    for now (the next function converts types on purpose)."""
    paths = sorted(RAW_DIR.glob("page_*.json"))
    pages = []
    for path in paths:
        pages.append(pd.read_json(path, dtype=False))
    return pd.concat(pages, ignore_index=True)


def rename_columns(df):
    """Rename the columns using RENAME. Hint: df.rename(columns=...)."""
    return df.rename(columns=RENAME, errors="raise")


def convert_types(df):
    """Dates -> datetime, latitude/longitude -> numbers.
    Hint: pd.to_datetime(df["created_date"]) and pd.to_numeric(..., errors="coerce")
    (errors="coerce" turns anything unreadable into NaN instead of crashing)."""
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Flag coordinates that are missing or outside Edmonton, then blank them out
    # so they can't end up on a map. The rows themselves are kept.
    inside = df["latitude"].between(*LAT_RANGE) & df["longitude"].between(*LON_RANGE)
    df["bad_location"] = ~inside
    df.loc[~inside, ["latitude", "longitude"]] = np.nan
    return df


def add_days_to_close(df):
    """New column days_to_close = closed_date - created_date, in whole days.
    Open tickets have no closed_date, so they'll get NaN, which is what we want.
    Hint: (df["closed_date"] - df["created_date"]).dt.days"""
    df["days_to_close"] = (df["closed_date"] - df["created_date"]).dt.days
    return df


def standardise_categories(df):
    """Merge renamed categories using CATEGORY_MAP. Categories not in the map stay as they are.
    Hint: df["category"].replace(CATEGORY_MAP)"""
    df["category"] = df["category"].replace(CATEGORY_MAP)
    return df


def add_time_columns(df):
    """Add year, month (1-12) and season (from SEASONS) based on created_date.
    Hint: df["created_date"].dt.year, .dt.month, and .map(SEASONS) on the month."""
    df["year"] = df["created_date"].dt.year
    df["month"] = df["created_date"].dt.month
    df["season"] = df["month"].map(SEASONS)
    return df


def add_ward_system(df):
    """New column ward_system: "old" if the ward is a number like "06" (pre-2021 boundaries),
    "new" if it's a name like "Métis", and missing if there's no ward.
    Hint: df["ward"].str.fullmatch(r"\\d+") is True for numbers; np.select or np.where can build the column."""
    is_number = df["ward"].str.fullmatch(r"\d+").fillna(False)
    df["ward_system"] = np.where(is_number, "old", "new")
    df.loc[df["ward"].isna(), "ward_system"] = None
    return df


def add_quality_flags(df):
    """Flag problem rows instead of deleting them:
      - closed_without_date: status is "Closed" but closed_date is missing
      - partial_year: created in 2013 (system just starting) or in the current, unfinished year
    Both should be True/False columns."""
    df["closed_without_date"] = (df["status"] == "Closed") & df["closed_date"].isna()
    df["partial_year"] = df["year"].isin([2013, pd.Timestamp.now().year])
    return df


def main():
    # Step 1: load, then run each transform function in order
    df = load_raw()
    df = rename_columns(df)
    df = convert_types(df)
    df = add_days_to_close(df)
    df = standardise_categories(df)
    df = add_time_columns(df)
    df = add_ward_system(df)
    df = add_quality_flags(df)

    # Step 2: print a short summary so every run shows what the data looks like
    closed = df["status"] == "Closed"
    print(f"Rows:                 {len(df):,}")
    print(f"Closed / open:        {closed.sum():,} / {(~closed).sum():,}")
    print(f"Median days to close: {df['days_to_close'].median():.0f}")
    print(f"Date range:           {df['created_date'].min():%Y-%m-%d} to {df['created_date'].max():%Y-%m-%d}")
    print(f"Categories:           {df['category'].nunique()}")
    print("Ward system:          " + ", ".join(
        f"{name} {count:,}" for name, count in df["ward_system"].value_counts(dropna=False).items()))
    print("Flagged rows:")
    for flag in ["bad_location", "closed_without_date", "partial_year"]:
        print(f"  {flag:<20}{df[flag].sum():>9,}")

    # Step 3: make the output folder and save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    print(f"\nSaved {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
