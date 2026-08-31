"""
Muressons Global Corporation â€” Round-Specific State Mutation Logic
Dispatches to per-round handlers that apply conditional mutations
BEFORE and AFTER the generic tick engine runs.

Architecture:
  1. pre_tick(round, state, decisions)  â†’ validates, modifies crisis_severity
  2. engine.process_tick()              â†’ runs the 8 generic formulas
  3. post_tick(round, state, decisions) â†’ applies round-specific mutations
"""

from __future__ import annotations
import random
from typing import Any

from round_configs import get_round_config, get_round_options

# ARCH-001: Import extracted handlers from impact_engine
import impact_engine as _ie
from config import SIM_ROUNDS, ECONOMIC_CIRCULAR_ECONOMY_BONUS


# ═══════════════════════════════════════════════════════════════
#  AR-A: Terminal archetype — solvency gate + reveal-key mapping
# ═══════════════════════════════════════════════════════════════
# The R10 archetype was classified on M_R alone. M_R is a *multiplier* — a high
# multiple applied to a negative base is still failure — so an insolvent company
# could be crowned "De-risked Safe-Haven." These two pure helpers (a) block
# flattering labels for value-destroyed companies, and (b) map the lowercase
# profile to the UPPERCASE key the capstone reveal themes off (that key was never
# populated, so the reveal fell back to SAFE_HAVEN for every player). They only
# READ existing numbers; M_R, the valuation math and scoring are unchanged.

_FLATTERING_PROFILES = ("regenerative_titan", "derisked_safe_haven", "fragile_giant")

_ARCHETYPE_REVEAL_KEY = {
    "regenerative_titan": "REGENERATIVE_TITAN",
    "derisked_safe_haven": "SAFE_HAVEN",
    "fragile_giant": "FRAGILE_GIANT",
    "pragmatic_operator": "PRAGMATIC_OPERATOR",
    "stranded_relic": "STRANDED_RELIC",
    "hollow_idealist": "HOLLOW_IDEALIST",
    "turnaround_manager": "TURNAROUND_MANAGER",
}


def solvency_gated_profile(profile: str, dmav: float) -> str:
    """Value-destroyed companies (Double-Materiality Adjusted Value <= 0) cannot
    wear a flattering archetype, regardless of M_R. DMAV = final_treasury x M_R
    - NCD — the same figure the reveal screen shows the player.

    AR-B: split the failure by ESG tier. A strong-ESG company that still went
    bankrupt (titan / safe-haven tier) becomes the 'hollow_idealist' — a real
    regenerative story on an insolvent balance sheet; a mediocre-ESG failure
    (fragile-giant OR pragmatic-operator tier) becomes the 'stranded_relic'.
    The Pragmatic Operator is a *solvent* label, so an insolvent one is
    demoted to Stranded Relic just like the Fragile Giant."""
    if dmav > 0:
        return profile
    if profile in ("regenerative_titan", "derisked_safe_haven"):
        return "hollow_idealist"
    if profile in ("fragile_giant", "pragmatic_operator"):
        return "stranded_relic"
    return profile


def terminal_archetype_key(profile: str, mr: float) -> str:
    """Map the lowercase terminal profile to the UPPERCASE ARCHETYPE_MATRIX key
    the reveal screen requires. Custom/unknown profiles theme by M_R tier."""
    key = _ARCHETYPE_REVEAL_KEY.get(profile)
    if key:
        return key
    if mr >= 1.8:
        return "REGENERATIVE_TITAN"
    if mr >= 1.2:
        return "SAFE_HAVEN"
    if mr >= 0.8:
        return "FRAGILE_GIANT"
    return "STRANDED_RELIC"


def match_custom_archetype(customs: list, mr: float, solvent: bool):
    """AR-C: pick a god-mode custom archetype by M_R, honouring the per-archetype
    'requires_solvent' axis (the second, facilitator-configurable dimension). A
    solvency-gated archetype is only awarded to a solvent company; otherwise fall
    back to a non-gated (designated failure) archetype, else the lowest tier."""
    if not customs:
        return None
    ordered = sorted(customs, key=lambda a: a.get("mr_threshold", 0), reverse=True)
    matched = next(
        (a for a in ordered
         if mr >= a.get("mr_threshold", 0)
         and (solvent or not a.get("requires_solvent", False))),
        None,
    )
    if matched is None:
        matched = next(
            (a for a in reversed(ordered) if not a.get("requires_solvent", False)),
            ordered[-1],
        )
    return matched


# I2: Import scope-weighted CI applicator from engine (no circular risk — engine does not import round_logic)
# BUG-2026-07-20: switched to the IN-PLACE wrapper. The pure apply_ci_delta_to_bus
# was being called as if it mutated: new CIs were never written back (deltas
# silently dropped) and the CIDeltaResult dataclass leaked into flags, which
# Postgres could not serialize — the round-7 "Failed to persist round" stall.
try:
    from engine import apply_ci_delta_in_place as _apply_ci_delta_to_bus
except ImportError:
    # Fallback for test contexts — mutates and returns a plain dict, same contract.
    def _apply_ci_delta_to_bus(bus, ci_delta, routing="uniform"):
        for bu in bus:
            bu["carbon_intensity"] = max(0.0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))
        return {bu.get("bu_id", ""): ci_delta for bu in bus}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  PRE-TICK HOOKS
#  Run BEFORE the generic engine.  Can modify crisis_severity,
#  reject invalid inputs (raise ValueError), or set flags.
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def pre_tick(
    round_number: int,
    current_global: dict,
    current_bus: list[dict],
    decisions: list[dict],
    crisis_severity: float,
    force_override_cfo: bool = False,
) -> dict[str, Any]:
    """
    Returns a dict that may contain:
      - "crisis_severity"  â†’ overridden value
      - "validation_error" â†’ string message (will become 400)
      - "pre_events"       â†’ dict of events to merge
    """
    result: dict[str, Any] = {"crisis_severity": crisis_severity, "pre_events": {}}
    handler = _PRE_TICK_MAP.get(round_number)
    if handler:
        if round_number == 2:
            handler(result, current_global, current_bus, decisions, force_override_cfo=force_override_cfo)
        else:
            handler(result, current_global, current_bus, decisions)
    return result


# â”€â”€ R2: CFO Materiality Gate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _pre_r2_materiality_gate(
    result: dict, current_global: dict, current_bus: list[dict], decisions: list[dict], force_override_cfo: bool = False
):
    """
    Validate that all budget-allocated decision nodes fall within
    the 'High Financial / High Impact' quadrant.
    """
    cfg = get_round_config(2)
    if not cfg:
        return
    rules = cfg.get("validation_rules", {})
    if not rules.get("cfo_materiality_gate"):
        return

    # Start with the static whitelist from config
    high_impact_nodes = set(rules.get("high_impact_nodes", []))

    # Dynamically add all BU IDs from the current session so healthcare
    # (and any future industry type) passes the gate correctly.
    for bu in current_bus:
        high_impact_nodes.add(f"round_2_{bu.get('bu_id', '')}")

    for dec in decisions:
        capex = dec.get("capex_allocated", 0)
        node = dec.get("decision_node_id", "")
        if capex > 0 and node and node not in high_impact_nodes:
            if force_override_cfo:
               # Apply executive bypass -> penalize group reputation!
               # FIX AUDIT-014: We flag this in pre_events but do NOT mutate
               # current_global here (which is input state). The penalty is
               # applied in post_tick on the output state.
               result["pre_events"]["cfo_override_used"] = True
               return # bypass validation return!
            else:
                result["validation_error"] = (
                    f"CFO Override: Proposed initiative '{node}' lacks material "
                    f"justification. Budget allocation denied per Double "
                    f"Materiality framework."
                )
                return


# â”€â”€ R4: Electronics Blindspot doubles crisis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _pre_r4_contagion(
    result: dict, current_global: dict, current_bus: list[dict], decisions: list[dict]
):
    """If electronics_blindspot flag is active, double crisis severity."""
    flags = current_global.get("active_event_flags", {})
    # Walk history flags â€” check any flag list that might contain it
    all_flags = _collect_all_flags(flags)

    cfg = get_round_config(4)
    special = cfg.get("special_rules", {}) if cfg else {}
    base = special.get("base_crisis_severity", 40)

    if "electronics_blindspot" in all_flags:
        result["crisis_severity"] = base * 2  # doubled
        result["pre_events"]["electronics_blindspot_triggered"] = True
        result["pre_events"]["crisis_severity_doubled"] = True
    elif "deferred_audit" in all_flags:
        result["crisis_severity"] = round(base * 1.5)  # 1.5x for phased audit
        result["pre_events"]["deferred_audit_penalty"] = True
        result["pre_events"]["crisis_severity_multiplied"] = 1.5
    elif "compliance_gap" in all_flags or "waste_compliance_gap" in all_flags:
        # Healthcare: skipping compliance in R1 -> 1.5x crisis severity
        result["crisis_severity"] = round(base * 1.5)
        result["pre_events"]["compliance_gap_triggered"] = True
        result["pre_events"]["crisis_severity_multiplied"] = 1.5
    elif "outsource_opacity" in all_flags:
        # Healthcare: outsourced waste management creates supply chain opacity
        result["crisis_severity"] = round(base * 1.25)
        result["pre_events"]["outsource_opacity_triggered"] = True
        result["pre_events"]["crisis_severity_multiplied"] = 1.25
    else:
        result["crisis_severity"] = base
        result["pre_events"]["deep_audit_protected"] = True

    # C16: Poor stakeholder map accuracy modulates crisis severity
    # If player scored < 70% on R1 stakeholder map, multiply crisis by 1.25
    # (stacks with electronics_blindspot — misanalysing stakeholders AND
    #  skipping the audit compounds into significantly worse crisis response)
    stakeholder_accuracy = current_global.get("stakeholder_map_accuracy", 100)
    if stakeholder_accuracy < 70:
        multiplier = 1.25
        result["crisis_severity"] = round(result["crisis_severity"] * multiplier)
        result["pre_events"]["stakeholder_misanalysis_penalty"] = True
        result["pre_events"]["stakeholder_accuracy_at_crisis"] = stakeholder_accuracy
        result["pre_events"]["stakeholder_crisis_multiplier"] = multiplier


_PRE_TICK_MAP = {
    2: _pre_r2_materiality_gate,
    4: _pre_r4_contagion,
}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  POST-TICK HOOKS
#  Run AFTER the generic engine.  Mutate the already-computed
#  next-round state in place.
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _apply_treasury_with_green_fund(
    gs: dict, cost: float, extra: dict,
) -> None:
    """
    Deduct a treasury cost, using green_transition_fund first if available.
    This ensures the green fund subsidises ALL round costs in advanced_climate mode.
    Cost should be positive for expenses, negative for revenue/gains.
    """
    if cost <= 0:
        # Positive impacts (revenues) bypass the fund — add to treasury directly
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)
        return
    fund = gs.get("green_transition_fund", 0.0)
    if fund >= cost:
        gs["green_transition_fund"] = round(fund - cost, 2)
        extra["green_fund_used"] = extra.get("green_fund_used", 0) + cost
    elif fund > 0:
        gs["green_transition_fund"] = 0.0
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - (cost - fund), 2)
        extra["green_fund_used"] = extra.get("green_fund_used", 0) + fund
    else:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)


def _post_brsr_grand_finale(gs: dict, bus: list[dict], decs: list[dict], events: dict, extra: dict, prev_flags: dict):
    # Determine choice selected in R5
    choice = _get_primary_choice(decs)
    
    # Standard exit multiple and carbon tax
    exit_multiple = 12.0
    # I10: Sync terminal tax to peak internal AC fee when advanced_climate paradigm is active
    _peak_ac_fee = gs.get("active_event_flags", {}).get("peak_internal_carbon_fee", 0)
    decision_paradigm_g = gs.get("active_event_flags", {}).get("decision_paradigm", "legacy_abc")
    if decision_paradigm_g == "advanced_climate" and _peak_ac_fee > 0:
        carbon_tax_per_ton = max(250.0, round(_peak_ac_fee, 2))  # I10: at least $250, up to peak AC fee
    else:
        carbon_tax_per_ton = 250.0
    
    # Calculate ebitda
    total_revenue = sum(bu["revenue_base"] for bu in bus)
    total_opex = sum(bu["opex_base"] for bu in bus)
    carbon_tonnage_group = sum(
        bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000 
        for bu in bus
    )
    carbon_cost = round(carbon_tonnage_group * carbon_tax_per_ton, 2)
    terminal_ebitda = round((total_revenue - total_opex) - carbon_cost, 2)
    
    # Calculate MR (Management Readiness / Materiality Response)
    all_flags = _collect_all_flags(prev_flags)
    
    # Build standard bonuses
    mr = 1.0
    extra["mr_breakdown"] = {"base": 1.0}
    
    # +0.05 ESG Alpha Dividend
    # Note: finalise_brsr_track sets this in the SAME R10 post_tick,
    # so check current state first, then fall back to prev_flags.
    _cf = gs.get("active_event_flags", {})
    brsr_div = _cf.get("brsr_net_positive_dividend", 0) or prev_flags.get("brsr_net_positive_dividend", 0)

    # Truth Premium Gating: if brsr_truth_premium_blocked is active
    # (set by R5 option_c — compliance-only filers), the ESG Alpha
    # Dividend is forfeited.  This penalises teams that skip the
    # Integrated Report in R5 even if they recover in R10.
    _truth_blocked = _cf.get("brsr_truth_premium_blocked", False) or prev_flags.get("brsr_truth_premium_blocked", False)
    if _truth_blocked and brsr_div:
        extra["mr_breakdown"]["brsr_truth_premium_blocked"] = -brsr_div
        extra["brsr_truth_premium_blocked_applied"] = True
        brsr_div = 0  # forfeit the dividend

    if brsr_div:
        mr += brsr_div
        extra["mr_breakdown"]["brsr_esg_alpha_dividend"] = brsr_div

    # BRSR Compliance Score → M_R scaling
    # Note: finalise_brsr_track runs in the SAME R5 post_tick, so the score
    # is on gs["active_event_flags"] (current state), not prev_flags.
    _current_flags = gs.get("active_event_flags", {})
    _brsr_ts = _current_flags.get("_brsr_track_state") or prev_flags.get("_brsr_track_state")
    if isinstance(_brsr_ts, dict):
        _brsr_score = _brsr_ts.get("total_score", 0)
    else:
        _brsr_score = _current_flags.get("brsr_performance_score", 0) or prev_flags.get("brsr_performance_score", 0)
    if not _brsr_score:
        # Recalculate from track_state if available
        try:
            from side_tracks.brsr_ngrbc.track import BRSRNGRBCTrack as _BT
            if isinstance(_brsr_ts, dict):
                _brsr_score = _BT().calculate_score(_brsr_ts).get("total_score", 0)
        except Exception:
            pass
    if _brsr_score >= 85:
        mr += 0.65
        extra["mr_breakdown"]["brsr_pioneer_bonus"] = 0.65
    elif _brsr_score >= 70:
        mr += 0.35
        extra["mr_breakdown"]["brsr_steward_bonus"] = 0.35
    elif _brsr_score > 0 and _brsr_score < 40:
        mr -= 0.30
        extra["mr_breakdown"]["brsr_laggard_penalty"] = -0.30

    # Standard workforce and burnout bonuses if they apply
    workforce_readiness = gs.get("workforce_readiness", 50.0)
    if workforce_readiness >= 75.0:
        mr += 0.10
        extra["mr_breakdown"]["workforce_bonus"] = 0.10
        extra["mr_workforce_bonus"] = True
        
    avg_burnout = round(sum(bu.get("staff_burnout_index", 0.0) for bu in bus) / len(bus), 2) if bus else 0.0
    if avg_burnout < 20.0:
        mr += 0.05
        extra["mr_breakdown"]["wellbeing_bonus"] = 0.05
        extra["mr_wellbeing_bonus"] = True
        
    avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 0
    if avg_sl < 75:
        mr -= 0.40
        extra["mr_breakdown"]["instability_discount"] = -0.40
        extra["mr_instability_discount"] = True
        
    # Ensure mr is rounded and positive
    mr = round(max(0.0, mr), 4)
    
    # Calculate terminal value
    terminal_value = round(terminal_ebitda * exit_multiple * mr, 2)
    
    # Profile archetype
    if mr >= 1.8:
        profile = "regenerative_titan"
        profile_title = "The Regenerative Titan"
        profile_desc = "A truly regenerative enterprise."
        profile_icon = ""
        profile_gradient = "linear-gradient(135deg, #10b981, #059669)"
    elif mr >= 1.2:
        profile = "derisked_safe_haven"
        profile_title = "The De-risked Safe-Haven"
        profile_desc = "A resilient corporation that avoided the worst tail risks."
        profile_icon = ""
        profile_gradient = "linear-gradient(135deg, #3b82f6, #1d4ed8)"
    elif mr >= 0.8:
        profile = "fragile_giant"
        profile_title = "The Fragile Giant"
        profile_desc = "Big but brittle."
        profile_icon = ""
        profile_gradient = "linear-gradient(135deg, #f59e0b, #d97706)"
    else:
        profile = "stranded_relic"
        profile_title = "The Stranded Relic"
        profile_desc = "A cautionary tale."
        profile_icon = ""
        profile_gradient = "linear-gradient(135deg, #ef4444, #b91c1c)"
        
    # Populate Extra & Global State
    extra["terminal_ebitda"] = terminal_ebitda
    extra["carbon_tonnage_group"] = carbon_tonnage_group
    extra["carbon_cost"] = carbon_cost
    extra["carbon_tax_per_ton"] = carbon_tax_per_ton
    extra["regenerative_multiple"] = mr
    extra["terminal_value"] = terminal_value
    extra["exit_multiple"] = exit_multiple
    extra["final_treasury"] = gs["corporate_treasury"]
    extra["profile"] = profile
    extra["profile_title"] = profile_title
    extra["profile_description"] = profile_desc
    extra["profile_icon"] = profile_icon
    extra["profile_gradient"] = profile_gradient
    extra["synergy_score"] = round(gs.get("synergy_multiplier", 1.0) * 100, 2)
    extra["avg_social_license"] = round(avg_sl, 2)
    extra["r5_choice"] = choice
    
    # Persist into global state flags
    gs["active_event_flags"]["terminal_value"] = terminal_value
    gs["active_event_flags"]["regenerative_multiple"] = mr
    gs["active_event_flags"]["terminal_ebitda"] = terminal_ebitda
    gs["active_event_flags"]["profile"] = profile
    gs["active_event_flags"]["profile_title"] = profile_title


