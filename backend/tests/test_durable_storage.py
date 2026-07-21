"""Durable-storage verification (Railway volume / MURESSONS_DATA_DIR).

All mutable state — facilitator registry, token versions, virtual-account
profiles, and the game-state snapshot (which holds every cohort's settings
overlay: pacing, briefing-video URLs, templates, visibility) — lives under
runtime_paths.data_dir(). On Railway the container FS is ephemeral, so that dir
MUST be a mounted volume pointed at by MURESSONS_DATA_DIR or every redeploy
wipes it. Pins:

  1. storage_status() reports durability correctly for the deploy matrix
     (on/off Railway × configured/unset × writable/not).
  2. /health and /api/health both exist (railway.json health-checks
     /api/health) and surface the durability flag.
"""

import importlib
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _fresh_runtime_paths(monkeypatch, *, data_dir=None, railway=False):
    """Reload runtime_paths under a controlled environment."""
    for var in ("MURESSONS_DATA_DIR", "RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID"):
        monkeypatch.delenv(var, raising=False)
    if data_dir is not None:
        monkeypatch.setenv("MURESSONS_DATA_DIR", str(data_dir))
    if railway:
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    import runtime_paths
    return importlib.reload(runtime_paths)


def test_railway_without_volume_is_not_durable(monkeypatch, tmp_path):
    # On Railway with no MURESSONS_DATA_DIR ⇒ ephemeral repo dir ⇒ NOT durable.
    rp = _fresh_runtime_paths(monkeypatch, data_dir=None, railway=True)
    st = rp.storage_status()
    assert st["on_railway"] is True
    assert st["configured"] is False
    assert st["durable"] is False


def test_railway_with_writable_volume_is_durable(monkeypatch, tmp_path):
    vol = tmp_path / "data"
    rp = _fresh_runtime_paths(monkeypatch, data_dir=vol, railway=True)
    st = rp.storage_status()
    assert st["on_railway"] is True
    assert st["configured"] is True
    assert st["writable"] is True
    assert st["durable"] is True
    assert st["data_dir"] == str(vol)


def test_off_railway_repo_dir_is_durable(monkeypatch, tmp_path):
    # Local dev / docker-compose bind mount: <repo>/db is as durable as the host.
    rp = _fresh_runtime_paths(monkeypatch, data_dir=None, railway=False)
    st = rp.storage_status()
    assert st["on_railway"] is False
    assert st["durable"] is True   # writable local dir


def test_configured_but_unwritable_is_not_durable(monkeypatch):
    # MURESSONS_DATA_DIR pointing at a path that cannot be created/written.
    rp = _fresh_runtime_paths(monkeypatch, data_dir="/proc/muressons_nope", railway=True)
    st = rp.storage_status()
    assert st["writable"] is False
    assert st["durable"] is False


def test_health_endpoints_report_storage():
    for path in ("/health", "/api/health"):
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        body = r.json()
        assert body["status"] == "ok"
        assert "durable_storage" in body
        assert "storage" in body and "data_dir" in body["storage"]


def teardown_module(module):
    # Restore runtime_paths to the ambient (test) environment so later suites
    # that import it see the normal repo-dir configuration.
    import runtime_paths
    importlib.reload(runtime_paths)
