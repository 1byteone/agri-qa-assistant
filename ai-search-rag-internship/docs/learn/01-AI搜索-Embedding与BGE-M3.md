# 01 AI搜索 · Embedding 与 BGE-M3

> 能力域：AI 搜索 ｜ 对应简历："基于BGE-M3模型构建Faiss向量索引"

## 0 企业案例与用户故事

**周主任 vs "找不到的导数教案"**

教研组长周主任在传习智学后台搜索：

> "人教A版必修二导数教案"

结果前三页全是**必修一的函数教案**。他打电话给数据产品同学：

> "我明明写了'导数'，为什么给我'函数'？还有，学生搜'圆锥曲线怎么学提分快'，咱们系统居然一条圆锥曲线的课都推不出来——学生说的是大白话啊。"

产品经理补充了两个观测事实：

1. 关键词匹配只能命中**字面相同**的词。学生说"圆锥曲线"，课标题写"椭圆、双曲线、抛物线"，字面完全不同 → 匹配失败。
2. 老师写"导数"，系统却推"函数"——因为**词面**上"导数"和"函数"同时出现在必修一/必修二的教案文本里，关键词打分无法区分哪个才是用户要的。

```text
业务痛点：用户用自然语言表达意图，系统只按字面匹配，同义/相关表达全部漏召回
技术问题：Embedding 向量与余弦相似度——让"意思相近"的文本在向量空间靠近
业务指标：Recall@10（用户意图能否在 Top-10 里被召回）
```

## 1 原理直觉

### 1.1 从"查字"到"比意"

关键词搜索（BM25）的逻辑是**倒排索引**：查哪些文档包含这些词。它的优势是快、可解释、精确词很强（SKU、错误码、教材编号）；劣势是**不理解意思**——"圆锥曲线"和"椭圆"没有任何共同字符，就被判为无关。

Embedding 的思路完全不同：把每段文本用一个模型编码成**一个高维向量**，让"语义相近的文本"落在向量空间相近的位置。

```text
"圆锥曲线怎么学提分快"  ──BGE-M3──►  [0.021, -0.132, 0.832, ...]  ┐
                                                                   ├─ cosine ≈ 0.91 → 高相似
"椭圆双曲线抛物线解题技巧"  ──BGE-M3──► [0.014, -0.145, 0.807, ...]  ┘
```

然后比较查询向量与文档向量的余弦相似度，取 Top-K。

### 1.2 为什么"意思近"就能算出来

Embedding 模型（如 BERT 系）被训练成：把**上下文意思相同**的句子映射到相近向量。Transformer 对每个 token 生成一个向量，再通过 pooling（如 `[CLS]` 或 mean pooling）压成一个代表整句语义的向量。相似度 = 方向夹角余弦，**与向量长度无关**（这就是为什么要 L2 归一化）。

### 1.3 BGE-M3 是什么：一个模型，三种检索能力

BGE-M3（BAAI）是"多功能、多语言、多粒度"的统一 Embedding 模型，**一次编码同时给出三种输出**：

| 输出 | 维度 | 用途 | 类比 |
| --- | --- | --- | --- |
| `dense_vecs` 稠密向量 | 1024 | 语义召回（ANN 搜索） | 理解的"大意" |
| `lexical_weights` 稀疏权重 | 词表大小（~250k） | 词汇精确匹配（类似 BM25 但可学习） | 记忆的"关键词" |
| `colbert_vecs` 多向量 | token 级 | 精排（ColBERT late-interaction） | 逐字对位的"细看" |

- 多语言：100+ 语言，中英混合检索可用。
- 上下文 8192 token。
- **不需要给 query 加指令**（对比 BGE 第一代需要 instruction）。
- 论文用自知识蒸馏把三种能力联合训练；sparse 检索在所有语言上超过 BM25；多向量在 Dense 之上再提升约 5 分。

## 2 最小实验

### 2.1 先不装模型：numpy 手写余弦相似度（5 分钟建立直觉）

```python
import numpy as np

def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# 假设两个"意思相近"的向量（用玩具数据代替真实 embedding）
q = np.array([1.0, 0.0, 1.0])      # 圆锥曲线怎么学
d1 = np.array([0.9, 0.1, 0.8])     # 椭圆解题技巧（近义）
d2 = np.array([0.0, 1.0, -1.0])    # 完全无关
print(cosine(q, d1), cosine(q, d2))  # 高 / 低
```

预期输出：第一个相似度明显高、第二个接近 0。**归一化后 inner product == cosine**，这正是 Faiss 用 `IndexFlatIP` 的原因。

