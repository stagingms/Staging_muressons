"""Audit #4 — commit-turn input validation hardening.

Two gaps the audit flagged:
  • an UNKNOWN/foreign bu_id in the decisions list slipped past the existing
    "missing BU" check and reached the engine, and
  • the decisions list was unbounded (a crafted request could submit an
    arbitrarily large array to amplify engine CPU/memory).

These tests pin both. Legitimate play (exact set of the session's BUs) is
unaffected; only foreign ids / oversized lists are rejected.
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
        json={"player_name": "VAL", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    return sid, bus


def _decision(bu_id):
    return {
        "bu_id": bu_id,
        "investment_ratio": 0.5,
        "capex_allocated": 1_000_000,
        "choice_selected": "option_a",
    }


def _post(sid, decisions, rnd=1):
    _commit_timestamps[sid] = 0.0
    return client.post(
        f"/api/simulations/{sid}/commit-turn",
        json={"decisions": decisions, "force_override_cfo": True, "expected_round": rnd},
    )


def test_valid_decisions_still_commit():
    """The exact set of the session's BUs must still be accepted (no regression)."""
    sid, bus = _solo()
    r = _post(sid, [_decision(b["bu_id"]) for b in bus])
    assert r.status_code == 201, r.text


def test_unknown_bu_id_is_rejected():
    """All real BUs present PLUS a foreign bu_id → 400 (would previously slip
    through because the 'missing' check only requires the real ones)."""
    sid, bus = _solo()
    decisions = [_decision(b["bu_id"]) for b in bus] + [_decision("BU-DOES-NOT-EXIST")]
    r = _post(sid, decisions)
    assert r.status_code == 400, r.text
    assert "Unknown BU" in r.text


def test_oversized_decisions_list_is_rejected():
    """> max_length (64) decisions → 422 from Pydantic before any engine work."""
    sid, bus = _solo()
    huge = [_decision(f"BU-{i}") for i in range(100)]
    r = _post(sid, huge)
    assert r.status_code == 422, r.text
