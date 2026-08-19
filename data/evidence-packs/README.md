# CropWise 证据包契约

每个知识包对应一个业务域，例如 `jiangxi-rice`、`jiangxi-rapeseed`、`gannan-citrus`、`jiangxi-policy`。包内仅收录已通过来源核验的文档；原文件不提交到仓库时，清单仍必须保留其来源、发布日期、版本、许可证和哈希。

## 文档元数据

入库接口支持以下表单字段：`source_id`、`source_url`、`published_at`、`region`、`pack_id`、`pack_version`。其中 A 级来源必须使用已登记官方 HTTPS 域名、提供发布日期，并自动产生稳定 `evidence_id`。

## 清单格式

```json
{
  "schema_version": "1.0",
  "pack_id": "jiangxi-rice",
  "version": "2026.08.0",
  "owner": "CropWise data steward",
  "documents": []
}
```

填充 `documents` 前需要由农技专家核验。空清单表示契约已建立，不能被当作可引用证据。

## 当前包清单

| 包 | 版本 | 状态 | 覆盖范围 |
| --- | --- | --- | --- |
| `national-pesticide-policy` | `2026.08.0` | 已物化并入库 | 农药治理、登记核验 |
| `national-crop-technical` | `2026.08.0` | 已物化并入库 | 水稻高温响应、水肥管理、油菜病虫害与用药边界 |
| `gannan-citrus` | `2026.08.0` | 已物化并入库 | 赣州脐橙低温风险与防冻农事建议 |
| `jiangxi-rice` | `2026.08.0` | 待官方 HTTPS 材料核验 | 江西水稻县域生产规程 |
| `jiangxi-policy` | `2026.08.0` | 待官方 HTTPS 材料核验 | 江西政策、补贴、申报要求 |

已物化材料的发布日期、正文哈希和 `evidence_id` 以各包 `manifest.json` 为准；任何文档更新必须递增包版本，并通过导入器的哈希替换/回滚流程。

已登记的公开材料可由 `python backend/evidence_pack_importer.py <manifest> --ingest` 导入。导入器仅允许清单中预登记的 HTTPS 页面，保存正文哈希和 `evidence_id`，并在页面发布日期与清单不一致时中止。
