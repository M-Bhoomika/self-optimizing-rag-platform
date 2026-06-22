"""PostgreSQL pgvector-backed vector store."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Sequence

from sqlalchemy import text

from .interfaces import VectorStore
from .schemas import RetrievalResult
from .types import VectorStoreItem, normalize_items

logger = logging.getLogger(__name__)


def _format_vector(values: Sequence[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in values) + "]"


class PgVectorStore(VectorStore):
    """Retrieves chunk embeddings from PostgreSQL using pgvector cosine distance."""

    def __init__(self, dimension: int = 1536) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0.")
        self.dimension = dimension

    def _session(self):
        from api.db.session import get_db_session

        return get_db_session()

    def upsert(
        self,
        items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return
        for item in normalize_items(items, **kwargs):
            if len(item.embedding) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(item.embedding)}"
                )
            try:
                with self._session() as session:
                    session.execute(
                        text(
                            """
                            INSERT INTO chunks (
                                tenant_id, document_id, chunk_text, chunk_index, embedding_vector
                            )
                            VALUES (
                                :tenant_id, :document_id, :chunk_text, :chunk_index,
                                CAST(:embedding AS vector)
                            )
                            ON CONFLICT DO NOTHING
                            """
                        ),
                        {
                            "tenant_id": item.tenant_id,
                            "document_id": item.document_id,
                            "chunk_text": item.chunk_text,
                            "chunk_index": int(item.metadata.get("chunk_index", 0)),
                            "embedding": _format_vector(item.embedding),
                        },
                    )
            except Exception as exc:
                logger.warning("PgVectorStore upsert skipped: %s", exc)

    def similarity_search(
        self,
        tenant_id: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
        filters: Dict[str, Any] | None = None,
    ) -> List[RetrievalResult]:
        if not tenant_id:
            raise ValueError("tenant_id is required.")
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return []
        if filters:
            raise ValueError("PgVectorStore does not support metadata filters.")

        query_vector = _format_vector(query_embedding)
        try:
            with self._session() as session:
                rows = session.execute(
                    text(
                        """
                        SELECT
                            id::text AS chunk_id,
                            document_id::text AS document_id,
                            chunk_text,
                            1 - (embedding_vector <=> CAST(:query_embedding AS vector)) AS score
                        FROM chunks
                        WHERE tenant_id = :tenant_id
                          AND embedding_vector IS NOT NULL
                        ORDER BY embedding_vector <=> CAST(:query_embedding AS vector)
                        LIMIT :top_k
                        """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "query_embedding": query_vector,
                        "top_k": top_k,
                    },
                ).mappings().all()
        except Exception as exc:
            logger.warning("PgVectorStore search failed: %s", exc)
            return []

        return [
            RetrievalResult(
                chunk_id=str(row["chunk_id"]),
                document_id=str(row["document_id"]),
                score=float(row["score"]),
                chunk_text=str(row["chunk_text"]),
                metadata={},
            )
            for row in rows
        ]
