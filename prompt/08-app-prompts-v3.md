# 08 应用提示词：Premium 产品级 Prompt 合集

> 本文件聚焦**高质量、有个性、有商品价值、有产品属性**的应用 Prompt。
> 所有 Prompt 均按**可直接生成商业级前端产品**设计，融入 2025-2026 流行前端生态：
> - **组件库**：shadcn/ui、NextUI、Magic UI
> - **样式**：Tailwind CSS、CSS Variables、暗色主题
> - **图标**：Lucide、Heroicons、Phosphor Icons
> - **插画**：Undraw、Storyset、DrawKit、Open Doodles
> - **3D/动效**：Three.js、React Three Fiber、Framer Motion、Lottie
> - **表单/数据**：React Hook Form、Zod、TanStack Query、tremor

---

## 8.1 AI + 3D 沉浸式体验

### 1. AI 品牌 3D 产品配置器
```
你是一个高端品牌电商产品专家。

任务：构建一个 3D 产品配置器，让用户实时定制产品并预览。

产品场景：奢侈品牌手表 / 运动鞋 / 耳机 / 首饰

功能：
1. 3D 模型实时渲染（Three.js / React Three Fiber）
2. 材质切换（金属/皮革/碳纤维，带 PBR 贴图）
3. 颜色定制（实时换色，支持渐变和金属漆）
4.  engraving 文字（用户输入文字，实时 3D 雕刻预览）
5. 环境光照（工作室/户外/展厅，HDR 环境映射）
6. AR 预览（WebXR，手机端查看真实大小）
7. 分享与购买（生成配置链接，跳转结账）

技术栈：
- 前端：Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- 3D：React Three Fiber + @react-three/drei + @react-three/postprocessing
- 状态：Zustand（配置状态）+ TanStack Query（产品数据）
- 后端：Next.js API Routes + Stripe（支付）
- 部署：Vercel + Cloudflare Images（CDN）

设计要求：
- 使用 Inter 字体 + 宽字距营造奢侈感
- 深色背景 + 聚光灯效果突出产品
- 加载动画：3D 模型渐进式加载
- 微交互：按钮磁性吸附、配置项切换动画
- 插画：使用 Undraw 风格的简约线条插画作为空状态

输出：完整的 3D 配置器代码 + 产品页面 + 结账流程
```

### 2. AI 3D 角色 Avatar 生成器
```
你是一个元宇宙/数字人产品专家。

任务：构建一个 AI 驱动的 3D 角色 Avatar 生成器。

功能：
1. 文本/图片描述生成 3D 角色（AI + 3D 模板混合）
2. 实时编辑（发型/服饰/配饰/肤色/表情）
3. 姿势库（100+ 预设姿势，支持自定义）
4. 场景背景（虚拟摄影棚/风景/纯色）
5. 输出格式（GLB/GLTF/FBX，支持 Blender/Unity/Unreal）
6. 社交分享（生成角色卡片，支持 PNG/GIF）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Three.js
- 3D：React Three Fiber + @react-three/fiber + @react-three/drei
- AI：Stable Diffusion + ControlNet（角色生成）+ LoRA（风格）
- 后端：FastAPI + Celery（异步生成任务）
- 存储：S3（模型文件）+ Redis（任务队列）

设计要求：
- 使用玻璃拟态（Glassmorphism）UI 面板
- 左侧 3D 视口，右侧属性面板
- 色彩：赛博朋克风格渐变（紫/粉/蓝）
- 图标：Phosphor Icons（线性风格）
- 插画：使用 Storyset 科技风格插画作为引导页

输出：完整的 Avatar 生成器 + 3D 编辑器 + 导出功能
```

