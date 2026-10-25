-- Question 5: Do requests made through the mobile app get closed faster than phone calls?
--
-- Goal: compare how fast requests are closed depending on HOW they were reported,
-- within the same kinds of request. One row per (category, channel) pair, for three
-- common categories: 'Potholes', 'Litter', 'Maintenance - Snow & Ice'. Show:
--   * category
--   * channel          - the reporting channel, grouped (see below)
--   * closed_requests
--   * median_days and p90_days
-- Sort by category, then by median_days (fastest channel first within each category).
--
-- Same filters as questions 3 and 4 (since 2022, closed, not closed_without_date, no
-- duplicates). Since 2022 the sources are:
--   Mobile App 272,334 | Phone Call 166,326 | Mobile App Generic 98,150 |
--   ESRI MAP 34,143 | Email 1,176 | Web Forms 1
-- Group them into three channels:
--   'Mobile App' and 'Mobile App Generic'  -> 'App'
--   'Phone Call'                           -> 'Phone'
--   everything else (map, email, web form) -> 'Online / other'
--
-- Why within categories again? Same confounder as question 4: if app users mostly report
-- fast categories (like parking), the app would look faster even if it isn't.
--
-- New concepts:
--   CASE WHEN ... THEN ... ELSE ... END   build a new value row by row, e.g.
--       CASE WHEN source IN ('Mobile App', 'Mobile App Generic') THEN 'App'
--            WHEN source = 'Phone Call' THEN 'Phone'
--            ELSE 'Online / other' END AS channel
--   IN ('a', 'b')                          shorthand for  = 'a' OR = 'b'
--   GROUP BY category, channel             one group per COMBINATION of the two
--   Tip: put the CASE in a CTE first (like question 4), then GROUP BY channel outside it;
--   that way you don't have to repeat the whole CASE in the GROUP BY.
--
-- Run: python -m src.run_sql sql/05_source_response_times.sql

-- Step 1: pick the rows and label each one with its reporting channel
WITH requests_by_channel AS (
    SELECT
        category,
        CASE
            WHEN source IN ('Mobile App', 'Mobile App Generic') THEN 'App'
            WHEN source = 'Phone Call'                          THEN 'Phone'
            ELSE 'Online / other'
        END AS channel,
        days_to_close
    FROM requests
    WHERE year >= 2022
      AND status = 'Closed'
      AND NOT closed_without_date
      AND (status_detail IS NULL OR status_detail NOT LIKE 'Duplicate%')
      AND category IN ('Potholes', 'Litter', 'Maintenance - Snow & Ice')
)

-- Step 2: one row per (category, channel), with the same measures as questions 3 and 4
SELECT
    category,
    channel,
    COUNT(*) AS closed_requests,
    MEDIAN(days_to_close) AS median_days,
    QUANTILE_CONT(days_to_close, 0.9) AS p90_days
FROM requests_by_channel
GROUP BY category, channel
HAVING COUNT(*) >= 100          -- leave out groups too small to be reliable
ORDER BY category, median_days, p90_days;
