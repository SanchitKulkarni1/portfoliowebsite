"""Application factory. Run with: uvicorn app.main:create_app --factory"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import api_router, health_router
from app.config import Settings, get_settings
from app.container import Container, build_container

ContainerFactory = Callable[[Settings], Awaitable[Container]]


def create_app(settings: Settings | None = None, container_factory: ContainerFactory = build_container) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = await container_factory(settings)
        app.state.container = container
        warm_up = asyncio.create_task(container.warm_up())
        try:
            yield
        finally:
            warm_up.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await warm_up
            await container.close()

    app = FastAPI(
        title="Career Graph API",
        version="1.0.0",
        description="Ask questions about Sanchit Kulkarni's career. Answered with text-to-Cypher over a Neo4j knowledge graph.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=settings.allowed_origin_regex,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        max_age=600,
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    return app
