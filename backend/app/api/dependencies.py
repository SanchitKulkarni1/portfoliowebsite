"""FastAPI dependency providers. Routes get services from here, never by constructing them."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.api.state import Container
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_chat_service(container: Container = Depends(get_container)) -> ChatService:
    return container.chat_service


def get_graph_service(container: Container = Depends(get_container)) -> GraphService:
    return container.graph_service


def enforce_chat_rate_limit(request: Request, container: Container = Depends(get_container)) -> None:
    # request.client is the real client IP when uvicorn runs with --proxy-headers behind Render's proxy.
    client = request.client.host if request.client else "unknown"
    decision = container.chat_rate_limiter.hit(client)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many questions. Please wait a few minutes and try again.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )
