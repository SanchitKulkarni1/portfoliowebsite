"""Load and validate the career dataset (data/career_graph.json) against the schema."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain import schema
from app.domain.errors import InvalidCareerDataError


@dataclass(frozen=True)
class NodeRecord:
    label: str
    properties: dict[str, Any]  # includes id and name

    @property
    def id(self) -> str:
        return self.properties["id"]


@dataclass(frozen=True)
class RelationshipRecord:
    type: str
    source: str
    target: str


@dataclass(frozen=True)
class CareerDataset:
    nodes: tuple[NodeRecord, ...]
    relationships: tuple[RelationshipRecord, ...]

    def nodes_by_label(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for node in self.nodes:
            grouped.setdefault(node.label, []).append(node.properties)
        return grouped

    def relationships_by_type(self) -> dict[str, list[dict[str, str]]]:
        grouped: dict[str, list[dict[str, str]]] = {}
        for rel in self.relationships:
            grouped.setdefault(rel.type, []).append({"source": rel.source, "target": rel.target})
        return grouped


def load_career_data(path: Path) -> CareerDataset:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidCareerDataError(f"Cannot read {path}: {exc}") from exc
    return parse_career_data(raw)


def parse_career_data(raw: dict[str, Any]) -> CareerDataset:
    errors: list[str] = []
    nodes: list[NodeRecord] = []
    labels_by_id: dict[str, str] = {}

    for index, item in enumerate(raw.get("nodes", [])):
        label = item.get("label")
        props = {k: v for k, v in item.items() if k != "label"}
        where = f"nodes[{index}] ({props.get('id', '?')})"
        if label not in schema.NODE_LABELS:
            errors.append(f"{where}: unknown label {label!r}")
            continue
        missing = [p for p in schema.BASE_PROPERTIES if not props.get(p)]
        if missing:
            errors.append(f"{where}: missing {', '.join(missing)}")
            continue
        unknown = set(props) - schema.allowed_properties(label)
        if unknown:
            errors.append(f"{where}: properties not in schema: {', '.join(sorted(unknown))}")
        if props["id"] in labels_by_id:
            errors.append(f"{where}: duplicate id")
        labels_by_id[props["id"]] = label
        nodes.append(NodeRecord(label, props))

    relationships: list[RelationshipRecord] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(raw.get("relationships", [])):
        rel_type, source, target = item.get("type"), item.get("source"), item.get("target")
        where = f"relationships[{index}] ({source}-{rel_type}->{target})"
        if source not in labels_by_id or target not in labels_by_id:
            errors.append(f"{where}: endpoint does not exist")
            continue
        if not schema.is_valid_relationship(rel_type, labels_by_id[source], labels_by_id[target]):
            errors.append(f"{where}: {labels_by_id[source]}-[{rel_type}]->{labels_by_id[target]} is not in the schema")
            continue
        if (source, rel_type, target) in seen:
            errors.append(f"{where}: duplicate relationship")
        seen.add((source, rel_type, target))
        relationships.append(RelationshipRecord(rel_type, source, target))

    if errors:
        raise InvalidCareerDataError("Invalid career data:\n  " + "\n  ".join(errors))
    return CareerDataset(tuple(nodes), tuple(relationships))
