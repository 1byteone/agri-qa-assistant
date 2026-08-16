# 传习教育 AI Search/RAG 学习文档系列 — 设计文档

日期：2026-08-16
状态：待用户审阅

## 1. 专业 Goal

面向"江西传习教育科技有限公司"（化名，教育科技定位）的真实业务场景，把简历中的 4 条实习经历转化为 **2 条产品线 × 4 个能力域** 的可演示项目作品集。每一册学习文档 = 1 个真实企业案例/用户故事 → 用案例驱动学习技术 → 用实验复现简历数字 → 用面试叙事讲清因果。核心原则是**干中学，学中用**：不背名词，每个技术点都能回到业务问题、数据、代码和指标。

简历数字（72%→89%、61%→87%、180ms→65ms、零结果率降52%、长尾CVR+18%）必须在本项目固定 qrels/QA 集与基准配置上可复现，否则不写入简历。

## 2. 场景设定

### 2.1 公司背景（化名）

- 公司定位：教育科技公司，面向 K12 与职业教育提供"智能学习 + 教研数字化"产品。
- 品牌世界观：公司名取"传习"（源自王阳明《传习录》，知行合一），产品线化名如下。

### 2.2 两条产品线

```
江西传习教育科技有限公司（教育科技）
├── 产品线1：传习智学 · 学习资源搜索
│     学生/老师/家长用自然语言搜索课程、题目、教辅、讲义、名师视频。
│     被检索的"商品" = 教育资源（含课程包，带出"课程即商品"的商城视角）。
│     ← 对应简历"AI商品搜索混合检索"经历
│
└── 产品线2：传习智答 · 教研知识库 RAG
      教研资料（课程标准/教案/制度/通知/招生政策/教资面试题库）入库，
      教师、教务、新员工、备考学生问答。
      ← 对应简历"企业级RAG知识库"经历
```

### 2.3 固定人物角色（跨册复用，增强连续性）

| 角色 | 身份 | 主要痛点 | 主要出现在 |
| --- | --- | --- | --- |
| 小陈 | 高二学生 | 搜"圆锥曲线怎么学提分快"匹配不到"椭圆/双曲线/抛物线" | 01、02、03、05 |
| 周主任 | 教研组长 | 搜"人教A版必修二导数教案"被旧教案干扰，要求精确教材编号 | 01、02、03、04 |
| 王老师 | 新入职教师 | 不熟悉制度，问"教案提交规范是什么" | 04、05、06 |
| 李教务 | 教务老师 | 搜"2024秋季课程调整通知"，常问多跳问题 | 05、06 |
| 备考学员 | 教资面试考生 | 搜"教资面试结构化真题"，口语化、缩略词多 | 03、05 |
| 数据产品同学（"我"） | 实习算法/产品 | 复现简历数字、写实验、做评测、提需求 | 全册（第一人称） |

### 2.4 场景驱动的黄金句式

每册"企业案例"一节以固定句式收尾，把业务痛点翻译成技术问题：

```text
业务痛点：<用户语言描述的失败现象>
技术问题：<本册要解决的技术概念>
业务指标：<Recall@10 / MRR / Faithfulness / P99 等>
```

## 3. 交付物：docs/learn/ 十册系列

新建 `docs/learn/` 目录，10 个文件（按简历能力域分组编号）：

| 册 | 文件 | 能力域 | 简历条目 |
| --- | --- | --- | --- |
| 00 | 学习总纲与导航 | 导航 | 全部 |
| 01 | AI搜索-Embedding与BGE-M3 | 搜索 | "基于BGE-M3模型构建Faiss向量索引" |
| 02 | AI搜索-Faiss与混合检索 | 搜索 | 同上 + BM25/RRF |
| 03 | AI搜索-QueryRewrite与结果融合 | 搜索 | "Query改写与结果融合，Top-10 72%→89%" |
| 04 | RAG工程-文档解析与分块 | RAG | "文档解析与分块Pipeline，Recursive Splitter" |
| 05 | RAG工程-端到端RAG | RAG | "问答准确率61%→87%" |
| 06 | 效果评估-RAGAS与检索指标 | 评估 | "RAGAS评测代码，200条标注集，多跳短板" |
| 07 | 效果评估-BadCase与AB测试 | 评估 | 产品岗：2万日志、零结果率降52%、CVR+18%、人工评测 |
| 08 | 工程优化-HNSW性能调优 | 优化 | "调整HNSW索引参数，P99 180ms→65ms" |
| 09 | 工程优化-ONNX量化 | 优化 | "ONNX Runtime量化Embedding模型" |

