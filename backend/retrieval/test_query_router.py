# -*- coding: utf-8 -*-
"""QueryRouter 查询路由测试。"""
import pytest
from retrieval.query_router import QueryRouter, Route


class TestQueryRouter:
    """QueryRouter 路由分类测试。"""

    def setup_method(self):
        self.router = QueryRouter()

    def test_empty_query_returns_general(self):
        assert self.router.route("") == Route.GENERAL
        assert self.router.route(None) == Route.GENERAL

    def test_diagnosis_query_routes_to_rag_direct(self):
        # 作物 + 病害名 → RAG_DIRECT
        assert self.router.route("水稻稻飞虱怎么防治") == Route.RAG_DIRECT
        assert self.router.route("小麦条锈病怎么治") == Route.RAG_DIRECT
        assert self.router.route("玉米螟虫用什么药") == Route.RAG_DIRECT

    def test_crop_with_diagnosis_keyword_routes_to_rag_direct(self):
        assert self.router.route("水稻什么病") == Route.RAG_DIRECT
        assert self.router.route("柑橘有什么虫害") == Route.RAG_DIRECT

    def test_weather_query_routes_to_tool_first(self):
        assert self.router.route("今天天气怎么样") == Route.TOOL_FIRST
        assert self.router.route("明天会下雨吗") == Route.TOOL_FIRST
        assert self.router.route("最近气温多少") == Route.TOOL_FIRST

    def test_weather_with_crop_routes_to_rag_direct(self):
        # 天气 + 作物 + 病害 → 仍走 RAG_DIRECT
        assert self.router.route("水稻稻飞虱的天气") == Route.RAG_DIRECT

    def test_compound_question_routes_to_rag_decomposed(self):
        assert self.router.route("水稻怎么施肥和灌溉") == Route.RAG_DECOMPOSED
        assert self.router.route("小麦什么时候播种比较好") == Route.RAG_DECOMPOSED

    def test_crop_only_routes_to_rag_decomposed(self):
        assert self.router.route("水稻") == Route.RAG_DECOMPOSED
        assert self.router.route("柑橘") == Route.RAG_DECOMPOSED

    def test_general_non_agricultural(self):
        # 纯非农业问题，无任何农业关键词
        # 注意：含"怎么"的查询会被路由到 RAG_DECOMPOSED，这是正确的
        # 因为 Router 无法判断是否农业，需要 domain_guard 进一步过滤
        assert self.router.route("怎么做红烧肉") == Route.RAG_DECOMPOSED
        assert self.router.route("Python怎么学") == Route.RAG_DECOMPOSED
        assert self.router.route("你好") == Route.GENERAL
        assert self.router.route("谢谢") == Route.GENERAL


class TestQueryRouterScenario:
    """QueryRouter 场景分类测试。"""

    def setup_method(self):
        self.router = QueryRouter()

    def test_diagnosis_scenario(self):
        assert self.router.classify_scenario("水稻稻飞虱怎么防治") == "diagnosis"
        assert self.router.classify_scenario("小麦什么病") == "diagnosis"
        assert self.router.classify_scenario("柑橘溃疡病症状") == "diagnosis"

    def test_fertilizer_scenario(self):
        assert self.router.classify_scenario("水稻怎么施肥") == "fertilizer"
        assert self.router.classify_scenario("小麦追肥方案") == "fertilizer"
        assert self.router.classify_scenario("柑橘灌溉技术") == "fertilizer"

    def test_calendar_scenario(self):
        assert self.router.classify_scenario("水稻什么时候播种") == "calendar"
        assert self.router.classify_scenario("小麦播期") == "calendar"
        assert self.router.classify_scenario("柑橘几月收获") == "calendar"

    def test_policy_scenario(self):
        assert self.router.classify_scenario("农业补贴政策") == "policy"
        assert self.router.classify_scenario("农药登记标准") == "policy"

    def test_no_scenario_returns_none(self):
        assert self.router.classify_scenario("你好") is None
        assert self.router.classify_scenario("谢谢") is None


class TestQueryRouterHints:
    """QueryRouter 检索提示测试。"""

    def setup_method(self):
        self.router = QueryRouter()

    def test_diagnosis_hints(self):
        hints = self.router.get_search_hints("水稻稻飞虱怎么防治")
        assert hints.get("strategy_boost") == "pest"
        assert "pest" in hints.get("category_filter", [])

    def test_fertilizer_hints(self):
        hints = self.router.get_search_hints("水稻怎么施肥")
        assert hints.get("strategy_boost") == "fertilizer"

    def test_crop_extraction(self):
        hints = self.router.get_search_hints("水稻稻飞虱怎么防治")
        assert hints.get("crop") == "水稻"

    def test_pest_extraction(self):
        hints = self.router.get_search_hints("水稻稻飞虱怎么防治")
        assert hints.get("pest") == "稻飞虱"
