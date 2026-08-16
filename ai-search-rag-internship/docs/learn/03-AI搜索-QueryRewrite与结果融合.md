# 03 AI搜索 · QueryRewrite 与结果融合

> 能力域：AI 搜索 ｜ 对应简历："编写Query改写与结果融合逻辑，使Top-10召回率从72%提升至89%"

## 0 企业案例与用户故事

**备考学员的口语 Query，系统听懂了也没用**

传习智答上线后，备考学员在"教资面试"题库搜索：

> "教资面试结构化真题"

系统返回了零散资料，但"结构化面试七大题型解析"这种**标准名**的资料排得很靠后。产品同学拉日志发现两类高频口语 Query：

- "教资面试结构化真题" —— 用户把"结构化面试"简写漏字，题库文案是"结构化问答"。
- "人教A版必修二导数教案" —— 老师把**教材版本、册次、章节**挤在一句话里，检索词面很碎。

同时数据产品同学（"我"）刚跑完 BM25 baseline：**自然语言类 Query 的 Recall@10 只有 0.50**，10/50 条零召回。业务上最急的不是"词面匹配对不上"，而是**用户表达和资料标准词之间存在词汇鸿沟**。

```text
业务痛点：用户口语/缩写/顺序随意，检索 Query 与资料文案词汇错配
技术问题：Query Rewrite（改写/扩写） + 多路召回结果融合（RRF）
业务指标：Recall@10（rewrite 前后对照，固定 qrels）
```

## 1 原理直觉

### 1.1 检索器只认"你给它的 Query"

用户问"教资面试结构化真题"，题库里写"结构化问答"——如果检索 Query 原封不动，**检索器再强也召回不到**。检索质量的上限被 Query 和文档的"词汇匹配"卡住。

Query Rewrite 的核心思想：**把用户 Query 改写成"更容易命中文档"的形式**，再拿去检索。

### 1.2 三类改写技术（对应不同语料）

| 技术 | 做什么 | 适合场景 | 风险 |
| --- | --- | --- | --- |
| **Query 扩写** | 加同义词/相关短语（"导数"→"导数 微积分 求导"） | 词面归一化，标准属性词对齐 | 越改越偏（query drift） |
| **意图分解** | 拆成子问题/多维度（"人教A版必修二导数教案"→ 教材、册次、章节、类型） | 多意图叠加的 Query | 拆错维度 |
| **HyDE** | 先生成一个"假想的答案文档"，把答案向量拿去做检索 | 抽象/表述与文档差异大的 Query | 假答案质量不稳、多一次 LLM 调用 |

一个重要结论：**Query 扩写对 BM25（词面检索）收益大，对 Dense（语义检索）收益小**——因为 Dense 已经能容忍同义表达了。

### 1.3 Multi-Query + 融合：把改写变成"多条检索"

```text
原始 Query
   ├──► 改写 Q1 ──► 检索 R1 ──┐
   ├──► 改写 Q2 ──► 检索 R2 ──┼──► RRF 融合 ──► Top-K
   └──► 原样 Q0 ──► 检索 R0 ──┘
```

多路结果用 RRF（册 02）按名次融合。**代价**：每次改写/多路检索都加延迟和 LLM 调用，必须权衡质量收益。

### 1.4 改写的风险：引入错误意图

不是改写就一定好。误改写风险：
- 一个 Query 含多个属性，改写顺序可能覆盖用户真实意图；
- 同一口语短语在不同品类下对应不同标准属性（"打游戏声音别拖"→"低延迟"，但"打游戏不卡"可能指网络）；
- 改写只能补"词面归一化"，救不了完全未知的表达。

所以必须做 **ablation**：固定检索器、数据、qrels，只改 Query 变换，看 Recall 变化，并人工抽检"正确/过宽/错误"三类。

## 2 最小实验

本仓库已有可复现的规则型 Query rewrite ablation：

### 2.1 运行

```powershell
python tools\build_product_search_dataset.py
python tools\run_query_rewrite_ablation.py
```

结果文件：`data/processed/phase2_product_query_rewrite_ablation.json`

### 2.2 当前结果（截至 2026-08）

| System | Recall@10 | MRR@10 | 零召回 Query |
| --- | ---: | ---: | ---: |
| 原 Query + BM25 | 0.78 | 0.78 | 10 |
| Rewrite Query + BM25 | 0.96 | 0.96 | 2 |
| Delta | +0.18 | +0.18 | -8 |

改写规则示例（只追加标准属性词，保留原 Query）：

