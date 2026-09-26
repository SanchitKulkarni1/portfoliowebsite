"""Pre-answer the suggested questions at startup, so the chips visitors click most are instant.

Runs in the background after the server starts, one question at a time and spaced out, so the
warm-up never uses the LLM's per-minute quota faster than visitors could."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from app.domain.errors import CareerGraphError, LanguageModelBusyError
from app.domain.models import ChatStatus
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


async def warm_answers(
    chat: ChatService,
    questions: Sequence[str],
    *,
    spacing_seconds: float,
    busy_backoff_seconds: float = 60.0,
) -> int:
    """Answer and pin each question. Returns how many were answered from the graph."""
    answered = 0
    for index, question in enumerate(questions):
        if index:
            await asyncio.sleep(spacing_seconds)
        try:
            answer = await chat.ask(question, pin=True)
        except LanguageModelBusyError as exc:
            logger.warning("warm-up paused, LLM busy (%s); skipping %r", exc, question)
            await asyncio.sleep(busy_backoff_seconds)
            continue
        except CareerGraphError as exc:
            logger.warning("warm-up skipped %r: %s", question, exc)
            continue
        if answer.status is ChatStatus.ANSWERED:
            answered += 1
        else:
            logger.warning(
                "suggested question %r did not answer from the graph (status=%s)", question, answer.status.value
            )
    logger.info("warm-up done: %d/%d suggested questions pre-answered", answered, len(questions))
    return answered
