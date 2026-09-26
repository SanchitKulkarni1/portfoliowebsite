"""Per-request stage timings, so latency can be attributed to the LLM, the database or the cache."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager


class StageTimings:
    def __init__(self) -> None:
        self._stages: list[tuple[str, float]] = []

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self._stages.append((stage, (time.perf_counter() - started) * 1000))

    @property
    def stages(self) -> tuple[tuple[str, float], ...]:
        return tuple(self._stages)

    def total_ms(self) -> float:
        return sum(ms for _, ms in self._stages)

    def as_log(self) -> str:
        return " ".join(f"{stage}_ms={ms:.0f}" for stage, ms in self._stages)

    def as_server_timing(self) -> str:
        """Render as an HTTP Server-Timing header value (shown in the browser's network panel)."""
        return ", ".join(f"{stage};dur={ms:.1f}" for stage, ms in self._stages)
