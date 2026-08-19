# -*- coding: utf-8 -*-
"""
图谱数据模型 — 实体类型、关系类型、三元组结构。
"""
from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class EntityType(str, Enum):
    """农业知识图谱实体类型。"""
    CROP = "crop"                    # 作物
    DISEASE = "disease"              # 病害
    PEST = "pest"                    # 害虫
    PESTICIDE = "pesticide"          # 农药
    VARIETY = "variety"              # 品种
    GROWTH_STAGE = "growth_stage"    # 生育期
    PRACTICE = "practice"            # 农事操作
    SYMPTOM = "symptom"              # 症状
    REGION = "region"                # 地区
    EVIDENCE_PACK = "evidence_pack"  # 证据包
    DOCUMENT = "document"            # 文档
    FERTILIZER = "fertilizer"        # 肥料


class RelationType(str, Enum):
    """农业知识图谱关系类型。"""
    INFECTS = "infects"                  # 病原/害虫 → 作物（危害）
    DAMAGES = "damages"                  # 害虫 → 作物（啃食）
    CONTROLS = "controls"                # 农药 → 害虫/病害（防治）
    TREATED_BY = "treated_by"            # 病害 → 农药（治疗）
    CAUSES = "causes"                    # 病害/害虫 → 症状
    RECOMMENDED_FOR = "recommended_for"  # 品种 → 地区（推荐种植）
    APPLIES_TO = "applies_to"            # 农事操作 → 生育期
    CONTAINS = "contains"                # 证据包 → 文档
    GROWN_IN = "grown_in"                # 作物 → 地区（种植区域）
    HAS_EVIDENCE = "has_evidence"        # 文档 → 证据级别
    RELATED_TO = "related_to"            # 泛化关联
    MANAGES = "manages"                  # 农事操作 → 作物
    OCCURS_IN = "occurs_in"              # 生育期 → 作物
    USES = "uses"                        # 农事操作 → 肥料/农药


# 实体类型中文标签
ENTITY_TYPE_LABELS: Dict[str, str] = {
    "crop": "作物",
    "disease": "病害",
    "pest": "害虫",
    "pesticide": "农药",
    "variety": "品种",
    "growth_stage": "生育期",
    "practice": "农事操作",
    "symptom": "症状",
    "region": "地区",
    "evidence_pack": "证据包",
    "document": "文档",
    "fertilizer": "肥料",
}

# 关系类型中文标签
RELATION_TYPE_LABELS: Dict[str, str] = {
    "infects": "危害",
    "damages": "啃食",
    "controls": "防治",
    "treated_by": "治疗",
    "causes": "引发",
    "recommended_for": "推荐种植于",
    "applies_to": "适用于",
    "contains": "包含",
    "grown_in": "种植于",
    "has_evidence": "证据级别",
    "related_to": "关联",
    "manages": "管理",
    "occurs_in": "发生于",
    "uses": "使用",
}

ENTITY_TYPES = list(EntityType)
RELATION_TYPES = list(RelationType)


@dataclass
class Entity:
    """图谱实体。"""
    id: str
    name: str
    entity_type: str  # EntityType.value
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, entity_type: str, **properties) -> "Entity":
        """创建实体并生成稳定 ID。"""
        entity_id = stable_entity_id(name, entity_type)
        return cls(id=entity_id, name=name, entity_type=entity_type, properties=properties)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "properties": self.properties,
        }


@dataclass
class Relation:
    """图谱关系。"""
    source: str  # 源实体 ID
    relation_type: str  # RelationType.value
    target: str  # 目标实体 ID
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "relation_type": self.relation_type,
            "target": self.target,
            "properties": self.properties,
        }


@dataclass
class GraphTriple:
    """三元组，JSONL 存储格式。"""
    h: str          # head 实体名称
    h_type: str     # head 实体类型
    r: str          # 关系类型
    t: str          # tail 实体名称
    t_type: str     # tail 实体类型
    properties: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 来源文档

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "GraphTriple":
        data = json.loads(line)
        return cls(**data)


def stable_entity_id(name: str, entity_type: str) -> str:
    """生成实体稳定 ID。"""
    digest = hashlib.sha1(f"{entity_type}|{name}".encode("utf-8")).hexdigest()[:16]
    return f"E_{digest}"


def stable_triple_id(h: str, r: str, t: str) -> str:
    """生成三元组稳定 ID。"""
    digest = hashlib.sha1(f"{h}|{r}|{t}".encode("utf-8")).hexdigest()[:16]
    return f"T_{digest}"