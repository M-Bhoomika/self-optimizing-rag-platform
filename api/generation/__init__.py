"""Generation layer exports."""

from .factory import get_llm_provider
from .interfaces import LLMProvider
from .prompts import build_evaluation_prompt, build_rag_prompt
from .providers import DummyLLMProvider, LocalFallbackProvider, OpenAICompatibleProvider
from .schemas import AnswerEvaluationResult, Citation, GenerationRequest, GenerationResponse
from .service import (
    GenerationService,
    answer_length_score,
    citation_coverage_score,
    compute_confidence_score,
    context_utilization_score,
)

__all__ = [
    "LLMProvider",
    "GenerationRequest",
    "GenerationResponse",
    "Citation",
    "AnswerEvaluationResult",
    "DummyLLMProvider",
    "LocalFallbackProvider",
    "OpenAICompatibleProvider",
    "get_llm_provider",
    "GenerationService",
    "build_rag_prompt",
    "build_evaluation_prompt",
    "context_utilization_score",
    "citation_coverage_score",
    "answer_length_score",
    "compute_confidence_score",
]
