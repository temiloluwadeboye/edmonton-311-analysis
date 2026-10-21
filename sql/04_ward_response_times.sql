-- Question 4: Are some wards served faster than others?
--
-- Goal: for each of Edmonton's 12 current wards, how fast are POTHOLE requests closed?
-- Show, per ward:
--   * closed_requests
--   * median_days and p90_days (same as question 3)
--   * speed_rank: 1 = fastest median, using RANK() OVER (ORDER BY median_days)
-- Sort by speed_rank.
--
-- Same filters as question 3 (since 2022, closed, not closed_without_date, no duplicates),
-- plus: only the new ward system (ward_system = 'new'), only category = 'Potholes'.
--
-- Why one category only? Wards report different MIXES of problems. A ward with lots of
-- quick parking complaints would look "fast" even if every service were equally fast
-- there. Comparing the same kind of request in every ward makes it fair. (This is called
-- controlling for a confounder: something that affects the result but isn't what
-- you're trying to measure.)
--
-- New concepts:
--   WITH name AS ( ...query... )   a CTE: a named temporary result you can query from.
--       Write the filtered rows (or the per-ward summary) as a CTE, then select from it.
--   RANK() OVER (ORDER BY median_days)   gives 1, 2, 3... (ties share a rank)
--
-- Run: python -m src.run_sql sql/04_ward_response_times.sql

-- Step 1: keep only the rows we want to compare (closed pothole requests, current wards)
WITH pothole_requests AS (
    SELECT ward, days_to_close
    FROM requests
    WHERE year >= 2022
      AND status = 'Closed'
      AND NOT closed_without_date
      AND (status_detail IS NULL OR status_detail NOT LIKE 'Duplicate%')
      AND ward_system = 'new'
      AND category = 'Potholes'
),

-- Step 2: summarise each ward
ward_summary AS (
    SELECT
        ward,
        COUNT(*) AS closed_requests,
        MEDIAN(days_to_close) AS median_days,
        QUANTILE_CONT(days_to_close, 0.9) AS p90_days
    FROM pothole_requests
    GROUP BY ward
)

-- Step 3: rank the wards from fastest to slowest median
SELECT
    RANK() OVER (ORDER BY median_days, p90_days) AS speed_rank,
    ward,
    closed_requests,
    median_days,
    p90_days
FROM ward_summary
ORDER BY speed_rank;
