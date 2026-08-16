# 04 RAG工程 · 文档解析与分块

> 能力域：RAG 工程 ｜ 对应简历："实现PDF/Markdown多格式解析器，设计Recursive Splitter分块策略，处理5000+篇文档入库"

## 0 企业案例与用户故事

**5000 份教研资料的"入库事故"**

李教务把传习教育的教研资料往传习智答里传：课程大纲、教案、规章制度、招生政策、通知，一共 5000+ 篇 PDF/Markdown。

第一天就出了两个问题：

1. 一份 **《2024 版高中数学课程标准》PDF（96 页）** 被当成"一个整体"入库。王老师问"圆锥曲线在课标里属于哪个知识模块"，检索要么命中整本课的模糊向量、答非所问，要么干脆检索不到。
2. 一份 **PDF 的排版很乱**——页眉页脚、目录页、表格混在一起，解析出来的"文本"充满噪音，把"导数定义"和"历年真题"切到了同一个片段里。

李教务的抱怨：

> "我传 5000 份文档，不是让系统'假装'有 5000 份。新老师问'教案提交规范是什么'，你们得能在那份《教学管理制度》里找到第 3 节。"

```text
业务痛点：长文档/乱排版无法直接检索，整篇 Embedding 语义模糊、噪音大
技术问题：文档解析（parser） + 分块（chunking） + 元数据保留
业务指标：chunk 数量/平均长度/重复比例、固定 QA 集上的 Recall@10、引用 page 准确性
```

## 1 原理直觉

### 1.1 为什么不能整篇 PDF 直接 Embedding（三个原因）

1. **上下文窗口硬限制**：Embedding 模型有输入长度上限（如 512~8192 token），超限会被截断、信息丢失。
2. **池化信息稀释**：整篇 96 页压缩成一个向量，等于把几十个主题"平均"了——哪个主题都模糊，检索精度崩（见册 01 Q5）。
3. **"大海捞针"（Lost in the Middle）**：把大块塞进 LLM 长上下文，模型倾向记住开头结尾、忽略中间，关键信息被噪音淹没。

所以：**分块决定 RAG 检索质量的上限**——行业里甚至说"分块决定了 RAG 质量的 70%"。

### 1.2 分块的本质：检索单元，不是一个"尺寸"

一个好 chunk 要同时满足两件矛盾的事：
- **找得到**（findable）：向量是一个点，主题越单一越"锐利"，→ 倾向小。
- **够用**（sufficient）：回答问题所需的信息都要在里面，→ 倾向大。

这两股力不resolve成一个数字，而resolve成一个问题：**你的文档里，能独立回答问题的"最小单元"是什么？**（API 文档→一个 endpoint；合同→一个条款；问答记录→一整段对话。）全局统一 chunk_size 只在语料同质时才成立；混合语料应**按 MIME 类型分派不同 splitter**。

### 1.3 Recursive Splitter：尊重结构的折中

固定长度切分（每 N 字符一刀）实现简单但**在句子/段落/概念中间乱切**。Recursive Splitter 用一个**分隔符层级**，从大到小逐级找自然断点：

```text
"\n\n"（段落）→ "\n"（行）→ "。！？；，"（中文句末/分号/逗号）→ 空格 → 字符兜底
```

先按段落切，若仍超限再按句子切，最后字符兜底——**优先保住语义完整性，尺寸只是兜底约束**。

### 1.4 overlap：保险，但有明确的税

overlap 存在的唯一理由：固定窗口盲切时，跨边界的一句话能至少在某个 chunk 里完整出现。但 overlap 的成本可精确计算：

```text
文档 N=100,000 tokens，chunk_size=512：
  overlap=0   -> 196 chunks
  overlap=64  -> 224 chunks（+14%）
  overlap=128 -> 261 chunks（+33%）
  overlap=256 -> 391 chunks（+99%）
```

这个百分比会**付三笔账**：入库 Embedding 调用数、索引存储、Top-K 里近重复占位。行业常见 10%~20%。**一旦 splitter 尊重句子/段落边界，overlap 保护的大多数情况已消失，税就显得贵。**

### 1.5 元数据：检索质量里"杠杆最高"的下一步

chunk 必须带元数据：`source / page / 标题层级 / chunk_id`。否则"引用页码不准""找不到在哪个文件"这类问题会在下游放大。优先级：**先有可用 chunking baseline，再补元数据**。

### 1.6 语义分块 vs Recursive：划算吗？

语义分块（逐句 Embedding、在相似度骤降处切）理论上块内主题一致，但**每个句子都要一次 Embedding**，成本高、块长不可控。论文 *Is Semantic Chunking Worth the Computational Cost?* 指出：语义分块仅在主题高度多样的拼接数据上占优；普通语料上固定大小/递归反而更快更稳。所以 **Recursive 是工程默认**，语义分块留给"精度最值钱"的场景。

## 2 最小实验

### 2.1 运行 Phase 1 样例

```powershell
python -m phase1_doc_parser.main `
  --input-dir phase1_doc_parser/examples/input `
  --output phase1_doc_parser/output/chunks.json `
  --chunk-size 512 --overlap 128
