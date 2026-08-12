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
from pathlib import Path

import pytest
from sqlalchemy import create_engine
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
