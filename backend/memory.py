import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math
import re
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Float, func, select, and_, or_

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


class ConversationThread(Base):
    """Thread metadata keeps conversation list queries cheap and stable."""
    __tablename__ = "conversation_threads"

    thread_id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), default="新对话")
    last_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AgentMemory(Base):
    """Structured memory kept separate from RAG evidence and raw messages."""
    __tablename__ = "agent_memories"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    scope: Mapped[str] = mapped_column(String(20), default="task")
    memory_type: Mapped[str] = mapped_column(String(30), default="fact")
    content: Mapped[str] = mapped_column(Text)
    normalized_key: Mapped[str] = mapped_column(String(240), index=True)
    source_thread_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.65)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    authority_score: Mapped[float] = mapped_column(Float, default=0.5)
    event_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    temporal_label: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    source_kind: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    extraction_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    verification_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)


_TOKEN_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]{2,}")
_AGRI_FACT_PATTERNS = (
    ("crop", r"(?:种植|栽培|田里|地里|种了|作物是)\s*([\u4e00-\u9fffA-Za-z]{2,10})"),
    ("region", r"(?:在|位于|地区|地点|江西)\s*([\u4e00-\u9fff]{2,12})(?:地区|县|市|乡|村)?"),
    ("growth_stage", r"([\u4e00-\u9fff]{2,12}(?:期|阶段))"),
)

_TEMPORAL_PATTERNS = (
    ("today", re.compile(r"今天|目前|现在")),
    ("recent", re.compile(r"最近|近几天|这几天|本周")),
    ("last_week", re.compile(r"上周|上星期")),
    ("last_month", re.compile(r"上月|上个月")),
    ("last_year", re.compile(r"去年|上年度")),
    ("historical", re.compile(r"曾经|以前|历史上|多年前")),
)


def resolve_temporal_reference(text: str, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Resolve common Chinese time references without pretending to know an exact date."""
    current = now or datetime.utcnow()
    value = (text or "").strip()
    for label, pattern in _TEMPORAL_PATTERNS:
        if pattern.search(value):
            offsets = {"today": 0, "recent": 2, "last_week": 7, "last_month": 30, "last_year": 365, "historical": 730}
            return {"event_at": current - timedelta(days=offsets[label]), "temporal_label": label}
    year = re.search(r"(20\d{2})年", value)
    if year:
        try:
            return {"event_at": current.replace(year=int(year.group(1)), month=6, day=30), "temporal_label": "calendar_year"}
        except ValueError:
            pass
    return {"event_at": current, "temporal_label": "unspecified"}


def normalize_memory_key(content: str) -> str:
    """Normalize a memory for deterministic deduplication."""
    value = re.sub(r"\s+", "", (content or "").strip().lower())
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", value)[:240]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def extract_candidate_memories(message: str, thread_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extract explicit, low-risk task facts; never infer a long-term preference."""
    text = re.sub(r"\s+", " ", (message or "").strip())
    if not text:
        return []
    candidates: List[Dict[str, Any]] = []
    temporal = resolve_temporal_reference(text)
    for memory_type, pattern in _AGRI_FACT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1).strip(" ，。,.：:")
            if len(value) < 2:
                continue
            content = f"当前任务{memory_type}：{value}"
            candidates.append({
                "scope": "task", "memory_type": memory_type, "content": content,
                "normalized_key": normalize_memory_key(content), "thread_id": thread_id,
                "user_id": user_id, "confidence": 0.82, "importance": 0.75,
                "expires_at": datetime.utcnow() + timedelta(days=14),
                "authority_score": 0.55, "event_at": temporal["event_at"], "temporal_label": temporal["temporal_label"],
                "source_kind": "user_statement",
                "extraction_mode": "passive", "verification_status": "pending",
            })
    # Constraints/goals are stored only when explicitly stated by the user.
    for label, pattern in (("constraint", r"(?:不要|避免|尽量|不能|限制)([^，。；;]{2,40})"),
                           ("goal", r"(?:目标是|想要|希望|需要)([^，。；;]{2,40})")):
        for match in re.finditer(pattern, text):
            value = match.group(1).strip()
            content = f"当前任务{label}：{value}"
            candidates.append({
                "scope": "task", "memory_type": label, "content": content,
                "normalized_key": normalize_memory_key(content), "thread_id": thread_id,
                "user_id": user_id, "confidence": 0.9, "importance": 0.9,
                "expires_at": datetime.utcnow() + timedelta(days=14),
                "authority_score": 0.65, "event_at": temporal["event_at"], "temporal_label": temporal["temporal_label"],
                "source_kind": "user_statement",
                "extraction_mode": "passive", "verification_status": "pending",
            })
    return candidates[:8]


