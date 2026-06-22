"""Embedding provider implementations and dimension validation."""

from __future__ import annotations

import hashlib
from typing import List, Optional

from .interfaces import EmbeddingProvider

EMBEDDING_DIMENSION = 1536


def validate_embedding_dimension(vector: List[float], expected: int) -> None:
    if len(vector) != expected:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected}, got {len(vector)}"
        )


class DummyEmbeddingProvider(EmbeddingProvider):
    """Deterministic offline embedding provider."""

    def __init__(self, dimension: int = EMBEDDING_DIMENSION) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0.")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return "dummy"

    def _embed(self, text: str) -> List[float]:
        vector: List[float] = []
        block_index = 0
        encoded = text.encode("utf-8")
        while len(vector) < self._dimension:
            digest = hashlib.sha256(encoded + block_index.to_bytes(8, "big")).digest()
            for byte in digest:
                if len(vector) >= self._dimension:
                    break
                vector.append((byte / 127.5) - 1.0)
            block_index += 1
        validate_embedding_dimension(vector, self._dimension)
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class SentenceTransformersProvider(EmbeddingProvider):
    """Embedding provider backed by sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", expected_dimension: Optional[int] = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            ) from exc

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dimension = int(self._model.get_sentence_embedding_dimension())
        if expected_dimension is not None and expected_dimension != self._dimension:
            raise ValueError(
                f"Model dimension {self._dimension} does not match expected {expected_dimension}"
            )

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        output = [vec.tolist() for vec in vectors]
        for vector in output:
            validate_embedding_dimension(vector, self._dimension)
        return output

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0].tolist()
        validate_embedding_dimension(vector, self._dimension)
        return vector
