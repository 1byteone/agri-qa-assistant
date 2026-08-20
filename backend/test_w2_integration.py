"""
CropWise W2 集成测试
=====================

测试 BGE-M3 嵌入、BM25 检索、RRF 融合、QueryTransformer 等新模块的功能。
"""

import sys
import os

# 确保 backend 目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import math


# ============================================================
# 1. BM25 检索器测试
# ============================================================

class TestBM25Retriever:
    """BM25 检索器单元测试"""

    def test_tokenizer_basic(self):
        from retrieval.bm25_retriever import ChineseAgriculturalTokenizer
        tokenizer = ChineseAgriculturalTokenizer()
        tokens = tokenizer.tokenize("南昌县晚稻分蘖期稻飞虱防治")
        assert len(tokens) > 0
        # 应该能识别出农业术语
        assert any("水稻" in t or "晚稻" in t or "分蘖" in t or "飞虱" in t for t in tokens)

    def test_tokenizer_empty(self):
        from retrieval.bm25_retriever import ChineseAgriculturalTokenizer
        tokenizer = ChineseAgriculturalTokenizer()
        assert tokenizer.tokenize("") == []
        assert tokenizer.tokenize("   ") == []

    def test_bm25_build_and_search(self):
        from retrieval.bm25_retriever import BM25Retriever
        retriever = BM25Retriever()
        docs = [
            {"content": "水稻稻飞虱防治：可用吡虫啉、噻虫嗪等药剂喷雾", "metadata": {"category": "pest"}},
            {"content": "水稻纹枯病防治：可用井冈霉素喷雾", "metadata": {"category": "pest"}},
            {"content": "油菜蕾薹期施肥方案", "metadata": {"category": "fertilizer"}},
            {"content": "赣南脐橙采后保鲜技术", "metadata": {"category": "postharvest"}},
        ]
        retriever.build_index(docs)
        assert retriever._built is True
        assert len(retriever._documents) == 4

        results = retriever.search("稻飞虱防治", top_k=2)
        assert len(results) > 0
        # 第一个结果应该与稻飞虱相关
        assert "飞虱" in results[0].content or "稻" in results[0].content

    def test_bm25_empty_index(self):
        from retrieval.bm25_retriever import BM25Retriever
        retriever = BM25Retriever()
        results = retriever.search("测试", top_k=5)
        assert results == []

    def test_bm25_stats(self):
        from retrieval.bm25_retriever import BM25Retriever
        retriever = BM25Retriever()
        retriever.build_index([
            {"content": "水稻种植技术", "metadata": {}},
            {"content": "小麦病虫害防治", "metadata": {}},
        ])
        stats = retriever.get_stats()
        assert stats["total_documents"] == 2
        assert stats["built"] is True
        assert stats["vocab_size"] > 0


# ============================================================
# 2. RRF 融合测试
# ============================================================

class TestRRFFusion:
    """RRF 融合单元测试"""

    def test_rrf_basic_fusion(self):
        from retrieval.rrf_fusion import rrf_fusion, RRFFusion
        # 两路检索结果
        vector_results = [
            {"content": "水稻稻飞虱防治", "relevance": 0.9},
            {"content": "水稻纹枯病防治", "relevance": 0.7},
            {"content": "油菜施肥", "relevance": 0.5},
        ]
        bm25_results = [
            {"content": "水稻纹枯病防治", "relevance": 0.85},
            {"content": "水稻稻飞虱防治", "relevance": 0.6},
            {"content": "脐橙保鲜", "relevance": 0.4},
        ]
        fused = rrf_fusion([vector_results, bm25_results], k=60)
        assert len(fused) > 0
        # 每个结果都应该有 rrf_score
        for item in fused:
            assert "rrf_score" in item
        # 融合后应该包含两个来源的文档
        contents = [item["content"] for item in fused]
        assert "水稻稻飞虱防治" in contents
        assert "水稻纹枯病防治" in contents

    def test_rrf_with_weights(self):
        from retrieval.rrf_fusion import rrf_fusion
        list_a = [{"content": "A", "relevance": 0.9}]
        list_b = [{"content": "B", "relevance": 0.8}]
        # 等权重
        fused = rrf_fusion([list_a, list_b], weights=[0.5, 0.5])
        assert len(fused) == 2
        # A 排在前面（因为 list_a 排名更高且权重相同）
        assert fused[0]["content"] == "A"

    def test_rrf_empty(self):
        from retrieval.rrf_fusion import rrf_fusion
        assert rrf_fusion([]) == []

    def test_rrf_class_fuse_with_trace(self):
        from retrieval.rrf_fusion import RRFFusion
        fusion = RRFFusion(k=60, weights={"vector": 0.6, "bm25": 0.4})
        ranked_lists = {
            "vector": [
                {"content": "文档A", "relevance": 0.9},
                {"content": "文档B", "relevance": 0.7},
            ],
            "bm25": [
                {"content": "文档B", "relevance": 0.85},
                {"content": "文档C", "relevance": 0.6},
            ],
        }
        results, trace = fusion.fuse_with_trace(ranked_lists)
        assert len(results) > 0
        assert "k" in trace
        assert "branches_used" in trace
        assert "branch_contribution" in trace


