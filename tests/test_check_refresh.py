"""Tests for the weekly-refresh safety check (src/check_refresh.py)."""

import json

import pandas as pd
import pytest

from src import check_refresh


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Point the module at a temporary app/data folder holding small summary files."""
    for name in check_refresh.SUMMARY_FILES:
        pd.DataFrame({"x": range(10)}).to_parquet(tmp_path / f"{name}.parquet")
    monkeypatch.setattr(check_refresh, "DATA_DIR", tmp_path)
    monkeypatch.setattr(check_refresh, "REFRESH_PATH", tmp_path / "last_refresh.json")
    return tmp_path


def test_count_rows_counts_each_file(data_dir):
    assert check_refresh.count_rows() == {name: 10 for name in check_refresh.SUMMARY_FILES}


def test_count_rows_missing_file_counts_as_zero(data_dir):
    (data_dir / "ward_times.parquet").unlink()
    assert check_refresh.count_rows()["ward_times"] == 0


def test_load_previous_first_run_returns_none(data_dir):
    assert check_refresh.load_previous() is None


def test_check_counts_first_run_only_flags_empty_files():
    assert check_refresh.check_counts({"a": 5, "b": 0}, None) == ["b: 0 rows"]


def test_check_counts_flags_drop_over_limit():
    problems = check_refresh.check_counts({"a": 75}, {"a": 100})
    assert problems == ["a: 75 rows, was 100 (-25%)"]


def test_check_counts_allows_small_drop_and_growth():
    assert check_refresh.check_counts({"a": 80, "b": 150}, {"a": 100, "b": 100}) == []


def test_save_then_load_round_trip(data_dir):
    record = check_refresh.save_refresh({"a": 1})
    saved = json.loads((data_dir / "last_refresh.json").read_text(encoding="utf-8"))
    assert saved == record
    assert check_refresh.load_previous() == {"a": 1}


def test_main_stops_on_bad_data(data_dir):
    check_refresh.save_refresh({name: 1000 for name in check_refresh.SUMMARY_FILES})
    with pytest.raises(SystemExit) as stopped:
        check_refresh.main()
    assert stopped.value.code == 1
