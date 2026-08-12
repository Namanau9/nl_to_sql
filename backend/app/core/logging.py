"""Structured (JSON) logging configuration.

Logs are emitted as JSON lines to stdout so they are easy to ship to a log
aggregator. Secrets are never logged by design — callers must redact before
logging (see `redact`).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


_REDACT_KEYS = {
    "password", "pwd", "secret", "token", "api_key", "apikey",
    "authorization", "database_url", "readonly_database_url", "x-api-key",
}


def redact(obj):
    """Recursively redact fields whose name looks sensitive."""
    if isinstance(obj, dict):
        return {k: ("***REDACTED***" if any(r in k.lower() for r in _REDACT_KEYS) else redact(v))
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(i) for i in obj]
    return obj


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_data", None)
        if extra:
            payload["data"] = redact(extra)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
