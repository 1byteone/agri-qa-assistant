# 02 设计原则与框�?

## 2.1 ICIO 框架

最简单的结构化提示框架，适合快速上手�?

| 要素 | 说明 | 示例 |
|------|------|------|
| Instruction（指令） | 明确的任务动�?| "提取以下文本中的关键实体" |
| Context（背景） | 任务相关的前置信�?| "这是一�?2025 年财�?.." |
| Input Data（输入数据） | 待处理的具体内容 | 附上财报原文 |
| Output Indicator（输出指示） | 期望的输出格�?| "�?JSON 数组返回" |

**模板**�?
```
你是{角色}�?
{背景信息}
请执行以下任务：{任务描述}
输入：{输入数据}
输出要求：{格式与约束}
```

## 2.2 CRISPE 框架

更强调角色设定和示例引导�?

- **C**apacity and Role：模型扮演什么角�?
- **R**elevant Background：提供充足背�?
- **I**nstruction：具体任务描�?
- **S**tyle and Format：输出风格与格式
- **P**rovide Examples：给出示�?
- **E**valuate and Refine：评估并迭代优化

## 2.3 BROKE 框架

面向迭代优化场景�?

- **B**ackground：背景信�?
- **R**ole：角色定�?
- **O**bjectives：具体目�?
- **K**ey Points：关键关注点
- **E**volve：根据输出改�?Prompt

## 2.4 RASCEF 框架

适合角色扮演和复杂任务执行�?

- **R**ole：角�?
- **A**ction：具体行�?
- **S**teps：详细步�?
- **C**ontext：背�?
- **E**xamples：示�?
- **F**ormat：输出格�?

## 2.5 七大要素（综合版�?

将上述框架整合为通用检查清单：

1. **Role（角色）**：明确具体，�?15 年经验的量子计算 MIT 教授"，而非模糊�?专家"
2. **Context（背景）**：前置关键信息，用分隔符（`"""` / XML 标签）与指令区分
3. **Task（任务）**：用指令动词开头，复杂任务拆解为步�?
4. **Examples（示例）**：质�?> 数量，格式严格一�?
5. **Format（格式）**：直接要�?JSON / Markdown / XML，最好附带空模板
6. **Quality & Constraints（质量与约束�?*：量化指�?+ 负向约束
7. **Thinking Time（思考时间）**：要�?`<thinking>...</thinking>` + `<answer>...</answer>`

**示例对比**�?

�?Prompt�?
```
总结一下黑洞是什么�?
```

�?Prompt�?
```
# Role
你是天体物理学家，也是出色的科普教育家，擅长向青少年解释复杂宇宙概念�?

# Context
受众�?4-16 岁中学生，无专业物理背景�?

# Task
请解释什么是黑洞，使用生动比喻，避免专业术语�?

# Format
- 长度�?50 字以�?
- 结构�? 个核心比�?+ 1 句现实类�?

# Thinking Time
先在 <thinking> 内列�?2-3 个候选比喻，再在 <answer> 内输出最终答案�?
```

## 2.6 设计原则总结

| 原则 | 做法 | 反例 |
|------|------|------|
| 具体而非模糊 | "提取姓名、邮箱、电�? | "提取信息" |
| 正面指令 | "使用正式商务语气" | "不要太随�? |
| 结构�?| Markdown 标题 + XML 标签 | 一大段无分隔文�?|
| 示例先行 | 提供 2-3 个高质量示例 | 仅靠文字描述 |
| 格式模板 | 给出�?JSON 模板 | 仅说"返回结构化数�? |
| 思考空�?| 要求逐步推理 | 直接要答�?|
| 版本管理 | �?Prompt 存入代码�?| 仅存在于聊天窗口 |

## 2.7 代码示例：Python / TypeScript 调用（Agnes AI 国内默认�?

以下代码默认使用 **Agnes AI** 国内地址，优先读取系统环境变量�?

**Python（OpenAI SDK + 国内地址�?*�?
```python
import os
from openai import OpenAI

# 优先读取环境变量；兼容完�?endpoint 或基础 URL
AGNES_API_KEY = os.getenv("AGNES_AI_API_KEY", os.getenv("AGNES_API_KEY", ""))
_raw_base = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.cn/v1")
AGNES_BASE_URL = _raw_base.rsplit("/chat/completions", 1)[0] if "/chat/completions" in _raw_base else _raw_base
AGNES_MODEL = os.getenv("AGNES_AI_MODEL", "agnes-2.0-flash")

if not AGNES_API_KEY:
    raise EnvironmentError("请设�?AGNES_AI_API_KEY �?AGNES_API_KEY 环境变量")

client = OpenAI(
    api_key=AGNES_API_KEY,
    base_url=AGNES_BASE_URL
)

response = client.chat.completions.create(
    model=AGNES_MODEL,
    messages=[
        {"role": "system", "content": "你是一个专业的代码审查员�?},
        {"role": "user", "content": "请审查以下代码：\n\n```python\ndef add(a, b):\n    return a + b\n```"}
    ]
)

print(response.choices[0].message.content)
```

**TypeScript（OpenAI SDK�?*�?
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.AGNES_AI_API_KEY || process.env.AGNES_API_KEY,
  baseURL: process.env.AGNES_BASE_URL || "https://apihub.agnes-ai.cn/v1"
});

const response = await client.chat.completions.create({
  model: "agnes-2.0-flash",
  messages: [
    { role: "system", content: "你是一个专业的代码审查员�? },
    { role: "user", content: "请审查以下代�?.." }
  ]
});

console.log(response.choices[0].message.content);
```

**关键区别**�?
- OpenAI SDK：用 `client.chat.completions.create`，`base_url` 只需要基础地址，SDK 自动追加 `/chat/completions`
- Anthropic SDK：用独立�?`system` 参数，`messages` 中只�?`user` / `assistant`
- 两者都支持多轮对话，通过维护消息数组实现
