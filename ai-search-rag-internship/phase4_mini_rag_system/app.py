"""FastAPI application for the evidence-first Mini RAG project."""

from __future__ import annotations

from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from .knowledge_base import KnowledgeBase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "phase1_doc_parser" / "examples" / "input"
STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


class IngestRequest(BaseModel):
    input_dir: str | None = None
    chunk_size: int = Field(default=512, ge=32, le=4096)
    overlap: int = Field(default=128, ge=0, lt=4096)

    @model_validator(mode="after")
    def validate_overlap(self) -> "IngestRequest":
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        return self


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    source: str | None = None


class ChatRequest(SearchRequest):
    pass


def create_app(input_dir: str | Path = DEFAULT_INPUT_DIR) -> FastAPI:
    knowledge_base = KnowledgeBase()
    knowledge_base.ingest(input_dir)
    app = FastAPI(title="EvidenceDesk Mini RAG", version="0.1.0")
    app.state.knowledge_base = knowledge_base

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_INDEX)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "chunks": len(knowledge_base.chunks),
            "index_version": knowledge_base.index_version,
        }

    @app.post("/documents/ingest")
    def ingest(request: IngestRequest) -> dict[str, object]:
        target = Path(request.input_dir) if request.input_dir else input_dir
        try:
            count = knowledge_base.ingest(target, chunk_size=request.chunk_size, overlap=request.overlap)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail={"code": "INPUT_DIR_NOT_FOUND", "message": str(exc)}) from exc
        return {"chunks": count, "index_version": knowledge_base.index_version}

    @app.post("/search")
    def search(request: SearchRequest) -> dict[str, object]:
        results = knowledge_base.search(request.query, top_k=request.top_k, source=request.source)
        return {
            "query": request.query,
            "results": results,
            "trace_id": f"search-{uuid.uuid4().hex[:12]}",
            "index_version": knowledge_base.index_version,
        }

    @app.post("/chat")
    def chat(request: ChatRequest) -> dict[str, object]:
        results = knowledge_base.search(request.query, top_k=request.top_k, source=request.source)
        answer, mode = knowledge_base.answer(request.query, results)
        return {
            "query": request.query,
            "answer": answer,
            "citations": results,
            "trace_id": f"chat-{uuid.uuid4().hex[:12]}",
            "mode": mode,
            "index_version": knowledge_base.index_version,
        }

    return app


app = create_app()
