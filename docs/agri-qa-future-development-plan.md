# CropWise 农业智能知识服务平台 — 后续开发设计方案

**版本**：1.0\n**日期**：2026-08-20\n**适用项目**：`agri-qa-assistant`\n**编制依据**：SEEDS、AgriKG、Crop GraphRAG、AgriEval、中国农科院农业智能知识服务平台、问稷/识农AI 等真实项目与论文

---

## 1. 项目现状与技术缺口分析

### 1.1 当前技术基线

| 维度 | 当前实现 | 成熟度 |
|------|----------|--------|
| **后端框架** | FastAPI + Python | ⭐⭐⭐⭐ 稳定 |
| **Agent 架构** | LangGraph 工具循环 + SSE 流式 | ⭐⭐⭐⭐ 已具备 Agent 能力 |
| **向量检索** | ChromaDB 本地持久化 + 本地哈希 Embedding | ⭐⭐⭐ 可用但精度受限 |
| **检索策略** | 单一 `KnowledgeBase.search()` + 简单 BM25 混合 | ⭐⭐⭐ 有融合但非 RRF |
| **知识库** | 6 证据包 + 120 条 P0 评测骨架 | ⭐⭐ 覆盖面窄 |
| **领域守卫** | Domain Guard + 证据等级门控 | ⭐⭐⭐⭐ 安全边界已建立 |
| **对话记忆** | SQLite 多轮记忆 + 候选事实提取 | ⭐⭐⭐ 功能完整 |
| **前端** | Next.js 14 + Apple Liquid Glass UI | ⭐⭐⭐⭐ 颜值与交互成熟 |
| **MCP 工具** | 农时/天气/网页/图片/资源/时间 6 个内嵌工具 | ⭐⭐⭐ 功能可用但未标准化 |
| **评测体系** | 120 条骨架 + 手动 Recall@K | ⭐⭐ 缺乏自动化评测流水线 |

### 1.2 核心缺口（对标行业标杆）

| 缺口 | 说明 | 对标参考 |
|------|------|----------|
| **无知识图谱** | 缺少实体-关系-属性三元组，无法做结构化推理和 GraphRAG | AgriKG / Crop GraphRAG |
| **无 Hybrid RAG** | 缺少真正的向量+BM25+RRF 混合检索 + Reranker 重排 | SEEDS / BRAG 教程 |
| **无农业大模型微调** | 通用 LLM 对农业术语、农药登记号、生育期等理解不足 | CropSeek-LLM / AgriEval |
| **知识库规模小** | 仅 6 证据包，缺少系统化的农业文档/论文/标准/政策入库 | 中国农科院 10 亿条知识资源 |
| **评测不自动化** | 无离线评测集、无 CI 门控、无 AgriEval 式农业领域 Benchmark | AgriEval (20K+ 题) |
| **无多模态能力** | 缺少图片识别、病害图像诊断 | 识农AI / 问稷 |
| **无江西特色知识体系** | 缺少江西 11 地市的县域农时、特色作物、地方政策 | 问稷县域数据模式 |
| **无数据治理** | 缺少数据源注册表、来源等级、版本管理、许可证追溯 | 中国农科院数据平台 |

---

## 2. 目标架构设计

### 2.1 总体架构：Hybrid RAG + GraphRAG + 农业知识图谱

```text
                        ┌──────────────────────────────┐
                        │        用户层（多端）          │
                        │  Web · 小程序 · 微信公众号    │
                        └──────────────┬───────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │      API Gateway (Spring Boot) │
                        │  认证 · 限流 · 审计 · 路由     │
                        └──────────────┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
   ┌────────▼────────┐      ┌─────────▼─────────┐     ┌─────────▼─────────┐
   │  AI Agent Engine │      │  知识图谱服务       │     │  评测服务           │
   │  (LangGraph)     │      │  (Neo4j + REST)    │     │  (AgriEval)        │
   └────────┬────────┘      └─────────┬─────────┘     └─────────┬─────────┘
            │                          │                          │
            │               ┌──────────▼──────────┐              │
            │               │  农业知识图谱        │              │
            │               │  作物-病虫害-农药-   │              │
            │               │  地区-政策-品种       │              │
            │               └──────────┬──────────┘              │
            │                          │                          │
   ┌────────▼──────────────────────────▼──────────────────────────▼────────┐
   │                         Hybrid Retrieval Layer                       │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
   │  │ Vector   │  │ BM25     │  │ Graph    │  │ Temporal │            │
   │  │ (BGE-M3) │  │ (Lucene) │  │ (Neo4j)  │  │ (时间衰减) │            │
   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
   │       └──────────────┼──────────────┼──────────────┘                 │
   │                      │     RRF Fusion │                              │
   │                      └────────┬───────┘                              │
   │                               │                                      │
   │                      ┌────────▼────────┐                             │
   │                      │  Reranker        │                             │
   │                      │  (BGE-Reranker)  │                             │
   │                      └────────┬────────┘                             │
   └───────────────────────────────┼──────────────────────────────────────┘
                                   │
   ┌───────────────────────────────▼──────────────────────────────────────┐
   │                         Storage Layer                                │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
   │  │ ChromaDB │  │ Neo4j    │  │ Milvus/  │  │ SQLite/  │           │
   │  │ (向量库)  │  │ (知识图谱)│  │ pgvector │  │ Redis    │           │
   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
   └─────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心数据流

```text
用户问题
  │
  ▼
