"""HTTP routes. Thin: validate input, call a service, map the result to a DTO."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import enforce_chat_rate_limit, get_chat_service, get_graph_service
from app.api.schemas import ChatRequest, ChatResponse, ErrorResponse, GraphOut, HealthResponse, ReadinessResponse
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService
from app.services.timing import StageTimings

health_router = APIRouter(tags=["health"])
api_router = APIRouter(prefix="/api/v1", tags=["career-graph"])

_ERRORS = {
    429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    503: {"model": ErrorResponse, "description": "Graph database or LLM unavailable"},
}


@health_router.get("/health", response_model=HealthResponse, summary="Liveness (no dependencies checked)")
async def health() -> HealthResponse:
    return HealthResponse()


@health_router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
    summary="Readiness (checks Neo4j connectivity)",
)
async def ready(response: Response, graph: GraphService = Depends(get_graph_service)) -> ReadinessResponse:
    if await graph.is_ready():
        return ReadinessResponse(status="ready", neo4j="up")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="unavailable", neo4j="down")


@api_router.get("/graph", response_model=GraphOut, responses=_ERRORS, summary="Full career graph snapshot")
async def get_graph(graph: GraphService = Depends(get_graph_service)) -> GraphOut:
    return GraphOut.from_domain(await graph.snapshot())


@api_router.post(
    "/chat",
    response_model=ChatResponse,
    responses=_ERRORS,
    dependencies=[Depends(enforce_chat_rate_limit)],
    summary="Ask a question about Sanchit's career",
)
async def chat(
    body: ChatRequest, response: Response, chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    timings = StageTimings()
    answer = await chat_service.ask(body.question, timings)
    response.headers["Server-Timing"] = timings.as_server_timing()
    return ChatResponse.from_domain(answer)
