"""HNSW vector store tests."""

from __future__ import annotations

from api.retrieval.hnsw_store import BruteForceHNSWVectorStore


def test_bruteforce_hnsw_tenant_isolation() -> None:
    store = BruteForceHNSWVectorStore(dimension=4)
    store.upsert(
        tenant_id="tenant-a",
        chunk_id="a1",
        document_id="d1",
        embedding=[1.0, 0.0, 0.0, 0.0],
        chunk_text="tenant a chunk",
    )
    store.upsert(
        tenant_id="tenant-b",
        chunk_id="b1",
        document_id="d2",
        embedding=[0.0, 1.0, 0.0, 0.0],
        chunk_text="tenant b chunk",
    )
    results = store.similarity_search("tenant-a", [1.0, 0.0, 0.0, 0.0], top_k=3)
    assert len(results) == 1
    assert results[0].chunk_id == "a1"