### 3.1 每册统一结构（六段式）

```text
# <册名>
## 0 企业案例与用户故事   ← 场景驱动开头（1~2 屏完整案例，含角色/痛点/业务目标，黄金句式收尾）
## 1 原理直觉             ← 为什么存在这个问题、核心概念一句话讲清、配示意图
## 2 最小实验             ← 可运行代码 + 预期输出（复用/指向现有 phase 代码与 notebooks）
## 3 简历映射             ← 这条简历数字怎么在项目里复现、口径怎么说圆、实验记录链接
## 4 面试深挖             ← 5~8 个连续追问 + 参考答案（必须结合实验，不背书）
## 5 参考资料             ← 本次 anysearch 提取要点 + 来源链接
```

实验代码一律指向现有 `phase1_doc_parser/`、`phase2_semantic_search/`、`phase3_optimization_eval/`、`phase4_mini_rag_system/`，不在文档里粘贴大段新代码；`00 总纲` 统一给出每个实验的运行命令。

### 3.2 每册案例与内容要点

- **01 Embedding 与 BGE-M3**：周主任搜"人教A版必修二导数教案"被旧教案干扰 → 关键词匹配不识别语义 → 引出向量与余弦相似度、BGE-M3 的 dense/sparse/colbert 三输出；实验：numpy 手写 cosine + `BGEM3FlagModel` 编码；简历：BGE-M3 归一化、为何不需 query 指令；面试：为什么两文本能算相似度、稠密/稀疏/多向量怎么选。
- **02 Faiss 与混合检索**：引入语义召回后长尾提升，但"2024高考数学真题""MBP-M3MAX-32-1TB"式精确词反而变差 → 引出 BM25 + Dense + RRF；实验：`IndexFlatIP`/`IndexHNSWFlat` + BM25 对照 + RRF 融合，Recall@10/MRR；面试：Faiss 与 MySQL 区别、HNSW 为何比暴力快、何时不该用向量检索。
- **03 QueryRewrite 与融合**：备考学员搜"教资面试结构化真题"口语化缩略词多 → LLM 改写为多 Query → 融合；实验：rewrite ablation（before/after Recall@10、Bad Case）；简历：72%→89% 口径 = 固定 qrels 上 Recall@10，改写引入错误意图的反例；面试：改写何时伤害结果、expansion 对 BM25 还是 Dense 收益大、HyDE 是什么。
- **04 文档解析与分块**：李教务上传《2024版高中数学课程标准》PDF，5000+ 篇文档入库，排版乱、章节长 → 引出 parser + Recursive Splitter + overlap；实验：运行 phase1 parser，对比 fixed vs recursive chunk 策略；简历：为何 Recursive Splitter 适合中文知识库、overlap 的成本算术；面试：为什么不能整篇 PDF 直接 Embedding、overlap 过大的代价。
- **05 端到端 RAG**：王老师问制度、李教务问多跳 → 文档上传→问答→带引用；实验：跑 phase4 Mini RAG，evidence-first 引用；简历：61%→87% 的"准确率"定义必须写明口径（人工通过率/RAGAS）；面试：RAG 与微调区别、引用为何不准、多跳为何难。
- **06 RAGAS 与检索指标**：需要量化"从 61% 到 87%"，构建 200 条 QA 标注集 → RAGAS Faithfulness/Answer Relevancy/Context Precision/Recall；实验：跑 phase3 评测，先手写 Recall@10/MRR 再上 RAGAS；简历：三个指标各解决什么问题、为什么需要人工评测；面试：Faithfulness 是什么、LLM-as-judge 的坑。
- **07 BadCase 与 A/B 测试**：产品岗——2 万条搜索日志梳理 3 类痛点（自然语言找货/属性模糊匹配…）、零结果率降 52%、Query 改写长尾 CVR+18%、3 名标注员 200 条 QA 人工评测；实验：日志样本分类 + A/B 计划模板（沿用 `docs/templates/AB_test_plan.md`）；面试：为什么不能直接比两个版本 CTR、novelty 效应、多指标假阳性。
- **08 HNSW 性能调优**：题库向量从 1 万涨到 50 万，P99 180ms 不可接受 → HNSW M/efConstruction/efSearch 参数扫描；实验：benchmark 脚本，画 Recall-P99 表（efSearch 20/50/100/200）；简历：P99 口径需说明请求次数、是否含冷启动；面试：三参数分别影响什么、为什么不能一味追 Recall。
- **09 ONNX 量化**：BGE-M3 在 CPU 服务器上推理慢 → ONNX 导出 + INT8/FP16 量化；实验：对照原模型 vs ONNX vs INT8 的 Recall@10/Latency/Memory；面试：ONNX 为何能提速、INT8 掉点如何决策上线、静态 vs 动态量化。

