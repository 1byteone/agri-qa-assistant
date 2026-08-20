from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(description="消息角色: user | assistant | system")
    content: str = Field(description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000, description="用户输入消息（1-4000 个字符）")
    thread_id: str = Field(min_length=1, max_length=128, description="会话标识符")
    user_id: Optional[str] = Field(default=None, max_length=128, description="用户ID（可选）")
    answer_mode: Literal["professional", "brief"] = Field(default="professional", description="回答模式：专业回答或简要回答")
    scenario_context: Optional[Dict[str, Any]] = Field(default=None, description="结构化农业场景上下文")

class ChatResponse(BaseModel):
    thread_id: str
    message: str
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="参考来源")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具调用记录")
    answer_mode: Literal["professional", "brief"] = Field(default="professional", description="实际采用的回答模式")
    completion_status: Literal["complete", "fallback", "error", "guarded"] = Field(default="complete", description="回答完成状态")
    timestamp: datetime = Field(default_factory=datetime.now)


class EvaluationAnnotationRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=128)
    gold_evidence_ids: List[str] = Field(min_length=1)
    retrieval_relevant: bool = True
    citation_covered: bool
    faithful: bool
    safety_ok: bool

class KnowledgeBaseStatus(BaseModel):
    total_documents: int
    collection_name: str
    last_updated: Optional[datetime] = None

class DependencyStatus(BaseModel):
    status: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    knowledge_base: KnowledgeBaseStatus
    llm_connected: bool
    dependencies: Dict[str, DependencyStatus] = Field(default_factory=dict)


# ── 案例管理 ─────────────────────────────────────────────────

class CaseCreateRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=128)
    user_id: Optional[str] = Field(default=None, max_length=128)
    topic_category: Optional[str] = Field(default=None, max_length=50)
    title: Optional[str] = Field(default=None, max_length=200)
    summary: Optional[str] = Field(default=None)


class FeedbackRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=128)
    thread_id: str = Field(min_length=1, max_length=128)
    message_id: Optional[str] = Field(default=None, max_length=128)
    feedback_type: Literal["helpful", "inaccurate", "needs_expert"]
    comment: Optional[str] = Field(default=None, max_length=2000)