def post_tick(
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    decisions: list[dict],
    events: dict,
    previous_flags: dict,
    decision_paradigm: str = "legacy_abc",
) -> dict[str, Any]:
    """
    Applies round-specific state mutations after the engine tick.
    Mutates global_state / bu_states in place.
    Returns extra events to merge.
    """
    extra_events: dict[str, Any] = {}

    if decision_paradigm == "brsr_ngrbc":
        from brsr_controller import process_brsr_round
        choice = _get_primary_choice(decisions)
        brsr_extra = process_brsr_round(
            round_number=round_number,
            choice=choice,
            global_state=global_state,
            bu_states=bu_states,
            events=events,
            extra_events=extra_events,
            previous_flags=previous_flags,
        )
        extra_events.update(brsr_extra)
        
        # Save round-level flags set in active_event_flags for UI / audit consistency
        _apply_option_flags(round_number, decisions, global_state, extra_events, bus=bu_states, decision_paradigm=decision_paradigm)
        
        # Also run finalize/grand finale if round_number == 10
        if round_number == 10:
            from brsr_controller import finalise_brsr_track
            wb = finalise_brsr_track(global_state)
            extra_events.update(wb)
            
            # Calculate final terminal valuation
            _post_brsr_grand_finale(global_state, bu_states, decisions, events, extra_events, previous_flags)
            
        return extra_events

    # Invalidate forecast cache for this session on round commit
    try:
        from engine import invalidate_forecast_cache
        _session_id = global_state.get("session_id", "")
        if _session_id:
            invalidate_forecast_cache(_session_id)
    except ImportError:
        pass

    # FIX AUDIT-014: Apply the CFO override reputation penalty here
    # rather than mutating the input state directly in pre_tick.
    if events.get("cfo_override_used"):
        global_state["group_reputation"] = max(0.0, global_state.get("group_reputation", 50.0) - 5.0)
    handler = _POST_TICK_MAP.get(round_number)
    if handler:
        handler(global_state, bu_states, decisions, events, extra_events, previous_flags)

    # I7: Reverse R5 hard engineering CI pulse after 2 rounds (construction phase ends R7)
    _revert_r5_hard_engineering_pulse(global_state, bu_states, extra_events, round_number)

    # Apply generic impacts (carbon_intensity_delta, revenue_delta) for ALL rounds
    _apply_common_impacts(round_number, global_state, bu_states, decisions, extra_events)

    # I9: Apply mid-game carbon cost (legacy_abc / un_sdg — not advanced_climate)
    # Skip R10: terminal valuation already applies a lump-sum carbon tax on exit EBITDA.
    # Applying I9 OPEX in R10 would double-charge carbon in the terminal year.
    if round_number != SIM_ROUNDS:
        _dp = global_state.get("active_event_flags", {}).get("decision_paradigm", "legacy_abc")
        _apply_midgame_carbon_cost(round_number, global_state, bu_states, extra_events, decision_paradigm=_dp)



    # Apply HR mechanics: burnout accumulation + workforce readiness (all rounds)
    _apply_hr_mechanics(round_number, global_state, bu_states, events, extra_events)

    # Persist new flags from chosen option into active_event_flags
    _apply_option_flags(round_number, decisions, global_state, extra_events, bus=bu_states)

    # C7: Dynamic Salience Migration (Ackermann & Eden 2011)
    # Check if any stakeholders shift quadrants this round based on events/flags
    from stakeholder_map import apply_salience_migrations
    migrations = apply_salience_migrations(round_number, global_state)
    if migrations:
        extra_events["salience_migrations"] = migrations
        extra_events["salience_migration_count"] = len(migrations)
        migrated_names = [m["stakeholder_name"] for m in migrations]
        extra_events["salience_migration_message"] = (
            f"Stakeholder salience shift: {', '.join(migrated_names)} "
            f"changed quadrant due to Round {round_number} events."
        )

    # ── Ending Pathway: Foreshadowing Events (R5–R8) ──────────────
    # Inject news releases / market intelligence as indirect hints
    # about the ending pathway. Only if foreshadowing_enabled (god-mode).
    ending_pathway = previous_flags.get("ending_pathway", "activist_ultimatum")
    try:
        from admin_shared import _god_mode_settings
        foreshadowing_on = _god_mode_settings.get("foreshadowing_enabled", True)
    except ImportError:
        foreshadowing_on = True

    if foreshadowing_on and 5 <= round_number <= 8:
        from ending_pathways import get_foreshadowing_events
        foreshadow_items = get_foreshadowing_events(ending_pathway, round_number)
        if foreshadow_items:
            extra_events["foreshadowing_events"] = foreshadow_items
            # Inject any flags from foreshadowing items
            for item in foreshadow_items:
                if item.get("flag"):
                    global_state.setdefault("active_event_flags", {})[item["flag"]] = True

    # Inject pathway-specific KPIs for dashboard display (R7+)
    if round_number >= 7 and foreshadowing_on:
        from ending_pathways import calc_stranded_asset_exposure, calc_social_capital_index, calc_takeover_vulnerability, calc_compliance_risk_index
        if ending_pathway == "climate_black_swan":
            extra_events["stranded_asset_exposure"] = calc_stranded_asset_exposure(bu_states)
        elif ending_pathway == "stakeholder_revolt":
            extra_events["social_capital_index"] = calc_social_capital_index(bu_states, global_state)
        elif ending_pathway == "hostile_takeover":
            extra_events["takeover_vulnerability_index"] = calc_takeover_vulnerability(bu_states, global_state)
        elif ending_pathway == "regulatory_shutdown":
            extra_events["compliance_risk_index"] = calc_compliance_risk_index(bu_states, global_state)

    # ── F-2 guard: no flag may exist in dual form (boolean key + list entry) ──
    _dual = _find_dual_form_flags(global_state.get("active_event_flags", {}) or {})
    if _dual:
        print(f"[round_logic] WARNING dual-form flags detected at R{round_number} post_tick: {sorted(_dual)}")
        extra_events["dual_form_flags_detected"] = sorted(_dual)

    return extra_events


# ═══════════════════════════════════════════════════════════════
#  NEW ENGINES POST-TICK PROCESSOR
#  Runs AFTER the core post_tick, wrapped for resilience.
#  Called from router.py commit_turn after post_tick returns.
# ═══════════════════════════════════════════════════════════════

