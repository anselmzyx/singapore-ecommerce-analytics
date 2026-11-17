# Stage 2 EDA Findings — Shopee Singapore Listing Samples

Source: `notebooks/01_ecommerce_eda.ipynb`, executed against
`data/processed/listings_observations.csv` (2,996 rows) and
`data/processed/listings_unique_reference.csv` (2,727 rows). Figures saved to `figures/`.

**Scope reminder:** every finding below describes the **sampled** 6 Category groups, 17
Keyword search terms, and 12 Store handles in this 18 August 2025 snapshot only. None of
these findings describe the Singapore e-commerce marketplace broadly, and `sold`,
`monthly_sold`, `rating`, and `reviews_count` are source-reported platform counters, not
independently audited sales, revenue, or customer-satisfaction measures.

## Chart 1 — Listing-price distribution and outliers (`figures/01_price_distribution.png`)

Using the 2,727 distinct listings (minimum recorded price across views where a listing
appears more than once, to avoid inflating the distribution): median price **SGD 12.90**,
IQR-based outlier fence at **SGD 58.50**, with **238 listings (8.7%)** above that fence.

**New finding:** 22 of those 2,727 listings are priced at exactly **SGD 999**, with
**zero** listings priced between SGD 900 and 998. This gap is consistent with a platform-
or crawler-side display/storage price ceiling at 999 — but this is a **suspected
anomaly, not proven censoring** (corrected during Stage 3 review; see
`docs/STAGE2_CORRECTIONS_ADDENDUM.md` §1). The true price for these 22 listings should
**not** be assumed to be ≥999; a coincidental clustering at exactly 999 cannot be ruled
out from this data alone. `sql/02_pricing_by_category.sql` reports category pricing both
with and without these rows (see Chart/Q2 sensitivity check) so the effect is visible
either way rather than assumed.

## Chart 2 — Price by sampled Category group (`figures/02_price_by_category.png`)

Category-view median prices range from **SGD 2.53 (Housekeeping)** to **SGD 11.56 (Body
lotion)**, with Detergents (SGD 8.93) and Softeners (SGD 8.08) in between and Laundry Care
(SGD 3.51) and Bath & Body (SGD 5.77) lower. Each group shows a long right tail of
higher-priced variants/outliers. This ordering describes the 998 sampled Category-view
listings only — it is not a statement about typical prices for these product types
Singapore-wide, and variant/pack-size differences are not reconciled in this chart (see
`variant_comparability_uncertain` in the cleaned data, flagged for 36.4% of all rows).

## Chart 3 — Discount field status by view (`figures/03_discount_status_by_view.png`)

Discount-field reliability differs materially by view:

| View | Consistent | Inconsistent (>1pt) | No recorded discount | Invalid/missing reference |
|---|---|---|---|---|
| Category | 63.1% | 15.0% | 21.8% | 0% |
| Keyword | 60.5% | 7.0% | 32.5% | 0% |
| Store | 68.8% | 0% | 0% | 31.2% |

(Percentages of each view's identifiable rows; see
`docs/STAGE1_CORRECTIONS_ADDENDUM.md` §A for why these are reported against the correct
denominator.) Store has no internal inconsistency (0 of 999) precisely because the only
rows with an invalid reference price (the 312 `-1` sentinels) are routed to "invalid
reference" rather than being compared at all — had they been force-compared, they would
not meaningfully disagree since `discount = "0%"` is recorded for all of them (see
`docs/STAGE1_DATASET_REVIEW.md` §5.5).

## Chart 4 — Price-implied discount distribution (`figures/04_implied_discount_distribution.png`)

Among the 2,684 observations with a valid reference price, price-implied discounts have a
median of **20.4%** and a mean of **24.9%**. This is the discount implied purely by the
recorded price fields, independent of whatever the `discount` field states — the two
should be read together with `discount_consistency_status`, not interchangeably.

## Chart 5 — Rating vs. review count (`figures/05_rating_vs_reviews.png`)

Among 2,362 distinct listings with both fields recorded and a nonzero review count:
recorded ratings range from **3.0 to 5.0** (median **4.92**), and review counts are
heavily right-skewed (median **73.5**, maximum **15,093**). High ratings are near-universal
in this sample — there is little discriminating signal in `rating` alone across these
listings, and because these are platform-reported counters, this should be read as "what
the listings in this sample report," not as independently verified customer satisfaction.

## Chart 6 — Seller coverage and assortment (`figures/06_store_assortment.png`)

The Store view's 999 listings are spread across only **12 distinct, named store handles**
(e.g., `kenvue.sg`, `colgate.palmolive`, `cetaphil.sg`), ranging from 55 to 90 listings
per store — a fairly even split among the 12, but still a very shallow seller sample.
**This cannot support any representative seller-strategy or competitive-positioning
conclusion** — it describes assortment size for 12 named handles only.

## Chart 7 — Sponsored vs. organic composition, Keyword view (`figures/07_sponsored_by_keyword.png`)

**56.7%** of the 999 Keyword-view observations are flagged `sponsored = True`; this share
varies substantially by search term (from a handful of sponsored slots on some keywords
to near-total sponsored saturation on others, e.g. "antiperspirant deodorant"). This
describes paid-placement prevalence in the sampled search results only, not demand,
popularity, or conversion.

## Cross-cutting findings (not a single chart, carried from cleaning)

- **9 of 63 (14.3%)** listings appearing in more than one view have a conflicting
  recorded price across views (1.8%–12.5% apart), consistent with Store being crawled
  ~15–18 hours after Category/Keyword on the same day (see
  `docs/STAGE1_CORRECTIONS_ADDENDUM.md` §C). Treat `price` as view- and time-specific, not
  a single canonical current price per listing.
- **1,091 of 2,996 (36.4%)** observations have `variant_comparability_uncertain = True`
  (a min/max price or MRP range), meaning more than a third of rows may span multiple
  pack sizes or variants under one listing — a material caveat for any price or discount
  comparison at the listing level.

## What cannot be independently recalculated without the raw dataset

Everything in this document was recalculated directly from `data/processed/*.csv`, which
in turn was built directly from the original raw workbooks (checksum-verified unchanged;
see `docs/STAGE2_DATA_CLEANING.md` §8). **Correction (applied during Stage 3 review — see
`docs/STAGE2_CORRECTIONS_ADDENDUM.md` §4):** this section previously and incorrectly
stated that `data/processed/listings_observations.csv` and `listings_unique_reference.csv`
are included in the ChatGPT review ZIP. They are **not** — both are processed row-level
derivatives of the still-unresolved-license third-party dataset and are excluded from
every review ZIP, exactly like the raw workbooks, per `CLAUDE.md`'s licensing rule (see
`docs/STAGE2_HANDOFF.md` §10 for the exclusion as actually implemented). A reviewer
without local filesystem access can verify every number in this document only via the
aggregate JSON/CSV outputs in `results/stage2/`, `results/stage1/`, and, from Stage 3
onward, `results/sql/` — all of which are aggregate-only and are included.

## Explicitly excluded claims

Per the project brief, this analysis makes no revenue, profitability, retention, market
share, causal, or time-series claims. All findings above are descriptive statistics about
the sampled listings in this single-day snapshot.
