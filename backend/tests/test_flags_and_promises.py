"""Flags and promises — audit 2026-09-04 FLAG-2/3/4/5/9/10, VAL-05/07/08/09, SOC-3/4/7 · WP-24.

FLAG-2  multi_toggles persisted the legacy PROXY option's flags (insurance_only,
        electronics_blindspot …) for options the team never saw.
FLAG-3  the 58-flag sentiment rule map never received a decision flag.
FLAG-4  flag-dependency "active" status tested dict keys on list-held flags.
FLAG-5  "adaptive crisis severity" announced every round from R6, never applied.
FLAG-9  greenwashing_detected read in five places, written nowhere; the scandal
        was not a betrayal (SOC-4) and did not block the Fortress premium.
FLAG-10 seven text/number promises the model contradicted.
VAL-05  workforce_readiness reset to 50 every round (Workforce Excellence dead).
VAL-07  R10 Divest reset synergy to 1.0 and earned the +0.15 premium.
VAL-08  +0.15 Carbon Transition dead — baseline_ci never passed.
VAL-09  two solvency definitions (DMAV vs equity).
SOC-3   stakeholder fatigue dead — baseline captured after reconciliation.
SOC-7   greenwash messages stated the wrong bar / "no green option selected".
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

from bu_profiles import build_bu_states  # noqa: E402
from engine import process_tick  # noqa: E402
from round_logic import post_tick, run_new_engines, _apply_option_flags  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent


def _gs(round_number: int = 1, **flags) -> dict:
    return {
        "round_number": round_number, "corporate_treasury": 50_000_000.0, "group_reputation": 60.0,
        "synergy_multiplier": 0.35, "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "wp24-flags", **flags},
        "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0,
        "tipping_point_active": False, "workforce_readiness": 50.0, "momentum_history": [],
        "pending_capex_projects": [], "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _decisions(bus, choice="option_b", ratio=0.2, capex=1_000_000):
    return [{"bu_id": b["bu_id"], "capex_allocated": capex, "investment_ratio": ratio,
             "choice_selected": choice} for b in bus]


def _tick(gs, bus, decisions=None, **kw):
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                        decisions=decisions or _decisions(bus), dividends_paid=0, crisis_severity=40.0,
                        imitation_decay_rate=0.05, decision_paradigm="legacy_abc", **kw)


# ── FLAG-2 ────────────────────────────────────────────────────────────────────

def test_pillar_mode_never_persists_the_proxy_options_flags():
    bus = build_bu_states()
    legacy, pillar = _gs(5), _gs(5)
    _apply_option_flags(5, _decisions(bus, "option_c"), legacy, extra := {}, bus=bus, events={})
    assert legacy["active_event_flags"].get("r5_flags") == ["insurance_only"]
    _apply_option_flags(5, _decisions(bus, "option_c"), pillar, extra_p := {}, bus=bus,
                        events={"pillar_cost_applied": -1_000_000})
    assert "r5_flags" not in pillar["active_event_flags"]
    assert extra_p.get("proxy_option_flags_skipped_r5") is True


def test_post_tick_in_pillar_mode_leaves_no_insurance_only_behind():
    bus = build_bu_states()
    gs = _gs(5)
    events = {"pillar_cost_applied": 0, "pillar_flags": ["generator_backup"]}
    post_tick(round_number=5, global_state=gs, bu_states=bus, decisions=_decisions(bus, "option_c"),
              events=events, previous_flags={}, decision_paradigm="multi_toggles")
    from flag_utils import collect_all_flags
    assert "insurance_only" not in collect_all_flags(gs["active_event_flags"])


# ── FLAG-3 ────────────────────────────────────────────────────────────────────

def test_option_flags_reach_the_stakeholder_sentiment_rules():
    bus = build_bu_states()
    plain = _tick(_gs(3), bus)
    decs = _decisions(bus, "option_a")
    decs[0]["flags_set"] = ["renewable_ppa_signed"]
    flagged = _tick(_gs(3), bus, decisions=decs)
    narr = " ".join((sh.get("sentiment_narrative") or "") for sh in flagged["events"].get("sentiment_stakeholders", []))
    assert "renewable" in narr.lower(), narr[:200]
    plain_narr = " ".join((sh.get("sentiment_narrative") or "") for sh in plain["events"].get("sentiment_stakeholders", []))
    assert "renewable" not in plain_narr.lower()


def test_commit_turn_attaches_the_chosen_options_flags():
    from fastapi.testclient import TestClient
    from main import app
    from router import _commit_timestamps
    from round_configs import get_round_options
    client = TestClient(app)
    r = client.post("/api/simulations/solo-start", json={"player_name": "WP24", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:200]
    sid = r.json()["session_id"]
    sess = client.get(f"/api/simulations/{sid}/dashboard").json()
    _commit_timestamps.pop(sid, None)
    r = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "investment_ratio": 0.2,
                       "choice_selected": "option_a"} for b in sess["business_units"]],
        "force_override_cfo": True, "expected_round": 1})
    assert r.status_code == 201, r.text[:300]
    ev = r.json()["events"]
    canonical = next(k for k in ("option_a", "option_b", "option_c") if k not in (ev.get("decision_regret") or {}).get("alternatives", {"option_a": 1, "option_b": 1}))
    assert ev.get("option_flags_this_round") == get_round_options(1)[canonical]["flags_set"]


# ── FLAG-4 ────────────────────────────────────────────────────────────────────

def test_flag_dependency_status_reads_list_held_flags_and_false_booleans():
    from terminal_valuation import get_flag_dependency_graph
    g = get_flag_dependency_graph({"materiality_aligned": False, "materiality_ignored": True,
                                   "r7_flags": ["synergy_unlock"], "r1_flags": ["deep_audit_completed"]})
    status = {d["flag"]: d["status"] for d in g["dependencies"]}
    assert status.get("synergy_unlock") == "active"
    assert status.get("deep_audit_completed") == "active"
    assert status.get("materiality_aligned") == "inactive"


# ── FLAG-5 ────────────────────────────────────────────────────────────────────

def test_adaptive_crisis_severity_is_a_diagnostic_not_an_announcement():
    bus = build_bu_states()
    gs = _gs(6)
    gs["player_archetype"] = "pragmatic_optimizer"
    extra = run_new_engines(round_number=6, global_state=gs, bu_states=bus, events={"crisis_severity_effective": 40})
    assert "adaptive_crisis_severity" not in extra
    diag = extra.get("_adaptive_crisis_severity_diagnostic")
    assert diag and diag.get("applied") is False and "adjusted_severity_not_applied" in diag
    catalog = (REPO / "frontend/app/components/consequenceCatalog.js").read_text(encoding="utf-8")
    assert "adaptive_crisis_severity: {" not in catalog


# ── FLAG-9 / SOC-4 / SOC-7 ────────────────────────────────────────────────────

def _scandal_tick():
    bus = build_bu_states()
    # R1 option_a is a full green claim; 5 % investment and $1M CapEx clear neither bar
    return _tick(_gs(1), bus, decisions=_decisions(bus, "option_a", ratio=0.05, capex=1_000_000))


def test_the_greenwashing_scandal_is_detected_a_betrayal_and_blocks_the_premiums():
    ev = _scandal_tick()["events"]
    assert ev.get("greenwashing_scandal") is True and ev.get("greenwashing_detected") is True
    from npc_stakeholders import detect_betrayal
    from autonomous_agents import detect_betrayal as agent_betrayal
    assert detect_betrayal(ev) is True and agent_betrayal(ev) is True
    from ending_pathways import calc_hostile_takeover_mr
    bus = build_bu_states()
    for b in bus:
        b["opex_base"] = b["revenue_base"] * 0.5    # 50 % EBITDA margin → Fortress territory
    gs = _gs(10); gs["synergy_multiplier"] = 1.0
    clean, dirty = {}, {}
    calc_hostile_takeover_mr(bus, gs, set(), clean)
    calc_hostile_takeover_mr(bus, gs, {"greenwashing_scandal"}, dirty)
    assert clean.get("mr_fortress_premium", 0) > 0 and "mr_fortress_premium" not in dirty


def test_greenwashing_detected_is_the_record_and_greenwashing_scandal_the_verdict():
    """Wave 2 gate (2026-09-05): a clean round clears this round's verdict but
    does not touch the record. The router merges every event key into
    active_event_flags, so a key written False clears and a key not written
    persists — the two flags deliberately use the two behaviours."""
    bus = build_bu_states()
    clean = _tick(_gs(1), bus, decisions=_decisions(bus, "option_a", ratio=0.5, capex=5_000_000))["events"]
    assert clean["greenwashing_scandal"] is False
    assert "greenwashing_detected" not in clean
    scandal = _scandal_tick()["events"]
    assert scandal["greenwashing_scandal"] is True and scandal["greenwashing_detected"] is True
    # the persisted bag after scandal → clean, as the router merges it
    bag = {}
    bag.update({k: v for k, v in scandal.items() if isinstance(v, bool)})
    bag.update({k: v for k, v in clean.items() if isinstance(v, bool)})
    assert bag["greenwashing_scandal"] is False and bag["greenwashing_detected"] is True


def test_greenwash_messages_state_the_claims_own_bar_and_the_absolute_escape():
    from config import GREENWASH_INVESTMENT_THRESHOLD, GREENWASH_MODERATE_THRESHOLD_SCALE, GREENWASH_ABS_CAPEX_FLOOR
    bus = build_bu_states()
    moderate_fail = _tick(_gs(1), bus, decisions=_decisions(bus, "option_b", ratio=0.08, capex=1_000_000))["events"]
    assert moderate_fail["greenwashing_scandal"] is True
    bar = round(GREENWASH_INVESTMENT_THRESHOLD * GREENWASH_MODERATE_THRESHOLD_SCALE, 4)
    assert moderate_fail["greenwashing_threshold"] == bar and "moderate green claim" in moderate_fail["greenwashing_message"]
    assert "required 15%" not in moderate_fail["greenwashing_message"]
    escaped = _tick(_gs(1), bus, decisions=_decisions(bus, "option_a", ratio=0.12, capex=GREENWASH_ABS_CAPEX_FLOOR))["events"]
    assert escaped["greenwashing_scandal"] is False
    assert "absolute floor" in escaped["greenwashing_message"] and "no green option" not in escaped["greenwashing_message"]
    assert escaped["greenwashing_claim_level"] == "full"


# ── FLAG-10 ───────────────────────────────────────────────────────────────────

def test_green_bond_lowers_ncd_over_three_rounds_as_the_text_says():
    from round_configs import get_round_options
    opt = get_round_options(3)["option_b"]
    assert "over 3 rounds" in opt["description"] and opt["impacts"]["natural_capital_debt_rounds"] == 3
    bus = build_bu_states()
    for b in bus:
        b["natural_capital_debt"] = 40.0
    gs = _gs(3)
    extra = post_tick(round_number=3, global_state=gs, bu_states=bus, decisions=_decisions(bus, "option_b"),
                      events={}, previous_flags={}, decision_paradigm="legacy_abc")
    assert extra["natural_capital_debt_applied_r3"] == -5.0
    assert extra["natural_capital_debt_scheduled_r3"] == {"per_round": -5.0, "rounds": 3, "total": -15}
    assert all(b["natural_capital_debt"] == 35.0 for b in bus)
    drops = [p for p in gs["pending_capex_projects"] if p["type"] == "ncd_drop"]
    assert sorted(p["rounds_remaining"] for p in drops) == [1, 2] and all(p["amount"] == -5.0 for p in drops)
    # the queue matures on the next two ticks and not on a third
    gs["round_number"] = 4
    r4 = _tick(gs, bus)
    assert [p["amount"] for p in r4["events"].get("capex_project_completed", []) if p["type"] == "ncd_drop"] == [-5.0]
    g5 = r4["global_state"]; g5["pedagogical_overrides"] = gs["pedagogical_overrides"]
    r5 = _tick(g5, r4["bu_states"])
    assert [p["amount"] for p in r5["events"].get("capex_project_completed", []) if p["type"] == "ncd_drop"] == [-5.0]
    g6 = r5["global_state"]; g6["pedagogical_overrides"] = gs["pedagogical_overrides"]
    r6 = _tick(g6, r5["bu_states"])
    assert not [p for p in r6["events"].get("capex_project_completed", []) if p["type"] == "ncd_drop"]


def test_the_seven_text_promises_match_the_code():
    from round_configs import get_round_options, get_round_config
    r9a = get_round_options(9)["option_a"]["description"]
    assert "50% chance" in r9a and "75%" not in r9a
    assert get_round_config(9)["special_rules"]["strike_probability_override"] == 0.50
    assert "over 3 rounds" not in (REPO / "backend/pillar_configs.py").read_text(encoding="utf-8").split("hybrid_transition")[1][:400]
    std = (REPO / "frontend/app/briefings/data/standard.js").read_text(encoding="utf-8")
    assert "+0.35" not in std and "75% chance of a total strike" not in std and "+0.30" in std
    mve = (REPO / "frontend/app/components/MasterVariableEditor.js").read_text(encoding="utf-8")
    assert "+0.35" not in mve and "overrides to 75%" not in mve
    tele = (REPO / "frontend/app/components/FacilitatorTeleprompter.js").read_text(encoding="utf-8")
    assert "$3M/round" not in tele and "+0.35 synergy" not in tele and "0.5 per $1M" not in tele
    src = (REPO / "backend/impact_engine.py").read_text(encoding="utf-8")
    assert "gs.get('round_number', 6) + 1" in src and "gs.get('round_number', 5) + 2" not in src


def test_full_materiality_alignment_scales_ncd_forgiveness_in_advanced_climate():
    bus = build_bu_states()
    for b in bus:
        b["natural_capital_debt"] = 40.0
    base = process_tick(current_global=copy.deepcopy(_gs(4)), current_bus=copy.deepcopy(bus),
                        decisions=_decisions(bus, capex=4_000_000), dividends_paid=0, crisis_severity=40.0,
                        imitation_decay_rate=0.05, decision_paradigm="advanced_climate")
    aligned = process_tick(current_global=copy.deepcopy(_gs(4, r2_flags=["full_materiality_alignment"])),
                           current_bus=copy.deepcopy(bus), decisions=_decisions(bus, capex=4_000_000),
                           dividends_paid=0, crisis_severity=40.0, imitation_decay_rate=0.05,
                           decision_paradigm="advanced_climate")
    assert aligned["events"]["ncd_forgiveness_applied"] == pytest.approx(base["events"]["ncd_forgiveness_applied"] * 1.25, abs=0.02)
    assert aligned["events"]["ncd_forgiveness_materiality_bonus"] == 1.25


# ── VAL-05 ────────────────────────────────────────────────────────────────────

def test_workforce_readiness_crosses_the_tick_and_earns_workforce_excellence():
    bus = build_bu_states()
    gs = _gs(6); gs["workforce_readiness"] = 66.0; gs["pillar_effectiveness_modifier"] = 0.9
    out = _tick(gs, bus)
    assert out["global_state"]["workforce_readiness"] == 66.0
    assert out["global_state"]["pillar_effectiveness_modifier"] == 0.9
    # the finale reads the carried stock: readiness 85 → +0.10 Workforce Excellence
    g10 = _gs(10); g10["workforce_readiness"] = 85.0
    b10 = build_bu_states()
    extra = post_tick(round_number=10, global_state=g10, bu_states=b10, decisions=_decisions(b10, "option_b"),
                      events={}, previous_flags={}, decision_paradigm="legacy_abc")
    assert extra["mr_breakdown"].get("workforce_bonus", 0) == pytest.approx(0.10, abs=0.001)


# ── VAL-07 ────────────────────────────────────────────────────────────────────

def test_divest_wipes_synergy_and_cannot_earn_the_premium_spin_off_is_denied():
    def finale(choice):
        gs = _gs(10, r7_flags=["synergy_unlock"]); gs["synergy_multiplier"] = 0.60
        b = build_bu_states()
        extra = post_tick(round_number=10, global_state=gs, bu_states=b, decisions=_decisions(b, choice),
                          events={}, previous_flags={"r7_flags": ["synergy_unlock"]}, decision_paradigm="legacy_abc")
        return gs, extra
    gs_c, divest = finale("option_c")
    gs_b, spinoff = finale("option_b")
    assert divest.get("synergy_wiped") is True and divest["synergy_before_wipe"] == 0.6 and gs_c["synergy_multiplier"] == 0.0
    assert "synergy_bonus" not in divest["mr_breakdown"] and "synergy_bonus" not in spinoff["mr_breakdown"]


# ── VAL-08 ────────────────────────────────────────────────────────────────────

def test_carbon_transition_bonus_is_reachable():
    gs = _gs(10, ending_pathway="climate_black_swan")
    bus = build_bu_states()
    for b in bus:
        b["ci_baseline_r1"] = 100.0
        b["carbon_intensity"] = 30.0
    extra = post_tick(round_number=10, global_state=gs, bu_states=bus, decisions=_decisions(bus, "option_b"),
                      events={}, previous_flags={"ending_pathway": "climate_black_swan"}, decision_paradigm="legacy_abc")
    assert extra.get("mr_carbon_transition_bonus", 0) == pytest.approx(0.15, abs=0.001)
    assert extra.get("mr_carbon_transition_pct") == 70.0


# ── VAL-09 ────────────────────────────────────────────────────────────────────

def test_one_solvency_gate_positive_dmav_with_wiped_equity_is_not_a_safe_haven():
    from round_logic import _equity_and_solvency, solvency_gated_profile
    bus = build_bu_states()
    gs = _gs(10); gs["corporate_treasury"] = 15_000_000.0
    extra = {}
    eq = _equity_and_solvency(gs, bus, extra, terminal_value=15_000_000.0, mr=1.65,
                              effective_exit_multiple=12.0, total_revenue=53_500_000.0)
    assert eq["dmav"] > 0 and eq["equity_value"] < 0 and eq["equity_wiped_out"] is True
    assert eq["solvent"] is False
    assert solvency_gated_profile("derisked_safe_haven", eq["dmav"], solvent=eq["solvent"]) == "hollow_idealist"
    assert solvency_gated_profile("derisked_safe_haven", eq["dmav"]) == "derisked_safe_haven"  # legacy DMAV-only callers


# ── SOC-3 ─────────────────────────────────────────────────────────────────────

def test_stakeholder_fatigue_dampens_between_tick_reputation_gains():
    bus = build_bu_states()
    for b in bus:
        b["reputation_score"] = 50.0
    gs = _gs(5)
    gs["group_reputation"] = 70.0          # a between-tick recovery not yet folded into the BU stock
    gs["active_event_flags"]["crisis_count_lifetime"] = 2
    out = _tick(gs, bus)
    assert out["events"].get("stakeholder_fatigue_applied"), "the fatigue dampener never fired (SOC-3)"
    # the dampened stock is below what the same recovery yields with no crisis history
    fresh = _gs(5); fresh["group_reputation"] = 70.0
    calm = _tick(fresh, bus)
    assert out["global_state"]["group_reputation"] < calm["global_state"]["group_reputation"]


# ── GATE-1 (Wave 2 gate, 2026-09-05) ─────────────────────────────────────────

def test_a_running_cascade_is_read_from_the_persisted_flags_and_not_relaunched():
    from round_logic import _active_npc_cascades
    from systemic_risk_engine import evaluate_npc_cascades
    campaign = {"npc_id": "activist_investor", "action": "divestment_campaign",
                "round_triggered": 6, "persistence_rounds": 2}
    injunction = {"npc_id": "community_leader", "action": "court_injunction",
                  "round_triggered": 6, "persistence_rounds": 1}
    gs = {"active_event_flags": {"active_npc_cascades": [campaign, injunction]}}
    # R7: the two-round campaign is still running, the one-round injunction is over
    live = _active_npc_cascades(gs, {}, 7)
    assert [c["action"] for c in live] == ["divestment_campaign"]
    # R8: the campaign has run its course and may be launched again
    assert _active_npc_cascades(gs, {}, 8) == []
    # this tick's events never carry the list — the old read returned nothing
    assert {}.get("active_npc_cascades", []) == []
    # and evaluate_npc_cascades honours the live list: with trust on the floor
    # the activist does not relaunch a running campaign
    floor = {nid: 0.0 for nid in ("activist_investor", "regulator", "community_leader", "journalist")}
    relaunched = [c["action"] for c in evaluate_npc_cascades(floor, 7, live)]
    assert "divestment_campaign" not in relaunched
    assert "divestment_campaign" in [c["action"] for c in evaluate_npc_cascades(floor, 7, [])]
