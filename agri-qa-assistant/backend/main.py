import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import settings
from schemas import ChatRequest, ChatResponse, HealthResponse, KnowledgeBaseStatus
from agent import agri_agent
from knowledge_base import knowledge_base, init_default_knowledge_base
from memory import conversation_memory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化 AgriQA Assistant...")
    await conversation_memory.initialize()
    init_default_knowledge_base()
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
        )
        return ChatResponse(
            thread_id=result["thread_id"],
            message=result["message"],
            tool_calls=result.get("tool_calls"),
        )
    except Exception as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{thread_id}")
async def get_history(thread_id: str, limit: int = 20):
    """获取对话历史"""
    try:
        history = await agri_agent.get_history(thread_id, limit)
        return {"thread_id": thread_id, "history": history}
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
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


@app.get("/knowledge-base/status")
async def knowledge_base_status():
    """知识库状态"""
    return knowledge_base.get_status()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )