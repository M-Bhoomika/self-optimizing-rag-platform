"""FAISS-backed vector store for fast approximate nearest-neighbor search.

FAISS (Facebook AI Similarity Search) is used here because it provides highly
optimized in-memory ANN indexes. For pure vector similarity without metadata
filters, FAISS delivers low-latency top-k search at scale compared to brute-force
scans. Vectors are L2-normalized and indexed with inner product, which is
equivalent to cosine similarity for unit vectors.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import numpy as np

from .interfaces import VectorStore
from .schemas import RetrievalResult
from .types import VectorStoreItem, normalize_items


def _require_faiss() -> Any:
    try:
        import faiss  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "faiss is required for FAISSVectorStore. Install it with: pip install faiss-cpu"
        ) from exc
    return faiss


class FAISSVectorStore(VectorStore):
    """Per-tenant FAISS index with in-memory metadata aligned to vector IDs."""

    def __init__(self, dimension: int = 1536) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0.")
        self._faiss = _require_faiss()
        self.dimension = dimension
        # tenant_id -> faiss IndexIDMap2
        self._indices: Dict[str, Any] = {}
        # tenant_id -> faiss vector id -> stored record
        self._records: Dict[str, Dict[int, VectorStoreItem]] = {}
        # tenant_id -> chunk_id -> faiss vector id
        self._chunk_ids: Dict[str, Dict[str, int]] = {}
        # tenant_id -> next faiss vector id
        self._next_vector_id: Dict[str, int] = {}

    def _get_index(self, tenant_id: str) -> Any:
        if tenant_id not in self._indices:
            base = self._faiss.IndexFlatIP(self.dimension)
            self._indices[tenant_id] = self._faiss.IndexIDMap2(base)
            self._records[tenant_id] = {}
            self._chunk_ids[tenant_id] = {}
            self._next_vector_id[tenant_id] = 1
        return self._indices[tenant_id]

    def _normalize(self, vector: Sequence[float]) -> np.ndarray:
        arr = np.asarray(vector, dtype=np.float32).reshape(1, -1)
        self._faiss.normalize_L2(arr)
        return arr

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Insert or replace chunk vectors for one or more items."""
        for item in normalize_items(items, **kwargs):
            index = self._get_index(item.tenant_id)
            records = self._records[item.tenant_id]
            chunk_map = self._chunk_ids[item.tenant_id]

            vector = self._normalize(item.embedding)
            if item.chunk_id in chunk_map:
                vector_id = chunk_map[item.chunk_id]
                index.remove_ids(np.array([vector_id], dtype=np.int64))

            vector_id = chunk_map.get(item.chunk_id, self._next_vector_id[item.tenant_id])
            if item.chunk_id not in chunk_map:
                self._next_vector_id[item.tenant_id] += 1
                chunk_map[item.chunk_id] = vector_id

            index.add_with_ids(vector, np.array([vector_id], dtype=np.int64))
            records[vector_id] = item

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        """Return top-k similar chunks for a tenant using FAISS inner-product search."""
        if filters:
            raise ValueError(
                "FAISSVectorStore does not support metadata filters; use ChromaVectorStore "
                "or HybridVectorStore when filters are required."
            )
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        index = self._indices.get(tenant_id)
        if index is None or index.ntotal == 0:
            return []

        query = self._normalize(query_embedding)
        k = min(max(top_k, 0), index.ntotal)
        if k == 0:
            return []

        scores, vector_ids = index.search(query, k)
        records = self._records[tenant_id]
        results: List[RetrievalResult] = []
        for score, vector_id in zip(scores[0], vector_ids[0]):
            if vector_id < 0:
                continue
            record = records.get(int(vector_id))
            if record is None:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    score=float(score),
                    chunk_text=record.chunk_text,
                    metadata=dict(record.metadata),
                )
            )
        return results
