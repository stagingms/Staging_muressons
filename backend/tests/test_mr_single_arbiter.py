"""Single M_R arbiter + EU AI Act enforcement (DEEP-1/2/3, branch fix/mr-single-arbiter).

Design rulings (2026-08-31):
  - terminal_valuation.calculate_mr's semantics are canonical: synergy gated on
    flag AND multiplier >= 0.80 (ramped), GAME-2 ramps replace hard cliffs, and
    one global clamp [0.0, 2.05] governs the FINAL M_R after pathway bonuses
    and mr_cap. The R10 engine must award exactly what calculate_mr computes.
  - EU AI Act (ai_monetised): $3M conformity assessment + governance +5 once at
    R7, then $1M/round ongoing monitoring R8-R10.

All three test families are RED against the pre-fix engine:
  - the EU AI Act enforcement never fires (dead code in the R6-only handler);
  - the engine awards cliff-based, unclamped M_R that diverges from the
    projection players see (consequence_dna/pedagogical use calculate_mr);
  - pathway stacking exceeds 2.05 and penalty stacking goes below 0.
"""

import random
import sys

import pytest


def _mk_bus(slo=50.0, burnout=10.0):
    return [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
             "carbon_intensity": 10.0, "social_license_score": slo,
             "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
             "water_dependency": 30.0, "staff_burnout_index": burnout,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def _mk_gs(rnd, workforce=50.0):
    return {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
            "green_transition_fund": 0.0, "synergy_multiplier": 1.0,
            "round_number": rnd, "active_event_flags": {},
            "workforce_readiness": workforce, "climate_resilience": 0.5,
            "session_id": "", "cost_of_capital": 0.08}


def _run_r10(choice, prev_flags, bus, gs):
    from round_logic import post_tick
    random.seed(11)
    decs = [{"choice_selected": choice, "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(10, gs, bus, decs, {}, prev_flags)
    return extra


# ═════════════════════════════════════════════════════════════════
#  1. EU AI Act enforcement actually fires (DEEP-1)
# ═════════════════════════════════════════════════════════════════

def _run_round(rnd, prev_flags, gs=None, bus=None):
    from round_logic import post_tick
    random.seed(11)
    gs = gs or _mk_gs(rnd)
    bus = bus or _mk_bus()
    decs = [{"choice_selected": "option_b", "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(rnd, gs, bus, decs, {}, prev_flags)
    return gs, bus, extra


def test_eu_ai_act_assessment_fires_once_at_r7():
    prev = {"ai_monetised": True}
    gs, bus, extra = _run_round(7, prev)
    comp = extra.get("eu_ai_act_compliance")
    assert comp, "R7 with ai_monetised must charge the conformity assessment"
    assert comp["cost"] == 3_000_000
    # R7 option_b itself costs -5M (green-fund path) — the assessment is on top.
    assert gs["corporate_treasury"] == pytest.approx(100_000_000.0 - 5_000_000 - 3_000_000)
    from round_configs import get_round_options
    _gov_opt = (get_round_options(7)["option_b"].get("impacts") or {}).get("governance_risk_delta", 0)
    for bu in bus:
        # +5 from the assessment, plus whatever R7 option_b itself applies.
        assert bu["governance_risk_score"] == pytest.approx(20.0 + 5 + _gov_opt)
    assert gs["active_event_flags"].get("eu_ai_act_assessed") is True


def test_eu_ai_act_monitoring_recurs_after_assessment():
    prev = {"ai_monetised": True, "eu_ai_act_assessed": True}
    for rnd in (8, 9, 10):
        gs, bus, extra = _run_round(rnd, dict(prev))
        mon = extra.get("eu_ai_act_monitoring")
        assert mon, f"R{rnd}: ongoing monitoring must charge after assessment"
        assert mon["cost"] == 1_000_000
        assert gs["active_event_flags"].get("eu_ai_act_assessed") is True
        from round_configs import get_round_options
        _gov_opt = (get_round_options(rnd)["option_b"].get("impacts") or {}).get("governance_risk_delta", 0)
        for bu in bus:
            # Monitoring is a cost, not a repeated governance shock — only the
            # round's own option delta may move governance.
            assert bu["governance_risk_score"] == pytest.approx(20.0 + _gov_opt)


def test_eu_ai_act_never_charges_without_monetisation():
    gs, bus, extra = _run_round(7, {})
    assert "eu_ai_act_compliance" not in extra
    assert "eu_ai_act_monitoring" not in extra
    # Only the R7 option's own -5M cost — no AI Act charge.
    assert gs["corporate_treasury"] == pytest.approx(100_000_000.0 - 5_000_000)


# ═════════════════════════════════════════════════════════════════
#  2. The award equals the projection (DEEP-2)
# ═════════════════════════════════════════════════════════════════

def test_engine_award_equals_calculate_mr():
    """A team hovering at SLO 72 must get the RAMPED discount (-0.32), not the
    -0.40 cliff — and in general the engine's awarded M_R must equal
    calculate_mr evaluated on the same closing state."""
    from terminal_valuation import calculate_mr
    # R10 option_b applies SLO -5: start 77 -> close at 72 (inside the ramp band)
    bus = _mk_bus(slo=77.0, burnout=40.0)
    gs = _mk_gs(10, workforce=50.0)
    extra = _run_r10("option_b", {}, bus, gs)

    avg_slo = sum(b["social_license_score"] for b in bus) / len(bus)
    avg_burnout = sum(b["staff_burnout_index"] for b in bus) / len(bus)
    expected = calculate_mr(
        {}, avg_slo=avg_slo, avg_burnout=avg_burnout,
        workforce_readiness=gs.get("workforce_readiness", 50.0),
        synergy_multiplier=gs.get("synergy_multiplier", 1.0),
        hr_investment_rounds=0,
    )["mr"]
    assert extra["regenerative_multiple"] == pytest.approx(expected), (
        f"engine awarded {extra['regenerative_multiple']}, projection says {expected} "
        f"(avg SLO {avg_slo:.1f} — cliff vs ramp divergence)")


def test_waste_to_energy_alone_earns_no_synergy_premium():
    """calculate_mr canon: the synergy premium needs synergy_unlock (and the
    multiplier gate) — waste_to_energy is the ANTI-circular R7 path and must
    not qualify."""
    bus = _mk_bus(slo=90.0, burnout=40.0)
    gs = _mk_gs(10)
    extra = _run_r10("option_b", {"r7_flags": ["waste_to_energy"]}, bus, gs)
    bd = extra.get("mr_breakdown") or {}
    assert not bd.get("synergy_bonus"), (
        "waste_to_energy alone earned the synergy premium")


# ═════════════════════════════════════════════════════════════════
#  3. One global clamp [0, 2.05] (DEEP-3)
# ═════════════════════════════════════════════════════════════════

def test_pathway_bonus_stack_cannot_exceed_ceiling():
    prev = {"ending_pathway": "regulatory_shutdown",
            "materiality_aligned": True, "synergy_unlock": True,
            "ethical_ai_overhaul": True, "community_fund": True,
            "full_remediation": True, "scope_3_transparency": True}
    bus = _mk_bus(slo=87.0, burnout=5.0)
    gs = _mk_gs(10, workforce=90.0)
    gs["group_reputation"] = 90.0
    extra = _run_r10("option_a", prev, bus, gs)
    mr = extra["regenerative_multiple"]
    assert mr <= 2.05 + 1e-9, f"pathway stacking blew past the ceiling: {mr}"


def test_penalty_stack_cannot_go_negative():
    prev = {"ending_pathway": "stakeholder_revolt",
            "planet_expendable": True, "insurance_only": True}
    bus = _mk_bus(slo=1.0, burnout=95.0)
    gs = _mk_gs(10, workforce=5.0)
    gs["group_reputation"] = 5.0
    # Corporate Hardball: mr_penalty -0.30 + slo_all_penalty on an already
    # collapsed licence — the deepest shipped penalty stack.
    extra = _run_r10("option_c", prev, bus, gs)
    mr = extra["regenerative_multiple"]
    assert mr >= 0.0, f"M_R went negative: {mr} — terminal value flips sign"
