import asyncio
import json

from langchain_core.messages import AIMessage

import agent
import tools
from schemas import ChatRequest
from knowledge_base import knowledge_base
from memory import conversation_memory


def test_current_datetime_uses_configured_timezone_and_server_clock():
    payload = json.loads(tools.get_current_datetime.invoke({"timezone": "Asia/Shanghai"}))
    assert payload["ok"] is True
    assert payload["kind"] == "current_datetime"
    assert payload["source"] == "server_system_clock"
    assert payload["is_actual_now"] is True
    assert payload["timezone"] == "Asia/Shanghai"


def test_reference_date_is_not_reported_as_now():
    payload = json.loads(tools.get_current_datetime.invoke({"reference_date": "2026年5月29日"}))
    assert payload == {
        "ok": True,
        "kind": "evaluation_datetime",
        "date": "2026-05-29",
        "local_datetime": "2026-05-29T12:00:00",
        "timezone": "Asia/Shanghai",
        "source": "user_reference",
        "is_actual_now": False,
        "notice": "这是用户指定的评估日期，不代表服务器当前日期。",
    }


def test_invalid_temporal_inputs_are_structured():
    assert json.loads(tools.get_current_datetime.invoke({"timezone": "Not/AZone"}))["error_code"] == "INVALID_TIMEZONE"
    assert json.loads(tools.get_current_datetime.invoke({"reference_date": "2026-02-31"}))["error_code"] == "INVALID_REFERENCE_DATE"


def test_jiangxi_growing_period_and_unknown_crop():
    jiangxi = json.loads(tools.calculate_growing_period.invoke({"crop_name": "水稻", "region": "南昌", "evaluation_date": "2026-05-29"}))
    assert jiangxi["ok"] is True
    assert jiangxi["region"] == "江西"
    assert jiangxi["date_semantics"] == "用户指定评估日期，不是服务器当前日期"
    unknown = json.loads(tools.calculate_growing_period.invoke({"crop_name": "咖啡", "region": "江西"}))
    assert unknown["error_code"] == "CROP_REGION_NOT_FOUND"


def test_query_crop_knowledge_returns_retrieval_evidence(monkeypatch):
    monkeypatch.setattr(knowledge_base, "search", lambda *_args, **_kwargs: [{"content": "稻飞虱在分蘖期需重点监测。", "metadata": {"source": "test"}, "relevance": 0.81}])
    payload = json.loads(tools.query_crop_knowledge.invoke({"crop_name": "水稻", "topic": "病虫害"}))
    assert payload["ok"] is True
    assert payload["source"] == "CropWise农业知识库"
    assert payload["results"][0]["relevance"] == 0.81


def test_tool_audit_has_outcome_source_and_duration():
    audit = agent._run_tool_audited("get_current_datetime", {"reference_date": "2026-05-29"})
    assert audit["ok"] is True
    assert audit["source"] == "internal-mcp"
    assert isinstance(audit["duration_ms"], (int, float))
    assert audit["args"]["reference_date"] == "2026-05-29"


def test_mcp_status_is_truthful_about_connection_mode():
    status = tools.get_mcp_status()
    assert status["mode"] == "embedded-mcp-compatible"
    assert status["external_process_connected"] is False
    assert {item["name"] for item in status["tools"]} >= {"get_current_datetime", "get_agri_weather", "query_crop_knowledge"}


def test_weather_tool_validates_forecast_window_without_network():
    payload = json.loads(tools.get_agri_weather.invoke({"location": "南昌", "days": 0}))
    assert payload["ok"] is False
    assert payload["error_code"] == "INVALID_DAYS"


def test_answer_modes_are_explicit_and_brief_mode_is_bounded():
    assert ChatRequest(message="水稻怎么种", thread_id="mode-test").answer_mode == "professional"
    assert ChatRequest(message="水稻怎么种", thread_id="mode-test", answer_mode="brief").answer_mode == "brief"
    compact = agent._compact_answer(
        "现场摘要\n江西早稻叶片发黄。\n\n优先判断\n可能是缺素或病害。\n\n现在做什么\n先拍照并检查田间积水。\n\n风险边界\n农药按标签使用。\n\n复查节点\n48小时后复查。",
        "水稻叶片发黄",
    )
    assert "判断：" in compact and "建议：" in compact and "注意：" in compact
    assert "现场摘要" not in compact
    assert len(compact) <= 600


class _DeterministicModel:
    async def astream(self, _messages):
        yield AIMessage(content="现场摘要\n江西早稻需要结合评估日期判断播期。\n\n优先判断\n以评估日期为准。\n\n现在做什么\n核对当地农时。\n\n风险边界\n以气象部门预警为准。\n\n复查节点\n48小时后复查。")


async def _run_preflight_stream(answer_mode="professional"):
    original = {
        "llm": agent.agri_agent.llm,
        "search": knowledge_base.search,
        "history": conversation_memory.get_history,
        "memories": conversation_memory.relevant_memories,
        "organize": conversation_memory.organize_if_needed,
        "add": conversation_memory.add_message,
    }
    agent.agri_agent.llm = _DeterministicModel()
    knowledge_base.search = lambda *_args, **_kwargs: []
    conversation_memory.get_history = lambda *_args, **_kwargs: asyncio.sleep(0, result=[])
    conversation_memory.relevant_memories = lambda *_args, **_kwargs: asyncio.sleep(0, result={"used": [], "skipped": []})
    conversation_memory.organize_if_needed = lambda *_args, **_kwargs: asyncio.sleep(0, result={"triggered": False, "conflicts": [], "archived": 0})
    conversation_memory.add_message = lambda *_args, **_kwargs: asyncio.sleep(0)
    try:
        return [event async for event in agent.agri_agent.stream_chat("按2026年5月29日判断江西早稻播期", "temporal-preflight-test", answer_mode=answer_mode)]
    finally:
        agent.agri_agent.llm = original["llm"]
        knowledge_base.search = original["search"]
        conversation_memory.get_history = original["history"]
        conversation_memory.relevant_memories = original["memories"]
        conversation_memory.organize_if_needed = original["organize"]
        conversation_memory.add_message = original["add"]


def test_stream_preflight_labels_user_date_and_audits_tool():
    events = asyncio.run(_run_preflight_stream())
    time_event = next(event for event in events if event["type"] == "time-context")
    assert time_event["context"]["date"] == "2026-05-29"
    assert time_event["context"]["is_actual_now"] is False
    tool_event = next(event for event in events if event["type"] == "tool" and event["status"] == "complete")
    assert tool_event["ok"] is True
    assert tool_event["source"] == "internal-mcp"
    assert isinstance(tool_event["duration_ms"], (int, float))
    assert events[-1]["tool_calls"][0]["error_code"] is None


def test_brief_stream_replaces_long_model_output_and_skips_decision_card():
    events = asyncio.run(_run_preflight_stream("brief"))
    assert any(event["type"] == "mode" and event["mode"] == "brief" for event in events)
    replacement = next(event for event in events if event["type"] == "answer-replace")
    assert "判断：" in replacement["text"]
    assert not any(event.get("type") == "ui" and event.get("component") == "decision-card" for event in events)
    assert events[-1]["answer_mode"] == "brief"
