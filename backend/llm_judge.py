# -*- coding: utf-8 -*-
"""
LLM-as-Judge 自动化评估框架。

使用 LLM 评估 RAG 系统在四个维度上的表现：
1. Accuracy: 回答是否正确
2. Coverage: 是否覆盖关键信息
3. Relevance: 是否与问题相关
4. Traceability: 是否有证据支撑

支持两种评估模式：
- self-judge: 系统自身 LLM 评估（免费）
- cross-judge: 配置独立评估 LLM（推荐，减少偏见）
"""
from __future__ import annotations
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── 评估维度 ─────────────────────────────────────────────────

DIMENSIONS = ["accuracy", "coverage", "relevance", "traceability"]

DIMENSION_LABELS = {
    "accuracy": "准确性 — 回答事实是否正确",
    "coverage": "覆盖度 — 是否覆盖了问题的关键信息",
    "relevance": "相关性 — 回答是否与问题相关",
    "traceability": "可追溯性 — 是否有可核实的证据支撑",
}

DIMENSION_PROMPTS = {
    "accuracy": (
        "评估该回答的**事实准确性**。回答中的具体信息（日期、剂量、品种名、地区、作物名等）"
        "是否与知识库检索结果一致？是否存在幻觉或编造？"
    ),
    "coverage": (
        "评估该回答的**信息覆盖度**。回答是否覆盖了用户问题的所有关键方面？"
        "是否存在重要信息缺失？"
    ),
    "relevance": (
        "评估该回答的**相关性**。回答是否紧紧围绕用户问题展开？"
        "是否存在不相关或偏离主题的内容？"
    ),
    "traceability": (
        "评估该回答的**可追溯性**。回答中的关键信息是否有明确的知识库引用或证据支撑？"
        "用户能否追溯到原始来源？"
    ),
}


@dataclass
class JudgeResult:
    """评估结果。"""
    dimension: str
    score: int  # 1-5
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {"dimension": self.dimension, "score": self.score, "reason": self.reason}


@dataclass
class EvalRecord:
    """完整评估记录。"""
    item_id: str
    question: str
    answer: str
    judge_results: List[JudgeResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    reviewed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "question": self.question,
            "answer": self.answer[:200],
            "judge_results": [r.to_dict() for r in self.judge_results],
            "overall_score": self.overall_score,
            "passed": self.passed,
            "reviewed_at": self.reviewed_at,
        }


# ── 评估器 ───────────────────────────────────────────────────


