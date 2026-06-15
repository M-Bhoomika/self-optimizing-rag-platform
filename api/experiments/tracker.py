"""In-memory experiment tracker.

Tracks experiment runs and their metrics in a process-local dictionary. This is
a stand-in for a real tracking backend during early development.

TODO: Add an MLflow-backed implementation. ``start_run`` would map to
``mlflow.start_run`` (storing the returned run id), ``log_metrics`` to
``mlflow.log_metrics``, and config fields to ``mlflow.log_params``. Keep this
class's public methods as the stable interface so callers don't change.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from .schemas import ExperimentConfig, ExperimentRun


class ExperimentTracker:
    """Stores experiment runs in memory, keyed by run id."""

    def __init__(self) -> None:
        self._runs: Dict[str, ExperimentRun] = {}

    def start_run(self, config: ExperimentConfig) -> ExperimentRun:
        """Create and store a new run for ``config``; returns the run."""
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
        """Merge ``metrics`` into an existing run; returns the updated run.

        Raises:
            KeyError: if ``run_id`` is unknown.
        """
        if run_id not in self._runs:
            raise KeyError(f"Unknown run_id: {run_id!r}")
        run = self._runs[run_id]
        updated_metrics = {**run.metrics, **metrics}
        updated_run = run.model_copy(update={"metrics": updated_metrics})
        self._runs[run_id] = updated_run
        return updated_run

    def get_run(self, run_id: str) -> ExperimentRun:
        """Return the run for ``run_id``.

        Raises:
            KeyError: if ``run_id`` is unknown.
        """
        if run_id not in self._runs:
            raise KeyError(f"Unknown run_id: {run_id!r}")
        return self._runs[run_id]

    def list_runs(self) -> List[ExperimentRun]:
        """Return all tracked runs in insertion order."""
        return list(self._runs.values())
