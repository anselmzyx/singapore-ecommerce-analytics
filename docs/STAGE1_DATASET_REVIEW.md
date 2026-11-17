# Stage 1 Dataset Review — Shopee Singapore Listing Samples (August 2025)

Status: Stage 1 — Dataset Acquisition, Evaluation & Inspection only. No cleaning, EDA, SQL,
Power BI, or GitHub publication has occurred.

## 1. Publisher and Provenance

- **Kaggle dataset:** `johnphamed/shopee-singapore-listing-samples-august-2025`
- **Kaggle owner/display name:** Easy Data (Kaggle username `johnphamed`)
- **Kaggle URL:** https://www.kaggle.com/datasets/johnphamed/shopee-singapore-listing-samples-august-2025
- **Original publisher documentation (GitHub):** https://github.com/JohnPham-easydata/Shopee-Dataset
- **Linked Google Drive folder (publisher-referenced, not used for acquisition):**
  https://drive.google.com/drive/folders/14f9Uj9D5uG7gEw2r6YEnUYGz7EC1HueD
- **Kaggle dataset version:** Version 1 (1.57 MB), "Updated a month ago" as shown on the
  Kaggle page at review time (2026-11-16).
- **Kaggle usability score:** 3.53
- **Kaggle tags:** Business, Retail and Shopping

The dataset is explicitly marketed on Kaggle as "Historical Shopee Singapore listing samples
from 18 August 2025... Three Excel workbooks capture store, keyword and category views."
This is a **retrospective snapshot**, not a live feed. The Kaggle "Updated a month ago" date
reflects when the listing was last touched on Kaggle, not a fresh crawl.

## 2. Dataset Dates and Coverage

- All identifiable rows across all three workbooks record `domain = SHOPEE.SG`,
  `currency = SGD`, and crawl/parse timestamps on **2025-08-18** (Mon 18 Aug 2025).
  - **`crawl_time` range differs by view** (corrected from an earlier Store-only
    description — see `docs/STAGE1_CORRECTIONS_ADDENDUM.md` §C): Category
    00:21:24–00:24:58; Keyword 02:34:39–03:10:05; Store 18:43:09–18:47:02. The three
    views were not all crawled in the same short window — each view's crawl itself was a
    brief (~4-minute) burst, but the three bursts were spread across the day.
  - `parse_time` range (all views): 2025-08-18 18:10:42 – 19:46:52, several hours after
    Category's and Keyword's crawl bursts and close to Store's own crawl burst — which is
    why only the Store view shows rows where `parse_time` precedes `crawl_time` (§5).
  - Timezone is not documented by the publisher.
  - No malformed/unparseable timestamp values were found in `crawl_time` or `parse_time`
    among identifiable rows in any view.
- Coverage is **Singapore only**, **Shopee only**, **a single calendar day**. No other
  country, marketplace, or collection period is present or should be merged in per the
  project brief.
- Category coverage is narrow: six personal-care/household categories (Laundry Care,
  Housekeeping, Detergents, Softeners, Bath & Body, Body lotion) in the Category view, and
  17 personal-care/household search terms in the Keyword view. This is **not** a general
  marketplace sample — see §7 (selection bias).

## 3. File Inventory

Downloaded manually via the Kaggle web UI (Kaggle CLI was available locally but no API
token was configured on this machine; the user authorized manual browser download instead
of setting up credentials). Original archive and workbooks preserved unchanged in
`data/raw/`.

| File | Format | Size (bytes) | SHA-256 |
|---|---|---|---|
| `shopee_sg_listing_samples_aug2025.zip` | ZIP | 1,556,790 | `6b4e85517f235ceb1a7bdd411977b314be461c64e116bb6fa477f665ee1880da` |
| `SG_Category_Data_Mon_18_Aug_2025.xlsx` | XLSX | 412,133 | `ba8c8cb8142dea8b5355796c7f20aa527e566505bc28bb5fc2f9681276a81003` |
| `SG_Keyword_Data_Mon_18_Aug_2025.xlsx` | XLSX | 809,641 | `e4726104138d37c55603bc4feda8cd375cf64220afbd6a3b9d3665e804102406` |
| `SG_Store_Data_Mon_18_Aug_2025.xlsx` | XLSX | 347,185 | `b9f7f229b8c5c3a1570175d3af6afb674e43af28cd4fe2cacad0295cab7cf006` |

