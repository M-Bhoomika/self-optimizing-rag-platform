"""Load held-out demo QA fixtures for RAGAS evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .testset import EvaluationExample

FIXTURE_PATH = Path(__file__).resolve().parent / "testsets" / "sample_qa_100.jsonl"


def load_held_out_testset(limit: int | None = None) -> List[EvaluationExample]:
    """Load synthetic demo QA pairs from ``sample_qa_100.jsonl``."""
    if not FIXTURE_PATH.exists():
        raise FileNotFoundError(
            f"Held-out fixture missing: {FIXTURE_PATH}. "
            "Run scripts/generate_demo_testset.py to create it."
        )

    rows: List[EvaluationExample] = []
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rows.append(
                EvaluationExample(
                    question=str(record["question"]),
                    answer=str(record.get("answer", "")),
                    contexts=[str(c) for c in record.get("contexts", [])],
                    ground_truth=str(record["ground_truth"]),
                )
            )
            if limit is not None and len(rows) >= limit:
                break
    return rows
