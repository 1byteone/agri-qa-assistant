# -*- coding: utf-8 -*-
"""
图谱存储 — JSONL 三元组存储 + 内存图索引。
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from graph.schema import (
    Entity,
    Relation,
    GraphTriple,
    EntityType,
    RelationType,
    stable_entity_id,
    stable_triple_id,
)

logger = logging.getLogger(__name__)


class GraphStore:
    """轻量图谱存储：JSONL 文件持久化 + 内存索引。

    Parameters
    ----------
    graph_dir : str
        图谱数据目录，默认为 data/knowledge_graph。
    """

    def __init__(self, graph_dir: str = "data/knowledge_graph"):
        self.graph_dir = Path(graph_dir)
        self.triples_path = self.graph_dir / "triples.jsonl"
        self.entity_index_path = self.graph_dir / "entity_index.json"

        # 内存索引
        self._entities: Dict[str, Entity] = {}       # entity_id → Entity
        self._name_to_id: Dict[str, str] = {}        # name → entity_id
        self._adjacency: Dict[str, List[Tuple[str, str, str]]] = {}  # entity_id → [(rel, target_id, rel_id)]
        self._triples: Dict[str, GraphTriple] = {}   # triple_id → GraphTriple
        self._loaded = False

    # ── 生命周期 ─────────────────────────────────────────────

    def initialize(self) -> None:
        """确保目录存在并加载已有数据。"""
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self) -> None:
        """从 JSONL 加载图谱。"""
        if not self.triples_path.exists():
            return
        with open(self.triples_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    triple = GraphTriple.from_json(line)
                    self._add_triple_in_memory(triple)
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning("跳过无效三元组: %s", exc)

    def _persist(self) -> None:
        """将内存中的三元组写回 JSONL。"""
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        with open(self.triples_path, "w", encoding="utf-8") as f:
            for triple in self._triples.values():
                f.write(triple.to_json() + "\n")
        # 写实体索引
        with open(self.entity_index_path, "w", encoding="utf-8") as f:
            json.dump(self._name_to_id, f, ensure_ascii=False, indent=2)

    # ── 写入操作 ─────────────────────────────────────────────

    def add_entity(self, entity: Entity) -> None:
        """添加或更新实体。"""
        self.initialize()
        self._entities[entity.id] = entity
        self._name_to_id[entity.name] = entity.id

    def add_triple(self, triple: GraphTriple) -> bool:
        """添加三元组，返回是否新增（去重）。"""
        self.initialize()
        triple_id = stable_triple_id(triple.h, triple.r, triple.t)
        if triple_id in self._triples:
            return False
        # 自动创建实体节点
        for name, etype in ((triple.h, triple.h_type), (triple.t, triple.t_type)):
            entity_id = stable_entity_id(name, etype)
            if entity_id not in self._entities:
                self._entities[entity_id] = Entity.create(name, etype)
                self._name_to_id[name] = entity_id
        self._add_triple_in_memory(triple)
        self._persist()
        return True

    def _add_triple_in_memory(self, triple: GraphTriple) -> None:
        """仅更新内存索引，不落盘。"""
        triple_id = stable_triple_id(triple.h, triple.r, triple.t)
        self._triples[triple_id] = triple

        h_id = stable_entity_id(triple.h, triple.h_type)
        t_id = stable_entity_id(triple.t, triple.t_type)
        self._entities.setdefault(h_id, Entity.create(triple.h, triple.h_type))
        self._entities.setdefault(t_id, Entity.create(triple.t, triple.t_type))
        self._name_to_id.setdefault(triple.h, h_id)
        self._name_to_id.setdefault(triple.t, t_id)

        self._adjacency.setdefault(h_id, []).append((triple.r, t_id, triple_id))
        self._adjacency.setdefault(t_id, []).append((triple.r, h_id, triple_id))

    def add_documents(self, triples: List[GraphTriple]) -> int:
        """批量添加三元组，返回新增数。"""
        added = 0
        for triple in triples:
            if self.add_triple(triple):
                added += 1
        return added

    # ── 查询操作 ─────────────────────────────────────────────

    def get_entity(self, name: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """按名称查询实体。"""
        self.initialize()
        entity_id = self._name_to_id.get(name)
        if not entity_id:
            return None
        entity = self._entities.get(entity_id)
        if entity and entity_type and entity.entity_type != entity_type:
            return None
        return entity

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        self.initialize()
        return self._entities.get(entity_id)

    def resolve_entity(self, text: str) -> Optional[Entity]:
        """从文本中模糊匹配实体名称（支持子串匹配）。"""
        self.initialize()
        # 精确匹配优先
        entity = self.get_entity(text.strip())
        if entity:
            return entity
        # 子串匹配：实体名是查询的子串
        for name, entity_id in self._name_to_id.items():
            if len(name) >= 2 and name in text:
                return self._entities[entity_id]
        return None

    def neighbors(
        self, entity_id: str, relation_type: Optional[str] = None,
        hops: int = 1,
    ) -> List[Dict[str, Any]]:
        """获取实体邻域（1-2 跳）。

        Returns
        -------
        list of dict
            每条包含 relation, entity, hops。
        """
        self.initialize()
        results = []
        visited = {entity_id}

        def _expand(current_id: str, current_hops: int) -> None:
            if current_hops > hops:
                return
            for rel, neighbor_id, _ in self._adjacency.get(current_id, []):
                if neighbor_id in visited and current_hops == hops:
                    # 允许一跳邻居通过二跳连接时跳过
                    continue
                if relation_type and rel != relation_type:
                    continue
                neighbor = self._entities.get(neighbor_id)
                if neighbor:
                    results.append({
                        "relation": rel,
                        "entity": neighbor.to_dict(),
                        "hops": current_hops,
                    })
                if current_hops < hops:
                    visited.add(neighbor_id)
                    _expand(neighbor_id, current_hops + 1)

        _expand(entity_id, 1)
        return results

    def get_adjacent_subgraph(self, entity_id: str, hops: int = 1) -> Dict[str, Any]:
        """获取以实体为中心的子图（用于 LLM 上下文注入）。

        Returns
        -------
        dict
            包含 center, nodes, edges 的 JSON 化子图。
        """
        self.initialize()
        center = self._entities.get(entity_id)
        if not center:
            return {"center": None, "nodes": [], "edges": []}

        nodes: Dict[str, Dict[str, Any]] = {center.id: center.to_dict()}
        edges: List[Dict[str, Any]] = []

        for rel, neighbor_id, triple_id in self._adjacency.get(entity_id, []):
            neighbor = self._entities.get(neighbor_id)
            if neighbor:
                nodes[neighbor.id] = neighbor.to_dict()
                edges.append({
                    "id": triple_id,
                    "relation": rel,
                    "source": entity_id,
                    "target": neighbor_id,
                })
                # 一跳邻居的二跳扩展（受限）
                for rel2, n2_id, triple2_id in self._adjacency.get(neighbor_id, []):
                    if n2_id in nodes:
                        continue
                    if n2_id == entity_id:
                        continue
                    n2 = self._entities.get(n2_id)
                    if n2:
                        nodes[n2.id] = n2.to_dict()
                        edges.append({
                            "id": triple2_id,
                            "relation": rel2,
                            "source": neighbor_id,
                            "target": n2_id,
                        })

        return {
            "center": center.to_dict(),
            "nodes": list(nodes.values()),
            "edges": edges,
        }

    def format_entity_context(self, entity_name: str, hops: int = 1) -> str:
        """格式化工文本格式的实体邻域上下文。"""
        entity = self.resolve_entity(entity_name)
        if not entity:
            return ""
        subgraph = self.get_adjacent_subgraph(entity.id, hops=hops)
        if not subgraph["center"]:
            return ""

        lines = [f"【{entity.name}】（{entity.entity_type}）"]
        for edge in subgraph["edges"]:
            source = next((n["name"] for n in subgraph["nodes"] if n["id"] == edge["source"]), "")
            target = next((n["name"] for n in subgraph["nodes"] if n["id"] == edge["target"]), "")
            rel_label = edge["relation"]
            lines.append(f"- {source} —{rel_label}→ {target}")
        return "\n".join(lines)

    # ── 统计 ─────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """图谱统计信息。"""
        self.initialize()
        by_type: Dict[str, int] = {}
        for entity in self._entities.values():
            by_type[entity.entity_type] = by_type.get(entity.entity_type, 0) + 1
        return {
            "entity_count": len(self._entities),
            "relation_count": len(self._triples),
            "entity_by_type": by_type,
        }

    def all_entities(self) -> List[Dict[str, Any]]:
        self.initialize()
        return [e.to_dict() for e in self._entities.values()]

    def all_triples(self) -> List[GraphTriple]:
        self.initialize()
        return list(self._triples.values())

    def clear(self) -> None:
        """清空图谱。"""
        self._entities = {}
        self._name_to_id = {}
        self._adjacency = {}
        self._triples = {}
        if self.triples_path.exists():
            self.triples_path.unlink()
        if self.entity_index_path.exists():
            self.entity_index_path.unlink()