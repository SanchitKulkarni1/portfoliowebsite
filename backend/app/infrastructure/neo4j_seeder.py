"""Writes the career dataset into Neo4j. Used only by scripts/seed.py, never by the API,
which holds a read-only code path."""

from __future__ import annotations

from dataclasses import dataclass

from neo4j import AsyncDriver, AsyncManagedTransaction

from app.domain import schema
from app.domain.career_data import CareerDataset


@dataclass(frozen=True)
class SeedSummary:
    nodes: int
    relationships: int


class Neo4jSeeder:
    def __init__(self, driver: AsyncDriver, *, database: str) -> None:
        self._driver = driver
        self._database = database

    async def replace_graph(self, dataset: CareerDataset) -> SeedSummary:
        """Make the database exactly match the dataset (idempotent: safe to re-run)."""
        for node_type in schema.NODE_TYPES:
            # Labels come from the schema module, never from user input.
            await self._driver.execute_query(
                f"CREATE CONSTRAINT {node_type.label.lower()}_id IF NOT EXISTS "
                f"FOR (n:{node_type.label}) REQUIRE n.id IS UNIQUE",
                database_=self._database,
            )
        async with self._driver.session(database=self._database) as session:
            await session.execute_write(self._write, dataset)
        return SeedSummary(len(dataset.nodes), len(dataset.relationships))

    @staticmethod
    async def _write(tx: AsyncManagedTransaction, dataset: CareerDataset) -> None:
        await (await tx.run("MATCH (n) DETACH DELETE n")).consume()

        for label, rows in dataset.nodes_by_label().items():
            await (await tx.run(f"UNWIND $rows AS row CREATE (n:{label}) SET n = row", rows=rows)).consume()

        label_of = {node.id: node.label for node in dataset.nodes}
        grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
        for rel in dataset.relationships:
            key = (rel.type, label_of[rel.source], label_of[rel.target])
            grouped.setdefault(key, []).append({"source": rel.source, "target": rel.target})

        for (rel_type, source_label, target_label), rows in grouped.items():
            await (
                await tx.run(
                    f"UNWIND $rows AS row "
                    f"MATCH (a:{source_label} {{id: row.source}}) "
                    f"MATCH (b:{target_label} {{id: row.target}}) "
                    f"CREATE (a)-[:{rel_type}]->(b)",
                    rows=rows,
                )
            ).consume()
