# -*- coding: utf-8 -*-
"""
QueryRouter — 查询意图分类与路由。

基于规则 + 关键词的意图分类器，将用户查询路由到不同检索路径：
- RAG_DIRECT: 作物+病害明确，直接检索
- RAG_DECOMPOSED: 复合问题，需分解后检索
- TOOL_FIRST: 天气/日期查询，先调工具
- GENERAL: 通用回答（由 domain_guard 拦截非农业问题）
"""
from __future__ import annotations
import re
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Route(Enum):
    """查询路由类型。"""
    RAG_DIRECT = "rag_direct"              # 直接检索
    RAG_DECOMPOSED = "rag_decomposed"      # 需分解后检索
    TOOL_FIRST = "tool_first"             # 先调工具再检索
    GENERAL = "general"                   # 通用回答


# ── 农业实体词典 ─────────────────────────────────────────────

# 常见作物名
CROP_NAMES = (
    "水稻|稻|小麦|麦|玉米|苞谷|油菜|花生|大豆|棉花|红薯|马铃薯|土豆|"
    "柑橘|脐橙|苹果|梨|桃|葡萄|蔬菜|番茄|辣椒|黄瓜|白菜|茄子|"
    "柑|橙|柚|橘|橙子|橘子|柚子|脐橙|赣南脐橙|"
    "双季稻|早稻|晚稻|中稻|杂交稻|超级稻|再生稻"
)

# 常见病害名
PEST_DISEASE_NAMES = (
    "稻飞虱|纹枯病|稻瘟病|白叶枯病|螟虫|二化螟|三化螟|"
    "条锈病|赤霉病|白粉病|蚜虫|红蜘蛛|"
    "玉米螟|草地贪夜蛾|粘虫|"
    "柑橘黄龙病|溃疡病|炭疽病|"
    "蚜虫|蓟马|粉虱|"
    "根腐病|枯萎病|病毒病"
)

# 诊断关键词
DIAGNOSIS_KEYWORDS = "什么病|什么虫|怎么了|怎么治|怎么防|如何防治|怎么防治|如何处理|如何解决|症状|发病|感染|危害|虫害|病害|疫情"

# 时间/天气关键词
TIME_WEATHER_KEYWORDS = "什么时候|什么时候|几天|多久|第几天|今天|明天|本周|近期|最近|去年|去年|天气|气温|降雨|降水|霜冻|寒潮|高温|干旱|暴雨|积温|播期|生育期|农时"

# 工具调用关键词
TOOL_KEYWORDS = "天气|气温|降雨|降水|霜冻|寒潮|高温|干旱|暴雨|积温|日期|时间|今天|明天|后天|本周|当前日期|当前时间"


class QueryRouter:
    """查询意图分类器 → 路由到不同检索路径。

    规则优先级：
    1. TOOL_FIRST: 明确的天气/日期查询
    2. RAG_DIRECT: 作物+病害/症状明确
    3. RAG_DECOMPOSED: 含疑问词的复合问题
    4. GENERAL: 默认路由
    """

    def __init__(self):
        # 预编译正则
        self._crop_re = re.compile(f"({CROP_NAMES})", re.IGNORECASE)
        self._pest_re = re.compile(f"({PEST_DISEASE_NAMES})", re.IGNORECASE)
        self._diagnosis_re = re.compile(f"({DIAGNOSIS_KEYWORDS})", re.IGNORECASE)
        self._time_re = re.compile(f"({TIME_WEATHER_KEYWORDS})", re.IGNORECASE)
        self._tool_re = re.compile(f"({TOOL_KEYWORDS})", re.IGNORECASE)

    def route(self, query: str) -> Route:
        """将查询路由到合适的检索路径。

        Parameters
        ----------
        query : str
            用户查询文本。

        Returns
        -------
        Route
            路由决策。
        """
        text = (query or "").strip()
        if not text:
            return Route.GENERAL

        # 1. 工具优先：明确的天气/日期查询
        if self._tool_re.search(text):
            # 但如果同时有作物+病害，仍然优先 RAG
            if not (self._crop_re.search(text) and self._pest_re.search(text)):
                return Route.TOOL_FIRST

        # 2. 直接检索：作物+病害/症状明确
        has_crop = bool(self._crop_re.search(text))
        has_pest = bool(self._pest_re.search(text))
        has_diagnosis = bool(self._diagnosis_re.search(text))

        if has_crop and (has_pest or has_diagnosis):
            return Route.RAG_DIRECT

        # 3. 分解检索：含疑问词的复合问题
        if re.search(r"怎么|如何|什么时候|多少|哪些|为什么|能不能|可以", text):
            return Route.RAG_DECOMPOSED

        # 4. 有作物名但无明确诊断
        if has_crop:
            return Route.RAG_DECOMPOSED

        return Route.GENERAL

    def classify_scenario(self, query: str) -> Optional[str]:
        """场景分类：诊断/施肥/日历/政策/边界。

        Parameters
        ----------
        query : str
            用户查询文本。

        Returns
        -------
        str or None
            场景类型：diagnosis/fertilizer/calendar/policy/boundary，或 None。
        """
        text = (query or "").lower()

        if re.search(r"政策|补贴|保险|法规|标准|规范|登记|文件|编号", text):
            return "policy"
        if re.search(r"施肥|灌溉|追肥|底肥|肥料|氮|磷|钾|复合肥|有机肥|叶面肥|水肥", text):
            return "fertilizer"
        if re.search(r"什么时候|播期|播种|收获|农时|生育期|日历|节气|几月", text):
            return "calendar"
        if re.search(r"什么病|什么虫|怎么治|怎么防|如何防治|症状|发病|感染|虫害|病害|识别|诊断", text):
            return "diagnosis"
        return None

    def get_search_hints(self, query: str, scenario: Optional[str] = None) -> dict:
        """根据路由和场景生成检索提示。

        Parameters
        ----------
        query : str
            用户查询。
        scenario : str, optional
            场景分类结果。

        Returns
        -------
        dict
            包含 strategy_boost, category_filter, metadata_filter 等检索提示。
        """
        scenario = scenario or self.classify_scenario(query)
        hints: dict = {}

        if scenario == "diagnosis":
            hints["strategy_boost"] = "pest"
            hints["category_filter"] = ["pest", "crop"]
        elif scenario == "fertilizer":
            hints["strategy_boost"] = "fertilizer"
            hints["category_filter"] = ["fertilizer", "soil"]
        elif scenario == "calendar":
            hints["strategy_boost"] = "temporal"
            hints["category_filter"] = ["crop"]
        elif scenario == "policy":
            hints["strategy_boost"] = "metadata"
            hints["category_filter"] = ["policy"]

        # 提取作物名
        crop_match = self._crop_re.search(query)
        if crop_match:
            hints["crop"] = crop_match.group(1)

        # 提取病害名
        pest_match = self._pest_re.search(query)
        if pest_match:
            hints["pest"] = pest_match.group(1)

        return hints


# 全局单例
query_router = QueryRouter()
