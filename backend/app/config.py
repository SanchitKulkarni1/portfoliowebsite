"""Runtime configuration, read from environment variables (or a local .env file)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    """Database connection only. Enough for scripts/seed.py, which needs no LLM key."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    neo4j_uri: str
    # Aura's downloadable credentials file calls this NEO4J_USERNAME; accept both.
    neo4j_user: str = Field("neo4j", validation_alias=AliasChoices("neo4j_user", "neo4j_username"))
    neo4j_password: SecretStr
    neo4j_database: str = "neo4j"


class Settings(Neo4jSettings):
    """Everything the API needs."""

    query_timeout_seconds: float = Field(5.0, gt=0)
    max_result_rows: int = Field(50, ge=1, le=500)

    # LLM
    google_api_key: SecretStr
    gemini_model: str = "gemini-3.5-flash-lite"  # 15 req/min on the free tier vs 5 for 2.5-flash
    llm_timeout_seconds: float = Field(30.0, gt=0)

    # HTTP
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:8080"]
    # Optional full-match regex for origins that can't be listed up front, e.g. Vercel preview URLs.
    allowed_origin_regex: str | None = None
    chat_rate_limit_requests: int = Field(10, ge=1)
    chat_rate_limit_window_seconds: float = Field(600.0, gt=0)
    graph_snapshot_ttl_seconds: float = Field(300.0, ge=0)
    chat_cache_ttl_seconds: float = Field(3600.0, ge=0)  # 0 disables the answer cache
    chat_cache_max_entries: int = Field(500, ge=1)
    log_level: str = "INFO"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("allowed_origin_regex")
    @classmethod
    def _compile_origin_regex(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        re.compile(value)  # fail at startup, not on the first request
        return value.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
