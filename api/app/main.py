"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from api.config.settings import get_settings
from api.observability.logging import configure_logging
from api.observability.metrics import get_metrics
from api.observability.middleware import PrometheusMiddleware
from api.observability.tracing import setup_tracing
from api.routes.admin import router as admin_router
from api.routes.documents import router as documents_router
from api.routes.experiments import router as experiments_router
from api.routes.query import router as query_router
from api.routes.rag import router as rag_router

from .health import SERVICE_VERSION, router as health_router
from .middleware import TenantAuthMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Self-Optimizing RAG Platform",
        version=SERVICE_VERSION,
    )

    metrics = get_metrics()
    if metrics.enabled:
        app.add_middleware(PrometheusMiddleware)
    app.add_middleware(TenantAuthMiddleware)

    setup_tracing(app)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled error",
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(health_router)
    app.include_router(rag_router)
    app.include_router(query_router)
    app.include_router(documents_router)
    app.include_router(experiments_router)
    app.include_router(admin_router)

    @app.get("/metrics")
    def metrics_endpoint() -> PlainTextResponse:
        if not metrics.enabled:
            return PlainTextResponse(
                "prometheus_client not installed\n",
                status_code=503,
            )
        from prometheus_client import generate_latest  # type: ignore

        return PlainTextResponse(
            generate_latest().decode("utf-8"),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


app = create_app()
