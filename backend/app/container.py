"""Composition root: the only place concrete adapters are chosen and wired together."""

from __future__ import annotations

import logging
from pathlib import Path

from app.api.rate_limit import SlidingWindowRateLimiter
from app.api.state import Container
from app.config import Settings
from app.domain.career_data import load_suggested_questions
from app.infrastructure.gemini_model import GeminiLanguageModel
from app.infrastructure.neo4j_repository import Neo4jGraphRepository, create_driver
from app.services.answer_cache import AnswerCache
from app.services.cache_warmer import warm_answers
from app.services.chat_service import ChatService, ChatSettings
from app.services.cypher_guard import CypherGuard
from app.services.graph_service import GraphService

__all__ = ["Container", "build_container", "build_rate_limiter"]

logger = logging.getLogger(__name__)

SUGGESTED_QUESTIONS = Path(__file__).resolve().parent.parent / "data" / "suggested_questions.json"


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

    chat_service = ChatService(
        llm,
        repository,
        CypherGuard(max_rows=settings.max_result_rows),
        ChatSettings(max_answer_rows=settings.max_result_rows),
        AnswerCache(max_entries=settings.chat_cache_max_entries, ttl_seconds=settings.chat_cache_ttl_seconds),
    )

    async def warm_up() -> None:
        if not settings.chat_cache_warm_up:
            return
        try:
            await warm_answers(
                chat_service,
                load_suggested_questions(SUGGESTED_QUESTIONS),
                spacing_seconds=settings.chat_cache_warm_up_spacing_seconds,
            )
        except Exception:  # a failed warm-up must never take the API down
            logger.exception("warm-up failed")

    return Container(
        chat_service=chat_service,
        graph_service=GraphService(repository, snapshot_ttl_seconds=settings.graph_snapshot_ttl_seconds),
        chat_rate_limiter=build_rate_limiter(settings),
        close=close,
        warm_up=warm_up,
    )
