"""Chunking unit tests."""

from __future__ import annotations

import pytest

from api.ingestion.chunker import chunk_text


def test_chunk_text_preserves_order() -> None:
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_short_document_single_chunk() -> None:
    chunks = chunk_text("short document", chunk_size=1000, overlap=200)
    assert len(chunks) == 1


def test_empty_text_returns_empty_list() -> None:
    assert chunk_text("   ") == []


def test_invalid_overlap_raises() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=100, overlap=100)
