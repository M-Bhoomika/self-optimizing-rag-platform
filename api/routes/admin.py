"""Admin API routes for tenant and platform status."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from api.app.auth import _MEMORY_TENANTS
from api.cache.redis_cache import RedisCache
from api.config.settings import get_settings
from api.retrieval.factory import get_vector_store
from api.services.document_persistence import DocumentPersistenceService
from api.services.experiment_persistence import ExperimentPersistenceService
from api.services.query_persistence import QueryPersistenceService
from api.worker.queue import get_task_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _list_db_tenants(limit: int = 50) -> List[Dict[str, Any]]:
    if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
        return []
    try:
        from api.db.session import get_db_session
        from api.models.tenant import Tenant
        from sqlalchemy import select

        with get_db_session() as session:
            rows = session.execute(select(Tenant).limit(limit)).scalars().all()
            return [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "document_quota": row.document_quota,
                    "query_quota_per_day": row.query_quota_per_day,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]
    except Exception as exc:
        logger.debug("Admin tenant list unavailable: %s", exc)
        return []


@router.get("/status")
def platform_status() -> Dict[str, Any]:
    settings = get_settings()
    cache = RedisCache(redis_url=settings.cache.redis_url, default_ttl=settings.cache.ttl)
    queue = get_task_queue()
    store = get_vector_store()
    return {
        "service": "Self-Optimizing RAG Platform",
        "auth_required": settings.auth.required,
        "retrieval_backend": settings.retrieval.backend,
        "vector_store_class": store.__class__.__name__,
        "embedding_provider": settings.embedding.provider,
        "cache_backend": "redis" if cache.enabled else "memory",
        "worker_queue_backend": queue.backend,
        "worker_queue_depth": queue.depth(),
        "skip_db": os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"},
    }


@router.get("/config")
def platform_config() -> Dict[str, Any]:
    return get_settings().to_dict()


@router.get("/tenants")
def list_tenants(limit: int = 50) -> Dict[str, Any]:
    db_tenants = _list_db_tenants(limit=limit)
    if db_tenants:
        return {"source": "postgres", "tenants": db_tenants}

    memory_tenants = [
        {
            "id": tenant.id,
            "name": tenant.name,
            "document_quota": tenant.document_quota,
            "query_quota_per_day": tenant.query_quota_per_day,
        }
        for tenant in _MEMORY_TENANTS.values()
    ]
    return {"source": "memory", "tenants": memory_tenants[:limit]}


@router.get("/tenants/{tenant_id}/stats")
def tenant_stats(tenant_id: str) -> Dict[str, Any]:
    doc_service = DocumentPersistenceService()
    query_service = QueryPersistenceService()
    document_count = doc_service.count_documents(tenant_id)
    queries = query_service.list_history(tenant_id, limit=1000)
    return {
        "tenant_id": tenant_id,
        "document_count": document_count,
        "query_count": len(queries),
        "recent_queries": queries[:10],
    }


@router.get("/experiments")
def list_persisted_experiments(limit: int = 50) -> Dict[str, Any]:
    rows = ExperimentPersistenceService().list_persisted(limit=limit)
    return {"count": len(rows), "experiments": rows}
