"""Document ingestion API routes."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from api.app.auth import TenantContext, resolve_tenant_context
from api.app.dependencies import get_retrieval_service, get_tenant_auth_service
from api.ingestion.async_tasks import IngestionTaskPayload, enqueue_ingestion_task
from api.ingestion.parser import detect_document_type, parse_bytes
from api.ingestion.service import IngestionService
from api.retrieval.service import RetrievalService
from api.services.document_persistence import DocumentPersistenceService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def tenant_from_form(
    tenant_id: str = Form(...),
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
) -> TenantContext:
    return resolve_tenant_context(tenant_id, x_tenant_key)


def _ingestion_service(retrieval_service: RetrievalService) -> IngestionService:
    return IngestionService(
        embedding_provider=retrieval_service.embedding_provider,
        vector_store=retrieval_service.vector_store,
    )


def _list_documents(tenant_id: str) -> List[Dict[str, Any]]:
    if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
        return []
    try:
        from api.db.session import get_db_session
        from api.repositories.documents import DocumentRepository

        with get_db_session() as session:
            rows = DocumentRepository(session).list_documents_for_tenant(tenant_id)
            return [
                {
                    "id": str(row.id),
                    "tenant_id": str(row.tenant_id),
                    "title": row.title,
                    "document_type": row.document_type,
                    "chunk_count": row.chunk_count,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]
    except Exception:
        return []


@router.get("")
def list_documents(tenant_id: str, x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key")) -> Dict[str, Any]:
    tenant = resolve_tenant_context(tenant_id, x_tenant_key)
    return {"tenant_id": tenant.id, "documents": _list_documents(tenant.id)}


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    tenant_id: str,
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
) -> Dict[str, Any]:
    tenant = resolve_tenant_context(tenant_id, x_tenant_key)
    if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
        raise HTTPException(status_code=503, detail="Document delete requires PostgreSQL (SKIP_DB=false).")
    from api.db.session import get_db_session
    from api.repositories.documents import DocumentRepository

    with get_db_session() as session:
        repo = DocumentRepository(session)
        document = repo.get_document(document_id)
        if document is None or str(document.tenant_id) != tenant.id:
            raise HTTPException(status_code=404, detail="Document not found.")
        repo.delete_document(document_id)
    return {"tenant_id": tenant.id, "document_id": document_id, "deleted": True}


@router.post("/upload")
async def upload_document(
    title: str = Form(...),
    document_type: str = Form("txt"),
    source: str = Form("upload"),
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(tenant_from_form),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> Dict[str, Any]:
    auth_service = get_tenant_auth_service()
    auth_service.enforce_document_quota(tenant)

    raw_bytes = await file.read()
    filename = file.filename or title
    doc_type = document_type if document_type != "txt" else detect_document_type(filename)
    parsed_text = parse_bytes(raw_bytes, doc_type, filename=filename)
    document_id = filename or title
    service = _ingestion_service(retrieval_service)
    result = service.ingest_document(
        tenant_id=tenant.id,
        document_id=document_id,
        title=title,
        content=parsed_text,
        document_type=doc_type,
        source=source,
    )

    persistence = DocumentPersistenceService()
    persisted = persistence.persist_ingestion(
        tenant_id=tenant.id,
        title=title,
        content=parsed_text,
        document_type=doc_type,
        source=source,
        chunk_records=result.get("chunk_records", []),
        embedding_model=str(result.get("embedding_model", "")),
    )
    response = {"tenant_id": tenant.id, **result}
    if persisted is not None:
        response["postgres_document_id"] = persisted["document_id"]
        response["postgres_persisted"] = True
    get_tenant_auth_service().record_document_upload(tenant.id)
    return response


@router.post("/upload/async")
async def upload_document_async(
    title: str = Form(...),
    document_type: str = Form("txt"),
    source: str = Form("upload"),
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(tenant_from_form),
) -> Dict[str, Any]:
    auth_service = get_tenant_auth_service()
    auth_service.enforce_document_quota(tenant)

    from api.ingestion.storage import get_raw_file_storage

    raw_bytes = await file.read()
    filename = file.filename or title
    location = get_raw_file_storage().write_bytes(f"{tenant.id}/{filename}", raw_bytes)
    payload = IngestionTaskPayload(
        tenant_id=tenant.id,
        title=title,
        document_type=document_type if document_type != "txt" else detect_document_type(filename),
        source=source,
        document_id=filename,
        raw_location=location,
    )
    queued = enqueue_ingestion_task(payload)
    get_tenant_auth_service().record_document_upload(tenant.id)
    return {"tenant_id": tenant.id, "queued": queued}
