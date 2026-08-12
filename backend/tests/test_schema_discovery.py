"""Tests for dynamic schema discovery against the project schema file."""
from __future__ import annotations


def test_discovers_all_business_tables(discovery_service):
    schema = discovery_service.discover()
    assert set(schema.table_names) == {
        "customers", "products", "orders", "order_items"
    }


def test_customer_columns_discovered(discovery_service):
    schema = discovery_service.discover()
    customers = schema.find_table("customers")
    assert customers is not None
    col_names = customers.column_names
    for expected in ("customer_id", "first_name", "last_name", "email",
                     "region", "country", "created_at"):
        assert expected in col_names


def test_primary_keys_discovered(discovery_service):
    schema = discovery_service.discover()
    pk_by_table = {t.name: t.primary_key for t in schema.tables}
    assert pk_by_table["customers"] == ["customer_id"]
    assert pk_by_table["products"] == ["product_id"]
    assert pk_by_table["orders"] == ["order_id"]
    assert pk_by_table["order_items"] == ["order_item_id"]


def test_primary_key_flags_on_columns(discovery_service):
    schema = discovery_service.discover()
    customers = schema.find_table("customers")
    cid = next(c for c in customers.columns if c.name == "customer_id")
    assert cid.is_primary_key is True


def test_foreign_keys_discovered(discovery_service):
    schema = discovery_service.discover()
    fk_pairs = {
        (fk.table_name, tuple(fk.columns), fk.referenced_table, tuple(fk.referenced_columns))
        for fk in schema.foreign_keys
    }
    assert ("orders", ("customer_id",), "customers", ("customer_id",)) in fk_pairs
    assert ("order_items", ("order_id",), "orders", ("order_id",)) in fk_pairs
    assert ("order_items", ("product_id",), "products", ("product_id",)) in fk_pairs


def test_to_llm_context_includes_tables_and_relationships(discovery_service):
    schema = discovery_service.discover()
    context = schema.to_llm_context()
    assert "TABLES" in context
    assert "customers" in context
    assert "order_items" in context
    assert "RELATIONSHIPS" in context
    assert "->" in context


def test_find_table_missing_returns_none(discovery_service):
    schema = discovery_service.discover()
    assert schema.find_table("nonexistent") is None


def test_table_exists(discovery_service):
    assert discovery_service.table_exists("customers") is True
    assert discovery_service.table_exists("nope") is False


def test_discovery_does_not_require_hardcoded_answers(discovery_service, sqlite_engine):
    """If a table is removed from the schema, discovery must not report it."""
    from sqlalchemy import text
    with sqlite_engine.connect() as conn:
        conn.execute(text("DROP TABLE order_items"))
        conn.commit()
    schema = discovery_service.discover()
    assert "order_items" not in schema.table_names
    assert "customers" in schema.table_names
