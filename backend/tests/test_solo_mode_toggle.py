"""Solo sessions are a facilitator-controlled platform switch.

Request: make "Start Solo Session" on the login screen togglable from the
facilitator dashboard; when off, the option must not appear.

The switch is `solo_mode_enabled` on the Sim Switchboard (god-mode settings),
following the exact pattern of its siblings (front_page_enabled etc.):

  * read by the LOGIN SCREEN through the public, unauthenticated
    /api/admin/global-settings payload — the login page renders before any
    auth exists, so this is the only view it can use;
  * written through PATCH /api/admin/global-settings (super-admin gated);
  * enforced SERVER-SIDE on /solo-start — the endpoint is public, so a
    hidden button must never be the only line of defence (V-B/V-C
    precedent: gated content is refused, not merely unrendered);
  * DEFAULT ON — an absent key behaves exactly as before the toggle
    existed, so no existing deployment changes behaviour on upgrade.
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


@pytest.fixture
def god(client):
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    r = client.post("/api/admin/facilitators/login",
                    json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert r.status_code == 200
    return client


@pytest.fixture(autouse=True)
def restore_setting():
    """Leave the shared god-mode store how we found it — other tests read it."""
    from admin_shared import _god_mode_settings
    had = "solo_mode_enabled" in _god_mode_settings
    old = _god_mode_settings.get("solo_mode_enabled")
    yield
    if had:
        _god_mode_settings["solo_mode_enabled"] = old
    else:
        _god_mode_settings.pop("solo_mode_enabled", None)


def _solo(client):
    return client.post("/api/simulations/solo-start",
                       json={"player_name": "Solo Probe"})


def test_default_is_on_and_publicly_readable(client):
    """The login screen reads this anonymously; absent key must read True."""
    r = client.get("/api/admin/global-settings")
    assert r.status_code == 200
    assert r.json()["solo_mode_enabled"] is True


def test_solo_start_works_by_default(client):
    assert _solo(client).status_code == 201


def test_toggle_off_hides_and_refuses(god):
    p = god.patch("/api/admin/global-settings",
                  json={"solo_mode_enabled": False, "reason": "classroom-only run"})
    assert p.status_code == 200

    # The login screen's view flips…
    god.cookies.clear()
    assert god.get("/api/admin/global-settings").json()["solo_mode_enabled"] is False
    # …and the endpoint refuses even a direct, button-less call.
    r = _solo(god)
    assert r.status_code == 403
    assert "disabled" in r.json()["detail"].lower()


def test_toggle_back_on_restores_solo(god):
    god.patch("/api/admin/global-settings",
              json={"solo_mode_enabled": False, "reason": "off"})
    god.patch("/api/admin/global-settings",
              json={"solo_mode_enabled": True, "reason": "on again"})
    assert _solo(god).status_code == 201


def test_the_switch_is_write_gated(client):
    """Anonymous callers can READ the flag (the login page must) but never
    write it."""
    r = client.patch("/api/admin/global-settings", json={"solo_mode_enabled": False})
    assert r.status_code in (401, 403)
    assert client.get("/api/admin/global-settings").json()["solo_mode_enabled"] is True
