"""SEAM-12 (audit 2026-09-04, Wave 3): "peer benchmarking" percentiles and the
"cohort average" spanned every session on the server — cohort shells, solo runs,
other cohorts, test runs (a 3-team cohort reported player_count 55 and a cohort
average treasury of −$67M). The peer set is the cohort's team sessions.
"""
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from test_answer_key_leaks import client, _login_god, _cohort, _player, _player_headers, _anon  # noqa: E402,F401


def test_percentiles_are_against_the_cohort_s_teams_only(client):
    _login_god(client)
    cohort_a = _cohort(client, "PeerScopeA")
    cohort_b = _cohort(client, "PeerScopeB")
    a1_sid, a1_pid, a1_tok = _player(client, cohort_a)
    a2_sid, _, _ = _player(client, cohort_a)
    for _ in range(3):
        _player(client, cohort_b)                      # a second, bigger cohort on the same server
    # and a solo session, which used to join everyone's peer set
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    solo = _anon(client).post("/api/simulations/solo-start", json={"player_name": "S", "decision_paradigm": "legacy_abc"})
    assert solo.status_code in (200, 201), solo.text[:200]
    solo_sid = solo.json()["session_id"]

    r = client.get(f"/api/admin/analytics/player/{a1_sid}")
    assert r.status_code == 200, r.text[:200]
    pb = r.json()["peer_benchmarking"]
    assert pb["player_count"] == 2 and pb["peer_scope"] == "cohort" and pb["cohort_id"] == cohort_a
    # the solo session's peer set is itself
    rs = client.get(f"/api/admin/analytics/player/{solo_sid}")
    assert rs.status_code == 200, rs.text[:200]
    ps = rs.json()["peer_benchmarking"]
    assert ps["player_count"] == 1 and ps["peer_scope"] == "solo"
    # a team reading its own panel sees the same scoped count
    rp = _anon(client).get(f"/api/admin/analytics/player/{a1_sid}", headers=_player_headers(a1_pid, a1_tok))
    assert rp.status_code == 200 and rp.json()["peer_benchmarking"]["player_count"] == 2
