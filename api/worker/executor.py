"""Execute background worker tasks."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def execute_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Run a queued task and return a result summary."""
    task_type = str(task.get("type", "")).strip()
    payload = dict(task.get("payload") or {})
    task_id = str(task.get("task_id", ""))

    if task_type == "ingest":
        return _execute_ingest(task_id, payload)
    if task_type == "evaluate":
        return _execute_evaluate(task_id, payload)

    raise ValueError(f"Unsupported task type: {task_type}")


def _execute_ingest(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from api.worker.ingest_pipeline import run_full_ingestion

    result = run_full_ingestion(payload)
    logger.info("Worker ingest completed task_id=%s chunks=%s", task_id, result.get("ingestion", {}).get("chunk_count"))
    return {"task_id": task_id, **result}


def _execute_evaluate(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from api.app.dependencies import get_evaluation_service
    from api.experiments.schemas import ExperimentConfig

    config_data = dict(payload.get("config") or {})
    config = ExperimentConfig(
        experiment_name=str(config_data.get("experiment_name", "worker-eval")),
        embedding_model=str(config_data.get("embedding_model", "dummy")),
        chunk_size=int(config_data.get("chunk_size", 1000)),
        overlap=int(config_data.get("overlap", 200)),
        top_k=int(config_data.get("top_k", 5)),
    )
    summary = get_evaluation_service().run_experiment(
        config=config,
        tenant_id=str(payload.get("tenant_id", "eval-tenant")),
        use_mlflow=bool(payload.get("use_mlflow", False)),
    )
    logger.info("Worker evaluate completed task_id=%s run_id=%s", task_id, summary.run_id)
    return {
        "task_id": task_id,
        "status": "completed",
        "run_id": summary.run_id,
        "metrics": summary.metrics,
    }
