# -*- coding: utf-8 -*-
"""
社区检测与摘要 — 图社区发现 + 社区摘要生成。

实现轻量级社区检测（LPA - Label Propagation Algorithm），
为每个社区生成摘要文本，支持社区级检索（global querying）。
"""
from __future__ import annotations
import json
import logging
import random
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from graph.schema import Entity, Relation, GraphTriple
from graph.graph_store import GraphStore

logger = logging.getLogger(__name__)


class CommunityDetector:
    """社区检测器：LPA 标签传播 + 社区摘要。

    Parameters
    ----------
    graph_store : GraphStore
        图谱存储实例。
    iterations : int
        LPA 最大迭代次数。
    """

    def __init__(self, graph_store: GraphStore, iterations: int = 10):
        self.graph = graph_store
        self.iterations = iterations
        self._communities: List[Set[str]] = []  # 社区 → 实体 ID 集合
        self._entity_to_community: Dict[str, int] = {}
        self._summaries: List[str] = []

    def detect(self) -> List[Set[str]]:
        """运行 LPA 社区检测。

        Returns
        -------
        list of set
            社区列表，每个社区是一组实体 ID。
        """
        entities = list(self.graph._entities.keys())
        if not entities:
            self._communities = []
            return self._communities

        # 初始化每个节点为独立社区
        labels: Dict[str, str] = {eid: eid for eid in entities}

        # 构建邻接表
        adjacency: Dict[str, List[str]] = {}
        for eid in entities:
            adjacency[eid] = []
        for triple in self.graph._triples.values():
            h_id = _entity_id(triple.h, triple.h_type)
            t_id = _entity_id(triple.t, triple.t_type)
            adjacency.setdefault(h_id, []).append(t_id)
            adjacency.setdefault(t_id, []).append(h_id)

        # LPA 迭代
        for _ in range(self.iterations):
            updated = 0
            for eid in entities:
                neighbor_labels = [labels[n] for n in adjacency.get(eid, [])]
                if not neighbor_labels:
                    continue
                # 选择出现次数最多的标签
                counter = Counter(neighbor_labels)
                max_count = max(counter.values())
                candidates = [label for label, count in counter.items() if count == max_count]
                new_label = candidates[0]  # 确定性选择
                if new_label != labels[eid]:
                    labels[eid] = new_label
                    updated += 1
            if updated == 0:
                break

        # 按标签分组
        groups: Dict[str, Set[str]] = defaultdict(set)
        for eid, label in labels.items():
            groups[label].add(eid)

        self._communities = list(groups.values())
        self._entity_to_community = {}
        for idx, community in enumerate(self._communities):
            for eid in community:
                self._entity_to_community[eid] = idx
        return self._communities

    def generate_summaries(self, community_size_limit: int = 20) -> List[str]:
        """为每个社区生成摘要文本。

        Parameters
        ----------
        community_size_limit : int
            社区内实体数超过该值时截断展示。

        Returns
        -------
        list of str
            每个社区的摘要文本。
        """
        if not self._communities:
            self.detect()
        if not self._communities:
            return []

        self._summaries = []
        for community in self._communities:
            entities = [self.graph._entities[eid] for eid in community]
            if not entities:
                continue

            # 统计实体类型分布
            type_counter = Counter(e.entity_type for e in entities)
            entity_names = [e.name for e in entities[:community_size_limit]]

            lines = [
                f"社区 (共{len(entities)}个实体)",
                "类型分布: " + ", ".join(f"{et}({n})" for et, n in type_counter.most_common(3)),
                "实体: " + ", ".join(entity_names),
            ]
            self._summaries.append("\n".join(lines))

        return self._summaries

    def save(self, summary_path: Optional[str] = None) -> None:
        """保存社区检测结果和摘要。"""
        if not summary_path:
            summary_path = str(self.graph.graph_dir / "communities.json")
        if not self._summaries:
            self.generate_summaries()

        data = {
            "entity_to_community": self._entity_to_community,
            "communities": [
                {
                    "id": idx,
                    "entity_count": len(c),
                    "entities": [eid for eid in c],
                    "summary": self._summaries[idx] if idx < len(self._summaries) else "",
                }
                for idx, c in enumerate(self._communities)
            ],
        }
        Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, summary_path: Optional[str] = None) -> List[Set[str]]:
        """从文件加载社区检测结果。"""
        if not summary_path:
            summary_path = str(self.graph.graph_dir / "communities.json")
        if not Path(summary_path).exists():
            return self.detect()
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._communities = [set(c["entities"]) for c in data["communities"]]
        self._entity_to_community = {k: int(v) for k, v in data.get("entity_to_community", {}).items()}
        self._summaries = [c.get("summary", "") for c in data["communities"]]
        return self._communities

    def community_for(self, entity_id: str) -> Optional[int]:
        """返回实体所属社区 ID。"""
        return self._entity_to_community.get(entity_id)

    def get_summary(self, community_id: int) -> str:
        """返回社区摘要。"""
        if 0 <= community_id < len(self._summaries):
            return self._summaries[community_id]
        return ""


def _entity_id(name: str, entity_type: str) -> str:
    """生成与 GraphStore 一致的实体 ID。"""
    import hashlib
    digest = hashlib.sha1(f"{entity_type}|{name}".encode("utf-8")).hexdigest()[:16]
    return f"E_{digest}"