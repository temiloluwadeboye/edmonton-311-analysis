-- Question 2: How do requests change through the year?
--
-- Goal: one row per month (1-12), showing the AVERAGE number of requests per year
-- in that month for: all requests, Potholes, Maintenance - Snow & Ice, Encampments, Litter.
-- Use only full years from 2022 onwards (leave out the unfinished current year:
-- the partial_year column is already TRUE for it).
--
-- Why an average per year? 2022-2025 is four years, so dividing each month's
-- count by the number of years gives "a typical January", "a typical July", etc.
--
-- New concept: conditional aggregation (counting only some rows inside a group).
--   count(*) FILTER (WHERE category = 'Potholes') AS potholes
-- counts only the pothole rows in each month. This turns one long list into a
-- wide table with one column per category (a "pivot").
--
-- Hint: count(DISTINCT year) gives the number of years in the data you kept,
-- so count(*) / count(DISTINCT year) is the yearly average.
-- Round to whole numbers.
--
-- Run: python -m src.run_sql sql/02_seasonal_patterns.sql

SELECT
    month,
    -- * 1.0 forces decimal division (PostgreSQL would otherwise round down 7/2 to 3);
    -- ::INTEGER turns the rounded result into a whole number
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT year))::INTEGER AS avg_requests,
    ROUND(COUNT(*) FILTER (WHERE category = 'Potholes') * 1.0 / COUNT(DISTINCT year))::INTEGER AS avg_potholes,
    ROUND(COUNT(*) FILTER (WHERE category = 'Maintenance - Snow & Ice') * 1.0 / COUNT(DISTINCT year))::INTEGER AS avg_snow_ice,
    ROUND(COUNT(*) FILTER (WHERE category = 'Encampments') * 1.0 / COUNT(DISTINCT year))::INTEGER AS avg_encampments,
    ROUND(COUNT(*) FILTER (WHERE category = 'Litter') * 1.0 / COUNT(DISTINCT year))::INTEGER AS avg_litter
FROM requests
WHERE year >= 2022 AND NOT partial_year
GROUP BY month
ORDER BY month;
