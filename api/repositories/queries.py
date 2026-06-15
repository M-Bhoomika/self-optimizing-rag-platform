"""Query-log persistence repository.

There is no ORM model for the ``queries`` table yet, so this repository uses
SQLAlchemy Core ``text()`` statements directly against the schema defined in
``api/db/schema.sql``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

_INSERT_QUERY = text(
    """
    INSERT INTO queries (
        tenant_id, query_text, answer_text, retrieved_chunk_ids,
        latency_ms, model_version, cached
    )
    VALUES (
        :tenant_id, :query_text, :answer_text, CAST(:retrieved_chunk_ids AS JSONB),
        :latency_ms, :model_version, :cached
    )
    RETURNING id, tenant_id, query_text, answer_text, retrieved_chunk_ids,
              faithfulness_score, answer_relevance_score, latency_ms,
              model_version, cached, created_at
    """
)

_LIST_QUERIES = text(
    """
    SELECT id, tenant_id, query_text, answer_text, retrieved_chunk_ids,
           faithfulness_score, answer_relevance_score, latency_ms,
           model_version, cached, created_at
    FROM queries
    WHERE tenant_id = :tenant_id
    ORDER BY created_at DESC
    LIMIT :limit
    """
)


class QueryRepository:
    """Data-access methods for the ``queries`` table."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_query_record(
        self,
        tenant_id: str,
        query_text: str,
        answer_text: str,
        retrieved_chunk_ids: Sequence[str],
        latency_ms: Optional[int] = None,
        model_version: Optional[str] = None,
        cached: bool = False,
    ) -> Dict[str, Any]:
        """Insert a query-log row and return it as a dict.

        Raises:
            ValueError: if ``tenant_id`` or ``query_text`` is empty.
        """
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        if not query_text or not query_text.strip():
            raise ValueError("query_text must not be empty.")

        params = {
            "tenant_id": tenant_id,
            "query_text": query_text,
            "answer_text": answer_text,
            "retrieved_chunk_ids": json.dumps(list(retrieved_chunk_ids or [])),
            "latency_ms": latency_ms,
            "model_version": model_version,
            "cached": cached,
        }
        row = self.session.execute(_INSERT_QUERY, params).mappings().one()
        return dict(row)

    def list_queries_for_tenant(
        self, tenant_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Return recent query-log rows for a tenant, newest first."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        rows = (
            self.session.execute(
                _LIST_QUERIES, {"tenant_id": tenant_id, "limit": limit}
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]
