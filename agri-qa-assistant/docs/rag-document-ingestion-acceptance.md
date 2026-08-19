# CropWise RAG 文档上传与入库交付标准

日期：2026-08-09

## 交付范围

- 顶部“上传 RAG 文档”入口和输入框回形针入口共用文件选择器。
- 支持 `.txt`、`.md`、`.markdown`、`.csv`、`.html`、`.htm`、`.json`、`.docx`、`.pdf`。
- 上传后先解析文本、判定农业领域、显示置信度、预计分块数和预览；未经确认不写向量库。
- 确认后按 1000 字符块、200 字符重叠切分，调用当前 local/remote embedding 模式并写入 Chroma。
- 使用 SHA-256 内容哈希去重，重复文件不新增向量。

## 验收门槛

| 级别 | 标准 | 通过条件 |
| --- | --- | --- |
| P0 | 上传 API 与前端代理可用 | analyze/ingest 均无非预期 5xx；生产构建通过 |
| P0 | 入库完整性 | 明确确认后分块数大于 0，检索能命中新文档；未确认时文档数量不变 |
| P1 | 领域安全 | 无农业主题、否定农业范围、纯编程/数学或混合代码文档不得入库 |
| P1 | 文件安全 | 仅允许白名单扩展名，单文件不超过 15MB，解析文本不超过 500,000 字符 |
| P1 | 可重复性 | 相同内容重复上传必须返回 duplicate=true 且 added_chunks=0 |
| P1 | 用户反馈 | 前端明确显示解析中、可入库/不建议入库、置信度、分块数、入库完成或失败原因 |
| P2 | 响应式与可访问性 | 桌面/390px 移动端无水平溢出；文件选择器、移除、确认按钮有 aria-label |
| P2 | 依赖与运维 | requirements 明确声明 python-multipart、python-docx、PyMuPDF；日志不打印全文内容 |

## 已执行测试

### 1. 单元测试

`python -m pytest backend/test_document_ingestion.py backend/test_domain_guard.py -q`

覆盖 UTF-8/GB18030、HTML/JSON、农业判定、混合编程拒绝、扩展名/空文件/短文本/15MB 边界。

### 2. 后端 API 集成测试

- 农业 Markdown：`/analyze` 返回 `eligible=true`，无 `text` 全文泄漏。
- `confirm=false`：返回 `requires_confirmation=true`，不写库。
- `confirm=true`：返回 `added_chunks=1`，向量检索命中新文件。
- 相同文件再次确认：`duplicate=true`、`added_chunks=0`。
- 非农业/编程 Markdown：分析返回 `eligible=false`，确认入库返回 422。
- 健康接口保持 200，知识库文档数量按预期增加。

### 3. 前端真实交互测试

- Chrome 桌面端：两个上传入口均可触发选择器；农业文档显示“可进入农业知识库”、置信度、预计分块和确认按钮。
- 确认后显示“已向量化入库”，知识库计数更新；重复文件显示“已存在，未重复写入”。
- 非农业文档显示“不建议入库”，不显示确认按钮。
- 390x844 移动端无水平溢出。
- `/api/knowledge-base/documents/analyze` 通过 Next rewrite 返回 200。

### 4. 类型、构建与回归

- `npx tsc --noEmit`：通过。
- `NEXT_DIST_DIR=.next-upload NODE_OPTIONS=--max-old-space-size=1536 npm run build`：通过。
- 原有 `backend/test_domain_guard.py`：3 passed。
- 原有 `backend/test_stream_contract.py`：通过。

## 可靠性边界

当前入库链路可靠地完成“文本解析→农业预检→分块→向量化→去重→检索验证”。PDF 扫描图片、复杂版式、OCR 尚未纳入承诺；远程 embedding 失败时不会伪造成功，需由调用方重试。上传内容未做用户级权限隔离，生产环境必须在 API 前增加认证、配额、审计和租户隔离。

## 生产发布前必须完成

1. 加入用户身份、文档归属和删除/撤回能力，避免不同用户共享私有知识。
2. 增加异步任务队列、进度事件和超时/重试策略，避免大 PDF 阻塞请求。
3. 增加病毒扫描、真实 MIME/魔数校验、PDF 页数上限和 OCR 资源限制。
4. 为每个文档补齐来源 URL、发布日期、授权和版本字段，前端展示证据新鲜度。
5. CI 固定浏览器和 embedding 测试替身，持续执行 API、SSE、检索相关性和移动端回归。
