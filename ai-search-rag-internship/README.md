# AI Search & RAG Internship

这是一个以可交付项目为主线的 AI 搜索 / RAG 学习仓库。学习顺序不是“先把课程学完”，而是每个 Phase 先定义可运行结果，再用实验和文档证明技术决策。

## 专业目标

在 8 周内交付一个可演示、可评测、可解释的 Mini RAG 系统：支持 PDF/Markdown 导入、中文分块、混合检索、性能实验、自动化评估和带引用问答。最终成果应能在面试中用代码、实验数据和报告复现，而不是只展示概念名词。

面向你这份“AI 商品搜索 + 企业级 RAG”实习经历的执行蓝图见：`docs/internship-experience-execution-plan.md`。它把简历条目拆成可运行任务、实验指标、趣味业务实例和面试深挖问题。

## 当前状态

- 已识别已有环境：`base`、`env_ai`
- 本项目独立环境：`ai-rag-internship`，基于现有 `env_ai` 克隆，Python 3.12
- 已落地：Phase 1 文档解析与中文 Recursive Splitter
- 已落地：Phase 2 的 RRF 融合与 Recall/MRR 评估骨架
- 已落地：evidence-first Mini RAG MVP（BM25 + FastAPI + 引用页面）
- 增强项：BGE-M3/Faiss/ONNX/LLM 作为可测量的后续升级，不是项目能否运行的前置条件

## 创建环境

PowerShell（本机已验证的环境路径）：

```powershell
$ragEnv = 'F:\anaconda\miniconda3\envs\ai-rag-internship'
conda create -p $ragEnv --clone 'F:\anaconda\miniconda3\envs\env_ai' -y
conda run -p $ragEnv python -m pip install -r requirements/phase1.txt
conda run -p $ragEnv python -m pip install -r requirements/notebook.txt
conda run -p $ragEnv python -m pytest -q
```

环境创建完成后可以按路径激活：

```powershell
conda activate 'F:\anaconda\miniconda3\envs\ai-rag-internship'
python -m pytest -q
```

在其他机器上可将路径换成自己的 Conda 环境目录，或使用 `conda create -n ai-rag-internship python=3.12 pip -y` 创建基础环境，再安装 `requirements/phase1.txt`。

进入后续阶段时按需安装依赖，避免第一天下载大模型和完整评测栈：

```powershell
python -m pip install -r requirements/phase2.txt
python -m pip install -r requirements/phase3.txt
python -m pip install -r requirements/phase4.txt
```

Notebook 工具链：

```powershell
python -m pip install -r requirements/notebook.txt
jupyter lab notebooks
```

## 运行 Phase 1

```powershell
python -m phase1_doc_parser.main `
  --input-dir phase1_doc_parser/examples/input `
  --output phase1_doc_parser/output/chunks.json `
  --chunk-size 512 `
  --overlap 128
```

查看结果：

```powershell
Get-Content phase1_doc_parser/output/chunks.json -Raw
```

## 目录

```text
phase1_doc_parser/       PDF/Markdown 解析与中文递归分块
phase2_semantic_search/  BGE-M3、Faiss、BM25、RRF 混合检索
phase3_optimization_eval/ONNX、量化、Benchmark、RAGAS
phase4_mini_rag_system/  FastAPI 端到端服务
docs/                    学习教程、实验记录、报告模板
notebooks/               每阶段的可运行 Jupyter 学习入口
requirements/            按阶段拆分的 Python 依赖
```

后续教程入口：`docs/learning-guide-phase2-4.md`；Notebook 详细学习手册：`docs/notebook-learning-manual.md`；资料索引入口：`docs/research-sources.md`。

简历能力域 × 面试深挖体系（传习教育双产品线场景）入口：`docs/learn/00-学习总纲与导航.md`。每册以真实企业案例/用户故事开头，六段式结构：企业案例 → 原理直觉 → 最小实验 → 简历映射 → 面试深挖 → 参考资料。

实习经历对齐入口：`docs/internship-experience-execution-plan.md`；需求确认入口：`docs/alignment.md`。

从 0 到 1 的细分 Notebook 路线：`docs/zero-to-one-roadmap.md`。这条路线默认面向“会 Python 基础，但不会机器学习/RAG”的学习者；每课都遵循“原理直觉 -> 手写最小实现 -> 对照生产模块 -> 项目交付 -> 验收”。

## Notebook-first 学习：Evidence Quest

课程现在以“证据侦探社”作为统一任务世界。先打开 Mission Control，选择你愿意持续追问的主题和真实观众；之后每个 Phase 都会为同一宗案件增加一件可展示的作品。

作品链路：

```text
案件档案 -> 文档考古工具 -> 搜索对决排行榜 -> 质量-速度实验板 -> 证据工作台
```

每个 Notebook 都有任务卡和专业 Goal；关键示范代码逐行配中文注释；末尾 Boss Challenge 默认保持注释，让你自己重新敲一遍；作品检查站会报告产物是否真的落盘。详细设计依据见 `docs/course-design-research.md`。

每个 Notebook 都先运行一个不依赖外部 API 的最小实验，再进入对应阶段的大模型或服务化任务：

```powershell
conda activate 'F:\anaconda\miniconda3\envs\ai-rag-internship'
jupyter lab notebooks
```

Notebook 顺序：

```text
notebooks/phase1_document_parser.ipynb
notebooks/phase2_hybrid_retrieval.ipynb
notebooks/phase3_benchmark_evaluation.ipynb
notebooks/phase4_mini_rag.ipynb
```

首次学习请优先运行细分路线，而不是直接打开阶段总览：

```text
notebooks/00_mission_control.ipynb
notebooks/00_project_orientation.ipynb
notebooks/phase1/01_files_and_documents.ipynb
notebooks/phase1/02_chunking_from_scratch.ipynb
notebooks/phase1/03_phase1_delivery.ipynb
notebooks/phase2/01_tokenization_and_bm25.ipynb
notebooks/phase2/02_dense_and_rrf.ipynb
notebooks/phase2/03_phase2_evaluation.ipynb
notebooks/phase3/01_metrics_and_timing.ipynb
notebooks/phase3/02_single_variable_experiments.ipynb
notebooks/phase3/03_phase3_report.ipynb
notebooks/phase4/01_http_and_api_contract.ipynb
notebooks/phase4/02_build_mini_rag.ipynb
notebooks/phase4/03_acceptance_and_demo.ipynb
```

四个根目录 Notebook 保留为阶段总览和最终复习版；细分 Notebook 才是逐句跟写、从空白概念到完整项目的主教程。每一课都会产生下一阶段可读取的文件，详见 `docs/zero-to-one-roadmap.md`。

前置知识矩阵：`docs/prerequisites-by-phase.md`。每个 Notebook 都包含通俗的原理解释、最小实验、项目代码、反例和阶段闸门，不要求先学完所有机器学习内容。

## 启动完整 MVP

```powershell
conda activate 'F:\anaconda\miniconda3\envs\ai-rag-internship'
python -m phase4_mini_rag_system
```

浏览器打开 `http://127.0.0.1:8000/`。这条链路默认离线工作：Phase 1 文档解析 -> BM25 KnowledgeBase -> FastAPI -> 带来源引用的 evidence-only 响应。

## 学习规则

每个阶段必须留下四种证据：可运行代码、可重复命令、实验数据、设计说明。任何性能数字都要同时记录硬件、数据规模、模型版本和参数，否则不能作为结论。
