# Power BI Dashboard Build Guide: Stage 4

Preparation only. No PBIX/PBIP has been created and the dashboard has not been
built. This is a manual-construction plan for Stage 5. Canvas: **2560 x 1440 px
(16:9 QHD)** for both pages. All coordinates are suggested starting positions, not
pixel-exact requirements. Adjust to taste during construction while keeping the
grouping logic (KPI row, then visuals) intact.

**Standing caveats to carry onto every visual on both pages** (state in a small
footer text box on each page, 11pt italic, see the Typography section below,
bottom-left, e.g. `x=40, y=1390, w=1400, h=40`):
*"Shopee Singapore sample, 18 Aug 2025 only, not the full marketplace. `price` is a
listing-price observation, not a verified transaction. `rating`/`reviews_count` are
platform-reported counters, not audited satisfaction or sales."*

---

## Page 1: "Product Pricing & Promotions"

### Title
Text box, `x=40, y=20, w=1600, h=60`, 32pt bold: **"Product Pricing & Promotions"**
Subtitle text box directly below, `x=40, y=82, w=1600, h=35`, 16pt regular:
*"Shopee Singapore sample, 18 August 2025: Category, Keyword & Store views"*

### KPI card row (`y=120, h=140`)
Four Card visuals, each `w=580`, 20px gaps, starting `x=40`:

| # | x | Measure | Label override | Format note |
|---|---|---|---|---|
| 1 | 40 | `Distinct Listings` | "Distinct Listings (All Views)" | Whole number |
| 2 | 640 | `Distinct Shops` | "Distinct Shops" | Whole number |
| 3 | 1240 | `Median Representative Listing Price` | "Median Listing Price (Representative)" | Currency SGD |
| 4 | 1840 | `Listings at SGD 999` | "Listings at SGD 999 (suspected ceiling)" | Whole number; set card's conditional subtitle/tooltip text to "unproven, not confirmed censoring" |

No visual-level filters on the KPI row; these are whole-dataset figures. See the
"Edit Interactions (Page 1)" table below for the full set of required interaction
settings that keep these cards fixed regardless of what's selected elsewhere on the
page.

### Slicer: Category (`x=40, y=280, w=380, h=460`)
Field: `category_name`. **Visual-level filter: `source_view = "category"`** (so
only the 6 real category names appear, never a blank entry from the other two
views). Type: List, **multi-select enabled** (so the user can compare two or more
categories at once), with **"Select All" enabled** as the default selection
state, both set in the slicer's **Format > Selection controls** pane. Title:
**"Filter: Category"**. Applies only to the Category Pricing visual below (edit
interactions on every other visual on this page to set this slicer's effect to
**None**; see the Edit Interactions section below).

### Visual A: Median Price by Category
`x=440, y=280, w=1000, h=460`. **Clustered bar chart** (horizontal).
- Axis: `category_name`
- Values: `Median Observed Price`
- Visual-level filter: `source_view = "category"`
- Sort: by `Median Observed Price`, ascending (cheapest category at top)
- Data labels on: `"SGD" #,##0.00`
- Title: **"Median Price by Category (Category View, n=998 obs / 956 distinct listings)"**
- Tooltip: add `Category Listing Count` so hovering shows the listing count behind
  each bar
- Caveat text box beneath chart (`h=30`): *"Categories aren't mutually exclusive:
  42 listings are sampled under two categories, so summing these counts
  overstates the view-wide distinct total (956)."*

### Visual B: Observations vs. Distinct Listings by View
`x=1480, y=280, w=1040, h=460`. **Clustered column chart**.
- Axis: `source_view`
- Values: `Listing Observations`, `Distinct Listings` (two series)
- No visual-level filter (all three views shown)
- Sort: axis in fixed order `category, keyword, store` (use a sort-by-column
  workaround if needed, or manually reorder via "Sort axis")
