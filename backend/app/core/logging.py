"""Structured application logging.

Every event is emitted to stdout (container-friendly) and persisted to the
``log_entries`` table so the dashboard "Logs" page can display it.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid import cycles at runtime
    from sqlalchemy.orm import Session

_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
        )
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    _configured = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(
    db: Session,
    level: str,
    message: str,
    *,
    project_id: int | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    """Persist an event to the DB log stream (best effort) and to stdout."""
    logger = get_logger("studio.events")
    logger.log(getattr(logging, level.upper(), logging.INFO), message)
    try:
        from app.models.log import LogEntry

        db.add(
            LogEntry(project_id=project_id, level=level.upper(), message=message, context=context or {})
        )
        db.commit()
    except Exception:  # pragma: no cover - logging must never break the app
        logger.exception("failed to persist log event")
