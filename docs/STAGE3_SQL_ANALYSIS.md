# Stage 3 SQL Business Analysis: Shopee Singapore Listing Samples

Executed via DuckDB (`scripts/run_sql_analysis.py`) against
`data/processed/listings_observations.csv` (2,996 rows) and
`listings_unique_reference.csv` (2,727 rows). SQL source is in `sql/`, and raw outputs
are in `results/sql/`. All numbers below are read directly from those executed
outputs.

**Scope reminder:** every finding describes the sampled 6 Category groups, 17 Keyword
search terms, and 12 Store handles in this 18 August 2025 snapshot only, not the
Singapore e-commerce marketplace broadly. `price` is a historical listing-price
observation, not a verified completed-transaction price. `rating`, `reviews_count`,
`sold`, and `monthly_sold` are source-reported platform counters, not independently
audited sales or satisfaction measures. I don't make any revenue, profitability,
market share, retention, causal, or time-series claim anywhere in this document.

## Representative-price selection rule (correction from Stage 2 review)

Stage 2's EDA used each listing's **minimum** price across views as a convenience
"listing price," without a documented rule. Stage 3 replaces this with an explicit,
deterministic rule wherever a single representative price per listing is needed
(`sql/01_marketplace_overview.sql`, `overall_representative_price`): **the observation
with the latest `crawl_time` for that `listing_key`** (tiebreak: `source_view` then
`source_excel_row`, ascending; verified to never actually trigger in this dataset,
since no listing has two observations sharing the same `crawl_time`). Per-view prices
and cross-view conflicts continue to be reported separately (Q7) rather than
collapsed into this one figure.

---

## Q1. Marketplace Sample Overview

From `overview_totals`, `cross_view_overlap`, `overall_representative_price`.

| Metric | Value |
|---|---|
| Total observations | 2,996 |
| Total distinct listings | **2,727** |
| Total distinct shops | **968** |
| Category view | 998 obs, 956 distinct listings, 482 shops |
| Keyword view | 999 obs, 836 distinct listings, 543 shops |
| Store view | 999 obs, 999 distinct listings, 12 shops |

Cross-view membership (sums to 2,727, no double-count): Store-only 977, Category-only
898, Keyword-only 789, Category+Keyword 41, Category+Store 16, Keyword+Store 5, all
three 1.

**Representative-price summary** (one row per listing, latest-crawl-time rule): median
**SGD 12.90**, IQR SGD 6.00 to 27.00, range SGD 0.10 to 999.00, n=2,727.

**Commercial implication:** the sample is broad in shop count (968), but each view
covers it from a different angle. The Store view trades shop breadth for very deep
per-shop-handle coverage of only 12 shops, while Category and Keyword views trade shop
depth for broader but shallower shop sampling. Any seller-level claim needs to specify
which view it's drawn from.

## Q2. Product Pricing by Category

From `pricing_by_category`, `category_view_distinct_total`,
`price_999_sensitivity_overall`.

| Category | Listings | Median price (SGD) | IQR | % variant-uncertain |
|---|---|---|---|---|
| Housekeeping | 180 | 2.53 | 0.98 to 5.39 | 56.7% |
| Laundry Care | 180 | 3.51 | 1.96 to 8.68 | 62.2% |
| Bath & Body | 180 | 5.77 | 2.93 to 11.92 | 49.4% |
| Softeners | 180 | 8.08 | 5.56 to 15.10 | 43.3% |
| Detergents | 180 | 8.93 | 5.47 to 21.11 | 46.1% |
| Body lotion | 98 | 11.56 | 7.35 to 25.53 | 58.2% |

**Per-category listing counts already deduplicate correctly** (`COUNT(*)` equals
`COUNT(DISTINCT listing_key)` within every category: no same-category duplicate rows
exist). However, **summing these six counts (998) is not the Category view's true
distinct-listing total, which is 956** (`category_view_distinct_total`), because 42
listings are sampled under two different categories each and are counted once per
category above but only once view-wide. Categories aren't mutually exclusive groups.

