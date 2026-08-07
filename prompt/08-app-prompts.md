# 08 一键生成应用 Prompt 案例

> 本节精选 20+ 可直接用于生成完整应用的专业 Prompt，覆盖 Web、移动端、CLI、数据、自动化等场景。
> 所有 Prompt 均按“一键生成”级别设计，复制后即可使用。

---

## 8.1 Web 应用类

### 1. 全栈 Todo 应用
```
你是一个全栈工程师。使用 Next.js 14 (App Router) + TypeScript + Tailwind CSS + Prisma + SQLite 构建一个生产级 Todo 应用。

功能需求：
- 用户注册/登录（NextAuth.js，Credentials provider）
- CRUD Todo（标题、描述、截止日期、优先级、标签）
- 拖拽排序（@dnd-kit/core）
- 过滤与搜索（按状态、标签、日期范围）
- 数据持久化到 SQLite（Prisma ORM）

技术要求：
- 使用 Server Actions 处理所有数据变更
- 响应式布局，移动端优先
- 添加 loading skeleton 和错误边界
- 输出完整项目结构，每个文件包含完整代码

输出格式：按文件路径列出代码块。
```

### 2. 实时聊天应用
```
使用 React + TypeScript + Socket.IO + Node.js + Express 构建一个实时聊天应用。

功能需求：
- 多房间支持
- 用户名登录（无需注册）
- 在线用户列表
- 消息时间戳和发送者高亮
- 支持发送代码块（带语法高亮）

技术要求：
- 前端使用 Vite + React + Zustand 状态管理
- 后端使用 Express + Socket.IO + cors
- 消息存储在内存数组中（可替换为 Redis）
- 添加“正在输入...”指示器
- 输出完整的 package.json 和启动脚本

输出格式：前端/后端分离，按目录结构组织。
```

### 3. 个人博客系统
```
使用 Astro 5 + Markdown + RSS + 评论系统构建一个静态博客。

功能需求：
- 首页文章列表（分页）
- 文章详情页（支持代码高亮、数学公式）
- 标签分类和归档页
- RSS/Atom 订阅
- 搜索功能（基于页面索引）
- 深色/浅色主题切换

技术要求：
- 内容存储在 Markdown 文件中（frontmatter 含日期、标签、摘要）
- 使用 Astro Content Collections 管理文章
- 部署到 Vercel/Netlify，提供 CI/CD 配置
- 添加 sitemap.xml 和 SEO meta 标签
- 输出完整的 astro.config.mjs 和目录结构

输出格式：配置文件 + 页面组件 + 布局组件。
```

### 4. URL 缩短服务
```
使用 FastAPI + SQLAlchemy + SQLite + Redis 构建一个 URL 缩短服务。

功能需求：
- 创建短链接（自定义别名可选）
- 302 重定向（带点击统计）
- 链接过期时间设置
- 批量创建短链接（CSV 导入）
- RESTful API 文档（自动生成 Swagger）

技术要求：
- 使用 Pydantic 做数据校验
- Redis 缓存热点链接（LRU 策略）
- 添加速率限制（slowapi）
- 输出 Dockerfile 和 docker-compose.yml
- 包含单元测试（pytest）

输出格式：按模块列出完整代码。
```

### 5. 在线代码编辑器
```
使用 React + TypeScript + Monaco Editor + WebContainer 构建一个在线代码编辑器。

功能需求：
- 支持 HTML/CSS/JS 实时预览
- 多文件标签页
- 代码格式化（Prettier）
- 本地存储（localStorage）自动保存
- 分享功能（生成可分享链接）

技术要求：
- 使用 Sandpack 或 WebContainer API 实现安全沙箱
- 支持暗色主题
- 响应式布局
- 输出完整的组件结构和样式

输出格式：单个 HTML 文件（包含所有依赖 CDN）或完整 React 项目。
```

---

## 8.2 移动应用类

### 6. 习惯追踪器
```
使用 React Native + Expo + TypeScript + AsyncStorage 构建一个习惯追踪应用。

功能需求：
- 添加/删除习惯（名称、图标、颜色、频率）
- 每日打卡（带手势操作）
- 统计页面（连续天数、完成率热力图）
- 提醒通知（expo-notifications）
- 数据导出（JSON/CSV）

技术要求：
- 使用 Expo Router 做导航
- 使用 React Native Reanimated 做动画
- 使用 React Native Chart Kit 做统计图表
- 输出完整的 app.json 和目录结构

输出格式：按屏幕列出组件代码。
```

