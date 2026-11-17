# Stage 2 Data Cleaning: Shopee Singapore Listing Samples

Produced by `scripts/clean_data.py`, which reads the three original raw workbooks
directly and never modifies them. Outputs: `data/processed/listings_observations.csv`
(2,996 rows) and `data/processed/listings_unique_reference.csv` (2,727 rows), plus
`results/stage2/cleaning_validation_report.json`.

## 1. Inputs and exclusion rule

All three workbooks (`SG_Category_Data_Mon_18_Aug_2025.xlsx`,
`SG_Keyword_Data_Mon_18_Aug_2025.xlsx`, `SG_Store_Data_Mon_18_Aug_2025.xlsx`) are read
with `dtype=str` to prevent any precision loss on identifier fields, then concatenated
with a `source_view` column (`category`/`keyword`/`store`), `source_file`, and
`source_excel_row` (the original workbook's physical Excel row number, 1-indexed with
row 1 as the header) attached to every row before any filtering.

Rows lacking a non-blank `shop_id` **and** `product_id` are excluded from both cleaned
datasets (11,862 rows, all from the Keyword workbook, confirmed to match the Stage 1
count exactly). They are **not** deleted, forward-filled, or otherwise altered in the
original workbooks, which remain untouched in `data/raw/`. Their exclusion is logged in
`results/stage2/cleaning_validation_report.json` (`n_incomplete_rows_excluded`).

## 2. Column name standardisation

| Raw name(s) | Standardised name | Reason |
|---|---|---|
| `videos_count` (Category), `videos_counts` (Keyword, Store) | `videos_count` | Same field, inconsistent pluralisation across workbooks (Stage 1 finding) |
| `Keyword` (Keyword workbook only) | `search_keyword` | Avoids clashing with the literal word "keyword" used elsewhere to mean the *view* |

All other column names are kept as published (`category_name`, `category_id`,
`store_name`, `shop_locations`, `flex_name`, `media`, `seed`, `free_shipping`, and so
on), including columns that only exist in some views. Missing columns for a given view
are `NaN` after concatenation, not fabricated.

## 3. Type conversion

Converted on **identifiable rows only** (the 2,996-row set), with the original string
value preserved alongside in a `<column>_raw` field wherever a conversion was applied,
so no information is destroyed by the conversion:

- **Numeric:** `price`, `price_before_discount`, `min_price`, `max_price`, `min_mrp`,
  `max_mrp`, `rating`, `rating_count`, `reviews_count`, `reviews_image_count`, `sold`,
  `monthly_sold`, `liked_count`, `stock`, `page_number`, `rank`, `videos_count`,
  `category_id`, via `pd.to_numeric(..., errors="coerce")`. **0 conversion failures**
  across all of these columns and all 2,996 rows (verified in the validation report).
- **Boolean:** `sponsored`, `isVirtualItem`, `isSaleItemVerified`, `free_shipping`,
  mapped case-insensitively (`"TRUE"/"True"/"1"` becomes `True`, `"FALSE"/"False"/"0"`
  becomes `False`). Raw values were a mix of `"0"/"1"` (sponsored) and
  `"True"/"False"/"TRUE"/"FALSE"` (the others).
- **Datetime:** `crawl_time`, `parse_time`, via `pd.to_datetime(..., errors="coerce")`.
  **0 malformed or unparseable timestamps** among identifiable rows.
- **Text:** `title`, `brand`, `category_name`, `search_keyword`, `store_name`,
  `domain`, `currency`, `language`, `shop_locations`, whitespace-stripped only, no
  other transformation.
- **Identifiers (`shop_id`, `product_id`, `id`):** left as plain string digit
  sequences, never coerced to numeric. **Note for downstream use:** when re-reading
  `listings_observations.csv` or `listings_unique_reference.csv` with plain
  `pd.read_csv`, pandas will auto-infer `shop_id`/`product_id` as integers, because the
  file contains plain digits with no leading zeros or non-numeric characters. This is a
  read-time inference only and causes no precision loss (max observed ID length is 11
  digits, well under the 19-digit int64/float64-safe-integer boundary that originally
  motivated string-typing in Stage 1), but I'd still recommend passing
  `dtype={"shop_id": str, "product_id": str}` on read to guarantee string semantics
  downstream (as done in `notebooks/01_ecommerce_eda_public.ipynb`).

I never guessed ambiguous values. Where a transformation's correct interpretation was
unclear (for example, `discount` as a stated percentage versus a price-implied figure,
see §4), both the original and derived values are kept as separate, clearly named
columns rather than overwriting one with the other.

## 4. Price and discount handling

**Reference price sentinel.** `price_before_discount == -1` is treated as a sentinel,
not a real price, per Stage 1 findings (confirmed: 312 Store rows, 0 rows in any other
view). A `reference_price_status` column records one of: `valid`, `sentinel_invalid`
(the -1 case), `missing`, or `invalid_nonpositive` (none observed: 0 rows had a
non-positive, non-sentinel reference price).

**Five explicitly separate discount dimensions**, none folded into a single combined
field:

1. `discount_recorded_pct`: the stated `discount` field, parsed from its original
   `"NN%"` text, kept exactly as published.
