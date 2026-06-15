"""Lightweight validation helpers for the ingestion pipeline.

Each helper raises ``ValueError`` on invalid input and returns the cleaned
value on success.
"""

from __future__ import annotations

MAX_TITLE_LENGTH = 512


def validate_document_text(text: str) -> str:
    """Validate raw document text.

    Args:
        text: The document body.

    Returns:
        The original text (unchanged) when valid.

    Raises:
        ValueError: if ``text`` is not a string or is empty/whitespace-only.
    """
    if not isinstance(text, str):
        raise ValueError("Document text must be a string.")
    if not text.strip():
        raise ValueError("Document text must not be empty.")
    return text


def validate_document_title(title: str) -> str:
    """Validate a document title.

    Args:
        title: The document title.

    Returns:
        The trimmed title when valid.

    Raises:
        ValueError: if ``title`` is not a string, is empty/whitespace-only, or
            exceeds ``MAX_TITLE_LENGTH`` characters.
    """
    if not isinstance(title, str):
        raise ValueError("Document title must be a string.")
    trimmed = title.strip()
    if not trimmed:
        raise ValueError("Document title must not be empty.")
    if len(trimmed) > MAX_TITLE_LENGTH:
        raise ValueError(
            f"Document title must be at most {MAX_TITLE_LENGTH} characters."
        )
    return trimmed
