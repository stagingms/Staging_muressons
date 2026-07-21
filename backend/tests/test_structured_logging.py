"""Audit #16 — structured logging + request/session correlation."""

import json
import logging
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import logging_config
from main import app

client = TestClient(app)


def test_response_carries_request_id_header():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Request-Id")  # non-empty correlation id echoed back


def test_client_request_id_is_propagated():
    r = client.get("/health", headers={"X-Request-Id": "trace-abc-123"})
    assert r.headers.get("X-Request-Id") == "trace-abc-123"


def test_json_formatter_includes_context_ids():
    logging_config.set_request_context("req-42", "sess-xyz")
    try:
        rec = logging.LogRecord("t", logging.INFO, __file__, 1, "hello", None, None)
        logging_config._ContextFilter().filter(rec)
        line = logging_config.JsonFormatter().format(rec)
        obj = json.loads(line)
        assert obj["msg"] == "hello"
        assert obj["request_id"] == "req-42"
        assert obj["session_id"] == "sess-xyz"
        assert obj["level"] == "INFO"
    finally:
        logging_config.reset_request_context()


def test_empty_ids_are_omitted_from_json():
    logging_config.reset_request_context()
    rec = logging.LogRecord("t", logging.WARNING, __file__, 1, "no ctx", None, None)
    logging_config._ContextFilter().filter(rec)
    obj = json.loads(logging_config.JsonFormatter().format(rec))
    assert "request_id" not in obj and "session_id" not in obj
    assert obj["msg"] == "no ctx"