① Domain Guard（领域守卫 + 安全分类）
  │
  ▼
② Query Understanding（查询理解）
  ├── 场景分类（诊断/施肥/农时/政策/越界）
  ├── 结构化字段提取（作物/地区/生育期/症状）
  ├── 查询改写 + Multi-Query 分解（最多 4 个子查询）
  └── 路由决策（hybrid / hybrid-temporal / hybrid-graph）
  │
  ▼
③ Hybrid Retrieval（混合检索）
  ├── Vector Branch：BGE-M3 Dense Embedding → ChromaDB/Milvus
  ├── Lexical Branch：BM25 → 倒排索引
  ├── Graph Branch：实体链接 → Neo4j 邻域子图
  └── Temporal Branch：时间衰减过滤
  │
  ▼
④ RRF Fusion（Reciprocal Rank Fusion）
  ├── 融合多路召回结果
  └── 输出统一排序列表 + 分支贡献度
  │
  ▼
⑤ Reranker（重排序）
  ├── BGE-Reranker-v2-M3 交叉编码器
  └── 证据等级/适用范围二次过滤
  │
  ▼
⑥ Context Assembly（上下文组装）
  ├── Parent-Child 上下文恢复
  ├── 证据等级门控（A/B/C/D）
  ├── 冲突来源检测
  └── 上下文压缩
  │
  ▼
⑦ Generation（大模型生成）
  ├── 五段式决策卡（摘要/判断/行动/边界/复查）
  ├── 引用溯源（evidence_id + source_url）
  └── 安全边界检查
  │
  ▼
⑧ Post-Processing（后处理）
  ├── 专业术语注释
  ├── 证据政策执行
  └── SSE 流式输出
```

### 2.3 Spring Boot 后端服务拆分（如需 Java 化）

当前系统为 Python FastAPI 单体。若需升级为 Spring Boot 微服务架构：

```
agri-platform/
├── agri-gateway/              # Spring Cloud Gateway（路由/限流/认证）
├── agri-auth/                 # Spring Security + JWT 认证服务
├── agri-agent/                # AI Agent 编排服务（调用 Python RAG 引擎）
├── agri-rag/                  # RAG 检索引擎（Python FastAPI，通过 gRPC/HTTP 被 Java 调用）
├── agri-knowledge-graph/      # 知识图谱服务（Neo4j + Spring Data Neo4j）
├── agri-knowledge-base/       # 知识库管理服务（Spring Boot + JPA，管理文档元数据）
├── agri-evaluation/           # 评测服务（Ragas + AgriEval）
├── agri-weather/              # 气象数据聚合服务
├── agri-policy/               # 政策检索服务
├── agri-case/                 # 病例管理服务
└── agri-common/               # 公共模块（DTO/异常/工具类）
```

> **推荐策略**：Python RAG 引擎保持不变，Java 侧负责 API Gateway + 知识库管理 + 病例管理 + 认证。通过 gRPC 或 HTTP Feign 桥接。

---

## 3. 专业 Goal 定义

### 3.1 产品 Goal

> **在 12 周内，将 CropWise 从农业问答原型升级为"江西县域种植者和农技人员可信赖的农业智能知识服务平台"：支持水稻、油菜、赣南脐橙、蔬菜四大场景，输出带知识图谱推理、引用溯源、可复查的决策卡；知识库规模从 6 个证据包扩展到 50+ 结构化知识包；评测体系从 120 条骨架扩展到 500+ 自动化评测集。**

### 3.2 工程 Goal

```text
建立可评测、可追溯、可降级的农业智能知识服务流水线：

结构化场景输入
  → 领域守卫 + 场景分类
  → 查询理解 + Multi-Query 分解
  → Vector RAG + Graph RAG + BM25 混合检索
  → RRF 融合 + Reranker 重排
  → 知识图谱推理 + 实体关系查询
  → 证据等级门控 + 冲突检测
  → 五段式决策卡 + 引用溯源 + SSE trace
  → 病例管理 + 复查闭环
  → 离线评测 + CI 门控
