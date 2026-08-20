# 🌾 CropWise - 江西农业智能知识服务平台

<p align="center">
  <img src="docs/marketing-kit/screenshots/chat-streaming.png" alt="CropWise Demo" width="800">
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Next.js-14-black" alt="Next.js 14"></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-3.11+-blue" alt="FastAPI"></a>
  <a href="#"><img src="https://img.shields.io/badge/LangGraph-Agent-purple" alt="LangGraph"></a>
  <a href="#"><img src="https://img.shields.io/badge/ChromaDB-VectorDB-orange" alt="ChromaDB"></a>
  <a href="#"><img src="https://img.shields.io/badge/BGE--M3-Embedding-1024d-green" alt="BGE-M3"></a>
  <a href="#"><img src="https://img.shields.io/badge/Neo4j-KnowledgeGraph-5.x-red" alt="Neo4j"></a>
</p>

<p align="center">
  <b>基于 Hybrid RAG + GraphRAG + 农业知识图谱的智能问答系统</b><br>
  集成 ChromaDB 向量库 · Neo4j 知识图谱 · BGE-M3 嵌入 · Reranker 重排序 · 多轮对话记忆
</p>

---

## ✨ 核心特性

<table>
<tr>
<td width="25%">
<h3>🔍 Hybrid RAG</h3>
<p>Vector + BM25 + RRF 融合 + BGE-Reranker 重排序，多路召回精准匹配</p>
</td>
<td width="25%">
<h3>📊 知识图谱</h3>
<p>Neo4j 农业知识图谱，12 类实体 + 16 类关系，支持结构化推理</p>
</td>
<td width="25%">
<h3>🧠 Multi-Query</h3>
<p>复杂问题自动分解为多个子查询，并行检索后 RRF 融合</p>
</td>
<td width="25%">
<h3>🎨 Liquid Glass UI</h3>
<p>Apple 风格毛玻璃设计、流畅动画、响应式布局</p>
</td>
</tr>
<tr>
<td>
<h3>💬 智能对话</h3>
<p>SSE 流式响应、决策卡、知识溯源、专业词条注释</p>
</td>
<td>
<h3>🔍 作物诊断</h3>
<p>结构化症状输入 → 智能诊断 → 证据来源背书</p>
</td>
<td>
<h3>📅 农事日历</h3>
<p>基于作物、地区、生长阶段的智能农事安排</p>
</td>
<td>
<h3>📋 政策咨询</h3>
<p>检索惠农政策证据，A 级来源背书，可追溯验证</p>
</td>
</tr>
</table>

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────────────────┐
│                    前端：Next.js 14 + shadcn/ui                   │
│    Apple Liquid Glass 风格 · 毛玻璃效果 · 流畅动画 · 响应式布局    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP/SSE
┌──────────────────────────▼───────────────────────────────────────┐
│                 后端：FastAPI + LangGraph Agent                    │
│  Domain Guard → Query Router → RAG Pipeline → LLM → Post-process │
│  6 工具：作物知识 · 生长周期 · 农事天气 · 网页获取 · 资源搜索 · 时间  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│              Hybrid Retrieval Layer (混合检索层)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Vector   │  │ BM25     │  │ Graph    │  │ Temporal │        │
│  │ (BGE-M3) │  │ (Lucene) │  │ (Neo4j)  │  │ (时间衰减) │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └──────────────┼──────────────┼──────────────┘             │
│                      │     RRF Fusion │                          │
│                      └────────┬───────┘                          │
│                               │                                  │
│                      ┌────────▼────────┐                         │
│                      │  BGE-Reranker    │                         │
│                      │  (交叉编码器精排)  │                         │
│                      └────────┬────────┘                         │
└───────────────────────────────┼──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                         Storage Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ ChromaDB │  │ Neo4j    │  │ SQLite   │  │ Redis    │       │
│  │ (向量库)  │  │ (知识图谱)│  │ (记忆)    │  │ (缓存)    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Agnes AI API Key

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/1byteone/agri-qa-assistant.git
cd agri-qa-assistant

# 2. 后端
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000

# 3. 前端（新终端）
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:3000
```

### 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env，填入 AGNES_AI_API_KEY
```

### 导入知识包

```bash
cd backend
python import_knowledge_packs.py
# 将 10 个农业知识包导入 ChromaDB
```

### 启动 Neo4j（可选）

```bash
# Docker 方式
docker compose -f docker-compose.neo4j.yml up -d

# 导入种子数据
python kg/import_seeds.py
```

---

## 📊 知识库规模

