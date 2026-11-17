-- Q6. Sponsored Keyword Listings (Keyword view only, 17 sampled search terms).
-- `sponsored` is a source-provided search-result flag; it is not interpreted
-- as a cause of demand or sales anywhere in this analysis.

-- name: sponsored_overall
SELECT
    sponsored,
    COUNT(*) AS n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM observations
WHERE source_view = 'keyword'
GROUP BY sponsored
ORDER BY sponsored DESC;

-- name: sponsored_by_keyword
SELECT
    search_keyword,
    COUNT(*) AS n_total,
    SUM(CASE WHEN sponsored THEN 1 ELSE 0 END) AS n_sponsored,
    SUM(CASE WHEN NOT sponsored THEN 1 ELSE 0 END) AS n_organic,
    ROUND(100.0 * SUM(CASE WHEN sponsored THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_sponsored
FROM observations
WHERE source_view = 'keyword'
GROUP BY search_keyword
ORDER BY pct_sponsored DESC;
