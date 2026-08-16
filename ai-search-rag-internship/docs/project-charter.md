# Project Charter

## Professional Goal

在 8 周内完成一个可运行、可评测、可解释的中文 Mini RAG 系统，并沉淀为 4 条可验证的简历素材：文档工程、混合检索、性能与质量评估、端到端产品化。

业务场景采用"江西传习教育科技有限公司"（化名，教育科技）双产品线：传习智学（学习资源搜索）+ 传习智答（教研知识库 RAG）。场景化学习体系与简历映射见 `docs/learn/00-学习总纲与导航.md`。

## Scope

### In scope

- PDF/Markdown/TXT 导入与来源元数据保留。
- 中文友好的 Recursive Splitter。
- BGE-M3 Dense Retrieval、BM25、Faiss HNSW 和 RRF Hybrid。
- Benchmark、Recall/MRR、RAGAS 或等价的可复现评估。
- FastAPI 服务、引用展示、PRD、A/B 测试方案和技术报告。

### Out of scope for the first 8 weeks

- 多租户权限、生产级分布式索引、复杂前端设计。
- 在没有标注数据和基线的情况下追求模型微调。
- 把第三方框架默认结果当作实验结论。

## Success Metrics

| 维度 | 目标 | 证据 |
| --- | --- | --- |
| 可运行性 | 新环境可安装，Phase 1 命令一键运行 | `README.md`、环境版本、测试输出 |
| 解析质量 | PDF/Markdown 均能输出可追溯 Chunk | `parser.py`、测试和样例 JSON |
| 检索质量 | 在固定标注集上比较 BM25/Dense/Hybrid | Phase 2 实验表 |
| 性能 | 报告 P50/P95、吞吐、内存和硬件信息 | Phase 3 Benchmark |
| 产品交付 | 导入 -> 提问 -> 带引用回答 | Phase 4 Demo 和接口文档 |

## Complete MVP

项目完成后的最小闭环是：

```text
Markdown/PDF 目录
    -> Phase 1 解析与分块
    -> data/processed/chunks.json
    -> BM25 KnowledgeBase
    -> FastAPI /search 与 /chat
    -> source/page/chunk_id/score 引用
```

该 MVP 默认离线可运行，不依赖 LLM key。BGE-M3、Faiss、ONNX/INT8 和 OpenAI-compatible LLM 是可以用实验数据证明价值的增强项；它们不能成为项目无法启动的理由。

## Working Agreement

- 每次实验至少保留一个 baseline。
- 每次只改变一个主变量。
- 所有结论必须绑定数据集、模型版本、硬件和参数。
- 失败实验也记录原因，避免重复踩坑。
