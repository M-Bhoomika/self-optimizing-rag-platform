"""Embedding provider factory."""

from __future__ import annotations

import os
from typing import Optional

from .interfaces import EmbeddingProvider
from .providers import DummyEmbeddingProvider, SentenceTransformersProvider


def get_embedding_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    expected_dimension: Optional[int] = None,
) -> EmbeddingProvider:
    """Select embedding provider from environment or explicit arguments.

    ``EMBEDDING_PROVIDER``:
    - ``sentence-transformers`` — local SentenceTransformer model
    - ``dummy`` or unset — deterministic offline embeddings
    """
    selected = (provider_name or os.getenv("EMBEDDING_PROVIDER", "dummy")).strip().lower()
    model = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    dimension_env = os.getenv("EMBEDDING_DIMENSION")
    expected = int(dimension_env) if dimension_env else None

    if selected in {"sentence-transformers", "sentence_transformers", "st"}:
        return SentenceTransformersProvider(model_name=model, expected_dimension=expected)

    return DummyEmbeddingProvider(dimension=expected or 1536)
