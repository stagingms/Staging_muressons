"""G08 (AUDIT_Engines_Flow_Classroom50_20260909; EVAL §2: "Board API permits
catalogue IDs without timing checks" — owner-bound, no UI caller, guard when
convenient) — the board-vote endpoint accepts a resolution only while it is
on the table, and only once.

Before: any catalogue id could be voted in any round, as often as the
caller liked; each passed vote credited the reputation impact and charged
the cost again.
"""
import os
os.environ["USE_MEMORY_DB"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from router import _commit_timestamps

client = TestClient(app)


def _solo(name):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    r = client.post("/api/simulations/solo-start", json={"player_name": name, "decision_paradigm": "legacy_abc"})
    assert r.status_code == 201, r.text
    return r.json()["session_id"]


def _advance_to(sid, target_round):
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    rnd = client.get(f"/api/simulations/{sid}/dashboard").json()["current_round"]
    while rnd < target_round:
        _commit_timestamps.pop(sid, None)
        r = client.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": 1_000_000.0,
                           "choice_selected": "option_a"} for b in bus],
            "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, r.text[:300]
        bus = r.json().get("business_units") or bus
        rnd = r.json()["new_round_number"]
    return rnd


def _vote(sid, resolution_id, recommendation="support"):
    return client.post(f"/api/simulations/{sid}/board-vote",
                       json={"resolution_id": resolution_id, "recommendation": recommendation})


def _board(sid):
    return client.get(f"/api/simulations/{sid}/board-governance").json()["board_governance"]


def test_a_resolution_is_not_on_the_table_before_its_round():
    sid = _solo("BV-early")
    assert _advance_to(sid, 2) == 2              # the board exists after the first commit
    r = _vote(sid, "climate_disclosure")          # tabled R3
    assert r.status_code == 409, r.text
    assert r.json()["detail"]["code"] == "resolution_not_on_the_table"
    assert r.json()["detail"]["tabled_round"] == 3 and r.json()["detail"]["current_round"] == 2
    r = _vote(sid, "nature_positive")             # tabled R6
    assert r.status_code == 409


def test_a_resolution_is_voted_once_in_its_window_and_the_impact_lands_once():
    sid = _solo("BV-once")
    assert _advance_to(sid, 3) == 3
    before = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    r = _vote(sid, "climate_disclosure")
    assert r.status_code == 200, r.text
    body = r.json()
    after = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    if body["passed"]:
        assert after["corporate_treasury"] == pytest.approx(before["corporate_treasury"] - body["cost"])
        assert after["group_reputation"] == pytest.approx(min(100, before["group_reputation"] + body["impact"]["reputation"]))
    else:
        assert after["corporate_treasury"] == pytest.approx(before["corporate_treasury"])
    assert _board(sid)["resolutions_voted"]["climate_disclosure"]["round"] == 3
    # the second vote is refused and moves nothing
    r2 = _vote(sid, "climate_disclosure", "oppose")
    assert r2.status_code == 409 and r2.json()["detail"]["code"] == "resolution_already_voted"
    again = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    assert again["corporate_treasury"] == pytest.approx(after["corporate_treasury"])
    assert again["group_reputation"] == pytest.approx(after["group_reputation"])


def test_the_window_is_the_tabled_round_and_the_next_then_it_closes():
    sid = _solo("BV-window")
    assert _advance_to(sid, 4) == 4
    assert _vote(sid, "exec_esg_pay").status_code == 200          # tabled R3, still on the table in R4
    assert _advance_to(sid, 5) == 5
    r = _vote(sid, "climate_disclosure")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "resolution_not_on_the_table"


def test_bad_inputs():
    sid = _solo("BV-bad")
    assert _advance_to(sid, 2) == 2
    assert _vote(sid, "no_such_resolution").status_code == 404
    assert _vote(sid, "climate_disclosure", "abstain").status_code == 400
