-- Question 3: How long does the City take to close each type of request?
--
-- Goal: for each category since 2022, using CLOSED requests only, show:
--   * closed_requests  - how many closed requests the category has
--   * mean_days        - the average days to close (1 decimal)
--   * median_days      - the middle value: half close faster, half slower
--   * p90_days         - 90% of requests close within this many days
--   * pct_same_day     - % closed on the same day they were opened (1 decimal)
-- Only keep categories with at least 1,000 closed requests (small groups give
-- unreliable numbers), and sort from slowest to fastest median.
--
-- Use: days_to_close (already calculated), status = 'Closed', and leave out the
-- 37 rows flagged closed_without_date (they have no days_to_close anyway).
--
-- New concepts:
--   median(days_to_close)                 the median (DuckDB shortcut)
--   quantile_cont(days_to_close, 0.9)     the 90th percentile
--       (PostgreSQL writes it: percentile_cont(0.9) WITHIN GROUP (ORDER BY days_to_close))
--   avg(CASE WHEN days_to_close = 0 THEN 1 ELSE 0 END) * 100   share that are 0 days
--   HAVING count(*) >= 1000               like WHERE, but filters GROUPS after counting
--
-- Note: "days to close" is days until the ticket was CLOSED, which is not always days
-- until the problem was FIXED (e.g. 'Deferred-Future Work Planned' closes in ~1 day).
--
-- Run: python -m src.run_sql sql/03_response_times.sql

SELECT
    category,
    COUNT(*) AS closed_requests,
    ROUND(AVG(days_to_close), 1) AS mean_days,
    MEDIAN(days_to_close) AS median_days,
    QUANTILE_CONT(days_to_close, 0.9) AS p90_days,
    ROUND(AVG(CASE WHEN days_to_close = 0 THEN 1 ELSE 0 END) * 100, 1) AS pct_same_day
FROM requests
WHERE year >= 2022
  AND status = 'Closed'
  AND NOT closed_without_date
  -- Duplicates are closed almost instantly and aren't separate requests, so they would
  -- make busy categories look faster. IS NULL keeps the many rows with no detail
  -- (NULL NOT LIKE '...' is "unknown", which WHERE would silently drop).
  AND (status_detail IS NULL OR status_detail NOT LIKE 'Duplicate%')
GROUP BY category
HAVING COUNT(*) >= 1000
ORDER BY median_days DESC, p90_days DESC;  -- second key breaks ties in the median