# AgriQA Assistant - 智慧农业问答系统

## 项目概述

基于 LangGraph 智能体架构的农业智能问答原型系统，集成 ChromaDB 私有农业知识库，支持多轮对话记忆，配备 Apple Liquid Glass 风格的高颜值前端界面。

---

## 核心价值

### 解决什么问题？
- 农业技术知识分散，农民难以获取专业指导
- 传统问答系统缺乏上下文理解能力
- 知识库更新滞后，无法提供实时准确信息

### 我们的解决方案
- **专业农业知识库**：覆盖作物种植、病虫害防治等综合农技知识
- **智能对话系统**：基于 LangGraph 的多轮对话记忆
- **私有知识库优先**：确保答案专业可靠
- **用户体验极致**：Apple Liquid Glass UI 设计

---

## 技术架构

```
前端 (Next.js + shadcn/ui)
    ↓ HTTP/SSE
后端 (FastAPI + LangGraph)
    ↓
外部服务 (Agnes AI + ChromaDB)
```

### 前端技术栈
- **框架**：Next.js 14
- **UI库**：shadcn/ui + Tailwind CSS
- **设计**：Apple Liquid Glass 风格
- **动画**：Framer Motion

### 后端技术栈
- **框架**：FastAPI
- **AI框架**：LangGraph
- **向量数据库**：ChromaDB
- **关系数据库**：SQLite
- **AI模型**：Agnes AI (agnes-2.0-flash)

---

## 核心功能

### 1. 智能问答系统
- 多轮对话记忆
- 上下文连续性
- 专业农业知识检索

### 2. 知识库管理
- 私有农业知识库
- 文档上传与解析
- 向量化存储与检索

### 3. 用户界面
- Apple Liquid Glass 设计
- 响应式布局
- 流畅动画效果

### 4. 工具集成
- MCP 服务支持
- 时间查询
- 网页内容获取

---

## 产品演示

### 场景1：水稻病虫害防治
**用户问题**：水稻稻飞虱怎么防治？

**系统回答**：
1. 识别害虫类型
2. 提供防治方法
3. 给出用药建议
4. 预防措施

### 场景2：施肥指导
**用户问题**：小麦什么时候追肥？

**系统回答**：
1. 生长阶段分析
2. 施肥时间建议
3. 肥料配比推荐
4. 注意事项

---

## 技术亮点

### 1. LangGraph 智能体架构
- 目标导向型智能体
- 五层架构设计
- 工具调用与记忆管理

### 2. ChromaDB 向量检索
- 私有知识库优先
- 语义相似度匹配
- 实时更新支持

### 3. Apple Liquid Glass UI
- 毛玻璃效果
- 半透明层叠
- 动态光效
- iOS 风格动画

### 4. MCP 工具集成
- 开源标准协议
- 可扩展性强
- 跨平台支持

---

## 项目结构

```
agri-qa-assistant/
├── backend/           # FastAPI 后端
│   ├── main.py       # 主应用
│   ├── agent.py      # LangGraph Agent
│   ├── knowledge_base.py  # 知识库
│   └── memory.py     # 对话记忆
├── frontend/          # Next.js 前端
│   ├── app/          # 页面组件
│   ├── components/   # UI组件
│   └── lib/          # 工具函数
└── docs/             # 文档资料
```

---

## 部署指南

### 快速启动
1. 克隆项目
2. 启动后端：`python main.py`
3. 启动前端：`npm run dev`
4. 访问 `http://localhost:3000`

### 环境要求
- Python 3.10+
- Node.js 18+
- Agnes AI API Key

---

## 未来规划

### 短期目标
- [ ] 集成实时农产品价格 API
- [ ] 支持图片上传（病虫害识别）
- [ ] 添加语音输入/输出

### 长期目标
- [ ] 用户认证和多用户隔离
- [ ] 导出对话记录
- [ ] 部署到 Docker
- [ ] 移动端 App 开发

---

## 团队介绍

**江西农业大学** - 农业智能技术研究团队

致力于将人工智能技术应用于农业领域，提升农业生产效率和质量。

---

## 联系方式

- **GitHub**: https://github.com/1byteone/AI_EXAM
- **演示站点**: http://localhost:3000
- **文档**: docs/landing-page.html

---

## 致谢

- LangGraph 团队提供的智能体框架
- ChromaDB 团队提供的向量数据库
- Agnes AI 提供的 AI 模型服务
- 所有开源贡献者

---

**谢谢观看！**
