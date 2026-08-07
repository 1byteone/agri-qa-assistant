import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, select

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class ConversationMessage(Base):
    """对话消息表"""
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ConversationMemory:
    """持久化对话记忆管理"""

    def __init__(self):
        self.engine = create_async_engine(settings.sqlite_db_url, echo=settings.debug)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)
        self._initialized = False

    async def initialize(self):
        """初始化数据库表"""
        if self._initialized:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True
        logger.info("对话记忆数据库初始化完成")

    async def add_message(self, thread_id: str, role: str, content: str, extra: Optional[Dict] = None):
        """添加消息"""
        await self.initialize()
        import uuid
        msg = ConversationMessage(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            role=role,
            content=content,
            extra=json.dumps(extra, ensure_ascii=False) if extra else None,
        )
        async with self.async_session() as session:
            session.add(msg)
            await session.commit()

    async def get_history(self, thread_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取对话历史"""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(ConversationMessage)
                .where(ConversationMessage.thread_id == thread_id)
                .order_by(ConversationMessage.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "extra": json.loads(msg.extra) if msg.extra else None,
                }
                for msg in reversed(messages)
            ]

    async def clear_thread(self, thread_id: str):
        """清空指定会话"""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(ConversationMessage).where(ConversationMessage.thread_id == thread_id)
            )
            messages = result.scalars().all()
            for msg in messages:
                await session.delete(msg)
            await session.commit()

    async def get_thread_stats(self) -> Dict[str, int]:
        """获取会话统计"""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(ConversationMessage.thread_id, ConversationMessage.id)
                .group_by(ConversationMessage.thread_id)
            )
            threads = result.all()
            return {"total_threads": len(threads)}


# 全局记忆实例
conversation_memory = ConversationMemory()