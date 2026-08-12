"""Shared pytest fixtures.

The schema-discovery and pipeline tests run against an in-memory SQLite
database built directly from the project's real PostgreSQL schema file
(database/init/01_schema.sql), so the tests exercise the actual schema
definition. Live PostgreSQL integration tests are gated on env vars so the
unit suite stays runnable without a running database.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SCHEMA_SQL = ROOT / "database" / "init" / "01_schema.sql"


def _run_script(engine: Engine, script: str) -> None:
    """Execute a multi-statement SQL script on a SQLite engine."""
    raw = engine.raw_connection()
    try:
        raw.cursor().executescript(script)
        raw.commit()
    finally:
        raw.close()


def _seed_sqlite(engine: Engine) -> None:
    """Insert minimal deterministic test data (seed SQL uses PG-specific syntax)."""
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO customers (customer_id, first_name, last_name, email, region, country) "
            "VALUES (1, 'John', 'Doe', 'john@test.com', 'North', 'India'),"
            "(2, 'Jane', 'Smith', 'jane@test.com', 'South', 'India'),"
            "(3, 'Bob', 'Brown', 'bob@test.com', 'West', 'India'),"
            "(4, 'Alice', 'White', 'alice@test.com', 'East', 'India'),"
            "(5, 'Charlie', 'Gray', 'charlie@test.com', 'North', 'India')"
        ))
        conn.execute(text(
            "INSERT INTO products (product_id, name, category, unit_price, cost) "
            "VALUES (1, 'Widget', 'Electronics', 100.00, 50.00),"
            "(2, 'Gadget', 'Electronics', 200.00, 100.00),"
            "(3, 'Table', 'Furniture', 15000.00, 8000.00),"
            "(4, 'Chair', 'Furniture', 12000.00, 6000.00),"
            "(5, 'Rice', 'Groceries', 750.00, 500.00)"
        ))
        conn.execute(text(
            "INSERT INTO orders (order_id, customer_id, order_date, status) "
            "VALUES (1, 1, '2026-01-15', 'completed'),"
            "(2, 1, '2026-02-20', 'completed'),"
            "(3, 2, '2026-01-10', 'completed'),"
            "(4, 3, '2026-03-05', 'completed'),"
            "(5, 4, '2026-01-25', 'completed')"
        ))
        conn.execute(text(
            "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) "
            "VALUES (1, 1, 1, 2, 100.00),"
            "(2, 1, 2, 1, 200.00),"
            "(3, 2, 3, 1, 15000.00),"
            "(4, 3, 4, 3, 12000.00),"
            "(5, 4, 5, 5, 750.00),"
            "(6, 5, 1, 1, 100.00)"
        ))
        conn.commit()


@pytest.fixture
def sqlite_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    _run_script(engine, SCHEMA_SQL.read_text(encoding="utf-8"))
    return engine


@pytest.fixture
def discovery_service(sqlite_engine):
    from app.services.schema.discovery import SchemaDiscoveryService

    return SchemaDiscoveryService(sqlite_engine)


@pytest.fixture
def postgres_url_env():
    """Returns the configured PostgreSQL URL or skips the test."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("READONLY_DATABASE_URL")
    if not url:
        pytest.skip("No DATABASE_URL/READONLY_DATABASE_URL configured")
    return url


@pytest.fixture
def sqlite_db():
    """File-based SQLite Database (discovery + readonly) with schema + seed data."""
    from app.database.connection import Database

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        url = f"sqlite:///{path}"
        engine = create_engine(url, connect_args={"check_same_thread": False})
        _run_script(engine, SCHEMA_SQL.read_text(encoding="utf-8"))
        _seed_sqlite(engine)
        engine.dispose()
        db = Database(database_url=url, readonly_database_url=url)
        yield db
    finally:
        db.close()
        try:
            os.unlink(path)
        except PermissionError:
            pass


@pytest.fixture
def execution_service(sqlite_db):
    from app.services.execution import ExecutionService

    return ExecutionService(sqlite_db, row_limit=1000)


@pytest.fixture
def mock_llm_service():
    from app.services.llm import LLMService, MockProvider

    return LLMService(MockProvider())


@pytest.fixture
def api_client(sqlite_db, mock_llm_service):
    """FastAPI TestClient with test services wired after startup."""
    from fastapi.testclient import TestClient

    from app.api import configure_services
    from app.main import app

    with TestClient(app) as client:
        configure_services(database=sqlite_db, llm_service=mock_llm_service)
        yield client
