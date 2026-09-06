"""FLOW-08, FLOW-10 (audit 2026-09-04, Wave 3).

FLOW-08  A tab running a pre-2026-08-02 bundle (no expected_round) could
         double-commit after a lost response (probe B3: a stale re-post after the
         cooldown ADVANCED the round again). expected_round is required at the
         gate by default now; the server's own auto-commit sends it.
FLOW-10  A facilitator / god-mode freeze was a 503 the client read as "server
         busy" and retried. The detail carries code "frozen".
FLOW-07 and FLOW-11 were closed by WP-26 (reset copy + password-version bump)
and the RunBar target_round; pinned here.
"""
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    with TestClient(app) as c:
        yield c


def _solo(client, name):
    from router import _commit_timestamps
    r = client.post("/api/simulations/solo-start", json={"player_name": name, "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps.pop(sid, None)
    return sid, bus


def _decisions(bus):
    return [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": 1.0, "choice_selected": "option_b"} for b in bus]


def test_a_commit_without_expected_round_is_refused_with_a_refresh_message(client, monkeypatch):
    monkeypatch.delenv("REQUIRE_EXPECTED_ROUND", raising=False)
    sid, bus = _solo(client, "F08")
    r = client.post(f"/api/simulations/{sid}/commit-turn", json={"decisions": _decisions(bus), "force_override_cfo": True})
    assert r.status_code == 400, r.text[:200]
    assert "Refresh the page" in r.json()["detail"]
    # the round did not move
    assert client.get(f"/api/simulations/{sid}/dashboard").json()["current_round"] == 1
    # the current client's shape commits
    from router import _commit_timestamps
    _commit_timestamps.pop(sid, None)
    r2 = client.post(f"/api/simulations/{sid}/commit-turn", json={"decisions": _decisions(bus), "force_override_cfo": True, "expected_round": 1})
    assert r2.status_code == 201, r2.text[:200]
    # the escape hatch restores warning-only mode
    monkeypatch.setenv("REQUIRE_EXPECTED_ROUND", "false")
    _commit_timestamps.pop(sid, None)
    r3 = client.post(f"/api/simulations/{sid}/commit-turn", json={"decisions": _decisions(bus), "force_override_cfo": True})
    assert r3.status_code == 201, r3.text[:200]


def test_the_server_s_own_auto_commit_carries_the_round():
    from router import _auto_commit_request
    body = _auto_commit_request({"corporate_treasury": 5e7, "saved_allocations": {}}, [{"bu_id": "pharma"}], 4)
    assert body.expected_round == 4


def test_a_freeze_is_a_coded_503_not_a_busy_server(client):
    import admin_shared
    sid, bus = _solo(client, "F10")
    admin_shared._god_mode_settings["system_frozen"] = True
    try:
        r = client.post(f"/api/simulations/{sid}/commit-turn", json={"decisions": _decisions(bus), "force_override_cfo": True, "expected_round": 1})
    finally:
        admin_shared._god_mode_settings["system_frozen"] = False
    assert r.status_code == 503
    d = r.json()["detail"]
    assert d["code"] == "frozen" and d["scope"] == "system" and "facilitator" in d["message"]


def test_reset_password_copy_and_the_run_bar_advance_are_the_wp26_shapes():
    root = _BACKEND_DIR.parent / "frontend" / "app" / "components"
    reg = (root / "PlayerRegistry.js").read_text(encoding="utf-8")
    assert "A new random password will be generated" not in reg
    assert "returns to the default (ID@123)" in reg and "must set a personal one" in reg
    runbar = (root / "RunBar.js").read_text(encoding="utf-8")
    assert "body: JSON.stringify({ target_round: nextRound })" in runbar
