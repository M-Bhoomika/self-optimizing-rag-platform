"""Settings validation tests."""

from __future__ import annotations

import pytest

from api.config.settings import ApplicationSettings


def test_validate_rejects_unknown_retrieval_backend() -> None:
    settings = ApplicationSettings()
    settings.retrieval.backend = "unknown"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="RETRIEVAL_BACKEND"):
        settings.validate()


def test_validate_requires_openai_key_when_provider_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = ApplicationSettings()
    settings.llm.provider = "openai"
    settings.llm.openai_api_key = ""
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        settings.validate()
