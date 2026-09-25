"""Neo4j adapter for the GraphRepository port."""

from __future__ import annotations

from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, Query, RoutingControl
from neo4j.exceptions import DriverError, Neo4jError, ServiceUnavailable, SessionExpired
from neo4j.graph import Node, Path, Relationship
from neo4j.time import Date, DateTime, Duration, Time

from app.domain import schema
from app.domain.errors import GraphUnavailableError, QueryExecutionError, QueryTimeoutError
from app.domain.models import GraphEdge, GraphNode, JsonValue, QueryResult, SafeCypher, Subgraph


def create_driver(uri: str, user: str, password: str) -> AsyncDriver:
    return AsyncGraphDatabase.driver(uri, auth=(user, password))


class Neo4jGraphRepository:
    def __init__(self, driver: AsyncDriver, *, database: str, timeout_seconds: float) -> None:
        self._driver = driver
        self._database = database
        self._timeout = timeout_seconds

    async def run_read(self, query: SafeCypher) -> QueryResult:
        records = await self._read(query.text)
        return _ResultConverter(records).convert()

    async def fetch_snapshot(self) -> Subgraph:
        node_records = await self._read("MATCH (n) RETURN n")
        edge_records = await self._read("MATCH (a)-[r]->(b) RETURN a.id AS source, type(r) AS type, b.id AS target")
        nodes = [_to_graph_node(record["n"]) for record in node_records]
        edges = [GraphEdge(r["source"], r["target"], r["type"]) for r in edge_records]
        return Subgraph.merge([n for n in nodes if n is not None], edges)

    async def ping(self) -> bool:
        try:
            await self._driver.verify_connectivity()
            return True
        except (DriverError, Neo4jError, OSError):
            return False

    async def _read(self, cypher: str) -> list[Any]:
        """Run in a READ transaction: the database itself rejects any write."""
        try:
            result = await self._driver.execute_query(
                Query(cypher, timeout=self._timeout),
                routing_=RoutingControl.READ,
                database_=self._database,
            )
        except (ServiceUnavailable, SessionExpired) as exc:
            raise GraphUnavailableError(str(exc)) from exc
        except Neo4jError as exc:
            if "TransactionTimedOut" in (exc.code or ""):
                raise QueryTimeoutError(exc.message or str(exc)) from exc
            raise QueryExecutionError(exc.message or str(exc)) from exc
        except DriverError as exc:
            raise QueryExecutionError(str(exc)) from exc
        return result.records


def _to_graph_node(node: Node) -> GraphNode | None:
    props = dict(node)
    node_id = props.pop("id", None)
    if node_id is None:
        return None  # not part of the career graph
    name = props.pop("name", node_id)
    labels = sorted(node.labels)
    label = next((lbl for lbl in labels if lbl in schema.NODE_LABELS), labels[0] if labels else "Node")
    return GraphNode(id=node_id, label=label, name=name, properties=_jsonable(props))


def _jsonable(value: Any) -> JsonValue:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (Date, DateTime, Time, Duration)):
        return str(value)
    return value


class _ResultConverter:
    """Turns driver records into JSON rows (for the LLM) plus a subgraph (for highlighting).

    A relationship only carries its endpoints' element ids, so nodes are collected
    first and edges are resolved against them afterwards.
    """

    def __init__(self, records: list[Any]) -> None:
        self._records = records
        self._nodes: dict[str, GraphNode] = {}  # element_id -> node
        self._relationships: list[Relationship] = []

    def convert(self) -> QueryResult:
        for record in self._records:
            for value in record.values():
                self._collect(value)
        rows = tuple({key: self._serialise(value) for key, value in record.items()} for record in self._records)
        edges = [edge for rel in self._relationships if (edge := self._to_edge(rel)) is not None]
        return QueryResult(rows, Subgraph.merge(list(self._nodes.values()), edges))

    def _collect(self, value: Any) -> None:
        if isinstance(value, Node):
            self._add_node(value)
        elif isinstance(value, Relationship):
            self._relationships.append(value)
            for endpoint in (value.start_node, value.end_node):
                if endpoint is not None:
                    self._add_node(endpoint)
        elif isinstance(value, Path):
            for node in value.nodes:
                self._add_node(node)
            self._relationships.extend(value.relationships)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._collect(item)
        elif isinstance(value, dict):
            for item in value.values():
                self._collect(item)

    def _add_node(self, node: Node) -> None:
        if node.element_id not in self._nodes and (graph_node := _to_graph_node(node)) is not None:
            self._nodes[node.element_id] = graph_node

    def _to_edge(self, rel: Relationship) -> GraphEdge | None:
        start = self._nodes.get(rel.start_node.element_id) if rel.start_node else None
        end = self._nodes.get(rel.end_node.element_id) if rel.end_node else None
        if start is None or end is None:
            return None
        return GraphEdge(start.id, end.id, rel.type)

    def _serialise(self, value: Any) -> JsonValue:
        if isinstance(value, Node):
            node = self._nodes.get(value.element_id)
            if node is None:
                return _jsonable(dict(value))
            return {"label": node.label, "id": node.id, "name": node.name, **node.properties}
        if isinstance(value, Relationship):
            edge = self._to_edge(value)
            return {
                "type": value.type,
                "source": edge.source if edge else None,
                "target": edge.target if edge else None,
            }
        if isinstance(value, Path):
            return {
                "nodes": [self._serialise(n) for n in value.nodes],
                "relationships": [self._serialise(r) for r in value.relationships],
            }
        if isinstance(value, (list, tuple)):
            return [self._serialise(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialise(v) for k, v in value.items()}
        return _jsonable(value)
