# -*- coding: utf-8 -*-
"""试点管理测试。"""
import pytest
from pilot_manager import PilotManager


@pytest.fixture
def manager():
    return PilotManager()


class TestPilotManager:
    """PilotManager 测试。"""

    @pytest.mark.asyncio
    async def test_add_user(self, manager):
        result = await manager.add_user(
            username="test_teacher_001",
            display_name="张老师",
            role="teacher",
            organization="江西农业大学",
        )
        assert result["id"].startswith("pilot_")
        assert result["username"] == "test_teacher_001"
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_start_session(self, manager):
        user = await manager.add_user(
            username="test_farmer_001",
            display_name="李农民",
            role="farmer",
        )
        session = await manager.start_session(user["id"], "thread_001")
        assert session["session_id"].startswith("sess_")
        assert session["thread_id"] == "thread_001"

    @pytest.mark.asyncio
    async def test_end_session(self, manager):
        user = await manager.add_user(
            username="test_worker_001",
            display_name="王技术员",
            role="extension_worker",
        )
        session = await manager.start_session(user["id"], "thread_002")
        result = await manager.end_session(
            session["session_id"],
            message_count=15,
            topics=["水稻", "施肥"],
            satisfaction_score=4,
        )
        assert result["status"] == "ended"

    @pytest.mark.asyncio
    async def test_submit_feedback(self, manager):
        user = await manager.add_user(
            username="test_teacher_002",
            display_name="刘老师",
            role="teacher",
        )
        feedback = await manager.submit_feedback(
            user_id=user["id"],
            feedback_type="suggestion",
            content="建议增加更多病虫害图片",
            rating=4,
            category="feature",
        )
        assert feedback["id"].startswith("fb_")
        assert feedback["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_get_user_stats(self, manager):
        user = await manager.add_user(
            username="test_farmer_002",
            display_name="赵农民",
            role="farmer",
        )
        session = await manager.start_session(user["id"], "thread_003")
        await manager.end_session(session["session_id"], message_count=10, satisfaction_score=5)
        stats = await manager.get_user_stats(user["id"])
        assert stats["session_count"] == 1
        assert stats["total_messages"] == 10
        assert stats["avg_satisfaction"] == 5.0

    @pytest.mark.asyncio
    async def test_get_pilot_summary(self, manager):
        # 添加测试用户
        await manager.add_user(username="teacher_001", display_name="教师1", role="teacher")
        await manager.add_user(username="farmer_001", display_name="农民1", role="farmer")
        summary = await manager.get_pilot_summary()
        assert summary["total_users"] >= 2
        assert "role_distribution" in summary

    @pytest.mark.asyncio
    async def test_list_users(self, manager):
        await manager.add_user(username="list_test_001", display_name="列表测试1", role="teacher")
        await manager.add_user(username="list_test_002", display_name="列表测试2", role="farmer")
        users = await manager.list_users()
        assert len(users) >= 2
