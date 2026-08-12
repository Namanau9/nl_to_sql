"""Tests for the database foundation (schema, seed, read-only role).

These validate the SQL definition files. A live-DB integration test is gated on
environment configuration to keep the unit-test suite runnable off-DB.
"""

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "database" / "init" / "01_schema.sql"
SEED = ROOT / "database" / "seed" / "02_seed.sql"
ROLE = ROOT / "database" / "init" / "03_readonly_role.sql"

REQUIRED_TABLES = {"customers", "products", "orders", "order_items"}


def test_schema_file_exists():
    assert SCHEMA.exists()
    assert "CREATE TABLE IF NOT EXISTS customers" in SCHEMA.read_text()
    assert "CREATE TABLE IF NOT EXISTS products" in SCHEMA.read_text()
    assert "CREATE TABLE IF NOT EXISTS orders" in SCHEMA.read_text()
    assert "CREATE TABLE IF NOT EXISTS order_items" in SCHEMA.read_text()


def test_schema_defines_primary_and_foreign_keys():
    sql = SCHEMA.read_text()
    # Primary keys
    assert "SERIAL PRIMARY KEY" in sql
    assert "REFERENCES customers(customer_id)" in sql
    assert "REFERENCES orders(order_id)" in sql
    assert "REFERENCES products(product_id)" in sql
    # Analytical index support
    assert "idx_orders_order_date" in sql
    assert "idx_order_items_product" in sql


def test_seed_generates_deterministic_data():
    seed = SEED.read_text()
    assert "INSERT INTO customers" in seed
    assert "INSERT INTO products" in seed
    assert "INSERT INTO orders" in seed
    assert "INSERT INTO order_items" in seed
    assert "random(" not in seed  # reproducibility
    # Covers 2025 and 2026 for monthly-revenue questions
    assert "2025" in seed and "2026" in seed


def test_readonly_role_grants_select_only():
    role = ROLE.read_text()
    assert "CREATE ROLE nlsql_readonly" in role
    assert "GRANT SELECT ON ALL TABLES" in role
    assert "LOGIN PASSWORD" in role
    # no write privileges granted
    for kw in ("GRANT INSERT", "GRANT UPDATE", "GRANT DELETE", "GRANT DROP"):
        assert kw not in role


def _run_readonly_delete_is_blocked(database_url: str):
    """Integration assertion used when a live DB is configured."""
    engine = create_engine(database_url)
    from sqlalchemy.exc import ProgrammingError

    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM customers"))
            conn.commit()
    except ProgrammingError:
        return True  # read-only role rejected the write
    finally:
        engine.dispose()
    raise AssertionError("DELETE should have been rejected by the read-only role")


def test_database_is_reachable_and_readonly(monkeypatch):
    url = __import__("os").environ.get("READONLY_DATABASE_URL")
    if not url:
        import pytest

        pytest.skip("READONLY_DATABASE_URL not set; skipping live-DB integration test")
    assert _run_readonly_delete_is_blocked(url) is True


def test_column_inventory_covered():
    """All tables/columns referenced by spec docs exist in the schema."""
    sql = SCHEMA.read_text().lower()
    required_cols = [
        "customer_id", "first_name", "last_name", "email", "region", "country",
        "product_id", "name", "category", "unit_price", "cost",
        "order_id", "customer_id", "order_date", "status", "quantity",
    ]
    for col in required_cols:
        assert col in sql

