import os
import logging
from typing import Dict, Any, List, Optional, Sequence

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from config import settings
from knowledge_base import knowledge_base
from memory import conversation_memory
from tools import get_all_tools

logger = logging.getLogger(__name__)


# ==================== 系统提示词 ====================

AGRICULTURE_SYSTEM_PROMPT = """\
你是 AgriQA Assistant，一个专业的农业智能问答助手。你的知识涵盖作物种植、病虫害防治、施肥灌溉、土壤管理、农机具使用等农业领域。

## 核心职责
1. **优先查询私有知识库**：对于农业技术问题，首先检索私有知识库，确保答案专业可靠
2. **多轮对话记忆**：记住用户提到的作物类型、地理位置、种植历史等上下文
3. **引导式兜底**：如果知识库中没有相关信息，诚实告知用户，并提供一般性解答建议
4. **结构化输出**：回答简洁明了，使用列表、分点等便于阅读的格式

## 行为准则
- 严格基于知识库内容回答，不编造数据
- 涉及农药、化肥时，提醒用户按说明书使用
- 对于严重病虫害，建议咨询当地农技站
- 时间相关提问使用 get_current_datetime 工具
- 作物生育期问题使用 calculate_growing_period 工具
- 不确定的知识明确告知"知识库中暂无此信息"

## 输出格式
- 使用清晰的分点说明
- 关键信息使用加粗标记
- 必要时提供操作步骤
- 回答长度适中，避免过长
"""


# ==================== Agent 工厂 ====================

class AgricultureAgent:
    """农业智能问答 Agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.agnes_base_url,
            openai_api_key=settings.agnes_api_key,
            model=settings.agnes_chat_model,
            temperature=0.1,
        )
        self.tools = get_all_tools()
        self._agent = None
        self._checkpointer = InMemorySaver()
        self._store = InMemoryStore()

    def _build_agent(self):
        """构建 LangGraph Agent"""
        if self._agent is not None:
            return self._agent

        prompt = ChatPromptTemplate.from_messages([
            ("system", AGRICULTURE_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])

        self._agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=AGRICULTURE_SYSTEM_PROMPT,
            checkpointer=self._checkpointer,
            store=self._store,
        )
        return self._agent

    async def chat(self, message: str, thread_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """多轮对话接口"""
        agent = self._build_agent()
        
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id or "anonymous",
            }
        }

        # 调用 Agent
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
        )

        # 提取结果
        messages = result.get("messages", [])
        last_ai_message = None
        for msg in reversed(messages):
            if hasattr(msg, "role") and msg.role == "assistant":
                last_ai_message = msg
                break

        response_content = last_ai_message.content if last_ai_message else "抱歉，我现在无法回答这个问题。"

        # 提取工具调用记录
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "name": tc.get("name", "unknown"),
                        "args": tc.get("args", {}),
                    })

        # 持久化对话历史
        await conversation_memory.add_message(thread_id, "user", message)
        await conversation_memory.add_message(thread_id, "assistant", response_content)

        return {
            "message": response_content,
            "tool_calls": tool_calls,
            "thread_id": thread_id,
        }

    async def get_history(self, thread_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return await conversation_memory.get_history(thread_id, limit)

    async def clear_history(self, thread_id: str):
        """清空对话历史"""
        await conversation_memory.clear_thread(thread_id)


# 全局 Agent 实例
agri_agent = AgricultureAgent()