(Full, unambiguous checksums are also recorded in `results/stage1/file_inventory.json`.)

- Download date: 2026-11-16.
- Each workbook contains exactly one worksheet, `Sheet1`.
- Total: 114 columns across the three workbooks combined (38 + 39 + 37), per the Kaggle
  page summary — confirmed against the actual files in §4.

## 4. Actual Schema and Independently Verified Counts

All figures below were computed directly from the three XLSX files using
`scripts/inspect_dataset.py` (not copied from the publisher's claims) and cross-checked
against the publisher's Kaggle page text. **Every headline figure the publisher reports was
independently reproduced from the raw files.**

### 4.1 Physical rows vs. identifiable observations

| View | Physical rows | Identifiable observations (shop_id & product_id present) | Incomplete rows |
|---|---|---|---|
| Category | 998 | 998 | 0 |
| Keyword | 12,861 | 999 | **11,862** |
| Store | 999 | 999 | 0 |
| **Total** | 14,858 | **2,996** | 11,862 |

This confirms the publisher's claim of 2,996 identifiable observations and the Keyword
view's 11,862 incomplete rows **exactly**.

The 11,862 incomplete Keyword rows (Excel rows 1001–12862) contain non-null values in
**only seven columns**: `free_shipping`, `rating`, `rating_count`, `reviews_count`,
`reviews_image_count`, `isVirtualItem`, `isSaleItemVerified`. They have no `shop_id`,
`product_id`, `title`, `source_url`, `currency`, or timestamp fields, and were **not**
forward-filled or merged with any other row — they remain untouched in the original file
and were excluded from every count above, per the project brief.

### 4.2 Distinct listing keys and shops (per view)

| View | Distinct shop_id/product_id pairs | Distinct shops | Repeated rows within view | Repeated pairs with conflicting price |
|---|---|---|---|---|
| Category | 956 | 482 | 42 | 0 |
| Keyword | 836 | 543 | 163 | 0 |
| Store | 999 | 12 | 0 | 0 |

No repeated listing (within any view) was found with a conflicting `price` across its
repeated appearances — repeats represent the same listing captured under multiple
categories/keywords/pages in the same ~4-minute crawl window, not independent re-samples.

### 4.3 Cross-view totals and overlap

| Metric | Value |
|---|---|
| Sum of identifiable observations across views | 2,996 |
| **Union** of distinct shop_id/product_id pairs across all views | **2,727** |
| **Union** of distinct shops across all views | **968** |
| Overlap: Category ∩ Keyword | 42 |
| Overlap: Category ∩ Store | 17 |
| Overlap: Keyword ∩ Store | 6 |
| Overlap: all three views | 1 |

This exactly matches the publisher's reported 2,996 observations / 2,727 shop-product pairs
/ 968 shops, and the reported view-intersection counts. **The publisher's per-view counts
(998/999/999 identifiable; 956/836/999 distinct pairs; 482/543/12 shops) are also
independently confirmed from the raw files** (see `results/stage1/key_counts.csv`).

Per the project brief, **workbook distinct-pair counts were not summed** to estimate a
combined total — the union was computed directly on the pair sets, which is the correct
way to avoid double-counting shared listings.

### 4.4 Columns per view

- **Category (38 columns):** `language, page_number, rank, id, seed, source_url,
  sponsored, url, videos_count, domain, flex_name, media, category_name, product_id,
  shop_id, title, currency, stock, crawl_time, parse_time, monthly_sold, sold,
  liked_count, category_id, brand, price, price_before_discount, min_price, max_price,
  min_mrp, max_mrp, discount, rating, rating_count, reviews_image_count, reviews_count,
  isVirtualItem, isSaleItemVerified`
- **Keyword (39 columns):** as above, plus `Keyword` (capitalized, the search query) and
  `shop_locations` and `free_shipping`; column is spelled `videos_counts` (plural) here,
  vs. `videos_count` (singular) in Category — a schema-alignment issue to handle
  explicitly in any later stage, not during Stage 1.
- **Store (37 columns):** similar to Category but adds `store_name`, lacks
  `category_name`, `isVirtualItem`, and `free_shipping`; also uses `videos_counts`
  (plural).

All identifier fields (`shop_id`, `product_id`, `id`) were loaded and retained as strings
throughout to avoid floating-point precision loss, per the project brief. `id` is a
per-row/result identifier (not stable across views); `shop_id` + `product_id` (+ `domain`,
constant here) is the usable composite listing key, consistent with the publisher's field
guide. This composite key was present and populated consistently across the three
collection views whenever `shop_id`/`product_id` were non-null.

### 4.5 Missing values

Full per-column missing-value counts and percentages for all three views are in
`results/stage1/column_profiles.csv`. Headline findings:

- `brand` is missing in 370/998 Category rows (37.1%), 395/999 Keyword rows (39.5%), and
  64/999 Store rows (6.4%) — all exactly matching the publisher's reported figures.
- `seed` is blank (100% missing) across all three workbooks, confirming the publisher's
  note.
- No other core identifying or pricing field (`shop_id`, `product_id`, `price`,
  `price_before_discount`) has missing values among identifiable rows.

## 5. Data-Quality Findings

All of the following were computed independently from the raw files, not assumed from the
publisher's description.

1. **Headline counts (2,996 / 2,727 / 968) — CONFIRMED** (§4.1–4.3).
2. **View-level identifiable counts (998 / 999 / 999) — CONFIRMED** (§4.1).
3. **11,862 incomplete Keyword rows — CONFIRMED**, and their field content (only the 7
   trailing engagement columns) matches the publisher's description exactly (§4.1).
4. **312 Store `price_before_discount == -1` — CONFIRMED.** These 312 rows all carry
   `discount = "0%"`, consistent with the reference price being an unusable sentinel
   rather than a real pre-discount price. These rows must be excluded from any discount
   calculation, as the project brief requires.
5. **39 Store rows with `parse_time` earlier than `crawl_time` — CONFIRMED.** This affects
   only the Store view; `parse_time` spans a wider window (18:11:40–19:10:09) than
   `crawl_time` (18:43:09–18:47:02), suggesting parsing happened asynchronously from
   crawling and the two timestamps cannot be used to infer a reliable processing duration.
6. **Prices:** no zero, negative, or missing `price` values in any view among identifiable
   rows (excluding the Store `-1` sentinel on `price_before_discount`, which is a
   reference-price field, not the transaction price). Price ranges from SGD 0.10–999.00
   across views; `min_price`/`max_price`/`min_mrp`/`max_mrp` fields exist and suggest
   product variants with a price range, which must be accounted for before any
   price-comparison claim (per the project brief).
7. **Discount field is present but partially populated and not always internally
   consistent** *(percentages corrected during Stage 2 review — see
   `docs/STAGE1_CORRECTIONS_ADDENDUM.md` §A; raw counts unchanged)*:
   - Category: populated in 780/998 rows (78.2%); of those **780 populated rows, 150
     (19.2%)** have a stated discount % that differs by more than 1 percentage point
     from the value implied by `1 − price/price_before_discount`.
   - Keyword: populated in 674/999 rows (67.5%); of those **674 populated rows, 70
     (10.4%)** show the same >1pt discrepancy.
   - Store: populated in 999/999 rows (100%, including "0%" for the 312 sentinel rows);
     **0 of 999 (0.0%)** rows show a >1pt discrepancy.
   - **Conclusion:** the stated `discount` field cannot be assumed reliable without
     cross-checking against `price`/`price_before_discount`, and is only usable where both
     price fields are non-sentinel and variant-comparable, confirming the project brief's
     caution against assuming discount calculability.
8. **Rating/review fields** (`rating`, `rating_count`, `reviews_count`,
   `reviews_image_count`) are 100% populated among identifiable rows in all three views —
   usable, but these are source-reported counters, not independently validated.
9. **`sold` / `monthly_sold` counters** are present and fully populated in all views
   (`sold` ranges roughly 0–229,144; `monthly_sold` 0–4,505), but per the project brief
   these are **platform-displayed counters, not audited transactions, revenue, or a
   documented monthly period**, and must not be treated as such.
10. **Category/keyword selection bias — CONFIRMED and material.** The Category view is
    limited to 6 household/personal-care categories (180 rows each, except Body lotion at
    98). The Keyword view is limited to 17 personal-care/household search terms (60 rows
    each, except "body lotion" at 39), of which 566/999 (56.7%) are flagged
    `sponsored = 1`. **This dataset is a narrow, curated personal-care/household sample,
    not a representative cross-category marketplace sample**, and any business conclusion
    must be scoped accordingly.
11. **No duplicate listings with conflicting prices** were found within any view (§4.2).
12. **Cross-view price conflicts (new finding, added during Stage 2 review — see
    `docs/STAGE1_CORRECTIONS_ADDENDUM.md` §C).** Of the 63 shop_id/product_id pairs that
    appear in more than one collection view, **9 (14.3%) carry a different recorded
    `price` depending on which view recorded it**, differing by 1.8%–12.5%. All 9
    conflicts involve the Store view paired with either Category or Keyword; no
    Category/Keyword pair conflicts. This is consistent with Store's crawl burst
    occurring roughly 15–18 hours after Category's and Keyword's (finding 2 below) —
    i.e., some prices appear to have genuinely changed between crawl bursts on the same
    day. **Implication for later stages:** `price` must be treated as a view- and
    time-specific point observation, not a single canonical "current price" per listing.
13. **Column-level missingness denominators (clarification added during Stage 2
    review — see `docs/STAGE1_CORRECTIONS_ADDENDUM.md` §B).** The machine-readable
    `results/stage1/column_profiles.csv` now reports missing-value rates separately for
    "whole_workbook" (all physical rows, including the Keyword view's 11,862 incomplete
    rows) and "identifiable_rows" (identifiable rows only) populations, to prevent the
    two from being read interchangeably — they can differ by 50+ percentage points for
    the Keyword workbook specifically, because the incomplete rows are missing nearly
    every column by construction.

No original rows were modified, removed, or forward-filled during this inspection, per the
project brief.

## 6. Licensing and Publication Findings

- **Kaggle license field:** displays as **"Unknown"** on the dataset's Kaggle metadata
  panel (confirmed directly from the live Kaggle page on 2026-11-16, not inferred).
- **Dataset owner:** Easy Data (Kaggle account `johnphamed`).
- **Original source URLs:** Kaggle dataset page (above); publisher GitHub documentation
  at `github.com/JohnPham-easydata/Shopee-Dataset`; a publisher-linked Google Drive folder
  (not accessed, not used for acquisition).
- **Publisher's own reuse statement (quoted from the Kaggle page, "Attribution and reuse"
  section):** *"Cite Easy Data, the dataset title, observation date and Kaggle version
  used. Reuse licensing is not specified; public availability does not establish
  unrestricted reuse rights."* The linked GitHub repository states the same position in
  substance.