def propose_active_memory_questions(message: str, candidates: List[Dict[str, Any]]) -> List[str]:
    """Ask for only decision-critical facts; do not turn every turn into an interview."""
    text = (message or "").strip()
    if not text or not re.search(r"怎么|如何|防治|用药|施肥|播种|移栽|适合|判断|诊断", text):
        return []
    candidate_types = {item.get("memory_type") for item in candidates}
    questions: List[str] = []
    # The missing facts depend on the task. A seed-treatment question should
    # not be presented with a disease-diagnosis intake form.
    if re.search(r"种子|浸种|催芽|晒种|包衣|播种前", text):
        if not re.search(r"品种|品系|杂交|常规稻", text):
            questions.append("请补充水稻品种（或杂交/常规稻）及计划播种日期，便于确定处理窗口。")
        if not re.search(r"包衣|霉变|发芽率|种子状态|种源|批次", text):
            questions.append("请说明种子是否已包衣、是否有霉变，以及预计发芽率或种子批次。")
        return questions[:2]
    if re.search(r"土壤|红壤|酸性|盐碱|黏重|沙质|改良|ph", text.lower()):
        if not re.search(r"pH|酸碱|有机质|速效氮|速效磷|速效钾|盐分|质地", text, re.IGNORECASE):
            questions.append("请补充土壤 pH、质地和有机质/速效氮磷钾检测结果。")
        if not re.search(r"作物|水稻|小麦|玉米|油菜|果树|蔬菜", text):
            questions.append("请补充目标作物和当前生育期，以便匹配改良窗口。")
        return questions[:2]
    if re.search(r"施肥|灌溉|水肥|追肥|底肥", text):
        if not re.search(r"目标产量|产量", text):
            questions.append("请补充目标作物、生育期和目标产量。")
        if not re.search(r"测土|pH|氮|磷|钾|养分", text, re.IGNORECASE):
            questions.append("请补充测土结果或近期施肥、灌溉记录。")
        return questions[:2]
    if "region" not in candidate_types and not re.search(r"江西|南昌|赣州|九江|上饶|吉安|宜春|景德镇|萍乡|新余|鹰潭|抚州", text):
        questions.append("请补充地块所在地区（县/市即可），同一作物在江西不同区域的农时和病虫害窗口可能不同。")
    if "growth_stage" not in candidate_types and not re.search(r"分蘖|拔节|孕穗|抽穗|灌浆|返青|苗期|开花|结果|成熟|生育期", text):
        questions.append("请补充当前生育期或播种/移栽日期，便于判断措施窗口。")
    if re.search(r"病|虫|黄化|斑|枯|卷叶|症状|诊断", text) and not re.search(r"症状|叶片|茎秆|果实|扩散|照片|面积", text):
        questions.append("如涉及诊断，请补充症状部位、出现时间和影响范围；必要时上传现场照片。")
    return questions[:2]


