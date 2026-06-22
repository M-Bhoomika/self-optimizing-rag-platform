"""Tests for generation service structured responses."""

from __future__ import annotations

from api.generation.providers import LocalFallbackProvider
from api.generation.service import GenerationService, compute_confidence_score


def test_generate_answer_returns_citations_and_confidence() -> None:
    service = GenerationService(llm_provider=LocalFallbackProvider())
    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "chunk_text": "Vector search finds similar embeddings.",
            "score": 0.8,
        }
    ]
    response = service.generate_answer(
        question="What is vector search?",
        context="Vector search finds similar embeddings.",
        chunks=chunks,
        retrieval_score=0.8,
    )
    assert response.answer
    assert len(response.citations) == 1
    assert response.confidence_score >= 0.0
    assert response.model == "local-fallback"


def test_low_confidence_when_no_context() -> None:
    service = GenerationService(llm_provider=LocalFallbackProvider())
    response = service.generate_answer(
        question="What is RAG?",
        context="",
        retrieval_score=0.0,
    )
    assert response.low_confidence is True


def test_compute_confidence_score() -> None:
    score = compute_confidence_score(
        answer="vector search embeddings",
        context="vector search finds embeddings",
        retrieval_score=0.9,
    )
    assert 0.0 <= score <= 1.0
