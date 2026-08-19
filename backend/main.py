import os
import logging
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict, Any
from urllib.parse import urlparse

import requests

# 限制 OpenBLAS / MKL 线程数，避免 Windows 下内存分配失败
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import settings
from schemas import ChatRequest, ChatResponse, EvaluationAnnotationRequest, HealthResponse, KnowledgeBaseStatus
from agent import agri_agent
from tools import get_mcp_status
from knowledge_base import knowledge_base, init_default_knowledge_base
from memory import conversation_memory
from document_ingestion import DocumentIngestionError, MAX_UPLOAD_BYTES, parse_document, public_analysis
from agri_terms import lookup_term
from agriir_pipeline import agriir_pipeline
from agriir_evaluation import annotate_eval_item, build_review_queue, evaluate_retrieval, load_eval_items
from source_registry import SourceValidationError, build_evidence_metadata, list_sources

logger = logging.getLogger(__name__)

_RESOURCE_IMAGE_HOSTS = {
    "upload.wikimedia.org",
    "images.unsplash.com",
    "images.pexels.com",
    "cdn.pixabay.com",
}
_RESOURCE_IMAGE_MAX_BYTES = 8 * 1024 * 1024


def _allowed_resource_image_host(hostname: str) -> bool:
    return hostname in _RESOURCE_IMAGE_HOSTS or hostname.endswith(".wikimedia.org")


def encode_sse(event: Dict[str, Any]) -> str:
    """Encode one complete SSE frame. JSON stays within the event boundary."""
    event_type = str(event.get("type", "message"))
    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化 AgriQA Assistant...")
    await conversation_memory.initialize()
    try:
        init_default_knowledge_base()
    except Exception as e:
        logger.warning(f"知识库初始化失败，将以通用模式运行: {e}")
    logger.info("初始化完成")
    yield
    # 关闭时清理
    logger.info("正在关闭应用...")


