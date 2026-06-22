#!/usr/bin/env python3
"""Run an evaluation experiment and log metrics to MLflow when available.

Usage:
    python scripts/run_experiment.py
    python scripts/run_experiment.py --use-mlflow
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.evaluation.metrics import (
    compute_answer_relevance,
    compute_faithfulness,
)
from api.evaluation.schemas import EvaluationSample
from api.evaluation.testset import get_sample_testset
from api.experiments.schemas import ExperimentConfig
from api.experiments.tracker import ExperimentTracker


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG evaluation experiment")
    parser.add_argument("--use-mlflow", action="store_true", help="Log to MLflow if installed")
    args = parser.parse_args()

    config = ExperimentConfig(
        experiment_name="sample-eval-run",
        embedding_model="dummy",
        chunk_size=1000,
        overlap=200,
        top_k=5,
    )

    tracker = ExperimentTracker()
    run = tracker.start_run(config)

    faithfulness_scores = []
    relevance_scores = []
    retrieval_latencies = []
    generation_latencies = []

    for example in get_sample_testset():
        sample = EvaluationSample(
            question=example.question,
            expected_answer=example.ground_truth,
            generated_answer=example.answer,
            retrieved_chunk_ids=["sample-chunk"],
        )
        start = time.perf_counter()
        _ = compute_faithfulness(sample)
        retrieval_latencies.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        faithfulness_scores.append(compute_faithfulness(sample))
        relevance_scores.append(compute_answer_relevance(sample))
        generation_latencies.append((time.perf_counter() - start) * 1000)

    metrics = {
        "faithfulness_score_mean": sum(faithfulness_scores) / len(faithfulness_scores),
        "answer_relevance_score_mean": sum(relevance_scores) / len(relevance_scores),
        "mean_retrieval_latency_ms": sum(retrieval_latencies) / len(retrieval_latencies),
        "mean_generation_latency_ms": sum(generation_latencies) / len(generation_latencies),
    }
    tracker.log_metrics(run.run_id, metrics)
    print(f"Experiment run_id={run.run_id}")
    print("Metrics:", metrics)

    if args.use_mlflow:
        try:
            from api.experiments.mlflow_tracker import MLflowTracker

            mlflow_tracker = MLflowTracker()
            mlflow_run_id = mlflow_tracker.start_run(config)
            mlflow_tracker.log_metrics(metrics)
            mlflow_tracker.end_run()
            print(f"MLflow run_id={mlflow_run_id}")
        except ImportError as exc:
            print(f"MLflow logging skipped: {exc}")

    try:
        from api.evaluation.ragas_eval import evaluate_with_ragas_if_available

        ragas_result = evaluate_with_ragas_if_available()
        print("RAGAS details:", ragas_result.details)
    except ImportError as exc:
        print(f"RAGAS evaluation skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