2. `discount_implied_pct`: `(1 − price / price_before_discount) × 100`, computed only
   where `reference_price_status == "valid"` and `price` is present, and `NaN`
   otherwise. **Never used to overwrite `discount_recorded_pct`.**
3. `discount_consistency_status`: one of `consistent` (|recorded minus implied| ≤ 1
   percentage point), `inconsistent` (more than 1 point apart), `no_recorded_discount`
   (recorded blank, implied available), `invalid_or_missing_reference_price` (implied
   not computable), or `no_recorded_and_no_valid_reference` (neither available).
4. `reference_price_status` (see above): a missing or invalid reference price is
   tracked separately from consistency, since an invalid reference price is not itself
   a disagreement.
5. `variant_comparability_uncertain`: `True` whenever `min_price != max_price` or
   `min_mrp != max_mrp` for that row, flagging that the recorded price may span
   multiple pack sizes or variants, so a discount or price comparison for that row may
   not be comparing like for like. **A `consistent` discount status doesn't imply a
   genuine, comparable promotional saving** when this flag is also `True`. The two are
   reported separately and need to be read together, not substituted for one another.

Validation counts (from `results/stage2/cleaning_validation_report.json`): 2,684 of
2,996 rows (89.6%) have a valid reference price. Of those, 1,921 are `consistent` and
220 are `inconsistent`. 543 rows have no recorded discount at all, and 312 rows (all
Store sentinels) fall under `invalid_or_missing_reference_price`. 1,091 of 2,996 rows
(36.4%) are flagged `variant_comparability_uncertain`.

**New finding during cleaning:** 24 observations (22 distinct listings) record a
`price` of exactly 999, with **zero** observations priced between 900 and 998. This gap
pattern is consistent with a platform- or crawler-side display or storage ceiling at
999, but **this is a suspected anomaly, not a proven one** (a framing I corrected
during Stage 3 review). A coincidental price clustering at exactly 999 can't be ruled
out from this data alone, and the true price for these rows shouldn't be assumed to be
999 or higher. No value is altered. `sql/02_pricing_by_category.sql` includes a
sensitivity check (category pricing computed with and without these rows) so
downstream analysis can see the effect either way rather than relying on an unproven
assumption.

## 5. Stable listing key

`listing_key = domain + "|" + shop_id + "|" + product_id` (domain is constant,
`SHOPEE.SG`, across the dataset). This is the composite key used to deduplicate across
views in the unique-listing reference table.

## 6. Repeated observations and source-view context

- `is_repeated_within_view` flags rows whose `(source_view, shop_id, product_id)`
  repeats within the same workbook (42 Category, 163 Keyword, 0 Store rows, matching
  Stage 1 exactly). These are **not** removed from `listings_observations.csv`.
  Repeats are kept because they can carry different `category_name`, `search_keyword`,
  page, or rank context.
- `listings_observations.csv` is therefore an **observation-level** table: 2,996 rows,
  one per identifiable physical row, with full view, category, keyword, and store
  context preserved and never collapsed.
- `listings_unique_reference.csv` is a **listing-level** table: exactly 2,727 rows, one
  per distinct `listing_key`, built to support KPIs that shouldn't double-count a
  listing appearing in more than one view. It records `views_present`
  (comma-separated list), `n_observations` (total rows contributing to this key across
  all views), `price_category`/`price_keyword`/`price_store` (the first recorded price
  for that key in each view where present), `price_min_across_views`,
  `price_max_across_views`, and `cross_view_price_conflict` (`True` when the price
  differs by more than SGD 0.005 across views for the same listing).
- **Categories and keywords are not treated as mutually exclusive product groups.** A
  listing can legitimately appear under one category and also match a different
  keyword search, or appear in the Store view too. The `views_present` column in
  `listings_unique_reference.csv` makes this overlap explicit rather than assuming
  exclusivity.
- **Cross-view price disagreement, investigated and preserved, not resolved:** of the
  63 listing keys appearing in more than one view, 9 (14.3%) have
  `cross_view_price_conflict == True`, ranging from 1.8% to 12.5% apart, all between
  Store and either Category or Keyword. This lines up with a gap between when Store was
  crawled and when Category and Keyword were crawled (see `docs/STAGE1_DATASET_REVIEW.md`
  §2). No price is treated as more "correct" than another. Every view-specific price
  is retained in `listings_observations.csv` and the per-view columns of
  `listings_unique_reference.csv`.

## 7. What was deliberately not done

- No forward-filling of missing identifiers, prices, or any other analytical field.
- No fabrication or interpolation of any missing value.
- No overwriting of the recorded `discount` field with the implied calculation.
- No assumption that a matching recorded and implied discount proves a genuine,
  comparable promotional saving.
- No deduplication that would discard view-specific context (category, keyword query,
  store handle, page/rank). Repeats are flagged, not removed.
- No unnecessary additional tables beyond the two described above.

## 8. Reproducing this stage

```
source .venv/bin/activate
python scripts/clean_data.py
```

Re-running recomputes the raw-file SHA-256 checksums against the values recorded in
`results/stage1/file_inventory.json` and raises an error if any raw file has changed,
before producing identical output given identical inputs.
