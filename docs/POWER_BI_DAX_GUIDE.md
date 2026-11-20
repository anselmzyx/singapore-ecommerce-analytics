# Power BI DAX Guide

## Status of this document (updated 20 November 2026)

The dashboard is built. This guide began as the Stage 4 specification, written before
any measure existed, and the measure definitions below are that original specification.
Its wording was not changed when the dashboard was finished. What is known about the
final build:

1. **Original design.** The 15 core and 2 supporting measures below, with their
   validation targets taken from `results/sql/` (Stage 3).
2. **Final as-built.** The two-page report uses these measures plus three additions
   (`Store-View Shops`, `Discount Status Label`, `Sponsored Status`; see the as-built
   section at the end). The final card and chart titles differ from measure names; the
   mapping is in the as-built section.
3. **Verified independently (static, read-only).** The visual field bindings in the
   saved report definition confirm which measures and columns each visual uses. The
   displayed values in both screenshots match the Stage 3 SQL outputs.
4. **Owner-reported manual comparison.** On 20 November 2026 the project owner opened
   the PBIX in Power BI Desktop and compared six formulas against this guide:
   `Median Representative Listing Price`, `Discount Inconsistency Rate`,
   `Mean Observed Price`, `Mean Observed Price Excl. SGD 999`,
   `Testable Discount Count` and `RepresentativeRank`. All six matched the
   documented formulas. This is a manual comparison of six formulas, not an extraction
   of the whole model, and it doesn't cover the other measures.
5. **Not verified.** The formulas of the remaining measures, including the three
   as-built additions, have not been independently inspected: the compressed
   `DataModel` in the PBIX can't be read outside Power BI Desktop.
   `Median Implied Discount` is specified below, but its presence in the final model
   hasn't been confirmed. The PBIX isn't published (dataset licensing), so readers
   can't check any of this directly.

Where this guide says a measure "has not been executed" or lists a "validation
target", that is historical design wording. Read the status above for the final state.

Every "validation target" below is the already-executed SQL result from
`results/sql/` (Stage 3, corrected) that the measure is designed to reproduce.

All measures assume the single table `Observations` from `docs/POWER_BI_MODEL_GUIDE.md`.

## Percentage convention: read this before using any % measure

Two different conventions coexist in this model, and mixing them up double-multiplies
or halves a displayed percentage:

- **`discount_recorded_pct` and `discount_implied_pct` are pre-scaled 0-100** (e.g.
  `64.0` means 64%). Any measure or visual using these columns directly must use a
  **custom format string `0.0"%"`**, never Power BI's built-in Percentage format
  (which multiplies by 100 again and would display `6400.0%`).
- **Ratio measures computed here with `DIVIDE(...)`** (Discount Inconsistency Rate,
  Sponsored Listing Share) produce a genuine **0-1 proportion** and should use Power
  BI's standard **Percentage** format (which correctly multiplies by 100 for
  display).

Each measure below states which convention it uses.

## Fixed-population vs. filter-sensitive measures

- **Filter-sensitive**: responds fully to whatever slicers/visual filters are
  active (e.g. `Median Observed Price` on a Category-axis bar chart shows a
  different value per category because `category_name` is in the visual's row
  context).
- **Fixed-population / partially filter-sensitive**: `Median Representative Listing
  Price` is computed from a pre-ranked column (`RepresentativeRank`, ranked once
  over the whole table, not recomputed per filter context). Slicing by
  `source_view` restricts *which* already-ranked rows are visible; it does **not**
  re-rank within the filtered subset. See the measure's own note below.

---

### 1. Listing Observations
```
Listing Observations = COUNTROWS(Observations)
```
Observation-based. Format: Whole Number, `#,##0`. **Validation target (unfiltered):
2,996** (`results/sql/overview_totals.csv`, `overall`/`all_views` row).

### 2. Distinct Listings
```
Distinct Listings = DISTINCTCOUNT(Observations[listing_key])
```
Unique-listing-based. Format: Whole Number. **Validation target (unfiltered):
2,727.** Filtered to `source_view = "category"`: 956; `"keyword"`: 836; `"store"`:
999 (`overview_totals.csv`, `by_view` rows).

### 3. Distinct Shops
```
Distinct Shops = DISTINCTCOUNT(Observations[shop_id])
```
Unique-listing-based (shop-level). Format: Whole Number. **Validation target
(unfiltered): 968.** By view: Category 482, Keyword 543, Store 12.

### 4. Median Representative Listing Price
```
Median Representative Listing Price =
CALCULATE(
    MEDIAN(Observations[price]),
    Observations[RepresentativeRank] = 1
)
```
Fixed-population (see note above): this is a whole-dataset, one-row-per-listing
median using the documented latest-crawl-time rule. It is **not** the same as
"median price in the currently filtered view." Format: Currency, `"SGD" #,##0.00`.
**Validation target (unfiltered): SGD 12.90**, n = 2,727
(`overall_representative_price.csv`). Don't place this measure on a visual sliced by
`category_name`/`search_keyword`/`store_name` expecting it to behave like `Median
Observed Price`; use `Median Observed Price` for that instead.

