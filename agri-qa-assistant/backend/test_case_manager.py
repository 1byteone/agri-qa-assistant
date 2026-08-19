# -*- coding: utf-8 -*-
"""案例管理系统测试。"""
import pytest
import asyncio
from case_manager import CaseManager


@pytest.fixture
def manager():
    return CaseManager()


class TestCaseManager:
    """CaseManager CRUD 测试。"""

    @pytest.mark.asyncio
    async def test_create_case(self, manager):
        result = await manager.create_case(
            thread_id="test_thread_001",
            user_id="test_user",
            topic_category="diagnosis",
            title="水稻稻飞虱防治",
        )
        assert result["id"].startswith("case_")
        assert result["status"] == "open"
        assert result["severity"] == "normal"

    @pytest.mark.asyncio
    async def test_get_case(self, manager):
        created = await manager.create_case(thread_id="test_thread_002", title="测试案例")
        case = await manager.get_case(created["id"])
        assert case is not None
        assert case["id"] == created["id"]
        assert case["thread_id"] == "test_thread_002"

    @pytest.mark.asyncio
    async def test_add_event(self, manager):
        created = await manager.create_case(thread_id="test_thread_003")
        event = await manager.add_event(
            case_id=created["id"],
            event_type="answer_generated",
            payload={"message_id": "msg_001"},
            actor="agent",
        )
        assert event["id"].startswith("evt_")
        assert event["event_type"] == "answer_generated"

    @pytest.mark.asyncio
    async def test_get_case_timeline(self, manager):
        created = await manager.create_case(thread_id="test_thread_004")
        await manager.add_event(case_id=created["id"], event_type="answer_generated")
        await manager.add_event(case_id=created["id"], event_type="feedback", payload={"feedback_type": "helpful"})
        timeline = await manager.get_case_timeline(created["id"])
        assert len(timeline) == 3  # create + answer + feedback
        assert timeline[0]["event_type"] == "case_created"
        assert timeline[1]["event_type"] == "answer_generated"
        assert timeline[2]["event_type"] == "feedback"

    @pytest.mark.asyncio
    async def test_escalate_case(self, manager):
        created = await manager.create_case(thread_id="test_thread_005")
        result = await manager.escalate_case(created["id"], reason="高风险农药问题")
        assert result["status"] == "escalated"
        case = await manager.get_case(created["id"])
        assert case["status"] == "escalated"
        assert case["severity"] == "elevated"

    @pytest.mark.asyncio
    async def test_resolve_case(self, manager):
        created = await manager.create_case(thread_id="test_thread_006")
        await manager.escalate_case(created["id"])
        result = await manager.resolve_case(created["id"], resolution="已咨询农技站")
        assert result["status"] == "resolved"
        case = await manager.get_case(created["id"])
        assert case["status"] == "resolved"
        assert case["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_submit_feedback(self, manager):
        created = await manager.create_case(thread_id="test_thread_007")
        feedback = await manager.submit_feedback(
            case_id=created["id"],
            thread_id="test_thread_007",
            message_id="msg_002",
            feedback_type="helpful",
            comment="回答很有帮助",
        )
        assert feedback["event_type"] == "feedback"

    @pytest.mark.asyncio
    async def test_invalid_feedback_type(self, manager):
        created = await manager.create_case(thread_id="test_thread_008")
        with pytest.raises(ValueError, match="无效的反馈类型"):
            await manager.submit_feedback(
                case_id=created["id"],
                thread_id="test_thread_008",
                message_id=None,
                feedback_type="invalid",
            )

    @pytest.mark.asyncio
    async def test_list_cases(self, manager):
        await manager.create_case(thread_id="test_thread_009", title="案例A")
        await manager.create_case(thread_id="test_thread_010", title="案例B")
        cases = await manager.list_cases()
        assert len(cases) >= 2

    @pytest.mark.asyncio
    async def test_list_cases_filter_status(self, manager):
        created = await manager.create_case(thread_id="test_thread_011", title="待升级")
        await manager.escalate_case(created["id"])
        escalated = await manager.list_cases(status="escalated")
        assert any(c["id"] == created["id"] for c in escalated)

    @pytest.mark.asyncio
    async def test_get_feedback_summary(self, manager):
        created = await manager.create_case(thread_id="test_thread_012")
        await manager.submit_feedback(created["id"], "test_thread_012", None, "helpful")
        await manager.submit_feedback(created["id"], "test_thread_012", None, "inaccurate")
        summary = await manager.get_feedback_summary(created["id"])
        assert summary["total"] == 2
        assert summary["breakdown"]["helpful"] == 1
        assert summary["breakdown"]["inaccurate"] == 1

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, manager):
        case = await manager.get_case("nonexistent_case")
        assert case is None

    def test_should_auto_escalate(self, manager):
        # 高风险 + 无 A 级证据 → 应升级
        assert manager.should_auto_escalate("水稻每亩施多少农药", []) is True
        # 高风险 + 有 A 级证据 → 不升级
        assert manager.should_auto_escalate("水稻每亩施多少农药", [{"eligible": True, "evidence_level": "A"}]) is False
        # 低风险 → 不升级
        assert manager.should_auto_escalate("水稻什么时候播种", []) is False
