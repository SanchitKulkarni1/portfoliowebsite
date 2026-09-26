"""What the HTTP layer needs at runtime. Built by the composition root (app/container.py)
and stored on app.state, so the api package never imports infrastructure."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.api.rate_limit import SlidingWindowRateLimiter
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService


async def _noop() -> None:
    return None


@dataclass
class Container:
    chat_service: ChatService
    graph_service: GraphService
    chat_rate_limiter: SlidingWindowRateLimiter
    close: Callable[[], Awaitable[None]] = _noop
