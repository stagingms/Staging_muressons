"""Black-swan semantics and the difficulty vocabulary — audit 2026-09-04
IMP-05, FIN-08, FIN-09, FLAG-8, IMP-11 · WP-23.

IMP-05  The revenue / OPEX percentages were written into the persisted BU
        base — permanent erosion while the narrative said "for N round(s)"
        and the headline showed the cash hit alone (4–5× understated).
FIN-08  Sessions carry foundation/advanced/expert; the tier table knew
        easy/standard/expert, so "Classroom (Easy)" silently got standard.
        Four tier keys were read by nothing.
FIN-09  The regulator's enforcement fine was uniform($5M, $25M) every
        enforcement round, uncapped by tier, ~17% of annual revenue per round.
FLAG-8  Three readers tested a top-level key for flags that live in the
        rN_flags lists: ethical_ai_overhaul (swan modifier), hard_engineering
        (R7 CI pulse reversal), carbon_deferred (carbon futures market).
IMP-11  The embargo modifier read supply_chain_transparency_avg, which
        nothing writes, so it applied forever.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick  # noqa: E402
import black_swan_registry as bsr  # noqa: E402
from tests.test_comprehensive import make_global, make_bus  # noqa: E402


def _decisions(bus, choice="option_b"):
    return [{"bu_id": b["bu_id"], "capex_allocated": 1.0, "investment_ratio": 0.0, "choice_selected": choice}
            for b in bus]


def _tick(gs, bus, paradigm="legacy_abc"):
    t = process_tick(current_global=gs, current_bus=bus, decisions=_decisions(bus), dividends_paid=0,
                     crisis_severity=0.0, imitation_decay_rate=0.05, decision_paradigm=paradigm,
                     emergency_credit_used=False)
    ng, nb, ev = t["global_state"], t["bu_states"], t["events"]
    # the router merges the round's events into the flags the next tick reads
    merged = dict(gs["active_event_flags"]); merged.update(ng.get("active_event_flags", {})); merged.update(ev)
    ng["active_event_flags"] = merged
    return ng, nb, ev


def _play(force_at: dict[int, str] | None = None, rounds=(4, 5, 6, 7), seed="wp23-seed", tier="advanced"):
    gs = make_global(round_number=4, treasury=60_000_000, flags={"stochastic_seed": seed, "difficulty_tier": tier})
    bus = make_bus()
    for b in bus:
        b.setdefault("staff_burnout_index", 10.0)
        b.setdefault("governance_risk_score", 15.0)
    out = {}
    for r in rounds:
        gs["round_number"] = r
        gs["active_event_flags"]["forced_black_swan"] = (force_at or {}).get(r)
        gs, bus, ev = _tick(gs, bus)
        out[r] = {"treasury": gs["corporate_treasury"],
                  "revenue": round(sum(b["revenue_base"] for b in bus), 2),
                  "opex": round(sum(b["opex_base"] for b in bus), 2),
                  "fired": [e["event_id"] for e in ev.get("black_swan_events", [])],
                  "events": ev}
    return out


# ── IMP-05 ───────────────────────────────────────────────────────────────────

def test_a_black_swan_revenue_shock_is_a_flow_for_its_duration_not_permanent_erosion():
    base = _play()
    sov = _play({4: "sovereign_debt_crisis"})          # −10% revenue for duration 2, −12% treasury
    assert sov[4]["fired"] == ["sovereign_debt_crisis"]
    # the persisted revenue base is restored every round (F-04: a shock is a flow)
    for r in (4, 5, 6, 7):
        assert sov[r]["revenue"] == pytest.approx(base[r]["revenue"], abs=0.05), r   # cent-level rounding
    # the treasury gap opens at the trigger, widens once for the continuing round, then holds
    gap = {r: round(sov[r]["treasury"] - base[r]["treasury"], 2) for r in (4, 5, 6, 7)}
    assert gap[4] < 0
    assert gap[5] < gap[4] - 1_000_000, "the second round of a 2-round event still costs revenue"
    assert abs(gap[6] - gap[5]) < 1_000_000, "after the duration the erosion stops"
    assert abs(gap[7] - gap[6]) < 1_000_000
    # the continuing round records its flow explicitly
    assert sov[5]["events"].get("black_swan_continuing_flows"), "R5 is the event's second round"
    assert not sov[6]["events"].get("black_swan_continuing_flows")


def test_the_headline_is_the_all_in_cost_not_the_cash_hit_alone():
    gs = make_global(round_number=4, treasury=60_000_000,
                     flags={"stochastic_seed": "wp23", "difficulty_tier": "advanced"})
    bus = make_bus()
    res = bsr.evaluate_black_swans(gs, bus, 4, difficulty_tier="advanced", forced_event_id="sovereign_debt_crisis")
    ev = res["events_triggered"][0]
    ia = ev["impacts_applied"]
    revenue = sum(b["revenue_base"] for b in bus)
    assert ia["flow_cost_per_round"] == pytest.approx(0.10 * revenue, rel=1e-6)
    assert ia["flow_cost_total"] == pytest.approx(2 * 0.10 * revenue, rel=1e-6)
    assert ia["headline_cost"] == pytest.approx(ia["treasury_hit"] + ia["flow_cost_total"], abs=0.01)
    assert ia["headline_cost"] > 2 * ia["treasury_hit"]
    assert f"${ia['headline_cost']:,.0f}" in ev["narrative"]


# ── FIN-08 ───────────────────────────────────────────────────────────────────

def test_tier_table_speaks_the_session_vocabulary():
    assert set(bsr.DIFFICULTY_TIERS) == {"foundation", "advanced", "expert"}
    assert bsr.get_difficulty_config("foundation")["impact_multiplier"] < bsr.get_difficulty_config("advanced")["impact_multiplier"] \
        < bsr.get_difficulty_config("expert")["impact_multiplier"]
    # aliases keep old callers honest; unknown → advanced
    assert bsr.get_difficulty_config("easy") is bsr.DIFFICULTY_TIERS["foundation"]
    assert bsr.get_difficulty_config("standard") is bsr.DIFFICULTY_TIERS["advanced"]
    assert bsr.get_difficulty_config("nonsense") is bsr.DIFFICULTY_TIERS["advanced"]
    # the dead keys are gone; every remaining key has a reader
    for cfg in bsr.DIFFICULTY_TIERS.values():
        assert not {"treasury_floor", "bailout_amount", "natural_decay_rate"} & set(cfg)
        assert {"impact_multiplier", "npc_max_fine", "covenant_trigger_ratio"} <= set(cfg)


def test_foundation_hurts_less_than_expert_on_the_same_swan():
    gs = make_global(round_number=4, treasury=60_000_000, flags={"stochastic_seed": "wp23"})
    bus = make_bus()
    f = bsr.evaluate_black_swans(copy.deepcopy(gs), copy.deepcopy(bus), 4, difficulty_tier="foundation",
                                 forced_event_id="sovereign_debt_crisis")["events_triggered"][0]["impacts_applied"]
    e = bsr.evaluate_black_swans(copy.deepcopy(gs), copy.deepcopy(bus), 4, difficulty_tier="expert",
                                 forced_event_id="sovereign_debt_crisis")["events_triggered"][0]["impacts_applied"]
    assert f["treasury_hit"] < e["treasury_hit"]
    assert f["treasury_hit"] == pytest.approx(0.7 * 0.12 * 60_000_000, rel=1e-6)


# ── FIN-09 ───────────────────────────────────────────────────────────────────

def test_regulator_fine_is_capped_by_tier_and_turnover_and_the_message_matches():
    from npc_stakeholders import process_npc_tick, create_initial_npc_state
    tier_cap = bsr.get_difficulty_config("advanced")["npc_max_fine"]
    for seed in ("s1", "s2", "s3", "s4", "s5"):
        gs = make_global(round_number=6, treasury=80_000_000, reputation=5,
                         flags={"stochastic_seed": seed, "difficulty_tier": "advanced"})
        bus = make_bus()
        for b in bus:
            b["governance_risk_score"] = 95.0     # the regulator's satisfaction collapses → enforcement
            b["social_license_score"] = 5.0
            b["carbon_intensity"] = 95.0
        npc = create_initial_npc_state()
        npc["npcs"]["regulator"]["satisfaction"] = 5.0
        # staged escalation: a relationship worsens one tier per round, so
        # walk the regulator down to "enforcement" over a few rounds
        diag = {}
        for rnd in (4, 5, 6, 7, 8):
            t0 = gs["corporate_treasury"]
            _, diag = process_npc_tick(npc, gs, bus, {}, rnd)
            if "regulatory_fine" in diag:
                break
        if "regulatory_fine" not in diag:
            continue
        fine = diag["regulatory_fine"]
        basis = diag["regulatory_fine_basis"]
        annual = 2 * sum(b["revenue_base"] for b in bus)
        assert fine <= tier_cap
        assert fine <= 0.04 * annual + 0.01
        assert fine == pytest.approx(min(basis["drawn"], tier_cap, round(0.04 * annual, 2)), abs=0.01)
        assert gs["corporate_treasury"] == pytest.approx(t0 - fine, abs=0.01)
        msg = next(a["message"] for a in diag["npc_actions"] if a.get("npc_id") == "regulator")
        assert f"€{fine / 1_000_000:.1f}M fine" in msg, msg
        break
    else:
        pytest.fail("no enforcement fine fired across five seeds — fixture no longer reaches enforcement")


# ── FLAG-8 / IMP-11 ─────────────────────────────────────────────────────────

def test_list_held_ethical_ai_overhaul_lowers_the_ai_wave_probability():
    gs_plain = make_global(round_number=6, flags={"stochastic_seed": "wp23"})
    gs_flag = make_global(round_number=6, flags={"stochastic_seed": "wp23", "r6_flags": ["ethical_ai_overhaul"]})
    bus = make_bus()
    p_plain = bsr.evaluate_black_swans(gs_plain, copy.deepcopy(bus), 6, forced_event_id="ai_disruption_wave")["events_triggered"][0]["probability"]
    p_flag = bsr.evaluate_black_swans(gs_flag, copy.deepcopy(bus), 6, forced_event_id="ai_disruption_wave")["events_triggered"][0]["probability"]
    assert p_flag == pytest.approx(max(0.0, p_plain - 0.05), abs=1e-6)


def test_supply_chain_transparency_is_read_from_the_key_the_engine_writes():
    bus = make_bus()
    lo = make_global(round_number=5, flags={"stochastic_seed": "wp23", "supply_chain_transparency": 20})
    hi = make_global(round_number=5, flags={"stochastic_seed": "wp23", "supply_chain_transparency": 90})
    p_lo = bsr.evaluate_black_swans(lo, copy.deepcopy(bus), 5, forced_event_id="supply_chain_embargo")["events_triggered"][0]["probability"]
    p_hi = bsr.evaluate_black_swans(hi, copy.deepcopy(bus), 5, forced_event_id="supply_chain_embargo")["events_triggered"][0]["probability"]
    assert p_lo > p_hi, "a transparent supply chain must lower the embargo probability"


def test_r5_hard_engineering_pulse_reverts_in_r7_from_the_list_held_flag():
    from round_logic import _revert_r5_hard_engineering_pulse
    gs = make_global(round_number=7, flags={"r5_flags": ["hard_engineering"]})
    bus = make_bus()
    ci_before = [b["carbon_intensity"] for b in bus]
    extra = {}
    _revert_r5_hard_engineering_pulse(gs, bus, extra, 7)
    assert extra.get("hard_engineering_pulse_reverted") is True
    assert [b["carbon_intensity"] for b in bus] == [max(0.0, round(c - 3.0, 2)) for c in ci_before]


def test_carbon_futures_market_opens_for_a_list_held_carbon_deferred_flag():
    gs = make_global(round_number=4, treasury=60_000_000,
                     flags={"stochastic_seed": "wp23", "r3_flags": ["carbon_deferred"], "decision_paradigm": "advanced_climate"})
    bus = make_bus()
    _, _, ev = _tick(gs, bus, paradigm="advanced_climate")
    assert "carbon_offset_market" in ev, sorted(k for k in ev if "carbon" in k)[:12]
