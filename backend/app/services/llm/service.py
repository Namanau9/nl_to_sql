"""LLM service: build prompts, call provider, extract SQL.

The :class:`LLMService` ties together a configured :class:`BaseLLMProvider`
with the schema-context selection that was already performed.  It is
responsible for prompt assembly and SQL extraction, *not* validation -- that
is handled by the SQL validator module.
"""
from __future__ import annotations

import re

from app.core import get_logger
from app.core.errors import LLMError
from app.services.llm.base import BaseLLMProvider
from app.services.llm.models import LLMResponse
from app.services.schema.discovery import DatabaseSchema

log = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are a SQL generation assistant. Convert the user's question into a single,
valid PostgreSQL query.

Rules:
- Use ONLY the tables and columns provided in the schema context below.
- Do NOT invent table or column names that are not listed.
- Output only the SQL query. No explanations, no markdown fences.
- If the question cannot be answered with the given schema, output nothing.
- Use snake_case for aliases and prefer lowercase SQL keywords.

Schema:
{schema_context}
"""

_SQL_FENCE_RE = re.compile(r"```sql\n(.*?)```", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```\n(.*?)```", re.DOTALL)


def _extract_sql(raw: str) -> str:
    """Pull the first SQL statement out of an LLM response.

    Handles markdown code-fences, inline backticks, and raw SQL.
    """
    text = raw.strip()

    match = _SQL_FENCE_RE.search(text)
    if match:
        text = match.group(1).strip()
    else:
        match = _CODE_FENCE_RE.search(text)
        if match:
            text = match.group(1).strip()

    text = text.strip("`").strip()

    lines = text.splitlines()
    if lines:
        first = lines[0].strip().upper()
        if first.startswith("EXPLAIN"):
            lines = lines[1:]
            text = "\n".join(lines).strip()

    if not text:
        raise LLMError(message="LLM response contained no SQL.")

    upper = text.upper()
    if not any(upper.startswith(kw) for kw in ("SELECT", "WITH", "VALUES")):
        raise LLMError(message="LLM response did not contain SQL.")

    return text


class LLMService:
    """High-level orchestration of prompt assembly and SQL extraction."""

    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        return self._provider

    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        temperature: float = 0.0,
        max_tokens: int | None = 4000,
        timeout_seconds: int = 30,
    ) -> str:
        """Generate a SQL query for *question* using the provided *schema*."""
        if not question or not question.strip():
            raise LLMError(message="Empty question provided to LLMService.")

        schema_context = schema.to_llm_context()
        system = _SYSTEM_PROMPT.format(schema_context=schema_context)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question.strip()},
        ]

        log.info("Requesting SQL generation", extra={"extra_data": {"question": question}})

        try:
            response = self._provider.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                message=f"Unexpected provider error: {type(exc).__name__}"
            ) from exc

        sql = _extract_sql(response.content)

        log.info("SQL generated", extra={"extra_data": {"model": response.model, "length": len(sql)}})
        return sql

    def generate_explanation(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list],
        temperature: float = 0.0,
        timeout_seconds: int = 30,
    ) -> str:
        """Summarize query results in natural language grounded in the data."""
        system = (
            "You are a helpful data assistant. Summarize the query results "
            "in a concise natural-language response that directly answers the "
            "user's question. Use only the data shown; do not invent facts. "
            "Do not output SQL."
        )

        result_text = _format_results(columns, rows)
        user_msg = (
            f"Question: {question}\n\n"
            f"SQL:\n```sql\n{sql}\n```\n\n"
            f"Results:\n{result_text}"
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

        try:
            response = self._provider.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
                timeout_seconds=timeout_seconds,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                message=f"Unexpected provider error: {type(exc).__name__}"
            ) from exc

        return response.content.strip()


def _format_results(columns: list[str], rows: list[list]) -> str:
    if not rows:
        return "(no rows returned)"
    lines = [",".join(columns)]
    for row in rows[:50]:
        lines.append(",".join(str(v) if v is not None else "" for v in row))
    if len(rows) > 50:
        lines.append(f"... ({len(rows) - 50} more rows)")
    return "\n".join(lines)
