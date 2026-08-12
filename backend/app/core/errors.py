"""Application-level exception hierarchy.

All exceptions raised to the API surface are mapped to safe, user-facing messages
so that stack traces, credentials, or infrastructure details are never leaked.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for application errors surfaced to callers."""

    user_message: str = "Something went wrong."
    status_code: int = 500

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message is not None:
            self.user_message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.user_message)


class SchemaDiscoveryError(AppError):
    user_message = "Could not inspect the database schema."
    status_code = 500


class SchemaSelectionError(AppError):
    user_message = "Could not identify relevant schema for the question."
    status_code = 500


class LLMError(AppError):
    user_message = "The language model did not return a usable response."
    status_code = 502

    def __init__(self, message: str | None = None, status_code: int | None = None, detail: str | None = None):
        super().__init__(message, status_code)
        self.detail = detail


class SQLValidationError(AppError):
    user_message = "The generated SQL was unsafe or invalid."
    status_code = 422

    def __init__(self, message: str | None = None, detail: str | None = None):
        super().__init__(message)
        self.detail = detail

    # The actual generated SQL must never be returned on a security failure.


class ExecutionError(AppError):
    user_message = "The query could not be executed against the database."
    status_code = 500

    def __init__(self, message: str | None = None, detail: str | None = None):
        super().__init__(message)
        self.detail = detail


class ResultProcessingError(AppError):
    user_message = "Results could not be processed."
    status_code = 500


class ExplanationError(AppError):
    user_message = "Could not generate an explanation of the results."
    status_code = 502


class UnauthorizedQuestionError(AppError):
    user_message = "Unable to answer that question with the available data."
    status_code = 422