### 7. 简易天气应用
```
使用 Flutter + Dart + OpenWeatherMap API 构建一个天气应用。

功能需求：
- 当前天气展示（温度、湿度、风速、天气图标）
- 7 天预报
- 城市搜索（支持中文拼音）
- 单位切换（摄氏度/华氏度）
- 离线缓存最近查询

技术要求：
- 使用 Riverpod 做状态管理
- 使用 Dio 做网络请求
- 使用 Hive 做本地存储
- 添加骨架屏加载效果
- 输出完整的 pubspec.yaml

输出格式：按页面和模型列出代码。
```

---

## 8.3 CLI 工具类

### 8. 项目脚手架工具
```
使用 Python + Click + Jinja2 构建一个项目脚手架 CLI 工具。

功能需求：
- 交互式问答选择项目类型（Web/CLI/ML）
- 从模板生成项目结构
- 自动初始化 git 和虚拟环境
- 支持自定义模板目录

技术要求：
- 使用 Click 处理命令行参数
- 使用 Jinja2 渲染模板文件
- 使用 rich 美化终端输出
- 输出完整的 setup.py/pyproject.toml
- 添加 --dry-run 模式

输出格式：单个 .py 文件 + 模板目录结构。
```

### 9. 日志分析工具
```
使用 Go + Cobra + Viper 构建一个 CLI 日志分析工具。

功能需求：
- 支持多格式日志解析（JSON/纯文本/CSV）
- 统计错误率、响应时间分布
- 过滤指定时间范围和关键词
- 生成 HTML 报告

技术要求：
- 使用 Cobra 构建子命令（analyze/export/report）
- 使用 Viper 管理配置
- 使用 Go template 生成 HTML 报告
- 支持并发解析大文件
- 输出完整的 go.mod 和目录结构

输出格式：按模块列出代码。
```

---

## 8.4 数据分析类

### 10. 销售数据仪表盘
```
使用 Python + Streamlit + Plotly + Pandas 构建一个销售数据仪表盘。

功能需求：
- 上传 CSV/Excel 销售数据
- 核心指标卡片（总销售额、订单量、客单价、同比增长）
- 趋势图（按日/周/月）
- 区域分布地图
- 产品类别占比（饼图/旭日图）
- 客户分层（RFM 分析）

技术要求：
- 使用 Streamlit 的 session_state 管理状态
- 使用 Plotly 做交互式图表
- 添加数据导出功能
- 使用缓存避免重复计算
- 输出完整的 requirements.txt 和启动脚本

输出格式：单个 app.py 文件。
```

### 11. 自动化财务报表
```
使用 Python + OpenPyXL + Pandas + Matplotlib 构建一个自动化财务报表生成器。

功能需求：
- 读取多个月度销售数据
- 生成损益表、资产负债表、现金流量表
- 自动计算关键财务比率（毛利率、净利率、ROE）
- 生成可视化图表（收入趋势、费用结构）
- 导出为 Excel（多 sheet）和 PDF

技术要求：
- 使用 OpenPyXL 美化 Excel 格式（条件格式、图表）
- 使用 WeasyPrint 或 ReportLab 生成 PDF
- 使用 Jinja2 模板化报告内容
- 输出完整的项目结构

输出格式：按模块列出代码。
```

### 12. A/B 测试分析器
```
使用 Python + SciPy + Statsmodels + Streamlit 构建一个 A/B 测试分析器。

功能需求：
- 上传实验数据（用户ID、分组、转化、收入）
- 计算样本量和统计功效
- 执行假设检验（t-test、chi-square）
- 可视化置信区间
- 输出实验结论和建议

技术要求：
- 使用 Statsmodels 进行统计检验
- 使用 Plotly 做交互式可视化
- 添加数据质量检查（样本比率不匹配、新奇效应检测）
- 输出完整的 requirements.txt

输出格式：单个 app.py 文件。
```

---

## 8.5 自动化与集成类

### 13. 邮件自动回复机器人
```
使用 Python + IMAP + OpenAI API + Jinja2 构建一个智能邮件自动回复机器人。

功能需求：
- 定期检查新邮件（IMAP）
- 使用 LLM 分类邮件类型（咨询/投诉/商务/垃圾）
- 根据类型生成个性化回复
- 支持自定义模板和品牌语气
- 发送回复（SMTP）并标记已处理

技术要求：
- 使用 IMAPClient 或 imaplib 收邮件
- 使用 OpenAI API 生成回复
- 使用 Jinja2 管理回复模板
- 使用 schedule 或 APScheduler 定时执行
- 添加日志和错误通知
- 输出完整的配置文件

输出格式：单个 .py 文件 + 配置文件模板。
```

