# 05 最佳实践

> 综合 OpenAI、Anthropic 官方文档及 Lilian Weng 的权威综述。

## 5.1 OpenAI 官方建议

### 消息角色优先级
```
developer > user > assistant
```

- `developer` 消息：应用开发者的系统级指令，优先级最高
- `user` 消息：最终用户输入，优先级次之
- 类比：developer 如同函数定义，user 如同函数参数

### Developer Message 标准结构
```
# Identity
描述助手的目标、沟通风格、受众

# Instructions
规则、边界、工具调用方式

# Examples
输入-输出示范

# Context
私有数据、检索内容、当前会话信息
```

### 版本化管理
- **不要**使用可复用的 Prompt 对象（2026 年 11 月停用）
- **要**将 Prompt Builder 放在功能附近的小模块中
- **要**使用类型化函数参数传动态值
- **要**在改生产 Prompt 前，先补代表性 fixtures 和测试

### 模型选型
| 模型类型 | 特点 | 适用场景 |
|----------|------|----------|
| Reasoning Models | 内部推理链，适合复杂任务 | 数学证明、多步规划 |
| GPT 系列 | 快速、低成本、需要精确指令 | 通用文本生成 |
| 大模型 | 理解力强、跨域泛化 | 复杂推理、少样本学习 |
| 小模型 | 延迟低、成本低 | 分类、简单抽取 |

## 5.2 Anthropic 官方建议

### Agent 设计三原则
1. **简洁性**：优先用最简方案，仅在需要时增加复杂度
2. **透明性**：显式展示 Agent 的规划步骤
3. **ACI 质量**：工具文档和测试投入 ≥ Prompt 优化投入

### 何时使用 Agent
- 任务步骤数难以预测
- 需要灵活决策
- 环境可信、可沙箱测试
- 不适用：简单单步任务、高延迟敏感场景

### 工具设计（Poka-yoke）
- 优先使用绝对路径而非相对路径
- 参数命名清晰，避免歧义
- 提供示例用法和边界说明
- 在 Workbench 中多次测试，观察模型错误模式

### 工作流选择决策

| 模式 | 特点 | 适用 |
|------|------|------|
| Prompt Chaining | 固定顺序子任务 | 翻译后润色、大纲→正文 |
| Routing | 分类后分发 | 客服分流、模型选型 |
| Parallelization | 并行/投票 | 内容审核、代码审查 |
| Orchestrator-Workers | 动态拆解 | 多文件修改、跨源搜索 |
| Evaluator-Optimizer | 生成-评估循环 | 文学翻译、长文润色 |
| Autonomous Agent | 自主规划 | 开放式问题、长期任务 |

## 5.3 Lilian Weng 核心要点

### Few-shot 示例选择
- 语义相似性优先（embedding k-NN）
- 标签分布均衡
- 顺序随机化

### CoT 有效条件
- 任务复杂度高时效果显著
- 模型规模 > 50B 参数时收益更大
- 简单任务收益有限

### 推理链格式
- 用 `\n` 分隔步骤，优于 `step 1:` 或分号
- `Question:` 比 `Q:` 更有效
- 复杂示例 > 简单示例

### 自我一致性
1. 多次采样（temperature > 0）
2. 选择标准：多数投票 / 可执行验证
3. 可结合示例顺序扰动引入多样性

## 5.3.1 多模型特定最佳实践

### GPT 系列（OpenAI）
```python
# 推荐：使用 developer 角色传递系统指令
response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "developer", "content": system_instructions},
        {"role": "user", "content": user_input}
    ]
)

# 结构化输出推荐用 JSON mode
response = client.responses.create(
    model="gpt-4o",
    input=[...],
    text={
        "format": {
            "type": "json_schema",
            "name": "structured_output",
            "schema": {...}
        }
    }
)
```

**GPT 特定建议**：
- 精确指令比高层目标更有效
- 使用 `developer` 消息而非旧版 `system` 消息
- 复杂任务拆分为多步，每步用独立的 API 调用
- 利用 Prompt Caching：静态内容放最前面

### Claude 系列（Anthropic）
```python
# 推荐：使用独立的 system 参数
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是一个专业的{角色}...",
    messages=[{"role": "user", "content": user_input}]
)
```

**Claude 特定建议**：
- 可以给高层目标和约束，Claude 会自主规划
- 长文本处理能力极强，适合文档分析
- 善用 `thinking` 预算（`thinking={"type": "enabled", "budget_tokens": 10000}`）
- XML 标签对 Claude 特别有效（训练数据中常见）

### 开源模型（Llama / Qwen / DeepSeek）
```python
# 使用 Ollama 本地调用
import requests

response = requests.post("http://localhost:11434/api/generate", json={
    "model": "llama3:70b",
    "prompt": formatted_prompt,
    "stream": False,
    "options": {
        "temperature": 0.7,
        "num_ctx": 8192  # 上下文窗口
    }
})
```

**开源模型特定建议**：
- 指令遵循能力弱于 GPT/Claude，需要更多示例
- 推荐使用 ChatML 或 Llama 指令模板格式
- 本地部署时注意显存限制（7B 模型 ≈ 14GB 显存）
- 中文场景优先选 Qwen 或 DeepSeek

### 模型选择决策矩阵

| 任务特征 | 首选模型 | 备选模型 | 原因 |
|----------|----------|----------|------|
| 精确指令遵循 | GPT-4o | Claude 3.5 | 指令遵循能力强 |
| 长文档分析 | Claude 3.5 Sonnet | GPT-4o | 200K 上下文 |
| 复杂推理/数学 | o1 / DeepSeek-R1 | Claude 3.5 | 推理模型 |
| 代码生成 | GPT-4o | Claude 3.5 | 代码能力强 |
| 中文写作 | DeepSeek / Qwen | GPT-4o | 中文优化好 |
| 成本敏感 | Qwen / DeepSeek | GPT-4o-mini | API 价格低 |
| 数据隐私 | Llama 3 / Qwen | - | 本地部署 |
| 多模态（图片） | GPT-4o | Claude 3.5 | 原生视觉能力 |

## 5.4 上下文窗口管理

### Prompt Caching 优化
- 将重复使用的静态内容放在 Prompt 最前面
- 在 JSON 请求体中靠前的位置传递
- 适用于系统指令、知识库片段、工具定义

### 上下文压缩策略
- 摘要历史对话
- 仅检索最相关片段（RAG Top-K）
- 设置硬性 Token 预算

## 5.5 结构化输出

### JSON 模式
- 明确指定 Schema
- 提供空模板示例
- 接收后做语法校验
- 校验失败时，用"修复提示"让模型自行修正

### Markdown 标准
- 行内代码用反引号
- 代码块用 fences + 语言标签
- 文件路径、函数名、类名用反引号
- 列表、表格提升可读性

## 5.6 安全与护栏

- 在 System Prompt 中植入安全红线
- 对敏感任务添加输出审核层
- 要求模型在不确定时声明 "I don't know"
- 对用户输入做预处理（脱敏、过滤）
- 对模型输出做后处理（PII 检测、合规检查）

## 5.7 评估与监控

### 最小评估集
- 代表性场景覆盖
- 边界 case 与失败模式
- 定期回归测试

### 监控指标
- 输出质量（人工评分 / LLM-as-judge）
- 延迟与 Token 消耗
- 幻觉率（事实性校验）
- 格式合规率

### 迭代流程
```
1. 建立基线（Baseline Prompt）
2. 设计测试集（10-50 cases）
3. 提出改进假设
4. A/B 测试对比
5. 胜出者晋升为基线
6. 重复循环
```