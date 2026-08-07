# 07 工具链与学习资源

## 7.1 开发与测试工具

| 工具 | 用途 | 说明 |
|------|------|------|
| [OpenAI Playground](https://platform.openai.com/playground) | Prompt 快速迭代 | 可视化调整参数、对比模型 |
| [Claude Console / Workbench](https://console.anthropic.com) | Claude Prompt 测试 | 官方 Workbench 支持工具调用测试 |
| [LangSmith](https://smith.langchain.com) | Prompt 评估与追踪 | LangChain 生态的 PromptOps 工具 |
| [PromptFoo](https://promptfoo.dev) | 开源 Prompt 评估框架 | 本地化、可集成的测试套件 |
| [Helicone](https://helicone.ai) | LLM 请求监控 | 开源，支持延迟、成本、质量追踪 |
| [LiteLLM](https://github.com/BerriAI/litellm) | 统一 API 网关 | 一次接入，切换多模型 |
| [PromptPerfect](https://promptperfect.jina.ai) | 自动优化 Prompt | Jina AI 出品 |

## 7.2 Prompt 管理

- **版本控制**：将 Prompt 作为代码管理，使用 Git + Code Review
- **环境隔离**：开发 / 测试 / 生产 Prompt 分离
- **Feature Flags**：新 Prompt 灰度发布
- **A/B 测试**：对比不同 Prompt 版本的输出质量

## 7.3 评估方法

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| 人工评分 | 专家或众包打分 | 质量要求高的场景 |
| LLM-as-Judge | 用强模型评估弱模型输出 | 大规模自动化评估 |
| 单元测试式 | 针对代码/JSON 做精确校验 | 结构化输出 |
| 回归测试 | 固定测试集定期跑 | 防止 Prompt 变更退步 |
| 对抗测试 | 构造边界 case 攻击模型 | 安全与护栏验证 |

## 7.4 学习资源

### 官方文档
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [OpenAI Cookbook](https://github.com/openai/openai-cookbook)
- [Anthropic Cookbook](https://platform.claude.com/cookbook)

### 经典文章
- [Lilian Weng - Prompt Engineering](https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/)（OpenAI 研究主管的权威综述）
- [Andrej Karpathy - Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY)
- [Andrej Karpathy - Context Engineering](https://karpathy.ai)（2025 年概念）

### 开源项目
- [awesome-chatgpt-prompts](https://github.com/f/awesome-chatgpt-prompts)
- [Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [Learn Prompting](https://learnprompting.org)
- [Awesome-LLM-Prompt-Libraries](https://github.com/danielrosehill/Awesome-LLM-Prompt-Libraries)

### 书籍
- 《The Art of ChatGPT Prompting》（fka.gumroad.com）
- 《Prompt Engineering for Generative AI》（O'Reilly）
- 《Building LLM Applications》（Chris McCrodick, O'Reilly）

### 论文速查

| 论文 | 技术 | 年份 |
|------|------|------|
| GPT-3 (Brown et al.) | In-Context Learning | 2020 |
| Chain-of-Thought (Wei et al.) | CoT | 2022 |
| Self-Consistency (Wang et al.) | 采样聚合 | 2022 |
| ReAct (Yao et al.) | 推理+行动 | 2023 |
| Tree of Thoughts (Yao et al.) | 思维树 | 2023 |
| Reflexion (Shinn et al.) | 自我反思 | 2023 |
| Toolformer (Schick et al.) | 工具调用 | 2023 |
| RAG (Lewis et al.) | 检索增强 | 2020 |

## 7.4 视频教程精选

### 必看系列

1. **[Andrej Karpathy - Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY)**
   - 时长：2 小时
   - 适合：理解 Transformer 和 LLM 底层原理
   - 语言：英文

2. **[Prompt Engineering 完整教程（李宏毅）](https://www.youtube.com/watch?v=xxx)**
   - 时长：1.5 小时
   - 适合：中文用户入门
   - 语言：中文

3. **[Lilian Weng - Prompt Engineering 综述讲解](https://www.youtube.com/watch?v=xxx)**
   - 时长：45 分钟
   - 适合：系统梳理技术脉络
   - 语言：英文

### 进阶视频

4. **[Building Effective Agents - Anthropic 官方讲解](https://www.youtube.com/watch?v=xxx)**
   - 时长：30 分钟
   - 适合：学习 Agent 设计模式
   - 语言：英文

5. **[RAG 从入门到精通（LangChain）](https://www.youtube.com/watch?v=xxx)**
   - 时长：1 小时
   - 适合：实战 RAG 系统
   - 语言：英文

6. **[Prompt Engineering for Developers（DeepLearning.AI）](https://www.youtube.com/watch?v=xxx)**
   - 时长：1 小时
   - 适合：开发者快速上手
   - 语言：英文

### 中文资源

7. **[提示工程入门到精通（B站）](https://www.bilibili.com/video/xxx)**
   - 时长：系列视频
   - 适合：中文用户系统学习
   - 语言：中文

8. **[李沐 - 大模型提示工程精讲](https://www.bilibili.com/video/xxx)**
   - 时长：2 小时
   - 适合：有深度学习基础的学习者
   - 语言：中文

### 学习建议

- **Week 1**：看视频 1（Karpathy）+ 阅读 01 基础概念
- **Week 2**：看视频 3（Lilian Weng）+ 学习 03 进阶技术
- **Week 3**：看视频 5（RAG）+ 实战项目
- **Week 4**：看视频 4（Agents）+ 学习 05 最佳实践

> 注意：视频链接为示例占位符，请根据实际可用的视频资源替换。

## 7.5 推荐学习路径

```
Week 1: 01 + 02
理解基础概念，掌握 ICIO / CRISPE 框架
练习：为日常工作场景写 5 个 Prompt

Week 2: 03
学习 CoT / RAG / ReAct
练习：用 CoT 解决 3 个复杂推理问题

Week 3: 04
收集和改编开源模板
练习：建立自己的 Prompt 模板库

Week 4: 05 + 06
学习最佳实践，识别反模式
练习：对自己 Week 1 的 Prompt 做重构

持续：07
搭建工具链，建立评估集
```

## 7.6 社区与动态

- **Reddit**: r/ChatGPT, r/PromptEngineering
- **Discord**: OpenAI Community, LangChain Discord
- **Twitter/X**: 关注 @OpenAI, @AnthropicAI, @karpathy, @swyx
- **Newsletter**: The Rundown AI, Ben's Bites, Prompt Engineering Daily