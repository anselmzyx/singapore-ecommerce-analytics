-- Q4. Seller Assortment and Pricing (Store view only -- 12 named shop handles).
-- Purely descriptive: counts, median observed price, assortment size. No
-- composite score, rank, or performance/profitability claim is computed.

-- name: seller_assortment
-- Correction (Stage 4 review): median_rating is computed on RATED listings only
-- (rating > 0); rating = 0 is a "not yet rated" sentinel (see sql/05), and
-- including it previously pulled some stores' medians down artificially --
-- e.g. azren_albakri92.sg has 38 of its 89 listings unrated, which understated
-- its true median rating. n_rated / n_unrated are reported per store so this
-- is never hidden.
SELECT
    store_name,
    COUNT(*) AS n_listings,
    COUNT(DISTINCT listing_key) AS n_distinct_listings,
    MEDIAN(price) AS median_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    ROUND(100.0 * SUM(CASE WHEN variant_comparability_uncertain THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_variant_uncertain,
    SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS n_rated,
    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS n_unrated,
    MEDIAN(rating) FILTER (WHERE rating > 0) AS median_rating_rated_only,
    MEDIAN(reviews_count) FILTER (WHERE rating > 0) AS median_reviews_count_rated_only
FROM observations
WHERE source_view = 'store'
GROUP BY store_name
ORDER BY n_listings DESC;
