# -*- coding: utf-8 -*-
"""
AgricultureAgent — 农业智能问答 Agent。
使用 prompts.py 提供系统提示词，answer_formatter.py 提供答案后处理。
"""
from __future__ import annotations
import os
import logging
import asyncio
import json
import re
from typing import AsyncIterator, Dict, List, Optional, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from config import settings
from tools import get_all_tools
from memory import conversation_memory, extract_candidate_memories, propose_active_memory_questions
from knowledge_base import knowledge_base
from domain_guard import build_domain_rejection, classify_query
from agriir_pipeline import agriir_pipeline

# 从提取的模块导入
from prompts import (
    AGRICULTURE_SYSTEM_PROMPT,
    ANSWER_MODES,
    ANSWER_MODE_PROMPTS,
    normalize_answer_mode,
    extract_explicit_date,
    extract_date_literal,
    needs_time_preflight,
)
from answer_formatter import (
    extract_text_tool_queries,
    requests_related_resources,
    clean_tool_markers,
    extract_decision_card,
    strip_evidence_process,
    compact_answer,
    enforce_evidence_policy,
    build_evidence_gap_answer,
    EVIDENCE_SCOPE_LABELS,
)

logger = logging.getLogger(__name__)

# 预载所有工具并建立名称索引
_ALL_TOOLS = get_all_tools()
_TOOL_MAP = {t.name: t for t in _ALL_TOOLS if hasattr(t, "name")}


def _safe_tool_args(args: Any) -> Dict[str, Any]:
    if not isinstance(args, dict):
        return {}
    safe: Dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[str(key)] = str(value)[:300] if isinstance(value, str) else value
        else:
            safe[str(key)] = str(value)[:300]
    return safe


def _run_tool_audited(name: str, args: Any) -> Dict[str, Any]:
    """Invoke a tool and return a stable audit record for SSE and API clients."""
    import time
    started = time.perf_counter()
    safe_args = _safe_tool_args(args)
    tool = _TOOL_MAP.get(name)
    if not tool:
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": False, "error_code": "TOOL_NOT_FOUND", "duration_ms": 0, "result": f"[工具 {name} 不存在]"}
    try:
        result = tool.invoke(args if isinstance(args, dict) else {})
        result_text = str(result) if result else ""
        ok = True
        error_code = None
        try:
            parsed = json.loads(result_text)
            if isinstance(parsed, dict) and parsed.get("ok") is False:
                ok = False
                error_code = parsed.get("error_code") or "TOOL_REPORTED_ERROR"
        except (TypeError, ValueError):
            if result_text.startswith("[") and "失败" in result_text:
                ok = False
                error_code = "TOOL_EXECUTION_ERROR"
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": ok, "error_code": error_code, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "result": result_text}
    except Exception as exc:
        logger.warning("工具 %s 执行失败: %s", name, exc)
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": False, "error_code": "TOOL_EXECUTION_ERROR", "duration_ms": round((time.perf_counter() - started) * 1000, 2), "result": f"[工具 {name} 执行失败]"}


