import pytest

from phase2_semantic_search.fusion import reciprocal_rank_fusion
from phase2_semantic_search.metrics import evaluate_qrels, mrr_at_k, recall_at_k


def test_rrf_merges_rankings_and_ignores_duplicate_ids() -> None:
    results = reciprocal_rank_fusion(
        {"bm25": ["a", "b", "b"], "dense": ["b", "a", "c"]},
        rrf_k=1,
    )

    assert [item.doc_id for item in results] == ["a", "b", "c"]
    assert results[0].score == pytest.approx(1 / 2 + 1 / 3)
    assert results[0].best_rank == 1


def test_retrieval_metrics() -> None:
    ranked = ["wrong", "target", "other"]

    assert recall_at_k(ranked, {"target", "missing"}, k=2) == pytest.approx(0.5)
    assert mrr_at_k(ranked, {"target"}, k=3) == pytest.approx(0.5)
    assert evaluate_qrels({"q1": ranked, "q2": ["target"]}, {"q1": {"target"}, "q2": {"target"}}, k=3) == {
        "recall@3": 1.0,
        "mrr@3": 0.75,
    }


def test_rrf_requires_positive_constant() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank_fusion({"bm25": ["a"]}, rrf_k=0)

