"""HTTP routes. Thin: validate input, call a service, map the result to a DTO."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import enforce_chat_rate_limit, get_chat_service, get_graph_service
from app.api.errors import LLM_BUSY_MESSAGE, LLM_UNAVAILABLE_MESSAGE
from app.api.schemas import ChatRequest, ChatResponse, ErrorResponse, GraphOut, HealthResponse, ReadinessResponse
from app.domain.errors import LanguageModelBusyError, LanguageModelError
from app.services.chat_service import ChatService, PreparedAnswer
from app.services.graph_service import GraphService
from app.services.timing import StageTimings

logger = logging.getLogger(__name__)

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


@api_router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-sent events: `meta` (status, cypher, nodes, edges), then `delta` "
            "chunks of answer text, then `done` with the full answer; or `error` if the answer fails mid-stream.",
        },
        **_ERRORS,
    },
    dependencies=[Depends(enforce_chat_rate_limit)],
    summary="Ask a question and stream the answer",
)
async def chat_stream(body: ChatRequest, chat_service: ChatService = Depends(get_chat_service)) -> StreamingResponse:
    # Everything before the final LLM call runs here, so its failures still get a normal
    # HTTP error envelope. Only the answer text is streamed.
    timings = StageTimings()
    prepared = await chat_service.prepare(body.question, timings)
    return StreamingResponse(
        _answer_events(chat_service, prepared, timings),
        media_type="text/event-stream",
        headers={
            "Server-Timing": timings.as_server_timing(),
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _answer_events(
    chat_service: ChatService, prepared: PreparedAnswer, timings: StageTimings
) -> AsyncIterator[str]:
    yield _sse("meta", ChatResponse.from_domain(prepared.answer).model_dump(exclude={"answer"}))
    parts: list[str] = []
    try:
        async for chunk in chat_service.stream(prepared, timings):
            parts.append(chunk)
            yield _sse("delta", {"text": chunk})
    except LanguageModelBusyError as exc:
        logger.warning("LLM busy mid-stream: %s", exc)
        yield _sse("error", {"code": "llm_busy", "message": LLM_BUSY_MESSAGE})
        return
    except LanguageModelError as exc:
        logger.error("LLM failed mid-stream: %s", exc)
        yield _sse("error", {"code": "llm_unavailable", "message": LLM_UNAVAILABLE_MESSAGE})
        return
    yield _sse("done", {"answer": "".join(parts).strip()})
