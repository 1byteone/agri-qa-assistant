# AgriQA Assistant — Pitch Deck

## Slide 1: 封面
**AgriQA Assistant — 智慧农业智能问答系统**
基于 LangGraph 智能体架构的农业知识服务平台
江西农业大学 · 2026

---

## Slide 2: 问题
**农业技术知识获取困难**
- 农业技术知识分散在各类文档、政策、标准中
- 农民难以快速获取专业的农技指导
- 传统搜索工具缺乏对农业领域术语的理解
- 政策信息更新频繁，难以及时获取

---

## Slide 3: 解决方案
**AI 驱动的智能问答系统**
- 私有农业知识库 → 专业可靠
- 多轮对话记忆 → 上下文连续
- 场景化服务 → 精准匹配
- 证据溯源 → 有据可查

---

## Slide 4: 技术架构
**LangGraph + ChromaDB + FastAPI + Next.js**

```
前端 (Next.js + shadcn/ui + Liquid Glass)
    ↓ HTTP/SSE
后端 (FastAPI + LangGraph Agent)
    ↓
知识库 (ChromaDB + 多策略检索)
    ↓
AI (Agnes AI + MCP 工具)
```

---

## Slide 5: 智能对话
**SSE 流式响应 + 决策卡**
- 实时流式回答
- 结构化决策卡（结论、诊断、行动方案、风险边界）
- 知识溯源与引用来源
- 专业词条释义

---

## Slide 6: 作物诊断
**结构化诊断服务**
- 症状输入 → 智能诊断 → 证据背书
- 覆盖作物、病虫害、生长阶段
- 安全边界检查

---

## Slide 7: 农事日历
**智能农事规划**
- 基于作物、地区、生长阶段
- 天气风险评估
- 可执行农事安排

---

## Slide 8: 政策咨询
**政策证据检索**
- A 级来源背书
- 可追溯、可验证
- 覆盖惠农政策、补贴、法规

---

## Slide 9: RAG 评估
**检索质量保障**
- 120 项 P0 评估用例
- 5 场景覆盖
- 专家标注工作流
- 量化指标：Recall@K、Citation Coverage

---

## Slide 10: 试点管理
**用户管理与分析**
- 三种角色：教师、农技员、农户
- 会话统计与满意度分析
- 反馈收集

---

## Slide 11: 江农集成
**江西农业大学品牌**
- 科研成果展示面板
- 校徽、校训、品牌色
- 新闻动态

---

## Slide 12: 技术差异化
**核心优势**
- RAG Fusion 多策略检索
- 证据治理框架
- Domain Guard 安全过滤
- 专业词条注释
- Apple Liquid Glass UI

---

## Slide 13: 演示
**产品演示视频**
[嵌入演示视频/GIF]

---

## Slide 14: 路线图
**下一步计划**
- 实时农产品价格 API
- 图片上传（病虫害识别）
- 语音输入/输出
- 用户认证与多用户隔离
- Docker 部署
- 移动端 App

---

## Slide 15: 团队
**江西农业大学 · 农业智能技术研究团队**
致力于将人工智能技术应用于农业领域，提升农业生产效率和质量。

---

## Slide 16: 联系
**了解更多**
- GitHub: https://github.com/1byteone/agri-qa-assistant
- 演示分支: demo/marketing-kit
- 文档: docs/landing-page.html