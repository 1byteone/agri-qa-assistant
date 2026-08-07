# 03 进阶技术

## 3.1 Few-Shot Learning（少样本学习）

在 Prompt 中提供若干输入-输出示例，让模型模仿模式。

```
Text: (lawrence bounces) all over the stage, dancing...
Sentiment: positive

Text: despite all evidence to the contrary, this clunker...
Sentiment: negative

Text: i'll bet the video game is a lot more fun than the film.
Sentiment:
```

**示例选择要点**：
- 语义上与待预测样本相似（k-NN 聚类）
- 标签分布均衡，避免 majority label bias
- 顺序随机化，避免 recency bias

## 3.2 Chain-of-Thought（链式思考）

要求模型展示逐步推理过程，显著提升数学、逻辑、代码任务准确率。

### Few-shot CoT
```
Question: 一个农夫有 17 只羊，除了 9 只以外都死了。他还剩几只？
Answer: Let's think step by step.
```

### Zero-shot CoT
```
Question: Marty has 100 centimeters of ribbon that he must cut into 4 equal parts...
Answer: Let's think step by step.
```

**扩展技巧**：
- **Self-Consistency**：多次采样，多数投票
- **Complexity-based Consistency**：优先选择推理链更复杂的答案
- **STaR**：保留生成正确推理链的样本，迭代微调

## 3.3 Tree of Thoughts（思维树）

在每一步生成多个候选思路，形成树结构，用 BFS/DFS 搜索最优路径。

```
1. 将问题分解为 n 个 thought steps
2. 每个 step 生成 m 个候选 thoughts
3. 用分类器或多数投票评估每个 state
4. 搜索最优路径
```

适用场景：复杂规划、数学证明、创意写作。

## 3.4 ReAct（推理 + 行动）

交替进行思考（Thought）和工具调用（Action），将推理过程显式化。

```
Thought: 我需要查一下当前北京的天气。
Action: WeatherAPI("Beijing")
Observation: 15°C，晴
Thought: 用户问的是穿衣建议，我需要基于温度给出推荐。
Answer: 建议穿薄外套...
```

## 3.5 RAG（检索增强生成）

```
1. 用户提问
2. 检索系统从知识库找出最相关的 Top-K 文档片段
3. 将片段作为 Context 注入 Prompt
4. 模型生成基于检索内容的答案
```

**格式建议**：
```
Evidence: {检索到的段落}
Question: {用户问题}
Answer:
```

## 3.6 Tool Use / Agent 模式

### 完整项目案例 1：RAG 问答系统

**场景**：基于公司内部文档的智能问答

```
架构：
用户问题 → Embedding 检索 → Top-3 文档片段 → Prompt 注入 → LLM 生成答案

核心 Prompt（OpenAI SDK）：
"""

You are a helpful assistant for {company_name} internal documentation.

# Instructions
- Answer questions based ONLY on the provided context
- If the context doesn't contain the answer, say "I don't have that information"
- Cite the source document for each piece of information
- If unsure, express uncertainty rather than guessing

# Context
{retrieved_context}

# Question
{user_question}

# Format
Provide answer in:
1. Direct answer (2-3 sentences)
2. Supporting evidence (quote from context)
3. Source document name
4. Confidence level (High/Medium/Low)

"""
```

**Python 实现骨架**：
```python
import chromadb
from openai import OpenAI

client = OpenAI()

# 1. 检索
query_embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=user_question
).data[0].embedding

results = chromadb_client.query(
    collection="docs",
    query_embeddings=[query_embedding],
    n_results=3
)

# 2. 构建 Prompt
context = "\n\n".join([doc["text"] for doc in results["documents"][0]])

prompt = f"""...（上述 Prompt 模板）..."""

# 3. 生成
response = client.responses.create(
    model="gpt-4o",
    input=prompt
)
```

### 完整项目案例 2：代码生成 Agent

**场景**：根据需求描述自动生成代码 + 测试

```
工作流：
需求分析 → 生成代码 → 生成测试 → 执行测试 → 修复错误 → 输出最终代码

提示链设计：
Step 1 - 需求澄清：
"Analyze this requirement and list: (1) input/output specs, (2) edge cases,
(3) error handling needs. Requirement: {user_requirement}"

Step 2 - 代码生成：
"Write a {language} function that: {analyzed_specs}
Requirements: clean code, type hints, docstrings, no external dependencies."

Step 3 - 测试生成：
"Generate pytest unit tests covering: happy path, edge cases, error cases."

Step 4 - 自修复：
"Run these tests. If any fail, analyze the error and fix the code.
Repeat until all tests pass."
```

### 完整项目案例 3：多 Agent 协作系统

**场景**：市场调研报告自动生成

```
Agent 1 - 信息搜集：
- 搜索最新市场动态
- 提取竞争对手信息
- 整理行业数据

Agent 2 - 数据分析：
- 分析趋势
- 计算关键指标
- 识别异常

Agent 3 - 报告撰写：
- 整合 Agent 1 和 2 的输出
- 撰写结构化报告
- 添加可视化建议

Orchestrator：
- 分发任务
- 检查质量
- 决定是否需要补充调研
```
将任务拆成固定顺序的子任务，每个 LLM 调用处理前一步的输出。

适用：翻译后润色、大纲检查后写全文。

### Routing（路由）
先分类输入，再交给专用 Prompt 处理。

适用：客服分流、模型选型（简单问题用小模型，复杂问题用大模型）。

### Parallelization（并行化）
- **Sectioning**：任务拆分后并行执行
- **Voting**：同一任务多次执行，结果聚合

适用：内容审核、代码漏洞审查。

### Orchestrator-Workers
一个中心 LLM 动态拆分子任务，分发给 Worker，最后汇总。

适用：多文件代码修改、跨源信息搜集。

### Evaluator-Optimizer
生成 → 评估 → 反馈 → 再生成，循环迭代。

适用：文学翻译、复杂搜索任务、长文润色。

### Autonomous Agent（自主 Agent）
LLM + 工具 + 记忆 + 反馈循环，自主规划多步执行。

核心原则（Anthropic）：
1. **简洁性**：避免过度复杂的框架
2. **透明性**：显式展示规划步骤
3. **ACI（Agent-Computer Interface）**：精心设计工具文档与参数

## 3.7 Automatic Prompt Design

- **AutoPrompt / Prefix-Tuning / P-Tuning**：将 Prompt 作为可训练参数优化
- **APE（Automatic Prompt Engineer）**：让 LLM 生成候选指令，按得分筛选
- **Prompt Compression**：用更少 Token 表达相同意图

## 3.8 技术选型决策树

```
任务复杂吗？
├── 否 → Zero-shot + 明确指令
└── 是
    ├── 需要外部知识？ → RAG
    ├── 需要多步推理？ → CoT / ToT
    ├── 需要工具调用？ → ReAct / Agent
    ├── 步骤固定？ → Prompt Chaining
    └── 需多视角验证？ → Parallelization / Voting
```