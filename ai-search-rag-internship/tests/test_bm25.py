from phase2_semantic_search import BM25Retriever


def test_bm25_prefers_exact_model_term() -> None:
    retriever = BM25Retriever(
        [
            {"id": "exact", "text": "BGE-M3 模型支持多种检索"},
            {"id": "semantic", "text": "语义向量可以找到相近含义"},
        ]
    )

    results = retriever.search("BGE-M3 模型", top_k=2)

    assert results[0].doc_id == "exact"
    assert results[0].score > 0

