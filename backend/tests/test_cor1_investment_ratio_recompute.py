"""
COR-1 / TECH-2 regression tests.

The client-supplied investment_ratio is advisory only: commit_turn recomputes it
server-side from the ACTUAL committed spend as
    csf_pool = max(corporate_treasury * 0.20, 5_000_000)
    investment_ratio = clamp(capex_allocated / csf_pool, 0.0, 1.0)
so the ESG reward (gradated SLO/reputation growth + greenwashing detection) can no
longer be decoupled from real capex.

Observable: the engine echoes the (recomputed) average into the commit response
as events["greenwashing_avg_investment_ratio"].
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from main import app
from router import _commit_timestamps

client = TestClient(app)


def _solo():
    sid = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "COR1", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    return sid, bus


def _commit(sid, bus, ratio, capex, rnd=1):
    decs = [
        {
            "bu_id": b["bu_id"],
            "investment_ratio": ratio,
            "capex_allocated": capex,
            "choice_selected": "option_a",
        }
        for b in bus
    ]
    _commit_timestamps[sid] = 0.0
    return client.post(
        f"/api/simulations/{sid}/commit-turn",
        json={
            "decisions": decs,
            "dividends_paid": 0,
            "crisis_severity": 0,
            "imitation_decay_rate": 0.05,
            "force_override_cfo": True,
            "expected_round": rnd,
        },
    )


def test_gaming_ratio_is_neutralized():
    """investment_ratio=1.0 with capex=$1 must NOT be trusted: the recomputed
    average collapses to ~0 (well below the 0.15 ESG threshold)."""
    sid, bus = _solo()
    r = _commit(sid, bus, ratio=1.0, capex=1)
    assert r.status_code == 201, r.text
    avg = r.json()["events"]["greenwashing_avg_investment_ratio"]
    assert avg < 0.05, f"expected recomputed ~0, got {avg}"


def test_ratio_derived_from_capex_not_client_value():
    """The sent investment_ratio is ignored; a larger capex yields a larger
    recomputed ratio even when the client sends 0.0 for both."""
    sid_small, bus_small = _solo()
    r_small = _commit(sid_small, bus_small, ratio=0.0, capex=100_000)
    sid_big, bus_big = _solo()
    r_big = _commit(sid_big, bus_big, ratio=0.0, capex=2_000_000)
    assert r_small.status_code == 201 and r_big.status_code == 201
    avg_small = r_small.json()["events"]["greenwashing_avg_investment_ratio"]
    avg_big = r_big.json()["events"]["greenwashing_avg_investment_ratio"]
    # Sent ratio was 0.0 in both, yet the recomputed ratios track capex.
    assert avg_big > avg_small > 0.0, (avg_small, avg_big)


def test_ratio_never_exceeds_one():
    """Even a very large capex clamps the recomputed ratio to <= 1.0."""
    sid, bus = _solo()
    r = _commit(sid, bus, ratio=0.0, capex=10_000_000_000)
    assert r.status_code == 201, r.text
    avg = r.json()["events"]["greenwashing_avg_investment_ratio"]
    assert 0.0 <= avg <= 1.0
