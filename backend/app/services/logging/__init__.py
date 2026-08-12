"""Structured query logging.

Captures the full lifecycle of a question: the original question, generated
SQL, validation result, execution status, duration, and any error.  Logs
are emitted as JSON via the standard logging infrastructure and never
include sensitive values (passwords, API keys are redacted by the logging
layer).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core import get_logger

log = get_logger(__name__)


@dataclass
class QueryLogEntry:
    """Immutable record of a single question-to-results cycle."""

    question: str
    sql: str | None = None
    validation_status: str = "pending"
    validation_error: str | None = None
    execution_status: str = "pending"
    execution_error: str | None = None
    row_count: int | None = None
    execution_ms: float | None = None
    explanation: str | None = None
    error: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QueryLogger:
    """Builds and persists :class:`QueryLogEntry` records for observability."""

    def __init__(self):
        self._entries: list[QueryLogEntry] = []

    def create_entry(self, question: str) -> QueryLogEntry:
        entry = QueryLogEntry(question=question)
        self._entries.append(entry)
        return entry

    def set_sql(self, entry: QueryLogEntry, sql: str) -> None:
        entry.sql = sql

    def set_validation(self, entry: QueryLogEntry, status: str, error: str | None = None) -> None:
        entry.validation_status = status
        entry.validation_error = error

    def set_execution(
        self,
        entry: QueryLogEntry,
        status: str,
        row_count: int | None = None,
        execution_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        entry.execution_status = status
        entry.row_count = row_count
        entry.execution_ms = execution_ms
        entry.execution_error = error

    def set_explanation(self, entry: QueryLogEntry, explanation: str) -> None:
        entry.explanation = explanation

    def set_error(self, entry: QueryLogEntry, error: str) -> None:
        entry.error = error

    def log(self, entry: QueryLogEntry) -> None:
        """Emit the entry as a structured JSON log line."""
        log.info(
            "Query lifecycle complete",
            extra={"extra_data": entry.to_dict()},
        )

    @property
    def entries(self) -> list[QueryLogEntry]:
        return list(self._entries)