### 3. AI 空间设计 3D 预览
```
你是一个室内设计科技产品专家。

任务：构建一个 AI 空间设计 3D 预览应用。

功能：
1. 房间扫描（手机 LiDAR 或手动输入尺寸）
2. AI 设计生成（基于风格偏好自动生成布局）
3. 3D 实时渲染（Three.js，支持漫游模式）
4. 家具替换（拖拽更换家具，自动对齐）
5. 材质编辑（地板/墙面/窗帘，实时更换）
6. 光照模拟（自然光/人工光，基于时间地点）
7. 预算计算（自动汇总家具价格）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui
- 3D：Three.js + React Three Fiber + @react-three/rapier（物理）
- AI：LLM（设计理解）+ 3D 生成模型
- 后端：FastAPI + 家具数据库 API

设计要求：
- 使用 Bento Grid 布局展示设计方案
- 色彩：温暖的中性色（米白/浅灰/原木色）
- 字体：Playfair Display（标题）+ Inter（正文）
- 插画：使用 DrawKit 室内设计风格插画
- 动效：页面切换视差滚动（Framer Motion）

输出：3D 室内设计预览器 + AI 设计生成 + 家具目录
```

---

## 8.2 AI 驱动的内容创作平台

### 4. AI 播客/视频自动剪辑工作台
```
你是一个多媒体内容创作产品专家。

任务：构建一个专业级 AI 播客/视频自动剪辑工作台。

功能：
1. 多轨时间轴（音频/视频/字幕/音效）
2. AI 自动剪辑（静音移除、 filler words 删除、节奏优化）
3. 精彩片段自动标记（基于语义重要性）
4. 多版本输出（精简版/完整版/社交媒体切片）
5. 自动字幕生成与美化（Whisper + 样式模板）
6. 背景音乐推荐与混音（Audiio/Storyblocks 集成）
7. 团队协作（评论/审批/版本管理）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + WaveSurfer.js
- 后端：FastAPI + FFmpeg + Whisper
- AI：LLM（内容理解）+ 音频分析模型
- 存储：S3 + CloudFront（CDN）
- 协作：Liveblocks（实时协作）

设计要求：
- 使用深色主题（专业视频软件风格）
- 时间轴组件：自定义 Canvas 绘制，支持缩放/拖拽
- 波形可视化：渐变色波形，播放头带发光效果
- 图标：Lucide 图标（线性风格）
- 插画：使用 Open Doodles 人物插画作为空状态
- 字体：JetBrains Mono（时间码）+ Inter（UI）

输出：完整的多轨编辑器 + AI 剪辑引擎 + 协作系统
```

### 5. AI 品牌视觉生成器
```
你是一个品牌设计 SaaS 产品专家。

任务：构建一个 AI 品牌视觉生成器，5 分钟生成完整品牌视觉系统。

功能：
1. 品牌输入（名称、行业、价值观、目标用户）
2. Logo 生成（多风格：极简/复古/科技/手绘，带 SVG 导出）
3. 配色方案（主色+辅色+强调色，WCAG 对比度检查）
4. 字体推荐（中英文搭配，Google Fonts 集成）
5. 应用场景预览（名片/社交媒体/网站/包装）
6. 品牌手册导出（PDF，使用 Puppeteer）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Canvas API
- AI：DALL-E 3 / Stable Diffusion（图像生成）+ LLM（品牌策略）
- 后端：Next.js API Routes + Supabase
- 导出：Puppeteer（PDF）+ Sharp（图像处理）

设计要求：
- 使用 Bento Grid 展示品牌资产
- 色彩：纯净白底 + 品牌色点缀
- 字体：Space Grotesk（标题，几何感）+ DM Sans（正文）
- 插画：使用 Undraw 风格自定义插画
- 动效：页面元素交错进入（Framer Motion）
- 微交互：颜色选择器带实时预览

输出：完整的品牌生成器 + 资产管理系统 + PDF 导出
```

