from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def md(text: str) -> dict:
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str) -> dict:
    return nbf.v4.new_code_cell(text.strip())


def notebook(cells: list[dict]) -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3 (ai-rag-internship)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    }
    return nb


COMMON_ROOT = '''from pathlib import Path
import json
import sys


def find_project_root() -> Path:
    """兼容从项目根目录、notebooks 目录或 JupyterLab 启动目录运行。"""
    candidates = [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        if (candidate / "phase1_doc_parser").is_dir() and (candidate / "phase2_semantic_search").is_dir():
            return candidate
    raise RuntimeError("找不到项目根目录，请从 ai-search-rag-internship 启动 JupyterLab")


ROOT = find_project_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
print("项目根目录:", ROOT)
'''


def build_phase1() -> nbf.NotebookNode:
    cells = [
        md("""
# Phase 1：文档解析与中文分块

## 今天交付什么？

今天不是学习“什么是 RAG”然后结束，而是把真实文件加工成后续检索可以直接使用的 `data/processed/chunks.json`。这一步是整个项目的地基：如果来源、页码和文本边界丢失，后面的检索即使命中了，也无法向用户证明“答案来自哪里”。

**完成后你要能回答：**

1. 为什么不能把整本 PDF 直接塞给检索器？
2. 为什么 Chunk 需要 `id/source/page/text`，而不是只保存一段字符串？
3. `chunk_size` 和 `overlap` 改变时，信息完整性、索引成本和重复召回如何变化？

**最终产物：** 一份稳定、可追溯、可重复生成的 Chunk 数据集。今天的每个实验都必须服务于这个产物。
"""),
        md("""
## 0. 前置知识：只补今天会用到的

你不需要先学完机器学习。够用的知识是：

| 知识 | 今天怎么用 | 验收方式 |
| --- | --- | --- |
| `Path` 和文件编码 | 批量找到 `.md/.txt/.pdf` 并读取 UTF-8 | 能指出输入目录和输出文件 |
| 列表、字典、函数 | 表示文档和 Chunk | 能读取一条 Chunk 的字段 |
| 字符串长度和切片 | 限制 Chunk 大小、保留重叠上下文 | 能解释 `text[a:b]` |
| 元数据 | 保留 source/page/headings | 能从检索结果回到原文件 |

**学习原则：** 看到一个知识点后马上在项目数据上做一个小实验；如果它没有改变代码、数据或判断，就先不扩展。
"""),
        code(COMMON_ROOT),
        md("""
## 1. 先看全链路：为什么要分块？

一个 RAG 系统通常经历：

```text
原始文件 -> 解析成文本和元数据 -> 分块 -> 建索引 -> 查询 -> 返回引用
```

分块解决的是一个具体矛盾：

- Chunk 太大：一次召回带来很多无关内容，排序不精确，也更占上下文窗口。
- Chunk 太小：关键词或事实可能被切到两个 Chunk 中，单个 Chunk 失去完整语义。
- 有 overlap：相邻 Chunk 共享边界文字，能降低“事实刚好被切开”的概率；代价是 Chunk 数、索引体积和重复结果增加。

先不要背结论。下面从项目输入开始观察。
"""),
        code("""from phase1_doc_parser.parser import parse_file

input_dir = ROOT / "phase1_doc_parser" / "examples" / "input"
files = sorted(path for path in input_dir.iterdir() if path.is_file())
print("输入目录:", input_dir)
print("文件:", [path.name for path in files])

for path in files:
    documents = parse_file(path)
    print(f"\\n{path.name}: 解析为 {len(documents)} 个文档片段")
    for document in documents:
        print({"source": document.source, "page": document.page, "chars": len(document.text), "metadata": document.metadata})
"""),
        md("""
### 你刚才观察到的是什么？

`parse_file` 没有急着把所有东西变成 Chunk。它先统一输出 `ParsedDocument`：

- Markdown/TXT 通常是一份文档，`page=None`。
- PDF 按页输出，`page=1,2,...`，这样一个 Chunk 才能精确引用页码。
- Markdown heading 被放入 metadata，而不是混进一个无法查询的隐藏状态。

这叫**数据契约**：后续模块只依赖稳定字段，不需要知道文件是怎么解析的。换句话说，Phase 2 不应该重新猜“这段文字来自哪个文件”。
"""),
        code("""document = parse_file(files[0])[0]
print("文本前 240 个字符:\\n", document.text[:240])
print("\\n字段含义:")
print("text = 可检索正文")
print("source = 用户需要回看的原始文件")
print("page = PDF 页码；Markdown 没有页码时为 None")
print("metadata = 不参与正文检索但有助于解释的附加信息")
"""),
        md("""
## 2. Recursive Splitter：它到底在递归什么？

本项目的分隔符顺序是：

```text
段落(\\n\\n) -> 换行(\\n) -> 中文句号/问号/分号 -> 逗号 -> 空格 -> 单字符
```

“递归”不是神秘算法：先尝试用最能保留语义的边界切；如果某一段仍然超过上限，就降级到更细的边界；最后实在没有边界，才按字符切。这样做的原因是**优先保留自然语言结构，同时保证硬性长度上限**。

长度上限不是为了让数字好看，而是为了控制一次检索返回的上下文大小。当前实现用 Python 的 `len` 统计字符数，适合教学和中文 baseline；生产系统还应记录 tokenizer token 数，因为模型上下文窗口按 token 计费和限制。
"""),
        code("""from phase1_doc_parser.splitter import RecursiveSplitter

sample = "第一段：检索需要来源。\\n\\n第二段：overlap 保留跨边界上下文。\\n第三段：如果段落过长，再按标点继续切。"
splitter = RecursiveSplitter(chunk_size=36, overlap=8)
chunks = splitter.split(sample)
for index, chunk in enumerate(chunks):
    print(f"Chunk {index} ({len(chunk)} chars): {chunk!r}")
"""),
        md("""
### 用一个反例理解 overlap

假设关键事实是：`答案在句子末尾，证据在下一段开头`。如果恰好在边界切开，检索其中一半时，用户看到的文本可能无法独立解释问题。overlap 会把前一个 Chunk 的尾部复制到下一个 Chunk 的头部，增加两边同时含有线索的机会。

但 overlap 不是越大越好：如果 `overlap=chunk_size-1`，相邻 Chunk 几乎重复，索引变大，top-k 可能被同一段内容占满，反而降低结果多样性。下面只改变 overlap，其他变量保持不变。
"""),
        code("""def summarize_split(chunk_size: int, overlap: int) -> dict[str, float | int]:
    result = RecursiveSplitter(chunk_size=chunk_size, overlap=overlap).split(document.text)
    lengths = [len(item) for item in result]
    return {
        "chunk_size": chunk_size,
        "overlap": overlap,
        "count": len(result),
        "avg_chars": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "max_chars": max(lengths, default=0),
    }

for overlap in (0, 16, 32):
    print(summarize_split(64, overlap))
"""),
        md("""
**如何读这个实验：**

- `count` 增大说明重复上下文带来了更多索引项。
- `max_chars` 不应超过 `chunk_size`，这是硬约束。
- `avg_chars` 只能描述数据形状，不能证明检索质量变好；质量要在 Phase 2 用 qrels 验证。

这一区分很重要：**分块统计是原因线索，Recall/MRR 才是检索证据。**
"""),
        code("""from phase1_doc_parser.main import build_chunks

splitter = RecursiveSplitter(chunk_size=128, overlap=32)
project_chunks = build_chunks(input_dir, splitter)
print("生成 Chunk 数:", len(project_chunks))
print(json.dumps(project_chunks[0], ensure_ascii=False, indent=2))

required = {"id", "text", "source", "page", "chunk_index", "metadata"}
assert project_chunks and required <= project_chunks[0].keys()
assert all(item["text"] and len(item["text"]) <= 128 for item in project_chunks)
assert all(item["id"] and item["source"] for item in project_chunks)
print("数据契约检查通过：正文、来源、ID 和长度约束都满足。")
"""),
        md("""
## 3. 可重复性：为什么 ID 不能每次随机？

评估时我们要知道“这次排名变了，是算法变了，还是文档 ID 变了”。因此项目使用由 `source/page/index/text` 计算出来的稳定哈希作为 Chunk ID：同一输入和同一参数会得到同一 ID；正文或边界改变时，ID 会变化，提醒我们索引需要更新。
"""),
        code("""run_a = build_chunks(input_dir, RecursiveSplitter(chunk_size=128, overlap=32))
run_b = build_chunks(input_dir, RecursiveSplitter(chunk_size=128, overlap=32))
assert [item["id"] for item in run_a] == [item["id"] for item in run_b]
print("两次运行 ID 完全一致，共", len(run_a), "个 Chunk")

output_path = ROOT / "data" / "processed" / "chunks.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(run_a, ensure_ascii=False, indent=2), encoding="utf-8")
print("已写入:", output_path)
"""),
        md("""
## 4. 故意制造错误：理解边界比记住 API 更重要

好的工程学习不只验证正常输入，也要观察系统如何拒绝危险参数。`overlap` 必须小于 `chunk_size`，否则“保留上下文”会覆盖整个 Chunk，算法无法前进；不支持的文件格式也必须尽早报错，而不是静默生成空数据。
"""),
        code("""try:
    RecursiveSplitter(chunk_size=10, overlap=10)
except ValueError as exc:
    print("非法参数被拒绝:", exc)

try:
    parse_file(input_dir / "not-supported.csv")
except (ValueError, FileNotFoundError) as exc:
    print("不支持的输入会显式失败:", exc)
"""),
        md("""
## Phase 1 阶段闸门

完成下面清单后才进入 Phase 2：

- [ ] 能解释解析、分块、索引三者的边界。
- [ ] 能从任意 Chunk 找到 `source/page`，并说明为什么保存它们。
- [ ] 至少比较 3 组 `chunk_size/overlap`，但不把 Chunk 数当作质量指标。
- [ ] 输出 `data/processed/chunks.json`，且重复运行 ID 稳定。
- [ ] 能解释 overlap 的收益、索引成本和重复召回风险。

**项目交付物：** `chunks.json` + 一段分块策略结论。下一阶段只读取这份真实产物，建立 BM25 baseline。
"""),
    ]
    return notebook(cells)


