"""
Stage 2 cleaning pipeline for the Shopee Singapore Listing Samples (Aug 2025) dataset.

Reads the three original raw workbooks (unchanged), builds an observation-level cleaned
dataset (one row per identifiable physical row, source view preserved) and a
unique-listing reference dataset (one row per distinct shop_id/product_id pair, unioned
across views), with explicit type conversion, sentinel handling, and discount validation.

Does not modify the original workbooks. Does not forward-fill or fabricate missing
listing identifiers or analytical values. Incomplete rows (no shop_id/product_id) are
excluded from both output datasets but their counts are documented in the validation
report; they remain untouched in the original workbooks.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "extracted"
STAGE1_RESULTS_DIR = PROJECT_ROOT / "results" / "stage1"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results" / "stage2"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_raw_files_unchanged() -> dict:
    """Recompute SHA-256 of each raw workbook and compare against the checksum
    recorded in Stage 1's file_inventory.json. Raises if any file has changed."""
    with open(STAGE1_RESULTS_DIR / "file_inventory.json") as f:
        stage1_inventory = json.load(f)
    results = {}
    for entry in stage1_inventory:
        path = RAW_DIR / entry["filename"]
        current = sha256_of(path)
        matches = current == entry["sha256"]
        results[entry["filename"]] = {
            "stage1_sha256": entry["sha256"],
            "current_sha256": current,
            "unchanged": matches,
        }
        if not matches:
            raise RuntimeError(
                f"Raw file {entry['filename']} has changed since Stage 1! "
                f"Expected {entry['sha256']}, got {current}."
            )
    return results

WORKBOOKS = {
    "category": "SG_Category_Data_Mon_18_Aug_2025.xlsx",
    "keyword": "SG_Keyword_Data_Mon_18_Aug_2025.xlsx",
    "store": "SG_Store_Data_Mon_18_Aug_2025.xlsx",
}

ID_COLS = ["shop_id", "product_id"]

# Canonical name <- raw name, applied per-workbook before concatenation.
COLUMN_RENAMES = {
    "videos_counts": "videos_count",  # Keyword, Store use plural; Category uses singular
    "Keyword": "search_keyword",  # avoid clashing with the "keyword" view name itself
}

NUMERIC_COLUMNS = [
    "price", "price_before_discount", "min_price", "max_price", "min_mrp", "max_mrp",
    "rating", "rating_count", "reviews_count", "reviews_image_count", "sold",
    "monthly_sold", "liked_count", "stock", "page_number", "rank", "videos_count",
    "category_id",
]
BOOL_COLUMNS = ["sponsored", "isVirtualItem", "isSaleItemVerified", "free_shipping"]
DATETIME_COLUMNS = ["crawl_time", "parse_time"]
TEXT_STRIP_COLUMNS = [
    "title", "brand", "category_name", "search_keyword", "store_name", "domain",
    "currency", "language", "shop_locations",
]

BOOL_MAP = {"true": True, "false": False, "1": True, "0": False}


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().map(BOOL_MAP)


def parse_discount_pct(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.rstrip("%"), errors="coerce")


