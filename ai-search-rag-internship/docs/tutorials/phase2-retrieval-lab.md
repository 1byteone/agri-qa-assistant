# Phase 2 实验课：从 BM25 到 BGE-M3 Hybrid

## 课程结果

完成本实验课后，你应能从同一份 JSONL 数据生成三种排序：BM25、Dense、Hybrid，并用同一份 qrels 比较它们。课程默认先做小数据和 exact baseline，再扩大到 500 条记录。

## 0. 前置检查

```powershell
python -m phase2_semantic_search.demo
python -m pytest -q tests/test_phase2_core.py
python -m pip install -r requirements/phase2.txt
```

如果 `faiss-cpu` 或 `FlagEmbedding` 在 Windows 安装失败，先保留本仓库的 model-free 骨架，并在 WSL/Linux 或 Conda-forge 环境继续。安装失败本身要记录在实验日志中，不能静默换成不可比的库。

## 1. 建立数据契约

每行一个文档，`id` 永久稳定；文本改变时更新 `content_hash` 或 `data_version`。

```json
{"id":"doc-001","title":"...","text":"...","source":"manual.md","page":3,"data_version":"v1"}
```

练习：

1. 从 `phase1_doc_parser/output/chunks.json` 转成 JSONL。
2. 检查 `id` 非空、`text` 非空、`source` 可追溯。
3. 统计文档数、字符数、长度 P50/P95、空文本数和重复 ID 数。

完成标准：同一输入运行两次，输出 ID 和顺序一致。

### 商品搜索练习数据

为了贴近“自然语言找货”和“属性模糊匹配”，先生成一份明确标注为合成数据的商品目录：

```powershell
python tools\build_product_search_dataset.py
python tools\run_bm25_product_baseline.py
```

这会生成 500 条商品、50 条 Query 和固定 qrels。结果会保存在 `data/processed/phase2_product_bm25_baseline.json`，报告见 `docs/phase2-product-bm25-baseline.md`。先读 Query 级 `bad_cases`，再决定下一步改 tokenizer、做 Query rewrite，还是接 Dense。

Query rewrite 的第一轮单变量实验：

```powershell
python tools\run_query_rewrite_ablation.py
```

报告见 `docs/phase2-product-query-rewrite-ablation.md`。这个实验只改变 Query transform，不能和 Dense 或 RRF 同时作为第一轮结论。

## 2. BM25：先理解词项匹配

### 关键概念

- TF：词项在当前文档中的出现频率。
- IDF：词项在整个语料中有多稀有。
- 长度归一化：避免长文档因为出现更多词而天然占优。
- 中文 tokenizer：字符级 token 对短语边界不敏感，分词 token 对专有词更友好；必须通过 qrels 决定。

练习顺序：

1. 先用 `rank_bm25` 跑 5 条 Query。
2. 对同一 Query 切换字符级 tokenizer 和词级 tokenizer。
3. 保存 top-k 文档 ID，不要只打印标题。
4. 对 3 条 Query 手工解释 BM25 为什么把某文档排第一。

你必须能回答：一个词在所有文档都出现时，为什么它的 IDF 贡献应该较低？

## 3. Dense：BGE-M3 的最小路径

Dense-only 第一轮只取 `dense_vecs`，不同时打开 sparse 和 multi-vector，避免一次改变多个变量。

```python
import numpy as np
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)
texts = ["检索文档一", "检索文档二"]
encoded = model.encode(
    texts,
    batch_size=4,
    max_length=512,
    return_dense=True,
    return_sparse=False,
    return_colbert_vecs=False,
)
vectors = np.asarray(encoded["dense_vecs"], dtype="float32")
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True).clip(min=1e-12)
```

记录以下元数据：模型 ID、revision、设备、batch size、max length、向量维度、归一化方式和运行时间。query 和 document 的编码规则必须一致。

## 4. Faiss：Exact 先于 Approximate

先用 Flat 建 ground truth：

```python
import faiss

index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)
scores, ids = index.search(query_vectors, 10)
```

再切换 HNSW：

```python
index = faiss.IndexHNSWFlat(vectors.shape[1], 32, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = 128
index.hnsw.efSearch = 64
index.add(vectors)
```

练习：固定 `M=32`，扫描 `efSearch=32/64/128/256`，比较 HNSW top-10 与 Flat top-10 的集合重合率。这个重合率是 ANN 近似质量，不是业务 Recall；业务 Recall 仍然要用 qrels 计算。

## 5. RRF：只融合排名

将 BM25 和 Dense 的文档 ID 排名传入现有工具：

```python
from phase2_semantic_search import reciprocal_rank_fusion

fused = reciprocal_rank_fusion(
    {"bm25": bm25_ids, "dense": dense_ids},
    rrf_k=60,
)
top_ids = [item.doc_id for item in fused[:10]]
```

对照实验必须有：BM25-only、Dense-only、Hybrid。不要把原始 BM25 分数和 cosine 分数直接相加，除非你另外完成了校准实验。

## 6. qrels 与评估

使用 `docs/templates/qrels.example.json` 创建标注集。每条 Query 至少标注一个 relevant ID；无法回答 Query 单独标记，不要把“没有答案”误标成随机文档。

```python
from phase2_semantic_search import evaluate_qrels

metrics = evaluate_qrels(run, qrels, k=10)
print(metrics)
```

第一轮输出：Recall@5、Recall@10、MRR@10、P50/P95 latency。若实现 nDCG，明确 graded relevance 的 0/1/2 定义。

## 7. 课程验收题

- 为什么 Flat 可以作为 HNSW 的 ground truth？
- 为什么 RRF 不需要比较 BM25 和 cosine 的绝对分数？
- 如果 Hybrid Recall 提升但 P95 翻倍，你是否会选择它？依据是什么？
- 如果模型把同义表达召回了，但漏掉产品型号，你会优先改 embedding、BM25 tokenizer 还是 fusion？

## 交付清单

```text
phase2_semantic_search/embedding.py
phase2_semantic_search/index_builder.py
phase2_semantic_search/hybrid_search.py
phase2_semantic_search/eval.py
data/processed/documents.jsonl
data/eval/qrels.json
reports/phase2_baseline.csv
docs/phase2_report.md
```
