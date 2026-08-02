"""Cohort Trends comparison must produce data for EVERY cohort size.

Reported: "there is no comparative graph giving competitors or cohort averages
against the player's performance — the toggle switch does not work."

The toggle was wired correctly. /peer-trend-history simply never returned
usable data, for two independent reasons — so the switch flipped and nothing
was ever drawn:

  1. SINGLE-TEAM COHORT — the synthetic AI benchmark was gated on
     `not parent_id`, i.e. solo sessions only. A cohort that happened to hold
     one team fell through to the multiplayer branch, found no siblings, and
     returned available=False. One team is the normal case when piloting or
     running a small class.

  2. MULTI-TEAM COHORT — the peer branch read `_sessions`, an UNDEFINED NAME
     (pyflakes flags it on the committed file). Every 2+ team cohort raised
     NameError before returning. Pre-existing, and invisible because case 1
     short-circuited before reaching it in small cohorts.

Together those two covered every possible cohort size.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="peertrend_")
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


def _cohort_with(client, name, n_players):
    import database_memory as dm
    from rate_limit import _rate_buckets, _persistent_bans
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": name, "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    for _ in range(n_players):
        _rate_buckets.clear(); _persistent_bans.clear()
        g = client.post(f"/api/admin/{sid}/generate-player").json()
        client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]})
    kids = [s for s, v in dm._sessions.items() if v.get("parent_cohort_id") == sid]
    return sid, kids


def test_solo_session_gets_ai_benchmark(client):
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "PT-Solo", "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    d = client.get(f"/api/simulations/{sid}/peer-trend-history").json()
    assert d["available"] is True
    assert d["ai_benchmark"] is True
    assert d["rounds"], "an available benchmark with no rounds draws nothing"


def test_single_team_cohort_gets_ai_benchmark(client):
    """Defect #1. A one-team cohort must still get a comparison line."""
    _, kids = _cohort_with(client, "PT-One", 1)
    d = client.get(f"/api/simulations/{kids[0]}/peer-trend-history").json()
    assert d["available"] is True, (
        f"one-team cohort returned unavailable ({d.get('reason')}) — the "
        "Cohort Trends toggle would flip and draw nothing"
    )
    assert d["ai_benchmark"] is True
    assert d["rounds"]


def test_multi_team_cohort_uses_real_peers_not_the_fallback(client):
    """Defect #2. This path raised NameError on `_sessions` before returning."""
    _, kids = _cohort_with(client, "PT-Three", 3)
    d = client.get(f"/api/simulations/{kids[0]}/peer-trend-history").json()
    assert d["available"] is True
    assert d.get("ai_benchmark", False) is False, \
        "a cohort with real peers must not fall back to synthetic benchmarks"
    assert d["peerCount"] == 2, "should average the OTHER two teams"
    assert d["rounds"]


def test_peer_rounds_carry_the_series_the_charts_plot(client):
    """The charts read avgCI / tco2e / ebitda / rep plus a per-peer list."""
    _, kids = _cohort_with(client, "PT-Series", 2)
    d = client.get(f"/api/simulations/{kids[0]}/peer-trend-history").json()
    first = d["rounds"][0]
    for key in ("round", "avgCI", "tco2e", "ebitda", "rep", "peers"):
        assert key in first, f"round entry missing {key}"
    assert isinstance(first["peers"], list) and first["peers"]
    for peer in first["peers"]:
        assert peer.get("name"), "peer needs a display name for the chart legend"


def test_router_has_no_undefined_names():
    """`_sessions` was undefined in the peer branch and only exploded at
    runtime. Keep the module clean so the next one fails in CI instead."""
    import subprocess
    import sys
    backend = pathlib.Path(__file__).resolve().parents[1]
    out = subprocess.run([sys.executable, "-m", "pyflakes", str(backend / "router.py")],
                         capture_output=True, text=True, timeout=120)
    undefined = [l for l in (out.stdout + out.stderr).splitlines() if "undefined name" in l]
    assert not undefined, "undefined names in router.py: " + "; ".join(undefined)