### 6. AI 独立游戏开发助手
```
你是一个游戏开发工具产品专家。

任务：构建一个 AI 驱动的独立游戏开发助手。

功能：
1. 游戏设计文档生成（基于一句话描述）
2. 剧情与对话生成（带分支选项和角色一致性）
3. 像素画/图标生成（风格统一，支持 sprite sheet）
4. 代码生成（Unity C# / Godot GDScript / 纯 JS）
5. 关卡设计建议（难度曲线、敌人配置）
6. 测试用例生成（功能测试/平衡性测试）
7. 资源导出（PNG/WAV/JSON，支持主流引擎）

技术栈：
- 前端：Electron + React + TypeScript + Tailwind + shadcn/ui
- 后端：FastAPI + Redis（缓存生成结果）
- AI：多模型协作（剧情用创意模型，代码用代码模型）
- 集成：Unity/Godot CLI 工具 + Aseprite（像素画）

设计要求：
- 使用游戏化 UI（像素风按钮、8-bit 图标）
- 色彩：深色主题 + 霓虹色点缀（赛博朋克风）
- 字体：Press Start 2P（标题像素风）+ Inter（正文）
- 图标：使用 Phosphor Icons（游戏相关图标）
- 插画：使用 8-bit 风格像素插画
- 动效：CRT 扫描线效果、像素化过渡

输出：完整的游戏开发工作台 + AI 生成引擎 + 资源导出
```

---

## 8.3 开发者工具新范式

### 7. AI 全栈项目生成器
```
你是一个全栈开发工具产品专家。

任务：构建一个 AI 全栈项目生成器，输入自然语言描述，输出完整可运行项目。

功能：
1. 自然语言解析（提取技术栈、功能需求、设计偏好）
2. 项目脚手架生成（目录结构 + 配置文件）
3. 代码生成（前端/后端/数据库/测试）
4. 设计系统应用（自动应用 Tailwind + shadcn/ui 组件）
5. 一键部署（Vercel/Railway/Netlify）
6. 迭代修改（自然语言描述修改，自动 diff 和 apply）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui
- AI：Claude 3.5 Sonnet（代码生成）+ GPT-4o（需求理解）
- 后端：FastAPI + LangChain（编排）
- 数据库：PostgreSQL + Prisma
- 部署：Vercel SDK + Railway SDK

设计要求：
- 使用分屏布局（左侧输入，右侧实时预览）
- 色彩：中性灰底 + 绿色成功提示（类终端风格）
- 字体：JetBrains Mono（代码）+ Inter（UI）
- 图标：Lucide 图标（开发相关）
- 插画：使用 Open Doodles 开发者风格插画
- 动效：代码生成时的打字机效果

输出：完整的项目生成器 + 实时预览 + 部署系统
```

### 8. AI 数据库设计助手
```
你是一个数据库工具产品专家。

任务：构建一个 AI 数据库设计助手，从自然语言生成完整数据库方案。

功能：
1. 需求理解（自然语言描述业务场景）
2. ER 图自动生成（Mermaid/DBML）
3. SQL 生成（CREATE TABLE + INSERT + 索引建议）
4. 迁移脚本（Alembic/Flyway 格式）
5. 查询优化建议（慢查询分析、索引推荐）
6. 数据模拟（Faker 集成，生成测试数据）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + React Flow
- 后端：FastAPI + SQLAlchemy + Alembic
- AI：LLM（需求转 Schema）+ RAG（数据库最佳实践）
- 数据库：PostgreSQL + pgvector

设计要求：
- 使用 Bento Grid 展示 ER 图和数据表
- 色彩：专业蓝主题（数据库/企业软件风格）
- 字体：Inter（UI）+ JetBrains Mono（SQL 代码）
- 图标：Lucide 数据库/服务器图标
- 插画：使用 Storyset 数据分析风格插画
- 动效：ER 图节点展开动画（Framer Motion）

输出：数据库设计工具 + ER 图编辑器 + SQL 生成器
```