app = FastAPI(
    title="AgriQA Assistant",
    description="面向农业领域的智能问答原型系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    kb_status = knowledge_base.get_status()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        knowledge_base=KnowledgeBaseStatus(**kb_status),
        llm_connected=True,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """多轮对话接口"""
    try:
        result = await agri_agent.chat(
            message=request.message,
            thread_id=request.thread_id,
            user_id=request.user_id,
            answer_mode=request.answer_mode,
            scenario_context=request.scenario_context,
        )
        return ChatResponse(
            thread_id=result["thread_id"],
            message=result["message"],
            sources=result.get("sources"),
            tool_calls=result.get("tool_calls"),
            answer_mode=result.get("answer_mode", request.answer_mode),
            completion_status=result.get("completion_status", "complete"),
        )
    except Exception as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """POST-compatible SSE endpoint for token and structured UI events."""
    async def event_stream():
        try:
            async for event in agri_agent.stream_chat(
                message=request.message,
                thread_id=request.thread_id,
                user_id=request.user_id,
                answer_mode=request.answer_mode,
                scenario_context=request.scenario_context,
            ):
                yield encode_sse(event)
        except asyncio.CancelledError:
            logger.info("客户端中止了流式请求: %s", request.thread_id)
            raise
        except Exception as exc:
            logger.exception("流式对话处理失败")
            yield encode_sse({"type": "error", "message": "流式服务暂时不可用，请稍后重试。", "detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/mcp/status")
async def mcp_status():
    """Describe embedded MCP-compatible tools without overstating external connectivity."""
    return get_mcp_status()


@app.get("/history/{thread_id}")
async def get_history(thread_id: str, limit: int = 20):
    """获取对话历史"""
    try:
        history = await agri_agent.get_history(thread_id, limit)
        return {"thread_id": thread_id, "history": history}
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads")
async def list_threads(limit: int = 50):
    """List persisted conversations for the session switcher."""
    try:
        return {"threads": await conversation_memory.list_threads(limit)}
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{thread_id}")
async def clear_history(thread_id: str):
    """清空对话历史"""
    try:
        await agri_agent.clear_history(thread_id)
        return {"message": "对话历史已清空"}
    except Exception as e:
        logger.error(f"清空历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete one persisted conversation and its messages."""
    try:
        await agri_agent.clear_history(thread_id)
        return {"message": "会话已删除"}
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/{thread_id}")
async def list_thread_memory(thread_id: str, user_id: str | None = None, include_archived: bool = False):
    """Return structured memory for the explainability panel."""
    try:
        return {"thread_id": thread_id, "memories": await conversation_memory.list_memories(
            thread_id=thread_id, user_id=user_id, include_archived=include_archived
        )}
    except Exception as e:
        logger.error("获取记忆失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/user/{user_id}")
async def list_user_memory(user_id: str, include_archived: bool = False):
    try:
        return {"user_id": user_id, "memories": await conversation_memory.list_memories(
            user_id=user_id, include_archived=include_archived
        )}
    except Exception as e:
        logger.error("获取用户记忆失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    if not await conversation_memory.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="记忆不存在")
    return {"memory_id": memory_id, "status": "deleted"}


@app.post("/memory/{memory_id}/confirm")
async def confirm_memory(memory_id: str):
    memory = await conversation_memory.confirm_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return {"memory": memory}


@app.post("/memory/整理")
async def organize_memory(thread_id: str | None = None, user_id: str | None = None):
    archived = await conversation_memory.archive_stale_memories()
    summary = await conversation_memory.summarize_thread(thread_id, user_id) if thread_id else None
    return {"archived": archived, "summary": summary, "message": "已归档过期记忆并整理当前记忆"}


@app.get("/knowledge-base/status")
async def knowledge_base_status():
    """知识库状态"""
    return knowledge_base.get_status()


@app.get("/knowledge-base/search")
async def knowledge_base_search(query: str, limit: int = 3, strategy: str | None = None):
    """Diagnostic endpoint for confirming retrieval quality without an LLM call."""
    if strategy:
        selected_strategy = strategy
        results = knowledge_base.search(query, top_k=max(1, min(limit, 10)), strategy=selected_strategy)
        return {"query": query, "strategy": selected_strategy, "results": results, "citations": agriir_pipeline.build_citations(results, query=query, threshold=agriir_pipeline.citation_threshold_for(knowledge_base))}
    trace = agriir_pipeline.retrieve(query, knowledge_base)
    trace["results"] = trace["results"][:max(1, min(limit, 10))]
    trace["citations"] = agriir_pipeline.build_citations(trace["results"], query=query, threshold=agriir_pipeline.citation_threshold_for(knowledge_base))
    return trace


@app.get("/agriir/config")
async def agriir_config():
    """Expose the active declarative pipeline for diagnostics and deployment checks."""
    return agriir_pipeline.describe()


@app.get("/evaluations/retrieval")
async def retrieval_evaluation(limit: int | None = None):
    """Run the fixed P0 retrieval baseline; quality metrics await expert labels."""
    if limit is not None and not 1 <= limit <= 120:
        raise HTTPException(status_code=422, detail="limit 必须在 1-120 之间")
    return evaluate_retrieval(knowledge_base, agriir_pipeline, load_eval_items(), limit=limit)


@app.get("/evaluations/items")
async def evaluation_items(scenario: str | None = None, limit: int = 120):
    """List pending or reviewed P0 items for expert annotation."""
    if not 1 <= limit <= 120:
        raise HTTPException(status_code=422, detail="limit 必须在 1-120 之间")
    items = load_eval_items()
    if scenario:
        items = [item for item in items if item.get("scenario") == scenario]
    return {"items": items[:limit], "total": len(items)}


@app.get("/evaluations/review-queue")
async def evaluation_review_queue(scenario: str | None = None, limit: int = 120):
    """Export current candidates for offline expert review without writing labels."""
    if not 1 <= limit <= 120:
        raise HTTPException(status_code=422, detail="limit 必须在 1-120 之间")
    items = load_eval_items()
    if scenario:
        items = [item for item in items if item.get("scenario") == scenario]
    return {"items": build_review_queue(knowledge_base, agriir_pipeline, items[:limit]), "total": len(items)}


@app.post("/evaluations/items/{item_id}/annotation")
async def annotate_evaluation_item(item_id: str, request: EvaluationAnnotationRequest):
    """Store a reviewed label after validating each referenced evidence ID."""
    vectorstore = knowledge_base._get_vectorstore()
    metadata = vectorstore.get(include=["metadatas"]).get("metadatas", [])
    evidence_ids = {str(item.get("evidence_id")) for item in metadata if item and item.get("evidence_id")}
    try:
        item = annotate_eval_item(item_id, request.model_dump(), evidence_ids)
    except KeyError:
        raise HTTPException(status_code=404, detail="评测条目不存在")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"item": item}


@app.get("/agri-terms/lookup")
async def agri_term_lookup(term: str):
    """Return a curated authoritative definition for an optional term marker."""
    item = lookup_term(term)
    if not item:
        raise HTTPException(status_code=404, detail="暂无可核验的专业词条")
    return item


async def _read_upload(file: UploadFile) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        return parse_document(file.filename, file.content_type, data)
    except DocumentIngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/evidence-sources")
async def evidence_sources():
    """List approved source IDs and their admissible domains for evidence packs."""
    return {"sources": list_sources()}


@app.post("/knowledge-base/documents/analyze")
async def analyze_knowledge_document(
    file: UploadFile = File(...),
    source_id: str | None = Form(None),
    source_url: str | None = Form(None),
    published_at: str | None = Form(None),
    region: str | None = Form(None),
    pack_id: str | None = Form(None),
    pack_version: str | None = Form(None),
    evidence_scope: str | None = Form(None),
):
    """Parse and classify an upload without mutating the knowledge base."""
    parsed = await _read_upload(file)
    try:
        evidence = build_evidence_metadata(
            filename=parsed["filename"], content_hash=parsed["content_hash"], content_type=parsed["content_type"],
            source_id=source_id, source_url=source_url, published_at=published_at, region=region, pack_id=pack_id, pack_version=pack_version, evidence_scope=evidence_scope,
        )
    except SourceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**public_analysis(parsed), "evidence": evidence}


@app.post("/knowledge-base/documents")
async def ingest_knowledge_document(
    file: UploadFile = File(...),
    confirm: bool = Form(False),
    source_id: str | None = Form(None),
    source_url: str | None = Form(None),
    published_at: str | None = Form(None),
    region: str | None = Form(None),
    pack_id: str | None = Form(None),
    pack_version: str | None = Form(None),
    evidence_scope: str | None = Form(None),
):
    """Analyze an upload, then ingest only after explicit confirmation."""
    parsed = await _read_upload(file)
    analysis = public_analysis(parsed)
    if not parsed["eligible"]:
        raise HTTPException(status_code=422, detail=analysis)
    try:
        evidence = build_evidence_metadata(
            filename=parsed["filename"], content_hash=parsed["content_hash"], content_type=parsed["content_type"],
            source_id=source_id, source_url=source_url, published_at=published_at, region=region, pack_id=pack_id, pack_version=pack_version, evidence_scope=evidence_scope,
        )
    except SourceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not confirm:
        return {**analysis, "evidence": evidence, "ingested": False, "requires_confirmation": True}
    result = knowledge_base.ingest_document(
        parsed["text"],
        metadata=evidence,
    )
    return {**analysis, "evidence": evidence, **result, "ingested": True}


@app.get("/resource-image")
async def resource_image(url: str):
    """Proxy approved public image hosts so the browser gets a stable image response."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not _allowed_resource_image_host(parsed.hostname):
        raise HTTPException(status_code=403, detail="图片来源不在允许范围内")

    try:
        upstream = await asyncio.to_thread(
            requests.get,
            url,
            headers={
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "User-Agent": "CropWise/1.0 (+https://www.jxau.edu.cn)",
            },
            timeout=20,
            allow_redirects=True,
        )
        upstream.raise_for_status()
        final = urlparse(upstream.url)
        if final.scheme != "https" or not final.hostname or not _allowed_resource_image_host(final.hostname):
            raise HTTPException(status_code=502, detail="图片重定向到不受信任来源")
        content_type = upstream.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=415, detail="资源不是图片")
        if len(upstream.content) > _RESOURCE_IMAGE_MAX_BYTES:
            raise HTTPException(status_code=413, detail="图片超过大小限制")
        return Response(
            content=upstream.content,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except HTTPException:
        raise
    except requests.RequestException as exc:
        logger.warning("图片代理请求失败: %s", exc)
        raise HTTPException(status_code=502, detail="图片暂时无法获取") from exc


@app.get("/news")
async def get_news():
    """获取江农最新成就/新闻"""
    from mcp_news import fetch_jxau_news
    return {"news": fetch_jxau_news()}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