# ============================================================
# 3. QueryTransformer 测试
# ============================================================

class TestQueryTransformer:
    """QueryTransformer 单元测试"""

    def test_rewrite_basic(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        result = qt.rewrite("稻飞虱怎么防治")
        assert "稻飞虱" in result
        assert len(result) > 0

    def test_rewrite_with_context(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        result = qt.rewrite("怎么防治", {"crop": "水稻", "region": "南昌"})
        assert len(result) > 0

    def test_decompose(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        parts = qt.decompose("南昌水稻分蘖期，并且叶片出现黄色斑点")
        assert len(parts) >= 1

    def test_multi_query_complex(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        query = "南昌县晚稻分蘖期，连续高温后叶尖干枯，田里有飞虫，昨天已灌水"
        subqueries, trace = qt.multi_query(query)
        assert len(subqueries) > 0
        assert len(subqueries) <= 4
        assert "detected_intents" in trace
        assert "extracted_entities" in trace

    def test_multi_query_simple(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        query = "水稻怎么种植"
        subqueries, trace = qt.multi_query(query)
        assert len(subqueries) >= 1

    def test_extract_entities(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        entities = qt._extract_entities("南昌县晚稻分蘖期稻飞虱防治")
        assert entities.get("crop") in ["水稻", "晚稻"]
        assert entities.get("region") == "南昌"
        assert entities.get("stage") == "分蘖期"
        assert entities.get("pest_disease") == "稻飞虱"

    def test_expand_synonyms(self):
        from retrieval.query_transformer import QueryTransformer
        qt = QueryTransformer()
        variants = qt.expand_synonyms("稻飞虱怎么防治")
        assert len(variants) >= 1
        assert "稻飞虱" in variants[0]


# ============================================================
# 4. BGE-M3 Embedding 测试
# ============================================================

class TestBGEM3Embedding:
    """BGE-M3 嵌入函数测试"""

    def test_hash_fallback(self):
        from retrieval.bge_m3_embedding import BGEM3EmbeddingFunction
        ef = BGEM3EmbeddingFunction(mode="unavailable")
        embeddings = ef.embed_documents(["水稻种植技术", "病虫害防治"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024  # BGE-M3 维度

    def test_hash_fallback_query(self):
        from retrieval.bge_m3_embedding import BGEM3EmbeddingFunction
        ef = BGEM3EmbeddingFunction(mode="unavailable")
        embedding = ef.embed_query("水稻种植技术")
        assert len(embedding) == 1024

    def test_info(self):
        from retrieval.bge_m3_embedding import BGEM3EmbeddingFunction
        ef = BGEM3EmbeddingFunction(mode="unavailable")
        info = ef.get_info()
        assert info["mode"] == "unavailable"
        assert info["dimension"] == 1024


# ============================================================
# 5. 知识图谱 Schema 测试
# ============================================================

class TestKGSchma:
    """知识图谱 Schema 测试"""

    def test_entity_types(self):
        from kg.schema import ENTITY_TYPES
        assert len(ENTITY_TYPES) >= 12
        assert "Crop" in ENTITY_TYPES
        assert "Disease" in ENTITY_TYPES
        assert "Pest" in ENTITY_TYPES
        assert "Chemical" in ENTITY_TYPES

    def test_relation_types(self):
        from kg.schema import RELATION_TYPES
        assert len(RELATION_TYPES) >= 15
        assert "SUSCEPTIBLE_TO" in RELATION_TYPES
        assert "CONTROLLED_BY" in RELATION_TYPES

    def test_seed_data(self):
        from kg.schema import SEED_CROPS, SEED_DISEASES, SEED_PESTS, SEED_CHEMICALS
        assert len(SEED_CROPS) >= 10
        assert len(SEED_DISEASES) >= 10
        assert len(SEED_PESTS) >= 8
        assert len(SEED_CHEMICALS) >= 8

    def test_cypher_templates(self):
        from kg.schema import CypherTemplates
        assert "CREATE_ENTITY" in CypherTemplates.__dict__
        assert "DIAGNOSE_BY_SYMPTOM" in CypherTemplates.__dict__


# ============================================================
# 6. 评测集加载测试
# ============================================================

class TestEvalSet:
    """评测集测试"""

    def test_load_eval_set(self):
        from evaluation.agri_eval_runner import load_eval_set
        items = load_eval_set()
        assert len(items) > 0
        assert len(items) == 15  # 当前子集大小

    def test_eval_set_structure(self):
        from evaluation.agri_eval_runner import load_eval_set
        items = load_eval_set()
        for item in items:
            assert "id" in item
            assert "scenario" in item
            assert "question" in item
            assert "expected_evidence_ids" in item
            assert "forbidden_claims" in item

    def test_group_by_scenario(self):
        from evaluation.agri_eval_runner import load_eval_set, group_by_scenario
        items = load_eval_set()
        groups = group_by_scenario(items)
        assert "diagnosis" in groups
        assert "fertilizer" in groups
        assert "weather" in groups
        assert "policy" in groups
        assert "safety" in groups


# ============================================================
# 运行测试
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