def build_phase2() -> nbf.NotebookNode:
    cells = [
        md("""
# Phase 2：从 BM25 到 Hybrid 检索

## 今天交付什么？

读取 Phase 1 的真实 `chunks.json`，建立一个能解释、能评估的 BM25 检索 baseline；然后用小型数学实验理解 Dense 检索和 RRF 融合为什么可能有价值。今天不把“用了大模型”当作成绩，成绩是：**同一批 Query、同一份 qrels、不同检索策略的可复现实验证据。**

**完成后你要能回答：**

1. BM25 为什么擅长型号、编号和精确词匹配？
2. Dense 检索为什么可能找回词面不同但语义相近的文本？
3. 为什么不能直接把 BM25 分数和 cosine 分数相加？RRF 解决了什么问题？
4. Recall@k 和 MRR@k 分别在衡量什么？
"""),
        md("""
## 0. 前置知识与学习顺序

| 知识 | 够用理解 | 立即实验 |
| --- | --- | --- |
| 排序和集合 | 能看 top-k ID，求交集 | 手算 Recall |
| BM25 直觉 | 词频、稀有度、文档长度 | 改 Query 看排名 |
| 向量和 cosine | 方向相似，不只看长度 | 2D 向量手算 |
| RRF | 只使用名次，不比较异构分数 | 看融合贡献 |

先做最小可解释实验，再调用项目模块。这样你知道模块输出为什么长这样，而不是只记住一个 import。
"""),
        code(COMMON_ROOT + '''\nfrom phase1_doc_parser.main import build_chunks\nfrom phase1_doc_parser.splitter import RecursiveSplitter\nfrom phase2_semantic_search.bm25 import BM25Retriever, tokenize\nfrom phase2_semantic_search.fusion import reciprocal_rank_fusion\nfrom phase2_semantic_search.metrics import evaluate_qrels, recall_at_k, mrr_at_k\n\nchunks_path = ROOT / "data" / "processed" / "chunks.json"\nif not chunks_path.exists():\n    chunks = build_chunks(ROOT / "phase1_doc_parser" / "examples" / "input", RecursiveSplitter(128, 32))\n    chunks_path.parent.mkdir(parents=True, exist_ok=True)\n    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")\nelse:\n    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))\nprint("读取", len(chunks), "个真实 Chunk")\n'''),
        md("""
## 1. 先观察 tokenizer：中文为什么不能照搬英文？

BM25 的输入不是原句，而是一串 token。英文通常按空格或词切分；中文没有天然空格，本项目 baseline 使用“英文单词/数字 + 单个中文字符”的确定性 tokenizer。它的优点是无需外部分词器、不会因为词典版本变化而改变结果；缺点是“检索”可能被拆成多个字符，短语边界和专业词完整性较弱。

这不是哪种 tokenizer 永远正确的问题，而是要用你的 qrels 做选择。
"""),
        code("""examples = ["BM25 对产品型号更稳", "Dense retrieval 理解语义相近表达", "RRF@10"]
for text in examples:
    print(text, "->", tokenize(text))
"""),
        md("""
## 2. BM25 原理：把公式翻译成人话

对查询中的每个词，BM25 大致做三件事：

1. **匹配奖励**：这个词在文档出现，分数增加；出现多次会增加，但不会无限增加（`k1` 控制饱和）。
2. **稀有词加权**：只在少数文档出现的词更能区分文档（IDF）。所有文档都有的词贡献较低。
3. **长度归一化**：长文档天然更容易包含词，所以要按平均长度修正（`b` 控制修正程度）。

因此 BM25 的强项很直观：产品型号、错误码、法规编号这种“必须精确出现”的词，通常不应该被语义模型的近义联想替代。
"""),
        code("""import math

def idf(document_count: int, document_frequency: int) -> float:
    return math.log(1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))

for df in (1, 2, 10):
    print(f"N=10, df={df}, IDF={idf(10, df):.3f}")
print("观察：df 越小，词越稀有，区分能力越强。")
"""),
        code("""retriever = BM25Retriever(chunks)
queries = {
    "q-001": "Chunk overlap",
    "q-002": "Dense BM25",
}

runs = {}
for query_id, query in queries.items():
    results = retriever.search(query, top_k=5)
    runs[query_id] = [item.doc_id for item in results]
    print(f"\\n{query_id}: {query}")
    for rank, item in enumerate(results, start=1):
        print(rank, item.doc_id, round(item.score, 4), item.metadata.get("source"))
"""),
        md("""
### 如何解释一次 BM25 排名？

不要只说“第一个分数最高”。请按这个顺序解释：

1. 查询被切成了哪些 token？
2. 结果文档命中了哪些 token？
3. 命中的 token 是常见词还是稀有词？
4. 文档长度是否让它受到归一化影响？

这套解释方式比背“BM25 是一种稀疏检索算法”更有用，因为当结果错了，你知道下一步应该检查 tokenizer、数据还是参数。
"""),
        md("""
## 3. Dense 检索：先用二维向量理解，不急着下载模型

Dense 检索把文本映射成向量。相似度常用 cosine：

```text
cos(a,b) = a·b / (||a|| ||b||)
```

它关注向量方向，所以“长度不同但方向相近”的文本仍可能相似。下面用人为定义的二维向量模拟：`猫` 和 `小猫` 方向接近，`汽车型号` 与它们方向不同。这个实验不是模型效果，而是帮助你理解排序机制。
"""),
        code("""import numpy as np

vectors = {
    "doc-cat": np.array([0.95, 0.20]),
    "doc-kitten": np.array([0.80, 0.35]),
    "doc-car-model": np.array([0.10, 0.99]),
}
query_vector = np.array([1.0, 0.0])

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

dense_scores = {doc_id: cosine(query_vector, vector) for doc_id, vector in vectors.items()}
print(sorted(dense_scores.items(), key=lambda item: item[1], reverse=True))
print("cosine 只比较方向；真实模型负责学习文本到向量的映射。")
"""),
        md("""
## 4. 为什么要 Hybrid？

BM25 和 Dense 的错误模式不同：

- BM25 可能漏掉“词面不同但意思接近”的表达。
- Dense 可能把语义相近但型号不一样的文档放得太前。

如果两路结果互补，Hybrid 可以先分别召回，再融合排名。这里使用 RRF（Reciprocal Rank Fusion）：

```text
RRF(d) = Σ 1 / (rrf_k + rank(d))
```

它只看名次，不要求 BM25 分数和 cosine 分数处在同一量纲，因此不需要先做不可靠的“分数相加”。
"""),
        code("""toy_rankings = {
    "bm25": ["exact-model", "semantic-doc", "unrelated"],
    "dense": ["semantic-doc", "exact-model", "another"],
}
fused = reciprocal_rank_fusion(toy_rankings, rrf_k=60)
for item in fused:
    print(item)

print("\\n同一个文档出现在两路排名中，会得到两份 rank contribution；这就是互补信号的来源。")
"""),
        md("""
## 5. 用 qrels 评估：相关性必须先被定义

`qrels` 是“Query -> 相关文档 ID”的人工或规则标注。它把“我觉得这个结果不错”变成可计算的证据。

- **Recall@k**：相关文档中有多少进入前 k 名？适合衡量“有没有找全”。
- **MRR@k**：第一个相关结果排第几？`1/rank`，适合衡量“用户第一眼能不能看到”。

当前样例很小，因此 qrels 只作为教学演示。真实项目要扩大 Query、记录标注依据，并单独标记不可回答问题。
"""),
        code("""first_chunk = chunks[0]["id"]
second_chunk = chunks[1]["id"] if len(chunks) > 1 else first_chunk
qrels = {"q-001": {first_chunk}, "q-002": {second_chunk}}
metrics = evaluate_qrels(runs, qrels, k=5)
print("qrels:", qrels)
print("BM25 metrics:", metrics)
print("手算 q-001:", "Recall=", recall_at_k(runs["q-001"], qrels["q-001"], k=5), "MRR=", mrr_at_k(runs["q-001"], qrels["q-001"], k=5))
"""),
        md("""
### 一个重要的诚实边界

本 Notebook 当前能真实运行的是 BM25 baseline 和 RRF 接口；二维 Dense 是机制实验，不是 BGE-M3 的效果报告。只有在安装 `requirements/phase2.txt`、下载固定模型、记录 revision 和设备后，才能把真实 Dense 结果写进对比表。

先检查能力是否存在，不因为环境没有模型就偷偷用别的结果冒充：
"""),
        code("""import importlib.util

optional = {
    "numpy": importlib.util.find_spec("numpy") is not None,
    "faiss": importlib.util.find_spec("faiss") is not None,
    "FlagEmbedding": importlib.util.find_spec("FlagEmbedding") is not None,
}
print(optional)
if not optional["FlagEmbedding"]:
    print("当前环境未安装 BGE-M3；保留可运行 baseline，真实 Dense 放到独立实验。")
"""),
        md("""
## 6. 小实验：k 改变了什么？

`top_k` 不是越大越好：增大 k 可能提高 Recall，但会增加返回数据、上下文噪声和后续生成成本。下面记录同一批 Query 的结果形状；Phase 3 再把它和延迟放在一起看。
"""),
        code("""for k in (1, 2, 5):
    per_query = {}
    for query_id, query in queries.items():
        ids = [item.doc_id for item in retriever.search(query, top_k=k)]
        per_query[query_id] = {"ids": ids, "recall": recall_at_k(ids, qrels[query_id], k=k)}
    print("k=", k, per_query)
"""),
        md("""
## Phase 2 阶段闸门

- [ ] 能用自己的话解释 BM25 的匹配、稀有度和长度归一化。
- [ ] 能用二维向量解释 cosine，而不是把 Dense 当作黑盒魔法。
- [ ] 能说明 RRF 为什么融合排名而不是直接融合分数。
- [ ] BM25 结果来自 Phase 1 真实 Chunk，并由 qrels 计算 Recall/MRR。
- [ ] 能明确区分“真实模型结果”和“教学模拟结果”。

**项目交付物：** BM25 baseline、qrels、指标表、一次失败结果的原因分析。下一阶段不追求更复杂模型，而是先证明当前系统的质量和速度到底是多少。
"""),
    ]
    return notebook(cells)


