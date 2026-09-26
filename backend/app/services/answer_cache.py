"""In-memory LRU + TTL cache of chat answers.

Visitors mostly ask the same handful of questions (often the suggested prompts),
so caching them saves LLM quota and makes repeat questions instant. Per-process,
like the rate limiter.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable

from app.domain.models import ChatAnswer


def cache_key(question: str) -> str:
    """Treat questions differing only in case, spacing or trailing punctuation as the same."""
    return " ".join(question.lower().split()).rstrip("?!. ")


class AnswerCache:
    def __init__(
        self,
        *,
        max_entries: int,
        ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_entries
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, ChatAnswer]] = OrderedDict()

    def get(self, question: str) -> ChatAnswer | None:
        key = cache_key(question)
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, answer = entry
        if self._clock() - stored_at >= self._ttl:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return answer

    def put(self, question: str, answer: ChatAnswer) -> None:
        if self._ttl <= 0:
            return
        key = cache_key(question)
        self._entries[key] = (self._clock(), answer)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)