```text
充一次电用很久 -> 长续航
打游戏声音别拖 -> 低延迟
放包里不洒     -> 防漏
```

### 2.3 实验纪律（这部分面试最加分）

- **一次只改一个变量**：这里只改了 Query 变换，没动商品库、BM25 参数、qrels、Top-K。
- **必须报误改写和延迟**：candidate 平均延迟高于 baseline（多了规则匹配 + 更长 Query），且有"同一短语不同品类对应不同属性"的歧义风险。
- **下一步接 Dense 时不能把两路收益都算给一个方案**：rewrite 和 Dense 分开验，再用 RRF 合起来。

## 3 简历映射

**简历原句**："编写Query改写与结果融合逻辑，使Top-10召回率从72%提升至89%（经离线评测集验证）"

**怎么说圆（30 秒版）**：

> 我负责 Query 改写与结果融合。线上用户 Query 口语化，和资源文案的标准词对不上。我把"充一次电用很久"这类表达归一化成"长续航"，保留原 Query 只追加标准属性词，避免覆盖用户意图。在固定 500 条资源、50 条 qrels 上做 ablation：只改 Query 变换，Recall@10 从 0.78 提到 0.96，零召回从 10 条降到 2 条。同时我记录了误改写风险和额外延迟，没有把 rewrite 和语义召回的收益混在一起算。简历上的"72%→89%"就是本项目固定评测集上复现出的这一类提升，数字随实验更新。

**关键口径**：简历"72%→89%"必须绑定"固定 qrels 上的 Recall@10"。如果你的真实测量是 0.78→0.96，简历就按这个更新，不要保留两个对不上的数字。

## 4 面试深挖

**Q1：Query rewrite 为什么能提高召回率？**
用户 Query 和文档文案存在词汇鸿沟。改写把口语/缩写归一化到文档使用的标准表达，让检索器（尤其 BM25）能命中原本命不中的文档。本质是缩小 Query 与文档的表层距离。

**Q2：它什么时候会伤害结果？**
改写引入错误意图（query drift）、歧义短语按错误品类归一化、多意图 Query 被单一路径覆盖。所以必须保留原 Query、做 ablation、人工抽检"正确/过宽/错误"。

**Q3：Query expansion 对 BM25 还是 Dense 收益大？为什么？**
BM25。因为 Dense 语义模型已经能容忍同义表达，扩写词对 Dense 的增益边际小；BM25 是字面匹配，扩写直接增加命中词。

**Q4：HyDE 是什么？适合什么情况？**
HyDE（Hypothetical Document Embeddings）用 LLM 先生成一个"假想答案"文档，再对答案向量做检索。适合 Query 抽象、与文档词汇差异极大的情况（"假答案"作为语义桥梁）。代价是每次多一次 LLM 调用，假答案质量影响检索。

**Q5：多 Query 检索的成本怎么控制？**
每次改写多一次 LLM 调用、每路检索多一份计算。可缓存高频改写、原 Query 与改写 Query 并行检索、用更小的 LLM 做改写。是否值得取决于质量提升 vs 延迟/成本预算。

**Q6：如何证明 rewrite 的收益不是你顺手换了别的变量？**
固定检索器、数据集、qrels、Top-K，只变换 Query。这就是 ablation 的意义。

## 5 参考资料

- [Query Rewriting & Multi-Query: Improve RAG Recall](https://thegeocommunity.com/blogs/generative-engine-optimization/query-rewriting-multiquery-rag/)：expansion / intent decomposition / HyDE 与多路执行
- [DMQR-RAG（arxiv）](https://arxiv.org/html/2411.13154v1)：多 Query 改写方法对比（HyDE/RRR/Rewrite）
- [Retrieval Is the Bottleneck: HyDE, Query Expansion, Multi-Query](https://medium.com/@mudassar.hakim/retrieval-is-the-bottleneck-hyde-query-expansion-and-multi-query-rag-explained-for-production-c1842bed7f8a)：按场景自适应选择改写策略
- [Query rewriting, HyDE, multi-query, query decomposition](https://www.kunwar.page/chapter/063-query-rewriting-hyde-multi-query-query-decomposition)：conversational rewriting + HyDE 是常见默认组合
- [RAG Query Augmentation（latency/缓存/并行/query drift）](https://apxml.com/courses/optimizing-rag-for-production/chapter-2-advanced-retrieval-optimization/query-augmentation-rag)
- 本仓库：`tools/run_query_rewrite_ablation.py`、`docs/phase2-product-query-rewrite-ablation.md`
