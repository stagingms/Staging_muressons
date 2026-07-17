"""
Turnaround Module — P2: completion snapshot + eligibility.

Pins (PLAN_Turnaround_Module_Implementation.md §3, WS-C):
  4. Eligibility threshold — canonical M_R 0.79 eligible, 0.80 not.
  5. Completion invariant — the canonical R10 snapshot is written exactly once
     and never mutated (record_canonical_completion uses setdefault).
Plus the score/offer helper matrix and the admin eligibility endpoint's auth.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from admin_shared import _god_mode_settings
from engine import (
    turnaround_score_eligible,
    record_canonical_completion,
    turnaround_offer_for,
)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}
_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}
_REASON = {"reason": "P2 test"}


def _client(creds):
    c = TestClient(app)
    r = c.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return c


@pytest.fixture(autouse=True)
def _reset():
    e = _god_mode_settings.get("turnaround_module_enabled", False)
    p = dict(_god_mode_settings.get("turnaround_facilitator_permissions", {}))
    yield
    _god_mode_settings["turnaround_module_enabled"] = e
    _god_mode_settings["turnaround_facilitator_permissions"] = p


# ── 4. Score threshold ───────────────────────────────────────────

def test_score_threshold():
    assert turnaround_score_eligible(0.79) is True
    assert turnaround_score_eligible(0.80) is False
    assert turnaround_score_eligible(1.0) is False
    assert turnaround_score_eligible(None) is False
    assert turnaround_score_eligible("nan") is False


# ── 5. Completion invariant (write-once) ─────────────────────────

def test_canonical_snapshot_written_once():
    gs = {}
    first = record_canonical_completion(
        gs, terminal_value=1_000, regenerative_multiple=0.7,
        archetype="STRANDED_RELIC", profile="fragile_giant", profile_title="X")
    assert gs["final_report_canonical"]["regenerative_multiple"] == 0.7
    # A second (different) completion must NOT overwrite the canonical snapshot.
    second = record_canonical_completion(
        gs, terminal_value=9_999, regenerative_multiple=1.9,
        archetype="REGEN_TITAN", profile="regenerative_titan", profile_title="Y")
    assert gs["final_report_canonical"]["regenerative_multiple"] == 0.7
    assert second is first  # same object returned


# ── Offer helper matrix ──────────────────────────────────────────

def _completed_gs(mr):
    return {"game_over": True, "round_number": 10,
            "final_report_canonical": {"regenerative_multiple": mr}}


def test_offer_matrix():
    # module off → no offer even when eligible by score
    assert turnaround_offer_for(_completed_gs(0.7), module_enabled=False) is None
    # completed + low M_R + module on → offer
    offer = turnaround_offer_for(_completed_gs(0.7), module_enabled=True)
    assert offer and offer["eligible"] and offer["current_mr"] == 0.7
    assert offer["threshold"] == 0.80 and offer["max_rounds"] == 4
    # M_R at/above threshold → no offer
    assert turnaround_offer_for(_completed_gs(0.85), module_enabled=True) is None
    # not completed → no offer
    assert turnaround_offer_for(
        {"round_number": 6, "regenerative_multiple": 0.5}, module_enabled=True) is None
    # already run / in-flight → no offer
    ran = _completed_gs(0.5)
    ran["active_event_flags"] = {"turnaround_status": "graduated"}
    assert turnaround_offer_for(ran, module_enabled=True) is None


# ── Admin eligibility endpoint auth ──────────────────────────────

def test_eligibility_endpoint_missing_session_404():
    gm = _client(_GOD)
    gm.put("/api/admin/turnaround/global", json={"enabled": True, **_REASON})
    r = gm.get("/api/admin/turnaround/eligibility/does-not-exist")
    assert r.status_code == 404, r.text


def test_eligibility_endpoint_excludes_project_admin():
    pa = _client(_PA)
    r = pa.get("/api/admin/turnaround/eligibility/whatever")
    assert r.status_code == 403, r.text