def load_raw(view: str, filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    df = pd.read_excel(path, sheet_name="Sheet1", dtype=str)
    df.insert(0, "source_view", view)
    df.insert(1, "source_file", filename)
    # Excel row numbers: row 1 is the header, so first data row is Excel row 2.
    df.insert(2, "source_excel_row", range(2, len(df) + 2))
    df = df.rename(columns=COLUMN_RENAMES)
    return df


def main():
    checksum_verification = verify_raw_files_unchanged()

    frames = [load_raw(view, filename) for view, filename in WORKBOOKS.items()]
    combined = pd.concat(frames, ignore_index=True, sort=False)

    def nonblank(s):
        return s.notna() & (s.str.strip() != "")

    has_id = nonblank(combined["shop_id"]) & nonblank(combined["product_id"])
    identifiable = combined[has_id].copy()
    incomplete = combined[~has_id].copy()

    # --- Type conversion (identifiable rows only); original raw string preserved in *_raw ---
    for col in NUMERIC_COLUMNS:
        if col in identifiable.columns:
            identifiable[col + "_raw"] = identifiable[col]
            identifiable[col] = pd.to_numeric(identifiable[col], errors="coerce")

    for col in BOOL_COLUMNS:
        if col in identifiable.columns:
            identifiable[col + "_raw"] = identifiable[col]
            identifiable[col] = to_bool(identifiable[col])

    for col in DATETIME_COLUMNS:
        if col in identifiable.columns:
            identifiable[col + "_raw"] = identifiable[col]
            identifiable[col] = pd.to_datetime(identifiable[col], errors="coerce")

    for col in TEXT_STRIP_COLUMNS:
        if col in identifiable.columns:
            identifiable[col] = identifiable[col].str.strip()

    # --- Reference-price sentinel handling (price_before_discount == -1) ---
    pbd = identifiable.get("price_before_discount")
    identifiable["reference_price_status"] = np.select(
        [pbd.isna(), pbd == -1, pbd <= 0],
        ["missing", "sentinel_invalid", "invalid_nonpositive"],
        default="valid",
    )
    reference_price_valid = identifiable["reference_price_status"] == "valid"

    # --- Discount: recorded vs. price-implied, kept as separate fields ---
    identifiable["discount_recorded_pct"] = (
        parse_discount_pct(identifiable["discount"]) if "discount" in identifiable.columns else np.nan
    )
    price = identifiable.get("price")
    pbd_for_implied = pbd.where(reference_price_valid)
    implied = np.where(
        reference_price_valid & price.notna(),
        (1 - price / pbd_for_implied) * 100,
        np.nan,
    )
    identifiable["discount_implied_pct"] = implied

    diff = (identifiable["discount_recorded_pct"] - identifiable["discount_implied_pct"]).abs()
    recorded_missing = identifiable["discount_recorded_pct"].isna()
    implied_missing = identifiable["discount_implied_pct"].isna()
    identifiable["discount_consistency_status"] = np.select(
        [
            recorded_missing & implied_missing,
            recorded_missing & ~implied_missing,
            ~recorded_missing & implied_missing,
            diff <= 1,
        ],
        [
            "no_recorded_and_no_valid_reference",
            "no_recorded_discount",
            "invalid_or_missing_reference_price",
            "consistent",
        ],
        default="inconsistent",
    )

    # Variant/pack-size comparability ambiguity: a price range exists for the listing.
    min_price = identifiable.get("min_price")
    max_price = identifiable.get("max_price")
    min_mrp = identifiable.get("min_mrp")
    max_mrp = identifiable.get("max_mrp")
    identifiable["variant_comparability_uncertain"] = (
        ((min_price.notna()) & (max_price.notna()) & (min_price != max_price))
        | ((min_mrp.notna()) & (max_mrp.notna()) & (min_mrp != max_mrp))
    )

    # --- Stable composite listing key ---
    identifiable["listing_key"] = (
        identifiable["domain"].fillna("") + "|"
        + identifiable["shop_id"] + "|"
        + identifiable["product_id"]
    )

    # --- Within-view repeat flag (does NOT imply a data error; see Stage 1 findings) ---
    identifiable["is_repeated_within_view"] = identifiable.duplicated(
        subset=["source_view"] + ID_COLS, keep=False
    )

    # Order columns: context first, then identifiers, then the rest as encountered.
    front_cols = [
        "listing_key", "source_view", "source_file", "source_excel_row",
        "domain", "shop_id", "product_id", "is_repeated_within_view",
    ]
    remaining_cols = [c for c in identifiable.columns if c not in front_cols]
    identifiable = identifiable[front_cols + remaining_cols]

    identifiable.to_csv(PROCESSED_DIR / "listings_observations.csv", index=False)

    # --- Unique-listing reference dataset (one row per listing_key, unioned across views) ---
    def agg_view_price(group):
        return {row["source_view"]: row["price"] for _, row in group.iterrows()}

    price_pivot = (
        identifiable.pivot_table(
            index="listing_key", columns="source_view", values="price", aggfunc="first"
        )
        .rename(columns=lambda c: f"price_{c}")
        .reset_index()
    )

    views_by_key = (
        identifiable.groupby("listing_key")["source_view"]
        .agg(lambda s: ",".join(sorted(set(s))))
        .rename("views_present")
    )
    n_obs_by_key = identifiable.groupby("listing_key").size().rename("n_observations")
    shop_by_key = identifiable.groupby("listing_key")["shop_id"].first()
    product_by_key = identifiable.groupby("listing_key")["product_id"].first()
    brand_by_key = identifiable.groupby("listing_key")["brand"].first()
    title_by_key = identifiable.groupby("listing_key")["title"].first()

    unique_listings = (
        price_pivot.set_index("listing_key")
        .join([views_by_key, n_obs_by_key, shop_by_key, product_by_key, brand_by_key, title_by_key])
        .reset_index()
    )

    price_cols = [c for c in unique_listings.columns if c.startswith("price_")]
    unique_listings["n_views_present"] = unique_listings["views_present"].str.split(",").apply(len)
    unique_listings["price_min_across_views"] = unique_listings[price_cols].min(axis=1)
    unique_listings["price_max_across_views"] = unique_listings[price_cols].max(axis=1)
    unique_listings["cross_view_price_conflict"] = (
        unique_listings["n_views_present"] > 1
    ) & (
        unique_listings["price_max_across_views"] - unique_listings["price_min_across_views"] > 0.005
    )

    unique_listings.to_csv(PROCESSED_DIR / "listings_unique_reference.csv", index=False)

    # --- Validation / reconciliation report ---
    validation = {
        "raw_file_checksum_verification": checksum_verification,
        "n_physical_rows_combined": int(len(combined)),
        "n_identifiable_observations": int(len(identifiable)),
        "n_incomplete_rows_excluded": int(len(incomplete)),
        "n_identifiable_by_view": identifiable["source_view"].value_counts().to_dict(),
        "n_distinct_listing_keys": int(identifiable["listing_key"].nunique()),
        "n_distinct_shops": int(identifiable["shop_id"].nunique()),
        "n_unique_listing_rows": int(len(unique_listings)),
        "reconciles_2996_identifiable": int(len(identifiable)) == 2996,
        "reconciles_2727_distinct_keys": int(identifiable["listing_key"].nunique()) == 2727,
        "reconciles_968_distinct_shops": int(identifiable["shop_id"].nunique()) == 968,
        "reconciles_11862_incomplete_rows": int(len(incomplete)) == 11862,
        "reference_price_status_counts": identifiable["reference_price_status"].value_counts().to_dict(),
        "store_sentinel_neg1_count": int((identifiable.loc[identifiable["source_view"] == "store", "reference_price_status"] == "sentinel_invalid").sum()),
        "discount_consistency_status_counts": identifiable["discount_consistency_status"].value_counts().to_dict(),
        "cross_view_price_conflicts": int(unique_listings["cross_view_price_conflict"].sum()),
        "n_listings_in_multiple_views": int((unique_listings["n_views_present"] > 1).sum()),
        "variant_comparability_uncertain_count": int(identifiable["variant_comparability_uncertain"].sum()),
        "price_exactly_999_count": int((identifiable["price"] == 999).sum()),
        "price_between_900_and_998_count": int(((identifiable["price"] >= 900) & (identifiable["price"] < 999)).sum()),
        "store_parse_before_crawl_preserved_count": int(
            (
                (identifiable["source_view"] == "store")
                & (identifiable["parse_time"] < identifiable["crawl_time"])
            ).sum()
        ),
        "numeric_conversion_failures": {
            col: int(identifiable[col].isna().sum() - identifiable[col + "_raw"].isna().sum())
            for col in NUMERIC_COLUMNS
            if col in identifiable.columns
        },
        "datetime_conversion_failures": {
            col: int(identifiable[col].isna().sum() - identifiable[col + "_raw"].isna().sum())
            for col in DATETIME_COLUMNS
            if col in identifiable.columns
        },
    }

    with open(RESULTS_DIR / "cleaning_validation_report.json", "w") as f:
        json.dump(validation, f, indent=2, default=str)

    print(json.dumps(validation, indent=2, default=str))


if __name__ == "__main__":
    main()
