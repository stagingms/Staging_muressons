"""VAL-11 hygiene bundle (audit 2026-09-04, Wave 3) and the VAL-10 facilitator note.

a) the HR ROI report's terminal-value uplift is on the TV formula actually used
   (floored EBITDA × effective multiple × M_SDG), not config 12× on raw EBITDA;
c) /final-report's `terminal_valuation` was a key nothing wrote — always null;
f) the hostile-takeover cap is a breakdown line, so the components sum to the
   M_R awarded;
g) the front page follows the solvency-gated archetype, not the M_R band alone;
h) the BRSR side-track dividend (+0.05, numeric) reaches a non-BRSR finale as
   its value — never as +1.0, never dropped.
"""
import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import round_logic  # noqa: E402


def _strong(bus):
    """A team that earns HR bonuses and clears the instability discount."""
    for b in bus:
        b["social_license_score"] = 92.0
        b["staff_burnout_index"] = 5.0


def _finale(treasury=40_000_000, extra_flags=None, choice="option_b", bus_tweak=None, strong=False):
    from tests.test_launch_audit_2026_09_01 import _tick_state
    gs, bus = _tick_state(round_number=10, treasury=treasury)
    if strong:
        _strong(bus)
        gs["synergy_multiplier"] = 1.2
        gs["workforce_readiness"] = 80.0
    if bus_tweak:
        bus_tweak(bus)
    prev_flags = dict(gs.get("active_event_flags") or {})
    prev_flags.setdefault("ending_pathway", "activist_ultimatum")
    prev_flags.update(extra_flags or {})
    gs.setdefault("active_event_flags", {}).update(extra_flags or {})
    decs = [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "choice_selected": choice} for b in bus]
    extra: dict = {}
    round_logic._post_r10_grand_finale(gs, bus, decs, {}, extra, prev_flags)
    return gs, bus, extra


def test_a_hr_uplift_is_on_the_terminal_value_formula_actually_used():
    gs, bus, extra = _finale(treasury=60_000_000, strong=True)
    rep = extra["hr_roi_report"]
    assert rep["mr_bonus_from_hr"] == pytest.approx(0.15)   # workforce 0.10 + wellbeing 0.05
    # uplift = the same EBITDA floor, multiple and M_SDG the TV used × the HR share of M_R
    tv = extra["terminal_value"]; mr = extra["regenerative_multiple"]
    assert rep["terminal_value_uplift_from_hr"] == pytest.approx(tv / mr * rep["mr_bonus_from_hr"], rel=0.02)


def test_a_source_uses_effective_multiple_and_floored_ebitda():
    import inspect
    src = inspect.getsource(round_logic._stamp_finale_valuation)
    assert "ebitda_for_tv * effective_exit_multiple * m_sdg * hr_mr_value" in src
    assert "terminal_ebitda * exit_multiple * hr_mr_value" not in src


def test_f_the_hostile_takeover_cap_is_a_breakdown_line():
    from terminal_valuation import calculate_mr
    # a strong M_R with the cap: components must still sum to the award
    gs, bus, extra = _finale(treasury=60_000_000, extra_flags={"ending_pathway": "hostile_takeover"},
                             choice="option_c", strong=True)
    assert extra.get("mr_capped_at") == 1.0
    bd = extra["mr_breakdown"]
    assert "hostile_takeover_cap" in bd and bd["hostile_takeover_cap"] < 0
    summed = sum(v for k, v in bd.items() if isinstance(v, (int, float)) and k not in ("max_achievable_mr", "jt_scaling_factor"))
    assert round(summed, 3) == pytest.approx(extra["regenerative_multiple"], abs=0.01)


def test_h_the_brsr_dividend_reaches_a_legacy_finale_as_its_value():
    gs0, bus0, base = _finale()
    gs1, bus1, with_div = _finale(extra_flags={"brsr_net_positive_dividend": 0.05})
    assert with_div["mr_breakdown"].get("brsr_esg_alpha_dividend") == pytest.approx(0.05)
    assert with_div["regenerative_multiple"] - base["regenerative_multiple"] == pytest.approx(0.05, abs=0.011) \
        or with_div["mr_ceiling_clamped"]
    # never the +1.0 that collecting the flag as True would have produced
    assert with_div["regenerative_multiple"] - base["regenerative_multiple"] < 0.2


# ── (c) and (g) through the router ────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    with TestClient(app) as c:
        yield c


def _play_ten(client, paradigm="legacy_abc", ratio=0.3, capex=1_500_000.0):
    from router import _commit_timestamps
    r = client.post("/api/simulations/solo-start", json={"player_name": "V11", "decision_paradigm": paradigm})
    sid = r.json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    last = None
    for rnd in range(1, 11):
        _commit_timestamps.pop(sid, None)
        res = client.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": ratio, "capex_allocated": capex,
                           "choice_selected": "option_b"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert res.status_code == 201, res.text[:300]
        last = res.json(); bus = last.get("business_units") or bus
    return sid, last


def test_c_final_report_terminal_valuation_is_the_awarded_record(client):
    sid, last = _play_ten(client)
    rep = client.get(f"/api/simulations/{sid}/final-report").json()
    tv = rep["terminal_valuation"]
    assert tv is not None, "terminal_valuation was null for every finished game (VAL-11c)"
    canonical = rep["final_report_canonical"]
    assert tv["terminal_value"] == canonical["terminal_value"]
    assert tv["regenerative_multiple"] == canonical["regenerative_multiple"]
    assert tv["source"] == "final_report_canonical"
    assert rep["regenerative_multiple"] == canonical["regenerative_multiple"]


def test_g_the_front_page_follows_the_solvency_gated_archetype(client, monkeypatch):
    sid, last = _play_ten(client)
    import router as _router
    import database as db
    real_fetch = db.fetch_latest_state

    async def gated(session_id, *a, **kw):
        latest = await real_fetch(session_id, *a, **kw)
        latest = copy.deepcopy(latest)
        fl = latest["global_state"].setdefault("active_event_flags", {})
        fl["regenerative_multiple"] = 1.9          # a titan M_R …
        fl["profile"] = "hollow_idealist"          # … the solvency gate demoted
        return latest

    monkeypatch.setattr(_router.db, "fetch_latest_state", gated)
    fp = client.get(f"/api/simulations/{sid}/front-page").json()
    assert fp["band"] == "hollow", fp
    assert "BALANCE SHEET" in fp["headline"]
    assert fp["source"] == "deterministic"
    # and without the gate the same M_R is a titan
    async def titan(session_id, *a, **kw):
        latest = copy.deepcopy(await real_fetch(session_id, *a, **kw))
        latest["global_state"].setdefault("active_event_flags", {})["regenerative_multiple"] = 1.9
        latest["global_state"]["active_event_flags"]["profile"] = "regenerative_titan"
        return latest
    monkeypatch.setattr(_router.db, "fetch_latest_state", titan)
    assert client.get(f"/api/simulations/{sid}/front-page").json()["band"] == "titan"