**SGD 999 sensitivity check** (a suspected, unproven price-ceiling anomaly): 4
Category-view observations sit at exactly SGD 999 (2 in Bath & Body, 2 in Body
lotion). Excluding them, category medians shift by at most **SGD 0.12** (Body lotion:
11.56 to 11.45), which is negligible. View-wide, the mean price drops from **SGD 15.58
to SGD 11.62** (roughly a 25% difference) when these rows are excluded, while the
median barely moves (SGD 6.41 to 6.35). **Medians are robust to this anomaly; means are
not.** Any mean-based price claim should be reported alongside this sensitivity figure.

**Commercial implication:** category price positioning (Housekeeping and Laundry Care
as cheaper staples versus Body lotion and Detergents as higher-value items) is a
reasonable descriptive read for *this sample*, but variant and pack-size ambiguity
affects 43 to 62% of listings per category. A price comparison between two specific
listings in the same category still needs a manual check that they're comparable pack
sizes.

## Q3. Discount Analysis

From `discount_status_by_view`, `discount_testable_population`,
`implied_discount_distribution`, `reference_price_status_by_view`.

**Correction (Stage 4 review):** a recorded-versus-implied comparison is only
meaningful where *both* values are available, not merely where the recorded field is
populated. `discount_testable_population` reports three distinct counts per view
instead of one:

| View | Recorded populated | **Testable (both available)** | Populated but untestable | Inconsistent (of testable) |
|---|---|---|---|---|
| Category | 780 | 780 | 0 | **19.2%** (150/780) |
| Keyword | 674 | 674 | 0 | **10.4%** (70/674) |
| Store | 999 | **687** | **312** | **0.0%** (0/687) |

For Category and Keyword, "populated" and "testable" are identical (reference price
is 100% valid in both views), so their inconsistency percentages are unchanged from
the prior report. For Store, the 312 `-1`-sentinel rows are now explicitly separated
out as *populated but untestable* rather than silently folded into, and diluting, a
single denominator. Store's 0.0% inconsistency rate is based on its 687 genuinely
testable rows only.

The overall discount-status breakdown (percentage of identifiable rows per view) is
unchanged: 63.1%/60.5%/68.8% consistent, 21.8%/32.5%/0% no recorded discount.

Price-implied discount (valid-reference-price rows only): Category median 19.6% (mean
26.8%), Keyword median 17.1% (mean 23.3%), Store median 23.2% (mean 24.6%).

**Commercial implication:** the recorded `discount` field can't be trusted at face
value in 10 to 19% of the rows where it's even populated, and it's simply absent in
22 to 33% of rows depending on view. Any "X% off" marketing claim drawn from this
field needs row-level validation against `price`/`price_before_discount` first. This
is a data-quality finding about the sample, not a statement about actual Shopee
discount accuracy.

## Q4. Seller Assortment and Pricing

From `seller_assortment` (Store view, 12 named shop handles). Purely descriptive, with
no seller ranking, score, or performance/profitability claim.

Listings per store range from 55 to 90 (median 89.5). Median observed price per store
ranges from SGD 10.36 (azren_albakri92.sg) to SGD 66.76 (eucerin.sg). 4 of 12 stores
(garnier.sg, kimagesalon, eucerin.sg, laneigesg) have at least one listing at the
suspected SGD 999 ceiling (see Q2). `pct_variant_uncertain` ranges from 2.7% to 34.4%
by store.

**Correction (Stage 4 review):** `median_rating_rated_only` now excludes `rating = 0`
("not yet rated," see Q5) rows per store. Previously these were included and
understated some stores' true median rating. The effect is material for
**azren_albakri92.sg**, where 38 of its 89 listings (42.7%) are unrated: its median
rating rises from a previously reported 4.67 to **4.94** once those 38 unrated
listings are excluded (51 rated listings remain). All other stores shift negligibly
(1 or fewer unrated listings each, except kaobeautyofficialstore and kimagesalon at 4
each, and garnier.sg/eucerin.sg at 5 to 7 each). `n_rated`/`n_unrated` are reported per
store so this stays visible.

**Commercial implication:** assortment size and price positioning vary descriptively
across these 12 named handles, but with only 12 shops sampled, this can't support any
seller-strategy, competitiveness, or performance ranking. It describes assortment and
pricing for these 12 named handles in this sample only.