def build_phase3() -> nbf.NotebookNode:
    cells = [
        md("""
# Phase 3：Benchmark 与质量评估

## 今天交付什么？

把“系统很快”“效果不错”改写成可复现的工程结论：在固定数据、固定硬件、固定参数下，查询延迟是多少，top-k 质量是多少，改变一个变量后发生了什么。

**完成后你要能回答：**

1. 为什么第一次查询的时间不能直接当平均延迟？
2. 为什么 P95 比平均值更能暴露长尾？
3. 为什么只报告速度提升是不完整的？
4. 如何区分“没有召回证据”和“召回了但回答不忠实”？
"""),
        md("""
## 0. 前置知识：Benchmark 是一个公平比较问题

一次可信实验至少要固定：

```text
数据版本 + 模型/索引版本 + 硬件 + 线程数 + 输入长度 + warmup + 迭代次数
```

如果 A 使用短文本、B 使用长文本，或者 A 的第一次加载时间包含在测量里，最后的数字就不能归因于“算法更快”。本 Notebook 先测项目当前真实 BM25 服务，再把优化接口留成可替换边界。
"""),
        code(COMMON_ROOT + '''\nfrom statistics import mean, median\nfrom time import perf_counter\nimport platform\nimport sys\n\nfrom phase4_mini_rag_system.knowledge_base import KnowledgeBase\nfrom phase2_semantic_search.metrics import recall_at_k, mrr_at_k\n\nknowledge_base = KnowledgeBase()\nknowledge_base.ingest(ROOT / "phase1_doc_parser" / "examples" / "input", chunk_size=128, overlap=32)\nprint("chunks:", len(knowledge_base.chunks))\nprint("index_version:", knowledge_base.index_version)\n'''),
        md("""
## 1. 先理解 warmup：第一次慢不一定是算法慢

第一次调用可能包含 Python 函数首次执行、缓存建立、内存分配或操作系统文件缓存。线上用户可能确实会遇到冷启动，但它和稳定态查询是两个问题，应该分别报告。
"""),
        code("""def timed_search(query: str, top_k: int = 5) -> float:
    start = perf_counter()
    knowledge_base.search(query, top_k=top_k)
    return (perf_counter() - start) * 1000

first = timed_search("Chunk overlap")
steady = [timed_search("Chunk overlap") for _ in range(20)]
print("first_ms:", round(first, 4))
print("steady_mean_ms:", round(mean(steady), 4))
print("steady_samples_ms:", [round(value, 4) for value in steady[:5]], "...")
"""),
        md("""
## 2. P50/P95：为什么不能只看平均值？

把延迟从小到大排序后：

- P50 是中位数，代表一个“典型请求”。
- P95 是 95% 请求不超过的延迟，能看到少数慢请求对体验的影响。
- 平均值会被极端值拉高或拉低，单独使用容易掩盖长尾。

下面使用 nearest-rank 的简单实现。生产报告要写清楚 percentile 定义，避免不同工具的插值规则造成误解。
"""),
        code("""def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(p * len(ordered))) - 1))
    return ordered[index]

def benchmark_search(query: str, *, top_k: int = 5, warmup: int = 5, iterations: int = 50) -> dict[str, float | int]:
    for _ in range(warmup):
        knowledge_base.search(query, top_k=top_k)
    samples = [timed_search(query, top_k) for _ in range(iterations)]
    return {
        "query": query,
        "top_k": top_k,
        "iterations": iterations,
        "mean_ms": round(mean(samples), 4),
        "p50_ms": round(percentile(samples, 0.50), 4),
        "p95_ms": round(percentile(samples, 0.95), 4),
    }

benchmark = benchmark_search("Chunk overlap")
print(benchmark)
"""),
        md("""
**读数纪律：** 当前语料只有几个 Chunk，所以这个延迟不能代表生产规模。它的价值在于建立 harness：以后替换 Dense、Faiss、ONNX 或更大数据集时，仍然用同一套测量方法，比较才公平。
"""),
        code("""benchmarks = [
    benchmark_search("Chunk overlap", top_k=k)
    for k in (1, 2, 5)
]
for row in benchmarks:
    print(row)
print("观察：top_k 同时影响返回结果量和潜在质量；结论需要和 qrels 一起看。")
"""),
        md("""
## 3. 质量闸门：快但错，仍然是失败

把 Phase 2 的 qrels 带过来。对于每个配置同时记录：

- `Recall@k`：有没有把相关 Chunk 召回？
- `MRR@k`：第一个相关 Chunk 排名是否靠前？
- `P95 latency`：长尾请求有多慢？

这三个数字共同描述“用户能否及时看到正确证据”。
"""),
        code("""chunks = knowledge_base.chunks
def first_id_containing(text: str) -> str:
    for item in chunks:
        if text.lower() in str(item["text"]).lower():
            return str(item["id"])
    return str(chunks[0]["id"])

evaluation_queries = {
    "q-001": {"text": "Chunk overlap", "relevant": {first_id_containing("overlap")}},
    "q-002": {"text": "Dense BM25", "relevant": {first_id_containing("Dense")}},
}

for query_id, case in evaluation_queries.items():
    result_ids = [item["chunk_id"] for item in knowledge_base.search(case["text"], top_k=5)]
    print(query_id, {
        "ranked_ids": result_ids,
        "recall@5": recall_at_k(result_ids, case["relevant"], k=5),
        "mrr@5": mrr_at_k(result_ids, case["relevant"], k=5),
    })
"""),
        md("""
## 4. 单变量实验：Chunk 参数是否会改变系统？

现在只改变 `chunk_size/overlap`，查询、输入文件和评估问题不变。我们同时记录 Chunk 数、Recall 和 P95。这样才能回答“更细的 Chunk 是否值得它带来的索引成本”，而不是凭经验争论 256 还是 512。
"""),
        code("""config_results = []
for chunk_size, overlap in ((64, 16), (128, 32), (256, 64)):
    kb = KnowledgeBase()
    kb.ingest(ROOT / "phase1_doc_parser" / "examples" / "input", chunk_size=chunk_size, overlap=overlap)
    start = perf_counter()
    ids = [item["chunk_id"] for item in kb.search("Chunk overlap", top_k=5)]
    elapsed = (perf_counter() - start) * 1000
    relevant = {str(item["id"]) for item in kb.chunks if "overlap" in str(item["text"]).lower()}
    config_results.append({
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks": len(kb.chunks),
        "one_query_ms": round(elapsed, 4),
        "recall@5": recall_at_k(ids, relevant, k=5),
    })
for row in config_results:
    print(row)
"""),
        md("""
### 如何避免过度解读？

这个实验只有一个查询，不能宣布某个参数“最佳”。它只能告诉你：参数确实同时影响数据规模和结果，需要扩大 qrels 后再做结论。专业报告会写：

> 在当前数据版本和一个示例 Query 上观察到……；该现象尚不足以证明普遍规律，下一步扩充标注集并重复实验。

谨慎不是保守，而是让简历和技术报告里的数字经得起追问。
"""),
        md("""
## 5. 错误归因：评估分数低到底是谁的问题？

把一次失败拆成链路，而不是只给系统打一个总分：

```text
文件解析失败 -> 没有正确 Chunk
正确 Chunk 不在 top-k -> 召回/分块问题
正确 Chunk 在 top-k，但答案缺事实 -> 上下文编排/生成问题
答案包含证据没有支持的内容 -> 忠实性问题
评估器与人工判断冲突 -> 评估集或 judge 问题
```

下面用一条小表把“现象”映射到下一步只改变的变量。
"""),
        code("""failure_cases = [
    {"observed": "相关 Chunk 不在 top-k", "layer": "retrieval", "next_change": "只改 tokenizer 或检索策略"},
    {"observed": "相关 Chunk 在 top-k，回答缺少事实", "layer": "generation/context", "next_change": "只改上下文截断或 prompt"},
    {"observed": "答案添加了证据中没有的数字", "layer": "faithfulness", "next_change": "增加引用约束并做人工复核"},
]
for case in failure_cases:
    print(case)
"""),
        md("""
## 6. ONNX/INT8 为什么先做“准备检查”？

量化不是自动加速按钮。它可能带来：模型更小、推理更快，也可能带来输出偏差、Recall 下降或 P95 变差。真实实验必须同时保存：

```text
模型/索引版本、文件大小、mean/P50/P95、cosine 相似度、Recall@k、设备和线程数
```

当前 Notebook 不伪造量化结果，只检查可选依赖和记录当前环境。等模型导出完成后，沿用本 Notebook 的 benchmark harness。
"""),
        code("""import importlib.util

print({
    "onnx": importlib.util.find_spec("onnx") is not None,
    "onnxruntime": importlib.util.find_spec("onnxruntime") is not None,
    "psutil": importlib.util.find_spec("psutil") is not None,
})
print("当前 benchmark 环境:")
print({"python": sys.version.split()[0], "platform": platform.platform(), "processor": platform.processor() or "unknown"})
"""),
        md("""
## Phase 3 阶段闸门

- [ ] 解释 warmup、mean、P50、P95 各自回答什么问题。
- [ ] 延迟数据包含输入规模、迭代次数、设备和版本信息。
- [ ] 同一实验同时报告速度和质量，不把一次测量当结论。
- [ ] 能把失败归因到解析、召回、上下文、生成或评估层。
- [ ] 能写出量化实验的质量闸门，而不是只追求更小模型。

**项目交付物：** baseline benchmark 表、参数对照结果、错误归因记录。下一阶段把这条经过验证的链路包装成别人可以调用的服务。
"""),
    ]
    return notebook(cells)


