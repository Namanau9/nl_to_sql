"""Pre-flight detection of destructive intent in user questions.

Before sending a question to the LLM, this guard checks whether the user is
asking for write, delete, or schema-modification operations.  If so it raises
:class:`ReadonlyRestrictionError` with a **user-friendly, helpful message**
instead of a generic error.

This is the first line of defense — it gives immediate, clear feedback without
consuming LLM tokens.  The SQL validator provides the second line of defense
for any destructive SQL the LLM might still generate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core import get_logger
from app.core.errors import ReadonlyRestrictionError

log = get_logger(__name__)

_DESTRUCTIVE_KEYWORDS: dict[str, list[str]] = {
    "delete": ["delete", "delete from", "delete row", "remove"],
    "insert": ["insert", "add new", "create a new", "add a new", "new entry"],
    "update": ["update", "modify", "change", "alter", "set "],
    "drop": ["drop table", "drop column", "drop database", "delete table"],
    "truncate": ["truncate", "clear table", "wipe"],
    "create": ["create table", "create database", "create index", "new table"],
    "grant": ["grant", "give ", "add permission", "add role"],
    "admin": ["admin", "administrator", "superuser", "root user"],
}

_MESSAGES: dict[str, str] = {
    "delete": (
        "This assistant only supports read-only queries (SELECT statements).\n"
        "I can't delete or remove data, but I can help you analyze your existing data.\n"
        "Try asking: 'How many customers do we have?' or 'Which product sold the most?'"
    ),
    "insert": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't create or insert new records, but I can help you analyze your existing data.\n"
        "Try asking: 'How many products do we have?' or 'Show me the latest orders.'"
    ),
    "update": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't update or modify existing records, but I can help you analyze your data.\n"
        "Try asking: 'Show top-selling products' or 'What's our revenue by region?'"
    ),
    "drop": (
        "This assistant only supports read-only queries (SELECT statements).\n"
        "I can't delete tables or modify the schema, but I can help you explore your data.\n"
        "Try asking: 'What tables do we have?' or 'How many columns are in the orders table?'"
    ),
    "truncate": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't clear or wipe tables, but I can help you summarize your existing data.\n"
        "Try asking: 'How many records are in each table?' or 'Show me the largest table.'"
    ),
    "create": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't create new tables or database objects, but I can help you explore your existing schema.\n"
        "Try asking: 'What tables do we have?' or 'Describe the customer table.'"
    ),
    "grant": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't grant permissions or manage roles, but I can help you analyze your data.\n"
        "Try asking about your existing tables and their relationships."
    ),
    "admin": (
        "This assistant is restricted to read-only queries (SELECT statements).\n"
        "I can't create admin users or manage access, but I can help you analyze your data.\n"
        "Try asking: 'How many customers do we have?' or 'What was our revenue last month?'"
    ),
}

_DEFAULT_MESSAGE = (
    "This assistant is restricted to read-only queries (SELECT statements).\n"
    "I can't perform write, delete, or schema operations, but I can help you "
    "analyze your existing data. Try asking: 'How many customers do we have?' "
    "or 'What was our total revenue?'"
)


@dataclass
class RestrictionResult:
    """Result of checking a question for destructive intent."""
    is_violation: bool
    detected_action: str | None
    message: str


def _normalize_question(question: str) -> str:
    return question.strip().lower()


def check_question(question: str) -> RestrictionResult:
    """Check whether *question* requests a destructive or write operation.

    Returns a :class:`RestrictionResult`.  When ``is_violation`` is ``True``,
    ``message`` contains a user-friendly explanation and ``detected_action``
    identifies the category (e.g. ``"delete"``, ``"insert"``).
    """
    normalized = _normalize_question(question)

    if not normalized:
        return RestrictionResult(is_violation=False, detected_action=None, message="")

    for action, keywords in _DESTRUCTIVE_KEYWORDS.items():
        for kw in keywords:
            if kw in normalized:
                message = _MESSAGES.get(action, _DEFAULT_MESSAGE)
                log.info(
                    "Destructive intent detected",
                    extra={"extra_data": {"action": action, "keyword": kw}},
                )
                return RestrictionResult(
                    is_violation=True,
                    detected_action=action,
                    message=message,
                )

    return RestrictionResult(
        is_violation=False,
        detected_action=None,
        message="",
    )


def enforce_readonly(question: str) -> None:
    """Raise :class:`ReadonlyRestrictionError` if *question* is destructive."""
    result = check_question(question)
    if result.is_violation:
        raise ReadonlyRestrictionError(result.message, detail=f"Detected action: {result.detected_action}")