### 9. AI API 网关管理器
```
你是一个 API 管理平台产品专家。

任务：构建一个 AI API 网关管理器，简化 API 的设计、测试和部署。

功能：
1. API 设计（OpenAPI/Swagger 可视化编辑器）
2. 自动文档生成（从代码注释提取）
3. Mock 服务器（基于设计自动生成 Mock 数据）
4. 测试工作台（发送请求、查看响应、断言验证）
5. 监控仪表盘（延迟/错误率/流量/QPS）
6. AI 助手（自然语言查询 API 使用方式）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Monaco Editor
- 后端：FastAPI + Kong/Tyk（网关引擎）
- AI：LLM（API 理解）+ RAG（API 文档库）
- 数据：PostgreSQL + Redis（缓存）+ Prometheus（监控）

设计要求：
- 使用侧边栏布局（类 Postman/Insomnia）
- 色彩：深色主题 + 语法高亮
- 字体：JetBrains Mono（请求/响应代码）
- 图标：Lucide 网络/API 图标
- 插画：使用 Undraw 科技风格插画
- 动效：请求发送时的加载动画

输出：API 网关管理平台 + 可视化编辑器 + 监控系统
```

---

## 8.4 企业级 AI 应用

### 10. AI 客户声音（VoC）分析平台
```
你是一个客户体验产品专家。

任务：构建一个 AI 客户声音分析平台，聚合多源反馈并生成洞察。

数据源：
- 客服对话（电话/聊天/邮件）
- 社交媒体（微博/小红书/抖音评论）
- 应用商店评论
- 问卷调查
- 投诉工单

功能：
1. 情感分析（细粒度：产品/服务/物流/售后）
2. 主题建模（自动发现热点问题）
3. 紧急预警（负面情绪激增）
4. 洞察报告（自动生成周报/月报）
5. 行动建议（基于问题自动建议改进措施）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Tremor（数据可视化）
- 后端：Python + FastAPI + Celery
- AI：LLM + 情感分析 + 主题模型
- 数据：Kafka（实时流）+ ClickHouse（OLAP）

设计要求：
- 使用仪表盘布局（Tremor 组件）
- 色彩：企业蓝主题 + 红色警告色
- 字体：Inter（正文）+ DM Sans（标题）
- 图标：Lucide 图表/分析图标
- 插画：使用 Storyset 数据分析风格插画
- 动效：数据更新时的数字滚动效果

输出：完整的 VoC 分析平台 + 数据管道 + 洞察引擎
```

### 11. AI 销售话术教练
```
你是一个销售科技产品专家。

任务：构建一个 AI 销售话术教练，通过模拟对话提升销售能力。

功能：
1. 角色扮演模拟（AI 扮演客户，模拟真实场景）
2. 实时反馈（话术、节奏、异议处理）
3. 录音分析（语音语调、语速、填充词）
4. 最佳话术推荐（基于 top sales 数据）
5. 个性化训练计划

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + WaveSurfer.js
- 后端：FastAPI + WebSocket
- AI：LLM（对话生成）+ 语音分析模型
- 数据：PostgreSQL + Redis

设计要求：
- 使用分屏布局（左侧对话，右侧反馈）
- 色彩：激励性橙红色调 + 深色背景
- 字体：Inter（UI）+ JetBrains Mono（数据）
- 图标：Lucide 麦克风/图表图标
- 插画：使用 Undraw 会议/销售风格插画
- 动效：反馈面板滑入动画

输出：销售话术教练 + 语音分析 + 训练系统
```

### 12. AI 员工入职助手
```
你是一个 HR Tech 产品专家。

任务：构建一个 AI 员工入职助手，提升新员工入职体验和效率。

功能：
1. 个性化欢迎（基于部门/岗位/背景）
2. 文档自动生成（offer letter、合同、设备申请）
3. 知识库问答（公司政策、IT 设置、团队介绍）
4. 任务追踪（入职 checklist 自动推送）
5. 反馈收集（入职体验调研）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui
- 后端：FastAPI + Workflow 引擎
- AI：LLM + RAG（公司知识库）
- 集成：Slack/Teams + HRIS 系统

设计要求：
- 使用卡片布局展示入职进度
- 色彩：温暖友好的绿色/蓝色调
- 字体：Inter（通用）+ 圆体（中文友好）
- 图标：Lucide HR/团队图标
- 插画：使用 DrawKit 办公室人物插画
- 动效：任务完成时的庆祝动画

输出：入职助手 + 知识库 + 工作流引擎
```

