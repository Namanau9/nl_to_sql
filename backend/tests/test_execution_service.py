"""Tests for the execution service (F-006, read-only execution)."""
from __future__ import annotations

import pytest

from app.core.errors import ExecutionError
from app.services.execution import ExecutionService, QueryResult


def test_execute_simple_select(sqlite_db):
    svc = ExecutionService(sqlite_db)
    result = svc.execute("SELECT COUNT(*) AS cnt FROM customers")
    assert result.status == "success"
    assert result.error is None
    assert result.row_count == 1
    assert result.columns == ["cnt"]


def test_execute_returns_rows(sqlite_db):
    svc = ExecutionService(sqlite_db)
    result = svc.execute("SELECT customer_id, region FROM customers LIMIT 3")
    assert result.row_count == 3
    assert result.columns == ["customer_id", "region"]
    assert all(len(row) == 2 for row in result.rows)


def test_execute_join_query(sqlite_db):
    svc = ExecutionService(sqlite_db)
    sql = (
        "SELECT c.region, COUNT(o.order_id) AS order_count "
        "FROM customers c JOIN orders o ON c.customer_id = o.customer_id "
        "GROUP BY c.region ORDER BY order_count DESC"
    )
    result = svc.execute(sql)
    assert result.status == "success"
    assert result.row_count >= 1


def test_execute_invalid_sql_returns_error(sqlite_db):
    svc = ExecutionService(sqlite_db)
    result = svc.execute("SELECT * FROM nonexistent_table")
    assert result.status == "error"
    assert result.error is not None


def test_execute_respects_row_limit(sqlite_db):
    svc = ExecutionService(sqlite_db, row_limit=5)
    result = svc.execute("SELECT customer_id FROM customers", row_limit=5)
    assert result.row_count == 5


def test_execute_without_readonly_config_raises():
    from app.database.connection import Database

    db = Database(database_url="sqlite:///:memory:")
    svc = ExecutionService(db)
    with pytest.raises(ExecutionError, match="Read-only"):
        svc.execute("SELECT 1")


def test_query_result_to_dict(sqlite_db):
    svc = ExecutionService(sqlite_db)
    result = svc.execute("SELECT COUNT(*) AS cnt FROM customers")
    d = result.to_dict()
    assert "columns" in d
    assert "rows" in d
    assert "row_count" in d
    assert "execution_ms" in d
    assert "status" in d
    assert "error" in d