### 2.2 接入真实 BGE-M3（运行前先装 `requirements/phase2.txt`）

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False, devices="cpu")
out = model.encode(
    ["圆锥曲线怎么学提分快", "椭圆双曲线抛物线解题技巧"],
    return_dense=True, return_sparse=True, return_colbert_vecs=True,
)
dense = out["dense_vecs"]            # shape (2, 1024)
sparse = out["lexical_weights"]      # {token: weight}，类似可学习 BM25
colbert = out["colbert_vecs"]        # token 级向量，供精排
```

- 本仓库封装入口：`phase2_semantic_search/README.md` 里的 `encode_with_bge_m3`（懒加载，缺依赖时报可解释错误）。
- 实验约定：向量统一 `float32` + L2 归一化，余弦用 inner product 表达（`normalize_vectors`）。

### 2.3 记录实验身份（evidence-first 要求）

```text
model: BAAI/bge-m3
revision: 记录 HF 上的具体 commit
device: CPU / GPU
max_length: 8192
normalization: L2
python: 3.12
```

## 3 简历映射

**简历原句**："基于 BGE-M3 模型构建 Faiss 向量索引"

**怎么说圆**（面试 30 秒版）：

> 我们线上先有 BM25 关键词召回，发现学生/老师的自然语言表达命中不了商品文案里的标准词（"圆锥曲线"对不上"椭圆"）。我负责语义召回模块：用 BGE-M3 把 500 条教育资源记录编码成 1024 维稠密向量，L2 归一化后建 Faiss 索引；查询时同一模型编码 query，做 Top-K 相似度检索。同时在离线固定 50 条 qrels 上对比 BM25 / Dense / Hybrid 的 Recall@10，避免只凭主观例子判断效果。

**注意口径**：简历说"构建 Faiss 索引"——Faiss 检索逻辑见 `docs/learn/02`。本册只负责"向量怎么来"。`dense` 向量才能直接进 Faiss；`sparse` 和 `colbert` 用法不同，不要混为一谈（这正是面试官爱追的细节）。

## 4 面试深挖

**Q1：为什么两个文本可以通过向量计算相似度？**
训练时，模型把意思相近的句子推到向量空间相近的位置（对比学习/蒸馏）；相似度用方向夹角余弦衡量。核心是"语义由上下文塑造"，不是字面重合。

**Q2：BGE-M3 为什么适合语义检索？一个模型三种输出怎么理解？**
统一编码器一次给出 dense（大意）、sparse（可学习的关键词权重，超过 BM25）、colbert（token 级精排）。多语言 + 8192 长上下文，中英混合/长文档可用。混合检索时用 dense 召回 + sparse 补词面，多向量精排候选集。

**Q3：向量为什么要归一化？**
余弦相似度只关心方向。归一化成单位向量后，内积 == 余弦，Faiss `IndexFlatIP` 就能直接算，性能更好；不归一化会把向量长度（噪音）混进相似度。

**Q4：稠密、稀疏、多向量输出怎么选？**
只做语义召回 → dense；需要精确词匹配兜底 → sparse（或单独 BM25）；召回后做精排 → colbert/reranker。BGE-M3 的论文里多向量在 dense 之上提升约 5 分，但代价是计算量大，通常只对 Top-200 做精排。

**Q5：Embedding 的 pooling 是什么？为什么 chunk 越长信息越稀释？**
Transformer 为每个 token 生成向量，pooling（[CLS]/mean）压成一个代表整句的向量。压缩必有信息损失——文本越长，单一向量要概括的主题越多，越"稀释"，检索精度下降（这是"为什么不能整篇 PDF 直接 Embedding"的根源，见册 04）。

**Q6：关键词搜索（BM25）和语义搜索（Dense）各自的盲区？**
BM25：精确词强（SKU/教材编号/错误码），但同义/口语/语序变化全部失效；"automobile" 对 "car" 召回为空。Dense：理解同义和意图，但对精确编号、否定词、稀有实体名容易失焦。所以生产系统是混合，不是二选一。

## 5 参考资料

- [BGE-M3 官方文档（三种输出与用法）](https://bge-model.com/bge/bge_m3.html)：`dense_vecs` / `lexical_weights` / `colbert_vecs` 的返回与 `compute_score`
- [BAAI/bge-m3 模型卡（HF）](https://huggingface.co/BAAI/bge-m3)：无需 query 指令、use_fp16、8192 token、100+ 语言
- [BGE-M3 论文](https://arxiv.org/html/2402.03216v3)：`[CLS]` 做 dense、自知识蒸馏、sparse 超过 BM25、多向量 +5.1
- [Milvus BGE M3 集成文档](https://milvus.io/docs/embed-with-bgm-m3.md)：dense 1024 维、sparse ~250002 维
- [Pristren: BGE-M3 Embeddings 2026](https://pristren.com/blog/bge-m3-embeddings-multilingual/)：dense/sparse/multi-vector 对比、alpha=0.5 混合默认值
- [NVIDIA BGE-M3 模型卡](https://build.nvidia.com/baai/bge-m3/modelcard)
- 本仓库：`phase2_semantic_search/README.md`（`encode_with_bge_m3`、`normalize_vectors`）
