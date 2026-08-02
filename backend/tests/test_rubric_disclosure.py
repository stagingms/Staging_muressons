"""The grading rubric must not be publicly readable mid-game (F-21).

/api/admin/global-settings is deliberately unauthenticated — players call it
on mount for climate mode, briefing videos, currency, etc. That carried the
facilitator-tunable esg_profile_weights along with it, so ANY student could
fetch the exact end-game scoring weights mid-run and optimise to the rubric
instead of the strategy. (The audit flagged this; the raw
/esg-profile-weights GET was additionally missing a guard its own setter had.)

Disclosure rule now: an authenticated facilitator always sees the weights;
an anonymous caller sees them only for a FINISHED session — the ESG
Leadership Profile screen renders them at end-of-game, when there is nothing
left to optimise. The client already falls back to defaults when the field
is null, so player rendering is unaffected mid-game.
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


def _clear_limits():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def test_anonymous_caller_gets_no_weights(client):
    r = client.get("/api/admin/global-settings")
    assert r.status_code == 200, "the endpoint must stay public for players"
    assert r.json().get("esg_profile_weights") is None


def test_anonymous_caller_with_a_live_session_gets_no_weights(client):
    _clear_limits()
    login = client.post("/api/admin/facilitators/login",
                        json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert login.status_code == 200
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "RubricProbe",
                                "facilitator_id": "god_mode"}).json()["session_id"])
    # Drop the facilitator cookie the TestClient captured at login — this
    # request must arrive exactly as a player's browser would send it.
    client.cookies.clear()
    r = client.get(f"/api/admin/global-settings?session_id={sid}")
    assert r.status_code == 200
    assert r.json().get("esg_profile_weights") is None, (
        "a running cohort just leaked its grading rubric to an anonymous caller")


def test_facilitator_still_sees_the_weights(client):
    _clear_limits()
    login = client.post("/api/admin/facilitators/login",
                        json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert login.status_code == 200
    r = client.get("/api/admin/global-settings", cookies=login.cookies)
    assert r.status_code == 200
    assert isinstance(r.json().get("esg_profile_weights"), dict), (
        "the Sim Switchboard and ESG editor read this authenticated view")


def test_raw_weights_endpoint_now_requires_auth(client):
    """The setter was guarded; the getter was not. They must match."""
    _clear_limits()
    assert client.get("/api/admin/esg-profile-weights").status_code in (401, 403)


def test_everything_else_in_the_payload_is_untouched(client):
    """The gate must remove ONE field, not degrade the player-config surface."""
    r = client.get("/api/admin/global-settings")
    body = r.json()
    for key in ("simulation_mode", "climate_paradigm", "currency_symbol",
                "front_page_enabled", "briefing_videos"):
        assert key in body
