"""Prompt template builders for RAG generation and evaluation.

Centralizes prompt formatting so templates stay consistent, deterministic, and
easy to extend. Future template variants (multi-turn, tool-use, JSON output)
can be added as new builder functions without changing the generation service.
"""

from __future__ import annotations

RAG_SYSTEM_INSTRUCTIONS = (
    "You are a helpful assistant. Answer the user's question using only the "
    "provided context. If the context does not contain enough information, "
    "say you do not know."
)

EVALUATION_SYSTEM_INSTRUCTIONS = (
    "You are an evaluation assistant. Review the answer against the provided "
    "context and question. Assess whether the answer is grounded, relevant, "
    "and complete."
)


def build_rag_prompt(question: str, context: str) -> str:
    """Build a deterministic RAG prompt with dedicated context and question sections."""
    cleaned_question = question.strip()
    cleaned_context = context.strip()

    return (
        "### System\n"
        f"{RAG_SYSTEM_INSTRUCTIONS}\n\n"
        "### Context\n"
        f"{cleaned_context}\n\n"
        "### Question\n"
        f"{cleaned_question}\n\n"
        "### Answer\n"
    )


def build_evaluation_prompt(question: str, answer: str, context: str) -> str:
    """Build a deterministic evaluation prompt for answer review."""
    cleaned_question = question.strip()
    cleaned_answer = answer.strip()
    cleaned_context = context.strip()

    return (
        "### System\n"
        f"{EVALUATION_SYSTEM_INSTRUCTIONS}\n\n"
        "### Context\n"
        f"{cleaned_context}\n\n"
        "### Question\n"
        f"{cleaned_question}\n\n"
        "### Answer\n"
        f"{cleaned_answer}\n\n"
        "### Evaluation\n"
    )
