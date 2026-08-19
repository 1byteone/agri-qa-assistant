# CropWise BRAG 农业 RAG 开发计划

版本：0.2  
日期：2026-08-10  
适用项目：`agri-qa-assistant` 现有 FastAPI + Chroma + LangGraph Agent + Next.js

## 1. 专业 Goal

### 产品 Goal

在 8 周内把 CropWise 从“农业问答原型”收敛为一个面向江西县域种植者和农技人员的**水稻病虫害与高温胁迫证据优先决策助手**：用户提交作物、地区、生育期、症状/天气和已采取措施后，系统输出可执行的五段式决策卡、可点击的官方依据、风险边界和复查节点；无法由证据支持时，明确降级为待核验或人工转交。

### 工程 Goal

建立可回放、可评测、可降级的 RAG 流水线：

```text
结构化场景输入
  -> 逻辑路由与元数据过滤
  -> 查询改写/按需分解
  -> 向量 + 关键词 + 时间/来源检索
  -> RRF 融合与候选重排
  -> 父文档上下文恢复与压缩
  -> 证据等级/适用范围闸门
  -> 带引用决策卡 + SSE trace + 复查事件
```

### 8 周可验收结果

| 指标 | 目标 | 说明 |
| --- | ---: | --- |
| Top-5 专家相关证据召回 | >= 85% | 仅统计已完成专家金标的样本 |
| 关键判断引用覆盖率 | >= 90% | 每个结论可回到稳定 `evidence_id` |
| 高风险安全提醒覆盖率 | 100% | 农药、剂量、间隔期、灾害处置等 |
| 无依据具体处方率 | 0% | 没有 A 级且 scope 匹配的证据不得输出 |
| 五段式决策卡完整率 | >= 95% | 摘要、判断、行动、边界、复查 |
| 非农业越界率 | < 1% | 由领域闸门和回归集共同验证 |
| 正常 SSE 完成率 | >= 99% | 最终 `done` 有明确 completion_status |
| P95 首字/首事件延迟 | <= 3 秒 | 本地知识库，不含大文件导入 |

这些目标是发布门槛，不是相似度分数的替代品。未完成专家标注前，只报告候选召回，不宣称 Recall@K 或回答质量达标。

## 2. 场景选择与边界

### 首要场景：江西县域水稻病虫害与高温胁迫复查

一次典型任务是：

> “南昌县晚稻分蘖期，连续高温后叶尖干枯，田里有飞虫，昨天已灌水，应该先做什么，什么时候复查？”

系统需要识别多个子问题：症状与生育期、天气胁迫、病虫害候选、现场观察、立即行动、复查条件。该任务天然要求查询分解、跨来源融合和来源适用范围判断，比单一事实问答更能验证 BRAG 五章技术。

### 输入协议

```json
{
  "scenario": "rice_pest_heat_review",
  "crop": "水稻",
  "region": "江西省南昌市某县",
  "stage": "分蘖期",
  "observations": ["叶尖干枯", "发现飞虫"],
  "weather_window": "近3天",
  "spread": "局部/全田/未知",
  "actions_taken": ["昨天灌水"],
  "review_at": null
}
```

缺失字段要进入“待补充现场信息”，不能由模型补造。精确坐标不是 P0 必填项，默认只保留县/区级位置。

### 暂不纳入 P0

- 直接用图片确诊病害；图片仅作为辅助证据，必须结合文字观察和复查。
- 具体农药剂量、登记作物和安全间隔的自由生成；此类结论只接受登记/官方标签等 A 级、scope 匹配材料。
- 施肥、油菜、赣南脐橙、政策补贴作为独立产品流；先复用统一检索契约，P1 再扩展。
- 本地大模型、知识图谱、RAPTOR 全量索引和多租户认证；它们会扩大运维面，不能证明首个场景的核心价值。

## 3. BRAG 五章到本项目的映射

