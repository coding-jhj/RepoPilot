from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, system: str, prompt: str) -> str:
        """Return a model completion for a small, scoped agent step."""


@dataclass
class FakeLLMProvider:
    label: str = "fake"

    def complete(self, system: str, prompt: str) -> str:
        if "bug" in prompt.lower():
            return "Potential issue found from retrieved evidence."
        if "patch" in prompt.lower():
            return "Generated a scoped patch draft."
        return "Generated a grounded repository summary."


@dataclass
class ExternalLLMProvider:
    provider: str
    model: str

    def complete(self, system: str, prompt: str) -> str:
        raise RuntimeError(
            f"{self.provider} provider is configured for production use but no "
            "network client is enabled in this local scaffold. Use FakeLLMProvider "
            "for tests or wire the SDK in this adapter."
        )


def build_llm_provider(provider: str) -> LLMProvider:
    if provider == "fake":
        return FakeLLMProvider()
    if provider in {"openai", "anthropic", "gemini", "ollama"}:
        return ExternalLLMProvider(provider=provider, model="configured-by-env")
    raise ValueError(f"Unsupported LLM provider: {provider}")
