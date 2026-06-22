"""Tests for iterative retrieval pipeline."""

from __future__ import annotations

from api.embeddings.providers import DummyEmbeddingProvider
from api.retrieval.pipeline import IterativeRetrievalPipeline
from api.retrieval.service import RetrievalService
from api.retrieval.vector_store import InMemoryVectorStore


def _index_sample(service: RetrievalService) -> None:
    service.index_chunks(
        [
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "tenant_id": "tenant-1",
                "chunk_text": "Vector search enables fast similarity retrieval.",
                "metadata": {},
            }
        ]
    )


def test_pipeline_returns_answer_and_citations() -> None:
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
    _index_sample(service)
    pipeline = IterativeRetrievalPipeline(
        retrieval_service=service,
        relevance_threshold=0.0,
        max_iterations=2,
    )
    state = pipeline.run(tenant_id="tenant-1", query="vector search", top_k=3)

    assert state["answer"]
    assert isinstance(state["citations"], list)
    assert state["iteration_count"] >= 1


def test_pipeline_rewrites_on_poor_retrieval() -> None:
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
    pipeline = IterativeRetrievalPipeline(
        retrieval_service=service,
        relevance_threshold=0.99,
        max_iterations=2,
    )
    state = pipeline.run(tenant_id="tenant-1", query="missing topic", top_k=3)

    assert len(state.get("rewritten_queries", [])) >= 1


def test_tenant_isolation_in_pipeline() -> None:
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
    _index_sample(service)
    pipeline = IterativeRetrievalPipeline(retrieval_service=service, relevance_threshold=0.0)
    state = pipeline.run(tenant_id="other-tenant", query="vector search", top_k=3)
    assert state.get("retrieved_chunks", []) == []
