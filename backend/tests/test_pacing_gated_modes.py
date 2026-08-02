"""Entering a gated pacing mode must actually close the gate. 2026-08-02.

Reported: "the manual mode was implemented but not working" — the Round
Pacing panel showed MODE 🖐 Manual next to UNLOCKED UP TO Round ∞, and teams
kept advancing on their own.

THE DEFECT
----------
Both gated branches of POST /sessions/{id}/pacing did:

    pacing["unlocked_round"] = max(pacing["unlocked_round"], 1)

which can only RAISE a ceiling, never lower one. Every cohort starts at the
free-play sentinel 999 (the _get_pacing default, and what "free" mode and
"Unlock all rounds" both write), so switching to Manual computed
max(999, 1) = 999 and left every round open. The badge said Manual; nothing
was gated. Scheduled/timed carried the identical line, so BOTH gated modes
had never worked on any cohort — the bug was total, not intermittent.

The gate itself (is_round_unlocked) was always correct; only the ceiling
written at the mode switch was wrong.
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
                    json={"cohort_name": "PacingGate", "facilitator_id": "god_mode"})
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


# ── the ceiling actually closes ────────────────────────────────────────────

@pytest.mark.parametrize("mode", ["manual", "timed"])
def test_entering_a_gated_mode_clamps_the_free_play_ceiling(client, cohort, mode):
    """THE bug: 999 survived the switch, so nothing was gated."""
    from admin_shared import _get_pacing, is_round_unlocked

    assert _get_pacing(cohort)["unlocked_round"] == 999, "precondition: starts at the sentinel"
    body = {"mode": mode}
    if mode == "timed":
        body["interval_seconds"] = 300
    assert client.post(f"/api/admin/sessions/{cohort}/pacing", json=body).status_code == 200

    p = _get_pacing(cohort)
    assert p["mode"] == mode
    assert p["unlocked_round"] <= 10, f"ceiling stayed at {p['unlocked_round']} — mode gates nothing"
    assert is_round_unlocked(cohort, 1) is True, "the round in progress must stay playable"
    assert is_round_unlocked(cohort, 2) is False, "the NEXT round must not be open"


def test_free_mode_still_opens_everything(client, cohort):
    from admin_shared import is_round_unlocked
    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})
    assert client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "free"}).status_code == 200
    assert is_round_unlocked(cohort, 9) is True


def test_a_deliberate_ceiling_is_not_silently_revoked(client, cohort):
    """Re-applying a mode must not take back rounds a class was told are open:
    only the free-play sentinel is treated as 'not a deliberate gate'."""
    from admin_shared import _get_pacing
    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})
    # facilitator opens two more rounds by hand
    client.post(f"/api/admin/sessions/{cohort}/pacing/unlock")
    client.post(f"/api/admin/sessions/{cohort}/pacing/unlock")
    opened = _get_pacing(cohort)["unlocked_round"]
    assert opened == 3

    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})
    assert _get_pacing(cohort)["unlocked_round"] == opened, "re-applying manual revoked open rounds"


# ── end to end: a real player is actually held ─────────────────────────────

def test_manual_pacing_holds_a_player_until_the_facilitator_advances(client, cohort):
    """The behaviour the mode promises: 'teams commit whenever they are ready;
    the next round opens only when you advance it'."""
    psid, headers = _join(client, cohort)
    assert client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"}).status_code == 200

    # the current round is playable
    assert _commit(client, psid, headers, 1).status_code == 201

    # …but the next one is not
    blocked = _commit(client, psid, headers, 2)
    assert blocked.status_code == 403, f"round 2 was NOT gated: {blocked.status_code}"
    assert "locked" in blocked.json()["detail"].lower()

    # the facilitator releases it
    assert client.post(f"/api/admin/sessions/{cohort}/pacing/unlock").status_code == 200
    assert _commit(client, psid, headers, 2).status_code == 201


def test_unlock_all_then_manual_re_closes_the_gate(client, cohort):
    """The exact screenshot state: MODE Manual with UNLOCKED UP TO Round ∞,
    reached by having pressed 'All rounds unlocked' at some point."""
    from admin_shared import _get_pacing, is_round_unlocked
    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "free"})
    assert _get_pacing(cohort)["unlocked_round"] == 999

    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})
    assert is_round_unlocked(cohort, 2) is False, \
        "Manual after Unlock-All still left every round open — the reported bug"


# ── tripwire on the shape that caused it ───────────────────────────────────

def test_no_gated_branch_uses_a_raise_only_ceiling():
    """`max(existing, 1)` can only raise a ceiling. Against a default of 999
    that is a no-op, which is precisely why the modes silently did nothing."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    i = src.index('if body.mode == "free":')
    block = src[i:i + 1200]
    assert 'max(pacing["unlocked_round"], 1)' not in block, \
        "a gated branch is back to a raise-only ceiling — the mode will gate nothing"
