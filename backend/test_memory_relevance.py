"""Acceptance tests for the relatedness-over-similarity memory contract."""
from datetime import datetime, timedelta

from memory import (
    extract_candidate_memories,
    normalize_memory_key,
    score_memory_relevance,
    select_relevant_memories,
    resolve_temporal_reference,
    propose_active_memory_questions,
)


def test_explicit_task_facts_are_candidates_but_not_preferences():
    items = extract_candidate_memories("我在赣州种植脐橙，目标是控制黄龙病扩散", "t-1", "u-1")
    assert items
    assert all(item["scope"] == "task" for item in items)
    assert any(item["memory_type"] == "goal" for item in items)
    assert not any(item["scope"] == "user" for item in items)


def test_similar_breakfast_memory_is_not_relevant_to_agri_task():
    memories = [
        {"id": "breakfast", "scope": "user", "memory_type": "preference", "content": "用户喜欢中式早餐和生煎包", "confidence": .95, "importance": .5, "status": "active"},
        {"id": "rice", "scope": "task", "memory_type": "fact", "content": "当前任务作物：水稻", "confidence": .82, "importance": .75, "status": "active"},
    ]
    result = select_relevant_memories(memories, "水稻分蘖期如何防治稻飞虱")
    assert "rice" in {item["id"] for item in result["used"]}
    assert "breakfast" in {item["id"] for item in result["skipped"]}


def test_expired_memory_is_hard_skipped_and_keys_are_deterministic():
    expired = {"id": "old", "scope": "task", "memory_type": "fact", "content": "当前任务作物：水稻", "confidence": 1, "importance": 1, "expires_at": datetime.utcnow() - timedelta(days=1), "status": "active"}
    assert score_memory_relevance(expired, "水稻") == 0
    assert normalize_memory_key(" 当前任务作物：水稻 ") == normalize_memory_key("当前任务作物-水稻")


def test_new_goal_has_priority_over_old_preference_by_relevance():
    memories = [
        {"id": "pref", "scope": "user", "memory_type": "preference", "content": "用户偏好少用农药", "confidence": .95, "importance": .5, "status": "active"},
        {"id": "goal", "scope": "task", "memory_type": "goal", "content": "当前任务目标：控制稻飞虱扩散", "confidence": .9, "importance": .95, "status": "active"},
    ]
    result = select_relevant_memories(memories, "当前目标是控制稻飞虱扩散")
    assert result["used"][0]["id"] == "goal"


def test_temporal_reference_is_preserved_for_reasoning():
    resolved = resolve_temporal_reference("上周江西早稻出现叶片黄化")
    assert resolved["temporal_label"] == "last_week"
    assert resolved["event_at"] < datetime.utcnow()


def test_authority_and_task_type_outweigh_old_preference():
    memories = [
        {"id": "pref", "scope": "user", "memory_type": "preference", "content": "偏好少用药", "confidence": 1, "importance": 1, "authority_score": .2, "status": "active"},
        {"id": "fact", "scope": "task", "memory_type": "constraint", "content": "当前任务约束：必须遵守登记标签", "confidence": .9, "importance": .9, "authority_score": .9, "status": "active"},
    ]
    result = select_relevant_memories(memories, "当前病虫害防治必须遵守登记标签")
    assert result["used"][0]["id"] == "fact"


def test_unverified_user_memory_is_hard_gated():
    memory = {"scope": "user", "memory_type": "preference", "content": "长期偏好：红壤地块", "verification_status": "pending", "confidence": 1, "importance": 1}
    assert score_memory_relevance(memory, "红壤地块怎么施肥") == 0


def test_passive_extraction_is_pending_and_active_extraction_asks_for_context():
    candidates = extract_candidate_memories("水稻叶片发黄怎么防治？", "t-2")
    assert candidates == []
    questions = propose_active_memory_questions("水稻叶片发黄怎么防治？", candidates)
    assert questions
    assert any("地区" in question for question in questions)


def test_explicit_passive_memory_carries_verification_contract():
    candidates = extract_candidate_memories("我在赣州种植脐橙", "t-3")
    assert candidates
    assert all(item["extraction_mode"] == "passive" for item in candidates)
    assert all(item["verification_status"] == "pending" for item in candidates)
