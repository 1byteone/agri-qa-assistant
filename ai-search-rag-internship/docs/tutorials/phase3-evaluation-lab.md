# Phase 3 实验课：Benchmark、量化与 RAG 评估

## 课程结果

完成本实验课后，你应能证明一个优化是否真实改善了系统，而不是只展示一个更小的延迟数字。你还应能把一次失败拆分成：解析失败、召回失败、上下文排序失败、生成不忠实或评估器不稳定。

## 六天安排

| 天 | 学习与编码 | 交付 |
| --- | --- | --- |
| Day 1 | 写 benchmark harness，先测 RRF 和序列化 | `benchmark.py` + 固定参数 JSON |
| Day 2 | 测 PyTorch FP32，完成 warmup/P50/P95/RSS | FP32 baseline |
| Day 3 | 导出 dense-only ONNX，比较输出 cosine | export log + 对齐检查 |
| Day 4 | 做 INT8 动态量化，比较大小、延迟和 Recall | FP32/INT8 表 |
| Day 5 | 构造分层 QA 集，完成 ID-based retrieval 评估 | `qa.json` + 标注规范 |
| Day 6 | 接入 Ragas，人工复核 20 条并写归因报告 | quality report |

## 1. 建立 Benchmark Harness

### 固定变量

每次运行都记录：

```text
run_id, git_commit, model_id, model_revision, device, threads,
batch_size, max_length, input_count, warmup, iterations
```

### 最小计时器

```python
from time import perf_counter
from statistics import mean, median

def benchmark(fn, inputs, warmup=20, iterations=100):
    for item in inputs[:warmup]:
        fn(item)
    samples = []
    for item in (inputs * iterations)[:iterations]:
        start = perf_counter()
        fn(item)
        samples.append((perf_counter() - start) * 1000)
    samples.sort()
    p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
    return {"mean_ms": mean(samples), "p50_ms": median(samples), "p95_ms": p95}
```

练习：先对 Phase 2 的 RRF 函数计时，再替换成 Dense encode。这样可以区分“模型耗时”和“融合/序列化耗时”。

## 2. ONNX 导出闸门

只导出 dense-only wrapper，明确以下三点：

1. tokenizer 的输入输出名称和动态维度。
2. pooling 取哪个 token，是否做 L2 normalization。
3. PyTorch 输出和 ONNX 输出如何对齐。

先验证：

```python
cosine = (torch_output * onnx_output).sum(-1)
assert cosine.mean().item() >= 0.99
```

这只是输出相似度闸门，不能代替 Recall@10。导出 BGE-M3 的 sparse 或 multi-vector 路径时单独记录，不要把 dense-only 结果宣传成完整 BGE-M3 结果。

## 3. INT8 量化实验

比较动态量化和静态量化时，至少固定同一批文本和同一 Execution Provider：

```python
from onnxruntime.quantization import QuantType, quantize_dynamic

quantize_dynamic(
    "model_fp32.onnx",
    "model_int8.onnx",
    weight_type=QuantType.QInt8,
)
```

必须同时报告：文件大小、平均/P50/P95 延迟、峰值 RSS、平均 cosine、Recall@10。量化后更快但 Recall 下降，或模型更小但 P95 变差，都要原样记录。

## 4. 构建 QA 评估集

从 `docs/templates/qa-eval.example.json` 开始，按以下比例抽样：

```text
事实型       30%
跨 Chunk      20%
术语/编号     15%
长尾表达      20%
不可回答      15%
```

两阶段评估：

1. 不使用 LLM：reference context IDs、retrieval Recall/Precision、answerable 分类。
2. 使用 Ragas：Faithfulness、Context Precision、Context Recall、Response Relevancy。

每次 LLM judge 运行记录 provider、model、temperature、prompt_version、cost_estimate、failed_samples。抽取 20 条人工复核，记录“评估器错判”而不是盲信分数。

## 5. 错误归因表

| 现象 | 可能原因 | 下一实验只改什么 |
| --- | --- | --- |
| relevant Chunk 不在 top-k | tokenizer、embedding、索引参数 | 只改召回策略 |
| relevant Chunk 在 top-k，回答缺事实 | prompt、context 截断、生成模型 | 只改生成链路 |
| Faithfulness 高但答案没回答问题 | 忠实但不相关 | 增加 relevance 指标和人工标签 |
| 分数波动很大 | LLM judge、随机性、样本太少 | 固定 prompt/temperature 并增加重复运行 |

## 6. 课程验收题

- 为什么平均延迟下降不能证明用户体验改善？
- “精度损失小于 1%”要具体定义成哪些字段？
- 如何证明 ONNX 的差异来自 pooling，而不是 tokenizer？
- Faithfulness=1 是否意味着答案一定正确？

## 交付清单

```text
phase3_optimization_eval/benchmark.py
phase3_optimization_eval/export_onnx.py
phase3_optimization_eval/quantize.py
phase3_optimization_eval/evaluate.py
data/eval/qa.json
reports/phase3_benchmark.csv
reports/phase3_quality.md
```