def run_new_engines(
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    events: dict,
) -> dict[str, Any]:
    """
    Process all new engine modules for this round.
    Toggle-gated via pedagogical toggles.
    Returns extra_events dict to merge into events.

    ARCHITECTURE NOTE: This is separated from post_tick to maintain
    strict decoupling — new engines cannot break the core simulation.
    Each engine is wrapped in try/except: failure is logged, never fatal.
    """
    extra: dict[str, Any] = {}

    # Read pedagogical toggles for this session
    try:
        from pedagogical_engine import get_pedagogical_toggles
        _ped_overrides = global_state.get("pedagogical_overrides", {})
        _toggles = get_pedagogical_toggles(_ped_overrides)
    except Exception:
        _toggles = {}

    # ── SE-4: Biodiversity Engine ──────────────────────────────
    if _toggles.get("biodiversity_engine_enabled", True):
        try:
            from biodiversity_engine import (
                create_initial_biodiversity_state,
                process_biodiversity_tick,
            )
            if "biodiversity_state" not in global_state:
                global_state["biodiversity_state"] = create_initial_biodiversity_state()

            bio_state = global_state["biodiversity_state"]
            bio_events = {
                "natural_capital_debt_delta": events.get("natural_capital_debt_delta", 0),
                "active_event_flags": global_state.get("active_event_flags", {}),
            }
            bio_state, bio_diag = process_biodiversity_tick(
                bio_state, global_state, bu_states, bio_events, round_number
            )
            global_state["biodiversity_state"] = bio_state
            extra["biodiversity"] = bio_diag

            # Apply M_R bonus from TNFD disclosure
            tnfd_mr = bio_diag.get("tnfd_mr_bonus", 0)
            if tnfd_mr > 0:
                extra["tnfd_mr_bonus"] = tnfd_mr
        except Exception as exc:
            print(f"[WARN] Biodiversity engine failed: {exc}")

    # ── SE-6: Balance Sheet Engine ────────────────────────────
    if _toggles.get("balance_sheet_enabled", True):
        try:
            from balance_sheet import (
                create_initial_balance_sheet,
                process_balance_sheet_tick,
            )
            if "balance_sheet" not in global_state:
                global_state["balance_sheet"] = create_initial_balance_sheet(bu_states)
                # Wire difficulty-tier covenant trigger ratio
                try:
                    from black_swan_registry import get_difficulty_config
                    _diff_tier = global_state.get("active_event_flags", {}).get("difficulty_tier", "standard")
                    _diff_cfg = get_difficulty_config(_diff_tier)
                    global_state["balance_sheet"]["covenant_trigger_ratio"] = _diff_cfg.get("covenant_trigger_ratio", 3.5)
                except Exception:
                    pass  # Graceful fallback to default 3.5×
            bs = global_state["balance_sheet"]
            # Compute total CAPEX allocated by the player this round
            _total_capex = sum(
                d.get("capex_allocated", 0)
                for d in (events.get("decisions_raw", []) or [])
            )
            bs_events = {
                "csf_this_round":        events.get("csf_delta", 0),
                "total_capex_allocated": _total_capex,
                "dividends_paid":        events.get("dividends_paid", 0),
                "remediation_events":    [],
                "tipping_tier":          global_state.get("tipping_tier", "none"),
                # FIX-B: Wire green bond issuance so Round 3 Scope 3 decisions
                # correctly update green_bonds_outstanding on the balance sheet.
                "green_bond_issued":     events.get("green_bond_issued", False),
                "green_bond_amount":     events.get("green_bond_amount", 0),
            }
            _include_esg_on_bs = global_state.get("esg_bs_scholarly_mode", False)
            bs, bs_diag = process_balance_sheet_tick(
                bs, global_state, bu_states, bs_events, round_number,
                include_esg_on_bs=_include_esg_on_bs,
            )
            global_state["balance_sheet"] = bs
            extra["balance_sheet"] = bs_diag

            # Covenant warning message for UI (surcharge already applied inside engine)
            # FIX-A: Removed duplicate surcharge block — balance_sheet.py Step 9
            # already deducts the covenant penalty from gs["corporate_treasury"].
            # Applying it again here was charging teams 2× the penalty.
            covenant_st = bs.get("covenant_status", "green")
            if covenant_st in ("amber", "red", "breached"):
                extra["covenant_warning"] = bs_diag.get("covenants", {}).get("message", "")
            if covenant_st in ("red", "breached"):
                # Expose surcharge amount for frontend display (engine has already applied it)
                extra["covenant_surcharge"] = bs_diag.get("covenants", {}).get(
                    "treasury_surcharge", 0
                )
                extra["covenant_surcharge_rate"] = (
                    0.02 if covenant_st == "red" else 0.05
                )
        except Exception as exc:
            print(f"[WARN] Balance sheet engine failed: {exc}")

    # ── SE-1: Board Governance ────────────────────────────────
    if _toggles.get("board_governance_enabled", True):
        try:
            from board_governance import (
                create_initial_board_state,
                process_board_tick,
                get_resolutions_for_round,
            )
            if "board_governance" not in global_state:
                global_state["board_governance"] = create_initial_board_state()

            board = global_state["board_governance"]
            board, board_diag = process_board_tick(
                board, global_state, bu_states, round_number
            )
            global_state["board_governance"] = board
            extra["board_governance"] = board_diag

            # Inject pending resolutions for voting rounds
            resolutions = get_resolutions_for_round(round_number)
            if resolutions:
                extra["pending_shareholder_resolutions"] = resolutions
        except Exception as exc:
            print(f"[WARN] Board governance engine failed: {exc}")

    # ── SI-5: Organisational Politics ─────────────────────────
    if _toggles.get("org_politics_enabled", True):
        try:
            from org_politics import (
                create_initial_org_politics_state,
                process_org_politics_tick,
            )
            if "org_politics" not in global_state:
                global_state["org_politics"] = create_initial_org_politics_state()

            org = global_state["org_politics"]
            org, org_diag = process_org_politics_tick(
                org, global_state, bu_states, events, round_number
            )
            global_state["org_politics"] = org
            extra["org_politics"] = org_diag
        except Exception as exc:
            print(f"[WARN] Org politics engine failed: {exc}")

    # ── SE-2: Supply Chain Network ────────────────────────────
    if _toggles.get("supply_chain_network_enabled", True):
        try:
            from supply_chain_network import (
                create_initial_supply_chain,
                process_supply_chain_tick,
            )
            if "supply_chain" not in global_state:
                global_state["supply_chain"] = create_initial_supply_chain()

            sc = global_state["supply_chain"]
            sc, sc_diag = process_supply_chain_tick(
                sc, global_state, bu_states, events, round_number
            )
            global_state["supply_chain"] = sc
            extra["supply_chain"] = sc_diag
        except Exception as exc:
            print(f"[WARN] Supply chain engine failed: {exc}")

    # ── SI-2: NPC Stakeholders ────────────────────────────────
    if _toggles.get("npc_stakeholders_enabled", True):
        try:
            from npc_stakeholders import (
                create_initial_npc_state,
                process_npc_tick,
            )
            if "npc_stakeholders" not in global_state:
                global_state["npc_stakeholders"] = create_initial_npc_state()

            npc = global_state["npc_stakeholders"]
            _memory_on = _toggles.get("stakeholder_memory_enabled", False)
            npc, npc_diag = process_npc_tick(
                npc, global_state, bu_states, events, round_number,
                memory_enabled=_memory_on,
                uncertainty_enabled=_toggles.get("stakeholder_uncertainty_enabled", False),
            )
            global_state["npc_stakeholders"] = npc
            extra["npc_stakeholders"] = npc_diag

            # ── PHASE-6 (F6): intent-forward intel for the stakeholder rail ──
            # Read-only: emit demand/leverage/trend cards (numbers kept in the
            # facilitator sub-dict). Diagnostics-only, so it never touches engine
            # state. Gated on `stakeholder_intel_ui_enabled` (default off).
            if _toggles.get("stakeholder_intel_ui_enabled", False):
                try:
                    from npc_stakeholders import build_stakeholder_intel
                    extra["stakeholder_intel"] = build_stakeholder_intel(npc, global_state, bu_states)
                except Exception as exc:
                    print(f"[WARN] Stakeholder intel (F6) failed: {exc}")

            # ── PHASE-1: NPC Cascading Reactions (evaluate_npc_cascades) ──
            # After NPC satisfaction is computed, check if any NPCs cross
            # cascade thresholds (divestment, enforcement, injunction, resignation)
            try:
                from systemic_risk_engine import evaluate_npc_cascades
                # Cascades gate on trust when memory is on, so discrete reactions
                # inherit relationship memory and stop flickering round-to-round;
                # otherwise on raw satisfaction (legacy). SPEC F1 §1.2.
                npc_sats = {}
                for nid, ndata in npc.get("npcs", {}).items():
                    npc_sats[nid] = (
                        ndata.get("trust", ndata.get("satisfaction", 50))
                        if _memory_on else ndata.get("satisfaction", 50)
                    )
                active_cascades = events.get("active_npc_cascades", [])
                cascades = evaluate_npc_cascades(npc_sats, round_number, active_cascades)

                # ── PHASE-4 (F3): coalitions & salience contagion ──────
                # Detect a coalition from the round's hostile tiers and apply
                # one hop of cascade→target contagion. The resulting pressure
                # amplifies F2 below and (persisted) next round's strike risk.
                _coalition_pressure = 0.0
                if _toggles.get("stakeholder_coalitions_enabled", False):
                    try:
                        from systemic_risk_engine import evaluate_coalition_and_contagion
                        from config import COALITION_TIER_MIN, CONTAGION_SAT_NUDGE
                        _coal = evaluate_coalition_and_contagion(
                            npc, cascades,
                            tier_min=COALITION_TIER_MIN,
                            contagion_nudge=CONTAGION_SAT_NUDGE,
                        )
                        _coalition_pressure = _coal.get("coalition_pressure", 0.0)
                        npc["coalition_pressure"] = _coalition_pressure  # persist for next-round strike
                        if _coalition_pressure > 0 or _coal.get("contagion_nudges"):
                            extra["stakeholder_coalition"] = _coal
                    except Exception as exc:
                        print(f"[WARN] Stakeholder coalition (F3) failed: {exc}")

                # ── PHASE-2 (F2): continuous tier→SLO feedback ──────────
                # Runs on the round's escalation tiers, AFTER cascade detection
                # so cascaded NPCs can be suppressed (their discrete
                # social_license_delta supersedes the continuous term — no
                # double count), and BEFORE cascade effects are applied. The
                # later social-tipping cap still clamps SLO. SPEC F2 §2.3.
                if _toggles.get("stakeholder_slo_feedback_enabled", False):
                    try:
                        from npc_stakeholders import apply_stakeholder_slo_feedback
                        from config import STAKEHOLDER_SLO_COUPLING, COALITION_F2_GAIN
                        _cascaded_ids = {c.get("npc_id") for c in cascades}
                        # A coalition makes the continuous feedback bite harder
                        # (F3). _coalition_pressure is 0 when coalitions are off,
                        # so this reduces to the plain coupling. SPEC F3 §3.2.
                        _coupling = STAKEHOLDER_SLO_COUPLING * (1.0 + _coalition_pressure * COALITION_F2_GAIN)
                        _slo_fb = apply_stakeholder_slo_feedback(
                            npc, bu_states, round_number,
                            cascaded_npc_ids=_cascaded_ids,
                            coupling=_coupling,
                        )
                        if _slo_fb:
                            extra["npc_slo_feedback"] = _slo_fb
                    except Exception as exc:
                        print(f"[WARN] Stakeholder SLO feedback (F2) failed: {exc}")

                if cascades:
                    extra["npc_cascade_events"] = cascades
                    extra["active_npc_cascades"] = cascades
                    for cascade in cascades:
                        eff = cascade.get("effects", {})
                        # Treasury percentage hit
                        if eff.get("treasury_pct_hit"):
                            t_hit = round(global_state.get("corporate_treasury", 0) * abs(eff["treasury_pct_hit"]), 2)
                            global_state["corporate_treasury"] = round(global_state.get("corporate_treasury", 0) - t_hit, 2)
                            extra[f"npc_cascade_treasury_{cascade['npc_id']}"] = t_hit
                        # Treasury flat hit
                        if eff.get("treasury_flat_hit"):
                            global_state["corporate_treasury"] = round(
                                global_state.get("corporate_treasury", 0) + eff["treasury_flat_hit"], 2
                            )
                        # Reputation delta
                        if eff.get("reputation_delta"):
                            global_state["group_reputation"] = max(0, min(100, round(
                                global_state.get("group_reputation", 50) + eff["reputation_delta"], 2
                            )))
                        # Social license delta
                        if eff.get("social_license_delta"):
                            for bu in bu_states:
                                bu["social_license_score"] = max(0, min(100, round(
                                    bu.get("social_license_score", 50) + eff["social_license_delta"], 2
                                )))
                        # Burnout delta
                        if eff.get("burnout_delta"):
                            for bu in bu_states:
                                bu["staff_burnout_index"] = max(0, min(100, round(
                                    bu.get("staff_burnout_index", 0) + eff["burnout_delta"], 2
                                )))
                        # OPEX percentage increase
                        if eff.get("opex_pct_increase"):
                            for bu in bu_states:
                                bu["opex_base"] = round(bu["opex_base"] * (1 + eff["opex_pct_increase"]), 2)
                        # Surface narrative as custom black swan
                        events.setdefault("custom_black_swans", []).append({
                            "title": f"NPC CASCADE — {cascade['npc_id'].replace('_', ' ').title()}",
                            "narrative": cascade["narrative"],
                            "icon": "⚡",
                            "severity": "critical",
                        })
            except Exception as exc:
                print(f"[WARN] NPC cascade evaluation failed: {exc}")

        except Exception as exc:
            print(f"[WARN] NPC stakeholders engine failed: {exc}")

    # ── PHASE-3 (F5): Stakeholder engagement actions & promise ledger ──
    # Runs after the NPC tick (trust is set) and reads the persistent
    # npc_stakeholders sub-dict. Resolve promises maturing THIS round first (so a
    # promise is judged on the round it comes due), then apply the player's new
    # engagement action. Gated on `stakeholder_engagement_enabled` (default off).
    if _toggles.get("stakeholder_engagement_enabled", False):
        try:
            from stakeholder_engagement import apply_engagement_action, resolve_promises
            npc = global_state.get("npc_stakeholders")
            if npc:
                _res = resolve_promises(npc, global_state, bu_states, round_number)
                if _res:
                    extra["promise_resolutions"] = _res
                _action = events.get("engagement_action") or global_state.get("engagement_action")
                if _action:
                    _ar = apply_engagement_action(npc, global_state, _action, round_number)
                    extra["engagement_action_result"] = _ar
        except Exception as exc:
            print(f"[WARN] Stakeholder engagement (F5) failed: {exc}")

    # ── SI-2+: Autonomous Stakeholder Agents ──────────────────
    if _toggles.get("npc_stakeholders_enabled", True):
        try:
            from autonomous_agents import (
                create_initial_agent_state,
                process_agent_tick,
                get_agent_summary,
            )
            if "autonomous_agents" not in global_state:
                global_state["autonomous_agents"] = create_initial_agent_state()

            aa = global_state["autonomous_agents"]
            aa, aa_diag = process_agent_tick(
                aa, global_state, bu_states, events, round_number,
                memory_enabled=_toggles.get("stakeholder_memory_enabled", False),
                slo_feedback_enabled=_toggles.get("stakeholder_slo_feedback_enabled", False),
                engagement_enabled=_toggles.get("stakeholder_engagement_enabled", False),
                coalitions_enabled=_toggles.get("stakeholder_coalitions_enabled", False),
                uncertainty_enabled=_toggles.get("stakeholder_uncertainty_enabled", False),
            )
            global_state["autonomous_agents"] = aa
            extra["autonomous_agents"] = aa_diag
            _agent_summary = get_agent_summary(aa)
            extra["agent_summary"] = _agent_summary
            # Persist the frontend-ready summary into global_state so the live
            # dashboard (GlobalStateOut.agent_summary) shows the accumulated
            # escalation every round, not just in the post-commit results.
            global_state["agent_summary"] = _agent_summary
        except Exception as exc:
            print(f"[WARN] Autonomous agents engine failed: {exc}")

    # ── PHASE-1: Systemic Tipping Point Penalty Application ──────
    # After all engines run, apply irreversibility penalties from
    # tipping state computed in engine.py process_tick
    try:
        tipping_state = events.get("systemic_tipping", {}).get("tipping_state", {})
        if tipping_state.get("climate_tipped"):
            # NCD interest multiplier: double NCD accrual
            for bu in bu_states:
                ncd = bu.get("natural_capital_debt", 0)
                extra_ncd = round(ncd * 0.5, 2)  # +50% on top of existing accrual
                bu["natural_capital_debt"] = round(ncd + extra_ncd, 2)
            # Reputation ceiling: cap at 60
            if global_state.get("group_reputation", 50) > 60:
                global_state["group_reputation"] = 60.0
            extra["climate_tipping_penalties_applied"] = True

        if tipping_state.get("social_tipped"):
            # Permanent OPEX surcharge: +5%
            for bu in bu_states:
                bu["opex_base"] = round(bu["opex_base"] * 1.05, 2)
            # Social license ceiling: cap at 50
            for bu in bu_states:
                if bu.get("social_license_score", 50) > 50:
                    bu["social_license_score"] = 50.0
            extra["social_tipping_penalties_applied"] = True

        if tipping_state.get("financial_tipped"):
            # Borrowing premium: +4% to cost of capital
            coc = global_state.get("cost_of_capital", 0.05)
            global_state["cost_of_capital"] = round(coc + 0.04, 4)
            # CapEx cap: 50% reduction
            events["capex_cap_multiplier"] = 0.50
            events["dividend_suspended"] = True
            extra["financial_tipping_penalties_applied"] = True

        # Persist tipping state for next round
        if tipping_state:
            events["systemic_tipping_state"] = tipping_state
    except Exception as exc:
        print(f"[WARN] Tipping penalty application failed: {exc}")

    # ── SI-1: Non-Linear Branching (R5 checkpoint) ────────────
    if _toggles.get("branching_enabled", True) and round_number == 5:
        try:
            from branching_engine import classify_player_archetype
            decision_history = global_state.get("decision_history", [])
            archetype_result = classify_player_archetype(
                global_state, bu_states, decision_history
            )
            global_state["player_archetype"] = archetype_result["archetype_id"]
            global_state["archetype_detail"] = archetype_result
            extra["archetype_classification"] = archetype_result
        except Exception as exc:
            print(f"[WARN] Branching engine failed: {exc}")

    # ── SE-3: Adaptive Crisis Severity (R6+ with archetype) ───
    if _toggles.get("branching_enabled", True) and round_number > 5:
        try:
            from branching_engine import calc_adaptive_crisis_severity
            archetype_id = global_state.get("player_archetype", "pragmatic_optimizer")
            base_severity = events.get("crisis_severity_effective", 40)
            adj_severity, sev_diag = calc_adaptive_crisis_severity(
                base_severity, archetype_id, global_state, bu_states, round_number
            )
            extra["adaptive_crisis_severity"] = sev_diag
        except Exception as exc:
            print(f"[WARN] Adaptive crisis severity failed: {exc}")

    # ── SE-8: Dynamic Case Injection ──────────────────────────
    if _toggles.get("dynamic_cases_enabled", True):
        try:
            from dynamic_cases import select_contextual_cases
            cases = select_contextual_cases(
                global_state, bu_states, round_number, max_cases=2
            )
            if cases:
                extra["contextual_cases"] = cases
        except Exception as exc:
            print(f"[WARN] Dynamic cases engine failed: {exc}")

    # ── QW-5: Peer Learning Prompts (R5, R6) ──────────────────
    if _toggles.get("peer_learning_prompts_enabled", True):
        try:
            from pedagogical_engine import get_peer_prompts_for_round
            prompts = get_peer_prompts_for_round(round_number, _toggles)
            if prompts:
                extra["peer_learning_prompts"] = prompts
        except Exception as exc:
            print(f"[WARN] Peer learning prompts failed: {exc}")

    # ── QW-1: Decision Timer Config ───────────────────────────
    if _toggles.get("decision_timer_enabled", False):
        try:
            from pedagogical_engine import get_timer_config
            extra["decision_timer"] = get_timer_config(_toggles)
        except Exception as exc:
            print(f"[WARN] Decision timer config failed: {exc}")

    # ── Meadows / Senge: System Archetypes Detection ──────────
    if _toggles.get("system_archetypes_enabled", True):
        try:
            from meadows_leverage import detect_archetypes
            flags = global_state.get("active_event_flags", {})
            archetypes = detect_archetypes(global_state, bu_states, flags)
            if archetypes:
                extra["system_archetypes_detected"] = archetypes
        except Exception as exc:
            print(f"[WARN] System archetypes detection failed: {exc}")

    # ── SE-7: Regulatory Sandbox Effects ──────────────────────
    # ARCHITECTURE: Middleware intercept runs FIRST (before values
    # finalize), then standard instrument effects, then agent cross-wiring.
    if _toggles.get("regulatory_sandbox_enabled", False):
        try:
            from regulatory_sandbox import (
                apply_sandbox_effects,
                intercept_state_transition,
                crosswire_sandbox_to_agents,
                create_sandbox_state,
            )
            if "regulatory_sandbox" not in global_state:
                global_state["regulatory_sandbox"] = create_sandbox_state()
            sandbox = global_state["regulatory_sandbox"]

            # Phase 1: Middleware intercept (Pigouvian per-BU penalties,
            # Carbon Minsky Moment, Coasian friction, polycentric burdens,
            # exogenous event evaluation for R7-R9)
            if sandbox.get("sandbox_mode"):
                intercept_diag = intercept_state_transition(
                    sandbox, global_state, bu_states, events, round_number
                )
                if intercept_diag:
                    extra["regulatory_sandbox_intercept"] = intercept_diag

            # Phase 2: Standard instrument effects (carbon tax, ETS, etc.)
            if sandbox.get("sandbox_mode") and sandbox.get("active_regulations"):
                sandbox_diag = apply_sandbox_effects(
                    sandbox, global_state, bu_states, round_number
                )
                if sandbox_diag:
                    extra["regulatory_sandbox"] = sandbox_diag

            # Phase 3: Agent cross-wiring — check if sandbox shocks
            # push Carson or Jay Buffet past thresholds
            if sandbox.get("sandbox_mode") and _toggles.get("npc_stakeholders_enabled", True):
                agent_diag = crosswire_sandbox_to_agents(
                    sandbox, global_state, bu_states, events, round_number
                )
                if agent_diag.get("agent_crosswire_triggers"):
                    extra["regulatory_sandbox_agent_crosswire"] = agent_diag
        except Exception as exc:
            print(f"[WARN] Regulatory sandbox engine failed: {exc}")

    # ── Analytics: Collaboration Gap Tracker ─────────────────────
    # Measures the spread between financial accumulation and ESG
    # stewardship each round.  Pure analytics — result is merged into
    # extra_events for the debrief dashboard only.  No feedback into
    # engine state, terminal value, or any game mechanic.
    if _toggles.get("collaboration_gap_enabled", True):
        try:
            from round_analytics import calc_collaboration_gap
            gap_data = calc_collaboration_gap(round_number, global_state, bu_states)
            extra["collaboration_gap"] = gap_data

            # Accumulate history on global_state so the debrief summary
            # function (summarise_gap_history) can build a full trend chart
            # without querying the database.
            gap_history = global_state.setdefault("_collaboration_gap_history", [])
            # Avoid duplicate entries if run_new_engines is called more than
            # once for the same round (defensive guard).
            if not gap_history or gap_history[-1].get("round") != round_number:
                gap_history.append(gap_data)
        except Exception as exc:
            print(f"[WARN] Collaboration gap analytics failed: {exc}")

    return extra



from healthcare_configs import get_healthcare_round_options



def _apply_midgame_carbon_cost(
    round_number: int,
    gs: dict,
    bus: list[dict],
    extra: dict,
    decision_paradigm: str | None = None,
) -> None:
    """
    I9 — Mid-game carbon cost applied to EBITDA every round (legacy_abc / un_sdg only).
    Advanced_climate already has the escalating internal fee — avoid double-counting.

    Formula: OPEX penalty = total_tco2e × base_rate × (1.10^(round-1))
    Base rate: $25/tCO2e in R1, escalating 10%/round.
    R1:$25 → R5:$37 → R10:$60 (modest but real mid-game consequence).
    Applied by adding to each BU's opex_base proportional to its CI share.
    """
    if decision_paradigm == "advanced_climate":
        return  # Already paying escalating internal carbon fee
    if decision_paradigm == "brsr_ngrbc":
        return  # BRSR track has its own carbon accounting

    base_rate = 25.0  # $/tCO2e in R1
    current_rate = round(base_rate * (1.10 ** (round_number - 1)), 2)
    group_tco2e = sum(
        bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000
        for bu in bus
    )
    if group_tco2e <= 0:
        return

    total_cost = round(group_tco2e * current_rate, 2)
    # Distribute cost to BUs proportionally to their absolute emissions
    for bu in bus:
        bu_tco2e = bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000
        if group_tco2e > 0:
            share = round(bu_tco2e / group_tco2e * total_cost, 2)
            bu["opex_base"] = round(bu.get("opex_base", 0) + share, 2)

    extra[f"midgame_carbon_cost_r{round_number}"] = total_cost
    extra[f"midgame_carbon_rate_r{round_number}"] = current_rate
    extra["midgame_carbon_cost_message"] = (
        f"Mid-game carbon OPEX: ${current_rate:.0f}/tCO₂e × {group_tco2e:.0f}t = "
        f"-${total_cost:,.0f} distributed across BUs (I9: annual carbon operating cost)."
    )

def _fetch_options_for_industry(round_number: int, bus: list[dict], decision_paradigm: str | None = None) -> dict:
    if decision_paradigm == "brsr_ngrbc":
        from side_tracks.brsr_ngrbc.configs import get_brsr_round_options
        return get_brsr_round_options(round_number)
    if any(b["bu_id"] == "hospitals" for b in bus):
        return get_healthcare_round_options(round_number)
    return get_round_options(round_number)

