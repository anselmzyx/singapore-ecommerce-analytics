-- Q7. Cross-View Price Differences.
-- Aggregate-only outputs -- no per-listing row (which could combine price
-- values into a near-identifying fingerprint) is exported, per the project
-- brief. Uses data/processed/listings_unique_reference.csv, which already
-- pivots one row per listing_key with per-view prices.

-- name: multiview_summary
SELECT
    COUNT(*) AS n_total_listings,
    SUM(CASE WHEN n_views_present > 1 THEN 1 ELSE 0 END) AS n_multiview_listings,
    ROUND(100.0 * SUM(CASE WHEN n_views_present > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_multiview_listings
FROM unique_listings;

-- name: price_conflict_summary
SELECT
    COUNT(*) AS n_multiview_listings,
    SUM(CASE WHEN cross_view_price_conflict THEN 1 ELSE 0 END) AS n_conflicting,
    ROUND(100.0 * SUM(CASE WHEN cross_view_price_conflict THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_conflicting,
    ROUND(
        AVG(
            CASE WHEN cross_view_price_conflict
                 THEN 100.0 * (price_max_across_views - price_min_across_views) / NULLIF(price_min_across_views, 0)
            END
        ),
        1
    ) AS avg_pct_spread_when_conflicting
FROM unique_listings
WHERE n_views_present > 1;

-- name: price_conflict_spread_distribution
-- Aggregate bucket counts only -- no individual listing's price values are exported.
SELECT
    CASE
        WHEN spread_pct < 2 THEN '<2%'
        WHEN spread_pct < 5 THEN '2-5%'
        WHEN spread_pct < 10 THEN '5-10%'
        ELSE '>=10%'
    END AS spread_bucket,
    COUNT(*) AS n_listings
FROM (
    SELECT 100.0 * (price_max_across_views - price_min_across_views) / NULLIF(price_min_across_views, 0) AS spread_pct
    FROM unique_listings
    WHERE cross_view_price_conflict = true
) t
GROUP BY spread_bucket
ORDER BY spread_bucket;
