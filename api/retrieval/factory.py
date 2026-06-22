"""Vector store factory."""

from __future__ import annotations

import os
from typing import Optional

from api.config.settings import get_settings
from api.embeddings.factory import get_embedding_provider

from .chroma_store import ChromaVectorStore
from .faiss_store import FAISSVectorStore
from .hnsw_store import BruteForceHNSWVectorStore, HNSWVectorStore
from .hybrid_store import HybridVectorStore
from .interfaces import VectorStore
from .pgvector_store import PgVectorStore
from .vector_store import InMemoryVectorStore


def get_vector_store(backend: Optional[str] = None) -> VectorStore:
    selected = (backend or os.getenv("RETRIEVAL_BACKEND") or get_settings().retrieval.backend).lower()
    dimension = get_embedding_provider().dimension

    if selected in {"memory", "in-memory", "inmemory"}:
        return InMemoryVectorStore()
    if selected == "faiss":
        return FAISSVectorStore(dimension=dimension)
    if selected == "chroma":
        return ChromaVectorStore()
    if selected == "hybrid":
        return HybridVectorStore(dimension=dimension)
    if selected == "pgvector":
        return PgVectorStore(dimension=dimension)
    if selected == "hnsw":
        try:
            return HNSWVectorStore(dimension=dimension)
        except ImportError:
            return BruteForceHNSWVectorStore(dimension=dimension)
    raise ValueError(f"Unknown retrieval backend: {selected}")
