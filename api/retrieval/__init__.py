"""Retrieval-domain contracts and abstractions for the RAG platform.

Exposes request/response schemas, the vector store interface, in-memory and
production store implementations, and reranking utilities.

Embedding providers are defined in ``api.embeddings``; :class:`EmbeddingProvider`
is re-exported here for convenience.
"""

from api.embeddings.interfaces import EmbeddingProvider

from .chroma_store import ChromaVectorStore
from .faiss_store import FAISSVectorStore
from .hybrid_store import HybridVectorStore
from .interfaces import VectorStore
from .pipeline import IterativeRetrievalPipeline
from .reranker import CrossEncoderReranker, DEFAULT_RERANKER_MODEL
from .schemas import RetrievalRequest, RetrievalResponse, RetrievalResult
from .types import VectorStoreItem
from .vector_store import InMemoryVectorStore

__all__ = [
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalResponse",
    "EmbeddingProvider",
    "VectorStore",
    "VectorStoreItem",
    "InMemoryVectorStore",
    "FAISSVectorStore",
    "ChromaVectorStore",
    "HybridVectorStore",
    "IterativeRetrievalPipeline",
    "CrossEncoderReranker",
    "DEFAULT_RERANKER_MODEL",
]
