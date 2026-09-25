"""Composition root: the only place concrete adapters are chosen and wired together."""

from __future__ import annotations

from app.api.rate_limit import SlidingWindowRateLimiter
from app.api.state import Container
from app.config import Settings
from app.infrastructure.gemini_model import GeminiLanguageModel
from app.infrastructure.neo4j_repository import Neo4jGraphRepository, create_driver
from app.services.chat_service import ChatService, ChatSettings
from app.services.cypher_guard import CypherGuard
from app.services.graph_service import GraphService

__all__ = ["Container", "build_container", "build_rate_limiter"]


def build_rate_limiter(settings: Settings) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(
        max_requests=settings.chat_rate_limit_requests,
        window_seconds=settings.chat_rate_limit_window_seconds,
    )


async def build_container(settings: Settings) -> Container:
    driver = create_driver(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password.get_secret_value())
    repository = Neo4jGraphRepository(
        driver, database=settings.neo4j_database, timeout_seconds=settings.query_timeout_seconds
    )
    llm = GeminiLanguageModel(
        api_key=settings.google_api_key.get_secret_value(),
        model=settings.gemini_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )

    async def close() -> None:
        await driver.close()
        await llm.aclose()

    return Container(
        chat_service=ChatService(
            llm,
            repository,
            CypherGuard(max_rows=settings.max_result_rows),
            ChatSettings(max_answer_rows=settings.max_result_rows),
        ),
        graph_service=GraphService(repository, snapshot_ttl_seconds=settings.graph_snapshot_ttl_seconds),
        chat_rate_limiter=build_rate_limiter(settings),
        close=close,
    )
