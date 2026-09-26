"""Seeds Neo4j through the HTTPS Query API (POST /db/{database}/query/v2).

Use this where the Bolt port (7687) is unreachable but HTTPS works, e.g. behind an
HTTP-only egress proxy. Like Neo4jSeeder, it is only used by scripts/seed.py.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.domain.career_data import CareerDataset
from app.domain.errors import CareerGraphError
from app.infrastructure.cypher_script import COUNT_STATEMENT, seed_statements
from app.infrastructure.neo4j_seeder import SeedSummary


class HttpSeedError(CareerGraphError):
    pass


def query_api_base_url(neo4j_uri: str) -> str:
    """neo4j+s://abc.databases.neo4j.io -> https://abc.databases.neo4j.io"""
    parsed = urlparse(neo4j_uri)
    secure = parsed.scheme.endswith("+s") or parsed.scheme.endswith("+ssc")
    if not parsed.hostname:
        raise ValueError(f"Cannot derive a Query API URL from {neo4j_uri!r}")
    return f"{'https' if secure else 'http'}://{parsed.hostname}" + ("" if secure else ":7474")


class Neo4jHttpSeeder:
    def __init__(self, *, base_url: str, database: str, user: str, password: str, timeout_seconds: float = 60) -> None:
        self._url = f"{base_url.rstrip('/')}/db/{database}/query/v2"
        self._client = httpx.AsyncClient(auth=(user, password), timeout=timeout_seconds)

    async def replace_graph(self, dataset: CareerDataset) -> SeedSummary:
        try:
            for statement in seed_statements(dataset):
                await self._run(statement)
            nodes, relationships = (await self._run(COUNT_STATEMENT))["values"][0]
        finally:
            await self._client.aclose()
        if (nodes, relationships) != (len(dataset.nodes), len(dataset.relationships)):
            raise HttpSeedError(
                f"Loaded {nodes} nodes / {relationships} relationships, expected {len(dataset.nodes)} / {len(dataset.relationships)}."
            )
        return SeedSummary(nodes, relationships)

    async def _run(self, statement: str) -> dict:
        try:
            response = await self._client.post(self._url, json={"statement": statement})
        except httpx.HTTPError as exc:
            raise HttpSeedError(f"Query API request failed: {exc}") from exc
        body = response.json() if response.content else {}
        if response.status_code >= 400 or body.get("errors"):
            raise HttpSeedError(f"Query API error {response.status_code}: {body.get('errors') or response.text[:300]}")
        return body.get("data", {})
