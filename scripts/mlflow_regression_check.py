#!/usr/bin/env python3
"""Compare current RAGAS metrics against a production baseline file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.evaluation.ragas_eval import RagasEvaluator


DEFAULT_BASELINE = ROOT / "monitoring" / "mlflow_production_baseline.json"
METRIC_KEYS = (
    "ragas_faithfulness",
    "ragas_answer_relevance",
    "ragas_context_recall",
    "ragas_context_precision",
)


def _load_baseline(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", data)
    return {key: float(metrics[key]) for key in METRIC_KEYS if key in metrics}


def _current_metrics() -> Dict[str, float]:
    evaluator = RagasEvaluator(use_heuristic_fallback=True)
    result = evaluator.evaluate(use_held_out_fixture=True)
    return {
        "ragas_faithfulness": float(result.ragas_faithfulness or 0.0),
        "ragas_answer_relevance": float(result.ragas_answer_relevance or 0.0),
        "ragas_context_recall": float(result.ragas_context_recall or 0.0),
        "ragas_context_precision": float(result.ragas_context_precision or 0.0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MLflow/RAGAS regression gate")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--improvement-threshold", type=float, default=0.01)
    parser.add_argument("--regression-tolerance", type=float, default=0.0)
    args = parser.parse_args()

    if not args.baseline.exists():
        print(f"Baseline file not found: {args.baseline}")
        return 2

    baseline = _load_baseline(args.baseline)
    current = _current_metrics()

    print("Current metrics (heuristic over demo held-out fixture):")
    print(json.dumps(current, indent=2))
    print("Baseline metrics:")
    print(json.dumps(baseline, indent=2))

    improved = all(
        current[key] >= baseline[key] + args.improvement_threshold for key in METRIC_KEYS if key in baseline
    )
    regressed = any(current[key] < baseline[key] - args.regression_tolerance for key in METRIC_KEYS if key in baseline)

    if regressed:
        print("REGRESSION DETECTED: current metrics fell below baseline.")
        return 1
    if improved:
        print("PROMOTION RECOMMENDED: metrics improved by configured threshold.")
        return 0

    print("NO PROMOTION: metrics did not improve enough and did not regress.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
