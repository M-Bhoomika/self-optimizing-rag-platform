"""ChromaDB-backed vector store for metadata-filtered retrieval.

ChromaDB is used here because it combines vector similarity search with rich
metadata filtering in a single query. That makes it well suited for tenant-scoped
retrieval with additional predicates (document type, source, tags, etc.) that
pure ANN indexes like FAISS handle less conveniently.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .interfaces import VectorStore
from .schemas import RetrievalResult
from .types import VectorStoreItem, normalize_items


def _require_chromadb() -> Any:
    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "chromadb is required for ChromaVectorStore. Install it with: pip install chromadb"
        ) from exc
    return chromadb


class ChromaVectorStore(VectorStore):
    """Chroma collection-backed store with tenant isolation via metadata filters."""

    def __init__(self, collection_name: str = "rag_chunks") -> None:
        chromadb = _require_chromadb()
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(name=collection_name)

    @staticmethod
    def _build_metadata(item: VectorStoreItem) -> Dict[str, Any]:
        metadata = dict(item.metadata)
        metadata.update(
            {
                "tenant_id": item.tenant_id,
                "document_id": item.document_id,
                "chunk_text": item.chunk_text,
            }
        )
        return metadata

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Insert or replace chunk vectors in the Chroma collection."""
        batch = normalize_items(items, **kwargs)
        if not batch:
            return

        self._collection.upsert(
            ids=[item.chunk_id for item in batch],
            embeddings=[list(item.embedding) for item in batch],
            metadatas=[self._build_metadata(item) for item in batch],
            documents=[item.chunk_text for item in batch],
        )

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        """Return top-k similar chunks, scoped to a tenant and optional filters."""
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        where: Dict[str, Any] = {"tenant_id": tenant_id}
        if filters:
            where = {"$and": [{"tenant_id": tenant_id}, filters]}

        response = self._collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=max(top_k, 0),
            where=where,
            include=["metadatas", "documents", "distances"],
        )

        ids = (response.get("ids") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        documents = (response.get("documents") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]

        results: List[RetrievalResult] = []
        for chunk_id, metadata, document, distance in zip(ids, metadatas, documents, distances):
            metadata = metadata or {}
            score = 1.0 / (1.0 + float(distance)) if distance is not None else 0.0
            extra = {
                key: value
                for key, value in metadata.items()
                if key not in {"tenant_id", "document_id", "chunk_text"}
            }
            results.append(
                RetrievalResult(
                    chunk_id=str(chunk_id),
                    document_id=str(metadata.get("document_id", "")),
                    score=score,
                    chunk_text=str(document or metadata.get("chunk_text", "")),
                    metadata=extra,
                )
            )
        return results
