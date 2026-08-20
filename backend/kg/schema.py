"""
CropWise 农业知识图谱 Schema 定义
===================================

本模块定义农业知识图谱的实体类型、关系类型和属性结构。
参考文献：
- Crop GraphRAG (Frontiers in Plant Science, 2026)
- AgriKG (DASFAA 2019)
- 中国农科院农业智能知识服务平台

实体类型 (12 类)：
  Crop, Disease, Pest, Chemical, Fertilizer, Variety,
  Region, Policy, Measure, GrowthStage, Symptom, Document

关系类型 (16 类)：
  作物-病害-农药-肥料-品种-地区-政策-措施-生育期-症状-文档之间的语义关系
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


# ============================================================
# 实体类型定义
# ============================================================

@dataclass
class EntitySchema:
    """实体类型 Schema"""
    label: str                    # Neo4j 节点标签
    description: str              # 中文描述
    required_props: List[str]     # 必填属性
    optional_props: List[str]     # 可选属性
    aliases: List[str] = field(default_factory=list)  # 别名（用于实体链接）


# 农业实体类型注册表
ENTITY_TYPES: Dict[str, EntitySchema] = {
    "Crop": EntitySchema(
        label="Crop",
        description="作物",
        required_props=["name"],
        optional_props=["alias", "category", "family", "origin", "growing_season", "description"],
        aliases=["作物", "农作物"],
    ),
    "Disease": EntitySchema(
        label="Disease",
        description="病害",
        required_props=["name"],
        optional_props=["alias", "pathogen", "pathogen_type", "symptoms", "severity", "description"],
        aliases=["病害", "病"],
    ),
    "Pest": EntitySchema(
        label="Pest",
        description="虫害",
        required_props=["name"],
        optional_props=["alias", "taxonomic_order", "damage_stage", "description"],
        aliases=["虫害", "虫", "害虫"],
    ),
    "Chemical": EntitySchema(
        label="Chemical",
        description="农药/化学药剂",
        required_props=["name"],
        optional_props=["alias", "active_ingredient", "chemical_class", "registration_no",
                        "target_pest", "target_disease", "dosage", "safety_interval",
                        "preharvest_interval", "toxicity_class", "description"],
        aliases=["农药", "药剂", "杀虫剂", "杀菌剂", "除草剂"],
    ),
    "Fertilizer": EntitySchema(
        label="Fertilizer",
        description="肥料",
        required_props=["name"],
        optional_props=["alias", "npk_ratio", "type", "application_method", "description"],
        aliases=["肥料", "化肥", "有机肥"],
    ),
    "Variety": EntitySchema(
        label="Variety",
        description="品种",
        required_props=["name"],
        optional_props=["alias", "crop", "breeding_institute", "maturity_group",
                        "yield_potential", "disease_resistance", "description"],
        aliases=["品种", "种子"],
    ),
    "Region": EntitySchema(
        label="Region",
        description="地区/行政区划",
        required_props=["name"],
        optional_props=["alias", "province", "city", "county", "latitude", "longitude",
                        "climate_zone", "soil_type", "description"],
        aliases=["地区", "区域", "省", "市", "县"],
    ),
    "Policy": EntitySchema(
        label="Policy",
        description="农业政策/标准/法规",
        required_props=["policy_id", "name"],
        optional_props=["issuer", "publish_date", "valid_until", "level", "category",
                        "url", "description"],
        aliases=["政策", "标准", "法规", "补贴"],
    ),
    "Measure": EntitySchema(
        label="Measure",
        description="农业技术措施/管理措施",
        required_props=["name"],
        optional_props=["alias", "category", "target_crop", "target_stage",
                        "application_method", "description"],
        aliases=["措施", "技术", "管理", "防治", "栽培"],
    ),
    "GrowthStage": EntitySchema(
        label="GrowthStage",
        description="生育期/生长阶段",
        required_props=["name"],
        optional_props=["alias", "crop", "duration_days", "temperature_range",
                        "key_operations", "description"],
        aliases=["生育期", "生长期", "阶段"],
    ),
    "Symptom": EntitySchema(
        label="Symptom",
        description="症状/表型",
        required_props=["name"],
        optional_props=["alias", "affected_part", "visual_description", "severity", "description"],
        aliases=["症状", "表现", "特征"],
    ),
    "Document": EntitySchema(
        label="Document",
        description="文档/证据来源",
        required_props=["content_hash", "title"],
        optional_props=["source_url", "publisher", "publish_date", "valid_until",
                        "evidence_level", "evidence_scope", "license", "version",
                        "crop", "region", "description"],
        aliases=["文档", "来源", "资料"],
    ),
}


# ============================================================
# 关系类型定义
# ============================================================

@dataclass
class RelationSchema:
    """关系类型 Schema"""
    name: str                    # 关系名称（Cypher 中的类型）
    description: str             # 中文描述
    source_labels: List[str]     # 源实体标签（允许的起始节点）
    target_labels: List[str]     # 目标实体标签（允许的终止节点）
    required_props: List[str]    # 必填属性
    optional_props: List[str]    # 可选属性
    bidirectional: bool = False  # 是否双向


# 农业关系类型注册表
RELATION_TYPES: Dict[str, RelationSchema] = {
    # ---- 作物与病虫害 ----
    "SUSCEPTIBLE_TO": RelationSchema(
        name="SUSCEPTIBLE_TO",
        description="作物易感（某病害/虫害）",
        source_labels=["Crop"],
        target_labels=["Disease", "Pest"],
        required_props=[],
        optional_props=["season", "region_prevalence", "severity_level"],
    ),
    # ---- 病虫害与防治措施 ----
    "CONTROLLED_BY": RelationSchema(
        name="CONTROLLED_BY",
        description="病虫害被（某措施/药剂）防治",
        source_labels=["Disease", "Pest"],
        target_labels=["Chemical", "Measure"],
        required_props=[],
        optional_props=["efficacy", "stage", "dosage", "application_method"],
    ),
    # ---- 农药适用作物 ----
    "APPLIES_TO": RelationSchema(
        name="APPLIES_TO",
        description="农药/肥料适用于（某作物）",
        source_labels=["Chemical", "Fertilizer"],
        target_labels=["Crop"],
        required_props=[],
        optional_props=["dosage", "timing", "method", "registration_no"],
    ),
    # ---- 品种属于作物 ----
    "VARIANT_OF": RelationSchema(
        name="VARIANT_OF",
        description="品种属于（某作物）",
        source_labels=["Variety"],
        target_labels=["Crop"],
        required_props=[],
        optional_props=["maturity", "yield", "resistance"],
    ),
    # ---- 作物适宜种植地区 ----
    "SUITABLE_FOR_REGION": RelationSchema(
        name="SUITABLE_FOR_REGION",
        description="作物适宜种植于（某地区）",
        source_labels=["Crop"],
        target_labels=["Region"],
        required_props=[],
        optional_props=["season", "soil_type", "climate", "area_ha"],
    ),
    # ---- 地区执行政策 ----
    "GOVERNED_BY": RelationSchema(
        name="GOVERNED_BY",
        description="地区执行（某政策）",
        source_labels=["Region"],
        target_labels=["Policy"],
        required_props=[],
        optional_props=["effective_date", "scope"],
    ),
    # ---- 作物关键生育期 ----
    "HAS_STAGE": RelationSchema(
        name="HAS_STAGE",
        description="作物具有（某生育期）",
        source_labels=["Crop"],
        target_labels=["GrowthStage"],
        required_props=[],
        optional_props=["duration_days", "calendar_month", "key_operations"],
    ),
    # ---- 症状与病虫害关联 ----
    "INDICATES": RelationSchema(
        name="INDICATES",
        description="症状指示（某病虫害）",
        source_labels=["Symptom"],
        target_labels=["Disease", "Pest"],
        required_props=[],
        optional_props=["confidence", "differential"],
    ),
    # ---- 作物出现症状 ----
    "SHOWS_SYMPTOM": RelationSchema(
        name="SHOWS_SYMPTOM",
        description="作物出现（某症状）",
        source_labels=["Crop"],
        target_labels=["Symptom"],
        required_props=[],
        optional_props=["stage", "severity", "frequency"],
    ),
    # ---- 生育期适用措施 ----
    "MEASURE_AT_STAGE": RelationSchema(
        name="MEASURE_AT_STAGE",
        description="措施适用于（某生育期）",
        source_labels=["Measure"],
        target_labels=["GrowthStage"],
        required_props=[],
        optional_props=["priority", "timing"],
    ),
    # ---- 文档来源 ----
    "DOCUMENTS": RelationSchema(
        name="DOCUMENTS",
        description="文档记载了（某实体）",
        source_labels=["Document"],
        target_labels=["Crop", "Disease", "Pest", "Chemical", "Fertilizer",
                        "Variety", "Region", "Policy", "Measure", "Symptom"],
        required_props=[],
        optional_props=["relevance_score", "extracted_text"],
    ),
    # ---- 农药间相互作用 ----
    "INTERACTS_WITH": RelationSchema(
        name="INTERACTS_WITH",
        description="农药间存在（相互作用）",
        source_labels=["Chemical"],
        target_labels=["Chemical"],
        required_props=[],
        optional_props=["interaction_type", "effect", "severity"],
        bidirectional=True,
    ),
    # ---- 病害导致症状 ----
    "CAUSES_SYMPTOM": RelationSchema(
        name="CAUSES_SYMPTOM",
        description="病害/虫害导致（某症状）",
        source_labels=["Disease", "Pest"],
        target_labels=["Symptom"],
        required_props=[],
        optional_props=["affected_part", "stage", "severity"],
    ),
    # ---- 品种抗性 ----
    "RESISTS": RelationSchema(
        name="RESISTS",
        description="品种抗（某病虫害）",
        source_labels=["Variety"],
        target_labels=["Disease", "Pest"],
        required_props=[],
        optional_props=["resistance_level", "gene_source"],
    ),
    # ---- 政策覆盖作物 ----
    "COVERS_CROP": RelationSchema(
        name="COVERS_CROP",
        description="政策覆盖（某作物）",
        source_labels=["Policy"],
        target_labels=["Crop"],
        required_props=[],
        optional_props=["subsidy_amount", "conditions"],
    ),
    # ---- 肥料适用生育期 ----
    "FERTILIZER_AT_STAGE": RelationSchema(
        name="FERTILIZER_AT_STAGE",
        description="肥料适用于（某生育期）",
        source_labels=["Fertilizer"],
        target_labels=["GrowthStage"],
        required_props=[],
        optional_props=["dosage", "method"],
    ),
}


# ============================================================
# 初始种子数据（核心农业实体）
# ============================================================

# 作物实体
SEED_CROPS = [
    {"name": "水稻", "alias": "rice", "category": "粮食作物", "family": "禾本科", "growing_season": "双季/单季"},
    {"name": "小麦", "alias": "wheat", "category": "粮食作物", "family": "禾本科", "growing_season": "冬小麦/春小麦"},
    {"name": "玉米", "alias": "corn/maize", "category": "粮食作物", "family": "禾本科", "growing_season": "春播/夏播"},
    {"name": "油菜", "alias": "rapeseed", "category": "油料作物", "family": "十字花科", "growing_season": "秋播-次年春收"},
    {"name": "赣南脐橙", "alias": "Gannan navel orange", "category": "水果", "family": "芸香科", "growing_season": "全年管理"},
    {"name": "蔬菜", "alias": "vegetables", "category": "蔬菜", "family": "多种", "growing_season": "全年"},
    {"name": "大豆", "alias": "soybean", "category": "油料作物", "family": "豆科", "growing_season": "春播/夏播"},
    {"name": "棉花", "alias": "cotton", "category": "经济作物", "family": "锦葵科", "growing_season": "春播"},
    {"name": "茶叶", "alias": "tea", "category": "经济作物", "family": "山茶科", "growing_season": "全年采摘"},
    {"name": "水稻（早稻）", "alias": "early rice", "category": "粮食作物", "family": "禾本科", "growing_season": "3月-7月"},
    {"name": "水稻（晚稻）", "alias": "late rice", "category": "粮食作物", "family": "禾本科", "growing_season": "6月-10月"},
]

# 病害实体
SEED_DISEASES = [
    {"name": "稻瘟病", "alias": "rice blast", "pathogen": "稻瘟病菌", "pathogen_type": "真菌"},
    {"name": "纹枯病", "alias": "sheath blight", "pathogen": "立枯丝核菌", "pathogen_type": "真菌"},
    {"name": "白叶枯病", "alias": "bacterial leaf blight", "pathogen": "黄单胞杆菌", "pathogen_type": "细菌"},
    {"name": "稻飞虱", "alias": "rice planthopper", "pathogen": "", "pathogen_type": "害虫"},
    {"name": "稻纵卷叶螟", "alias": "rice leaf folder", "pathogen": "", "pathogen_type": "害虫"},
    {"name": "二化螟", "alias": "rice stem borer", "pathogen": "", "pathogen_type": "害虫"},
    {"name": "赤霉病", "alias": "Fusarium head blight", "pathogen": "禾谷镰刀菌", "pathogen_type": "真菌"},
    {"name": "锈病", "alias": "rust", "pathogen": "锈菌", "pathogen_type": "真菌"},
    {"name": "溃疡病", "alias": "citrus canker", "pathogen": "地毯草黄单胞杆菌", "pathogen_type": "细菌"},
    {"name": "炭疽病", "alias": "anthracnose", "pathogen": "炭疽菌", "pathogen_type": "真菌"},
    {"name": "菌核病", "alias": "Sclerotinia rot", "pathogen": "核盘菌", "pathogen_type": "真菌"},
    {"name": "病毒病", "alias": "viral disease", "pathogen": "多种病毒", "pathogen_type": "病毒"},
]

# 虫害实体
SEED_PESTS = [
    {"name": "稻飞虱", "alias": "rice planthopper"},
    {"name": "稻纵卷叶螟", "alias": "rice leaf folder"},
    {"name": "二化螟", "alias": "rice stem borer"},
    {"name": "三化螟", "alias": "yellow stem borer"},
    {"name": "玉米螟", "alias": "corn borer"},
    {"name": "蚜虫", "alias": "aphid"},
    {"name": "菜青虫", "alias": "cabbage caterpillar"},
    {"name": "红蜘蛛", "alias": "spider mite"},
    {"name": "柑橘木虱", "alias": "citrus psyllid"},
    {"name": "棉铃虫", "alias": "cotton bollworm"},
]

# 农药实体
SEED_CHEMICALS = [
    {"name": "吡虫啉", "alias": "imidacloprid", "chemical_class": "新烟碱类", "toxicity_class": "低毒",
     "target_pest": "蚜虫、飞虱", "safety_interval": "7天"},
    {"name": "噻虫嗪", "alias": "thiamethoxam", "chemical_class": "新烟碱类", "toxicity_class": "低毒",
     "target_pest": "飞虱、蓟马", "safety_interval": "14天"},
    {"name": "戊唑醇", "alias": "tebuconazole", "chemical_class": "三唑类", "toxicity_class": "低毒",
     "target_disease": "锈病、纹枯病", "safety_interval": "21天"},
    {"name": "三唑酮", "alias": "triadimefon", "chemical_class": "三唑类", "toxicity_class": "低毒",
     "target_disease": "锈病、白粉病", "safety_interval": "20天"},
    {"name": "氯虫苯甲酰胺", "alias": "chlorantraniliprole", "chemical_class": "双酰胺类", "toxicity_class": "微毒",
     "target_pest": "螟虫、稻纵卷叶螟", "safety_interval": "14天"},
    {"name": "阿维菌素", "alias": "abamectin", "chemical_class": "大环内酯类", "toxicity_class": "低毒",
     "target_pest": "红蜘蛛、菜青虫", "safety_interval": "7天"},
    {"name": "井冈霉素", "alias": "validamycin", "chemical_class": "抗生素类", "toxicity_class": "低毒",
     "target_disease": "纹枯病", "safety_interval": "14天"},
    {"name": "春雷霉素", "alias": "kasugamycin", "chemical_class": "抗生素类", "toxicity_class": "低毒",
     "target_disease": "稻瘟病", "safety_interval": "21天"},
    {"name": "代森锰锌", "alias": "mancozeb", "chemical_class": "有机硫类", "toxicity_class": "低毒",
     "target_disease": "多种真菌病害", "safety_interval": "15天"},
    {"name": "苏云金杆菌(Bt)", "alias": "Bacillus thuringiensis", "chemical_class": "生物农药", "toxicity_class": "微毒",
     "target_pest": "鳞翅目幼虫", "safety_interval": "3天"},
]

# 症状实体
SEED_SYMPTOMS = [
    {"name": "叶尖干枯", "affected_part": "叶片", "visual_description": "叶尖变黄、干枯"},
    {"name": "叶片黄化", "affected_part": "叶片", "visual_description": "叶片整体变黄"},
    {"name": "褐色斑点", "affected_part": "叶片", "visual_description": "叶片出现褐色梭形斑"},
    {"name": "白穗", "affected_part": "稻穗", "visual_description": "抽穗后穗部变白、空秕"},
    {"name": "倒伏", "affected_part": "茎秆", "visual_description": "茎秆折断或倾斜"},
    {"name": "卷叶", "affected_part": "叶片", "visual_description": "叶片纵向卷曲"},
    {"name": "虫蛀茎秆", "affected_part": "茎秆", "visual_description": "茎秆有蛀孔、排粪"},
    {"name": "果实溃疡", "affected_part": "果实", "visual_description": "果皮出现隆起病斑"},
    {"name": "根腐", "affected_part": "根部", "visual_description": "根系变褐、腐烂"},
    {"name": "萎蔫", "affected_part": "全株", "visual_description": "植株失水萎蔫"},
]

# 生育期实体（水稻）
SEED_GROWTH_STAGES = [
    {"name": "播种期", "crop": "水稻", "key_operations": "浸种催芽、秧田管理"},
    {"name": "秧田期", "crop": "水稻", "key_operations": "苗床管理、病虫害防治"},
    {"name": "移栽期", "crop": "水稻", "key_operations": "插秧、施底肥"},
    {"name": "分蘖期", "crop": "水稻", "key_operations": "浅水灌溉、追施分蘖肥"},
    {"name": "拔节期", "crop": "水稻", "key_operations": "晒田、施穗肥"},
    {"name": "孕穗期", "crop": "水稻", "key_operations": "水分管理、防治病虫害"},
    {"name": "抽穗期", "crop": "水稻", "key_operations": "保持水层、喷施叶面肥"},
    {"name": "灌浆期", "crop": "水稻", "key_operations": "干湿交替、防止早衰"},
    {"name": "成熟期", "crop": "水稻", "key_operations": "适时收获、排水晒田"},
]

# 江西地区实体
SEED_REGIONS = [
    {"name": "江西省", "province": "江西省", "climate_zone": "亚热带季风气候"},
    {"name": "南昌市", "province": "江西省", "city": "南昌市", "climate_zone": "亚热带湿润气候"},
    {"name": "赣州市", "province": "江西省", "city": "赣州市", "climate_zone": "亚热带季风气候"},
    {"name": "上饶市", "province": "江西省", "city": "上饶市", "climate_zone": "亚热带季风气候"},
    {"name": "吉安市", "province": "江西省", "city": "吉安市", "climate_zone": "亚热带季风气候"},
    {"name": "宜春市", "province": "江西省", "city": "宜春市", "climate_zone": "亚热带季风气候"},
    {"name": "抚州市", "province": "江西省", "city": "抚州市", "climate_zone": "亚热带季风气候"},
    {"name": "九江市", "province": "江西省", "city": "九江市", "climate_zone": "亚热带季风气候"},
    {"name": "萍乡市", "province": "江西省", "city": "萍乡市", "climate_zone": "亚热带季风气候"},
    {"name": "景德镇市", "province": "江西省", "city": "景德镇市", "climate_zone": "亚热带季风气候"},
    {"name": "新余市", "province": "江西省", "city": "新余市", "climate_zone": "亚热带季风气候"},
    {"name": "鹰潭市", "province": "江西省", "city": "鹰潭市", "climate_zone": "亚热带季风气候"},
]


# ============================================================
# Cypher 查询模板
# ============================================================

class CypherTemplates:
    """常用 Cypher 查询模板"""

    # 创建实体
    CREATE_ENTITY = """
    MERGE (n:{label} {{name: $name}})
    SET n += $properties
    RETURN n
    """

    # 创建关系
    CREATE_RELATION = """
    MATCH (a:{source_label} {{name: $source_name}})
    MATCH (b:{target_label} {{name: $target_name}})
    MERGE (a)-[r:{relation_name}]->(b)
    SET r += $properties
    RETURN a, r, b
    """

    # 查询实体及其邻居（Graph RAG 核心查询）
    GET_NEIGHBORHOOD = """
    MATCH (e {{name: $entity_name}})-[r]-(neighbor)
    WHERE e:{label}
    RETURN e, r, neighbor
    LIMIT $limit
    """

    # 根据症状推断病虫害（诊断查询）
    DIAGNOSE_BY_SYMPTOM = """
    MATCH (s:Symptom)-[:INDICATES]->(d)
    WHERE s.name IN $symptoms
    WITH d, count(s) AS match_count
    ORDER BY match_count DESC
    LIMIT $limit
    MATCH (d)-[r1]-(m)
    WHERE (m:Chemical OR m:Measure)
    RETURN d.name AS disease, collect(DISTINCT {{name: m.name, type: labels(m)[0], relation: type(r1)}}) AS treatments
    """

    # 查询作物的所有病虫害
    CROP_PESTS_DISEASES = """
    MATCH (c:Crop {{name: $crop_name}})-[:SUSCEPTIBLE_TO]->(pd)
    WHERE pd:Disease OR pd:Pest
    OPTIONAL MATCH (pd)-[:CONTROLLED_BY]->(t)
    WHERE t:Chemical OR t:Measure
    RETURN pd.name AS pest_or_disease, labels(pd)[0] AS type,
           collect(DISTINCT t.name) AS treatments
    """

    # 查询地区适用的政策
    REGION_POLICIES = """
    MATCH (r:Region {{name: $region_name}})-[:GOVERNED_BY]->(p:Policy)
    WHERE p.valid_until IS NULL OR p.valid_until > date()
    RETURN p.policy_id AS id, p.name AS name, p.issuer AS issuer,
           p.publish_date AS date, p.category AS category
    ORDER BY p.publish_date DESC
    """

    # 实体搜索（全文索引）
    SEARCH_ENTITIES = """
    CALL db.index.fulltext.queryNodes('entity_search', $query)
    YIELD node, score
    RETURN labels(node)[0] AS type, node.name AS name, score
    ORDER BY score DESC
    LIMIT $limit
    """

    # 查询品种抗性
    VARIETY_RESISTANCE = """
    MATCH (v:Variety {{name: $variety_name}})-[r:RESISTS]->(d)
    RETURN d.name AS target, r.resistance_level AS level
    """

    # 查询生育期管理措施
    STAGE_MEASURES = """
    MATCH (gs:GrowthStage {{name: $stage_name}})<-[:MEASURE_AT_STAGE]-(m:Measure)
    OPTIONAL MATCH (m)<-[:CONTROLLED_BY]-(pd)
    RETURN m.name AS measure, m.category AS category,
           collect(DISTINCT pd.name) AS targets
    """
