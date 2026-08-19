# 江西农业 MCP 兼容工具契约

## 当前边界

CropWise 当前运行的是内嵌的 MCP-compatible tool layer，不宣称已经连接独立的外部 MCP Server。所有工具均通过 Agent 的统一审计包装执行，SSE 和 `done.tool_calls` 会返回：`name`、安全参数、`source`、`ok`、`error_code`、`duration_ms`。

## 工具

| 工具 | 数据/能力 | 真实性边界 |
| --- | --- | --- |
| `query_crop_knowledge` | Chroma 农业知识库混合检索 | 只返回当前知识库证据，不命中时返回 `NO_KNOWLEDGE_MATCH` |
| `get_current_datetime` | Asia/Shanghai 系统时钟或用户评估日期 | 用户日期标记为 `evaluation_datetime`，不代表当前日期 |
| `calculate_growing_period` | 江西城市别名与基础农时规则 | `requires_local_validation=true`，不能替代县域农技意见 |
| `get_agri_weather` | Open-Meteo 公共预报 | 无需 API Key；不是江西官方站点数据，灾害预警以气象部门为准 |
| `search_agri_resources` | Wikimedia、FAO、农业农村部公开入口 | 图片仅供识别参考，不能单独用于确诊 |
| `fetch_web_content` | 公开网页抓取与 6 小时缓存 | 受目标站点可访问性和内容时效影响 |

## 时间预检

当问题包含完整日期、当前/今天、播期、生育期或天气等时间语义时，Agent 在调用模型前先执行 `get_current_datetime`，并把结构化结果注入系统上下文。非法日期不会回退到系统当前日期，而是返回 `INVALID_REFERENCE_DATE`。

## 诊断接口

```text
GET /health
GET /mcp/status
GET /knowledge-base/search?query=江西早稻什么时候播种&limit=3
```

`/mcp/status` 的 `external_process_connected=false` 是有意的诚实标记；后续接入独立 MCP 进程时，需要在此处增加真实连接探活和版本信息后再改为 `true`。

## 验收标准

1. 用户指定日期在回答和工具审计中显示为评估日期，不得称为当前日期。
2. 每个工具完成事件均有 `ok`、来源和耗时；失败必须有稳定错误码。
3. 江西早稻、双季稻等查询能从知识库返回带匹配度和元数据的证据。
4. 外部天气不可用时在 8 秒内返回结构化超时/不可用错误，不阻塞整个对话。
5. 领域守卫仍在工具和模型之前执行，非农业问题不能触发 MCP 工具。
