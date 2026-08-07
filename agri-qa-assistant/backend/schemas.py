from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(description="消息角色: user | assistant | system")
    content: str = Field(description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str = Field(description="用户输入消息")
    thread_id: str = Field(description="会话标识符")
    user_id: Optional[str] = Field(default=None, description="用户ID（可选）")

class ChatResponse(BaseModel):
    thread_id: str
    message: str
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="参考来源")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具调用记录")
    timestamp: datetime = Field(default_factory=datetime.now)

class KnowledgeBaseStatus(BaseModel):
    total_documents: int
    collection_name: str
    last_updated: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    knowledge_base: KnowledgeBaseStatus
    llm_connected: bool