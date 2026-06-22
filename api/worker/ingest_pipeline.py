"""Full ingestion pipeline for worker/Celery tasks."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from api.ingestion.async_tasks import IngestionTaskPayload
from api.ingestion.parser import detect_document_type, parse_bytes
from api.ingestion.service import IngestionService
from api.ingestion.storage import get_raw_file_storage
from api.retrieval.factory import get_vector_store
from api.services.document_persistence import DocumentPersistenceService

logger = logging.getLogger(__name__)


def _resolve_content(payload: IngestionTaskPayload) -> tuple[str, str]:
    if payload.content:
        doc_type = payload.document_type or detect_document_type(payload.source or payload.title)
        parsed = parse_bytes(payload.content.encode("utf-8"), doc_type, filename=payload.title)
        return parsed, doc_type

    if not payload.raw_location:
        raise ValueError("Ingestion task requires content or raw_location.")

    storage = get_raw_file_storage(prefer_s3=payload.raw_location.startswith("s3://"))
    raw_bytes = storage.read_bytes(payload.raw_location)
    doc_type = payload.document_type or detect_document_type(payload.raw_location)
    parsed = parse_bytes(raw_bytes, doc_type, filename=payload.raw_location)
    return parsed, doc_type


def run_full_ingestion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Download/read -> extract -> chunk -> embed -> store in configured backends."""
    task = IngestionTaskPayload.from_dict(payload)
    parsed_text, document_type = _resolve_content(task)
    document_id = task.document_id or task.title

    from api.app.dependencies import get_retrieval_service

    retrieval = get_retrieval_service()
    primary_store = retrieval.vector_store
    service = IngestionService(
        embedding_provider=retrieval.embedding_provider,
        vector_store=primary_store,
    )
    result = service.ingest_document(
        tenant_id=task.tenant_id,
        document_id=document_id,
        title=task.title,
        content=parsed_text,
        document_type=document_type,
        source=task.source,
    )

    secondary_backends: Dict[str, Any] = {}
    for backend in ("chroma", "pgvector"):
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"} and backend == "pgvector":
            continue
        try:
            store = get_vector_store(backend)
            if store.__class__ is primary_store.__class__:
                continue
            secondary = IngestionService(
                embedding_provider=retrieval.embedding_provider,
                vector_store=store,
            )
            secondary.ingest_document(
                tenant_id=task.tenant_id,
                document_id=document_id,
                title=task.title,
                content=parsed_text,
                document_type=document_type,
                source=task.source,
            )
            secondary_backends[backend] = store.__class__.__name__
        except Exception as exc:
            logger.warning("Secondary backend %s skipped: %s", backend, exc)

    persisted = DocumentPersistenceService().persist_ingestion(
        tenant_id=task.tenant_id,
        title=task.title,
        content=parsed_text,
        document_type=document_type,
        source=task.source,
        chunk_records=result.get("chunk_records", []),
        embedding_model=str(result.get("embedding_model", "")),
    )

    return {
        "status": "completed",
        "ingestion": result,
        "secondary_backends": secondary_backends,
        "postgres": persisted,
    }
