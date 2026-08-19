# 农业场景免费 MCP 服务评估

## 已落地的零密钥方案

当前系统新增 `search_agri_resources` 工具，不依赖第三方 API Key：

- Wikimedia Commons API：搜索开放授权农业图片，返回缩略图 URL、详情页和许可证元数据。
- FAO 搜索入口：提供农业知识、作物和粮食安全资料入口。
- 中国农业农村部公开检索入口：提供政策、技术和公开信息入口。

图片和文档通过 `resources` 事件进入前端白名单卡片，模型不能直接注入任意 HTML 或脚本。

## 推荐评估的开源 MCP 服务

| 服务 | 用途 | 成本/权限 | 当前建议 |
| --- | --- | --- | --- |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) 的 Fetch | 抓取指定网页 | 开源；目标站点访问规则仍适用 | 已有内嵌 Fetch 逻辑，优先保持本地实现，后续可替换为官方 server。 |
| [Rudra-ravi/wikipedia-mcp](https://github.com/Rudra-ravi/wikipedia-mcp) | Wikipedia 检索 | 开源；Wikipedia 公共内容 | 适合补充作物百科，需增加来源可信度提示。 |
| [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | arXiv 论文检索 | 开源；arXiv 公共 API | 适合科研问答，不适合直接作为农药剂量依据。 |
| [hellokaton/unsplash-mcp-server](https://github.com/hellokaton/unsplash-mcp-server) | 图片搜索 | 服务开源，但 Unsplash API 凭据/额度要求需自行确认 | 可作为高质量农田场景图片补充，不作为病虫害鉴定证据。 |
| [mikechao/brave-search-mcp](https://github.com/mikechao/brave-search-mcp) | 网页/图片/新闻搜索 | 需要 Brave Search API Key | 仅在配置 Key 后启用，结果必须展示来源和时间。 |
| [jztan/pdf-mcp](https://github.com/jztan/pdf-mcp) | PDF、OCR、表格和图片读取 | 开源；本地文件为主 | 适合导入农技规程、标准和试验报告。 |

## 安全与运维边界

- 第三方搜索结果只能作为参考来源，不能覆盖本地 RAG 的品种、用量和安全间隔规则。
- 所有外部链接在前端新窗口打开，并展示来源域名/许可信息。
- 生产环境要增加域名白名单、请求超时、响应大小限制和速率限制。
- 农药、兽药和政策问题要标注资料日期，并建议用户核对当地官方最新规定。

## 研究依据

- [MCP 官方服务器仓库](https://github.com/modelcontextprotocol/servers)
- [Wikimedia Commons API 文档](https://www.mediawiki.org/wiki/API:Main_page)
- [FAO 官网](https://www.fao.org/)
- [农业农村部官网](https://www.moa.gov.cn/)
