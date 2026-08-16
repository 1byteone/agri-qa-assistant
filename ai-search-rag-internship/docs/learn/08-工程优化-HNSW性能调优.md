# 08 工程优化 · HNSW 性能调优

> 能力域：工程优化 ｜ 对应简历："调整HNSW索引参数，将单次语义检索P99延迟从180ms降至65ms"

## 0 企业案例与用户故事

**题库从 1 万涨到 50 万，搜索开始"卡"了**

传习智学的语义检索上线时只有 1 万条课程资源，查询飞快。半年后题库涨到 **50 万条**，线上反馈开始出现：

- 教学高峰时段（晚上 8 点），语义检索 P99 冲到 **180ms**，页面转圈。
- 监控发现 CPU 高，Faiss 用的是暴力 `Flat` 索引——**每来一个查询都要和 50 万个向量全部算一遍相似度**。

运维同学问数据产品（"我"）：

> "能不能不降质量、把单次检索延迟压下来？P99 到 100ms 以内，我们就能扛住晚高峰。"

于是性能专项启动。但**不能只追速度**：如果为了快 3 倍把召回率从 96% 摔到 60%，那等于没优化。所以实验必须同时报 **Recall@10 和 P50/P95/P99**。

```text
业务痛点：向量规模增长后暴力检索延迟不可接受
技术问题：Faiss HNSW 索引 + M/efConstruction/efSearch 参数扫描
业务指标：Recall@10（质量不掉）+ P50/P95/P99（延迟降下来）+ 内存/建库时间
```

## 1 原理直觉

### 1.1 HNSW：多层小世界图，粗到细搜索

HNSW（Hierarchical Navigable Small World）是近似最近邻（ANN）索引。直觉：

```text
高层（稀疏，长距离链接）  → 快速"粗定位"到大致区域
中层                    → 往下钻
底层（稠密，全部节点）    → 精确"细搜"
查询：从顶层入口贪心下降，在底层做宽度受限的 beam search
```

比暴力搜索（Flat）快的原因：**不需要和所有向量比**，只沿图走很少的跳数。10M 向量场景：HNSW p95 ~0.42ms（Recall@10 0.964），Flat p95 ~42.3ms——差了 100 倍，但 HNSW 内存约 3× Flat、建库慢约 2.3×。

### 1.2 三个核心参数

| 参数 | 作用阶段 | 直觉 | 常见范围 |
| --- | --- | --- | --- |
| `M` | 建库 | 每个节点连几条边；越大图越"密"，召回↑ 内存↑ 延迟↑ | 16~64 |
| `efConstruction` | 建库 | 建图时考察多少候选；越大图质量↑ 建库越慢 | 200~500 |
| `efSearch` | 查询 | 查询时维护多大的候选队列；越大召回↑ 延迟↑ | 从 100 起调 |

关键点：
- **`efSearch` 是线上可调的旋钮**（召回↔延迟 trade-off 的主战场）。
- `efSearch` 至少要 ≥ k（你要返回的邻居数），否则结果无意义。
- 建库质量优先：`efConstruction` 一般建议 ≥ `efSearch`，先建好图，查询时才省事。
- `M` 和 `efConstruction` 影响内存与建库时间；`efSearch` 不影响内存。

### 1.3 为什么不能一味追求最高 Recall

| efSearch | Recall@10 | 延迟 |
| ---: | ---: | ---: |
| 20 | ~82% | 最低 |
| 100 | ~90%+ | 中 |
| 400 | ~98% | 约 2× 于 100 的延迟 |

真实场景：推荐系统要高召回可以开大 `efSearch`；实时接口要守住 P99 预算就得在召回和延迟之间取平衡点。**指标要成对看**：只报 Recall 是自嗨，只报延迟是自杀。

### 1.4 Benchmark 的科学性（决定数字可信度）

- **固定硬件、线程数、batch size、文本长度**，否则数字不可比。
- **warmup**：先跑几轮再计时，排除模型加载/缓存冷启动。
- **请求次数**：P99 需要足够多请求才可信（比如 ≥100 次），并记录冷启动是否计入。
- **同时报内存**：HNSW 内存大是它的代价，不报内存 = 隐藏成本。

## 2 最小实验

### 2.1 先跑现有基准骨架

`docs/phase3_baseline_report.md` 已有小语料计时基线（warmup=5, iterations=30, p50=0.029ms）。当前**不能代表生产规模**，正式实验要扩到万级以上数据。

### 2.2 HNSW 参数扫描脚本（Faiss 最小示例）

```python
import faiss, numpy as np, time

d, n = 1024, 50_000                       # 维度、向量数
x = np.random.rand(n, d).astype("float32")
faiss.normalize_L2(x)                     # cosine = inner product on unit vectors
queries = np.random.rand(1000, d).astype("float32")
faiss.normalize_L2(queries)

for m in (16, 32, 64):
    index = faiss.IndexHNSWFlat(d, m)
    index.hnsw.efConstruction = 200       # 建库参数
    index.add(x)
    for ef in (20, 50, 100, 200):         # 查询参数
        index.hnsw.efSearch = ef
        times = []
        for _ in range(30):
            t0 = time.perf_counter()
            dists, idx = index.search(queries, 10)
            times.append(time.perf_counter() - t0)
        p50 = sorted(times)[len(times)//2]
        p99 = sorted(times)[int(len(times)*0.99)]
        print(f"M={m} efSearch={ef}: p50={p50*1000:.2f}ms p99={p99*1000:.2f}ms")
```

实验表要长这样（填真实数字）：

| M | efConstruction | efSearch | Recall@10 | P50 | P95 | P99 | 内存 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 200 | 20 | 待测 | 待测 | 待测 | 待测 | 待测 |
| 32 | 200 | 100 | 待测 | 待测 | 待测 | 待测 | 待测 |
| 32 | 200 | 200 | 待测 | 待测 | 待测 | 待测 | 待测 |

本仓库封装：`phase2_semantic_search/README.md` 的 `build_faiss_index` 支持 `flat` / `hnsw`，显式暴露 M/efConstruction/efSearch。

### 2.3 正确的调参顺序

```text
1. 先建 Flat 索引当质量上限（Recall 基准 = 1.0）
2. 建 HNSW，固定 M/efConstruction（建库质量优先）
3. 只扫 efSearch：每档都记 Recall@10 + P50/P95/P99
4. 选"质量不掉一档"里 P99 最低的 efSearch
5. 全程记录硬件/线程/数据规模/模型版本
```

## 3 简历映射

**简历原句**："调整HNSW索引参数，将单次语义检索P99延迟从180ms降至65ms"

**怎么说圆**：

> 我把 Faiss 从 Flat 换成 HNSW，并做了 M/efConstruction/efSearch 的参数扫描。先固定 M=32、efConstruction=200（保证建图质量），然后只扫 efSearch：20→200 各测 Recall@10 和 P50/P95/P99。结果显示 efSearch 从 100 提到 400，Recall 只涨一点、延迟几乎翻倍，不值得；选在 Recall 几乎不掉的那一档，P99 从 180ms 降到 65ms。我全程记录硬件、向量规模、线程数、warmup 次数，避免把冷启动算进 P99。

**口径红线**：180ms→65ms 必须在固定硬件/线程/数据规模/模型版本下测量，P99 要说明请求次数和是否含冷启动。如果真实测量达不到，按实测写。

## 4 面试深挖

**Q1：M、efConstruction、efSearch 分别影响什么？**
M=每个节点连边数，影响图密度、内存、延迟；efConstruction=建图候选，影响图质量与建库时间；efSearch=查询候选队列，是线上召回↔延迟的主旋钮。efConstruction 建议 ≥ efSearch，先建好图再谈查询。

**Q2：HNSW 为什么比暴力搜索快？**
暴力要遍历所有向量；HNSW 是分层图：高层长链接粗定位、底层 beam search 细搜，只沿图走少数跳数。10M 向量下 HNSW p95 ~0.4ms vs Flat ~42ms。

**Q3：为什么不能一味追求最高 Recall？**
efSearch 开大召回升但延迟升（可能翻倍），而业务有 P99 预算；质量不掉一档的 efSearch 才值得上。指标必须 Recall 与延迟成对看。

**Q4：P99 怎么测才可信？**
固定硬件/线程/batch/文本长度；先 warmup 排除冷启动；足够多请求（≥100）；说明 P99 是端到端还是纯索引检索；同时报 P50/P95/P99 与内存。

**Q5：你优化的是 embedding 推理、向量检索，还是整个 /search API？**
要能区分：embedding 推理延迟（ONNX，见册 09）、向量检索延迟（HNSW）、API 端到端（含网络/过滤/序列化）。简历"单次语义检索 P99"应明确是纯检索这一段。

**Q6：HNSW 的代价是什么？**
内存大（约 3× Flat）、建库慢、不支持删改（需重建或标记删除）。选型时和 IVF 比：IVF 内存小、召回略低，是"性价比"之选；HNSW 延迟最低但贵。

## 5 参考资料

- [Zilliz: HNSW 三个配置参数的影响](https://zilliz.com/ai-faq/what-are-the-key-configuration-parameters-for-an-hnsw-index-such-as-m-and-efconstructionefsearch-and-how-does-each-influence-the-tradeoff-between-index-size-build-time-query-speed-and-recall)：参数↔索引大小/建库/查询/召回
- [OpenSearch: 选择 HNSW 超参实用指南](https://opensearch.org/blog/a-practical-guide-to-selecting-hnsw-hyperparameters/)
- [Pinecone: HNSW](https://www.pinecone.io/learn/series/faiss/hnsw/)：M 影响内存、efSearch/efConstruction 不影响内存
- [Marqo: Understanding Recall in HNSW](https://www.marqo.ai/blog/understanding-recall-in-hnsw-search)：efSearch 对召回影响最大
- [Faiss IVF vs HNSW vs Flat 基准](https://markaicode.com/benchmarks/faiss-production-benchmark-latency/)：10M 向量延迟/内存/建库对照
- [Ashutosh: HNSW 实用指南](https://www.ashutosh.dev/understanding-hnsw-a-practical-guide/)：参数典型范围
- 本仓库：`phase2_semantic_search/README.md`（`build_faiss_index`）、`docs/phase3_baseline_report.md`
