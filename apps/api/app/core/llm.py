from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMError(RuntimeError):
    """Raised when a real LLM provider call fails (network, quota, bad key)."""


class LLMProvider(Protocol):
    enabled: bool

    def complete(self, system: str, prompt: str) -> str:
        """Return a model completion for a small, scoped agent step."""


@dataclass
class FakeLLMProvider:
    """Deterministic, offline default. Keeps the free-first path working with no key."""

    label: str = "fake"
    enabled: bool = False

    def complete(self, system: str, prompt: str) -> str:
        if "bug" in prompt.lower():
            return "Potential issue found from retrieved evidence."
        if "patch" in prompt.lower():
            return "Generated a scoped patch draft."
        return "Generated a grounded repository summary."


@dataclass
class GeminiLLMProvider:
    """Free-tier Google Gemini provider via REST (no SDK dependency)."""

    api_key: str
    model: str = DEFAULT_GEMINI_MODEL
    timeout_seconds: float = 30.0
    enabled: bool = True

    def complete(self, system: str, prompt: str) -> str:
        url = GEMINI_ENDPOINT.format(model=self.model)
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }
        try:
            response = httpx.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            raise LLMError(f"Gemini request failed ({exc.response.status_code}): {detail}") from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"Gemini response could not be parsed: {exc}") from exc


def build_llm_provider(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    if provider == "fake":
        return FakeLLMProvider()
    if provider == "gemini":
        if not api_key:
            return FakeLLMProvider()
        return GeminiLLMProvider(api_key=api_key, model=model or DEFAULT_GEMINI_MODEL)
    raise ValueError(f"Unsupported LLM provider: {provider}")