| BRAG 章节 | 结论 | CropWise 落地 |
| --- | --- | --- |
| 基础 RAG / 查询理解 | 先建立稳定索引、召回、生成和来源链 | 保留现有 `agriir_pipeline.py`，补齐 trace、版本和基线对比 |
| 查询转换 | Multi-Query 适合措辞不清；分解适合多步骤问题；HyDE 有额外调用且可能生成虚假细节 | 结构化场景先做规则改写；复杂症状按需并行分解；HyDE 只做离线 A/B，不进入 P0 主链路 |
| RAG-Fusion / 高级查询 | RRF 只依赖排名，适合融合不同检索分支 | 为 Chroma、关键词、时间/官方来源分支统一生成 rank list，再做 RRF |
| 路由 / 查询构建 | 逻辑路由可解释，Self-Query 适合元数据过滤 | P0 用确定性路由选择 `hybrid`、`hybrid-temporal`、`hybrid-metadata`；必要时调用结构化过滤器 |
| 高级索引 | 小块检索、大块返回可保持上下文；时间衰减适合时效资料 | 导入时保存 parent/child、章节、作物、地区、生育期、scope；检索命中 child 后恢复 parent |
| 重排序 / 集成 | 混合检索提高覆盖，交叉编码器提高精度，但成本和延迟更高 | 先用现有本地 lexical + vector；离线确认收益后再加可选 cross-encoder |

### 关键取舍

1. **先逻辑路由，后语义路由。** 场景字段、作物、地区和高风险词已有明确规则，规则更快、更可解释；语义路由只作为分类不确定时的回退。
2. **先 Multi-Query/分解，暂缓 HyDE。** 农业回答有安全责任，假设性文档可能引入不存在的药剂、剂量或症状；必须先证明收益覆盖额外风险。
3. **先父子文档和元数据过滤，暂缓 RAPTOR。** 当前证据包数量较小，层级摘要的收益不足以抵消版本、回滚和引用映射复杂度。
4. **先 RRF，后交叉编码器。** RRF 对分数尺度不敏感，可在本地 embedding 与远程 embedding 间保持稳定；cross-encoder 作为可插拔 reranker，按延迟和质量 A/B 决定是否上线。

## 4. 当前基线与差距

### 已有能力

- `backend/agriir_pipeline.py` 已有查询规范化、子查询拆分、去重、稳定引用 ID、阈值和 trace。
- `backend/knowledge_base.py` 已有 Chroma、中文二元词片段、向量 + lexical 混合排序和策略选择。
- `backend/source_registry.py`、`data/evidence-packs/` 和证据闸门已支持来源等级、`evidence_scope`、官方 HTTPS 域名和版本化材料。
- 已有江西水稻高温热害、油菜、农药管理和赣南脐橙材料；`agriir_eval_skeleton.jsonl` 已有 120 条 P0 骨架。
- `scenario_context`、SSE `trace`/`sources`/`done`、决策卡和专家标注 API 已经存在。

### 主要差距

1. 检索器仍集中在单一 `KnowledgeBase.search()`，没有可替换的 Retriever registry。
2. 当前分块固定为 1000 字符/200 overlap，没有 parent-child、章节边界和版本化索引构建任务。
3. 当前 hybrid 排序是本地启发式，不是真正的 BM25 + vector rank list + RRF；没有可比较的 ablation 报告。
4. `scenario_context` 尚未形成稳定 schema、字段校验和场景路由契约。
5. 评测骨架存在，但真实金标、查询级 trace 采集和发布前自动门槛仍需完善。
6. 高风险引用已能阻断不合格证据，但还缺“结论句 -> 证据片段”的覆盖分析和冲突来源展示。

## 5. 目标架构与模块职责

### 检索阶段

```text
ChatRequest
  -> ScenarioContract.validate()
  -> QueryRouter.route()
       - domain / scenario / crop / region / stage
       - evidence_scope / temporal policy
  -> QueryTransformer
       - deterministic refinement
       - optional multi-query
       - parallel decomposition (max 4)
  -> RetrieverRegistry
       - ChromaRetriever
       - LexicalRetriever
       - TemporalOfficialRetriever
  -> RRFEnsembler
  -> OptionalReranker
  -> ParentContextRestorer + ContextCompressor
  -> EvidenceGate
```

### 建议文件边界

