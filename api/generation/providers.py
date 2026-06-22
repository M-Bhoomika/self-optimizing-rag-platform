"""LLM provider implementations."""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Iterator, List, Optional
from urllib import error, request

from .interfaces import LLMProvider

DEFAULT_PROMPT_PREVIEW_CHARS = 120
_CONTEXT_RE = re.compile(r"### Context\s*\n(.*?)\n### Question", re.DOTALL)
_QUESTION_RE = re.compile(r"### Question\s*\n(.*?)\n### Answer", re.DOTALL)


def _extract_section(pattern: re.Pattern[str], prompt: str) -> str:
    match = pattern.search(prompt)
    return match.group(1).strip() if match else ""


class LocalFallbackProvider(LLMProvider):
    """Offline provider that grounds answers in retrieved context without API calls."""

    def __init__(self, preview_chars: int = DEFAULT_PROMPT_PREVIEW_CHARS) -> None:
        if preview_chars <= 0:
            raise ValueError("preview_chars must be greater than 0.")
        self.preview_chars = preview_chars

    @property
    def model_name(self) -> str:
        return "local-fallback"

    def generate(self, prompt: str) -> str:
        context = _extract_section(_CONTEXT_RE, prompt)
        question = _extract_section(_QUESTION_RE, prompt)
        if not context:
            return "I do not have enough context to answer that question confidently."
        lead = context.split(".")[0].strip()
        if question:
            return f"Based on the provided context, {lead}. This addresses: {question}"
        return f"Based on the provided context, {lead}."

    def stream_generate(self, prompt: str) -> Iterator[str]:
        for token in self.generate(prompt).split():
            yield token + " "


class DummyLLMProvider(LocalFallbackProvider):
    """Backward-compatible alias for tests expecting deterministic dummy output."""

    @property
    def model_name(self) -> str:
        return "dummy-llm"

    def generate(self, prompt: str) -> str:
        normalized = prompt.strip()
        preview = normalized[: self.preview_chars]
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return (
            f"[dummy-llm:{digest}] "
            f"Generated answer based on prompt preview: {preview}"
        )


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible chat completions provider (OpenAI, Azure, local gateways)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAICompatibleProvider.")

    @property
    def model_name(self) -> str:
        return self._model

    def _chat_payload(self, prompt: str, stream: bool) -> dict:
        return {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }

    def _post(self, payload: dict) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def generate(self, prompt: str) -> str:
        payload = self._chat_payload(prompt, stream=False)
        try:
            raw = self._post(payload)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI-compatible API error: {detail}") from exc
        data = json.loads(raw.decode("utf-8"))
        return str(data["choices"][0]["message"]["content"]).strip()

    def stream_generate(self, prompt: str) -> Iterator[str]:
        payload = self._chat_payload(prompt, stream=True)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                for line in resp:
                    decoded = line.decode("utf-8").strip()
                    if not decoded.startswith("data:"):
                        continue
                    chunk = decoded[len("data:") :].strip()
                    if chunk == "[DONE]":
                        break
                    data = json.loads(chunk)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content")
                    if token:
                        yield token
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI-compatible stream error: {detail}") from exc
