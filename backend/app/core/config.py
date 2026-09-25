from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "PayResolve AI"
    app_env: str = "development"
    debug: bool = True
    version: str = "1.0.0"
    database_url: str = "sqlite+aiosqlite:///./payresolve.db"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "payresolve_policies"
    llm_provider: str = "demo"
    llm_model: str = "local-demo"
    llm_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    semantic_rag_enabled: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    auth_demo_token: str = "payresolve-demo-token"
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str): return [x.strip() for x in v.split(",") if x.strip()]
        return v

@lru_cache
def get_settings() -> Settings: return Settings()
settings = get_settings()