def score_memory_relevance(memory: Dict[str, Any], query: str, task_context: Optional[Dict[str, Any]] = None) -> float:
    """Score task relevance; lexical similarity is only one weak signal."""
    if memory.get("scope") == "user" and memory.get("verification_status") not in {None, "confirmed"}:
        return 0.0
    query_tokens = _tokens(query)
    memory_tokens = _tokens(memory.get("content", ""))
    overlap = len(query_tokens & memory_tokens) / max(1, len(query_tokens))
    score = 0.36 * overlap
    type_weight = {"constraint": 1.0, "goal": 0.95, "crop": 0.88, "region": 0.82, "growth_stage": 0.78, "summary": 0.7, "preference": 0.45}.get(memory.get("memory_type"), 0.55)
    scope_weight = {"task": 0.28, "thread": 0.2, "user": 0.08}.get(memory.get("scope"), 0.05)
    score += scope_weight * type_weight
    score += 0.12 * float(memory.get("confidence") or 0.5)
    score += 0.08 * float(memory.get("importance") or 0.5)
    score += 0.10 * float(memory.get("authority_score") or 0.5)
    created_at = memory.get("created_at") or memory.get("event_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            created_at = None
    if isinstance(created_at, datetime):
        age_days = max(0.0, (datetime.utcnow() - created_at).total_seconds() / 86400)
        score += 0.08 * math.exp(-age_days / 45)
    expires_at = memory.get("expires_at")
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            expires_at = None
    if isinstance(expires_at, datetime) and expires_at < datetime.utcnow():
        return 0.0
    if task_context:
        current_goal = str(task_context.get("goal", ""))
        if current_goal and current_goal in memory.get("content", ""):
            score += 0.25
    return min(1.0, round(score, 4))


def select_relevant_memories(memories: List[Dict[str, Any]], query: str, max_items: int = 6) -> Dict[str, List[Dict[str, Any]]]:
    """Return used/skipped memories with deduplication and an explainable score."""
    active = [item for item in memories if item.get("status", "active") == "active"]
    ranked = []
    seen = set()
    for item in active:
        key = item.get("normalized_key") or normalize_memory_key(item.get("content", ""))
        if key in seen:
            continue
        seen.add(key)
        scored = dict(item)
        scored["relevance"] = score_memory_relevance(scored, query)
        ranked.append(scored)
    ranked.sort(key=lambda item: item["relevance"], reverse=True)
    used = [item for item in ranked if item["relevance"] >= 0.32][:max_items]
    used_ids = {item.get("id") for item in used}
    skipped = [item for item in ranked if item.get("id") not in used_ids][:max_items]
    return {"used": used, "skipped": skipped}


class ConversationMemory:
    """持久化对话记忆管理"""

    def __init__(self):
        self.engine = create_async_engine(settings.sqlite_db_url, echo=settings.debug)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self._initialized = False

    async def initialize(self):
        """初始化数据库表"""
        if self._initialized:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # SQLite installations created before structured memory existed do
            # not need a migration for new tables, but may miss newly added
            # nullable/default columns. Add them idempotently when possible.
            if self.engine.url.get_backend_name() == "sqlite":
                from sqlalchemy import inspect
                # 读取模型声明的所有 agent_memories 列
                declared = {c.name: c for c in AgentMemory.__table__.columns}
                columns = (await conn.exec_driver_sql("PRAGMA table_info(agent_memories)")).all()
                existing = {row[1] for row in columns}
                missing = {name: col for name, col in declared.items() if name not in existing}
                for name, col in missing.items():
                    col_type = col.type.compile(dialect=self.engine.dialect)
                    default = ""
                    if col.default is not None:
                        default = f" DEFAULT {col.default.arg!r}" if not isinstance(col.default.arg, str) else f" DEFAULT '{col.default.arg}'"
                    await conn.exec_driver_sql(f"ALTER TABLE agent_memories ADD COLUMN {name} {col_type}{default}")
        await self._backfill_threads()
        self._initialized = True
        logger.info("对话记忆数据库初始化完成")

    async def _backfill_threads(self):
        """Create metadata rows for conversations written before this table existed."""
        async with self.async_session() as session:
            existing = set((await session.execute(select(ConversationThread.thread_id))).scalars().all())
            messages = (await session.execute(
                select(ConversationMessage).order_by(ConversationMessage.thread_id, ConversationMessage.created_at)
            )).scalars().all()
            threads: Dict[str, ConversationThread] = {}
            for message in messages:
                if message.thread_id in existing:
                    continue
                thread = threads.get(message.thread_id)
                if thread is None:
                    thread = ConversationThread(
                        thread_id=message.thread_id,
                        title=self._title_from_content(message.content) if message.role == "user" else "新对话",
                        last_message=message.content,
                        created_at=message.created_at,
                        updated_at=message.created_at,
                    )
                    threads[message.thread_id] = thread
                    session.add(thread)
                else:
                    if thread.title == "新对话" and message.role == "user":
                        thread.title = self._title_from_content(message.content)
                    thread.last_message = message.content
                    thread.updated_at = message.created_at
            if threads:
                await session.commit()

    @staticmethod
    def _title_from_content(content: str) -> str:
        compact = " ".join(content.strip().split())
        return compact[:36] or "新对话"

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
            thread = await session.get(ConversationThread, thread_id)
            now = datetime.utcnow()
            if thread is None:
                thread = ConversationThread(
                    thread_id=thread_id,
                    title=self._title_from_content(content) if role == "user" else "新对话",
                    created_at=now,
                    updated_at=now,
                )
                session.add(thread)
            elif thread.title == "新对话" and role == "user":
                thread.title = self._title_from_content(content)
            thread.last_message = content
            thread.updated_at = now
            session.add(msg)
            await session.commit()

    async def upsert_memory(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or refresh a structured memory item, keeping the newest fact."""
        await self.initialize()
        key = item.get("normalized_key") or normalize_memory_key(item.get("content", ""))
        async with self.async_session() as session:
            # A task has one current crop/region/stage. New explicit facts
            # supersede older values instead of silently merging conflicts.
            if item.get("scope") == "task" and item.get("memory_type") in {"crop", "region", "growth_stage"}:
                prior = (await session.execute(select(AgentMemory).where(and_(
                    AgentMemory.thread_id == item.get("thread_id"),
                    AgentMemory.scope == "task",
                    AgentMemory.memory_type == item.get("memory_type"),
                    AgentMemory.status == "active",
                )))).scalars().all()
                for row in prior:
                    if row.normalized_key != key:
                        row.status = "archived"
            result = await session.execute(select(AgentMemory).where(
                and_(AgentMemory.normalized_key == key, AgentMemory.status == "active",
                     or_(AgentMemory.user_id == item.get("user_id"), AgentMemory.thread_id == item.get("thread_id")))
            ))
            existing = result.scalars().first()
            if existing:
                existing.content = item.get("content", existing.content)
                existing.confidence = max(existing.confidence, float(item.get("confidence", existing.confidence)))
                existing.importance = max(existing.importance, float(item.get("importance", existing.importance)))
                existing.authority_score = max(existing.authority_score or 0.5, float(item.get("authority_score", existing.authority_score or 0.5)))
                existing.event_at = item.get("event_at", existing.event_at)
                existing.temporal_label = item.get("temporal_label", existing.temporal_label)
                existing.source_kind = item.get("source_kind", existing.source_kind)
                existing.extraction_mode = item.get("extraction_mode", existing.extraction_mode)
                existing.verification_status = item.get("verification_status", existing.verification_status)
                existing.expires_at = item.get("expires_at", existing.expires_at)
                await session.commit()
                return self._memory_dict(existing)
            memory = AgentMemory(id=str(uuid.uuid4()), normalized_key=key, **{
                field: item[field] for field in ("user_id", "thread_id", "scope", "memory_type", "content",
                                                 "source_thread_id", "source_message_id", "confidence", "importance",
                                                 "authority_score", "event_at", "temporal_label", "source_kind", "extraction_mode", "verification_status", "expires_at")
                if field in item
            })
            session.add(memory)
            await session.commit()
            return self._memory_dict(memory)

    @staticmethod
    def _memory_dict(memory: AgentMemory) -> Dict[str, Any]:
        return {
            "id": memory.id, "user_id": memory.user_id, "thread_id": memory.thread_id,
            "scope": memory.scope, "memory_type": memory.memory_type, "content": memory.content,
            "normalized_key": memory.normalized_key, "source_thread_id": memory.source_thread_id,
            "source_message_id": memory.source_message_id, "confidence": memory.confidence,
            "importance": memory.importance, "authority_score": memory.authority_score,
            "event_at": memory.event_at.isoformat() if memory.event_at else None,
            "temporal_label": memory.temporal_label, "source_kind": memory.source_kind,
            "extraction_mode": memory.extraction_mode, "verification_status": memory.verification_status,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "last_used_at": memory.last_used_at.isoformat() if memory.last_used_at else None,
            "expires_at": memory.expires_at.isoformat() if memory.expires_at else None, "status": memory.status,
        }

    async def list_memories(self, thread_id: Optional[str] = None, user_id: Optional[str] = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        await self.initialize()
        async with self.async_session() as session:
            conditions = []
            if thread_id and user_id:
                conditions.append(or_(AgentMemory.thread_id == thread_id, and_(AgentMemory.scope == "user", AgentMemory.user_id == user_id)))
            elif thread_id:
                conditions.append(AgentMemory.thread_id == thread_id)
            elif user_id:
                conditions.append(and_(AgentMemory.scope == "user", AgentMemory.user_id == user_id))
            if not include_archived:
                conditions.append(AgentMemory.status == "active")
            query = select(AgentMemory).where(and_(*conditions)).order_by(AgentMemory.created_at.desc()) if conditions else select(AgentMemory).order_by(AgentMemory.created_at.desc())
            rows = (await session.execute(query.limit(100))).scalars().all()
            return [self._memory_dict(row) for row in rows]

    async def delete_memory(self, memory_id: str) -> bool:
        await self.initialize()
        async with self.async_session() as session:
            row = await session.get(AgentMemory, memory_id)
            if not row:
                return False
            row.status = "deleted"
            await session.commit()
            return True

    async def confirm_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        await self.initialize()
        async with self.async_session() as session:
            row = await session.get(AgentMemory, memory_id)
            if not row:
                return None
            row.scope = "user"
            row.confidence = max(row.confidence, 0.95)
            row.importance = max(row.importance, 0.8)
            row.verification_status = "confirmed"
            row.extraction_mode = "active"
            row.expires_at = None
            await session.commit()
            return self._memory_dict(row)

    async def archive_stale_memories(self) -> int:
        await self.initialize()
        async with self.async_session() as session:
            rows = (await session.execute(select(AgentMemory).where(
                and_(AgentMemory.status == "active", AgentMemory.expires_at.is_not(None), AgentMemory.expires_at < datetime.utcnow())
            ))).scalars().all()
            for row in rows:
                row.status = "archived"
            await session.commit()
            return len(rows)

    async def relevant_memories(self, query: str, thread_id: str, user_id: Optional[str] = None, max_items: int = 6) -> Dict[str, List[Dict[str, Any]]]:
        memories = await self.list_memories(thread_id=thread_id, user_id=user_id)
        selection = select_relevant_memories(memories, query, max_items=max_items)
        used_ids = [item.get("id") for item in selection.get("used", []) if item.get("id")]
        if used_ids:
            async with self.async_session() as session:
                rows = (await session.execute(select(AgentMemory).where(AgentMemory.id.in_(used_ids)))).scalars().all()
                now = datetime.utcnow()
                for row in rows:
                    row.last_used_at = now
                await session.commit()
        return selection

    async def summarize_thread(self, thread_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Produce a deterministic memory ledger summary for UI/admin use."""
        memories = await self.list_memories(thread_id=thread_id, user_id=user_id, include_archived=True)
        active = [item for item in memories if item.get("status") == "active"]
        by_type: Dict[str, int] = {}
        for item in active:
            by_type[item.get("memory_type", "fact")] = by_type.get(item.get("memory_type", "fact"), 0) + 1
        return {"thread_id": thread_id, "active_count": len(active), "total_count": len(memories), "by_type": by_type, "memories": active[:20]}

    async def organize_if_needed(self, thread_id: str, user_id: Optional[str] = None, threshold: int = 12) -> Dict[str, Any]:
        """Use a threshold trigger so every message does not rewrite memory."""
        memories = await self.list_memories(thread_id=thread_id, user_id=user_id, include_archived=False)
        conflict_types = {"crop": {}, "region": {}, "growth_stage": {}}
        conflicts = []
        for item in memories:
            memory_type = item.get("memory_type")
            if memory_type in conflict_types:
                key = item.get("normalized_key")
                conflict_types[memory_type][key] = item
        for memory_type, values in conflict_types.items():
            if len(values) > 1:
                conflicts.append({"memory_type": memory_type, "ids": [item.get("id") for item in values.values()]})
        should_organize = len(memories) >= threshold or bool(conflicts)
        archived = await self.archive_stale_memories() if should_organize else 0
        summary = await self.summarize_thread(thread_id, user_id) if should_organize else None
        return {"triggered": should_organize, "reason": "count_or_conflict" if should_organize else "below_threshold", "archived": archived, "conflicts": conflicts, "summary": summary}

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
            thread = await session.get(ConversationThread, thread_id)
            if thread:
                await session.delete(thread)
            await session.commit()

    async def list_threads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return session-list data without loading each conversation body."""
        await self.initialize()
        async with self.async_session() as session:
            counts = dict((await session.execute(
                select(ConversationMessage.thread_id, func.count(ConversationMessage.id)).group_by(ConversationMessage.thread_id)
            )).all())
            threads = (await session.execute(
                select(ConversationThread).order_by(ConversationThread.updated_at.desc()).limit(limit)
            )).scalars().all()
            return [
                {
                    "thread_id": thread.thread_id,
                    "title": thread.title,
                    "last_message": thread.last_message,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "message_count": counts.get(thread.thread_id, 0),
                }
                for thread in threads
            ]

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
