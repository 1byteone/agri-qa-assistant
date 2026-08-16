# Phase 3 Baseline Report

## 实验范围

本报告来自本地小型 Markdown 语料，检索器为 BM25，目标是验证 benchmark 方法而不是宣称生产 SLA。

## 计时基线

- index_version: `chunks-4-size-128-overlap-32`
- query: `Chunk overlap`
- warmup: `5`
- iterations: `30`
- mean_ms: `0.0312`
- p50_ms: `0.0293`
- p95_ms: `0.0460`

## 单变量实验

### top_k
- top_k=1: results=1, recall=1.000, elapsed_ms=0.0379
- top_k=2: results=2, recall=1.000, elapsed_ms=0.0290
- top_k=5: results=2, recall=1.000, elapsed_ms=0.0226

### chunk_size/overlap

- size=64, overlap=16: chunks=6, recall=0.000, elapsed_ms=0.0834
- size=128, overlap=32: chunks=4, recall=1.000, elapsed_ms=0.0845
- size=256, overlap=64: chunks=2, recall=0.000, elapsed_ms=0.0642

## 限制与下一步

- 当前语料规模很小，不能代表生产规模延迟。
- 当前没有执行真实 ONNX/INT8 导出，因此不报告量化收益。
- 下一步应固定更大数据集和 qrels，再比较 Dense/Hybrid 与 BM25。
