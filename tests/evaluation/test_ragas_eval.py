"""Tests for RAGAS evaluation integration."""

from __future__ import annotations

import pytest

from api.evaluation.ragas_eval import RagasEvaluator
from api.evaluation.testset import get_sample_testset


def test_sample_testset_is_small_and_realistic() -> None:
    rows = get_sample_testset()
    assert 1 <= len(rows) <= 10
    assert rows[0].question
    assert rows[0].contexts


def test_ragas_import_error_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    import api.evaluation.ragas_eval as ragas_module

    def _raise() -> None:
        raise ImportError("ragas missing")

    monkeypatch.setattr(ragas_module, "_require_ragas", _raise)
    with pytest.raises(ImportError, match="ragas"):
        RagasEvaluator(use_heuristic_fallback=False)


def test_ragas_heuristic_fallback_when_unavailable() -> None:
    result = RagasEvaluator(use_heuristic_fallback=True).evaluate()
    assert result.ragas_faithfulness is not None
    assert result.details["mode"] == "heuristic_fallback"


def test_ragas_evaluator_with_fake_ragas(monkeypatch: pytest.MonkeyPatch) -> None:
    import api.evaluation.ragas_eval as ragas_module

    monkeypatch.setattr(ragas_module, "_require_ragas", lambda: object())
    result = RagasEvaluator().evaluate(
        retrieval_latencies_ms=[10.0, 12.0],
        generation_latencies_ms=[20.0, 22.0],
    )
    assert result.mean_retrieval_latency_ms == 11.0
    assert result.mean_generation_latency_ms == 21.0
    assert result.details["example_count"] == len(get_sample_testset())
