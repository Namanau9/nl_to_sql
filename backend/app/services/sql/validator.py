"""AST-based SQL validation and guardrails.

Uses sqlglot to parse the generated SQL into an abstract syntax tree, then
walks that tree to enforce a strict allow-list of operations and table
references. This is the second line of defense after the prompt-level schema
boundary (the LLM should only ever receive the relevant sub-schema); the
validator independently rejects anything the prompt did not successfully
constrain.

Security model (defense in depth):
  1. Schema boundary — only relevant tables are sent to the LLM.
  2. AST validation — this module.
  3. Read-only DB role — enforced by the database itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import sqlglot
import sqlglot.expressions as exp

from app.core import get_logger
from app.core.errors import SQLValidationError

log = get_logger(__name__)

_ALLOWED_STMT_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Select,
    exp.Union,
    exp.Subquery,
    exp.CTE,
)

_BLOCKED_STMT_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Create,
    exp.Grant,
    exp.Set,
    exp.Command,
)

_DANGEROUS_HINTS = ("INTO", "OUTFILE", "DUMPFILE", "LOAD")


@dataclass
class ValidationResult:
    """Outcome of validating a single SQL string."""

    is_valid: bool
    statement_count: int
    referenced_tables: list[str]
    error: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def _collect_table_names(stmt: exp.Expression) -> list[str]:
    """Return normalized, de-duplicated, non-cte table names in *stmt*."""
    cte_names = {cte.alias_or_name for cte in stmt.find_all(exp.CTE)}
    names: set[str] = set()
    for table in stmt.find_all(exp.Table):
        if table.args.get("this") is None:
            continue
        name = table.name
        if not name or name.lower() in cte_names:
            continue
        names.add(name.lower())
    return sorted(names)


def _check_statement_type(stmt: exp.Expression) -> str | None:
    """Return an error message if *stmt* is of a disallowed type."""
    if isinstance(stmt, _BLOCKED_STMT_TYPES):
        return (
            f"Statement type '{type(stmt).__name__}' is not permitted; "
            f"only read-only SELECT/WITH queries are allowed."
        )
    if not isinstance(stmt, _ALLOWED_STMT_TYPES):
        return f"Statement type '{type(stmt).__name__}' is not recognized as a safe read-only query."
    return None


def _check_no_dangerous_hints(stmt: exp.Expression) -> str | None:
    """Reject constructs that hint at data exfiltration (e.g. SELECT INTO)."""
    sql = stmt.sql(dialect="postgres").upper()
    for keyword in _DANGEROUS_HINTS:
        if keyword in sql:
            return f"Query contains prohibited keyword '{keyword}'."
    return None


def validate_sql(
    sql: str,
    allowed_tables: Iterable[str] | None = None,
    dialect: str = "postgres",
) -> ValidationResult:
    """Validate a SQL string against the safety allow-list.

    Parameters
    ----------
    sql:
        The raw SQL string produced by the LLM.
    allowed_tables:
        Table names that the query is permitted to reference.  When *None*
        the table-reference check is skipped (useful for unit tests that only
        care about statement-type validation).
    dialect:
        SQL dialect passed to the sqlglot parser (default ``postgres``).

    Raises
    ------
    SQLValidationError
        If the query should never reach the database.  The exception message
        is safe to surface to API callers; the raw SQL is **never** included.
    """
    check_tables = allowed_tables is not None
    allowed = {t.lower() for t in (allowed_tables or [])}

    if not sql or not sql.strip():
        raise SQLValidationError("Empty SQL query.")

    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError("Generated SQL could not be parsed (syntax error).") from exc

    if statements is None or len(statements) == 0:
        raise SQLValidationError("Generated SQL produced no parseable statements.")

    if len(statements) > 1:
        raise SQLValidationError(
            f"Multiple SQL statements detected ({len(statements)}); "
            f"only a single statement is permitted."
        )

    stmt = statements[0]
    if stmt is None:
        raise SQLValidationError("Generated SQL produced no parseable statements.")

    type_error = _check_statement_type(stmt)
    if type_error:
        log.warning("SQL validation failed: statement type", extra={"extra_data": {"error": type_error}})
        raise SQLValidationError(type_error)

    hint_error = _check_no_dangerous_hints(stmt)
    if hint_error:
        log.warning("SQL validation failed: dangerous construct", extra={"extra_data": {"error": hint_error}})
        raise SQLValidationError(hint_error)

    referenced = _collect_table_names(stmt)

    unauthorized = (
        [t for t in referenced if t not in allowed]
        if check_tables
        else []
    )
    if unauthorized:
        error = (
            "Query references one or more unauthorized table(s). "
            "Only tables in the approved schema may be used."
        )
        log.warning("SQL validation failed: unauthorized tables", extra={"extra_data": {"error": error}})
        raise SQLValidationError(error)

    log.info(
        "SQL validated successfully",
        extra={"extra_data": {"tables": referenced, "stmt_type": type(stmt).__name__}},
    )
    return ValidationResult(
        is_valid=True,
        statement_count=1,
        referenced_tables=referenced,
    )


class SQLValidator:
    """Stateful wrapper around :func:`validate_sql` with a fixed allow-list."""

    def __init__(self, allowed_tables: Iterable[str]):
        self._allowed_tables = {t.lower() for t in allowed_tables}

    @property
    def allowed_tables(self) -> list[str]:
        return sorted(self._allowed_tables)

    def validate(self, sql: str, dialect: str = "postgres") -> ValidationResult:
        return validate_sql(sql, allowed_tables=self._allowed_tables, dialect=dialect)