---

## 8.5 创意与设计工具

### 13. AI 品牌视觉生成器
```
你是一个品牌设计产品专家。

任务：构建一个 AI 品牌视觉生成器，5 分钟生成完整品牌视觉系统。

功能：
1. 品牌输入（名称、行业、价值观、目标用户）
2. Logo 生成（多风格变体，带 SVG 导出）
3. 配色方案（主色+辅色+强调色，WCAG 检查）
4. 字体推荐（中英文搭配）
5. 应用场景预览（名片/社交媒体/网站）
6. 品牌手册导出（PDF）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Canvas API
- AI：DALL-E 3 / Stable Diffusion（图像生成）+ LLM（品牌策略）
- 后端：Next.js API Routes + Supabase
- 导出：Puppeteer（PDF）+ Sharp（图像）

设计要求：
- 使用 Bento Grid 展示品牌资产
- 色彩：纯净白底 + 品牌色点缀
- 字体：Space Grotesk（标题）+ DM Sans（正文）
- 插画：使用 Undraw 风格自定义插画
- 动效：页面元素交错进入
- 微交互：颜色选择器带实时预览

输出：完整的品牌生成器 + 资产管理系统
```

### 14. AI 交互式小说引擎
```
你是一个互动娱乐产品专家。

任务：构建一个 AI 交互式小说引擎，让用户成为故事的主角。

功能：
1. 动态剧情生成（基于用户选择和 LLM）
2. 角色一致性保持（记忆系统）
3. 多结局支持（分支树管理）
4. 世界观编辑器（作者工具）
5. 社区功能（分享/游玩/评论）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Framer Motion
- 后端：FastAPI + WebSocket
- AI：LLM（剧情生成）+ 记忆管理
- 存储：PostgreSQL + Redis

设计要求：
- 使用分屏布局（左侧剧情，右侧选项）
- 色彩：神秘紫/深蓝主题 + 金色点缀
- 字体：Crimson Text（小说正文）+ Inter（UI）
- 插画：使用 Storyset 奇幻风格插画
- 动效：翻页效果、选项悬浮动画
- 音效：背景音乐控制面板

输出：交互式小说引擎 + 阅读器 + 作者工具
```

### 15. AI 音乐创作工作室
```
你是一个音乐科技产品专家。

任务：构建一个 AI 音乐创作工作室，降低音乐制作门槛。

功能：
1. 歌词生成（基于主题/情绪/风格）
2. 旋律生成（MIDI，支持多种风格）
3. 和声建议（基于当前旋律）
4. 编曲建议（乐器配置、节奏型）
5. 歌词优化（押韵、节奏、意象）
6. 导出（MIDI/WAV/MP3）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Tone.js
- 后端：FastAPI + Music21 + FFmpeg
- AI：LLM（歌词）+ 音乐生成模型
- 音频：Web Audio API + Tone.js

设计要求：
- 使用深色主题（专业 DAW 风格）
- 色彩：深灰底 + 霓虹色轨道
- 字体：JetBrains Mono（音轨数据）+ Inter（UI）
- 插画：使用 Open Doodles 音乐人风格插画
- 动效：音轨波形动画、播放指针移动
- 微交互：钢琴键盘点击反馈

输出：音乐创作工作台 + AI 生成引擎 + 音频导出
```

---

## 8.6 个人效率与生活方式

### 16. AI 个人财务总监
```
你是一个个人理财产品专家。

任务：构建一个 AI 个人财务总监应用，帮助用户实现财务健康。

功能：
1. 多账户同步（银行/支付宝/微信/证券）
2. 智能分类（消费自动归类）
3. 预算预警（基于消费习惯预测超支）
4. 投资组合分析（风险敞口、再平衡建议）
5. 财务目标规划（买房/退休/教育金）
6. 税务优化建议

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Tremor
- 后端：FastAPI + 财务计算引擎
- AI：LLM（个性化建议）+ 时间序列预测
- 安全：本地加密存储 + 银行级加密

设计要求：
- 使用仪表盘布局（Tremor 图表组件）
- 色彩：金融绿/金色调 + 深色模式
- 字体：Inter（UI）+ JetBrains Mono（数字）
- 图标：Lucide 财务图标
- 插画：使用 DrawKit 金融人物插画
- 动效：数字增长动画、图表过渡

输出：完整的财务仪表盘 + AI 建议引擎 + 目标追踪
```

