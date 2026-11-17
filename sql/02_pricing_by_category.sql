-- Q2. Product Pricing by Category (Category view only; category_name exists
-- only in this view). COUNT(DISTINCT listing_key) is used deliberately rather
-- than COUNT(*), per Stage 2 review correction 3 -- within each category these
-- happen to be equal here (no same-category duplicate rows exist in this
-- dataset), but the query is written to stay correct even if that changes.
-- Summing the per-category distinct-listing counts below (998) is NOT the
-- same as the Category view's own total distinct-listing count (956): 42
-- listings are sampled under more than one category (see sql/01, cross_view_overlap
-- is listing-vs-view; this is category-vs-category within the same view), so
-- they are counted once per category here but only once overall.

-- name: pricing_by_category
WITH cat AS (
    SELECT * FROM observations WHERE source_view = 'category'
),
main_stats AS (
    SELECT
        category_name,
        COUNT(*) AS n_rows,
        COUNT(DISTINCT listing_key) AS n_distinct_listings,
        MEDIAN(price) AS median_price,
        QUANTILE_CONT(price, 0.25) AS q1_price,
        QUANTILE_CONT(price, 0.75) AS q3_price,
        MIN(price) AS min_price,
        MAX(price) AS max_price,
        STDDEV(price) AS stddev_price,
        SUM(CASE WHEN variant_comparability_uncertain THEN 1 ELSE 0 END) AS n_variant_uncertain,
        ROUND(100.0 * SUM(CASE WHEN variant_comparability_uncertain THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_variant_uncertain,
        SUM(CASE WHEN price = 999 THEN 1 ELSE 0 END) AS n_at_999
    FROM cat
    GROUP BY category_name
),
excl_999 AS (
    SELECT
        category_name,
        COUNT(*) AS n_listings_excl_999,
        MEDIAN(price) AS median_price_excl_999,
        AVG(price) AS mean_price_excl_999
    FROM cat
    WHERE price < 999
    GROUP BY category_name
)
SELECT
    m.category_name,
    m.n_rows,
    m.n_distinct_listings,
    m.median_price,
    m.q1_price,
    m.q3_price,
    m.min_price,
    m.max_price,
    m.stddev_price,
    m.n_variant_uncertain,
    m.pct_variant_uncertain,
    m.n_at_999,
    e.n_listings_excl_999,
    e.median_price_excl_999,
    e.mean_price_excl_999,
    ROUND(m.median_price - e.median_price_excl_999, 4) AS median_sensitivity_to_999_ceiling
FROM main_stats m
JOIN excl_999 e USING (category_name)
ORDER BY m.median_price;

-- name: category_view_distinct_total
-- The Category view's own non-inflated distinct-listing total (956), for
-- comparison against the sum of the per-category n_distinct_listings above
-- (998) -- the 42-listing difference is genuine multi-category membership,
-- not double-counting error (see note above).
SELECT
    COUNT(*) AS n_rows_category_view,
    COUNT(DISTINCT listing_key) AS n_distinct_listings_category_view
FROM observations
WHERE source_view = 'category';

-- name: price_999_sensitivity_overall
-- Suspected price-ceiling sensitivity check at the whole-Category-view level
-- (not proven censoring -- see docs/STAGE3_SQL_ANALYSIS.md).
SELECT
    (SELECT COUNT(*) FROM observations WHERE source_view = 'category' AND price = 999) AS n_at_999,
    (SELECT MEDIAN(price) FROM observations WHERE source_view = 'category') AS median_price_all,
    (SELECT MEDIAN(price) FROM observations WHERE source_view = 'category' AND price < 999) AS median_price_excl_999,
    (SELECT AVG(price) FROM observations WHERE source_view = 'category') AS mean_price_all,
    (SELECT AVG(price) FROM observations WHERE source_view = 'category' AND price < 999) AS mean_price_excl_999;
