# Stage 2 EDA Findings: Shopee Singapore Listing Samples

Source: `notebooks/01_ecommerce_eda_public.ipynb`, executed against
`data/processed/listings_observations.csv` (2,996 rows) and
`data/processed/listings_unique_reference.csv` (2,727 rows). Figures saved to
`figures/`.

**Scope reminder:** every finding below describes the **sampled** 6 Category groups, 17
Keyword search terms, and 12 Store handles in this 18 August 2025 snapshot only. None
of these findings describe the Singapore e-commerce marketplace broadly, and `sold`,
`monthly_sold`, `rating`, and `reviews_count` are source-reported platform counters,
not independently audited sales, revenue, or customer-satisfaction measures.

## Chart 1: Listing-price distribution and outliers (`figures/01_price_distribution.png`)

Using the 2,727 distinct listings (minimum recorded price across views where a listing
appears more than once, to avoid inflating the distribution), the median price is
**SGD 12.90**, the IQR-based outlier fence sits at **SGD 58.50**, and **238 listings
(8.7%)** sit above that fence.

**New finding:** 22 of those 2,727 listings are priced at exactly **SGD 999**, with
**zero** listings priced between SGD 900 and 998. This gap is consistent with a
platform- or crawler-side display/storage price ceiling at 999, but this is a
**suspected anomaly, not proven censoring** (a framing I corrected during Stage 3
review). The true price for these 22 listings shouldn't be assumed to be 999 or
higher. A coincidental clustering at exactly 999 can't be ruled out from this data
alone. `sql/02_pricing_by_category.sql` reports category pricing both with and without
these rows, so the effect is visible either way rather than assumed.

## Chart 2: Price by sampled Category group

*(This chart, `figures/02_price_by_category.png`, isn't included in the public
release of this repository; the finding below is still reproducible locally with the
public notebook.)*

Category-view median prices range from **SGD 2.53 (Housekeeping)** to **SGD 11.56
(Body lotion)**, with Detergents (SGD 8.93) and Softeners (SGD 8.08) in between, and
Laundry Care (SGD 3.51) and Bath & Body (SGD 5.77) lower. Each group shows a long right
tail of higher-priced variants and outliers. This ordering describes the 998 sampled
Category-view listings only. It isn't a statement about typical prices for these
product types Singapore-wide, and variant and pack-size differences aren't reconciled
in this chart (see `variant_comparability_uncertain` in the cleaned data, flagged for
36.4% of all rows).

## Chart 3: Discount field status by view (`figures/03_discount_status_by_view.png`)

Discount-field reliability differs materially by view:

| View | Consistent | Inconsistent (>1pt) | No recorded discount | Invalid/missing reference |
|---|---|---|---|---|
| Category | 63.1% | 15.0% | 21.8% | 0% |
| Keyword | 60.5% | 7.0% | 32.5% | 0% |
| Store | 68.8% | 0% | 0% | 31.2% |

(These are percentages of each view's identifiable rows; see
`docs/STAGE1_DATASET_REVIEW.md` for why these are reported against the correct
denominator.) Store has no internal inconsistency (0 of 999) precisely because the only
rows with an invalid reference price (the 312 `-1` sentinels) are routed to "invalid
reference" rather than being compared at all. Had they been force-compared, they
wouldn't meaningfully disagree, since `discount = "0%"` is recorded for all of them
(see `docs/STAGE1_DATASET_REVIEW.md` §5).

## Chart 4: Price-implied discount distribution (`figures/04_implied_discount_distribution.png`)

Among the 2,684 observations with a valid reference price, price-implied discounts
have a median of **20.4%** and a mean of **24.9%**. This is the discount implied purely
by the recorded price fields, independent of whatever the `discount` field states. The
two need to be read together with `discount_consistency_status`, not interchangeably.

## Chart 5: Rating vs. review count

*(This chart, `figures/05_rating_vs_reviews.png`, isn't included in the public
release of this repository; the finding below is still reproducible locally with the
public notebook.)*

Among 2,362 distinct listings with both fields recorded and a nonzero review count,
recorded ratings range from **3.0 to 5.0** (median **4.92**), and review counts are
heavily right-skewed (median **73.5**, maximum **15,093**). High ratings are
near-universal in this sample, so there's little discriminating signal in `rating`
alone across these listings. Because these are platform-reported counters, I read
this as "what the listings in this sample report," not as independently verified
customer satisfaction.

## Chart 6: Seller coverage and assortment (`figures/06_store_assortment.png`)

The Store view's 999 listings are spread across only **12 distinct, named store
handles** (for example `kenvue.sg`, `colgate.palmolive`, `cetaphil.sg`), ranging from
55 to 90 listings per store, a fairly even split among the 12, but still a very
shallow seller sample. **This can't support any representative seller-strategy or
competitive-positioning conclusion.** It describes assortment size for 12 named
handles only.

## Chart 7: Sponsored vs. organic composition, Keyword view (`figures/07_sponsored_by_keyword.png`)

**56.7%** of the 999 Keyword-view observations are flagged `sponsored = True`. This
share varies substantially by search term, from a handful of sponsored slots on some
keywords to near-total sponsored saturation on others, such as "antiperspirant
deodorant." This describes paid-placement prevalence in the sampled search results
only, not demand, popularity, or conversion.

## Cross-cutting findings (not a single chart, carried from cleaning)

- **9 of 63 (14.3%)** listings appearing in more than one view have a conflicting
  recorded price across views (1.8% to 12.5% apart), consistent with Store being
  crawled roughly 15 to 18 hours after Category/Keyword on the same day (see
  `docs/STAGE1_DATASET_REVIEW.md` §2). I treat `price` as view- and time-specific,
  not a single canonical current price per listing.
- **1,091 of 2,996 (36.4%)** observations have `variant_comparability_uncertain =
  True` (a min/max price or MRP range), meaning more than a third of rows may span
  multiple pack sizes or variants under one listing, a material caveat for any price
  or discount comparison at the listing level.

## What cannot be independently recalculated without the raw dataset

Everything in this document was recalculated directly from `data/processed/*.csv`,
which in turn was built directly from the original raw workbooks (checksum-verified
unchanged, see `docs/STAGE2_DATA_CLEANING.md` §8). The processed CSVs themselves
aren't included in this public repository, since they're row-level derivatives of a
dataset whose reuse license remains unresolved. A reader without local access to the
raw dataset can verify every number in this document through the aggregate JSON and
CSV outputs in `results/stage2/`, `results/stage1/`, and `results/sql/`, all of which
are aggregate-only and are included here.

## Explicitly excluded claims

This analysis makes no revenue, profitability, retention, market share, causal, or
time-series claims. All findings above are descriptive statistics about the sampled
listings in this single-day snapshot.
