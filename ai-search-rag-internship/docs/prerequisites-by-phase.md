# 四阶段前置知识：只学马上要用的内容

本文件的原则是：前置知识不是入场考试，也不是把所有 Python、数学和机器学习学完再开始。每个阶段只补足“今天的项目会用到、并且能在当天代码里验证”的知识；其余内容放到遇到问题时再学。

配套的详细 Notebook 学习手册见 [`notebook-learning-manual.md`](notebook-learning-manual.md)。四个 Notebook 已按“前置知识 -> 直觉实验 -> 项目代码 -> 反例 -> 指标 -> 阶段闸门”编排；本矩阵回答的是“学到什么程度够用”，不是要求背诵完整课程。

Notebook 工具链本身是共同前置：能启动 Jupyter、选择 `ai-rag-internship` kernel、运行一个代码 cell，并知道 Notebook 输出不是最终生产代码。安装：`python -m pip install -r requirements/notebook.txt`。

## 总体规则

每个前置知识都要通过三种证据之一验收：

- 能在 Notebook 中写出最小代码。
- 能用一个反例解释为什么需要它。
- 能把它连接到一个项目指标或工程决策。

如果一个知识点不能改变代码、实验或判断，就暂时不纳入本阶段必修。

## Phase 1：文档解析与分块

### 必须会

| 知识 | 够用程度 | 立即用途 |
| --- | --- | --- |
| Python 基础语法、函数、列表/字典 | 能读写 30-50 行脚本 | 组织解析结果和 Chunk |
| `pathlib`、文件编码、JSON | 能批量遍历目录并保存 UTF-8 JSON | 读取 PDF/Markdown，输出可追溯数据 |
| 正则表达式基础 | 会写标题、空白和扩展名匹配 | 提取 Markdown headings 和过滤文件 |
| Python dataclass | 知道字段、默认值和类型标注 | 统一 `ParsedDocument` 数据结构 |
| 字符串长度与切片 | 理解字符级上限和边界 | 实现 `chunk_size` 与 `overlap` |

### 用到时再学

PDF 页面对象、Markdown AST、Unicode grapheme、异步 I/O、LangChain 源码。第一阶段不要求先掌握它们。

### 不要求先学

深度学习、向量数据库、LLM Prompt、复杂面向对象设计。

### 闸门

给定 1 个 Markdown 和 1 个 PDF，能说明每个 Chunk 来自哪个文件、哪一页、为什么在这个边界切开。对应 Notebook：`notebooks/phase1_document_parser.ipynb`。

## Phase 2：语义检索与混合召回

### 必须会

| 知识 | 够用程度 | 立即用途 |
| --- | --- | --- |
| Python 模块和虚拟环境 | 能导入本地包、锁定依赖 | 组织 embedding、index、eval 模块 |
| NumPy 数组、shape、dtype | 能解释 `(n, d)` 和 float32 | 保存向量并避免隐式类型转换 |
| 向量点积、L2、cosine | 能手算一个 2D 例子 | 选择 Faiss metric 和归一化方式 |
| TF-IDF/BM25 直觉 | 能解释 TF、IDF、长度归一化 | 理解关键词召回和型号匹配 |
| Precision/Recall/MRR | 能用 3 条 Query 手算 | 判断 top-k 是否真的变好 |
| 排序、字典和集合 | 能按 rank 合并 ID | 实现 RRF，不混加不同量纲的分数 |

### 用到时再学

对比学习、InfoNCE、HNSW 图细节、ANN 内存布局、reranker、Query rewrite。先通过实验看到现象，再回头学公式。

### 不要求先学

从零训练 embedding、分布式向量数据库、CUDA kernel。

### 闸门

能用同一份 qrels 对 BM25、Dense、Hybrid 做对照，并解释一个 Query 为什么排名发生变化。对应 Notebook：`notebooks/phase2_hybrid_retrieval.ipynb`。

## Phase 3：性能优化与质量评估

### 必须会

| 知识 | 够用程度 | 立即用途 |
| --- | --- | --- |
| `time.perf_counter` 与 warmup | 知道首次运行不稳定 | 设计可重复延迟实验 |
| 平均值、P50、P95 | 能解释长尾延迟 | 避免只报告平均速度 |
| 基线与单变量实验 | 一次只改变一个主变量 | 归因 ONNX/INT8 的收益或损失 |
| cosine similarity 与 Recall | 能比较前后输出 | 判断量化是否破坏召回 |
| JSON/CSV 实验记录 | 能保存参数和结果 | 让报告可以复现 |
| QA 标注与错误分类 | 能区分 answerable/不可回答 | 区分召回失败和生成失败 |

### 用到时再学

ONNX graph、Execution Provider、静态量化校准、显著性检验、LLM judge 偏差、RAGAS 内部实现。它们在对应实验前一小时学习即可。

### 不要求先学

编译器优化、GPU kernel、完整统计学课程。

### 闸门

能回答“更快了吗、质量损失多少、在什么硬件和输入下成立”。对应 Notebook：`notebooks/phase3_benchmark_evaluation.ipynb`。

## Phase 4：端到端产品化

### 必须会

| 知识 | 够用程度 | 立即用途 |
| --- | --- | --- |
| HTTP 方法、状态码、JSON | 能读写请求/响应 | 设计 `/health`、`/search`、`/chat` |
| Pydantic schema | 能定义字段和校验 | 防止 API 输入污染检索服务 |
| FastAPI 路由与 TestClient | 能写一个 GET/POST 和测试 | 建立可运行的服务合同 |
| 依赖注入/生命周期 | 知道模型不能每次请求加载 | 复用索引和 embedding 模型 |
| 日志、trace_id、环境变量 | 能记录一次请求的链路 | 追踪引用、错误和配置 |
| 用户故事与指标 | 能把功能写成可验收条目 | PRD、A/B 测试和产品取舍 |

### 用到时再学

Docker、反向代理、认证、队列、缓存、并发控制、线上显著性检验。先让本地 retrieval-only 服务可用。

### 不要求先学

微服务、Kubernetes、多租户权限、复杂前端框架。

### 闸门

别人只看 README 就能启动服务，提交一个 Query，得到带来源的结果；没有 LLM key 时也能运行 `/search`。对应 Notebook：`notebooks/phase4_mini_rag.ipynb`。

## 学习顺序

每阶段按以下循环执行：

```text
前置最小知识 -> Notebook 最小实验 -> 修改一个变量 -> 记录指标 -> 写出工程结论
```

不要把 Notebook 当成最终生产代码。Notebook 负责探索和教学，已经验证的稳定逻辑再沉淀到 `phase*_*/` Python 模块，并用测试保护。

## 每阶段的“知其然 / 知其所以然”验收

| 阶段 | 知其然：能做什么 | 知其所以然：能解释什么 |
| --- | --- | --- |
| Phase 1 | 生成带来源和页码的 `chunks.json` | 为什么分块、overlap 和元数据会影响后续召回 |
| Phase 2 | 运行 BM25、RRF 和 Recall/MRR | 为什么精确匹配与语义匹配互补，为什么不能直接混加异构分数 |
| Phase 3 | 输出 mean/P50/P95 和质量对照 | 为什么 warmup、长尾和单变量实验决定性能结论是否可信 |
| Phase 4 | 调用 `/search`、`/chat` 并得到 citations | 为什么 API 合同、fallback、索引复用和引用决定产品是否可用 |
