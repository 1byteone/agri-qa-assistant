from knowledge_base import KnowledgeBase


def test_strategy_selection_matches_agriculture_scenarios():
    assert KnowledgeBase.choose_strategy("江西早稻什么时候播种") == "hybrid-temporal"
    assert KnowledgeBase.choose_strategy("农药登记标准和官方政策文件") == "hybrid-metadata"
    assert KnowledgeBase.choose_strategy("水稻稻飞虱怎么防治") == "hybrid"


def test_query_terms_support_chinese_bigrams_and_identifiers():
    terms = KnowledgeBase._query_terms("水稻 稻飞虱 ID-22")
    assert "水稻" in terms
    assert "稻飞" in terms
    assert "id" in terms
