# AI Search/RAG 实习经历执行蓝图

这份蓝图把你的简历描述拆成可以真实练习、真实复现、面试能深挖的项目任务。核心原则是：趣味性服务于记忆和坚持，但所有数字、方案和故事都必须能回到代码、数据、参数和实验记录。

## 1. 专业 Goal

在 8 周内完成一个双场景 AI Search/RAG 项目作品集：

1. 商品搜索场景：围绕“自然语言找货”和“属性模糊匹配”，实现 BM25、BGE-M3/Faiss、RRF Hybrid、Query rewrite、Recall@10/MRR@10 评测。
2. 企业知识库场景：围绕“文档上传 -> 解析分块 -> 检索问答 -> 反馈评测”，实现 PDF/Markdown 解析、Recursive Splitter、Mini RAG API、引用展示、RAGAS 或等价质量评估。
3. 性能与产品场景：围绕“质量不掉、延迟下降、指标可解释”，完成 HNSW 参数扫描、ONNX/INT8 可行性验证、P50/P95/P99 记录、PRD、A/B 测试方案和 Bad Case 分析。

最终你要能把每条简历素材讲成这样的闭环：

```text
业务问题 -> 数据样本 -> baseline -> 技术方案 -> 实验参数 -> 指标变化 -> 失败样本 -> 下一步
```

## 2. 企业案例与业务场景：传习教育双产品线

项目世界观采用"江西传习教育科技有限公司"（化名，教育科技）的双产品线设定，但所有对象都映射到真实工程概念。完整角色表见 `docs/learn/00-学习总纲与导航.md`。

| 场景对象 | 真实含义 | 你要留下的证据 |
| --- | --- | --- |
| 传习智学·学习资源搜索 | 教育资源搜索系统（课程/题目/教辅/讲义，"课程即商品"） | 资源 JSON、Query 标注集、Recall/MRR 报告 |
| 找课侦探 | 搜索 Bad Case 分析 | 零结果 Query、错召回 Query、需求拆解文档 |
| 传习智答·教研知识库 | 企业 RAG 知识库（课标/教案/制度/通知） | PDF/Markdown 解析产物、chunk 元数据、引用回答 |
| 速度试炼场 | 检索性能优化 | P50/P95/P99、HNSW 参数、ONNX/INT8 对照 |
| 评测审判台 | 自动化和人工评测 | qrels、QA 标注、Faithfulness/Relevance 明细 |

可用的业务 Query 示例：

| Query | 场景 | 面试官深挖时你要能解释 |
| --- | --- | --- |
| `想找一款适合露营的轻便保温杯，别太贵`（映射到教育：`想找适合高三冲刺的物理专题课，别太贵`） | 自然语言找货 | Query rewrite 如何抽取品类、场景、价格偏好；BM25 和 Dense 各召回了什么 |
| `蓝牙耳机 降噪 通勤 续航久`（映射到教育：`导数 圆锥曲线 高考 压轴题`） | 属性模糊匹配 | 属性字段是否参与索引；Dense 对同义词的帮助；Hybrid 为什么比单路召回稳 |
| `知识库上传 PDF 后为什么有些页码引用不准` | RAG 运维问答 | PDF parser 如何保留 page；chunk overlap 如何影响引用边界 |
| `多跳问题为什么准确率低`（`这学期数学课改后高考大纲考点有哪些变化`） | RAG 质量分析 | 单跳/多跳标注如何区分；检索失败和生成失败如何拆开看 |

这些例子可以有一点故事感，但不能把"魔法课程""虚构能力"写进最终实验结论。最终报告只使用真实字段、真实参数和真实指标。

## 3. 简历条目到可执行任务

### 3.1 AI 商品搜索混合检索

目标条目：

```text
参与 AI 商品搜索混合检索链路开发，负责语义召回模块的实现与调优：
基于 BGE-M3 模型构建 Faiss 向量索引，编写 Query 改写与结果融合逻辑，
使 Top-10 召回率从 72% 提升至 89%。
```