| 类型 | 数量 | 说明 |
|------|------|------|
| **知识包** | 10 个 | 水稻病虫害/脐橙/油菜/肥料/农时/政策/灌溉/土壤/农机/蔬菜 |
| **文档块** | 122+ 块 | 结构化 Markdown 知识包 |
| **默认文档** | 19 篇 | 基础农业知识（种植/病虫害/肥料/土壤/农机） |
| **评测样本** | 15 条 | 诊断/施肥/天气/政策/安全场景 |
| **知识图谱** | 64 实体 | 12 类实体 + 16 类关系（种子数据） |
| **数据源** | 12 个 | A/B/C/D 四级来源登记 |

---

## 🔧 检索增强架构

### Hybrid RAG Pipeline

```
用户问题
  → QueryTransformer.multi_query()
    实体提取 + 意图检测 + Multi-Query 分解
  → 多子查询并行检索
    ├─→ Vector Branch (BGE-M3 / ChromaDB)
    ├─→ BM25 Branch (中文农业分词)
    └─→ RRF Fusion (k=60, 分支加权)
  → Reranker (BGE-Reranker-v2-M3)
    交叉编码器精排，top-30 → top-5
  → 证据门控 + 决策卡生成
  → SSE 流式输出
```

### 知识图谱 Schema

```
实体类型 (12):
├── Crop（作物）         ├── Disease（病害）
├── Pest（虫害）         ├── Chemical（农药）
├── Fertilizer（肥料）   ├── Variety（品种）
├── Region（地区）       ├── Policy（政策）
├── Measure（技术措施）   ├── GrowthStage（生育期）
├── Symptom（症状）      └── Document（文档/证据）

关系类型 (16):
├── SUSCEPTIBLE_TO    作物易感病虫害
├── CONTROLLED_BY     病虫害被药剂防治
├── APPLIES_TO        药剂适用于作物
├── SUITABLE_FOR_REGION 作物适宜地区
└── ... (共 16 类)
```

---

## 📡 API 接口

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/stream` | SSE 流式对话 |
| POST | `/chat` | 非流式对话 |
| GET | `/health` | 健康检查 |
| GET | `/system/info` | 系统信息 |

### 检索接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/retrieval/hybrid` | 混合检索诊断 |
| GET | `/retrieval/multi-query` | Multi-Query 分解 |
| GET | `/knowledge-base/search` | 知识库搜索 |
| GET | `/knowledge-base/status` | 知识库状态 |

### 知识图谱接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-graph/status` | 知识图谱状态 |
| GET | `/knowledge-graph/entity/{name}` | 实体邻域查询 |
| GET | `/knowledge-graph/search` | 全文搜索实体 |
| POST | `/knowledge-graph/build` | 构建知识图谱 |

### 知识包接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-packs` | 列出知识包 |
| POST | `/knowledge-packs/import` | 导入知识包 |

### 评测接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/evaluations/agri-eval` | 运行 AgriEval 评测 |
| GET | `/evaluations/retrieval` | 检索评测 |
| GET | `/evaluations/items` | 评测条目列表 |

### 病例管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/cases` | 创建病例 |
| GET | `/cases` | 列出病例 |
| GET | `/cases/{id}` | 病例详情 |
| GET | `/cases/{id}/timeline` | 病例时间线 |
| POST | `/cases/{id}/escalate` | 升级病例 |
| POST | `/cases/{id}/resolve` | 解决病例 |

---

## 🧪 测试

```bash
cd backend

# 运行所有测试（75+ 项）
python -m pytest test_w2_integration.py retrieval/ -v

# 运行知识图谱测试
python kg/import_seeds.py

# 运行知识包导入测试
python import_knowledge_packs.py
```

---

## 📁 项目结构

