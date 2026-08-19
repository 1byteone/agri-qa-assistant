# -*- coding: utf-8 -*-
"""
实体抽取引擎 — 从农业文档中抽取实体和关系三元组。

三个阶段：
1. 结构化抽取：从已有 metadata 和 manifest 中直接提取
2. 规则抽取：从文档文本中通过正则和模式匹配提取
3. LLM 辅助抽取：对复杂文档做实体关系联合抽取
"""
from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from graph.schema import (
    EntityType,
    RelationType,
    Entity,
    GraphTriple,
    stable_entity_id,
)
from graph.graph_store import GraphStore

logger = logging.getLogger(__name__)


# ── 农业实体词典 ─────────────────────────────────────────────

# 作物名
CROP_DICT = {
    "水稻": "水稻", "稻": "水稻", "早稻": "早稻", "晚稻": "晚稻", "中稻": "中稻",
    "小麦": "小麦", "麦": "小麦",
    "玉米": "玉米", "苞谷": "玉米",
    "油菜": "油菜", "菜籽": "油菜", "双季稻": "双季稻",
    "赣南脐橙": "赣南脐橙", "脐橙": "赣南脐橙", "柑橘": "柑橘", "橘子": "柑橘", "柑": "柑橘",
    "蔬菜": "蔬菜", "番茄": "番茄", "辣椒": "辣椒", "黄瓜": "黄瓜",
}

# 病害名
DISEASE_DICT = {
    "稻瘟病": "稻瘟病", "稻曲病": "稻曲病", "白叶枯病": "白叶枯病",
    "纹枯病": "纹枯病", "恶苗病": "恶苗病",
    "条锈病": "条锈病", "赤霉病": "赤霉病", "白粉病": "白粉病", "锈病": "锈病",
    "菌核病": "菌核病", "霜霉病": "霜霉病",
    "黄龙病": "黄龙病", "柑橘黄龙病": "柑橘黄龙病",
    "炭疽病": "炭疽病", "溃疡病": "溃疡病",
    "病毒病": "病毒病", "枯萎病": "枯萎病", "根腐病": "根腐病",
}

# 害虫名
PEST_DICT = {
    "稻飞虱": "稻飞虱", "褐飞虱": "褐飞虱", "白背飞虱": "白背飞虱",
    "二化螟": "二化螟", "三化螟": "三化螟", "大螟": "大螟",
    "稻纵卷叶螟": "稻纵卷叶螟",
    "蚜虫": "蚜虫", "麦蚜": "麦蚜",
    "玉米螟": "玉米螟",
    "红蜘蛛": "红蜘蛛", "柑橘红蜘蛛": "柑橘红蜘蛛",
    "潜叶蛾": "潜叶蛾",
    "蓟马": "蓟马", "稻蓟马": "稻蓟马",
    "草地贪夜蛾": "草地贪夜蛾", "粘虫": "粘虫",
}

# 农药名
PESTICIDE_DICT = {
    "吡蚜酮": "吡蚜酮", "噻虫嗪": "噻虫嗪", "吡虫啉": "吡虫啉",
    "氯虫苯甲酰胺": "氯虫苯甲酰胺",
    "三环唑": "三环唑", "井冈霉素": "井冈霉素",
    "腐霉利": "腐霉利", "百菌清": "百菌清",
    "咪鲜胺": "咪鲜胺",
    "石硫合剂": "石硫合剂",
    "赤霉素": "赤霉素", "磷酸二氢钾": "磷酸二氢钾",
    "2,4-D": "2,4-D",
}

# 生育期
GROWTH_STAGE_DICT = {
    "分蘖期": "分蘖期", "孕穗期": "孕穗期", "抽穗扬花期": "抽穗扬花期",
    "抽穗期": "抽穗期", "扬花期": "扬花期", "开花期": "开花期",
    "灌浆期": "灌浆期", "灌浆成熟期": "灌浆成熟期",
    "返青期": "返青期", "拔节期": "拔节期",
    "苗期": "苗期", "秧苗期": "秧苗期",
    "蕾薹期": "蕾薹期", "角果期": "角果期",
    "萌芽期": "萌芽期", "生理落果期": "生理落果期",
    "果实膨大期": "果实膨大期", "果实转色期": "果实转色期",
    "采收期": "采收期", "收获期": "收获期",
    "越冬期": "越冬期", "秋梢期": "秋梢期",
}

# 肥料名
FERTILIZER_DICT = {
    "尿素": "尿素", "氯化钾": "氯化钾", "复合肥": "复合肥",
    "磷酸二氢钾": "磷酸二氢钾", "硼砂": "硼砂", "硼肥": "硼肥",
    "有机肥": "有机肥", "石灰": "石灰",
    "叶面肥": "叶面肥", "断奶肥": "断奶肥",
    "分蘖肥": "分蘖肥", "穗肥": "穗肥", "蕾薹肥": "蕾薹肥",
    "返青肥": "返青肥", "壮果肥": "壮果肥",
}

