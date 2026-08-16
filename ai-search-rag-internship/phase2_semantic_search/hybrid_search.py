"""Hybrid ranking adapters shared by BM25, Dense and future product APIs."""

from __future__ import annotations

from collections.abc import Sequence

from .bm25 import SearchResult
from .fusion import FusedResult, reciprocal_rank_fusion


def fuse_bm25_and_dense(
    bm25_results: Sequence[SearchResult],
    dense_doc_ids: Sequence[str],
    *,
    top_k: int = 10,
    rrf_k: int = 60,
) -> list[FusedResult]:
    """Fuse rank lists without mixing incomparable BM25/cosine scores."""

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    fused = reciprocal_rank_fusion(
        {
            "bm25": [result.doc_id for result in bm25_results],
            "dense": list(dense_doc_ids),
        },
        rrf_k=rrf_k,
    )
    return fused[:top_k]
