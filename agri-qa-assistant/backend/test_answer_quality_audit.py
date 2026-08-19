"""User-facing answer quality audit contracts (TDD).

These tests intentionally exercise the deterministic boundary between model
output, retrieval evidence and the UI transport.  They do not require a live
LLM or network access.
"""
import asyncio

from langchain_core.messages import AIMessage

import agent
from agriir_pipeline import agriir_pipeline
from knowledge_base import knowledge_base
from memory import conversation_memory


def test_decision_card_does_not_call_missing_field_information_complete():
    card = agent._extract_decision_card(
        "现场摘要\n待补充地区、生育期、症状和影响范围。\n\n"
        "优先判断\n当前信息不足。\n\n现在做什么\n记录变化。\n\n"
        "风险边界\n按标签使用。\n\n复查节点\n48小时后复查。",
        "小麦叶片发黄",
    )
    assert card["complete"] is False


def test_decision_card_omits_horizontal_rule_artifacts():
    card = agent._extract_decision_card(
        "### 1. 现场摘要\n酸性土壤\n---\n### 2. 优先判断\n- 先测 pH\n---\n### 3. 现在做什么\n- 记录田块\n### 4. 风险边界\n- 按标签核验\n### 5. 复查节点\n- 48小时后复查",
        "酸性土壤如何改良",
    )
    assert card["summary"] == "酸性土壤"
    assert all(item not in {"--", "---"} for section in ("judgments", "actions", "risks", "followup") for item in card[section])


def test_user_answer_removes_retrieval_process_from_primary_content():
    answer = """结论
先测土壤 pH，再制定改良方案（相关性52%）。

现场摘要
红壤酸性地块。

知识库依据
[S1] 土壤改良技术
[S2] 水肥管理
"""
    cleaned = agent._strip_evidence_process(answer)
    assert "相关性52%" not in cleaned
    assert "知识库依据" not in cleaned
    assert "[S1]" not in cleaned
    assert "现场摘要" in cleaned


def test_bold_evidence_heading_is_removed_from_primary_content():
    cleaned = agent._strip_evidence_process("现场摘要\n红壤酸性。\n\n**知识库依据**：[S1] 土壤改良技术")
    assert "知识库依据" not in cleaned
    assert "[S1]" not in cleaned


def test_high_risk_model_claim_triggers_policy_even_when_question_is_generic():
    sanitized = agent._enforce_evidence_policy("建议每亩施用石灰50-75公斤。", "江西红壤土壤如何改良？", [])
    assert "50-75公斤" not in sanitized
    assert "待官方核验" in sanitized


def test_decision_card_exposes_a_conclusion_separately():
    card = agent._extract_decision_card(
        "结论\n先测土壤 pH，再按测土结果确定石灰方案。\n\n"
        "现场摘要\n红壤酸性地块。\n\n优先判断\n酸性土壤需先测土。\n\n"
        "现在做什么\n取土检测。\n\n风险边界\n具体剂量待官方核验。\n\n复查节点\n30天后复查。",
        "红壤酸性土壤如何改良",
    )
    assert card["conclusion"] == "先测土壤 pH，再按测土结果确定石灰方案。"


def test_seed_treatment_defaults_do_not_use_disease_intake_fields():
    card = agent._extract_decision_card("", "水稻播种前需要做哪些种子处理？")
    assert "品种" in card["summary"]
    assert "包衣" in card["summary"]
    assert "症状" not in card["summary"]
    assert "催芽" in card["judgments"][0]


def test_seed_treatment_active_questions_are_scene_specific():
    from memory import propose_active_memory_questions
    questions = propose_active_memory_questions("水稻播种前需要做哪些种子处理？", [])
    assert any("品种" in question for question in questions)
    assert not any("症状" in question or "影响范围" in question for question in questions)


def test_history_enriches_legacy_assistant_messages_for_refresh():
    async def run():
        original = conversation_memory.get_history
        conversation_memory.get_history = lambda *_args, **_kwargs: asyncio.sleep(0, result=[{
            "role": "assistant",
            "content": "现场摘要\n红壤酸性地块。\n\n优先判断\n先测土。\n\n现在做什么\n取样。\n\n风险边界\n待官方核验。\n\n复查节点\n30天后复查。\n\n知识库依据\n[S1] 背景片段",
            "timestamp": "2026-08-10T00:00:00",
            "extra": None,
        }])
        try:
            history = await agent.agri_agent.get_history("legacy-refresh")
            assert history[0]["extra"]["answer_mode"] == "professional"
            assert history[0]["extra"]["decision_card"]["summary"] == "红壤酸性地块。"
            assert "知识库依据" not in history[0]["content"]
        finally:
            conversation_memory.get_history = original
    asyncio.run(run())