def _apply_common_impacts(
    round_number: int,
    gs: dict,
    bus: list[dict],
    decisions: list[dict],
    extra: dict,
    decision_paradigm: str | None = None,
):
    """
    Generic applicator for carbon_intensity_delta and revenue_delta.
    Runs for EVERY round after the round-specific handler.
    Skips if the round-specific handler already applied these (R3 carbon).
    """
    choice = _get_primary_choice(decisions)
    cfg_opts = _fetch_options_for_industry(round_number, bus, decision_paradigm=decision_paradigm)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # I2 — Carbon intensity delta with scope-aware routing
    # ci_routing="scope3_weighted" applies delta proportionally to each BU Scope3 fraction.
    # Supply-chain decisions (R3, R7) benefit high-Scope3 BUs most.
    ci_delta = impacts.get("carbon_intensity_delta", 0)
    ci_routing = opt.get("ci_routing", "uniform")  # set in round_configs per option
    if ci_delta != 0 and f"carbon_intensity_applied_r{round_number}" not in extra:
        applied = _apply_ci_delta_to_bus(bus, ci_delta, routing=ci_routing)
        extra[f"carbon_intensity_applied_r{round_number}"] = ci_delta
        extra[f"carbon_intensity_routing_r{round_number}"] = ci_routing
        if ci_routing == "scope3_weighted":
            extra[f"carbon_intensity_by_bu_r{round_number}"] = applied

    # Revenue delta â€” applied to all BUs equally
    rev_delta = impacts.get("revenue_delta", 0)
    if rev_delta != 0:
        for bu in bus:
            old_rev = bu.get("revenue_base", 0)
            bu["revenue_base"] = max(0, round(old_rev + rev_delta, 2))
        extra[f"revenue_delta_applied_r{round_number}"] = rev_delta

    # Governance risk delta — applied to all BUs
    gov_delta = impacts.get("governance_risk_delta", 0)
    if gov_delta != 0 and f"governance_risk_applied_r{round_number}" not in extra:
        for bu in bus:
            bu["governance_risk_score"] = max(
                0.0, min(100.0, round(bu.get("governance_risk_score", 20.0) + gov_delta, 2))
            )
        extra[f"governance_risk_applied_r{round_number}"] = gov_delta

    # Reputation delta — applied to group reputation
    rep_delta = impacts.get("reputation", 0)
    if rep_delta != 0 and f"reputation_applied_r{round_number}" not in extra:
        gs["group_reputation"] = max(
            0.0, min(100.0, round(gs.get("group_reputation", 50.0) + rep_delta, 2))
        )
        extra[f"reputation_applied_r{round_number}"] = rep_delta

    # NCD application is handled individually in each round's post handler
    # because some rounds (like R5 and R8) queue it as a pending capex project instead of applying immediately.

    # â”€â”€ Healthcare Specific Impacts â”€â”€
    if impacts.get("bed_capacity_increase"):
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["bed_capacity_utilization"] = max(0.0, b.get("bed_capacity_utilization", 0.0) - impacts["bed_capacity_increase"])
                
    if impacts.get("burnout_spike"):
        spike_amount = impacts.get("burnout_spike_amount", 25.0)
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["staff_burnout_index"] = min(100.0, b.get("staff_burnout_index", 0.0) + spike_amount)
                
    if impacts.get("burnout_recovery"):
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["staff_burnout_index"] = max(0.0, b.get("staff_burnout_index", 0.0) - 30.0)
                
    if impacts.get("telehealth_opex_delta"):
        for b in bus:
            if b["bu_id"] == "telehealth":
                b["opex_base"] = round(b["opex_base"] + impacts["telehealth_opex_delta"], 2)
                
    if impacts.get("opex_penalty"):
        targets = impacts.get("opex_penalty_targets")
        if targets:
            target_bus = [b for b in bus if b["bu_id"] in targets]
            share = impacts["opex_penalty"] / max(len(target_bus), 1)
            for b in target_bus:
                b["opex_base"] = round(b["opex_base"] + share, 2)
            extra[f"opex_penalty_targeted_r{round_number}"] = targets
        else:
            for b in bus:
                b["opex_base"] = round(b["opex_base"] + (impacts["opex_penalty"] / len(bus)), 2)

    # Healthcare: Elective surgery cancellation — targeted revenue impacts
    if impacts.get("elective_surgery_cancel"):
        is_healthcare = any(b["bu_id"] == "hospitals" for b in bus)
        if is_healthcare:
            for b in bus:
                if b["bu_id"] in ("hospitals", "specialised_care"):
                    b["revenue_base"] = max(0, round(b["revenue_base"] - 4_000_000, 2))
                elif b["bu_id"] == "clinics":
                    b["revenue_base"] = max(0, round(b["revenue_base"] - 1_000_000, 2))
                elif b["bu_id"] == "telehealth":
                    b["revenue_base"] = round(b["revenue_base"] + 2_000_000, 2)
            extra["elective_surgery_cancel_applied"] = True
            extra["elective_surgery_cancel_detail"] = (
                "Elective surgery cancellation: Hospitals -$4M, Specialised Care -$4M, "
                "Clinics -$1M, Telehealth +$2M (digital diversion surge)."
            )

    # Healthcare R10: opex_slash implementation — aggressive OPEX cut + treasury bonus
    if impacts.get("opex_slash"):
        slash_pct = impacts.get("opex_slash_pct", 0.15)
        treasury_bonus_pct = impacts.get("treasury_bonus_pct", 0.10)
        # Slash OPEX across all BUs
        for b in bus:
            reduction = round(b["opex_base"] * slash_pct, 2)
            b["opex_base"] = round(b["opex_base"] - reduction, 2)
        # Treasury bonus
        treasury_bonus = round(gs["corporate_treasury"] * treasury_bonus_pct, 2)
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + treasury_bonus, 2)
        # Patient outcomes penalty
        outcomes_penalty = impacts.get("patient_outcomes_penalty", -15)
        for b in bus:
            old_po = b.get("patient_outcomes_score", 50.0)
            b["patient_outcomes_score"] = max(0.0, round(old_po + outcomes_penalty, 2))
        extra["opex_slash_applied"] = True
        extra["opex_slash_reduction_pct"] = round(slash_pct * 100, 1)
        extra["opex_slash_treasury_bonus"] = treasury_bonus
        extra["opex_slash_outcomes_penalty"] = outcomes_penalty

    # Healthcare R10C: synergy_preserve — explicit protection + SLO boost
    if impacts.get("synergy_preserve"):
        extra["synergy_explicitly_preserved"] = True
        extra["synergy_preserve_message"] = (
            "Universal Care Mandate: Synergy multiplier explicitly protected. "
            "Corporate charter codifies patient outcomes above short-term margins."
        )
    sl_boost = impacts.get("social_license_boost", 0)
    if sl_boost != 0:
        for b in bus:
            b["social_license_score"] = max(0, min(100, round(b["social_license_score"] + sl_boost, 2)))
        extra[f"social_license_boost_applied_r{round_number}"] = sl_boost

    # Synergy is handled cleanly in R7 specific post_tick.
    if impacts.get("contagion_spike"):
        is_healthcare = any(b["bu_id"] == "hospitals" for b in bus)
        if is_healthcare:
            for b in bus:
                if b["bu_id"] == "hospitals":
                    b["reputation_score"] = max(0.0, b.get("reputation_score", 50.0) - 15.0)
                elif b["bu_id"] == "telehealth":
                    # Surge in digital health utilization during contagion
                    b["revenue_base"] = round(b.get("revenue_base", 0) * 1.15, 2)
                    extra["telehealth_surge_active"] = True
        else:
            gs["group_reputation"] = max(0.0, gs.get("group_reputation", 50.0) - 10.0)

    # â”€â”€ UN SDG Edition: Apply cluster score deltas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # These are the budget_delta-based deltas defined in sdg_configs.py options.
    # They are scaled by institutional_leakage_multiplier and sanitation_miracle_bonus.
    sdg_cluster_keys = [
        "basic_needs_delta", "human_capital_delta", "sustainable_growth_delta",
        "planet_delta", "governance_delta", "partnerships_delta",
    ]
    has_sdg_deltas = any(impacts.get(k, 0) != 0 for k in sdg_cluster_keys)

    if has_sdg_deltas:
        # Also scale by donor fatigue budget multiplier if available
        budget_mult = gs.get("active_event_flags", {}).get(
            "donor_fatigue_budget_multiplier", 1.0
        )

        target_regions = impacts.get("target_regions", [])
        for bu in bus:
            # If target_regions is specified, only apply to those BUs
            if target_regions and bu["bu_id"] not in target_regions:
                continue

            leakage = bu.get("institutional_leakage_multiplier", 1.0)
            miracle = bu.get("sanitation_miracle_bonus", 1.0)

            for key in sdg_cluster_keys:
                raw_delta = impacts.get(key, 0)
                if raw_delta == 0:
                    continue

                cluster_name = key.replace("_delta", "")
                effective_delta = raw_delta * leakage * budget_mult

                # Sanitation miracle doubles basic_needs investment returns
                if cluster_name == "basic_needs" and raw_delta > 0:
                    effective_delta *= miracle

                old_val = bu.get(cluster_name, 0)
                bu[cluster_name] = round(max(0, min(100, old_val + effective_delta)), 2)

        extra[f"sdg_clusters_applied_r{round_number}"] = True
        if budget_mult != 1.0:
            extra["donor_fatigue_scaling_applied"] = budget_mult

    # migration_pressure delta from option impacts
    mig_delta = impacts.get("migration_pressure", 0)
    if mig_delta != 0:
        target_regions = impacts.get("target_regions", [])
        for bu in bus:
            if target_regions and bu["bu_id"] not in target_regions:
                continue
            bu["migration_pressure"] = round(
                bu.get("migration_pressure", 0) + mig_delta, 2
            )
        extra["migration_pressure_applied"] = mig_delta


# ── HR Mechanics: Burnout + Workforce Readiness (every round) ────
def _apply_hr_mechanics(
    round_number: int,
    gs: dict,
    bus: list[dict],
    events: dict,
    extra: dict,
):
    """
    Process HR pillar impacts every round:

    1. Burnout Accumulation — per-BU staff_burnout_index driven by
       burnout_delta from HR pillar choices + natural drift.
       Creates OPEX penalty when burnout > 40 and governance risk spike > 70.

    2. Workforce Readiness — global-level competence score that modulates
       effectiveness of other strategic pillars.

    Interdependencies wired in:
    - R7 (_post_r7_circularity): Low readiness → synergy boost reduced
    - R9 (_post_r9_just_transition): High burnout → strike probability boost
    - R10 (_post_r10_grand_finale): High readiness → +0.05 M_R bonus
    """
    from engine import calc_burnout_accumulation, calc_workforce_readiness

    # ── 1. Determine HR pillar choice quality from events ──
    pillar_flags = set(events.get("pillar_flags", []) or [])
    hr_choice = events.get("hr_choice", None)

    # Classify HR investment tier based on known flags
    HIGH_HR_FLAGS = {
        "dei_program", "people_analytics", "green_skills_academy",
        "crisis_employee_support", "emergency_trained",
        "responsible_ai_trained", "circular_reskilled",
        "water_stewards_trained", "full_severance_redeployment",
        "employee_ownership",
    }
    MEDIUM_HR_FLAGS = {
        "leadership_pipeline", "engagement_survey", "ohs_basic",
        "basic_ppe", "ai_upskilling", "cross_trained",
        "shift_optimized", "statutory_minimum_hr", "retention_bonuses",
    }
    NEGATIVE_HR_FLAGS = {
        "burnout_risk", "hr_absent_transition",
    }

    if pillar_flags & HIGH_HR_FLAGS:
        hr_quality = "high"
        burnout_delta = -10.0  # Good HR actively reduces burnout
        natural_drift = 0.0   # Investment resets natural drift
    elif pillar_flags & MEDIUM_HR_FLAGS:
        hr_quality = "medium"
        burnout_delta = -4.0   # Moderate relief
        natural_drift = 1.0    # Partial drift still applies
    elif pillar_flags & NEGATIVE_HR_FLAGS:
        hr_quality = "none"
        burnout_delta = 12.0   # Overtime/neglect actively increases burnout
        natural_drift = 3.0    # Full entropy
    else:
        hr_quality = "none"
        burnout_delta = 0.0
        natural_drift = 3.0    # Passive burnout accumulation

    hr_invested = hr_quality in ("high", "medium")
    extra["hr_quality_tier"] = hr_quality
    extra["hr_invested"] = hr_invested

    # ── 2. Apply burnout to each BU ──
    burnout_diagnostics = {}
    for bu in bus:
        current = bu.get("staff_burnout_index", 0.0)
        new_burnout, diag = calc_burnout_accumulation(
            current, burnout_delta, natural_drift
        )
        bu["staff_burnout_index"] = new_burnout
        burnout_diagnostics[bu["bu_id"]] = diag

        # OPEX penalty when burnout > 40
        penalty_rate = diag["opex_penalty_rate"]
        if penalty_rate > 0:
            penalty_amount = round(bu["opex_base"] * penalty_rate, 2)
            bu["opex_base"] = round(bu["opex_base"] + penalty_amount, 2)
            extra[f"burnout_opex_penalty_{bu['bu_id']}"] = penalty_amount

        # Governance risk spike when burnout > 70 (critical)
        if diag["critical_burnout"]:
            gov_spike = 3.0
            bu["governance_risk_score"] = min(
                100.0, round(bu.get("governance_risk_score", 20.0) + gov_spike, 2)
            )
            extra[f"burnout_gov_spike_{bu['bu_id']}"] = gov_spike

    extra["burnout_diagnostics"] = burnout_diagnostics

    # ── 3. Workforce readiness (global-level) ──
    current_readiness = gs.get("workforce_readiness", 50.0)
    new_readiness, readiness_diag = calc_workforce_readiness(
        current_readiness, hr_invested, hr_quality
    )
    gs["workforce_readiness"] = new_readiness
    extra["workforce_readiness_diagnostics"] = readiness_diag

    # Set effectiveness modifier for other pillars to consume
    if new_readiness < 40.0:
        gs["pillar_effectiveness_modifier"] = 0.80  # 20% penalty
        extra["low_readiness_penalty_active"] = True
        extra["low_readiness_message"] = (
            f"⚠️ LOW WORKFORCE READINESS ({new_readiness:.0f}/100): "
            f"Undertrained workforce reduces strategic initiative effectiveness by 20%. "
            f"Invest in HR to restore capability."
        )
    else:
        gs["pillar_effectiveness_modifier"] = 1.0
        extra["low_readiness_penalty_active"] = False

    # Avg burnout for diagnostic reporting
    avg_burnout = round(
        sum(bu.get("staff_burnout_index", 0.0) for bu in bus) / len(bus), 2
    ) if bus else 0.0
    extra["avg_burnout_index"] = avg_burnout
    extra["workforce_readiness"] = new_readiness

    # ── 4. HR ROI Metric — visible financial value of HRM investment ──
    # Translates the indirect financial benefits of HR into $$ terms each round.
    # Two components:
    #   (a) Burnout OPEX Savings: penalty avoided vs a no-HR counterfactual
    #   (b) Pillar Effectiveness Value: 20% of pillar spend protected by readiness ≥ 40
    #
    # hr_roi_this_round = savings (a) + preserved value (b)
    # hr_roi_cumulative = rolling total persisted in global_state

    # (a) Compute total actual burnout OPEX penalty applied this round
    total_burnout_penalty_applied = sum(
        extra.get(f"burnout_opex_penalty_{bu['bu_id']}", 0.0) for bu in bus
    )

    # Counterfactual: pts of burnout prevented by HR investment this round
    if hr_quality == "high":
        delta_saved_per_bu = 13.0   # prevented: burnout_delta(-10) + drift(0 vs 3) = 13
    elif hr_quality == "medium":
        delta_saved_per_bu = 6.0    # prevented: burnout_delta(-4) + drift(1 vs 3) = 6
    else:
        delta_saved_per_bu = 0.0

    counterfactual_opex_savings = 0.0
    for bu in bus:
        current_boi = bu.get("staff_burnout_index", 0.0)
        counterfactual_burnout = min(100.0, current_boi + delta_saved_per_bu)
        if counterfactual_burnout > 20.0:
            counterfactual_rate = ((counterfactual_burnout - 20.0) ** 2) * 0.000028125
            counterfactual_opex_penalty = round(bu.get("opex_base", 0) * counterfactual_rate, 2)
            actual_rate = ((current_boi - 20.0) ** 2 * 0.000028125) if current_boi > 20.0 else 0.0
            actual_opex_penalty = round(bu.get("opex_base", 0) * actual_rate, 2)
            counterfactual_opex_savings += max(0.0, counterfactual_opex_penalty - actual_opex_penalty)
    counterfactual_opex_savings = round(counterfactual_opex_savings, 2)

    # (b) Pillar value preserved: HR investment protecting readiness ≥ 40
    # approximated as 20% of this round's pillar spend
    pillar_cost_proxy = abs(events.get("pillar_cost_applied", 0))
    pillar_value_preserved = round(pillar_cost_proxy * 0.20, 2) \
        if (new_readiness >= 40.0 and hr_quality in ("high", "medium")) else 0.0

    hr_roi_this_round = round(counterfactual_opex_savings + pillar_value_preserved, 2)

    # Accumulate running HR ROI total in global_state
    prev_cumulative = gs.get("hr_roi_cumulative", 0.0)
    hr_roi_cumulative = round(prev_cumulative + hr_roi_this_round, 2)
    gs["hr_roi_cumulative"] = hr_roi_cumulative

    extra["hr_roi_this_round"] = hr_roi_this_round
    extra["hr_roi_cumulative"] = hr_roi_cumulative
    extra["hr_roi_opex_savings_component"] = counterfactual_opex_savings
    extra["hr_roi_pillar_value_component"] = pillar_value_preserved
    extra["hr_roi_message"] = (
        f"💼 HR ROI this round: +${hr_roi_this_round:,.0f} "
        f"(${counterfactual_opex_savings:,.0f} OPEX saved + "
        f"${pillar_value_preserved:,.0f} pillar value protected). "
        f"Cumulative: +${hr_roi_cumulative:,.0f}."
    ) if hr_roi_this_round > 0 else (
        f"💼 HR ROI this round: $0 (no HR investment — "
        f"burnout accumulating, ${total_burnout_penalty_applied:,.0f} OPEX penalty active)."
    )