- Data labels on
- Title: **"Observations vs. Distinct Listings by Collection View"**
- Caveat tooltip/footer: *"The Store view's observation count equals its
  distinct-listing count (no within-view repeats). Category and Keyword views
  have fewer distinct listings than observations due to within-view repeats."*

### Visual C: Discount Field Status by View
`x=40, y=760, w=1480, h=560`. **100% Stacked bar chart** (horizontal).
- Axis: `source_view`
- Legend: `discount_consistency_status`
- Values: `Listing Observations` (as a percentage of total via the 100%-stacked
  chart type)
- No visual-level filter
- Sort: axis fixed order `category, keyword, store`
- Legend order/colors: `consistent` (green), `inconsistent` (red),
  `no_recorded_discount` (grey), `invalid_or_missing_reference_price` (amber),
  `no_recorded_and_no_valid_reference` (brown), set explicitly via Format > Data
  colors for consistency with `figures/03_discount_status_by_view.png` from
  Stage 2
- Data labels on, percentage format
- Title: **"Discount Field Status by Collection View"**
- Tooltip: add `Testable Discount Count` and `Discount Inconsistency Rate` so
  hovering the "inconsistent" segment shows the rate among testable rows, not
  just the raw share
- Caveat footer: *"Store's 312 `-1` sentinel rows are 'invalid/missing reference
  price,' not comparable to 'inconsistent.' See docs/STAGE3_SQL_ANALYSIS.md, Q3."*

### Visual D: SGD-999 Price Sensitivity (Category View)
`x=1560, y=760, w=960, h=560`. Two stacked Card visuals plus a caption text box,
**not** a chart (this is a small callout panel, deliberately simple). **Correction
(second Stage 4 review): both measures are Category-view means, not
overall-marketplace-sample means; labels below are updated accordingly, and the
measures themselves already carry the `source_view = "category"` filter
internally** (see DAX guide), so no visual-level filter is needed here.
- Card 1 (`y=760, h=170`): measure `Mean Observed Price` (supporting measure, see
  DAX guide addendum), label "Mean Price, Category View, All 998 Observations"
- Card 2 (`y=940, h=170`): measure `Mean Observed Price Excl. SGD 999`
  (supporting measure), label "Mean Price, Category View, Excl. 4 SGD-999
  Observations"
- Text box (`y=1120, h=180`): *"Within the Category view, median prices shift by
  at most SGD 0.12 when excluding these rows; the mean shifts about 25% (SGD
  15.58 to 11.62, see Card 1 vs Card 2). This is a suspected, unproven
  price-ceiling pattern specific to the Category view. Don't describe it as
  confirmed censoring, and don't generalize it to the Keyword or Store views
  without checking them separately."*
- No additional visual-level filters needed (the measures are self-scoped to the
  Category view).

### Edit Interactions (Page 1)

Set via **Format > Edit interactions** on each source visual, selected one at a
time. Default Power BI behavior, where every visual filters every other visual,
isn't safe here, because the four main visuals cover different, overlapping
scopes: the Category slicer and Visual A are Category-only, Visual B and Visual C
span all three views, and the KPI row and Visual D are whole-dataset or
Category-fixed figures. Left on default, selecting one category bar would
silently filter the all-views visuals down to a single view's worth of data,
which looks like "the whole marketplace changed" when only a category was
clicked.

