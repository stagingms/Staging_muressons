"""The cohort wizard's pacing choice is enforced — audit 2026-09-04 F-18(i) / FLOW-02.

THE DEFECT
----------
CreateCohortModal's last step is PUT /api/admin/cohort/{id}/pacing with the
wizard's vocabulary: {pacing_mode: "manual", max_unlocked_round: N} or
{pacing_mode: "scheduled", round_schedules: {...}}. The handler stored those
as session metadata and wrote `pacing["mode"] = "manual"` — but left
`unlocked_round` at the free-play sentinel 999 and armed no timer. The commit
gate (is_round_unlocked) reads `mode == "free"` and `unlocked_round`, so a
cohort created as "Manual, unlock up to Round 1" had every round open: the
console badge read Manual, a player could run R1→R10 unattended, and the
facilitator's Unlock button had nothing to unlock. "Scheduled" never fired.

THE FIX
-------
The wizard's ids are mapped onto the pacing engine's (free_play→free,
manual→manual, scheduled→timed) and applied through the SAME code as the
Round Pacing panel's POST /sessions/{id}/pacing (`_apply_pacing`), then the
manual ceiling is raised to `max_unlocked_round`. POST /cohort/{id}/apply-setup
(the API-only one-call setup) goes through the same helper.
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


def _clear():
    import rate_limit
    import router as rmod
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    getattr(rmod, "_commit_timestamps", {}).clear()


@pytest.fixture
def cohort(client):
    _clear()
    assert client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": "god_mode", "password": "test-master-pw"}
                       ).status_code == 200
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "WizardPacing", "facilitator_id": "god_mode"})
    assert r.status_code == 201, r.text
    return str(r.json()["session_id"])


BUS = ["pharma", "electronics", "consumer_goods", "software"]


def _join(client, sid):
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    return str(j["session_id"]), {"X-Player-Id": g["player_id"]}


def _commit(client, psid, headers, rnd):
    _clear()
    return client.post(f"/api/simulations/{psid}/commit-turn", headers=headers,
                       json={"decisions": [{"bu_id": b, "capex_allocated": 2_000_000,
                                            "choice_selected": "option_a",
                                            "investment_ratio": 0.2} for b in BUS],
                             "dividends_paid": 0, "expected_round": rnd})


def _wizard_put(client, sid, **body):
    """Exactly what CreateCohortModal sends (CreateCohortModal.js, 'Pacing' step)."""
    return client.put(f"/api/admin/cohort/{sid}/pacing", json=body)


# ── manual ─────────────────────────────────────────────────────────────────

def test_wizard_manual_up_to_r1_actually_gates_round_2(client, cohort):
    """THE bug: 'Manual, unlock up to Round 1' left unlocked_round at 999."""
    from admin_shared import _get_pacing, is_round_unlocked

    r = _wizard_put(client, cohort, pacing_mode="manual", max_unlocked_round=1, round_schedules=None)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "manual" and body["unlocked_round"] == 1, body

    # what the Round Pacing panel reads
    live = client.get(f"/api/admin/sessions/{cohort}/pacing").json()
    assert live["mode"] == "manual", "wizard wrote a mode id the panel/gate do not know"
    assert live["unlocked_round"] == 1, f"ceiling stayed at {live['unlocked_round']} — nothing is gated"
    assert _get_pacing(cohort)["set_by"] is None, "god_mode created it: no facilitator ownership claimed"
    assert is_round_unlocked(cohort, 1) is True
    assert is_round_unlocked(cohort, 2) is False

    # a real player is held at the ceiling
    psid, headers = _join(client, cohort)
    assert _commit(client, psid, headers, 1).status_code == 201
    blocked = _commit(client, psid, headers, 2)
    assert blocked.status_code == 403, f"round 2 was NOT gated: {blocked.status_code} {blocked.text[:120]}"
    assert "locked" in blocked.json()["detail"].lower()

    # …until the facilitator opens it (RunBar now names the round: idempotent)
    u = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", json={"target_round": 2})
    assert u.status_code == 200 and u.json()["unlocked_round"] == 2, u.text
    again = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", json={"target_round": 2})
    assert again.json().get("already_unlocked") is True and again.json()["unlocked_round"] == 2, \
        "a retried unlock opened a further round"
    assert _commit(client, psid, headers, 2).status_code == 201
    assert _commit(client, psid, headers, 3).status_code == 403


def test_wizard_manual_ceiling_is_the_number_the_facilitator_chose(client, cohort):
    from admin_shared import is_round_unlocked
    assert _wizard_put(client, cohort, pacing_mode="manual", max_unlocked_round=3).status_code == 200
    assert client.get(f"/api/admin/sessions/{cohort}/pacing").json()["unlocked_round"] == 3
    assert is_round_unlocked(cohort, 3) is True
    assert is_round_unlocked(cohort, 4) is False


def test_wizard_and_round_pacing_panel_agree(client, cohort):
    """Re-applying Manual from the console (what RoundPacingControl posts)
    must not revoke the wizard's ceiling, and vice versa."""
    from admin_shared import _get_pacing
    assert _wizard_put(client, cohort, pacing_mode="manual", max_unlocked_round=2).status_code == 200
    assert client.post(f"/api/admin/sessions/{cohort}/pacing",
                       json={"mode": "manual", "interval_seconds": 300}).status_code == 200
    assert _get_pacing(cohort)["unlocked_round"] == 2
    # a re-save with a LOWER number never takes back an open round
    assert _wizard_put(client, cohort, pacing_mode="manual", max_unlocked_round=1).status_code == 200
    assert _get_pacing(cohort)["unlocked_round"] == 2