```
agri-qa-assistant/
├── backend/                    # FastAPI 后端
│   ├── main.py                # 主应用入口（API 路由）
│   ├── agent.py               # LangGraph Agent
│   ├── knowledge_base.py      # ChromaDB 知识库 + 混合检索
│   ├── memory.py              # SQLite 对话记忆
│   ├── tools.py               # 农业工具 + MCP
│   ├── agriir_pipeline.py     # RAG 检索管道
│   ├── config.py              # 配置管理
│   ├── schemas.py             # Pydantic 模型
│   ├── case_manager.py        # 病例管理
│   ├── source_registry.py     # 数据源注册表
│   ├── knowledge_pack_importer.py  # 知识包导入器
│   ├── retrieval/             # 检索增强模块
│   │   ├── bge_m3_embedding.py    # BGE-M3 嵌入
│   │   ├── bm25_retriever.py      # BM25 检索
│   │   ├── reranker.py            # BGE-Reranker 重排序
│   │   ├── rrf_fusion.py          # RRF 融合
│   │   ├── query_transformer.py   # 查询改写 + Multi-Query
│   │   ├── query_router.py        # 查询路由
│   │   └── parent_child.py        # 父子文档索引
│   ├── kg/                    # 知识图谱模块
│   │   ├── schema.py          # 实体/关系 Schema
│   │   ├── connection.py      # Neo4j 连接
│   │   ├── builder.py         # 知识图谱构建器
│   │   ├── pipeline.py        # LLM 驱动构建 Pipeline
│   │   └── import_seeds.py    # 种子数据导入
│   ├── evaluation/            # 评测模块
│   │   └── agri_eval_runner.py    # AgriEval 评测运行器
│   └── data/                  # 数据存储
├── frontend/                   # Next.js 前端
├── data/
│   ├── knowledge-packs/       # 10 个农业知识包
│   │   ├── jiangxi-rice-pest-control.md
│   │   ├── gannan-citrus-management.md
│   │   ├── jiangxi-rapeseed-management.md
│   │   ├── national-fertilizer-standards.md
│   │   ├── jiangxi-county-calendar.md
│   │   ├── jiangxi-agri-subsidy.md
│   │   ├── water-conservation-irrigation.md
│   │   ├── soil-management.md
│   │   ├── jiangxi-agri-machinery.md
│   │   └── vegetable-cultivation.md
│   └── evals/                 # 评测集
│       └── agri_eval_subset.jsonl
├── docs/                      # 文档
├── docker-compose.neo4j.yml   # Neo4j Docker 配置
├── import_knowledge_packs.py  # 知识包导入脚本
└── .github/workflows/ci.yml   # CI 流水线
```

---

## 🛠️ 技术栈

| 维度 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Python 3.10+ | 异步高性能 |
| **Agent 架构** | LangGraph | 工具循环 + 状态管理 |
| **向量数据库** | ChromaDB | 本地持久化 |
| **嵌入模型** | BGE-M3 (1024d) / LocalHashing | 多语言语义嵌入 |
| **关键词检索** | BM25 (中文农业分词) | 精确术语匹配 |
| **融合算法** | RRF (k=60) | 多路排序融合 |
| **重排序** | BGE-Reranker-v2-M3 | 交叉编码器精排 |
| **知识图谱** | Neo4j 5.x | 实体-关系存储 |
| **LLM** | Agnes AI / Qwen / DeepSeek | 大语言模型 |
| **前端** | Next.js 14 + shadcn/ui | React 全栈 |
| **评测** | Ragas + AgriEval | RAG 质量评测 |

---

## 📈 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| Top-5 专家证据召回 | ≥ 85% | 基于专家金标 |
| 引用覆盖率 | ≥ 90% | 每个结论可追溯 |
| 高风险安全提醒 | 100% | 农药/剂量/间隔期 |
| 非农业越界率 | < 1% | Domain Guard |
| SSE 完整结束率 | ≥ 99% | done/error 明确 |
| P95 首字延迟 | ≤ 3s | 本地知识库 |

---

## 🗺️ 开发路线图

### ✅ 已完成 (W1-W6)

- [x] BGE-M3 嵌入模型集成
- [x] BM25 关键词检索分支
- [x] RRF 多路融合引擎
- [x] QueryTransformer Multi-Query 分解
- [x] BGE-Reranker 重排序
- [x] Neo4j 知识图谱 Schema + 种子数据
- [x] 知识图谱构建 Pipeline
- [x] 10 个农业知识包（122 块）
- [x] AgriEval 评测运行器
- [x] 数据源注册表（12 个来源）
- [x] GitHub Actions CI 流水线
- [x] API 接口文档

### 🔜 进行中

- [ ] Neo4j Docker 部署 + 生产验证
- [ ] 前端场景化入口 + 来源抽屉
- [ ] 病例管理前端组件
- [ ] 500+ 条评测集扩展

### 📋 规划中

- [ ] 多模态图片识别（病害诊断）
- [ ] 农业大模型 LoRA 微调
- [ ] 江西 11 地市县域数据体系
- [ ] 微信小程序端

---

## 📄 License

MIT © 2026 江西农业大学

---

<p align="center">
  <b>江西农业大学 · 农业智能技术研究团队</b><br>
  <a href="https://github.com/1byteone/agri-qa-assistant">GitHub</a> ·
  <a href="docs/agri-qa-future-development-plan.md">开发计划</a>
</p>
