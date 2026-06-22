"""Tests for prompt template builders."""

from __future__ import annotations

from api.generation.prompts import build_evaluation_prompt, build_rag_prompt


def test_build_rag_prompt_includes_system_context_and_question() -> None:
    prompt = build_rag_prompt(
        question="What is pgvector?",
        context="pgvector adds vector similarity search to PostgreSQL.",
    )

    assert "### System" in prompt
    assert "### Context" in prompt
    assert "### Question" in prompt
    assert "### Answer" in prompt
    assert "pgvector adds vector similarity search to PostgreSQL." in prompt
    assert "What is pgvector?" in prompt


def test_build_rag_prompt_is_deterministic() -> None:
    first = build_rag_prompt("same question", "same context")
    second = build_rag_prompt("same question", "same context")
    assert first == second


def test_build_rag_prompt_strips_whitespace() -> None:
    prompt = build_rag_prompt("  question  ", "  context  ")
    assert "\n  question  \n" not in prompt
    assert "question" in prompt
    assert "context" in prompt


def test_build_evaluation_prompt_includes_answer_section() -> None:
    prompt = build_evaluation_prompt(
        question="What is RAG?",
        answer="RAG combines retrieval and generation.",
        context="Retrieval augmented generation improves answer quality.",
    )

    assert "### System" in prompt
    assert "### Context" in prompt
    assert "### Question" in prompt
    assert "### Answer" in prompt
    assert "### Evaluation" in prompt
    assert "RAG combines retrieval and generation." in prompt


def test_build_evaluation_prompt_is_deterministic() -> None:
    first = build_evaluation_prompt("q", "a", "c")
    second = build_evaluation_prompt("q", "a", "c")
    assert first == second
