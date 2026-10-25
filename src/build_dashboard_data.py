"""Build the small summary files the dashboard reads (and a CSV for Tableau / Power BI).

Run from the project root (after src.load):
    python -m src.build_dashboard_data

The dashboard can't read the 48 MB database online, and shouldn't crunch 1.25 million rows
on every page load, so this script pre-calculates compact summaries. They contain no
street addresses or individual locations: only counts and response times grouped by
category, ward, neighbourhood and time.

Output (app/data/):
    monthly_counts.parquet     requests per category per month (all years)
    ward_times.parquet         one row per closed request since 2022: category, ward, days
    neighbourhoods.parquet     per neighbourhood since 2022: requests, median days, centre point
    channel_times.parquet      per category and reporting channel since 2022
    edmonton_311_summary.csv   a flat summary for Tableau / Power BI
"""

from pathlib import Path

import duckdb

from src.load import DB_PATH

OUT_DIR = Path("app/data")

# The same "fair comparison" rows used in questions 3-5 and the statistical test
CLEAN_CLOSED = """
    year >= 2022
    AND status = 'Closed'
    AND NOT closed_without_date
    AND (status_detail IS NULL OR status_detail NOT LIKE 'Duplicate%')
"""

CHANNEL = """
    CASE
        WHEN source IN ('Mobile App', 'Mobile App Generic') THEN 'App'
        WHEN source = 'Phone Call'                          THEN 'Phone'
        ELSE 'Online / other'
    END
"""

QUERIES = {
    # Every year, so the dashboard can show long-term and seasonal patterns
    "monthly_counts": """
        SELECT year, month, category, COUNT(*) AS requests
        FROM requests
        WHERE NOT (year = 2013)           -- the system was just starting (229 requests)
        GROUP BY year, month, category
    """,
    # Individual response times (no location) so the app can compute medians and the
    # Kruskal-Wallis test for ANY category the user picks, not just potholes
    "ward_times": f"""
        SELECT category, ward, days_to_close
        FROM requests
        WHERE {CLEAN_CLOSED} AND ward_system = 'new'
    """,
    # One point per neighbourhood (the median of its requests' coordinates), never addresses
    "neighbourhoods": f"""
        SELECT
            neighbourhood,
            COUNT(*) AS requests,
            MEDIAN(days_to_close) AS median_days,
            MEDIAN(latitude) AS latitude,
            MEDIAN(longitude) AS longitude
        FROM requests
        WHERE {CLEAN_CLOSED}
          AND neighbourhood IS NOT NULL
          AND NOT bad_location
        GROUP BY neighbourhood
        HAVING COUNT(*) >= 50
    """,
    "channel_times": f"""
        SELECT
            category,
            {CHANNEL} AS channel,
            COUNT(*) AS closed_requests,
            MEDIAN(days_to_close) AS median_days,
            QUANTILE_CONT(days_to_close, 0.9) AS p90_days
        FROM requests
        WHERE {CLEAN_CLOSED}
        GROUP BY ALL
        HAVING COUNT(*) >= 100
    """,
}

# One flat table that Tableau / Power BI can open directly
BI_SUMMARY = f"""
    SELECT
        year, month, season, category, ward, neighbourhood,
        {CHANNEL} AS channel,
        COUNT(*) AS requests,
        COUNT(*) FILTER (WHERE status = 'Closed') AS closed_requests,
        MEDIAN(days_to_close) AS median_days_to_close
    FROM requests
    WHERE year >= 2022
    GROUP BY ALL
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        for name, query in QUERIES.items():
            path = OUT_DIR / f"{name}.parquet"
            con.execute(f"COPY ({query}) TO '{path.as_posix()}' (FORMAT parquet)")
            rows = con.execute(f"SELECT count(*) FROM read_parquet('{path.as_posix()}')").fetchone()[0]
            print(f"{path}: {rows:,} rows, {path.stat().st_size / 1e6:.1f} MB")

        csv_path = OUT_DIR / "edmonton_311_summary.csv"
        con.execute(f"COPY ({BI_SUMMARY}) TO '{csv_path.as_posix()}' (HEADER, DELIMITER ',')")
        print(f"{csv_path}: {csv_path.stat().st_size / 1e6:.1f} MB (for Tableau / Power BI)")


if __name__ == "__main__":
    main()
