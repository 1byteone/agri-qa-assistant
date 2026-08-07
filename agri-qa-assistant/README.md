# AgriQA Assistant - 农业智能问答原型系统

基于《第2章_构建智能体》构建的面向农业领域的智能问答原型系统，采用 LangGraph 目标导向型智能体架构，集成 ChromaDB 私有农业知识库，支持多轮对话记忆，并配备 Apple Liquid Glass 风格的高颜值前端界面。

## 核心特性

- **专业农业知识库**：覆盖作物种植、病虫害防治、施肥灌溉、土壤管理、农机具使用等综合农技知识
- **多轮对话记忆**：基于 SQLite 持久化存储对话历史，支持上下文连续性
- **私有知识库优先**：优先检索 ChromaDB 向量数据库，确保答案专业可靠
- **引导式兜底策略**：知识库无结果时诚实告知，并提供一般性解答建议
- **Apple Liquid Glass UI**：深度毛玻璃效果、半透明层叠、动态光效、iOS 风格动画
- **MCP 工具集成**：支持开源 MCP 服务（Fetch、Time、Memory）

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端：Next.js + shadcn/ui                  │
│   Apple Liquid Glass 风格聊天界面                            │
│   - 毛玻璃消息卡片                                            │
│   - 圆角输入框 + SF 风格字体                                   │
│   - 打字机效果 + 流式响应                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/SSE
┌───────────────────────────▼─────────────────────────────────┐
│                  后端：FastAPI + LangGraph                    │
│   - Agent 路由层：意图识别 → RAG / 通用 / 工具                 │
│   - Memory 层：SQLite 持久化对话历史                          │
│   - RAG 层：ChromaDB + 农业知识库                             │
│   - Tools 层：MCP Fetch / Time + 农业工具                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      外部服务                                 │
│   - LLM：Agnes AI (agnes-2.0-flash)                          │
│   - Embedding：Agnes AI embedding 模型                       │
│   - 向量数据库：ChromaDB (本地持久化)                          │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- pip / npm

### 1. 克隆项目

```bash
cd d:\code\codeByCursor\AI_EXAM\agri-qa-assistant
```

### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件，填入 Agnes AI API Key

# 启动服务
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

### 4. 访问应用

打开浏览器访问 `http://localhost:3000`

## 环境配置

### 后端环境变量 (.env)

```env
# LLM 配置（必填）
AGNES_AI_API_KEY=sk-your-agnes-api-key
AGNES_AI_BASE_URL=https://apihub.agnes-ai.cn
AGNES_AI_CHAT_MODEL=agnes-2.0-flash
AGNES_AI_EMBEDDING_MODEL=text-embedding-3-small

# 数据库配置
CHROMA_PERSIST_DIR=./data/chroma_db
SQLITE_DB_URL=sqlite+aiosqlite:///./data/agri_qa.db

# MCP 服务
MCP_FETCH_ENABLED=true
MCP_TIME_ENABLED=true
MCP_MEMORY_ENABLED=false
```

## 知识库管理

### 初始化默认知识库

首次启动后端时，系统会自动初始化默认农业知识库，包含：
- 作物种植技术（水稻、小麦、玉米）
- 病虫害防治（稻飞虱、小麦锈病、玉米螟、蚜虫）
- 肥料施用（氮磷钾肥、测土配方、叶面肥）
- 土壤管理（土壤改良、节水灌溉）
- 农机具（旋耕机、植保无人机）

### 添加自定义知识

```python
from knowledge_base import knowledge_base

# 添加文档
documents = [
    Document(
        page_content="你的农业知识内容...",
        metadata={"category": "crop", "crop": "蔬菜", "topic": "planting"}
    )
]
knowledge_base.add_documents(documents)

# 或添加纯文本
knowledge_base.add_texts(
    ["文本内容1", "文本内容2"],
    metadatas=[{"category": "crop"}, {"category": "pest"}]
)
```

## API 接口

### POST /chat
多轮对话接口

