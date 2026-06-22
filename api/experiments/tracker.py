"""In-memory and optional MLflow experiment tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .schemas import ExperimentConfig, ExperimentRun


class ExperimentTracker:
    """Stores experiment runs in memory, keyed by run id."""

    _shared: "ExperimentTracker | None" = None

    def __init__(self) -> None:
        self._runs: Dict[str, ExperimentRun] = {}

    @classmethod
    def shared(cls) -> "ExperimentTracker":
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def start_run(self, config: ExperimentConfig) -> ExperimentRun:
        run_id = str(uuid.uuid4())
        run = ExperimentRun(
            run_id=run_id,
            config=config,
            metrics={},
            created_at=datetime.now(timezone.utc),
        )
        self._runs[run_id] = run
        return run

    def log_metrics(self, run_id: str, metrics: Dict[str, float]) -> ExperimentRun:
        if run_id not in self._runs:
            raise KeyError(f"Unknown run_id: {run_id!r}")
        run = self._runs[run_id]
        updated_metrics = {**run.metrics, **metrics}
        updated_run = run.model_copy(update={"metrics": updated_metrics})
        self._runs[run_id] = updated_run
        return updated_run

    def get_run(self, run_id: str) -> ExperimentRun:
        if run_id not in self._runs:
            raise KeyError(f"Unknown run_id: {run_id!r}")
        return self._runs[run_id]

    def list_runs(self) -> List[ExperimentRun]:
        return list(self._runs.values())


class CompositeExperimentTracker:
    """Fan-out tracker that logs to in-memory storage and optional MLflow."""

    def __init__(
        self,
        memory: Optional[ExperimentTracker] = None,
        use_mlflow: bool = False,
        experiment_name: str = "rag-platform",
    ) -> None:
        self._memory = memory or ExperimentTracker.shared()
        self._use_mlflow = use_mlflow
        self._experiment_name = experiment_name
        self._mlflow = None
        self._mlflow_run_id: Optional[str] = None
        if use_mlflow:
            try:
                from .mlflow_tracker import MLflowTracker

                self._mlflow = MLflowTracker(experiment_name=experiment_name)
            except ImportError:
                self._mlflow = None

    def start_run(self, config: ExperimentConfig) -> ExperimentRun:
        run = self._memory.start_run(config)
        if self._mlflow is not None:
            self._mlflow_run_id = self._mlflow.start_run(config)
        return run

    def log_metrics(self, run_id: str, metrics: Dict[str, float]) -> ExperimentRun:
        run = self._memory.log_metrics(run_id, metrics)
        if self._mlflow is not None:
            self._mlflow.log_metrics(metrics)
        return run

    def end_run(self) -> None:
        if self._mlflow is not None:
            self._mlflow.end_run()
            self._mlflow_run_id = None

    @property
    def memory(self) -> ExperimentTracker:
        return self._memory