执行拆解：

| 步骤 | 任务 | 交付物 |
| --- | --- | --- |
| 1 | 构造 500 条商品记录，字段含 `id/title/category/attributes/description` | `data/products/*.json` |
| 2 | 标注 50 条 Query，每条至少 1 个相关商品 ID | `docs/templates/qrels.example.json` 的真实副本 |
| 3 | 跑 BM25 baseline，记录 Recall@10/MRR@10 | `data/processed/phase2_bm25_baseline.json` |
| 4 | 做规则型 Query rewrite ablation，先验证属性归一化收益 | `docs/phase2-product-query-rewrite-ablation.md` |
| 5 | 接入 BGE-M3 embedding 与 Faiss Flat/HNSW | `phase2_semantic_search/embedding.py`、`index_builder.py` |
| 6 | 实现 RRF 融合，单独开关 Dense 与 Query rewrite | `hybrid_search.py`、实验日志 |
| 7 | 对比 BM25/Dense/Hybrid/Hybrid+rewrite | Phase 2 报告 |

面试深挖点：

- BGE-M3 输出向量如何归一化？为什么 cosine 和 inner product 不能混用得不明不白？
- Faiss Flat 与 HNSW 的差异是什么？HNSW 的 `M/efConstruction/efSearch` 分别影响什么？
- Query rewrite 是否可能引入错误意图？你如何用 ablation 证明它有贡献？
- 72% 到 89% 只能作为复现实验结果写入简历，不能在没有固定 qrels 时提前承诺。

### 3.2 企业级 RAG 文档解析与分块

目标条目：

```text
完成企业级 RAG 知识库的文档解析与分块 Pipeline：
实现 PDF/Markdown 多格式解析器，设计 Recursive Splitter 分块策略，
处理 5000+ 篇文档入库，问答准确率从 61% 提升至 87%。
```

执行拆解：

| 步骤 | 任务 | 交付物 |
| --- | --- | --- |
| 1 | 先用 20 篇样本文档验证 parser，再扩展到更大语料 | `document_inventory.json` |
| 2 | 对比 `chunk_size/overlap/separator` 的 3 组实验 | `phase1_chunk_experiment.json` |
| 3 | 保留 `source/page/headings/chunk_id` 元数据 | `chunks.json` |
| 4 | 用固定 QA 集评估不同分块策略对检索的影响 | Phase 3 单变量实验 |
| 5 | 对无法回答、多跳、引用错误样本分类 | 周度效果报告 |

面试深挖点：

- 为什么 Recursive Splitter 比固定长度截断更适合中文知识库？
- overlap 过大会带来什么成本？如何影响索引大小、召回重复和上下文噪声？
- “5000+ 篇”必须能说明平均页数、总 chunk 数、处理耗时和失败文件比例。
- “准确率 61% 到 87%”必须说明准确率定义：人工评测通过率、RAGAS 指标，还是 answer exactness。

### 3.3 向量检索性能优化

目标条目：

```text
通过 ONNX Runtime 量化 Embedding 模型、调整 HNSW 索引参数，
将单次语义检索 P99 延迟从 180ms 降至 65ms。
```

执行拆解：

| 步骤 | 任务 | 交付物 |
| --- | --- | --- |
| 1 | 固定硬件、线程数、batch size、文本长度 | Benchmark 配置 |
| 2 | 建立 FP32 baseline，做 warmup 后测 P50/P95/P99 | `phase3_timing_baseline.json` |
| 3 | 验证 ONNX 输出与原模型 cosine similarity | 一致性报告 |
| 4 | 扫描 HNSW 参数，画质量-延迟表 | `phase3_single_variable_experiments.json` |
| 5 | 同时报告 Recall@10 变化，避免只追速度 | Phase 3 报告 |

面试深挖点：

