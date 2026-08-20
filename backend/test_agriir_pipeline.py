from agriir_pipeline import AgriIRPipeline, PipelineConfig, StageConfig


class StubKnowledgeBase:
    @staticmethod
    def choose_strategy(_query):
        return "hybrid"

    @staticmethod
    def search(query, top_k=3, strategy="hybrid"):
        rows = {
            "水稻稻飞虱防治": [{"content": "稻飞虱应在若虫盛发期综合防治。", "metadata": {"source": "江西农技规程", "content_hash": "a"}, "relevance": 0.9}],
            "水稻田观察": [{"content": "稻飞虱应在若虫盛发期综合防治。", "metadata": {"source": "江西农技规程", "content_hash": "a"}, "relevance": 0.8}],
        }
        return rows.get(query, [])[:top_k]


def test_pipeline_is_configurable_and_deduplicates_results():
    pipeline = AgriIRPipeline(PipelineConfig(max_subqueries=4, citation_threshold=0.75, stages=(StageConfig("parallel_retrieval", top_k=3),)))
    trace = pipeline.retrieve("水稻稻飞虱防治和水稻田观察", StubKnowledgeBase())
    assert trace["subqueries"] == ["水稻稻飞虱防治", "水稻田观察"]
    assert len(trace["results"]) == 1
    assert trace["citations"][0]["label"] == "S1"
    assert trace["citations"][0]["eligible"] is True


def test_citation_ids_are_stable_and_answer_block_is_deterministic():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.75))
    citations = pipeline.build_citations([{"content": "水稻分蘖期保持浅水层。", "metadata": {"source": "农技规程"}, "relevance": 0.8}])
    again = pipeline.build_citations([{"content": "水稻分蘖期保持浅水层。", "metadata": {"source": "农技规程"}, "relevance": 0.8}])
    assert citations[0]["id"] == again[0]["id"]
    answer = pipeline.append_citation_block("## 现在做什么\n保持浅水层。", citations)
    assert "## 参考来源" in answer
    assert "[S1]" in answer


def test_high_risk_queries_require_level_a_evidence():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.75))
    result = {"content": "建议施肥", "metadata": {"source": "普通知识库", "evidence_level": "B", "evidence_scope": "rice_fertilizer_recommendation"}, "relevance": 0.95}
    assert pipeline.build_citations([result], query="水稻施肥用量")[0]["eligible"] is False
    result["metadata"]["evidence_level"] = "A"
    assert pipeline.build_citations([result], query="水稻施肥用量")[0]["eligible"] is True


def test_colloquial_fertilizer_quantity_phrase_requires_official_scope():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.75))
    assert pipeline.requires_official_evidence("水稻每亩施多少肥") is True
    assert pipeline.required_evidence_scope("水稻每亩施多少肥") == "rice_fertilizer_recommendation"


def test_crop_specific_fertilizer_evidence_does_not_cross_apply():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.5))
    result = {"content": "水稻测土施肥", "metadata": {"source": "农业农村部", "evidence_level": "A", "evidence_scope": "rice_fertilizer_recommendation"}, "relevance": 0.9}
    assert pipeline.build_citations([result], query="水稻分蘖期如何施肥")[0]["eligible"] is True
    assert pipeline.build_citations([result], query="油菜蕾薹期是否追肥")[0]["eligible"] is False


def test_crop_specific_fertilizer_query_adds_only_its_own_retrieval_anchor():
    pipeline = AgriIRPipeline(PipelineConfig())
    rice = pipeline.refine_query("南昌水稻分蘖期如何根据测土结果安排施肥？")
    rapeseed = pipeline.refine_query("油菜蕾薹期是否需要追肥？")
    assert "水稻施肥 测土配方 目标产量 土壤肥力" in rice
    assert "油菜施肥 测土配方 蕾薹期" in rapeseed
    assert "水稻施肥" not in rapeseed


def test_high_risk_retrieval_keeps_matching_official_evidence_in_top_k():
    class ScopeKnowledgeBase:
        @staticmethod
        def choose_strategy(_query):
            return "hybrid"

        @staticmethod
        def search(query, top_k=3, strategy="hybrid"):
            background = {"content": "通用施肥背景", "metadata": {"content_hash": "background"}, "relevance": 0.95}
            official = {"content": "水稻测土配方施肥", "metadata": {"content_hash": "rice-official", "evidence_level": "A", "evidence_scope": "rice_fertilizer_recommendation"}, "relevance": 0.55}
            return [background, official][:top_k]

    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.5, stages=(StageConfig("parallel_retrieval", top_k=1),)))
    trace = pipeline.retrieve("水稻分蘖期如何施肥", ScopeKnowledgeBase())
    assert trace["results"][0]["metadata"]["content_hash"] == "rice-official"
    assert trace["citations"][0]["eligible"] is True


def test_embedding_specific_threshold_is_used_for_local_retrieval():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.75, citation_threshold_by_embedding={"local": 0.55}))

    class LocalKnowledgeBase:
        embedding_mode = "local"

    result = {"content": "农药登记制度", "metadata": {"source": "农业农村部", "evidence_level": "A", "evidence_scope": "pesticide_registration"}, "relevance": 0.6}
    assert pipeline.build_citations([result], query="农药登记", threshold=pipeline.citation_threshold_for(LocalKnowledgeBase()))[0]["eligible"] is True


def test_high_risk_citation_requires_matching_evidence_scope():
    pipeline = AgriIRPipeline(PipelineConfig(citation_threshold=0.5))
    result = {"content": "农药登记制度", "metadata": {"source": "农业农村部", "evidence_level": "A", "evidence_scope": "pesticide_governance|pesticide_registration"}, "relevance": 0.8}
    assert pipeline.build_citations([result], query="农药登记制度")[0]["eligible"] is True
    citation = pipeline.build_citations([result], query="水稻农药每亩用量")[0]
    assert citation["eligible"] is False
    assert citation["eligibility_reason"] == "evidence-scope-required"
