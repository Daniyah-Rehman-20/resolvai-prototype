from functools import lru_cache
import json
from typing import Annotated
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

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
    async_ingestion_enabled: bool = False
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    rate_limit_requests: int = Field(default=60, ge=1, le=100000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=86400)
    auth_demo_enabled: bool = False
    auth_session_hours: int = Field(default=24, ge=1, le=168)
    auth_demo_token: str = "payresolve-demo-token"

    @model_validator(mode="after")
    def guard_demo_auth(self):
        if self.auth_demo_enabled and self.app_env not in {"development", "test"}:
            raise ValueError("Demo authentication is permitted only in development or test")
        return self

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        if isinstance(value, str) and value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value[len("postgresql://"):]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            origins = json.loads(value) if value.strip().startswith("[") else [x.strip() for x in value.split(",") if x.strip()]
        else:
            origins = value
        if isinstance(origins, list):
            return [
                origin
                if origin == "*" or origin.startswith(("http://", "https://"))
                else f"https://{origin}"
                for origin in origins
            ]
        return origins

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
