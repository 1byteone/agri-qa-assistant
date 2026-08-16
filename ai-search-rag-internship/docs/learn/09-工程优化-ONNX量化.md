# 09 工程优化 · ONNX 量化

> 能力域：工程优化 ｜ 对应简历："通过ONNX Runtime量化Embedding模型，将单次语义检索P99延迟从180ms降至65ms"

## 0 企业案例与用户故事

**CPU 服务器上，BGE-M3 编码太慢了**

性能专项里，HNSW 把**检索**这段压下来了（册 08），但数据产品（"我"）发现延迟大头其实在**查询编码**：每来一个查询，都得在 CPU 上用 PyTorch 跑一遍 BGE-M3 把 query 变成向量。高峰期 CPU 吃满，**编码 P99 比 HNSW 检索还高**。

运维给的约束很现实：

> "我们没有 GPU 推理集群，只有 8 核 CPU 服务器。模型要能用，就得在 CPU 上跑得快、省内存。"

于是试了一条路：**把 BGE-M3 从 PyTorch 导成 ONNX，再量化成 FP16/INT8**，目标是用更小的模型体积、更快的推理、更低的内存，换尽可能小的 Embedding 质量损失。

但这里有个坑必须踩明白：**不能只测速度**。量化后如果 Recall@10 掉了，就不是优化而是回退。所以要做"原模型 vs ONNX vs INT8"三组对照，**同时报 Recall@10 / Latency / Memory**。

```text
业务痛点：Embedding 模型在 CPU 上推理慢、内存大
技术问题：PyTorch → ONNX 导出 + FP16/INT8 量化 + 一致性/质量验证
业务指标：Recall@10（质量不掉）+ P50/P95/P99 + 模型体积/内存
```

## 1 原理直觉

### 1.1 ONNX 是什么：让模型脱离训练框架跑推理

ONNX 是一个**模型交换格式 + 推理优化运行时**。PyTorch 模型导出成 ONNX 图后，由 ONNX Runtime 执行，能享受：

- **算子融合**（graph optimization）：把多个算子合成一个优化内核（如 transformer 的 QAttention 融合），减少内存搬运和调度开销。
- **硬件优化**：针对 CPU/GPU 指令集优化执行。
- **可移植**：脱离 PyTorch 版本依赖，模型以标准格式部署。

### 1.2 量化：用更低的精度换速度和体积

把权重和激活从 FP32 降到 FP16 或 INT8：

| | FP32 | FP16 | INT8 |
| --- | --- | --- | --- |
| 位数 | 32 | 16 | 8 |
| 体积 | 基准 | ~1/2 | ~1/4 |
| 速度 | 基准 | 更快 | 最快（有硬件支持时 2~4×） |
| 质量损失 | — | 很小 | 小，需验证 |

一个常见数据点（BERT 类模型，8 核 CPU）：原模型 420MB/110ms → ONNX 优化 380MB/75ms → ONNX+INT8 108MB/42ms，F1 91.0→90.8——**体积 1/4、延迟降到约 1/2.6、质量几乎不掉**。

### 1.3 动态 vs 静态量化

| | 动态量化 | 静态量化 |
| --- | --- | --- |
| 权重 | 量化到 INT8 | 量化到 INT8 |
| 激活 | 推理时动态计算范围 | 用**校准数据**预先统计范围，再量化 |
| 速度收益 | 中 | 更大 |
| 需要校准集 | 否 | 是 |

Embedding 模型常用**静态量化**（对一批代表样本跑一遍收集激活分布）。

### 1.4 硬件的"潜规则"

量化不是在所有硬件上都提速：

- CPU 需要支持相应指令（x86 的 VNNI / ARM 的 dot-product 指令），旧硬件可能更慢（有量化和反量化开销）。
- GPU 需要支持 Tensor Core INT8（如 T4/A100）。
- 模型 opset ≥ 10 才能量化；transformer 有专门的 QAttention 优化。
- 如果后训练量化掉点太多，可考虑量化感知训练（QAT）。

### 1.5 关键纪律：先验证"输出一致"，再谈"快"

导出和量化都可能**悄悄改变输出**。正确顺序：

```text
1. 原模型 FP32 baseline（固定 qrels，记 Recall@10）
2. PyTorch → ONNX 导出，先验证 ONNX 与原模型输出 cosine 一致性
3. INT8/FP16 量化，再验证输出一致性
4. 三组对照：Recall@10 / Latency / Memory
5. 只有"质量不掉一档 + 延迟达标"才接入主链路
```

BGE-M3 有 dense/sparse/colbert 三种输出，**导出时三种输出要分别验证**，不能默认 wrapper 直接可导。

## 2 最小实验

### 2.1 导出 + 量化最小流程（骨架，真实模型需 `requirements/phase2.txt`）

```python
# 1) torch → onnx（以 dense 输出为例）
import torch
from FlagEmbedding import BGEM3FlagModel
model = BGEM3FlagModel("BAAI/bge-m3")
dummy = {"input_ids": torch.ones(1, 128, dtype=torch.long),
         "attention_mask": torch.ones(1, 128, dtype=torch.long)}
torch.onnx.export(model.model.model, (dummy["input_ids"], dummy["attention_mask"]),
                  "bge_m3.onnx", input_names=["input_ids", "attention_mask"],
                  output_names=["dense_vecs"], opset_version=17)

# 2) onnx → int8（动态量化示例）
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic("bge_m3.onnx", "bge_m3_int8.onnx",
                 weight_type=QuantType.QInt8)
```

