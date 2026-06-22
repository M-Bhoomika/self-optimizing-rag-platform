"""HNSW-backed vector store using the optional hnsw_cpp extension."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence

import numpy as np

from .interfaces import VectorStore
from .schemas import RetrievalResult
from .types import VectorStoreItem, normalize_items


def _require_hnsw() -> Any:
    try:
        import hnsw_cpp  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "hnsw_cpp is required for HNSWVectorStore. Build and install from hnsw-cpp/."
        ) from exc
    return hnsw_cpp


def _l2_normalize(vector: Sequence[float]) -> np.ndarray:
    arr = np.asarray(vector, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0.0:
        return arr
    return arr / norm


def _distance_to_score(distance: float) -> float:
    return 1.0 / (1.0 + max(float(distance), 0.0))


class HNSWVectorStore(VectorStore):
    """Per-tenant HNSW index with metadata sidecar."""

    def __init__(self, dimension: int = 1536, max_elements: int = 100_000) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0.")
        self._hnsw = _require_hnsw()
        self.dimension = dimension
        self.max_elements = max_elements
        self._indices: Dict[str, Any] = {}
        self._records: Dict[str, Dict[int, VectorStoreItem]] = {}
        self._chunk_ids: Dict[str, Dict[str, int]] = {}
        self._next_vector_id: Dict[str, int] = {}

    def _get_index(self, tenant_id: str) -> Any:
        if tenant_id not in self._indices:
            self._indices[tenant_id] = self._hnsw.HNSWIndex(
                self.dimension,
                self.max_elements,
            )
            self._records[tenant_id] = {}
            self._chunk_ids[tenant_id] = {}
            self._next_vector_id[tenant_id] = 1
        return self._indices[tenant_id]

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        for item in normalize_items(items, **kwargs):
            index = self._get_index(item.tenant_id)
            records = self._records[item.tenant_id]
            chunk_map = self._chunk_ids[item.tenant_id]

            vector = _l2_normalize(item.embedding)
            vector_id = chunk_map.get(item.chunk_id, self._next_vector_id[item.tenant_id])
            if item.chunk_id not in chunk_map:
                self._next_vector_id[item.tenant_id] += 1
                chunk_map[item.chunk_id] = vector_id

            index.add_items(
                np.asarray([vector], dtype=np.float32),
                [int(vector_id)],
            )
            records[vector_id] = item

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        if filters:
            raise ValueError("HNSWVectorStore does not support metadata filters.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        index = self._indices.get(tenant_id)
        records = self._records.get(tenant_id, {})
        if index is None or not records:
            return []

        query = _l2_normalize(query_embedding)
        raw_results = index.search(np.asarray(query, dtype=np.float32), k=top_k, ef=50)
        results: List[RetrievalResult] = []
        for vector_id, distance in raw_results:
            record = records.get(int(vector_id))
            if record is None:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    score=_distance_to_score(distance),
                    chunk_text=record.chunk_text,
                    metadata=dict(record.metadata),
                )
            )
        return results


class BruteForceHNSWVectorStore(VectorStore):
    """Pure-Python fallback when hnsw_cpp is unavailable (tests/local dev)."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension
        self._records: Dict[str, Dict[str, VectorStoreItem]] = {}

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        for item in normalize_items(items, **kwargs):
            tenant_records = self._records.setdefault(item.tenant_id, {})
            tenant_records[item.chunk_id] = item

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        if filters:
            raise ValueError("BruteForceHNSWVectorStore does not support metadata filters.")
        tenant_records = self._records.get(tenant_id, {})
        if not tenant_records:
            return []
        query = _l2_normalize(query_embedding)
        scored: List[tuple[float, VectorStoreItem]] = []
        for record in tenant_records.values():
            vector = _l2_normalize(record.embedding)
            distance = float(np.linalg.norm(query - vector))
            scored.append((_distance_to_score(distance), record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievalResult(
                chunk_id=record.chunk_id,
                document_id=record.document_id,
                score=score,
                chunk_text=record.chunk_text,
                metadata=dict(record.metadata),
            )
            for score, record in scored[:top_k]
        ]
