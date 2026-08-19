# -*- coding: utf-8 -*-
"""Parent-Child 分块索引测试。"""
import pytest
from langchain_core.documents import Document
from retrieval.parent_child import ParentChildIndexer


class TestParentChildIndexer:
    """Parent-Child 索引器测试。"""

    def _make_doc(self, content: str, **kwargs) -> Document:
        return Document(page_content=content, metadata=kwargs or {})

    def test_add_short_document(self):
        indexer = ParentChildIndexer(parent_chunk_size=200, child_chunk_size=100)
        doc = self._make_doc("短文档内容", category="crop")
        results = indexer.add_documents([doc])
        assert len(results) >= 1
        child_docs, parent_id = results[0]
        assert len(child_docs) >= 1
        assert parent_id
        assert indexer.parent_count >= 1
        assert indexer.child_count >= 1

    def test_add_long_document_creates_multiple_parents(self):
        indexer = ParentChildIndexer(parent_chunk_size=100, child_chunk_size=50)
        # 500 字符应拆分为多个 parent
        content = "这是一段较长的农业知识内容。" * 50  # ~450 chars
        doc = self._make_doc(content, category="crop")
        results = indexer.add_documents([doc])
        assert len(results) >= 2  # 应该有多个 parent

    def test_get_parent_context(self):
        indexer = ParentChildIndexer(parent_chunk_size=500, child_chunk_size=200)
        doc = self._make_doc("水稻稻飞虱防治知识", category="pest")
        results = indexer.add_documents([doc])
        child_docs, parent_id = results[0]
        # 子块 metadata 应包含 parent_id
        child_meta = child_docs[0].metadata
        assert "parent_id" in child_meta
        # 通过子块 metadata 恢复父文档
        parent_text = indexer.get_parent_context(child_meta)
        assert parent_text is not None
        assert "水稻稻飞虱" in parent_text

    def test_enrich_results_adds_parent_context(self):
        indexer = ParentChildIndexer(parent_chunk_size=500, child_chunk_size=200)
        doc = self._make_doc("水稻施肥技术要点", category="fertilizer")
        results = indexer.add_documents([doc])
        child_docs, parent_id = results[0]
        # 模拟检索结果
        search_results = [
            {
                "content": child_docs[0].page_content,
                "metadata": child_docs[0].metadata,
                "relevance": 0.9,
            }
        ]
        enriched = indexer.enrich_results(search_results)
        assert "parent_context" in enriched[0]
        assert "水稻施肥" in enriched[0]["parent_context"]

    def test_dedupe_by_parent(self):
        indexer = ParentChildIndexer(parent_chunk_size=200, child_chunk_size=100)
        # 使用较长文本确保拆分为多个 child 块
        content = "这是关于水稻种植的详细知识内容，包含病虫害防治、施肥灌溉等多方面信息。" * 5
        doc = self._make_doc(content, category="crop")
        results = indexer.add_documents([doc])
        child_docs, parent_id = results[0]
        # 确保有多个 child 块
        if len(child_docs) >= 2:
            # 构造多个来自同一 parent 的结果
            search_results = [
                {"content": cd.page_content, "metadata": dict(cd.metadata), "relevance": 0.9 - i * 0.1}
                for i, cd in enumerate(child_docs[:3])
            ]
            deduped = indexer.dedupe_by_parent(search_results, max_per_parent=1)
            assert len(deduped) == 1
        else:
            # 文本不够长，只有一个 child 块
            pytest.skip("文本不够长，无法测试去重")

    def test_empty_documents(self):
        indexer = ParentChildIndexer()
        results = indexer.add_documents([])
        assert results == []
        assert indexer.parent_count == 0
        assert indexer.child_count == 0

    def test_metadata_preserved(self):
        indexer = ParentChildIndexer(parent_chunk_size=500, child_chunk_size=200)
        doc = self._make_doc("柑橘黄龙病防治", category="pest", region="赣南")
        results = indexer.add_documents([doc])
        child_docs, _ = results[0]
        meta = child_docs[0].metadata
        assert meta["category"] == "pest"
        assert meta["region"] == "赣南"
        assert meta["is_child"] is True
        assert "parent_id" in meta
        assert "content_hash" in meta