### 2.2 三组对照实验表（填空）

| 模型 | 体积(MB) | P50(ms) | P95(ms) | P99(ms) | Recall@10 | 内存(MB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PyTorch FP32 | 待测 | 待测 | 待测 | 待测 | 待测（baseline） | 待测 |
| ONNX FP32 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |
| ONNX INT8 | 待测 | 待测 | 待测 | 待测 | 待测 | 待测 |

实验身份必须含：硬件型号、线程数、batch size、文本长度、warmup 次数、请求数、onnxruntime 版本、量化方式（动态/静态）。

### 2.3 一致性验证（不能跳过）

```python
import numpy as np, onnxruntime as ort
sess = ort.InferenceSession("bge_m3_int8.onnx")
out = sess.run(None, {"input_ids": ids.numpy(), "attention_mask": mask.numpy()})
# 与原模型 dense_vecs 算 cosine，记 max/mean cosine；掉点超过阈值要停下排查
```

## 3 简历映射

**简历原句**："通过ONNX Runtime量化Embedding模型、调整HNSW索引参数，将单次语义检索P99延迟从180ms降至65ms"

**怎么说圆（HNSW 部分在册 08，这里聚焦 ONNX）**：

> 检索延迟压下来后，我发现查询编码（BGE-M3 在 CPU 上推理）成了瓶颈。我把模型导成 ONNX 并量化到 INT8，但先做了三件事防止"为了快丢质量"：一是在固定 qrels 上对比 PyTorch/ONNX/INT8 的 Recall@10；二是验证量化前后 dense 输出的 cosine 一致性；三是固定硬件、线程、batch、文本长度和 warmup 来测 P50/P95/P99。最终体积减到约 1/4、编码延迟明显下降，Recall@10 基本不掉，才把 ONNX 版本接入主链路。简历的 180ms→65ms 是 HNSW+ONNX 两段叠加后的端到端语义检索 P99，口径我说明是纯检索+编码、不含网络。

**口径红线**：180ms→65ms 若同时含 HNSW 和 ONNX 收益，要能拆开说各贡献多少（比如 HNSW：检索段，ONNX：编码段）。不要混在一起说不清。

## 4 面试深挖

**Q1：ONNX Runtime 为什么能提升推理性能？**
ONNX 图脱离训练框架后能做算子融合（减少内存搬运/调度）、针对硬件指令集优化、并支持量化；Embedding 场景常见 2~3× 提速、体积缩到 1/4，质量损失很小。

**Q2：INT8 量化后如果 Recall 掉了，怎么决定是否上线？**
先量化掉点幅度：极小（如 <1 分）且延迟收益大 → 可上；明显掉 → 换静态量化（校准集更贴业务）/调量化范围/QAT/只量化部分算子。决策标准是"质量不掉一档 + 延迟达标"，不能只看速度。

**Q3：动态量化和静态量化区别？**
动态：激活范围推理时动态算，简单、无需校准；静态：用校准数据预先统计激活分布，量化更充分、更快，但需要代表样本。Embedding 模型常用静态。

**Q4：为什么量化不是对所有硬件都快？**
量化有量化和反量化开销，CPU 需 VNNI、GPU 需 Tensor Core INT8；旧硬件可能更慢。所以"先验证输出一致性，再谈速度"，而且报告里要写硬件型号。

**Q5：你优化的是 embedding 推理还是整个 /search API？**
要能拆：embedding 编码（ONNX）、向量检索（HNSW）、API 端到端。简历数字要对应到明确边界。

**Q6：BGE-M3 导出 ONNX 有什么特殊注意？**
BGE-M3 有 dense/sparse/colbert 三种输出，sparse（lexical_weights）和 colbert（多向量）导出路径与 dense 不同，要分别验证一致性；不能默认 wrapper 一键导出全可用。

## 5 参考资料

- [ONNX Runtime Quantization（官方）](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)：U8U8/U8S8 等、动态/静态、校准、QAT、opset≥10、硬件要求
- [ONNX Runtime Model Optimizations](https://onnxruntime.ai/docs/performance/model-optimizations/)：算子融合、体积/复杂度优化
- [Medium: Optimizing Transformer Inference with ONNX + Quantization](https://medium.com/@bhagyarana80/optimizing-transformer-inference-with-onnx-runtime-and-quantization-098f8149a15c)：BERT 420→108MB、110→42ms、F1 91.0→90.8
- [Nixiesearch: LLM Embeddings 3× faster with quantization](https://medium.com/nixiesearch/how-to-compute-llm-embeddings-3x-faster-with-model-quantization-25523d9b4ce5)：QAttention 融合内核、硬件指令影响
- [PyTorch ONNX Export（官方）](https://pytorch.org/docs/stable/onnx.html)：导出边界
- 本仓库：`phase3_optimization_eval/README.md`、`docs/phase3_baseline_report.md`
