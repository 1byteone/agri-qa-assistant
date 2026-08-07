# 02 设计原则与框架

## 2.1 ICIO 框架

最简单的结构化提示框架，适合快速上手。

| 要素 | 说明 | 示例 |
|------|------|------|
| Instruction（指令） | 明确的任务动词 | "提取以下文本中的关键实体" |
| Context（背景） | 任务相关的前置信息 | "这是一份 2025 年财报..." |
| Input Data（输入数据） | 待处理的具体内容 | 附上财报原文 |
| Output Indicator（输出指示） | 期望的输出格式 | "以 JSON 数组返回" |

**模板**：

**Python（OpenAI SDK）**：
```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "developer", "content": "你是{角色}。"},
        {"role": "developer", "content": "{背景信息}"},
        {"role": "user", "content": "请执行以下任务：{任务描述}\n输入：{输入数据}\n输出要求：{格式与约束}"}
    ]
)

print(response.output_text)
```

**TypeScript（OpenAI SDK）**：
```typescript
import OpenAI from "openai";

const client = new OpenAI();

const response = await client.responses.create({
  model: "gpt-4o",
  input: [
    { role: "developer", content: "你是{角色}。" },
    { role: "developer", content: "{背景信息}" },
    { role: "user", content: "请执行以下任务：{任务描述}\n输入：{输入数据}\n输出要求：{格式与约束}" }
  ]
});

console.log(response.output_text);
```

**Python（Anthropic SDK）**：
```python
from anthropic import Anthropic

client = Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是{角色}。\n\n{背景信息}",
    messages=[
        {"role": "user", "content": "请执行以下任务：{任务描述}\n输入：{输入数据}\n输出要求：{格式与约束}"}
    ]
)

print(message.content[0].text)
```

**关键区别**：
- OpenAI：用 `developer` 角色传递系统指令，`user` 角色传用户输入
- Anthropic：用独立的 `system` 参数，`messages` 中只有 `user` / `assistant`
- 两者都支持多轮对话，通过维护消息数组实现

## 2.2 CRISPE 框架

更强调角色设定和示例引导。

- **C**apacity and Role：模型扮演什么角色
- **R**elevant Background：提供充足背景
- **I**nstruction：具体任务描述
- **S**tyle and Format：输出风格与格式
- **P**rovide Examples：给出示例
- **E**valuate and Refine：评估并迭代优化

## 2.3 BROKE 框架

面向迭代优化场景。

- **B**ackground：背景信息
- **R**ole：角色定义
- **O**bjectives：具体目标
- **K**ey Points：关键关注点
- **E**volve：根据输出改进 Prompt

## 2.4 RASCEF 框架

适合角色扮演和复杂任务执行。

- **R**ole：角色
- **A**ction：具体行动
- **S**teps：详细步骤
- **C**ontext：背景
- **E**xamples：示例
- **F**ormat：输出格式

## 2.5 七大要素（综合版）

将上述框架整合为通用检查清单：

1. **Role（角色）**：明确具体，如"15 年经验的量子计算 MIT 教授"，而非模糊的"专家"
2. **Context（背景）**：前置关键信息，用分隔符（`"""` / XML 标签）与指令区分
3. **Task（任务）**：用指令动词开头，复杂任务拆解为步骤
4. **Examples（示例）**：质量 > 数量，格式严格一致
5. **Format（格式）**：直接要求 JSON / Markdown / XML，最好附带空模板
6. **Quality & Constraints（质量与约束）**：量化指标 + 负向约束
7. **Thinking Time（思考时间）**：要求 `<thinking>...</thinking>` + `<answer>...</answer>`

**示例对比**：

弱 Prompt：
```
总结一下黑洞是什么。
```

强 Prompt：
```
# Role
你是天体物理学家，也是出色的科普教育家，擅长向青少年解释复杂宇宙概念。

# Context
受众：14-16 岁中学生，无专业物理背景。

# Task
请解释什么是黑洞，使用生动比喻，避免专业术语。

# Format
- 长度：150 字以内
- 结构：1 个核心比喻 + 1 句现实类比

# Thinking Time
先在 <thinking> 内列出 2-3 个候选比喻，再在 <answer> 内输出最终答案。
```

## 2.6 设计原则总结

| 原则 | 做法 | 反例 |
|------|------|------|
| 具体而非模糊 | "提取姓名、邮箱、电话" | "提取信息" |
| 正面指令 | "使用正式商务语气" | "不要太随意" |
| 结构化 | Markdown 标题 + XML 标签 | 一大段无分隔文本 |
| 示例先行 | 提供 2-3 个高质量示例 | 仅靠文字描述 |
| 格式模板 | 给出空 JSON 模板 | 仅说"返回结构化数据" |
| 思考空间 | 要求逐步推理 | 直接要答案 |
| 版本管理 | 将 Prompt 存入代码库 | 仅存在于聊天窗口 |