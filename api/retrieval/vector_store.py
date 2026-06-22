"""In-memory vector store.

A lightweight, dependency-free :class:`VectorStore` implementation used for
local development and tests. Production backends (FAISS, ChromaDB, hybrid) live
in the same package; see ``faiss_store.py``, ``chroma_store.py``, and
``hybrid_store.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from .interfaces import VectorStore
from .schemas import RetrievalResult


@dataclass
class _StoredVector:
    """Internal record held by the in-memory store."""

    chunk_id: str
    document_id: str
    embedding: List[float]
    chunk_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Return cosine similarity between two equal-length vectors.

    Returns 0.0 when either vector has zero magnitude or lengths differ.
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStore):
    """Stores vectors in a per-tenant in-memory dictionary.

    Not persistent and not thread-safe; intended only as a stand-in until the
    pgvector/Chroma backends land.
    """

    def __init__(self) -> None:
        # tenant_id -> { chunk_id -> _StoredVector }
        self._store: Dict[str, Dict[str, _StoredVector]] = {}

    def upsert(
        self,
        tenant_id: str,
        chunk_id: str,
        document_id: str,
        embedding: Sequence[float],
        chunk_text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Insert or replace a chunk's vector for the given tenant."""
        tenant_bucket = self._store.setdefault(tenant_id, {})
        tenant_bucket[chunk_id] = _StoredVector(
            chunk_id=chunk_id,
            document_id=document_id,
            embedding=list(embedding),
            chunk_text=chunk_text,
            metadata=dict(metadata or {}),
        )

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        """Return the ``top_k`` most similar chunks for ``tenant_id``."""
        if filters:
            raise ValueError("InMemoryVectorStore does not support metadata filters.")
        tenant_bucket = self._store.get(tenant_id, {})
        scored: List[RetrievalResult] = [
            RetrievalResult(
                chunk_id=record.chunk_id,
                document_id=record.document_id,
                score=_cosine_similarity(query_embedding, record.embedding),
                chunk_text=record.chunk_text,
                metadata=record.metadata,
            )
            for record in tenant_bucket.values()
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        if top_k >= 0:
            return scored[:top_k]
        return scored
