"""Tests for production vector store routing and tenant isolation."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import pytest

from api.retrieval.hybrid_store import HybridVectorStore
from api.retrieval.schemas import RetrievalResult
from api.retrieval.types import VectorStoreItem
from api.retrieval.vector_store import InMemoryVectorStore


class _RecordingStore:
    """Minimal store that records which search path was used."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name
        self.upsert_calls = 0
        self.search_calls = 0
        self.last_filters: Dict[str, Any] | None = None

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        self.upsert_calls += 1

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        self.search_calls += 1
        self.last_filters = filters
        return [
            RetrievalResult(
                chunk_id=f"{self.name}-chunk",
                document_id="doc-1",
                score=0.9,
                chunk_text=f"result from {self.name}",
                metadata={"backend": self.name},
            )
        ]


def test_in_memory_tenant_isolation() -> None:
    store = InMemoryVectorStore()
    vector = [1.0, 0.0, 0.0]

    store.upsert(
        tenant_id="tenant-a",
        chunk_id="a1",
        document_id="doc-a",
        embedding=vector,
        chunk_text="tenant a chunk",
    )
    store.upsert(
        tenant_id="tenant-b",
        chunk_id="b1",
        document_id="doc-b",
        embedding=vector,
        chunk_text="tenant b chunk",
    )

    tenant_a_results = store.similarity_search(
        tenant_id="tenant-a",
        query_embedding=vector,
        top_k=5,
    )
    tenant_b_results = store.similarity_search(
        tenant_id="tenant-b",
        query_embedding=vector,
        top_k=5,
    )

    assert len(tenant_a_results) == 1
    assert tenant_a_results[0].chunk_id == "a1"
    assert len(tenant_b_results) == 1
    assert tenant_b_results[0].chunk_id == "b1"


def test_hybrid_store_upserts_to_both_backends() -> None:
    faiss_store = _RecordingStore("faiss")
    chroma_store = _RecordingStore("chroma")
    hybrid = HybridVectorStore(faiss_store=faiss_store, chroma_store=chroma_store)

    hybrid.upsert(
        items=[
            VectorStoreItem(
                tenant_id="tenant-1",
                chunk_id="c1",
                document_id="d1",
                embedding=[0.1, 0.2, 0.3],
                chunk_text="hello",
            )
        ]
    )

    assert faiss_store.upsert_calls == 1
    assert chroma_store.upsert_calls == 1


def test_hybrid_store_uses_faiss_without_filters() -> None:
    faiss_store = _RecordingStore("faiss")
    chroma_store = _RecordingStore("chroma")
    hybrid = HybridVectorStore(faiss_store=faiss_store, chroma_store=chroma_store)

    results = hybrid.similarity_search(
        tenant_id="tenant-1",
        query_embedding=[0.1, 0.2, 0.3],
        top_k=3,
    )

    assert faiss_store.search_calls == 1
    assert chroma_store.search_calls == 0
    assert results[0].metadata["backend"] == "faiss"


def test_hybrid_store_uses_chroma_with_filters() -> None:
    faiss_store = _RecordingStore("faiss")
    chroma_store = _RecordingStore("chroma")
    hybrid = HybridVectorStore(faiss_store=faiss_store, chroma_store=chroma_store)
    filters = {"document_type": "pdf"}

    results = hybrid.similarity_search(
        tenant_id="tenant-1",
        query_embedding=[0.1, 0.2, 0.3],
        top_k=3,
        filters=filters,
    )

    assert faiss_store.search_calls == 0
    assert chroma_store.search_calls == 1
    assert chroma_store.last_filters == filters
    assert results[0].metadata["backend"] == "chroma"


def test_faiss_store_import_error_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    import api.retrieval.faiss_store as faiss_module

    def _raise_import_error() -> None:
        raise ImportError(
            "faiss is required for FAISSVectorStore. Install it with: pip install faiss-cpu"
        )

    monkeypatch.setattr(faiss_module, "_require_faiss", _raise_import_error)

    with pytest.raises(ImportError, match="faiss-cpu"):
        faiss_module.FAISSVectorStore()


def test_chroma_store_import_error_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    import api.retrieval.chroma_store as chroma_module

    def _raise_import_error() -> None:
        raise ImportError(
            "chromadb is required for ChromaVectorStore. Install it with: pip install chromadb"
        )

    monkeypatch.setattr(chroma_module, "_require_chromadb", _raise_import_error)

    with pytest.raises(ImportError, match="chromadb"):
        chroma_module.ChromaVectorStore()
