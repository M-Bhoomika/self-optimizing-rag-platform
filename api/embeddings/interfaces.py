"""Abstract interface for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Turns text into embedding vectors."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding vector dimension."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return provider model identifier."""
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError
