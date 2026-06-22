"""HTTP middleware for Prometheus metrics."""

from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .metrics import get_metrics


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records request count and latency when prometheus_client is available."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        metrics = get_metrics()
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        if metrics.enabled:
            path = request.url.path
            method = request.method
            status = str(response.status_code)
            metrics.request_count.labels(method=method, path=path, status=status).inc()
            metrics.request_latency_seconds.labels(method=method, path=path).observe(elapsed)
        return response
