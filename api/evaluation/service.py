"""Evaluation execution service."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from api.evaluation.metrics import (
    compute_answer_relevance,
    compute_faithfulness,
    compute_retrieval_precision,
    compute_retrieval_recall,
)
from api.evaluation.schemas import EvaluationResult, EvaluationSample
from api.evaluation.testset import EvaluationExample, get_sample_testset
from api.experiments.schemas import ExperimentConfig
from api.experiments.tracker import ExperimentTracker
from api.generation.service import GenerationService
from api.observability.metrics import get_metrics
from api.retrieval.pipeline import IterativeRetrievalPipeline
from api.services.experiment_persistence import ExperimentPersistenceService


@dataclass
class EvaluationRunSummary:
    run_id: str
    example_count: int
    metrics: Dict[str, float]
    details: Dict[str, Any]


class EvaluationService:
    """Run evaluation configurations and record experiment metrics."""

    def __init__(
        self,
        pipeline: Optional[IterativeRetrievalPipeline] = None,
        generation_service: Optional[GenerationService] = None,
        tracker: Optional[ExperimentTracker] = None,
    ) -> None:
        self.pipeline = pipeline or IterativeRetrievalPipeline()
        self.generation_service = generation_service or self.pipeline.generation_service
        self.tracker = tracker or ExperimentTracker.shared()
        self.experiment_persistence = ExperimentPersistenceService()

    def evaluate_examples(
        self,
        tenant_id: str,
        examples: Optional[List[EvaluationExample]] = None,
        expected_chunk_map: Optional[Dict[str, List[str]]] = None,
    ) -> List[EvaluationResult]:
        rows = examples or get_sample_testset()
        results: List[EvaluationResult] = []
        chunk_map = expected_chunk_map or {}

        for example in rows:
            start = time.perf_counter()
            state = self.pipeline.run(tenant_id=tenant_id, query=example.question, top_k=5)
            latency_ms = (time.perf_counter() - start) * 1000
            chunks = state.get("reranked_chunks") or state.get("retrieved_chunks", [])
            retrieved_ids = [str(c.get("chunk_id", "")) for c in chunks]
            generated = str(state.get("answer", ""))

            sample = EvaluationSample(
                question=example.question,
                expected_answer=example.ground_truth,
                generated_answer=generated,
                retrieved_chunk_ids=retrieved_ids,
            )
            expected_chunks = chunk_map.get(example.question, retrieved_ids)
            recall = compute_retrieval_recall(sample, expected_chunks)
            results.append(
                EvaluationResult(
                    faithfulness_score=compute_faithfulness(sample),
                    answer_relevance_score=compute_answer_relevance(sample),
                    retrieval_precision=compute_retrieval_precision(sample, expected_chunks),
                    retrieval_recall=recall,
                )
            )
            metrics = get_metrics()
            if metrics.enabled and metrics.context_recall_score is not None:
                metrics.context_recall_score.set(recall)
            _ = latency_ms
        return results

    def run_experiment(
        self,
        config: ExperimentConfig,
        tenant_id: str = "eval-tenant",
        use_mlflow: bool = False,
    ) -> EvaluationRunSummary:
        run = self.tracker.start_run(config)
        results = self.evaluate_examples(tenant_id=tenant_id)

        metrics = {
            "faithfulness_score_mean": sum(r.faithfulness_score for r in results) / len(results),
            "answer_relevance_score_mean": sum(r.answer_relevance_score for r in results) / len(results),
            "retrieval_precision_mean": sum(r.retrieval_precision for r in results) / len(results),
            "retrieval_recall_mean": sum(r.retrieval_recall for r in results) / len(results),
            "example_count": float(len(results)),
        }
        self.tracker.log_metrics(run.run_id, metrics)

        mlflow_run_id: Optional[str] = None
        if use_mlflow:
            try:
                from api.experiments.mlflow_tracker import MLflowTracker

                mlflow = MLflowTracker(experiment_name=config.experiment_name)
                mlflow_run_id = mlflow.start_run(config)
                mlflow.log_metrics(metrics)
                mlflow.end_run()
            except ImportError:
                mlflow_run_id = None

        ragas_scores: Dict[str, Optional[float]] = {}
        try:
            from api.evaluation.ragas_eval import RagasEvaluator

            ragas = RagasEvaluator(use_heuristic_fallback=True)
            ragas_result = ragas.evaluate()
            ragas_scores = {
                "ragas_faithfulness": ragas_result.ragas_faithfulness,
                "ragas_answer_relevance": ragas_result.ragas_answer_relevance,
                "ragas_context_recall": ragas_result.ragas_context_recall,
                "ragas_context_precision": ragas_result.ragas_context_precision,
            }
            numeric = {k: v for k, v in ragas_scores.items() if v is not None}
            if numeric:
                self.tracker.log_metrics(run.run_id, numeric)
        except ImportError:
            pass

        persisted = self.experiment_persistence.persist_experiment(
            mlflow_run_id=mlflow_run_id or run.run_id,
            config=config.model_dump(),
            ragas_scores={k: v for k, v in ragas_scores.items() if v is not None} or metrics,
            traffic_percentage=0.0,
        )

        return EvaluationRunSummary(
            run_id=run.run_id,
            example_count=len(results),
            metrics={**metrics, **{k: v for k, v in ragas_scores.items() if v is not None}},
            details={
                "mlflow_run_id": mlflow_run_id,
                "config": config.model_dump(),
                "postgres_experiment_id": persisted.get("id") if persisted else None,
            },
        )
