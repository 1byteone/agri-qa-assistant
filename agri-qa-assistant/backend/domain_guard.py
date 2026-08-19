"""Deterministic domain policy for CropWise requests.

The guard runs before retrieval, tool calls, or an LLM request.  It is
intentionally conservative: uncertain requests are routed to clarification
instead of allowing a general-purpose model to answer outside agriculture.
"""
from __future__ import annotations

import re
from typing import Dict, List, TypedDict


class DomainDecision(TypedDict):
    allowed: bool
    category: str
    reason: str


AGRICULTURE_TERMS: tuple[str, ...] = (
    "农业", "农田", "农作", "农时", "农产品", "农技", "农艺", "育种", "品种",
    "作物", "水稻", "早稻", "晚稻", "稻谷", "小麦", "玉米", "油菜", "棉花", "蔬菜", "果树",
    "茶", "甘蔗", "大豆", "花生", "烟草", "马铃薯", "脐橙", "赣南", "果蔬", "采后", "保鲜", "播种", "育苗", "移栽",
    "分蘖", "抽穗", "拔节", "返青", "灌浆", "成熟期", "生育期", "播期", "施肥", "追肥", "底肥",
    "灌溉", "排水", "病虫害", "病害", "虫害", "稻飞虱", "螟虫", "蚜虫", "锈病",
    "霜霉病", "白粉病", "土壤", "酸碱", "盐碱", "测土", "氮磷钾", "农药",
    "植保", "农机", "旋耕机", "收割机", "无人机", "农膜", "大棚", "农业政策",
    "农技站", "产量", "亩产", "田间", "农资", "农产品", "农业气象", "霜冻",
    "agriculture", "crop", "rice", "wheat", "maize", "corn", "soybean", "fertilizer",
    "irrigation", "soil", "pest", "disease", "planting", "farmland", "農業",
)

NON_AGRICULTURE_TERMS: tuple[str, ...] = (
    "java", "python", "javascript", "typescript", "c++", "c#", "sql", "react", "next.js",
    "代码", "编程", "程序", "算法", "开发", "前端", "后端", "接口", "api", "网页",
    "乘法表", "数学题", "数学", "递归", "数据结构", "leetcode", "论文", "小说",
    "游戏", "娱乐", "歌词", "通用翻译", "写邮件", "简历", "股票", "法律咨询",
)

CODE_INTENT = re.compile(r"(写|编写|实现|生成|运行|调试|开发).{0,12}(代码|程序|脚本|java|python|javascript|typescript|c\+\+|sql)", re.I)


def _contains_any(text: str, terms: tuple[str, ...]) -> List[str]:
    return [term for term in terms if term in text]


def classify_query(message: str) -> DomainDecision:
    """Classify a user request against the CropWise agriculture boundary."""
    text = re.sub(r"\s+", " ", (message or "").strip().lower())
    if not text:
        return {"allowed": False, "category": "empty", "reason": "问题不能为空"}

    agriculture_hits = _contains_any(text, AGRICULTURE_TERMS)
    non_agriculture_hits = _contains_any(text, NON_AGRICULTURE_TERMS)
    has_code_intent = bool(CODE_INTENT.search(text))

    # Code generation remains outside the product scope, even when a crop is
    # mentioned. The assistant may explain an agricultural method in prose,
    # but must not become a general programming assistant.
    if has_code_intent or (agriculture_hits and non_agriculture_hits and any(
        term in text for term in ("代码", "编程", "程序", "java", "python", "javascript", "typescript", "c++", "sql")
    )):
        return {
            "allowed": False,
            "category": "unsupported_action",
            "reason": "当前仅提供农业知识咨询，不提供代码、编程或通用软件开发实现",
        }

    if non_agriculture_hits and not agriculture_hits:
        return {
            "allowed": False,
            "category": "non_agriculture",
            "reason": "问题不属于 CropWise 的农业知识服务范围",
        }

    if agriculture_hits:
        return {"allowed": True, "category": "agriculture", "reason": "命中农业知识范围"}

    return {
        "allowed": False,
        "category": "ambiguous",
        "reason": "无法确认问题与农业生产、农技服务或农业资料有关",
    }


def build_domain_rejection(decision: DomainDecision) -> str:
    """Return a stable, user-facing boundary response."""
    return (
        "我是 CropWise 农业知识问答助手，目前只回答农业相关问题，包括作物种植、病虫害防治、"
        "施肥灌溉、土壤管理、农机具、农时、农业气象、农业政策及相关图片与官方资料。\n\n"
        f"你刚才的问题暂不在服务范围内：{decision['reason']}。\n\n"
        "你可以改问：\n"
        "1. 水稻稻飞虱怎么防治？\n"
        "2. 小麦返青期如何追肥？\n"
        "3. 江西早稻什么时候播种？"
    )
