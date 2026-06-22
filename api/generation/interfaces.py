"""Abstract interfaces for LLM generation providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, List


class LLMProvider(ABC):
    """Generates text from a fully assembled prompt string."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier used by this provider."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return complete model output for ``prompt``."""
        raise NotImplementedError

    def stream_generate(self, prompt: str) -> Iterator[str]:
        """Yield output token-by-token. Default: split ``generate`` output."""
        text = self.generate(prompt)
        for token in text.split():
            yield token + " "