```

### 3.3 KPI 与验收门槛

| 指标 | 当前值 | 8周目标 | 12周目标 | 说明 |
|------|--------|---------|----------|------|
| **Top-5 专家相关证据召回** | ~60%（估算） | ≥ 85% | ≥ 90% | 基于专家金标 |
| **关键判断引用覆盖率** | ~70% | ≥ 90% | ≥ 95% | 每个结论可追溯 evidence_id |
| **高风险安全提醒覆盖率** | 100% | 100% | 100% | 农药/剂量/间隔期 |
| **无依据具体处方率** | 待测 | 0% | 0% | 无 A 级 scope 匹配不输出 |
| **五段式决策卡完整率** | ~80% | ≥ 95% | ≥ 98% | 摘要/判断/行动/边界/复查 |
| **非农业越界率** | < 1% | < 1% | < 0.5% | Domain Guard + 回归集 |
| **知识库规模** | 6 证据包 | 30+ 知识包 | 50+ 知识包 | 含论文/标准/政策/百科 |
| **评测集规模** | 120 条骨架 | 300 条金标 | 500+ 条金标 | 含 AgriEval 适配 |
| **CI 自动化门控** | 无 | 基础测试 | 完整评测流水线 | 每次 PR 必跑 |
| **P95 首字延迟** | ~2s | ≤ 3s | ≤ 3s | 本地知识库 |
| **SSE 完整结束率** | ≥ 99% | ≥ 99% | ≥ 99.5% | done/error 明确 |

---

## 4. 开发任务清单（按优先级和依赖排序）

### Phase 1：基础设施升级（第 1-3 周）

#### T1.1 知识图谱构建与 Neo4j 接入 ⭐⭐⭐⭐⭐

**目标**：构建农业领域知识图谱，实现结构化实体-关系查询

```text
农业实体类型：
├── 作物（水稻、油菜、脐橙、蔬菜...）
├── 病虫害（稻飞虱、纹枯病、溃疡病...）
├── 农药（吡虫啉、噻虫嗪、戊唑醇...）
├── 肥料（尿素、磷酸二氢钾...）
├── 品种（隆两优1988、赣南脐橙...）
├── 地区（江西省、南昌市、赣州市...）
├── 政策（农机补贴、种粮补贴...）
├── 技术措施（浅水勤灌、测土配方...）
└── 生育期（分蘖期、抽穗期、返青期...）

关系类型：
├── 作物 -[易感]-> 病虫害
├── 病虫害 -[防治使用]-> 农药
├── 农药 -[适用作物]-> 作物
├── 作物 -[适宜种植]-> 地区
├── 地区 -[执行]-> 政策
├── 作物 -[推荐品种]-> 品种
├── 作物 -[关键期]-> 生育期
├── 技术措施 -[适用阶段]-> 生育期
└── 作物 -[适用]-> 技术措施
```

**技术选型**：
- Neo4j 5.x Community Edition（本地部署）
- Spring Data Neo4j（Java 层）或 neo4j-driver（Python 层）
- 知识图谱嵌入：TransE / RotatE 用于链接预测和补全

**交付物**：
- Neo4j 本地部署 + Docker Compose
- 知识图谱 Schema 定义（实体/关系/属性）
- 知识图谱构建脚本（从农业文档抽取实体关系）
- Graph RAG 检索接口（邻域子图查询 + 路径推理）
- 与现有 Vector RAG 的融合接口

---

#### T1.2 BGE-M3 嵌入模型替换 ⭐⭐⭐⭐⭐

**目标**：替换本地哈希 Embedding 为高质量农业语义嵌入

```text
当前：LocalHashingEmbeddingFunction（384维，纯哈希，无语义）
替换为：BAAI/bge-m3（1024维，多语言，密集+稀疏+多向量）
```

**技术细节**：
- 模型：`BAAI/bge-m3`（支持 100+ 语言，8192 token 上下文）
- 推理：本地 GPU 推理 或 BGE-M3 API（推荐本地）
- 向量库：ChromaDB 保持兼容，后续可迁移 Milvus/pgvector
- 兼容性：`embed_documents` + `embed_query` 接口不变

**交付物**：
- `BGEEmbeddingFunction` 实现
- 重新索引所有证据包
- 离线 A/B 对比（Recall@5 / MRR）
- 延迟/成本评估报告

---

#### T1.3 BM25 关键词检索分支 ⭐⭐⭐⭐

**目标**：建立独立的 BM25 倒排索引，支持精确术语匹配

**技术选型**：
- Python：`rank_bm25` 或 `whoosh`
- 后续可升级为 Elasticsearch/OpenSearch

**交付物**：
- `BM25Retriever` 实现
- 农业术语分词词典（水稻/病虫害/农药专业词）
- 与 Vector 检索的 RRF 融合

---

#### T1.4 RRF 融合引擎 ⭐⭐⭐⭐

**目标**：实现多路检索的 Reciprocal Rank Fusion

```python
RRF_score(d) = Σ 1/(k + rank_i(d))  # k=60 默认
```

**交付物**：
- `RRFEnsembler` 模块
- k 参数调优实验（k=20/40/60/80/100）
- 分支贡献度 trace 输出
- A/B 实验：vector-only vs hybrid vs RRF

---

### Phase 2：检索增强与知识工程（第 4-6 周）

#### T2.1 查询理解与 Multi-Query 分解 ⭐⭐⭐⭐

**目标**：将复杂农业问题分解为多个可独立检索的子查询

```text
示例：
输入："南昌县晚稻分蘖期，连续高温后叶尖干枯，田里有飞虫，昨天已灌水"
分解为：
  Q1: "水稻分蘖期 叶尖干枯 高温热害 防治措施"
  Q2: "晚稻飞虫 稻飞虱 防治药剂"
  Q3: "水稻高温热害 灌溉管理 复查时间"
  Q4: "南昌县 晚稻 农时 分蘖期"