def _chunk_text(content: Any) -> str:
    """Normalise provider-specific streamed content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


# 旧函数别名，保持 stream_chat 内部调用兼容
_extract_text_tool_queries = extract_text_tool_queries
_requests_related_resources = requests_related_resources
_clean_tool_markers = clean_tool_markers
_extract_decision_card = extract_decision_card
_strip_evidence_process = strip_evidence_process
_compact_answer = compact_answer
_enforce_evidence_policy = enforce_evidence_policy
_build_evidence_gap_answer = build_evidence_gap_answer
_normalize_answer_mode = normalize_answer_mode
_extract_explicit_date = extract_explicit_date
_extract_date_literal = extract_date_literal
_needs_time_preflight = needs_time_preflight


# 从多智能体模块导入（用于安全和分析检查）
try:
    from multiagent_orchestrator import Orchestrator as _MultiAgentOrchestrator
    _HAS_MULTIAGENT = True
except ImportError:
    _HAS_MULTIAGENT = False

# _enforce_evidence_policy 需要注入 agriir_pipeline 引用
def _enforce_evidence_policy_with_pipeline(answer: str, question: str, citations: List[Dict[str, Any]]) -> str:
    return enforce_evidence_policy(answer, question, citations, requires_official_evidence_fn=agriir_pipeline.requires_official_evidence)


class AgricultureAgent:
    """农业智能问答 Agent（修复版）"""

    def __init__(self):
        proxy = (os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
                 os.environ.get("https_proxy") or os.environ.get("http_proxy") or "")

        print("[DEBUG] agnes_base_url :", settings.agnes_base_url)
        print("[DEBUG] agnes_chat_model:", settings.agnes_chat_model)
        print("[DEBUG] tools registered:", list(_TOOL_MAP.keys()))
        print("[DEBUG] proxy:", proxy)

        self.llm = ChatOpenAI(
            base_url=settings.agnes_base_url,
            openai_api_key=settings.agnes_api_key,
            model=settings.agnes_chat_model,
            temperature=0.3,
            openai_proxy=proxy or None,
        ).bind_tools(_ALL_TOOLS)

        # 内存会话历史（仅本进程有效，限制每条 thread 防内存泄漏）
        self._hist: Dict[str, List] = {}
        self._hist_max_per_thread = 100

    async def stream_chat(self, message: str, thread_id: str, user_id=None, answer_mode: str = "professional", scenario_context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """Yield a transport-neutral event stream while preserving the existing tool loop."""
        answer_mode = _normalize_answer_mode(answer_mode)
        # Domain policy is deliberately before status events, retrieval, memory,
        # tools, and the model. This prevents out-of-scope prompts from reaching
        # any expensive or general-purpose capability.
        decision = classify_query(message)
        if not decision["allowed"]:
            rejection = build_domain_rejection(decision)
            yield {
                "type": "guard",
                "guarded": True,
                "category": decision["category"],
                "reason": decision["reason"],
                "scope": "农业知识、农业生产决策、农时、农业气象、农业政策及农业资料",
                "recommendations": ["水稻稻飞虱怎么防治？", "小麦返青期如何追肥？", "江西早稻什么时候播种？"],
            }
            yield {"type": "delta", "text": rejection}
            yield {
                "type": "done",
                "thread_id": thread_id,
                "message": rejection,
                "tool_calls": [],
                "guarded": True,
                "guard_reason": decision["reason"],
                "completion_status": "guarded",
            }
            return

        yield {"type": "mode", "mode": answer_mode}
        yield {"type": "status", "message": "正在匹配农业知识库"}
        tool_calls_out: List[Dict[str, Any]] = []
        time_context: Optional[Dict[str, Any]] = None
        # Deterministic temporal preflight prevents the model from silently
        # using a stale training date or treating a user example date as now.
        if _needs_time_preflight(message):
            reference_date = _extract_explicit_date(message)
            date_literal = _extract_date_literal(message)
            time_args = {"timezone": settings.app_timezone}
            if date_literal:
                # Preserve invalid user dates as input so the tool can return
                # INVALID_REFERENCE_DATE instead of silently using server now.
                time_args["reference_date"] = reference_date or date_literal
            yield {"type": "tool", "name": "get_current_datetime", "status": "running", "args": _safe_tool_args(time_args), "source": "internal-mcp"}
            time_audit = await asyncio.to_thread(_run_tool_audited, "get_current_datetime", time_args)
            time_context = None
            try:
                parsed_time = json.loads(time_audit["result"])
                if isinstance(parsed_time, dict):
                    time_context = parsed_time
            except (TypeError, ValueError):
                pass
            tool_calls_out.append({key: value for key, value in time_audit.items() if key != "result"})
            yield {"type": "tool", "name": "get_current_datetime", "status": "complete", "args": time_audit["args"], "source": time_audit["source"], "ok": time_audit["ok"], "error_code": time_audit.get("error_code"), "duration_ms": time_audit["duration_ms"]}
            if time_context:
                yield {"type": "time-context", "context": time_context}
        # Memory is a separate evidence channel: candidates are explicit task
        # facts, while retrieval decides what is relevant to this turn.
        candidates = extract_candidate_memories(message, thread_id, user_id)
        for candidate in candidates:
            stored = await conversation_memory.upsert_memory(candidate)
            yield {
                "type": "memory-candidate",
                "memory": {"id": stored.get("id"), "type": stored.get("memory_type"), "content": stored.get("content"), "status": "待确认"},
            }
        active_questions = propose_active_memory_questions(message, candidates)
        if active_questions:
            yield {"type": "memory-action", "mode": "active", "questions": active_questions, "reason": "当前农业决策缺少关键现场条件"}
        organization = await conversation_memory.organize_if_needed(thread_id, user_id)
        if organization.get("triggered"):
            yield {"type": "memory-organized", "reason": organization.get("reason"), "conflicts": organization.get("conflicts", []), "archived": organization.get("archived", 0)}
        memory_selection = await conversation_memory.relevant_memories(message, thread_id, user_id, max_items=6)
        used_memories = memory_selection.get("used", [])
        skipped_memories = memory_selection.get("skipped", [])
        if used_memories or skipped_memories:
            yield {"type": "memory", "used": [
                {"id": item.get("id"), "content": item.get("content"), "relevance": item.get("relevance")}
                for item in used_memories
            ], "skipped": [
                {"id": item.get("id"), "content": item.get("content"), "relevance": item.get("relevance"), "reason": "相似但未达到当前任务相关性门槛"}
                for item in skipped_memories
            ]}
        # 查询路由：决定检索路径
        try:
            from retrieval.query_router import query_router
            route = query_router.route(message)
            scenario_type = query_router.classify_scenario(message)
            search_hints = query_router.get_search_hints(message, scenario_type)
            yield {"type": "trace", "stage": "routing", "route": route.value, "scenario": scenario_type, "hints": search_hints}
        except ImportError:
            route = None
            scenario_type = None
            search_hints = {}
        retrieval_trace = agriir_pipeline.retrieve(message, knowledge_base, scenario_context)
        retrieval_strategy = retrieval_trace["strategy"]
        kb_results = retrieval_trace["results"]
        citations = retrieval_trace["citations"]
        yield {"type": "trace", "stage": "retrieval", "query": retrieval_trace["query"], "refined_query": retrieval_trace["refined_query"], "subqueries": retrieval_trace["subqueries"], "strategy": retrieval_strategy, "citation_count": len(citations)}

        kb_ctx = ""
        if kb_results:
            kb_ctx = "\n\n## 知识库检索结果：\n" + "\n".join(
                f"- [{citations[index]['label']}] {result.get('content', '')}" for index, result in enumerate(kb_results[:3])
            )
            kb_ctx += "\n\n## 可引用证据：\n" + agriir_pipeline.citation_context(citations)
            items = []
            for result in kb_results[:3]:
                content = str(result.get("content", "")).strip().replace("\n", " ")
                metadata = result.get("metadata") or {}
                citation = citations[len(items)] if len(items) < len(citations) else {}
                items.append({
                    "title": str(metadata.get("title") or metadata.get("source") or "农业知识库"),
                    "excerpt": content[:120],
                    "relevance": round(float(result.get("relevance", 0.0)), 3),
                    "eligible": bool(citation.get("eligible", False)),
                    "evidence_level": str(citation.get("evidence_level", "C")),
                    "eligibility_reason": citation.get("eligibility_reason", "similarity-threshold"),
                })
            yield {"type": "ui", "component": "knowledge-context", "props": {"items": items, "strategy": retrieval_strategy}}
            yield {"type": "sources", "items": citations}

        required_evidence_scope = agriir_pipeline.required_evidence_scope(message)
        has_eligible_evidence = any(item.get("eligible") and item.get("evidence_level") == "A" for item in citations)
        if required_evidence_scope and not has_eligible_evidence:
            answer = _build_evidence_gap_answer(message, required_evidence_scope, answer_mode)
            yield {"type": "status", "message": "缺少适用的官方依据，已启用安全回答"}
            yield {"type": "delta", "text": answer}
            if answer_mode == "professional":
                yield {"type": "ui", "component": "decision-card", "props": _extract_decision_card(answer, message)}
            await conversation_memory.add_message(thread_id, "user", message)
            await conversation_memory.add_message(thread_id, "assistant", answer)
            self._hist.setdefault(thread_id, []).extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": answer},
            ])
            yield {"type": "done", "thread_id": thread_id, "message": answer, "tool_calls": tool_calls_out, "answer_mode": answer_mode, "completion_status": "guarded", "evidence_guarded": True, "required_evidence_scope": required_evidence_scope}
            return

        memory_ctx = ""
        if used_memories:
            memory_ctx = "\n\n## 当前任务相关记忆（仅供参考，不是知识库证据）：\n" + "\n".join(
                f"- {item.get('content')}（相关性 {item.get('relevance', 0):.0%}）" for item in used_memories
            )
        time_ctx = ""
        if time_context:
            time_ctx = "\n\n## 时间上下文（服务端确定性预检，必须遵守）:\n" + json.dumps(time_context, ensure_ascii=False)
        scenario_ctx = ""
        if scenario_context:
            scenario_ctx = "\n\n## 结构化场景上下文（服务端字段，缺失处不得猜测）：\n" + json.dumps(scenario_context, ensure_ascii=False)
        system_prompt = AGRICULTURE_SYSTEM_PROMPT + ANSWER_MODE_PROMPTS[answer_mode] + time_ctx + memory_ctx + scenario_ctx + kb_ctx
        history = self._hist.get(thread_id)
        if history is None:
            stored_history = await conversation_memory.get_history(thread_id, limit=8)
            history = [
                {"role": item["role"], "content": item["content"]}
                for item in stored_history
                if item["role"] in {"user", "assistant"}
            ]
            self._hist[thread_id] = history
        messages = [SystemMessage(content=system_prompt)]
        for item in history:
            messages.append(HumanMessage(content=item["content"]) if item["role"] == "user" else AIMessage(content=item["content"]))
        messages.append(HumanMessage(content=message))

        answer_parts: List[str] = []
        generation_failed = False
        failure_detail = ""

        for loop_index in range(3):
            try:
                yield {"type": "status", "message": "正在生成农技建议"}
                combined_chunk = None
                async for chunk in self.llm.astream(messages):
                    combined_chunk = chunk if combined_chunk is None else combined_chunk + chunk
                    text = _chunk_text(getattr(chunk, "content", ""))
                    if text:
                        answer_parts.append(text)
                        yield {"type": "delta", "text": text}

                if answer_parts:
                    break

                tool_calls = getattr(combined_chunk, "tool_calls", None) or []
                if not tool_calls:
                    break

                messages.append(combined_chunk)
                for tool_call in tool_calls:
                    name = tool_call.get("name", "")
                    args = tool_call.get("args", {})
                    yield {"type": "tool", "name": name, "status": "running", "args": _safe_tool_args(args), "source": "internal-mcp"}
                    audit = await asyncio.to_thread(_run_tool_audited, name, args)
                    tool_calls_out.append({key: value for key, value in audit.items() if key != "result"})
                    result = audit["result"]
                    yield {"type": "tool", "name": name, "status": "complete", "args": audit["args"], "source": audit["source"], "ok": audit["ok"], "error_code": audit.get("error_code"), "duration_ms": audit["duration_ms"]}
                    if name == "search_agri_resources":
                        try:
                            resources = json.loads(result)
                            if isinstance(resources, list):
                                yield {"type": "resources", "items": resources[:6]}
                        except (TypeError, ValueError):
                            logger.info("资源工具返回了不可解析的数据")
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call.get("id", "")))
            except asyncio.CancelledError:
                logger.info("流式对话已被客户端取消: %s", thread_id)
                raise
            except Exception as exc:
                logger.error("LLM astream 失败 (_loop %d): %s", loop_index, exc)
                generation_failed = True
                failure_detail = str(exc)
                break

        raw_answer = "".join(answer_parts).strip()
        text_tool_queries = _extract_text_tool_queries(raw_answer)
        if not any(call.get("name") == "search_agri_resources" for call in tool_calls_out) and _requests_related_resources(message):
            # Some providers fall back to plain text and skip the structured
            # tool-call field. Honor the user's explicit resource request on
            # the server so the UI still receives real resource cards.
            text_tool_queries.append(message)
        answer = _strip_evidence_process(_clean_tool_markers(raw_answer))

        # Some OpenAI-compatible providers occasionally serialize a function
        # call as XML-like text instead of populating `tool_calls`. Recover the
        # resource request so the UI still receives a real resource event.
        if text_tool_queries and not any(call.get("name") == "search_agri_resources" for call in tool_calls_out):
            for query in text_tool_queries[:2]:
                yield {"type": "tool", "name": "search_agri_resources", "status": "running", "args": {"query": query}, "source": "internal-mcp"}
                audit = await asyncio.to_thread(_run_tool_audited, "search_agri_resources", {"query": query})
                tool_calls_out.append({key: value for key, value in audit.items() if key != "result"})
                result = audit["result"]
                yield {"type": "tool", "name": "search_agri_resources", "status": "complete", "args": audit["args"], "source": audit["source"], "ok": audit["ok"], "error_code": audit.get("error_code"), "duration_ms": audit["duration_ms"]}
                try:
                    resources = json.loads(result)
                    if isinstance(resources, list):
                        yield {"type": "resources", "items": resources[:6]}
                except (TypeError, ValueError):
                    logger.info("文本工具调用返回了不可解析的资源数据")

        if text_tool_queries and not answer:
            answer = "已根据你的请求整理相关农业图片与资料，请查看下方资源卡片。"

        completion_status = "fallback" if generation_failed else "complete"
        if not answer:
            try:
                yield {"type": "status", "message": "正在使用备用回答通道"}
                fallback_llm = ChatOpenAI(
                    base_url=settings.agnes_base_url,
                    openai_api_key=settings.agnes_api_key,
                    model=settings.agnes_chat_model,
                    temperature=0.1,
                    openai_proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
                )
                fallback = await fallback_llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=message)])
                answer = _chunk_text(getattr(fallback, "content", "")).strip()
                if answer:
                    completion_status = "fallback"
                    yield {"type": "delta", "text": answer}
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("LLM fallback 失败: %s", exc)
                failure_detail = str(exc)

        if not answer:
            answer = "抱歉，我现在无法回答这个问题，请稍后重试。"
            yield {"type": "delta", "text": answer}
            completion_status = "error"
            yield {"type": "error", "message": "模型生成未完成，请检查服务后重试。", "error_code": "MODEL_GENERATION_FAILED"}

        answer = _strip_evidence_process(_clean_tool_markers(answer))
        policy_answer = _enforce_evidence_policy_with_pipeline(answer, message, citations)
        if policy_answer != answer:
            answer = policy_answer
            yield {"type": "answer-replace", "text": answer, "mode": answer_mode, "reason": "evidence-policy"}

        # ── 多智能体安全/分析检查 ──
        if _HAS_MULTIAGENT:
            try:
                _orchestrator = _MultiAgentOrchestrator()
                _orchestrator.setup(knowledge_base)
                _retrieval = {
                    "results": kb_results,
                    "citations": citations,
                    "graph_channel_used": retrieval_trace.get("graph_channel_used", False),
                    "graph_count": retrieval_trace.get("graph_count", 0),
                    "strategy": retrieval_strategy,
                }
                _analyst = _orchestrator.analyst.run(message, _retrieval)
                _safety = _orchestrator.safety.run(message, answer, citations, _analyst)
                yield {"type": "trace", "stage": "multiagent",
                       "analyst_risk": _analyst.get("risk_scope"),
                       "safety_safe": _safety.get("safe", True),
                       "safety_warnings": _safety.get("reasons", [])}
                # 安全检查失败时附加警告（不阻止回答）
                if not _safety.get("safe", True):
                    warnings_text = "; ".join(_safety.get("reasons", []))
                    answer = answer + f"\n\n⚠️ **安全提醒**: {warnings_text}"
                    yield {"type": "answer-replace", "text": answer, "mode": answer_mode, "reason": "safety-warning"}
            except Exception as exc:
                logger.debug("多智能体检查跳过: %s", exc)

        # Build the decision card before appending the traceable citation block;
        # citations belong to the collapsed evidence layer, not the action card.
        decision_card = _extract_decision_card(answer, message) if answer_mode != "brief" else None

        # Sources are delivered as a separate structured event and rendered in
        # the collapsed evidence layer. Keep retrieval/citation prose out of
        # primary and persisted answer content.

        if answer_mode == "brief":
            compact = _compact_answer(answer, message)
            if compact != answer:
                answer = compact
                # Replace the streamed answer in the persisted/API result. The
                # model text may already have been displayed, so emit a mode
                # correction event for clients that reconcile the final value.
                yield {"type": "answer-replace", "text": answer, "mode": answer_mode}
        if answer_mode != "brief":
            yield {"type": "ui", "component": "decision-card", "props": decision_card}

        await conversation_memory.add_message(thread_id, "user", message)
        await conversation_memory.add_message(
            thread_id,
            "assistant",
            answer,
            extra={
                "answer_mode": answer_mode,
                "completion_status": completion_status,
                "decision_card": decision_card,
                "runtime_details": {
                    "persisted": True,
                    "tool_count": len(tool_calls_out),
                    "knowledge_count": len(kb_results[:3]) if isinstance(kb_results, list) else 0,
                    "citation_count": len(citations),
                    "memory_used_count": len(used_memories),
                    "memory_skipped_count": len(skipped_memories),
                    "has_time_context": bool(time_context),
                },
            },
        )
        self._hist.setdefault(thread_id, []).extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ])
        # 截断防内存泄漏
        if len(self._hist[thread_id]) > self._hist_max_per_thread:
            self._hist[thread_id] = self._hist[thread_id][-self._hist_max_per_thread:]
        yield {"type": "done", "thread_id": thread_id, "message": answer, "tool_calls": tool_calls_out, "answer_mode": answer_mode, "completion_status": completion_status}

    async def chat(self, message: str, thread_id: str, user_id=None, answer_mode: str = "professional", scenario_context: Optional[Dict[str, Any]] = None):
        """Backwards-compatible non-streaming adapter for existing API consumers."""
        answer = ""
        tool_calls = []
        sources = []
        completion_status = "complete"
        async for event in self.stream_chat(message, thread_id, user_id, answer_mode, scenario_context):
            if event["type"] == "done":
                answer = event["message"]
                tool_calls = event["tool_calls"]
                completion_status = event.get("completion_status", "complete")
            elif event["type"] == "sources" and isinstance(event.get("items"), list):
                sources = event["items"]
        return {"message": answer, "sources": sources, "tool_calls": tool_calls, "thread_id": thread_id, "answer_mode": _normalize_answer_mode(answer_mode), "completion_status": completion_status}

    async def get_history(self, thread_id, limit=20):
        history = await conversation_memory.get_history(thread_id, limit)
        enriched = []
        for item in history:
            current = dict(item)
            if current.get("role") == "assistant":
                current["content"] = _strip_evidence_process(_clean_tool_markers(str(current.get("content") or "")))
                extra = dict(current.get("extra") or {})
                if extra.get("answer_mode") not in ANSWER_MODES:
                    extra["answer_mode"] = "professional" if "现场摘要" in current["content"] else "brief"
                if extra.get("answer_mode") == "professional" and not isinstance(extra.get("decision_card"), dict):
                    extra["decision_card"] = _extract_decision_card(current["content"])
                current["extra"] = extra
            enriched.append(current)
        return enriched

    async def clear_history(self, thread_id):
        await conversation_memory.clear_thread(thread_id)
        self._hist.pop(thread_id, None)


agri_agent = AgricultureAgent()