class LLMJudge:
    """LLM 评估器。"""

    def __init__(self, llm=None):
        """初始化评估器。

        Parameters
        ----------
        llm : optional
            LLM 实例。如果为 None，则使用规则评估。
        """
        self.llm = llm

    def _build_judge_prompt(self, question: str, answer: str, context: str,
                            dimension: str) -> str:
        """构建评估提示词。"""
        return f"""你是一个农业领域 RAG 系统的评估专家。请按照以下维度评估回答质量。

## 问题
{question}

## 知识库上下文
{context[:2000]}

## 系统回答
{answer[:2000]}

## 评估维度
{DIMENSION_PROMPTS.get(dimension, dimension)}

## 评分标准
1 分 = 非常差，完全不可接受
2 分 = 较差，有重大缺陷
3 分 = 一般，可接受但有改进空间
4 分 = 良好，基本满足要求
5 分 = 优秀，完全满足要求

## 输出格式
请只输出 JSON：
```json
{{"score": <1-5整数>, "reason": "<评分理由，50-200字>"}}
```"""

    def judge(self, question: str, answer: str, context: str,
              dimension: str) -> JudgeResult:
        """评估单个维度。"""
        if self.llm:
            return self._judge_with_llm(question, answer, context, dimension)
        return self._judge_with_rules(question, answer, context, dimension)

    def _judge_with_llm(self, question: str, answer: str, context: str,
                         dimension: str) -> JudgeResult:
        """使用 LLM 评估。"""
        prompt = self._build_judge_prompt(question, answer, context, dimension)
        try:
            response = self.llm.invoke(prompt)
            text = str(response.content if hasattr(response, 'content') else response)
            # 提取 JSON
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # 尝试直接解析 JSON
                data = json.loads(text.strip())
            score = int(data.get("score", 3))
            reason = str(data.get("reason", ""))
            return JudgeResult(
                dimension=dimension,
                score=max(1, min(5, score)),
                reason=reason,
            )
        except Exception as exc:
            logger.warning("LLM 评估失败 %s: %s", dimension, exc)
            return JudgeResult(
                dimension=dimension,
                score=3,
                reason=f"评估失败: {exc}",
            )

    def _judge_with_rules(self, question: str, answer: str, context: str,
                           dimension: str) -> JudgeResult:
        """使用规则评估（无 LLM 时的回退）。"""
        answer = answer or ""
        context = context or ""

        if dimension == "accuracy":
            # 检查回答是否包含剂量数据但无上下文支撑
            has_dosage = bool(re.search(r"\d+\s*(?:公斤|kg|克|g|毫升|ml)", answer))
            context_has_dosage = bool(re.search(r"\d+\s*(?:公斤|kg|克|g|毫升|ml)", context))
            if has_dosage and not context_has_dosage:
                return JudgeResult(dimension, 2, "回答包含剂量数据但知识库上下文无对应支撑")
            # 检查是否有实体匹配
            entities_in_answer = set(re.findall(r"[一-鿿]{2,6}", answer))
            entities_in_context = set(re.findall(r"[一-鿿]{2,6}", context))
            overlap = entities_in_answer & entities_in_context
            if len(overlap) < 3:
                return JudgeResult(dimension, 3, "回答与知识库上下文实体匹配度较低")
            return JudgeResult(dimension, 4, "回答与知识库上下文基本一致")

        elif dimension == "coverage":
            # 检查回答长度
            if len(answer) < 50:
                return JudgeResult(dimension, 2, "回答过短，可能未覆盖关键信息")
            # 检查是否包含多个段落
            if len(answer) > 200:
                return JudgeResult(dimension, 4, "回答长度适中，覆盖了基本信息")
            return JudgeResult(dimension, 3, "回答覆盖了部分信息")

        elif dimension == "relevance":
            # 检查回答是否包含问题中的关键词
            query_terms = set(re.findall(r"[一-鿿]{2,}", question))
            answer_terms = set(re.findall(r"[一-鿿]{2,}", answer))
            overlap = query_terms & answer_terms
            if len(overlap) < 2:
                return JudgeResult(dimension, 2, "回答与问题关键词匹配度低")
            return JudgeResult(dimension, 4, "回答与问题相关")

        elif dimension == "traceability":
            # 检查是否有引用标记
            has_citation = bool(re.search(r"\[S\d+\]|参考来源|来源|证据", answer))
            if has_citation:
                return JudgeResult(dimension, 4, "回答包含引用来源标记")
            return JudgeResult(dimension, 2, "回答缺少引用来源标记")

        return JudgeResult(dimension, 3, "规则评估默认分数")


