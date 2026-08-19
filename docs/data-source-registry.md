# CropWise 数据源注册表（P0 冻结版）

## 准入规则

- A 级：农业农村部门、正式登记/国家标准、江西省及设区市政府正式文件、已审核官方技术规程。可支持农药、肥料、政策、补贴、标准和登记结论。
- B 级：Open-Meteo、FAO、科研机构开放数据等公开资料。可支持天气/统计/背景信息，不能替代 A 级高风险依据。
- C 级：Wikimedia、公开百科和未完成审核的内部知识。只能作为补充参考或图片素材。
- D 级：论坛、博客、未经核验的搜索结果。不得进入最终证据。

## 已登记来源

| source_id | 来源 | 级别 | 用途 | 时间/许可 | 降级策略 |
| --- | --- | --- | --- | --- | --- |
| `open-meteo-forecast` | [Open-Meteo](https://open-meteo.com/) | B | 县/区级天气 PoC、农时风险提示 | 保留 `retrieved_at`、`valid_at`；CC BY 4.0/署名 | 超时返回结构化错误，不猜测天气；灾害预警以气象部门为准 |
| `moa-official` | [农业农村部](https://www.moa.gov.cn/) | A | 国家政策、登记、技术规范 | 保存发布日期、原文 URL、版本 | 只返回已核验官方入口 |
| `jx-agri-official` | 江西省农业农村厅及地方政府公开文件 | A | 江西县域政策、农时和生产规程 | 保存发布日期、适用地区、有效期 | 无县域适用范围时降级为待核验 |
| `cropwise-curated` | CropWise 已审核知识包 | C（可逐条升级） | 背景解释和场景召回 | 必须补齐来源 URL、审核人、版本 | 不得支撑高风险具体处方 |
| `wikimedia-commons` | [Wikimedia Commons](https://commons.wikimedia.org/) | C | 开放农业图片 | 保存许可证、作者、原图页 | 图片只作识别参考，不作确诊证据 |

## 上线前必填字段

`source_id`、`publisher`、`evidence_level`、`title`、`url`、`retrieved_at`、`valid_at`/`published_at`、`license`、`region`、`version`、`owner`、`fallback`。

## 当前代码闸门

`backend/agriir_pipeline.py` 会对包含农药、肥料、兽药、疫病、政策、补贴、标准、规范或登记的查询强制要求 `evidence_level=A`；不满足时来源卡标记为“待核验”，模型不得把普通知识库片段写成官方依据。

高风险引用还必须匹配 `evidence_scope`。例如《农药管理条例》可支撑 `pesticide_governance`、`pesticide_registration`，但不可以支撑 `pesticide_label`，因此不能据此输出某作物的具体剂量或安全间隔。
