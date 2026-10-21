-- Question 1: What do Edmontonians report most?
--
-- Goal: the 10 most common request categories since 2022 (when the City's current
-- categories and wards are stable), with:
--   * the number of requests in each category
--   * each category's share of all requests since 2022, as a percentage
--
-- Concepts: WHERE, GROUP BY, COUNT(*), ORDER BY ... DESC, LIMIT, and a percentage
-- using a window function: count(*) * 100.0 / sum(count(*)) OVER ()
-- 
-- Run: python -m src.run_sql sql/01_top_categories.sql
SELECT
    category,
    COUNT(*) AS num_requests,
    round(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percent_requests
FROM requests
WHERE year >= 2022
GROUP BY category
ORDER BY num_requests DESC
LIMIT 10;