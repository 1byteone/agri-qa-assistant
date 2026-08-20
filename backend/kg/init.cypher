// ============================================================
// CropWise 农业知识图谱 Schema 初始化脚本
// 基于 Crop GraphRAG + AgriKG 论文的本体设计
// ============================================================

// ------------------------------------------------------------
// 1. 约束（Constraints）—— 保证实体唯一性
// ------------------------------------------------------------

// 作物实体
CREATE CONSTRAINT crop_name_unique IF NOT EXISTS
FOR (c:Crop) REQUIRE c.name IS UNIQUE;

// 病害实体
CREATE CONSTRAINT disease_name_unique IF NOT EXISTS
FOR (d:Disease) REQUIRE d.name IS UNIQUE;

// 虫害实体
CREATE CONSTRAINT pest_name_unique IF NOT EXISTS
FOR (p:Pest) REQUIRE p.name IS UNIQUE;

// 农药实体
CREATE CONSTRAINT pesticide_name_unique IF NOT EXISTS
FOR (pest:Chemical) REQUIRE pest.name IS UNIQUE;

// 肥料实体
CREATE CONSTRAINT fertilizer_name_unique IF NOT EXISTS
FOR (f:Fertilizer) REQUIRE f.name IS UNIQUE;

// 品种实体
CREATE CONSTRAINT variety_name_unique IF NOT EXISTS
FOR (v:Variety) REQUIRE v.name IS UNIQUE;

// 地区实体
CREATE CONSTRAINT region_name_unique IF NOT EXISTS
FOR (r:Region) REQUIRE r.name IS UNIQUE;

// 政策实体
CREATE CONSTRAINT policy_id_unique IF NOT EXISTS
FOR (pol:Policy) REQUIRE pol.policy_id IS UNIQUE;

// 技术措施实体
CREATE CONSTRAINT measure_name_unique IF NOT EXISTS
FOR (m:Measure) REQUIRE m.name IS UNIQUE;

// 生育期实体
CREATE CONSTRAINT growth_stage_name_unique IF NOT EXISTS
FOR (gs:GrowthStage) REQUIRE gs.name IS UNIQUE;

// 症状实体
CREATE CONSTRAINT symptom_name_unique IF NOT EXISTS
FOR (s:Symptom) REQUIRE s.name IS UNIQUE;

// 文档/证据实体
CREATE CONSTRAINT document_hash_unique IF NOT EXISTS
FOR (doc:Document) REQUIRE doc.content_hash IS UNIQUE;

// ------------------------------------------------------------
// 2. 索引（Indexes）—— 加速查询
// ------------------------------------------------------------

// 全文索引（用于模糊搜索）
CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
FOR (n:Crop|Disease|Pest|Chemical|Fertilizer|Variety|Region|Measure|Symptom)
ON EACH [n.name, n.alias];

// 作物-地区组合索引
CREATE INDEX crop_region_idx IF NOT EXISTS
FOR (cr:CropRegion) ON (cr.crop_name, cr.region_name);

// ------------------------------------------------------------
// 3. 空间索引（用于地理位置查询）
// ------------------------------------------------------------

// Neo4j 5.x 支持点空间索引
// CREATE POINT INDEX region_location IF NOT EXISTS
// FOR (r:Region) ON (r.location);

// ------------------------------------------------------------
// 4. 标签统计视图
// ------------------------------------------------------------

// 可通过以下 Cypher 查看各标签实体数量：
// MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC;

// ============================================================
// Schema 完成，接下来的数据导入由 Python 脚本执行
// ============================================================
