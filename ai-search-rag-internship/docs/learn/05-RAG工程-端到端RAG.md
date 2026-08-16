# 05 RAG工程 · 端到端 RAG

> 能力域：RAG 工程 ｜ 对应简历："配合算法同学完成检索效果联调，问答准确率从61%提升至87%"

## 0 企业案例与用户故事

**王老师的第一天 vs 李教务的多跳**

王老师（新入职教师）在传习智答问：

> "教案提交规范是什么？"

系统从《教学管理制度》里找到第 3 节，给出带引用的回答："教案需在开课前 3 天提交，包含三维目标……"——**检索对了，回答也忠实**。

但李教务问了一个更难的问题：

> "这学期数学课改之后，高考大纲的考点有哪些变化？"

这个问题要**跨两份文档**：《2024 数学课改通知》和《高考大纲》。系统只在其中一份里检索，回答要么只覆盖课改、要么只覆盖大纲，**多跳信息拼不起来**。

产品同学把两类问题分开统计后发现：**单跳问题准确率不错，多跳问题明显拉低整体**。于是团队决定把"检索质量"和"生成质量"拆开评测——否则永远不知道 61% 的准确率到底坏在哪一环。

```text
业务痛点：检索对但生成错、检索错生成再好也没用，两阶段混在一起无法定位
技术问题：端到端 RAG（Retriever + Generator）+ 引用 + 两阶段分而治之的评测
业务指标：准确率（需定义口径）、Faithfulness、Context Recall、引用 page 准确
```

## 1 原理直觉

### 1.1 RAG 是什么：让 LLM "带着资料答题"

LLM 的知识是静态训练数据里的，无法访问你的知识库。RAG 在生成前加一步**检索**：把用户问题去向量库/关键词库找出相关 chunk，塞进 prompt，再让 LLM 基于这些证据作答。

```text
用户问题 → Query处理 → Retriever → Top-K chunks → Prompt(证据) → LLM → Answer
                                          └──────────► 带 [chunk_id] 引用
```

### 1.2 RAG vs Fine-tuning（经典面试题）

| | RAG | Fine-tuning |
| --- | --- | --- |
| 知识来源 | 外部知识库，检索时取 | 模型参数（训练时固化） |
| 更新知识 | 改文档即可，秒级 | 需重新训练 |
| 可解释性 | 有引用，可追溯 | 黑盒 |
| 成本 | 每次检索+推理 | 训练成本高 |
| 适用 | 私有/高频更新的业务知识 | 稳定风格/行为/格式适配 |

RAG 和微调**互补**：RAG 管"知识怎么取"，微调管"模型怎么答"。面试说"我用 RAG 解决知识时效和私有资料，因为改文档就能更新、还能给引用"就对了。

### 1.3 为什么 61% 的准确率说不清"坏在哪"

一个 RAG 回答 = **检索**（哪些 chunk 进了 prompt）+ **生成**（模型怎么用这些 chunk）。单看端到端准确率，分不清：

| 症状 | 坏在哪一环 | 对应指标 |
| --- | --- | --- |
| 答案存在但说"不知道" | 检索 | Context Recall |
| 相关 chunk 被排到第 8 位，模型没看到 | 检索排序 | Context Precision / MRR |
| 编造了上下文里没有的事实 | 生成 | Faithfulness |
| 忠实但答非所问 | 生成 | Answer Relevancy |

所以好团队**拆开打分**：先评检索（Recall/Precision/MRR），再评生成（Faithfulness/Relevancy），才能定位 61% 卡在哪。

### 1.4 两阶段检索：快召回 + 慢精排

第一路检索（bi-encoder）目标是把正确答案塞进 Top-50~200，**不是 Top-1**；而 LLM 只读 Top-3~10。中间加一个 **cross-encoder Rerank**（对 (query, doc) 联合编码打分）能把 NDCG@10 提升 5~15 分。典型链路：

```text
Retrieve(Top-100) → Rerank(Top-10) → Prompt → LLM
```

### 1.5 引用的价值：可解释 + 可纠错

每个回答关键事实后保留 `[chunk_id]`，用户能点开溯源。这既是产品体验，也是排障手段：引用页码不准时，多半是 parser/page 元数据或 overlap 边界问题（册 04）。

## 2 最小实验

### 2.1 跑通 evidence-first Mini RAG（默认离线，不依赖 LLM key）

```powershell
conda activate 'F:\anaconda\miniconda3\envs\ai-rag-internship'
python -m phase4_mini_rag_system
```

浏览器打开 `http://127.0.0.1:8000/`。链路：Phase 1 解析分块 → BM25 KnowledgeBase → FastAPI `/search`、`/chat` → 带 source/page/chunk_id/score 的 evidence-only 回答。

