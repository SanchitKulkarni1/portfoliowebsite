"""Render the career dataset as self-contained Cypher statements (data inlined as literals).

Shared by scripts/export_cypher.py (paste into the Aura console) and the HTTP seeder
(Aura's Query API takes one statement per request and no driver-side batching).
"""

from __future__ import annotations

import json
from typing import Any

from app.domain import schema
from app.domain.career_data import CareerDataset

COUNT_STATEMENT = "MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS relationships"


def _literal(value: Any) -> str:
    """Render a JSON value as a Cypher literal. json.dumps' escaping is valid Cypher string syntax."""
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key}: {_literal(v)}" for key, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_literal(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=True)


def seed_statements(dataset: CareerDataset) -> list[str]:
    """Statements that replace the database contents with the dataset. Labels come from the schema."""
    statements = [
        f"CREATE CONSTRAINT {t.label.lower()}_id IF NOT EXISTS FOR (n:{t.label}) REQUIRE n.id IS UNIQUE"
        for t in schema.NODE_TYPES
    ]
    statements.append("MATCH (n) DETACH DELETE n")

    for label, rows in dataset.nodes_by_label().items():
        statements.append(f"UNWIND {_literal(rows)} AS row\nCREATE (n:{label}) SET n = row")

    label_of = {node.id: node.label for node in dataset.nodes}
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for rel in dataset.relationships:
        key = (rel.type, label_of[rel.source], label_of[rel.target])
        grouped.setdefault(key, []).append({"source": rel.source, "target": rel.target})
    for (rel_type, source_label, target_label), rows in grouped.items():
        statements.append(
            f"UNWIND {_literal(rows)} AS row\n"
            f"MATCH (a:{source_label} {{id: row.source}})\n"
            f"MATCH (b:{target_label} {{id: row.target}})\n"
            f"CREATE (a)-[:{rel_type}]->(b)"
        )
    return statements
