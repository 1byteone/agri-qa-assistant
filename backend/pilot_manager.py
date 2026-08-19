# -*- coding: utf-8 -*-
"""
小规模试用基础设施 — 为 10-20 名用户提供试用支持。

功能：
1. 试用用户管理
2. 试用会话跟踪
3. 使用数据收集
4. 反馈收集与分析
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, Boolean

from memory import Base, conversation_memory

logger = logging.getLogger(__name__)


# ── 数据模型 ─────────────────────────────────────────────────


class PilotUser(Base):
    """试用用户表。"""
    __tablename__ = "pilot_users"

    id: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(50))  # teacher/extension_worker/farmer
    organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PilotSession(Base):
    """试用会话表 — 跟踪每次试用的使用情况。"""
    __tablename__ = "pilot_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    thread_id: Mapped[str] = mapped_column(String(128), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5


class PilotFeedback(Base):
    """试用反馈表 — 收集详细的用户反馈。"""
    __tablename__ = "pilot_feedback"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50))  # survey/comment/bug/suggestion
    content: Mapped[str] = mapped_column(Text)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


# ── 管理器 ───────────────────────────────────────────────────


class PilotManager:
    """试用管理器。"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """确保数据库表已创建。"""
        if self._initialized:
            return
        await conversation_memory.initialize()
        async with conversation_memory.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def add_user(
        self,
        username: str,
        display_name: str,
        role: str,
        organization: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """添加试用用户。"""
        await self.initialize()
        user_id = f"pilot_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            user = PilotUser(
                id=user_id,
                username=username,
                display_name=display_name,
                role=role,
                organization=organization,
                phone=phone,
                email=email,
                created_at=now,
                last_active_at=now,
                is_active=True,
            )
            session.add(user)
            await session.commit()
        logger.info("试用用户已添加: %s (%s)", username, display_name)
        return {"id": user_id, "username": username, "role": role}

    async def start_session(self, user_id: str, thread_id: str) -> Dict[str, Any]:
        """开始试用会话。"""
        await self.initialize()
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            pilot_session = PilotSession(
                id=session_id,
                user_id=user_id,
                thread_id=thread_id,
                started_at=now,
                message_count=0,
            )
            session.add(pilot_session)
            # 更新用户最后活跃时间
            user = await session.get(PilotUser, user_id)
            if user:
                user.last_active_at = now
            await session.commit()
        return {"session_id": session_id, "thread_id": thread_id}

    async def end_session(
        self,
        session_id: str,
        message_count: int = 0,
        topics: Optional[List[str]] = None,
        satisfaction_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """结束试用会话。"""
        await self.initialize()
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            pilot_session = await session.get(PilotSession, session_id)
            if pilot_session:
                pilot_session.ended_at = now
                pilot_session.message_count = message_count
                pilot_session.topics = json.dumps(topics or [], ensure_ascii=False)
                pilot_session.satisfaction_score = satisfaction_score
                await session.commit()
        return {"session_id": session_id, "status": "ended"}

    async def submit_feedback(
        self,
        user_id: str,
        feedback_type: str,
        content: str,
        rating: Optional[int] = None,
        category: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """提交试用反馈。"""
        await self.initialize()
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            feedback = PilotFeedback(
                id=feedback_id,
                user_id=user_id,
                session_id=session_id,
                feedback_type=feedback_type,
                content=content,
                rating=rating,
                category=category,
                created_at=now,
                resolved=False,
            )
            session.add(feedback)
            await session.commit()
        return {"id": feedback_id, "status": "submitted"}

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户试用统计。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            # 会话数
            session_count = (await session.execute(
                select(func.count(PilotSession.id)).where(PilotSession.user_id == user_id)
            )).scalar() or 0
            # 消息总数
            total_messages = (await session.execute(
                select(func.sum(PilotSession.message_count)).where(PilotSession.user_id == user_id)
            )).scalar() or 0
            # 反馈数
            feedback_count = (await session.execute(
                select(func.count(PilotFeedback.id)).where(PilotFeedback.user_id == user_id)
            )).scalar() or 0
            # 平均满意度
            avg_satisfaction = (await session.execute(
                select(func.avg(PilotSession.satisfaction_score))
                .where(PilotSession.user_id == user_id)
                .where(PilotSession.satisfaction_score.is_not(None))
            )).scalar()
            return {
                "user_id": user_id,
                "session_count": session_count,
                "total_messages": total_messages,
                "feedback_count": feedback_count,
                "avg_satisfaction": round(float(avg_satisfaction), 2) if avg_satisfaction else None,
            }

    async def get_pilot_summary(self) -> Dict[str, Any]:
        """获取试点整体统计。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            # 总用户数
            total_users = (await session.execute(
                select(func.count(PilotUser.id)).where(PilotUser.is_active == True)
            )).scalar() or 0
            # 总会话数
            total_sessions = (await session.execute(
                select(func.count(PilotSession.id))
            )).scalar() or 0
            # 总消息数
            total_messages = (await session.execute(
                select(func.sum(PilotSession.message_count))
            )).scalar() or 0
            # 总反馈数
            total_feedback = (await session.execute(
                select(func.count(PilotFeedback.id))
            )).scalar() or 0
            # 平均满意度
            avg_satisfaction = (await session.execute(
                select(func.avg(PilotSession.satisfaction_score))
                .where(PilotSession.satisfaction_score.is_not(None))
            )).scalar()
            # 按角色统计
            role_stats = {}
            for role in ["teacher", "extension_worker", "farmer"]:
                count = (await session.execute(
                    select(func.count(PilotUser.id))
                    .where(PilotUser.role == role)
                    .where(PilotUser.is_active == True)
                )).scalar() or 0
                role_stats[role] = count
            return {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_feedback": total_feedback,
                "avg_satisfaction": round(float(avg_satisfaction), 2) if avg_satisfaction else None,
                "role_distribution": role_stats,
            }

    async def list_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """列出试用用户。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            filters = []
            if active_only:
                filters.append(PilotUser.is_active == True)
            query = select(PilotUser).order_by(PilotUser.created_at.desc())
            if filters:
                query = query.where(and_(*filters))
            result = await session.execute(query)
            users = result.scalars().all()
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "role": u.role,
                    "organization": u.organization,
                    "created_at": u.created_at.isoformat(),
                    "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
                }
                for u in users
            ]


# 全局实例
pilot_manager = PilotManager()
