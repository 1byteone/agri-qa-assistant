# 06 效果评估 · RAGAS 与检索指标

> 能力域：效果评估 ｜ 对应简历："基于RAGAS框架编写Faithfulness/Relevance评测代码，构建200条标注测试集"

## 0 企业案例与用户故事

**"从 61% 到 87%"到底是怎么算出来的**

版本评审会上，算法同学说"这版 RAG 好了很多"。产品经理当场追问：

> "好多少？你凭什么说好？是检索变好了还是回答变好了？"

没人能当场回答。于是数据产品同学（"我"）接了个任务：**建立可量化的效果基线**。

要求很具体：

1. 建一个 **200 条 QA 标注集**，包含单跳、多跳、不可回答三种样本——因为上次分析发现多跳问题在拉低整体。
2. 把 **检索质量** 和 **回答质量** 分开打分：检索看 Recall/Context Precision，回答看 Faithfulness/Relevance。
3. 每次版本迭代都重跑同一套评测，产出"61% → 74% → 87%"这种有依据的曲线，而不是拍脑袋。

一个真实的尴尬插曲：王老师问"教案提交规范"，回答很流畅、也带引用，但**内容和文档里的规范完全相反**——流畅 ≠ 正确。这正好说明只看"有没有引用/回答顺不顺"不够，要测 **Faithfulness**。

```text
业务痛点：RAG 好坏无法量化，检索和生成混在一起无法定位短板
技术问题：检索指标（Recall@K/MRR/NDCG）+ RAGAS（Faithfulness/Relevancy/Context Precision/Recall）
业务指标：Faithfulness、Answer Relevancy、Context Recall、Context Precision + 人工通过率
```

## 1 原理直觉

### 1.1 一个 RAG 分数要拆成两半

- **检索**决定哪些 chunk 进模型；**生成**决定模型怎么用。单看端到端准确率，永远不知道坏在哪。
- 好团队把失败按"症状→环节→指标"归类：

| 症状 | 环节 | 指标 |
| --- | --- | --- |
| 答案存在但说"不知道" | 检索 | Context Recall / Hit Rate |
| 正确 chunk 排第 8，模型没读 | 检索排序 | MRR / NDCG / Context Precision |
| 回答流畅但编造上下文里没有的事实 | 生成 | Faithfulness |
| 忠实但没回答提问 | 生成 | Answer Relevancy |
| 答对了但漏了一半要点 | 端到端 | Answer Correctness |

### 1.2 检索指标（不需要 LLM，可手写）

```text
Precision@K = (Top-K 中相关数) / K              # 返回的对不对
Recall@K    = (Top-K 中相关数) / (总相关数)       # 该召回的召回了吗
MRR         = mean(1 / 首个相关结果的排名)          # 第一个对的排第几
NDCG@K      = 按位置折价的累积增益 / 理想排序       # 越靠前越值钱
```

为什么排序重要？LLM 不是每格权重一样——**相关 chunk 排第 9 和排第 1 对回答贡献天差地别**（Lost in the Middle）。

### 1.3 RAGAS：LLM 当裁判的结构化评测

RAGAS 用 **LLM-as-judge**：让一个 LLM 按固定 schema 输出结构化打分。核心机制：

1. 先定义输出 JSON schema + few-shot 示例；
2. 调用 judge LLM 按 schema 打分；
3. 解析失败就"修复格式"重试。

四个核心指标：

| 指标 | 需要哪些输入 | 它回答什么 | 算法要点 |
| --- | --- | --- | --- |
| `faithfulness` | 问题、回答、检索上下文 | 回答是否被证据支持？ | 把回答拆成原子声明，逐个判断是否被上下文蕴含 |
| `answer_relevancy` | 问题、回答、上下文 | 回答是否相关？ | 由回答反推问题，与原始问题算语义相似 |
| `context_precision` | 问题、上下文、参考 | 相关 chunk 是否排前面？ | 按位置加权的 precision@k |
| `context_recall` | 上下文、参考 | 参考要点是否都被覆盖？ | 参考拆句，逐句判断能否由上下文支持 |

**典型生产目标参考**：Context Precision ~0.7、Context Recall ~0.85、Faithfulness ~0.85（随领域浮动，不是教条）。

### 1.4 三个指标要一起读

- Context Precision = 是否**返回了有用**的块（能不能定位）。
- Context Recall = 是否**返回了足够**的块（全不全）。
- Faithfulness = 回答是否**忠实于**上下文。

**低 recall 会伪装成高 faithfulness**：模型只看到很少上下文，干脆拒绝回答——Faithfulness 高但 Recall 低，短板在检索。诊断决策树：

```text
低 Context Recall  → 扩大检索 / 换分块 / 更大 Top-K
低 Context Precision → 加 Rerank / 改 Query / 更好 Embedding
高 Recall/Precision 但低 Faithfulness → 问题在 prompt 或生成模型
```

### 1.5 为什么还要人工评测？

LLM-as-judge 快但会错：judge 模型选择影响分数、小样本下易出 0/1 二值、对"事实相反"这类错误不敏感（流畅但错误的回答往往被高估）。所以 200 条标注集 + 3 名标注员的人工评测（见册 07）仍是基线，RAGAS 负责规模化迭代。

## 2 最小实验

