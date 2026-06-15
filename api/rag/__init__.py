"""RAG orchestration layer for the platform.

Exposes the orchestration schemas and the service that ties retrieval to the
(future) generation step.
"""

from .schemas import RAGContext, RAGRequest, RAGResponse
from .service import RAGService

__all__ = [
    "RAGRequest",
    "RAGContext",
    "RAGResponse",
    "RAGService",
]