# 农事操作
PRACTICE_DICT = {
    "晒种": "晒种", "浸种": "浸种", "催芽": "催芽",
    "播种": "播种", "育秧": "育秧",
    "移栽": "移栽", "定植": "定植",
    "追肥": "追肥", "基肥": "基肥",
    "灌溉": "灌溉", "排水": "排水",
    "晒田": "晒田", "中耕": "中耕", "除草": "除草",
    "修剪": "修剪", "涂白": "涂白", "培土": "培土", "壅根": "壅根",
    "清园": "清园", "覆盖": "覆盖", "熏烟": "熏烟",
}

# 症状
SYMPTOM_DICT = {
    "叶片斑点": "叶片斑点", "叶片发黄": "叶片发黄", "叶片枯萎": "叶片枯萎",
    "根部腐烂": "根部腐烂", "茎秆腐烂": "茎秆腐烂",
    "白穗": "白穗", "枯心": "枯心", "枯黄": "枯黄",
    "卷叶": "卷叶", "虫瘿": "虫瘿",
    "落叶": "落叶", "落果": "落果", "裂果": "裂果",
    "霉层": "霉层", "粉状物": "粉状物",
}

# 江西地区
REGION_DICT = {
    "江西": "江西", "江西省": "江西",
    "南昌": "南昌", "赣州": "赣州", "九江": "九江",
    "上饶": "上饶", "吉安": "吉安", "宜春": "宜春",
    "抚州": "抚州", "鹰潭": "鹰潭", "景德镇": "景德镇",
    "萍乡": "萍乡", "新余": "新余",
    "赣南": "赣南", "赣中南": "赣中南", "赣北": "赣北",
}

# 剂量模式
_DOSAGE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:[-~至]\s*\d+(?:\.\d+)?)?\s*"
    r"(?:公斤|千克|kg|克|g|毫升|ml|升|L|立方米|m³|%)\s*"
    r"(?:/\s*(?:亩|公顷|株))?"
)

# 农药+剂量模式
_PESTICIDE_DOSAGE_RE = re.compile(
    r"(\d+%?\s*(?:[一-鿿]{2,10}(?:可湿性粉剂|悬浮剂|水剂|乳油|水分散粒剂|颗粒剂)?))"
    r"\s*(\d+(?:\.\d+)?)\s*(?:克|g|毫升|ml)\s*/\s*亩"
)


