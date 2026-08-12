"""Tests for the LLM service abstraction (F-004)."""
from __future__ import annotations

import pytest

from app.core.errors import LLMError
from app.services.llm import MockProvider, create_provider
from app.services.llm.models import LLMResponse, LLMUsage
from app.services.llm.service import LLMService, _extract_sql
from app.services.schema.discovery import ColumnInfo, DatabaseSchema, TableInfo


def _make_schema() -> DatabaseSchema:
    return DatabaseSchema(tables=[
        TableInfo(
            name="customers",
            primary_key=["customer_id"],
            columns=[
                ColumnInfo(name="customer_id", data_type="integer", is_primary_key=True),
                ColumnInfo(name="region", data_type="text"),
                ColumnInfo(name="country", data_type="text"),
            ],
        ),
        TableInfo(
            name="orders",
            primary_key=["order_id"],
            columns=[
                ColumnInfo(name="order_id", data_type="integer", is_primary_key=True),
                ColumnInfo(name="customer_id", data_type="integer"),
                ColumnInfo(name="order_date", data_type="date"),
            ],
        ),
    ])


def test_extract_sql_strips_markdown_fences():
    raw = "```sql\nSELECT * FROM customers\n```"
    assert _extract_sql(raw) == "SELECT * FROM customers"


def test_extract_sql_strips_plain_backticks():
    raw = "`SELECT 1`"
    assert _extract_sql(raw) == "SELECT 1"


def test_extract_sql_handles_raw_response():
    raw = "SELECT customer_id FROM customers"
    assert _extract_sql(raw) == "SELECT customer_id FROM customers"


def test_extract_sql_empty_raises():
    with pytest.raises(LLMError, match="did not contain SQL"):
        _extract_sql("No SQL here")


def test_extract_sql_strips_explain_prefix():
    raw = "EXPLAIN\nSELECT 1"
    assert _extract_sql(raw) == "SELECT 1"


def test_mock_provider_returns_canned_sql():
    provider = MockProvider()
    response = provider.complete(
        messages=[{"role": "system", "content": "..."}, {"role": "user", "content": "How many customers do we have?"}]
    )
    assert "COUNT" in response.content
    assert "customers" in response.content


def test_mock_provider_raises_on_unknown_question():
    provider = MockProvider()
    with pytest.raises(LLMError, match="No mock response"):
        provider.complete(messages=[{"role": "user", "content": "What is the meaning of life?"}])


def test_create_provider_mock():
    provider = create_provider("mock")
    assert isinstance(provider, MockProvider)


def test_create_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_provider("nonexistent")


def test_create_provider_openrouter_requires_key():
    with pytest.raises(ValueError, match="api_key is required"):
        create_provider("openai", api_key=None)


def test_create_provider_openrouter_with_key():
    provider = create_provider("openai", api_key="test-key", model="gpt-4o-mini")
    assert provider is not None


def test_llm_service_generates_sql():
    provider = MockProvider()
    service = LLMService(provider)
    schema = _make_schema()
    sql = service.generate_sql("How many customers do we have?", schema)
    assert sql.startswith("SELECT")
    assert "customers" in sql.lower()


def test_llm_service_rejects_empty_question():
    service = LLMService(MockProvider())
    schema = _make_schema()
    with pytest.raises(LLMError, match="Empty question"):
        service.generate_sql("", schema)


def test_llm_service_wraps_provider_error():
    class FailingProvider(MockProvider):
        def complete(self, *args, **kwargs):
            raise RuntimeError("boom")

    service = LLMService(FailingProvider())
    schema = _make_schema()
    with pytest.raises(LLMError, match="Unexpected provider error"):
        service.generate_sql("How many customers do we have?", schema)


def test_openrouter_provider_headers_dont_leak_key():
    provider = create_provider("openai", api_key="secret123", model="gpt-4o-mini")
    headers = provider._headers()
    assert "Bearer secret123" in headers["Authorization"]
    assert provider._api_key == "secret123"