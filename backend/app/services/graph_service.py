"""The /graph and readiness use cases."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from app.domain.models import Subgraph
from app.domain.ports import GraphRepository


class GraphService:
    """Serves the full graph snapshot, cached because it only changes when we re-seed."""

    def __init__(
        self,
        repository: GraphRepository,
        *,
        snapshot_ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._repository = repository
        self._ttl = snapshot_ttl_seconds
        self._clock = clock
        self._cached: Subgraph | None = None
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def snapshot(self) -> Subgraph:
        async with self._lock:
            if self._cached is None or self._clock() - self._cached_at >= self._ttl:
                self._cached = await self._repository.fetch_snapshot()
                self._cached_at = self._clock()
            return self._cached

    async def is_ready(self) -> bool:
        return await self._repository.ping()