- **No explicit redistribution right is established** for either the raw workbooks or any
  processed/derived listing-level file. Kaggle's "Unknown" license designation and the
  publisher's own text both point the same direction: public visibility and downloadability
  on Kaggle does **not** imply a right to redistribute the files or derived data publicly.
- **Recommendation:** Keep the raw workbooks (`data/raw/`), any processed/cleaned
  listing-level files produced in a later stage, and any Power BI `.pbix` file that embeds
  the source rows **out of the public GitHub repository** until explicit permission is
  obtained from Easy Data / the Kaggle account owner. Aggregate, non-identifying summary
  statistics, charts, and narrative findings (not row-level data) are lower-risk for public
  write-up, but this is a risk-reduction recommendation, not a legal clearance — this is
  not legal advice, and no legal assurance is made here.
- Images, listing text (titles), and other listing-level content are part of the same
  unresolved-rights dataset and should be treated with the same restriction.

## 7. Analytical Suitability Assessment

| Area | Supporting columns | Sample adequacy | Main limitations | Verdict |
|---|---|---|---|---|
| **A. Listing price distributions & product-group comparisons** | `price`, `min_price`/`max_price`, `min_mrp`/`max_mrp`, `category_name` (Category view only), `Keyword` (Keyword view) | Adequate within the 6 categories / 17 keywords sampled (956–999 distinct listings per view) | Limited to a narrow personal-care/household slice (§5.10); price ranges imply variants that must be reconciled before comparing "a price" | **Retain, but narrow scope explicitly to the sampled categories/keywords — do not generalize to "Singapore e-commerce prices" broadly** |
| **B. Valid recorded discount comparisons** | `discount`, `price`, `price_before_discount` | Discount field only 67–100% populated depending on view; Store's 312 `-1` sentinels must be excluded | Discount field disagrees with implied discount in 70–150 rows per view (§5.7); variant/pack-size differences not reconciled | **Narrow: only usable after excluding sentinel/missing rows and validating against price fields row-by-row; do not treat the raw `discount` column as ground truth** |
| **C. Seller assortment & price positioning** | `shop_id`, `store_name` (Store view), `category_name`/`Keyword`, `price` | Store view has only 12 distinct shops (999 listings) — a very shallow seller sample; Category/Keyword views have 482/543 shops but each shop likely has very few listings each (956/836 pairs ÷ 482/543 shops) | Seller-level patterns from 12 stores, or from shops with 1–2 listings each, are not statistically robust | **Narrow to descriptive, illustrative seller comparisons only — explicitly avoid claiming representative "seller strategy" conclusions** |
| **D. Rating and review comparisons** | `rating`, `rating_count`, `reviews_count`, `reviews_image_count` | Fully populated (100%) in all three views | Fields are source-reported counters, not independently audited; no verification of review authenticity or recency | **Retain for descriptive comparison of recorded ratings within the sampled categories; do not claim verified customer satisfaction** |
| **E. Commercially meaningful seller recommendations** | Combination of price, discount, rating, `sold`/`monthly_sold`, assortment fields | Single-day, 12-shop (Store view) or shallow-assortment (Category/Keyword) snapshot | No time series, no revenue/profitability data, no causal structure, narrow category scope, unverified counters | **Reject as a standalone business-recommendation claim; retain only as an illustrative/portfolio-style descriptive exercise, explicitly labeled as such** |

