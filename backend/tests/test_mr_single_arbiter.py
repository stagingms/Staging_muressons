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


# ═════════════════════════════════════════════════════════════════
#  4. Every finale path computes M_R through calculate_mr (item 5, 2026-09-03)
# ═════════════════════════════════════════════════════════════════
#
# F-12 recorded calculate_mr as THE M_R arbiter, and this file's own docstring
# says the R10 engine must award exactly what it computes. _post_brsr_grand_finale
# did not: it built M_R inline with hard steps where the canon ramps, so the same
# named component returned different values depending on which finale ran
# (workforce readiness exactly 75: canon +0.05, BRSR +0.10; average licence just
# below 75: canon -0.204, BRSR -0.40; at exactly 75: canon -0.20, BRSR nothing).
# It also floored M_R without applying MR_CEILING and duplicated the archetype
# thresholds. Ruled DRIFT and routed through the arbiter, with the BRSR-specific
# awards passed via `pathway_bonuses`.
#
# The exception list is the point: adding a finale that scores its own way is
# then a reviewable diff carrying a reason, not something an audit rediscovers.

_MR_ARBITER_EXCEPTIONS: dict[str, str] = {
    # "module.function": "reason, ruling date, and the companion test that pins
    #                     what it does instead"
}


def _finale_functions():
    """Every function that writes a terminal `regenerative_multiple`, by AST —
    never by grep, so a function's own body is what is attributed to it."""
    import ast, os
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = {}
    for fn in sorted(f for f in os.listdir(backend) if f.endswith(".py")):
        path = os.path.join(backend, fn)
        try:
            tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
        except SyntaxError:
            continue
        mod = fn[:-3]
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            writes = calls = False
            for sub in ast.walk(node):
                # WRITES, not reads: `x["regenerative_multiple"] = ...` only.
                # A report endpoint that .get()s the value is a consumer, not a
                # second arbiter, and must not be caught here.
                if isinstance(sub, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target]
                    for t in targets:
                        if (isinstance(t, ast.Subscript)
                                and isinstance(t.slice, ast.Constant)
                                and t.slice.value == "regenerative_multiple"):
                            writes = True
                if isinstance(sub, ast.Call):
                    f = sub.func
                    name = getattr(f, "id", None) or getattr(f, "attr", None)
                    if name == "calculate_mr":
                        calls = True
            if writes:
                found[f"{mod}.{node.name}"] = calls
    return found


def test_every_finale_path_routes_through_calculate_mr():
    """A second M_R implementation is drift unless someone wrote down why."""
    offenders = [
        name for name, calls in _finale_functions().items()
        if not calls and name not in _MR_ARBITER_EXCEPTIONS
        # the arbiter's own module and the what-if projection wrap it, not duplicate it
        and not name.startswith("terminal_valuation.")
    ]
    assert not offenders, (
        f"these finale paths write regenerative_multiple without calling "
        f"calculate_mr: {offenders}.\nRoute them through the arbiter (pass any "
        f"ending-specific awards via pathway_bonuses), or add each to "
        f"_MR_ARBITER_EXCEPTIONS with a reason AND a companion test asserting "
        f"its intended divergence."
    )


def test_every_exception_names_a_reason():
    """An exception without a written reason is drift with paperwork."""
    for name, reason in _MR_ARBITER_EXCEPTIONS.items():
        assert reason and len(reason) > 20, f"{name} is exempted without a real reason"


def test_brsr_finale_uses_the_canonical_component_shapes():
    """The three shared components that used to differ. At average licence
    exactly 75 the BRSR path awarded NOTHING where the canon takes -0.20; just
    below it took the full -0.40 against the canon's ramped -0.204."""
    from terminal_valuation import calculate_mr, _ramp_fraction, _MR_RAMP_BAND_KPI
    canon = calculate_mr({}, avg_slo=75.0, avg_burnout=20.0, workforce_readiness=75.0,
                         synergy_multiplier=0.0)["breakdown"]
    assert canon.get("instability_discount") == pytest.approx(-0.20), (
        "the canon ramps the instability discount at the 75 threshold")
    assert canon.get("workforce_bonus") == pytest.approx(0.05)
    # and the BRSR finale must now produce these same shapes, not hard steps
    import inspect, round_logic
    src = inspect.getsource(round_logic._post_brsr_grand_finale)
    for stale in ('mr += 0.10', 'mr += 0.05', 'mr -= 0.40', 'if avg_sl < 75'):
        assert stale not in src, (
            f"_post_brsr_grand_finale still contains the inline hard step {stale!r}")
    assert "calculate_mr(" in src, "_post_brsr_grand_finale must call the arbiter"