### 17. AI 旅行规划师
```
你是一个旅行科技产品专家。

任务：构建一个 AI 旅行规划师，生成高度个性化的旅行方案。

功能：
1. 需求理解（预算、时间、兴趣、体力）
2. 智能行程生成（考虑地理 proximity、开放时间）
3. 实时调整（天气/活动/交通变化）
4. 预订集成（酒店/机票/门票）
5. 本地体验推荐（非 tourist trap）
6. 社交分享（精美行程图）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Mapbox
- 后端：FastAPI + 旅行数据 API
- AI：LLM（行程优化）+ 推荐系统
- 地图：Mapbox GL JS

设计要求：
- 使用地图优先布局（全屏地图 + 浮动卡片）
- 色彩：温暖的地中海蓝/白主题
- 字体：Playfair Display（标题，旅行感）+ Inter（正文）
- 图标：Lucide 地图/旅行图标
- 插画：使用 Storyset 旅行风格插画
- 动效：路线动画、卡片滑入

输出：旅行规划器 + 地图集成 + 预订系统
```

### 18. AI 健康饮食管家
```
你是一个健康科技产品专家。

任务：构建一个 AI 健康饮食管家，解决"今天吃什么"和"怎么吃健康"两大问题。

功能：
1. 冰箱扫描（拍照识别现有食材）
2. 菜谱生成（基于食材 + 健康目标）
3. 营养分析（热量、宏量营养素、微量元素）
4. 购物清单自动生成
5. 饮食追踪（拍照记录餐食）
6. 个性化建议（基于体检报告/目标）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui
- 后端：FastAPI + 营养数据库
- AI：视觉识别（食材）+ LLM（菜谱生成）
- 数据库：USDA FoodData Central

设计要求：
- 使用卡片布局展示菜谱
- 色彩：健康绿/橙色调 + 浅色背景
- 字体：Nunito（圆润友好）+ Inter（正文）
- 图标：Lucide 食物/健康图标
- 插画：使用 Open Doodles 健康饮食风格插画
- 动效：食材识别时的扫描动画

输出：健康饮食管家 + 菜谱引擎 + 营养分析
```

---

## 8.7 社会影响力 AI

### 19. AI 残障人士辅助助手
```
你是一个无障碍科技产品专家。

任务：构建一个 AI 辅助工具，帮助视障/听障人士更好地与数字世界交互。

功能模块 A（视障）：
- 屏幕内容实时描述（OCR + 场景理解）
- 导航辅助（室内定位 + 障碍物检测）
- 文档朗读（智能摘要，跳过无关内容）

功能模块 B（听障）：
- 实时字幕（会议/视频/电话）
- 声音警报识别（门铃/火警/婴儿哭）
- 语音转手语动画

技术栈：
- 移动端：React Native + TypeScript + Tailwind
- AI：多模态模型（视觉/听觉）
- 后端：FastAPI + WebSocket
- 硬件：蓝牙信标 + 摄像头

设计要求：
- 使用高对比度主题（无障碍标准）
- 色彩：高对比度黑白 + 强调色
- 字体：大号字体 + 无障碍字体
- 图标：Lucide 无障碍图标
- 插画：使用 Storyset 无障碍风格插画
- 动效：清晰的视觉反馈（振动/闪烁）

输出：无障碍助手 + 多模态交互 + 移动应用
```