def test_low_relevance_citation_is_explicitly_weak_evidence():
    citations = agriir_pipeline.build_citations([
        {"content": "无关的农业背景片段", "metadata": {"source": "农业知识库"}, "relevance": 0.14}
    ], query="水稻稻飞虱怎么防治")
    assert citations[0]["eligible"] is False
    assert citations[0]["eligibility_reason"] == "similarity-threshold"


def test_high_risk_answer_without_official_evidence_is_degraded_to_principles():
    answer = "现在做什么\n每亩使用石灰50-100公斤，施用后深翻20-30cm。\n参考：75-100 kg/亩"
    sanitized = agent._enforce_evidence_policy(answer, "酸性土壤施用石灰多少？", [])
    assert "50-100公斤" not in sanitized
    assert "75-100 kg/亩" not in sanitized
    assert "待官方核验" in sanitized


def test_high_risk_principle_answer_still_exposes_evidence_boundary():
    sanitized = agent._enforce_evidence_policy("先测土壤 pH，再按土壤质地制定方案。", "酸性土壤施用石灰多少？", [])
    assert "待官方核验" in sanitized


def test_malformed_markdown_is_normalized_before_persistence():
    cleaned = agent._clean_tool_markers("*结论**：先观察\n*江西早稻播期判断。**\n-\n- 补充田间照片")
    assert "**结论**" in cleaned
    assert "**江西早稻播期判断。**" in cleaned
    assert "\n-\n" not in cleaned


def test_brief_compaction_does_not_break_bold_markers():
    compact = agent._compact_answer("*江西早稻播期。**\n*结论：已过播期。**", "江西早稻播期")
    assert all(not line.startswith("*") or line.startswith("**") for line in compact.splitlines())


class _FailingModel:
    def astream(self, _messages):
        async def _raise():
            raise RuntimeError("provider unavailable")
            yield None
        return _raise()


async def _run_failed_generation():
    original = {
        "llm": agent.agri_agent.llm,
        "search": knowledge_base.search,
        "history": conversation_memory.get_history,
        "memories": conversation_memory.relevant_memories,
        "organize": conversation_memory.organize_if_needed,
        "add": conversation_memory.add_message,
    }
    agent.agri_agent.llm = _FailingModel()
    knowledge_base.search = lambda *_args, **_kwargs: []
    conversation_memory.get_history = lambda *_args, **_kwargs: asyncio.sleep(0, result=[])
    conversation_memory.relevant_memories = lambda *_args, **_kwargs: asyncio.sleep(0, result={"used": [], "skipped": []})
    conversation_memory.organize_if_needed = lambda *_args, **_kwargs: asyncio.sleep(0, result={"triggered": False, "conflicts": [], "archived": 0})
    conversation_memory.add_message = lambda *_args, **_kwargs: asyncio.sleep(0)
    try:
        return [event async for event in agent.agri_agent.stream_chat("水稻稻飞虱怎么防治？", "quality-failure-test")]
    finally:
        agent.agri_agent.llm = original["llm"]
        knowledge_base.search = original["search"]
        conversation_memory.get_history = original["history"]
        conversation_memory.relevant_memories = original["memories"]
        conversation_memory.organize_if_needed = original["organize"]
        conversation_memory.add_message = original["add"]


def test_failed_generation_is_not_reported_as_normal_completion():
    events = asyncio.run(_run_failed_generation())
    done = events[-1]
    assert done["type"] == "done"
    assert done["completion_status"] in {"fallback", "error"}
    if done["completion_status"] == "error":
        assert any(event["type"] == "error" for event in events)


def test_tool_completion_contract_is_user_visible_and_auditable():
    audit = agent._run_tool_audited("get_current_datetime", {"reference_date": "2026-05-29"})
    assert {"ok", "source", "duration_ms", "error_code"} <= audit.keys()
