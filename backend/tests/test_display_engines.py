"""Display engines fixed or retired — audit 2026-09-04 F-19 (IMP-01/02/03/08), IMP-04, IMP-06, IMP-07 · WP-22.

F-19a  Biodiversity: EHI fell 65 → ~2.5 for every team (constant deforestation
       + drift; the NCD wire read an events key nobody wrote). Now the NCD term
       reads the round's `natural_capital_debt_applied_r*` sum and the constant
       drivers are zero — a greenest and an extractive team diverge.
F-19b  TCFD: the emissions proxy assumed $1B per BU (×69) so the "annual carbon
       cost" was 85–120 % of revenue; the price index never advanced by decade.
F-19c  Meadows: always "LP12 · 0 %" — no history reached it and the DNA caller's
       signature was wrong (swallowed as TypeError).
F-19d  SDG: two arbiters in one payload; NCD normalised against 500,000 (index
       caps at 5,000) so SDG-12 read ~100 for every team; EHI read a key that
       never existed.
IMP-04 R6/R7/R8 journey panels promised effects nothing applied and PATCHed a
       super-admin route from the player's browser. They are reflection
       exercises: labelled so, OFF by default, filed to the player endpoint.
IMP-06 The god-mode "Systemic Risk Controls" had no reader. Stamped at commit
       into active_event_flags["_systemic_toggles"]; engine/round_logic gate.
IMP-06b (found while wiring IMP-06) run_new_engines read the cohort's engine
       toggles from global_state["pedagogical_overrides"], which only dry_run
       ever set — the cohort toggles modal was inert in the live commit path.
IMP-07 A materiality shock was a blocking modal with no state effect and no
       link to the team's own R2 matrix. It is a one-round OPEX flow, halved
       when the team placed the issue as financially material in R2.
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


def _gs(round_number: int = 1, **flags) -> dict:
    return {
        "round_number": round_number,
        "corporate_treasury": 50_000_000.0,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "wp22-display", **flags},
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "workforce_readiness": 50.0,
        "momentum_history": [],
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _decisions(bus, choice="option_b"):
    return [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "investment_ratio": 0.2,
             "choice_selected": choice} for b in bus]


def _tick(gs, bus, **kw):
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                        decisions=_decisions(bus), dividends_paid=0, crisis_severity=40.0,
                        imitation_decay_rate=0.05, decision_paradigm="legacy_abc", **kw)


# ── F-19a biodiversity ────────────────────────────────────────────────────────

def test_biodiversity_greenest_and_extractive_teams_diverge_and_ehi_moves_with_ncd():
    from biodiversity_engine import create_initial_biodiversity_state, process_biodiversity_tick
    bus = build_bu_states()

    def run(ncd_delta, ci):
        state = create_initial_biodiversity_state()
        b = copy.deepcopy(bus)
        for x in b:
            x["carbon_intensity"] = ci
        ehi = []
        for rnd in range(1, 11):
            events = {"natural_capital_debt_delta": ncd_delta}
            state, diag = process_biodiversity_tick(state, _gs(rnd), b, events, rnd)
            ehi.append(state["ecosystem_health_index"])
        return ehi, diag

    green, gdiag = run(0.0, 10.0)
    extractive, xdiag = run(60.0, 90.0)
    # the constant drivers that sank every team are gone …
    assert gdiag["ehi"]["deforestation_impact"] == 0.0 and gdiag["ehi"]["natural_drift"] == 0.0
    # … so the greenest team is not red by R4 and the extractive team is
    assert green[3] > 60, green
    assert extractive[-1] < green[-1] - 20, (green[-1], extractive[-1])
    # and EHI answers to the NCD the team actually accrues
    assert xdiag["ehi"]["ncd_impact"] != 0.0 and gdiag["ehi"]["ncd_impact"] == 0.0


def test_round_logic_feeds_the_rounds_applied_ncd_into_the_biodiversity_engine():
    import inspect
    import round_logic
    src = inspect.getsource(round_logic.run_new_engines)
    assert 'startswith("natural_capital_debt_applied_r")' in src
    assert "tnfd_disclosure_credit" in src and "tnfd_mr_bonus" not in src


# ── F-19b TCFD ────────────────────────────────────────────────────────────────

def test_tcfd_carbon_cost_is_a_few_percent_of_revenue_and_the_price_indexes_by_decade():
    from tcfd_scenarios import run_scenario_analysis, CLIMATE_SCENARIOS
    bus = build_bu_states()
    gs = _gs()
    sid = "orderly_1_5"
    traj = CLIMATE_SCENARIOS[sid]["carbon_price_trajectory"]
    r10 = run_scenario_analysis(sid, bus, gs, None, time_horizon_years=10)
    pct = r10["carbon_exposure"]["carbon_cost_as_pct_revenue"]
    assert 0.1 <= pct <= 5.0, pct  # was 85–120 %
    # price index per decade: 2y → decade 1, 20y → decade 2, 45y → decade 5
    assert run_scenario_analysis(sid, bus, gs, None, 2)["carbon_exposure"]["carbon_price_at_horizon"] == traj[0]
    assert run_scenario_analysis(sid, bus, gs, None, 20)["carbon_exposure"]["carbon_price_at_horizon"] == traj[1]
    assert run_scenario_analysis(sid, bus, gs, None, 45)["carbon_exposure"]["carbon_price_at_horizon"] == traj[4]
    # revenue 0 no longer divides by zero
    dead = [dict(b, revenue_base=0) for b in bus]
    assert "error" not in run_scenario_analysis(sid, dead, gs, None, 10)
    # a negative treasury has no physical loss to lose
    broke = dict(gs, corporate_treasury=-5_000_000)
    assert run_scenario_analysis(sid, bus, broke, None, 10)["physical_risk"]["annual_expected_loss"] == 0.0


# ── F-19c Meadows ─────────────────────────────────────────────────────────────

def test_meadows_a_diverse_history_is_not_lp12_and_the_dna_caller_reaches_it():
    from meadows_leverage import analyse_session_leverage_points
    import consequence_dna_api as cd
    bus = build_bu_states()
    gs = _gs()
    best = [{"round_number": n, "primary_choice": c, "allocations": {"x": 1}} for n, c in
            ((1, "option_a"), (2, "option_a"), (3, "option_a"), (5, "option_b"), (7, "option_a"), (9, "option_b"))]
    worst = [{"round_number": n, "primary_choice": "option_c", "allocations": {"x": 1}} for n in range(1, 11)]
    b = analyse_session_leverage_points(best, gs, bus)
    w = analyse_session_leverage_points(worst, gs, bus)
    assert b["dominant_leverage_point"] != 12 and b["dominant_leverage_point"] < w["dominant_leverage_point"]
    assert b["effectiveness_score"] > 0.8 > w["effectiveness_score"] > 0.0
    # the DNA caller passes (history, gs, bus) — it used to pass one argument and swallow the TypeError
    data = cd.build_consequence_dna_data("wp22", gs, bus, [
        {"round_number": 1, "decisions": [{"bu_id": "pharma", "choice_selected": "option_a", "capex": 1_000_000}]},
    ])
    assert data["leverage_summary"]["effectiveness_score"] > 0.0


# ── F-19d SDG ─────────────────────────────────────────────────────────────────

def test_sdg_reads_the_real_keys_and_the_router_has_one_arbiter():
    from sdg_linkage_engine import calc_group_sdg_score
    bus = build_bu_states()
    gs = _gs()

    def score(mutate):
        g, b = copy.deepcopy(gs), copy.deepcopy(bus)
        mutate(g, b)
        return calc_group_sdg_score(b, g)

    def bu_sdg(res, bu, sdg):
        return next(d for d in res["bu_scores"][bu]["sdg_details"] if d["sdg"] == sdg)["normalized_score"]

    ncd0 = score(lambda g, b: [x.update(natural_capital_debt=0) for x in b if x["bu_id"] == "consumer_goods"])
    ncd5k = score(lambda g, b: [x.update(natural_capital_debt=5000) for x in b if x["bu_id"] == "consumer_goods"])
    assert bu_sdg(ncd0, "consumer_goods", 12) > bu_sdg(ncd5k, "consumer_goods", 12) + 50
    ehi0 = score(lambda g, b: g.setdefault("biodiversity_state", {}).update(ecosystem_health_index=0))
    ehi100 = score(lambda g, b: g.setdefault("biodiversity_state", {}).update(ecosystem_health_index=100))
    assert ehi100["group_sdg_score"] > ehi0["group_sdg_score"]


def test_sdg_dashboard_endpoint_returns_the_engines_bu_scores():
    import asyncio
    from fastapi.testclient import TestClient
    from main import app
    import database as db
    from sdg_linkage_engine import calc_group_sdg_score
    client = TestClient(app)
    ck = client.post("/api/admin/facilitators/login",
                     json={"facilitator_id": "god_mode", "password": os.environ["MASTER_PASSWORD"]}).cookies
    sid = client.post("/api/simulations/start", json={"cohort_name": "wp22-sdg", "facilitator_id": "god_mode"},
                      cookies=ck).json()["session_id"]
    st = asyncio.run(db.fetch_latest_state(sid))
    bus = copy.deepcopy(st["bu_states"])
    for x in bus:
        if x["bu_id"] == "consumer_goods":
            x["natural_capital_debt"] = 84.0
    asyncio.run(db.update_latest_global_state(sid, copy.deepcopy(st["global_state"]), bus))
    r = client.get(f"/api/simulations/{sid}/sdg-dashboard", cookies=ck)
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    eng = calc_group_sdg_score(bus, st["global_state"])
    assert d["group_sdg_score"] == eng["group_sdg_score"]
    assert {b: v["sdg_score"] for b, v in d["bu_scores"].items()} == \
           {b: round(v["sdg_score"], 1) for b, v in eng["bu_scores"].items()}
    assert "alerts" in d and "materiality_map" in d


# ── IMP-06 systemic-risk toggles ──────────────────────────────────────────────

def test_systemic_toggle_reader_precedence():
    from systemic_risk_engine import systemic_toggle_on, SYSTEMIC_TOGGLES_FLAG
    assert systemic_toggle_on({}, "systemic_risk_enabled") is True
    assert systemic_toggle_on(None, "systemic_risk_enabled") is True
    assert systemic_toggle_on({"pedagogical_overrides": {"black_swan_events_enabled": False}},
                              "black_swan_events_enabled") is False
    gs = {"active_event_flags": {SYSTEMIC_TOGGLES_FLAG: {"black_swan_events_enabled": True}},
          "pedagogical_overrides": {"black_swan_events_enabled": False}}
    assert systemic_toggle_on(gs, "black_swan_events_enabled") is True  # the stamped bag wins


def test_toggles_off_mean_no_wacc_adjustment_no_swan_draw_and_no_foreshadowing():
    from systemic_risk_engine import SYSTEMIC_TOGGLES_FLAG
    bus = build_bu_states()
    on = _tick(_gs(7), bus)
    gs_off = _gs(7)
    gs_off["active_event_flags"][SYSTEMIC_TOGGLES_FLAG] = {
        "systemic_risk_enabled": False, "black_swan_events_enabled": False,
        "npc_cascading_enabled": False, "foreshadowing_signals_enabled": False}
    gs_off["active_event_flags"]["forced_black_swan"] = "sovereign_debt_crisis"
    gs_off["pedagogical_overrides"]["black_swan_events_enabled"] = True  # the bag, not the override, decides
    off = _tick(gs_off, bus)
    assert "esg_adjusted_wacc" in on["events"] and "esg_adjusted_wacc" not in off["events"]
    assert off["events"].get("_systemic_risk_disabled") is True
    assert off["events"].get("_black_swan_events_disabled") is True
    assert not off["events"].get("black_swan_events")            # the forced swan did not fire …
    assert "forced_black_swan" not in off["events"]              # … and is not consumed (the router keeps the flag)
    assert on["events"].get("black_swan_events") or on["events"].get("active_black_swans") is not None
    assert "foreshadowing_signals" not in off["events"]
    assert "materiality_shocks" not in off["events"] and "systemic_tipping" not in off["events"]
    # the settings live in a private bag: none of them is a decision flag
    from flag_utils import collect_all_flags
    assert not {"systemic_risk_enabled", "black_swan_events_enabled"} & collect_all_flags(off["global_state"]["active_event_flags"])


def test_cascade_switch_gates_npc_cascades(monkeypatch):
    import systemic_risk_engine as sre
    from round_logic import run_new_engines
    fake = [{"npc_id": "activist_investor", "reaction": "divestment_campaign", "narrative": "x",
             "effects": {"reputation_delta": -5}, "round_triggered": 4}]
    monkeypatch.setattr(sre, "evaluate_npc_cascades", lambda sats, rn, active=None: list(fake))
    bus = build_bu_states()

    def run(enabled):
        gs = _gs(4)
        gs["active_event_flags"][sre.SYSTEMIC_TOGGLES_FLAG] = {"npc_cascading_enabled": enabled}
        return run_new_engines(round_number=4, global_state=gs, bu_states=copy.deepcopy(bus), events={})

    assert run(True).get("npc_cascade_events")
    off = run(False)
    assert not off.get("npc_cascade_events") and off.get("_npc_cascading_disabled") is True


# ── IMP-07 materiality shock ──────────────────────────────────────────────────

def test_materiality_shock_posture_reads_the_teams_own_r2_matrix():
    from systemic_risk_engine import materiality_shock_posture
    scores = {
        "water_scarcity": {"title": "Water Scarcity in Deccan Plateau", "placed_quadrant": "q1",
                           "esrs_reference": "ESRS E3 (Water & Marine Resources)"},
        "tier3_labor": {"title": "Tier-3 Supply Chain Labor Practices", "placed_quadrant": "q4"},
        "led_bulbs": {"title": "LED Bulb Swaps", "placed_quadrant": "q1"},
    }
    water = materiality_shock_posture("water_crisis", scores)
    assert water["posture"] == "anticipated" and water["flow_multiplier"] == 0.5
    assert water["anticipated_issues"] == ["water_scarcity"]
    labour = materiality_shock_posture("supply_chain_collapse", scores)
    assert labour["posture"] == "missed" and labour["flow_multiplier"] == 1.0 and labour["related_issues"] == ["tier3_labor"]
    assert materiality_shock_posture("biodiversity_tipping", scores)["posture"] == "unassessed"
    assert materiality_shock_posture("water_crisis", None)["posture"] == "unassessed"


class _Zero:
    def random(self):
        return 0.0


def _force_water_shock(monkeypatch):
    import systemic_risk_engine as sre
    monkeypatch.setattr(sre, "MATERIALITY_SHOCKS", {"water_crisis": sre.MATERIALITY_SHOCKS["water_crisis"]})
    monkeypatch.setattr(sre, "event_rng", lambda *a, **k: _Zero())


def test_materiality_shock_is_a_one_round_opex_flow_sized_by_the_r2_bet(monkeypatch):
    from black_swan_registry import get_difficulty_config
    bus = build_bu_states()
    quiet = _tick(_gs(6), bus)                       # no shock (the seeded roll misses)
    _force_water_shock(monkeypatch)
    missed = _tick(_gs(6, materiality_issue_scores={
        "water_scarcity": {"title": "Water Scarcity", "placed_quadrant": "q4"}}), bus)
    anticipated = _tick(_gs(6, materiality_issue_scores={
        "water_scarcity": {"title": "Water Scarcity", "placed_quadrant": "q1"}}), bus)

    shock = missed["events"]["materiality_shocks"][0]
    assert shock["posture"] == "missed" and shock["severity"] == "critical"
    total_opex = sum(b["opex_base"] for b in quiet["bu_states"])  # the base the flow was sized on … roughly
    tier = get_difficulty_config("advanced")["impact_multiplier"]
    cost = shock["forced_reallocation_cost"]
    assert cost > 0 and cost == missed["events"]["materiality_shock_cost"]
    assert abs(cost - 0.10 * total_opex * tier) / cost < 0.25   # 10 % of Σ OPEX × tier, sized mid-tick
    # a FLOW: the persisted OPEX base is untouched, the cash left the treasury
    for q, m in zip(quiet["bu_states"], missed["bu_states"]):
        assert abs(q["opex_base"] - m["opex_base"]) < 1.0, (q["bu_id"], q["opex_base"], m["opex_base"])
    drop = quiet["global_state"]["corporate_treasury"] - missed["global_state"]["corporate_treasury"]
    assert abs(drop - cost) / cost < 0.02, (drop, cost)
    assert "$" in shock["narrative"] and "immaterial" in shock["narrative"]
    # the team that placed it as financially material pays half, as a warning
    a = anticipated["events"]["materiality_shocks"][0]
    assert a["posture"] == "anticipated" and a["severity"] == "warning"
    assert abs(a["forced_reallocation_cost"] - cost / 2) / cost < 0.02
    modal = [s for s in anticipated["events"]["custom_black_swans"] if "MATERIALITY" in s["title"]][0]
    assert modal["severity"] == "warning"


# ── IMP-04 journey panels ─────────────────────────────────────────────────────

def test_journey_panels_are_labelled_reflection_exercises_and_default_off(monkeypatch):
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    from journey_improvements import (R6_REVELATION_MECHANIC, R7_BUDGET_ALLOCATION_VARIANT,
                                      R8_STAKEHOLDER_TRIBUNAL_VARIANT, JOURNEY_REFLECTION_NOTE)
    for payload in (R6_REVELATION_MECHANIC, R7_BUDGET_ALLOCATION_VARIANT, R8_STAKEHOLDER_TRIBUNAL_VARIANT):
        assert payload["engine_impact"] is False and payload["note"] == JOURNEY_REFLECTION_NOTE
    assert "not applied by the engine" in R7_BUDGET_ALLOCATION_VARIANT["instruction"]
    for k in ("r6_revelation_enabled", "r7_budget_allocation_enabled", "r8_tribunal_enabled"):
        monkeypatch.delitem(admin_shared._god_mode_settings, k, raising=False)
    client = TestClient(app)
    feats = {f["key"]: f for f in client.get("/api/admin/scaffolding-status").json()["features"]}
    for k in ("r6_revelation_enabled", "r7_budget_allocation_enabled", "r8_tribunal_enabled"):
        assert feats[k]["enabled"] is False, k
        assert "reflection" in feats[k]["description"].lower()
    # the note reaches the player projection of every panel
    client.cookies.clear()
    assert client.get("/api/admin/journey/r6-revelation").json()["revelation"]["note"] == JOURNEY_REFLECTION_NOTE
    assert client.get("/api/admin/journey/mechanic-variant/7").json()["variant"]["note"] == JOURNEY_REFLECTION_NOTE
    assert client.get("/api/admin/journey/mechanic-variant/8").json()["variant"]["engine_impact"] is False


def test_the_cockpit_files_journey_answers_to_the_player_endpoint_not_god_mode():
    src = (Path(__file__).resolve().parent.parent.parent / "frontend/app/components/ExecutiveCockpit.js").read_text(encoding="utf-8")
    assert "journey_r6_response_" not in src and "journey_r7_allocs_" not in src and "journey_r8_responses_" not in src
    assert "/journey-response" in src and "postJourneyResponse('r7_allocs', allocs)" in src
    assert "pedToggles.r6_revelation_enabled === true" in src
    assert "pedToggles.r7_budget_allocation_enabled === true" in src
    assert "pedToggles.r8_tribunal_enabled === true" in src
    ped = (Path(__file__).resolve().parent.parent.parent / "frontend/app/components/PedagogicalScaffolding.js").read_text(encoding="utf-8")
    assert "impacts will apply at round resolution" not in ped and "consequences will unfold" not in ped
    assert "no engine impact" in ped


# ── IMP-06 / IMP-06b live commit path ─────────────────────────────────────────

def test_cohort_toggles_reach_the_live_commit_path():
    from fastapi.testclient import TestClient
    from main import app
    from conftest import rotate_facilitator_password
    from router import _commit_timestamps
    from systemic_risk_engine import SYSTEMIC_TOGGLES_FLAG
    client = TestClient(app)
    gm = client.post("/api/admin/facilitators/login",
                     json={"facilitator_id": "god_mode", "password": os.environ["MASTER_PASSWORD"]}).cookies
    r = client.post("/api/admin/facilitators", json={"name": "WP22", "role": "facilitator"}, cookies=gm)
    fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
    pw = rotate_facilitator_password(client, fid, otp)
    client.cookies.clear()
    ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies

    def cohort(name, ped=None, settings=None):
        client.cookies.clear()
        cid = client.post("/api/simulations/start", json={"cohort_name": name, "facilitator_id": fid},
                          cookies=ck).json()["session_id"]
        if ped:
            assert client.put(f"/api/admin/cohort/{cid}/pedagogical-settings", json=ped, cookies=ck).status_code == 200
        if settings:
            assert client.patch(f"/api/admin/sessions/{cid}/cohort-settings", json=settings, cookies=gm).status_code == 200
        g = client.post(f"/api/admin/{cid}/generate-player", json={"player_name": "T"}, cookies=ck).json()
        pid, p0 = g["player_id"], g["password"]
        client.cookies.clear()
        assert client.post("/api/simulations/change-password",
                           json={"player_id": pid, "old_password": p0, "new_password": "T#2026pw"}).status_code == 200
        lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": "T#2026pw"}).json()
        sid, tok = lr["session_id"], lr["player_token"]
        h = {"Authorization": f"Bearer {tok}", "X-Player-Id": pid}
        dash = client.get(f"/api/simulations/{sid}/dashboard", headers=h).json()
        _commit_timestamps.pop(sid, None)
        r = client.post(f"/api/simulations/{sid}/commit-turn", headers=h, json={
            "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "investment_ratio": 0.2,
                           "choice_selected": "option_b"} for b in dash["business_units"]],
            "force_override_cfo": True, "expected_round": 1})
        assert r.status_code == 201, r.text[:300]
        return r.json()

    base = cohort("wp22-base")
    assert "biodiversity" in base["events"] and "esg_adjusted_wacc" in base["events"]
    assert base["global_state"]["active_event_flags"][SYSTEMIC_TOGGLES_FLAG] == {
        "systemic_risk_enabled": True, "black_swan_events_enabled": True,
        "npc_cascading_enabled": True, "foreshadowing_signals_enabled": True}
    assert "pedagogical_overrides" not in base["global_state"]

    # IMP-06b: the cohort toggles modal reaches run_new_engines
    bio_off = cohort("wp22-bio-off", ped={"biodiversity_engine_enabled": False})
    assert "biodiversity" not in bio_off["events"]
    assert "pedagogical_overrides" not in bio_off["global_state"]  # settings are not state

    # IMP-06: the systemic-risk switches reach the engine
    sys_off = cohort("wp22-sys-off", settings={
        "systemic_risk_enabled": False, "black_swan_events_enabled": False,
        "npc_cascading_enabled": False, "foreshadowing_signals_enabled": False})
    assert sys_off["global_state"]["active_event_flags"][SYSTEMIC_TOGGLES_FLAG] == {
        "systemic_risk_enabled": False, "black_swan_events_enabled": False,
        "npc_cascading_enabled": False, "foreshadowing_signals_enabled": False}
    assert "esg_adjusted_wacc" not in sys_off["events"]
    assert sys_off["events"].get("_systemic_risk_disabled") is True
    assert sys_off["events"].get("_black_swan_events_disabled") is True
