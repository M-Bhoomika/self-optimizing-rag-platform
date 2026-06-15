"""Abstract interfaces for the retrieval layer.

Defines the contracts that concrete embedding providers and vector stores must
implement. Implementations (OpenAI, pgvector, Chroma, ...) are added later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

from .schemas import RetrievalResult


class EmbeddingProvider(ABC):
    """Turns text into embedding vectors."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string into a vector."""
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document texts into vectors."""
        raise NotImplementedError


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
    ) -> List[RetrievalResult]:
        """Return the ``top_k`` most similar chunks for ``tenant_id``."""
        raise NotImplementedError
