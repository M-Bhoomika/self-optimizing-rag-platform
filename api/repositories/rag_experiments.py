"""RAG experiment persistence repository."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.rag_experiment import RagExperiment


class RagExperimentRepository:
    """Data-access methods for :class:`RagExperiment` rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_experiment(
        self,
        mlflow_run_id: str,
        config: Dict[str, Any],
        ragas_scores: Dict[str, Any],
        traffic_percentage: float = 0.0,
    ) -> RagExperiment:
        if not mlflow_run_id or not mlflow_run_id.strip():
            raise ValueError("mlflow_run_id must not be empty.")
        experiment = RagExperiment(
            mlflow_run_id=mlflow_run_id.strip(),
            config=config,
            ragas_scores=ragas_scores,
            traffic_percentage=traffic_percentage,
        )
        self.session.add(experiment)
        self.session.flush()
        return experiment

    def get_by_mlflow_run_id(self, mlflow_run_id: str) -> Optional[RagExperiment]:
        if not mlflow_run_id:
            raise ValueError("mlflow_run_id must not be empty.")
        stmt = select(RagExperiment).where(RagExperiment.mlflow_run_id == mlflow_run_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_experiments(self, limit: int = 50) -> List[RagExperiment]:
        stmt = select(RagExperiment).order_by(RagExperiment.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
