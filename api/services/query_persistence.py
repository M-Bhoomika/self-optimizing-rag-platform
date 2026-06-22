"""Query-log persistence and evaluation score updates."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Sequence

from api.config.settings import get_settings
from api.evaluation.metrics import compute_answer_relevance, compute_faithfulness
from api.evaluation.schemas import EvaluationSample
from api.repositories.queries import QueryRepository

logger = logging.getLogger(__name__)


class QueryPersistenceService:
    """Persist query history and optional evaluation scores to PostgreSQL."""

    def persist_query(
        self,
        tenant_id: str,
        query_text: str,
        answer_text: str,
        retrieved_chunk_ids: Sequence[str],
        latency_ms: Optional[int] = None,
        model_version: Optional[str] = None,
        cached: bool = False,
        expected_answer: Optional[str] = None,
        context_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return None
        settings = get_settings()
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                repo = QueryRepository(session)
                record = repo.create_query_record(
                    tenant_id=tenant_id,
                    query_text=query_text,
                    answer_text=answer_text,
                    retrieved_chunk_ids=list(retrieved_chunk_ids),
                    latency_ms=latency_ms,
                    model_version=model_version,
                    cached=cached,
                )
                if settings.evaluation.enable_evaluation:
                    reference = expected_answer or context_text or ""
                    sample = EvaluationSample(
                        question=query_text,
                        expected_answer=reference or answer_text,
                        generated_answer=answer_text,
                        retrieved_chunk_ids=list(retrieved_chunk_ids),
                    )
                    faithfulness = (
                        compute_faithfulness(sample)
                        if reference
                        else compute_answer_relevance(sample)
                    )
                    repo.update_evaluation_scores(
                        query_id=str(record["id"]),
                        faithfulness_score=faithfulness,
                        answer_relevance_score=compute_answer_relevance(sample),
                    )
                return record
        except Exception as exc:
            logger.warning(
                "Query persistence skipped",
                extra={"tenant_id": tenant_id, "error": str(exc)},
            )
            return None

    def list_history(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return []
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                return QueryRepository(session).list_queries_for_tenant(tenant_id, limit=limit)
        except Exception as exc:
            logger.warning("Query history unavailable: %s", exc)
            return []