### 2.2 理解代码（`phase4_mini_rag_system/knowledge_base.py`）

- `ingest()`：`build_chunks` + `BM25Retriever`，index_version 记录 `chunks-{n}-size-{s}-overlap-{o}`。
- `search()`：按 source 过滤的可追溯检索。
- `answer()`：`RAG_ENABLE_LLM=true` 时走 OpenAI-compatible 模型，system prompt 强制"只根据证据回答 + 保留 [chunk_id] 引用"；无 key 时回退 evidence-only。**LLM 供应商通过环境变量注入，不写死。**

### 2.3 给"准确率"下一个可测量的定义

在写"61%→87%"之前，先定义准确率。三种常见口径：

| 口径 | 怎么测 | 优缺点 |
| --- | --- | --- |
| 人工通过率 | 标注员判定回答是否正确 | 最贴近业务，慢、贵 |
| RAGAS 分数 | LLM-as-judge（见册 06） | 快、可自动，受 judge 模型影响 |
| answer exactness | 与 ground truth 字符串匹配 | 最机械，忽略合理变体 |

**口径必须先定死再谈 61%→87%**，否则这个数字在面试里一击就碎。

## 3 简历映射

**简历原句**："配合算法同学完成检索效果联调，问答准确率从61%提升至87%"

**怎么说圆**：

> 我搭的 Mini RAG 是两阶段可拆的：文档解析分块 → 检索 → 带引用生成。为定位准确率卡在哪，我把"检索"和"生成"分开评测：检索用固定 QA 集上的 Recall/Context Precision，生成用 Faithfulness。发现大部分失败是检索没把相关 chunk 带进来（尤其多跳问题），于是主攻检索（扩 chunk、调 Top-K、补元数据、必要时接 rerank），生成侧只约束"依据证据回答+引用"。迭代后整体准确率提升，但简历上的数字我会写清楚用的是哪种口径、在哪个评测集上测的。

**口径红线**：如果"61%→87%"没有对应的评测集和口径定义，就不要原样写进简历。可以先写成"在某 200 条 QA 评测集上，人工通过率/正确答案率从 X% 提升到 Y%"。

## 4 面试深挖

**Q1：RAG 和 Fine-tuning 有什么区别？什么时候用哪个？**
见 1.2。RAG 管知识获取（改文档即更新、可引用），微调管行为/风格适配。知识更新频繁、要可追溯 → RAG；需要稳定输出格式/领域口吻 → 微调；常两者结合。

**Q2：为什么检索对但回答还错？**
生成阶段问题：模型没忠实依据证据（幻觉）、答非所问、或 prompt 约束不够。这正是 Faithfulness/Relevancy 指标存在的意义。

**Q3：为什么多跳问题难？**
答案分散在多个文档/chunk，单路 Top-K 常常只带回其中一部分；需要查询分解、多轮检索、或上下文拼接。评测时要把单跳/多跳样本分开标注，否则一个数字掩盖结构性问题。

**Q4：引用为什么会不准？**
parser 未保留 page、chunk 边界切在段落中、overlap 造成同一事实重复出现在多个 chunk 里导致引用歧义。对策：保留 source/page/chunk_index 元数据，回答强制带引用。

**Q5：为什么召回之后还要 Rerank？**
召回为"不漏"设计（Recall），精排为"把对的放前面"设计（Precision）。LLM 只读前几名，一个相关 chunk 排第 9 和排第 1 的效果天差地别（Lost in the Middle 也说明位置重要）。

**Q6：如何证明是检索环节的问题而不是生成环节？**
拆开评测：固定生成、换检索（或反之），看端到端分数怎么动；配合 Bad Case 分类（无召回/错召回/召回对但答错）。

## 5 参考资料

- [IBM: Evaluate RAG pipeline using Ragas with watsonx](https://www.ibm.com/think/tutorials/evaluate-rag-pipeline-using-ragas-in-python-with-watsonx)：RAG 全流程 + 评测
- [Netguru: From keyword search to semantic discovery](https://www.netguru.com/blog/semantic-search-vector-search-explained)：检索层是 LLM 访问私有数据的关键
- [BigDataAbout: RAG Reranking with Cross-Encoders](https://bigdataboutique.com/blog/rag-reranking-improving-retrieval-quality-with-cross-encoders)：bi-encoder vs cross-encoder、NDCG 提升 5-15 分
- [Mixpeek: Cross-Encoder Reranking（两阶段检索）](https://mixpeek.com/guides/cross-encoder-reranking)：快召回 + 慢精排
- [Datawhale all-in-rag](https://github.com/datawhalechina/all-in-rag)：RAG 全栈中文教程
- 本仓库：`phase4_mini_rag_system/`、`docs/templates/qa-eval.example.json`
