# AgriIR 对 CropWise 的下一阶段开发计划

日期：2026-08-10  
基线：CropWise 现有 FastAPI + Chroma + LangChain Agent + SSE

## 调研结论与证据

| 来源 | 已核验信息 | 对本项目的含义 |
| --- | --- | --- |
| [arXiv 2604.16353](https://arxiv.org/abs/2604.16353) | AgriIR 将 query refinement、sub-query planning、retrieval、synthesis、evaluation 拆成声明式阶段；强调 1B 模型、可观测性和确定性引用 | 保留现有 Agent，先增加阶段契约和 trace，再把模型改写器做成可插拔 provider |
| [AgriIR README](https://github.com/Shuvam-Banerji-Seal/AgriIR) | 公开实现采用 FAISS + DuckDuckGo 并行检索、领域 agent catalogue、相似度阈值 0.75；提供 `config.yml` 和模型角色配置 | 当前 Chroma 不必立即迁移；把向量/结构化/网页能力统一成检索注册中心 |
| [Ragas 论文](https://arxiv.org/abs/2309.15217) | 将 context precision、context recall、faithfulness、answer relevancy 分开评估 | 评测不能只看答案流畅度，必须保留召回、引用覆盖和忠实度指标 |
| [MCP 官方 servers](https://github.com/modelcontextprotocol/servers) | Fetch 等能力适合标准化工具接入，但数据许可、超时和来源治理仍由应用负责 | P0 继续内嵌 adapter；通过准入清单后再迁移 MCP stdio/HTTP |

## 当前已执行

- 新增 `backend/agriir_pipeline.py`：声明式阶段配置、查询规范化、确定性子查询拆分、跨子查询去重、稳定引用 ID、引用阈值和检索 trace。
- 新增 `backend/agriir_pipeline.json`：查询改写 `T=0.1`、子查询拆分 `T=0.5`、合成 `T=0.2`、引用阈值 `0.75`，后续可无代码修改调整。
- `ChatRequest` 支持结构化 `scenario_context`；Agent 会把场景字段送入检索上下文并发出 `trace`、`sources` SSE 事件。
- `/knowledge-base/search` 返回 refined query、subqueries、results、citations；新增 `/agriir/config` 用于部署自检。
- 专业回答在存在达标证据时追加确定性 `## 参考来源` 区块；低于阈值的结果仍展示为未达标证据，不会冒充权威引用。
- 已冻结产品决策：首批江西县/区级水稻、油菜、赣南脐橙、蔬菜；暂不引入本地模型；天气 P0 使用 Open-Meteo；农药/肥料/政策只接受 A 级官方来源；评测集先由研发搭骨架再交专家标注。
- 已登记 `docs/data-source-registry.md`，并在 pipeline 中加入高风险 `evidence_level=A` 引用闸门。
- 引用阈值按 embedding provider 校准：本地 hashing embedding 暂使用 `0.45`（已覆盖官方材料标题完全匹配的 `0.49` 实测分值），远程 embedding 保持 `0.75`。该本地阈值在专家标注形成后需重新校准；阈值只决定检索置信度，不能绕过高风险 A 级来源要求。
- 新增 `backend/source_registry.py`、`/evidence-sources` 和证据包导入器；A 级材料入库前校验官方 HTTPS 域名、发布日期，并写入稳定 `evidence_id`。
- 已登记并导入 A 级材料：农业农村部法规司《农药管理条例》（2023-12-05），以及农业农村部《当前水稻应对高温热害技术意见》（2026-08-05）、《科学规范合理用药 有效防控油菜病虫害》（2026-03-17）；赣州市农业农村局公开的《脐橙冻害风险预警（2026第一期）》（2026-01-20）已纳入 `gannan-citrus` 包。版本化清单位于 `data/evidence-packs/`。
- 高风险引用同时校验 `evidence_scope`；缺少匹配范围的 A 级材料时，Agent 在模型调用前短路为安全决策卡，不会给出具体处方。
- 已开放专家标注队列：`GET /evaluations/items`、`POST /evaluations/items/{id}/annotation`。只有 `expert_approved` 的真实证据 ID 进入质量指标。
- 已生成 `data/evals/agriir_eval_skeleton.jsonl` 的 120 条固定 P0 测试骨架，并新增 `/evaluations/retrieval`。专家金标为空时接口只报告候选检索率，`recall_at_k` 保持为空；专家补齐 `gold_evidence_ids`、`citation_covered`、`faithful`、`safety_ok` 后，接口自动计算 Recall@K、引用覆盖率、忠实度和安全覆盖率。

## 分阶段开发计划

### P0（本周）：契约与可测基线

交付 `scenario_context` schema、检索 trace、来源字段注册表、120 条评测集骨架和 CI 中的 pipeline 单测。验收：阶段配置可被 JSON 修改；一次请求可还原 query → subqueries → results → citations；引用 ID 在重复运行中稳定。

### P1（第 2-3 周）：多源能力注册中心

建立 `Retriever` 协议和 registry，内置 Chroma、结构化 SQLite、官方网页 adapter；每个 adapter 返回统一 `ToolResult/evidence`，包含 publisher、retrieved_at、valid_at、license、error_code 和可重试标志。验收：任一来源超时不阻断回答；降级路径在 SSE 中可解释；官方来源优先级高于通用网页。

### P1（第 3-4 周）：远程模型与阶段 provider

将 query refinement、decomposition、synthesis 绑定到模型 registry，本阶段只支持远程 Agnes；暂不引入本地 Ollama/1B 模型。温度、最大 token、超时全部由配置控制。验收：切换远程模型不修改业务代码；阶段耗时和错误率进入 trace。

### P1（第 4-5 周）：确定性引用与安全闸门

增加回答句子到证据片段的覆盖评估、冲突来源标记、农药/肥料/动物健康高风险规则。验收：关键判断引用覆盖率 >=85%；安全提醒覆盖率 100%；低置信度时自动降级为“待核验/建议农技人员复核”。

### P2（第 6-8 周）：病例复查闭环

落地 `cases`、`case_events`、review、escalate API 和前端时间线。验收：诊断问题可保存现场摘要、行动、复查时间；复查后生成差异记录；转交前显示将共享字段。

### P2（第 9-12 周）：江西数据包和试点

版本化 `jiangxi-rice`、`jiangxi-rapeseed`、`gannan-citrus`、`jiangxi-policy` 知识包，接入县域农时/天气和官方政策检索。验收：120 条离线集通过门槛，10-20 名真实用户完成试用，形成失败案例回灌清单。

## 交付标准（发布门槛）

1. 农业领域越界率 <1%，高风险安全提醒覆盖率 100%。
2. Top-5 证据相关性 >=80%，关键判断引用覆盖率 >=85%。
3. 五段式决策卡完整率 >=95%，缺失现场字段只显示“待补充”。
4. SSE `done`/可解释 `error` 完整率 >=99%，来源卡可打开且包含来源机构和时间。
5. 配置、知识包和数据源均有版本、许可证、回滚方式；无 CI 构建或类型错误。

## 已确认的产品决策

1. 首个试点锁定“江西县/区级 + 水稻、油菜、赣南脐橙、蔬菜”。
2. 暂不引入本地模型，继续使用现有远程 Agnes 模型。
3. 实时天气 P0 使用 Open-Meteo 公开接口，并明确其为 B 级参考数据。
4. 农药、肥料、政策、补贴、标准、规范和登记只允许 A 级官方来源支撑具体结论。
5. 评测集由研发先维护 120 条骨架，再交农技专家标注和复核。
