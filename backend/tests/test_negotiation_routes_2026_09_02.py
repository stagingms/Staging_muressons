"""Negotiation Room HTTP routes — accept / walk-out / close-on-commit.

The deal engine in negotiation.py was well covered (test_negotiation_rooms.py),
but two of the four endpoints the frontend (NegotiationRoom.js) calls were never
implemented in router.py: POST /negotiation/accept and POST /negotiation/walk-out.
So a player could open a room (paying the $250k entry fee) and talk, but the
Accept button — accept_concession() is "THE only path to state" — and the
Walk-out button both 404'd, and an open room could only leak until the round
committed (close_on_commit() had no caller either).

These tests drive the REAL HTTP layer so the routes can never silently vanish
again, and pin the frontend/backend contract that their absence violated.
"""
import os
import re
import pathlib

os.environ.setdefault("USE_MEMORY_DB", "true")

from fastapi.testclient import TestClient

import router
import database_memory as dm
from main import app
from autonomous_agents import create_initial_agent_state

MASTER = {"password": os.environ.get("MASTER_PASSWORD", "sim2026@iim")}
_FRONTEND = pathlib.Path(__file__).resolve().parents[2] / "frontend"


def _clear_rl():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def _god():
    c = TestClient(app)
    _clear_rl()
    assert c.post("/api/admin/facilitators/login",
                  json={"facilitator_id": "god_mode", **MASTER}).status_code == 200
    return c


def _cohort_and_player(name):
    """god_mode cohort + one inducted player who has set a personal password.
    Returns (client, player_session_id, player_id, headers)."""
    god = _god()
    sid = god.post("/api/simulations/start", json={
        "cohort_name": name, "facilitator_id": "god_mode", "decision_paradigm": "legacy_abc",
    }).json()["session_id"]
    _clear_rl()
    g = god.post(f"/api/admin/{sid}/generate-player").json()
    pid, defpw = g["player_id"], g["password"]
    _clear_rl()
    j = god.post("/api/simulations/player-login", json={"player_id": pid, "password": defpw}).json()
    psid = j["session_id"]
    _clear_rl()
    god.post("/api/simulations/change-password",
             json={"player_id": pid, "old_password": defpw, "new_password": "NegRoute#2026x"})
    _clear_rl()
    j2 = god.post("/api/simulations/player-login",
                  json={"player_id": pid, "password": "NegRoute#2026x"}).json()
    tok = j2.get("player_token") or j2.get("token")
    hdr = {"X-Player-Id": pid}
    if tok:
        hdr["X-Player-Token"] = tok
    return god, psid, pid, hdr


def _make_hostile(psid, agent="the_regulator", tol=12.0):
    row = dm._global_states[psid][-1]
    aa = row.get("autonomous_agents") or create_initial_agent_state()
    aa["agents"][agent]["escalation_stage"] = "hostile"
    aa["agents"][agent]["tolerance"] = tol
    row["autonomous_agents"] = aa


def _neg(client, psid, path, hdr, body=None):
    return client.post(f"/api/simulations/{psid}/negotiation{path}", json=body or {}, headers=hdr)


# ── the two routes that used to 404 ──────────────────────────────────────────

def test_accept_route_exists_and_applies_a_concession():
    """Regression: POST /negotiation/accept was missing → the Accept button
    404'd and a paid-for meeting could never produce a deal."""
    client, psid, pid, hdr = _cohort_and_player("NegAcceptCohort")
    _make_hostile(psid, "the_regulator")

    opened = _neg(client, psid, "/open", hdr, {"agent_id": "the_regulator"})
    assert opened.status_code == 200, opened.text
    menu_ids = {m["id"] for m in opened.json()["menu"]}
    assert "governance_audit" in menu_ids  # on the regulator's menu

    t_before = dm._global_states[psid][-1]["corporate_treasury"]
    gov_before = min(b["governance_risk_score"] for b in dm._global_states[psid][-1]["bu_states"]) \
        if dm._global_states[psid][-1].get("bu_states") else None

    r = _neg(client, psid, "/accept", hdr, {"concession_id": "governance_audit"})
    assert r.status_code == 200, r.text            # NOT 404
    deal = r.json()["deal"]
    assert deal["concession_id"] == "governance_audit"

    # State actually moved and PERSISTED: treasury paid the priced cost, and the
    # audit's immediate governance-risk relief landed on the BUs.
    row = dm._global_states[psid][-1]
    assert row["corporate_treasury"] == round(t_before - deal["cost_paid"], 2)
    if gov_before is not None:
        assert min(b["governance_risk_score"] for b in row["bu_states"]) < gov_before


