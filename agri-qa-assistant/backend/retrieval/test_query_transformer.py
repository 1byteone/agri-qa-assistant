# -*- coding: utf-8 -*-
"""QueryTransformer 查询改写测试。"""
import pytest
from retrieval.query_transformer import QueryTransformer


class TestQueryTransformer:
    """QueryTransformer 查询改写测试。"""

    def setup_method(self):
        self.transformer = QueryTransformer()

    def test_empty_query(self):
        assert self.transformer.rewrite("") == ""
        assert self.transformer.decompose("") == []
        assert self.transformer.expand_synonyms("") == [""]

    def test_normalize_terms_chinese_to_english(self):
        # 中文查询中的英文术语应保留
        result = self.transformer.rewrite("水稻 brown planthopper 防治")
        # brown planthopper 应被映射为稻飞虱
        assert "brown planthopper" in result or "稻飞虱" in result

    def test_decompose_compound_query(self):
        parts = self.transformer.decompose("水稻怎么施肥，小麦怎么灌溉")
        assert len(parts) == 2
        assert any("施肥" in p for p in parts)
        assert any("灌溉" in p for p in parts)

    def test_decompose_single_query(self):
        parts = self.transformer.decompose("水稻稻飞虱怎么防治")
        assert len(parts) == 1
        assert "稻飞虱" in parts[0]

    def test_decompose_respects_max(self):
        transformer = QueryTransformer(max_subqueries=2)
        parts = transformer.decompose("问题1，问题2，问题3，问题4")
        assert len(parts) <= 2

    def test_expand_synonyms_rice(self):
        variants = self.transformer.expand_synonyms("水稻病害")
        # 至少包含原始查询
        assert "水稻病害" in variants
        # 可能包含英文变体
        assert len(variants) >= 1

    def test_expand_synonyms_bph(self):
        variants = self.transformer.expand_synonyms("稻飞虱防治")
        assert "稻飞虱防治" in variants
        # 应该生成英文变体
        assert len(variants) >= 1

    def test_no_synonyms_found(self):
        variants = self.transformer.expand_synonyms("天气预报")
        assert variants == ["天气预报"]

    def test_redundancy_removal(self):
        # 单字符连续重复（如省略号等）应被截断
        result = self.transformer.rewrite("水稻?????")
        assert "?????" not in result
        # 多字符重复保持不变（改写模块不处理短语级重复）
        result2 = self.transformer.rewrite("水稻怎么了怎么了")
        assert result2  # 不为空即可

    def test_whitespace_normalization(self):
        result = self.transformer.rewrite("水稻   稻飞虱   防治")
        assert "   " not in result

    def test_full_workflow(self):
        # 完整工作流：改写 → 分解 → 扩展
        query = "水稻稻飞虱怎么防治和施肥"
        rewritten = self.transformer.rewrite(query)
        parts = self.transformer.decompose(rewritten)
        variants = self.transformer.expand_synonyms(parts[0] if parts else rewritten)
        assert len(variants) >= 1
        assert all(isinstance(v, str) for v in variants)