```

**交付物**：
- `QueryTransformer`（结构化改写 + Multi-Query）
- `QueryRouter`（场景路由：诊断/施肥/农时/政策/越界）
- 并行分解引擎（最多 4 个子查询并行检索）
- 路由 trace 输出

---

#### T2.2 Reranker 重排序 ⭐⭐⭐⭐

**目标**：使用交叉编码器对召回结果进行精排

```text
候选集（top-30）→ BGE-Reranker-v2-M3 → 精排集（top-5）
```

**技术选型**：
- `BAAI/bge-reranker-v2-m3`（多语言交叉编码器）
- 备选：`BAAI/bge-reranker-v2-minicpm-2B`（更强但更慢）

**交付物**：
- `Reranker` 接口实现
- 延迟-质量 A/B 对比
- 可插拔开关（有/无 Reranker 对比）
- P95 延迟控制（≤ 1.5s 增量）

---

#### T2.3 知识图谱构建自动化 ⭐⭐⭐⭐

**目标**：从农业文档自动抽取实体和关系，构建知识图谱

```text
文档 → 文档解析 → 实体识别（NER）→ 关系抽取 → 知识融合 → Neo4j 导入
```

**技术方案**：
- 实体识别：基于 LLM 的 Few-Shot NER（Qwen/DeepSeek）
- 关系抽取：基于 LLM 的 Few-Shot RE
- 去重/融合：实体链接 + 属性合并
- 增量更新：文档变更检测 → 增量抽取

**交付物**：
- NER + RE Prompt 模板
- 知识图谱构建 Pipeline
- 实体/关系质量评测集
- 增量更新机制

---

#### T2.4 知识库规模扩展 ⭐⭐⭐⭐⭐

**目标**：从 6 证据包扩展到 30+ 知识包

```text
知识包清单：
├── P0 核心知识包（已有）
│   ├── jiangxi-rice（江西水稻）
│   ├── jiangxi-rapeseed（江西油菜）
│   ├── gannan-citrus（赣南脐橙）
│   └── jiangxi-policy（江西政策）
├── P1 扩展知识包（新增）
│   ├── national-pest-control（国家病虫害防治）
│   ├── national-fertilizer（国家肥料标准）
│   ├── jiangxi-vegetables（江西蔬菜）
│   ├── jiangxi-county-calendar（县域农时）
│   ├── jiangxi-agri-subsidy（农业补贴政策）
│   ├── jiangxi-agri-machinery（农机规范）
│   ├── national-water-conservation（节水灌溉）
│   ├── national-soil-management（土壤管理）
│   ├── jiangxi-weather-patterns（江西气象模式）
│   └── crop-breeding-variety（品种信息）
├── P2 研究知识包（后续）
│   ├── caas-research-papers（农科院论文摘要）
│   ├── jiangxi-agri-journal（江西农业期刊）
│   ├── international-agri-standards（国际标准）
│   └── agri-economic-data（农业经济数据）
└── P3 用户贡献知识包
    ├── farmer-practices（农户实践经验）
    └── expert-annotations（专家标注）
