# Phase 1 分块策略选型报告

## 实验目的

比较不同 `chunk_size` 与 `overlap` 对 Chunk 数量、平均长度、重复比例和后续召回的影响。

## 当前实现

- 入口：`phase1_doc_parser/parser.py`
- 分块：`phase1_doc_parser/splitter.py`
- 批处理：`phase1_doc_parser/main.py`
- 当前基线：`chunk_size=512`、`overlap=128`
- 分隔符优先级：段落、换行、中文句末标点、分号、逗号、空格、字符级兜底

## 为什么从 512/128 开始

512 是一个便于实验的字符级上限，能让中文段落保留相对完整的语义单元；128 约为四分之一的重叠，能够缓解答案跨 Chunk 边界时的上下文断裂。它们只是基线，不是普适最优值。overlap 过大会增加索引体积、重复召回和生成上下文成本。

## 需要补齐的实验表

| chunk_size | overlap | chunks | avg_chars | duplicate_ratio | Recall@10 | notes |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 256 | 64 | TODO | TODO | TODO | TODO | |
| 512 | 128 | TODO | TODO | TODO | TODO | baseline |
| 768 | 192 | TODO | TODO | TODO | TODO | |

## 结论规则

只有在固定语料、Query 标注集和检索参数下，才能把某个组合写成推荐策略。下一步是在 Phase 2 用 Recall@10 和 P95 latency 验证本报告的假设。

