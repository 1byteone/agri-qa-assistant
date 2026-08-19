# AgriQA Assistant — 智慧农业智能问答系统

> **项目简介**：基于 LangGraph 智能体架构的农业领域 AI 问答原型系统，集成 ChromaDB 私有农业知识库，支持多轮对话记忆、作物诊断、农事日历、政策咨询四大场景化服务。

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 前端 | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion |
| 后端 | Python 3.11, FastAPI, LangGraph, LangChain |
| 数据库 | ChromaDB（向量数据库）, SQLite + aiosqlite（关系数据库） |
| AI | Agnes AI (agnes-2.5-flash), text-embedding-3-small |
| 工具 | MCP (Fetch, Time, Memory), Open-Meteo API, Playwright |
| 设计 | Apple Liquid Glass UI, 深度毛玻璃效果, 响应式布局 |

## 核心贡献

### 1. LangGraph 智能体架构设计
- 实现了 **目标导向型智能体** 的五层架构：Domain Guard → Query Router → RAG Pipeline → LLM Generation → Answer Post-processing
- 设计 **6 个农业工具**：作物知识查询、生长周期计算、农事天气、网页内容获取、农业资源搜索、时间查询
- 实现 **SSE 流式协议**，16 种事件类型（mode, delta, tool, trace, sources, ui, guard 等），支持实时前端渲染

### 2. RAG Fusion 检索管道
- 构建 **多策略检索管道**：Query Refinement → Subquery Decomposition → Parallel Retrieval → RRF Fusion → Parent-Child Context Recovery → Citation Insertion
- 实现 **4 种检索策略**：Hybrid（向量+词法+元数据）、Hybrid-metadata、Hybrid-temporal、Pure vector
- 设计 **证据治理框架**：4 级来源注册表（A 级官方 → C 级内部），严格 URL 域验证，高风险主题强制 A 级证据

### 3. 四大场景化服务
- **作物诊断**：结构化症状输入 → 智能诊断 → 证据来源背书
- **农事日历**：基于作物/地区/生长阶段的智能农事安排 + 天气风险评估
- **政策咨询**：惠农政策证据检索，A 级来源背书，可追溯验证
- **RAG 评估工作台**：120 项 P0 评估用例，5 场景覆盖，专家标注工作流

### 4. 评估体系
- 构建 **120 项 P0 评估集**（病虫害诊断 40 项、施肥灌溉 25 项、农时天气 25 项、政策核验 20 项、安全边界 10 项）
- 指标：Recall@K、Citation Coverage、Faithfulness、Safety Coverage
- 专家标注工作流：gold evidence ID 选择 + 4 项质量标记

### 5. Apple Liquid Glass 前端设计
- 深度毛玻璃效果（backdrop-filter: blur(20px) + 半透明层叠）
- 流畅动画（framer-motion 消息入场、按钮悬停、打字机效果）
- 响应式布局（桌面端 1280×800 + 移动端 375×812）
- 侧边栏知识面板、RAG 测试面板、场景服务入口

## 关键指标
- **检索质量**：Recall@K 评估体系，120 项 P0 用例
- **知识库规模**：6 个证据包，覆盖水稻、油菜、脐橙、政策等
- **服务模式**：2 种回答模式（专业/简要），支持 SSE 流式
- **安全机制**：Domain Guard 前置过滤，50+ 农业术语白名单，代码生成强制拦截

## 项目地址
- GitHub: https://github.com/1byteone/agri-qa-assistant
- 演示分支: demo/marketing-kit