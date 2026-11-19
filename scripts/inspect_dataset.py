"""
Stage 1 inspection script for the Shopee Singapore Listing Samples (Aug 2025) dataset.

Reads the three raw workbooks from data/raw/extracted/, computes file-level,
sheet-level, and listing-key-level diagnostics, and writes machine-readable
results to results/stage1/. Does not modify, clean, or drop any original rows.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
EXTRACTED_DIR = RAW_DIR / "extracted"
RESULTS_DIR = PROJECT_ROOT / "results" / "stage1"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WORKBOOKS = {
    "category": "SG_Category_Data_Mon_18_Aug_2025.xlsx",
    "keyword": "SG_Keyword_Data_Mon_18_Aug_2025.xlsx",
    "store": "SG_Store_Data_Mon_18_Aug_2025.xlsx",
}

ID_COLS = ["shop_id", "product_id"]

# Dtype overrides so identifier-like fields never get parsed as floats
ID_LIKE_SUBSTR = ["id", "_id", "shop_id", "product_id"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sheet_as_str(path: Path) -> pd.DataFrame:
    # Load everything as string first to avoid precision loss on IDs,
    # then infer types per column for reporting purposes only.
    df = pd.read_excel(path, sheet_name="Sheet1", dtype=str)
    return df


def infer_dtype(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "empty"
    numeric = pd.to_numeric(non_null, errors="coerce")
    if numeric.notna().all():
        if (numeric == numeric.astype(int, errors="ignore")).all():
            try:
                if (numeric.astype(float) % 1 == 0).all():
                    return "integer-like (stored as text)"
            except Exception:
                pass
        return "numeric (stored as text)"
    return "text"


def profile_columns(df: pd.DataFrame, population: str) -> list:
    """Profile columns for a given population ('whole_workbook' or 'identifiable_rows').

    IMPORTANT: missing_pct denominators differ by population. For the Keyword workbook
    in particular, 'whole_workbook' includes the 11,862 incomplete rows (which are
    missing nearly every column by construction), while 'identifiable_rows' reflects
    missingness only among the 999 rows that carry a usable shop_id/product_id. The two
    must not be conflated when reading a single missing_pct figure.
    """
    profiles = []
    n = len(df)
    for col in df.columns:
        series = df[col]
        missing = series.isna().sum() + (series == "").sum()
        profiles.append(
            {
                "population": population,
                "column": col,
                "inferred_dtype": infer_dtype(series),
                "denominator_rows": n,
                "missing_count": int(missing),
                "missing_pct": round(100 * missing / n, 2) if n else 0.0,
                "n_unique": int(series.nunique(dropna=True)),
            }
        )
    return profiles


def has_identifier(row) -> bool:
    shop = row.get("shop_id")
    product = row.get("product_id")
    shop_ok = shop is not None and str(shop).strip() not in ("", "nan", "None")
    product_ok = product is not None and str(product).strip() not in ("", "nan", "None")
    return shop_ok and product_ok


def main():
    file_inventory = []
    sheet_profiles = {}
    identifiable_frames = {}

    for key, filename in WORKBOOKS.items():
        path = EXTRACTED_DIR / filename
        size_bytes = path.stat().st_size
        checksum = sha256_of(path)

        xl = pd.ExcelFile(path)
        sheet_names = xl.sheet_names

        file_inventory.append(
            {
                "view": key,
                "filename": filename,
                "size_bytes": size_bytes,
                "sha256": checksum,
                "sheet_names": sheet_names,
                "n_sheets": len(sheet_names),
            }
        )

        df = load_sheet_as_str(path)
        n_rows, n_cols = df.shape

        has_id_mask = df.apply(has_identifier, axis=1) if n_rows else pd.Series([], dtype=bool)
        identifiable_df = df[has_id_mask].copy()
        incomplete_df = df[~has_id_mask].copy()

        identifiable_frames[key] = identifiable_df

        n_identifiable = len(identifiable_df)
        n_incomplete = len(incomplete_df)

        distinct_pairs = (
            identifiable_df[ID_COLS].drop_duplicates().shape[0] if n_identifiable else 0
        )
        distinct_shops = (
            identifiable_df["shop_id"].nunique(dropna=True) if n_identifiable else 0
        )
        repeated_rows = n_identifiable - distinct_pairs

        incomplete_nonnull_cols = []
        if n_incomplete:
            nonnull_rate = incomplete_df.notna().mean().sort_values(ascending=False)
            incomplete_nonnull_cols = [
                {"column": c, "nonnull_pct": round(100 * v, 2)}
                for c, v in nonnull_rate.items()
                if v > 0
            ]

        price_before_discount_neg1 = None
        parse_before_crawl = None
        if key == "store":
            if "price_before_discount" in identifiable_df.columns:
                pbd_numeric = pd.to_numeric(
                    identifiable_df["price_before_discount"], errors="coerce"
                )
                price_before_discount_neg1 = int((pbd_numeric == -1).sum())
            if {"parse_time", "crawl_time"}.issubset(identifiable_df.columns):
                parse_dt = pd.to_datetime(identifiable_df["parse_time"], errors="coerce")
                crawl_dt = pd.to_datetime(identifiable_df["crawl_time"], errors="coerce")
                parse_before_crawl = int((parse_dt < crawl_dt).sum())

        # Timestamp range and malformed-timestamp diagnostics (all views)
        timestamp_quality = {}
        for col in ["crawl_time", "parse_time"]:
            if col in identifiable_df.columns:
                parsed = pd.to_datetime(identifiable_df[col], errors="coerce")
                n_nonnull_raw = identifiable_df[col].notna().sum()
                n_malformed = int(n_nonnull_raw - parsed.notna().sum())
                timestamp_quality[col] = {
                    "min": str(parsed.min()) if parsed.notna().any() else None,
                    "max": str(parsed.max()) if parsed.notna().any() else None,
                    "n_malformed_unparseable": n_malformed,
                }

        brand_missing = None
        if "brand" in identifiable_df.columns:
            brand_missing = int(
                identifiable_df["brand"].isna().sum()
                + (identifiable_df["brand"] == "").sum()
            )

        currency_values = (
            sorted(identifiable_df["currency"].dropna().unique().tolist())
            if "currency" in identifiable_df.columns
            else []
        )
        domain_values = (
            sorted(identifiable_df["domain"].dropna().unique().tolist())
            if "domain" in identifiable_df.columns
            else []
        )

        price_quality = {}
        for col in ["price", "price_before_discount"]:
            if col in identifiable_df.columns:
                numeric = pd.to_numeric(identifiable_df[col], errors="coerce")
                price_quality[col] = {
                    "min": float(numeric.min()) if numeric.notna().any() else None,
                    "max": float(numeric.max()) if numeric.notna().any() else None,
                    "n_null": int(numeric.isna().sum()),
                    "n_zero_or_negative_excl_sentinel": int(
                        ((numeric <= 0) & (numeric != -1)).sum()
                    ),
                }
        discount_quality = None
        if "discount" in identifiable_df.columns:
            disc_pct = pd.to_numeric(
                identifiable_df["discount"].astype(str).str.rstrip("%"), errors="coerce"
            )
            price_num = pd.to_numeric(identifiable_df.get("price"), errors="coerce")
            pbd_num = pd.to_numeric(identifiable_df.get("price_before_discount"), errors="coerce")
            implied_pct = (1 - price_num / pbd_num.replace(-1, pd.NA)) * 100
            diff = (disc_pct - implied_pct).abs()
            n_populated = int(disc_pct.notna().sum())
            n_diff_gt_1pt = int((diff > 1).sum())
            discount_quality = {
                "n_populated": n_populated,
                "n_total_identifiable": n_identifiable,
                "min_pct": float(disc_pct.min()) if disc_pct.notna().any() else None,
                "max_pct": float(disc_pct.max()) if disc_pct.notna().any() else None,
                "n_diff_gt_1pt_vs_implied": n_diff_gt_1pt,
                # Denominator is populated discount rows, not total identifiable rows.
                # The two denominators give materially different percentages and must
                # not be conflated (Stage 1 review correction).
                "pct_diff_gt_1pt_of_populated": (
                    round(100 * n_diff_gt_1pt / n_populated, 1) if n_populated else None
                ),
            }
        sold_quality = {}
        for col in ["sold", "monthly_sold"]:
            if col in identifiable_df.columns:
                numeric = pd.to_numeric(identifiable_df[col], errors="coerce")
                sold_quality[col] = {
                    "n_null": int(numeric.isna().sum()),
                    "min": float(numeric.min()) if numeric.notna().any() else None,
                    "max": float(numeric.max()) if numeric.notna().any() else None,
                }

        category_distribution = None
        if key == "category" and "category_name" in identifiable_df.columns:
            category_distribution = (
                identifiable_df["category_name"].value_counts().to_dict()
            )
        keyword_distribution = None
        if key == "keyword":
            kw_col = "Keyword" if "Keyword" in identifiable_df.columns else "keyword"
            if kw_col in identifiable_df.columns:
                keyword_distribution = identifiable_df[kw_col].value_counts().to_dict()
        sponsored_counts = None
        if "sponsored" in identifiable_df.columns:
            sponsored_counts = identifiable_df["sponsored"].value_counts(dropna=False).to_dict()

        # Within-view duplicate pairs: do repeated appearances carry conflicting prices?
        conflicting_price_groups = None
        if n_identifiable and "price" in identifiable_df.columns:
            dup_mask = identifiable_df.duplicated(subset=ID_COLS, keep=False)
            dups = identifiable_df[dup_mask]
            if len(dups):
                price_nunique = dups.groupby(ID_COLS)["price"].nunique()
                conflicting_price_groups = int((price_nunique > 1).sum())
            else:
                conflicting_price_groups = 0

        sheet_profiles[key] = {
            "filename": filename,
            "physical_rows": n_rows,
            "physical_cols": n_cols,
            "columns": list(df.columns),
            "n_identifiable_observations": n_identifiable,
            "n_incomplete_rows": n_incomplete,
            "incomplete_row_nonnull_columns": incomplete_nonnull_cols,
            "distinct_shop_product_pairs": distinct_pairs,
            "distinct_shops": distinct_shops,
            "repeated_rows_within_view": repeated_rows,
            "currency_values_found": currency_values,
            "domain_values_found": domain_values,
            "brand_missing_count": brand_missing,
            "store_price_before_discount_eq_neg1": price_before_discount_neg1,
            "store_parse_time_before_crawl_time": parse_before_crawl,
            "price_quality": price_quality,
            "discount_quality": discount_quality,
            "sold_counter_quality": sold_quality,
            "timestamp_quality": timestamp_quality,
            "category_distribution": category_distribution,
            "keyword_distribution": keyword_distribution,
            "sponsored_value_counts": sponsored_counts,
            "repeated_pairs_with_conflicting_price": conflicting_price_groups,
            "column_profile_whole_workbook": profile_columns(df, "whole_workbook"),
            "column_profile_identifiable_rows": profile_columns(
                identifiable_df, "identifiable_rows"
            ),
        }

    # Cross-view overlap on distinct shop_id/product_id pairs
    pair_sets = {
        k: set(map(tuple, identifiable_frames[k][ID_COLS].drop_duplicates().values))
        for k in identifiable_frames
    }
    overlap = {
        "category_keyword": len(pair_sets["category"] & pair_sets["keyword"]),
        "category_store": len(pair_sets["category"] & pair_sets["store"]),
        "keyword_store": len(pair_sets["keyword"] & pair_sets["store"]),
        "all_three": len(pair_sets["category"] & pair_sets["keyword"] & pair_sets["store"]),
    }
    union_all_pairs = set.union(*pair_sets.values())
    total_identifiable_observations = sum(
        sheet_profiles[k]["n_identifiable_observations"] for k in sheet_profiles
    )
    total_shops_union = len(
        set.union(
            *[
                set(identifiable_frames[k]["shop_id"].dropna().unique())
                for k in identifiable_frames
            ]
        )
    )

    # Cross-view price conflicts: for shop_id/product_id pairs appearing in more than
    # one view, does the recorded price agree across views? (Stage 1 review correction:
    # the original script only checked for price conflicts *within* a single view.)
    price_by_view = {}
    for k, frame in identifiable_frames.items():
        price_by_view[k] = (
            frame.assign(price_num=pd.to_numeric(frame["price"], errors="coerce"))
            .groupby(ID_COLS)["price_num"]
            .first()
        )
    all_pairs_multi_view = {}
    for k, pset in pair_sets.items():
        for pair in pset:
            all_pairs_multi_view.setdefault(pair, []).append(k)
    cross_view_price_conflicts = []
    for pair, views_present in all_pairs_multi_view.items():
        if len(views_present) < 2:
            continue
        prices = {v: price_by_view[v].get(pair) for v in views_present}
        distinct_prices = {p for p in prices.values() if pd.notna(p)}
        if len(distinct_prices) > 1:
            cross_view_price_conflicts.append(
                {
                    "shop_id": pair[0],
                    "product_id": pair[1],
                    "views": views_present,
                    "prices_by_view": {v: prices[v] for v in views_present},
                }
            )
    cross_view_price_check = {
        "n_pairs_in_multiple_views": sum(
            1 for v in all_pairs_multi_view.values() if len(v) > 1
        ),
        "n_pairs_with_price_conflict": len(cross_view_price_conflicts),
        "conflicting_pairs": cross_view_price_conflicts,
    }

    summary = {
        "file_inventory": file_inventory,
        "sheet_profiles": sheet_profiles,
        "cross_view_overlap_distinct_pairs": overlap,
        "cross_view_price_check": cross_view_price_check,
        "total_identifiable_observations_sum_of_views": total_identifiable_observations,
        "total_distinct_shop_product_pairs_union": len(union_all_pairs),
        "total_distinct_shops_union": total_shops_union,
    }

    with open(RESULTS_DIR / "file_inventory.json", "w") as f:
        json.dump(file_inventory, f, indent=2)

    with open(RESULTS_DIR / "sheet_profiles.json", "w") as f:
        json.dump(sheet_profiles, f, indent=2)

    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Flat CSV of column-level missing-value profile for all views, with BOTH
    # populations (whole_workbook and identifiable_rows) clearly labeled and their
    # distinct denominators recorded explicitly (denominator_rows column).
    rows = []
    for view, profile in sheet_profiles.items():
        for col_profile in profile["column_profile_whole_workbook"]:
            rows.append({"view": view, **col_profile})
        for col_profile in profile["column_profile_identifiable_rows"]:
            rows.append({"view": view, **col_profile})
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "column_profiles.csv", index=False)

    # Flat CSV summary of key counts
    key_counts_rows = []
    for view, profile in sheet_profiles.items():
        key_counts_rows.append(
            {
                "view": view,
                "physical_rows": profile["physical_rows"],
                "n_identifiable_observations": profile["n_identifiable_observations"],
                "n_incomplete_rows": profile["n_incomplete_rows"],
                "distinct_shop_product_pairs": profile["distinct_shop_product_pairs"],
                "distinct_shops": profile["distinct_shops"],
                "repeated_rows_within_view": profile["repeated_rows_within_view"],
            }
        )
    pd.DataFrame(key_counts_rows).to_csv(RESULTS_DIR / "key_counts.csv", index=False)

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
