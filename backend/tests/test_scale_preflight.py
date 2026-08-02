"""Audit #7 — the multi-worker safety gate.

Fanning out to >1 worker is only safe on the shared Postgres backend; on the
in-memory store every worker holds its own state and the classroom split-brains.
These tests pin that gate so a future config change can't silently allow an
unsafe fan-out.
"""

from scale_preflight import is_shared_backend, safe_worker_count


def test_postgres_backend_is_shared():
    env = {"USE_MEMORY_DB": "false", "DEBUG": "false"}
    assert is_shared_backend(env) is True


def test_memory_db_is_not_shared():
    assert is_shared_backend({"USE_MEMORY_DB": "true"}) is False


def test_debug_is_not_shared():
    assert is_shared_backend({"USE_MEMORY_DB": "false", "DEBUG": "true"}) is False


def test_allow_memory_in_prod_is_not_shared():
    assert is_shared_backend({"USE_MEMORY_DB": "false", "ALLOW_MEMORY_DB_IN_PROD": "true"}) is False


def test_multiworker_allowed_on_postgres():
    workers, warns = safe_worker_count({"USE_MEMORY_DB": "false", "DEBUG": "false", "WEB_CONCURRENCY": "5"})
    assert workers == 5
    assert warns == []


def test_multiworker_clamped_on_memory():
    workers, warns = safe_worker_count({"USE_MEMORY_DB": "true", "WEB_CONCURRENCY": "5"})
    assert workers == 1
    assert warns and "forcing 1 worker" in warns[0]


def test_multiworker_clamped_in_debug():
    workers, _ = safe_worker_count({"USE_MEMORY_DB": "false", "DEBUG": "true", "WEB_CONCURRENCY": "8"})
    assert workers == 1


def test_default_is_single_worker():
    workers, warns = safe_worker_count({"USE_MEMORY_DB": "false", "DEBUG": "false"})
    assert workers == 1
    assert warns == []


def test_non_integer_concurrency_defaults_to_one():
    workers, warns = safe_worker_count({"USE_MEMORY_DB": "false", "DEBUG": "false", "WEB_CONCURRENCY": "abc"})
    assert workers == 1
    assert any("not an integer" in w for w in warns)


def test_single_worker_on_memory_is_fine_no_warning():
    workers, warns = safe_worker_count({"USE_MEMORY_DB": "true", "WEB_CONCURRENCY": "1"})
    assert workers == 1
    assert warns == []
