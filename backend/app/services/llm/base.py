"""Abstract base for LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.llm.models import LLMResponse


class BaseLLMProvider(ABC):
    """Minimal provider interface: given messages, return a completion string."""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout_seconds: int = 30,
    ) -> LLMResponse:
        """Return an :class:`LLMResponse` for the given conversation."""
        raise NotImplementedError
