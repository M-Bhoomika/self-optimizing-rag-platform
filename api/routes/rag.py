"""RAG API routes."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header

from api.app.auth import TenantContext, resolve_tenant_context
from api.app.dependencies import (
    get_embedding_provider_cached,
    get_query_persistence,
    get_rag_service,
    get_settings_cached,
    get_tenant_auth_service,
    get_vector_store_cached,
)
from api.config.settings import ApplicationSettings
from api.rag.schemas import RAGRequest, RAGResponse
from api.rag.service import RAGService
from api.services.query_persistence import QueryPersistenceService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

SERVICE_NAME = "Self-Optimizing RAG Platform"
SERVICE_VERSION = "0.1.0"


class QueryRequest(RAGRequest):
    """Request body for the RAG query endpoint."""


class QueryResponse(RAGResponse):
    """Response body for the RAG query endpoint."""


def rag_tenant(
    request: QueryRequest,
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
) -> TenantContext:
    return resolve_tenant_context(request.tenant_id, x_tenant_key)


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    tenant: TenantContext = Depends(rag_tenant),
    rag_service: RAGService = Depends(get_rag_service),
    persistence: QueryPersistenceService = Depends(get_query_persistence),
) -> RAGResponse:
    """Run the iterative RAG pipeline and return contexts with a generated answer."""
    started = time.perf_counter()
    response = rag_service.retrieve_context(
        RAGRequest(tenant_id=tenant.id, query=request.query, top_k=request.top_k)
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    get_tenant_auth_service().record_query_usage(tenant.id)
    persistence.persist_query(
        tenant_id=tenant.id,
        query_text=request.query,
        answer_text=response.generated_answer,
        retrieved_chunk_ids=[c.chunk_id for c in response.contexts],
        latency_ms=latency_ms,
        model_version=response.model,
        cached=False,
        context_text=RAGService.build_context_string(response.contexts) or None,
    )
    return response


@router.get("/config")
def config(
    settings: ApplicationSettings = Depends(get_settings_cached),
) -> Dict[str, Any]:
    """Return the current application configuration."""
    return settings.to_dict()


@router.get("/health/details")
def health_details() -> Dict[str, Any]:
    """Return service health details with active backend identifiers."""
    settings = get_settings_cached()
    embedding = get_embedding_provider_cached()
    vector_store = get_vector_store_cached()
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "retrieval_backend": settings.retrieval.backend,
        "vector_store_class": vector_store.__class__.__name__,
        "embedding_backend": embedding.model_name,
        "embedding_dimension": embedding.dimension,
        "auth_required": settings.auth.required,
    }
