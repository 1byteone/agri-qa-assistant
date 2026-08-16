import numpy as np
import pytest

from phase2_semantic_search.bm25 import SearchResult
from phase2_semantic_search.embedding import normalize_vectors
from phase2_semantic_search.hybrid_search import fuse_bm25_and_dense


def test_normalize_vectors_returns_float32_unit_rows() -> None:
    normalized = normalize_vectors([[3, 4], [0, 0]])

    assert normalized.dtype == np.float32
    assert np.linalg.norm(normalized[0]) == pytest.approx(1.0)
    assert np.allclose(normalized[1], [0.0, 0.0])


def test_hybrid_adapter_fuses_rankings_without_score_addition() -> None:
    bm25_results = [
        SearchResult("exact", 9.0, "", {}),
        SearchResult("shared", 5.0, "", {}),
    ]

    fused = fuse_bm25_and_dense(bm25_results, ["shared", "semantic"], top_k=3, rrf_k=1)

    assert [item.doc_id for item in fused] == ["shared", "exact", "semantic"]
