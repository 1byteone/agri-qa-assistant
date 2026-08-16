# 后续学习教程指南：Phase 2-4

这份指南接在 Phase 1 文档解析和分块项目之后。目标不是把依赖一次性装全，而是按实验闸门逐步把“可读代码”推进为“可证明的检索系统”。

逐日实验课入口：Phase 2 [检索实验课](tutorials/phase2-retrieval-lab.md)、Phase 3 [评估实验课](tutorials/phase3-evaluation-lab.md)、Phase 4 [产品实验课](tutorials/phase4-product-lab.md)。

## 总体目标

在后续 6 周交付三项成果：

1. 一个能解释 Dense、BM25、Hybrid 差异的检索基线。
2. 一份带质量、延迟、内存和成本约束的优化评估报告。
3. 一个可调用、可测试、带引用的 Mini RAG API 与产品文档。

### 后续完成定义

- 所有实验有固定数据版本、模型版本、参数和硬件记录。
- 检索评估有 qrels，而不是用“看起来相关”代替标注。
- Hybrid 结果同时报告 Recall/MRR/nDCG 与 P95 latency。
- ONNX/INT8 只有在输出一致性和性能收益都被验证后，才进入主链路。
- RAGAS 结果能追溯到单条样本，并区分 retrieval failure 与 generation failure。
- API 可以健康检查、检索、回答和返回来源；无 API key 时也能运行 retrieval-only 模式。

## Phase 2：语义检索与混合召回（第 3-4 周）

### 2.1 先掌握这些概念

**Dense retrieval** 把 query/document 映射为连续向量，适合词面不同但语义相近的表达。BGE-M3 官方文档同时展示 dense、sparse lexical weights 和 ColBERT-style multi-vector 三种信号；本项目第一轮只启用 dense + BM25，控制变量。

**BM25** 依赖词项频率、逆文档频率和长度归一化，通常对型号、法规编号、专有名词更稳。中文需要显式决定分词策略：先用字符级或结巴分词做 baseline，再用实际 Query 评估，不要把英文空格 tokenizer 直接套到中文。

**Faiss HNSW** 以图结构近似最近邻。`M` 主要影响连接数和内存，`efConstruction` 影响建图成本与质量，`efSearch` 影响查询时的探索预算。先用 `IndexFlatIP` 建 exact baseline，再用 HNSW 比较近似损失。

**RRF** 在 rank 层融合，不直接把 BM25 分数和 cosine 分数相加：

```text
RRF(d) = sum(1 / (rrf_k + rank_i(d)))
```

### 2.2 六天教程

| 天 | 学习与编码 | 交付证据 |
| --- | --- | --- |
| Day 1 | 从 Phase 1 `chunks.json` 生成统一记录，补 `id/text/source` 校验 | `data/documents.jsonl` + schema |
| Day 2 | 跑 BGE-M3 dense encode；记录维度、batch、最大长度和模型 revision | `embedding.py` + `embedding_run.json` |
| Day 3 | 用 `IndexFlatIP` 检索，确认向量归一化与 inner product 关系 | `index_builder.py` + exact baseline |
| Day 4 | 接入 BM25；比较中文字符 tokenization 与分词 tokenization | tokenizer 对照表 |
| Day 5 | 使用本仓库的 `reciprocal_rank_fusion`，实现 Hybrid | `hybrid_search.py` + 20 条手工检查 Query |
| Day 6 | 构造 50 条 qrels，跑 Recall@5/10、MRR@10、nDCG@10 | `eval.py` + CSV 报告 |

### 2.3 HNSW 实验矩阵

固定模型、语料和 Query，仅扫描：

```text
M:             16, 32, 64
efConstruction: 64, 128, 256
efSearch:      32, 64, 128, 256
```

每组至少预热 20 次，再测 100 次；报告平均值、P50、P95。第一阶段不追求 500 条数据一定达到某个毫秒数，而是确认“Recall 下降多少换来多少延迟收益”。

### 2.4 Phase 2 验收闸门

