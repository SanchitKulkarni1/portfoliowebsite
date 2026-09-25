"""Runtime configuration, read from environment variables (or a local .env file)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    """Database connection only. Enough for scripts/seed.py, which needs no LLM key."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    neo4j_uri: str
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr
    neo4j_database: str = "neo4j"


class Settings(Neo4jSettings):
    """Everything the API needs."""

    query_timeout_seconds: float = Field(5.0, gt=0)
    max_result_rows: int = Field(50, ge=1, le=500)

    # LLM
    google_api_key: SecretStr
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: float = Field(30.0, gt=0)

    # HTTP
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:8080"]
    chat_rate_limit_requests: int = Field(10, ge=1)
    chat_rate_limit_window_seconds: float = Field(600.0, gt=0)
    graph_snapshot_ttl_seconds: float = Field(300.0, ge=0)
    log_level: str = "INFO"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
