"""SQL generation and validation services.

Submodules:
  - validator: AST-based safety validation of generated SQL using sqlglot.
"""
from app.services.sql.validator import (
    SQLValidator,
    ValidationResult,
    validate_sql,
)

__all__ = [
    "SQLValidator",
    "ValidationResult",
    "validate_sql",
]
