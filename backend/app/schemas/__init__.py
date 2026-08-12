"""Pydantic request/response schemas for the HTTP API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Natural-language business question")


class QueryResultSchema(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_ms: float


class QueryResponseSchema(BaseModel):
    question: str
    sql: str
    explanation: str
    results: QueryResultSchema | None = None
    status: str
    error: str | None = None
    execution_ms: float


class HealthResponse(BaseModel):
    status: str
    schema_tables: list[str] | None = None
