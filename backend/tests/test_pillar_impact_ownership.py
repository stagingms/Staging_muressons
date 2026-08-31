"""Pillar-mode impact ownership (2026-08-31 follow-up branch).

The ownership rule these tests pin, per design ruling:

  R1-R9:  in pillar mode the ROUTER is the single applier of option impacts
          (the pillar aggregates, scaled by effectiveness). The legacy
          translation exists for flags and round bookkeeping only — the
          translated A/B/C option's config impacts must NOT also apply.
  R10:    the finale is the exception — the pillar selections MAP to an
          A/B/C ending, and that ending's FULL impact set (treasury,
          reputation, revenue, CI, governance, SLO, NCD, mechanics) is the
          single impact source; the router does NOT apply R10 pillar-option
          aggregates on top.

Before the fix, test 1 fails on every R1-R9 round (the translated legacy
option's reputation / revenue_delta / carbon_intensity_delta /
governance_risk_delta stacked on top of the router aggregates) and test 2
fails on R10 SLO/NCD (the ending's licence and debt effects never landed
in pillar mode).
"""

import random

import pytest

# Seed chosen so the R5 cyclone roll (first random draw in that handler)
# misses: random.seed(15) -> 0.9652 > every shipped threshold.
_SEED = 15

_BASE_TREASURY = 100_000_000.0
_BASE_REP = 70.0
_BASE_SLO = 50.0
_BASE_NCD = 50.0
_BASE_CI = 50.0
_BASE_GOV = 20.0
_BASE_REV = 10_000_000.0