- BM25、Dense、Hybrid 可分别关闭和运行。
- Hybrid 相比最强单路 baseline 的提升写成实际百分点，不能预设“至少 5 个百分点”。
- Exact Flat 作为 ground truth，HNSW 报告 Recall@10 相对 exact 的损失。
- 所有结果包含 `model_id`、`data_version`、`seed`、`k`、`M`、`efSearch` 和硬件信息。

## Phase 3：性能优化与质量评估（第 5-6 周）

### 3.1 Benchmark 设计

不要直接把路线图中的“从 180ms 到 65ms”当作目标。先建立统一 harness：

```text
输入：固定文本列表、batch_size、max_length、线程数
预热：至少 20 次
测量：至少 100 次
输出：mean、P50、P95、吞吐、峰值 RSS、模型/索引大小
```

比较顺序：PyTorch FP32 -> PyTorch FP16（若有 GPU）-> ONNX FP32 -> ONNX INT8。每一步都保存 embedding 输出，计算 cosine similarity 和检索 Recall@10。

### 3.2 ONNX/INT8 实验原则

ONNX Runtime 官方文档区分动态和静态量化，并提供量化调试方法。BGE-M3 不是一个只有单一 dense 输出的普通分类模型：sparse lexical weights 和 multi-vector 输出可能有不同导出边界。因此先导出 dense-only wrapper，明确 pooling 与 normalization，再评估是否扩展到其它信号。

`精度损失 <1%` 必须改写为具体指标，例如“Recall@10 下降不超过 1 个百分点，且平均 cosine similarity >= 0.99”。速度提升必须注明 CPU/GPU、线程数、文本长度和 batch size。

### 3.3 RAG 评估数据集

构造 200 条 QA 时，每条记录至少包含：

```json
{
  "question": "...",
  "reference_answer": "...",
  "reference_context_ids": ["chunk-id"],
  "is_answerable": true,
  "difficulty": "long_tail",
  "notes": "标注依据"
}
```

分层抽样：事实型、跨段落、术语/编号、长尾表达、不可回答。先用 ID-based Recall/Precision 做不依赖 LLM 的 retrieval 评估，再用 Ragas 的 Faithfulness、Context Precision、Context Recall 评估生成链路。LLM judge 需要记录模型、温度、prompt 版本、费用和重试。

### 3.4 Phase 3 验收闸门

- Benchmark 一键运行，失败样本和异常输入可定位。
- 量化后至少有一个质量指标、一个延迟指标和一个资源指标的前后对比。
- 评估报告区分“没召回正确 Chunk”和“召回了但回答不忠实”。
- 200 条 QA 有标注规范，至少抽样复核 20 条并记录一致性问题。

## Phase 4：端到端 Mini RAG（第 7-8 周）

### 4.1 最小 API 合同

```text
GET  /health
POST /documents/ingest
POST /search        -> query + top_k + filters + citations
POST /chat          -> question + answer + citations + trace_id
```

`/search` 必须在无 LLM key 时可用；`/chat` 的回答必须返回引用 Chunk ID、source、page 和检索分数。错误响应统一包含可读的 `code` 和 `message`。

### 4.2 产品化教程

1. 用 Pydantic 定义 request/response schema，并用 FastAPI TestClient 写契约测试。
2. 将 Phase 1-3 通过 service 层注入，避免路由函数直接创建模型和索引。
3. 增加 ingestion 状态、索引版本和 `trace_id`，让回答能回放。
4. 增加 retrieval-only fallback、超时和空结果处理。
5. 写 PRD：目标用户、用户故事、P0/P1 功能、成功指标和明确不做项。
6. 写 A/B 方案：A=BM25，B=Hybrid；主指标=Recall@10 或 grounded answer rate，护栏指标=P95 latency、成本和无答案率。

### 4.3 Phase 4 验收闸门

- 新用户可以按 README 启动并完成一条端到端问答。
- API 测试覆盖健康检查、空输入、无结果、引用返回和 LLM 失败。
- 至少 10 条固定问题能展示来源；其中包含 2 条不可回答问题。
- PRD、A/B 方案、竞品分析和技术报告与实际代码一致。

## 每周复盘模板

```text
本周唯一主问题：
Baseline 是什么：
只改变了哪个变量：
最强证据文件：
失败或反常结果：
下周是否继续该方向：
简历可写的一句话：
```
