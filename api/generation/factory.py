"""Factory for LLM provider selection."""

from __future__ import annotations

import os

from .interfaces import LLMProvider
from .providers import LocalFallbackProvider, OpenAICompatibleProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider based on environment variables.

    ``LLM_PROVIDER`` values:
    - ``openai`` — OpenAI-compatible API (requires ``OPENAI_API_KEY``)
    - ``local`` or unset — offline local fallback provider
    """
    provider = os.getenv("LLM_PROVIDER", "local").strip().lower()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleProvider()
    return LocalFallbackProvider()
