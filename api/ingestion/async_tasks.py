"""Async ingestion task interface for worker/Celery execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class IngestionTaskPayload:
    tenant_id: str
    title: str
    document_type: str
    source: str
    document_id: Optional[str] = None
    raw_location: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "title": self.title,
            "document_type": self.document_type,
            "source": self.source,
            "document_id": self.document_id,
            "raw_location": self.raw_location,
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IngestionTaskPayload":
        return cls(
            tenant_id=str(data["tenant_id"]),
            title=str(data["title"]),
            document_type=str(data.get("document_type", "txt")),
            source=str(data.get("source", "async")),
            document_id=data.get("document_id"),
            raw_location=data.get("raw_location"),
            content=data.get("content"),
            metadata=dict(data.get("metadata") or {}),
        )


def enqueue_ingestion_task(payload: IngestionTaskPayload) -> Dict[str, Any]:
    """Enqueue ingestion via Celery when available, otherwise Redis/in-memory queue."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    body = payload.to_dict()
    try:
        from worker.ingest import ingest_document_task, is_celery_enabled

        if is_celery_enabled():
            async_result = ingest_document_task.delay(body)
            return {"backend": "celery", "task_id": async_result.id, "status": "queued"}
    except ImportError:
        pass

    from api.worker.queue import get_task_queue

    queued = get_task_queue().enqueue("ingest", body)
    return {"backend": get_task_queue().backend, "task_id": queued.task_id, "status": "queued"}
