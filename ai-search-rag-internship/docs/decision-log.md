# Decision Log

## 2026-08-11

### 独立 Conda 环境

- 现有环境：`base`、`env_ai`。
- 决策：从现有 `env_ai` 克隆出 `ai-rag-internship`，实际 Python 版本为 3.12。
- 原因：本机 Conda 求解器访问配置的镜像源耗时过长，而 `env_ai` 已提供 LangChain、FastAPI、OpenAI 等基础依赖；克隆可以快速得到隔离环境，再按阶段补充检索依赖。
- 代价：环境继承了一些当前项目暂时不用的通用包；后续可用显式导出文件进一步收敛。

### 分阶段安装依赖

- 决策：Phase 1 只安装 PyMuPDF 和 pytest，后续按阶段安装检索、优化和服务依赖。
- 原因：BGE-M3、Faiss、ONNX 和 RAGAS 体积大、平台差异明显，第一天不应让环境安装阻塞文档解析学习。

### 先做自实现 Splitter

- 决策：Phase 1 维护一个小而清晰的自实现，再和 LangChain 结果对比。
- 原因：学习目标是理解递归切分、overlap 和边界，而不是把框架调用当成原理。

### 性能指标作为实验目标

- 决策：路线图中的 `<5ms`、`>40%`、`<1%` 作为目标区间，不作为预先承诺。
- 原因：结果依赖 CPU/GPU、文本长度、batch size、索引规模和指标定义，必须由实验数据支持。

### 后续资料与 Phase 2 骨架

- 决策：优先依据 BGE-M3 官方文档、Faiss Wiki、RRF 原论文、MTEB、ONNX Runtime 和 Ragas 官方文档；博客与排行榜只做补充。
- 原因：教程需要同时覆盖原理、API 和可复现实验，单一来源无法支撑完整链路。
- 决策：先实现无模型依赖的 RRF、Recall@K、MRR@K 工具，再接入 BGE-M3/Faiss。
- 原因：融合和评估逻辑可以先独立验证，避免大模型下载或平台兼容性阻塞学习；真实模型只替换 ranking producer。

### Notebook-first 学习入口

- 决策：每个 Phase 使用一个可执行 `.ipynb` 作为学习和实验入口，Python 模块保留为复用层。
- 原因：Notebook 能把前置知识、代码、输出、实验解释和验收问题放在同一条学习链路中；验证后的稳定逻辑再回写模块和测试。
- 环境：项目 Conda 环境补充 JupyterLab、nbformat、nbclient、nbconvert、ipykernel，并验证四个 Notebook 可执行。

### Evidence-first MVP

- 决策：先交付 BM25 + FastAPI + citations 的离线完整闭环，LLM 通过 `RAG_ENABLE_LLM=true` 显式开启。
- 原因：完整项目必须可复现、可离线验收，且不能因 API key 自动产生外部调用；模型增强项应由 Recall、延迟和 grounded answer 指标证明价值。
