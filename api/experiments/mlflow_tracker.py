"""MLflow experiment tracking integration."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import ExperimentConfig
from .tracker import ExperimentTracker


def _require_mlflow() -> Any:
    try:
        import mlflow  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "mlflow is required for MLflowTracker. Install with: pip install mlflow"
        ) from exc
    return mlflow


class MLflowTracker:
    """Logs experiment params/metrics to MLflow when available."""

    def __init__(self, experiment_name: str = "rag-platform") -> None:
        self._mlflow = _require_mlflow()
        self._mlflow.set_experiment(experiment_name)
        self._fallback = ExperimentTracker()
        self._active_run_id: Optional[str] = None

    def start_run(self, config: ExperimentConfig) -> str:
        run = self._mlflow.start_run(run_name=config.experiment_name)
        self._active_run_id = run.info.run_id
        self._mlflow.log_params(
            {
                "embedding_model": config.embedding_model,
                "chunk_size": config.chunk_size,
                "overlap": config.overlap,
                "top_k": config.top_k,
            }
        )
        return self._active_run_id

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        if self._active_run_id is None:
            raise RuntimeError("No active MLflow run. Call start_run() first.")
        self._mlflow.log_metrics(metrics)

    def end_run(self) -> None:
        if self._active_run_id is not None:
            self._mlflow.end_run()
            self._active_run_id = None

    @property
    def fallback_tracker(self) -> ExperimentTracker:
        """In-memory tracker used when MLflow is unavailable."""
        return self._fallback
