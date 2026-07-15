"""
logging_config.py — structured logging with request/session correlation (audit #16).

A live 500-user classroom is impossible to debug from bare `print()` lines: when
a facilitator says "team X is stuck", you need to pull every log line for that
session/request. This module adds:

  • a JSON formatter (one object per line — greppable + ingestible by any log
    platform), and
  • request_id / session_id carried on ContextVars so EVERY log record emitted
    while handling a request is automatically tagged, without threading the ids
    through every function.

Format is JSON in production and human-readable in local dev (DEBUG=true), or
force either with LOG_FORMAT=json|plain. Existing print() calls are left as-is;
this is additive infrastructure plus the per-request access log wired in main.py.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_session_id_var: ContextVar[str] = ContextVar("session_id", default="")


# ── Context helpers ─────────────────────────────────────────────────────────
def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def set_request_context(request_id: str = "", session_id: str = "") -> None:
    if request_id:
        _request_id_var.set(request_id)
    if session_id:
        _session_id_var.set(session_id)


def get_request_id() -> str:
    return _request_id_var.get()


def get_session_id() -> str:
    return _session_id_var.get()


def reset_request_context() -> None:
    _request_id_var.set("")
    _session_id_var.set("")


# ── Formatter / filter ──────────────────────────────────────────────────────
class _ContextFilter(logging.Filter):
    """Attach the current request/session ids to every record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = _request_id_var.get()
        record.session_id = _session_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "session_id": getattr(record, "session_id", ""),
        }
        # Drop empty correlation ids to keep lines tidy.
        payload = {k: v for k, v in payload.items() if v not in ("", None)}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class _PlainFormatter(logging.Formatter):
    """Dev-friendly single line: LEVEL logger [req/sess] message."""

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", "")
        sid = getattr(record, "session_id", "")
        tag = ""
        if rid or sid:
            tag = f" [{rid}{('/' + sid[:8]) if sid else ''}]"
        base = f"{record.levelname:<7} {record.name}{tag}: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def _use_json() -> bool:
    fmt = os.getenv("LOG_FORMAT", "").strip().lower()
    if fmt == "json":
        return True
    if fmt == "plain":
        return False
    # Default: JSON in production, plain in local dev.
    return os.getenv("DEBUG", "false").lower() != "true"


_configured = False


def configure_logging(level: str | None = None) -> None:
    """Idempotently install the structured handler on the root logger."""
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    root.setLevel(getattr(logging, lvl, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if _use_json() else _PlainFormatter())
    handler.addFilter(_ContextFilter())

    # Replace any pre-existing handlers so records aren't double-formatted.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    _configured = True
