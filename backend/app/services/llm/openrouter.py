"""OpenRouter-compatible LLM provider.

Communicates with any OpenAI-compatible HTTP endpoint (OpenRouter by default).
The API key is never logged.
"""
from __future__ import annotations

import httpx

from app.core import get_logger
from app.core.errors import LLMError, ReadonlyRestrictionError
from app.services.llm.base import BaseLLMProvider
from app.services.llm.models import LLMResponse, LLMUsage

log = get_logger(__name__)

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseLLMProvider):
    """Provider that calls an OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        temperature: float = 0.0,
    ):
        if not api_key:
            raise ValueError("api_key is required for OpenRouterProvider")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/") if base_url else _OPENROUTER_BASE
        self._temperature = temperature

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout_seconds: int = 30,
    ) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                resp = client.post(url, json=payload, headers=self._headers())
        except httpx.TransportError as exc:
            raise LLMError(
                detail=f"LLM request failed: {type(exc).__name__}"
            ) from exc

        if resp.status_code != 200:
            log.error(
                "LLM API error",
                extra={"extra_data": {"status": resp.status_code}},
            )
            raise LLMError(
                detail=f"LLM provider returned HTTP {resp.status_code}"
            )

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(detail="Malformed LLM response") from exc

        if content is None:
            raise LLMError(
                message="LLM returned an empty or refused response.",
                detail="Response content was null (likely a model refusal).",
            )

        usage_data = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
        return LLMResponse(
            content=content,
            model=data.get("model", self._model),
            usage=usage,
            raw=data,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nl-to-sql.local",
            "X-Title": "nl-to-sql-backend",
        }
