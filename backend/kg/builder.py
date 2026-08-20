"""
CropWise 知识图谱导入器
=========================

从种子数据和农业文档构建 Neo4j 知识图谱。
支持增量导入、去重和版本管理。
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional
from kg.connection import neo4j_conn, create_entity, create_relation
from kg.schema import (
    SEED_CROPS, SEED_DISEASES, SEED_PESTS, SEED_CHEMICALS,
    SEED_SYMPTOMS, SEED_GROWTH_STAGES, SEED_REGIONS,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self):
        self.conn = neo4j_conn
        self._stats = {
            "entities_created": 0,
            "relations_created": 0,
            "errors": 0,
        }

    def build_seed_data(self) -> Dict[str, Any]:
        """导入种子数据"""
        logger.info("开始导入种子数据到 Neo4j...")

        # 1. 创建作物实体
        for crop in SEED_CROPS:
            if create_entity("Crop", crop["name"], crop):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 2. 创建病害实体
        for disease in SEED_DISEASES:
            if create_entity("Disease", disease["name"], disease):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 3. 创建虫害实体
        for pest in SEED_PESTS:
            if create_entity("Pest", pest["name"], pest):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 4. 创建农药实体
        for chem in SEED_CHEMICALS:
            if create_entity("Chemical", chem["name"], chem):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 5. 创建症状实体
        for sym in SEED_SYMPTOMS:
            if create_entity("Symptom", sym["name"], sym):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 6. 创建生育期实体
        for stage in SEED_GROWTH_STAGES:
            if create_entity("GrowthStage", stage["name"], stage):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        # 7. 创建地区实体
        for region in SEED_REGIONS:
            if create_entity("Region", region["name"], region):
                self._stats["entities_created"] += 1
            else:
                self._stats["errors"] += 1

        logger.info(f"种子实体导入完成: {self._stats}")
        return self._stats

    def build_seed_relations(self) -> Dict[str, Any]:
        """导入种子关系"""
        logger.info("开始导入种子关系...")

        # ---- 水稻病虫害关系 ----
        rice_pests = [
            ("水稻", "Disease", "稻瘟病", {}),
            ("水稻", "Disease", "纹枯病", {}),
            ("水稻", "Disease", "白叶枯病", {}),
            ("水稻（早稻）", "Disease", "稻瘟病", {"season": "早稻"}),
            ("水稻（晚稻）", "Disease", "稻瘟病", {"season": "晚稻"}),
            ("水稻", "Pest", "稻飞虱", {}),
            ("水稻", "Pest", "稻纵卷叶螟", {}),
            ("水稻", "Pest", "二化螟", {}),
            ("水稻", "Pest", "三化螟", {}),
            ("水稻", "Pest", "蚜虫", {}),
        ]
        for crop_name, target_label, target_name, props in rice_pests:
            if create_relation("Crop", crop_name, target_label, target_name, "SUSCEPTIBLE_TO", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 小麦病虫害关系 ----
        wheat_pests = [
            ("小麦", "Disease", "赤霉病", {}),
            ("小麦", "Disease", "锈病", {}),
            ("小麦", "Pest", "蚜虫", {}),
        ]
        for crop_name, target_label, target_name, props in wheat_pests:
            if create_relation("Crop", crop_name, target_label, target_name, "SUSCEPTIBLE_TO", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 脐橙病虫害关系 ----
        orange_pests = [
            ("赣南脐橙", "Disease", "溃疡病", {}),
            ("赣南脐橙", "Disease", "炭疽病", {}),
            ("赣南脐橙", "Pest", "柑橘木虱", {}),
        ]
        for crop_name, target_label, target_name, props in orange_pests:
            if create_relation("Crop", crop_name, target_label, target_name, "SUSCEPTIBLE_TO", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 药剂防治关系 ----
        pest_controls = [
            ("稻飞虱", "Pest", "Chemical", "吡虫啉", {}),
            ("稻飞虱", "Pest", "Chemical", "噻虫嗪", {}),
            ("稻瘟病", "Disease", "Chemical", "春雷霉素", {}),
            ("纹枯病", "Disease", "Chemical", "井冈霉素", {}),
            ("锈病", "Disease", "Chemical", "戊唑醇", {}),
            ("锈病", "Disease", "Chemical", "三唑酮", {}),
            ("稻纵卷叶螟", "Pest", "Chemical", "氯虫苯甲酰胺", {}),
            ("二化螟", "Pest", "Chemical", "氯虫苯甲酰胺", {}),
            ("蚜虫", "Pest", "Chemical", "吡虫啉", {}),
            ("蚜虫", "Pest", "Chemical", "噻虫嗪", {}),
            ("红蜘蛛", "Pest", "Chemical", "阿维菌素", {}),
            ("溃疡病", "Disease", "Chemical", "代森锰锌", {}),
        ]
        for source_name, source_label, target_label, target_name, props in pest_controls:
            if create_relation(source_label, source_name, target_label, target_name, "CONTROLLED_BY", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 作物适宜地区 ----
        crop_regions = [
            ("水稻", "江西省", {"season": "双季稻"}),
            ("水稻（早稻）", "江西省", {"season": "早稻"}),
            ("水稻（晚稻）", "江西省", {"season": "晚稻"}),
            ("水稻", "南昌市", {}),
            ("水稻", "上饶市", {}),
            ("水稻", "吉安市", {}),
            ("水稻", "宜春市", {}),
            ("赣南脐橙", "赣州市", {"specialty": True}),
            ("油菜", "江西省", {"season": "秋播-春收"}),
            ("茶叶", "江西省", {}),
        ]
        for crop_name, region_name, props in crop_regions:
            if create_relation("Crop", crop_name, "Region", region_name, "SUITABLE_FOR_REGION", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 症状-病虫害关联 ----
        symptom_links = [
            ("褐色斑点", "Symptom", "Disease", "稻瘟病", {}),
            ("白穗", "Symptom", "Disease", "纹枯病", {}),
            ("卷叶", "Symptom", "Pest", "稻纵卷叶螟", {}),
            ("虫蛀茎秆", "Symptom", "Pest", "二化螟", {}),
            ("果实溃疡", "Symptom", "Disease", "溃疡病", {}),
            ("叶尖干枯", "Symptom", "Disease", "稻瘟病", {"confidence": "中等"}),
            ("萎蔫", "Symptom", "Disease", "根腐", {"confidence": "低"}),
        ]
        for sym_name, sym_label, target_label, target_name, props in symptom_links:
            if create_relation(sym_label, sym_name, target_label, target_name, "INDICATES", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        # ---- 作物生育期 ----
        crop_stages = [
            ("水稻", "播种期", {}),
            ("水稻", "秧田期", {}),
            ("水稻", "移栽期", {}),
            ("水稻", "分蘖期", {}),
            ("水稻", "拔节期", {}),
            ("水稻", "孕穗期", {}),
            ("水稻", "抽穗期", {}),
            ("水稻", "灌浆期", {}),
            ("水稻", "成熟期", {}),
            ("水稻（早稻）", "播种期", {"calendar": "3月"}),
            ("水稻（早稻）", "分蘖期", {"calendar": "4-5月"}),
            ("水稻（晚稻）", "播种期", {"calendar": "6月"}),
            ("水稻（晚稻）", "分蘖期", {"calendar": "7-8月"}),
        ]
        for crop_name, stage_name, props in crop_stages:
            if create_relation("Crop", crop_name, "GrowthStage", stage_name, "HAS_STAGE", props):
                self._stats["relations_created"] += 1
            else:
                self._stats["errors"] += 1

        logger.info(f"种子关系导入完成: {self._stats}")
        return self._stats

    def build_full(self) -> Dict[str, Any]:
        """完整构建知识图谱"""
        logger.info("=== 开始完整构建农业知识图谱 ===")
        self._stats = {"entities_created": 0, "relations_created": 0, "errors": 0}

        self.build_seed_data()
        self.build_seed_relations()

        logger.info(f"=== 知识图谱构建完成 ===")
        logger.info(f"  实体: {self._stats['entities_created']}")
        logger.info(f"  关系: {self._stats['relations_created']}")
        logger.info(f"  错误: {self._stats['errors']}")

        return self._stats


# 全局实例
kg_builder = KnowledgeGraphBuilder()


def build_knowledge_graph() -> Dict[str, Any]:
    """一键构建知识图谱"""
    return kg_builder.build_full()
