"""
Turnaround Module — P3: engine + orchestration.

Engine (turnaround_engine) unit tests cover the arc mechanics end-to-end:
  6. Deliberate entry — enter_arc drops into Crisis + applies the $3M bailout.
  7. Graduation — a disciplined path reaches Exit; amended M_R = base + 0.10.
  8. Expiry — a treasury-only path stalls; amended M_R clamped at last phase cap.
  9. Cap enforcement — a run stuck in Crisis is clamped to the 0.60 cap.
 10. Abort — restores the completed state; canonical is untouched throughout.
Plus orchestration-endpoint auth (require_sim_manager + ownership + module gate).
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from admin_shared import _god_mode_settings
import turnaround_engine as te

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}
_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}
_REASON = {"reason": "P3 test"}


def _client(creds):
    c = TestClient(app)
    r = c.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return c


def _distressed_gs(base_mr=0.7, treasury=-2_000_000, rep=18):
    return {
        "corporate_treasury": treasury,
        "group_reputation": rep,
        "game_over": True,
        "round_number": 10,
        "final_report_canonical": {"regenerative_multiple": base_mr},
        "active_event_flags": {},
    }


@pytest.fixture(autouse=True)
def _reset():
    e = _god_mode_settings.get("turnaround_module_enabled", False)
    p = dict(_god_mode_settings.get("turnaround_facilitator_permissions", {}))
    yield
    _god_mode_settings["turnaround_module_enabled"] = e
    _god_mode_settings["turnaround_facilitator_permissions"] = p


# ── 6. Deliberate entry ──────────────────────────────────────────

def test_enter_arc_crisis_and_bailout():
    gs = _distressed_gs()
    r = te.enter_arc(gs, [])
    assert r["phase"] == "crisis" and r["turnaround_round"] == 1
    assert r["bailout_applied"] == 3_000_000
    assert gs["turnaround_mode"] is True
    assert gs["corporate_treasury"] == 1_000_000  # -2M + 3M bailout
    assert gs["active_event_flags"]["turnaround_phase"] == "crisis"


# ── 7. Graduation ────────────────────────────────────────────────

def test_graduation_path():
    gs = _distressed_gs(base_mr=0.7)
    te.enter_arc(gs, [])
    result = None
    for _ in range(4):
        result = te.apply_commit(gs, [], "option_a")
        if result["arc_complete"]:
            break
    assert result["graduated"] is True
    rep = gs["turnaround_amended_report"]
    assert rep["graduated"] is True
    assert rep["regenerative_multiple"] == pytest.approx(0.8, abs=1e-6)  # 0.7 + 0.10
    # Graduation lifts the survival clamp — archetype climbs out of the relic band.
    assert rep["archetype"] != "stranded_relic"
    # Canonical untouched.
    assert gs["final_report_canonical"] == {"regenerative_multiple": 0.7}
    assert gs["turnaround_mode"] is False and gs["game_over"] is True


# ── 8. Expiry ────────────────────────────────────────────────────

def test_expiry_path_clamps_at_phase_cap():
    gs = _distressed_gs(base_mr=0.7)
    te.enter_arc(gs, [])
    result = None
    for _ in range(4):
        result = te.apply_commit(gs, [], "option_c")  # treasury-only, trust-light
    assert result["arc_complete"] is True and result["graduated"] is False
    rep = gs["turnaround_amended_report"]
    assert rep["graduated"] is False
    # Stalls in stabilisation (cap 0.80); base 0.7 < cap so amended stays 0.7.
    assert rep["regenerative_multiple"] == pytest.approx(0.7, abs=1e-6)
    assert gs["final_report_canonical"] == {"regenerative_multiple": 0.7}


# ── 9. Cap enforcement (stuck in Crisis → 0.60) ──────────────────

def test_cap_enforcement_crisis_floor():
    # Never clear the first gate (rep stays <=20): amended M_R clamps at 0.60
    # even though the base M_R is higher.
    gs = _distressed_gs(base_mr=0.75, treasury=-2_000_000, rep=0)
    te.enter_arc(gs, [])
    gs["group_reputation"] = 0  # force reputation floor so no gate ever clears
    result = None
    for _ in range(4):
        gs["group_reputation"] = 0
        result = te.apply_commit(gs, [], "option_c")
    assert result["phase"] == "crisis"  # never left Crisis
    rep = gs["turnaround_amended_report"]
    assert rep["regenerative_multiple"] == pytest.approx(0.60, abs=1e-6)


# ── 10. Abort ────────────────────────────────────────────────────

def test_abort_restores_completion():
    gs = _distressed_gs(base_mr=0.7)
    te.enter_arc(gs, [])
    te.apply_commit(gs, [], "option_a")
    out = te.abort_arc(gs)
    assert gs["turnaround_mode"] is False and gs["game_over"] is True
    assert gs["active_event_flags"]["turnaround_status"] == "aborted"
    assert "turnaround_amended_report" not in gs
    assert gs["final_report_canonical"] == {"regenerative_multiple": 0.7}
    assert out["canonical"] == {"regenerative_multiple": 0.7}


# ── Arc state helper ─────────────────────────────────────────────

def test_arc_state_shape():
    gs = _distressed_gs()
    assert te.arc_state(gs)["active"] is False
    te.enter_arc(gs, [])
    st = te.arc_state(gs)
    assert st["active"] is True and st["phase"] == "crisis"
    assert st["turnaround_round"] == 1 and st["max_rounds"] == 4
    assert st["config"]["title"].startswith("T1")


# ── Orchestration endpoint auth ──────────────────────────────────

def test_open_excludes_project_admin():
    pa = _client(_PA)
    r = pa.post("/api/admin/turnaround/whatever/open")
    assert r.status_code == 403, r.text


def test_open_404_for_missing_session():
    gm = _client(_GOD)
    gm.put("/api/admin/turnaround/global", json={"enabled": True, **_REASON})
    r = gm.post("/api/admin/turnaround/does-not-exist/open")
    assert r.status_code == 404, r.text


def test_open_blocked_when_module_disabled():
    gm = _client(_GOD)
    gm.put("/api/admin/turnaround/global", json={"enabled": False, **_REASON})
    r = gm.post("/api/admin/turnaround/any-session/open")
    assert r.status_code == 403, r.text
