"""Run the reproducible BM25 product-search baseline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase2_semantic_search.product_baseline import run_product_bm25_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="data/processed/product_catalog_v1.json")
    parser.add_argument("--queries", default="data/processed/product_queries_v1.json")
    parser.add_argument(
        "--output",
        default="data/processed/phase2_product_bm25_baseline.json",
    )
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    result = run_product_bm25_baseline(
        Path(args.catalog),
        Path(args.queries),
        Path(args.output),
        top_k=args.top_k,
    )
    metrics = result["metrics"]
    latency = result["latency_ms"]
    print(
        "BM25 baseline:",
        f"Recall@{args.top_k}={metrics[f'recall@{args.top_k}']:.4f},",
        f"MRR@{args.top_k}={metrics[f'mrr@{args.top_k}']:.4f},",
        f"P95={latency['p95']:.3f}ms,",
        f"bad_cases={len(result['bad_cases'])}",
    )


if __name__ == "__main__":
    main()
