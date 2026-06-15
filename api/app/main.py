"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes.rag import router as rag_router

from .health import SERVICE_VERSION, router as health_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Self-Optimizing RAG Platform",
        version=SERVICE_VERSION,
    )

    app.include_router(health_router)
    app.include_router(rag_router)

    return app


app = create_app()
