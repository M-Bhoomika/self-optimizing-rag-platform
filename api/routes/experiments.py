"""Experiment and evaluation API routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.app.dependencies import get_evaluation_service
from api.evaluation.service import EvaluationService
from api.experiments.schemas import ExperimentConfig
from api.experiments.tracker import ExperimentTracker
from api.services.experiment_persistence import ExperimentPersistenceService

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


class RunExperimentRequest(BaseModel):
    experiment_name: str = "api-eval-run"
    embedding_model: str = "dummy"
    chunk_size: int = 1000
    overlap: int = 200
    top_k: int = 5
    tenant_id: str = "eval-tenant"
    use_mlflow: bool = False


@router.post("/run")
def run_experiment(
    request: RunExperimentRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> Dict[str, Any]:
    config = ExperimentConfig(
        experiment_name=request.experiment_name,
        embedding_model=request.embedding_model,
        chunk_size=request.chunk_size,
        overlap=request.overlap,
        top_k=request.top_k,
    )
    summary = evaluation_service.run_experiment(
        config=config,
        tenant_id=request.tenant_id,
        use_mlflow=request.use_mlflow,
    )
    return {
        "run_id": summary.run_id,
        "example_count": summary.example_count,
        "metrics": summary.metrics,
        "details": summary.details,
    }


@router.get("/runs")
def list_runs() -> List[Dict[str, Any]]:
    in_memory = [
        {
            "run_id": run.run_id,
            "experiment_name": run.config.experiment_name,
            "metrics": run.metrics,
            "created_at": run.created_at.isoformat(),
            "source": "memory",
        }
        for run in ExperimentTracker.shared().list_runs()
    ]
    persisted = [
        {**row, "run_id": row.get("mlflow_run_id"), "source": "postgres"}
        for row in ExperimentPersistenceService().list_persisted()
    ]
    return persisted + in_memory


@router.get("/metrics/summary")
def metrics_summary() -> Dict[str, Any]:
    runs = ExperimentTracker.shared().list_runs()
    if not runs:
        return {"run_count": 0, "metrics": {}}
    latest = runs[-1]
    return {"run_count": len(runs), "latest_run_id": latest.run_id, "metrics": latest.metrics}
