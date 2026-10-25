"""Tests for src/transform.py, using tiny hand-made tables where the right answer is obvious.

Run from the project root:
    python -m pytest
"""

import numpy as np
import pandas as pd
import pytest

from src.transform import (
    add_days_to_close,
    add_quality_flags,
    add_time_columns,
    add_ward_system,
    convert_types,
    rename_columns,
    standardise_categories,
)

# The raw API column names, in the order extract.py downloads them
RAW_COLUMNS = [
    "ticket_id", "ticket_created_date_time", "ticket_closed_date_time", "ticket_status",
    "status_detail", "issue_type", "issue_description", "agency_responsible",
    "display_name", "neighborhood_district", "lat", "long", "ticket_source",
]


def make_raw(**overrides):
    """One raw API row as text (like the real download), with any field overridden.

    make_raw(ticket_status="Open") gives one row that is normal except for its status.
    Combine several with pd.concat([make_raw(...), make_raw(...)], ignore_index=True).
    """
    row = {
        "ticket_id": "1",
        "ticket_created_date_time": "2023-03-01T00:00:00.000",
        "ticket_closed_date_time": "2023-03-04T00:00:00.000",
        "ticket_status": "Closed",
        "status_detail": None,
        "issue_type": "Potholes",
        "issue_description": "Pothole on road",
        "agency_responsible": "Roads",
        "display_name": "WALKER",
        "neighborhood_district": "Métis",
        "lat": "53.54",
        "long": "-113.49",
        "ticket_source": "Mobile App",
    }
    row.update(overrides)
    return pd.DataFrame([row], columns=RAW_COLUMNS)


def clean(df):
    """Run the first two steps every later test needs: rename, then convert types."""
    return convert_types(rename_columns(df))


# ---------------------------------------------------------------------------
# A complete example: copy this pattern for the tests below
# ---------------------------------------------------------------------------

def test_rename_columns_gives_clear_names():
    df = make_raw()                                  # arrange: one raw row

    result = rename_columns(df)                      # act

    assert "neighbourhood" in result.columns         # assert: new names exist...
    assert "ward" in result.columns
    assert "display_name" not in result.columns      # ...and old ones are gone
    assert result.loc[0, "neighbourhood"] == "WALKER"


def test_rename_columns_fails_loudly_if_a_column_is_missing():
    df = make_raw().drop(columns=["display_name"])   # the API "renamed" a column

    with pytest.raises(KeyError):                    # the test passes only if this raises KeyError
        rename_columns(df)


# ---------------------------------------------------------------------------
# The rest of transform.py
# ---------------------------------------------------------------------------

def test_convert_types_parses_dates_and_numbers():
    df = clean(make_raw())

    assert df.loc[0, "created_date"] == pd.Timestamp("2023-03-01")
    assert pd.api.types.is_datetime64_any_dtype(df["created_date"])
    assert pd.api.types.is_float_dtype(df["latitude"])
    assert df.loc[0, "latitude"] == pytest.approx(53.54)


def test_bad_coordinates_are_blanked_and_flagged():
    raw = pd.concat(
        [make_raw(ticket_id="good"), make_raw(ticket_id="bad", lat=None, long="30741.0")],
        ignore_index=True,
    )

    df = clean(raw)
    good, bad = df.iloc[0], df.iloc[1]

    # the broken row: both coordinates blanked, and flagged
    assert pd.isna(bad["latitude"]) and pd.isna(bad["longitude"])
    assert bad["bad_location"]
    # the normal row: untouched, not flagged
    assert good["latitude"] == pytest.approx(53.54)
    assert not good["bad_location"]
    # the row itself is kept, not deleted
    assert len(df) == 2


def test_days_to_close_and_open_tickets():
    raw = pd.concat(
        [make_raw(), make_raw(ticket_status="Open", ticket_closed_date_time=None)],
        ignore_index=True,
    )

    df = add_days_to_close(clean(raw))

    assert df.loc[0, "days_to_close"] == 3          # 2023-03-01 -> 2023-03-04
    assert pd.isna(df.loc[1, "days_to_close"])     # open: no close date, so no response time yet


def test_standardise_categories_merges_renames_only():
    raw = pd.concat(
        [make_raw(issue_type="Pothole"), make_raw(issue_type="Encampments")],
        ignore_index=True,
    )

    df = standardise_categories(clean(raw))

    assert df.loc[0, "category"] == "Potholes"      # old name merged into the current one
    assert df.loc[1, "category"] == "Encampments"   # not in CATEGORY_MAP, so unchanged


def test_add_time_columns_seasons():
    raw = pd.concat(
        [make_raw(ticket_created_date_time="2023-12-15T00:00:00.000"),
         make_raw(ticket_created_date_time="2024-03-10T00:00:00.000")],
        ignore_index=True,
    )

    df = add_time_columns(clean(raw))

    assert df.loc[0, "season"] == "Winter"
    assert df.loc[1, "season"] == "Spring"
    assert df.loc[0, "year"] == 2023 and df.loc[0, "month"] == 12


def test_ward_system_old_new_and_missing():
    raw = pd.concat(
        [make_raw(neighborhood_district="06"),
         make_raw(neighborhood_district="Métis"),
         make_raw(neighborhood_district=None)],
        ignore_index=True,
    )

    df = add_ward_system(clean(raw))

    assert df.loc[0, "ward_system"] == "old"
    assert df.loc[1, "ward_system"] == "new"
    # a truly missing value, not the text "nan" (the bug fixed during development)
    assert pd.isna(df.loc[2, "ward_system"])


def test_quality_flags():
    raw = pd.concat(
        [make_raw(),                                                               # normal closed ticket
         make_raw(ticket_closed_date_time=None),                                   # "Closed" but no close date
         make_raw(ticket_status="Open", ticket_closed_date_time=None),             # open: no date is expected
         make_raw(ticket_created_date_time="2013-06-01T00:00:00.000",
                  ticket_closed_date_time="2013-06-02T00:00:00.000")],             # 2013: partial year
        ignore_index=True,
    )

    df = add_quality_flags(add_time_columns(clean(raw)))

    assert list(df["closed_without_date"]) == [False, True, False, False]
    assert list(df["partial_year"]) == [False, False, False, True]
