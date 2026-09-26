"""Core value objects shared by every layer. Pure data, no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

JsonValue = Any  # anything json.dumps can serialise


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    name: str
    properties: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    type: str

    @property
    def id(self) -> str:
        return f"{self.source}-{self.type}-{self.target}"


@dataclass(frozen=True)
class Subgraph:
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()

    @staticmethod
    def merge(nodes: list[GraphNode], edges: list[GraphEdge]) -> Subgraph:
        """Build a subgraph, de-duplicating nodes by id and edges by (source, type, target)."""
        unique_nodes = {node.id: node for node in nodes}
        unique_edges = {edge.id: edge for edge in edges}
        return Subgraph(tuple(unique_nodes.values()), tuple(unique_edges.values()))


@dataclass(frozen=True)
class SafeCypher:
    """A query that has passed CypherGuard. Only the guard should construct these."""

    text: str


@dataclass(frozen=True)
class QueryResult:
    rows: tuple[dict[str, JsonValue], ...]
    subgraph: Subgraph

    @property
    def is_empty(self) -> bool:
        return not self.rows


class ChatStatus(StrEnum):
    ANSWERED = "answered"
    NO_RESULTS = "no_results"
    OFF_TOPIC = "off_topic"
    REFUSED = "refused"
    FAILED = "failed"


@dataclass(frozen=True)
class ChatAnswer:
    status: ChatStatus
    answer: str
    cypher: str | None = None
    subgraph: Subgraph = Subgraph()
