"""Tests for AST-based SQL validation (F-005, F-006, security cases)."""
from __future__ import annotations

import pytest

from app.core.errors import ReadonlyRestrictionError, SQLValidationError
from app.services.sql import SQLValidator, validate_sql

ALLOWED = {"customers", "orders", "order_items", "products"}


def test_valid_select_passes():
    sql = "SELECT c.customer_id, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id ORDER BY order_count DESC"
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True
    assert result.statement_count == 1
    assert "customers" in result.referenced_tables
    assert "orders" in result.referenced_tables
    assert result.error is None


def test_with_cte_passes():
    sql = "WITH monthly AS (SELECT DATE_TRUNC('month', order_date) AS month, SUM(oi.quantity * oi.unit_price) AS revenue FROM order_items oi JOIN orders o ON oi.order_id = o.order_id GROUP BY month) SELECT month, revenue FROM monthly ORDER BY month"
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True


def test_union_passes():
    sql = "SELECT customer_id FROM customers WHERE region = 'North' UNION SELECT customer_id FROM customers WHERE region = 'South'"
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True
    assert result.referenced_tables == ["customers"]


def test_subquery_passes():
    sql = "SELECT * FROM customers WHERE customer_id IN (SELECT customer_id FROM orders)"
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True


# --- Destructive operations -> ReadonlyRestrictionError (user-friendly) ---

@pytest.mark.parametrize("sql", [
    "DELETE FROM customers",
    "DELETE FROM customers WHERE region = 'North'",
])
def test_delete_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "INSERT INTO customers (first_name) VALUES ('Test')",
    "INSERT INTO customers VALUES (99, 'evil', 'x@x.com')",
])
def test_insert_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "UPDATE customers SET region = 'North'",
    "UPDATE customers SET email = 'hacked@evil.com' WHERE customer_id = 1",
])
def test_update_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "DROP TABLE customers",
    "DROP TABLE orders CASCADE",
    "DROP TABLE products",
])
def test_drop_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "ALTER TABLE customers ADD COLUMN foo TEXT",
    "ALTER TABLE customers RENAME TO users",
])
def test_alter_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "TRUNCATE customers",
    "TRUNCATE orders, products",
])
def test_truncate_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


@pytest.mark.parametrize("sql", [
    "CREATE TABLE foo (id INT)",
    "CREATE TABLE secret_data AS SELECT * FROM customers",
    "CREATE INDEX idx_secret ON customers(customer_id)",
])
def test_create_rejected(sql):
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql(sql, allowed_tables=ALLOWED)


def test_grant_rejected():
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql("GRANT ALL ON customers TO public", allowed_tables=ALLOWED)


def test_revoke_rejected():
    with pytest.raises(ReadonlyRestrictionError, match="read-only"):
        validate_sql("REVOKE SELECT ON customers FROM nlsql_readonly", allowed_tables=ALLOWED)


# --- Non-destructive validation errors -> SQLValidationError ---

def test_empty_sql_rejected():
    with pytest.raises(SQLValidationError, match="Empty SQL"):
        validate_sql("", allowed_tables=ALLOWED)


def test_whitespace_only_sql_rejected():
    with pytest.raises(SQLValidationError, match="Empty SQL"):
        validate_sql("   \n  ", allowed_tables=ALLOWED)


def test_parse_error_rejected():
    with pytest.raises(SQLValidationError, match="could not be parsed"):
        validate_sql("SELEC * FROM customers", allowed_tables=ALLOWED)


def test_multiple_statements_rejected():
    with pytest.raises(SQLValidationError, match="Multiple SQL statements"):
        validate_sql("SELECT 1; DROP TABLE customers", allowed_tables=ALLOWED)


def test_unauthorized_table_rejected():
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validate_sql("SELECT * FROM pg_shadow", allowed_tables=ALLOWED)


def test_unauthorized_table_with_select_rejected():
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validate_sql("SELECT * FROM customers, pg_shadow", allowed_tables=ALLOWED)


def test_select_into_rejected():
    with pytest.raises(SQLValidationError, match="INTO"):
        validate_sql("SELECT * INTO customers_backup FROM customers", allowed_tables=ALLOWED)


# --- Positive cases ---

def test_cte_not_flagged_as_table():
    """CTE aliases should not trip the unauthorized-table check."""
    sql = "WITH cte AS (SELECT customer_id FROM customers) SELECT * FROM cte"
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True
    assert result.referenced_tables == ["customers"]


def test_validator_class_wrapper():
    validator = SQLValidator(allowed_tables={"customers"})
    assert "customers" in validator.allowed_tables
    result = validator.validate("SELECT customer_id FROM customers")
    assert result.is_valid is True


def test_validator_class_rejects_unauthorized():
    validator = SQLValidator(allowed_tables={"customers"})
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validator.validate("SELECT * FROM orders")


def test_subquery_table_not_flagged_as_cte():
    sql = (
        "SELECT * FROM customers c "
        "WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)"
    )
    result = validate_sql(sql, allowed_tables=ALLOWED)
    assert result.is_valid is True
    assert set(result.referenced_tables) == {"customers", "orders"}


# --- Error message safety ---

def test_destructive_error_messages_never_contain_sql():
    """Security: destructive error messages must not echo the raw SQL back."""
    sql = "DELETE FROM customers WHERE email LIKE '%evil%'"
    try:
        validate_sql(sql, allowed_tables=ALLOWED)
        assert False, "Should have raised"
    except ReadonlyRestrictionError as exc:
        msg = str(exc)
        assert "DELETE" not in msg
        assert "email" not in msg
        assert "evil" not in msg
