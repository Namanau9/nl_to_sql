"""Comprehensive security test suite (F-018, F-019, F-020, F-023).

Negative security tests that verify the SQL validator rejects all destructive
operations, multi-statement injection, and unauthorized schema access.
"""
from __future__ import annotations

import pytest

from app.core.errors import ReadonlyRestrictionError, SQLValidationError
from app.services.sql import SQLValidator

ALLOWED = {"customers", "orders", "order_items", "products"}


def _validator() -> SQLValidator:
    return SQLValidator(allowed_tables=ALLOWED)


# --- Destructive operations (F-018) — now raise ReadonlyRestrictionError ---

@pytest.mark.parametrize("sql", [
    "DELETE FROM customers",
    "DELETE FROM customers WHERE region = 'North'",
    "DELETE FROM orders WHERE order_date < '2025-01-01'",
])
def test_delete_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "INSERT INTO customers (first_name) VALUES ('Hacker')",
    "INSERT INTO customers VALUES (99, 'evil', 'evil', 'x@x.com', 'X', 'X', now())",
])
def test_insert_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "UPDATE customers SET region = 'North'",
    "UPDATE customers SET email = 'hacked@evil.com' WHERE customer_id = 1",
])
def test_update_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "DROP TABLE customers",
    "DROP TABLE orders CASCADE",
    "DROP TABLE products",
])
def test_drop_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "ALTER TABLE customers ADD COLUMN secret TEXT",
    "ALTER TABLE customers RENAME TO users",
    "ALTER TABLE orders ADD CONSTRAINT fk FOREIGN KEY (customer_id) REFERENCES customers",
])
def test_alter_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "TRUNCATE customers",
    "TRUNCATE orders, products",
    "TRUNCATE customers RESTART IDENTITY CASCADE",
])
def test_truncate_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


@pytest.mark.parametrize("sql", [
    "CREATE TABLE backdoor (id INT)",
    "CREATE TABLE secret_data AS SELECT * FROM customers",
    "CREATE INDEX idx_secret ON customers(customer_id)",
])
def test_create_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(sql)


def test_grant_rejected():
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate("GRANT ALL ON customers TO PUBLIC")


def test_revoke_rejected():
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate("REVOKE ALL ON customers FROM nlsql_readonly")


# --- Multi-statement injection (F-018) ---

@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers; DROP TABLE customers",
    "SELECT COUNT(*) FROM orders; DELETE FROM customers; INSERT INTO backdoor VALUES(1)",
    "SELECT 1; SELECT 2; SELECT 3",
    "SELECT * FROM customers -- comment\n; DROP TABLE products",
])
def test_multi_statement_rejected(sql):
    with pytest.raises(SQLValidationError, match="Multiple SQL statements"):
        _validator().validate(sql)


# --- Unauthorized schema access (F-005) ---

@pytest.mark.parametrize("sql", [
    "SELECT * FROM pg_shadow",
    "SELECT * FROM pg_user",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM sqlite_master",
])
def test_unauthorized_system_table_rejected(sql):
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        _validator().validate(sql)


def test_validates_referenced_tables():
    """Only tables in the allowed list may be referenced."""
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        _validator().validate("SELECT * FROM customers, pg_shadow")


# --- Valid queries still pass (positive security case) ---

@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM customers",
    "SELECT c.region, COUNT(o.order_id) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.region",
    "SELECT c.first_name, c.last_name, SUM(oi.quantity * oi.unit_price) AS total FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_items oi ON o.order_id = oi.order_id GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY total DESC LIMIT 10",
    "WITH monthly AS (SELECT DATE_TRUNC('month', order_date) AS m, SUM(quantity * unit_price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id GROUP BY m) SELECT m, revenue FROM monthly ORDER BY m",
    "SELECT p.name, p.category FROM products p WHERE p.category = 'Electronics' ORDER BY p.name",
    "SELECT customer_id, first_name, last_name FROM customers WHERE region = 'North' ORDER BY last_name",
])
def test_valid_select_queries_pass(sql):
    result = _validator().validate(sql)
    assert result.is_valid is True
    assert result.error is None


# --- Edge cases ---

def test_empty_sql_rejected():
    with pytest.raises(SQLValidationError, match="Empty SQL"):
        _validator().validate("")


def test_whitespace_only_sql_rejected():
    with pytest.raises(SQLValidationError, match="Empty SQL"):
        _validator().validate("   \n\t  ")


def test_syntax_error_rejected():
    with pytest.raises(SQLValidationError):
        _validator().validate("SELEC * FROMM customers")


def test_select_into_rejected():
    with pytest.raises(SQLValidationError, match="INTO"):
        _validator().validate("SELECT * INTO customer_backup FROM customers")


def test_command_fallback_rejected():
    """SQLglot falls back to Command type for unsupported statements."""
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate("VACUUM customers")


def test_error_messages_never_contain_sql():
    """Security: error messages must not echo the raw SQL back."""
    sql = "DELETE FROM customers WHERE email LIKE '%evil%'"
    try:
        _validator().validate(sql)
        assert False, "Should have raised"
    except (ReadonlyRestrictionError, SQLValidationError) as exc:
        msg = str(exc)
        assert "DELETE" not in msg
        assert "email" not in msg
        assert "evil" not in msg


def test_error_messages_never_contain_table_values():
    """Security: error messages must not leak sensitive column/table names."""
    sql = "SELECT * FROM pg_shadow"
    try:
        _validator().validate(sql)
        assert False, "Should have raised"
    except SQLValidationError as exc:
        msg = str(exc)
        assert "pg_shadow" not in msg


def test_destructive_sql_reaches_validator():
    """Destructive SQL must reach the SQL validator, not be pre-rejected by _extract_sql."""
    from app.services.llm.service import _extract_sql

    destructive = "DROP TABLE customers"
    extracted = _extract_sql(destructive)
    assert extracted == destructive
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        _validator().validate(extracted)


def test_non_sql_response_reaches_validator():
    """Refusal text should reach the validator and be rejected as unparseable."""
    from app.services.llm.service import _extract_sql

    extracted = _extract_sql("I'm sorry, I can't help with that.")
    with pytest.raises(SQLValidationError, match="could not be parsed"):
        _validator().validate(extracted)
