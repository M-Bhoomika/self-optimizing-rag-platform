"""Embedding-domain contracts and a local placeholder implementation.

Exposes the request/response schemas, the abstract provider interface, and the
deterministic development provider.
"""

from .interfaces import EmbeddingProvider
from .providers import EMBEDDING_DIMENSION, DummyEmbeddingProvider
from .schemas import EmbeddingRequest, EmbeddingResponse

__all__ = [
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingProvider",
    "DummyEmbeddingProvider",
    "EMBEDDING_DIMENSION",
]
