"""Interfaces the service layer depends on. Infrastructure adapters implement them;
tests substitute fakes. Nothing here knows about Neo4j or Gemini."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from app.domain.models import QueryResult, SafeCypher, Subgraph


class GraphRepository(Protocol):
    async def run_read(self, query: SafeCypher) -> QueryResult:
        """Execute a guarded query in a read-only transaction."""
        ...

    async def fetch_snapshot(self) -> Subgraph:
        """Return every node and relationship in the graph."""
        ...

    async def ping(self) -> bool:
        """Return True if the database is reachable."""
        ...


class LanguageModel(Protocol):
    async def complete(self, *, system: str, prompt: str) -> str:
        """Return the model's text completion. Raises LanguageModelError on failure."""
        ...

    def stream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        """Yield the completion in chunks as they are generated. Raises LanguageModelError on failure."""
        ...