```

**交付物**：
- 知识包版本管理（manifest + content_hash + 回滚脚本）
- 文档解析 Pipeline（PDF/Word/HTML → 结构化文本）
- 元数据标准（crop/region/stage/source/date/scope/license）
- 知识包质量门控（人工审核 + 自动校验）

---

### Phase 3：Agent 增强与评测体系（第 7-9 周）

#### T3.1 农业大模型微调（可选） ⭐⭐⭐

**目标**：提升 LLM 对农业术语和专业场景的理解

**技术路线**：
```text
Qwen-7B / DeepSeek-7B
  → LoRA 微调（农业 QA 对 + 农业术语 + 江西方言表达）
  → AgriEval 评测
  → 与通用模型 A/B 对比
```

**数据来源**：
- AgriEval 评测集（20K+ 题）
- 农业 QA 数据集（175K pairs，Agri-Llama）
- 本项目 500+ 金标数据
- 农业论文摘要/标准文本

**交付物**：
- 微调数据清洗 Pipeline
- LoRA 微调脚本（Unsloth / PEFT）
- AgriEval 评测结果
- 成本-收益分析报告

> **推荐**：先用 Qwen/DeepSeek API 验证，数据量达标后再做微调。

---

#### T3.2 AgriEval 评测体系集成 ⭐⭐⭐⭐⭐

**目标**：建立农业领域自动化评测流水线

```text
评测维度：
├── Recall@K（检索召回率）
├── MRR（平均倒数排名）
├── Context Precision（上下文精度）
├── Context Recall（上下文召回）
├── Faithfulness（回答忠实度）
├── Answer Relevancy（回答相关性）
├── Citation Accuracy（引用准确性）
├── Safety Coverage（安全覆盖率）
├── Decision Card Completeness（决策卡完整率）
└── Hallucination Rate（幻觉率）
```

**技术选型**：
- 评测框架：Ragas（主流 RAG 评测）
- 农业适配：AgriEval 题库 + 自建金标
- CI 集成：GitHub Actions / GitLab CI

**交付物**：
- 500+ 条金标评测集（含答案、证据、禁止结论）
- 自动化评测脚本
- CI 门控（每次 PR 自动跑评测）
- 评测报告 Dashboard

---

#### T3.3 病例管理与复查闭环 ⭐⭐⭐⭐

**目标**：支持农业病虫害的"诊断→行动→复查→升级"完整流程

```text
用户描述症状
  → 系统生成诊断建议 + 行动方案
  → 保存为病例（case）
  → 到期提醒复查
  → 用户反馈复查结果
  → 系统对比差异
  → 必要时升级到农技人员
```

**交付物**：
- `cases` / `case_events` 数据模型
- 病例 CRUD API
- 复查时间线前端组件
- 农技人员升级接口

---

#### T3.4 多模态图片识别（P1） ⭐⭐⭐

**目标**：支持农业病害图片辅助识别

```text
用户上传图片
  → 图片预处理 + 分类
  → 病害识别（CLIP / 专用模型）
  → 与文字症状交叉验证
  → 辅助诊断（不自动确诊）
