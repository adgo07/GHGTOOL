"""Structured, allow-listed application logging for G00.

Only controlled operational tokens are written. Arbitrary messages and fields
are deliberately excluded so activity data, enterprise information and license
secrets cannot be emitted as clear text by this foundation logger.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


_TOKEN_PATTERN = re.compile(r"^[a-z0-9_.-]{1,64}$")
_SAFE_FIELDS = frozenset({"component", "outcome", "error_type"})


def _safe_token(value: Any) -> str | None:
    """Return a bounded operational token, never arbitrary user text."""

    if isinstance(value, bool):
        candidate = "true" if value else "false"
    elif isinstance(value, (str, int, float)):
        candidate = str(value)
    else:
        return None

    if _TOKEN_PATTERN.fullmatch(candidate):
        return candidate
    return None


class _JsonFormatter(logging.Formatter):
    """Serialize only fields controlled by :class:`StructuredLogger`."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "qz_event", "unstructured_event"),
            "app_version": getattr(record, "qz_app_version", "unknown"),
        }
        payload.update(getattr(record, "qz_fields", {}))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class StructuredLogger:
    """Small event-only facade that prevents free-form log messages."""

    def __init__(self, logger: logging.Logger, app_version: str, log_path: Path):
        self._logger = logger
        self._app_version = app_version
        self.log_path = log_path

    def event(self, event: str, **fields: Any) -> None:
        safe_event = _safe_token(event) or "invalid_event"
        safe_fields = {
            key: token
            for key, value in fields.items()
            if key in _SAFE_FIELDS
            for token in [_safe_token(value)]
            if token is not None
        }
        self._logger.info(
            "event",
            extra={
                "qz_event": safe_event,
                "qz_app_version": self._app_version,
                "qz_fields": safe_fields,
            },
        )

    def close(self) -> None:
        """Flush and release the file handler, including on Windows."""

        for handler in list(self._logger.handlers):
            handler.flush()
            self._logger.removeHandler(handler)
            handler.close()


def configure_logging(log_directory: Path, app_version: str = "1.0.0") -> StructuredLogger:
    """Configure JSON-lines logging and return the safe event facade."""

    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "application.jsonl"
    logger = logging.getLogger("qingzhou.carbon_accounting")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    return StructuredLogger(logger, app_version, log_path)
