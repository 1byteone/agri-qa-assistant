# -*- coding: utf-8 -*-
"""
案例管理系统 — cases + case_events 表。

提供案例的创建、查询、事件追加、反馈收集功能。
案例生命周期：open → escalated → resolved
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer

from memory import Base, conversation_memory

logger = logging.getLogger(__name__)


# ── 数据模型 ─────────────────────────────────────────────────


class Case(Base):
    """案例表：记录一次需要跟踪的农业问答会话。"""
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    thread_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    topic_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CaseEvent(Base):
    """案例事件表：追加写入案例生命周期中的每个动作。"""
    __tablename__ = "case_events"

    id: Mapped[str] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── 常量 ─────────────────────────────────────────────────────

SEVERITY_LEVELS = {"normal", "elevated", "critical"}
STATUS_LEVELS = {"open", "escalated", "resolved"}

# 高风险关键词：触发自动升级
_ESCALATION_KEYWORDS = (
    r"农药|药剂|用药|剂量|安全间隔|肥料|施肥|追肥|石灰|有机肥|掺沙|"
    r"兽药|疫病|补贴|政策|登记|标准|规范|死亡|扩散|大面积|严重"
)


# ── CRUD 操作 ────────────────────────────────────────────────


class CaseManager:
    """案例管理器。"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """确保数据库表已创建。"""
        if self._initialized:
            return
        await conversation_memory.initialize()
        async with conversation_memory.async_session() as session:
            async with session.bind.connect() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await session.commit()
        self._initialized = True

    async def create_case(
        self,
        thread_id: str,
        user_id: Optional[str] = None,
        topic_category: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建新案例。"""
        await self.initialize()
        case_id = f"case_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            case = Case(
                id=case_id,
                user_id=user_id,
                thread_id=thread_id,
                status="open",
                severity="normal",
                topic_category=topic_category,
                title=title or "新案例",
                summary=summary,
                created_at=now,
                updated_at=now,
            )
            session.add(case)
            # 追加创建事件
            event = CaseEvent(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                case_id=case_id,
                event_type="case_created",
                payload=json.dumps({"thread_id": thread_id, "topic": topic_category}, ensure_ascii=False),
                actor=user_id or "system",
                created_at=now,
            )
            session.add(event)
            await session.commit()
        logger.info("案例已创建: %s (thread: %s)", case_id, thread_id)
        return {"id": case_id, "status": "open", "severity": "normal", "created_at": now.isoformat()}

    async def add_event(
        self,
        case_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        actor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """追加案例事件。"""
        await self.initialize()
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            event = CaseEvent(
                id=event_id,
                case_id=case_id,
                event_type=event_type,
                payload=json.dumps(payload or {}, ensure_ascii=False),
                actor=actor or "system",
                created_at=now,
            )
            session.add(event)
            # 更新案例的 updated_at
            case = await session.get(Case, case_id)
            if case:
                case.updated_at = now
            await session.commit()
        return {"id": event_id, "event_type": event_type, "created_at": now.isoformat()}

    async def submit_feedback(
        self,
        case_id: str,
        thread_id: str,
        message_id: Optional[str],
        feedback_type: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """提交用户反馈。

        feedback_type: helpful / inaccurate / needs_expert
        """
        if feedback_type not in ("helpful", "inaccurate", "needs_expert"):
            raise ValueError(f"无效的反馈类型: {feedback_type}")
        return await self.add_event(
            case_id=case_id,
            event_type="feedback",
            payload={
                "feedback_type": feedback_type,
                "thread_id": thread_id,
                "message_id": message_id,
                "comment": comment,
            },
            actor="user",
        )

    async def escalate_case(self, case_id: str, reason: str = "") -> Dict[str, Any]:
        """升级案例状态。"""
        await self.initialize()
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            case = await session.get(Case, case_id)
            if case and case.status != "escalated":
                case.status = "escalated"
                case.severity = "elevated"
                case.updated_at = now
                event = CaseEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    case_id=case_id,
                    event_type="escalated",
                    payload=json.dumps({"reason": reason}, ensure_ascii=False),
                    actor="system",
                    created_at=now,
                )
                session.add(event)
                await session.commit()
        return {"case_id": case_id, "status": "escalated"}

    async def resolve_case(self, case_id: str, resolution: str = "") -> Dict[str, Any]:
        """标记案例为已解决。"""
        await self.initialize()
        now = datetime.utcnow()
        async with conversation_memory.async_session() as session:
            case = await session.get(Case, case_id)
            if case and case.status != "resolved":
                case.status = "resolved"
                case.resolved_at = now
                case.updated_at = now
                event = CaseEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    case_id=case_id,
                    event_type="resolved",
                    payload=json.dumps({"resolution": resolution}, ensure_ascii=False),
                    actor="system",
                    created_at=now,
                )
                session.add(event)
                await session.commit()
        return {"case_id": case_id, "status": "resolved"}

    async def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取案例详情。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            case = await session.get(Case, case_id)
            if not case:
                return None
            return {
                "id": case.id,
                "user_id": case.user_id,
                "thread_id": case.thread_id,
                "status": case.status,
                "severity": case.severity,
                "topic_category": case.topic_category,
                "title": case.title,
                "summary": case.summary,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
                "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
            }

    async def get_case_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        """获取案例时间线（事件列表）。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            result = await session.execute(
                select(CaseEvent)
                .where(CaseEvent.case_id == case_id)
                .order_by(CaseEvent.created_at.asc())
            )
            events = result.scalars().all()
            return [
                {
                    "id": evt.id,
                    "event_type": evt.event_type,
                    "payload": json.loads(evt.payload) if evt.payload else {},
                    "actor": evt.actor,
                    "created_at": evt.created_at.isoformat(),
                }
                for evt in events
            ]

    async def list_cases(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """列出案例。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            filters = []
            if status:
                filters.append(Case.status == status)
            if user_id:
                filters.append(Case.user_id == user_id)
            query = select(Case).order_by(Case.updated_at.desc()).limit(limit)
            if filters:
                query = query.where(and_(*filters))
            result = await session.execute(query)
            cases = result.scalars().all()
            return [
                {
                    "id": c.id,
                    "thread_id": c.thread_id,
                    "status": c.status,
                    "severity": c.severity,
                    "topic_category": c.topic_category,
                    "title": c.title,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in cases
            ]

    async def get_feedback_summary(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """获取反馈聚合统计。"""
        await self.initialize()
        async with conversation_memory.async_session() as session:
            filters = [CaseEvent.event_type == "feedback"]
            if case_id:
                filters.append(CaseEvent.case_id == case_id)
            result = await session.execute(
                select(CaseEvent).where(and_(*filters))
            )
            events = result.scalars().all()
            counts = {"helpful": 0, "inaccurate": 0, "needs_expert": 0}
            for evt in events:
                payload = json.loads(evt.payload) if evt.payload else {}
                ft = payload.get("feedback_type", "")
                if ft in counts:
                    counts[ft] += 1
            total = sum(counts.values())
            return {
                "total": total,
                "breakdown": counts,
                "helpful_rate": round(counts["helpful"] / max(total, 1), 3),
                "needs_expert_rate": round(counts["needs_expert"] / max(total, 1), 3),
            }

    def should_auto_escalate(self, message: str, citations: Optional[List[Dict]] = None) -> bool:
        """判断是否需要自动升级（高风险回答无 A 级证据）。"""
        import re
        has_high_risk = bool(re.search(_ESCALATION_KEYWORDS, message or "", re.IGNORECASE))
        if not has_high_risk:
            return False
        if citations:
            has_official = any(c.get("eligible") and c.get("evidence_level") == "A" for c in citations)
            return not has_official
        return True


# 全局实例
case_manager = CaseManager()
