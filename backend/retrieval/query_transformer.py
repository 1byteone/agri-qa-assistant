# -*- coding: utf-8 -*-
"""
QueryTransformer — 查询改写与子查询分解。

提供以下能力：
- 查询改写：补充隐含信息、规范化术语
- 子查询分解：复合问题拆分为独立子查询
- 同义词扩展：农业术语双语扩展
- Multi-Query 分解：复杂问题拆分为多个可独立检索的子查询
"""
from __future__ import annotations
import re
import logging
from typing import Dict, List, Optional, Tuple

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

# ── Multi-Query 分解规则 ─────────────────────────────────────

# 复合意图关键词（出现时触发分解）
COMPOSITE_INTENT_KEYWORDS = [
    # 症状 + 行动
    (r"(?:叶[片尖]|茎|根|穗|果).{0,10}(?:干枯|发黄|斑点|卷曲|腐烂)", "symptom"),
    (r"(?:怎么|如何|应该).{0,6}(?:防治|治疗|管理|处理)", "action"),
    # 天气 + 农事
    (r"(?:高温|暴雨|寒潮|干旱|连续阴雨)", "weather"),
    (r"(?:什么时候|几月|播期|农时)", "timing"),
    # 施肥 + 药剂
    (r"(?:施肥|追肥|肥料|用量)", "fertilizer"),
    (r"(?:药剂|农药|喷药|用药)", "pesticide"),
    # 地区 + 作物
    (r"(?:南昌|赣州|上饶|吉安|宜春|抚州|九江)", "region"),
    (r"(?:水稻|油菜|脐橙|小麦|玉米|蔬菜)", "crop"),
]

# 子查询模板
SUBQUERY_TEMPLATES = {
    "symptom": "{crop}{stage}出现{symptom}的可能原因和鉴别方法",
    "action": "{crop}{symptom}情况下应该采取什么防治措施",
    "weather": "{region}{crop}{stage}遇到{weather}如何管理",
    "timing": "{region}{crop}{stage}的{timing}安排",
    "fertilizer": "{crop}{stage}的施肥方案和用量",
    "pesticide": "{crop}{pest_disease}的登记药剂和安全使用",
    "region": "{region}{crop}的种植技术和管理要点",
    "crop": "{crop}的栽培管理和病虫害防治",
}


class QueryTransformer:
    """查询改写 + 子查询分解 + Multi-Query 分解。

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

    def multi_query(
        self,
        query: str,
        context: Optional[Dict] = None,
    ) -> Tuple[List[str], Dict]:
        """
        Multi-Query 分解：将复杂农业问题分解为多个可独立检索的子查询。

        分解策略：
        1. 规则分解：基于关键词模式识别复合意图
        2. 场景补全：根据提取的实体补全子查询
        3. 去重排序：确保子查询多样性

        Returns
        -------
        (subqueries, trace) : tuple
            子查询列表和 trace 信息。
        """
        text = (query or "").strip()
        if not text:
            return [query], {"strategy": "empty", "subqueries": []}

        trace = {
            "original_query": text,
            "detected_intents": [],
            "extracted_entities": {},
            "strategy": "multi_query",
        }

        # 1. 提取实体（作物/地区/阶段/症状）
        entities = self._extract_entities(text)
        trace["extracted_entities"] = entities

        # 2. 检测复合意图
        intents = self._detect_intents(text)
        trace["detected_intents"] = intents

        # 3. 生成子查询
        subqueries = []

        # 策略 A：基于意图分解
        if len(intents) >= 2:
            for intent_type in intents[:self.max_subqueries]:
                sq = self._generate_subquery(intent_type, entities, text)
                if sq and sq not in subqueries:
                    subqueries.append(sq)

        # 策略 B：如果意图不够，按连接词分解
        if len(subqueries) < 2:
            decomposed = self.decompose(text)
            for sq in decomposed:
                if sq not in subqueries:
                    subqueries.append(sq)

        # 策略 C：补全缺失维度
        if len(subqueries) < 2 and entities:
            if "crop" in entities and "region" not in entities:
                subqueries.append(f"江西省{entities['crop']}的种植技术")
            if "crop" in entities and "stage" not in entities:
                subqueries.append(f"{entities['crop']}的生育期管理要点")

        # 确保至少有一个子查询
        if not subqueries:
            subqueries = [text]

        subqueries = subqueries[:self.max_subqueries]
        trace["subqueries"] = subqueries
        trace["subquery_count"] = len(subqueries)

        return subqueries, trace

    def _extract_entities(self, text: str) -> Dict[str, str]:
        """从查询中提取实体"""
        entities = {}

        # 作物
        crops = ["水稻", "早稻", "晚稻", "双季稻", "小麦", "玉米", "油菜", "赣南脐橙", "脐橙", "蔬菜", "大豆", "棉花"]
        for crop in crops:
            if crop in text:
                entities["crop"] = crop
                break

        # 地区
        regions = ["江西省", "南昌", "赣州", "上饶", "吉安", "宜春", "抚州", "九江", "萍乡", "景德镇", "新余", "鹰潭"]
        for region in regions:
            if region in text:
                entities["region"] = region
                break

        # 生育期
        stages = ["播种期", "秧田期", "移栽期", "分蘖期", "拔节期", "孕穗期", "抽穗期", "灌浆期", "成熟期",
                   "苗期", "蕾薹期", "花期", "膨果期", "采收期"]
        for stage in stages:
            if stage in text:
                entities["stage"] = stage
                break

        # 症状
        symptoms = ["叶尖干枯", "叶片黄化", "褐色斑点", "白穗", "倒伏", "卷叶", "虫蛀茎秆",
                     "果实溃疡", "根腐", "萎蔫", "发黄", "斑点"]
        for symptom in symptoms:
            if symptom in text:
                entities["symptom"] = symptom
                break

        # 病虫害
        pests = ["稻飞虱", "稻纵卷叶螟", "二化螟", "蚜虫", "红蜘蛛", "柑橘木虱"]
        for pest in pests:
            if pest in text:
                entities["pest_disease"] = pest
                break

        diseases = ["稻瘟病", "纹枯病", "白叶枯病", "赤霉病", "锈病", "溃疡病", "炭疽病"]
        for disease in diseases:
            if disease in text:
                entities["pest_disease"] = disease
                break

        return entities

    def _detect_intents(self, text: str) -> List[str]:
        """检测查询中的复合意图"""
        intents = []
        seen = set()
        for pattern, intent_type in COMPOSITE_INTENT_KEYWORDS:
            if re.search(pattern, text) and intent_type not in seen:
                intents.append(intent_type)
                seen.add(intent_type)
        return intents

    def _generate_subquery(
        self,
        intent_type: str,
        entities: Dict[str, str],
        original: str,
    ) -> str:
        """根据意图类型和提取的实体生成子查询"""
        crop = entities.get("crop", "作物")
        region = entities.get("region", "江西")
        stage = entities.get("stage", "")
        symptom = entities.get("symptom", "")
        pest_disease = entities.get("pest_disease", "")

        template = SUBQUERY_TEMPLATES.get(intent_type)
        if not template:
            return ""

        sq = template.format(
            crop=crop,
            region=region,
            stage=stage if stage else "",
            symptom=symptom if symptom else "",
            weather="异常天气",
            timing="时间安排",
            pest_disease=pest_disease if pest_disease else "",
        )
        # 清理空占位
        sq = re.sub(r"\s+", " ", sq).strip()
        sq = re.sub(r"的\s+(的|和|与)", " ", sq)
        return sq

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
