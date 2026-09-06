"""IMP-10, IMP-12, IMP-14, IMP-15, IMP-16, IMP-17 (audit 2026-09-04, Wave 3).

IMP-10  The social tipping tiers tested avg_slo ≥ threshold: the best-SLO team
        in the room tipped, a team at SLO 5 never did.
IMP-12  The facilitator's Regional ESG Report summed a BU key nobody writes
        (`total_tco2e`) and printed Scope 1+2 = 0 tCO₂e, GREEN, for every cohort.
IMP-14  Every turnaround lever injected free cash ($34–70M over the arc) that the
        re-valuation turned into equity value. It is rescue financing, carried
        as debt in the re-valuation; the graduation gates are unchanged.
IMP-15  In pillar mode the R9 retraining clawback read a key the pillar branch
        never wrote, so "30% clawed back" was printed with nothing clawed back.
IMP-16  Tipping penalties documented as one-off levels were applied as
        compounding per-round flows; two documented penalties had no reader.
IMP-17  A duplicate dict key and a constant hectares-as-percent pill.
"""
import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")


# ── IMP-10 ────────────────────────────────────────────────────────────────────

def _bus(slo, burnout, n=4):
    return [{"bu_id": f"bu_{i}", "carbon_intensity": 30, "social_license_score": slo,
             "staff_burnout_index": burnout} for i in range(n)]


@pytest.mark.parametrize("slo,burnout,tier", [
    (5, 95, "tipped"), (14, 90, "tipped"), (15, 90, "tipped"),
    (16, 95, "stressed"), (24, 80, "stressed"), (30, 65, "warning"),
    (90, 95, "none"), (90, 60, "none"), (40, 95, "none"),
])
def test_social_collapse_is_low_licence_and_high_burnout(slo, burnout, tier):
    from systemic_risk_engine import evaluate_tipping_points
    gs = {"biodiversity_state": {"ecosystem_health_index": 60}, "active_event_flags": {}}
    out = evaluate_tipping_points(gs, _bus(slo, burnout), {})
    assert out["dimensions"]["social"]["tier"] == tier


# ── IMP-12 ────────────────────────────────────────────────────────────────────

def test_the_regional_report_sums_the_emissions_the_bus_carry():
    from regional_reporting import generate_regional_report
    bus = [{"bu_id": "pharma", "carbon_intensity": 30.0, "revenue_base": 20_000_000, "absolute_emissions": 600.0,
            "social_license_score": 55, "governance_risk_score": 20},
           {"bu_id": "software", "carbon_intensity": 10.0, "revenue_base": 20_000_000,     # no figure → CI × revenue / $1M
            "social_license_score": 55, "governance_risk_score": 20}]
    rep = generate_regional_report({"region": "europe"}, {"global_state": {"group_reputation": 60, "corporate_treasury": 5e7,
                                                                           "active_event_flags": {}}, "bu_states": bus})
    metric = next(v for k, v in rep["metrics"].items() if "tco2e" in k) if isinstance(rep.get("metrics"), dict) else None
    if metric is None:   # find it wherever the framework put it
        import json
        blob = json.dumps(rep)
        assert '"value": 800' in blob or '"value": 800.0' in blob, blob[:400]
    else:
        assert metric["value"] == 800


# ── IMP-14 ────────────────────────────────────────────────────────────────────

def test_turnaround_injections_are_rescue_financing_not_equity():
    import turnaround_engine as te
    from turnaround_engine import TURNAROUND_ROUNDS
    gs = {"corporate_treasury": -2_000_000.0, "group_reputation": 20.0, "game_over": True, "round_number": 10,
          "final_report_canonical": {"regenerative_multiple": 0.7},
          "active_event_flags": {"net_debt": 30_000_000.0, "exit_multiple_applied": 12.0}}
    entry = te.enter_arc(gs, [])
    assert gs["turnaround_rescue_financing"] == entry["bailout_applied"] > 0     # the entry bailout is rescue money too
    injected = float(entry["bailout_applied"])
    bus = [{"bu_id": "pharma", "revenue_base": 20_000_000, "opex_base": 12_000_000, "carbon_intensity": 30,
            "social_license_score": 55, "governance_risk_score": 20, "natural_capital_debt": 50}]
    r = None
    for ch in ("option_a", "option_a", "option_a", "option_a"):
        injected += TURNAROUND_ROUNDS[int(gs["turnaround_round"])]["options"][ch]["impacts"]["treasury"]
        r = te.apply_commit(gs, bus, ch)
        if r["arc_complete"]:
            break
    rep = r["amended_report"]
    assert rep["rescue_financing"] == pytest.approx(injected)
    # net debt at re-valuation = R10 net debt − cash recovered + the rescue money that produced it
    assert rep["net_debt"] == pytest.approx(30_000_000.0 - rep["cash_recovered"] + injected, abs=1.0)
    assert rep["net_debt"] >= 30_000_000.0 - 1.0        # free cash did not de-lever the company
    # the calibration is untouched: disciplined play still graduates from this floor
    assert rep["graduated"] is True


# ── IMP-15 ────────────────────────────────────────────────────────────────────

class _FixedRoller:
    def __init__(self, v): self.v = v
    def random(self): return self.v


