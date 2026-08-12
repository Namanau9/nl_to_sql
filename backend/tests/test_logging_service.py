"""Tests for the query logging service."""
from __future__ import annotations

from app.services.logging import QueryLogger


def test_create_entry_assigns_trace_id():
    logger = QueryLogger()
    entry = logger.create_entry("How many customers?")
    assert entry.trace_id
    assert entry.question == "How many customers?"
    assert entry.validation_status == "pending"
    assert entry.execution_status == "pending"


def test_set_sql():
    logger = QueryLogger()
    entry = logger.create_entry("test")
    logger.set_sql(entry, "SELECT 1")
    assert entry.sql == "SELECT 1"


def test_set_validation():
    logger = QueryLogger()
    entry = logger.create_entry("test")
    logger.set_validation(entry, "passed")
    assert entry.validation_status == "passed"
    logger.set_validation(entry, "failed", error="bad SQL")
    assert entry.validation_status == "failed"
    assert entry.validation_error == "bad SQL"


def test_set_execution():
    logger = QueryLogger()
    entry = logger.create_entry("test")
    logger.set_execution(entry, "success", row_count=5, execution_ms=12.3)
    assert entry.execution_status == "success"
    assert entry.row_count == 5
    assert entry.execution_ms == 12.3


def test_set_explanation():
    logger = QueryLogger()
    entry = logger.create_entry("test")
    logger.set_explanation(entry, "There are 15 customers.")
    assert entry.explanation == "There are 15 customers."


def test_set_error():
    logger = QueryLogger()
    entry = logger.create_entry("test")
    logger.set_error(entry, "Something broke")
    assert entry.error == "Something broke"


def test_to_dict_round_trip():
    logger = QueryLogger()
    entry = logger.create_entry("How many customers?")
    logger.set_sql(entry, "SELECT COUNT(*) FROM customers")
    logger.set_validation(entry, "passed")
    logger.set_execution(entry, "success", row_count=1, execution_ms=5.0)
    logger.set_explanation(entry, "15 customers.")
    d = entry.to_dict()
    assert d["question"] == "How many customers?"
    assert d["sql"] == "SELECT COUNT(*) FROM customers"
    assert d["validation_status"] == "passed"
    assert d["execution_status"] == "success"
    assert d["row_count"] == 1
    assert d["explanation"] == "15 customers."