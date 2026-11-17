"""
Stage 3 SQL analysis runner for the Shopee Singapore Listing Samples dataset.

Executes the SQL files in sql/ against the Stage 2 processed CSVs via DuckDB,
exports each named result set to results/sql/<name>.csv, and writes a
validation summary (results/sql/validation_summary.json) reconciling the SQL
output against the Stage 1/2 headline figures.

Does not modify data/raw or data/processed. Only reads them.
"""

import json
import re
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SQL_DIR = PROJECT_ROOT / "sql"
RESULTS_DIR = PROJECT_ROOT / "results" / "sql"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

NAME_MARKER = re.compile(r"^--\s*name:\s*(\S+)\s*$", re.MULTILINE)


def split_named_statements(sql_text: str):
    """Split a .sql file into (name, statement) pairs on '-- name: <label>' markers."""
    markers = list(NAME_MARKER.finditer(sql_text))
    statements = []
    for i, m in enumerate(markers):
        name = m.group(1)
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(sql_text)
        statement = sql_text[start:end].strip()
        if statement:
            statements.append((name, statement))
    return statements


def main():
    con = duckdb.connect(database=":memory:")

    obs_path = str(PROCESSED_DIR / "listings_observations.csv").replace("'", "''")
    ul_path = str(PROCESSED_DIR / "listings_unique_reference.csv").replace("'", "''")

    # Explicit VARCHAR typing on identifier columns: shop_id/product_id/listing_key
    # must retain string semantics (never auto-inferred as numeric by DuckDB).
    con.execute(f"""
        CREATE VIEW observations AS
        SELECT * FROM read_csv_auto(
            '{obs_path}',
            types={{'listing_key': 'VARCHAR', 'shop_id': 'VARCHAR', 'product_id': 'VARCHAR', 'id': 'VARCHAR'}}
        )
    """)
    con.execute(f"""
        CREATE VIEW unique_listings AS
        SELECT * FROM read_csv_auto(
            '{ul_path}',
            types={{'listing_key': 'VARCHAR', 'shop_id': 'VARCHAR', 'product_id': 'VARCHAR'}}
        )
    """)

    all_results = {}
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        sql_text = sql_file.read_text()
        statements = split_named_statements(sql_text)
        for name, statement in statements:
            df = con.execute(statement).df()
            out_path = RESULTS_DIR / f"{name}.csv"
            df.to_csv(out_path, index=False)
            all_results[name] = df
            print(f"[{sql_file.name}] -> {name}.csv ({len(df)} rows)")

    # --- Validation against Stage 1 / Stage 2 headline figures ---
    totals = all_results["overview_totals"]
    overall_row = totals[(totals["section"] == "overall")].iloc[0]
    n_observations = int(overall_row["observations"])
    n_distinct_listings = int(overall_row["distinct_listings"])
    n_distinct_shops = int(overall_row["distinct_shops"])

    overlap = all_results["cross_view_overlap"]
    overlap_sum = int(overlap["distinct_listings"].sum())

    discount_status = all_results["discount_status_by_view"]
    discount_status_total = int(discount_status["n"].sum())

    cat_total = all_results["category_view_distinct_total"].iloc[0]

    validation = {
        "n_observations": n_observations,
        "n_distinct_listings": n_distinct_listings,
        "n_distinct_shops": n_distinct_shops,
        "reconciles_2996_observations": n_observations == 2996,
        "reconciles_2727_distinct_listings": n_distinct_listings == 2727,
        "reconciles_968_distinct_shops": n_distinct_shops == 968,
        "cross_view_overlap_sum": overlap_sum,
        "cross_view_overlap_matches_total_distinct_listings": overlap_sum == n_distinct_listings,
        "discount_status_total_observations": discount_status_total,
        "discount_status_total_matches_2996": discount_status_total == 2996,
        "category_view_n_rows": int(cat_total["n_rows_category_view"]),
        "category_view_n_distinct_listings": int(cat_total["n_distinct_listings_category_view"]),
        "category_view_distinct_matches_stage1_956": int(cat_total["n_distinct_listings_category_view"]) == 956,
    }

    with open(RESULTS_DIR / "validation_summary.json", "w") as f:
        json.dump(validation, f, indent=2, default=str)

    print()
    print(json.dumps(validation, indent=2, default=str))

    failures = [k for k, v in validation.items() if k.startswith("reconciles_") or "_matches_" in k]
    failed = [k for k in failures if not validation[k]]
    if failed:
        raise RuntimeError(f"Validation failures: {failed}")
    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
