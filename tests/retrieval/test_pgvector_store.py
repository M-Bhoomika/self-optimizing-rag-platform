"""PgVector store tests."""

from __future__ import annotations

from api.retrieval.pgvector_store import PgVectorStore


def test_pgvector_search_returns_empty_when_skip_db() -> None:
    store = PgVectorStore(dimension=1536)
    results = store.similarity_search(
        tenant_id="tenant-1",
        query_embedding=[0.1] * 1536,
        top_k=3,
    )
    assert results == []
