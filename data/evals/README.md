# AgriIR 评测集骨架

本目录是研发先维护、专家后标注的 120 条 P0 评测集入口。首版配额：诊断 40、施肥灌溉 25、农时天气 25、政策 20、越界与安全 10。

每条样本先填写 `question`、`scenario`、`crop`、`region`、`expected_sources` 和 `forbidden_claims`；专家标注阶段再填写 `gold_evidence_ids`、`retrieval_relevant`、`citation_covered`、`faithful`、`safety_ok` 和 `reviewer`。

字段约束见 [agriir_eval_schema.json](./agriir_eval_schema.json)。未完成专家标注的样本不得用于发布结论，只能用于发现检索回归。

## 专家标注接口

1. `GET /evaluations/items?scenario=policy` 获取待审核题目。
2. 从来源卡或知识库条目中选择真实存在的 `evidence_id`。
3. `POST /evaluations/items/{id}/annotation` 提交 `reviewer`、`gold_evidence_ids`、`citation_covered`、`faithful`、`safety_ok`。

只有 `review_status=expert_approved` 的条目才会进入 `/evaluations/retrieval` 的 Recall@K、引用覆盖率、忠实度和安全覆盖率。接口拒绝不存在的 `evidence_id`，防止标注指向无法复现的材料。

在专家标注前，报告只提供覆盖诊断指标：`candidate_retrieval_rate` 表示检索到任意候选，`traceable_candidate_retrieval_rate` 表示至少一个候选带稳定 `evidence_id`，`official_candidate_retrieval_rate` 表示至少一个候选为 A 级官方来源。这三项不能替代专家 Recall@K 或回答质量结论。