def build_phase4() -> nbf.NotebookNode:
    cells = [
        md("""
# Phase 4：把检索链路做成可用的 Mini RAG 产品

## 今天交付什么？

把前三个阶段组合成一个别人可以启动、查询、查看证据的服务：

```text
文档目录 -> KnowledgeBase -> FastAPI -> /search 与 /chat -> 引用结果
```

本项目选择 **evidence-first**：没有 LLM API Key 时，`/search` 仍然可用，`/chat` 返回带 Chunk ID 的证据模式答案；有明确配置时才允许调用可选 LLM。这不是功能缩水，而是把“证据能否被检索”与“语言模型如何表达”分开，便于开发、测试和追责。

**完成后你要能回答：**

1. API 为什么要有清晰的请求/响应合同？
2. 为什么引用字段是产品核心，而不是调试信息？
3. 为什么模型和索引应该在服务启动时复用，而不是每次请求重建？
4. 没有 LLM Key 时，系统如何安全地降级？
"""),
        md("""
## 0. 前置知识与完成定义

| 知识 | 今天的用法 | 通过标准 |
| --- | --- | --- |
| HTTP 方法/状态码 | GET 健康检查、POST 查询 | 能解释 200 和 422 |
| JSON | 传输 Query、结果和 citations | 能定位结果字段 |
| Pydantic | 限制空 Query 和非法 top_k | 能触发并解释校验错误 |
| TestClient | 不启动外部服务器也测试 API | 能写出契约断言 |
| 环境变量 | 控制可选 LLM，避免密钥入库 | 能说明默认安全行为 |

**Definition of Done：** 新用户只看 README 就能启动；提交一个问题得到结果；结果包含 source/page/chunk_id；没有 API Key 也不会偷偷产生外部调用。
"""),
        code(COMMON_ROOT + '''\nfrom fastapi.testclient import TestClient\nfrom phase4_mini_rag_system.app import create_app\n\napp = create_app(ROOT / "phase1_doc_parser" / "examples" / "input")\nclient = TestClient(app)\nprint("FastAPI app 已创建，测试不会启动独立端口。")\n'''),
        md("""
## 1. `/health`：先确认服务准备好了

健康检查不是装饰页面。它告诉调用方：服务是否能响应、当前索引里有多少 Chunk、索引版本是什么。没有 `index_version` 时，用户很难判断“我刚刚导入的文档是否真的生效”。
"""),
        code("""health = client.get("/health")
print("status:", health.status_code)
print(json.dumps(health.json(), ensure_ascii=False, indent=2))
assert health.status_code == 200
assert health.json()["chunks"] > 0
assert health.json()["index_version"].startswith("chunks-")
"""),
        md("""
## 2. `/search`：先建立证据合同

搜索接口返回的不只是字符串列表。每个结果都要能回答：

- 这段证据的稳定 ID 是什么？
- 来自哪个文件、哪一页？
- 为什么排在这里？（至少保留可比较的 score）
- 当前索引是哪一版？

这是“可解释检索”的最小合同，也是未来生成答案时允许模型使用的证据边界。
"""),
        code("""search_response = client.post("/search", json={"query": "Chunk overlap", "top_k": 5})
payload = search_response.json()
print("status:", search_response.status_code)
print(json.dumps(payload, ensure_ascii=False, indent=2))

assert search_response.status_code == 200
assert payload["results"]
required_citation_fields = {"chunk_id", "text", "source", "page", "score"}
assert required_citation_fields <= payload["results"][0].keys()
"""),
        md("""
### “有引用”不等于“引用支持答案”

系统返回一个 source 只能证明“它来自某处”，不能自动证明它支持回答。更严格的产品验收还要检查：答案中的关键事实是否能在引用 Chunk 中找到。当前 evidence-only 模式直接展示证据，减少生成层把引用和事实脱钩的机会。
"""),
        code("""citation = payload["results"][0]
print({
    "citation_id": citation["chunk_id"],
    "source": citation["source"],
    "page": citation["page"],
    "score": citation["score"],
    "text_preview": citation["text"][:120],
})
"""),
        md("""
## 3. `/chat`：生成不是检索的替代品

`/chat` 的内部顺序是：

1. 用同一个 KnowledgeBase 检索。
2. 将结果作为受限证据传给回答层。
3. 返回答案、模式和 citations。

当前没有显式开启 `RAG_ENABLE_LLM=true` 且没有 `OPENAI_API_KEY`，所以应该得到 `evidence-only`。这让 Notebook 可离线运行，也防止学习时不小心产生 API 费用。
"""),
        code("""chat_response = client.post("/chat", json={"query": "Chunk overlap", "top_k": 3})
chat_payload = chat_response.json()
print("status:", chat_response.status_code)
print("mode:", chat_payload["mode"])
print("answer:\\n", chat_payload["answer"])
print("citations:", len(chat_payload["citations"]))
assert chat_response.status_code == 200
assert chat_payload["mode"] in {"evidence-only", "evidence-only-fallback", "llm"}
assert chat_payload["citations"]
"""),
        md("""
## 4. 错误处理：让调用方知道问题在输入还是系统

用户输入错误和服务器故障不能都返回 500：

- 空 Query：请求不符合 schema，FastAPI 返回 422。
- 不存在的 source：这是合法查询，但结果可以为空。
- 导入不存在目录：返回 400，并给出稳定错误码。

错误合同越清晰，前端和自动化测试越容易正确处理，也越容易定位问题。
"""),
        code("""empty_query = client.post("/search", json={"query": ""})
unknown_source = client.post("/search", json={"query": "overlap", "source": "does-not-exist.md"})
bad_ingest = client.post("/documents/ingest", json={"input_dir": str(ROOT / "missing-input")})

print("empty query:", empty_query.status_code, empty_query.json().get("detail"))
print("unknown source:", unknown_source.status_code, unknown_source.json()["results"])
print("bad ingest:", bad_ingest.status_code, bad_ingest.json())
assert empty_query.status_code == 422
assert unknown_source.status_code == 200 and unknown_source.json()["results"] == []
assert bad_ingest.status_code == 400
"""),
        md("""
## 5. TestClient：把用户故事变成可执行验收

用户故事：

> 作为需要查阅技术资料的实习生，我输入一个问题，希望看到答案和能回到原文的证据；当没有足够证据时，系统应该明确说不知道，而不是编造。

对应测试至少覆盖：健康、检索引用、无 LLM 降级、空输入、无结果和导入错误。Notebook 里的断言是快速学习反馈，`tests/` 里的 pytest 才是提交前的长期保护。
"""),
        code("""def assert_search_contract(query: str) -> dict:
    response = client.post("/search", json={"query": query, "top_k": 3})
    assert response.status_code == 200
    body = response.json()
    assert {"query", "results", "trace_id", "index_version"} <= body.keys()
    return body

contract = assert_search_contract("Dense BM25")
print("契约通过，trace_id:", contract["trace_id"])
print("结果数:", len(contract["results"]))
"""),
        md("""
## 6. 真实产品交付：把演示结果保存为证据

不要只在屏幕上看一眼结果。把一次 Demo 的配置、问题、回答模式、引用和索引版本保存下来，技术报告才能复盘，面试时也能展示系统确实运行过。
"""),
        code("""demo_record = {
    "project": "EvidenceDesk Mini RAG",
    "index_version": chat_payload["index_version"],
    "query": chat_payload["query"],
    "mode": chat_payload["mode"],
    "answer": chat_payload["answer"],
    "citations": [
        {key: item.get(key) for key in ("chunk_id", "source", "page", "score")}
        for item in chat_payload["citations"]
    ],
}
demo_path = ROOT / "data" / "processed" / "phase4_demo_record.json"
demo_path.write_text(json.dumps(demo_record, ensure_ascii=False, indent=2), encoding="utf-8")
print("Demo 记录已保存:", demo_path)
"""),
        md("""
## 最终项目验收

完成后，从项目根目录启动：

```powershell
conda activate 'F:\\anaconda\\miniconda3\\envs\\ai-rag-internship'
python -m phase4_mini_rag_system
```

浏览器打开 `http://127.0.0.1:8000/`，完成至少三种演示：

1. 能回答的问题：显示回答和引用。
2. 同义表达：观察 BM25 baseline 的能力边界，并记录下一步 Dense 实验。
3. 不可回答的问题：系统明确返回“没有足够证据”，不编造。

**最终系统链路：** 解析 → 分块 → 稳定 ID/来源 → BM25 检索 → FastAPI → evidence-only/可选 LLM → citations。

**最终交付清单：** 代码、4 个可运行 Notebook、测试、README、前置知识矩阵、实验记录、PRD/技术报告素材，以及 `phase4_demo_record.json`。
"""),
    ]
    return notebook(cells)


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    notebooks = {
        "phase1_document_parser.ipynb": build_phase1(),
        "phase2_hybrid_retrieval.ipynb": build_phase2(),
        "phase3_benchmark_evaluation.ipynb": build_phase3(),
        "phase4_mini_rag.ipynb": build_phase4(),
    }
    for filename, nb in notebooks.items():
        nbf.write(nb, NOTEBOOK_DIR / filename)
        print("wrote", NOTEBOOK_DIR / filename, "cells=", len(nb.cells))


if __name__ == "__main__":
    main()