# ── R1: Set foundation flags ────────────────────────────────────
def _post_r1_foundations(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    """Apply reputation impacts from R1 option choice."""
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        # Legacy mode: read and apply from config
        cfg_opts = _fetch_options_for_industry(1, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        if "treasury" in impacts:
            _apply_treasury_with_green_fund(gs, abs(impacts["treasury"]) if impacts["treasury"] < 0 else -impacts["treasury"], extra)
        if "reputation" in impacts:
            gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))
            extra["reputation_applied_r1"] = impacts["reputation"]

        extra["r1_flags_set"] = opt.get("flags_set", [])
    else:
        extra["r1_pillar_bypass"] = True

    extra["r1_choice"] = choice


# ── R4: Contagion recovery — post-tick handler (Fix #2) ─
def _post_r4_contagion(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    """
    Apply treasury, reputation, social licence, and governance risk impacts
    from R4 pillar/legacy choices.
    """
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        # Legacy mode: read and apply from config
        cfg_opts = _fetch_options_for_industry(4, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        if "treasury" in impacts:
            _apply_treasury_with_green_fund(
                gs,
                abs(impacts["treasury"]) if impacts["treasury"] < 0 else -impacts["treasury"],
                extra,
            )

        rep = impacts.get("reputation", 0)
        if rep:
            gs["group_reputation"] = max(0.0, min(100.0, round(gs["group_reputation"] + rep, 2)))
            extra["r4_reputation_applied"] = rep
            extra["reputation_applied_r4"] = rep

        sl = impacts.get("social_license", 0)
        if sl:
            for bu in bus:
                bu["social_license_score"] = max(
                    0.0, min(100.0, round(bu.get("social_license_score", 50.0) + sl, 2))
                )
            extra["r4_social_license_applied"] = sl

        gov = impacts.get("governance_risk_delta", 0)
        if gov:
            for bu in bus:
                bu["governance_risk_score"] = max(
                    0.0, min(100.0, round(bu.get("governance_risk_score", 20.0) + gov, 2))
                )
            extra["r4_governance_risk_applied"] = gov
            extra["governance_risk_applied_r4"] = gov
    else:
        extra["r4_pillar_bypass"] = True

    extra["r4_choice"] = choice

    # ── ITEM 14: Social Media Velocity Amplifier (R4+) ────────
    # Digital amplification accelerates contagion in later rounds
    round_num = gs.get("round_number", 4) if "round_number" in gs else 4
    velocity_multiplier = round(1.0 + 0.1 * (round_num - 3), 2)
    current_rep = gs.get("group_reputation", 50)
    if current_rep < 60:  # Only amplifies negative reputation
        rep_penalty = round((60 - current_rep) * 0.1 * (velocity_multiplier - 1.0), 2)
        if rep_penalty > 0:
            gs["group_reputation"] = max(0, round(current_rep - rep_penalty, 2))
            extra["social_media_velocity"] = {
                "multiplier": velocity_multiplier,
                "reputation_penalty": rep_penalty,
                "message": (
                    f"📱 Social media amplification: Crisis spread {velocity_multiplier}× faster "
                    f"than baseline. Reputation hit amplified by {rep_penalty:.1f} points."
                ),
            }



# ── R3: Scope 3 mutations ────────────────────────────────────────────────────
def _post_r3_scope3(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        # Legacy mode: read and apply from config
        cfg_opts = _fetch_options_for_industry(3, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        if "treasury" in impacts:
            treasury_cost = abs(impacts["treasury"]) if impacts["treasury"] < 0 else -impacts["treasury"]

            # ── Gap 4 Fix: Green Bond pricing modulated by R2 materiality posture ──
            # If R2A (materiality_aligned): institutional investors offer -$500K discount
            # If R2C (materiality_ignored): risk premium adds +$1M
            if choice == "option_b":  # Green Bond option
                r2_flags = _collect_all_flags(prev_flags)
                if "materiality_aligned" in r2_flags:
                    discount = 500_000
                    treasury_cost = max(0, treasury_cost - discount)
                    extra["green_bond_r2_alignment_discount"] = discount
                    extra["green_bond_r2_alignment_message"] = (
                        "📊 R2 Materiality Alignment Bonus: Institutional investors rewarded "
                        "your CSRD governance posture with a $500K Green Bond discount."
                    )
                elif "materiality_ignored" in r2_flags:
                    premium = 1_000_000
                    treasury_cost += premium
                    extra["green_bond_r2_risk_premium"] = premium
                    extra["green_bond_r2_risk_message"] = (
                        "⚠️ R2 Materiality Penalty: Investors applied a $1M risk premium "
                        "on your Green Bond — your governance track record raised red flags."
                    )
            _apply_treasury_with_green_fund(gs, treasury_cost, extra)

        ncd_delta = impacts.get("natural_capital_debt_delta", 0)
        if ncd_delta != 0:
            for bu in bus:
                bu["natural_capital_debt"] = max(0, round(bu["natural_capital_debt"] + ncd_delta, 2))

        ci_delta = impacts.get("carbon_intensity_delta", 0)
        if ci_delta != 0:
            for bu in bus:
                bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))
            extra["carbon_intensity_applied_r3"] = ci_delta

        if impacts.get("supply_chain_disruption"):
            for bu in bus:
                if bu["bu_id"] in ("electronics", "pharma"):
                    bu["governance_risk_score"] = min(100, bu["governance_risk_score"] + 10)
            extra["supply_chain_disruption_applied"] = True

        if "reputation" in impacts:
            gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))
            extra["reputation_applied_r3"] = impacts["reputation"]
    else:
        extra["r3_pillar_bypass"] = True
        # Carbon intensity guard for _apply_common_impacts
        extra["carbon_intensity_applied_r3"] = True

    # ── Round-specific logic (runs for BOTH paradigms) ──
    # UN SDG: Option A (Compulsory Schooling) → create education_lag pending project
    if choice == "option_a" and any(bu.get("basic_needs") is not None for bu in bus):
        if "pending_capex_projects" not in gs:
            gs["pending_capex_projects"] = []
        gs["pending_capex_projects"].append({
            "type": "education_lag",
            "rounds_remaining": 3,
            "amount": 0.8,
            "description": "Education Investment Maturing (SDG 4 → SDG 8)"
        })
        extra["education_lag_project_started"] = True

    # ── ITEM 13: Scope 3 Data Availability Challenge ──────────
    # Models the real-world difficulty of getting suppliers to disclose
    scope3_completeness = 30  # Baseline: only 30% of supply chain visible
    if choice == "option_a":
        scope3_completeness = 80  # Direct supplier audit → high visibility
    elif choice == "option_b":
        scope3_completeness = 60  # Green bond with partial audit
    gs["scope3_data_completeness"] = scope3_completeness
    extra["scope3_data_completeness"] = scope3_completeness
    if scope3_completeness < 60:
        extra["scope3_data_challenge"] = {
            "completeness": scope3_completeness,
            "noise_pct": round((100 - scope3_completeness) * 0.15, 1),
            "message": (
                f"⚠️ Scope 3 Data Gap: Only {scope3_completeness}% of your supply chain "
                f"emissions are verifiable. Suppliers are resisting disclosure. "
                f"Reported emissions have ±{round((100 - scope3_completeness) * 0.15, 1)}% uncertainty."
            ),
        }

    extra["r3_choice"] = choice


# ── R5: Stochastic Climate Event (extracted to impact_engine.py) ──
# _post_r5_climate = _ie._post_r5_climate  (registered in _POST_TICK_MAP below)


# ── R6: AI Bias ──────────────────────────────────────────────────────────────
def _post_r6_ai_bias(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        cfg_opts = _fetch_options_for_industry(6, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        rev_delta = impacts.get("software_revenue_delta", 0)
        if rev_delta != 0:
            for bu in bus:
                if bu["bu_id"] == "software":
                    bu["revenue_base"] = round(bu["revenue_base"] + rev_delta, 2)
                    break
            extra["software_revenue_boosted"] = rev_delta

        rep_delta = impacts.get("reputation_delta", 0)
        if rep_delta != 0:
            gs["group_reputation"] = max(0, min(100, round(gs["group_reputation"] + rep_delta, 2)))

        if impacts.get("contagion_spike"):
            extra["contagion_spike_triggered"] = True

        if "treasury" in impacts:
            _apply_treasury_with_green_fund(gs, abs(impacts["treasury"]) if impacts["treasury"] < 0 else -impacts["treasury"], extra)

        sl_delta = impacts.get("social_license_delta", 0)
        if sl_delta != 0:
            for bu in bus:
                bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))
            extra["social_license_boosted"] = sl_delta

        gov_delta = impacts.get("governance_risk_delta", 0)
        if gov_delta != 0:
            for bu in bus:
                bu["governance_risk_score"] = max(0, min(100, round(bu["governance_risk_score"] + gov_delta, 2)))
            extra["governance_risk_applied_r6"] = gov_delta
    else:
        extra["r6_pillar_bypass"] = True

    extra["r6_choice"] = choice

    # ── ITEM 16: EU AI Act Compliance Trigger ─────────────────
    # If AI was monetised (Option A) without ethical audit, EU AI Act
    # triggers compliance costs from R7 onward
    if choice == "option_a":
        gs.setdefault("active_event_flags", {})["ai_monetised"] = True
        extra["eu_ai_act_pending"] = {
            "message": (
                "🏛️ EU AI Act: Your AI deployment is classified as 'high-risk' "
                "under the EU Artificial Intelligence Act (Article 6). "
                "Compliance audit costs will apply from Round 7."
            ),
        }
    # Apply deferred EU AI Act cost if the flag was set in a previous round
    all_flags = _collect_all_flags(prev_flags)
    if "ai_monetised" in all_flags and gs.get("round_number", 6) >= 7:
        ai_compliance_cost = 3_000_000
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - ai_compliance_cost, 2)
        for bu in bus:
            bu["governance_risk_score"] = min(100, round(
                bu.get("governance_risk_score", 20) + 5, 2
            ))
        extra["eu_ai_act_compliance"] = {
            "cost": ai_compliance_cost,
            "governance_risk_delta": 5,
            "message": (
                f"🏛️ EU AI ACT ENFORCEMENT: Mandatory bias audit + conformity "
                f"assessment cost ${ai_compliance_cost:,.0f}. Governance risk "
                f"increased +5 across all BUs. Deploying AI without ethical "
                f"review has ongoing regulatory consequences."
            ),
        }


# ── R7: Circularity — Option C unlocks synergy multiplier ──────────────────
def _post_r7_circularity(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        cfg_opts = _fetch_options_for_industry(7, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        if "treasury" in impacts:
            cost = abs(impacts["treasury"])
            fund = gs.get("green_transition_fund", 0.0)
            if fund >= cost:
                gs["green_transition_fund"] -= cost
                extra["green_fund_used"] = cost
            else:
                gs["green_transition_fund"] = 0.0
                gs["corporate_treasury"] = round(gs["corporate_treasury"] - (cost - fund), 2)
                extra["green_fund_used"] = fund

        ncd_delta = impacts.get("natural_capital_debt_delta", 0)
        if ncd_delta != 0:
            for bu in bus:
                bu["natural_capital_debt"] = max(0, round(bu["natural_capital_debt"] + ncd_delta, 2))

        if "reputation" in impacts:
            gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))
            extra["reputation_applied_r7"] = impacts["reputation"]

        syn_boost = impacts.get("synergy_multiplier_boost", 0)
    else:
        extra["r7_pillar_bypass"] = True
        # In pillar mode, synergy boost comes from pillar aggregate
        agg_impacts = events.get("pillar_aggregate_impacts", {})
        syn_boost = agg_impacts.get("synergy_multiplier_boost", 0)
    if syn_boost > 0:
        # ── Workforce Readiness Interdependency ──
        # Low readiness → workforce can't execute complex circular transitions
        readiness = gs.get("workforce_readiness", 50.0)
        readiness_modifier = 1.0
        if readiness < 40.0:
            readiness_modifier = 0.70  # 30% penalty: undertrained workforce
            extra["synergy_readiness_penalty"] = True
            extra["synergy_readiness_message"] = (
                f"⚠️ LOW WORKFORCE READINESS ({readiness:.0f}/100): "
                f"Synergy boost reduced by 30% — workforce lacks circular economy skills. "
                f"Earlier HR investment would have preserved full synergy potential."
            )
        elif readiness >= 60.0:
            readiness_modifier = 1.10  # 10% bonus: skilled workforce amplifies innovation
            extra["synergy_readiness_bonus"] = True

        effective_boost = round(syn_boost * readiness_modifier, 4)
        gs["synergy_multiplier"] = round(gs["synergy_multiplier"] + effective_boost, 4)
        extra["synergy_multiplier_unlocked"] = True
        extra["synergy_boost_amount"] = effective_boost
        extra["synergy_boost_base"] = syn_boost
        extra["synergy_readiness_modifier"] = readiness_modifier

    # Early Decarboniser Bonus: R3 Option A gives +0.10 synergy
    all_flags = _collect_all_flags(prev_flags)
    if "early_decarboniser" in all_flags:
        gs["synergy_multiplier"] = round(gs["synergy_multiplier"] + 0.10, 4)
        extra["early_decarboniser_synergy_bonus"] = True
        extra["early_decarboniser_bonus_amount"] = 0.10

    # Apply circular economy efficiency bonus to OPEX base
    if choice in ("option_a", "option_b"):
        bonus_pct = ECONOMIC_CIRCULAR_ECONOMY_BONUS
        for bu in bus:
            old_opex = bu.get("opex_base", 0.0)
            bu["opex_base"] = round(old_opex * (1.0 - bonus_pct), 2)
        extra["circular_efficiency_bonus_applied"] = bonus_pct
        extra["circular_efficiency_message"] = (
            f"♻️ Circular Economy Efficiency Bonus: Circular transition choices "
            f"reduced business unit operational expenses (OPEX) by {bonus_pct:.1%}."
        )

    extra["r7_choice"] = choice


# ── R8: Blue Stress ──────────────────────────────────────────────────────────
def _post_r8_blue_stress(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    # Blockchain traceability check (runs for both paradigms)
    all_flags = _collect_all_flags(prev_flags)
    scandal_prevented = "blockchain_traceability" in all_flags
    if scandal_prevented:
        extra["scandal_shock_prevented"] = True
        extra["blockchain_traceability_dividend"] = True
        gs["group_reputation"] = min(100, round(gs.get("group_reputation", 50) + 5, 2))

    if not pillar_mode:
        cfg_opts = _fetch_options_for_industry(8, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

        if scandal_prevented:
            impacts = {k: v for k, v in impacts.items()
                       if k not in ("governance_delta",) or v >= 0}

        if "treasury" in impacts:
            cost = abs(impacts["treasury"])
            fund = gs.get("green_transition_fund", 0.0)
            if fund >= cost:
                gs["green_transition_fund"] -= cost
                extra["green_fund_used"] = cost
            else:
                gs["green_transition_fund"] = 0.0
                gs["corporate_treasury"] = round(gs["corporate_treasury"] - (cost - fund), 2)
                extra["green_fund_used"] = fund
    else:
        extra["r8_pillar_bypass"] = True
        impacts = {}  # Standard impacts already applied by router

    # ── Round-specific logic (runs for BOTH paradigms) ──
    # Fix #8: Only fire if electronics_water_priority was EXPLICITLY chosen
    r8_pillar_flags = set(
        events.get("pillar_flags", [])
        or events.get(f"r8_pillar_flags", [])
        or []
    )
    explicit_electronics_priority = (
        "electronics_water_priority" in r8_pillar_flags
        or (choice == "option_b" and "water_efficiency_all" not in r8_pillar_flags
            and "desalination_built" not in r8_pillar_flags)
    )
    if impacts.get("social_license_severe_drop") and explicit_electronics_priority:
        targets = impacts.get("social_license_drop_targets", [])
        drop_amt = impacts.get("social_license_drop_amount", -25)
        for bu in bus:
            if bu["bu_id"] in targets:
                bu["social_license_score"] = max(0, round(bu["social_license_score"] + drop_amt, 2))
        extra["social_license_severe_drop_applied"] = targets
    elif impacts.get("social_license_severe_drop") and not explicit_electronics_priority:
        extra["social_license_severe_drop_skipped"] = True
        extra["social_license_severe_drop_reason"] = (
            "electronics_water_priority flag not found in pillar choices — "
            "severe SLO drop suppressed to prevent incorrect cost-proxy punishment."
        )

    # Option C: NCD reduction (Desalination Plant - Delayed CapEx)
    ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    if ncd_delta != 0:
        if "pending_capex_projects" not in gs:
            gs["pending_capex_projects"] = []
        gs["pending_capex_projects"].append({
            "type": "ncd_drop",
            "amount": ncd_delta,
            "bu_target": "all",
            "rounds_remaining": 2,
            "description": "Water Infrastructure Mega-Project"
        })
        extra["water_project_started"] = True

    # Water dependency reduction
    wd_delta = impacts.get("water_dependency_delta", 0)
    if wd_delta != 0:
        for bu in bus:
            bu["water_dependency"] = max(0, round(bu.get("water_dependency", 0) + wd_delta, 2))

    # Desalination payback: generates revenue over subsequent rounds
    gen_rev = impacts.get("generates_revenue", 0)
    payback_rounds = impacts.get("payback_rounds", 0)
    if gen_rev > 0 and payback_rounds > 0:
        if "pending_capex_projects" not in gs:
            gs["pending_capex_projects"] = []
        gs["pending_capex_projects"].append({
            "type": "revenue_generation",
            "amount": gen_rev,
            "rounds_remaining": payback_rounds,
            "description": "Desalination Plant Revenue Generation"
        })
        extra["desalination_payback_started"] = True
        extra["desalination_payback_per_round"] = gen_rev

    # Social licence boost (Option A)
    sl_delta = impacts.get("social_license_delta", 0)
    if sl_delta != 0:
        for bu in bus:
            bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))

    extra["r8_choice"] = choice