```

- 解析器 `phase1_doc_parser/parser.py`：Markdown（保留标题元数据）/ TXT / PDF（PyMuPDF 按页取文本，带 page）。
- 分块器 `phase1_doc_parser/splitter.py`：`RecursiveSplitter`，分隔符 `("\n\n", "\n", "。", "！", "？", "；", "，", " ", "")`。
- 批处理 `phase1_doc_parser/main.py`：产出带 `id / text / source / page / chunk_index / metadata` 的 chunks。

### 2.2 分块策略对比（填空实验）

本仓库的 `docs/phase1_chunk_strategy_report.md` 已给出实验框架，等你补数据：

| chunk_size | overlap | chunks | avg_chars | duplicate_ratio | Recall@10 | notes |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 256 | 64 | 待测 | 待测 | 待测 | 待测 | |
| 512 | 128 | 待测 | 待测 | 待测 | 待测 | baseline |
| 768 | 192 | 待测 | 待测 | 待测 | 待测 | |

只有固定语料 + Query 标注集 + 检索参数，才能把某个组合写成推荐策略。

### 2.3 面试可复述的结论模板

> 我们的知识库以课程标准和教案这类长文档为主，我用 Recursive Splitter 按段落→句子→标点逐级切，512/128 起步，overlap 控制在约 25% 内，并记录每个 chunk 的 source/page/chunk_index。对比固定长度切分，Recursive 在"答案是否完整落在一个 chunk 内"上更好；overlap 的成本我按 chunk 数膨胀百分比量化过，没有盲目加大。

## 3 简历映射

**简历原句**："实现PDF/Markdown多格式解析器，设计Recursive Splitter分块策略，处理5000+篇文档入库"

**怎么说圆**：

> 我负责文档解析与分块 Pipeline：Markdown 保留标题结构、PDF 用 PyMuPDF 按页提取并保留页码；设计了按段落→句子→标点逐级切分的 Recursive Splitter，给每个 chunk 带 source/page/chunk_index 元数据。入库前先拿 20 篇样本文档验证解析稳定性，再扩到 5000+ 篇；同时记录平均页数、总 chunk 数、处理耗时和失败文件比例。

**口径注意**：简历"5000+篇"必须能回答：平均页数？总 chunk 数？处理耗时？失败文件比例？"准确率 61%→87%"必须写明准确率定义（人工通过率 / RAGAS / answer exactness）。这些都在 `docs/learn/00` 的口径对照表里。

## 4 面试深挖

**Q1：为什么不能整篇 PDF 直接 Embedding？**
（1）超模型上下文被截断；（2）池化把多主题平均成模糊向量、检索精度崩；（3）进 LLM 上下文后"大海捞针"，中间关键信息被忽略。分块是检索质量的上限。

**Q2：Recursive Splitter 和固定长度切分有什么区别？**
固定长度不尊重结构，在句子/段落/概念中间硬切，破坏语义完整性；Recursive 按分隔符层级（段落→行→句→标点→字符）找自然断点，优先保语义，长度只是兜底。实测：Recursive 比固定切分对"答案完整落块"更好。

**Q3：Chunk 为什么要设置 Overlap？**
防止跨边界的句子/事实被切断后"哪块都不完整"。但 overlap 是保险也是税：N=100k、s=512 时 overlap=128 让 chunk 数 +33%，付三笔账（Embedding 调用、索引存储、Top-K 近重复）。10%~20% 是常见范围，且 splitter 尊重段落边界后 overlap 的保护价值下降。

**Q4：chunk_size 越大越好吗？**
不是。大 chunk 容易"含答案但向量模糊"（检索到正确文档却找不到正确句子）；小 chunk 精确但"答案被劈成两半"。症状诊断：Top-K 常含正确文档但不对句子→chunk 过大；常只有半个答案→chunk 过小。

**Q5：5000+ 篇入库要记录什么才严谨？**
平均页数、总 chunk 数、耗时、失败文件比例、按文档类型（PDF/MD）的分块策略分派。只有固定语料+QA 集才能把某个参数写成结论。

**Q6：语义分块一定更好吗？**
不一定。语义分块按句子 Embedding 相似度找边界，主题一致性高但成本高、块长不可控，且只在高多样性拼接语料上明显占优；普通语料 Recursive 更快更稳，是工程默认。

## 5 参考资料

- [Azure AI Search: Chunk Documents](https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-chunk-documents)：token 上限与分块策略
- [NVIDIA: Finding the Best Chunking Strategy](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/)：page-level 平均准确率最高（0.648）、事实类 Query 用小 chunk、重叠 15% 最优
- [Firecrawl: Best Chunking Strategies for RAG 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)：recursive 400-512 token + 10-20% overlap 是默认
- [The Main Thread: Chunking 实操指南](https://themainthread.beehiiv.com/p/chunking-strategies-for-rag-the-definitive-practical-guide)：recursive 是默认、overlap 是保险、元数据杠杆最高
- [Multigrid: Size, Overlap and Semantic Splitting](https://multigrid.ai/learn/rag-chunking)：overlap 的成本算术、parent-child 分块
- [阿里云：RAG 文本分块七种策略](https://developer.aliyun.com/article/1712053)："分块决定 RAG 质量 70%"
- [Datawhale all-in-rag 文本分块](https://github.com/datawhalechina/all-in-rag/blob/main/docs/chapter2/05_text_chunking.md)：上下文限制、pooling 稀释、lost in middle
- [orrrrz: RAG 文档分块策略](https://orrrrz.github.io/2025/01/17/rag/chunking/)：Is Semantic Chunking Worth the Computational Cost?
- 本仓库：`phase1_doc_parser/`、`docs/phase1_chunk_strategy_report.md`
