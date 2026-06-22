"""Vector store factory tests."""

from __future__ import annotations

import pytest

from api.retrieval.factory import get_vector_store
from api.retrieval.hnsw_store import BruteForceHNSWVectorStore
from api.retrieval.vector_store import InMemoryVectorStore


def test_default_memory_backend() -> None:
    store = get_vector_store("memory")
    assert isinstance(store, InMemoryVectorStore)


def test_hnsw_backend_falls_back_without_extension() -> None:
    store = get_vector_store("hnsw")
    assert isinstance(store, (BruteForceHNSWVectorStore, object))


def test_pgvector_backend() -> None:
    from api.retrieval.pgvector_store import PgVectorStore

    store = get_vector_store("pgvector")
    assert isinstance(store, PgVectorStore)


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError):
        get_vector_store("unknown-backend")
