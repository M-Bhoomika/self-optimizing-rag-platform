"""Authentication middleware for tenant API key enforcement."""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.config.settings import get_settings

_PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
)


class TenantAuthMiddleware(BaseHTTPMiddleware):
    """Require ``X-Tenant-Key`` on protected API routes when auth is enabled."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        path = request.url.path

        if not settings.auth.required or not path.startswith("/api/"):
            return await call_next(request)
        if any(path == prefix or path.startswith(f"{prefix}/") for prefix in _PUBLIC_PREFIXES):
            return await call_next(request)

        header_name = settings.auth.header_name
        api_key = request.headers.get(header_name)
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Missing {header_name} header."},
            )

        request.state.tenant_api_key = api_key
        return await call_next(request)