# ── scheduled ──────────────────────────────────────────────────────────────

def test_wizard_scheduled_persists_the_schedule_and_arms_timers(client, cohort):
    from admin_shared import _get_pacing, is_round_unlocked
    # the wizard's shape: {round: datetime-local or ISO}; blanks and junk are skipped
    schedules = {"1": "2026-09-04T00:00", "2": "2030-01-01T09:00:00.000Z", "4": "2030-01-02T09:00", "x": "2030-01-03T09:00", "11": "2030-01-04T09:00", "3": ""}
    r = _wizard_put(client, cohort, pacing_mode="scheduled", max_unlocked_round=10, round_schedules=schedules)
    assert r.status_code == 200, r.text
    assert r.json()["mode"] == "timed"

    p = _get_pacing(cohort)
    assert p["mode"] == "timed", "the wizard's 'scheduled' never became the engine's 'timed'"
    assert p["unlocked_round"] == 1
    assert p["schedule"][0] == "2026-09-04T00:00"
    assert p["schedule"][1] == "2030-01-01T09:00:00.000Z"
    assert p["schedule"][3] == "2030-01-02T09:00"
    assert p["schedule"][2] is None and len(p["schedule"]) == 10
    assert p["next_unlock_at"], "no next unlock published for the countdown"
    # one unlock task per scheduled round (TestClient tears its loop down per
    # request, so only creation — not liveness — is observable here)
    assert len(p.get("_timer_tasks", [])) == 3, "no unlock timers armed for the scheduled rounds"
    assert is_round_unlocked(cohort, 2) is False

    # the panel shows the same schedule
    live = client.get(f"/api/admin/sessions/{cohort}/pacing").json()
    assert live["mode"] == "timed" and live["schedule"][1] == "2030-01-01T09:00:00.000Z"

    # and a player is held (the OPS-1 single-shot 'interval_seconds == 0 → +1' path is never taken)
    psid, headers = _join(client, cohort)
    assert _commit(client, psid, headers, 1).status_code == 201
    assert _commit(client, psid, headers, 2).status_code == 403

    for t in p.get("_timer_tasks", []):
        try:
            t.cancel()
        except Exception:
            pass


def test_wizard_scheduled_without_any_time_is_rejected(client, cohort):
    from admin_shared import _get_pacing
    r = _wizard_put(client, cohort, pacing_mode="scheduled", round_schedules={})
    assert r.status_code == 422, r.text
    assert _get_pacing(cohort)["unlocked_round"] == 999, "a rejected save must not change the live policy"


# ── free play / validation ─────────────────────────────────────────────────

def test_wizard_free_play_maps_to_free(client, cohort):
    from admin_shared import _get_pacing, is_round_unlocked
    _wizard_put(client, cohort, pacing_mode="manual", max_unlocked_round=1)
    r = _wizard_put(client, cohort, pacing_mode="free_play", max_unlocked_round=10, round_schedules=None)
    assert r.status_code == 200, r.text
    assert r.json()["mode"] == "free"
    assert _get_pacing(cohort)["mode"] == "free"
    assert is_round_unlocked(cohort, 9) is True
    # the session metadata still carries the wizard's own words (what the wizard re-reads)
    assert r.json()["pacing_mode"] == "free_play"


def test_wizard_unknown_mode_is_rejected(client, cohort):
    r = _wizard_put(client, cohort, pacing_mode="whenever")
    assert r.status_code == 422, r.text


# ── the one-call setup path ────────────────────────────────────────────────

def test_apply_setup_pacing_section_is_enforced_too(client, cohort):
    from admin_shared import _get_pacing, is_round_unlocked
    r = client.post(f"/api/admin/cohort/{cohort}/apply-setup",
                    json={"pacing": {"pacing_mode": "manual", "max_unlocked_round": 1}})
    assert r.status_code == 200, r.text
    sec = next(s for s in r.json()["sections"] if s["name"] == "Pacing")
    assert sec["status"] == "ok", sec
    assert _get_pacing(cohort)["mode"] == "manual"
    assert _get_pacing(cohort)["unlocked_round"] == 1
    assert is_round_unlocked(cohort, 2) is False


# ── source pin: the handler cannot drift back to writing the label alone ───

def test_save_cohort_pacing_goes_through_the_pacing_engine():
    import inspect
    import admin_router
    src = inspect.getsource(admin_router.save_cohort_pacing)
    assert "_enforce_wizard_pacing(" in src
    assert 'pacing["mode"] = body.get(' not in src, "the label-only write is back"
    helper = inspect.getsource(admin_router._enforce_wizard_pacing)
    assert "_apply_pacing(" in helper and "RoundPacingRequest(" in helper
