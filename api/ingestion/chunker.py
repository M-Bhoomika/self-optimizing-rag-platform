"""Simple sliding-window text chunker.

Splits raw document text into overlapping chunks for downstream embedding and
retrieval. Pure, in-memory, and dependency-free.
"""

from __future__ import annotations

from typing import List

from .schemas import DocumentChunk


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
    """Split ``text`` into overlapping chunks using a sliding window.

    Args:
        text: The document body to split.
        chunk_size: Maximum number of characters per chunk. Must be > 0.
        overlap: Number of characters each chunk shares with the previous one.
            Must be >= 0 and < ``chunk_size``.

    Returns:
        An ordered list of :class:`DocumentChunk`. Short documents (shorter than
        ``chunk_size``) yield a single chunk. Empty/whitespace-only text yields
        an empty list.

    Raises:
        ValueError: if ``chunk_size`` <= 0, ``overlap`` < 0, or ``overlap`` >=
            ``chunk_size``.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    if not text or not text.strip():
        return []

    step = chunk_size - overlap
    chunks: List[DocumentChunk] = []
    index = 0
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        piece = text[start:end]
        chunks.append(
            DocumentChunk(
                chunk_index=index,
                chunk_text=piece,
                metadata={"start": start, "end": min(end, text_length)},
            )
        )
        index += 1
        start += step

    return chunks