- 你优化的是 embedding 推理、向量检索，还是整个 `/search` API？
- P99 需要多少次请求才可信？是否包含冷启动和模型加载？
- INT8 量化后如果 Recall 掉了，如何决定是否上线？

### 3.4 RAG 自动化评估与产品分析

目标条目：

```text
基于 RAGAS 编写 Faithfulness/Relevance 评测代码，构建 200 条标注测试集；
梳理搜索日志、PRD、A/B 测试和人工评测，支撑版本上线。
```

执行拆解：

| 步骤 | 任务 | 交付物 |
| --- | --- | --- |
| 1 | 设计 200 条 QA 标注规范，含不可回答和多跳样本 | `qa-eval.json` |
| 2 | 记录 RAGAS 使用的评审模型、温度、失败重试和成本 | 评测日志 |
| 3 | 将 Bad Case 分为无召回、错召回、召回对但回答错 | 周报 |
| 4 | 写 PRD：文档上传、问答、引用、反馈闭环 | `docs/PRD.md` |
| 5 | 写 A/B 测试计划：zero-result rate、CTR、CVR、长尾 Query | `docs/AB_test_plan.md` |

面试深挖点：

- Faithfulness 和 Relevance 分别解决什么问题？
- 为什么人工评测仍然需要？标注员之间不一致怎么办？
- Query rewrite 对长尾词 CVR +18% 是怎样分流和统计的？

## 4. 8 周执行节奏

| 周 | 主题 | 必须产出 | 复盘问题 |
| --- | --- | --- | --- |
| 1 | 文档解析与元数据 | parser、inventory、失败样本 | 哪些文件会破坏解析稳定性？ |
| 2 | Recursive Splitter | chunk 实验、分块报告 | chunk 边界如何影响引用？ |
| 3 | BM25 与 qrels | 50 条 Query 标注、BM25 baseline | baseline 错在哪里？ |
| 4 | BGE-M3/Faiss/Hybrid | Dense、HNSW、RRF 对照 | Hybrid 的收益来自哪里？ |
| 5 | Query rewrite 与 Bad Case | ablation、需求拆解 | rewrite 什么时候会伤害结果？ |
| 6 | 性能优化 | ONNX/HNSW benchmark | 延迟下降是否牺牲质量？ |
| 7 | RAG 评估 | 200 条 QA、RAGAS/人工评测 | 失败样本如何分类？ |
| 8 | 产品化与面试包 | Demo、PRD、AB plan、技术报告 | 3 分钟内如何讲清闭环？ |

## 5. 今天开始的最小执行任务

先完成第一个可验证闭环，不急着下载大模型：

1. 运行 Phase 1 样例，确认 Markdown/PDF/TXT 到 chunk 的链路能工作。
2. 打开 `notebooks/00_project_orientation.ipynb`，生成项目画像。
3. 用 10 条商品数据手写 5 条 Query/qrels，跑 BM25 baseline。
4. 记录一个 Bad Case：Query 为什么没召回目标商品，是分词、字段、同义词还是标注问题？
5. 用下面模板写当天记录：

```text
今日问题：
我跑通的命令：
数据规模：
baseline 指标：
一个失败样本：
我的解释：
下一次只改变的变量：
证据文件：
```

## 6. 口径确认结果（2026-08-16 已确认）

原"需要确认的 4 个口径"已在 `docs/alignment.md` 中确认：

1. 场景：双产品线并存——传习智学"教育资源搜索"为主线，案例带出"课程即商品"商城视角。
2. 硬件：Windows + Conda + CPU 基线，有 GPU 再补对照。
3. LLM：OpenAI-compatible 抽象，不写死供应商。
4. 时间：每周约 16-20 小时，8 周第一版。

世界观统一口径、简历数字口径与"简历数字→实验→报告"对照表见 `docs/learn/00-学习总纲与导航.md`。后续按"中文教育资源搜索主线 + 传习智答知识库副线 + CPU 可运行基线 + OpenAI-compatible 抽象"推进。
