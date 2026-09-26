"""In-memory sliding-window rate limiter.

Per-process state: fine for a single Render instance. Move to Redis if the API is
ever scaled horizontally.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class SlidingWindowRateLimiter:
    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: float,
        max_tracked_clients: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._max_clients = max_tracked_clients
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, client: str) -> RateLimitDecision:
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(client, deque())
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._max:
                return RateLimitDecision(False, max(1, math.ceil(self._window - (now - hits[0]))))
            hits.append(now)
            if len(self._hits) > self._max_clients:
                self._evict_idle(now)
            return RateLimitDecision(True)

    def _evict_idle(self, now: float) -> None:
        for client in [c for c, h in self._hits.items() if not h or now - h[-1] >= self._window]:
            del self._hits[client]