### 14. 自动化测试脚本生成器
```
使用 Python + Selenium + Playwright + OpenAI API 构建一个自动化测试脚本生成器。

功能需求：
- 读取用户故事或验收标准
- 自动生成端到端测试脚本（Selenium/Playwright）
- 支持多浏览器（Chrome/Firefox/Edge）
- 生成测试报告（HTML）
- 集成到 CI/CD 流水线

技术要求：
- 使用 Pytest 或 Playwright Test 框架
- 使用 Page Object Model 设计模式
- 使用 OpenAI API 将自然语言转换为测试步骤
- 输出完整的项目结构

输出格式：按模块列出代码。
```

### 15. 数据同步 ETL 管道
```
使用 Python + Apache Airflow + SQLAlchemy 构建一个数据同步 ETL 管道。

功能需求：
- 从多个数据源提取数据（API/数据库/文件）
- 数据清洗和转换
- 加载到目标数据仓库
- 数据质量检查
- 失败重试和告警

技术要求：
- 使用 Airflow 编排任务
- 使用 SQLAlchemy 管理数据库连接
- 使用 Great Expectations 做数据质量验证
- 添加 Slack/邮件告警
- 输出完整的 Docker Compose 配置

输出格式：按 DAG 和模块列出代码。
```

---

## 8.6 游戏与娱乐类

### 16. 文字冒险游戏
```
使用 TypeScript + React + Framer Motion 构建一个文字冒险游戏前端。

功能需求：
- 故事节点系统（选择分支）
- 角色属性管理（生命值、金币、物品）
- 存档/读档（localStorage）
- 动态背景和音效
- 多结局支持

技术要求：
- 使用 React + TypeScript + Vite
- 使用 Framer Motion 做页面转场动画
- 使用 Zustand 管理游戏状态
- 故事数据独立为 JSON 文件
- 输出完整的项目结构

输出格式：按组件列出代码。
```

### 17. 2048 游戏
```
使用 HTML5 Canvas + JavaScript 构建一个完整的 2048 游戏。

功能需求：
- 4x4 网格，支持键盘和触摸滑动
- 动画过渡效果
- 分数系统和最高分（localStorage）
- 游戏结束检测和重新开始
- 响应式设计（桌面和移动端）

技术要求：
- 单文件 HTML（包含 CSS 和 JS）
- 使用 Canvas API 绘制
- 添加移动端触摸事件支持
- 使用 CSS 动画增强体验
- 输出可直接运行的 HTML 文件

输出格式：单个 HTML 文件。
```

---

## 8.7 浏览器插件类

### 18. 网页阅读助手
```
使用 Chrome Extension Manifest V3 + TypeScript + React 构建一个网页阅读助手插件。

功能需求：
- 选中文本后弹出工具栏（总结/翻译/解释）
- 侧边栏显示摘要和关键点
- 支持自定义提示词模板
- 阅读进度追踪
- 导出笔记（Markdown）

技术要求：
- 使用 Manifest V3 规范
- 使用 React + TypeScript + Vite 构建
- 使用 Chrome Storage API 保存设置
- 使用 Content Scripts 注入页面
- 输出完整的项目结构和 manifest.json

输出格式：按模块列出代码。
```

### 19. 广告拦截规则生成器
```
使用 JavaScript + Manifest V3 构建一个广告拦截规则生成器插件。

功能需求：
- 可视化规则编辑器（CSS 选择器匹配）
- 导入/导出规则（JSON）
- 一键启用/禁用规则
- 白名单管理
- 规则统计（拦截次数）

技术要求：
- 使用 Manifest V3 Declarative Net Request API
- 使用 Chrome Storage API 同步规则
- 使用 Popup 页面管理规则
- 输出完整的项目结构

输出格式：按文件列出代码。
```

---

## 8.8 API 服务类

### 20. RESTful API 脚手架
```
使用 FastAPI + SQLAlchemy + Pydantic + Alembic 构建一个生产级 RESTful API 脚手架。

功能需求：
- 用户认证（JWT + OAuth2）
- CRUD 资源管理
- 分页、过滤、排序
- 输入验证和错误处理
- 自动生成 OpenAPI/Swagger 文档

技术要求：
- 使用 Pydantic V2 做数据校验
- 使用 SQLAlchemy 2.0 + Alembic 做迁移
- 使用 JWT 做认证
- 添加 CORS、限流、日志中间件
- 输出完整的 Dockerfile 和 docker-compose.yml
- 包含 pytest 测试用例

输出格式：按模块列出代码。
```

