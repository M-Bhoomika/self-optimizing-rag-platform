"""Tests for the generation service, dummy provider, and evaluation scoring."""

from __future__ import annotations

import pytest

from api.generation.providers import DummyLLMProvider
from api.generation.service import GenerationService
from api.generation.schemas import GenerationResponse


def test_dummy_provider_is_deterministic() -> None:
    provider = DummyLLMProvider()
    prompt = "Answer this question using the provided context."

    first = provider.generate(prompt)
    second = provider.generate(prompt)

    assert first == second
    assert "Generated answer based on prompt preview:" in first
    assert prompt[:120] in first


def test_dummy_provider_includes_prompt_preview() -> None:
    provider = DummyLLMProvider(preview_chars=20)
    prompt = "abcdefghijklmnopqrstuvwxyz"
    output = provider.generate(prompt)

    assert "abcdefghijklmnopqrst" in output


def test_generation_service_returns_response() -> None:
    service = GenerationService(llm_provider=DummyLLMProvider())
    response = service.generate_answer(
        question="What is vector search?",
        context="Vector search finds similar embeddings.",
    )

    assert isinstance(response, GenerationResponse)
    assert response.answer
    assert "### Context" in response.prompt
    assert "What is vector search?" in response.prompt


def test_generation_service_rejects_empty_question() -> None:
    service = GenerationService()

    with pytest.raises(ValueError):
        service.generate_answer(question="", context="context")


def test_generation_service_empty_context_returns_low_confidence() -> None:
    service = GenerationService()
    response = service.generate_answer(question="What is RAG?", context="   ")
    assert response.low_confidence is True
    assert "Low-confidence" in response.answer


def test_evaluation_scores_are_bounded() -> None:
    service = GenerationService()
    result = service.evaluate_answer(
        question="What is RAG?",
        answer="RAG combines retrieval and generation for better answers.",
        context="Retrieval augmented generation improves answer quality.",
    )

    assert 0.0 <= result.context_utilization_score <= 1.0
    assert 0.0 <= result.citation_coverage_score <= 1.0
    assert 0.0 <= result.answer_length_score <= 1.0


def test_evaluation_scores_respond_to_content_overlap() -> None:
    service = GenerationService()
    grounded = service.evaluate_answer(
        question="What is pgvector?",
        answer="pgvector enables vector similarity search in PostgreSQL.",
        context="pgvector enables vector similarity search in PostgreSQL.",
    )
    ungrounded = service.evaluate_answer(
        question="What is pgvector?",
        answer="Unrelated content about something else entirely.",
        context="pgvector enables vector similarity search in PostgreSQL.",
    )

    assert grounded.context_utilization_score > ungrounded.context_utilization_score
    assert grounded.citation_coverage_score > ungrounded.citation_coverage_score
