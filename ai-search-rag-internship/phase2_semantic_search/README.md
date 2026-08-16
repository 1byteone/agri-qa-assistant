# Phase 2: BGE-M3 + Faiss + BM25

本目录用于构建 500 条记录的 Dense、Sparse 和 Hybrid 检索基线。当前已经有不依赖模型下载的 RRF 与 Recall/MRR 工具，可先运行实验逻辑。

逐日实验课：`../docs/tutorials/phase2-retrieval-lab.md`；qrels 和实验日志模板位于 `../docs/templates/`。

当前可直接复用的真实 baseline 是 `bm25.py`；BGE-M3/Faiss 只替换排名生产者，不改变 qrels、指标和 API 的数据合同。

建议实现顺序：

1. `embedding.py`：批量编码并保存向量与模型版本。
2. `index_builder.py`：构建 Faiss Flat，再切换 HNSW。
3. `hybrid_search.py`：BM25 + Dense + RRF。
4. `metrics.py`：固定 50 条 Query，计算 Recall@10、MRR@10 和延迟。

当前已提供的接口：

- `normalize_vectors`：统一 `float32` 和 L2 normalization，便于使用 inner product。
- `encode_with_bge_m3`：懒加载 `FlagEmbedding`，没有安装模型依赖时抛出可解释错误。
- `build_faiss_index`：支持 `flat` 和 `hnsw`，显式暴露 `M/efConstruction/efSearch`。
- `fuse_bm25_and_dense`：只融合排名，不直接把 BM25 分数和 cosine 分数相加。

先运行 model-free 骨架：

```powershell
python -m phase2_semantic_search.demo
python -m pytest -q tests/test_phase2_core.py
```

生成商品搜索练习数据并跑 BM25 baseline：

```powershell
python tools\build_product_search_dataset.py
python tools\run_bm25_product_baseline.py
```

当前一次可复现实验记录见 `docs/phase2-product-bm25-baseline.md`。数据是合成教学目录，不能冒充真实线上日志；后续 BGE-M3/Faiss/Query rewrite 继续复用同一份 qrels。

Query rewrite ablation：

```powershell
python tools\run_query_rewrite_ablation.py
```

结果与限制见 `docs/phase2-product-query-rewrite-ablation.md`。

安装真实 Dense/Faiss 实验依赖：

```powershell
python -m pip install -r requirements/phase2.txt
```

安装前先记录 Python、PyTorch、CPU/GPU 和磁盘空间；模型下载、索引文件和 embedding 缓存不提交 Git。

进入模型实验前安装 `requirements/phase2.txt`。模型下载和索引产物不提交 Git。