### 5. Median Observed Price
```
Median Observed Price = MEDIAN(Observations[price])
```
Filter-sensitive; use this for category/store-level price visuals. Format:
Currency. **Validation targets** (filtered to `source_view = "category"`, by
`category_name`): Housekeeping 2.53, Laundry Care 3.51, Bath & Body 5.77, Softeners
8.08, Detergents 8.93, Body lotion 11.56 (`pricing_by_category.csv`).

### 6. Category Listing Count
```
Category Listing Count =
CALCULATE(
    DISTINCTCOUNT(Observations[listing_key]),
    Observations[source_view] = "category"
)
```
Unique-listing-based, scoped to the Category view. Intended for use with
`category_name` as the visual's axis/legend (category context comes from the
visual, not hardcoded). Format: Whole Number. **Validation targets:**
180/180/180/180/180/98 (the six categories). **Caveat: don't sum across categories
and call it the Category view's total distinct count.** The sum (998) double-counts
the 42 listings sampled under two categories each; the Category view's true
distinct-listing total is **956** (`category_view_distinct_total.csv`). If a KPI
card needs the view-wide total, use `Distinct Listings` filtered to `source_view =
"category"` (measure 2), not a sum of this measure across category values.

### 7. Valid Reference Price Count
```
Valid Reference Price Count =
CALCULATE(
    COUNTROWS(Observations),
    Observations[reference_price_status] = "valid"
)
```
Observation-based. Format: Whole Number. **Validation targets:** Category 998,
Keyword 999, Store 687 (`reference_price_status_by_view.csv`).

### 8. Testable Discount Count
```
Testable Discount Count =
CALCULATE(
    COUNTROWS(Observations),
    NOT ISBLANK(Observations[discount_recorded_pct]),
    NOT ISBLANK(Observations[discount_implied_pct])
)
```
Observation-based; this is the **testable** population (both values available), not
merely "recorded populated." See `docs/STAGE3_SQL_ANALYSIS.md` (Q3) for why the
distinction matters: Store's 999 recorded-populated rows include 312 untestable
sentinel-reference rows. Format: Whole Number. **Validation targets:** Category 780,
Keyword 674, **Store 687** (not 999) (`discount_testable_population.csv`).

### 9. Discount Inconsistency Rate
```
Discount Inconsistency Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Observations), Observations[discount_consistency_status] = "inconsistent"),
    [Testable Discount Count]
)
```
Produces a genuine **0-1 proportion**; format with Power BI's standard
**Percentage** format (don't also apply a `"%"` custom string, that would double
it). Safe division via `DIVIDE` returns `BLANK()` if `Testable Discount Count` is 0
(can't occur in the current data, but the slicer context could isolate an empty
subset). **Validation targets:** Category 19.2%, Keyword 10.4%, Store 0.0%
(`discount_testable_population.csv`, `pct_inconsistent_of_testable`).

### 10. Median Implied Discount
```
Median Implied Discount =
CALCULATE(
    MEDIAN(Observations[discount_implied_pct]),
    Observations[reference_price_status] = "valid"
)
```
Pre-scaled 0-100 (inherits from `discount_implied_pct`); format `0.0"%"`, **not**
Percentage format. **Validation targets:** Category 19.6%, Keyword 17.1%, Store
23.2% (`implied_discount_distribution.csv`).

### 11. Rated Observations
*(Renamed from "Rated Listing Count" in the second Stage 4 review. The calculation
is unchanged; it's still observation-based, not a distinct-listing count, so the new
name better reflects what it measures.)*
```
Rated Observations =
CALCULATE(
    COUNTROWS(Observations),
    Observations[rating] > 0
)
```
Observation-based. `rating = 0` is a "not yet rated" sentinel in this dataset
(always co-occurs with zero rating/review counts), and this measure excludes it.
Format: Whole Number. **Validation target (unfiltered): 2,713** of 2,996
(`ratings_population_overview.csv`). **Don't** substitute
`Observations[reviews_count] > 0` for this filter; they aren't the same population
(115 observations have `rating > 0` with `reviews_count = 0`).

### 12. Median Rating (Rated Only)
```
Median Rating (Rated Only) =
CALCULATE(
    MEDIAN(Observations[rating]),
    Observations[rating] > 0
)
```
Rated-only measure, filter-sensitive otherwise (responds to
`category_name`/`store_name` context). Format: Decimal Number, `0.00`.
**Validation targets:** overall 4.92; by category 4.84 (Laundry Care) to 4.93
(Softeners); by store, e.g. azren_albakri92.sg 4.94 (**not** 4.67, which was an
earlier figure that wrongly included 38 unrated listings; see
`seller_assortment.csv`, corrected).

