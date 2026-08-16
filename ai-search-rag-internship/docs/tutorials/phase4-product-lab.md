# Phase 4 实验课：把检索系统做成可用产品

## 课程结果

最终用户可以导入文档目录、发起检索和提问；系统返回回答、来源、页码、Chunk ID、分数和 `trace_id`。无 LLM key 时，检索接口仍可用，方便开发和验收。

## 六天安排

| 天 | 学习与编码 | 交付 |
| --- | --- | --- |
| Day 1 | 定义 Pydantic schema、`/health` 和错误模型 | API contract |
| Day 2 | 接入文档导入与索引状态 | `/documents/ingest` |
| Day 3 | 接入 Phase 2 检索并返回引用 | `/search` + contract test |
| Day 4 | 增加 chat 编排、无 LLM fallback 和 trace_id | `/chat` |
| Day 5 | 完成 TestClient、超时、空结果和敏感配置检查 | test suite |
| Day 6 | 写 PRD、A/B 方案、竞品分析和技术报告 | product package |

## 1. 先写 API 合同

```text
GET  /health
POST /documents/ingest
POST /search
POST /chat
```

`POST /search` 请求：

```json
{"query":"如何配置索引？","top_k":5,"filters":{"source":"manual.md"}}
```

响应至少包含：

```json
{
  "query":"...",
  "results":[{"chunk_id":"...","text":"...","source":"...","page":3,"score":0.81}],
  "trace_id":"...",
  "index_version":"v1"
}
```

## 2. 服务分层练习

```text
api/             只负责 HTTP schema、状态码和错误
services/        编排 ingest/search/chat
retrieval/       BM25、Dense、Hybrid 实现
evaluation/      离线评估，不被 API 请求隐式触发
config/           环境变量和模型配置
```

路由函数不能在每次请求里加载模型或重建索引。使用 lifespan 或依赖注入初始化资源，并在 health 中报告 index version 和模型状态。

## 3. 可靠性任务

- 空 query 返回 422。
- 不存在的 source filter 返回空结果而不是 500。
- LLM 超时返回明确错误码，保留 `trace_id`。
- 检索成功但没有答案时返回“无足够证据”，不能让模型自由编造。
- 输入文档过大时返回可理解的限制信息。
- API key 只能从环境变量读取，不能写进仓库。

## 4. 测试驱动实现

至少写这些 TestClient 用例：

```text
test_health_ready
test_ingest_markdown
test_search_returns_citations
test_search_empty_query_is_422
test_chat_without_llm_uses_retrieval_only_or_returns_known_error
test_source_filter
```

测试数据使用固定的两个 Markdown 文件和一个不可回答 Query，避免测试依赖网络或在线模型。

## 5. PRD 写作课

用 `docs/templates/PRD.md`，只写能被当前系统验证的内容：

1. 用户：需要从内部技术资料快速找到依据的实习生/工程师。
2. 痛点：文档多、关键词不稳定、回答缺引用。
3. P0：导入、检索、引用问答、健康检查。
4. P1：过滤、历史记录、评估面板。
5. 不做：权限、多租户、生产级分布式索引。
6. 成功指标：有引用回答率、Recall@10、P95 latency、无答案率。

## 6. A/B 测试课

默认实验：A=BM25，B=Hybrid。主指标只选一个，例如 `grounded_answer_rate`；护栏指标包含 P95 latency、单次成本和无答案率。

实验记录必须包含：假设、流量分配、样本单位、开始/停止条件、最小可检测差异、统计方法和失败处理。离线 50 条 Query 只能做方向判断，不能冒充线上显著性结论。

## 7. 课程验收题

- 为什么 `/search` 必须脱离 LLM 独立可用？
- 如何避免每次请求重复加载 embedding 模型？
- “有引用”与“引用支持答案”有什么区别？
- A/B 测试中为什么要把 latency 和成本作为护栏指标？

## 交付清单

```text
phase4_mini_rag_system/app/main.py
phase4_mini_rag_system/app/schemas.py
phase4_mini_rag_system/app/services.py
phase4_mini_rag_system/tests/test_api.py
docs/PRD.md
docs/AB_test_plan.md
docs/competitive_analysis.md
docs/tech_report.md
```
