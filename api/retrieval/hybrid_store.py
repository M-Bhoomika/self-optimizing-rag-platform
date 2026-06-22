"""Hybrid vector store routing between FAISS and ChromaDB.

Uses FAISS for fast, filter-free ANN search and ChromaDB when metadata filters
are supplied. Both backends receive upserts so they stay in sync.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .interfaces import VectorStore
from .schemas import RetrievalResult
from .types import VectorStoreItem, normalize_items


class HybridVectorStore(VectorStore):
    """Routes similarity search to FAISS or Chroma based on filter presence."""

    def __init__(self, faiss_store: VectorStore, chroma_store: VectorStore) -> None:
        self.faiss_store = faiss_store
        self.chroma_store = chroma_store

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Write vectors to both FAISS and Chroma backends."""
        batch = normalize_items(items, **kwargs)
        if not batch:
            return
        self.faiss_store.upsert(items=batch)
        self.chroma_store.upsert(items=batch)

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        """Search FAISS by default; use Chroma when metadata filters are provided."""
        if filters:
            return self.chroma_store.similarity_search(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
            )
        return self.faiss_store.similarity_search(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )
