"""HTTP API routes: question-to-SQL pipeline endpoint.

POST /api/query  — runs the full pipeline:
  schema discovery -> relevance selection -> SQL generation ->
  AST validation -> read-only execution -> explanation

GET  /api/health  — liveness + schema availability check.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import get_logger
from app.core.errors import AppError
from app.database.connection import Database
from app.schemas import HealthResponse, QueryRequest, QueryResponseSchema
from app.services.execution import ExecutionService
from app.services.llm import LLMService
from app.services.logging import QueryLogger
from app.services.schema.discovery import SchemaDiscoveryService
from app.services.schema.relevance import RelevanceSelector
from app.services.sql.validator import SQLValidator

log = get_logger(__name__)

router = APIRouter(prefix="/api")


def _now_ms() -> float:
    return time.perf_counter() * 1000


# Dependency factories
_db: Database | None = None
_llm: LLMService | None = None
_logger: QueryLogger | None = None


def get_database() -> Database:
    global _db
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not initialised.")
    return _db


def get_discovery_service(db: Database = Depends(get_database)) -> SchemaDiscoveryService:
    return SchemaDiscoveryService(db.discovery_engine)


def get_execution_service(db: Database = Depends(get_database)) -> ExecutionService:
    return ExecutionService(db, row_limit=1000)


def get_llm_service() -> LLMService:
    global _llm
    if _llm is None:
        raise HTTPException(status_code=503, detail="LLM service not configured.")
    return _llm


def get_query_logger() -> QueryLogger:
    global _logger
    if _logger is None:
        _logger = QueryLogger()
    return _logger


def configure_services(database: Database, llm_service: LLMService) -> None:
    """Called by main.py during startup to inject service instances."""
    global _db, _llm
    _db = database
    _llm = llm_service


@router.get("/health", response_model=HealthResponse)
def health(discovery: SchemaDiscoveryService = Depends(get_discovery_service)):
    try:
        schema = discovery.discover()
        return HealthResponse(status="ok", schema_tables=schema.table_names)
    except Exception:
        return HealthResponse(status="degraded", schema_tables=None)


@router.post("/query", response_model=QueryResponseSchema)
def query(
    request: QueryRequest,
    discovery: SchemaDiscoveryService = Depends(get_discovery_service),
    llm: LLMService = Depends(get_llm_service),
    execution: ExecutionService = Depends(get_execution_service),
    logger: QueryLogger = Depends(get_query_logger),
):
    """Run a natural-language question through the full analytics pipeline."""
    entry = logger.create_entry(question=request.question)
    start_ms = _now_ms()

    try:
        # 1. Schema discovery
        schema = discovery.discover()

        # 2. Relevance selection
        relevant = RelevanceSelector(schema).select(request.question)

        # 3. SQL generation
        sql = llm.generate_sql(request.question, relevant)
        logger.set_sql(entry, sql)

        # 4. Validation
        validator = SQLValidator(allowed_tables=relevant.table_names)
        validator.validate(sql)
        logger.set_validation(entry, "passed")

        # 5. Execution
        result = execution.execute(sql)
        logger.set_execution(
            entry,
            result.status,
            row_count=result.row_count,
            execution_ms=result.execution_ms,
            error=result.error,
        )

        # 6. Explanation (use whatever rows we got, even if execution had an error)
        explanation = llm.generate_explanation(
            request.question, sql, result.columns, result.rows
        )
        logger.set_explanation(entry, explanation)

        total_ms = _now_ms() - start_ms
        logger.log(entry)

        response_status = "success" if result.status == "success" else "error"
        return QueryResponseSchema(
            question=request.question,
            sql=sql,
            explanation=explanation,
            results=result.to_dict() if result else None,
            status=response_status,
            error=result.error if result.status == "error" else None,
            execution_ms=total_ms,
        )

    except AppError as exc:
        logger.set_error(entry, exc.user_message)
        logger.log(entry)
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.user_message,
        )
    except HTTPException:
        logger.log(entry)
        raise
    except Exception as exc:
        logger.set_error(entry, str(exc))
        logger.log(entry)
        log.error("Unhandled pipeline error", extra={"extra_data": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question.",
        )
