"""Read-only query execution with structured results and timing."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core import get_logger
from app.core.errors import ExecutionError
from app.database.connection import Database

log = get_logger(__name__)


@dataclass
class QueryResult:
    """Structured result of executing a validated query."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_ms: float
    status: str = "success"
    error: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_ms": round(self.execution_ms, 2),
            "status": self.status,
            "error": self.error,
        }


class ExecutionService:
    """Executes validated SQL through a read-only database connection."""

    def __init__(self, database: Database, row_limit: int = 1000):
        self._db = database
        self._row_limit = row_limit

    def execute(self, sql: str, row_limit: int | None = None) -> QueryResult:
        """Execute *sql* read-only and return a :class:`QueryResult`."""
        limit = row_limit or self._row_limit
        start = time.perf_counter()

        if not self._db.is_readonly_configured():
            raise ExecutionError(message="Read-only database connection is not configured.")

        try:
            columns, rows = self._db.execute_readonly(sql, row_limit=limit)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            log.error(
                "Query execution failed",
                extra={"extra_data": {"error": str(exc)}},
            )
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_ms=elapsed,
                status="error",
                error=str(exc),
            )

        elapsed = (time.perf_counter() - start) * 1000
        log.info(
            "Query executed",
            extra={"extra_data": {"columns": len(columns), "rows": len(rows), "ms": round(elapsed, 2)}},
        )
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_ms=elapsed,
        )