### 2.1 先手写检索指标（5 分钟，别急着装 RAGAS）

```powershell
python -m pytest -q tests/test_phase2_core.py
```

```python
from phase2_semantic_search.metrics import recall_at_k, mrr_at_k, evaluate_qrels

recall_at_k(["a", "b", "c"], {"b"}, k=3)   # 1/1 = 1.0
mrr_at_k(["a", "b", "c"], {"b"}, k=3)      # 1/2 = 0.5
evaluate_qrels({"q1": ["a", "b"]}, {"q1": {"a", "b", "c"}}, k=2)  # recall@2=0.5, mrr@2=1.0
```

qrels 模板见 `docs/templates/qrels.example.json`。

### 2.2 设计 200 条 QA 标注集（先定规范再标数据）

标注维度（对齐业务）：
- 问题类型：单跳 / 多跳 / 不可回答
- 领域：制度 / 课程 / 教务 / 招生
- 难度：事实型 / 推理型
- 字段：`question / ground_truth / needed_documents / category / hop_type`

模板见 `docs/templates/qa-eval.example.json`。**200 条里必须掺不可回答和多跳样本**，否则评测集本身失真。

### 2.3 接入 RAGAS（装 `requirements/phase3.txt`）

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

result = evaluate(
    dataset,   # 需含 user_input / response / retrieved_contexts / reference
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
```

**实验记录必须含**：judge 模型与版本、温度、失败重试次数、成本、评测集版本。否则同一份代码换 judge 模型分数就漂移。

## 3 简历映射

**简历原句**："搭建RAG检索质量自动化评估脚本：基于RAGAS框架编写Faithfulness/Relevance评测代码，构建200条标注测试集，为算法迭代提供可量化的效果基线，支撑3轮版本上线"

**怎么说圆**：

> 我搭的评估分两层：检索层用手写的 Recall@K/MRR 和 Context Precision，生成层用 RAGAS 的 Faithfulness/Relevance。我牵头定了 200 条 QA 标注规范——单跳/多跳/不可回答三种类型都覆盖，避免评测集只测简单问题。每次版本迭代跑同一套评测，把"检索"和"生成"分开看：比如某版整体分数没动，但拆开发现是检索变差了、生成没变，就能精准定位。这套基线支撑了 3 轮版本上线，简历上的准确率提升就是以这套评测口径得出的。

**口径**："61%→87%"要绑定评测集版本和 judge 配置。如果 RAGAS 没接、只有人工评测，就写人工通过率。

## 4 面试深挖

**Q1：Faithfulness 是什么意思？**
衡量回答中的每个声明能否被检索到的上下文支持。算法：把回答拆成原子声明，逐个判断上下文是否蕴含，得分 = 被支持的声明比例。1.0 = 完全有据，0.0 = 全在编。它不等于"答案正确"，只等于"没跑出上下文"。

**Q2：Context Precision 和 Context Recall 的区别？**
Precision 看"返回的块里有用的多不多 + 有用的有没有排前面"；Recall 看"参考答案的要点有没有被覆盖"。一个管定位质量，一个管覆盖完整度，配合 Rerank/更大 Top-K 对症下药。

**Q3：为什么还需要人工评测？**
LLM-as-judge 受 judge 模型影响、小样本易二值、对"流畅但错误"不敏感；人工评测贴近业务真实标准，还能产生标注数据用于后续优化。RAGAS 管规模化，人工管兜底。

**Q4：三个指标怎么一起读？**
见 1.4 决策树：高 Precision 低 Recall → 检索不全；低 Precision → 排序/召回质量差；都高但 Faithfulness 低 → 生成/prompt 问题。

**Q5：评测集的 200 条怎么保证不偏？**
覆盖单跳/多跳/不可回答、多个业务领域、事实型与推理型；定义相关性标准；标注员间算一致性（见册 07）；版本化（`data_version`）。

**Q6：Recall@10 怎么计算？**
对每条 Query：`|Top-10 ∩ 相关集| / |相关集|`，再对所有 Query 取平均。相关集来自 qrels 标注。

## 5 参考资料

- [Ragas Metrics（官方文档）](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Ragas Context Precision（公式）](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)
- [EvalHub: RAGAS 指标参考](https://eval-hub.github.io/adapters/ragas/metrics/)：5 个核心指标、输入列要求
- [RAG Evaluation Metrics Guide 2026（症状→指标对照）](https://dev.to/dublecc/rag-evaluation-metrics-guide-2026-faithfulness-context-precision-and-how-to-score-a-pipeline-46gi)
- [QASkills: Context Precision/Recall/Faithfulness 深度解读](https://qaskills.sh/blog/ragas-context-precision-recall-faithfulness-guide)：三个指标交互、生产目标、决策树
- [Saulius: Ragas 指标实现机制](https://saulius.io/blog/ragas-rag-evaluation-metrics-llm-judge)：LLM-as-judge 的 schema/重试/嵌入
- [TowardsAI: P@K/MRR/NDCG 全解 + Python 实现](https://pub.towardsai.net/retrieval-evaluation-metrics-p-k-mrr-ndcg-explained-bf5611ca6be5)
- 本仓库：`phase2_semantic_search/metrics.py`、`docs/templates/qrels.example.json`、`docs/templates/qa-eval.example.json`
