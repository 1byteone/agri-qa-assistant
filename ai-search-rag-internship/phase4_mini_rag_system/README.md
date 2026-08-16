# Phase 4: Mini RAG System

本目录用于把前三个阶段串成可演示服务：文档导入 -> 解析分块 -> 建索引 -> 检索 -> LLM 生成 -> 引用展示。

详细实验课：`../docs/tutorials/phase4-product-lab.md`；PRD、A/B 测试和技术报告模板位于 `../docs/templates/`。

当前已提供完整 evidence-first MVP：

```powershell
python -m phase4_mini_rag_system
```

打开 `http://127.0.0.1:8000/`，或调用：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/search -Method Post -ContentType 'application/json' -Body '{"query":"Chunk overlap","top_k":5}'
```

默认不需要 LLM key，返回可追溯证据；只有同时设置 `RAG_ENABLE_LLM=true` 和 `OPENAI_API_KEY`，并可选配置 `OPENAI_BASE_URL`、`RAG_LLM_MODEL` 后，`/chat` 才会启用 OpenAI-compatible 生成，并保留 citations。

最终需要补齐 FastAPI 接口、最小前端、`docs/PRD.md`、`docs/AB_test_plan.md`、`docs/competitive_analysis.md` 和 `docs/tech_report.md`。LLM 通过 OpenAI-compatible 接口注入，密钥只放在本地 `.env`。
