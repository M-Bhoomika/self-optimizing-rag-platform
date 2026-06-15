"""Deterministic placeholder evaluation metrics.

These are lightweight, dependency-free heuristics that return scores in
``[0, 1]``. They exist so the evaluation/experiment pipeline can be exercised
end to end before a real metrics backend is wired in.

TODO: Replace these heuristics with RAGAS-based metrics (faithfulness, answer
relevance, context precision/recall). The function signatures should stay
stable so callers are unaffected.
"""

from __future__ import annotations

import re
from typing import List, Set

from .schemas import EvaluationSample

_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> Set[str]:
    """Lowercase word-token set for simple overlap heuristics."""
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Jaccard similarity of two token sets; 0.0 when both are empty."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _clamp(value: float) -> float:
    """Clamp a score into [0, 1]."""
    return max(0.0, min(1.0, value))


def compute_faithfulness(sample: EvaluationSample) -> float:
    """Heuristic faithfulness: token overlap of generated vs. expected answer.

    Proxy for how grounded the generated answer is in the expected answer.
    """
    score = _jaccard(_tokenize(sample.generated_answer), _tokenize(sample.expected_answer))
    return _clamp(score)


def compute_answer_relevance(sample: EvaluationSample) -> float:
    """Heuristic answer relevance: token overlap of generated answer vs. question."""
    score = _jaccard(_tokenize(sample.generated_answer), _tokenize(sample.question))
    return _clamp(score)


def compute_retrieval_precision(
    sample: EvaluationSample, expected_chunk_ids: List[str]
) -> float:
    """Fraction of retrieved chunks that are relevant (in ``expected_chunk_ids``)."""
    retrieved = sample.retrieved_chunk_ids
    if not retrieved:
        return 0.0
    expected: Set[str] = set(expected_chunk_ids)
    relevant = sum(1 for cid in retrieved if cid in expected)
    return _clamp(relevant / len(retrieved))


def compute_retrieval_recall(
    sample: EvaluationSample, expected_chunk_ids: List[str]
) -> float:
    """Fraction of expected chunks that were retrieved."""
    expected: Set[str] = set(expected_chunk_ids)
    if not expected:
        return 0.0
    retrieved: Set[str] = set(sample.retrieved_chunk_ids)
    found = len(expected & retrieved)
    return _clamp(found / len(expected))
