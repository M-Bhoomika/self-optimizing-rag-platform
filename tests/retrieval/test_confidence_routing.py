"""Confidence routing tests for iterative pipeline."""

from __future__ import annotations

from api.embeddings.providers import DummyEmbeddingProvider
from api.generation.providers import LocalFallbackProvider
from api.generation.service import GenerationService
from api.retrieval.pipeline import IterativeRetrievalPipeline
from api.retrieval.service import RetrievalService
from api.retrieval.vector_store import InMemoryVectorStore


def _service_with_data() -> RetrievalService:
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
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
    return service


def test_high_relevance_not_low_confidence() -> None:
    pipeline = IterativeRetrievalPipeline(
        retrieval_service=_service_with_data(),
        generation_service=GenerationService(llm_provider=LocalFallbackProvider()),
        relevance_threshold=0.0,
    )
    state = pipeline.run(tenant_id="tenant-1", query="vector search", top_k=3)
    assert state.get("answer")
    assert state.get("confidence_score", 0.0) >= 0.0


def test_low_relevance_marks_low_confidence_after_max_iterations() -> None:
    pipeline = IterativeRetrievalPipeline(
        retrieval_service=RetrievalService(
            embedding_provider=DummyEmbeddingProvider(),
            vector_store=InMemoryVectorStore(),
        ),
        generation_service=GenerationService(llm_provider=LocalFallbackProvider()),
        relevance_threshold=0.99,
        max_iterations=1,
    )
    state = pipeline.run(tenant_id="tenant-1", query="unrelated topic", top_k=3)
    assert state.get("low_confidence") is True
