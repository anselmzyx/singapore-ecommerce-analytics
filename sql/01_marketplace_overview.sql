-- Q1. Marketplace Sample Overview
-- Observation counts, distinct listings, distinct shops; per-view breakdown;
-- cross-view overlap (so a listing present in >1 view is never double-counted
-- in the overall distinct-listing total); and an overall representative price
-- summary using an explicit, deterministic per-listing selection rule.

-- name: overview_totals
SELECT
    'overall' AS section,
    'all_views' AS label,
    COUNT(*) AS observations,
    COUNT(DISTINCT listing_key) AS distinct_listings,
    COUNT(DISTINCT shop_id) AS distinct_shops
FROM observations

UNION ALL

SELECT
    'by_view' AS section,
    source_view AS label,
    COUNT(*) AS observations,
    COUNT(DISTINCT listing_key) AS distinct_listings,
    COUNT(DISTINCT shop_id) AS distinct_shops
FROM observations
GROUP BY source_view

ORDER BY section, label;

-- name: cross_view_overlap
-- One row per distinct combination of views a listing_key appears in.
-- distinct_listings here sums to the overall total (2,727) with no double count.
WITH view_membership AS (
    SELECT
        listing_key,
        STRING_AGG(DISTINCT source_view, '+' ORDER BY source_view) AS views_present
    FROM observations
    GROUP BY listing_key
)
SELECT
    views_present,
    COUNT(*) AS distinct_listings
FROM view_membership
GROUP BY views_present
ORDER BY distinct_listings DESC;

-- name: overall_representative_price
-- Representative-observation rule (documented in docs/STAGE3_SQL_ANALYSIS.md):
-- for each listing_key, take the observation with the LATEST crawl_time
-- (deterministic tiebreak: source_view then source_excel_row, ascending;
-- no ties actually occur in this dataset). This replaces the Stage 2 EDA's
-- use of the per-listing MINIMUM price across views, which was not an
-- unquestioned canonical price -- it is kept here only as a single descriptive
-- summary figure, with per-view prices still examined separately in Q7.
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY listing_key
            ORDER BY crawl_time DESC, source_view ASC, source_excel_row ASC
        ) AS rn
    FROM observations
)
SELECT
    COUNT(*) AS n_listings,
    MEDIAN(price) AS median_price,
    QUANTILE_CONT(price, 0.25) AS q1_price,
    QUANTILE_CONT(price, 0.75) AS q3_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM ranked
WHERE rn = 1;