| 模块 | 责任 | P0 是否改动 |
| --- | --- | --- |
| `schemas.py` | 场景结构和请求校验 | 是 |
| `agriir_pipeline.py` | 阶段编排、trace、引用 | 是 |
| `knowledge_base.py` | Chroma 兼容层和索引访问 | 是，保持旧 API |
| `retrievers.py` | 新的 Retriever 协议、关键词、RRF | 新增 |
| `indexing.py` | 文档解析、父子块、元数据和索引版本 | 新增 |
| `source_registry.py` | 来源等级、域名、scope、版本 | 小幅扩展 |
| `agent.py` | 证据上下文、决策卡、降级文案 | 是 |
| `memory.py` / `cases.py` | 病例、复查、升级 | P1 |
| `frontend/components/` | 场景表单、证据卡、trace、复查时间线 | P1 |

所有新阶段必须输出结构化 trace，不把检索内部协议塞进回答正文。

## 6. 8 周执行路线

### W1：冻结场景契约和离线基线

- 固化 `rice_pest_heat_review` 的字段、缺失字段、枚举和错误码。
- 用当前 Chroma/本地 embedding 跑 40 条水稻诊断题，保存 query、候选、来源、耗时和答案版本。
- 建立 B0 指标：候选检索率、可追溯候选率、官方候选率、平均延迟。
- 交付：`scenario_context` schema、基线报告、失败样例 Top 20。

### W2：查询理解与逻辑路由

- 将现有 `refine_query` 拆为结构化字段拼接、同义词扩展、场景 anchor 三层。
- 对“症状 + 天气 + 处理”类问题做最多 4 个并行子查询；简单事实问题不额外调用模型。
- 逻辑路由到 `hybrid`、`hybrid-temporal`、`hybrid-metadata`，输出路由理由。
- 交付：`QueryRouter`、`QueryTransformer`、路由单测和 trace schema。

### W3：证据包和高级索引

- 将文档切成 child chunk，并保留 `parent_id`、`section_path`、`document_id`、`evidence_id`。
- 元数据至少包含：`source_id`、`publisher`、`evidence_level`、`evidence_scope`、`crop`、`region`、`stage`、`published_at`、`valid_at`、`pack_version`。
- 对官方技术意见、当地预警和法规分别建立 scope，禁止用法规支撑具体标签剂量。
- 交付：可重复的索引构建脚本、manifest 校验、索引版本和回滚说明。

### W4：混合检索与 RRF

- 增加关键词检索分支，保持现有 Chroma 分支兼容。
- 每个分支返回稳定 `document_key`、rank、raw_score、retrieval_strategy。
- 使用 RRF 融合，不直接相加不同 embedding 的原始分数；保留分支贡献到 trace。
- 交付：RRF 检索器、分支 ablation（vector/lexical/hybrid/RRF）和 Top-5 对比报告。

### W5：重排序与上下文恢复

- 先用现有 lexical/metadata 规则作为确定性 reranker。
- 评估可选 cross-encoder；只有在 Top-5 相关性提升至少 5 个百分点且 P95 延迟增加不超过 1.5 秒时才进入默认配置。
- 命中 child 后恢复同一 parent 的必要上下文，并去重压缩；每个片段保留原始引用映射。
- 交付：可插拔 `Reranker`、父上下文恢复、上下文预算控制。

### W6：证据闸门与决策卡

- 将高风险 query 的 `required_evidence_scope` 前移到检索阶段。
- 实现结论句到证据片段的覆盖检查；未覆盖句子改写为“待核验”或删除具体数值。
- 增加冲突来源提示：同一主题不同日期/地区的材料不能静默合并。
- 交付：安全回归集、引用覆盖报告、`guarded`/`fallback` 状态卡。

### W7：病例复查闭环

- 新增 `cases`、`case_events`、`review`、`escalate` 资源和幂等 ID。
- 首次回答保存现场摘要、证据版本、行动、复查时间和需观察指标。
- 复查时比较新旧观察，生成差异记录；人工转交前显示待共享字段。
- 交付：病例时间线 API 和前端复查流程。

### W8：专家标注与小范围试点

- 诊断场景完成至少 40 条专家金标；从施肥、农时、政策各抽取 10 条兼容性回归。
- 10-20 名江农师生、农技人员或种植者进行受控试用，收集无效建议、误召回和未完成复查。
- 固化发布报告、回滚索引、来源清单和下一阶段 backlog。
- 交付：试点版本、质量看板、失败案例回灌清单。

## 7. 评测设计

