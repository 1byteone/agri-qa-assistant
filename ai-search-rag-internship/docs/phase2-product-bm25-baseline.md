# Phase 2 商品搜索 BM25 Baseline

## 实验身份

```text
experiment_id: EXP-20260816-PRODUCT-BM25-001
experiment_type: synthetic_product_search_baseline
data_version: product-search-v1
device: CPU
retriever: in_memory_bm25
tokenizer: single_chinese_character_or_ascii_word
top_k: 10
k1: 1.5
b: 0.75
```

## 数据说明

本实验使用可复现的合成商品目录，不冒充企业生产日志：

- 500 条商品记录
- 10 个商品族，覆盖数码、户外、办公、厨房和旅行用品
- 50 条 Query，每个商品族 5 条
- 每条 Query 10 个相关商品 ID
- 相关性定义：同一商品族且属于该 Query 对应的属性桶

数据生成与运行命令：

```powershell
python tools\build_product_search_dataset.py
python tools\run_bm25_product_baseline.py
```

## 当前结果

本次运行的结果文件是 `data/processed/phase2_product_bm25_baseline.json`。

| 指标 | 结果 |
| --- | ---: |
| Recall@10 | 0.7800 |
| MRR@10 | 0.7800 |
| 平均单次检索延迟 | 约 5.4 ms |
| P95 延迟 | 约 8.0 ms |
| P99 延迟 | 约 22.3 ms |
| 零召回 Query | 10/50 |

延迟会随机器、Python 版本和后台负载变化，因此不能把这组 CPU 本地结果直接写成生产 P99。质量指标和 Query 级排名证据更适合用于下一轮 Dense/Hybrid 对照。

## Query 类型拆分

| Query 类型 | Query 数 | Recall@10 | 现象 |
| --- | ---: | ---: | --- |
| exact_category | 10 | 1.00 | 商品类目和属性词与文案一致 |
| long_tail | 10 | 1.00 | 仍然包含较多可匹配的场景词 |
| attribute_filter | 10 | 0.80 | 类目词能召回商品族，但属性别名会造成排序噪声 |
| scenario_first | 10 | 0.60 | 先说场景和用户意图，词面不稳定 |
| natural_language | 10 | 0.50 | 用户表达与商品属性文案之间存在词汇鸿沟 |

## 一个 Bad Case

```text
Query:
想找无线耳机，用于通勤，重点是充一次电用很久

标注的相关属性:
长续航

BM25 Top-10:
prod-01-005, prod-01-010, prod-01-015, ...

现象:
BM25 找到了“降噪蓝牙耳机”这个商品族，但按字符词面把“入耳舒适”桶排在了“长续航”桶前面。
```

这不是“BM25 完全失效”，而是一个可定位的问题：

1. 商品文案使用“长续航”，用户说“充一次电用很久”。
2. 当前 tokenizer 是字符级，无法理解这两个表达是同一属性。
3. 类目和场景词提供了粗召回，但没有足够证据完成属性排序。

## 下一轮只改变一个变量

下一轮先做 Query rewrite ablation：

```text
baseline: 原始 Query -> BM25
candidate: Query rewrite -> BM25
```

Rewrite 只增加规范化属性词，不改商品库、不改 qrels、不改 BM25 参数。例如：

```text
充一次电用很久 -> 长续航
打游戏声音别拖 -> 低延迟
放包里不洒 -> 防漏
```

如果 rewrite 后 Recall@10 上升，仍然需要检查它是否引入错误属性；随后再接 BGE-M3，验证 Dense 对未登录表达的帮助。不能把 rewrite 和 Dense 同时打开后再把全部收益归给其中一个方案。

## 面试回答骨架

> 我先用 500 条合成商品数据和 50 条固定 qrels 建 BM25 baseline。整体 Recall@10 是 0.78，但精确属性词 Query 能到 1.0，自然语言 Query 只有 0.5。通过 Query 级结果我发现，系统常常能找到正确商品族，却把用户口语属性排错，说明问题不只是召回范围，也有词面和属性归一化问题。下一步我会先单独做 Query rewrite ablation，再接 BGE-M3/Faiss，并继续使用同一份 qrels 对比。

## 限制

- 合成数据不能证明真实线上 CTR、CVR 或零结果率。
- 当前是内存 BM25，不代表 Elasticsearch/OpenSearch 的线上延迟。
- 字符级 tokenizer 是教学 baseline，不应直接视为最终中文分词方案。
- 当前 qrels 只有二值相关性，尚未覆盖商品价格、库存、品牌偏好等排序业务约束。
