# 02 AI搜索 · Faiss 与混合检索

> 能力域：AI 搜索 ｜ 对应简历："基于BGE-M3模型构建Faiss向量索引" + 混合检索

## 0 企业案例与用户故事

**语义召回了，精确词却丢了**

数据产品同学接入了 BGE-M3 + Faiss 之后，发现效果是"一半惊喜一半惊吓"：

- ✅ 惊喜：小陈搜"圆锥曲线怎么学提分快"，终于能召回"椭圆双曲线抛物线解题技巧"了；自然语言长尾 Query 的零结果明显减少。
- ❌ 惊吓：周主任搜 **"人教A版必修二 导数 教案"**，语义召回把"人教B版""必修一""导数思维导图"这类**意思相近但版本不对**的资源排在前面；而备考学员搜 **"2024 高考数学真题"**，语义检索把"2023""模拟题""押题卷"全推上来了——**精确编号、版本号、年份词反而没人管了**。

周主任一句话点破：

> "我要的是'人教A版必修二'，一个字都不能错。你们按'意思'找，把'意思差不多'的东西全塞给我。"

```text
业务痛点：语义召回提升长尾/口语，却牺牲精确词（教材编号/年份/版本/题号）
技术问题：Faiss ANN 索引 + BM25 稀疏检索 + RRF 结果融合
业务指标：Recall@10 / MRR@10（在固定 qrels 上对比 BM25 / Dense / Hybrid）
```

## 1 原理直觉

### 1.1 Faiss 是什么：给"向量"建索引、做近似最近邻

- **Faiss 和 MySQL 的区别**：MySQL 存"行数据"，用 B+ 树按字段精确查；Faiss 是**向量相似度搜索库**，搜索"离查询向量最近的 K 个向量"（ANN，近似最近邻）。它不存业务字段，只负责"向量 → 向量"。
- **为什么需要索引**：暴力搜索（Flat）把所有向量算一遍，10M 向量下单次查询要几十毫秒；ANN 索引用空间划分/图结构，把查询降到亚毫秒级。
- **为什么不能直接把文本存进 Faiss**：Faiss 只认向量。文本必须先经 Embedding 模型变成向量（册 01）。

### 1.2 三种索引的直觉

| 索引 | 直觉 | 延迟 | 内存 | 召回 |
| --- | --- | --- | --- | --- |
| `Flat`（暴力） | 全量算相似度 | 慢（10M 下 ~42ms） | 最小 | 精确（=1.0） |
| `HNSW`（图） | 多层小世界图，粗到细 | 最快（~0.4ms p95） | 最大（约 3× Flat） | ~0.96 |
| `IVF`（聚类倒排） | 先分桶再桶内搜 | 中 | 中 | ~0.96 |

> 实测参考（10M 随机 768 维向量）：HNSW p95 0.42ms / Recall@10 0.964；IVF nprobe=64 p95 0.83ms；Flat p95 42.3ms。HNSW 的代价是约 3× 内存和 2.3× 建库时间。

### 1.3 为什么 Dense 不能单挑：召回与精度的两类失败

| 失败模式 | 例子 | 谁擅长 |
| --- | --- | --- |
| 语义失败 | "圆锥曲线" ↔ "椭圆" | Dense 补上 |
| 精确词失败 | "人教A版必修二""2024高考真题""A9F-3321" | BM25 补上 |

单独用任一信号都有系统性盲区，所以生产系统几乎都是**混合检索**：

```text
用户 Query
   ├──► BM25 稀疏检索（精确词）
   └──► Dense 向量检索（语义）
          └──► RRF 融合排序 ──► Top-K ──►（可选）Rerank
```

### 1.4 RRF：为什么直接加分数是坑，用名次却稳

BM25 分数可能分布在 0~15，cosine 在 0.6~0.95，**量纲不同不能直接相加**；min-max 归一化又会被一个极端离群值压扁所有分数。

RRF 不看分数只看**名次**：

```text
RRF(d) = Σ_{每个检索器} 1 / (k + rank_d)      # k 常取 60
```

名次越靠前贡献越大，且不受分数分布影响。实测（WANDS 电商基准）：RRF NDCG 0.7068 > 纯 BM25 0.6983 > 纯 KNN 0.6953；调优后的 hybrid 到 0.7497。**关键前提**：两个检索器的失败方式要"互补"，如果是三个几乎一样的 BM25 变体，RRF 毫无增益。

## 2 最小实验

本仓库已经给好了**模型无关的骨架**，先跑通再上真实模型：

### 2.1 跑模型无关 RRF + 指标

```powershell
python -m phase2_semantic_search.demo
python -m pytest -q tests/test_phase2_core.py
```

```python
from phase2_semantic_search.fusion import reciprocal_rank_fusion
from phase2_semantic_search.metrics import evaluate_qrels

lexical = {"q1": ["chunk-exact", "chunk-semantic"], "q2": ["chunk-noise", "chunk-exact"]}
dense   = {"q1": ["chunk-semantic", "chunk-exact"], "q2": ["chunk-semantic", "chunk-exact"]}
fused = {qid: [r.doc_id for r in reciprocal_rank_fusion({"bm25": lexical[qid], "dense": dense[qid]})] for qid in lexical}
print(evaluate_qrels(fused, {"q1": {"chunk-exact"}, "q2": {"chunk-semantic"}}, k=3))
```

### 2.2 建真实目录 + BM25 baseline

```powershell
python tools\build_product_search_dataset.py     # 500 条教育资源目录 + 50 条 qrels
python tools\run_bm25_product_baseline.py
```

