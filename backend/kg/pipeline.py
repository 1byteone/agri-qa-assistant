"""
CropWise 知识图谱构建 Pipeline
================================

从农业文档自动抽取实体和关系，构建 Neo4j 知识图谱。

Pipeline 流程：
  文档 → 文档解析 → 分块 → 实体识别(NER) → 关系抽取(RE) → 知识融合 → Neo4j 导入

支持：
- LLM 驱动的 Few-Shot NER + RE
- 批量处理和增量更新
- 实体去重和属性合并
- 质量评估和人工审核队列

参考：
- Crop GraphRAG (Frontiers in Plant Science, 2026)
- Autonomous construction of crop pest and disease knowledge graphs via LLM-driven expert modeling
"""

from __future__ import annotations
import json
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================
# Prompt 模板
# ============================================================

NER_PROMPT_TEMPLATE = """你是一个农业领域实体识别专家。请从以下文本中识别出所有农业实体。

## 实体类型
- Crop（作物）：水稻、小麦、玉米、油菜、脐橙、蔬菜等
- Disease（病害）：稻瘟病、纹枯病、白叶枯病、锈病等
- Pest（虫害）：稻飞虱、蚜虫、螟虫、红蜘蛛等
- Chemical（农药）：吡虫啉、噻虫嗪、戊唑醇等
- Fertilizer（肥料）：尿素、磷酸二氢钾、复合肥等
- Variety（品种）：隆两优1988、赣南脐橙等
- Region（地区）：江西省、南昌市、赣州市等
- GrowthStage（生育期）：分蘖期、抽穗期、灌浆期等
- Symptom（症状）：叶片黄化、褐色斑点、白穗等
- Measure（技术措施）：测土配方、节水灌溉、浅水勤灌等

## 输入文本
{text}

## 输出格式（JSON 数组）
```json
[
  {"type": "Crop", "name": "水稻", "properties": {}},
  {"type": "Disease", "name": "稻瘟病", "properties": {"pathogen": "稻瘟病菌"}},
  {"type": "Chemical", "name": "春雷霉素", "properties": {"target_disease": "稻瘟病"}}
]
```

只输出 JSON 数组，不要其他内容。"""


RE_PROMPT_TEMPLATE = """你是一个农业领域关系抽取专家。请从以下文本和实体列表中抽取实体之间的关系。

## 实体列表
{entities}

## 关系类型
- SUSCEPTIBLE_TO：作物易感病虫害（Crop → Disease/Pest）
- CONTROLLED_BY：病虫害被药剂防治（Disease/Pest → Chemical/Measure）
- APPLIES_TO：农药适用于作物（Chemical → Crop）
- SUITABLE_FOR_REGION：作物适宜地区（Crop → Region）
- HAS_STAGE：作物生育期（Crop → GrowthStage）
- INDICATES：症状指示病虫害（Symptom → Disease/Pest）
- CAUSES_SYMPTOM：病虫害导致症状（Disease/Pest → Symptom）
- RESISTS：品种抗性（Variety → Disease/Pest）
- MEASURE_AT_STAGE：措施适用生育期（Measure → GrowthStage）

## 输入文本
{text}

## 输出格式（JSON 数组）
```json
[
  {"source": "水稻", "source_type": "Crop", "target": "稻瘟病", "target_type": "Disease", "relation": "SUSCEPTIBLE_TO", "properties": {}},
  {"source": "稻瘟病", "source_type": "Disease", "target": "春雷霉素", "target_type": "Chemical", "relation": "CONTROLLED_BY", "properties": {}}
]
```

只输出 JSON 数组，不要其他内容。"""


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ExtractedEntity:
    """抽取的实体"""
    name: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class ExtractedRelation:
    """抽取的关系"""
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class ExtractionResult:
    """抽取结果"""
    document_id: str
    entities: List[ExtractedEntity]
    relations: List[ExtractedRelation]
    raw_text: str
    extraction_time_ms: float = 0.0
    model_used: str = ""
    errors: List[str] = field(default_factory=list)


# ============================================================
# 知识图谱构建 Pipeline
# ============================================================

