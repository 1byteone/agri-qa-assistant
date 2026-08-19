# -*- coding: utf-8 -*-
"""
QueryTransformer — 查询改写与子查询分解。

提供以下能力：
- 查询改写：补充隐含信息、规范化术语
- 子查询分解：复合问题拆分为独立子查询
- 同义词扩展：农业术语双语扩展
"""
from __future__ import annotations
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 农业术语同义词映射 ───────────────────────────────────────

SYNONYM_MAP: Dict[str, List[str]] = {
    # 病害
    "稻飞虱": ["brown planthopper", "BPH", "飞虱"],
    "条锈病": ["stripe rust", "小麦锈病"],
    "纹枯病": ["sheath blight", "水稻纹枯"],
    "稻瘟病": ["rice blast", "水稻瘟病"],
    "白叶枯病": ["bacterial leaf blight", "水稻白叶枯"],
    "赤霉病": ["Fusarium head blight", "小麦赤霉"],
    "蚜虫": ["aphid", "aphids"],
    "螟虫": ["stem borer", "水稻螟虫"],
    "二化螟": ["Chilo suppressalis", "水稻二化螟"],
    "柑橘黄龙病": ["Huanglongbing", "HLB", "黄龙病"],
    "溃疡病": ["canker", "柑橘溃疡"],
    "炭疽病": ["anthracnose"],
    "草地贪夜蛾": ["fall armyworm", "FAW"],
    # 作物
    "水稻": ["rice", "paddy", "稻"],
    "小麦": ["wheat"],
    "玉米": ["corn", "maize"],
    "油菜": ["rapeseed", "canola"],
    "赣南脐橙": ["Gannan navel orange", "脐橙"],
    "双季稻": ["double-crop rice", "双季"],
    # 术语
    "分蘖": ["tillering", "分蘖期"],
    "返青": ["greening", "返青期"],
    "抽穗": ["heading", "抽穗期"],
    "灌浆": ["grain filling", "灌浆期"],
    "测土配方": ["soil testing formula", "测土配方施肥"],
    "安全间隔期": ["pre-harvest interval", "PHI", "安全间隔"],
}

# 反向映射：英文 → 中文
EN_TO_CN_MAP: Dict[str, str] = {}
for cn_term, en_terms in SYNONYM_MAP.items():
    for en in en_terms:
        EN_TO_CN_MAP[en.lower()] = cn_term

# ── 查询改写规则 ─────────────────────────────────────────────

# 隐含信息补充规则
IMPLICIT_RULES = [
    # 无地区时补充"江西"
    (re.compile(r"^([^地\s]*(?:怎么|如何|防治|治疗|管理))"), r"\1（江西地区）"),
    # 无生育期时补充泛化
    (re.compile(r"^([^生\s]*(?:施肥|追肥|灌溉))"), r"\1（全生育期）"),
]


class QueryTransformer:
    """查询改写 + 子查询分解。

    Parameters
    ----------
    max_subqueries : int
        子查询最大数量。默认 4。
    """

    def __init__(self, max_subqueries: int = 4):
        self.max_subqueries = max_subqueries
        self._synonym_map = SYNONYM_MAP
        self._en_to_cn = EN_TO_CN_MAP

    def rewrite(self, query: str, context: Optional[Dict] = None) -> str:
        """查询改写：补充隐含信息、规范化术语。

        Parameters
        ----------
        query : str
            原始查询。
        context : dict, optional
            上下文信息，可包含 crop, region, stage 等字段。

        Returns
        -------
        str
            改写后的查询。
        """
        text = (query or "").strip()
        if not text:
            return text

        # 1. 规范化术语
        text = self._normalize_terms(text)

        # 2. 补充隐含信息
        if context:
            text = self._enrich_with_context(text, context)

        # 3. 去除冗余
        text = self._remove_redundancy(text)

        return text

    def decompose(self, query: str) -> List[str]:
        """子查询分解：复合问题拆分为独立子查询。

        Parameters
        ----------
        query : str
            原始查询。

        Returns
        -------
        list of str
            子查询列表。
        """
        text = (query or "").strip()
        if not text:
            return []

        # 按中文连接词分割
        parts = re.split(r"[，,；;。？?！!和|以及|还有|同时|另外]", text)
        parts = [p.strip() for p in parts if p.strip()]

        # 去重
        seen = set()
        unique_parts = []
        for part in parts:
            normalized = self._normalize_terms(part)
            if normalized not in seen:
                seen.add(normalized)
                unique_parts.append(normalized)

        # 限制数量
        return unique_parts[: self.max_subqueries]

    def expand_synonyms(self, query: str) -> List[str]:
        """同义词扩展：生成查询的同义词变体。

        Parameters
        ----------
        query : str
            原始查询。

        Returns
        -------
        list of str
            包含同义词变体的查询列表（含原始查询）。
        """
        text = (query or "").strip()
        if not text:
            return [text]

        variants = [text]
        for cn_term, en_terms in self._synonym_map.items():
            if cn_term in text:
                for en in en_terms[:1]:  # 每个术语只取第一个同义词
                    variant = text.replace(cn_term, en)
                    if variant != text:
                        variants.append(variant)
                break  # 每个查询只扩展一个术语

        return variants

    def _normalize_terms(self, text: str) -> str:
        """规范化农业术语：仅对主要为英文的查询进行英→中映射，避免中文内部误替换。"""
        # 统计中文字符比例
        cn_chars = len(re.findall(r"[一-鿿]", text))
        total_chars = max(len(text.strip()), 1)
        # 如果中文字符占比 > 30%，说明已经是中文查询，不做英→中映射
        if cn_chars / total_chars > 0.3:
            return text
        # 英文查询：映射为中文
        for en, cn in self._en_to_cn.items():
            text = re.sub(rf"\b{re.escape(en)}\b", cn, text, flags=re.IGNORECASE)
        return text

    def _enrich_with_context(self, text: str, context: Dict) -> str:
        """用上下文信息补充查询。"""
        # 如果有明确的地区信息但查询中没有，可以考虑补充
        # 但当前策略是不自动补充，避免过度改写
        return text

    def _remove_redundancy(self, text: str) -> str:
        """去除查询中的冗余信息。"""
        # 去除重复词
        text = re.sub(r"(.)\1{2,}", r"\1\1", text)
        # 去除多余空格
        text = re.sub(r"\s+", " ", text)
        return text.strip()


# 全局单例
query_transformer = QueryTransformer()