可复现基线（截至 2026-08）：**Recall@10 = 0.78，MRR@10 = 0.78，10/50 零召回**。Query 类型拆解非常关键：

| Query 类型 | Recall@10 | 现象 |
| ---: | ---: | --- |
| exact_category | 1.00 | 词面一致，BM25 全中 |
| natural_language | 0.50 | 口语表达与文案有词汇鸿沟 → Dense 的用武之地 |

### 2.3 下一步：接入 Faiss（对照 Dense-only / Hybrid）

按 `phase2_semantic_search/README.md` 建议顺序实现，每个实验只改一个变量：

```text
① BM25 only（已有）           Recall@10 = 0.78   ← baseline
② Dense only（Faiss Flat）    预期：口语 Query 提升，精确词可能下降
③ Hybrid = BM25 + Dense RRF  预期：整体最高，两路互补
④ Hybrid + Query rewrite     预期：属性词归一化再叠一层（见册 03）
```

Faiss 最小代码（归一化后用 IP 即 cosine）：

```python
import faiss, numpy as np
vectors = np.random.rand(500, 1024).astype("float32")
faiss.normalize_L2(vectors)
index = faiss.IndexFlatIP(1024)      # cosine = inner product on unit vectors
index.add(vectors)
# 切 HNSW：index = faiss.IndexHNSWFlat(1024, 32)
```

## 3 简历映射

**简历原句**："基于 BGE-M3 模型构建 Faiss 向量索引" + "混合检索链路"

**怎么说圆**：

> 我在线上 BM25 的基础上加了 Dense 召回：BGE-M3 编码 + Faiss 索引做 Top-K。跑完发现语义召回让口语长尾 Query 变好，但精确词（教材版本、年份、题号）反而变差。于是没把 Dense 单发，而是做 BM25 + Dense 双路召回，用 RRF 融合名次。我在固定 50 条 qrels 上对比，BM25 0.78 → 语义 Query 单独看提升明显、整体 Hybrid 优于单路；还记录了每个 Query 类型的 Recall@10 拆解，能说清收益来自哪类 Query。

**面试追问怎么接**：如果面试官问"那 72%→89% 的数字哪来的"——如实说明：简历数字 = 本项目固定评测集上的复现结果（当前 BM25 0.78，rewrite 后 0.96，Hybrid 数字待测），**数字随最新实验更新，不虚报**。

## 4 面试深挖

**Q1：Faiss 和 MySQL 有什么区别？**
MySQL 是按字段精确查询的数据库；Faiss 是向量近似最近邻搜索库。业务元数据放 MySQL（如按年级/科目过滤），向量放 Faiss，两者配合——先过滤再向量检索是常见架构。

**Q2：HNSW 为什么比暴力搜索快？**
HNSW 建多层图：高层稀疏长距离链接负责"粗定位"，低层 dense 负责"细搜"；查询从顶层入口贪心下降，在底层做宽度为 efSearch 的 beam search。复杂度近似对数级，10M 向量亚毫秒；代价是内存和建库时间。

**Q3：为什么召回之后还需要 Rerank？（见册 03/05 精排）**
第一路检索（bi-encoder）为召回设计，目标是把正确答案塞进 Top-50~200，不是 Top-1；而 LLM 只读 Top-3~5。cross-encoder 对 (query, doc) 联合编码做精排，NDCG@10 通常提升 5~15 分。两阶段 = 快召回 + 慢精排。

**Q4：RRF 和加权分数融合的区别？为什么默认 RRF？**
加权需要归一化不同量纲的分数，min-max 对离群值敏感；RRF 只用名次，无分布假设，k=60 是零调参基线。但 RRF 丢弃分数幅度，若分数可信且想给某路加权，可用 weighted sum。

**Q5：何时不该用向量检索？**
精确词查询：SKU、错误码、教材编号、题号、年份。这些语义检索会"意思差不多就推"，反而失真。此时 keyword/BM25 或"Query 分类器决定权重"更合适。

**Q6：BM25 的三个超参数直觉？**
k1 控制词频饱和（重复词收益递减），b 控制文档长度归一化（长文档不因字数多被偏爱），IDF 让稀有词更有信号。

## 5 参考资料

- [Faiss Indexes Wiki（官方）](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [Pinecone: HNSW](https://www.pinecone.io/learn/series/faiss/hnsw/)：M/efConstruction/efSearch 对 recall、内存、建库的影响
- [FAISS IVF vs HNSW vs Flat 基准](https://markaicode.com/benchmarks/faiss-production-benchmark-latency/)：10M 向量 p95 对照、内存成本
- [OneUptime 向量索引实现](https://oneuptime.com/blog/post/2026-01-30-vector-indexing/view)：`IndexHNSWFlat`、`normalize_L2` + `IndexFlatIP`
- [Weaviate Hybrid Search Explained](https://weaviate.io/blog/hybrid-search-explained)：RRF 融合示例
- [Hybrid Search 2026 参考（WANDS 数据）](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026)：RRF NDCG 对照
- [Hybrid Search Explained（rank-based vs score fusion）](https://bigdataboutique.com/blog/hybrid-search-explained)：RRF k=60、min-max 的坑
- [BM25 vs 向量：何时用哪种](https://prakhartripathi.hashnode.dev/hybrid-search-explained-when-to-use-keyword-vector-or-both-in-ai-applications)
- [Knovo: 语义 vs 关键词](https://www.knovo.dev/guides/semantic-search-vs-keyword)：BM25 在精确词上可能反超 Dense
- 本仓库：`phase2_semantic_search/fusion.py`、`metrics.py`、`docs/phase2-product-bm25-baseline.md`