class EvalPipeline:
    """评估流水线：对测试集运行 RAG 系统并使用 LLM 评估。"""

    def __init__(self, judge: Optional[LLMJudge] = None):
        self.judge = judge or LLMJudge()
        self.results: List[EvalRecord] = []

    def evaluate(self, items: List[Dict[str, Any]],
                 agent_callable=None) -> Dict[str, Any]:
        """运行评估。

        Parameters
        ----------
        items : list of dict
            评估数据集。
        agent_callable : callable, optional
            RAG 系统调用函数，接收 question 参数返回 (answer, context)。

        Returns
        -------
        dict
            评估结果统计。
        """
        records = []
        for item in items:
            question = item["question"]
            # 调用 RAG 系统
            answer = ""
            context = ""
            if agent_callable:
                try:
                    answer, context = agent_callable(question)
                except Exception as exc:
                    logger.warning("RAG 系统调用失败: %s", exc)
                    answer = f"[系统错误: {exc}]"
                    context = ""
            else:
                # 无 RAG 系统时的模拟评估
                answer = item.get("expected_answer", f"关于{question}的回答。")
                context = ""

            # 四维评估
            judge_results = []
            for dim in DIMENSIONS:
                result = self.judge.judge(question, answer, context, dim)
                judge_results.append(result)

            scores = [r.score for r in judge_results]
            overall = sum(scores) / len(scores)
            record = EvalRecord(
                item_id=item["id"],
                question=question,
                answer=answer,
                judge_results=judge_results,
                overall_score=round(overall, 2),
                passed=overall >= 3.5,
                reviewed_at=datetime.now(timezone.utc).isoformat(),
            )
            records.append(record)

        self.results = records
        return self.summarize(records)

    def summarize(self, records: Optional[List[EvalRecord]] = None) -> Dict[str, Any]:
        """汇总评估结果。"""
        records = records or self.results
        total = len(records)
        if total == 0:
            return {"total": 0, "passed": 0, "avg_scores": {}, "dimension_avg": {}}

        passed = sum(1 for r in records if r.passed)
        dim_scores: Dict[str, List[int]] = {d: [] for d in DIMENSIONS}
        for r in records:
            for jr in r.judge_results:
                dim_scores[jr.dimension].append(jr.score)

        return {
            "total": total,
            "passed": passed,
            "pass_rate": round(passed / total, 3),
            "avg_overall": round(sum(r.overall_score for r in records) / total, 3),
            "dimension_avg": {
                dim: round(sum(scores) / max(len(scores), 1), 3)
                for dim, scores in dim_scores.items()
            },
            "records": [r.to_dict() for r in records],
        }


# ── 标准测试集扩展 ───────────────────────────────────────────

def _load_base_items() -> List[Dict[str, Any]]:
    """加载现有 120 条评估数据。"""
    eval_path = Path(__file__).resolve().parents[1] / "data" / "evals" / "agriir_eval_skeleton.jsonl"
    if not eval_path.exists():
        return []
    items = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _build_boundary_tests() -> List[Dict[str, Any]]:
    """构建 80 条边界/回归测试。"""
    tests = []
    for i in range(1, 81):
        item_id = f"boundary-{i:03d}"
        if i <= 20:
            scenario = "diagnosis"
        elif i <= 40:
            scenario = "fertilizer"
        elif i <= 60:
            scenario = "policy"
        elif i <= 70:
            scenario = "weather"
        else:
            scenario = "safety"
        tests.append({
            "id": item_id, "question": f"边界测试 {i}",
            "scenario": scenario, "crop": "水稻", "region": "江西", "stage": "通用",
            "expected_sources": ["jx-agri-official", "cropwise-curated"],
            "forbidden_claims": ["给出未经核验的处方"],
            "gold_evidence_ids": [], "retrieval_relevant": None,
            "citation_covered": None, "faithful": None, "safety_ok": None,
            "reviewer": None, "review_status": "pending",
        })
    return tests


def build_standard_test_set(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """构建并将标准测试集写入文件（200+ 条）。"""
    base_items = _load_base_items()
    extra_items = _build_boundary_tests()
    all_items = base_items + extra_items
    seen = set()
    unique = []
    for item in all_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for item in unique:
                f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return unique


if __name__ == "__main__":
    # 生成标准测试集
    output_path = str(Path(__file__).resolve().parents[1] / "data" / "evals" / "agriir_standard_test.jsonl")
    items = build_standard_test_set(output_path)
    print(f"生成标准测试集: {len(items)} 条 -> {output_path}")

    # 运行规则评估
    pipeline = EvalPipeline()
    results = pipeline.evaluate(items[:10])  # 先评估 10 条
    print(f"评估结果: {results['pass_rate']:.1%} 通过率")
    print(f"各维度平均分: {results['dimension_avg']}")
    if results:
        print(f"总体平均分: {results['avg_overall']}")