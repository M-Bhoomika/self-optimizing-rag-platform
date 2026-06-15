"""Document parsing utilities.

Converts raw document content of a few supported types into normalized plain
text suitable for chunking.
"""

from __future__ import annotations

import re

SUPPORTED_DOCUMENT_TYPES = {"txt", "markdown", "html"}

_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and trim."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def _strip_html(content: str) -> str:
    """Remove HTML tags, preferring BeautifulSoup when available."""
    try:
        from bs4 import BeautifulSoup  # type: ignore

        return BeautifulSoup(content, "html.parser").get_text(separator=" ")
    except Exception:
        # Fallback: drop script/style blocks, then strip remaining tags.
        without_blocks = re.sub(
            r"<(script|style)[^>]*>.*?</\1>",
            " ",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return _HTML_TAG_RE.sub(" ", without_blocks)


def parse_document_text(content: str, document_type: str) -> str:
    """Parse and normalize raw document content into plain text.

    Args:
        content: The raw document body.
        document_type: One of ``txt``, ``markdown``, or ``html``.

    Returns:
        Normalized plain text.

    Raises:
        ValueError: if ``content`` is empty/whitespace-only or
            ``document_type`` is unsupported.
    """
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Document content must be a non-empty string.")

    doc_type = (document_type or "").strip().lower()
    if doc_type not in SUPPORTED_DOCUMENT_TYPES:
        raise ValueError(
            f"Unsupported document_type: {document_type!r}. "
            f"Supported types: {sorted(SUPPORTED_DOCUMENT_TYPES)}."
        )

    if doc_type == "html":
        text = _strip_html(content)
    else:
        # txt and markdown are treated as plain text for now.
        text = content

    return _normalize_whitespace(text)
