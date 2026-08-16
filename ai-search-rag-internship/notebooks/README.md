# Notebook 学习入口

这里有三类入口：`00_mission_control.ipynb` 负责选择真实案件和观众；细分 Notebook 负责真正从 0 到 1 跟写；根目录下的四个 `phase*_*.ipynb` 负责阶段总览和最终复习。所有入口属于同一个 Evidence Quest 项目，不是互不相关的代码示例。详细的学习方法、前置知识和“为什么这样做”见 [`docs/notebook-learning-manual.md`](../docs/notebook-learning-manual.md)。

请从项目根目录启动，并确认 Jupyter 使用 `ai-rag-internship` 的 `python3` kernel：

```powershell
conda activate 'F:\anaconda\miniconda3\envs\ai-rag-internship'
jupyter lab notebooks
```

| Notebook | 项目交付 | 关键问题 |
| --- | --- | --- |
| `00_mission_control.ipynb` | 案件档案、真实观众、5 道挑战题 | 这个作品究竟为谁解决什么问题？ |
| `phase1_document_parser.ipynb` | PDF/Markdown -> 可追溯 Chunk | 边界如何影响检索？ |
| `phase2_hybrid_retrieval.ipynb` | BM25 baseline、Dense 直觉、RRF 与 qrels | 哪种证据能证明召回更好？ |
| `phase3_benchmark_evaluation.ipynb` | 延迟、P50/P95、质量和错误归因 | 更快是否付出了质量代价？ |
| `phase4_mini_rag.ipynb` | FastAPI、引用、fallback、契约验收 | 如何让别人可靠使用？ |

每个 Notebook 都先做不依赖外部 API 的最小实验，再进入项目代码。Phase 2 的二维向量是原理模拟，不得冒充 BGE-M3 效果；Phase 3 的 ONNX/INT8 只有在依赖、模型、设备和输出对齐都记录后才可以写入性能报告。Notebook 会自动寻找项目根目录，因此从项目根目录或 `notebooks/` 目录启动都可以。

## 从 0 到 1 的推荐顺序

请优先按下面顺序学习。每个 Notebook 都有自己的小交付，下一课会读取上一课产生的文件：

```text
00_mission_control.ipynb
  -> 00_project_orientation.ipynb
  -> phase1/01_files_and_documents.ipynb
  -> phase1/02_chunking_from_scratch.ipynb
  -> phase1/03_phase1_delivery.ipynb
  -> phase2/01_tokenization_and_bm25.ipynb
  -> phase2/02_dense_and_rrf.ipynb
  -> phase2/03_phase2_evaluation.ipynb
  -> phase3/01_metrics_and_timing.ipynb
  -> phase3/02_single_variable_experiments.ipynb
  -> phase3/03_phase3_report.ipynb
  -> phase4/01_http_and_api_contract.ipynb
  -> phase4/02_build_mini_rag.ipynb
  -> phase4/03_acceptance_and_demo.ipynb
```

细分 Notebook 的代码标准是：先解释输入和目标，再逐步赋值、调用、检查和输出；核心算法先手写最小版本，再接入生产模块。为了让每条语句都能被追踪，代码单元格保持较小，注释说明“为什么写、输入是什么、输出是什么”。

首次运行某个 Notebook 时，请使用 `Kernel -> Restart Kernel and Run All Cells`，不要只点击中间某一个代码单元格。Notebook 的变量保存在当前 Kernel 中，中间单元格依赖前面的变量；如果确实需要单独重跑，先从顶部运行到目标单元格。教程已为关键依赖增加友好提示。

根目录的四个阶段总览 Notebook 可以在完成细分课程后运行，用于复习整条链路：

```text
phase1_document_parser.ipynb
phase2_hybrid_retrieval.ipynb
phase3_benchmark_evaluation.ipynb
phase4_mini_rag.ipynb
```

## 学习动作

每运行一个实验单元格，都回答三句话：

1. 这段代码改变了哪个项目能力？
2. 输出现象为什么会出现？
3. 如果结果异常，下一步只改变哪个变量？

如果只能回答“代码运行成功”，说明还没有完成该单元格的学习目标。

## 趣味化学习结构

每本课程 Notebook 都包含：

- 任务卡：身份、剧情、专业 Goal、展示作品和通关判定；
- 逐行跟敲区：重要语句上方有中文注释，先预测输出再运行；
- Boss Challenge：同一能力的独立重写模板，默认保持注释；
- 作品检查站：确认产物真的写入磁盘，并能交给下一阶段。

XP 和徽章只是即时反馈，不能替代指标、测试和可追溯产物。
