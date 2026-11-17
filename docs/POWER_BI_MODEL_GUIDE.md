# Power BI Model Guide: Stage 4

Preparation only. No PBIX/PBIP file has been created, and Power BI has not been opened
as part of this stage. This guide is for manual construction in Stage 5.

## Model shape: single table, no relationships

**Decision:** import only `data/processed/listings_observations.csv` as one table
named `Observations`. `data/processed/listings_unique_reference.csv` is **not**
imported.

**Why a single table is sufficient here:** every measure needed for the two dashboard
pages (coverage, pricing, discount validity, seller assortment, ratings, sponsored
composition) can be computed from `Observations` alone, using
`DISTINCTCOUNT(listing_key)` for unique-listing counts and view-scoped filters for
Category/Keyword/Store-specific visuals. `listings_unique_reference.csv` exists to
support the cross-view price-conflict analysis (Stage 3 Q7), which isn't a required
visual on either page (the page briefs cover assortment, pricing, discounts, ratings,
and sponsorship, not cross-view reconciliation). Importing it anyway would require a
`listing_key` relationship whose join behavior needs care: an
`Observations`-to-`UniqueListings` many-to-one relationship isn't inherently
ambiguous, but it adds a table, a relationship, and filter-direction decisions that
buy nothing for the two specified pages. If Stage 5 or later adds a
cross-view-conflict visual, that decision can be revisited then rather than importing
it speculatively now.

**Representative listing price** (the one summary figure needing a single value per
listing, per the Stage 3 correction) is computed **within** `Observations` via a
calculated column (below), not via the second table's pre-computed
`price_min_across_views`/pivoted columns. This keeps the model to one table while
still using the documented latest-crawl-time rule.

## File to import

`data/processed/listings_observations.csv`, via Power Query, **Get Data > Text/CSV**,
then **Choose Columns** (Transform/Manage Columns) to import only the columns below.
The full file has 76 columns (many `_raw` precision-preserving duplicates and fields
not used in any specified visual, such as `sold`/`monthly_sold`, which are
deliberately **not** imported at all; see the rationale below). Importing only what's
needed keeps the model lean and prevents fields that shouldn't be charted (sales
counters) from ever appearing in the field list.

## Columns to import (17 of 76)

| Column | Power Query type | Report visibility | Notes |
|---|---|---|---|
| `listing_key` | Text | **Hide** | Used by `DISTINCTCOUNT` measures and the representative-price ranking column only |
| `source_view` | Text | Visible | Values: `category`, `keyword`, `store`; primary slicer field |
| `shop_id` | Text | **Hide** | Used by `DISTINCTCOUNT` measures only |
| `category_name` | Text | Visible | Populated only where `source_view = "category"`; **blank string** (not null) elsewhere |
| `search_keyword` | Text | Visible | Populated only where `source_view = "keyword"`; blank string elsewhere |
| `store_name` | Text | Visible | Populated only where `source_view = "store"`; blank string elsewhere |
| `price` | Decimal Number | Visible | Format: Currency, `SGD #,##0.00` |
| `discount_recorded_pct` | Decimal Number | Visible | **0-100 scale** (e.g. `64.0` means 64%), not 0-1 |
| `discount_implied_pct` | Decimal Number | Visible | **0-100 scale**, same convention |
| `discount_consistency_status` | Text | Visible | Values: `consistent`, `inconsistent`, `no_recorded_discount`, `invalid_or_missing_reference_price`, `no_recorded_and_no_valid_reference` |
| `reference_price_status` | Text | Visible | Values: `valid`, `sentinel_invalid`, `missing`, `invalid_nonpositive` |
| `rating` | Decimal Number | Visible | `0` means "not yet rated," not a genuine 0-star score; see DAX guide |
| `reviews_count` | Whole Number | Visible | |
| `sponsored` | True/False | Visible | Stored as text `"True"`/`"False"` in the CSV; set the type explicitly to **True/False** in Power Query (don't rely on auto-detect) |
| `variant_comparability_uncertain` | True/False | Visible | Same type-setting note as `sponsored` |
| `crawl_time` | Date/Time | **Hide** | Needed only for the representative-price ranking column; hidden so it doesn't invite a time-series visual (this is a single-day snapshot, not a time series) |
| `source_excel_row` | Whole Number | **Hide** | Deterministic tiebreak for representative-price ranking (never actually exercised; no ties exist in this dataset, verified in `sql/01_marketplace_overview.sql`) |

**Intentionally excluded from import** (not needed for any specified visual, and in
the case of `sold`/`monthly_sold`, excluded specifically to prevent a
revenue-implying chart from being built by mistake): `price_before_discount`,
`min_price`, `max_price`, `min_mrp`, `max_mrp`, `brand`, `title`, `url`,
`source_url`, `domain`, `currency`, `language`, `media`, `flex_name`, `seed`,
`shop_locations`, `free_shipping`, `isVirtualItem`, `isSaleItemVerified`,
`liked_count`, `stock`, `monthly_sold`, `sold`, `rating_count`,
`reviews_image_count`, `videos_count`, `category_id`, `page_number`, `rank`, `id`,
`parse_time`, `is_repeated_within_view`, and all `*_raw` columns.

## Calculated column

One calculated column, needed to support the representative-listing-price measure
(see `docs/POWER_BI_DAX_GUIDE.md`):

```
RepresentativeRank =
RANKX(
    FILTER(Observations, Observations[listing_key] = EARLIER(Observations[listing_key])),
    Observations[crawl_time],
    ,
    DESC
)
```

This ranks each listing's observations by `crawl_time` descending within that
`listing_key`. Rank 1 is the latest-crawl-time observation, matching
`sql/01_marketplace_overview.sql`'s `overall_representative_price` rule exactly. No
tiebreak column is needed in the DAX, because the underlying data has zero ties
(verified during Stage 3 SQL preparation). If a future data refresh introduces one,
`RANKX` would assign the same rank to tied rows, which would very slightly inflate a
`COUNTROWS`-style check; the `DISTINCTCOUNT(listing_key)`-based measures are
unaffected either way. Hide this column from the report view, since it's a plumbing
column, not something to chart.

## No other relationships, no other tables

A single flat table has no relationship cardinality, filter-direction, or ambiguity
concerns to document. If a later stage adds the `listings_unique_reference.csv` table
for a cross-view analysis page, the relationship would be `Observations[listing_key]`
(many) to `UniqueListings[listing_key]` (one), with single-direction filtering from
`UniqueListings` to `Observations`. This is documented here for forward reference
only and wasn't implemented in Stage 4.

## Date/numeric formatting summary

- `price`: Currency, `"SGD" #,##0.00`
- `discount_recorded_pct`, `discount_implied_pct`: Decimal Number, `0.0` with a
  literal `%` suffix added via a custom format string (`0.0"%"`). **Don't** apply
  Power BI's built-in Percentage format, which would multiply the already-0-100 value
  by 100 again (see the DAX guide's "percentage convention" note).
- `rating`: Decimal Number, `0.00`
- `reviews_count`: Whole Number, `#,##0`
- `crawl_time`: not display-formatted (hidden column)

## Fields to hide, summary

`listing_key`, `shop_id`, `crawl_time`, `source_excel_row`, `RepresentativeRank`. All
are plumbing fields used only inside measures or the ranking column, and none should
be dragged directly into a visual.
