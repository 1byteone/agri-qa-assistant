# 从 0 到 1 的 Notebook 学习路线

本路线默认学习者会 Python 基础语法，但不了解机器学习、搜索和 RAG。目标不是把知识点学完再做项目，而是每学一个最小概念，就把它接到同一套 EvidenceDesk Mini RAG 中。

## 学习合同：Evidence Quest

你扮演知识库调查员，为一个真实观众处理一宗资料案件。不要先问“今天要学哪个 API”，先问“今天我要交付哪个能被别人使用的作品”。每一关的任务卡、Goal、作品和 Boss Query 都会把抽象知识拉回同一宗案件。

### 作品主线

```text
案件档案
  -> 文档考古工具
  -> 搜索对决排行榜
  -> 质量-速度实验板
  -> 可追溯证据工作台
```

`notebooks/00_mission_control.ipynb` 负责选择主题和服务对象；它生成的 `evidence_quest_profile.json` 会被后续 Notebook 读取。XP 和徽章只负责提供即时反馈，真正的完成标准是磁盘上的产物、指标和解释。

## 学习合同

每个代码单元格都遵循：

```text
概念直觉 -> 一条语句 -> 看输入/输出 -> 一个断言 -> 接入项目 -> 保存产物
```

“每条语句有注解”在本路线中具体表示：

- 每个重要可执行语句上方有中文注释；末尾的 Boss Challenge 默认全部注释，学员可以逐行自己敲。
- 长代码拆成多个单元格，避免一次复制几十行。
- 变量命名表达业务含义，不用 `a/b/c` 隐藏数据流。
- 循环、条件、函数参数和断言都解释它们保护的行为。
- 复杂的一行表达式会在后续 Notebook 中拆成可观察的中间变量。
- 核心算法先手写最小版本，再与生产模块比较。

## 推荐顺序与交付物

| 顺序 | Notebook | 你在学习什么 | 交付物 |
| --- | --- | --- | --- |
| 0 | `00_project_orientation.ipynb` | 环境、目录、数据流、阶段合同 | `project_orientation.json` |
| 1 | `phase1/01_files_and_documents.ipynb` | Path、编码、Document、元数据 | `document_inventory.json` |
| 2 | `phase1/02_chunking_from_scratch.ipynb` | 切片、步长、overlap、递归边界 | `phase1_chunk_experiment.json` |
| 3 | `phase1/03_phase1_delivery.ipynb` | 批处理、稳定 ID、JSON 交付 | `chunks.json` |
| 4 | `phase2/01_tokenization_and_bm25.ipynb` | Token、TF、DF、IDF、BM25 | `phase2_bm25_baseline.json` |
| 5 | `phase2/02_dense_and_rrf.ipynb` | 向量、cosine、RRF、模拟边界 | `phase2_rrf_demo.json` |
| 6 | `phase2/03_phase2_evaluation.ipynb` | qrels、Recall、MRR、Query 级定位 | `phase2_evaluation.json` |
| 7 | `phase3/01_metrics_and_timing.ipynb` | warmup、计时、mean、P50、P95 | `phase3_timing_baseline.json` |
| 8 | `phase3/02_single_variable_experiments.ipynb` | top-k、分块参数、单变量实验 | `phase3_single_variable_experiments.json` |
| 9 | `phase3/03_phase3_report.ipynb` | 从数据生成报告、限制和优化边界 | `docs/phase3_baseline_report.md` |
| 10 | `phase4/01_http_and_api_contract.ipynb` | HTTP、JSON、状态码、引用合同 | API 断言 |
| 11 | `phase4/02_build_mini_rag.ipynb` | ingest、索引复用、证据回答、fallback | service 行为验证 |
| 12 | `phase4/03_acceptance_and_demo.ipynb` | 用户故事、契约测试、Demo 记录 | `phase4_acceptance_record.json` |

## 每课怎么学

### 第一次运行

从上到下运行，不跳过输出。每个单元格都回答：

1. 这段代码接收什么输入？
2. 它改变了哪个变量或项目能力？
3. 输出为什么符合预期？

### 第二次运行

只改一个变量。例如只把 `overlap=0` 改成 `overlap=32`，只把 `top_k=1` 改成 `top_k=5`。观察变化后，把结果写入对应实验产物。

### 第三次运行

故意制造一个错误：空 Query、非法 overlap、不存在目录、没有相关文档。阅读错误信息，说明系统在哪一层拒绝了输入。

## 每个阶段的“从 0 到 1”定义

### Phase 1

输入一个目录，输出可重复生成的 `chunks.json`。每个 Chunk 能回到 source/page，长度不超过参数，ID 稳定且唯一。

### Phase 2

读取 `chunks.json`，先用 BM25 找证据；用小型数学实验理解 Dense；用 RRF 理解融合；用 qrels 计算 Recall/MRR。真实 Dense 未运行时必须明确标注。

### Phase 3

对真实 KnowledgeBase 搜索做 warmup 和多次计时，同时报告质量和延迟。所有结论包含数据规模、参数、环境和限制。

### Phase 4

别人通过 API 提交 Query，获得可追溯结果；没有 API Key 时仍能 evidence-only；空输入和不存在目录有明确错误；pytest 保护核心合同。

## 兴趣驱动执行法

每次打开 Notebook 都按这个顺序：

1. 先读任务卡，用一句话说出本关要救谁、交付什么。
2. 逐行敲示范代码，每敲一段就预测一个输出。
3. 只改一个变量，观察案件结果如何变化。
4. 完成 Boss Challenge，写下一个失败样本和原理解释。
5. 在作品检查站确认文件真的写入磁盘，再进入下一关。

详细的资料依据和设计决策见 [`docs/course-design-research.md`](course-design-research.md)。

## 常见学习错误

### 只看最终输出

修正方式：先遮住最后一格，自己预测中间变量和断言应该是什么，再运行验证。

### 把模块调用当作学习完成

修正方式：先阅读同课的手写最小实现，再打开生产模块，逐项对照生产代码额外处理了哪些边界。

### 把模拟结果当作真实模型结果

修正方式：检查记录中的 `experiment_type`、模型 ID、revision 和依赖。二维向量只说明 cosine 机制，不说明 BGE-M3 的 Recall。

### 把一个指标当成系统质量

修正方式：检索同时看 Recall/MRR，性能同时看 mean/P50/P95，产品同时看 citations 和错误处理。

## 最终复习

完成 13 个细分 Notebook 后，再运行根目录的四个总览 Notebook。这一步不是新的学习内容，而是把已经理解的模块串成完整链路，并确认最终服务仍然可运行。
