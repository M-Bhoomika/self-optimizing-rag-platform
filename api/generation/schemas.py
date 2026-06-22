"""Generation-domain Pydantic models."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Reference to a retrieved chunk used in answer generation."""

    chunk_id: str
    document_id: str
    chunk_text: str
    score: float = 0.0


class GenerationRequest(BaseModel):
    """Input for a generation call."""

    question: str
    context: str
    citations: List[Citation] = Field(default_factory=list)


class GenerationResponse(BaseModel):
    """Structured output from the generation layer."""

    answer: str
    prompt: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    model: str = "unknown"
    low_confidence: bool = False


class AnswerEvaluationResult(BaseModel):
    """Heuristic scores describing answer quality against provided context."""

    context_utilization_score: float = Field(ge=0.0, le=1.0)
    citation_coverage_score: float = Field(ge=0.0, le=1.0)
    answer_length_score: float = Field(ge=0.0, le=1.0)
