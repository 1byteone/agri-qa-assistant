from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    agnes_api_key: str
    agnes_base_url: str = "https://api.agnes-ai.cn/v1"
    agnes_chat_model: str = "agnes-2.5-flash"
    agnes_embedding_model: str = "text-embedding-3-small"
    rag_embedding_mode: str = "local"  # local / remote / bge_m3

    # Database
    chroma_persist_dir: str = "./data/chroma_db"
    sqlite_db_url: str = "sqlite+aiosqlite:///./data/agri_qa.db"
    redis_url: str = "redis://localhost:6379/0"

    # MCP
    mcp_fetch_enabled: bool = True
    mcp_time_enabled: bool = True
    mcp_memory_enabled: bool = False

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_timezone: str = "Asia/Shanghai"
    debug: bool = True

    # Proxy (from system environment variables)
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    # ============================================
    # W2-W4: 知识图谱 & 检索增强配置
    # ============================================

    # Neo4j 知识图谱
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "cropwise2026"

    # BGE-M3 嵌入
    bge_m3_api_url: str = ""  # 留空则使用本地哈希回退
    bge_m3_api_key: str = ""

    # BGE-Reranker
    reranker_api_url: str = ""  # 留空则自动检测本地模型
    reranker_api_key: str = ""
    reranker_enabled: bool = True
    reranker_score_threshold: Optional[float] = None

    # 检索配置
    rrf_k: int = 60  # RRF 平滑参数
    bm25_weight: float = 0.4
    vector_weight: float = 0.6
    hybrid_top_k: int = 5

    # 知识图谱构建
    kg_pipeline_max_chunk_size: int = 2000

    # 评测
    eval_auto_run: bool = False  # 是否每次启动自动运行评测

settings = Settings()
