# -*- coding: utf-8 -*-
"""图谱存储测试。"""
import pytest
from graph.schema import Entity, GraphTriple
from graph.graph_store import GraphStore


@pytest.fixture
def store():
    g = GraphStore()
    g.clear()
    return g


class TestGraphStore:
    """GraphStore 测试。"""

    def test_add_entity(self, store):
        entity = Entity.create("水稻", "crop")
        store.add_entity(entity)
        assert store.stats()["entity_count"] == 1

    def test_add_triple(self, store):
        triple = GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease")
        added = store.add_triple(triple)
        assert added is True
        assert store.stats()["entity_count"] == 2
        assert store.stats()["relation_count"] == 1

    def test_get_entity(self, store):
        store.add_entity(Entity.create("水稻", "crop"))
        entity = store.get_entity("水稻")
        assert entity is not None
        assert entity.name == "水稻"

    def test_resolve_entity(self, store):
        store.add_entity(Entity.create("水稻", "crop"))
        entity = store.resolve_entity("水稻稻飞虱怎么防治")
        assert entity is not None
        assert entity.name == "水稻"

    def test_neighbors(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        rice = store.get_entity("水稻")
        neighbors = store.neighbors(rice.id)
        assert len(neighbors) == 1
        assert neighbors[0]["entity"]["name"] == "稻瘟病"

    def test_adjacent_subgraph(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="damages", t="稻飞虱", t_type="pest"))
        rice = store.get_entity("水稻")
        subgraph = store.get_adjacent_subgraph(rice.id)
        assert len(subgraph["edges"]) == 2
        assert len(subgraph["nodes"]) == 3

    def test_format_entity_context(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        context = store.format_entity_context("水稻")
        assert "水稻" in context
        assert "稻瘟病" in context

    def test_duplicate_triple_skipped(self, store):
        triple = GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease")
        store.add_triple(triple)
        added = store.add_triple(triple)
        assert added is False
        assert store.stats()["relation_count"] == 1

    def test_persist_and_reload(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        # 重新加载
        store2 = GraphStore()
        store2.initialize()
        assert store2.stats()["entity_count"] == 2
        assert store2.stats()["relation_count"] == 1

    def test_clear(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        store.clear()
        assert store.stats()["entity_count"] == 0

    def test_stats_by_type(self, store):
        store.add_triple(GraphTriple(h="水稻", h_type="crop", r="infects", t="稻瘟病", t_type="disease"))
        stats = store.stats()
        assert stats["entity_by_type"]["crop"] == 1
        assert stats["entity_by_type"]["disease"] == 1