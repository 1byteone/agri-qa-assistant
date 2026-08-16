"""Small, deterministic retrieval metrics for qrels-based experiments."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence


def recall_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
    *,
    k: int = 10,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if not relevant_ids:
        return 0.0
    return len(set(ranked_ids[:k]) & set(relevant_ids)) / len(set(relevant_ids))


def mrr_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
    *,
    k: int = 10,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    relevant = set(relevant_ids)
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def evaluate_qrels(
    runs: Mapping[str, Sequence[str]],
    qrels: Mapping[str, Collection[str]],
    *,
    k: int = 10,
) -> dict[str, float]:
    """Average Recall@K and MRR@K over the qrels query IDs."""

    if not qrels:
        raise ValueError("qrels must not be empty")
    recalls = [recall_at_k(runs.get(query_id, ()), relevant, k=k) for query_id, relevant in qrels.items()]
    mrrs = [mrr_at_k(runs.get(query_id, ()), relevant, k=k) for query_id, relevant in qrels.items()]
    return {
        f"recall@{k}": sum(recalls) / len(recalls),
        f"mrr@{k}": sum(mrrs) / len(mrrs),
    }

