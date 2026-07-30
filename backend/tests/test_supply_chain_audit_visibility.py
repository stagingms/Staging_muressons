"""A paid supply-chain audit must move the headline number immediately.

BUG-2026-07-30. `conduct_supply_chain_audit` raised each supplier's
`visibility` but left the AGGREGATE stale: `overall_visibility` and
`overall_risk` were only recomputed inside the round tick.

So a student spent up to $2,000,000, watched "Supply Chain Visibility" not
move at all, and only saw the benefit a round later. From the front of a
classroom that is indistinguishable from a broken button — and it actively
teaches the wrong lesson, since the whole point of the mechanic is that
disclosure costs money and buys visibility.

Measured before the fix:

    tier-1 supplier visibility   0.95  -> 0.975   (immediately)
    overall_visibility           0.482 -> 0.482   (unchanged!)
    ... then after the NEXT commit 0.645          (a round late)

The aggregate is now recomputed in the audit itself, with the same formula the
tick uses, so the two can never disagree.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="scaudit_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
        assert r.status_code == 200, r.text
        yield c


@pytest.fixture
def played_session(client):
    """A joined player one round in, so the supply-chain engine is initialised."""
    from rate_limit import _rate_buckets, _persistent_bans
    import router as _router
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "SCA-" + os.urandom(4).hex(),
                                "facilitator_id": "god_mode"}).json()["session_id"])
    _rate_buckets.clear()
    _persistent_bans.clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    ps = str(client.post(f"/api/simulations/public/sessions/{sid}/join",
                         json={"player_id": g["player_id"], "password": g["password"]}
                         ).json()["session_id"])
    hdr = {"X-Player-Id": g["player_id"]}
    _router._commit_timestamps.clear()
    dash = client.get(f"/api/simulations/{ps}/dashboard", headers=hdr).json()
    bus = dash.get("business_units") or []
    decisions = [{"bu_id": b["bu_id"], "capex_allocated": 2_000_000,
                  "choice_selected": "option_b", "investment_ratio": 0.2} for b in bus]
    client.post(f"/api/simulations/{ps}/commit-turn",
                json={"decisions": decisions, "expected_round": 1}, headers=hdr)
    return ps, hdr


def _visibility(client, ps, hdr):
    sc = client.get(f"/api/simulations/{ps}/supply-chain", headers=hdr).json()
    return (sc.get("supply_chain") or {}).get("overall_visibility")


def test_audit_raises_overall_visibility_immediately(client, played_session):
    ps, hdr = played_session
    before = _visibility(client, ps, hdr)
    assert before is not None, "supply-chain engine did not initialise"

    r = client.post(f"/api/simulations/{ps}/supply-chain-audit",
                    json={"audit_depth": 2}, headers=hdr)
    assert r.status_code == 200, r.text

    after = _visibility(client, ps, hdr)
    assert after > before, (
        f"visibility did not move ({before} -> {after}). The student paid for "
        "the audit and the headline metric ignored it until the next round."
    )


def test_audit_response_reports_the_new_aggregate(client, played_session):
    """The endpoint returns it too, so the UI need not re-fetch to show payoff."""
    ps, hdr = played_session
    before = _visibility(client, ps, hdr)
    body = client.post(f"/api/simulations/{ps}/supply-chain-audit",
                       json={"audit_depth": 2}, headers=hdr).json()
    assert "overall_visibility" in body
    assert body["overall_visibility"] > before


def test_aggregate_matches_the_tick_formula(client, played_session):
    """The audit and the round tick must not compute this differently — that
    disagreement is what produced the stale value in the first place."""
    ps, hdr = played_session
    client.post(f"/api/simulations/{ps}/supply-chain-audit",
                json={"audit_depth": 3}, headers=hdr)
    sc = (client.get(f"/api/simulations/{ps}/supply-chain", headers=hdr).json()
          .get("supply_chain") or {})
    suppliers = (sc.get("tier_1_suppliers", []) + sc.get("tier_2_suppliers", [])
                 + sc.get("tier_3_suppliers", []))
    assert suppliers
    expected = round(sum(s["visibility"] for s in suppliers) / len(suppliers), 3)
    assert abs(sc["overall_visibility"] - expected) < 0.002


def test_deeper_audit_buys_more_visibility(client, played_session):
    """Tier depth is the cost/benefit lever; if depth 3 did not beat depth 1 the
    pricing would be teaching a false trade-off."""
    ps, hdr = played_session
    client.post(f"/api/simulations/{ps}/supply-chain-audit",
                json={"audit_depth": 1}, headers=hdr)
    shallow = _visibility(client, ps, hdr)
    client.post(f"/api/simulations/{ps}/supply-chain-audit",
                json={"audit_depth": 3}, headers=hdr)
    deep = _visibility(client, ps, hdr)
    assert deep > shallow, f"depth 3 ({deep}) did not exceed depth 1 ({shallow})"
