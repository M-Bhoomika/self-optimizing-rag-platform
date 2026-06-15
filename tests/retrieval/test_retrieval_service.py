"""Tests for the in-memory RetrievalService."""

from __future__ import annotations

import pytest

from api.embeddings.providers import DummyEmbeddingProvider
from api.retrieval.schemas import RetrievalRequest
from api.retrieval.service import RetrievalService
from api.retrieval.vector_store import InMemoryVectorStore

TENANT_ID = "tenant-1"


def _make_chunks():
    return [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "chunk_text": "The quick brown fox jumps over the lazy dog.",
            "tenant_id": TENANT_ID,
            "metadata": {"position": 0},
        },
        {
            "chunk_id": "c2",
            "document_id": "d1",
            "chunk_text": "Retrieval augmented generation improves answer quality.",
            "tenant_id": TENANT_ID,
            "metadata": {"position": 1},
        },
        {
            "chunk_id": "c3",
            "document_id": "d2",
            "chunk_text": "Vector databases enable fast similarity search.",
            "tenant_id": TENANT_ID,
            "metadata": {"position": 2},
        },
    ]


@pytest.fixture
def service() -> RetrievalService:
    return RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )


def test_index_chunks_returns_count(service: RetrievalService) -> None:
    indexed = service.index_chunks(_make_chunks())
    assert indexed == 3


def test_retrieve_returns_results(service: RetrievalService) -> None:
    service.index_chunks(_make_chunks())
    request = RetrievalRequest(tenant_id=TENANT_ID, query="similarity search", top_k=5)
    response = service.retrieve(request)

    assert len(response.results) == 3
    for result in response.results:
        assert result.chunk_id
        assert result.document_id
        assert isinstance(result.score, float)


def test_top_k_limits_results(service: RetrievalService) -> None:
    service.index_chunks(_make_chunks())
    request = RetrievalRequest(tenant_id=TENANT_ID, query="anything", top_k=2)
    response = service.retrieve(request)

    assert len(response.results) == 2


def test_results_sorted_by_score_descending(service: RetrievalService) -> None:
    service.index_chunks(_make_chunks())
    request = RetrievalRequest(tenant_id=TENANT_ID, query="vector search", top_k=3)
    response = service.retrieve(request)

    scores = [r.score for r in response.results]
    assert scores == sorted(scores, reverse=True)


def test_identical_query_is_deterministic(service: RetrievalService) -> None:
    service.index_chunks(_make_chunks())
    request = RetrievalRequest(tenant_id=TENANT_ID, query="deterministic check", top_k=3)

    first = service.retrieve(request)
    second = service.retrieve(request)

    first_ids = [(r.chunk_id, r.score) for r in first.results]
    second_ids = [(r.chunk_id, r.score) for r in second.results]
    assert first_ids == second_ids


def test_tenant_isolation(service: RetrievalService) -> None:
    service.index_chunks(_make_chunks())
    request = RetrievalRequest(tenant_id="other-tenant", query="anything", top_k=5)
    response = service.retrieve(request)

    assert response.results == []
