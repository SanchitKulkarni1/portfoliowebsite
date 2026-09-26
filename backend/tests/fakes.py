"""In-memory implementations of the domain ports, for unit tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.domain.models import QueryResult, SafeCypher, Subgraph


@dataclass
class FakeLanguageModel:
    """Returns scripted completions in order and records every call."""

    responses: list[str | Exception]
    calls: list[tuple[str, str]] = field(default_factory=list)

    async def complete(self, *, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def stream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        """Streams the next scripted completion word by word."""
        text = await self.complete(system=system, prompt=prompt)
        for i, word in enumerate(text.split(" ")):
            yield word if i == 0 else " " + word


@dataclass
class FakeGraphRepository:
    results: list[QueryResult | Exception] = field(default_factory=list)
    snapshot: Subgraph = field(default_factory=Subgraph)
    ready: bool = True
    executed: list[str] = field(default_factory=list)
    snapshot_calls: int = 0

    async def run_read(self, query: SafeCypher) -> QueryResult:
        self.executed.append(query.text)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    async def fetch_snapshot(self) -> Subgraph:
        self.snapshot_calls += 1
        return self.snapshot

    async def ping(self) -> bool:
        return self.ready
