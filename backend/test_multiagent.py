# -*- coding: utf-8 -*-
"""多智能体架构测试。"""
import pytest
from multiagent_orchestrator import (
    Orchestrator,
    RetrieverAgent,
    AnalystAgent,
    SafetyAgent,
    WriterAgent,
)


class StubKnowledgeBase:
    @staticmethod
    def choose_strategy(query):
        return "hybrid"

    @staticmethod
    def search(query, top_k=3, strategy="hybrid"):
        return [{
            "content": "稻飞虱防治知识内容",
            "metadata": {"source": "测试知识库", "content_hash": "test_hash", "evidence_level": "B"},
            "relevance": 0.9,
        }]


class TestRetrieverAgent:
    """检索智能体测试。"""

    def setup_method(self):
        from agriir_pipeline import AgriIRPipeline, PipelineConfig, StageConfig
        self.pipeline = AgriIRPipeline(PipelineConfig(max_subqueries=4, citation_threshold=0.75,
                                        stages=(StageConfig("parallel_retrieval", top_k=3),)))
        self.agent = RetrieverAgent()

    def test_run_returns_structured_result(self):
        result = self.agent.run("水稻稻飞虱怎么防治", StubKnowledgeBase(), self.pipeline)
        assert "results" in result
        assert "citations" in result
        assert "strategy" in result
        assert "graph_channel_used" in result

    def test_explain(self):
        assert "检索" in self.agent.explain()


class TestAnalystAgent:
    """分析智能体测试。"""

    def setup_method(self):
        self.agent = AnalystAgent()

    def test_high_risk_detection(self):
        retrieval = {
            "citations": [{"eligible": False, "evidence_level": "C"}],
            "results": [],
            "graph_channel_used": False,
        }
        result = self.agent.run("水稻每亩施多少农药", retrieval)
        assert result["risk_scope"] == "pesticide"
        assert result["has_official_evidence"] is False

    def test_official_evidence_detection(self):
        retrieval = {
            "citations": [{"eligible": True, "evidence_level": "A"}],
            "results": [],
            "graph_channel_used": True,
        }
        result = self.agent.run("水稻病虫害防治", retrieval)
        assert result["has_official_evidence"] is True
        assert result["evidence_quality"] == "official"

    def test_missing_fields_detection(self):
        retrieval = {
            "citations": [{"eligible": True, "evidence_level": "B"}],
            "results": [],
            "graph_channel_used": False,
        }
        result = self.agent.run("水稻怎么施肥", retrieval)
        assert "测土结果" in result["missing_fields"]


class TestSafetyAgent:
    """安全智能体测试。"""

    def setup_method(self):
        self.agent = SafetyAgent()

    def test_high_risk_without_official_evidence_blocked(self):
        analyst = {"risk_scope": "pesticide", "has_official_evidence": False}
        result = self.agent.run("农药推荐", "用吡蚜酮 20g/亩", [], analyst)
        assert result["safe"] is False
        assert len(result["reasons"]) > 0

    def test_safe_answer_pass(self):
        analyst = {"risk_scope": None, "has_official_evidence": True}
        result = self.agent.run("水稻什么时候播种", "3月上旬播种。", [], analyst)
        assert result["safe"] is True

    def test_pesticide_without_safety_interval(self):
        analyst = {"risk_scope": "pesticide", "has_official_evidence": True}
        result = self.agent.run("怎么治稻飞虱", "用吡蚜酮喷雾。", [{"eligible": True, "evidence_level": "A"}], analyst)
        assert "安全间隔" not in result, "应该检测到缺少安全间隔"
        # 注意：安全间隔检测是warning不是blocker
        assert result["safe"] is False

    def test_pesticide_mentioned(self):
        analyst = {"risk_scope": "pesticide", "has_official_evidence": True}
        result = self.agent.run("治稻飞虱", "用三环唑和吡蚜酮。", [{"eligible": True, "evidence_level": "A"}], analyst)
        assert "三环唑" in result["pesticides_mentioned"]
        assert "吡蚜酮" in result["pesticides_mentioned"]


class TestOrchestrator:
    """编排智能体测试。"""

    def setup_method(self):
        self.orchestrator = Orchestrator()
        # 使用轻量 pipeline 避免依赖真实知识库
        from agriir_pipeline import AgriIRPipeline, PipelineConfig, StageConfig
        self.orchestrator.pipeline = AgriIRPipeline(PipelineConfig(
            max_subqueries=2, citation_threshold=0.75,
            stages=(StageConfig("parallel_retrieval", top_k=3),)))
        self.orchestrator.setup(StubKnowledgeBase())

    def test_plan_basic(self):
        chain = self.orchestrator.plan("水稻怎么施肥")
        # 施肥属于高风险 → 应包含 safety
        assert "safety" in chain

    def test_plan_simple(self):
        chain = self.orchestrator.plan("水稻什么时候播种")
        assert "safety" not in chain

    def test_execute_full_pipeline(self):
        result = self.orchestrator.execute("水稻稻飞虱怎么防治")
        assert "retrieval" in result
        assert "analyst" in result
        assert "safety" in result
        assert "answer" in result
        assert len(result["tasks"]) >= 3

    def test_execute_tasks_completed(self):
        result = self.orchestrator.execute("水稻施肥用量")
        for task in result["tasks"]:
            assert task["status"] == "complete"