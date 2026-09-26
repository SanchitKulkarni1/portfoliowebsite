"""Map exceptions to the API's error envelope: {"error": {"code": ..., "message": ...}}."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.schemas import ErrorBody, ErrorResponse
from app.domain.errors import CareerGraphError, GraphUnavailableError, LanguageModelBusyError, LanguageModelError

LLM_BUSY_RETRY_AFTER_SECONDS = 30

logger = logging.getLogger(__name__)

_HTTP_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def _error(status_code: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(part) for part in first.get("loc", ())[1:]) or "body"
        return _error(422, "invalid_request", f"{field}: {first.get('msg', 'invalid input')}")

    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return _error(exc.status_code, code, str(exc.detail), exc.headers)

    @app.exception_handler(LanguageModelBusyError)
    async def _llm_busy(_: Request, exc: LanguageModelBusyError) -> JSONResponse:
        logger.warning("LLM busy: %s", exc)
        return _error(
            503,
            "llm_busy",
            "The assistant is getting a lot of questions right now. Please try again in a minute.",
            {"Retry-After": str(LLM_BUSY_RETRY_AFTER_SECONDS)},
        )

    @app.exception_handler(LanguageModelError)
    async def _llm(_: Request, exc: LanguageModelError) -> JSONResponse:
        logger.error("LLM unavailable: %s", exc)
        return _error(503, "llm_unavailable", "The assistant is temporarily unavailable. Please try again shortly.")

    @app.exception_handler(GraphUnavailableError)
    async def _graph(_: Request, exc: GraphUnavailableError) -> JSONResponse:
        logger.error("Graph unavailable: %s", exc)
        return _error(
            503, "graph_unavailable", "The career graph is temporarily unavailable. Please try again shortly."
        )

    @app.exception_handler(CareerGraphError)
    async def _domain(_: Request, exc: CareerGraphError) -> JSONResponse:
        logger.exception("Unhandled domain error", exc_info=exc)
        return _error(500, "internal_error", "Something went wrong.")
