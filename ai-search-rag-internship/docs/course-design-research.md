# Evidence Quest 课程设计研究记录

## 研究结论

当前课程的技术链路已经完整，但“完整”不等于“学得进去”。本次改造采用一个连续的 Evidence Quest 任务世界：学习者扮演知识库调查员，为自己选择的真实观众处理一宗案件。每一关都先交付一个能被看见、能被下一关读取的作品，再补上解释该作品所必需的知识。

这里没有可用的 `anysearch` 技能名称，也没有可用的 Firecrawl API Key，因此没有伪造搜索结果。研究使用已读取的 Firecrawl 深度研究规范，并采用可直接访问的论文、官方文档和项目制学习资料完成等价的多来源研究。限制是：没有对付费或需要登录的课程内容做结论。

## 资料与对课程的改变

| 资料 | 关键证据 | 对本课程的具体改变 |
| --- | --- | --- |
| [PBLWorks: What is PBL](https://www.pblworks.org/what-is-pbl) | 项目应围绕真实、有意义的问题，持续探究，并面向真实观众交付公开作品。 | 新增 Mission Control；先定义 audience、must_answer 和 must_refuse；每个 Phase 交付作品，而不是把项目放到课程最后。 |
| [Carpentries Instructor Training](https://carpentries.github.io/instructor-training/) | 短讲解和实践交替；live coding 是可学习的教学技能；反馈和认知负荷会影响学习。 | 每课使用“故事 -> 一小段跟敲 -> 观察输出 -> 独立挑战 -> 断言验收”；Boss Challenge 默认全是注释，减少复制粘贴。 |
| [原始 RAG 论文](https://arxiv.org/abs/2005.11401) | RAG 结合参数化记忆和可更新的非参数化记忆；检索结果应能支撑知识更新与来源追踪。 | 把 source、page、chunk_id 和 citations 变成案件证据合同，而不是最后临时添加的字段。 |
| [RAG Survey](https://arxiv.org/abs/2312.10997) | Naive、Advanced、Modular RAG 需要分别理解 retrieval、augmentation、generation 和 evaluation。 | 四个 Phase 采用明确角色：文档考古、搜索对决、性能实验、证据工作台；每关只聚焦下一条能力。 |
| [LlamaIndex RAG 文档](https://docs.llamaindex.ai/en/stable/understanding/rag/) | RAG 可拆成 Loading、Indexing、Storing、Querying、Evaluation；Node 是文档的原子 Chunk，metadata 很重要。 | Phase 1 的作品从 Document inventory 到 chunks.json；Phase 2/3/4 直接消费上一步文件，形成连续的生产线。 |
| [LangChain Retrieval 概念](https://python.langchain.com/docs/concepts/retrieval/) | Retrieval 的价值在于为模型提供其训练数据之外的外部知识；索引和查询是不同职责。 | 教程先建立离线 BM25 evidence-first baseline，再把 Dense、Hybrid 和 LLM 作为有边界的升级。 |
| [Elasticsearch BM25 Similarity](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-similarity.html) | BM25 的 TF、IDF、长度归一化参数影响词项匹配和文档长度公平性。 | Phase 2.1 增加关键词命中解释、稀有词/常见词实验和 Search Duel 排行榜。 |
| [Faiss Getting Started](https://github.com/facebookresearch/faiss/wiki/Getting-started) | 向量检索应先有可解释的基础索引，再讨论 ANN 的速度和召回权衡。 | Phase 2.2 用二维向量只解释 cosine 机制，明确标注不等同于 BGE-M3 真实成绩。 |
| [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) | 请求模型、响应模型、错误处理和自动化测试构成接口的可用性基础。 | Phase 4 先写 API 合同，再做服务；最终 Demo 必须展示 health、search、chat、fallback 和 citations。 |

## 采用的学习循环

每个 Notebook 生成器现在自动增加以下结构：

```text
任务卡：我是谁、案件是什么、Goal 是什么、作品是什么
逐行跟敲：每条关键语句上方都有中文注释
最小观察：先看中间变量和输出，再谈抽象原理
Boss Challenge：同一能力重新实现，模板默认注释
作品检查站：检查下一阶段需要的文件是否真的写入磁盘
```

## 兴趣驱动的质量标准

趣味性不能只靠颜色、积分或故事标题。每一关至少需要满足三项：

1. 学习者能在 30 分钟内看到一个新增能力，例如从文件得到可回溯 Chunk，或从 Query 得到带解释的排名。
2. 结果能被真实观众理解，例如排行榜、证据卡、速度计时卡或可点击引用，而不只是 Python 对象打印。
3. 失败也产生信息，例如边界救援、无证据拒答、Recall 下降或 P95 变差，并要求学习者写出归因。

## 诚实边界

- 当前默认链路是离线 BM25 + evidence-first，不依赖 API Key。
- 二维 Dense 实验只用于解释向量和融合机制，不能写成 BGE-M3 的实验结果。
- 课程中的 XP 和徽章是反馈工具，不是能力证明；真正的通关证据仍是代码、产物、指标和解释。
- 没有真实用户访谈时，`audience` 是学习者的可验证假设，不应包装成市场结论。

## Sources

以上链接均作为课程设计和技术边界的研究输入；技术资料的完整索引见 [`docs/research-sources.md`](research-sources.md)。

## Rerun Inputs

```text
workflow: firecrawl-deep-research equivalent local-source synthesis
topic: interest-driven project-based learning for an offline evidence-first Mini RAG
depth: thorough
output: markdown + generated Jupyter curriculum
```
