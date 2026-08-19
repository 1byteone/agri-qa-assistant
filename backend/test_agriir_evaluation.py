import json

import pytest

from agriir_evaluation import SCENARIO_COUNTS, annotate_eval_item, build_eval_skeleton, build_review_queue, evaluate_retrieval
from agriir_pipeline import AgriIRPipeline


class StubKnowledgeBase:
    @staticmethod
    def choose_strategy(_query):
        return "hybrid"

    @staticmethod
    def search(_query, top_k=3, strategy="hybrid"):
        return [{"content": "江西水稻知识", "metadata": {"evidence_id": "E-1"}, "relevance": 0.8}][:top_k]


def test_eval_skeleton_has_the_frozen_p0_quota():
    items = build_eval_skeleton()
    assert len(items) == 120
    assert {scenario: sum(item["scenario"] == scenario for item in items) for scenario in SCENARIO_COUNTS} == SCENARIO_COUNTS
    assert all(item["reviewer"] is None for item in items)


def test_unlabeled_evaluation_never_claims_recall():
    report = evaluate_retrieval(StubKnowledgeBase(), AgriIRPipeline(), build_eval_skeleton(), limit=3)
    assert report["candidate_retrieval_rate"] == 1.0
    assert report["traceable_candidate_retrieval_rate"] == 1.0
    assert report["official_candidate_retrieval_rate"] == 0.0
    assert report["scenario_coverage"]["diagnosis"]["traceable_candidate_retrieval_rate"] == 1.0
    assert report["recall_at_k"] is None
    assert report["quality_status"] == "requires_expert_annotation"


def test_expert_labels_produce_distinct_quality_metrics():
    items = build_eval_skeleton()[:2]
    items[0].update({"review_status": "expert_approved", "gold_evidence_ids": ["E-1"], "citation_covered": True, "faithful": True, "safety_ok": True})
    items[1].update({"review_status": "expert_approved", "gold_evidence_ids": ["E-2"], "citation_covered": False, "faithful": True, "safety_ok": False})
    report = evaluate_retrieval(StubKnowledgeBase(), AgriIRPipeline(), items)
    assert report["recall_at_k"] == 0.5
    assert report["citation_coverage"] == 0.5
    assert report["faithfulness_rate"] == 1.0
    assert report["safety_coverage"] == 0.5


def test_annotation_accepts_only_known_evidence_ids(tmp_path):
    path = tmp_path / "eval.jsonl"
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in build_eval_skeleton()) + "\n", encoding="utf-8")
    updated = annotate_eval_item("diagnosis-001", {"reviewer": "农技专家", "gold_evidence_ids": ["E-1"], "citation_covered": True, "faithful": True, "safety_ok": True}, {"E-1"}, path)
    assert updated["review_status"] == "expert_approved"
    with pytest.raises(ValueError, match="未知 evidence_id"):
        annotate_eval_item("diagnosis-002", {"reviewer": "农技专家", "gold_evidence_ids": ["missing"], "citation_covered": True, "faithful": True, "safety_ok": True}, {"E-1"}, path)


def test_review_queue_exports_candidates_without_creating_gold_labels():
    item = build_eval_skeleton()[0]
    queue = build_review_queue(StubKnowledgeBase(), AgriIRPipeline(), [item])
    assert queue[0]["id"] == item["id"]
    assert queue[0]["candidates"][0]["evidence_id"] == "E-1"
    assert "gold_evidence_ids" not in queue[0]
