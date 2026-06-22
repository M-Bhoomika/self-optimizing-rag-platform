#!/usr/bin/env python3
"""Generate synthetic demo held-out QA fixture (100 examples).

These are clearly marked demo/test fixtures, not real benchmark data.
"""

from __future__ import annotations

import json
from pathlib import Path

TOPICS = [
    ("retrieval-augmented generation", "RAG combines retrieval with generation."),
    ("tenant isolation", "Data is scoped by tenant_id across storage layers."),
    ("vector search", "Embeddings enable approximate nearest-neighbor retrieval."),
    ("query caching", "Repeated queries can be cached per tenant."),
    ("experiment tracking", "Evaluation runs can be logged for comparison."),
]

OUTPUT = Path(__file__).resolve().parents[1] / "api" / "evaluation" / "testsets" / "sample_qa_100.jsonl"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as handle:
        for index in range(100):
            topic, fact = TOPICS[index % len(TOPICS)]
            record = {
                "id": f"demo-{index + 1:03d}",
                "question": f"What should I know about {topic} (demo case {index + 1})?",
                "answer": fact,
                "contexts": [
                    f"Synthetic demo context {index + 1}: {fact}",
                    f"Additional demo note about {topic}.",
                ],
                "ground_truth": fact,
                "metadata": {
                    "fixture_type": "synthetic_demo",
                    "not_real_benchmark_data": True,
                },
            }
            handle.write(json.dumps(record) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
