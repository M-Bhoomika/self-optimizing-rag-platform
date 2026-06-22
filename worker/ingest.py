"""Celery-compatible ingestion tasks with synchronous fallback."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

_celery_app = None
_celery_enabled = False

try:
    from celery import Celery  # type: ignore

    _celery_app = Celery(
        "rag_platform",
        broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
        backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
    )
    _celery_enabled = os.getenv("CELERY_ENABLED", "").lower() in {"1", "true", "yes"}
except ImportError:
    _celery_app = None
    _celery_enabled = False


def is_celery_enabled() -> bool:
    return _celery_app is not None and _celery_enabled


def _run_ingest(payload: Dict[str, Any]) -> Dict[str, Any]:
    from api.worker.ingest_pipeline import run_full_ingestion

    return run_full_ingestion(payload)


if _celery_app is not None:

    @_celery_app.task(name="rag.ingest_document")
    def ingest_document_task(payload: Dict[str, Any]) -> Dict[str, Any]:
        return _run_ingest(payload)

else:

    def ingest_document_task(payload: Dict[str, Any]) -> Dict[str, Any]:
        return _run_ingest(payload)

    ingest_document_task.delay = lambda payload: _SyncAsyncResult(_run_ingest(payload))  # type: ignore[attr-defined]


class _SyncAsyncResult:
    def __init__(self, result: Dict[str, Any]) -> None:
        self.id = "sync-ingest"
        self._result = result

    def get(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        return self._result