def test_the_pillar_mode_clawback_is_real_and_the_message_says_what_happened(monkeypatch):
    import impact_engine as ie
    monkeypatch.setattr(ie, "_event_roller", lambda *a, **k: _FixedRoller(0.99))   # the programme fails
    bus = [{"bu_id": "pharma", "social_license_score": 50.0, "revenue_base": 2e7, "governance_risk_score": 20}]
    gs = {"corporate_treasury": 5e7, "group_reputation": 68.0, "active_event_flags": {}}
    events = {"pillar_cost_applied": 1_000_000, "pillar_aggregate_impacts": {"reputation": 8.0}, "pillar_flags": []}
    extra = {}
    ie._post_r9_just_transition(gs, bus, [{"choice_selected": "option_b"}], events, extra, {})
    assert extra["retraining_assessment"]["succeeded"] is False
    assert extra["retraining_clawback"] == pytest.approx(2.4)
    assert gs["group_reputation"] == pytest.approx(68.0 - 2.4)
    assert "2.4 pts" in extra["retraining_message"] and "clawed back" in extra["retraining_message"]
    # nothing booked → the message says so instead of claiming a clawback
    gs2 = {"corporate_treasury": 5e7, "group_reputation": 68.0, "active_event_flags": {}}
    extra2 = {}
    ie._post_r9_just_transition(gs2, copy.deepcopy(bus), [{"choice_selected": "option_b"}],
                                {"pillar_cost_applied": 1_000_000, "pillar_aggregate_impacts": {}, "pillar_flags": []}, extra2, {})
    assert "retraining_clawback" not in extra2 and gs2["group_reputation"] == 68.0
    assert "nothing to claw back" in extra2["retraining_message"]
    assert "30% of transition benefits have been clawed back" not in extra2["retraining_message"]


# ── IMP-16 ────────────────────────────────────────────────────────────────────

def _tipped_all():
    return {"climate_tipped": True, "social_tipped": True, "financial_tipped": True}


def test_level_shifts_apply_once_and_ceilings_every_round():
    from round_logic import apply_tipping_penalties
    from systemic_risk_engine import IRREVERSIBILITY_PENALTIES as PEN
    gs = {"group_reputation": 80.0, "cost_of_capital": 0.05}
    bus = [{"bu_id": "a", "natural_capital_debt": 100.0, "opex_base": 10_000_000.0, "social_license_score": 70.0}]
    events = {"systemic_tipping": {"tipping_state": _tipped_all()}}
    extra = {}
    apply_tipping_penalties(gs, bus, events, extra, 6)
    assert bus[0]["natural_capital_debt"] == pytest.approx(100.0 * (1 + PEN["climate_tipped"]["ncd_stock_uplift_once"]))
    assert bus[0]["opex_base"] == pytest.approx(10_000_000.0 * (1 + PEN["social_tipped"]["opex_surcharge_once"]))
    assert gs["cost_of_capital"] == pytest.approx(0.05 + PEN["financial_tipped"]["borrowing_premium_once"])
    assert gs["group_reputation"] == PEN["climate_tipped"]["reputation_ceiling"]
    assert bus[0]["social_license_score"] == PEN["social_tipped"]["social_license_ceiling"]
    assert events["capex_cap_multiplier"] == 0.5 and events["dividend_suspended"] is True
    state = events["systemic_tipping_state"]
    assert state["climate_penalty_applied"] == 6 and state["social_penalty_applied"] == 6 and state["financial_penalty_applied"] == 6
    assert gs["systemic_tipping_state"] is state                       # both locations, one object
    assert extra["climate_tipping_level_shift_round"] == 6
    # next round, still tipped: the levels do NOT move again; the ceilings and flags are re-asserted
    ncd, opex, coc = bus[0]["natural_capital_debt"], bus[0]["opex_base"], gs["cost_of_capital"]
    gs["group_reputation"] = 75.0; bus[0]["social_license_score"] = 66.0
    events2 = {"systemic_tipping": {"tipping_state": dict(state)}}
    extra2 = {}
    apply_tipping_penalties(gs, bus, events2, extra2, 7)
    assert bus[0]["natural_capital_debt"] == ncd and bus[0]["opex_base"] == opex and gs["cost_of_capital"] == coc
    assert gs["group_reputation"] == 60.0 and bus[0]["social_license_score"] == 50.0
    assert events2["capex_cap_multiplier"] == 0.5 and events2["dividend_suspended"] is True
    assert "climate_tipping_level_shift_round" not in extra2 and extra2["climate_tipping_penalties_applied"] is True


def test_the_penalty_table_describes_the_code():
    import inspect
    import round_logic
    from systemic_risk_engine import IRREVERSIBILITY_PENALTIES as PEN
    for dead in ("strike_probability_floor", "carbon_tax_multiplier", "ncd_interest_multiplier"):
        assert not any(dead in v for v in PEN.values()), dead
    src = inspect.getsource(round_logic.apply_tipping_penalties)
    for literal in ("* 0.5, 2)", "* 1.05, 2)", "coc + 0.04"):
        assert literal not in src, literal
    assert "IRREVERSIBILITY_PENALTIES" in src


# ── IMP-17 ────────────────────────────────────────────────────────────────────

def test_no_duplicate_keys_in_the_flag_metric_shift_table():
    import ast
    import consequence_dna_api
    src = inspect_src = open(consequence_dna_api.__file__, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "FLAG_METRIC_SHIFTS" for t in node.targets):
            keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
            assert len(keys) == len(set(keys)), sorted(k for k in keys if keys.count(k) > 1)
            break
    else:
        pytest.fail("FLAG_METRIC_SHIFTS not found")
    assert "planet_expendable" in consequence_dna_api.FLAG_METRIC_SHIFTS
