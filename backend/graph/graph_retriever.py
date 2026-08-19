# -*- coding: utf-8 -*-
"""
图谱检索器 — 实体邻域检索 + 社区摘要检索。

集成到 agriir_pipeline.retrieve() 中，与向量检索并行。
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional

from graph.schema import EntityType, Entity, stable_entity_id
from graph.graph_store import GraphStore

logger = logging.getLogger(__name__)


class GraphRetriever:
    """图谱检索器。

    提供两种检索模式：
    - local_search: 实体为中心的邻域检索
    - community_search: 社区级摘要检索
    """

    def __init__(self, graph_store: GraphStore):
        self.graph = graph_store

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """知识图谱检索。

        Parameters
        ----------
        query : str
            用户查询。
        top_k : int
            返回结果数。

        Returns
        -------
        list of dict
            每项包含 content, metadata, source, retrieval_strategy 等字段。
            与 knowledge_base.search() 返回格式兼容，可一起进入 RRF 融合。
        """
        results = []
        # 1. 从查询中识别实体
        entities = self._extract_query_entities(query)
        if not entities:
            return results

        # 2. 对每个实体扩展邻域
        for entity in entities[:3]:  # 最多 3 个实体
            subgraph = self.graph.get_adjacent_subgraph(entity.id, hops=1)
            if not subgraph["center"]:
                continue

            # 格式化实体邻域文本
            context = self._format_subgraph(subgraph)
            if not context:
                continue

            results.append({
                "content": context,
                "metadata": {
                    "title": f"图谱: {entity.name}",
                    "source": "knowledge_graph",
                    "entity_type": entity.entity_type,
                    "entity_name": entity.name,
                    "evidence_level": "B",
                },
                "relevance": _relevance_score(query, entity.name),
                "retrieval_strategy": "graph_local",
            })

            # 3. 二跳扩展（如果结果不够）
            if len(results) < top_k:
                subgraph_2hop = self.graph.get_adjacent_subgraph(entity.id, hops=2)
                context_2hop = self._format_subgraph(subgraph_2hop)
                if context_2hop and context_2hop != context:
                    results.append({
                        "content": context_2hop,
                        "metadata": {
                            "title": f"图谱关联: {entity.name}",
                            "source": "knowledge_graph",
                            "entity_type": entity.entity_type,
                            "entity_name": entity.name,
                            "evidence_level": "C",
                        },
                        "relevance": _relevance_score(query, entity.name) * 0.8,
                        "retrieval_strategy": "graph_local_2hop",
                    })

        # 按 relevance 排序
        results.sort(key=lambda x: float(x.get("relevance", 0.0)), reverse=True)
        return results[:top_k]

    def community_search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """社区级检索（适用于泛化/综合分析类问题）。

        Parameters
        ----------
        query : str
            用户查询。
        top_k : int
            返回社区数。

        Returns
        -------
        list of dict
            每项包含 content, metadata, relevance 等字段。
        """
        results = []
        # 识别查询中的关键词
        keywords = self._extract_keywords(query)
        if not keywords:
            return results

        # 按实体类型分组
        for keyword, etype in keywords:
            entity = self.graph.get_entity(keyword, entity_type=etype.value)
            if not entity:
                continue
            neighbors = self.graph.neighbors(entity.id, hops=1)
            if not neighbors:
                continue

            # 构建社区摘要
            community_text = self._build_community_summary(entity, neighbors)
            if community_text:
                results.append({
                    "content": community_text,
                    "metadata": {
                        "title": f"图谱社区: {etype.value}/{keyword}",
                        "source": "knowledge_graph",
                        "entity_type": "community",
                        "evidence_level": "C",
                    },
                    "relevance": _relevance_score(query, keyword),
                    "retrieval_strategy": "graph_community",
                })

        results.sort(key=lambda x: float(x.get("relevance", 0.0)), reverse=True)
        return results[:top_k]

    def _extract_query_entities(self, query: str) -> List[Entity]:
        """从查询中识别已知实体。"""
        entities = []
        seen_ids = set()
        for name in self.graph._name_to_id:
            if len(name) >= 2 and name in query:
                entity = self.graph.get_entity(name)
                if entity and entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    entities.append(entity)
        return entities

    def _extract_keywords(self, query: str) -> List[tuple[str, EntityType]]:
        """提取查询中的关键词及其预期实体类型。"""
        keywords = []
        rules = [
            (r"水稻|稻|小麦|玉米|油菜|脐橙|柑橘|蔬菜", EntityType.CROP),
            (r"稻瘟病|纹枯病|条锈病|赤霉病|菌核病|黄龙病", EntityType.DISEASE),
            (r"稻飞虱|二化螟|蚜虫|玉米螟|红蜘蛛|蓟马", EntityType.PEST),
            (r"吡蚜酮|三环唑|井冈霉素|腐霉利|咪鲜胺", EntityType.PESTICIDE),
            (r"分蘖|孕穗|抽穗|灌浆|返青|拔节|苗期|蕾薹", EntityType.GROWTH_STAGE),
            (r"江西|南昌|赣州|九江|上饶|吉安|宜春|赣南", EntityType.REGION),
        ]
        for pattern, etype in rules:
            for match in re.finditer(pattern, query):
                keywords.append((match.group(0), etype))
        return keywords

    def _format_subgraph(self, subgraph: Dict[str, Any]) -> str:
        """格式化工文本格式的子图。"""
        if not subgraph["center"]:
            return ""
        center = subgraph["center"]
        lines = [f"【{center['name']}】（{center['entity_type']}）"]
        for edge in subgraph["edges"]:
            source = next((n["name"] for n in subgraph["nodes"] if n["id"] == edge["source"]), "")
            target = next((n["name"] for n in subgraph["nodes"] if n["id"] == edge["target"]), "")
            lines.append(f"- {source} —{edge['relation']}→ {target}")
        return "\n".join(lines)

    def _build_community_summary(self, center: Entity, neighbors: List[Dict]) -> str:
        """构建社区摘要文本。"""
        lines = [f"领域: {center.name}"]
        lines.append(f"类型: {center.entity_type}")
        if neighbors:
            lines.append("相关实体:")
            for n in neighbors[:5]:
                en = n["entity"]
                lines.append(f"- {en['name']} ({en['entity_type']}) — {n['relation']}")
        return "\n".join(lines)


def _relevance_score(query: str, entity_name: str) -> float:
    """计算查询与实体的相关度分数。"""
    if entity_name in query:
        # 完全匹配
        return 0.85
    # 部分匹配
    if len(entity_name) >= 2 and entity_name in query:
        return 0.75
    return 0.5