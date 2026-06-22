"""Abstract interfaces for the retrieval layer.

Defines the vector store contract. Embedding providers live in
``api.embeddings.interfaces`` — import :class:`EmbeddingProvider` from there
or from ``api.embeddings``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

from .schemas import RetrievalResult


class VectorStore(ABC):
    """Stores chunk embeddings and supports similarity search."""

    @abstractmethod
    def upsert(
        self,
        tenant_id: str,
        chunk_id: str,
        document_id: str,
        embedding: Sequence[float],
        chunk_text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Insert or update a single chunk's embedding and payload."""
        raise NotImplementedError

    @abstractmethod
    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        """Return the ``top_k`` most similar chunks for ``tenant_id``."""
        raise NotImplementedError