### 20. AI 心理健康伴侣
```
你是一个心理健康科技产品专家。

任务：构建一个 AI 心理健康伴侣，提供 7x24 的情感支持。

功能：
1. 情绪追踪（日记 + 表情符号 + 语音语调）
2. 认知行为疗法（CBT）练习
3. 正念与冥想引导
4. 危机干预（识别高风险信号，提供资源）
5. 专业转介（严重情况推荐咨询师）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui
- 后端：FastAPI + 心理健康知识库
- AI：LLM（治疗对话）+ 情绪分析
- 安全：端到端加密 + 匿名化

设计要求：
- 使用柔和圆润的 UI（安全感和温暖）
- 色彩：柔和的蓝紫渐变 + 粉色点缀
- 字体：Quicksand（圆润友好）+ Inter（正文）
- 图标：Lucide 心形/冥想图标
- 插画：使用 DrawKit 心理健康风格插画
- 动效：柔和的浮动动画、呼吸效果

输出：心理健康伴侣 + 情绪追踪 + 治疗对话系统
```

### 21. AI 气候变化行动助手
```
你是一个气候科技产品专家。

任务：构建一个 AI 气候变化行动助手，帮助个人和组织减少碳足迹。

功能：
1. 碳足迹计算器（基于消费/出行/饮食）
2. 减排建议（个性化、可落地）
3. 绿色替代推荐（产品/服务/出行方式）
4. 社群挑战（团队减排竞赛）
5. 企业碳管理（Scope 1/2/3 报告）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Tremor
- 后端：FastAPI + 碳计算引擎
- AI：LLM（个性化建议）+ 推荐系统
- 数据：公开碳因子数据库

设计要求：
- 使用数据可视化布局（Tremor 图表）
- 色彩：自然绿/大地色系
- 字体：Inter（通用）+ Playfair Display（标题）
- 图标：Lucide 叶子/地球图标
- 插画：使用 Undraw 环保风格插画
- 动效：树木生长动画（达成目标时）

输出：碳足迹追踪器 + 减排建议引擎 + 社群功能
```

---

## 8.8 未来概念（2026+）

### 22. AI 数字孪生城市
```
你是一个智慧城市产品专家。

任务：设计一个城市级数字孪生平台，用于城市运营模拟与决策支持。

功能：
1. 实时数据接入（交通/能源/人流/环境）
2. 3D 可视化（城市数字孪生）
3. 模拟推演（政策/事件的影响预测）
4. 应急指挥（突发事件响应优化）
5. 长期规划（城市发展规划模拟）

技术栈：
- 3D：Three.js + Cesium（地理空间）
- 后端：Python + 时空数据库
- AI：图神经网络 + 模拟引擎
- 部署：边缘计算 + 云端协同

设计要求：
- 使用全屏 3D 地图布局
- 色彩：深色科技风 + 霓虹数据线
- 字体：Orbitron（科技标题）+ Inter（数据面板）
- 图标：Lucide 网络/数据图标
- 插画：使用自定义 3D 城市模型
- 动效：数据流动粒子效果、热力图渐变

输出：城市数字孪生平台 + 3D 可视化 + 模拟引擎
```

### 23. AI 个人数字孪生
```
你是一个个人 AI 产品专家。

任务：构建一个个人数字孪生系统，作为用户的数字分身。

功能：
1. 知识图谱构建（用户的经历、偏好、关系）
2. 行为预测（基于历史模式）
3. 代理执行（代回复邮件/安排会议）
4. 记忆管理（重要事件/关系/知识持久化）
5. 隐私控制（用户完全掌控数据）

技术栈：
- 前端：Next.js + TypeScript + Tailwind + shadcn/ui + Three.js
- 后端：FastAPI + 知识图谱
- AI：LLM + 长期记忆 + 个性化
- 存储：本地优先 + 端到端加密

设计要求：
- 使用个人主页布局（类 LinkedIn/个人网站）
- 色彩：用户可自定义主题色
- 字体：Inter（通用）+ 用户偏好字体
- 图标：Lucide 用户/记忆图标
- 插画：使用 3D Avatar 作为主角
- 动效：记忆时间线动画、知识图谱可视化

输出：个人数字孪生 + 记忆系统 + 代理引擎
```

