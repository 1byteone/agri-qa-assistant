"""Rank-based fusion utilities for Dense + Sparse experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FusedResult:
    doc_id: str
    score: float
    best_rank: int


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[str]],
    *,
    rrf_k: int = 60,
) -> list[FusedResult]:
    """Fuse ranked document IDs without assuming score scales are comparable."""

    if rrf_k <= 0:
        raise ValueError("rrf_k must be positive")

    scores: dict[str, float] = {}
    best_rank: dict[str, int] = {}
    for ranking in rankings.values():
        seen: set[str] = set()
        for rank, doc_id in enumerate(ranking, start=1):
            if doc_id in seen:
                continue
            seen.add(doc_id)
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
            best_rank[doc_id] = min(best_rank.get(doc_id, rank), rank)

    results = [
        FusedResult(doc_id=doc_id, score=score, best_rank=best_rank[doc_id])
        for doc_id, score in scores.items()
    ]
    return sorted(results, key=lambda item: (-item.score, item.best_rank, item.doc_id))

