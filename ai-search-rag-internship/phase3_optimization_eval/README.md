# Phase 3: Optimization & Evaluation

本目录用于建立 FP32、ONNX 和 INT8 的对照 Benchmark，以及 QA 质量评估 Pipeline。

详细实验课：`../docs/tutorials/phase3-evaluation-lab.md`；实验日志模板：`../docs/templates/experiment-log.md`。

先验证 BGE-M3 的导出、pooling 和相似度一致性，再决定是否把 ONNX 版本接入主链路。所有速度结论必须包含硬件、batch size、文本长度、预热策略和 P50/P95。

进入本阶段前安装 `requirements/phase3.txt`。模型文件、评估缓存和临时结果不提交 Git。