# ── R9: Just Transition (extracted to impact_engine.py) ──
# _post_r9_just_transition = _ie._post_r9_just_transition  (registered in _POST_TICK_MAP below)


# ── R10: Grand Finale — Terminal EBITDA, MR, Terminal Valuation ─────────────
def _post_r10_grand_finale(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    # FIX: Use industry-aware config so healthcare sessions get the correct R10 options.
    is_healthcare = any(b["bu_id"] == "hospitals" for b in bus)

    # ── Ending Pathway Detection ──
    ending_pathway = prev_flags.get("ending_pathway", "activist_ultimatum")
    extra["ending_pathway"] = ending_pathway

    # Load pathway-specific R10 config if not the default activist_ultimatum
    if ending_pathway not in ("activist_ultimatum", "") and not is_healthcare:
        from ending_pathways import get_pathway_r10_config, get_pathway_r10_options
        pw_cfg = get_pathway_r10_config(ending_pathway)
        if pw_cfg:
            cfg = pw_cfg
            cfg_opts = get_pathway_r10_options(ending_pathway)
            opt = cfg_opts.get(choice, {})
            impacts = opt.get("impacts", {})
            special = cfg.get("special_rules", {}) if cfg else {}
            all_flags = _collect_all_flags(prev_flags)
            extra["pathway_config_loaded"] = True
        else:
            # Fallback to standard configs
            cfg = get_round_config(10)
            cfg_opts = get_round_options(10)
            opt = cfg_opts.get(choice, {})
            impacts = opt.get("impacts", {})
            special = cfg.get("special_rules", {}) if cfg else {}
            all_flags = _collect_all_flags(prev_flags)
    elif is_healthcare:
        from healthcare_configs import get_healthcare_round_config, get_healthcare_round_options
        cfg = get_healthcare_round_config(10)
        cfg_opts = get_healthcare_round_options(10)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})
        special = cfg.get("special_rules", {}) if cfg else {}
        all_flags = _collect_all_flags(prev_flags)
    else:
        cfg = get_round_config(10)
        cfg_opts = get_round_options(10)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})
        special = cfg.get("special_rules", {}) if cfg else {}
        all_flags = _collect_all_flags(prev_flags)

    carbon_tax_per_ton = special.get("carbon_tax_per_ton", 250)
    exit_multiple = special.get("exit_multiple", 12.0)

    # ── Check for God Mode carbon tax override ──
    if prev_flags.get("carbon_tax_override_active"):
        carbon_tax_per_ton = prev_flags.get("carbon_tax_per_ton", carbon_tax_per_ton)

    # ── Apply Activist Ultimatum choice effects first ──
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Option A: Resist & Integrate — validate synergy gate
    synergy_gate = special.get("synergy_gate_threshold", 80)
    synergy_score = gs.get("synergy_multiplier", 1.0) * 100  # normalise
    # ═══════════════════════════════════════════════════════════════
    #  REGENERATIVE MULTIPLE (M_R)
    #  Base = 1.0
    #  +0.10  CSRD Governance Premium: R2A materiality_aligned (NEW)
    #  +0.30  if synergy achieved in R7  (synergy_unlock flag)
    #  +0.20  if survived R5/R8 without bailout
    #  +0.15  Truth Premium from R6 (ethical_ai_overhaul flag)
    #  +0.18  Community Champion R9 (community_fund)
    #  +0.12  Just Transition R9 (managed_transition)
    #  +0.10  Workforce Excellence (readiness >= 75)
    #  +0.05  Wellbeing Champion (avg burnout < 20)
    #  −0.40  Instability Discount if Social License < 75
    #  Max achievable (all bonuses): 1.0+0.10+0.30+0.20+0.15+0.18+0.10+0.05 = 2.08
    # ═══════════════════════════════════════════════════════════════
    if choice == "option_a":
        if synergy_score <= synergy_gate:
            # Should have been blocked by frontend; force fallback to B
            extra["synergy_gate_blocked"] = True
            extra["synergy_gate_message"] = (
                f"Resist & Integrate blocked: Synergy Score "
                f"{synergy_score:.0f} ≤ {synergy_gate}. Defaulting to Spin-off."
            )
            choice = "option_b"
            opt = cfg_opts.get(choice, {})
            impacts = opt.get("impacts", {})
        else:
            extra["synergy_gate_passed"] = True

    # Option B: Spin-off weakest BU
    if impacts.get("spinoff_weakest_bu"):
        weakest = min(bus, key=lambda b: b["revenue_base"] - b["opex_base"])
        extra["spinoff_bu_id"] = weakest["bu_id"]
        extra["spinoff_bu_margin"] = round(weakest["revenue_base"] - weakest["opex_base"], 2)
        # Remove weakest BU's contribution from terminal calc
        weakest["revenue_base"] = 0
        weakest["opex_base"] = 0

    # Option C: Divest — wipe synergy
    if impacts.get("synergy_wipe"):
        gs["synergy_multiplier"] = 1.0
        extra["synergy_wiped"] = True

    # ── Pathway-Specific Option Processing ───────────────────────────
    if ending_pathway == "climate_black_swan":
        # Option A: Emergency Decarb — halve CI and NCD
        if impacts.get("carbon_intensity_halve"):
            for bu in bus:
                bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) / 2, 2))
            extra["carbon_intensity_halved"] = True
        if impacts.get("ncd_halve"):
            for bu in bus:
                bu["natural_capital_debt"] = max(0, round(bu.get("natural_capital_debt", 0) / 2, 2))
            extra["ncd_halved"] = True
        # Option B: Divest high-CI BUs at fire-sale
        if impacts.get("divest_high_ci"):
            ci_threshold = impacts.get("ci_divest_threshold", 40)
            realloc = impacts.get("reallocation_per_bu", 3_000_000)
            divested_bus = []
            remaining_bus = []
            for bu in bus:
                if bu.get("carbon_intensity", 0) > ci_threshold:
                    # Fire-sale: 50% of book value added to treasury
                    book_val = max(0, bu["revenue_base"] - bu["opex_base"])
                    gs["corporate_treasury"] = round(gs["corporate_treasury"] + book_val * 0.5, 2)
                    bu["revenue_base"] = 0
                    bu["opex_base"] = 0
                    divested_bus.append(bu["bu_id"])
                else:
                    remaining_bus.append(bu["bu_id"])
            # Reallocation to remaining BUs
            for bu in bus:
                if bu["bu_id"] in remaining_bus:
                    bu["revenue_base"] = round(bu["revenue_base"] + realloc, 2)
            extra["climate_divested_bus"] = divested_bus
            extra["climate_remaining_bus"] = remaining_bus
        # Option C: carbon_tax_triple + ncd_double
        if impacts.get("carbon_tax_triple"):
            carbon_tax_per_ton = 750
            extra["carbon_tax_tripled"] = True
        if impacts.get("ncd_double"):
            for bu in bus:
                bu["natural_capital_debt"] = round(bu.get("natural_capital_debt", 0) * 2, 2)
            extra["ncd_doubled"] = True
        if impacts.get("exit_multiple_override"):
            exit_multiple = impacts["exit_multiple_override"]
            extra["exit_multiple_overridden"] = exit_multiple
        if impacts.get("mr_penalty"):
            extra["pathway_mr_penalty_from_option"] = impacts["mr_penalty"]

    elif ending_pathway == "stakeholder_revolt":
        # Option A: Revenue boost from brand loyalty
        if impacts.get("revenue_boost_pct"):
            boost = impacts["revenue_boost_pct"]
            for bu in bus:
                bu["revenue_base"] = round(bu["revenue_base"] * (1 + boost), 2)
            extra["stakeholder_revenue_boost"] = boost
        # Option B: Selective appeasement
        if impacts.get("selective_fix"):
            avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
            avg_bo = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)
            # Auto-fix worst dimension
            if avg_bo > (100 - avg_slo):  # burnout is worse
                for bu in bus:
                    bu["staff_burnout_index"] = max(0, round(bu.get("staff_burnout_index", 0) - 20, 2))
                extra["selective_fix_target"] = "employee_burnout"
            else:
                for bu in bus:
                    bu["social_license_score"] = min(100, round(bu.get("social_license_score", 0) + 15, 2))
                extra["selective_fix_target"] = "community_slo"
            # Unaddressed groups escalate
            penalty = impacts.get("unaddressed_slo_penalty", -10)
            if extra.get("selective_fix_target") == "employee_burnout":
                for bu in bus:
                    bu["social_license_score"] = max(0, round(bu.get("social_license_score", 0) + penalty, 2))
            else:
                for bu in bus:
                    bu["staff_burnout_index"] = min(100, round(bu.get("staff_burnout_index", 0) + 10, 2))
        # Option C: Corporate hardball
        if impacts.get("slo_all_penalty"):
            for bu in bus:
                bu["social_license_score"] = max(0, round(bu.get("social_license_score", 0) + impacts["slo_all_penalty"], 2))
        if impacts.get("burnout_all_increase"):
            for bu in bus:
                bu["staff_burnout_index"] = min(100, round(bu.get("staff_burnout_index", 0) + impacts["burnout_all_increase"], 2))
        if impacts.get("shutter_zero_slo"):
            for bu in bus:
                if bu.get("social_license_score", 0) <= 0:
                    extra.setdefault("shuttered_bus", []).append(bu["bu_id"])
                    bu["revenue_base"] = 0
                    bu["opex_base"] = 0
        if impacts.get("mr_penalty"):
            extra["pathway_mr_penalty_from_option"] = impacts["mr_penalty"]

    elif ending_pathway == "hostile_takeover":
        # Option A: White Knight — revenue drag
        if impacts.get("white_knight"):
            drag = impacts.get("revenue_drag_pct", -0.05)
            for bu in bus:
                bu["revenue_base"] = round(bu["revenue_base"] * (1 + drag), 2)
            extra["white_knight_revenue_drag"] = drag
        # Option B: Poison pill — exit multiple override
        if impacts.get("poison_pill"):
            if impacts.get("exit_multiple_override"):
                exit_multiple = impacts["exit_multiple_override"]
                extra["exit_multiple_overridden"] = exit_multiple
            extra["poison_pill_deployed"] = True
        # Option C: Accept bid — M_R cap + exit multiple override
        if impacts.get("mr_cap"):
            extra["mr_cap"] = impacts["mr_cap"]
        if impacts.get("exit_multiple_override") and not impacts.get("poison_pill"):
            exit_multiple = impacts["exit_multiple_override"]
            extra["exit_multiple_overridden"] = exit_multiple
        if impacts.get("mr_penalty"):
            extra["pathway_mr_penalty_from_option"] = impacts["mr_penalty"]

    elif ending_pathway == "regulatory_shutdown":
        # Option A: Full remediation — compliance cost per BU
        if impacts.get("compliance_cost_all_bus"):
            cost_per_bu = special.get("compliance_cost_per_bu", 4_000_000)
            total_cost = cost_per_bu * len(bus)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - total_cost, 2)
            extra["compliance_cost_total"] = total_cost
            extra["compliance_cost_per_bu"] = cost_per_bu
        # Option B: Consent decree — exit multiple override
        if impacts.get("consent_decree"):
            if impacts.get("exit_multiple_override"):
                exit_multiple = impacts["exit_multiple_override"]
                extra["exit_multiple_overridden"] = exit_multiple
            extra["consent_decree_active"] = True
        # Option C: Legal challenge — outcome based on ethical score
        if impacts.get("legal_challenge"):
            # Calculate ethical score to determine outcome
            avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)
            avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
            group_rep = gs.get("group_reputation", 50.0)
            ethical_score = (avg_slo * 0.3 + (100 - avg_ci) * 0.3 + group_rep * 0.4) / 10
            # Legal costs regardless of outcome
            gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts.get("legal_costs", -10_000_000), 2)
            if ethical_score >= 5:
                # Successful challenge — no fine, mild reputation hit
                gs["group_reputation"] = max(0, round(group_rep - 10, 2))
                extra["legal_challenge_outcome"] = "successful"
                extra["legal_challenge_ethical_score"] = round(ethical_score, 2)
            else:
                # Failed — double fine, suspend worst BU, exit 7×
                fine = special.get("fine_base", 30_000_000) * 2
                gs["corporate_treasury"] = round(gs["corporate_treasury"] - fine, 2)
                exit_multiple = 7.0
                extra["exit_multiple_overridden"] = 7.0
                gs["group_reputation"] = max(0, round(group_rep - 30, 2))
                # Suspend worst-performing BU
                worst_bu = min(bus, key=lambda b: b.get("social_license_score", 100))
                worst_bu["revenue_base"] = 0
                worst_bu["opex_base"] = 0
                extra["legal_challenge_outcome"] = "failed"
                extra["legal_challenge_fine"] = fine
                extra["legal_challenge_suspended_bu"] = worst_bu["bu_id"]
                extra["legal_challenge_ethical_score"] = round(ethical_score, 2)
        if impacts.get("mr_penalty"):
            extra["pathway_mr_penalty_from_option"] = impacts["mr_penalty"]

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  Terminal_EBITDA = Î£(Revenue_i âˆ’ OPEX_i) âˆ’ (Carbon_Tonnage Ã— $250/ton)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    total_revenue = sum(bu["revenue_base"] for bu in bus)
    total_opex = sum(bu["opex_base"] for bu in bus)

    # Carbon tonnage: sum of carbon_intensity Ã— revenue scale across all BUs
    # FIX AUDIT-027: Use correct revenue-scaled formula for carbon tonnage, matching engine.py
    carbon_tonnage_group = sum(
        bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000 
        for bu in bus
    )
    carbon_cost = round(carbon_tonnage_group * carbon_tax_per_ton, 2)

    terminal_ebitda = round(
        (total_revenue - total_opex) - carbon_cost,
        2,
    )

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  REGENERATIVE MULTIPLE (M_R)
    #  Base = 1.0
    #  +0.30  if synergy achieved in R7  (synergy_unlock flag)
    #  +0.20  if survived R5/R8 without bailout
    #  +0.15  Truth Premium from R6 (ethical_ai_overhaul flag)
    #  âˆ’0.40  Instability Discount if Social License < 75
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    mr = 1.0

    # +0.10: R2 Materiality Governance Alignment (CSRD good governance → long-term value)
    # Awarded when players chose Option A (Full Materiality Alignment) in Round 2.
    # This closes the pedagogical promise: "getting materiality right creates long-term value."
    if "materiality_aligned" in all_flags:
        mr += 0.10
        extra["mr_materiality_governance_bonus"] = True
        extra["mr_materiality_governance_message"] = (
            "📊 CSRD Governance Premium: Your Round 2 full materiality alignment earned "
            "+0.10 M_R. Institutional investors reward companies that embed ESG governance "
            "rigorously from the outset (ESRS 1 — General Requirements)."
        )

    # +0.15: R7 Synergy achieved (waste_to_energy / synergy_unlock)
    # STRAT-010: Reduced from +0.30 → +0.15.
    # Synergy OPEX savings ALREADY raise terminal_ebitda through the synergy engine.
    # Adding +0.30 on top multiplied a benefit already captured in the EBITDA base.
    # +0.15 represents the *strategic optionality premium* — the investor premium for
    # integrated, synergistic BUs, separate from the pure cash-flow benefit.
    if "synergy_unlock" in all_flags or "waste_to_energy" in all_flags:
        mr += 0.15
        extra["mr_synergy_bonus"] = True

    # +0.2: Survived R5/R8 without bailout
    r5_bailout = "insurance_only" in all_flags
    r8_bailout = "electronics_water_priority" in all_flags or "civil_water_priority" in all_flags
    if not r5_bailout and not r8_bailout:
        mr += 0.2
        extra["mr_resilience_bonus"] = True

    # +0.15: Truth Premium from R6 (chose ethical AI overhaul)
    if "ethical_ai_overhaul" in all_flags:
        mr += 0.15
        extra["mr_truth_premium"] = True

    # +0.18: Community Champion (highest just-transition investment in R9)
    # Requires community_fund — the $20M community investment, not just managed closure.
    # Narrowed gap from +0.20/+0.10 to +0.18/+0.12 so managed_transition
    # retains meaningful pedagogical value (not just a "consolation prize").
    #   community_fund (−$20M) → +0.18   [community-led transformation]
    #   managed_transition (−$12M) → +0.12 [responsible but company-led]
    if "community_fund" in all_flags:
        mr += 0.18
        extra["mr_community_champion_bonus"] = True
    elif "managed_transition" in all_flags:
        mr += 0.12
        extra["mr_just_transition_bonus"] = True

    # +0.10: Workforce Excellence (workforce_readiness >= 75 at R10)
    # Rewards sustained HR investment across multiple rounds.
    workforce_readiness = gs.get("workforce_readiness", 50.0)
    if workforce_readiness >= 75.0:
        mr += 0.10
        extra["mr_workforce_bonus"] = True
        extra["mr_workforce_readiness"] = round(workforce_readiness, 2)

    # +0.05: Wellbeing Champion (avg burnout < 20 at terminal valuation)
    # Rewards early, sustained HR investment — requires consistently choosing HIGH-tier
    # HRM options (typically 6+ rounds) to keep burnout below the 20-point OPEX threshold.
    # This is the second HRM-linked M_R pathway, complementing workforce_readiness.
    # Max M_R with all 6 bonuses: 1.0+0.3+0.2+0.20+0.10+0.10+0.05 = 1.95
    avg_burnout_r10 = round(
        sum(bu.get("staff_burnout_index", 0.0) for bu in bus) / len(bus), 2
    ) if bus else 0.0
    if avg_burnout_r10 < 20.0:
        mr += 0.05
        extra["mr_wellbeing_bonus"] = True
        extra["mr_wellbeing_avg_burnout"] = avg_burnout_r10
    # Just Transition M_R Scaling: bonus scales with sustained HR investment
    # Models ILO Just Transition Guidelines (social dialogue as process)
    # Use prev_flags (dict) not all_flags (set) for key-value iteration
    hr_investment_rounds = sum(
        1 for k, v in prev_flags.items()
        if isinstance(k, str) and k.startswith("hr_invested_r") and v is True
    )
    if hr_investment_rounds > 0 and (extra.get("mr_community_champion_bonus") or extra.get("mr_just_transition_bonus")):
        jt_scaling = round(1.0 + hr_investment_rounds * 0.10, 2)
        jt_scaling = min(jt_scaling, 1.5)  # Cap at +50%
        if extra.get("mr_community_champion_bonus"):
            mr += round(0.18 * jt_scaling, 4) - 0.18
        elif extra.get("mr_just_transition_bonus"):
            mr += round(0.12 * jt_scaling, 4) - 0.12
        extra["mr_jt_scaling_factor"] = jt_scaling
        extra["mr_jt_hr_rounds"] = hr_investment_rounds

    # Instability Discount if avg Social License < 75
    avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 0
    if avg_sl < 75:
        mr -= 0.4
        extra["mr_instability_discount"] = True
        extra["mr_instability_avg_sl"] = round(avg_sl, 2)

    mr = round(mr, 4)

    # ── Pathway-Specific M_R Modifiers ─────────────────────────────
    if ending_pathway == "climate_black_swan":
        from ending_pathways import calc_climate_black_swan_mr, calc_climate_exit_multiple
        pathway_mr = calc_climate_black_swan_mr(bus, gs, all_flags, extra)
        mr += pathway_mr
        # Apply option-level M_R penalty (Option C: -0.40)
        mr += extra.get("pathway_mr_penalty_from_option", 0)
        # CI-based exit multiple haircut
        if special.get("exit_multiple_ci_haircut") and not extra.get("exit_multiple_overridden"):
            exit_multiple = calc_climate_exit_multiple(bus, exit_multiple)
            extra["exit_multiple_ci_haircut"] = exit_multiple
    elif ending_pathway == "stakeholder_revolt":
        from ending_pathways import calc_stakeholder_revolt_mr
        pathway_mr = calc_stakeholder_revolt_mr(bus, gs, all_flags, extra)
        mr += pathway_mr
        # Apply option-level M_R penalty (Option C: -0.30)
        mr += extra.get("pathway_mr_penalty_from_option", 0)
    elif ending_pathway == "hostile_takeover":
        from ending_pathways import calc_hostile_takeover_mr
        pathway_mr = calc_hostile_takeover_mr(bus, gs, all_flags, extra)
        mr += pathway_mr
        mr += extra.get("pathway_mr_penalty_from_option", 0)
        # Option C: M_R cap
        if extra.get("mr_cap"):
            mr = min(mr, extra["mr_cap"])
            extra["mr_capped_at"] = extra["mr_cap"]
    elif ending_pathway == "regulatory_shutdown":
        from ending_pathways import calc_regulatory_shutdown_mr
        pathway_mr = calc_regulatory_shutdown_mr(bus, gs, all_flags, extra)
        mr += pathway_mr
        mr += extra.get("pathway_mr_penalty_from_option", 0)

    mr = round(mr, 4)

    # ---------------------------------------------------------------
    #  TERMINAL VALUE = (Terminal_EBITDA + Green_Fund) x Exit_Multiple x M_R
    #  Green Fund included as accumulated climate capital (AC mode)
    #
    #  STRAT-010: Dynamic exit multiple derived from WACC via Gordon Growth Model.
    #  Exit_Multiple = (1 + g) / (WACC − g)
    #  Teams that raised WACC through poor ESG governance now pay a multiple haircut.
    # ---------------------------------------------------------------
    from terminal_valuation import calculate_dynamic_exit_multiple, calculate_equity_bridge, SHARES_OUTSTANDING
    green_fund_balance = gs.get("green_transition_fund", 0.0)
    green_fund_terminal_bonus = green_fund_balance if green_fund_balance > 0 else 0.0
    if green_fund_terminal_bonus > 0:
        extra["green_fund_terminal_bonus"] = green_fund_terminal_bonus

    # ── Dynamic exit multiple (WACC-based) ──
    # Only override if exit_multiple hasn't been hard-set by a pathway special rule.
    current_wacc = gs.get("active_event_flags", {}).get("esg_adjusted_wacc", {})
    if isinstance(current_wacc, dict):
        wacc_value = current_wacc.get("adjusted_wacc", gs.get("cost_of_capital", 0.08))
    else:
        wacc_value = gs.get("cost_of_capital", 0.08)
    dynamic_multiple_result = calculate_dynamic_exit_multiple(wacc=wacc_value)
    dynamic_exit_multiple = dynamic_multiple_result["exit_multiple"]
    # Pathway-overridden exit_multiple (e.g. 7× for regulatory_shutdown) takes precedence
    effective_exit_multiple = exit_multiple  # may already be overridden by pathway rule
    if not extra.get("exit_multiple_overridden") and not extra.get("exit_multiple_ci_haircut"):
        effective_exit_multiple = dynamic_exit_multiple
        extra["exit_multiple_dynamic"] = True
    extra["exit_multiple_wacc_used"] = round(wacc_value, 4)
    extra["dynamic_exit_multiple_detail"] = dynamic_multiple_result

    terminal_value = round((terminal_ebitda + green_fund_terminal_bonus) * effective_exit_multiple * mr, 2)

    # ── STRAT-010: Equity Bridge ──────────────────────────────────────────────
    # Enterprise Value (TV) − Net Debt = Equity Value → Price Per Share
    # Net Debt = financial debt (revolving credit + bonds) − treasury cash
    # Balance sheet data (may be absent in early rounds — graceful fallback)
    _bs = gs.get("balance_sheet", {})
    _ncl = _bs.get("non_current_liabilities", {})
    _cl  = _bs.get("current_liabilities", {})
    total_financial_debt = (
        _ncl.get("revolving_credit_facility", 50_000_000)
        + _ncl.get("green_bonds_outstanding", 0.0)
        + _cl.get("short_term_debt", 0.0)
    )
    treasury_cash = gs.get("corporate_treasury", 0.0)
    net_debt = round(total_financial_debt - treasury_cash, 2)
    book_equity = _bs.get("net_assets", 0.0)  # IAS 1 net assets (total equity)

    equity_bridge = calculate_equity_bridge(
        enterprise_value=terminal_value,
        net_debt=net_debt,
        shares_outstanding=SHARES_OUTSTANDING,
        book_equity=book_equity,
        total_revenue=total_revenue,
    )
    equity_value    = equity_bridge["equity_value"]
    price_per_share = equity_bridge["price_per_share"]           # floored at $1 (never negative)
    equity_wiped_out = equity_bridge.get("equity_wiped_out", equity_value < 0)

    # ===================================================
    #  Year 5 PROFILE ARCHETYPE
    #  Custom archetypes from god-mode take priority
    # ===================================================
    try:
        from admin_shared import _god_mode_settings
        custom_archetypes = _god_mode_settings.get("custom_archetypes", [])
    except ImportError:
        custom_archetypes = []

    profile_icon = None
    profile_gradient = None

    # AR-A/C: Double-Materiality Adjusted Value = final_treasury x M_R - NCD —
    # the same figure the reveal shows. Drives the solvency axis for both the
    # default gate and custom (facilitator-configured) archetypes.
    _dmav = gs.get("corporate_treasury", 0.0) * mr - sum(
        b.get("natural_capital_debt", 0) for b in bus
    )
    _solvent = _dmav > 0

    if custom_archetypes:
        matched = match_custom_archetype(custom_archetypes, mr, _solvent)
        profile = matched["key"]
        profile_title = matched["title"]
        profile_desc = matched.get("description", "")
        profile_icon = matched.get("icon", "")
        profile_gradient = matched.get("gradient", "linear-gradient(135deg, #6366f1, #8b5cf6)")
    else:
        thresholds = special.get("profile_thresholds", {})
        if mr >= thresholds.get("regenerative_titan", 1.8):
            profile = "regenerative_titan"
            profile_title = "The Regenerative Titan"
            profile_desc = "A truly regenerative enterprise."
            profile_icon = ""
            profile_gradient = "linear-gradient(135deg, #10b981, #059669)"
        elif mr >= thresholds.get("derisked_safe_haven", 1.2):
            profile = "derisked_safe_haven"
            profile_title = "The De-risked Safe-Haven"
            profile_desc = "A resilient corporation that avoided the worst tail risks."
            profile_icon = ""
            profile_gradient = "linear-gradient(135deg, #3b82f6, #1d4ed8)"
        elif mr >= thresholds.get("fragile_giant", 0.8):
            profile = "fragile_giant"
            profile_title = "The Fragile Giant"
            profile_desc = "Big but brittle."
            profile_icon = ""
            profile_gradient = "linear-gradient(135deg, #f59e0b, #d97706)"
        else:
            # AR-B: solvent low-M_R is the "Pragmatic Operator" — kept the lights
            # on, unremarkable. "Stranded Relic" is reserved for value
            # destruction (applied by the solvency gate below); a solvent,
            # cautious operator is no longer mislabelled a failure.
            profile = "pragmatic_operator"
            profile_title = "The Pragmatic Operator"
            profile_desc = (
                "Kept the lights on — solvent and steady, but the strategy "
                "left regenerative value on the table."
            )
            profile_icon = ""
            profile_gradient = "linear-gradient(135deg, #475569, #334155)"

        # AR-A: solvency gate. The ladder above chose on M_R alone; if the
        # company ended value-destroyed (DMAV <= 0, the figure the reveal shows,
        # computed above), it cannot keep a flattering label.
        _gated = solvency_gated_profile(profile, _dmav)
        if _gated != profile:
            profile = _gated
            if profile == "hollow_idealist":
                profile_title = "The Hollow Idealist"
                profile_desc = (
                    "A regenerative story the balance sheet couldn't fund — "
                    "enterprise value turned negative."
                )
                profile_icon = ""
                profile_gradient = "linear-gradient(135deg, #a855f7, #7e22ce)"
            else:
                profile_title = "The Stranded Relic"
                profile_desc = (
                    "Value destroyed — Natural Capital Debt and losses outran "
                    "the M_R-adjusted balance sheet."
                )
                profile_icon = ""
                profile_gradient = "linear-gradient(135deg, #ef4444, #b91c1c)"

    # Healthcare archetype override: use industry-specific names
    if is_healthcare and not custom_archetypes:
        hc_archetypes = special.get("healthcare_archetypes", {})
        if profile in hc_archetypes:
            hc_arch = hc_archetypes[profile]
            profile_title = hc_arch.get("title", profile_title)
            profile_desc = hc_arch.get("description", profile_desc)
            profile_icon = hc_arch.get("icon", profile_icon)
            profile_gradient = hc_arch.get("gradient", profile_gradient)

    # Ending pathway archetype override: use pathway-specific names/icons
    if ending_pathway not in ("activist_ultimatum", "") and not custom_archetypes and not is_healthcare:
        from ending_pathways import get_pathway_archetype_overrides
        pw_archetypes = get_pathway_archetype_overrides(ending_pathway)
        if profile in pw_archetypes:
            pw_arch = pw_archetypes[profile]
            profile_title = pw_arch.get("title", profile_title)
            profile_icon = pw_arch.get("icon", profile_icon)
            profile_gradient = pw_arch.get("gradient", profile_gradient)

    # AR-A: resolve the UPPERCASE reveal key the capstone screen themes off.
    # gs['archetype'] was never populated, so the reveal fell back to SAFE_HAVEN
    # for every player regardless of outcome — wire the real archetype through.
    archetype_key = terminal_archetype_key(profile, mr)
    extra["archetype"] = archetype_key

    # Populate Extra & Global State
    extra["terminal_ebitda"] = terminal_ebitda
    extra["carbon_tonnage_group"] = carbon_tonnage_group
    extra["carbon_cost"] = carbon_cost
    extra["carbon_tax_per_ton"] = carbon_tax_per_ton
    extra["regenerative_multiple"] = mr
    # FIX-002: Use JT-scaled values in breakdown for facilitator accuracy
    _jt_scale = extra.get("mr_jt_scaling_factor", 1.0)
    extra["mr_breakdown"] = {
        "base": 1.0,
        "materiality_governance": 0.10 if extra.get("mr_materiality_governance_bonus") else 0,
        # STRAT-010: +0.15 (reduced from +0.30 to remove double-count with EBITDA synergy savings)
        "synergy_bonus": 0.15 if extra.get("mr_synergy_bonus") else 0,
        "resilience_bonus": 0.2 if extra.get("mr_resilience_bonus") else 0,
        "truth_premium": 0.15 if extra.get("mr_truth_premium") else 0,
        "community_champion_bonus": round(0.18 * _jt_scale, 4) if extra.get("mr_community_champion_bonus") else 0,
        "just_transition_bonus": round(0.12 * _jt_scale, 4) if extra.get("mr_just_transition_bonus") else 0,
        "jt_scaling_factor": _jt_scale if _jt_scale != 1.0 else None,
        "workforce_bonus": 0.10 if extra.get("mr_workforce_bonus") else 0,
        "wellbeing_bonus": 0.05 if extra.get("mr_wellbeing_bonus") else 0,
        "instability_discount": -0.4 if extra.get("mr_instability_discount") else 0,
        "max_achievable_mr": 1.93,  # STRAT-010: 1.0+0.10+0.15+0.20+0.15+0.18+0.10+0.05 = 1.93 (2.03 with JT-scaling)
    }
    # Enrich mr_breakdown with pathway-specific bonuses.
    # FIX-002 follow-up: report the ACTUAL ramped value the M_R received —
    # the GAME-2 ramp calculators store it in extra (e.g. a partially-earned
    # climate-leader bonus of +0.12) — never the nominal full bonus. The
    # end-of-game ESG Leadership radar consumes these entries and must agree
    # with the M_R that terminal value actually applied. Boolean extras
    # (flat, flag-based bonuses like adaptation_premium) keep their nominal.
    def _mrb(extra_key: str, nominal: float) -> float:
        v = extra.get(extra_key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        return nominal if v else 0
    if ending_pathway == "climate_black_swan":
        extra["mr_breakdown"]["climate_leader"] = _mrb("mr_climate_leader_bonus", 0.30)
        extra["mr_breakdown"]["adaptation_premium"] = _mrb("mr_adaptation_premium", 0.20)
        extra["mr_breakdown"]["carbon_transition"] = _mrb("mr_carbon_transition_bonus", 0.15)
        extra["mr_breakdown"]["stranded_asset_penalty"] = _mrb("mr_stranded_asset_penalty", -0.40)
        extra["mr_breakdown"]["option_mr_penalty"] = extra.get("pathway_mr_penalty_from_option", 0)
    elif ending_pathway == "stakeholder_revolt":
        extra["mr_breakdown"]["social_regeneration"] = _mrb("mr_social_regeneration_bonus", 0.35)
        extra["mr_breakdown"]["employee_champion"] = _mrb("mr_employee_champion_bonus", 0.15)
        extra["mr_breakdown"]["community_trust"] = _mrb("mr_community_trust_bonus", 0.15)
        extra["mr_breakdown"]["social_collapse"] = _mrb("mr_social_collapse_penalty", -0.50)
        extra["mr_breakdown"]["option_mr_penalty"] = extra.get("pathway_mr_penalty_from_option", 0)
    extra["terminal_value"] = terminal_value
    extra["exit_multiple"] = effective_exit_multiple
    extra["exit_multiple_applied"] = effective_exit_multiple      # STRAT-010 (consistent alias)
    extra["final_treasury"] = gs["corporate_treasury"]
    extra["profile"] = profile
    extra["profile_title"] = profile_title
    extra["profile_description"] = profile_desc
    extra["profile_icon"] = profile_icon
    extra["profile_gradient"] = profile_gradient
    extra["synergy_score"] = round(synergy_score, 2)
    extra["avg_social_license"] = round(avg_sl, 2)
    extra["r10_choice"] = choice
    # STRAT-010: Equity bridge fields
    extra["equity_value"]       = equity_value
    extra["price_per_share"]    = price_per_share
    extra["equity_wiped_out"]   = equity_wiped_out
    extra["net_debt"]           = net_debt
    extra["shares_outstanding"] = SHARES_OUTSTANDING
    extra["equity_bridge"]      = equity_bridge
    extra["total_financial_debt"] = total_financial_debt

    # ── HR ROI Report ──
    # Compute cumulative HR investment value for facilitator debrief
    avg_burnout = round(sum(bu.get("staff_burnout_index", 0.0) for bu in bus) / max(len(bus), 1), 2)
    burnout_opex_rate = ((max(0, avg_burnout - 20) ** 2) * 0.000028125) if avg_burnout > 20 else 0.0
    total_opex = sum(bu.get("opex_base", 0) for bu in bus)
    burnout_opex_cost = round(burnout_opex_rate * total_opex, 2)
    hr_mr_value = 0.0
    if extra.get("mr_workforce_bonus"):
        hr_mr_value += 0.10
    if extra.get("mr_wellbeing_bonus"):
        hr_mr_value += 0.05
    hr_terminal_uplift = round(terminal_ebitda * exit_multiple * hr_mr_value, 2) if hr_mr_value > 0 else 0

    extra["hr_roi_report"] = {
        "avg_burnout_r10": avg_burnout,
        "workforce_readiness_r10": round(workforce_readiness, 2),
        "burnout_opex_penalty_rate": round(burnout_opex_rate * 100, 2),  # as percentage
        "burnout_opex_cost_per_round": burnout_opex_cost,
        "mr_bonus_from_hr": hr_mr_value,
        "terminal_value_uplift_from_hr": hr_terminal_uplift,
        "workforce_bonus_earned": bool(extra.get("mr_workforce_bonus")),
        "wellbeing_bonus_earned": bool(extra.get("mr_wellbeing_bonus")),
    }

    # Additional KPIs for the TBL-BSC 4Ã—3 Grid
    extra["total_revenue"] = total_revenue
    extra["total_opex"] = total_opex
    extra["instability_discount_applied"] = bool(extra.get("mr_instability_discount"))
    # R&D allocation: sum capex_allocated across all BU decisions Ã· total_revenue
    total_capex = sum(d.get("capex_allocated", 0) for d in decs) if decs else 0
    extra["rd_allocation_pct"] = round(total_capex / max(total_revenue, 1) * 100, 2)
    # Climate resilience factor
    extra["climate_resilience_factor"] = round(gs.get("climate_resilience", 0.5), 2)
    # Talent penalty from software BU (or digital health BU in healthcare mode)
    tech_bu = next((b for b in bus if b["bu_id"] in ("software", "telehealth")), None)
    extra["talent_penalty"] = round(tech_bu.get("talent_penalty", 0), 2) if tech_bu else 0
    extra["group_reputation"] = round(gs.get("group_reputation", 0), 2)
    extra["synergy_multiplier_raw"] = round(gs.get("synergy_multiplier", 1.0), 4)
    extra["vrio_advantage"] = round(gs.get("vrio_advantage", 0), 4)
    extra["green_cost_of_debt_pct"] = round(
        sum(b.get("natural_capital_debt", 0) for b in bus) * 0.05, 2
    )
    # Just Transition pass/fail
    extra["just_transition_passed"] = (
        "just_transition_fund" in all_flags
        or "worker_retraining" in all_flags
        or choice in ("option_a", "option_c")
    )

    # Persist into global state flags for frontend/API access
    gs["active_event_flags"]["terminal_value"]        = terminal_value
    gs["active_event_flags"]["regenerative_multiple"]  = mr
    gs["active_event_flags"]["terminal_ebitda"]        = terminal_ebitda
    gs["active_event_flags"]["profile"]                = profile
    gs["active_event_flags"]["profile_title"]          = profile_title
    gs["active_event_flags"]["archetype"]              = archetype_key
    # P2: immutable canonical R10 completion snapshot (written once). The
    # post-completion Turnaround module reads but never mutates this.
    from engine import record_canonical_completion
    record_canonical_completion(
        gs, terminal_value=terminal_value, regenerative_multiple=mr,
        archetype=archetype_key, profile=profile, profile_title=profile_title,
    )
    gs["active_event_flags"]["profile_description"]    = profile_desc  # AR-D
    # STRAT-010: Equity bridge fields for leaderboard / frontend
    gs["active_event_flags"]["equity_value"]           = equity_value
    gs["active_event_flags"]["price_per_share"]        = price_per_share
    gs["active_event_flags"]["equity_wiped_out"]       = equity_wiped_out
    gs["active_event_flags"]["net_debt"]               = net_debt
    gs["active_event_flags"]["exit_multiple_applied"]  = effective_exit_multiple
    gs["active_event_flags"]["exit_multiple_wacc_used"]= round(wacc_value, 4)
    gs["active_event_flags"]["ev_over_revenue"]        = equity_bridge.get("ev_over_revenue")
    gs["active_event_flags"]["price_to_book"]          = equity_bridge.get("price_to_book")
    gs["active_event_flags"]["ev_revenue_signal"]      = equity_bridge.get("ev_revenue_signal")
    gs["active_event_flags"]["pb_signal"]              = equity_bridge.get("pb_signal")

    # ── ITEM 8: Pathway Discovery Debrief ─────────────────────
    # Reveal the full foreshadowing chain and active ending pathway
    try:
        ending_pathway = prev_flags.get("ending_pathway", "activist_ultimatum")
        from ending_pathways import get_foreshadowing_events, PATHWAY_DESCRIPTIONS
        discovery_chain = []
        for r in range(5, 9):
            items = get_foreshadowing_events(ending_pathway, r)
            if items:
                for item in items:
                    discovery_chain.append({
                        "round": r,
                        "headline": item.get("headline", item.get("title", "")),
                        "detail": item.get("body", item.get("narrative", "")),
                        "flag": item.get("flag", ""),
                    })
        pathway_desc = PATHWAY_DESCRIPTIONS.get(ending_pathway, {})
        extra["pathway_discovery"] = {
            "pathway_id": ending_pathway,
            "pathway_name": pathway_desc.get("name", ending_pathway),
            "pathway_description": pathway_desc.get("description", ""),
            "foreshadowing_chain": discovery_chain,
            "foreshadowing_count": len(discovery_chain),
            "pedagogical_note": (
                f"This ending was determined by the '{ending_pathway}' pathway. "
                f"The {len(discovery_chain)} foreshadowing events above were "
                f"seeded in Rounds 5-8 as indirect signals. The pedagogical "
                f"goal is pattern recognition: could you have predicted this "
                f"outcome from the signals?"
            ),
        }
    except Exception as exc:
        extra["pathway_discovery_error"] = str(exc)



def _revert_r5_hard_engineering_pulse(
    gs: dict, bus: list[dict], extra: dict, round_number: int
) -> None:
    """
    I7 — Reverse the +3 CI pulse from R5 Hard Engineering Defence after 2 rounds.
    Hard engineering (concrete/steel) causes a construction-phase CI increase
    that should revert once the infrastructure is complete.
    Triggers in R7 if hard_engineering flag is active and pulse not yet reverted.
    """
    flags = gs.get("active_event_flags", {})
    if round_number == 7 and flags.get("hard_engineering") and not flags.get("hard_engineering_pulse_reverted"):
        revert_delta = -3.0  # Reverse the +3 from R5
        for bu in bus:
            bu["carbon_intensity"] = max(0.0, round(bu.get("carbon_intensity", 0) + revert_delta, 2))
        extra["hard_engineering_pulse_reverted"] = True
        extra["hard_engineering_ci_reversal"] = revert_delta
        extra["hard_engineering_ci_reversal_message"] = (
            "R5 Hard Engineering construction pulse (+3 CI) reversed in R7: "
            "infrastructure complete, operational CI normalised (I7 time-bounded pulse)."
        )


# ── R2: Double Materiality reconciliation ────────────────────────────────────────────
def _post_r2_materiality(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    """
    F-1 structural fix. The Double Materiality matrix is a MID-round panel:
    router.submit_materiality_matrix scores it and persists the result the
    moment the player submits. The A/B/C governance choice only exists at
    end-of-round commit, through the ordinary decision path. This handler is
    the single point in the round where BOTH inputs exist, so it is the single
    arbiter for:

      1. the materiality tier flag — exactly ONE of materiality_aligned (+0.10
         M_R), materiality_partial (+0.05), materiality_ignored (0). No other
         code path may write these three flags (see test_r2_flag_tiering).
      2. the Option C clawback — 40% of the RELEASED materiality fund. It
         reduces the restricted fund first and charges any remainder to
         treasury, so it always reduces the team's position (F-3 fixed the
         previous inversion, where the clawback handed cash back).
      3. the governance_board assurance signal and the student-facing
         r2_esrs_debrief, both provisional at panel-submit time.

    Matrix results are read from the persisted panel state: both database
    backends pack extra global_state keys into active_event_flags, so they
    arrive here through prev_flags (or through gs when already unpacked).
    """
    def _panel(key, default=None):
        if key in events:
            return events[key]
        if key in gs:
            return gs[key]
        return prev_flags.get(key, default)

    choice = _get_primary_choice(decs)
    gs["r2_governance_choice"] = choice

    submitted = bool(_panel("csrd_completed", False))
    try:
        accuracy_pct = float(_panel("materiality_full_accuracy", 0.0) or 0.0)
    except (TypeError, ValueError):
        accuracy_pct = 0.0
    acc_ok = submitted and accuracy_pct >= 80.0

    # 1) ── Tier flag (§4.1) — accuracy and governance are separate obligations
    if choice == "option_c":
        tier = "materiality_ignored"    # governance breach voids any premium
    elif acc_ok and choice == "option_a":
        tier = "materiality_aligned"    # analysis right AND approved right
    elif acc_ok and choice == "option_b":
        tier = "materiality_partial"    # analysis right, governance partial
    else:
        tier = "materiality_ignored"    # accuracy < 80%
    flags = gs.setdefault("active_event_flags", {})
    for f in ("materiality_aligned", "materiality_partial", "materiality_ignored"):
        # Explicit False, never pop: commit-time flag merging is
        # current ∪ new ∪ events, so only an overwrite retires a stale value.
        flags[f] = (f == tier)
    gs["materiality_status"] = {
        "materiality_aligned": "aligned",
        "materiality_partial": "partial",
        "materiality_ignored": "ignored",
    }[tier]
    extra["r2_materiality_tier"] = tier
    extra["r2_materiality_tier_message"] = {
        "materiality_aligned": (
            "\U0001f4ca CSRD Governance Premium secured: \u226580% matrix accuracy under full "
            "board-committee oversight (Option A). materiality_aligned \u2192 +0.10 M_R at terminal valuation."
        ),
        "materiality_partial": (
            "\U0001f4ca Partial governance credit: \u226580% matrix accuracy, but Strategic Exceptions "
            "(Option B) weakened the governance posture. materiality_partial \u2192 +0.05 M_R at terminal valuation."
        ),
        "materiality_ignored": (
            "\u26a0\ufe0f No governance premium: "
            + ("Option C breaches ESRS 1 \u00a71.51 board oversight \u2014 accurate analysis cannot excuse "
               "approving it badly." if choice == "option_c"
               else "matrix accuracy below the 80% threshold.")
        ),
    }[tier]

    # 2) ── Option C clawback — always reduces the team's position ─────────
    if choice == "option_c":
        cfg_opts = _fetch_options_for_industry(2, bus)
        pct = float(cfg_opts.get("option_c", {}).get("budget_clawback_pct", 0.40))
        released = float(_panel("materiality_fund_released", 0.0) or 0.0)
        clawback = round(released * pct, 2)
        if clawback > 0:
            fund = float(_panel("materiality_restricted_fund", 0.0) or 0.0)
            taken = min(clawback, fund)
            gs["materiality_restricted_fund"] = round(fund - taken, 2)
            shortfall = round(clawback - taken, 2)
            if shortfall > 0:
                gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0.0) - shortfall, 2)
            gs["r2_budget_clawback"] = clawback
            extra["r2_budget_clawback"] = clawback
            extra["r2_budget_clawback_message"] = (
                f"\u26a0\ufe0f CFO Governance Review: Option C (CEO-only sign-off) triggered a "
                f"${clawback:,.0f} ({int(pct * 100)}%) clawback on your released materiality fund"
                + (f", ${shortfall:,.0f} of it charged directly to treasury" if shortfall > 0 else "")
                + ". Governance posture must be consistent with capital allocation rationale."
            )

    # 3) ── Assurance signal + debrief reconciliation ────────────────────
    debrief = _panel("r2_esrs_debrief", None)
    if isinstance(debrief, dict):
        from round2_csrd import ASSURANCE_LABELS
        debrief = dict(debrief)  # never mutate the idempotency snapshot in place
        signals = dict(debrief.get("assurance_signals") or {})
        signals["governance_board"] = (choice != "option_c")  # ESRS 1 §1.51
        stars = sum(1 for v in signals.values() if v)
        label, detail = ASSURANCE_LABELS.get(stars, ASSURANCE_LABELS[0])
        debrief.update({
            "assurance_signals": signals,
            "assurance_stars":   stars,
            "assurance_label":   label,
            "assurance_detail":  detail,
            "governance_choice": choice,
            "materiality_tier":  tier,
            "tier_message":      extra["r2_materiality_tier_message"],
        })
        if "r2_budget_clawback" in extra:
            debrief["clawback_applied"] = extra["r2_budget_clawback"]
        gs["r2_esrs_debrief"] = debrief