### 离线数据分层

| 集合 | 数量 | 用途 |
| --- | ---: | --- |
| P0 水稻诊断/热害 | 40 | 首要场景金标 |
| 跨场景兼容回归 | 30 | 施肥、农时、政策 |
| 安全与越界 | 20 | 无依据剂量、非农业问题、冲突来源 |
| 检索消融 | 30 | vector、lexical、RRF、rerank 对照 |

每条样本保存 `gold_evidence_ids`、`retrieval_relevant`、`citation_covered`、`faithful`、`safety_ok`、`forbidden_claims` 和审核人。只有 `expert_approved` 样本参与发布结论。

### 每次 PR 必跑

- schema 和场景路由单测。
- 检索确定性、引用 ID 稳定性、RRF 去重和 evidence scope 单测。
- 领域越界、高风险证据、SSE done/error、旧 Markdown 兼容测试。
- `npm run build` 和后端语法/核心测试。

### 每周离线报告

- Recall@5、MRR、候选可追溯率、A 级候选率。
- Context Precision、Context Recall、Faithfulness、Answer Relevancy。
- 五段式完整率、关键判断引用覆盖率、错误/降级率。
- P50/P95 延迟、模型调用次数、单请求 token 和外部来源失败率。

## 8. 数据治理与安全

- A 级来源：农业农村部、江西省及地方政府正式文件、正式登记/标准；可支撑高风险结论。
- B 级来源：Open-Meteo、FAO、科研机构公开数据；只支撑天气/背景，不替代 A 级处方依据。
- C 级来源：百科、图片和未完成审核资料；只能作补充参考。
- D 级来源：论坛、博客、未核验搜索结果；不得进入最终证据。
- 每个文档必须有来源机构、原文 URL、发布日期、有效时间、区域、许可、版本、owner、fallback。
- 外部网页和图片必须有域名白名单、超时、大小限制、速率限制和失败事件。
- 用户数据默认保存县/区级位置和主动提交的观察；图片、病例保留期限和删除入口在 P1 明确。

## 9. 发布门槛和回滚

发布前必须同时满足：

1. 专家金标的 Top-5 召回、引用覆盖、忠实度和安全指标达到 Goal。
2. 农药/肥料/灾害处置问题没有 A 级 scope 匹配证据时，输出 guarded/fallback，不给具体处方。
3. 所有回答能关联 `evidence_id`、索引版本、模型版本和检索 trace。
4. SSE 最终事件明确 `complete`、`fallback`、`guarded` 或 `error`，不能把异常伪装成完成。
5. 索引、知识包和配置有 manifest、校验 hash 和上一版本回滚路径。

任一高风险门槛失败，保留当前线上索引和旧 pipeline 配置，只回滚新索引/新阶段，不删除原始证据包。

## 10. 资料与依据

### BRAG 教程