def test_accept_off_menu_concession_is_a_clean_400_not_404_or_500():
    client, psid, pid, hdr = _cohort_and_player("NegOffMenuCohort")
    _make_hostile(psid, "the_regulator")
    assert _neg(client, psid, "/open", hdr, {"agent_id": "the_regulator"}).status_code == 200
    # wellbeing_program is the gen-z employee's concession, not the regulator's
    r = _neg(client, psid, "/accept", hdr, {"concession_id": "wellbeing_program"})
    assert r.status_code == 400, r.text
    assert r.json()["detail"]["error"] == "not_on_this_agents_menu"


def test_walkout_route_exists_and_closes_the_room():
    """Regression: POST /negotiation/walk-out was missing → the Walk-out button
    404'd and the room could only leak open until the round committed."""
    client, psid, pid, hdr = _cohort_and_player("NegWalkoutCohort")
    _make_hostile(psid, "the_regulator")
    assert _neg(client, psid, "/open", hdr, {"agent_id": "the_regulator"}).status_code == 200

    r = _neg(client, psid, "/walk-out", hdr)
    assert r.status_code == 200, r.text            # NOT 404
    assert r.json()["closed"]["status"] == "closed"
    assert r.json()["closed"]["resolution"] == "walk_out"

    # Room is really gone: a follow-up /say has nothing open to talk to.
    say = _neg(client, psid, "/say", hdr, {"text": "still there?"})
    assert say.status_code == 400
    assert say.json()["detail"]["error"] == "no_open_room"


# ── close-on-commit wiring ───────────────────────────────────────────────────

def test_committing_a_round_auto_closes_an_open_room():
    """A room never outlives its round: committing with a room still open must
    auto-close it (close_on_commit), not carry it into the next round."""
    client, psid, pid, hdr = _cohort_and_player("NegCommitCloseCohort")
    _make_hostile(psid, "the_regulator")
    assert _neg(client, psid, "/open", hdr, {"agent_id": "the_regulator"}).status_code == 200

    from negotiation import get_negotiation_log
    assert get_negotiation_log(dm._global_states[psid][-1]).get("active") is not None

    bus = client.get(f"/api/simulations/{psid}/dashboard", headers=hdr).json()["business_units"]
    router._commit_timestamps[psid] = 0.0
    body = {"decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.1,
                           "capex_allocated": 1, "choice_selected": "option_b"} for b in bus],
            "dividends_paid": 0}
    r = client.post(f"/api/simulations/{psid}/commit-turn", json=body, headers=hdr)
    assert r.status_code in (200, 201), r.text

    log = get_negotiation_log(dm._global_states[psid][-1])
    assert log.get("active") is None, "the open room should have been auto-closed on commit"
    assert any(room.get("resolution") == "round_committed" for room in log.get("history", []))


# ── frontend / backend contract tripwire ─────────────────────────────────────

def test_every_negotiation_path_the_frontend_calls_has_a_backend_route():
    """The bug that started this: NegotiationRoom.js POSTed to /open, /say,
    /accept and /walk-out, but only /open and /say existed. Pin the contract so
    a frontend call can never again reach a route that isn't registered."""
    src = (_FRONTEND / "app" / "components" / "NegotiationRoom.js").read_text(encoding="utf-8")
    called = set(re.findall(r"call\(\s*'(/[a-z\-]+)'", src))
    assert {"/open", "/say", "/accept", "/walk-out"} <= called, (
        f"expected the four negotiation calls in NegotiationRoom.js, found {called}")

    # The app wraps includes in a custom _IncludedRouter, so app.routes is not
    # walkable — enumerate the simulations router itself (its APIRoute paths
    # already carry the /api/simulations prefix).
    from router import router as sim_router
    registered = {r.path for r in sim_router.routes
                  if "/negotiation" in getattr(r, "path", "")}
    for p in called:
        full = f"/api/simulations/{{session_id}}/negotiation{p}"
        assert full in registered, f"frontend calls {p} but no backend route {full} is registered"
