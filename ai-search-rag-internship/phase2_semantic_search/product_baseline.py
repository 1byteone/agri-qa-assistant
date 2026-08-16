"""BM25 baseline evaluation for the synthetic product-search dataset."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
import json
from math import ceil
from pathlib import Path
from time import perf_counter_ns
from typing import Any
from collections.abc import Callable

from .bm25 import BM25Retriever
from .metrics import evaluate_qrels, mrr_at_k, recall_at_k


def _nearest_rank_percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = max(0, min(len(ordered) - 1, ceil(percentile / 100 * len(ordered)) - 1))
    return ordered[index]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_product_bm25(
    catalog: list[Mapping[str, Any]],
    queries: list[Mapping[str, Any]],
    *,
    top_k: int = 10,
    warmup_queries: int = 3,
    query_transform: Callable[[str], str] | None = None,
    experiment_id: str = "EXP-20260816-PRODUCT-BM25-001",
    experiment_type: str = "synthetic_product_search_baseline",
) -> dict[str, Any]:
    """Run one transparent BM25 experiment and retain query-level evidence."""

    retriever = BM25Retriever(catalog)
    transform = query_transform or (lambda query: query)
    for query in queries[:warmup_queries]:
        transform_result = transform(str(query["query"]))
        retriever.search(transform_result, top_k=top_k)

    runs: dict[str, list[str]] = {}
    qrels: dict[str, list[str]] = {}
    details: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    for query in queries:
        query_id = str(query["query_id"])
        query_text = str(query["query"])
        retrieval_query = transform(query_text)
        relevant_ids = [str(item) for item in query["relevant_ids"]]
        started_ns = perf_counter_ns()
        results = retriever.search(retrieval_query, top_k=top_k)
        latency_ms = (perf_counter_ns() - started_ns) / 1_000_000
        ranked_ids = [result.doc_id for result in results]
        runs[query_id] = ranked_ids
        qrels[query_id] = relevant_ids
        latencies_ms.append(latency_ms)
        details.append(
            {
                "query_id": query_id,
                "query": query_text,
                "retrieval_query": retrieval_query,
                "query_type": str(query["query_type"]),
                "family_id": str(query["family_id"]),
                "required_feature": str(query["required_feature"]),
                "relevant_ids": relevant_ids,
                "ranked_ids": ranked_ids,
                "recall": recall_at_k(ranked_ids, relevant_ids, k=top_k),
                "mrr": mrr_at_k(ranked_ids, relevant_ids, k=top_k),
                "top_results": [
                    {
                        "id": result.doc_id,
                        "score": round(result.score, 6),
                        "title": str(result.metadata.get("title", "")),
                    }
                    for result in results[:3]
                ],
                "latency_ms": round(latency_ms, 6),
            }
        )

    metrics = evaluate_qrels(runs, qrels, k=top_k)
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for detail in details:
        by_type[detail["query_type"]].append(detail)
    query_type_metrics = {
        query_type: {
            "query_count": len(items),
            f"recall@{top_k}": sum(item["recall"] for item in items) / len(items),
            f"mrr@{top_k}": sum(item["mrr"] for item in items) / len(items),
        }
        for query_type, items in sorted(by_type.items())
    }
    bad_cases = [
        {
            "query_id": item["query_id"],
            "query": item["query"],
            "query_type": item["query_type"],
            "relevant_ids": item["relevant_ids"],
            "ranked_ids": item["ranked_ids"],
            "recall": item["recall"],
            "mrr": item["mrr"],
            "diagnosis_hint": (
                "先检查词面覆盖、中文 tokenizer、字段拼接和标注定义；"
                "不要直接把失败归因于 embedding。"
            ),
        }
        for item in details
        if item["recall"] == 0
    ][:10]

    return {
        "experiment_id": experiment_id,
        "experiment_type": experiment_type,
        "data_version": "product-search-v1",
        "retriever": "in_memory_bm25",
        "tokenizer": "single_chinese_character_or_ascii_word",
        "parameters": {"k1": retriever.k1, "b": retriever.b, "top_k": top_k},
        "environment": {"device": "CPU", "warmup_queries": warmup_queries},
        "document_count": len(catalog),
        "query_count": len(queries),
        "metrics": metrics,
        "latency_ms": {
            "mean": sum(latencies_ms) / len(latencies_ms),
            "p50": _nearest_rank_percentile(latencies_ms, 50),
            "p95": _nearest_rank_percentile(latencies_ms, 95),
            "p99": _nearest_rank_percentile(latencies_ms, 99),
        },
        "query_type_metrics": query_type_metrics,
        "bad_cases": bad_cases,
        "query_details": details,
    }


def run_product_bm25_baseline(
    catalog_path: str | Path,
    queries_path: str | Path,
    output_path: str | Path,
    *,
    top_k: int = 10,
) -> dict[str, Any]:
    catalog = _load_json(catalog_path)
    queries = _load_json(queries_path)
    result = evaluate_product_bm25(catalog, queries, top_k=top_k)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