### 3.3 00 总纲内容

- 4 大能力域地图 + 2 条产品线场景总览（人物角色表）
- 推荐学习顺序（与 `docs/zero-to-one-roadmap.md` 的关系）
- 每个实验的启动命令清单 + 产出落盘位置
- 简历数字 → 实验 → 报告 的口径对照表
- 面试 Q&A 索引（各册"面试深挖"问题总表）

## 4. 存量文档迁移范围（同步替换世界观）

现有"星河商店 + 证据仓库"趣味世界观统一替换为"传习教育"场景，保持全仓库口径一致：

| 文件 | 改动 |
| --- | --- |
| `docs/alignment.md` | 场景/数据默认值更新为传习教育设定；明确化名口径 |
| `docs/internship-experience-execution-plan.md` | 趣味世界观表 → 传习教育；案例/Query 示例替换 |
| `README.md` | 增加 `docs/learn/00` 导航；世界观一句带过 |
| `docs/project-charter.md` | 在 scope 说明传习教育两条产品线（小改） |
| `docs/research-sources.md` | 追加本次 anysearch 新来源，保留原来源 |
| `notebooks/` | 本次不动（后续批次），仅 README 标注新导航 |

`docs/learn/` 系列是新文档，直接按传习教育世界观编写。两套世界观不允许并存。

## 5. 参考资料（本次 anysearch 提取要点）

本次已用 anysearch 完成 12 组检索，覆盖：BGE-M3 官方文档/HF/NVIDIA/Milvus/论文、Faiss HNSW 参数与 benchmark（zilliz/opensearch/pinecone/marqo/markaicode）、混合检索与 RRF（weaviate/digitalapplied/bigdataboutique）、Query Rewrite 与 HyDE（thegeocommunity/arxiv DMQR/medium）、Reranker 与 cross-encoder（bigdataboutique/mixpeek）、Chunking（Azure/NVIDIA/firecrawl/multigrid/aliyun/datawhale/themainthread/orrrrz）、RAGAS（docs.ragas.io/evalhub/dev.to/nvidia/IBM）、检索指标（towardsai/weaviate/zenn）、A/B 测试（growthbook/algorithmic/algolia）、Bad Case 分类（wizzy/SMOCC/nobi）、ONNX 量化（onnxruntime.ai/medium/nixiesearch）、语义 vs 关键词（prakhartripathi/hakia/netguru/knovo）。

各册"参考资料"节直接从上述来源摘取要点并附链接，不重复造轮子。详细来源与要点摘要见各册附录。

## 6. 工作约定（沿用 evidence-first）

- 每个实验保留 baseline，只改一个主变量。
- 所有性能/效果数字必须绑定：数据集、模型版本、硬件、参数、命令。
- 简历数字只能以本项目固定评测集上的复现结果为准。
- 失败实验也记录原因。
- 化名规则：公司=传习教育（教育科技）；产品=传习智学/传习智答；人物=第 2.3 节角色表。

## 7. 验收标准

1. `docs/learn/00~09` 十册全部落盘，每册包含六段式结构且以企业案例开头。
2. 每册"简历映射"能回答：简历该数字如何复现、口径是什么、证据文件在哪。
3. README 与 `docs/alignment.md`、`execution-plan` 世界观一致，无"星河商店"残留。
4. 每册"面试深挖"问题能由本册实验内容独立回答，无空泛背书。
5. 参考资料节保留权威来源链接。

## 8. 本次执行范围（Session 边界）

本次先交付：`docs/learn/` 十册 + 存量文档迁移（alignment/execution-plan/README/project-charter/research-sources）。notebooks 的改造、实验代码的新增属于下一批次，不在本次范围。
