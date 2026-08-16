"""Project service: ingest Phase 1 chunks and search them with BM25."""

from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from phase1_doc_parser.main import build_chunks
from phase1_doc_parser.splitter import RecursiveSplitter
from phase2_semantic_search import BM25Retriever, SearchResult


class KnowledgeBase:
    def __init__(self) -> None:
        self.chunks: list[dict[str, object]] = []
        self.retriever: BM25Retriever | None = None
        self.input_dir: Path | None = None
        self.index_version = "empty"

    def ingest(self, input_dir: str | Path, *, chunk_size: int = 512, overlap: int = 128) -> int:
        directory = Path(input_dir)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: {directory}")
        self.chunks = build_chunks(directory, RecursiveSplitter(chunk_size=chunk_size, overlap=overlap))
        self.retriever = BM25Retriever(self.chunks)
        self.input_dir = directory
        self.index_version = f"chunks-{len(self.chunks)}-size-{chunk_size}-overlap-{overlap}"
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 5, source: str | None = None) -> list[dict[str, Any]]:
        if self.retriever is None:
            return []

        def matches_source(document: dict[str, object]) -> bool:
            return not source or str(document.get("source", "")).endswith(source)

        results = self.retriever.search(query, top_k=top_k, predicate=matches_source)
        return [self._serialize_result(result) for result in results]

    @staticmethod
    def _serialize_result(result: SearchResult) -> dict[str, Any]:
        return {
            "chunk_id": result.doc_id,
            "text": result.text,
            "source": result.metadata.get("source"),
            "page": result.metadata.get("page"),
            "score": round(result.score, 6),
            "metadata": result.metadata,
        }

    def evidence_answer(self, query: str, results: list[dict[str, Any]]) -> str:
        if not results:
            return "当前知识库没有找到足够证据，无法回答该问题。"
        evidence_lines = [
            f"[{item['chunk_id']}] {item['text']}"
            for item in results[:3]
        ]
        return "当前为 evidence-only 模式。请依据以下可追溯证据作答：\n" + "\n".join(evidence_lines)

    def answer(self, query: str, results: list[dict[str, Any]]) -> tuple[str, str]:
        """Use an optional OpenAI-compatible model, with an explicit local fallback."""

        fallback = self.evidence_answer(query, results)
        api_key = os.getenv("OPENAI_API_KEY")
        llm_enabled = os.getenv("RAG_ENABLE_LLM", "false").lower() == "true"
        if not llm_enabled or not api_key or not results:
            return fallback, "evidence-only"

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or None,
            )
            context = "\n".join(f"[{item['chunk_id']}] {item['text']}" for item in results[:5])
            response = client.chat.completions.create(
                model=os.getenv("RAG_LLM_MODEL", "gpt-4o-mini"),
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "只根据给定证据回答。无法由证据支持时明确说不知道，并在关键事实后保留 [chunk_id] 引用。",
                    },
                    {"role": "user", "content": f"问题：{query}\n\n证据：\n{context}"},
                ],
            )
            content = response.choices[0].message.content or ""
            return content.strip() or fallback, "llm"
        except Exception:
            return fallback, "evidence-only-fallback"
