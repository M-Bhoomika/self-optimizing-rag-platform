"""FastAPI dependency providers.

Lightweight, local/in-memory wiring for now. Services are created as
process-wide singletons so retrieved/indexed data persists across requests
within a single process.
"""

from __future__ import annotations

from functools import lru_cache

from api.config.settings import ApplicationSettings, get_default_settings
from api.rag.service import RAGService
from api.retrieval.service import RetrievalService


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    """Return the application settings (cached for the process lifetime)."""
    return get_default_settings()


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    """Return a process-wide in-memory retrieval service."""
    return RetrievalService()


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Return a process-wide RAG service backed by the retrieval service."""
    return RAGService(retrieval_service=get_retrieval_service())