| Source visual | Target visual | Setting | Why |
|---|---|---|---|
| Category slicer | KPI cards 1 to 4 | **None** | KPI row reports whole-dataset coverage figures that must not change when the Category view is being explored |
| Category slicer | Visual B (Observations vs. Distinct Listings by View) | **None** | Visual B spans all three views; a single-category selection must not collapse it |
| Category slicer | Visual C (Discount Field Status by View) | **None** | Same reason as Visual B |
| Category slicer | Visual D (SGD-999 Sensitivity) | **None** | Visual D's measures are already fixed to the whole Category view; they shouldn't narrow further to one selected category |
| Category slicer | Visual A (Median Price by Category) | **Filter** (default) | This is the one intended, useful interaction. The slicer exists specifically to let the user focus Visual A |
| Visual A (click a category bar) | KPI cards, Visual B, Visual C, Visual D | **None** | Same reasoning as the slicer rows above: a bar click is just another form of category selection and must not leak into whole-dataset or cross-view visuals |
| Visual B, Visual C (click a view's bar/segment) | KPI cards | **None** | Selecting "category" within Visual B/C must not change the whole-dataset KPI cards |
| Visual B and Visual C | each other | **Filter** (default) | Both are already scoped per-view breakdowns; letting a view selection in one highlight the same view in the other is a useful, comparable-scope interaction worth keeping |

---

## Page 2: "Seller Landscape & Product Popularity"

### Title
Text box, `x=40, y=20, w=1800, h=60`, 32pt bold: **"Seller Landscape & Product
Popularity"**
Subtitle, `x=40, y=82, w=1800, h=35`, 16pt: *"Store view (12 shops) and Keyword
view (17 search terms): descriptive only, no performance ranking"*

### KPI card row (`y=120, h=140`)
Four Card visuals, each `w=580`, 20px gaps, starting `x=40`:

| # | x | Measure | Label override |
|---|---|---|---|
| 1 | 40 | `Rated Observations` | "Rated Observations (rating > 0)" |
| 2 | 640 | `Median Rating (Rated Only)` | "Median Rating (Rated Only)" |
| 3 | 1240 | `Sponsored Listings` | "Sponsored Observations (Keyword View)" |
| 4 | 1840 | `Sponsored Listing Share` | "Sponsored Share (Keyword View)" |

### Visual A: Listings per Sampled Store
`x=40, y=280, w=850, h=520`. **Clustered bar chart** (horizontal).
- Axis: `store_name`
- Values: `Distinct Listings`
- Visual-level filter: `source_view = "store"`
- Sort: by `Distinct Listings`, descending
- Data labels on
- Title: **"Listings per Sampled Store (12 Shops)"**
- Caveat footer: *"12 named shop handles only, descriptive, not a representative
  seller sample."*

### Visual B: Median Observed Price by Store
`x=910, y=280, w=800, h=520`. **Clustered bar chart** (horizontal).
- Axis: `store_name`
- Values: `Median Observed Price`
- Visual-level filter: `source_view = "store"`
- Sort: by `Median Observed Price`, descending
- Data labels: Currency SGD
- Title: **"Median Observed Price by Store"**

### Visual C: Median Rating by Store (Rated Only)
`x=1730, y=280, w=790, h=520`. **Clustered bar chart** (horizontal).
- Axis: `store_name`
- Values: `Median Rating (Rated Only)`
- Visual-level filter: `source_view = "store"`
- Sort: by `Median Rating (Rated Only)`, descending
- Data labels: `0.00`
- Tooltip: add `Rated Observations` so hovering shows how many of that store's
  listings were rated (flags cases like azren_albakri92.sg at 51 of 89, with 38
  unrated)
- Title: **"Median Rating by Store (Rated Listings Only)"**
- Caveat footer: *"Excludes rating = 0 (not-yet-rated). azren_albakri92.sg: 38 of
  89 listings unrated; the median shown is among its 51 rated listings only."*

### Visual D: Sponsored vs. Organic by Keyword
`x=40, y=840, w=1480, h=480`. **100% Stacked bar chart** (horizontal).
- Axis: `search_keyword`
- Legend: `sponsored` (True/False)
- Values: `Listing Observations`
- Visual-level filter: `source_view = "keyword"`
- Sort: by sponsored share (if available) or alphabetically by `search_keyword`
- Legend colors: Sponsored = amber, Organic = grey (match
  `figures/07_sponsored_by_keyword.png`)
- Data labels: percentage
- Title: **"Sponsored vs. Organic Observations by Sampled Keyword"**
- Caveat footer: *"`sponsored` describes placement in these search results only,
  not a cause of demand, sales, or listing quality."*

### Visual E: Median Rating by Category (Rated Only)
`x=1560, y=840, w=960, h=480`. **Clustered column chart**.
- Axis: `category_name`
- Values: `Median Rating (Rated Only)`
- Visual-level filter: `source_view = "category"`
- Sort: by `Median Rating (Rated Only)`, descending
- Data labels: `0.00`
- Title: **"Median Rating by Category (Rated Listings Only)"**
- Caveat footer: *"Narrow 0.09-point band across categories: limited
  discriminating signal in this sample."*

No slicer on Page 2: each visual already shows its full population (12 stores,
17 keywords, 6 categories), so a slicer would only reduce visible context, not
add useful filtering given the small cardinalities involved.

### Edit Interactions (Page 2)

Page 2 has three Store-view visuals (A, B, C) that share `store_name` and are
genuinely comparable, plus a Keyword-view visual (D) and a Category-view visual
(E) that aren't. Default Power BI cross-filtering would let a store selection
bleed into the Keyword and Category visuals (which have no `store_name` field,
but Power BI would still apply the underlying row filter and silently shrink
their totals), so interactions are set explicitly, letting only the genuinely
comparable, same-collection-view visuals affect each other.

| Source visual | Target visual | Setting | Why |
|---|---|---|---|
| Visual A, B, or C (click a store) | KPI cards 1 to 4 | **None** | KPI row reports whole-dataset/whole-Keyword-view figures that must not change when exploring one store |
| Visual A, B, or C (click a store) | Visual D (Sponsored vs. Organic by Keyword) | **None** | Store selections have no meaningful relationship to the Keyword view; leaving this on default would silently, and confusingly, filter Visual D |
| Visual A, B, or C (click a store) | Visual E (Median Rating by Category) | **None** | Same reasoning: Store and Category views are unrelated populations here |
| Visual A, Visual B, Visual C (click a store in any one) | the other two | **Filter** (default) | Genuinely useful: selecting a store in the assortment chart should highlight the same store's price and rating bars. This is the "preserve interactions within the same collection view" case |
| Visual D (click a keyword or sponsored/organic segment) | KPI cards, Visual A/B/C, Visual E | **None** | Keyword-view selections must not affect Store-view or Category-view visuals or the whole-dataset KPI cards |
| Visual E (click a category) | KPI cards, Visual A/B/C, Visual D | **None** | Category-view selections must not affect Store-view or Keyword-view visuals or the KPI cards |

---

## Typography (both pages, QHD 2560x1440)

Sized up from a typical 1920x1080 build guide's defaults to remain legible at QHD
and in a portfolio screenshot or recording:

| Element | Size | Weight |
|---|---|---|
| Page title (e.g. "Product Pricing & Promotions") | **32pt** | Bold |
| Page subtitle | **16pt** | Regular |
| Visual titles | **16pt** | Semibold |
| KPI card value (the big number) | **40pt** | Bold |
| KPI card label | **14pt** | Regular |
| Axis labels / data labels | **12pt** | Regular |
| Slicer title | **14pt** | Semibold |
| Slicer item list | **12pt** | Regular |
| Caveat/footer text boxes | **11pt** | Regular, italic |

(Correction, second Stage 4 review: the page titles and subtitles were
previously specified at 28pt/12pt, which is small for a 2560x1440 canvas viewed
at typical zoom, and are increased to 32pt/16pt above. The remaining elements in
this table weren't previously specified at all and are sized here for the first
time, calibrated to the same QHD canvas rather than Power BI's smaller
1920x1080-oriented defaults.)

---

## Visual type summary (standard Power BI visuals only, no custom-visual dependencies)

Card, Clustered Bar Chart, Clustered Column Chart, 100% Stacked Bar Chart, Slicer,
Text Box. No box-and-whisker, no custom visuals. This matches the brief's
instruction to avoid unnecessary custom-visual dependencies.
