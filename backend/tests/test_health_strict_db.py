"""OPS-4 (audit 2026-09-04, WP-20): /api/health never touched the database,
so the facilitator RunBar dot stayed green and an external monitor on
`?strict=1` saw "ok" with Postgres unreachable. Under ?strict=1 the report
now round-trips `SELECT 1` with a 2-second bound; a failure is a 503 with
the reason in the body. The unqualified endpoint stays cheap and 200 —
railway.json's container healthcheck restarts the service on a failure, and
a restart is the wrong response to a database outage.

Also pins the CFG-02 `config` block every /health carries (which file, its
fingerprint, the clamped keys, the volume-vs-image drift).
"""
import os
import types

os.environ["USE_MEMORY_DB"] = "true"

import pytest
from fastapi.testclient import TestClient

import main
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_default_health_does_not_touch_the_database(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["database_reachable"] is None      # not asked, not probed


def test_strict_on_the_memory_store_is_reachable_by_construction(client):
    r = client.get("/api/health?strict=1")
    assert r.status_code == 200
    assert r.json()["database_reachable"] is True


def _fake_db(get_pool):
    mod = types.ModuleType("database")   # __name__ != "database_memory" ⇒ "postgresql"
    mod.get_pool = get_pool
    return mod


def test_strict_fails_closed_when_postgres_is_unreachable(client, monkeypatch):
    async def _boom():
        raise ConnectionRefusedError("connection refused (probe)")
    monkeypatch.setattr(main, "_use_memory", False)
    monkeypatch.setattr(main, "db", _fake_db(_boom))
    r = client.get("/api/health?strict=1")
    assert r.status_code == 503, "a plain uptime monitor must see the outage"
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "postgresql"
    assert body["database_reachable"] is False
    assert "ConnectionRefusedError" in body["database_error"]
    # the unqualified endpoint still answers 200 — never restart on this
    assert client.get("/api/health").status_code == 200


def test_strict_passes_when_select_1_answers(client, monkeypatch):
    class _Pool:
        async def fetchval(self, q):
            assert q == "SELECT 1"
            return 1

    async def _pool():
        return _Pool()
    monkeypatch.setattr(main, "_use_memory", False)
    monkeypatch.setattr(main, "db", _fake_db(_pool))
    r = client.get("/api/health?strict=1")
    assert r.status_code == 200
    assert r.json()["database_reachable"] is True


def test_health_carries_the_config_block(client):
    """CFG-02: an operator can read from /health which config file the
    process runs, whether the volume copy drifted from the image, and which
    values config.py refused — the facts the deploy log prints at boot."""
    with TestClient(app) as booted:          # lifespan populates app.state.config_boot
        body = booted.get("/api/health").json()
    cfg = body["config"]
    assert cfg["path"].endswith("simulation_config.json")
    assert cfg["fingerprint"].startswith("sha256:")
    assert cfg["clamped_values"] == []                  # the committed config trips nothing
    assert cfg["volume_differs_from_image_on"] == []    # the test data dir is seeded from the image
    assert "mounted" in body["storage"]                 # OPS-3
