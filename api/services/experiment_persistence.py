"""Experiment persistence to PostgreSQL."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from api.repositories.rag_experiments import RagExperimentRepository

logger = logging.getLogger(__name__)


class ExperimentPersistenceService:
    """Persist evaluation runs to the ``rag_experiments`` table."""

    def persist_experiment(
        self,
        mlflow_run_id: str,
        config: Dict[str, Any],
        ragas_scores: Dict[str, Any],
        traffic_percentage: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return None
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                experiment = RagExperimentRepository(session).create_experiment(
                    mlflow_run_id=mlflow_run_id,
                    config=config,
                    ragas_scores=ragas_scores,
                    traffic_percentage=traffic_percentage,
                )
                return {
                    "id": str(experiment.id),
                    "mlflow_run_id": experiment.mlflow_run_id,
                    "traffic_percentage": experiment.traffic_percentage,
                }
        except Exception as exc:
            logger.warning("Experiment persistence skipped: %s", exc)
            return None

    def list_persisted(self, limit: int = 50) -> list[Dict[str, Any]]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return []
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                rows = RagExperimentRepository(session).list_experiments(limit=limit)
                return [
                    {
                        "id": str(row.id),
                        "mlflow_run_id": row.mlflow_run_id,
                        "config": row.config,
                        "ragas_scores": row.ragas_scores,
                        "traffic_percentage": row.traffic_percentage,
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in rows
                ]
        except Exception as exc:
            logger.warning("Experiment list unavailable: %s", exc)
            return []