def test_brsr_paradigm_can_actually_be_created():
    """The finale was unreachable: brsr_ngrbc was in the Pydantic enum and had a
    full engine path, but not in VALID_DECISION_PARADIGMS, so create_session
    answered 422 and no cohort could ever reach it."""
    import config
    assert "brsr_ngrbc" in config.VALID_DECISION_PARADIGMS


def test_the_brsr_finale_scores_through_the_arbiter_end_to_end():
    """First test to exercise _post_brsr_grand_finale at all — it had none,
    which is how it diverged unnoticed.

    Pins the three things the routing changed:
      * shared components take the CANON's ramped shapes, not hard steps
        (workforce readiness exactly 75 -> +0.05, not +0.10);
      * the BRSR-specific award arrives through `pathway_bonuses`;
      * the ceiling diagnostics exist, so MR_CEILING now applies here too.
    """
    import logging, random
    logging.disable(logging.CRITICAL)
    from round_logic import post_tick
    random.seed(11)
    bus = [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
            "carbon_intensity": 10.0, "social_license_score": 74.0,
            "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
            "water_dependency": 30.0, "staff_burnout_index": 19.0,
            "bed_capacity_utilization": 0.5, "talent_penalty": 0}
           for b in ("energy", "electronics", "agri", "software")]
    gs = {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
          "green_transition_fund": 0.0, "synergy_multiplier": 1.0, "round_number": 10,
          "active_event_flags": {"brsr_net_positive_dividend": 0.05},
          "workforce_readiness": 75.0, "climate_resilience": 0.5,
          "session_id": "", "cost_of_capital": 0.08}
    decs = [{"choice_selected": "option_b", "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(10, gs, bus, decs, {}, {}, decision_paradigm="brsr_ngrbc")
    bd = extra.get("mr_breakdown") or {}

    # Canon shapes, not hard steps. At readiness exactly 75 the old inline code
    # awarded +0.10; the ramp awards half of it.
    assert bd.get("workforce_bonus") == pytest.approx(0.05), bd
    # SLO 74 sits inside the ramp band: the canon takes -0.24, not the -0.40 cliff.
    assert bd.get("instability_discount") == pytest.approx(-0.24), bd
    # A BRSR-specific award routed through pathway_bonuses (which tier depends on
    # the track state finalise_brsr_track computes; any of the three proves it).
    assert any(k in bd for k in ("brsr_pioneer_bonus", "brsr_steward_bonus",
                                 "brsr_laggard_penalty")), bd
    assert bd.get("brsr_esg_alpha_dividend") == pytest.approx(0.05), bd
    # MR_CEILING now governs this path too; it never did before.
    assert "mr_raw" in extra and "mr_ceiling_clamped" in extra
    # And the WACC-driven multiple replaces the hard-coded 12.0.
    assert extra.get("exit_multiple_dynamic") is True
    assert extra.get("exit_multiple") != 12.0


def test_the_brsr_finale_now_earns_components_it_could_not_before():
    """Stated consequence of the ruling, pinned so nobody is surprised by it:
    routing through calculate_mr hands a BRSR ending the seven components the
    inline version had no way to award — resilience_bonus among them, which the
    canon grants BY DEFAULT when no water/insurance flag is set."""
    import logging, random
    logging.disable(logging.CRITICAL)
    from round_logic import post_tick
    random.seed(11)
    bus = [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
            "carbon_intensity": 10.0, "social_license_score": 74.0,
            "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
            "water_dependency": 30.0, "staff_burnout_index": 19.0,
            "bed_capacity_utilization": 0.5, "talent_penalty": 0}
           for b in ("energy", "electronics", "agri", "software")]
    gs = {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
          "green_transition_fund": 0.0, "synergy_multiplier": 1.0, "round_number": 10,
          "active_event_flags": {}, "workforce_readiness": 50.0,
          "climate_resilience": 0.5, "session_id": "", "cost_of_capital": 0.08}
    decs = [{"choice_selected": "option_b", "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(10, gs, bus, decs, {}, {}, decision_paradigm="brsr_ngrbc")
    bd = extra.get("mr_breakdown") or {}
    assert bd.get("resilience_bonus") == pytest.approx(0.20), (
        "a BRSR ending now earns the +0.20 resilience bonus by default — this is "
        "the documented consequence of the 2026-09-03 drift ruling. If the design "
        "intent is that it should NOT, suppress it via pathway_bonuses and say so "
        "here, rather than reverting to a second M_R implementation.")


# ═════════════════════════════════════════════════════════════════
#  5. No flag is charged twice — the canon and a pathway must not
#     both bill the same one (B-3, 2026-09-03)
# ═════════════════════════════════════════════════════════════════
#
# calculate_mr:238 applies -0.20 for `planet_expendable` on EVERY ending, and
# ending_pathways.calc_climate_black_swan_mr applied another -0.20 for the same
# flag, arriving back through pathway_bonuses["pathway_mr_delta"]. Measured
# before the fix: M_R 0.85 with the flag vs 1.25 without — a 0.40 swing for a
# flag both source comments document as 0.20. 0.80 is exactly the
# fragile_giant / stranded_relic boundary, so the extra 0.20 could hand a team
# the wrong ending archetype.

_PATHWAY_MR_CALCULATORS = {
    "climate_black_swan":  "calc_climate_black_swan_mr",
    "stakeholder_revolt":  "calc_stakeholder_revolt_mr",
    "hostile_takeover":    "calc_hostile_takeover_mr",
    "regulatory_shutdown": "calc_regulatory_shutdown_mr",
}

# Flags calculate_mr bills itself. A pathway calculator must not bill these too.
_CANON_OWNED_FLAGS = [
    "planet_expendable", "materiality_aligned", "synergy_unlock",
    "ethical_ai_overhaul", "community_fund", "managed_transition",
    "insurance_only", "electronics_water_priority", "civil_water_priority",
]


def _bus_for_pathway(slo=90.0, ci=37.0):
    return [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
             "carbon_intensity": ci, "social_license_score": slo,
             "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
             "water_dependency": 30.0, "staff_burnout_index": 10.0,
             "talent_penalty": 0} for b in ("a", "bb", "c")]


def _gs_for_pathway():
    return {"corporate_treasury": 1e8, "group_reputation": 70.0,
            "synergy_multiplier": 1.0, "active_event_flags": {},
            "workforce_readiness": 50.0, "cost_of_capital": 0.08}


@pytest.mark.parametrize("pathway,fn_name", sorted(_PATHWAY_MR_CALCULATORS.items()))
@pytest.mark.parametrize("flag", _CANON_OWNED_FLAGS)
def test_no_pathway_rebills_a_flag_calculate_mr_already_owns(pathway, fn_name, flag):
    """The pathway delta must not move when a canon-owned flag is toggled.

    If it does, that flag is billed twice on this ending and the player's M_R
    swings by double what the documentation says.
    """
    import ending_pathways
    fn = getattr(ending_pathways, fn_name)
    with_flag, without = {flag}, set()
    d_with = fn(_bus_for_pathway(), _gs_for_pathway(), with_flag, {})
    d_without = fn(_bus_for_pathway(), _gs_for_pathway(), without, {})
    assert d_with == pytest.approx(d_without), (
        f"{fn_name} changes its M_R delta by {d_with - d_without:+.4f} when "
        f"'{flag}' is set, but calculate_mr already bills that flag on every "
        f"ending — so it is charged twice on the {pathway} pathway."
    )


def test_planet_expendable_costs_exactly_its_documented_020():
    """End to end on the ending where it used to be doubled."""
    from terminal_valuation import calculate_mr
    from ending_pathways import calc_climate_black_swan_mr

    def total_mr(flags):
        extra = {}
        delta = calc_climate_black_swan_mr(_bus_for_pathway(), _gs_for_pathway(), flags, extra)
        return calculate_mr({f: True for f in flags}, avg_slo=90.0, avg_burnout=10.0,
                            workforce_readiness=50.0, synergy_multiplier=0.0,
                            pathway_bonuses={"pathway_mr_delta": delta})["mr"], extra

    with_flag, extra_with = total_mr({"planet_expendable"})
    without, _ = total_mr(set())
    assert without - with_flag == pytest.approx(0.20), (
        f"planet_expendable swung M_R by {without - with_flag:.4f}; documented 0.20")
    # the narrative explanation must survive the de-duplication
    assert extra_with.get("mr_shadow_board_planet_expendable") is True
    assert "mr_shadow_board_penalty_note" in extra_with
