"""Evaluation service execution tests."""

from __future__ import annotations

from api.evaluation.service import EvaluationService
from api.experiments.schemas import ExperimentConfig


def test_run_experiment_returns_metrics() -> None:
    service = EvaluationService()
    summary = service.run_experiment(
        ExperimentConfig(
            experiment_name="unit-test",
            embedding_model="dummy",
            chunk_size=500,
            overlap=50,
            top_k=3,
        ),
        tenant_id="eval-tenant",
    )
    assert summary.example_count >= 1
    assert "faithfulness_score_mean" in summary.metrics
    assert summary.run_id