---

## 8.9 精选生态系统资源

### 8.9.1 前端组件库

| 库 | 特点 | 适用场景 | 集成方式 |
|----|------|---------|---------|
| shadcn/ui | 可复制粘贴、高度可定制、基于 Radix | 所有 Web 应用 | `npx shadcn-ui@latest add` |
| NextUI | 现代化、动画丰富、React Server Components | 营销站点、SaaS | npm install @nextui-org/react |
| Magic UI | 动效丰富、适合落地页 | 产品官网、着陆页 | npm install magic-ui |
| Tremor | 数据可视化组件 | 仪表盘、分析平台 | npm install @tremor/react |
| React Hook Form + Zod | 表单处理 + 校验 | 所有需要表单的应用 | npm install react-hook-form zod |
| TanStack Query | 服务端状态管理 | 数据密集型应用 | npm install @tanstack/react-query |

### 8.9.2 图标库

| 库 | 特点 | 推荐场景 |
|----|------|---------|
| Lucide | 线性风格、统一、活跃维护 | 通用 UI、SaaS |
| Heroicons | 两种风格（Outline/Solid） | 营销站点、产品界面 |
| Phosphor Icons | 5 种风格、设计系统友好 | 设计系统、品牌产品 |
| Radix Icons | 15px 网格、像素完美 | 精密工具、开发工具 |
| Tabler Icons | 5000+ 图标、 stroke 统一 | 后台系统、数据面板 |

### 8.9.3 插画库

| 库 | 风格 | 适用场景 | 授权 |
|----|------|---------|------|
| Undraw | 简约线条、可定制颜色 | 所有 Web 应用 | MIT |
| Storyset | 场景插画、可动画化 | 营销页面、博客 | 免费需署名 |
| DrawKit | 矢量插画、人物丰富 | SaaS、企业站 | MIT |
| Open Doodles | 手绘风格、个性十足 | 创意项目、博客 | CC0 |
| Glaze | 3D 渲染、现代感 | 产品官网、科技 | 免费需署名 |

### 8.9.4 3D/动效资源

| 资源 | 特点 | 适用场景 |
|------|------|---------|
| Three.js | WebGL 标准库、生态丰富 | 所有 3D Web 应用 |
| React Three Fiber | React 封装、声明式 | React + 3D 项目 |
| @react-three/drei | 常用 3D 组件库 | 快速搭建 3D 场景 |
| @react-three/postprocessing | 后处理效果 | 游戏、产品展示 |
| Framer Motion | 动画库、手势支持 | UI 动画、页面过渡 |
| Lottie | 矢量动画、跨平台 | 加载动画、图标动画 |
| GSAP + ScrollTrigger | 专业级滚动动画 | 营销页面、叙事体验 |

---

## 8.10 Premium Prompt 质量自检清单

每个 Prompt 使用前请确认：

- [ ] **产品属性明确**：有目标用户、核心价值、商业模式
- [ ] **技术栈现代化**：使用 2025-2026 流行技术栈
- [ ] **设计系统完整**：指定了组件库、图标库、插画库、字体
- [ ] **3D/动效有特色**：不是 generic 的 3D，而是有产品个性
- [ ] **有商品价值**：用户愿意付费，或能产生商业价值
- [ ] **可落地性**：能在 4-12 周内做出可演示 MVP
- [ ] **差异化明显**：与现有产品有明显区别
- [ ] **可验证成功**：有明确的成功指标和 MVP 验证方式

---

## 8.11 下一步建议

1. **选择方向**：从 23 个 Premium Prompt 中选择 1-2 个最感兴趣的
2. **生成 MVP**：用对应 Prompt 生成最小可用产品
3. **快速验证**：找 5-10 个目标用户测试，收集反馈
4. **迭代优化**：基于反馈迭代 2-3 个版本
5. **考虑商业化**：选择合适的变现模式

---

*最后更新：2026-03-14*
*版本：v3.0 Premium 产品级*
*配套文档：09-app-directions.md*