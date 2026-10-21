"""Load: put the clean table into a DuckDB database file, ready for SQL.

Run from the project root (after src.transform):
    python -m src.load

Input:  data/processed/requests.parquet
Output: data/edmonton_311.duckdb  (table: requests)
"""

from pathlib import Path

import duckdb

PARQUET_PATH = Path("data/processed/requests.parquet")
DB_PATH = Path("data/edmonton_311.duckdb")


def main():
    # One connection = one open database file (created if it doesn't exist yet)
    with duckdb.connect(str(DB_PATH)) as con:
        # Rebuild the table from scratch each run, so re-running never duplicates rows
        con.execute("DROP TABLE IF EXISTS requests")
        con.execute(f"CREATE TABLE requests AS SELECT * FROM read_parquet('{PARQUET_PATH.as_posix()}')")

        rows = con.execute("SELECT count(*) FROM requests").fetchone()[0]
        columns = con.execute("SELECT count(*) FROM information_schema.columns WHERE table_name = 'requests'").fetchone()[0]

    print(f"Loaded {rows:,} rows and {columns} columns into {DB_PATH} (table: requests)")


if __name__ == "__main__":
    main()