### 21. GraphQL API 服务器
```
使用 Node.js + TypeScript + GraphQL Yoga + Prisma 构建一个 GraphQL API 服务器。

功能需求：
- 用户和文章模型
- 查询、变更、订阅
- DataLoader 解决 N+1 问题
- 实时订阅（WebSocket）
- 文件上传（GraphQL Multipart Request）

技术要求：
- 使用 GraphQL Yoga 4 做服务器
- 使用 Prisma 做 ORM
- 使用 Pothos 构建 Schema
- 使用 Redis 做缓存和 Pub/Sub
- 输出完整的项目结构和 Docker 配置

输出格式：按模块列出代码。
```

---

## 8.9 系统与工具类

### 22. 桌面笔记应用
```
使用 Electron + React + TypeScript + SQLite 构建一个桌面笔记应用。

功能需求：
- 创建/编辑/删除笔记（Markdown 支持）
- 文件夹组织
- 全文搜索
- 标签系统
- 云同步（可选，通过 WebDAV）

技术要求：
- 使用 Electron + React + TypeScript + Vite
- 使用 better-sqlite3 做本地存储
- 使用 CodeMirror 6 做 Markdown 编辑器
- 使用 Electron Builder 打包
- 输出完整的项目结构和构建配置

输出格式：按进程（main/preload/renderer）列出代码。
```

### 23. 终端 AI 助手
```
使用 Python + Typer + OpenAI SDK 构建一个终端 AI 助手。

功能需求：
- 交互式对话（支持多轮上下文）
- 命令历史（sqlite3 存储）
- 快捷指令（/summarize/translate/code）
- 流式输出（实时显示）
- 配置文件管理

技术要求：
- 使用 Typer 构建 CLI
- 使用 rich 美化终端输出
- 使用 prompt_toolkit 实现交互式输入
- 使用 OpenAI SDK 调用模型
- 输出完整的 pyproject.toml

输出格式：单个 .py 文件。
```

---

## 8.10 快速使用清单

| 编号 | 应用类型 | 技术栈 | 预计代码量 |
|------|---------|--------|-----------|
| 1 | 全栈 Todo | Next.js + Prisma | 500+ 行 |
| 2 | 实时聊天 | React + Socket.IO | 600+ 行 |
| 3 | 个人博客 | Astro + Markdown | 400+ 行 |
| 4 | URL 缩短 | FastAPI + Redis | 350+ 行 |
| 5 | 在线编辑器 | React + Monaco | 450+ 行 |
| 6 | 习惯追踪 | React Native | 500+ 行 |
| 7 | 天气应用 | Flutter | 400+ 行 |
| 8 | 脚手架工具 | Python + Click | 300+ 行 |
| 9 | 日志分析 | Go + Cobra | 400+ 行 |
| 10 | 销售仪表盘 | Streamlit + Plotly | 350+ 行 |
| 11 | 财务报表 | Python + OpenPyXL | 450+ 行 |
| 12 | A/B 测试 | Streamlit + SciPy | 400+ 行 |
| 13 | 邮件机器人 | Python + IMAP | 350+ 行 |
| 14 | 测试生成器 | Python + Selenium | 400+ 行 |
| 15 | ETL 管道 | Python + Airflow | 500+ 行 |
| 16 | 文字冒险 | React + Framer Motion | 400+ 行 |
| 17 | 2048 游戏 | HTML5 Canvas | 300+ 行 |
| 18 | 阅读助手 | Chrome Extension | 450+ 行 |
| 19 | 广告拦截 | Chrome Extension | 350+ 行 |
| 20 | REST API | FastAPI + Prisma | 500+ 行 |
| 21 | GraphQL API | Node.js + Yoga | 500+ 行 |
| 22 | 桌面笔记 | Electron + React | 600+ 行 |
| 23 | 终端 AI | Python + Typer | 300+ 行 |

---

## 8.11 使用建议

1. **先跑通最小版本**：选择 1-2 个应用，先要求生成核心功能，再迭代
2. **逐模块验证**：生成后先运行，确认每个模块可工作再继续
3. **结合版本控制**：每个应用生成后立即 git commit，便于回溯
4. **记录有效 Prompt**：把实际运行良好的 Prompt 存入个人模板库
5. **逐步增加约束**：从“能跑”到“好看”到“高性能”，分阶段迭代

---

*最后更新：2026-03-14*
*配套文档：09-app-directions.md*