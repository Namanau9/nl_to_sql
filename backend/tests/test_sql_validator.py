"""Tests for AST-based SQL validation (F-005, F-006, security cases)."""
from __future__ import annotations

import pytest

from app.core.errors import SQLValidationError
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


def test_empty_sql_rejected():
    with pytest.raises(SQLValidationError, match="Empty SQL query"):
        validate_sql("", allowed_tables=ALLOWED)
    with pytest.raises(SQLValidationError, match="Empty SQL query"):
        validate_sql("   \n  ", allowed_tables=ALLOWED)


def test_parse_error_rejected():
    with pytest.raises(SQLValidationError, match="could not be parsed"):
        validate_sql("SELEC * FROM customers", allowed_tables=ALLOWED)


def test_multiple_statements_rejected():
    sql = "SELECT 1; DROP TABLE customers"
    with pytest.raises(SQLValidationError, match="Multiple SQL statements"):
        validate_sql(sql, allowed_tables=ALLOWED)


def test_delete_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("DELETE FROM customers", allowed_tables=ALLOWED)


def test_insert_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("INSERT INTO customers (first_name) VALUES ('Test')", allowed_tables=ALLOWED)


def test_update_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("UPDATE customers SET region = 'North'", allowed_tables=ALLOWED)


def test_drop_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("DROP TABLE customers", allowed_tables=ALLOWED)


def test_alter_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("ALTER TABLE customers ADD COLUMN foo TEXT", allowed_tables=ALLOWED)


def test_truncate_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("TRUNCATE customers", allowed_tables=ALLOWED)


def test_create_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("CREATE TABLE foo (id INT)", allowed_tables=ALLOWED)


def test_grant_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("GRANT ALL ON customers TO public", allowed_tables=ALLOWED)


def test_revoke_rejected():
    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql("REVOKE SELECT ON customers FROM nlsql_readonly", allowed_tables=ALLOWED)


def test_unauthorized_table_rejected():
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validate_sql("SELECT * FROM pg_shadow", allowed_tables=ALLOWED)


def test_unauthorized_table_in_select_rejected():
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validate_sql("SELECT * FROM pg_shadow", allowed_tables=ALLOWED)


def test_allowed_tables_enforced():
    sql = "SELECT * FROM customers"
    with pytest.raises(SQLValidationError, match="unauthorized table"):
        validate_sql(sql, allowed_tables=set())


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


def test_select_into_rejected():
    with pytest.raises(SQLValidationError, match="INTO"):
        validate_sql("SELECT * INTO customers_backup FROM customers", allowed_tables=ALLOWED)
