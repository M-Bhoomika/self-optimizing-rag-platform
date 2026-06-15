"""Embedding provider implementations.

Currently only contains :class:`DummyEmbeddingProvider`, a deterministic local
placeholder used for development and testing.

TODO: Replace/augment with a real OpenAI embedding provider once that
integration is added. The :class:`EmbeddingProvider` contract should remain
stable so callers are unaffected by the swap.
"""

from __future__ import annotations

import hashlib
from typing import List

from .interfaces import EmbeddingProvider

EMBEDDING_DIMENSION = 1536


class DummyEmbeddingProvider(EmbeddingProvider):
    """Deterministic, offline embedding provider for development/testing.

    Generates fixed-length (``1536``) pseudo-embeddings purely from the input
    text using a hash-based expansion. The same input text always yields the
    same vector, and no network calls or external SDKs are involved.

    This is NOT a semantically meaningful embedding. It exists only so the rest
    of the pipeline can be exercised before the real OpenAI embedding
    integration is wired in.
    """

    def __init__(self, dimension: int = EMBEDDING_DIMENSION) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0.")
        self.dimension = dimension

    def _embed(self, text: str) -> List[float]:
        """Deterministically expand ``text`` into a normalized float vector.

        Uses a counter-mode hash stream (SHA-256 over ``text`` + block index) to
        produce enough bytes, then maps each byte to the range [-1, 1].
        """
        vector: List[float] = []
        block_index = 0
        encoded = text.encode("utf-8")

        while len(vector) < self.dimension:
            digest = hashlib.sha256(encoded + block_index.to_bytes(8, "big")).digest()
            for byte in digest:
                if len(vector) >= self.dimension:
                    break
                # Map byte [0, 255] -> [-1.0, 1.0].
                vector.append((byte / 127.5) - 1.0)
            block_index += 1

        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts deterministically."""
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string deterministically."""
        return self._embed(text)