### 13. Sponsored Listings
```
Sponsored Listings =
CALCULATE(
    COUNTROWS(Observations),
    Observations[source_view] = "keyword",
    Observations[sponsored] = TRUE
)
```
Observation-based, scoped to the Keyword view. Format: Whole Number. **Validation
target: 566** of 999 (`sponsored_overall.csv`).

### 14. Sponsored Listing Share
```
Sponsored Listing Share =
DIVIDE(
    [Sponsored Listings],
    CALCULATE(COUNTROWS(Observations), Observations[source_view] = "keyword")
)
```
Genuine 0-1 proportion, standard Percentage format. **Validation target: 56.7%**
(566/999). By `search_keyword`, use the same measure with `search_keyword` in the
visual's row context (`sponsored_by_keyword.csv` for per-keyword targets).

### 15. Listings at SGD 999
```
Listings at SGD 999 =
CALCULATE(
    DISTINCTCOUNT(Observations[listing_key]),
    Observations[price] = 999
)
```
Unique-listing-based. Format: Whole Number. **Validation target: 22** (verified to
match `DISTINCTCOUNT` on the single-table model exactly; none of these 22 listings
has a differing price in another view, so this is safe without the
unique-reference table). **Framing reminder:** this counts a *suspected*, unproven
price-ceiling pattern. Don't label any visual using this measure as "censored" or
"capped" prices; "at the SGD 999 ceiling (suspected)" is accurate, "censored
prices" is not.

---

## Supporting measures (for the Page 1 SGD-999 sensitivity panel only)

Two small additional measures, needed specifically for
`docs/POWER_BI_DASHBOARD_BUILD_GUIDE.md`'s Page 1 "Visual D" callout, not part of the
core 15 above, called out separately so the count isn't inflated artificially.

**Correction (second Stage 4 review):** both measures must be explicitly scoped to
the Category view, matching `sql/02_pricing_by_category.sql`'s
`price_999_sensitivity_overall` query, which has always computed its 15.58 / 11.62
figures over Category-view observations only (998 rows), not the whole three-view
dataset. An earlier draft of these measures omitted that filter; it's fixed below.

```
Mean Observed Price =
CALCULATE(
    AVERAGE(Observations[price]),
    Observations[source_view] = "category"
)
```
Filter-sensitive within the Category-view scope the `CALCULATE` already fixes.
Format: Currency. **Validation target: SGD 15.58**, all 998 Category-view
observations (`price_999_sensitivity_overall.csv`, `mean_price_all`).

```
Mean Observed Price Excl. SGD 999 =
CALCULATE(
    AVERAGE(Observations[price]),
    Observations[source_view] = "category",
    Observations[price] < 999
)
```
Filter-sensitive, same Category-view scope. Format: Currency. **Validation target:
SGD 11.62**, excluding the 4 Category-view observations at exactly SGD 999
(`price_999_sensitivity_overall.csv`, `mean_price_excl_999`). The roughly 25% gap
between these two measures, side by side, is the entire point of the Page 1
sensitivity panel. Within the Category view, medians barely move (see `Median
Observed Price` filtered the same two ways), but the mean is materially sensitive
to this suspected anomaly. **Both measures describe the Category-view sample only,
not an overall-marketplace or whole-dataset mean. Label them accordingly wherever
they appear.**

## Validation table (expected values under specified filter contexts)

| Measure | Filter context | Expected value | Source |
|---|---|---|---|
| Listing Observations | none | 2,996 | overview_totals.csv |
| Distinct Listings | none | 2,727 | overview_totals.csv |
| Distinct Listings | `source_view = "store"` | 999 | overview_totals.csv |
| Distinct Shops | none | 968 | overview_totals.csv |
| Median Representative Listing Price | none | SGD 12.90 | overall_representative_price.csv |
| Median Observed Price | `source_view="category"`, `category_name="Body lotion"` | SGD 11.56 | pricing_by_category.csv |
| Category Listing Count | `category_name="Housekeeping"` | 180 | pricing_by_category.csv |
| Valid Reference Price Count | `source_view="store"` | 687 | reference_price_status_by_view.csv |
| Testable Discount Count | `source_view="store"` | 687 | discount_testable_population.csv |
| Discount Inconsistency Rate | `source_view="category"` | 19.2% | discount_testable_population.csv |
| Median Implied Discount | `source_view="keyword"` | 17.1% | implied_discount_distribution.csv |
| Rated Observations | none | 2,713 | ratings_population_overview.csv |
| Median Rating (Rated Only) | `store_name="azren_albakri92.sg"` | 4.94 | seller_assortment.csv (corrected) |
| Sponsored Listings | none (Keyword view only by measure definition) | 566 | sponsored_overall.csv |
| Sponsored Listing Share | none | 56.7% | sponsored_overall.csv |
| Listings at SGD 999 | none | 22 | manual verification (see measure 15 note) |
| Mean Observed Price | (built-in filter: Category view only) | SGD 15.58 | price_999_sensitivity_overall.csv |
| Mean Observed Price Excl. SGD 999 | (built-in filter: Category view only) | SGD 11.62 | price_999_sensitivity_overall.csv |

