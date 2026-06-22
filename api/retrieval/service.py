"""Retrieval service layer.

Wires an embedding provider (``api.embeddings``) to a :class:`VectorStore` to
provide two high-level operations: indexing chunks and retrieving relevant
chunks for a query. Supports optional cross-encoder reranking after vector
search.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from api.embeddings.providers import DummyEmbeddingProvider
from api.retrieval.schemas import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
)
from api.retrieval.vector_store import InMemoryVectorStore


def _get_field(chunk: Any, name: str, default: Any = None) -> Any:
    """Read ``name`` from a chunk that may be a dict or an object."""
    if isinstance(chunk, dict):
        return chunk.get(name, default)
    return getattr(chunk, name, default)


class RetrievalService:
    """Coordinates embedding and vector storage for indexing and retrieval."""

    def __init__(
        self,
        embedding_provider: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        reranker: Optional[Any] = None,
    ) -> None:
        self.embedding_provider = embedding_provider or DummyEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.reranker = reranker
        from api.retrieval.langchain_retrievers import LangChainRetrievalOrchestrator

        self.langchain_orchestrator = LangChainRetrievalOrchestrator(use_langchain=False)

    def index_chunks(self, chunks: Iterable[Any]) -> int:
        """Embed and upsert a batch of chunks into the vector store.

        Each chunk may be a dict or an object exposing ``chunk_id``,
        ``document_id``, ``chunk_text``, and ``metadata``. The ``tenant_id`` is
        resolved from the chunk directly or from its ``metadata``.

        Returns:
            The number of chunks indexed.
        """
        chunk_list = list(chunks)
        if not chunk_list:
            return 0

        texts: List[str] = [_get_field(c, "chunk_text", "") or "" for c in chunk_list]
        embeddings = self.embedding_provider.embed_documents(texts)

        count = 0
        for chunk, embedding in zip(chunk_list, embeddings):
            metadata: Dict[str, Any] = _get_field(chunk, "metadata", {}) or {}
            tenant_id = _get_field(chunk, "tenant_id")
            if tenant_id is None:
                tenant_id = metadata.get("tenant_id")
            if tenant_id is None:
                raise ValueError(
                    "Each chunk must provide a tenant_id (on the chunk or in metadata)."
                )

            self.vector_store.upsert(
                tenant_id=str(tenant_id),
                chunk_id=str(_get_field(chunk, "chunk_id")),
                document_id=str(_get_field(chunk, "document_id")),
                embedding=embedding,
                chunk_text=_get_field(chunk, "chunk_text", "") or "",
                metadata=metadata,
            )
            count += 1

        return count

    def retrieve(
        self,
        request: RetrievalRequest,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResponse:
        """Embed the query, search the vector store, and optionally rerank."""

        def _search(query_text: str, top_k: int) -> List[RetrievalResult]:
            search_kwargs: Dict[str, Any] = {
                "tenant_id": request.tenant_id,
                "query_embedding": self.embedding_provider.embed_query(query_text),
                "top_k": top_k,
            }
            if filters is not None:
                search_kwargs["filters"] = filters
            return self.vector_store.similarity_search(**search_kwargs)

        if self.langchain_orchestrator is not None:
            results = self.langchain_orchestrator.retrieve(
                request.query,
                retrieve_fn=_search,
                top_k=request.top_k,
            )
        else:
            results = _search(request.query, request.top_k)

        if self.reranker is not None:
            results = self.reranker.rerank(
                query=request.query,
                results=results,
                top_k=request.top_k,
            )

        results = sorted(results, key=lambda item: item.score, reverse=True)
        return RetrievalResponse(results=results)
