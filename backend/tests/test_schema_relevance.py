"""Tests for relevant-schema selection against the example question set."""
from __future__ import annotations

from app.services.schema.discovery import DatabaseSchema, ForeignKeyInfo, TableInfo, ColumnInfo
from app.services.schema.relevance import RelevanceSelector


def _col(name: str, data_type: str = "text") -> ColumnInfo:
    return ColumnInfo(name=name, data_type=data_type, is_nullable=False)


def _make_schema() -> DatabaseSchema:
    tables = [
        TableInfo(name="customers", primary_key=["customer_id"],
                  columns=[_col("customer_id"), _col("region"), _col("country")]),
        TableInfo(name="orders", primary_key=["order_id"],
                  columns=[_col("order_id"), _col("customer_id"), _col("order_date")]),
                TableInfo(name="order_items", primary_key=["order_item_id"],
                  columns=[_col("order_item_id"), _col("order_id"), _col("product_id"),
                           _col("quantity"), _col("unit_price")]),
        TableInfo(name="products", primary_key=["product_id"],
                  columns=[_col("product_id"), _col("category"), _col("unit_price")]),
    ]
    fks = [
        ForeignKeyInfo(name="fk_orders_customer", table_schema="public",
                       table_name="orders", columns=["customer_id"],
                       referenced_schema="public", referenced_table="customers",
                       referenced_columns=["customer_id"]),
        ForeignKeyInfo(name="fk_oi_order", table_schema="public",
                       table_name="order_items", columns=["order_id"],
                       referenced_schema="public", referenced_table="orders",
                       referenced_columns=["order_id"]),
        ForeignKeyInfo(name="fk_oi_product", table_schema="public",
                       table_name="order_items", columns=["product_id"],
                       referenced_schema="public", referenced_table="products",
                       referenced_columns=["product_id"]),
    ]
    return DatabaseSchema(tables=tables, foreign_keys=fks)


CASES = [
    ("How many customers do we have?", {"customers"}),
    ("What was our revenue last month?", {"orders", "order_items"}),
    ("Which product sold the most?", {"products", "order_items"}),
    ("Show revenue by region.", {"customers", "orders", "order_items"}),
    ("Which category generated the most revenue?", {"products", "order_items"}),
    ("Who are our top 10 customers?", {"customers", "order_items", "orders"}),
    ("Show monthly revenue for 2026.", {"orders", "order_items"}),
]


def test_relevance_selector_returns_subschema(discovery_service):
    schema = discovery_service.discover()
    selector = RelevanceSelector(schema)
    sub = selector.select("Which product generated the highest revenue?")
    assert isinstance(sub, DatabaseSchema)
    assert "products" in sub.table_names
    assert "order_items" in sub.table_names


def test_relevance_includes_join_bridge_table():
    """customers + revenue => orders (bridge) and order_items (fact) included."""
    schema = _make_schema()
    selector = RelevanceSelector(schema)
    sub = selector.select("Show revenue by region.")
    assert set(sub.table_names) == {"customers", "orders", "order_items"}


def test_relevance_excludes_unrelated_tables(discovery_service):
    schema = discovery_service.discover()
    selector = RelevanceSelector(schema)
    sub = selector.select("How many customers do we have?")
    assert "order_items" not in sub.table_names


def test_relevance_empty_question_returns_full_schema(discovery_service):
    schema = discovery_service.discover()
    selector = RelevanceSelector(schema)
    sub = selector.select("xyzzy frobnicate")
    assert len(sub.table_names) == 4


def test_relevance_example_questions(discovery_service):
    schema = discovery_service.discover()
    selector = RelevanceSelector(schema)
    for question, expected in CASES:
        sub = selector.select(question)
        assert expected.issubset(set(sub.table_names)), (
            f"{question!r} expected {expected} subset of {sub.table_names}"
        )


def test_relevance_subschema_keeps_relationships(discovery_service):
    schema = discovery_service.discover()
    selector = RelevanceSelector(schema)
    sub = selector.select("What was our revenue last month?")
    assert len(sub.foreign_keys) >= 1

