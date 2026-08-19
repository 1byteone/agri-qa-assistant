# -*- coding: utf-8 -*-
"""
多智能体架构 — 规划-执行-反思协作框架。

智能体：
- Orchestrator: 任务规划与分发
- RetrieverAgent: 专业检索（向量+图谱双通道）
- AnalystAgent: 农业诊断分析、证据质量评估
- SafetyAgent: 农药/化肥/政策安全合规检查
- WriterAgent: 答案格式化与决策卡生成
"""
from __future__ import annotations
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── 任务状态 ─────────────────────────────────────────────────


@dataclass
class AgentTask:
    """子任务。"""
    id: str
    agent: str  # retriever / analyst / safety / writer
    instruction: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    status: str = "pending"  # pending/running/complete/failed
    error: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent": self.agent,
            "instruction": self.instruction,
            "input_data": self.input_data,
            "result": self.result,
            "status": self.status,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


# ── 各智能体 ─────────────────────────────────────────────────


class RetrieverAgent:
    """检索智能体：负责向量 + 图谱双通道检索，返回结构化证据。"""

    def run(self, query: str, knowledge_base: Any, agriir_pipeline: Any,
            scenario_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行检索。

        Returns
        -------
        dict
            包含 results, citations, graph_channel_used, strategy 等字段。
        """
        start = time.perf_counter()
        trace = agriir_pipeline.retrieve(query, knowledge_base, scenario_context)
        duration = (time.perf_counter() - start) * 1000

        return {
            "results": trace.get("results", []),
            "citations": trace.get("citations", []),
            "graph_channel_used": trace.get("graph_channel_used", False),
            "graph_count": trace.get("graph_count", 0),
            "strategy": trace.get("strategy", "hybrid"),
            "subqueries": trace.get("subqueries", [query]),
            "duration_ms": round(duration, 2),
        }

    def explain(self) -> str:
        return "检索智能体：执行向量+图谱双通道检索，聚合证据。"


class AnalystAgent:
    """分析智能体：评估证据质量、识别缺失信息、生成诊断判断。"""

    # 高风险证据范围标签
    RISKY_SCOPES = {
        "pesticide_label", "pesticide_registration", "pesticide_governance",
        "rice_fertilizer_recommendation", "rapeseed_fertilizer_recommendation",
        "citrus_fertilizer_recommendation", "vegetable_fertilizer_recommendation",
        "fertilizer_recommendation", "policy", "technical_standard",
        "animal_health_regulation",
    }

    def run(self, query: str, retrieval: Dict[str, Any]) -> Dict[str, Any]:
        """分析检索结果。

        Returns
        -------
        dict
            包含 evidence_quality, has_official, missing_fields, risk_scope。
        """
        citations = retrieval.get("citations", [])
        results = retrieval.get("results", [])

        eligible = [c for c in citations if c.get("eligible")]
        has_official = any(c.get("evidence_level") == "A" for c in eligible)

        # 判断是否高风险领域
        risk_scope = None
        if re.search(r"农药|药剂|用药|剂量|安全间隔", query or ""):
            risk_scope = "pesticide"
        elif re.search(r"施肥|追肥|肥料|用量", query or ""):
            risk_scope = "fertilizer"
        elif re.search(r"政策|补贴|标准|规范", query or ""):
            risk_scope = "policy"

        # 缺失字段识别
        missing_fields = []
        if re.search(r"诊断|什么病|什么虫|怎么治", query or "") and not re.search(r"叶片|茎|根|穗|叶", query or ""):
            missing_fields.append("现场症状")
        if re.search(r"施肥|追肥|灌溉", query or "") and not re.search(r"测土|土壤|pH", query or ""):
            missing_fields.append("测土结果")

        return {
            "evidence_quality": "official" if has_official else ("" if not citations else "background"),
            "has_official_evidence": has_official,
            "eligible_count": len(eligible),
            "risk_scope": risk_scope,
            "missing_fields": missing_fields,
            "graph_channel_used": retrieval.get("graph_channel_used", False),
        }

    def explain(self) -> str:
        return "分析智能体：评估证据质量，识别高风险领域与缺失信息。"


class SafetyAgent:
    """安全智能体：对高风险回答执行安全合规检查。"""

    FORBIDDEN = ["编制", "伪造", "未经登记", "推荐剂量"]

    def run(self, query: str, answer: str, citations: List[Dict[str, Any]],
            analyst: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全审查。

        Returns
        -------
        dict
            包含 safe, reasons, warnings 等字段。
        """
        warnings = []
        safe = True

        # 1. 高风险领域必须有 A 级证据
        if analyst.get("risk_scope") and not analyst.get("has_official_evidence"):
            warnings.append(f"高风险领域（{analyst['risk_scope']}）缺少 A 级官方证据")
            safe = False

        # 2. 检查剂量数据
        dosage_pattern = re.compile(
            r"\d+(?:\.\d+)?\s*(?:[-~至]\s*\d+(?:\.\d+)?)?\s*(?:公斤|千克|kg|克|g|毫升|ml|升|L|立方米|m³|%)\s*(?:/\s*(?:亩|公顷|株))?"
        )
        has_dosage = bool(dosage_pattern.search(answer or ""))
        if has_dosage and not analyst.get("has_official_evidence"):
            warnings.append("回答包含剂量数据但缺少官方依据")
            safe = False

        # 3. 检查禁用词
        for word in self.FORBIDDEN:
            if word in (answer or ""):
                warnings.append(f"检测到敏感表述: {word}")
                safe = False

        # 4. 农药/化肥安全标签
        pesticide_terms = re.findall(r"吡蚜酮|三环唑|井冈霉素|腐霉利|咪鲜胺|氯虫苯甲酰胺", answer or "")
        if pesticide_terms and "安全间隔" not in (answer or ""):
            warnings.append("回答提到农药但未说明安全间隔期")
            safe = False

        return {
            "safe": safe,
            "reasons": warnings,
            "pesticides_mentioned": list(dict.fromkeys(pesticide_terms)),
        }

    def explain(self) -> str:
        return "安全智能体：执行农药/化肥/政策安全合规审查。"


class WriterAgent:
    """写作智能体：将分析结果与安全审查合成为最终答案。"""

    def synthesize(self, query: str, retrieval: Dict[str, Any],
                   analyst: Dict[str, Any], safety: Dict[str, Any],
                   llm_answer: str = "") -> Dict[str, Any]:
        """合成最终答案。

        Returns
        -------
        dict
            包含 answer, notes 等字段。
        """
        notes = []
        if retrieval.get("graph_channel_used"):
            notes.append("已启用知识图谱补充检索")
        if analyst.get("missing_fields"):
            notes.append(f"建议补充: {', '.join(analyst['missing_fields'])}")
        if not safety.get("safe"):
            notes.extend(safety.get("reasons", []))

        # 组装答案（未调用 LLM 时用检索摘要）
        if llm_answer:
            answer = llm_answer
        else:
            excerpts = []
            for citation in retrieval.get("citations", [])[:3]:
                excerpts.append(citation.get("excerpt", ""))
            answer = "\n\n".join(excerpts) if excerpts else "当前知识库暂无匹配结果。"

        return {"answer": answer, "notes": notes}


class Orchestrator:
    """编排智能体：规划任务顺序并协调各智能体。"""

    def __init__(self):
        from agriir_pipeline import agriir_pipeline as pipeline
        self.retriever = RetrieverAgent()
        self.analyst = AnalystAgent()
        self.safety = SafetyAgent()
        self.writer = WriterAgent()
        self.pipeline = pipeline
        self.knowledge_base = None

    def setup(self, knowledge_base: Any) -> None:
        """注入知识库依赖。"""
        self.knowledge_base = knowledge_base

    def plan(self, query: str) -> List[str]:
        """规划任务链。

        Returns
        -------
        list of str
            智能体执行顺序。
        """
        chain = ["retriever", "analyst"]
        if re.search(r"农药|药剂|施肥|政策|补贴|标准", query or ""):
            chain.append("safety")
        chain.append("writer")
        return chain

    def execute(self, query: str, scenario_context: Optional[Dict[str, Any]] = None,
                llm_answer: str = "") -> Dict[str, Any]:
        """执行多智能体流水线。

        Returns
        -------
        dict
            包含 chain, retrieval, analyst, safety, answer 等字段。
        """
        chain = self.plan(query)
        tasks = []
        start = time.perf_counter()

        # 1. 检索智能体
        t0 = time.perf_counter()
        retrieval = self.retriever.run(query, self.knowledge_base, self.pipeline, scenario_context)
        tasks.append(AgentTask(
            id="retriever", agent="retriever", instruction="双通道检索",
            result=json.dumps({"count": len(retrieval["results"])}, ensure_ascii=False),
            status="complete", duration_ms=time.perf_counter() - t0,
        ).to_dict())

        # 2. 分析智能体
        t0 = time.perf_counter()
        analyst = self.analyst.run(query, retrieval)
        tasks.append(AgentTask(
            id="analyst", agent="analyst", instruction="证据质量评估",
            result=json.dumps({"quality": analyst["evidence_quality"], "risk": analyst["risk_scope"]}, ensure_ascii=False),
            status="complete", duration_ms=time.perf_counter() - t0,
        ).to_dict())

        # 3. 安全智能体（如需要）
        safety = {"safe": True, "reasons": [], "pesticides_mentioned": []}
        if "safety" in chain:
            t0 = time.perf_counter()
            safety = self.safety.run(query, llm_answer, retrieval["citations"], analyst)
            tasks.append(AgentTask(
                id="safety", agent="safety", instruction="安全合规检查",
                result=json.dumps({"safe": safety["safe"]}, ensure_ascii=False),
                status="complete", duration_ms=time.perf_counter() - t0,
            ).to_dict())

        # 4. 写作智能体
        t0 = time.perf_counter()
        writer = self.writer.synthesize(query, retrieval, analyst, safety, llm_answer)
        tasks.append(AgentTask(
            id="writer", agent="writer", instruction="答案合成",
            result=json.dumps({"length": len(writer["answer"])}, ensure_ascii=False),
            status="complete", duration_ms=time.perf_counter() - t0,
        ).to_dict())

        total_duration = (time.perf_counter() - start) * 1000

        return {
            "chain": chain,
            "retrieval": {
                "results": retrieval["results"],
                "citations": retrieval["citations"],
                "graph_channel_used": retrieval["graph_channel_used"],
                "graph_count": retrieval["graph_count"],
                "strategy": retrieval["strategy"],
            },
            "analyst": analyst,
            "safety": safety,
            "answer": writer["answer"],
            "notes": writer["notes"],
            "tasks": tasks,
            "total_duration_ms": round(total_duration, 2),
        }

    def explain(self) -> str:
        return "编排智能体：规划-执行-反思协作，协调检索/分析/安全/写作四角色。"


# 全局编排器
orchestrator = Orchestrator()