"""Document ingestion workflow.

Ties together parsing, validation, chunking, embedding, and vector storage into
a single :meth:`IngestionService.ingest_document` call.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from api.embeddings.providers import DummyEmbeddingProvider
from api.retrieval.vector_store import InMemoryVectorStore

from .chunker import chunk_text
from .parser import parse_document_text
from .validators import validate_document_text, validate_document_title


class IngestionService:
    """Coordinates the end-to-end ingestion of a single document."""

    def __init__(
        self,
        chunker: Optional[Callable[..., List[Any]]] = None,
        embedding_provider: Optional[Any] = None,
        vector_store: Optional[Any] = None,
    ) -> None:
        self.chunker = chunker or chunk_text
        self.embedding_provider = embedding_provider or DummyEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()

    def ingest_document(
        self,
        tenant_id: str,
        document_id: str,
        title: str,
        content: str,
        document_type: str,
        source: str,
    ) -> Dict[str, Any]:
        """Ingest one document and index its chunks.

        Returns:
            A summary dict with ``document_id``, ``tenant_id``, ``chunk_count``,
            and ``indexed_count``.
        """
        validate_document_title(title)
        parsed_text = parse_document_text(content, document_type)
        validate_document_text(parsed_text)

        chunks = self.chunker(parsed_text)
        chunk_count = len(chunks)

        texts: List[str] = [chunk.chunk_text for chunk in chunks]
        embeddings = self.embedding_provider.embed_documents(texts) if texts else []

        indexed_count = 0
        chunk_records: List[Dict[str, Any]] = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata: Dict[str, Any] = dict(chunk.metadata or {})
            metadata.update(
                {
                    "tenant_id": tenant_id,
                    "document_id": document_id,
                    "title": title,
                    "source": source,
                    "document_type": document_type,
                    "chunk_index": chunk.chunk_index,
                }
            )

            self.vector_store.upsert(
                tenant_id=tenant_id,
                chunk_id=f"{document_id}:{chunk.chunk_index}",
                document_id=document_id,
                embedding=embedding,
                chunk_text=chunk.chunk_text,
                metadata=metadata,
            )
            indexed_count += 1
            chunk_records.append(
                {
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "embedding": embedding,
                    "chunk_id": f"{document_id}:{chunk.chunk_index}",
                }
            )

        return {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "chunk_count": chunk_count,
            "indexed_count": indexed_count,
            "chunk_records": chunk_records,
            "embedding_model": getattr(self.embedding_provider, "model_name", "unknown"),
        }
