"""Retrieval-domain contracts and abstractions for the RAG platform.

Exposes the request/response schemas, the abstract provider/store interfaces,
and the in-memory vector store used during early development.
"""

from .interfaces import EmbeddingProvider, VectorStore
from .schemas import RetrievalRequest, RetrievalResponse, RetrievalResult
from .vector_store import InMemoryVectorStore

__all__ = [
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalResponse",
    "EmbeddingProvider",
    "VectorStore",
    "InMemoryVectorStore",
]