**请求体：**
```json
{
  "message": "水稻稻飞虱怎么防治？",
  "thread_id": "thread_001",
  "user_id": "user_123"
}
```

**响应体：**
```json
{
  "thread_id": "thread_001",
  "message": "稻飞虱是水稻主要害虫...",
  "tool_calls": [{"name": "query_crop_knowledge", "args": {...}}],
  "timestamp": "2025-01-15T10:30:00"
}
```

### GET /history/{thread_id}
获取对话历史

### DELETE /history/{thread_id}
清空对话历史

### GET /knowledge-base/status
知识库状态

### GET /health
健康检查

## MCP 服务配置

### 已集成的开源 MCP 服务

| 服务 | 用途 | 状态 |
|------|------|------|
| mcp-server-fetch | 网页内容获取 | ✅ 已启用 |
| mcp-server-time | 时间/时区查询 | ✅ 已启用 |
| mcp-server-memory | 知识图谱记忆 | ⏸️ 可选 |

### 安装 MCP 服务（可选）

```bash
# 使用 uvx 运行（推荐）
uvx mcp-server-fetch
uvx mcp-server-time

# 或使用 pip 安装
pip install mcp-server-fetch mcp-server-time
```

## 前端特性

### Apple Liquid Glass 设计元素

- **毛玻璃背景**：`backdrop-filter: blur(20px)` + 半透明背景
- **圆角卡片**：`rounded-2xl` / `rounded-3xl`
- **柔和阴影**：多层阴影模拟 iOS 浮层效果
- **流畅动画**：framer-motion 实现消息入场、按钮悬停
- **iOS 风格输入框**：内阴影 + 聚焦光效
- **SF 字体栈**：`-apple-system, BlinkMacSystemFont`

### 交互细节

- 消息气泡圆角适配（用户右圆角小，助手左圆角小）
- 自动滚动到底部
- Enter 发送，Shift+Enter 换行
- 加载状态动画
- 建议问题快捷按钮

## 项目结构

```
agri-qa-assistant/
├── backend/
│   ├── main.py              # FastAPI 主应用
│   ├── agent.py             # LangGraph Agent
│   ├── knowledge_base.py    # ChromaDB 知识库
│   ├── memory.py            # SQLite 持久化记忆
│   ├── tools.py             # 农业工具 + MCP 工具
│   ├── config.py            # 配置管理
│   ├── schemas.py           # Pydantic 模型
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 环境变量模板
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # 主页面
│   │   ├── layout.tsx       # 根布局
│   │   └── globals.css      # Apple Liquid Glass 样式
│   ├── components/
│   │   └── chat-interface.tsx  # 聊天界面
│   ├── lib/utils.ts         # 工具函数
│   ├── tailwind.config.ts   # Tailwind 配置
│   ├── next.config.js       # Next.js 配置
│   └── package.json         # Node.js 依赖
└── data/
    └── knowledge_base/      # ChromaDB 持久化数据
```

## 常见问题

### Q: 后端启动失败，提示找不到模块
A: 确保在虚拟环境中安装了所有依赖：`pip install -r requirements.txt`

### Q: 前端无法连接后端
A: 检查 `next.config.js` 中的 rewrites 配置，确保后端运行在 `localhost:8000`

### Q: 知识库为空
A: 首次启动时会自动初始化，如果失败可手动调用 `init_default_knowledge_base()`

### Q: 如何添加更多农业知识
A: 编辑 `knowledge_base.py` 中的 `default_docs` 列表，或通过代码调用 `knowledge_base.add_documents()`

## 下一步计划

- [ ] 集成实时农产品价格 API
- [ ] 支持图片上传（病虫害识别）
- [ ] 添加语音输入/输出
- [ ] 用户认证和多用户隔离
- [ ] 导出对话记录
- [ ] 部署到 Docker

## 基于文档

本项目基于《第2章_构建智能体.ipynb》中的 LangChain/LangGraph 智能体架构开发，核心代码模式遵循文档中的 `create_agent` 五层架构。

## License

MIT