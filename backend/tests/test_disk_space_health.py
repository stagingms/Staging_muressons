"""A full data volume must be visible BEFORE it breaks a class (A6).

The register listed "volume full" with no detection at all: `/health` reported
`writable: true` because the probe writes two bytes, and `durable: true`
because the volume is configured — both of which stay true with kilobytes
left. The first symptom would have been a pack upload or a registry write
failing mid-workshop, with every health signal green.

So `storage_status()` now reports free space and a single `low_space` flag,
hoisted to `/health` as `low_disk_space` for monitors to alert on.

The delicate part is the UNKNOWN case. `shutil.disk_usage` can refuse on some
sandboxes and read-only mounts. An unknown reading must not raise a false
alarm, and must not be silently reported as healthy either — the contract is
that the `free_*` keys are simply absent, and their absence is the signal.
"""
import shutil

import pytest

import runtime_paths


def _usage(free, total):
    return shutil._ntuple_diskusage(total=total, used=total - free, free=free)


GB = 1024 ** 3
MB = 1024 ** 2


# ── the flag itself ────────────────────────────────────────────────────────

def test_a_healthy_volume_is_not_flagged(monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(50 * GB, 100 * GB))
    st = runtime_paths.storage_status()
    assert st["low_space"] is False
    assert st["free_pct"] == 50.0
    assert st["free_bytes"] == 50 * GB


def test_a_nearly_full_volume_trips_on_percentage(monkeypatch):
    # 5% of a large disk: plenty of bytes, but the trend is what matters.
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(5 * GB, 100 * GB))
    st = runtime_paths.storage_status()
    assert st["low_space"] is True
    assert st["free_pct"] == 5.0


def test_a_small_volume_trips_on_bytes_even_at_a_healthy_percentage(monkeypatch):
    # 20% free of a 250 MB volume = 50 MB. The percentage looks fine; 50 MB is
    # not fine. Percentage alone would have missed this, which is why the flag
    # trips on whichever measure is more alarming.
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(50 * MB, 250 * MB))
    st = runtime_paths.storage_status()
    assert st["free_pct"] == 20.0
    assert st["low_space"] is True


@pytest.mark.parametrize("free_pct", [9.9, 10.1])
def test_the_percentage_threshold_is_where_it_says_it_is(monkeypatch, free_pct):
    total = 1000 * GB          # big enough that the byte floor never fires
    monkeypatch.setattr(shutil, "disk_usage",
                        lambda p: _usage(int(total * free_pct / 100), total))
    st = runtime_paths.storage_status()
    assert st["low_space"] is (free_pct < runtime_paths.LOW_SPACE_PCT)


# ── unknown is not healthy, and not an alarm ───────────────────────────────

def test_an_unreadable_filesystem_reports_unknown_rather_than_guessing(monkeypatch):
    def boom(_p):
        raise OSError("not supported here")
    monkeypatch.setattr(shutil, "disk_usage", boom)

    st = runtime_paths.storage_status()
    assert st["low_space"] is False, "an unknown reading must not page anyone"
    assert "free_bytes" not in st, "absence of the reading IS the signal"
    assert "free_pct" not in st
    # …and the durability report still works, so one failing probe cannot take
    # the whole health endpoint down.
    assert "durable" in st and "writable" in st


def test_a_zero_total_does_not_divide_by_zero(monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(0, 0))
    st = runtime_paths.storage_status()
    assert st["free_pct"] == 0.0
    assert st["low_space"] is True


# ── the endpoint contract ──────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def test_health_exposes_the_flag_at_the_top_level(client, monkeypatch):
    """A monitor should not have to reach into a nested object to alert."""
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(1 * MB, 100 * GB))
    body = client.get("/api/health").json()
    assert body["low_disk_space"] is True
    assert body["storage"]["low_space"] is True
    assert body["storage"]["free_bytes"] == 1 * MB


def test_health_stays_green_on_a_healthy_volume(client, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(80 * GB, 100 * GB))
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["low_disk_space"] is False


# ── ?strict=1 — turning the flag into a status code ────────────────────────
#
# A JSON field can only be alerted on by a monitor that inspects the body.
# `?strict=1` makes the same condition visible to the simplest possible check
# ("is this URL still 200?"), which is what most uptime services actually do.

def test_strict_fails_when_the_volume_is_low(client, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(1 * MB, 100 * GB))
    r = client.get("/api/health?strict=1")
    assert r.status_code == 503, "a plain uptime monitor must be able to see this"
    body = r.json()
    assert body["status"] == "degraded"
    assert body["low_disk_space"] is True
    # the full report still travels with the alert — no second call needed
    assert body["storage"]["free_bytes"] == 1 * MB


def test_strict_passes_on_a_healthy_volume(client, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(80 * GB, 100 * GB))
    r = client.get("/api/health?strict=1")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_the_DEFAULT_endpoint_never_fails_on_disk(client, monkeypatch):
    """THE safety property.

    railway.json points its container healthcheck at /api/health, and a failing
    healthcheck RESTARTS the container. Restarting is the wrong response to a
    full volume: it fixes nothing and takes a live workshop down. So the
    unqualified endpoint must stay 200 even when the disk is critically low.
    """
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(0, 100 * GB))
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["low_disk_space"] is True, "…but it still REPORTS the problem"


@pytest.mark.parametrize("q", ["strict=0", "strict=false", ""])
def test_strict_is_opt_in(client, monkeypatch, q):
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(0, 100 * GB))
    assert client.get(f"/api/health?{q}").status_code == 200


def test_strict_does_not_fail_on_an_unreadable_filesystem(client, monkeypatch):
    """Unknown is not an alarm — the same rule the flag itself follows.
    Paging someone because a probe is unsupported would train them to mute it.
    """
    def boom(_p):
        raise OSError("not supported")
    monkeypatch.setattr(shutil, "disk_usage", boom)
    assert client.get("/api/health?strict=1").status_code == 200


# ── tripwire on the shape that hid the problem ─────────────────────────────

def test_writability_alone_is_never_treated_as_enough(monkeypatch):
    """The defect was that a 2-byte probe stood in for capacity.

    Pin the two as independent: a volume can be writable AND nearly full, and
    the report must say so rather than letting `writable` imply headroom.
    """
    monkeypatch.setattr(shutil, "disk_usage", lambda p: _usage(1 * MB, 10 * GB))
    st = runtime_paths.storage_status()
    assert st["writable"] is True, "precondition: the probe still succeeds"
    assert st["low_space"] is True, "…yet the volume is one upload from full"


def test_health_reports_free_space_keys_when_the_platform_answers(client):
    """No monkeypatching: whatever this machine really reports must parse."""
    st = client.get("/api/health").json()["storage"]
    if "free_bytes" in st:
        assert st["free_bytes"] >= 0
        assert 0.0 <= st["free_pct"] <= 100.0
        assert st["total_bytes"] >= st["free_bytes"]
    else:
        # Unknown here is acceptable, but then the flag must be off.
        assert st["low_space"] is False
