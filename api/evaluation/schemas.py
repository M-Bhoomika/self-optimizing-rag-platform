"""Evaluation-domain Pydantic models."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    """A single evaluation example: expected vs. generated answer plus retrieval."""

    question: str
    expected_answer: str
    generated_answer: str
    retrieved_chunk_ids: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Computed evaluation scores for a sample (all in [0, 1])."""

    faithfulness_score: float
    answer_relevance_score: float
    retrieval_precision: float
    retrieval_recall: float
