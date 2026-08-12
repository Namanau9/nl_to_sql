"""Data models shared across LLM providers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """Result of a single LLM completion request."""

    content: str
    model: str = ""
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw: dict[str, Any] | None = None