```

**技术选型**：
- CLIP / BLIP-2 用于图片理解
- 专用病害识别模型（PlantVillage 预训练）
- 人工复核边界

**交付物**：
- 图片上传接口
- 图片特征提取
- 与文字症状的融合诊断
- 误判边界测试集

---

### Phase 4：产品化与试点（第 10-12 周）

#### T4.1 江西县域数据体系 ⭐⭐⭐⭐

**目标**：建立江西 11 地市 100+ 县区的结构化农业数据

```text
数据维度：
├── 县域农时日历（早稻/晚稻/油菜/脐橙）
├── 县域气象模式（温度/降雨/灾害频率）
├── 县域特色作物（南昌莲藕、赣州脐橙、婺源茶叶...）
├── 县域农业政策（地方补贴、农技推广项目）
├── 县域农技站联系（人工升级渠道）
└── 县域土壤特征（红壤、水稻土、黄壤...）
```

---

#### T4.2 前端场景化体验升级 ⭐⭐⭐⭐

**目标**：从自由问答升级为场景化引导 + 结构化输入

```text
场景入口：
├── 🌾 病虫害诊断（结构化症状输入 → 诊断卡）
├── 🌱 种植方案（作物+地区+阶段 → 方案卡）
├── 🌡️ 天气农事（地区+日期 → 农事卡）
├── 📋 政策咨询（关键词+地区 → 政策卡）
├── 📊 知识图谱探索（实体搜索 → 关系图谱）
└── 📸 图片识别（上传图片 → 辅助诊断）
```

---

#### T4.3 数据治理与来源追溯 ⭐⭐⭐⭐⭐

**目标**：建立完整的数据来源登记、版本管理、许可证追溯体系

```text
数据源注册表：
├── 来源机构（name, url, type）
├── API/下载入口（endpoint, auth_type, quota）
├── 数据字段（fields, spatial_granularity, temporal_granularity）
├── 更新周期（update_frequency, delay, history_coverage）
├── 许可证（license, commercial_use, attribution）
├── 安全等级（A/B/C/D）
├── 版本（version, published_at, valid_until）
└── 责任人（owner, fallback_contact）
```

---

## 5. 开发优先级矩阵

| 优先级 | 任务 | 周期 | 风险 | 价值 |
|--------|------|------|------|------|
| **P0** | T1.2 BGE-M3 替换 | W1-2 | 低 | ⭐⭐⭐⭐⭐ |
| **P0** | T1.3 BM25 检索分支 | W2-3 | 低 | ⭐⭐⭐⭐ |
| **P0** | T1.4 RRF 融合 | W3 | 低 | ⭐⭐⭐⭐⭐ |
| **P0** | T2.1 查询理解 | W3-4 | 中 | ⭐⭐⭐⭐⭐ |
| **P0** | T2.4 知识库扩展 | W2-6 | 中 | ⭐⭐⭐⭐⭐ |
| **P0** | T3.2 AgriEval 评测 | W5-7 | 低 | ⭐⭐⭐⭐⭐ |
| **P1** | T1.1 知识图谱 | W1-4 | 高 | ⭐⭐⭐⭐⭐ |
| **P1** | T2.2 Reranker | W5-6 | 中 | ⭐⭐⭐⭐ |
| **P1** | T2.3 知识图谱自动化 | W5-8 | 高 | ⭐⭐⭐⭐ |
| **P1** | T3.3 病例管理 | W7-8 | 低 | ⭐⭐⭐⭐ |
| **P1** | T4.2 前端升级 | W8-10 | 中 | ⭐⭐⭐⭐ |
| **P2** | T3.1 大模型微调 | W7-10 | 高 | ⭐⭐⭐ |
| **P2** | T3.4 多模态图片 | W9-11 | 高 | ⭐⭐⭐ |
| **P2** | T4.1 县域数据 | W9-11 | 中 | ⭐⭐⭐⭐ |
| **P2** | T4.3 数据治理 | W10-12 | 中 | ⭐⭐⭐⭐ |

---

## 6. 技术栈选型决策

### 6.1 向量数据库

| 选项 | 当前 | 推荐 | 理由 |
|------|------|------|------|
| ChromaDB | ✅ 已用 | ✅ P0 保持 | 简单够用，迁移成本高 |
| pgvector | — | ✅ P1 评估 | 与 Spring Boot JPA 天然集成 |
| Milvus | — | ✅ P2 评估 | 百万级向量性能好 |

### 6.2 嵌入模型

| 选项 | 当前 | 推荐 | 理由 |
|------|------|------|------|
| LocalHashing | ✅ 已用 | ❌ 替换 | 无语义，精度差 |
| text-embedding-3-small | ✅ 可选 | ✅ 备选 | OpenAI API，成本可控 |
| BGE-M3 | — | ✅ **首选** | 开源、多语言、8192 token |

### 6.3 知识图谱

| 选项 | 推荐 | 理由 |
|------|------|------|
| Neo4j 5.x | ✅ **首选** | 生态成熟、Cypher 查询、社区版免费 |
| Apache AGE | ✅ 备选 | PostgreSQL 扩展，适合已有 PG 的场景 |
| Nebula Graph | ✅ 备选 | 分布式，适合大规模 |

### 6.4 Reranker

| 选项 | 推荐 | 理由 |
|------|------|------|
| BGE-Reranker-v2-M3 | ✅ **首选** | 多语言、轻量、效果好 |
| Cohere Rerank | ✅ 备选 | API 调用，简单但有成本 |
| Jina Reranker | ✅ 备选 | 多语言支持好 |

### 6.5 后端框架

| 选项 | 当前 | 推荐 | 理由 |
|------|------|------|------|
| FastAPI (Python) | ✅ 已用 | ✅ RAG 引擎保持 | Python AI 生态强 |
| Spring Boot (Java) | — | ✅ API 网关 + 管理服务 | 企业级、事务管理、微服务 |
| 混合架构 | — | ✅ **推荐** | 各取所长 |

---

## 7. 检索实验矩阵（A/B 测试计划）

每个实验固定同一批评测集、同一 embedding、同一生成模型，只改变检索阶段：

| 实验 | 配置 | 主要假设 | 上线条件 |
|------|------|----------|----------|
| B0 | 当前 Chroma + lexical 混合 | 建立可复现基线 | 所有实验必须超过或解释 B0 |
| E1 | BGE-M3 + Chroma | 嵌入质量提升 | Recall@5 提升 ≥ 5pp |
| E2 | E1 + BM25 + RRF | 精确匹配+语义召回 | Recall@5/MRR 提升 ≥ 5pp |
| E3 | E2 + Parent-Child 恢复 | 上下文完整性 | Faithfulness 提升 ≥ 3pp |
| E4 | E3 + BGE-Reranker | 精排质量 | Context Precision 提升 ≥ 5pp |
| E5 | E2 + Graph RAG | 结构化推理 | 图谱相关问题提升 ≥ 10pp |
| E6 | E4 + Multi-Query 分解 | 复杂问题拆解 | 复杂问题 Recall 提升 ≥ 8pp |

---

## 8. 数据治理与安全策略

### 8.1 证据等级

| 等级 | 数据源 | 可支撑结论 | 生产策略 |
|------|--------|------------|----------|
| **A** | 农业农村部/江西省厅正式文件、已审核知识库 | 政策、登记、技术规范、安全边界 | 主证据，记录发布日期和版本 |
| **B** | 中国气象数据、CAAS、FAOSTAT、科研机构公开数据 | 气象、统计、科研背景 | 显示时间/空间分辨率 |
| **C** | 百科、公开摘要、开放 API | 图片、补充资料 | 不覆盖 A 级结论 |
| **D** | 论坛、博客、未核验搜索 | 线索 | 默认不进入证据 |

### 8.2 安全边界

- **农药/肥料**：无 A 级 scope 匹配 → 输出 `guarded`，不给具体处方
- **病害诊断**：图片仅作辅助 → 必须结合文字观察 + 复查
- **政策信息**：必须带原文链接 + 发布日期 + 有效性标注
- **用户数据**：默认保存县/区级位置，不强制精确坐标
- **API Key**：只存后端 secret，前端不接触第三方凭据

### 8.3 可观测性

每次请求记录：
- `trace_id` / `thread_id` / `case_id`
- 检索分支贡献度（vector/graph/bm25/temporal）
- Reranker 延迟增量
- 模型调用次数 / token 消耗
- 外部来源失败率
- 证据等级分布

---

## 9. 交付物清单

### 代码交付

| 交付物 | 格式 | 说明 |
|--------|------|------|
| Neo4j Docker Compose | docker-compose.yml | 一键启动知识图谱 |
| BGEEmbeddingFunction | Python class | 替换本地哈希 |
| BM25Retriever | Python class | BM25 检索分支 |
| RRFEnsembler | Python class | 多路融合 |
| QueryTransformer | Python class | 查询理解 + 分解 |
| QueryRouter | Python class | 场景路由 |
| Reranker | Python class | 交叉编码器重排 |
| GraphRetriever | Python class | 知识图谱检索 |
| 知识图谱构建脚本 | Python script | 实体关系抽取 + 导入 |
| 500+ 评测集 | JSONL | 金标 + 禁止结论 |
| 评测脚本 | Python script | Ragas 集成 |
| CI 配置 | YAML | GitHub Actions |
| 10+ 知识包 | Markdown/JSON | 版本化知识包 |

### 文档交付

| 交付物 | 说明 |
|--------|------|
| 架构设计文档 | 本文档 |
| API 接口文档 | OpenAPI 3.0 |
| 知识图谱 Schema | 实体/关系/属性定义 |
| 数据源注册表 | 来源/许可证/版本 |
| 评测报告 | 每周离线报告 |
| 部署指南 | Docker + 本地开发环境 |

---

## 10. 90 天里程碑

### 第 1-3 周：基础设施

- [x] 项目现状分析
- [ ] Neo4j 部署 + 知识图谱 Schema 定义
- [ ] BGE-M3 嵌入模型替换 + 重新索引
- [ ] BM25 检索分支实现
- [ ] RRF 融合引擎实现
- [ ] 100+ 条评测集骨架

### 第 4-6 周：检索增强

- [ ] 查询理解 + Multi-Query 分解
- [ ] 场景路由（诊断/施肥/农时/政策/越界）
- [ ] BGE-Reranker 重排序
- [ ] 知识图谱构建脚本（从文档抽取实体关系）
- [ ] 知识库扩展到 20+ 知识包
- [ ] 300+ 条评测集

### 第 7-9 周：Agent 增强

- [ ] AgriEval 评测体系集成
- [ ] CI 自动化门控
- [ ] 病例管理与复查闭环
- [ ] 前端场景化入口
- [ ] 大模型微调评估（可选）

### 第 10-12 周：产品化

- [ ] 江西 11 地市县域数据体系
- [ ] 500+ 条评测集
- [ ] 试点用户测试（江农师生 + 农技人员）
- [ ] 发布报告 + 回滚脚本
- [ ] 下一阶段 Backlog

---

## 11. 头脑风暴：需要对齐的决策

### 11.1 技术决策

| 问题 | 选项 A（推荐） | 选项 B | 影响 |
|------|----------------|--------|------|
| 后端是否 Java 化？ | Python RAG + Java Gateway 混合 | 纯 Python 全栈 | 开发效率 vs 企业级 |
| 向量库是否迁移？ | P0 保持 Chroma，P1 评估 pgvector | 立即迁移 Milvus | 迁移成本 vs 性能 |
| 知识图谱是否必须？ | P1 构建，P0 先做 Hybrid RAG | 立即构建 | 开发周期 vs 技术价值 |
| 是否做模型微调？ | P2 评估，先用 API | 立即微调 | 数据需求 vs 效果提升 |

### 11.2 产品决策

| 问题 | 选项 A（推荐） | 选项 B | 影响 |
|------|----------------|--------|------|
| 首批试点用户 | 江农师生 + 农技人员 | 种植户 | 反馈深度 vs 覆盖面 |
| 是否支持图片诊断？ | 辅助参考，不自动确诊 | 自动确诊 | 安全责任 vs 便利性 |
| 是否接入真实气象？ | P1 接入 Open-Meteo | 先用静态数据 | 实时性 vs 复杂度 |
| 人工升级渠道 | 生成可审计摘要 | 自动外发 | 隐私保护 vs 效率 |

### 11.3 数据决策

| 问题 | 选项 A（推荐） | 选项 B | 影响 |
|------|----------------|--------|------|
| 知识图谱数据来源 | LLM 抽取 + 人工审核 | 众包 | 质量 vs 规模 |
| 农业论文入库方式 | 摘要+元数据（合规） | 全文（需授权） | 合规性 vs 信息量 |
| 用户数据保留 | 县/区级默认 | 精确坐标 opt-in | 隐私 vs 精准性 |

---

## 12. 风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| Neo4j 知识图谱构建复杂度高 | 高 | 先做 Hybrid RAG 验证价值，知识图谱作为 P1 |
| BGE-M3 本地推理需要 GPU | 中 | 先用 API，后续评估本地部署 |
| 农业文档解析质量差 | 中 | 建立文档质量门控，人工审核关键材料 |
| 评测集标注工作量大 | 中 | 分阶段标注，先 300 条再扩展 |
| 大模型微调数据不足 | 高 | 先用 AgriEval + 开源数据集，再补充自有数据 |
| 多模态图片识别准确率低 | 高 | 明确"辅助参考"边界，不自动确诊 |

---

## 附录：参考项目与资料

### 开源项目

| 项目 | 价值 | 地址 |
|------|------|------|
| **SEEDS** | 农业 RAG + KG 架构参考 | [github.com/SCAI-BIO/SEEDS](https://github.com/SCAI-BIO/SEEDS) |
| **AgriKG** | 农业知识图谱数据结构 | [github.com/qq547276542/Agriculture_KnowledgeGraph](https://github.com/qq547276542/Agriculture_KnowledgeGraph) |
| **AgriEval** | 农业 LLM 评测体系 | [github.com/YanPioneer/AgriEval](https://github.com/YanPioneer/AgriEval) |
| **Agri-Llama** | 简单农业 RAG Demo | [github.com/KaifAhmad1/Agri-Llama](https://github.com/KaifAhmad1/Agri-Llama) |
| **Crop GraphRAG** | 作物病虫害 GraphRAG | [Frontiers in Plant Science](https://www.frontiersin.org/articles/10.3389/fpls.2025.1696872/full) |
| **KissanAI** | 农业 Agent 方向 | [github.com/kissanai](https://github.com/kissanai) |

### 企业/科研参考

| 平台 | 价值 | 地址 |
|------|------|------|
| **中国农科院农业智能知识服务平台** | 真实科研级应用架构 | [aii.caas.cn](https://aii.caas.cn/) |
| **问稷（托普云农）** | 农业 AI Agent 产品形态 | [tpyn.net](https://www.tpyn.net/) |
| **识农AI（天天学农）** | 农业 AI 面向农户服务 | [ttxn.com](https://www.ttxn.com/) |
| **天工开悟** | 农业大模型应用 | [tgkwai.com](https://www.tgkwai.com/) |

### 技术参考

| 资料 | 价值 |
|------|------|
| BGE-M3 | 多语言嵌入模型，混合检索 |
| BGE-Reranker-v2-M3 | 交叉编码器重排序 |
| Neo4j | 知识图谱存储与查询 |
| Ragas | RAG 评测框架 |
| BRAG 教程 | RAG 工程最佳实践 |
| LangChain Retriever | 检索器集成参考 |

---

> **本文档由 DeepSeek-V4-Pro 编制，基于 2026-08-20 最新搜索资料和项目分析。**
