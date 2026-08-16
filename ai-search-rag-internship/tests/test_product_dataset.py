from phase2_semantic_search.product_dataset import build_product_catalog, build_product_queries
from phase2_semantic_search.product_baseline import evaluate_product_bm25
from phase2_semantic_search.query_rewrite import rewrite_query


def test_product_dataset_has_stable_scale_and_qrels() -> None:
    catalog = build_product_catalog(500)
    queries, qrels = build_product_queries(catalog)

    assert len(catalog) == 500
    assert len({product["id"] for product in catalog}) == 500
    assert len(queries) == 50
    assert set(qrels) == {query["query_id"] for query in queries}
    assert all(query["relevant_ids"] for query in queries)


def test_product_text_keeps_business_fields_searchable() -> None:
    product = build_product_catalog(500)[0]

    assert product["title"] in product["text"]
    assert product["category"] in product["text"]
    assert product["description"] in product["text"]


def test_product_baseline_preserves_a_nontrivial_bad_case_signal() -> None:
    catalog = build_product_catalog(500)
    queries, _ = build_product_queries(catalog)

    result = evaluate_product_bm25(catalog, queries, top_k=10)

    assert result["metrics"]["recall@10"] < 1.0
    assert result["query_type_metrics"]["exact_category"]["recall@10"] == 1.0
    assert result["bad_cases"]


def test_query_rewrite_appends_a_canonical_attribute() -> None:
    result = rewrite_query("想找无线耳机，用于通勤，重点是充一次电用很久")

    assert result.applied_rules
    assert result.applied_rules[0].canonical_term == "长续航"
    assert result.rewritten_query.endswith("长续航")