- [教程主页](https://rag.deeptoai.com/docs/brag-tutorial)
- [基础 RAG：从零开始构建检索增强生成系统](https://rag.deeptoai.com/docs/brag-tutorial/1-query-understanding-transformation)
- [RAG 查询优化：多查询与查询转换](https://rag.deeptoai.com/docs/brag-tutorial/2-rag-fusion-advanced-query)
- [RAG 路由与查询构建](https://rag.deeptoai.com/docs/brag-tutorial/3-routing-query-construction)
- [高级索引与检索策略](https://rag.deeptoai.com/docs/brag-tutorial/4-indexing-advanced-retrieval)
- [重排序与查询集成](https://rag.deeptoai.com/docs/brag-tutorial/5-reranking-ensemble)

### 权威论文与工程资料

- Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)：RAG 的外部非参数记忆和来源可追溯性基础。
- Gao et al., [Precise Zero-Shot Dense Retrieval without Relevance Labels](https://arxiv.org/abs/2212.10496)：HyDE 的收益与“假设文档可能包含虚假细节”的风险依据。
- Zheng et al., [Take a Step Back](https://arxiv.org/abs/2310.06117)：抽象化查询的适用边界，作为复杂背景问题的实验候选。
- Sarthi et al., [RAPTOR](https://arxiv.org/abs/2401.18059)：递归摘要树的长文档收益；本计划基于当前规模暂不列为 P0。
- Es et al., [Ragas: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)：将检索相关性、上下文召回、忠实度和回答相关性分开评估。
- [LangChain RAG tutorial](https://python.langchain.com/docs/tutorials/rag/)：现有 LangChain 代码边界、检索器和链路的工程参考。
- [LangChain retrieval integrations](https://python.langchain.com/docs/integrations/retrievers/)：父文档、多向量、Self-Query 和 reranker 的实现参考；上线前以当前版本 API 为准。
- [Ragas documentation](https://docs.ragas.io/en/stable/)：评测指标与实验记录格式参考。

### 项目内依据

- [AgriIR 下一阶段开发计划](./agriir-next-development-plan.md)
- [CropWise 场景化产品开发设计](./cropwise-scenario-development-plan.md)
- [数据源注册表](./data-source-registry.md)
- [回答质量与前端可见性验收](./quality/answer-quality-audit.md)
- [评测集说明](../data/evals/README.md)

## 11. 头脑风暴待对齐项

以下问题不阻塞本计划执行，但会影响 W7-W8 的产品细节：

1. 首批试点用户更偏向种植户，还是江农师生/农技人员？这决定输入表单的专业字段数量和默认回答长度。
2. 是否允许上传田间图片作为病例附件？若允许，需要先确定保留期限、人工审核责任和可接受的误诊提示。
3. 试点是否必须接入真实江西县域农时/气象数据，还是先用已登记官方材料完成离线验证？
4. 人工升级的接收方是校内农技人员、地方农技站，还是只生成可复制的转交摘要？

默认决策：先面向农技人员和江农师生做受控试点；图片只作为可选辅助；真实天气在 P1 接入；人工升级先生成可审计摘要，不自动外发个人信息。

## 12. Firecrawl 研究与资料准入补充

### CLI 状态

本轮已安装并验证：

- 包：`firecrawl-cli@1.19.30`
- 全局命令：`firecrawl`
- 认证：已通过本机存储凭据认证
- 抓取并发：2
- 安装验证时额度：667 / 1000 credits；本轮抓取和搜索后剩余额度以 `firecrawl --status` 为准，不把动态额度作为产品门槛
- 产物目录：`.firecrawl/`

主页、五个核心章节和参考资料已通过 CLI 批量抓取，7/7 成功。CLI 生成的页面快照用于研究复核，不作为生产知识库原始数据的唯一来源。

### 新增研究结论

1. BRAG 主页明确要求“代码为主、来源背书”，并将五章组织为查询转换、融合与高级查询、路由与结构化查询、索引与高级检索、重排序与集成；本计划因此把每种技术绑定到实验和发布门槛，而不是按名词堆叠功能。
2. 重排序章节给出的 RRF 只依赖排序名次，并以常用 `k=60` 为起点；W4 应比较 `k=20/60/100`，不能把不同检索器的原始相似度直接相加。
3. 高级索引章节同时强调小块召回、大块上下文恢复、上下文压缩和时间衰减；农业材料必须把 `published_at`、`valid_at`、`region` 和 `evidence_scope` 放入同一个证据对象，否则无法解释“为什么这条资料现在适用”。
4. 检索评测搜索结果中，较有价值的证据是混合检索 + 重排 + claim-level grounding 的完整流程；它支持将“召回、重排、生成、声明级支撑”拆开记录，但其生物医学数据集不能替代本项目农业专家金标。
5. `site:` 限定的农业搜索仍返回旧政策、通用通知和不完全匹配页面。搜索结果只能用于发现候选 URL，不能绕过 `source_registry.py`、官方 HTTPS 白名单、日期/地区校验和专家审核。

### 资料准入流水线

```text
Firecrawl search / map
  -> 候选 URL 清单
  -> Firecrawl scrape 原文 Markdown
  -> source_registry 校验域名、发布日、区域、scope、许可
  -> 人工确认标题和正文是否真的支持结论
  -> 生成 manifest + content_hash + evidence_id
  -> 导入 Chroma / parent-child 索引
  -> 专家标注后才进入质量结论
```

建议命令：

```powershell
firecrawl map "https://www.moa.gov.cn/" -o .firecrawl/moa-map.json --json
firecrawl search "site:moa.gov.cn 水稻 高温 热害 技术意见" --limit 10 --scrape -o .firecrawl/moa-rice-search.json --json
firecrawl scrape "https://official.example/article" --format markdown,links --only-main-content -o .firecrawl/official-article.json --json
```

生产导入不能接受搜索结果中的 `description` 作为正文，也不能接受未核验的媒体转载、论坛或搜索摘要作为 A 级依据。抓取失败、页面变更或来源过期必须产生结构化错误，不得静默保留旧结论。

## 13. 检索实验矩阵

每个实验固定同一批 40 条水稻诊断问题、同一批证据包、同一 embedding 和同一生成模型，只改变一个检索阶段。结果保存为 JSONL，至少包含 `run_id`、`pipeline_version`、`index_version`、`query_id`、`retriever`、`reranker`、`latency_ms` 和指标。

| 实验 | 配置 | 主要假设 | 进入默认链路的条件 |
| --- | --- | --- | --- |
| B0 | 当前 Chroma + lexical 混合 | 建立可复现基线 | 所有实验必须超过或解释 B0 |
| E1 | 结构化改写 + 并行分解 | 复杂症状问题召回提升 | Recall@5 提升 >= 5pp，P95 增长 <= 500ms |
| E2 | vector + BM25 + RRF | 兼顾术语精确匹配和语义召回 | Recall@5 或 MRR 提升 >= 5pp，安全指标不下降 |
| E3 | child 检索 + parent 恢复 | 保留技术意见的上下文和限定条件 | Faithfulness 提升 >= 3pp，引用映射 100% |
| E4 | E2 + 可选 cross-encoder | 候选排序更贴近问题 | Context Precision 提升 >= 5pp，P95 增长 <= 1.5s |
| E5 | E2/E4 + context compression | 降低冗余和 token 成本 | token 下降 >= 15%，Faithfulness 不下降 |
| E6 | HyDE 离线对照 | 复杂术语是否值得增加一次模型调用 | 只在收益显著且无高风险虚构实体时考虑 P1 |

实验规则：任何实验如果降低 `safety_ok`、`citation_covered` 或官方候选率，即使平均相关性提高也不能上线。HyDE 生成的假设性文本永远不是证据，不能写入 citation 或 evidence pack。

## 14. W1 立即执行清单

下一轮开发按以下顺序执行，完成一项就产出可审计结果：

1. 在 `backend/schemas.py` 增加 `RicePestHeatContext` 的字段校验，并保持旧 `Dict[str, Any]` 请求兼容。
2. 在 `backend/agriir_pipeline.py` 增加 `route_reason`、`index_version`、`pipeline_version` 和每个子查询的耗时字段。
3. 新增 `backend/retrievers.py`，先实现统一结果契约和纯 Python RRF，不马上引入新的外部服务。
4. 从 `data/evidence-packs/national-crop-technical/` 和江西水稻包补齐 40 条诊断题对应的 `evidence_scope` 与专家审核队列。
5. 生成 B0 JSONL 报告，记录当前检索失败 Top 20，按“术语缺失、地区错配、时间过期、scope 不匹配、上下文截断、无证据”分类。
6. 增加一条 CI 门槛：不存在官方且 scope 匹配证据时，测试必须确认响应状态为 `guarded` 或 `fallback`，不得是 `complete`。

W1 完成定义：不要求业务功能全部上线，但必须能用一个固定 query 重放 `route -> subqueries -> retrievers -> fused results -> citations -> decision status` 全链路，并能从结果反查 `evidence_id` 和索引版本。

## 15. 研究限制与决策更新规则

- Firecrawl 搜索结果的排序和摘要不等于官方认可；每次资料导入仍需原文审核。
- BRAG 教程的对比表是工程选型启发，不是农业领域效果保证；本项目以 40 条专家金标和真实试点数据为最终依据。
- 第三方论文、博客和产品文档只能证明技术可能性，不能支撑农药剂量、登记、补贴和当地防灾处置。
- 任何新技术进入默认链路前必须补充：失败样例、消融对照、延迟/成本、可追溯性和安全回归。
- 每两周重新审查一次来源新鲜度、模型版本、embedding 阈值和评测样本分布；如阈值变更，必须生成新 `pipeline_version`，不得覆盖历史报告。
