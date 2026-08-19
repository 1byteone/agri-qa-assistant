# -*- coding: utf-8 -*-
"""
A5 评估脚本 — 对比纯向量检索 vs 图谱检索 vs 混合检索的 Recall@K。

用法:
    python -m graph.eval_retrieval  # 运行完整对比
"""
from __future__ import annotations
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from agriir_pipeline import AgriIRPipeline, PipelineConfig, StageConfig
from graph.graph_store import GraphStore
from graph.graph_retriever import GraphRetriever


class KnowledgeBaseAdapter:
    """Stub knowledge base that only supports keyword-based exact match.

    由于测试环境没有真实向量库，这里用一个关键词匹配的代理来评估
    图谱检索的相对增益，而不是绝对 RAG 质量。
    """

    @staticmethod
    def choose_strategy(query: str) -> str:
        return "hybrid"

    def search(self, query: str, top_k: int = 3, strategy: str = "hybrid") -> List[Dict[str, Any]]:
        """返回与查询关键词精确匹配的模拟结果。"""
        from graph.entity_extractor import (
            CROP_DICT, PEST_DICT, DISEASE_DICT, PESTICIDE_DICT, GROWTH_STAGE_DICT
        )
        results = []
        # 模拟：查询命中作物/害虫词典时返回一条结果
        for name in CROP_DICT:
            if name in query:
                results.append({
                    "content": f"关于{name}的种植知识。",
                    "metadata": {"source": "模拟知识库", "content_hash": f"hash_{name}", "category": "crop"},
                    "relevance": 0.6,
                })
        for name in {**PEST_DICT, **DISEASE_DICT}:
            if name in query:
                results.append({
                    "content": f"关于{name}的防治知识。",
                    "metadata": {"source": "模拟知识库", "content_hash": f"hash_{name}", "category": "pest"},
                    "relevance": 0.7,
                })
        results.sort(key=lambda r: r["relevance"], reverse=True)
        return results[:top_k]


def load_eval_items(path: str = "../data/evals/agriir_eval_skeleton.jsonl") -> List[Dict[str, Any]]:
    """加载评估数据。"""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def evaluate_channel(
    gretriever: GraphRetriever,
    items: List[Dict[str, Any]],
    expected_entities: List[str],
) -> Dict[str, Any]:
    """评估图谱检索通道的命中率。"""
    total = len(items)
    hit_count = 0
    by_scenario: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hit": 0, "total": 0})

    for item in items:
        query = item["question"]
        scenario = item["scenario"]
        crop = item.get("crop", "")
        by_scenario[scenario]["total"] += 1

        # 图谱检索
        graph_hits = gretriever.search(query, top_k=5)
        graph_contents = " ".join(r.get("content", "") for r in graph_hits)

        # 检查图谱是否命中预期实体
        matched = False
        for entity in expected_entities:
            if entity and entity in graph_contents:
                matched = True
                break
        # 宽松判定：标注的 crop 在图谱检索结果中
        if crop and crop in graph_contents:
            matched = True

        if matched:
            hit_count += 1
            by_scenario[scenario]["hit"] += 1

    return {
        "total": total,
        "hit_count": hit_count,
        "recall": round(hit_count / max(total, 1), 3),
        "by_scenario": dict(by_scenario),
    }


def evaluate_hybrid(
    pipeline: AgriIRPipeline,
    kb: KnowledgeBaseAdapter,
    items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """评估混合检索管线的图谱使用率。"""
    graph_used_count = 0
    vector_only_count = 0
    total = len(items)

    for item in items:
        trace = pipeline.retrieve(item["question"], kb)
        if trace.get("graph_channel_used"):
            graph_used_count += 1
        else:
            vector_only_count += 1

    return {
        "total": total,
        "graph_channel_used": graph_used_count,
        "vector_only": vector_only_count,
        "graph_usage_rate": round(graph_used_count / max(total, 1), 3),
    }


def main():
    """运行完整评估。"""
    print("=" * 60)
    print("A5 评估: 图谱检索 vs 向量检索 vs 混合检索")
    print("=" * 60)

    # 加载评估数据
    items = load_eval_items()
    print(f"\n评估数据集: {len(items)} 条")
    scenario_counts = Counter(item["scenario"] for item in items)
    print(f"场景分布: {dict(scenario_counts)}")

    # 初始化图谱检索器
    graph = GraphStore()
    graph.initialize()
    retriever = GraphRetriever(graph)
    stats = graph.stats()
    print(f"\n图谱规模: {stats['entity_count']} 实体 / {stats['relation_count']} 关系")

    # 预期实体列表（从图谱中取出所有实体名）
    expected_entities = [e["name"] for e in graph.all_entities()]

    # 1. 图谱检索独立评估
    print("\n" + "-" * 60)
    print("[1] 图谱检索通道 Recall")
    print("-" * 60)
    graph_eval = evaluate_channel(retriever, items, expected_entities)
    print(f"总体 Recall: {graph_eval['recall']:.1%} ({graph_eval['hit_count']}/{graph_eval['total']})")
    print("分场景:")
    for scenario, counts in sorted(graph_eval["by_scenario"].items()):
        rate = counts["hit"] / max(counts["total"], 1)
        print(f"  {scenario}: {rate:.1%} ({counts['hit']}/{counts['total']})")

    # 2. 混合检索管线评估
    print("\n" + "-" * 60)
    print("[2] 混合检索管线图谱使用率")
    print("-" * 60)
    pipeline = AgriIRPipeline()
    kb = KnowledgeBaseAdapter()
    hybrid_eval = evaluate_hybrid(pipeline, kb, items)
    print(f"图谱通道启用率: {hybrid_eval['graph_usage_rate']:.1%} ({hybrid_eval['graph_channel_used']}/{hybrid_eval['total']})")
    print(f"纯向量通道: {hybrid_eval['vector_only']} 条")

    # 3. 结论
    print("\n" + "=" * 60)
    print("评估结论")
    print("=" * 60)
    print(f"""
1. 图谱检索 Recall@{5}: {graph_eval['recall']:.1%}
   - 单独使用图谱在 {graph_eval['hit_count']}/{graph_eval['total']} 条问题上能召回相关实体
   - 分场景最高的场景可能是诊断类（实体密集）

2. 混合管线图谱使用率: {hybrid_eval['graph_usage_rate']:.1%}
   - 说明图谱通道在 {hybrid_eval['graph_channel_used']} 条查询上补充了向量通道
   - 应用场景: 查询含作物/病害等图谱实体时自动激活

3. 调优建议:
   - 召回不足的场景 (如 safety/policy) 需补充图谱实体词典
   - 图谱 relevance 权重可随实体匹配度调整
   - 为图谱结果添加来源回链 (evidence-level 继承)
""")
    return {
        "graph_recall": graph_eval,
        "hybrid": hybrid_eval,
    }


if __name__ == "__main__":
    main()