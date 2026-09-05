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
    # OPS-3: a Railway volume is a mount of its own; say so for this temp dir.
    monkeypatch.setattr(rp, "mount_point_of", lambda p: str(vol))
    st = rp.storage_status()
    assert st["on_railway"] is True
    assert st["configured"] is True
    assert st["writable"] is True
    assert st["mounted"] is True and st["mount_point"] == str(vol)
    assert st["durable"] is True
    assert st["data_dir"] == str(vol)


def test_railway_configured_writable_but_not_mounted_is_not_durable(monkeypatch, tmp_path):
    """OPS-3 (audit 2026-09-04): the image sets MURESSONS_DATA_DIR=/data and
    creates the directory, so `configured` and `writable` hold with NO volume
    attached — and `durable` said true while every redeploy wiped it. A data
    dir on the container root is not durable on Railway."""
    vol = tmp_path / "data"
    rp = _fresh_runtime_paths(monkeypatch, data_dir=vol, railway=True)
    monkeypatch.setattr(rp, "mount_point_of", lambda p: "/")
    st = rp.storage_status()
    assert st["configured"] is True and st["writable"] is True
    assert st["mounted"] is False
    assert st["durable"] is False


def test_unreadable_mount_table_is_not_a_verdict(monkeypatch, tmp_path):
    """No /proc/mounts (macOS/Windows): mounted is None and durability falls
    back to the configured+writable reading rather than failing closed."""
    vol = tmp_path / "data"
    rp = _fresh_runtime_paths(monkeypatch, data_dir=vol, railway=True)
    monkeypatch.setattr(rp, "mount_point_of", lambda p: None)
    st = rp.storage_status()
    assert st["mounted"] is None
    assert st["durable"] is True


def test_mount_point_of_reads_proc_mounts(monkeypatch, tmp_path):
    import runtime_paths as rp
    fake = tmp_path / "mounts"
    fake.write_text("overlay / overlay rw 0 0\n/dev/vdb /data ext4 rw 0 0\nproc /proc proc rw 0 0\n", encoding="utf-8")
    real_open = open

    def _open(path, *a, **kw):
        if str(path) == "/proc/mounts":
            return real_open(fake, *a, **kw)
        return real_open(path, *a, **kw)
    monkeypatch.setattr("builtins.open", _open)
    assert rp.mount_point_of("/data") == "/data"
    assert rp.mount_point_of("/data/sub/dir") == "/data"
    assert rp.mount_point_of("/var/lib/x") == "/"
    assert rp.is_mounted("/data") is True and rp.is_mounted("/var/lib/x") is False


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
        assert "mounted" in body["storage"]   # OPS-3


def teardown_module(module):
    # Restore runtime_paths to the ambient (test) environment so later suites
    # that import it see the normal repo-dir configuration.
    import runtime_paths
    importlib.reload(runtime_paths)
