"""RAG API routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from api.app.dependencies import get_rag_service, get_settings
from api.config.settings import ApplicationSettings
from api.rag.schemas import RAGContext, RAGRequest, RAGResponse
from api.rag.service import RAGService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

SERVICE_NAME = "Self-Optimizing RAG Platform"
SERVICE_VERSION = "0.1.0"


class QueryRequest(RAGRequest):
    """Request body for the RAG query endpoint."""


class QueryResponse(RAGResponse):
    """Response body for the RAG query endpoint."""


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGResponse:
    """Retrieve context for a query and return the (placeholder) answer."""
    return rag_service.retrieve_context(request)


@router.get("/config")
def config(
    settings: ApplicationSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Return the current application configuration."""
    return settings.to_dict()


@router.get("/health/details")
def health_details() -> Dict[str, Any]:
    """Return service health details with backend identifiers (placeholders)."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "retrieval_backend": "in-memory",
        "embedding_backend": "dummy",
    }
