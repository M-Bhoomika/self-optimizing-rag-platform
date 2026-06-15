"""Evaluation foundation for the RAG platform.

Exposes evaluation schemas and the deterministic placeholder metric functions.
"""

from .metrics import (
    compute_answer_relevance,
    compute_faithfulness,
    compute_retrieval_precision,
    compute_retrieval_recall,
)
from .schemas import EvaluationResult, EvaluationSample

__all__ = [
    "EvaluationSample",
    "EvaluationResult",
    "compute_faithfulness",
    "compute_answer_relevance",
    "compute_retrieval_precision",
    "compute_retrieval_recall",
]
