"""Domain models for the query pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnValue:
    name: str
    data_type: str | None = None
    value: Any = None


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_ms": round(self.execution_ms, 2),
        }


@dataclass
class QueryResponse:
    question: str
    sql: str
    explanation: str
    results: QueryResult | None = None
    status: str = "success"
    error: str | None = None
    execution_ms: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "sql": self.sql,
            "explanation": self.explanation,
            "results": self.results.to_dict() if self.results else None,
            "status": self.status,
            "error": self.error,
            "execution_ms": round(self.execution_ms, 2),
        }
