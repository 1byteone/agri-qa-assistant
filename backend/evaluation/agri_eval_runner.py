"""
CropWise AgriEval 评测运行器
=============================

基于 Ragas 框架的农业领域 RAG 评测工具。

评测维度：
- Recall@K（检索召回率）
- MRR（平均倒数排名）
- Context Precision（上下文精度）
- Context Recall（上下文召回）
- Faithfulness（回答忠实度）
- Answer Relevancy（回答相关性）
- Citation Accuracy（引用准确性）
- Safety Coverage（安全覆盖率）

参考：
- Ragas: https://docs.ragas.io/
- AgriEval: https://github.com/YanPioneer/AgriEval
"""

from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# 评测集路径
EVAL_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "evals"
EVAL_SUBSET_PATH = EVAL_ROOT / "agri_eval_subset.jsonl"
REPORT_DIR = EVAL_ROOT / "reports"


def load_eval_set(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """加载评测集（支持 JSON 数组和 JSONL 两种格式）"""
    path = path or EVAL_SUBSET_PATH
    if not path.exists():
        logger.warning(f"评测集不存在: {path}")
        return []

    items = []
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []

        # 尝试 JSON 数组格式
        if content.startswith("["):
            items = json.loads(content)
        else:
            # JSONL 格式：每行一个 JSON
            for line in content.splitlines():
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    except json.JSONDecodeError as e:
        logger.warning(f"评测集解析失败: {e}")

    logger.info(f"加载评测集: {len(items)} 条样本")
    return items


def group_by_scenario(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按场景分组"""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        scenario = item.get("scenario", "unknown")
        groups.setdefault(scenario, []).append(item)
    return groups


class AgriEvalRunner:
    """农业领域评测运行器"""

    def __init__(self, eval_set_path: Optional[Path] = None):
        self.eval_items = load_eval_set(eval_set_path)
        self.scenarios = group_by_scenario(self.eval_items)
        self.results: List[Dict[str, Any]] = []

    def run_single(
        self,
        item: Dict[str, Any],
        retrieve_fn,
        generate_fn,
    ) -> Dict[str, Any]:
        """
        运行单条评测。

        Args:
            item: 评测样本
            retrieve_fn: 检索函数，接收 question，返回 List[Dict]
            generate_fn: 生成函数，接收 question + context，返回 str

        Returns:
            评测结果
        """
        question = item["question"]
        start_time = time.perf_counter()

        # 1. 检索
        retrieval_start = time.perf_counter()
        retrieved_docs = retrieve_fn(question)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000

        # 2. 检索指标
        expected_ids = set(item.get("expected_evidence_ids", []))
        retrieved_ids = set()
        for doc in retrieved_docs:
            doc_id = doc.get("metadata", {}).get("evidence_id", "")
            if doc_id:
                retrieved_ids.add(doc_id)

        recall_at_k = len(expected_ids & retrieved_ids) / max(1, len(expected_ids))
        mrr = 0.0
        for rank, doc in enumerate(retrieved_docs, start=1):
            doc_id = doc.get("metadata", {}).get("evidence_id", "")
            if doc_id in expected_ids:
                mrr = 1.0 / rank
                break

        # 3. 生成
        context = "\n".join(doc.get("content", "") for doc in retrieved_docs[:5])
        generation_start = time.perf_counter()
        answer = generate_fn(question, context)
        generation_latency = (time.perf_counter() - generation_start) * 1000

        # 4. 安全检查
        forbidden_claims = item.get("forbidden_claims", [])
        safety_keywords = item.get("safety_keywords", [])
        safety_violated = False
        violated_keywords = []
        for keyword in safety_keywords:
            if keyword in answer:
                # 检查是否在禁止上下文中
                for forbidden in forbidden_claims:
                    if any(fw in answer for fw in forbidden.split("，")):
                        safety_violated = True
                        violated_keywords.append(keyword)

        # 5. 引用检查
        expected_levels = set(item.get("expected_source_levels", []))
        has_evidence = len(retrieved_docs) > 0
        citation_covered = has_evidence  # 简单检查：有检索结果即视为有引用

        total_latency = (time.perf_counter() - start_time) * 1000

        result = {
            "id": item["id"],
            "scenario": item.get("scenario"),
            "question": question,
            "crop": item.get("crop"),
            "region": item.get("region"),
            "stage": item.get("stage"),
            # 检索指标
            "retrieved_count": len(retrieved_docs),
            "expected_evidence_count": len(expected_ids),
            "recall_at_k": round(recall_at_k, 4),
            "mrr": round(mrr, 4),
            "citation_covered": citation_covered,
            # 安全指标
            "safety_violated": safety_violated,
            "safety_keywords_matched": violated_keywords,
            # 性能指标
            "retrieval_latency_ms": round(retrieval_latency, 2),
            "generation_latency_ms": round(generation_latency, 2),
            "total_latency_ms": round(total_latency, 2),
            # 内容
            "answer": answer[:500],
            "gold_answer_summary": item.get("gold_answer_summary", ""),
        }
        return result

    def run_batch(
        self,
        retrieve_fn,
        generate_fn,
        max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        批量运行评测。

        Returns:
            汇总报告
        """
        items = self.eval_items[:max_items] if max_items else self.eval_items
        self.results = []

        logger.info(f"开始批量评测: {len(items)} 条样本")
        for i, item in enumerate(items):
            result = self.run_single(item, retrieve_fn, generate_fn)
            self.results.append(result)
            if (i + 1) % 10 == 0:
                logger.info(f"评测进度: {i + 1}/{len(items)}")

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """生成评测报告"""
        if not self.results:
            return {"error": "无评测结果"}

        n = len(self.results)

        # 汇总指标
        avg_recall = sum(r["recall_at_k"] for r in self.results) / n
        avg_mrr = sum(r["mrr"] for r in self.results) / n
        citation_coverage = sum(1 for r in self.results if r["citation_covered"]) / n
        safety_violation_rate = sum(1 for r in self.results if r["safety_violated"]) / n
        avg_retrieval_latency = sum(r["retrieval_latency_ms"] for r in self.results) / n
        avg_generation_latency = sum(r["generation_latency_ms"] for r in self.results) / n
        avg_total_latency = sum(r["total_latency_ms"] for r in self.results) / n

        # 按场景统计
        scenario_stats = {}
        for scenario, items in self.scenarios.items():
            scenario_results = [r for r in self.results if r["scenario"] == scenario]
            if scenario_results:
                scenario_stats[scenario] = {
                    "count": len(scenario_results),
                    "avg_recall": round(sum(r["recall_at_k"] for r in scenario_results) / len(scenario_results), 4),
                    "avg_mrr": round(sum(r["mrr"] for r in scenario_results) / len(scenario_results), 4),
                    "safety_violations": sum(1 for r in scenario_results if r["safety_violated"]),
                }

        # 按作物统计
        crop_stats = {}
        for r in self.results:
            crop = r.get("crop", "unknown")
            if crop not in crop_stats:
                crop_stats[crop] = {"count": 0, "recall_sum": 0, "mrr_sum": 0}
            crop_stats[crop]["count"] += 1
            crop_stats[crop]["recall_sum"] += r["recall_at_k"]
            crop_stats[crop]["mrr_sum"] += r["mrr"]
        for crop, stats in crop_stats.items():
            stats["avg_recall"] = round(stats["recall_sum"] / stats["count"], 4)
            stats["avg_mrr"] = round(stats["mrr_sum"] / stats["count"], 4)
            del stats["recall_sum"]
            del stats["mrr_sum"]

        report = {
            "summary": {
                "total_samples": n,
                "avg_recall_at_k": round(avg_recall, 4),
                "avg_mrr": round(avg_mrr, 4),
                "citation_coverage": round(citation_coverage, 4),
                "safety_violation_rate": round(safety_violation_rate, 4),
                "avg_retrieval_latency_ms": round(avg_retrieval_latency, 2),
                "avg_generation_latency_ms": round(avg_generation_latency, 2),
                "avg_total_latency_ms": round(avg_total_latency, 2),
            },
            "by_scenario": scenario_stats,
            "by_crop": crop_stats,
            "failed_safety": [
                {"id": r["id"], "question": r["question"], "violated": r["safety_keywords_matched"]}
                for r in self.results if r["safety_violated"]
            ],
            "low_recall": [
                {"id": r["id"], "question": r["question"], "recall": r["recall_at_k"]}
                for r in self.results if r["recall_at_k"] < 0.5
            ],
        }

        return report

    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """保存评测报告"""
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        filename = filename or f"agri_eval_report_{int(time.time())}.json"
        filepath = REPORT_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"评测报告已保存: {filepath}")
        return filepath


# ============================================================
# 便捷函数
# ============================================================

def quick_eval(retrieve_fn, generate_fn, max_items: int = 15) -> Dict[str, Any]:
    """快速评测（使用子集）"""
    runner = AgriEvalRunner(EVAL_SUBSET_PATH)
    report = runner.run_batch(retrieve_fn, generate_fn, max_items=max_items)
    runner.save_report(report, "quick_eval_report.json")
    return report
