# Prompt Engineering 学习文档

> 本系列文档基于 OpenAI、Anthropic、Lilian Weng 等官方/权威资料，以及 awesome-chatgpt-prompts 等开源项目整理而成，面向实际工程应用，兼顾理论、框架与可复用模板。

## 文档结构

| 文件 | 章节 | 说明 |
|------|------|------|
| `00-index.md` | 总目录 | 本文件，快速导航与学习路径 |
| `01-basics.md` | 基础概念 | 术语、发展脉络、多模型对比 |
| `02-design-principles.md` | 设计框架 | ICIO / CRISPE / BROKE / RASCEF + 代码示例 |
| `03-advanced-techniques.md` | 进阶技术 | CoT / ToT / ReAct / RAG / Agent + 项目案例 |
| `04-open-source-templates.md` | 模板实例 | 分类模板 + JSON/YAML 结构化模板 |
| `05-best-practices.md` | 最佳实践 | OpenAI / Anthropic 官方建议 + 多模型适配 |
| `06-anti-patterns.md` | 反模式 | 常见错误 + 练习题与自检清单 |
| `07-tools-resources.md` | 资源 | 工具链 + 视频教程 + 学习路径 |

## 快速导航

- **新手入门**：01 → 02 → 04（先学框架，再套模板）
- **进阶提升**：03 → 05（掌握技术，学习最佳实践）
- **实战调试**：06 → 07（识别错误，选工具验证）
- **查框架**：直接翻到 `02-design-principles.md`
- **找模板**：直接翻到 `04-open-source-templates.md`
- **选技术**：直接翻到 `03-advanced-techniques.md` 的 3.8 决策树

## 学习路径图

```
Week 1: 基础筑基
├── Day 1-2: 01 基础概念（术语 + 发展脉络）
├── Day 3-4: 02 设计框架（ICIO + CRISPE + 七大要素）
└── Day 5-7: 04 模板实例（为 3 个日常场景写 Prompt）

Week 2: 进阶技术
├── Day 8-9: 03 CoT / RAG / ReAct
├── Day 10-11: 03 Agent 模式与决策树
└── Day 12-14: 05 最佳实践 + 06 反模式（重构 Week 1 的 Prompt）

Week 3: 项目实战
├── Day 15-17: 搭建第一个 RAG 应用
├── Day 18-20: 搭建简单 Agent（工具调用）
└── Day 21: 建立个人 Prompt 模板库

Week 4+: 持续精进
├── 07 工具链落地（LangSmith / PromptFoo）
├── 建立评估集，持续迭代
└── 关注社区新动态
```

## 多模型快速对比

| 维度 | GPT-4o / GPT-5 | Claude 3.5 / 4 | Llama 3 / Qwen | 推荐用法 |
|------|-----------------|-----------------|----------------|----------|
| 指令遵循 | 极强，需要精确 | 极强，可给高层目标 | 中等，需明确示例 | GPT 做精确任务；Claude 做长文本；开源做本地私有 |
| 上下文长度 | 128K / 1M | 200K | 8K-128K | 长文档用 Claude / GPT-5 |
| 推理能力 | o1 / o3 系列极强 | Claude 3.5 Sonnet 强 | 依赖模型规模 | 复杂推理优先 Reasoning 模型 |
| 工具调用 | Function Calling 成熟 | Tool Use 成熟 | 依赖框架 | 生产环境两者皆可 |
| 成本 | 中高 | 中 | 低（自托管） | 原型用 GPT；量产按需选型 |
| 本地部署 | 不支持 | 不支持 | 支持（Ollama / vLLM） | 数据敏感场景用开源 |

---

## 使用建议

1. **学习顺序**：按 01 → 07 顺序阅读建立完整体系；
2. **任务查询**：先查 02 选框架，再查 04 找模板，最后用 06 自检；
3. **代码实践**：02 和 03 中均有可运行示例，建议本地执行验证；
4. **模板复用**：04 中所有模板均标注了 `{占位符}`，替换后可直接使用；
5. **持续迭代**：05 的评估流程是工业级 Prompt 管理的核心，建议建立个人评估集。

## 快速参考：Prompt 七大要素

| 要素 | 说明 |
|------|------|
| Role（角色） | 为模型指定专家身份，激活相关知识网络 |
| Context（背景） | 提供任务所需的环境、历史、私有知识 |
| Task（任务） | 用明确动词描述“做什么”，避免模糊 |
| Examples（示例） | 少样本示范输入-输出模式，降低理解门槛 |
| Format（格式） | 指定 JSON / Markdown / XML 等输出结构 |
| Quality & Constraints（质量与约束） | 定义评分标准与禁止项 |
| Thinking Time（思考时间） | 要求模型先推理再作答，提升复杂任务准确率 |

## 常见任务速查表

| 任务类型 | 推荐框架 | 推荐技术 | 参考章节 |
|----------|----------|----------|----------|
| 文本分类 | ICIO | Zero-shot / Few-shot | 02, 03.1 |
| 复杂推理 | CRISPE + CoT | CoT / Self-Consistency | 02, 03.2 |
| 多步任务 | BROKE | Prompt Chaining / Agent | 02, 03.6 |
| 知识问答 | RASCEF + RAG | RAG + CoT | 02, 03.5 |
| 代码生成 | ICIO + Examples | Few-shot + 格式化输出 | 02, 04.1 |
| 内容创作 | CRISPE | Zero-shot + 风格约束 | 02, 04.2 |
| 数据分析 | RASCEF | Few-shot + 结构化输出 | 02, 04.3 |

---

*生成时间：2026-03-14*
*最后扩展：2026-03-14（新增代码示例、项目案例、视频教程、练习题）*
*资料来源：OpenAI Platform Docs、Anthropic Engineering、Lilian Weng's Prompt Engineering、awesome-chatgpt-prompts、dair-ai/Prompt-Engineering-Guide 等*