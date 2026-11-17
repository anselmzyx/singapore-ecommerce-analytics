-- Q3. Discount Analysis
-- Reports two denominators explicitly and never conflates them (Stage 1/2
-- review correction): share of ALL identifiable rows in a view, and share of
-- rows where a discount was actually RECORDED (populated) in that view.

-- name: discount_status_by_view
-- Denominator = all identifiable observations in that view.
SELECT
    source_view,
    discount_consistency_status,
    COUNT(*) AS n,
    SUM(COUNT(*)) OVER (PARTITION BY source_view) AS n_total_identifiable_in_view,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY source_view), 1) AS pct_of_identifiable_in_view
FROM observations
GROUP BY source_view, discount_consistency_status
ORDER BY source_view, discount_consistency_status;

-- name: discount_testable_population
-- Correction (Stage 4 review): a recorded-vs-implied discount COMPARISON is only
-- meaningful where BOTH discount_recorded_pct and discount_implied_pct are
-- available -- not merely where the recorded field is populated. A row can have
-- a populated recorded discount but still be untestable if its reference price
-- is invalid/missing (the Store view's 312 "-1" sentinel rows: discount is
-- recorded for all 999 Store rows, but only 687 have a valid reference price
-- and so only 687 are testable). This query reports n_recorded_populated,
-- n_testable_both_available, and n_populated_but_untestable as three distinct
-- counts, and bases the inconsistency rate on the testable count only.
SELECT
    source_view,
    SUM(CASE WHEN discount_recorded_pct IS NOT NULL THEN 1 ELSE 0 END) AS n_recorded_populated,
    SUM(CASE WHEN discount_recorded_pct IS NOT NULL AND discount_implied_pct IS NOT NULL THEN 1 ELSE 0 END) AS n_testable_both_available,
    SUM(CASE WHEN discount_recorded_pct IS NOT NULL AND discount_implied_pct IS NULL THEN 1 ELSE 0 END) AS n_populated_but_untestable,
    SUM(CASE WHEN discount_consistency_status = 'inconsistent' THEN 1 ELSE 0 END) AS n_inconsistent,
    ROUND(
        100.0 * SUM(CASE WHEN discount_consistency_status = 'inconsistent' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN discount_recorded_pct IS NOT NULL AND discount_implied_pct IS NOT NULL THEN 1 ELSE 0 END), 0),
        1
    ) AS pct_inconsistent_of_testable
FROM observations
GROUP BY source_view
ORDER BY source_view;

-- name: implied_discount_distribution
-- Only where reference_price_status = 'valid' (excludes the 312 Store -1
-- sentinel rows and any other missing/invalid reference price).
SELECT
    source_view,
    COUNT(*) AS n_valid_reference,
    MEDIAN(discount_implied_pct) AS median_implied_pct,
    AVG(discount_implied_pct) AS mean_implied_pct,
    MIN(discount_implied_pct) AS min_implied_pct,
    MAX(discount_implied_pct) AS max_implied_pct
FROM observations
WHERE reference_price_status = 'valid' AND discount_implied_pct IS NOT NULL
GROUP BY source_view
ORDER BY source_view;

-- name: reference_price_status_by_view
SELECT
    source_view,
    reference_price_status,
    COUNT(*) AS n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY source_view), 1) AS pct_of_view
FROM observations
GROUP BY source_view, reference_price_status
ORDER BY source_view, reference_price_status;
