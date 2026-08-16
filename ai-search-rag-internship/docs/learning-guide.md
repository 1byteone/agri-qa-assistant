# 项目驱动学习教程：AI Search & RAG

现在采用 Notebook-first 入口：先在 `notebooks/` 中完成可运行实验，再把稳定逻辑沉淀到 `phase*_*/` Python 模块。前置知识边界见 `docs/prerequisites-by-phase.md`。

## 1. 目标与完成定义

### 总目标

你要交付的是一个小型但完整的检索增强问答系统，并能回答四类面试问题：

1. 文档如何从原始文件变成可检索的 Chunk？
2. 为什么选择 Dense、BM25 和 Hybrid，而不是只用一种召回？
3. 如何证明优化真的降低了延迟且没有明显损失精度？
4. 如何把技术链路变成用户能使用、指标能衡量的产品？

### 最终完成定义（Definition of Done）

- 能上传 PDF/Markdown，完成解析、分块、索引和检索。
- 查询结果带有来源、Chunk ID 和分数，回答可以追溯。
- 有固定版本的数据集和标注规范。
- 至少有 BM25、Dense、Hybrid 三组对照实验。
- 有延迟、吞吐、内存和质量指标，而不是只说“效果更好”。
- 有 README、技术报告、PRD、A/B 测试方案和 3 分钟 Demo。

## 2. 八周交付路线

| 阶段 | 周期 | 交付项目 | 必须回答的问题 |
| --- | --- | --- | --- |
| Phase 1 | 第 1-2 周 | 文档解析 + Recursive Splitter | Chunk 边界、overlap 和元数据如何影响检索？ |
| Phase 2 | 第 3-4 周 | BGE-M3 + Faiss + BM25 | Dense、Sparse、Hybrid 的收益分别是多少？ |
| Phase 3 | 第 5-6 周 | 优化 + 评估 | 延迟下降是否以质量损失为代价？ |
| Phase 4 | 第 7-8 周 | Mini RAG 产品化 | 技术结果如何转成用户价值和产品指标？ |

每周按照“学习概念 -> 跑通最小例子 -> 改造成项目代码 -> 记录实验 -> 写复盘”的顺序推进。周末必须产生一个可提交的版本或报告。

## 3. Phase 1：文档解析与分块

### 学习目标

输入一个目录中的 PDF、Markdown、TXT，输出统一 JSON：

```json
{
  "id": "a1b2c3...",
  "text": "...",
  "source": "manual.md",
  "page": null,
  "metadata": {"format": "markdown", "headings": ["..."]}
}
```

### 执行任务

- Day 1：读取 PDF 和 Markdown，记录空文件、损坏文件和编码异常。
- Day 2：实现统一 `ParsedDocument` 数据结构。
- Day 3：手写 Recursive Splitter，优先按段落、换行、中文句号和分号切分。
- Day 4：加入 overlap、Chunk ID、来源和页码元数据。
- Day 5：准备至少 10 篇 PDF + 10 篇 Markdown，运行批处理。
- Day 6：与 LangChain `RecursiveCharacterTextSplitter` 对照，比较 Chunk 数、平均长度和边界。
- Day 7：写《分块策略选型报告》，说明 `chunk_size=512`、`overlap=128` 是否适合你的语料。

### 验收标准

- 20 个文件批处理无未捕获异常。
- 每个 Chunk 可追溯到 source；PDF Chunk 有 page。
- Chunk 长度不超过设定上限；overlap 行为有单元测试。
- 至少完成 3 组 chunk_size/overlap 实验，并保存 JSON 或 CSV 结果。
- 能解释 overlap 的收益、成本，以及为什么不能盲目设置得很大。

## 4. Phase 2：语义检索与混合召回

### 学习目标

对 500 条商品或文档记录建立可复现的检索基线。Dense 使用 BGE-M3，稀疏检索使用 BM25，融合使用 RRF 或可解释的加权方案。

### 执行任务

- 固定数据字段：`id/title/attributes/description`。
- 先做 BM25，再做 Dense，再做 Hybrid；不要一开始就隐藏差异。
- 构造至少 50 条带相关文档 ID 的 Query 标注集。
- 测量 Recall@10、MRR@10、P95 latency、索引大小。
- 扫描 HNSW 的 `M`、`efConstruction`、`efSearch`，画质量-延迟 Pareto 曲线。
- Query rewrite 作为独立实验开关，不能和召回策略混在一个结果里。

### 验收标准

- 三种召回均能独立运行。
- Hybrid 相对 BM25 的收益以标注集为准；“至少 5 个百分点”是目标，不是预设结论。
- 每个实验保存参数、随机种子、数据版本和结果。

## 5. Phase 3：性能与质量评估

### 学习目标

建立“优化前 -> 优化后”的可信对照。ONNX/INT8 不是必然适用于 BGE-M3 的所有输出路径，应先验证模型导出、pooling、dense 输出和相似度一致性，再决定是否纳入最终链路。

### 执行任务

- 用固定 batch size 和文本长度测 FP32、ONNX、INT8。
- 预热推理，分别报告平均值和 P50/P95，避免只测一次。
- 使用同一批文本比较 cosine similarity 和 Recall@K。
- 构造 200 条 QA，并写出 reference answer、relevant context、不可回答样本的标注规范。
- RAGAS 指标需要 LLM 或评审模型，记录其模型、温度、费用和失败重试。

### 验收标准

- 量化后的“精度损失 <1%”必须定义为哪个指标的损失。
- 速度提升必须注明 CPU/GPU、线程数、batch size 和文本长度。
- 自动评估失败时能定位到样本，而不是只返回一个总分。

## 6. Phase 4：端到端与产品输出

### 学习目标

把前三个阶段组合成一个能被别人启动和体验的 Mini RAG 服务。

### 交付清单

- FastAPI：上传、索引状态、检索、问答和引用接口。
- 简单前端：输入问题、展示回答、来源和召回 Chunk。
- `docs/PRD.md`：目标用户、用户故事、范围、优先级、成功指标。
- `docs/AB_test_plan.md`：假设、分流、主指标、样本量、停止条件。
- `docs/competitive_analysis.md`：至少 3 个产品的功能矩阵和差异化结论。
- `docs/tech_report.md`：架构、实验、限制、下一步。

## 7. 每日工作模板

```text
今日问题：
今日最小可运行结果：
使用的数据/参数：
观察到的现象：
我的解释：
下一次实验只改变什么：
留下的证据文件：
```

建议节奏是工作日每天 2-3 小时概念和代码，周六集中实验，周日整理报告。每次实验只改变一个主要变量，才能知道结果来自哪里。

## 8. 简历素材模板

```text
在 [数据规模] 上实现 [技术方案]，将 [指标] 从 [baseline] 提升到 [result]，
并通过 [实验/评估方式] 验证，在 [硬件与约束] 下达到 [延迟/吞吐]。
```

只有仓库中的代码、命令和结果能复现时，才把数字写进简历。
