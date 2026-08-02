"""Solo sessions are OPT-IN, controlled by a lead facilitator or super admin.

Policy (2026-08-01, by request): the login screen's "Start Solo Session"
option is OFF by default; a lead_facilitator or super_admin enables it per
workshop. One flag, `solo_mode_enabled`, is the single source of truth:

  * READ by the login screen through the public /api/admin/global-settings
    payload (pre-auth, so the only view it can use). Default OFF: an absent
    key reads False, so an unconfigured platform shows no solo option.
  * WRITTEN through the dedicated PATCH /api/admin/solo-mode, gated at
    require_lead_facilitator (admits lead_facilitator, super_admin, god_mode;
    excludes base facilitator and project_admin). The god-mode Sim Switchboard
    still writes the same flag for super admins.
  * ENFORCED server-side on /solo-start, which now FAILS CLOSED: off by
    default, and a settings error denies rather than admits (solo is opt-in).
"""
import pytest


@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _login(client, fac_id, password="test-master-pw"):
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    return client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": fac_id, "password": password})


@pytest.fixture
def god(client):
    assert _login(client, "god_mode").status_code == 200
    return client


@pytest.fixture(autouse=True)
def restore_setting():
    """Leave the shared god-mode store how we found it — other tests read it."""
    from admin_shared import _god_mode_settings
    had = "solo_mode_enabled" in _god_mode_settings
    old = _god_mode_settings.get("solo_mode_enabled")
    _god_mode_settings.pop("solo_mode_enabled", None)   # start each test unconfigured
    yield
    if had:
        _god_mode_settings["solo_mode_enabled"] = old
    else:
        _god_mode_settings.pop("solo_mode_enabled", None)


def _solo(client):
    return client.post("/api/simulations/solo-start", json={"player_name": "Solo Probe"})


# ── default OFF ────────────────────────────────────────────────────────────

def test_default_is_off_and_publicly_readable(client):
    """The login screen reads this anonymously; an absent key must read False."""
    r = client.get("/api/admin/global-settings")
    assert r.status_code == 200
    assert r.json()["solo_mode_enabled"] is False


def test_solo_start_is_refused_by_default(client):
    r = _solo(client)
    assert r.status_code == 403
    assert "not enabled" in r.json()["detail"].lower()


# ── the dedicated lead-facilitator endpoint ────────────────────────────────

def test_lead_facilitator_can_enable_and_disable(client):
    # A real lead_facilitator (not god_mode) provisioned by god_mode.
    assert _login(client, "god_mode").status_code == 200
    made = client.post("/api/admin/facilitators",
                       json={"name": "Lead One", "role": "lead_facilitator"})
    assert made.status_code == 200, made.text
    body = made.json()
    fac_id = (body.get("facilitator") or {}).get("facilitator_id") or body.get("facilitator_id")
    from default_credentials import default_facilitator_password
    client.cookies.clear()
    assert _login(client, fac_id, default_facilitator_password(fac_id)).status_code == 200

    on = client.patch("/api/admin/solo-mode", json={"enabled": True})
    assert on.status_code == 200 and on.json()["solo_mode_enabled"] is True
    assert client.get("/api/admin/global-settings").json()["solo_mode_enabled"] is True
    # now a public solo-start is admitted
    import rate_limit
    rate_limit._rate_buckets.clear(); rate_limit._persistent_bans.clear()
    assert _solo(client).status_code == 201

    off = client.patch("/api/admin/solo-mode", json={"enabled": False})
    assert off.status_code == 200 and off.json()["solo_mode_enabled"] is False
    rate_limit._rate_buckets.clear(); rate_limit._persistent_bans.clear()
    assert _solo(client).status_code == 403


def test_base_facilitator_cannot_toggle(client):
    assert _login(client, "god_mode").status_code == 200
    made = client.post("/api/admin/facilitators",
                       json={"name": "Base One", "role": "facilitator"})
    fac_id = (made.json().get("facilitator") or {}).get("facilitator_id") or made.json().get("facilitator_id")
    from default_credentials import default_facilitator_password
    client.cookies.clear()
    assert _login(client, fac_id, default_facilitator_password(fac_id)).status_code == 200
    r = client.patch("/api/admin/solo-mode", json={"enabled": True})
    assert r.status_code == 403
    # and it did NOT change the flag
    assert client.get("/api/admin/global-settings").json()["solo_mode_enabled"] is False


def test_anonymous_cannot_toggle_but_can_read(client):
    assert client.patch("/api/admin/solo-mode", json={"enabled": True}).status_code in (401, 403)
    assert client.get("/api/admin/solo-mode").status_code in (401, 403)  # GET is gated too
    # the public settings read stays open (the login screen needs it)
    assert client.get("/api/admin/global-settings").json()["solo_mode_enabled"] is False


# ── super admin path (god-mode switchboard) still works ────────────────────

def test_super_admin_switchboard_toggle_still_writes_the_same_flag(god):
    p = god.patch("/api/admin/global-settings",
                  json={"solo_mode_enabled": True, "reason": "workshop"})
    assert p.status_code == 200
    assert god.get("/api/admin/solo-mode").json()["solo_mode_enabled"] is True
    import rate_limit
    rate_limit._rate_buckets.clear(); rate_limit._persistent_bans.clear()
    assert _solo(god).status_code == 201


def test_solo_start_fails_closed_on_a_settings_error(client, monkeypatch):
    """A store hiccup must DENY (opt-in), never admit."""
    import admin_shared

    class _Boom(dict):
        def get(self, *a, **k):
            raise RuntimeError("settings unavailable")

    monkeypatch.setattr(admin_shared, "_god_mode_settings", _Boom())
    r = _solo(client)
    assert r.status_code == 403
