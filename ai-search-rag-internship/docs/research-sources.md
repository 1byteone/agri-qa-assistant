# AI Search / RAG 资料索引

这份索引按“先能做实验，再补理论，再做产品化”的顺序组织。官方文档和论文是结论依据；博客、视频和厂商教程只用来帮助理解或对照实现。

## A. Phase 2：Embedding、ANN 与 Hybrid Retrieval

| 资料 | 类型 | 用法 | 重点 |
| --- | --- | --- | --- |
| [BGE-M3 官方文档](https://bge-model.com/bge/bge_m3.html) | 官方文档 | 先读 Usage，再运行最小 encode | `dense_vecs`、`lexical_weights`、`colbert_vecs` 三种输出；不要把 sparse 当作普通 dense 向量 |
| [BAAI/bge-m3 模型卡](https://huggingface.co/BAAI/bge-m3) | 模型卡 | 确认模型版本、语言和上下文长度 | 记录模型 revision、最大长度、CPU/GPU 设置 |
| [FlagEmbedding 官方仓库](https://github.com/FlagOpen/FlagEmbedding) | 官方代码 | 对照推理、训练和统一微调示例 | 以仓库当前 API 为准，避免照抄旧博客 |
| [BGE-M3 论文](https://arxiv.org/abs/2402.03216) | 论文 | Phase 2 理论阅读 | 多语言、多功能、多粒度与知识蒸馏；重点理解为何同一模型可以提供不同召回信号 |
| [Faiss Indexes Wiki](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) | 官方 Wiki | 构建 Flat baseline 后读 HNSW | `M`、`efConstruction`、`efSearch` 的内存、建库和查询权衡 |
| [Faiss C++ API: IndexHNSW](https://faiss.ai/cpp_api/struct/structfaiss_1_1IndexHNSW.html) | 官方 API | 参数实验遇到歧义时查 | 确认 Python wrapper 暴露的字段和默认行为 |
| [Faiss 向量索引实战说明](https://www.pinecone.io/learn/series/faiss/vector-indexes/) | 工程教程 | 用于形成直观的索引对比 | 只采纳能在本机数据集复现的结论 |
| [Azure Hybrid Search Ranking](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking) | 官方产品文档 | 学 RRF 和分数融合 | RRF 只依赖名次，避免直接相加量纲不同的 BM25 与 cosine 分数 |
| [RRF 原论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) | 论文 | 写实验报告时引用 | 记录公式、`rrf_k`，并说明多个排序信号如何合并 |
| [Sentence Transformers Semantic Search](https://www.sbert.net/examples/applications/semantic-search/README.html) | 官方文档 | 理解 query/document 编码和 top-k | 适合先跑一个不含 Faiss 的小数据 baseline |

## B. Phase 2-3：数据集与检索评估

| 资料 | 类型 | 用法 | 重点 |
| --- | --- | --- | --- |
| [MTEB 项目](https://github.com/embeddings-benchmark/mteb/) | 官方代码/基准 | 了解通用 embedding benchmark | MTEB 不能替代你的领域数据；它用于模型横向背景，不用于直接证明本项目效果 |
| [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | 基准看板 | 观察模型任务差异 | 不只看总分，优先看 multilingual/retrieval 相关任务 |
| [BEIR 论文](https://arxiv.org/abs/2104.08663) | 论文 | 理解零样本检索评估 | 学习跨领域 benchmark 的数据划分和 nDCG@10 思路 |
| [Stanford IR Book](https://nlp.stanford.edu/IR-book/) | 教材 | 补 TF-IDF、BM25、评价指标 | 重点章节：词项权重、倒排索引、评估与 relevance judgments |
| [Hugging Face Datasets](https://huggingface.co/docs/datasets/index) | 官方文档 | 管理 QA、qrels 和版本 | 保存 dataset card、split、字段定义和随机种子 |

建议本项目统一记录：`Recall@k`、`MRR@k`、`nDCG@k`、P50/P95 latency、吞吐、索引大小、峰值内存。只报告一个指标会掩盖“召回更好但速度更慢”的真实权衡。

## C. Phase 3：ONNX、量化与 Benchmark

| 资料 | 类型 | 用法 | 重点 |
| --- | --- | --- | --- |
| [ONNX Runtime Quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) | 官方文档 | 实现动态量化和调试 | 动态/静态量化、校准、量化调试；先验证模型输出再谈速度 |
| [Optimum ONNX Runtime Quantization](https://huggingface.co/docs/optimum-onnx/onnxruntime/usage_guides/quantization) | 官方文档 | 了解 Transformers 导出路径 | 对比原生 `torch.onnx` 和 Optimum 的导出/推理封装 |
| [ONNX Runtime Performance](https://onnxruntime.ai/docs/performance/) | 官方文档 | 设计 benchmark | 预热、线程、Execution Provider、batch 和输入长度必须固定 |
| [PyTorch ONNX Export](https://pytorch.org/docs/stable/onnx.html) | 官方 API | 理解导出边界 | BGE-M3 的 dense/sparse/late-interaction 输出要分别验证，不能默认 wrapper 可直接导出 |

## D. Phase 3-4：RAG 质量与服务化

| 资料 | 类型 | 用法 | 重点 |
| --- | --- | --- | --- |
| [Ragas Metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) | 官方文档 | 选择评估指标 | Context Precision、Context Recall、Faithfulness、Response Relevancy 的输入和含义 |
| [Ragas Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) | 官方文档 | 实现生成质量评估 | Faithfulness 衡量回答声明能否被 retrieved context 支持，不等同于答案正确性 |
| [Ragas Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/) | 官方文档 | 评估排序质量 | 有 reference、无 reference、ID-based 三种思路，优先使用能人工复核的 ID 标注 |
| [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) | 官方文档 | 构建检索 API | 请求模型、错误处理、依赖注入、OpenAPI 和测试客户端 |
| [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/) | 官方文档 | Phase 4 发布 | worker、进程模型、环境变量和健康检查 |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | 官方代码 | 接入可替换 LLM | 通过环境变量和配置抽象注入，不将密钥或供应商写入代码 |

## 阅读顺序

1. BGE-M3 官方文档 + Faiss Wiki + RRF 原论文。
2. Sentence Transformers semantic search + Stanford IR Book 的 BM25/评估章节。
3. MTEB/BEIR 了解通用基准，再设计本项目自己的 qrels。
4. ONNX Runtime 官方量化文档，最后读 Ragas 与 FastAPI。

## 资料使用规范

- 论文用于解释”为什么”，官方文档用于解释”怎么做”。
- 每条外部结论都要在 `docs/experiments/` 中留下本地复现实验或明确标注为背景知识。
- 搜索结果中的 2026 年博客和排行榜只作为线索，不能替代模型卡、论文或本地测量。

## E. 2026-08-16 anysearch 新增资料（对应 docs/learn 系列）

以下资料由 anysearch 批量检索得到，要点已摘录进 `docs/learn/00~09` 各册”参考资料”节。

| 对应册 | 新增来源 | 用途 |
| --- | --- | --- |
| 01 | [BGE-M3 官方文档](https://bge-model.com/bge/bge_m3.html)、[HF 模型卡](https://huggingface.co/BAAI/bge-m3)、[BGE-M3 论文](https://arxiv.org/html/2402.03216v3)、[Milvus 集成](https://milvus.io/docs/embed-with-bgm-m3.md)、[Pristren 2026](https://pristren.com/blog/bge-m3-embeddings-multilingual/) | BGE-M3 三种输出、维度、多语言 |
| 02 | [Faiss Indexes Wiki](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)、[Zilliz HNSW 参数](https://zilliz.com/ai-faq/what-are-the-key-configuration-parameters-for-an-hnsw-index-such-as-m-and-efconstructionefsearch-and-how-does-each-influence-the-tradeoff-between-index-size-build-time-query-speed-and-recall)、[Pinecone HNSW](https://www.pinecone.io/learn/series/faiss/hnsw/)、[FAISS 10M 基准](https://markaicode.com/benchmarks/faiss-production-benchmark-latency/)、[Weaviate Hybrid](https://weaviate.io/blog/hybrid-search-explained)、[Hybrid 2026 参考](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026)、[bigdataboutique fusion](https://bigdataboutique.com/blog/hybrid-search-explained)、[BM25 vs 向量](https://prakhartripathi.hashnode.dev/hybrid-search-explained-when-to-use-keyword-vector-or-both-in-ai-applications)、[Knovo](https://www.knovo.dev/guides/semantic-search-vs-keyword) | HNSW、RRF、混合检索权衡 |
| 03 | [Query Rewriting & Multi-Query](https://thegeocommunity.com/blogs/generative-engine-optimization/query-rewriting-multiquery-rag/)、[DMQR-RAG](https://arxiv.org/html/2411.13154v1)、[HyDE/Multi-Query](https://medium.com/@mudassar.hakim/retrieval-is-the-bottleneck-hyde-query-expansion-and-multi-query-rag-explained-for-production-c1842bed7f8a)、[kunwar ch63](https://www.kunwar.page/chapter/063-query-rewriting-hyde-multi-query-query-decomposition)、[Query Augmentation](https://apxml.com/courses/optimizing-rag-for-production/chapter-2-advanced-retrieval-optimization/query-augmentation-rag) | 改写技术、HyDE、query drift |
| 04 | [Azure Chunk Documents](https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-chunk-documents)、[NVIDIA 分块策略](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/)、[Firecrawl Chunking 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)、[The Main Thread](https://themainthread.beehiiv.com/p/chunking-strategies-for-rag-the-definitive-practical-guide)、[Multigrid chunking](https://multigrid.ai/learn/rag-chunking)、[阿里云七种策略](https://developer.aliyun.com/article/1712053)、[Datawhale all-in-rag](https://github.com/datawhalechina/all-in-rag/blob/main/docs/chapter2/05_text_chunking.md)、[orrrrz](https://orrrrz.github.io/2025/01/17/rag/chunking/) | 分块策略、overlap 成本、Recursive 原理 |
| 05 | [IBM RAG + Ragas](https://www.ibm.com/think/tutorials/evaluate-rag-pipeline-using-ragas-in-python-with-watsonx)、[Netguru 语义检索](https://www.netguru.com/blog/semantic-search-vector-search-explained)、[BigDataAbout Rerank](https://bigdataboutique.com/blog/rag-reranking-improving-retrieval-quality-with-cross-encoders)、[Mixpeek Rerank](https://mixpeek.com/guides/cross-encoder-reranking) | 端到端 RAG、两阶段检索 |
| 06 | [Ragas Metrics 官方](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)、[Ragas Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)、[EvalHub 指标参考](https://eval-hub.github.io/adapters/ragas/metrics/)、[RAG 指标指南 2026](https://dev.to/dublecc/rag-evaluation-metrics-guide-2026-faithfulness-context-precision-and-how-to-score-a-pipeline-46gi)、[QASkills 深度解读](https://qaskills.sh/blog/ragas-context-precision-recall-faithfulness-guide)、[Saulius LLM-judge](https://saulius.io/blog/ragas-rag-evaluation-metrics-llm-judge)、[TowardsAI P@K/MRR/NDCG](https://pub.towardsai.net/retrieval-evaluation-metrics-p-k-mrr-ndcg-explained-bf5611ca6be5) | RAGAS 四指标、检索指标 |
| 07 | [GrowthBook AI 搜索 A/B](https://www.growthbook.io/insights/ab-test-ai-powered-search-recommendations)、[Algorithmic 搜索 A/B](https://www.algorithmic.co/blogs/search-relevance-testing-ab-evaluation)、[Algolia 指标](https://www.algolia.com/blog/engineering/a-b-testing-metrics-evaluating-the-best-metrics-for-your-search)、[Tunkelang](https://dtunkelang.medium.com/a-b-testing-for-search-is-different-f6b0f6f4d0f5)、[Wizzy 查询分类](https://wizzy.ai/blog/search-query-classification-for-ecommerce-models-signals-failure-modes/)、[Nobi 搜索成本](https://nobi.ai/blog/cost-of-bad-site-search) | A/B 陷阱、Bad Case 分类 |
| 08 | [OpenSearch HNSW 超参](https://opensearch.org/blog/a-practical-guide-to-selecting-hnsw-hyperparameters/)、[Marqo HNSW Recall](https://www.marqo.ai/blog/understanding-recall-in-hnsw-search)、[Ashutosh HNSW](https://www.ashutosh.dev/understanding-hnsw-a-practical-guide/)、[OneUptime 向量索引](https://oneuptime.com/blog/post/2026-01-30-vector-indexing/view) | HNSW 参数与 benchmark |
| 09 | [ONNX Runtime Quantization 官方](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)、[ONNX Model Optimizations](https://onnxruntime.ai/docs/performance/model-optimizations/)、[Medium ONNX+量化](https://medium.com/@bhagyarana80/optimizing-transformer-inference-with-onnx-runtime-and-quantization-098f8149a15c)、[Nixiesearch 3×](https://medium.com/nixiesearch/how-to-compute-llm-embeddings-3x-faster-with-model-quantization-25523d9b4ce5)、[PyTorch ONNX](https://pytorch.org/docs/stable/onnx.html) | ONNX 导出、量化、一致性验证 |

