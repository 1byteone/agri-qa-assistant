from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    agnes_api_key: str
    agnes_base_url: str = "https://api.agnes-ai.cn/v1"
    agnes_chat_model: str = "agnes-2.5-flash"
    agnes_embedding_model: str = "text-embedding-3-small"
    rag_embedding_mode: str = "local"

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

settings = Settings()