_POST_TICK_MAP = {
    1: _post_r1_foundations,
    2: _post_r2_materiality,
    3: _post_r3_scope3,
    4: _post_r4_contagion,   # Fix #2: R4 now has a registered post-tick handler
    5: _ie._post_r5_climate,       # ARCH-001: Extracted to impact_engine.py
    6: _post_r6_ai_bias,
    7: _post_r7_circularity,
    8: _post_r8_blue_stress,
    9: _ie._post_r9_just_transition,  # ARCH-001: Extracted to impact_engine.py
    10: _post_r10_grand_finale,
}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  HELPERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _get_primary_choice(decisions: list[dict]) -> str:
    """
    Extract the primary strategic choice from decisions.
    Looks for the choice_selected field (e.g. 'option_a').
    Falls back to 'option_b' if not set.
    """
    for dec in decisions:
        choice = dec.get("choice_selected", "")
        if choice.startswith("option_"):
            return choice
    return "option_b"  # default middle-ground


def _find_dual_form_flags(flags_dict: dict) -> set[str]:
    """
    F-2 guard. A flag that appears BOTH as a boolean key and inside an
    rN_flags-style list is unretirable: _collect_all_flags unions the two
    sources with no precedence, so a config flags_set silently outranks any
    later boolean removal (this is exactly how Option A at 40% accuracy kept
    the governance premium). Returns the offending flag names; empty = healthy.
    """
    bool_keys = {
        k for k, v in flags_dict.items()
        if isinstance(k, str) and isinstance(v, bool) and v
    }
    list_flags: set[str] = set()
    for k, v in flags_dict.items():
        if isinstance(k, str) and "flag" in k.lower() and isinstance(v, list):
            list_flags.update(str(x) for x in v)
    return bool_keys & list_flags


