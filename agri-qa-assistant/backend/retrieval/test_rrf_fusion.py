# -*- coding: utf-8 -*-
"""RRF 融合检索测试。"""
import pytest
from retrieval.rrf_fusion import rrf_fusion, RRFFusion


class TestRRFFusion:
    """RRF 融合算法测试。"""

    def test_empty_input_returns_empty(self):
        assert rrf_fusion([]) == []

    def test_single_list_passthrough(self):
        items = [
            {"content": "doc_a", "relevance": 0.9},
            {"content": "doc_b", "relevance": 0.7},
        ]
        result = rrf_fusion([items])
        assert len(result) == 2
        # 第一个文档 RRF 分数应最高
        assert result[0]["rrf_score"] > result[1]["rrf_score"]

    def test_two_lists_merge_and_rank(self):
        list_a = [
            {"content": "doc_a", "relevance": 0.9},
            {"content": "doc_b", "relevance": 0.7},
            {"content": "doc_c", "relevance": 0.5},
        ]
        list_b = [
            {"content": "doc_b", "relevance": 0.8},  # list_b 中 doc_b 排第一
            {"content": "doc_a", "relevance": 0.6},
            {"content": "doc_d", "relevance": 0.4},
        ]
        result = rrf_fusion([list_a, list_b])
        # 应该有 4 个唯一文档
        assert len(result) == 4
        # doc_a 和 doc_b 都出现在两路中，应排名靠前
        top_contents = [r["content"] for r in result[:2]]
        assert "doc_a" in top_contents
        assert "doc_b" in top_contents

    def test_weights_affect_ranking(self):
        list_a = [{"content": "doc_a", "relevance": 0.9}]
        list_b = [{"content": "doc_b", "relevance": 0.9}]
        # list_a 权重 0.9, list_b 权重 0.1
        result = rrf_fusion([list_a, list_b], weights=[0.9, 0.1])
        assert result[0]["content"] == "doc_a"

    def test_deduplication_by_content_hash(self):
        list_a = [{"content": "doc_a", "metadata": {"content_hash": "hash_a"}, "relevance": 0.9}]
        list_b = [{"content": "doc_a_copy", "metadata": {"content_hash": "hash_a"}, "relevance": 0.8}]
        result = rrf_fusion([list_a, list_b])
        # 应该去重为 1 个
        assert len(result) == 1
        assert result[0]["metadata"]["content_hash"] == "hash_a"

    def test_rrf_score_is_positive(self):
        items = [{"content": "doc_a", "relevance": 0.5}]
        result = rrf_fusion([items], k=60)
        assert result[0]["rrf_score"] > 0

    def test_k_parameter_controls_decay(self):
        # k 越小，排名靠前的文档优势越大
        list_a = [{"content": f"doc_{i}", "relevance": 0.9 - i * 0.1} for i in range(5)]
        result_small_k = rrf_fusion([list_a], k=1)
        result_large_k = rrf_fusion([list_a], k=1000)
        # 两种 k 值下排名应该一致（单路无差异）
        assert [r["content"] for r in result_small_k] == [r["content"] for r in result_large_k]

    def test_weight_mismatch_raises(self):
        with pytest.raises(ValueError, match="weights 长度"):
            rrf_fusion([[], []], weights=[0.5])


class TestRRFFusionClass:
    """RRFFusion 类测试。"""

    def test_fuse_with_named_routes(self):
        fusion = RRFFusion(k=60)
        ranked = {
            "vector": [
                {"content": "doc_a", "relevance": 0.9},
                {"content": "doc_b", "relevance": 0.7},
            ],
            "lexical": [
                {"content": "doc_b", "relevance": 0.8},
                {"content": "doc_a", "relevance": 0.6},
            ],
        }
        result = fusion.fuse(ranked)
        assert len(result) == 2
        # doc_a 和 doc_b 都在两路中
        contents = [r["content"] for r in result]
        assert "doc_a" in contents
        assert "doc_b" in contents

    def test_custom_weights(self):
        fusion = RRFFusion(k=60, weights={"vector": 0.8, "lexical": 0.2})
        ranked = {
            "vector": [{"content": "doc_a", "relevance": 0.9}],
            "lexical": [{"content": "doc_b", "relevance": 0.9}],
        }
        result = fusion.fuse(ranked)
        # vector 权重高，doc_a 应排第一
        assert result[0]["content"] == "doc_a"

    def test_empty_input(self):
        fusion = RRFFusion()
        assert fusion.fuse({}) == []