## Q5. Product Ratings and Reviews

From `ratings_population_overview`, `ratings_overall`, `ratings_by_category`,
`ratings_by_view`.

**Data-quality finding:** 283 of 2,996 observations (9.4%) record `rating = 0`, and
**every one** of them also has `rating_count = 0` and `reviews_count = 0`. In other
words, `rating = 0` marks "not yet rated," not a genuine 0-star score. "Rated" is
therefore defined as `rating > 0` throughout this section (2,713 of 2,996
observations, 90.6%).

**Correction (Stage 4 review):** `rating > 0` and `reviews_count > 0` are **not** the
same population. `ratings_population_overview` shows 115 observations have
`rating > 0` (a star rating exists) but `reviews_count = 0` (no written review was
left), while 0 observations show the reverse (`rating = 0` with `reviews_count > 0`).
Stage 2's EDA used `reviews_count > 0` as its rated-population filter, which is a
stricter, slightly smaller population (2,598 rows) than the correct `rating > 0`
definition (2,713 rows) used here.

Among the 2,713 rated observations: median rating **4.92**, minimum rating **3.0**,
median review count **68**.

By category (rated listings only, descending median rating): Softeners 4.93 (180/180
rated), Detergents 4.92 (180/180), Body lotion 4.91 (97/98 rated), Bath & Body 4.91
(180/180), Housekeeping 4.86 (180/180), Laundry Care 4.84 (180/180). That's a very
narrow band (0.09 points) with little discriminating signal.

**Commercial implication:** ratings are near-universally high and cluster tightly
across categories in this sample, so they're not useful for distinguishing "better"
from "worse" product groups here. These are platform-reported counters, not
independently verified customer satisfaction or completed-sale confirmations.

## Q6. Sponsored Keyword Listings

From `sponsored_overall`, `sponsored_by_keyword` (Keyword view, 17 search terms).

**56.7%** (566/999) of Keyword-view observations are flagged sponsored, and **43.3%**
(433) are organic. Sponsorship share varies widely by search term (full breakdown in
`results/sql/sponsored_by_keyword.csv`), from search terms with heavy organic
presence to others that are almost entirely sponsored slots.

**Commercial implication:** this describes paid-placement prevalence in the sampled
search results only. `sponsored` is a source-provided flag on how a listing appeared
in these particular search results. I don't interpret it here as a cause of demand,
sales, or listing quality.

## Q7. Cross-View Price Differences

From `multiview_summary`, `price_conflict_summary`, `price_conflict_spread_distribution`.
Aggregate-only: no per-listing row is exported.

Of 2,727 distinct listings, **63 (2.3%)** appear in more than one view. Of those 63,
**9 (14.3%)** show a conflicting recorded price across views, averaging a **7.4%**
spread when conflicting. Spread-magnitude distribution among the 9 conflicts: 1
listing under 2%, 2 listings between 2% and 5%, 3 listings between 5% and 10%, and 3
listings at 10% or above.

**Commercial implication:** `price` has to be treated as a view- and time-specific
point observation. Consistent with the Stage 1 finding that Category and Keyword were
crawled roughly 15 to 18 hours before Store on the same day, some of this spread
likely reflects genuine price changes during the day rather than measurement error.
This dataset can't distinguish the two causes, and I don't assert a single price as
"correct" for a multi-view listing.

## Main limitations (carried forward and new)

- Narrow category, keyword, and seller scope from Stage 1, unchanged by this
  analysis.
- SGD 999 price-ceiling pattern remains **suspected, not proven** (see Q2).
- 43 to 62% of listings per category have variant/pack-size ambiguity.
- Discount field requires row-level validation; 22 to 33% of rows have no recorded
  discount at all, depending on view.
- Only 12 shops sampled in the Store view, so no seller-performance claim is
  supportable.
- Ratings cluster in a narrow 0.09-point band across categories, with low
  discriminating value in this sample.
- Cross-view price conflicts (9 of 63 multi-view listings) are documented, not
  resolved.
- All findings are single-day, cross-sectional, and descriptive only.
