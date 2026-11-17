"""
Produces a sanitised, aggregate-only copy of results/stage1/summary.json for inclusion
in ChatGPT review ZIPs. The original local diagnostic file is never modified.

results/stage1/summary.json's cross_view_price_check.conflicting_pairs field records, for
each of the 9 cross-view price conflicts, the shop_id, product_id, and the price recorded
in each view -- i.e. identifiable row-level third-party records with prices attached.
That level of detail is appropriate for local diagnosis but not for a redistributed
review archive while the dataset's reuse rights remain unresolved (see CLAUDE.md).

This script replaces conflicting_pairs with an aggregate-only summary (count, view-pairs
involved, min/max/mean spread) -- the same facts already reported in
results/sql/price_conflict_summary.csv and price_conflict_spread_distribution.csv -- and
writes the result to results/stage1/summary_sanitized.json, which is what review ZIPs
should include instead of summary.json.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGE1_RESULTS_DIR = PROJECT_ROOT / "results" / "stage1"


def main():
    with open(STAGE1_RESULTS_DIR / "summary.json") as f:
        summary = json.load(f)

    pairs = summary["cross_view_price_check"]["conflicting_pairs"]
    spreads = []
    view_pair_counts = {}
    for p in pairs:
        prices = list(p["prices_by_view"].values())
        spread_pct = 100 * (max(prices) - min(prices)) / min(prices)
        spreads.append(spread_pct)
        key = "+".join(sorted(p["views"]))
        view_pair_counts[key] = view_pair_counts.get(key, 0) + 1

    sanitized = json.loads(json.dumps(summary))  # deep copy
    sanitized["cross_view_price_check"]["conflicting_pairs"] = (
        "REDACTED: individual shop_id/product_id/price records removed for the review "
        "archive -- see aggregate fields below and results/sql/price_conflict_summary.csv "
        "/ price_conflict_spread_distribution.csv for the full aggregate breakdown."
    )
    sanitized["cross_view_price_check"]["conflicting_pairs_aggregate"] = {
        "n_conflicting_pairs": len(pairs),
        "view_pair_combination_counts": view_pair_counts,
        "spread_pct_min": round(min(spreads), 1) if spreads else None,
        "spread_pct_max": round(max(spreads), 1) if spreads else None,
        "spread_pct_mean": round(sum(spreads) / len(spreads), 1) if spreads else None,
    }

    out_path = STAGE1_RESULTS_DIR / "summary_sanitized.json"
    with open(out_path, "w") as f:
        json.dump(sanitized, f, indent=2, default=str)

    print(f"Wrote sanitised copy to {out_path}")
    print(f"Redacted {len(pairs)} row-level conflicting-pair records.")


if __name__ == "__main__":
    main()
