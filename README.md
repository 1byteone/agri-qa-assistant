<div align="center">

# 🌾 Agri-QA-Assistant

### Agricultural Intelligent Q&A Prototype System

**基于 LangGraph 目标导向型智能体架构的农业知识问答系统**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-6C3EC1.svg?style=flat&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Overview

Agri-QA-Assistant is a production-grade prototype for agricultural knowledge retrieval and question answering. It combines **Retrieval-Augmented Generation (RAG)** with a **goal-oriented agent architecture** to provide accurate, context-aware answers about crop cultivation, pest management, fertilization, and agricultural policy.

### Key Features

| Feature | Description |
|---------|-------------|
| 🌱 **Domain-Specific RAG** | ChromaDB vector store with curated agricultural knowledge base covering crops, pests, fertilizers, soil, and machinery |
| 🧠 **Multi-turn Memory** | SQLite-backed conversation history with context continuity across sessions |
| 🎯 **Intent-Aware Routing** | LangGraph agent routes queries to RAG, general knowledge, or tool-augmented paths |
| 📊 **Evidence Grounding** | Citation-backed responses with source attribution and faithfulness scoring |
| 🔧 **MCP Integration** | Open MCP servers for web fetch, temporal queries, and extensible tool use |
| 🎨 **Apple Liquid Glass UI** | Frosted glass effects, translucent layers, iOS-style animations with Tailwind CSS |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend: Next.js 14 + Radix UI               │
│   Apple Liquid Glass Chat Interface                              │
│   ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐ │
│   │ Chat Panel   │ │ Knowledge    │ │ Generative UI           │ │
│   │ + Streaming  │ │ Panel        │ │ (Crop Diagnosis, etc.)  │ │
│   └─────────────┘ └──────────────┘ └─────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────────┐
│                  Backend: FastAPI + LangGraph                    │
│                                                                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│   │ Intent Router │──▶│ RAG Pipeline │──▶│ Response Builder │  │
│   │ (LangGraph)  │   │ (ChromaDB)   │   │ + Citations      │  │
│   └──────────────┘   └──────────────┘   └──────────────────┘  │
│         │                   │                    │              │
│   ┌─────▼─────┐    ┌───────▼──────┐    ┌───────▼────────┐    │
│   │ Memory     │    │ Knowledge    │    │ MCP Tools      │    │
│   │ (SQLite)   │    │ Base         │    │ Fetch / Time   │    │
│   └───────────┘    └──────────────┘    └────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        External Services                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│   │ LLM API      │  │ Embedding    │  │ ChromaDB         │    │
│   │ (OpenAI-     │  │ Model        │  │ (Local Persist)  │    │
│   │  Compatible) │  │              │  │                  │    │
│   └──────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Redis** (optional, for caching)
- **LLM API Key** (OpenAI-compatible endpoint)

### 1. Clone & Setup

```bash
git clone https://github.com/1byteone/agri-qa-assistant.git
cd agri-qa-assistant
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start server
python main.py
# → http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# → http://localhost:3000
```

### 4. Access Application

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## ⚙️ Configuration

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AGNES_AI_API_KEY` | LLM API key | ✅ | — |
| `AGNES_AI_BASE_URL` | LLM API endpoint | ✅ | `https://api.agnes-ai.cn/v1` |
| `AGNES_AI_CHAT_MODEL` | Chat model name | ❌ | `agnes-2.5-flash` |
| `AGNES_AI_EMBEDDING_MODEL` | Embedding model | ❌ | `text-embedding-3-small` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | ❌ | `./data/chroma_db` |
| `SQLITE_DB_URL` | SQLite connection string | ❌ | `sqlite+aiosqlite:///./data/agri_qa.db` |
| `REDIS_URL` | Redis connection string | ❌ | `redis://localhost:6379/0` |
| `MCP_FETCH_ENABLED` | Enable web fetch tool | ❌ | `true` |
| `MCP_TIME_ENABLED` | Enable time tool | ❌ | `true` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME` | Application display name | `CropWise` |
| `NEXT_PUBLIC_APP_DESCRIPTION` | Application description | `农业智能问答助手` |

---

## 📁 Project Structure

```
agri-qa-assistant/
├── backend/                     # FastAPI + LangGraph backend
│   ├── main.py                  # Application entry point & routes
│   ├── agent.py                 # LangGraph agent orchestration
│   ├── knowledge_base.py        # ChromaDB RAG pipeline
│   ├── memory.py                # SQLite conversation memory
│   ├── tools.py                 # Agricultural tools & MCP integration
│   ├── config.py                # Pydantic settings management
│   ├── schemas.py               # Request/response models
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment template
│   └── data/                    # Runtime data (gitignored)
├── frontend/                    # Next.js 14 application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Main chat page
│   │   ├── layout.tsx           # Root layout
│   │   ├── globals.css          # Global styles (Liquid Glass)
│   │   ├── crop-diagnosis/      # Crop diagnosis feature
│   │   ├── evaluations/         # QA evaluation dashboard
│   │   ├── farming-calendar/    # Farming calendar
│   │   ├── jxau-news/           # University news feed
│   │   └── policy/              # Agricultural policy lookup
│   ├── components/              # React components
│   │   ├── chat-interface.tsx   # Core chat UI
│   │   ├── knowledge-panel.tsx  # Knowledge source display
│   │   ├── markdown-message.tsx # Markdown renderer
│   │   └── ...
│   ├── lib/                     # Utilities
│   │   ├── utils.ts             # cn() helper
│   │   ├── sse.ts               # Server-Sent Events client
│   │   └── sidebar-context.ts   # Sidebar state
│   ├── public/                  # Static assets
│   ├── package.json
│   └── tailwind.config.ts
├── data/                        # Shared data resources
│   ├── evals/                   # Evaluation datasets
│   └── evidence-packs/          # Curated evidence documents
├── docs/                        # Project documentation
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Multi-turn chat with streaming |
| `GET` | `/history/{thread_id}` | Retrieve conversation history |
| `DELETE` | `/history/{thread_id}` | Clear conversation history |
| `GET` | `/knowledge-base/status` | Knowledge base statistics |
| `GET` | `/health` | Health check |
| `GET` | `/evaluations/items` | QA evaluation items |
| `POST` | `/evaluations/items/{id}/annotation` | Submit expert annotation |

---

## 🧪 Evaluation System

The project includes a built-in evaluation framework:

- **AgriIR Benchmark**: 120 curated agricultural questions across 5 scenarios
- **Metrics**: Recall@K, citation coverage, faithfulness, safety compliance
- **Expert Annotation**: Web-based UI for domain expert review

---

## 🛠️ Development

### Running Tests

```bash
cd backend
pytest -v
```

### Adding Knowledge

```python
from knowledge_base import knowledge_base
from langchain.schema import Document

docs = [
    Document(
        page_content="Your agricultural knowledge...",
        metadata={"category": "crop", "topic": "planting"}
    )
]
knowledge_base.add_documents(docs)
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for Agricultural Intelligence**

</div>
