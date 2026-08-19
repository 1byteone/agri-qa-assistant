# -*- coding: utf-8 -*-
"""LLM-as-Judge 评估框架测试。"""
import pytest
from llm_judge import (
    LLMJudge,
    EvalPipeline,
    JudgeResult,
    EvalRecord,
    DIMENSIONS,
    build_standard_test_set,
)


class TestLLMJudge:
    """LLM 评估器规则模式测试。"""

    def setup_method(self):
        self.judge = LLMJudge()  # 无 LLM，使用规则模式

    def test_accuracy_with_dosage_without_context(self):
        result = self.judge.judge(
            "水稻怎么施肥",
            "每亩施尿素 20kg",
            "水稻施肥的一般原则",
            "accuracy",
        )
        assert result.dimension == "accuracy"
        assert result.score <= 2  # 有剂量但上下文无支撑 → 低分

    def test_accuracy_with_context(self):
        result = self.judge.judge(
            "水稻怎么施肥",
            "水稻分蘖期追施尿素和钾肥，具体用量待官方核验。",
            "水稻分蘖期追施尿素和钾肥，具体用量待官方核验。",
            "accuracy",
        )
        assert result.score >= 3  # 上下文一致 → 中高分

    def test_coverage_short_answer(self):
        result = self.judge.judge("水稻病虫害防治大全", "好", "", "coverage")
        assert result.score <= 2  # 回答过短 → 低分

    def test_relevance_match(self):
        result = self.judge.judge(
            "水稻稻飞虱怎么防治",
            "稻飞虱应在若虫期综合防治，包括生物防治和化学防治。",
            "",
            "relevance",
        )
        # 规则模式下，查询和回答通常有"稻飞虱"和"防治"等关键词重叠
        print(f"relevance score: {result.score}, reason: {result.reason}")
        # 允许 2-4 分，取决于实际匹配度
        assert 2 <= result.score <= 4

    def test_traceability_with_citation(self):
        result = self.judge.judge(
            "施肥建议",
            "建议追施尿素，参考来源[S1]",
            "",
            "traceability",
        )
        assert result.score >= 4  # 有引用标记 → 高分

    def test_traceability_without_citation(self):
        result = self.judge.judge("施肥建议", "建议追施尿素", "", "traceability")
        assert result.score <= 2  # 无引用标记 → 低分

    def test_score_clamped(self):
        result = self.judge.judge("问题", "回答", "上下文", "relevance")
        assert 1 <= result.score <= 5


class TestEvalPipeline:
    """评估流水线测试。"""

    def setup_method(self):
        self.pipeline = EvalPipeline()

    def test_evaluate_basic(self):
        items = [
            {"id": "test-001", "question": "水稻稻飞虱怎么防治？", "scenario": "diagnosis", "expected_answer": "综合防治"},
        ]
        result = self.pipeline.evaluate(items)
        assert result["total"] == 1
        assert "pass_rate" in result
        assert "dimension_avg" in result
        assert "records" in result

    def test_evaluate_with_agent(self):
        def mock_agent(question):
            return "稻飞虱综合防治建议。", "知识库内容：稻飞虱防治"

        items = [
            {"id": "test-002", "question": "水稻稻飞虱防治？", "scenario": "diagnosis"},
            {"id": "test-003", "question": "如何施肥？", "scenario": "fertilizer"},
        ]
        result = self.pipeline.evaluate(items, agent_callable=mock_agent)
        assert result["total"] == 2
        assert result["pass_rate"] >= 0

    def test_summarize_empty(self):
        result = self.pipeline.summarize([])
        assert result["total"] == 0

    def test_dimension_avg_calculation(self):
        records = [
            EvalRecord(
                item_id="a", question="q1", answer="a1",
                judge_results=[
                    JudgeResult("accuracy", 4, "ok"),
                    JudgeResult("coverage", 3, "ok"),
                    JudgeResult("relevance", 4, "ok"),
                    JudgeResult("traceability", 2, "no"),
                ],
                overall_score=3.25, passed=True, reviewed_at="now",
            )
        ]
        result = self.pipeline.summarize(records)
        assert result["total"] == 1
        assert result["dimension_avg"]["accuracy"] == 4.0
        assert result["pass_rate"] == 1.0


class TestStandardTestSet:
    """标准测试集测试。"""

    def test_build_standard_test_set(self):
        items = build_standard_test_set()
        assert len(items) >= 200
        # 检查包含现有 120 条
        base_ids = {f"diagnosis-{i:03d}" for i in range(1, 41)}
        assert base_ids.issubset({item["id"] for item in items})

    def test_no_duplicates(self):
        items = build_standard_test_set()
        ids = [item["id"] for item in items]
        assert len(ids) == len(set(ids))

    def test_has_required_fields(self):
        items = build_standard_test_set()
        for item in items:
            assert "id" in item
            assert "question" in item
            assert "scenario" in item
            assert "forbidden_claims" in item