# 03 进阶技�?

## 3.1 Few-Shot Learning（少样本学习�?

�?Prompt 中提供若干输�?输出示例，让模型模仿模式�?

```
Text: (lawrence bounces) all over the stage, dancing...
Sentiment: positive

Text: despite all evidence to the contrary, this clunker...
Sentiment: negative

Text: i'll bet the video game is a lot more fun than the film.
Sentiment:
```

**示例选择要点**�?
- 语义上与待预测样本相似（k-NN 聚类�?
- 标签分布均衡，避�?majority label bias
- 顺序随机化，避免 recency bias

## 3.2 Chain-of-Thought（链式思考）

要求模型展示逐步推理过程，显著提升数学、逻辑、代码任务准确率�?

### Few-shot CoT
```
Question: 一个农夫有 17 只羊，除�?9 只以外都死了。他还剩几只�?
Answer: Let's think step by step.
```

### Zero-shot CoT
```
Question: Marty has 100 centimeters of ribbon that he must cut into 4 equal parts...
Answer: Let's think step by step.
```

**扩展技�?*�?
- **Self-Consistency**：多次采样，多数投票
- **Complexity-based Consistency**：优先选择推理链更复杂的答�?
- **STaR**：保留生成正确推理链的样本，迭代微调

## 3.3 Tree of Thoughts（思维树）

在每一步生成多个候选思路，形成树结构，用 BFS/DFS 搜索最优路径�?

```
1. 将问题分解为 n �?thought steps
2. 每个 step 生成 m 个候�?thoughts
3. 用分类器或多数投票评估每�?state
4. 搜索最优路�?
```

适用场景：复杂规划、数学证明、创意写作�?

## 3.4 ReAct（推�?+ 行动�?

交替进行思考（Thought）和工具调用（Action），将推理过程显式化�?

```
Thought: 我需要查一下当前北京的天气�?
Action: WeatherAPI("Beijing")
Observation: 15°C，晴
Thought: 用户问的是穿衣建议，我需要基于温度给出推荐�?
Answer: 建议穿薄外套...
```

## 3.5 RAG（检索增强生成）

```
1. 用户提问
2. 检索系统从知识库找出最相关�?Top-K 文档片段
3. 将片段作�?Context 注入 Prompt
4. 模型生成基于检索内容的答案
```

**格式建议**�?
```
Evidence: {检索到的段落}
Question: {用户问题}
Answer:
```

## 3.6 Tool Use / Agent 模式

### 完整项目案例：RAG 问答系统（Agnes AI 国内版）

**场景**：基于公司内部文档的智能问答

```
架构�?
用户问题 �?Embedding 检�?�?Top-3 文档片段 �?Prompt 注入 �?LLM 生成答案
```

**Python 实现骨架**�?
```python
import os
import chromadb
from openai import OpenAI

# 初始�?Agnes AI 客户端（国内地址�?
AGNES_API_KEY = os.getenv("AGNES_AI_API_KEY", os.getenv("AGNES_API_KEY", ""))
_raw_base = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.cn/v1")
AGNES_BASE_URL = _raw_base.rsplit("/chat/completions", 1)[0] if "/chat/completions" in _raw_base else _raw_base

client = OpenAI(
    api_key=AGNES_API_KEY,
    base_url=AGNES_BASE_URL
)

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("knowledge_base")

# 模拟知识库文�?
documents = [
    "公司年假政策：员工工作满 1 年享�?5 天年假，�?5 年享�?10 天，�?10 年享�?15 天�?,
    "请假流程：在 OA 系统提交申请，直属上级审批，超过 3 天需 HR 备案�?,
    "远程办公政策：每周二、周四可申请远程办公，需提前一天在系统提交�?
]

# 生成 embeddings 并存�?
for i, doc in enumerate(documents):
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=doc
    ).data[0].embedding
    collection.add(
        documents=[doc],
        embeddings=[embedding],
        ids=[f"doc_{i}"]
    )

# 检索并问答
def rag_query(question: str):
    query_embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    
    context = "\n\n".join(results["documents"][0])
    
    prompt = f"""
    # Identity
    你是公司内部智能助手，专门回答员工关于公司政策的问题�?

    # Instructions
    - 只基于提供的上下文回�?
    - 如果上下文中没有答案，说"我暂时没有这方面的信息，建议咨询 HR"
    - 引用具体政策条款

    # Context
    {context}

    # Question
    {question}
    """
    
    response = client.chat.completions.create(
        model="agnes-2.0-flash",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 测试
answer = rag_query("工作 3 年有多少天年假？")
print(answer)
```

### 完整项目案例 2：代码生�?Agent

**场景**：根据需求描述自动生成代�?+ 测试

```
工作流：
需求分�?�?生成代码 �?生成测试 �?执行测试 �?修复错误 �?输出最终代�?

提示链设计：
Step 1 - 需求澄清：
"Analyze this requirement and list: (1) input/output specs, (2) edge cases,
(3) error handling needs. Requirement: {user_requirement}"

Step 2 - 代码生成�?
"Write a {language} function that: {analyzed_specs}
Requirements: clean code, type hints, docstrings, no external dependencies."

Step 3 - 测试生成�?
"Generate pytest unit tests covering: happy path, edge cases, error cases."

Step 4 - 自修复：
"Run these tests. If any fail, analyze the error and fix the code.
Repeat until all tests pass."
```

### 完整项目案例 3：多 Agent 协作系统

**场景**：市场调研报告自动生�?

```
Agent 1 - 信息搜集�?
- 搜索最新市场动�?
- 提取竞争对手信息
- 整理行业数据

Agent 2 - 数据分析�?
- 分析趋势
- 计算关键指标
- 识别异常

Agent 3 - 报告撰写�?
- 整合 Agent 1 �?2 的输�?
- 撰写结构化报�?
- 添加可视化建�?

Orchestrator�?
- 分发任务
- 检查质�?
- 决定是否需要补充调�?
```

## 3.7 Automatic Prompt Design

- **AutoPrompt / Prefix-Tuning / P-Tuning**：将 Prompt 作为可训练参数优�?
- **APE（Automatic Prompt Engineer�?*：让 LLM 生成候选指令，按得分筛�?
- **Prompt Compression**：用更少 Token 表达相同意图

## 3.8 技术选型决策�?

```
任务复杂吗？
├── �?�?Zero-shot + 明确指令
└── �?
    ├── 需要外部知识？ �?RAG
    ├── 需要多步推理？ �?CoT / ToT
    ├── 需要工具调用？ �?ReAct / Agent
    ├── 步骤固定�?�?Prompt Chaining
    └── 需多视角验证？ �?Parallelization / Voting
```
