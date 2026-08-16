"""Compare original Query retrieval with a controlled rewrite ablation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase2_semantic_search.product_baseline import evaluate_product_bm25
from phase2_semantic_search.query_rewrite import rewrite_query


def main() -> None:
    catalog_path = Path("data/processed/product_catalog_v1.json")
    queries_path = Path("data/processed/product_queries_v1.json")
    output_path = Path("data/processed/phase2_product_query_rewrite_ablation.json")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    queries = json.loads(queries_path.read_text(encoding="utf-8"))

    baseline = evaluate_product_bm25(
        catalog,
        queries,
        experiment_id="EXP-20260816-PRODUCT-BM25-001",
        experiment_type="synthetic_product_search_baseline",
    )
    candidate = evaluate_product_bm25(
        catalog,
        queries,
        query_transform=lambda query: rewrite_query(query).rewritten_query,
        experiment_id="EXP-20260816-PRODUCT-REWRITE-001",
        experiment_type="synthetic_product_search_query_rewrite_ablation",
    )

    rewritten_queries = [
        detail
        for detail in candidate["query_details"]
        if detail["retrieval_query"] != detail["query"]
    ]
    result = {
        "experiment_id": "EXP-20260816-PRODUCT-REWRITE-001",
        "experiment_type": "synthetic_product_search_query_rewrite_ablation",
        "data_version": "product-search-v1",
        "changed_variable": "query_transform",
        "fixed_conditions": {
            "document_count": len(catalog),
            "query_count": len(queries),
            "retriever": "in_memory_bm25",
            "top_k": 10,
            "k1": 1.5,
            "b": 0.75,
        },
        "baseline": {
            "metrics": baseline["metrics"],
            "latency_ms": baseline["latency_ms"],
            "bad_case_count": len(baseline["bad_cases"]),
        },
        "candidate": {
            "metrics": candidate["metrics"],
            "latency_ms": candidate["latency_ms"],
            "bad_case_count": len(candidate["bad_cases"]),
            "rewritten_query_count": len(rewritten_queries),
            "query_details": candidate["query_details"],
        },
        "metric_delta": {
            "recall@10": candidate["metrics"]["recall@10"] - baseline["metrics"]["recall@10"],
            "mrr@10": candidate["metrics"]["mrr@10"] - baseline["metrics"]["mrr@10"],
        },
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "Query rewrite ablation:",
        f"Recall@10 {baseline['metrics']['recall@10']:.4f} -> {candidate['metrics']['recall@10']:.4f},",
        f"MRR@10 {baseline['metrics']['mrr@10']:.4f} -> {candidate['metrics']['mrr@10']:.4f},",
        f"rewritten_queries={len(rewritten_queries)}",
    )


if __name__ == "__main__":
    main()