def _mk_bus():
    return [{"bu_id": b, "revenue_base": _BASE_REV, "opex_base": 7_000_000.0,
             "carbon_intensity": _BASE_CI, "social_license_score": _BASE_SLO,
             "governance_risk_score": _BASE_GOV, "natural_capital_debt": _BASE_NCD,
             "water_dependency": 30.0, "staff_burnout_index": 10.0,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def _mk_gs(rnd):
    return {"corporate_treasury": _BASE_TREASURY, "group_reputation": _BASE_REP,
            "green_transition_fund": 0.0, "synergy_multiplier": 1.0,
            "round_number": rnd, "active_event_flags": {},
            "workforce_readiness": 50.0, "climate_resilience": 0.5,
            "session_id": "", "cost_of_capital": 0.08}


def _pillar_post_tick(rnd, translated_choice):
    """post_tick exactly as the router invokes it in pillar mode: the router
    has already applied the aggregates BEFORE this call, and events carry the
    pillar markers. Any state movement here therefore comes from post_tick
    itself — which for R1-R9 must be only the designed both-paradigm
    mechanics, never the translated option's config impacts."""
    from round_logic import post_tick
    random.seed(_SEED)
    gs, bus = _mk_gs(rnd), _mk_bus()
    events = {"pillar_cost_applied": -1_000_000,
              "pillar_aggregate_impacts": {},
              "pillar_flags": []}
    decs = [{"choice_selected": translated_choice, "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(rnd, gs, bus, decs, events, {})
    return gs, bus, extra


@pytest.mark.parametrize("rnd", range(1, 10))
@pytest.mark.parametrize("choice", ["option_a", "option_b", "option_c"])
def test_r1_r9_pillar_mode_translated_option_impacts_do_not_apply(rnd, choice):
    gs, bus, extra = _pillar_post_tick(rnd, choice)
    moved = {}
    if gs["group_reputation"] != _BASE_REP:
        moved["reputation"] = round(gs["group_reputation"] - _BASE_REP, 2)
    if gs["corporate_treasury"] != _BASE_TREASURY:
        moved["treasury"] = round(gs["corporate_treasury"] - _BASE_TREASURY, 2)
    for bu in bus:
        for field, base in (("revenue_base", _BASE_REV),
                            ("carbon_intensity", _BASE_CI),
                            ("governance_risk_score", _BASE_GOV),
                            ("social_license_score", _BASE_SLO),
                            ("natural_capital_debt", _BASE_NCD)):
            if bu[field] != base:
                moved.setdefault(field, {})[bu["bu_id"]] = round(bu[field] - base, 2)
    assert not moved, (
        f"R{rnd} translated {choice}: post_tick moved state in pillar mode — "
        f"the router already applied the pillar aggregates, so this is a "
        f"double-application of the legacy option's config: {moved}")


@pytest.mark.parametrize("choice", ["option_a", "option_b", "option_c"])
def test_r10_pillar_mode_ending_impacts_fully_apply(choice):
    from round_configs import get_round_options
    imp = (get_round_options(10).get(choice) or {}).get("impacts") or {}
    gs, bus, extra = _pillar_post_tick(10, choice)

    slo_cfg = imp.get("social_license_delta", 0) or 0
    ncd_cfg = imp.get("natural_capital_debt_delta", 0) or 0
    tre_cfg = imp.get("treasury", 0) or 0

    # Option B spins off the weakest BU (revenue/opex zeroed) — exclude it
    # from the per-BU assertions; its SLO/NCD are unaffected by the spinoff.
    for bu in bus:
        assert bu["social_license_score"] == pytest.approx(_BASE_SLO + slo_cfg), (
            f"R10 {choice} {bu['bu_id']}: ending SLO delta {slo_cfg} did not land "
            f"in pillar mode (got {bu['social_license_score'] - _BASE_SLO})")
        assert bu["natural_capital_debt"] == pytest.approx(_BASE_NCD + ncd_cfg), (
            f"R10 {choice} {bu['bu_id']}: ending NCD delta {ncd_cfg} did not land "
            f"in pillar mode (got {bu['natural_capital_debt'] - _BASE_NCD})")
    assert gs["corporate_treasury"] == pytest.approx(_BASE_TREASURY + tre_cfg), (
        f"R10 {choice}: ending treasury {tre_cfg} misapplied in pillar mode "
        f"(moved {gs['corporate_treasury'] - _BASE_TREASURY})")


def test_router_helper_applies_aggregates_with_effectiveness_scaling():
    """Direct unit test of the extracted router applier: reputation on the
    group, per-BU deltas revenue-weighted, everything scaled by
    effectiveness. The call site applies it for R1-R9 and skips it for R10
    (events carry pillar_aggregates_skipped_r10 there)."""
    from router import _apply_pillar_aggregate_impacts
    gs = {"group_reputation": 50.0}
    bus = [{"bu_id": "a", "revenue_base": 30_000_000.0, "opex_base": 1.0,
            "carbon_intensity": 50.0, "social_license_score": 50.0,
            "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
            "water_dependency": 30.0, "staff_burnout_index": 10.0},
           {"bu_id": "b", "revenue_base": 10_000_000.0, "opex_base": 1.0,
            "carbon_intensity": 50.0, "social_license_score": 50.0,
            "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
            "water_dependency": 30.0, "staff_burnout_index": 10.0}]
    events = {}
    agg = {"reputation": 6, "social_license_delta": 4, "burnout_delta": -2,
           "revenue_delta": 300_000}
    _apply_pillar_aggregate_impacts(gs, bus, events, agg, effectiveness=0.5)
    assert gs["group_reputation"] == pytest.approx(53.0)      # 6 × 0.5
    # Revenue: flat per BU (NOT revenue-weighted), effectiveness-scaled
    assert bus[0]["revenue_base"] == pytest.approx(30_150_000.0)
    assert bus[1]["revenue_base"] == pytest.approx(10_150_000.0)
    assert events["pillar_revenue_delta_applied"] == pytest.approx(150_000.0)
    # SLO: delta 4 × 0.5 = 2, revenue-weighted × num_bus: a gets 2×0.75×2=3, b 2×0.25×2=1
    assert bus[0]["social_license_score"] == pytest.approx(53.0)
    assert bus[1]["social_license_score"] == pytest.approx(51.0)
    # burnout is NOT effectiveness-scaled (visible HR impact), flat per BU
    assert bus[0]["staff_burnout_index"] == pytest.approx(8.0)
    assert events["pillar_burnout_delta_applied"] == -2


# ═════════════════════════════════════════════════════════════════
#  Pillar revenue design invariants (SPEC_Pillar_Revenue_Impacts v2)
# ═════════════════════════════════════════════════════════════════

def _pillar_revenue_surface():
    from pillar_configs import PILLAR_OPTIONS
    out = {}
    for r, cfg in PILLAR_OPTIONS.items():
        for area, acfg in (cfg.get("areas") or {}).items():
            for opt, ocfg in (acfg.get("options") or {}).items():
                rv = (ocfg.get("impacts") or {}).get("revenue_delta", 0)
                if rv:
                    out[(r, area, opt)] = rv
    return out


def test_r10_pillar_options_carry_no_revenue():
    """Design ruling: R10 pillar aggregates are skipped — the mapped ending
    owns R10 revenue. A revenue_delta on an R10 pillar option would be dead
    config (the exact defect class this whole audit exists to prevent)."""
    r10 = {k: v for k, v in _pillar_revenue_surface().items() if k[0] == 10}
    assert not r10, f"R10 pillar options must not declare revenue_delta: {r10}"


def test_pillar_revenue_values_stay_in_the_calibrated_band():
    """SPEC v2 realism band: every per-option value within ±$400K (±3.3% of a
    $12M BU), matching the evidence ceilings (severe-scandal / AI-monetisation
    class). A value outside the band means someone changed calibration without
    re-running the realism review."""
    for key, rv in _pillar_revenue_surface().items():
        assert -400_000 <= rv <= 400_000, f"{key}: {rv:+,} outside SPEC v2 band"
    # The two deliberate extremes exist and sit exactly at the band edges.
    surf = _pillar_revenue_surface()
    assert surf[(6, "operations", "monetise")] == 400_000
    assert surf[(4, "operations", "deny")] == -400_000
    assert surf[(9, "operations", "immediate_closure")] == -400_000


def test_pillar_revenue_is_aggregated_and_applied_once():
    """End-to-end through aggregation + the router applier: chosen options'
    revenue_delta sums, scales by effectiveness, lands flat on every BU."""
    from pillar_configs import aggregate_pillar_decisions
    from router import _apply_pillar_aggregate_impacts
    # NOTE: waste_to_energy + full_circular is a designed mutual-exclusivity
    # conflict in R7 (the aggregator reverses one side's impacts) — this test
    # uses heat_recovery deliberately to stay on the clean path.
    picks = {"operations": "full_circular", "energy": "heat_recovery"}
    agg = aggregate_pillar_decisions(7, picks)
    assert agg["impacts"]["revenue_delta"] == 400_000  # 350K + 50K
    gs = {"group_reputation": 50.0}
    bus = [{"bu_id": "a", "revenue_base": 12_000_000.0, "opex_base": 1.0,
            "carbon_intensity": 50.0, "social_license_score": 50.0,
            "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
            "water_dependency": 30.0, "staff_burnout_index": 10.0}]
    events = {}
    _apply_pillar_aggregate_impacts(gs, bus, events, agg["impacts"], effectiveness=1.0)
    assert bus[0]["revenue_base"] == pytest.approx(12_400_000.0)
    assert events["pillar_revenue_delta_applied"] == pytest.approx(400_000.0)