def _collect_all_flags(flags_dict: dict) -> set[str]:
    """
    FIX AUDIT-008: Collect boolean keys and specific flag lists (e.g., rX_flags),
    rather than recursively slurping every string value in the event dictionary.
    """
    result = set()
    for key, val in flags_dict.items():
        if not isinstance(key, str):
            continue  # Skip non-string keys (e.g. SDG integer indices)
        if "flag" in key.lower():
            if isinstance(val, list):
                result.update(str(v) for v in val)
            elif isinstance(val, str):
                result.add(val)
        elif isinstance(val, bool) and val:
            # Explicit boolean states are valid flags (e.g. cfo_override_used: True)
            result.add(key)
        elif isinstance(val, dict):
            # Recurse to find nested booleans or flag lists
            result.update(_collect_all_flags(val))
            
    # Fallback to check specific critical string keys if they weren't matched
    for flag_key in [
        "electronics_blindspot", "deep_audit_completed",
        "electronics_blindspot_triggered", "deep_audit_protected",
    ]:
        if flag_key in flags_dict:
            result.add(flag_key)
    return result


def _apply_option_flags(
    round_number: int,
    decisions: list[dict],
    global_state: dict,
    extra_events: dict,
    bus: list[dict] = None,
    decision_paradigm: str | None = None,
):
    """
    Persist the flags_set from the chosen option into the
    active_event_flags on the global state.
    """
    choice = _get_primary_choice(decisions)
    cfg_opts = _fetch_options_for_industry(round_number, bus or [], decision_paradigm=decision_paradigm)
    opt = cfg_opts.get(choice, {})
    flags = opt.get("flags_set", [])

    if flags:
        flag_key = f"r{round_number}_flags"
        global_state.setdefault("active_event_flags", {})
        global_state["active_event_flags"][flag_key] = flags
        extra_events[f"flags_set_r{round_number}"] = flags


# ═════════════════════════════════════════════════════════════════
#  ARCH-001: Late-bind impact_engine dependencies
#  Must run after all helper functions are defined.
# ═════════════════════════════════════════════════════════════════
_ie._inject_dependencies(_get_primary_choice, _fetch_options_for_industry, _apply_treasury_with_green_fund)