class KGBuildPipeline:
    """知识图谱构建 Pipeline"""

    def __init__(
        self,
        llm_call_fn=None,
        max_chunk_size: int = 2000,
        batch_size: int = 5,
    ):
        """
        初始化 Pipeline。

        Args:
            llm_call_fn: LLM 调用函数，签名 (prompt: str) -> str
            max_chunk_size: 最大分块大小
            batch_size: 批量处理大小
        """
        self.llm_call_fn = llm_call_fn
        self.max_chunk_size = max_chunk_size
        self.batch_size = batch_size
        self._stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "relations_extracted": 0,
            "entities_deduplicated": 0,
            "errors": 0,
        }

    def process_document(
        self,
        text: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        处理单个文档。

        Args:
            text: 文档文本
            document_id: 文档 ID（可选）
            metadata: 文档元数据

        Returns:
            ExtractionResult
        """
        if not document_id:
            document_id = hashlib.sha256(text[:500].encode()).hexdigest()[:12]

        start_time = time.perf_counter()
        all_entities: List[ExtractedEntity] = []
        all_relations: List[ExtractedRelation] = []
        errors: List[str] = []

        # 1. 分块
        chunks = self._split_text(text)
        logger.info(f"文档 {document_id} 分为 {len(chunks)} 个块")

        # 2. 对每个块进行 NER + RE
        for i, chunk in enumerate(chunks):
            try:
                entities = self._extract_entities(chunk, document_id)
                all_entities.extend(entities)

                relations = self._extract_relations(chunk, entities, document_id)
                all_relations.extend(relations)
            except Exception as e:
                error_msg = f"块 {i} 处理失败: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
                self._stats["errors"] += 1

        # 3. 去重
        deduplicated_entities = self._deduplicate_entities(all_entities)
        deduplicated_relations = self._deduplicate_relations(all_relations)

        self._stats["documents_processed"] += 1
        self._stats["entities_extracted"] += len(all_entities)
        self._stats["relations_extracted"] += len(all_relations)
        self._stats["entities_deduplicated"] += len(all_entities) - len(deduplicated_entities)

        extraction_time = (time.perf_counter() - start_time) * 1000

        return ExtractionResult(
            document_id=document_id,
            entities=deduplicated_entities,
            relations=deduplicated_relations,
            raw_text=text[:1000],
            extraction_time_ms=round(extraction_time, 2),
            errors=errors,
        )

    def process_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[ExtractionResult]:
        """
        批量处理文档。

        Args:
            documents: 文档列表，每个为 dict，需包含 "text" 字段

        Returns:
            ExtractionResult 列表
        """
        results = []
        for doc in documents:
            text = doc.get("text", "")
            doc_id = doc.get("id")
            metadata = doc.get("metadata", {})
            if text:
                result = self.process_document(text, doc_id, metadata)
                results.append(result)
        return results

    def import_to_neo4j(
        self,
        results: List[ExtractionResult],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        将抽取结果导入 Neo4j。

        Args:
            results: 抽取结果列表
            dry_run: 试运行（不实际写入）

        Returns:
            导入统计
        """
        if dry_run:
            return {
                "dry_run": True,
                "total_entities": sum(len(r.entities) for r in results),
                "total_relations": sum(len(r.relations) for r in results),
            }

        try:
            from kg.connection import neo4j_conn, create_entity, create_relation

            import_stats = {"entities_created": 0, "relations_created": 0, "errors": 0}

            for result in results:
                for entity in result.entities:
                    try:
                        props = dict(entity.properties)
                        if create_entity(entity.entity_type, entity.name, props):
                            import_stats["entities_created"] += 1
                        else:
                            import_stats["errors"] += 1
                    except Exception as e:
                        logger.warning(f"实体导入失败: {entity.name}: {e}")
                        import_stats["errors"] += 1

                for rel in result.relations:
                    try:
                        if create_relation(
                            rel.source_type, rel.source_name,
                            rel.target_type, rel.target_name,
                            rel.relation_type, rel.properties,
                        ):
                            import_stats["relations_created"] += 1
                        else:
                            import_stats["errors"] += 1
                    except Exception as e:
                        logger.warning(f"关系导入失败: {rel.source_name}->{rel.target_name}: {e}")
                        import_stats["errors"] += 1

            return import_stats
        except ImportError:
            logger.error("Neo4j 驱动未安装，无法导入")
            return {"error": "neo4j_import_unavailable"}

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return dict(self._stats)

    # ---- 内部方法 ----

    def _split_text(self, text: str) -> List[str]:
        """文本分块"""
        if not text:
            return []

        # 按段落分割
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 1 <= self.max_chunk_size:
                current_chunk = f"{current_chunk}\n{para}" if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text[:self.max_chunk_size]]

    def _extract_entities(self, text: str, document_id: str) -> List[ExtractedEntity]:
        """从文本中抽取实体"""
        if not self.llm_call_fn:
            # 无 LLM 时使用规则抽取
            return self._rule_based_ner(text)

        prompt = NER_PROMPT_TEMPLATE.format(text=text)
        try:
            response = self.llm_call_fn(prompt)
            entities_data = self._parse_json_response(response)
            return [
                ExtractedEntity(
                    name=item["name"],
                    entity_type=item["type"],
                    properties=item.get("properties", {}),
                    source_text=text[:200],
                )
                for item in entities_data
                if "name" in item and "type" in item
            ]
        except Exception as e:
            logger.warning(f"LLM NER 失败: {e}")
            return self._rule_based_ner(text)

    def _extract_relations(
        self,
        text: str,
        entities: List[ExtractedEntity],
        document_id: str,
    ) -> List[ExtractedRelation]:
        """从文本中抽取关系"""
        if not self.llm_call_fn:
            return self._rule_based_re(text, entities)

        entities_str = json.dumps(
            [{"name": e.name, "type": e.entity_type} for e in entities],
            ensure_ascii=False,
        )
        prompt = RE_PROMPT_TEMPLATE.format(entities=entities_str, text=text)
        try:
            response = self.llm_call_fn(prompt)
            relations_data = self._parse_json_response(response)
            return [
                ExtractedRelation(
                    source_name=item["source"],
                    source_type=item["source_type"],
                    target_name=item["target"],
                    target_type=item["target_type"],
                    relation_type=item["relation"],
                    properties=item.get("properties", {}),
                    source_text=text[:200],
                )
                for item in relations_data
                if all(k in item for k in ["source", "target", "relation"])
            ]
        except Exception as e:
            logger.warning(f"LLM RE 失败: {e}")
            return self._rule_based_re(text, entities)

    def _rule_based_ner(self, text: str) -> List[ExtractedEntity]:
        """基于规则的 NER（无 LLM 时的回退）"""
        from kg.schema import SEED_CROPS, SEED_DISEASES, SEED_PESTS, SEED_CHEMICALS

        entities = []
        text_lower = text.lower()

        for crop in SEED_CROPS:
            if crop["name"] in text:
                entities.append(ExtractedEntity(
                    name=crop["name"], entity_type="Crop",
                    properties=crop, source_text=text[:200],
                ))

        for disease in SEED_DISEASES:
            if disease["name"] in text:
                entities.append(ExtractedEntity(
                    name=disease["name"], entity_type="Disease",
                    properties=disease, source_text=text[:200],
                ))

        for pest in SEED_PESTS:
            if pest["name"] in text:
                entities.append(ExtractedEntity(
                    name=pest["name"], entity_type="Pest",
                    properties=pest, source_text=text[:200],
                ))

        for chem in SEED_CHEMICALS:
            if chem["name"] in text:
                entities.append(ExtractedEntity(
                    name=chem["name"], entity_type="Chemical",
                    properties=chem, source_text=text[:200],
                ))

        return entities

    def _rule_based_re(
        self,
        text: str,
        entities: List[ExtractedEntity],
    ) -> List[ExtractedRelation]:
        """基于规则的关系抽取（无 LLM 时的回退）"""
        relations = []
        entity_names = {e.name: e.entity_type for e in entities}

        # 简单共现规则
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if i >= j:
                    continue

                # Crop - SUSCEPTIBLE_TO - Disease/Pest
                if e1.entity_type == "Crop" and e2.entity_type in ("Disease", "Pest"):
                    if self._check_cooccurrence(text, e1.name, e2.name):
                        relations.append(ExtractedRelation(
                            source_name=e1.name, source_type=e1.entity_type,
                            target_name=e2.name, target_type=e2.entity_type,
                            relation_type="SUSCEPTIBLE_TO",
                            source_text=text[:200],
                        ))

                # Disease/Pest - CONTROLLED_BY - Chemical
                if e1.entity_type in ("Disease", "Pest") and e2.entity_type == "Chemical":
                    if self._check_cooccurrence(text, e1.name, e2.name, window=100):
                        relations.append(ExtractedRelation(
                            source_name=e1.name, source_type=e1.entity_type,
                            target_name=e2.name, target_type=e2.entity_type,
                            relation_type="CONTROLLED_BY",
                            source_text=text[:200],
                        ))

        return relations

    def _check_cooccurrence(
        self,
        text: str,
        entity1: str,
        entity2: str,
        window: int = 200,
    ) -> bool:
        """检查两个实体是否在文本中共现"""
        idx1 = text.find(entity1)
        idx2 = text.find(entity2)
        if idx1 == -1 or idx2 == -1:
            return False
        return abs(idx1 - idx2) <= window

    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的 JSON"""
        # 尝试提取 JSON 块
        import re
        json_match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()
        else:
            # 尝试直接解析
            text = response.strip()

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            # 尝试修复常见问题
            text = text.replace("'", '"')
            try:
                result = json.loads(text)
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                return []

    def _deduplicate_entities(
        self,
        entities: List[ExtractedEntity],
    ) -> List[ExtractedEntity]:
        """实体去重"""
        seen = {}
        for entity in entities:
            key = (entity.entity_type, entity.name)
            if key not in seen:
                seen[key] = entity
            else:
                # 合并属性
                existing = seen[key]
                for k, v in entity.properties.items():
                    if k not in existing.properties:
                        existing.properties[k] = v
        return list(seen.values())

    def _deduplicate_relations(
        self,
        relations: List[ExtractedRelation],
    ) -> List[ExtractedRelation]:
        """关系去重"""
        seen = set()
        unique = []
        for rel in relations:
            key = (rel.source_name, rel.target_name, rel.relation_type)
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        return unique


# ============================================================
# 全局实例
# ============================================================

def get_kg_pipeline(llm_call_fn=None, **kwargs) -> KGBuildPipeline:
    """获取知识图谱构建 Pipeline"""
    return KGBuildPipeline(llm_call_fn=llm_call_fn, **kwargs)
