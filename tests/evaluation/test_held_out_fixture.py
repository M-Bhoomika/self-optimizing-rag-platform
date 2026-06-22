"""Held-out demo fixture tests."""

from __future__ import annotations

from api.evaluation.fixtures import load_held_out_testset
from api.evaluation.ragas_eval import RagasEvaluator


def test_sample_qa_100_fixture_loads() -> None:
    rows = load_held_out_testset()
    assert len(rows) == 100
    assert rows[0].question


def test_ragas_runs_over_held_out_fixture() -> None:
    evaluator = RagasEvaluator(use_heuristic_fallback=True)
    result = evaluator.evaluate(use_held_out_fixture=True, held_out_limit=10)
    assert result.details["example_count"] == 10
    assert result.ragas_faithfulness is not None
    assert "synthetic demo" in result.details["fixture"]
