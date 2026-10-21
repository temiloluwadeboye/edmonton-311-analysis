"""Run a .sql file against the DuckDB database and print the result as a table.

Run from the project root:
    python -m src.run_sql sql/01_top_categories.sql

Add --save to also write the result to results/<file name>.csv
"""

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from src.load import DB_PATH

RESULTS_DIR = Path("results")


def run(sql_path):
    """Run the SQL in `sql_path` and return the result as a DataFrame."""
    query = Path(sql_path).read_text(encoding="utf-8")
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(query).df()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", help="path to a .sql file, e.g. sql/01_top_categories.sql")
    parser.add_argument("--save", action="store_true", help="also save the result as a CSV in results/")
    args = parser.parse_args()

    result = run(args.sql_file)
    with pd.option_context("display.max_rows", 100, "display.width", 200):
        print(result.to_string(index=False))
    print(f"\n({len(result):,} rows)")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        out = RESULTS_DIR / f"{Path(args.sql_file).stem}.csv"
        result.to_csv(out, index=False)
        print(f"Saved {out}")


if __name__ == "__main__":
    main()
