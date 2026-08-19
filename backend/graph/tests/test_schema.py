# -*- coding: utf-8 -*-
"""图谱数据模型测试。"""
import pytest
from graph.schema import Entity, Relation, GraphTriple, EntityType, RelationType, stable_entity_id


class TestSchema:
    """数据模型测试。"""

    def test_entity_creation(self):
        entity = Entity.create("水稻", "crop", alias="rice")
        assert entity.id.startswith("E_")
        assert entity.name == "水稻"
        assert entity.entity_type == "crop"
        assert entity.properties["alias"] == "rice"

    def test_entity_stable_id(self):
        id1 = stable_entity_id("水稻", "crop")
        id2 = stable_entity_id("水稻", "crop")
        assert id1 == id2

    def test_graph_triple_serialization(self):
        triple = GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease")
        json_str = triple.to_json()
        restored = GraphTriple.from_json(json_str)
        assert restored.h == "水稻"
        assert restored.r == "infects"
        assert restored.t == "稻瘟病"