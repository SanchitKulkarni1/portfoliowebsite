"""External API contract: request/response models for /api/v1.

These DTOs are the public shape the frontend builds against. Keep them stable;
map to and from domain models here rather than exposing domain types directly.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.models import ChatAnswer, ChatStatus, GraphEdge, GraphNode, Subgraph

MAX_QUESTION_LENGTH = 300


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH, examples=["What did you build at Evenflow?"])

    @field_validator("question")
    @classmethod
    def _normalise(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("question must not be blank")
        return collapsed


class NodeOut(BaseModel):
    id: str
    label: str
    name: str
    properties: dict[str, Any]

    @classmethod
    def from_domain(cls, node: GraphNode) -> NodeOut:
        return cls(id=node.id, label=node.label, name=node.name, properties=node.properties)


class EdgeOut(BaseModel):
    id: str
    source: str
    target: str
    type: str

    @classmethod
    def from_domain(cls, edge: GraphEdge) -> EdgeOut:
        return cls(id=edge.id, source=edge.source, target=edge.target, type=edge.type)


class GraphOut(BaseModel):
    nodes: list[NodeOut]
    edges: list[EdgeOut]

    @classmethod
    def from_domain(cls, subgraph: Subgraph) -> GraphOut:
        return cls(
            nodes=[NodeOut.from_domain(n) for n in subgraph.nodes],
            edges=[EdgeOut.from_domain(e) for e in subgraph.edges],
        )


class ChatResponse(BaseModel):
    status: ChatStatus = Field(
        description="answered | no_results | off_topic | refused | failed. Every status carries a displayable `answer`."
    )
    answer: str
    cypher: str | None = Field(description="The query that was executed, if any.")
    nodes: list[NodeOut] = Field(description="Nodes the query touched, for highlighting.")
    edges: list[EdgeOut] = Field(description="Relationships the query touched, for highlighting.")

    @classmethod
    def from_domain(cls, answer: ChatAnswer) -> ChatResponse:
        graph = GraphOut.from_domain(answer.subgraph)
        return cls(
            status=answer.status, answer=answer.answer, cypher=answer.cypher, nodes=graph.nodes, edges=graph.edges
        )


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unavailable"]
    neo4j: Literal["up", "down"]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
