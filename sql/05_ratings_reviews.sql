-- Q5. Product Ratings and Reviews.
-- rating/reviews_count are source-reported platform counters, not
-- independently verified sales or satisfaction -- see docs/STAGE3_SQL_ANALYSIS.md.
--
-- Correction (Stage 4 review): rating = 0 always co-occurs with rating_count = 0
-- and reviews_count = 0 in this dataset -- it marks "not yet rated," not a
-- genuine 0-star score. "Rated" is therefore defined as rating > 0 throughout
-- this file. IMPORTANT: rating > 0 and reviews_count > 0 are NOT the same
-- population -- 115 rows have rating > 0 (a star rating exists) but
-- reviews_count = 0 (no written reviews were left). ratings_population_overview
-- reports both populations and their overlap explicitly so this is never assumed.

-- name: ratings_population_overview
SELECT
    COUNT(*) AS n_total,
    SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS n_rated,
    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS n_unrated,
    SUM(CASE WHEN reviews_count > 0 THEN 1 ELSE 0 END) AS n_with_written_reviews,
    SUM(CASE WHEN reviews_count = 0 THEN 1 ELSE 0 END) AS n_without_written_reviews,
    SUM(CASE WHEN rating > 0 AND reviews_count = 0 THEN 1 ELSE 0 END) AS n_rated_but_no_written_reviews,
    SUM(CASE WHEN rating = 0 AND reviews_count > 0 THEN 1 ELSE 0 END) AS n_unrated_but_has_written_reviews
FROM observations;

-- name: ratings_overall
-- Rated listings only (rating > 0).
SELECT
    COUNT(*) AS n_rated_observations,
    MEDIAN(rating) AS median_rating,
    MIN(rating) AS min_rating,
    MAX(rating) AS max_rating,
    MEDIAN(reviews_count) AS median_reviews_count,
    MIN(reviews_count) AS min_reviews_count,
    MAX(reviews_count) AS max_reviews_count
FROM observations
WHERE rating > 0;

-- name: ratings_by_category
-- Category view only, rated listings only.
SELECT
    category_name,
    COUNT(*) AS n_listings_total,
    SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS n_rated,
    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS n_unrated,
    MEDIAN(rating) FILTER (WHERE rating > 0) AS median_rating_rated_only,
    MEDIAN(reviews_count) FILTER (WHERE rating > 0) AS median_reviews_count_rated_only
FROM observations
WHERE source_view = 'category'
GROUP BY category_name
ORDER BY median_rating_rated_only DESC;

-- name: ratings_by_view
SELECT
    source_view,
    COUNT(*) AS n_listings_total,
    SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS n_rated,
    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS n_unrated,
    MEDIAN(rating) FILTER (WHERE rating > 0) AS median_rating_rated_only,
    MEDIAN(reviews_count) FILTER (WHERE rating > 0) AS median_reviews_count_rated_only
FROM observations
GROUP BY source_view
ORDER BY source_view;
