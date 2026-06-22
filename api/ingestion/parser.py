"""Document parsing utilities.

Converts raw document content of supported types into normalized plain text
suitable for chunking.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Set

from .pdf_extractor import extract_pdf_text

TEXT_DOCUMENT_TYPES = {"txt", "markdown", "md", "html"}
CODE_DOCUMENT_TYPES = {
    "py",
    "js",
    "ts",
    "tsx",
    "jsx",
    "java",
    "go",
    "rs",
    "cpp",
    "c",
    "cs",
    "rb",
    "php",
    "sql",
    "yaml",
    "yml",
    "json",
    "code",
}
SUPPORTED_DOCUMENT_TYPES: Set[str] = TEXT_DOCUMENT_TYPES | CODE_DOCUMENT_TYPES | {"pdf"}

_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def detect_document_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in {"md"}:
        return "markdown"
    if suffix in CODE_DOCUMENT_TYPES:
        return suffix if suffix != "md" else "markdown"
    if suffix in {"htm"}:
        return "html"
    if suffix:
        return suffix
    return "txt"


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _strip_html(content: str) -> str:
    try:
        from bs4 import BeautifulSoup  # type: ignore

        return BeautifulSoup(content, "html.parser").get_text(separator=" ")
    except Exception:
        without_blocks = re.sub(
            r"<(script|style)[^>]*>.*?</\1>",
            " ",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return _HTML_TAG_RE.sub(" ", without_blocks)


def parse_document_text(content: str, document_type: str) -> str:
    """Parse and normalize raw document content into plain text."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Document content must be a non-empty string.")

    doc_type = (document_type or "").strip().lower()
    if doc_type == "md":
        doc_type = "markdown"
    if doc_type not in SUPPORTED_DOCUMENT_TYPES:
        raise ValueError(
            f"Unsupported document_type: {document_type!r}. "
            f"Supported types: {sorted(SUPPORTED_DOCUMENT_TYPES)}."
        )

    if doc_type == "html":
        text = _strip_html(content)
    else:
        text = content

    return _normalize_whitespace(text)


def parse_bytes(raw: bytes, document_type: str, filename: str = "") -> str:
    """Parse raw bytes for supported document types including PDF."""
    doc_type = (document_type or detect_document_type(filename)).strip().lower()
    if doc_type == "md":
        doc_type = "markdown"

    if doc_type == "pdf":
        return _normalize_whitespace(extract_pdf_text(raw))

    decoded = raw.decode("utf-8", errors="replace")
    return parse_document_text(decoded, doc_type)
