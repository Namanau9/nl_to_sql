"""Tests for the read-only intent guard (destructive / write operation detection)."""
from __future__ import annotations

import pytest

from app.core.errors import ReadonlyRestrictionError
from app.services.read_only.guard import check_question, enforce_readonly


@pytest.mark.parametrize("question", [
    "delete table customers",
    "DELETE FROM customers",
    "Can you remove all old orders?",
    "drop table users",
    "DROP TABLE customers",
    "truncate the orders table",
    "Add a new admin user",
    "insert a new product",
    "Update the price of laptops",
    "Alter table customers",
    "Grant admin privileges",
    "Create a new table called archive",
    "modify the customer record with id 5",
    "change the revenue for product 3",
])
def test_destructive_questions_detected(question):
    result = check_question(question)
    assert result.is_violation is True
    assert result.detected_action is not None
    assert len(result.message) > 20


@pytest.mark.parametrize("question", [
    "How many customers do we have?",
    "What was our total revenue?",
    "Which product sold the most?",
    "Show me monthly revenue for 2026.",
    "Select all from customers",
    "Top 5 products by revenue",
])
def test_safe_questions_pass(question):
    result = check_question(question)
    assert result.is_violation is False
    assert result.detected_action is None


def test_empty_question_returns_no_violation():
    result = check_question("")
    assert result.is_violation is False
    assert result.detected_action is None


def test_whitespace_only_question():
    result = check_question("   ")
    assert result.is_violation is False


def test_enforce_readonly_raises():
    with pytest.raises(ReadonlyRestrictionError) as exc_info:
        enforce_readonly("delete table customers")
    assert "read-only" in str(exc_info.value.user_message).lower()


def test_enforce_readonly_passes_safe():
    enforce_readonly("How many customers do we have?")
    # No exception raised


def test_enforce_readonly_error_has_status_code():
    with pytest.raises(ReadonlyRestrictionError) as exc_info:
        enforce_readonly("DROP TABLE customers")
    assert exc_info.value.status_code == 422


def test_message_is_user_friendly():
    result = check_question("delete table customers")
    assert "SELECT" in result.message
    assert "read-only" in result.message.lower()
    assert "try asking" in result.message.lower()


def test_different_actions_have_different_messages():
    delete_result = check_question("delete all rows")
    insert_result = check_question("insert a new row")
    assert delete_result.detected_action == "delete"
    assert insert_result.detected_action == "insert"
    assert delete_result.message != insert_result.message
