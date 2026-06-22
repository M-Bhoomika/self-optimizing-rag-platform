"""Tests for LLM providers."""

from __future__ import annotations

from api.generation.providers import DummyLLMProvider, LocalFallbackProvider


def test_local_fallback_grounded_answer() -> None:
    provider = LocalFallbackProvider()
    prompt = (
        "### Context\n"
        "Vector search finds similar embeddings in a database.\n\n"
        "### Question\n"
        "What is vector search?\n\n"
        "### Answer\n"
    )
    answer = provider.generate(prompt)
    assert "vector search" in answer.lower() or "embeddings" in answer.lower()


def test_dummy_provider_deterministic() -> None:
    provider = DummyLLMProvider()
    first = provider.generate("same prompt")
    second = provider.generate("same prompt")
    assert first == second


def test_stream_generate_yields_tokens() -> None:
    provider = LocalFallbackProvider()
    prompt = "### Context\nRAG combines retrieval and generation.\n\n### Question\nWhat is RAG?\n\n### Answer\n"
    tokens = list(provider.stream_generate(prompt))
    assert len(tokens) >= 1
