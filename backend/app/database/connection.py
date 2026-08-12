"""Database connection management.

Two engines are created:
* the discovery engine (owner/migration role) used to introspect schema;
* the execution engine (dedicated READ-ONLY role) used to run validated
  queries. The read-only engine sets default_transaction_read_only=on and a
  statement_timeout, so the database itself enforces read-only as a second
  line of defense should application validation fail.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool

from app.core import get_logger

log = get_logger(__name__)


class Database:
    def __init__(
        self,
        database_url: str,
        readonly_database_url: str | None = None,
        pool_size: int = 5,
        max_overflow: int = 2,
        statement_timeout_ms: int = 10000,
    ):
        if not database_url:
            raise ValueError("database_url is required")
        self._statement_timeout_ms = statement_timeout_ms
        self._is_sqlite = database_url.lower().startswith("sqlite")

        self.discovery_engine: Engine = self._create_engine(database_url)
        self.readonly_engine: Engine | None = None
        if readonly_database_url:
            self.readonly_engine = self._create_engine(readonly_database_url, readonly=True)

    def _create_engine(self, url: str, readonly: bool = False) -> Engine:
        is_sqlite = url.lower().startswith("sqlite")
        is_pg = "postgresql" in url.lower()

        connect_args: dict[str, Any] = {}
        pool_kwargs: dict[str, Any] = {}

        if is_sqlite:
            connect_args["check_same_thread"] = False
            pool_kwargs["poolclass"] = StaticPool
        else:
            pool_kwargs["poolclass"] = QueuePool
            pool_kwargs["pool_size"] = 5
            pool_kwargs["max_overflow"] = 2

        if is_pg and readonly:
            options = (
                f"-c default_transaction_read_only=on "
                f"-c statement_timeout={self._statement_timeout_ms}ms"
            )
            connect_args["options"] = options

        return create_engine(
            url,
            pool_pre_ping=True,
            future=True,
            connect_args=connect_args,
            **pool_kwargs,
        )

    def close(self) -> None:
        self.discovery_engine.dispose()
        if self.readonly_engine is not None:
            self.readonly_engine.dispose()

    def execute_readonly(
        self, sql: str, params: dict | None = None, row_limit: int = 1000
    ) -> tuple[list[str], list[list]]:
        """Execute a read-only query and return (columns, rows)."""
        if self.readonly_engine is None:
            raise RuntimeError("Read-only database URL is not configured")
        with self.readonly_engine.connect() as conn:
            try:
                result = conn.execute(text(sql), params or {})
            except SQLAlchemyError as exc:
                log.error(
                    "Query execution failed",
                    extra={"extra_data": {"error": str(exc)}},
                    exc_info=True,
                )
                raise
            columns = list(result.keys())
            rows: list[list] = []
            for i, row in enumerate(result):
                if i >= row_limit:
                    break
                rows.append(list(row))
            return columns, rows

    def health(self) -> bool:
        try:
            with self.discovery_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def is_readonly_configured(self) -> bool:
        return self.readonly_engine is not None