**Explicitly excluded** from any later-stage analysis, per the project brief: revenue,
profitability, retention, market share, causal claims, and time-series claims. This dataset
is a single-day cross-sectional sample and cannot support any of these.

## 8. Limitations Summary

- Narrow, curated category/keyword scope (personal-care/household only) — not a general
  marketplace sample.
- Single calendar day (2025-08-18), ~4-minute crawl window — no temporal variation.
- Store view has only 12 distinct shops — too shallow for seller-strategy generalization.
- `discount` field is unreliable in 7–15% of populated rows per view and must be
  recalculated/validated, not taken at face value.
- `sold`/`monthly_sold` are unverified platform counters.
- `brand` missing in 6–40% of rows depending on view.
- Minor schema inconsistency (`videos_count` vs `videos_counts`) across workbooks.
- Licensing status is unresolved ("Unknown" on Kaggle; publisher disclaims reuse rights).

## 9. Final Recommendation

## **CONDITIONAL GO**

The dataset is internally consistent, independently verifiable (every publisher-reported
figure reproduced exactly from the raw files), SGD-denominated, Singapore-only, and
single-collection-period as claimed. It can support **narrowly scoped, descriptive**
listing-price, discount-validity, and rating comparisons within the 6 sampled categories /
17 sampled keywords / 12 sampled stores, framed explicitly as a portfolio-style descriptive
analysis of a curated sample — not as a general-marketplace, seller-strategy, or
revenue/profitability study.

Conditions before proceeding to later stages:
1. Treat Category, Keyword, and Store as three distinct, overlapping views — do not
   silently merge or deduplicate across views without preserving view context.
2. Exclude the 11,862 incomplete Keyword rows from any listing-level analysis (already
   excluded here); do not forward-fill their missing identifiers.
3. Exclude or flag the 312 Store `price_before_discount = -1` sentinel rows before any
   discount calculation.
4. Validate `discount` against `price`/`price_before_discount` row-by-row rather than
   trusting the stored field.
5. Do not publish raw or processed row-level data, or any Power BI file embedding it, to
   the public GitHub repository until explicit reuse permission is obtained from Easy Data
   (§6).
6. Frame all findings as applying to the sampled categories/keywords/stores only — never
   as general Singapore e-commerce market claims.

Stage 1 is complete. Do not proceed to Stage 2 (cleaning), EDA, SQL analysis, Power BI
development, or GitHub publication without separate authorization.
