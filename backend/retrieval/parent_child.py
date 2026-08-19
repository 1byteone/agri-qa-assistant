# -*- coding: utf-8 -*-
"""
Parent-Child 分块索引器。

解决 chunk 断裂问题：检索时使用小块（child），返回时恢复大块上下文（parent）。

工作流程：
1. ingest 时：文档 → 大块（parent, 2000 chars）→ 小块（child, 1000 chars）
2. child 存入 ChromaDB 用于检索
3. parent 存入内存映射，检索时按 parent_id 恢复
"""
from __future__ import annotations
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ParentChildIndexer:
    """父文档索引器：保存 child → parent 的映射，用于上下文恢复。

    Parameters
    ----------
    parent_chunk_size : int
        父块大小（字符数）。默认 2000。
    parent_chunk_overlap : int
        父块重叠。默认 200。
    child_chunk_size : int
        子块大小（字符数）。默认 1000。
    child_chunk_overlap : int
        子块重叠。默认 200。
    """

    def __init__(
        self,
        parent_chunk_size: int = 2000,
        parent_chunk_overlap: int = 200,
        child_chunk_size: int = 1000,
        child_chunk_overlap: int = 200,
    ):
        # overlap 不能超过 chunk_size 的一半
        parent_chunk_overlap = min(parent_chunk_overlap, parent_chunk_size // 2)
        child_chunk_overlap = min(child_chunk_overlap, child_chunk_size // 2)
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_chunk_overlap,
            separators=["\n\n", "\n", "。", "；", " ", ""],
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=child_chunk_overlap,
            separators=["\n\n", "\n", "。", "；", " ", ""],
        )
        # parent_id → parent_text
        self._parent_map: Dict[str, str] = {}
        # child_content_hash → parent_id
        self._child_to_parent: Dict[str, str] = {}

    def add_documents(
        self, docs: List[Document]
    ) -> List[Tuple[List[Document], str]]:
        """将文档分块为 parent-child 结构。

        Returns
        -------
        list of (child_docs, parent_id)
            每个原文档对应的子块列表和父块 ID。
        """
        results = []
        for doc in docs:
            parent_chunks = self.parent_splitter.split_text(doc.page_content)
            for parent_text in parent_chunks:
                parent_id = _stable_hash(parent_text)
                self._parent_map[parent_id] = parent_text

                child_chunks = self.child_splitter.split_text(parent_text)
                child_docs = []
                for child_text in child_chunks:
                    child_hash = _stable_hash(child_text)
                    self._child_to_parent[child_hash] = parent_id
                    child_doc = Document(
                        page_content=child_text,
                        metadata={
                            **(doc.metadata or {}),
                            "parent_id": parent_id,
                            "content_hash": child_hash,
                            "is_child": True,
                            "parent_chunk_size": len(parent_text),
                        },
                    )
                    child_docs.append(child_doc)
                results.append((child_docs, parent_id))

        logger.info(
            "ParentChildIndexer: %d docs → %d parents → %d children",
            len(docs),
            len(self._parent_map),
            sum(len(chunks) for chunks, _ in results),
        )
        return results

    def get_parent_context(self, child_metadata: Dict[str, Any]) -> Optional[str]:
        """根据子块元数据恢复父文档上下文。

        Parameters
        ----------
        child_metadata : dict
            子块的 metadata，须包含 parent_id 字段。

        Returns
        -------
        str or None
            父文档全文；若未找到返回 None。
        """
        parent_id = child_metadata.get("parent_id")
        if not parent_id:
            return None
        return self._parent_map.get(parent_id)

    def get_parent_id(self, child_metadata: Dict[str, Any]) -> Optional[str]:
        """获取子块对应的 parent_id。"""
        return child_metadata.get("parent_id")

    def enrich_results(
        self,
        results: List[Dict[str, Any]],
        include_parent: bool = True,
    ) -> List[Dict[str, Any]]:
        """为检索结果附加父文档上下文。

        Parameters
        ----------
        results : list of dict
            检索结果，每项须包含 metadata 字段。
        include_parent : bool
            是否在结果中附加 parent_context 字段。

        Returns
        -------
        list of dict
            附加了 parent_context 的结果列表（原地修改 + 返回）。
        """
        for result in results:
            metadata = result.get("metadata") or {}
            parent_id = metadata.get("parent_id")
            if parent_id and include_parent:
                parent_text = self._parent_map.get(parent_id)
                if parent_text:
                    result["parent_context"] = parent_text
        return results

    def dedupe_by_parent(
        self,
        results: List[Dict[str, Any]],
        max_per_parent: int = 1,
    ) -> List[Dict[str, Any]]:
        """按 parent_id 去重，每个 parent 最多保留 max_per_parent 个子块。

        Parameters
        ----------
        results : list of dict
            检索结果。
        max_per_parent : int
            每个 parent 最多保留的子块数。

        Returns
        -------
        list of dict
            去重后的结果（保留分数最高的子块）。
        """
        parent_counts: Dict[str, int] = {}
        deduped = []
        for result in results:
            metadata = result.get("metadata") or {}
            parent_id = metadata.get("parent_id") or _doc_key(result)
            count = parent_counts.get(parent_id, 0)
            if count < max_per_parent:
                deduped.append(result)
                parent_counts[parent_id] = count + 1
        return deduped

    @property
    def parent_count(self) -> int:
        return len(self._parent_map)

    @property
    def child_count(self) -> int:
        return len(self._child_to_parent)


def _stable_hash(text: str) -> str:
    """生成内容的稳定哈希（SHA-256 前 16 位）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _doc_key(result: Dict[str, Any]) -> str:
    """从检索结果生成文档去重键。"""
    metadata = result.get("metadata") or {}
    return metadata.get("content_hash") or _stable_hash(result.get("content", "")[:200])
