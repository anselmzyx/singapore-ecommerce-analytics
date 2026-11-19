# Singapore E-commerce Marketplace & Pricing Analytics (Shopee)

## Project overview and objectives

For this project, I analysed a sample of Shopee Singapore product listings to
understand how prices, discounts, and product ratings vary across different categories
and sellers. I used Python to clean and explore the data, DuckDB SQL to answer specific
business questions, and Power BI to bring the findings together in an interactive
dashboard.

I kept the scope narrow and descriptive rather than trying to make broad claims about
the whole marketplace. The questions I wanted to answer were:

- How are listing prices distributed within and across a small set of sampled product
  categories, and how sensitive are those figures to a suspected price-recording
  anomaly?
- How reliable is the recorded "discount" field compared to what the listed prices
  themselves imply?
- What does assortment and pricing look like across a handful of sampled seller
  storefronts?
- How are recorded product ratings distributed, and how does sponsored placement show
  up in sampled keyword search results?

Every finding below is scoped to the sample described next. This project doesn't claim
to describe the Singapore e-commerce market as a whole, and it is **not endorsed by or
affiliated with Shopee**.

## Data source and collection date

Kaggle dataset: [`johnphamed/shopee-singapore-listing-samples-august-2025`](https://www.kaggle.com/datasets/johnphamed/shopee-singapore-listing-samples-august-2025),
published by Easy Data. Original publisher documentation:
[github.com/JohnPham-easydata/Shopee-Dataset](https://github.com/JohnPham-easydata/Shopee-Dataset).

I didn't collect this data myself. I obtained an existing dataset from Kaggle and
analysed it. Three Excel workbooks capture **Category**, **Keyword**, and **Store**
collection views of Shopee Singapore listings, denominated in SGD, sampled on
**18 August 2025**. Each view's own crawl burst is brief (around 4 minutes), but the
three views' bursts happen at different times of day. See
`docs/STAGE1_DATASET_REVIEW.md` for the detail. This is a single-day, cross-sectional,
curated sample, not a time series, and not a representative cross-section of the whole
marketplace (full scope and sampling bias discussion in `docs/STAGE1_DATASET_REVIEW.md`).

## Workflow

| Stage | Tooling | Output |
|---|---|---|
| 1. Acquisition and inspection | Python, pandas, openpyxl | I independently verified every publisher-reported figure directly from the raw files |
| 2. Cleaning and EDA | Python, pandas, matplotlib, Jupyter | Observation-level and unique-listing cleaned datasets, plus 7 EDA charts |
| 3. Business analysis | DuckDB SQL | 7 business questions, executed and reconciled against Stages 1 and 2 with zero discrepancies |
| 4 to 5. Dashboard | Power BI Desktop | A single-table model, 15+ DAX measures, and a two-page QHD (2560x1440) report, built manually and verified against the SQL outputs |

Each stage's methodology, corrections, and validation results are documented in full
under `docs/` (see Repository structure below). I reviewed each stage independently
before moving on to the next.

## Dashboard

### Page 1: Product Pricing & Promotions

![Product Pricing & Promotions dashboard page](dashboard/screenshots/01_pricing_promotions.png)

### Page 2: Seller Landscape, Ratings & Sponsorship

![Seller Landscape, Ratings & Sponsorship dashboard page](dashboard/screenshots/02_seller_landscape_ratings_sponsorship.png)

Both screenshots show aggregate figures only, with no row-level listing data. I'm
publishing them here as original analytical outputs of this project.

The PBIX file itself is **not** published (see Licensing below). The model, DAX, and
page-by-page build instructions are documented under `docs/POWER_BI_MODEL_GUIDE.md`,
`docs/POWER_BI_DAX_GUIDE.md`, and `docs/POWER_BI_DASHBOARD_BUILD_GUIDE.md`. The build
guide was written before the dashboard was built, and a short "Final as-built
dashboard" section at the top of it documents a few adjustments made during
construction, like one KPI card and two chart-label fields that ended up different
from the original plan.

## Key findings

All figures below are supported by the published SQL outputs in `results/sql/` (Stage 3,
DuckDB) and match what's shown in the dashboard screenshots above.

- I found **2,727** distinct listings sampled across 968 distinct shops (2,996 total
  observations across the three collection views, with 63 listings appearing in more
  than one view).
- Median listing price is **SGD 12.90** across all sampled listings. By category,
  medians range from SGD 2.53 (Housekeeping) to SGD 11.56 (Body lotion).
- **Suspected, unconfirmed price-ceiling pattern at SGD 999:** excluding the 4
  Category-view observations recorded at exactly SGD 999 drops the Category-view mean
  price from SGD 15.58 to SGD 11.62 (a 25.4% drop), while shifting category medians by
  at most SGD 0.12. Medians are robust to this anomaly; means are not.
- The recorded "discount" field disagrees with the price-implied discount in **19.2%**
  of Category-view rows and **10.4%** of Keyword-view rows that have a testable
  discount (both values available), or **10.3%** across all testable rows overall.
  The Store view's 312 "-1" reference-price rows are excluded from testing as
  sentinel values, not treated as a real discount of 0%.
- **56.7%** of sampled Keyword-view search results are flagged sponsored, and
  sponsorship share varies widely by search term.
- Recorded ratings cluster tightly and high (median 4.92 among 2,713 rated
  observations), a narrow 0.09-point band across categories with limited discriminating
  signal in this sample.

**I'm not claiming** anything about revenue, profitability, market share, customer
retention, or causal relationships. `rating`, `reviews_count`, `sold`, and
`monthly_sold` are source-reported platform counters, not independently audited sales
or satisfaction data.

## Data-quality methodology and limitations

- I independently reproduced every publisher-reported figure in the source dataset's
  documentation from the raw files before relying on it (Stage 1).
- Identifiers (`shop_id`, `product_id`, `listing_key`) are retained as strings
  throughout to avoid precision loss. I used a documented, deterministic rule (latest
  observed `crawl_time`) wherever a single "representative" price per listing is
  needed, rather than an arbitrary minimum or average across views.
- Recorded and price-implied discounts are kept as separate fields everywhere. A
  matching recorded and implied discount is **not** treated as proof of a genuine,
  comparable promotion, since variant and pack-size comparability is not confirmed for
  36% of observations.
- `rating = 0` is a "not yet rated" sentinel (it always co-occurs with zero rating and
  review counts in this data), so I excluded it from every rating statistic, including
  per-store medians.
- Main limitations: a narrow, curated sample (6 categories, 17 keywords, 12 stores), a
  single-day snapshot, an unresolved and suspected price-recording anomaly at SGD 999,
  and dataset reuse-licensing uncertainty (see below).

Full stage-by-stage methodology, every correction applied during independent review,
and every validation check are documented under `docs/`.

## Repository structure

```
scripts/           Reproducible Python: Stage 1 inspection, Stage 2 cleaning, Stage 3 SQL runner, sanitizer
sql/               DuckDB SQL for the 7 Stage 3 business questions
notebooks/         Public EDA notebook (code and markdown, outputs cleared; rerun to regenerate)
figures/           5 of 7 EDA charts generated during development (PNG), see note below
dashboard/         Final dashboard screenshots (the PBIX itself is kept private, see Licensing)
docs/              Dataset review, cleaning methodology, EDA findings, SQL analysis, and
                   Power BI model/DAX/dashboard-build guides
results/           Machine-readable, aggregate-only outputs: Stage 1 inspection summaries
                   (results/stage1/), Stage 2 cleaning validation (results/stage2/), and
                   Stage 3 SQL business-question outputs (results/sql/)
requirements.txt   Python dependencies
```

`data/raw/` and `data/processed/` are **not** included in this repository. See
Reproducibility below for how to regenerate them locally.

**Note on `figures/`:** I generated seven EDA charts during development and published
five of them here. The other two (a per-category price boxplot and a rating-vs-reviews
scatter) are left out of this public release because they weren't necessary for it, not
because of any data-quality issue. Both are fully reproducible locally with the public
notebook.

## Reproducibility

This repository doesn't include the original dataset or any processed row-level export
of it (see Licensing). To reproduce the pipeline locally:

1. **Get the data.** Download the dataset from Kaggle:
   [`johnphamed/shopee-singapore-listing-samples-august-2025`](https://www.kaggle.com/datasets/johnphamed/shopee-singapore-listing-samples-august-2025)
   (via the Kaggle website or `kaggle datasets download johnphamed/shopee-singapore-listing-samples-august-2025`).
   Unzip it and place the three workbooks at:
   ```
   data/raw/extracted/SG_Category_Data_Mon_18_Aug_2025.xlsx
   data/raw/extracted/SG_Keyword_Data_Mon_18_Aug_2025.xlsx
   data/raw/extracted/SG_Store_Data_Mon_18_Aug_2025.xlsx
   ```
   (filenames must match exactly, since the scripts reference them directly).
2. **Install dependencies.**
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run the pipeline in order:**
   ```
   python scripts/inspect_dataset.py      # Stage 1: independent verification -> results/stage1/
   python scripts/clean_data.py           # Stage 2: cleaning -> data/processed/
   python scripts/run_sql_analysis.py     # Stage 3: DuckDB business analysis -> results/sql/
   ```
4. **Explore the EDA notebook** (`notebooks/01_ecommerce_eda_public.ipynb`) and run it
   to regenerate all 7 charts locally (outputs are cleared in this published copy; the
   notebook's own code and markdown are unchanged from development).
5. **Rebuild the dashboard.** The PBIX is not distributed. Follow
   `docs/POWER_BI_MODEL_GUIDE.md`, `docs/POWER_BI_DAX_GUIDE.md`, and
   `docs/POWER_BI_DASHBOARD_BUILD_GUIDE.md` in Power BI Desktop to recreate both pages
   from the `data/processed/listings_observations.csv` produced in step 3.

Every number in `docs/` and in the dashboard traces back to a specific file produced by
these scripts in `results/`.

## Attribution and licensing

- **Dataset:** "Shopee Singapore Listing Samples, August 2025," published by **Easy
  Data** on Kaggle. Please cite Easy Data, the dataset title, observation date, and
  Kaggle version if you reuse the dataset itself.
- **License status: Unknown.** The Kaggle listing's license field is "Unknown," and the
  publisher's own documentation states that reuse licensing is not specified. An
  accessible Kaggle download doesn't, by itself, establish a right to redistribute the
  data.
- **What is and isn't in this repository, as a direct result:**
  - The original Kaggle dataset (raw Excel workbooks and archive) is **not**
    redistributed here. This repository does not provide the complete original
    dataset; you'll need to obtain it yourself from Kaggle (see Reproducibility).
  - Processed, row-level listing data (the cleaned CSVs produced in Stage 2) is **not**
    redistributed.
  - The Power BI report file (`.pbix`) is **not** redistributed.
  - The two dashboard screenshots and the aggregate statistical outputs under
    `results/` **are** published, as this project's own original analytical outputs,
    with the dataset's reuse-licensing status explicitly acknowledged as unresolved
    rather than assumed resolved.
- **Not affiliated with or endorsed by Shopee.** "Shopee" is referenced here only as
  the platform the sampled listings were collected from.
- This repository's own code and documentation (everything not derived row-by-row from
  the source dataset) may be reused under the terms stated in this repository, if any
  are added. Absent a stated license, standard copyright applies.
