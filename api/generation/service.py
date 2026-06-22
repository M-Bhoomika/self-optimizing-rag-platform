"""Generation service and answer evaluation utilities."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, List, Optional, Set

from .factory import get_llm_provider
from .interfaces import LLMProvider
from .prompts import build_rag_prompt
from .schemas import AnswerEvaluationResult, Citation, GenerationResponse

_TOKEN_RE = re.compile(r"\w+")
LOW_CONFIDENCE_PREFIX = "Low-confidence answer:"


def _tokenize(text: str) -> Set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def context_utilization_score(answer: str, context: str) -> float:
    return _clamp(_jaccard(_tokenize(answer), _tokenize(context)))


def citation_coverage_score(answer: str, context: str) -> float:
    answer_tokens = _tokenize(answer)
    if not answer_tokens:
        return 0.0
    context_tokens = _tokenize(context)
    covered = sum(1 for token in answer_tokens if token in context_tokens)
    return _clamp(covered / len(answer_tokens))


def answer_length_score(answer: str, min_chars: int = 20, ideal_chars: int = 200) -> float:
    length = len(answer.strip())
    if length <= 0:
        return 0.0
    if length < min_chars:
        return _clamp(length / min_chars * 0.5)
    if length >= ideal_chars:
        return 1.0
    return _clamp(0.5 + ((length - min_chars) / (ideal_chars - min_chars)) * 0.5)


def compute_confidence_score(
    answer: str,
    context: str,
    retrieval_score: float,
) -> float:
    """Combine retrieval relevance with answer-context overlap."""
    overlap = context_utilization_score(answer, context)
    return _clamp(min(float(retrieval_score), overlap))


def chunks_to_citations(chunks: List[Dict[str, Any]]) -> List[Citation]:
    return [
        Citation(
            chunk_id=str(c.get("chunk_id", "")),
            document_id=str(c.get("document_id", "")),
            chunk_text=str(c.get("chunk_text", "")),
            score=float(c.get("score", 0.0)),
        )
        for c in chunks
    ]


class GenerationService:
    """Builds prompts and delegates generation to an :class:`LLMProvider`."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        confidence_threshold: float = 0.35,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.confidence_threshold = confidence_threshold

    def generate_answer(
        self,
        question: str,
        context: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        retrieval_score: float = 0.0,
        force_low_confidence: bool = False,
    ) -> GenerationResponse:
        if not question or not question.strip():
            raise ValueError("question must not be empty.")
        if not context or not context.strip():
            return GenerationResponse(
                answer=f"{LOW_CONFIDENCE_PREFIX} insufficient retrieval context.",
                prompt="",
                citations=chunks_to_citations(chunks or []),
                confidence_score=0.0,
                model=self.llm_provider.model_name,
                low_confidence=True,
            )

        prompt = build_rag_prompt(question=question, context=context)
        answer = self.llm_provider.generate(prompt)
        confidence = compute_confidence_score(answer, context, retrieval_score)
        low_confidence = force_low_confidence or confidence < self.confidence_threshold
        if low_confidence:
            answer = f"{LOW_CONFIDENCE_PREFIX} {answer}"

        return GenerationResponse(
            answer=answer,
            prompt=prompt,
            citations=chunks_to_citations(chunks or []),
            confidence_score=confidence,
            model=self.llm_provider.model_name,
            low_confidence=low_confidence,
        )

    def stream_answer(
        self,
        question: str,
        context: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        retrieval_score: float = 0.0,
        force_low_confidence: bool = False,
    ) -> Iterator[str]:
        if not question or not question.strip():
            raise ValueError("question must not be empty.")
        if not context or not context.strip():
            yield f"{LOW_CONFIDENCE_PREFIX} insufficient retrieval context."
            return

        prompt = build_rag_prompt(question=question, context=context)
        if force_low_confidence:
            yield f"{LOW_CONFIDENCE_PREFIX} "
        for token in self.llm_provider.stream_generate(prompt):
            yield token

    @staticmethod
    def evaluate_answer(question: str, answer: str, context: str) -> AnswerEvaluationResult:
        return AnswerEvaluationResult(
            context_utilization_score=context_utilization_score(answer, context),
            citation_coverage_score=citation_coverage_score(answer, context),
            answer_length_score=answer_length_score(answer),
        )
