"""Abstract interface for embedding providers.

Defines the contract that all embedding providers (placeholder, OpenAI, ...)
must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Turns text into embedding vectors."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document texts into vectors."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string into a vector."""
        raise NotImplementedError
