# Phase 2 Query Rewrite Ablation

## 实验身份

```text
experiment_id: EXP-20260816-PRODUCT-REWRITE-001
changed_variable: query_transform
fixed_retriever: in_memory_bm25
fixed_data: product-search-v1
fixed_top_k: 10
```

## 实验问题

用户 Query 经常使用口语表达，而商品文案使用标准属性词。这里先只增加一个可审计的规则型 Query rewrite，不修改商品目录、BM25 参数、qrels 或 Top-K。

示例：

```text
充一次电用很久 -> 长续航
打游戏声音别拖 -> 低延迟
放包里不洒 -> 防漏
```

原 Query 会被保留，标准属性词只追加到检索 Query 中。这样后续仍然可以展示用户原话，也能定位 rewrite 是否改变了排序。

## 运行命令

```powershell
python tools\build_product_search_dataset.py
python tools\run_query_rewrite_ablation.py
```

结果文件：`data/processed/phase2_product_query_rewrite_ablation.json`

## 当前结果

| System | Recall@10 | MRR@10 | 零召回 Query |
| --- | ---: | ---: | ---: |
| 原 Query + BM25 | 0.7800 | 0.7800 | 10 |
| Rewrite Query + BM25 | 0.9600 | 0.9600 | 2 |
| Delta | +0.1800 | +0.1800 | -8 |

这组结果只能说明在当前合成数据和规则覆盖范围内，标准属性归一化有效；不能直接推导线上 CTR/CVR，也不能证明所有 Query 都适合改写。

## 质量与成本

本次运行中，candidate 的平均延迟高于 baseline，因为每次请求增加了规则匹配和更长的检索 Query。当前延迟仍是本机 Python 内存 baseline，不等于生产 API P99；后续需要在统一 warmup、请求数、硬件和服务边界下重新 benchmark。

更重要的风险是误改写：

- 一个 Query 可能包含多个属性，规则顺序不能随意覆盖用户意图。
- 同一个口语短语在不同品类下可能对应不同标准属性。
- rewrite 只解决词面归一化，不能解决完全未知的表达或复杂组合约束。

## 面试回答骨架

> 我没有把 Query rewrite 和 Dense 一起打开，而是先固定 BM25、商品库和 qrels，只把“充一次电用很久”映射成“长续航”等标准属性词。结果 Recall@10 从 0.78 到 0.96，零召回从 10 条降到 2 条。这个实验说明词面归一化确实贡献了收益，但还需要看误改写率和延迟，再决定是否接入主链路。剩下的失败样本再交给 BGE-M3 做语义召回对照。

## 下一步

1. 对 rewrite 做人工抽检，记录正确、过宽、错误三类。
2. 加入 Dense-only，继续复用同一份 qrels。
3. 用 RRF 对比 BM25、Dense、Hybrid、Hybrid+rewrite。
4. 把结果写入 Recall/MRR/P95 的统一实验表。
