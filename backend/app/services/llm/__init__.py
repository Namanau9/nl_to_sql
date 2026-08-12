"""Provider factory and re-exports for the LLM service layer."""
from __future__ import annotations

from app.services.llm.base import BaseLLMProvider
from app.services.llm.models import LLMMessage, LLMResponse, LLMUsage
from app.services.llm.mock import MockProvider
from app.services.llm.openrouter import OpenRouterProvider
from app.services.llm.service import LLMService

__all__ = [
    "BaseLLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMUsage",
    "MockProvider",
    "OpenRouterProvider",
    "LLMService",
    "create_provider",
]


def create_provider(
    provider_name: str = "mock",
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    base_url: str | None = None,
    temperature: float = 0.0,
) -> BaseLLMProvider:
    """Instantiate a provider by name.

    ``mock``  — deterministic canned responses (default, no API key).
    ``openai`` / ``openrouter`` — HTTP calls to an OpenAI-compatible endpoint.
    """
    name = provider_name.lower().strip()
    if name == "mock":
        return MockProvider()
    if name in ("openai", "openrouter", "openrouter-compatible"):
        return OpenRouterProvider(
            api_key=api_key or "",
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
    raise ValueError(f"Unknown LLM provider: {provider_name!r}")