## What could not be validated before the dashboard was built (historical note)

When this guide was written, the DAX hadn't been run. The open questions were the exact
behaviour of `RepresentativeRank` as a calculated column (whether Power BI's `EARLIER`
resolves as expected in this table), whether `DIVIDE`'s `BLANK()` handling displays as
expected in card visuals, and whether Power Query reads `sponsored` and
`variant_comparability_uncertain` as True/False. Once the dashboard was built, the
displayed KPI and chart values matched the SQL targets in both screenshots, which
resolves these for the visuals shown. The owner's manual comparison of
`RepresentativeRank` (see the status section) also found it matched this guide.

## Stage 5 as-built model additions (confirmed by Stage 6 read-only PBIX inspection)

The PBIX's compressed `DataModel` entry can't be read as text (no readable DAX
strings extractable via `strings`; no TMDL/plain-text model definition is present
in this PBIX's internal format), so the measure/calculated-column *expressions*
below aren't independently confirmed, only their *existence and binding type*, read
from the `Report/definition/pages/*/visuals/*/visual.json` query bindings (each
field reference states whether it's bound as a `Measure` or a `Column`, which is
enough to tell the two apart without opening Power BI).

**Three fields exist in the final model beyond this guide's original 15+2+1
(measures plus column):**

1. **`Store-View Shops`** (bound as `Measure`): feeds Page 2's "Store-View Shops:
   12" KPI card. It's not a relabeled `Distinct Shops`; it's a distinct,
   separately-defined measure (confirmed by its own `Property` name in the query
   binding). Presumably a store-view-filtered distinct-shop count, parallel to this
   guide's `Distinct Shops` but purpose-built rather than reusing `Distinct Shops`
   with a card-level filter as originally specified in
   `docs/POWER_BI_DASHBOARD_BUILD_GUIDE.md`.
2. **`Discount Status Label`** (bound as `Column`, a calculated column, not a
   measure): feeds the axis of Page 1's "Discount Consistency by Status" chart. It
   produces the friendly labels visible in the screenshot ("Consistent," "No
   discount recorded," "Invalid / missing reference," "Inconsistent") in place of
   the raw `discount_consistency_status` values ("consistent,"
   "no_recorded_discount," and so on).
3. **`Sponsored Status`** (bound as `Column`, a calculated column): feeds the
   legend of Page 2's "Sponsored vs Non-Sponsored by Keyword" chart. It produces
   "Sponsored"/"Non-sponsored" labels in place of the raw `sponsored` True/False
   column.

**Confirmed deviation from the build guide:** Page 1's fourth KPI card displays
`Discount Inconsistency Rate` (unfiltered, the whole-dataset 10.3% figure), not
`Listings at SGD 999` as originally specified. `Listings at SGD 999` still exists
in the model (it's bound on the private Validation page) but isn't shown as a
headline KPI on either published page.

**Final card and chart labels (display text only; the measures and their DAX are
unchanged).** Updated 20 November 2026 so pooled figures say what they pool:

| Displayed label | Measure used | Value |
|---|---|---|
| Distinct Listings | `Distinct Listings` | 2,727 |
| Distinct Shops | `Distinct Shops` | 968 |
| Median Price (All Views) | `Median Representative Listing Price` | S$12.90 |
| Discount Inconsistency (All Views) | `Discount Inconsistency Rate` | 10.3% (220 of 2,141 testable) |
| Mean Price (Category View) | `Mean Observed Price` | S$15.58 |
| Mean Price Excl. S$999 (Category View) | `Mean Observed Price Excl. SGD 999` | S$11.62 |

Chart titles: "Median Price by Category (Category View)" and "Discount Status (All Views)",
the latter with the subtitle "Mismatch among testable rows: Category 19.2% | Keyword
10.4% | Store 0.0%". The S$999 sensitivity cards deliberately cover only the four
Category-view observations at S$999; the dataset holds 24 across all three views (see
the README).

**Status of `RepresentativeRank` and `Median Implied Discount`.** Neither is bound to
any visual, so the read-only inspection of visual bindings couldn't show whether they
still exist. The owner's manual check on 20 November 2026 found `RepresentativeRank`
present and matching this guide, which is consistent with its role as a hidden column
used inside `Median Representative Listing Price`. Whether `Median Implied Discount`
still exists in the final model remains unconfirmed.
