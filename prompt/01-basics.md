# 01 基础概念

## 1.1 什么是 Prompt Engineering

**Prompt Engineering**（提示工程），又称 **In-Context Prompting**，是指在**不修改模型权重**的前提下，通过设计、优化和迭代输入文本，引导大型语言模型（LLM）生成期望输出的工程学科。

2025 年的标准定义可精炼为：

> 提示工程是一门通过系统性地设计、构建和优化与大型语言模型交互的指令（提示），以实现对其行为（如准确性、风格、安全性）的精确控制，并充分挖掘其在新任务上零样本或少样本学习能力的工程学科。

**核心比喻**：把 LLM 当作一位才华横溢但缺乏具体领域知识的实习生，Prompt Engineer 则是经验丰富的项目经理——不修改实习生的“大脑结构”，而是通过清晰的任务描述、详尽的背景资料、具体的成功范例和严格的质量标准，确保其高效、准确地完成复杂工作。

## 1.2 核心术语

| 术语 | 英文 | 说明 |
|------|------|------|
| Prompt | 提示词 | 输入给模型的文本指令 |
| System Prompt | 系统提示 | 设定模型身份、规则、风格的顶层指令，优先于用户输入 |
| Context Window | 上下文窗口 | 模型单次能处理的最大 Token 数 |
| Token | 词元 | 模型处理文本的基本单位，通常 ≈ 0.75 个英文单词 |
| Hallucination | 幻觉 | 模型生成看似合理但事实错误的内容 |
| Few-shot | 少样本 | 在 Prompt 中提供若干输入-输出示例 |
| Zero-shot | 零样本 | 不提供示例，直接要求模型完成任务 |
| RAG | 检索增强生成 | 从外部知识库检索内容注入 Prompt |
| CoT | 链式思考 | 要求模型逐步推理再给出答案 |
| Temperature | 温度 | 控制输出随机性的参数，0 为确定性，1 为高随机 |

## 1.3 发展脉络

```
2020  GPT-3 发布，In-Context Learning 概念确立
2021  Chain-of-Thought (CoT) 提出，推理能力大幅提升
2022  ChatGPT 发布，RLHF 让模型更安全、更听话
2023  GPT-4 / Claude 3 / Llama 2 多模态与长上下文
2024  o1 / Claude 3.5 Sonnet 推理模型（Reasoning Models）兴起
2025  Prompt Caching / MCP / Agentic Workflow 成为生产标配
2026  ...
```

## 1.4 Prompt Engineering 与模型优化的关系

| 技术 | 成本 | 速度 | 深度 | 适用场景 |
|------|------|------|------|----------|
| Prompt Engineering | 极低 | 分钟级 | 浅层控制 | 快速迭代、任务级定制 |
| PEFT / LoRA | 中 | 小时级 | 中等 | 稳定领域风格注入 |
| Full Fine-tuning | 高 | 天级 | 深层 | 全量领域知识迁移 |
| RLHF | 极高 | 周/月级 | 基础对齐 | 模型厂商出厂配置 |

**结论**：Prompt Engineering 是离应用最近、最灵活的层，应作为默认起点；效果不足时，再向上叠加 PEFT 或 Fine-tuning。

## 1.5 典型应用场景

- **文本生成**：写作辅助、营销文案、邮件撰写
- **代码生成**：函数实现、代码审查、测试用例
- **信息提取**：NER、摘要、结构化数据抽取
- **问答系统**：RAG + 检索增强
- **Agent / 工具调用**：让模型自主规划、调用 API、执行任务
- **安全合规**：内容审核、隐私过滤、红队测试

## 1.6 主流模型特性对比

| 维度 | GPT-4o / GPT-5 | Claude 3.5 / 4 | Llama 3 / Qwen | DeepSeek |
|------|-----------------|-----------------|----------------|----------|
| 开发商 | OpenAI | Anthropic | Meta / 阿里 | 深度求索 |
| 上下文长度 | 128K / 1M | 200K | 8K-128K | 64K-128K |
| 指令遵循 | 极强，需精确指令 | 极强，可给高层目标 | 中等，需明确示例 | 强，中文友好 |
| 推理能力 | o1 / o3 系列极强 | Claude Sonnet 强 | 依赖模型规模 | 数学/代码强 |
| 工具调用 | Function Calling 成熟 | Tool Use 成熟 | 依赖框架 | 支持 |
| 多模态 | 原生支持图片/语音 | 原生支持图片 | 部分支持 | 部分支持 |
| 成本 | 中高 | 中 | 低（自托管） | 低 |
| 本地部署 | 不支持 | 不支持 | 支持（Ollama） | 支持 |
| 中文能力 | 强 | 强 | Qwen 极强 | 极强 |
| 最佳用途 | 精确任务、复杂推理 | 长文本、写作、分析 | 本地私有、定制化 | 中文场景、代码、数学 |

**选型建议**：
- **原型验证**：GPT-4o 或 Claude 3.5 Sonnet（API 稳定，效果可预期）
- **量产文本**：GPT-4o（速度快，成本可控）
- **长文档处理**：Claude 3.5 Sonnet（200K 上下文）
- **中文场景**：DeepSeek / Qwen（中文优化好，成本低）
- **数据敏感/离线**：Llama 3 / Qwen（本地部署）
- **复杂推理/数学**：o1 / DeepSeek-R1（推理模型）

## 1.7 Prompt Engineering 的学习曲线

```
 beginner
  │
  │  ① 学会用 ICIO 框架写清晰指令
  │  ② 掌握 Zero-shot vs Few-shot
  │  ③ 能识别明显的 bad prompt
  │
 intermediate
  │
  │  ④ 熟练使用 CoT / Self-Consistency
  │  ⑤ 搭建第一个 RAG 系统
  │  ⑥ 构建简单 Agent（工具调用）
  │
 advanced
  │
  │  ⑦ 设计多步 Agent Workflow
  │  ⑧ 建立 PromptOps 流程（版本/评估/监控）
  │  ⑨ 针对不同模型做 Prompt 适配
  │
 expert
  │
  └── ⑩  Automatic Prompt Design / 领域微调结合
```

每个阶段的核心标志：
- **Beginner → Intermediate**：能独立完成一个有实际价值的 AI 应用
- **Intermediate → Advanced**：能稳定输出高质量结果，有评估集监控
- **Advanced → Expert**：能针对不同模型特性做深度适配，设计复杂 Agent 系统