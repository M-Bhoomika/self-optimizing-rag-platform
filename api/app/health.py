"""Health and readiness endpoints."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import text

from api.cache.redis_cache import RedisCache
from api.config.settings import get_settings
from api.retrieval.factory import get_vector_store

logger = logging.getLogger(__name__)

SERVICE_NAME = "Self-Optimizing RAG Platform"
SERVICE_VERSION = "0.1.0"

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Basic liveness check."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@router.get("/health/ready")
def readiness() -> Dict[str, Any]:
    """Readiness probe with dependency checks."""
    settings = get_settings()
    checks: Dict[str, Any] = {
        "database": {"status": "skipped"},
        "redis": {"status": "skipped"},
        "vector_store": {"status": "ok"},
    }

    try:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            checks["database"] = {"status": "skipped", "reason": "SKIP_DB=true"}
        else:
            from api.db.session import get_db_session

            with get_db_session() as session:
                session.execute(text("SELECT 1"))
                checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "unavailable", "error": str(exc)}

    try:
        cache = RedisCache(redis_url=settings.cache.redis_url, default_ttl=settings.cache.ttl)
        checks["redis"] = {"status": "ok" if cache.enabled else "memory_fallback"}
    except Exception as exc:
        checks["redis"] = {"status": "unavailable", "error": str(exc)}

    try:
        store = get_vector_store()
        checks["vector_store"] = {
            "status": "ok",
            "backend": settings.retrieval.backend,
            "class": store.__class__.__name__,
        }
    except Exception as exc:
        checks["vector_store"] = {"status": "unavailable", "error": str(exc)}

    overall = "ok" if all(item.get("status") in {"ok", "skipped", "memory_fallback"} for item in checks.values()) else "degraded"
    return {
        "status": overall,
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "checks": checks,
    }
