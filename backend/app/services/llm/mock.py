"""Mock LLM provider for tests and demos.

Returns deterministic, canned responses for known question patterns.
Handles both SQL generation and result explanation requests.  When a
question does not match any known pattern the provider raises
:class:`~app.core.errors.LLMError` so that callers can exercise their error
path.
"""
from __future__ import annotations

import re

from app.core.errors import LLMError
from app.services.llm.base import BaseLLMProvider
from app.services.llm.models import LLMResponse

_MOCK_RESPONSES: dict[str, str] = {
    "how many customers do we have": "SELECT COUNT(*) AS customer_count FROM customers",
    "what was our revenue last month": (
        "SELECT DATE_TRUNC('month', o.order_date) AS month, "
        "SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM orders o JOIN order_items oi ON o.order_id = oi.order_id "
        "WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') "
        "  AND o.order_date < DATE_TRUNC('month', CURRENT_DATE) "
        "GROUP BY month ORDER BY month"
    ),
    "which product sold the most": (
        "SELECT p.name, SUM(oi.quantity * oi.unit_price) AS total_revenue "
        "FROM order_items oi JOIN products p ON oi.product_id = p.product_id "
        "GROUP BY p.name ORDER BY total_revenue DESC LIMIT 1"
    ),
    "show revenue by region": (
        "SELECT c.region, SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM customers c JOIN orders o ON c.customer_id = o.customer_id "
        "JOIN order_items oi ON o.order_id = oi.order_id "
        "GROUP BY c.region ORDER BY revenue DESC"
    ),
    "which category generated the most revenue": (
        "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM order_items oi JOIN products p ON oi.product_id = p.product_id "
        "GROUP BY p.category ORDER BY revenue DESC LIMIT 1"
    ),
    "who are our top 10 customers": (
        "SELECT c.first_name, c.last_name, SUM(oi.quantity * oi.unit_price) AS total_spent "
        "FROM customers c JOIN orders o ON c.customer_id = o.customer_id "
        "JOIN order_items oi ON o.order_id = oi.order_id "
        "GROUP BY c.customer_id, c.first_name, c.last_name "
        "ORDER BY total_spent DESC LIMIT 10"
    ),
    "show monthly revenue for 2026": (
        "SELECT DATE_TRUNC('month', o.order_date) AS month, "
        "SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM orders o JOIN order_items oi ON o.order_id = oi.order_id "
        "WHERE o.order_date >= DATE '2026-01-01' AND o.order_date < DATE '2027-01-01' "
        "GROUP BY month ORDER BY month"
    ),
    "show monthly revenue for 2025": (
        "SELECT DATE_TRUNC('month', o.order_date) AS month, "
        "SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM orders o JOIN order_items oi ON o.order_id = oi.order_id "
        "WHERE o.order_date >= DATE '2025-01-01' AND o.order_date < DATE '2026-01-01' "
        "GROUP BY month ORDER BY month"
    ),
}

_MOCK_EXPLANATIONS: dict[str, str] = {
    "how many customers do we have": "The database contains 5 customers.",
    "which product sold the most": "The top-selling product by revenue appears in the results table.",
    "show revenue by region": "Revenue breakdown by region is shown in the results above.",
}

_DEFAULT_RESPONSE = (
    "I'm not configured to answer that question. "
    "Try asking about customers, revenue, products, or orders."
)

_EXPLANATION_MARKER = re.compile(r"^Question:\s*(.+?)\s*$", re.MULTILINE)


class MockProvider(BaseLLMProvider):
    """Deterministic provider that matches questions to canned SQL or explanations."""

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout_seconds: int = 30,
    ) -> LLMResponse:
        question = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                question = msg.get("content", "")
                break

        is_explanation = question.strip().startswith("Question:")
        if is_explanation:
            match = _EXPLANATION_MARKER.search(question)
            actual_q = match.group(1) if match else ""
            key = actual_q.lower().strip().rstrip("?")
            explanation = _MOCK_EXPLANATIONS.get(key)
            if explanation:
                return LLMResponse(content=explanation, model="mock")
            return LLMResponse(
                content="Based on the query results shown above, the answer is reflected in the returned data.",
                model="mock",
            )

        key = question.lower().strip().rstrip("?")
        sql = _MOCK_RESPONSES.get(key)
        if sql is None:
            raise LLMError(
                message="No mock response for the given question.",
                detail=f"question={question!r}",
            )
        return LLMResponse(content=sql, model="mock")