class EntityExtractor:
    """实体抽取引擎。

    Parameters
    ----------
    graph_store : GraphStore
        图谱存储实例。
    """

    def __init__(self, graph_store: GraphStore):
        self.graph = graph_store
        # 合并所有词典
        self._entity_dict: Dict[str, Tuple[str, str]] = {}  # name → (entity_type, canonical_name)
        self._build_dict()

    def _build_dict(self) -> None:
        """构建实体词典。"""
        for name, canonical in CROP_DICT.items():
            self._entity_dict[name] = ("crop", canonical)
        for name, canonical in DISEASE_DICT.items():
            self._entity_dict[name] = ("disease", canonical)
        for name, canonical in PEST_DICT.items():
            self._entity_dict[name] = ("pest", canonical)
        for name, canonical in PESTICIDE_DICT.items():
            self._entity_dict[name] = ("pesticide", canonical)
        for name, canonical in GROWTH_STAGE_DICT.items():
            self._entity_dict[name] = ("growth_stage", canonical)
        for name, canonical in FERTILIZER_DICT.items():
            self._entity_dict[name] = ("fertilizer", canonical)
        for name, canonical in PRACTICE_DICT.items():
            self._entity_dict[name] = ("practice", canonical)
        for name, canonical in SYMPTOM_DICT.items():
            self._entity_dict[name] = ("symptom", canonical)
        for name, canonical in REGION_DICT.items():
            self._entity_dict[name] = ("region", canonical)

    def extract_entities(self, text: str) -> List[Entity]:
        """从文本中提取实体。"""
        entities = []
        seen_ids: Set[str] = set()
        for name, (etype, canonical) in self._entity_dict.items():
            if name in text:
                entity = Entity.create(canonical, etype)
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    entities.append(entity)
        return entities

    def extract_triples(self, text: str, source: str = "") -> List[GraphTriple]:
        """从文本中抽取关系三元组。

        Parameters
        ----------
        text : str
            文档文本。
        source : str
            来源标识。

        Returns
        -------
        list of GraphTriple
        """
        triples = []
        entities = self.extract_entities(text)
        entity_map = {e.name: e for e in entities}

        # 规则 1: 病害/害虫 → 作物（"X 是 Y 的病害/害虫"）
        for pest_name in PEST_DICT:
            if pest_name in text:
                # 查找同一段落中的作物
                for crop_name in CROP_DICT:
                    if crop_name in text:
                        pest_entity = entity_map.get(PEST_DICT[pest_name])
                        crop_entity = entity_map.get(CROP_DICT[crop_name])
                        if pest_entity and crop_entity:
                            # 判断是病害还是害虫
                            disease_domain = {v for k, v in DISEASE_DICT.items()}
                            if pest_name in disease_domain:
                                rel = "infects"
                            else:
                                rel = "damages"
                            triples.append(GraphTriple(
                                h=PEST_DICT[pest_name], h_type="pest" if rel == "damages" else "disease",
                                r=rel,
                                t=CROP_DICT[crop_name], t_type="crop",
                                properties={"source": source},
                                source=source,
                            ))

        # 规则 2: 农药 → 靶标（"X 防治 Y"）
        for pesticide_name in PESTICIDE_DICT:
            if pesticide_name in text:
                for pest_name in {**PEST_DICT, **DISEASE_DICT}:
                    if pest_name in text:
                        triples.append(GraphTriple(
                            h=PESTICIDE_DICT[pesticide_name], h_type="pesticide",
                            r="controls",
                            t=PEST_DICT.get(pest_name, DISEASE_DICT.get(pest_name, pest_name)),
                            t_type="pest" if pest_name in PEST_DICT else "disease",
                            properties={"source": source},
                            source=source,
                        ))

        # 规则 3: 生育期 → 农事操作
        for stage_name in GROWTH_STAGE_DICT:
            if stage_name in text:
                for practice_name in PRACTICE_DICT:
                    if practice_name in text:
                        triples.append(GraphTriple(
                            h=PRACTICE_DICT[practice_name], h_type="practice",
                            r="applies_to",
                            t=GROWTH_STAGE_DICT[stage_name], t_type="growth_stage",
                            properties={"source": source},
                            source=source,
                        ))

        # 规则 4: 作物 → 生育期
        for crop_name in CROP_DICT:
            if crop_name in text:
                for stage_name in GROWTH_STAGE_DICT:
                    if stage_name in text:
                        triples.append(GraphTriple(
                            h=GROWTH_STAGE_DICT[stage_name], h_type="growth_stage",
                            r="occurs_in",
                            t=CROP_DICT[crop_name], t_type="crop",
                            properties={"source": source},
                            source=source,
                        ))

        # 规则 5: 农药 → 剂量（从文本中提取使用剂量）
        for pesticide_name in PESTICIDE_DICT:
            if pesticide_name in text:
                for match in _DOSAGE_RE.finditer(text):
                    triples.append(GraphTriple(
                        h=PESTICIDE_DICT[pesticide_name], h_type="pesticide",
                        r="related_to",
                        t=f"剂量_{match.group(0)}", t_type="pesticide",
                        properties={"dosage": match.group(0), "source": source},
                        source=source,
                    ))

        return triples

    def extract_from_document(self, doc_path: str, source: str = "") -> Dict[str, Any]:
        """从文档文件中抽取实体和关系。

        Returns
        -------
        dict
            包含 entities, triples, error 的字典。
        """
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as exc:
            return {"entities": [], "triples": [], "error": str(exc)}

        entities = self.extract_entities(text)
        triples = self.extract_triples(text, source=source or doc_path)

        # 去重
        entity_ids = set()
        unique_entities = []
        for e in entities:
            if e.id not in entity_ids:
                entity_ids.add(e.id)
                unique_entities.append(e)

        triple_ids = set()
        unique_triples = []
        for t in triples:
            tid = f"{t.h}|{t.r}|{t.t}"
            if tid not in triple_ids:
                triple_ids.add(tid)
                unique_triples.append(t)

        return {"entities": unique_entities, "triples": unique_triples, "error": None}

    def ingest_to_graph(self, doc_path: str, source: str = "") -> Dict[str, Any]:
        """抽取文档中的实体和关系并写入图谱。

        Returns
        -------
        dict
            包含 entity_count, triple_count 的统计字典。
        """
        result = self.extract_from_document(doc_path, source=source)
        if result["error"]:
            logger.warning("文档抽取失败: %s", result["error"])
            return {"entity_count": 0, "triple_count": 0, "error": result["error"]}

        for entity in result["entities"]:
            self.graph.add_entity(entity)

        added = 0
        for triple in result["triples"]:
            if self.graph.add_triple(triple):
                added += 1

        logger.info(
            "文档 %s: 抽取 %d 实体, %d 三元组 (新增 %d)",
            source or doc_path,
            len(result["entities"]),
            len(result["triples"]),
            added,
        )
        return {
            "entity_count": len(result["entities"]),
            "triple_count": len(result["triples"]),
            "added_triples": added,
        }