"""
Muressons Global Command â€” Round-Specific State Mutation Logic
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
    else:
        result["crisis_severity"] = base
        result["pre_events"]["deep_audit_protected"] = True


_PRE_TICK_MAP = {
    2: _pre_r2_materiality_gate,
    4: _pre_r4_contagion,
}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  POST-TICK HOOKS
#  Run AFTER the generic engine.  Mutate the already-computed
#  next-round state in place.
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def post_tick(
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    decisions: list[dict],
    events: dict,
    previous_flags: dict,
) -> dict[str, Any]:
    """
    Applies round-specific state mutations after the engine tick.
    Mutates global_state / bu_states in place.
    Returns extra events to merge.
    """
    extra_events: dict[str, Any] = {}

    # FIX AUDIT-014: Apply the CFO override reputation penalty here
    # rather than mutating the input state directly in pre_tick.
    if events.get("cfo_override_used"):
        global_state["group_reputation"] = max(0.0, global_state.get("group_reputation", 50.0) - 5.0)
    handler = _POST_TICK_MAP.get(round_number)
    if handler:
        handler(global_state, bu_states, decisions, events, extra_events, previous_flags)

    # Apply generic impacts (carbon_intensity_delta, revenue_delta) for ALL rounds
    _apply_common_impacts(round_number, global_state, bu_states, decisions, extra_events)

    # Persist new flags from chosen option into active_event_flags
    _apply_option_flags(round_number, decisions, global_state, extra_events, bus=bu_states)

    return extra_events


from healthcare_configs import get_healthcare_round_options


def _fetch_options_for_industry(round_number: int, bus: list[dict]) -> dict:
    if any(b["bu_id"] == "hospitals" for b in bus):
        return get_healthcare_round_options(round_number)
    return get_round_options(round_number)

def _apply_common_impacts(
    round_number: int,
    gs: dict,
    bus: list[dict],
    decisions: list[dict],
    extra: dict,
):
    """
    Generic applicator for carbon_intensity_delta and revenue_delta.
    Runs for EVERY round after the round-specific handler.
    Skips if the round-specific handler already applied these (R3 carbon).
    """
    choice = _get_primary_choice(decisions)
    cfg_opts = _fetch_options_for_industry(round_number, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Carbon intensity delta â€” applied to all BUs
    ci_delta = impacts.get("carbon_intensity_delta", 0)
    if ci_delta != 0 and f"carbon_intensity_applied_r{round_number}" not in extra:
        for bu in bus:
            old_ci = bu.get("carbon_intensity", 0)
            bu["carbon_intensity"] = max(0, round(old_ci + ci_delta, 2))
        extra[f"carbon_intensity_applied_r{round_number}"] = ci_delta

    # Revenue delta â€” applied to all BUs equally
    rev_delta = impacts.get("revenue_delta", 0)
    if rev_delta != 0:
        for bu in bus:
            old_rev = bu.get("revenue_base", 0)
            bu["revenue_base"] = max(0, round(old_rev + rev_delta, 2))
        extra[f"revenue_delta_applied_r{round_number}"] = rev_delta

    # NCD application is handled individually in each round's post handler
    # because some rounds (like R5 and R8) queue it as a pending capex project instead of applying immediately.

    # â”€â”€ Healthcare Specific Impacts â”€â”€
    if impacts.get("bed_capacity_increase"):
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["bed_capacity_utilization"] = max(0.0, b.get("bed_capacity_utilization", 0.0) - impacts["bed_capacity_increase"])
                
    if impacts.get("burnout_spike"):
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["staff_burnout_index"] = min(100.0, b.get("staff_burnout_index", 0.0) + 25.0)
                
    if impacts.get("burnout_recovery"):
        for b in bus:
            if b["bu_id"] in ("hospitals", "clinics"):
                b["staff_burnout_index"] = max(0.0, b.get("staff_burnout_index", 0.0) - 30.0)
                
    if impacts.get("telehealth_opex_delta"):
        for b in bus:
            if b["bu_id"] == "telehealth":
                b["opex_base"] = round(b["opex_base"] + impacts["telehealth_opex_delta"], 2)
                
    if impacts.get("opex_penalty"):
        for b in bus:
            b["opex_base"] = round(b["opex_base"] + (impacts["opex_penalty"] / len(bus)), 2)

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


# â”€â”€ R1: Set foundation flags â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r1_foundations(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    """Apply reputation impacts from R1 option choice."""
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(1, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)
    if "reputation" in impacts:
        gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))

    extra["r1_choice"] = choice
    extra["r1_flags_set"] = opt.get("flags_set", [])


# â”€â”€ R3: Scope 3 mutations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r3_scope3(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(3, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Treasury
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Natural Capital Debt delta (applied to all BUs equally)
    ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    if ncd_delta != 0:
        for bu in bus:
            bu["natural_capital_debt"] = max(0, round(bu["natural_capital_debt"] + ncd_delta, 2))

    # Carbon intensity delta
    ci_delta = impacts.get("carbon_intensity_delta", 0)
    if ci_delta != 0:
        for bu in bus:
            bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))
        extra["carbon_intensity_applied_r3"] = ci_delta  # prevent generic applicator double-apply

    # Option A: supply chain disruption risk â†’ increase governance risk
    if impacts.get("supply_chain_disruption"):
        for bu in bus:
            if bu["bu_id"] in ("electronics", "pharma"):
                bu["governance_risk_score"] = min(100, bu["governance_risk_score"] + 10)
        extra["supply_chain_disruption_applied"] = True

    # UN SDG: Option A (Compulsory Schooling) â†’ create education_lag pending project
    # Education investments yield 0% impact for 3 rounds, then +0.8 multiplier for SDG 8
    if choice == "option_a" and any(bu.get("basic_needs") is not None for bu in bus):
        if "pending_capex_projects" not in gs:
            gs["pending_capex_projects"] = []
        gs["pending_capex_projects"].append({
            "type": "education_lag",
            "rounds_remaining": 3,
            "amount": 0.8,
            "description": "Education Investment Maturing (SDG 4 â†’ SDG 8)"
        })
        extra["education_lag_project_started"] = True

    # Reputation impact
    if "reputation" in impacts:
        gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))

    extra["r3_choice"] = choice


# â”€â”€ R5: Stochastic Climate Event â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r5_climate(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(5, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    from healthcare_configs import get_healthcare_round_config
    if any(b["bu_id"] == "hospitals" for b in bus):
        cfg = get_healthcare_round_config(5)
    else:
        cfg = get_round_config(5)
    special = cfg.get("special_rules", {}) if cfg else {}
    base_damage = special.get("base_damage", 12_000_000)
    threshold = special.get("stochastic_threshold", 0.75)

    resilience_factor = impacts.get("resilience_factor", 0.0)

    # Stochastic dice roll
    roll = round(random.random(), 4)
    extra["stochastic_roll"] = roll
    extra["stochastic_threshold"] = threshold

    # Check for active resilience factor stored by completed pending projects
    active_resilience_factor = events.get("active_resilience_factor", 0.0)
    
    # FIX AUDIT-009 was reverted: Hard Engineering is a delayed capex, so its
    # resilience_factor does NOT apply immediately. Only previously completed 
    # projects provide protection.
    effective_resilience = active_resilience_factor

    if roll < threshold:
        # Event strikes â€” apply damage mitigated by resilience
        actual_damage = round(base_damage * (1 - effective_resilience), 2)

        # UN SDG: Carbon Retribution Hook â€” triples damage if global emissions
        # exceeded threshold by Round 5
        carbon_retribution = events.get("carbon_retribution_multiplier", 1.0)
        if carbon_retribution > 1.0:
            actual_damage = round(actual_damage * carbon_retribution, 2)
            extra["carbon_retribution_applied"] = True
            extra["carbon_retribution_multiplier"] = carbon_retribution

        gs["corporate_treasury"] = round(gs["corporate_treasury"] - actual_damage, 2)
        extra["climate_event_struck"] = True
        extra["base_damage"] = base_damage
        extra["resilience_factor"] = effective_resilience
        extra["actual_damage"] = actual_damage
    else:
        extra["climate_event_struck"] = False
        extra["climate_event_message"] = "The cyclone changed course. No damage."

    # Treasury cost of the option itself
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Advanced Climate Engine: Delay CapEx yields for Hard Engineering projects
    ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    
    if resilience_factor > 0 or ncd_delta != 0:
        if "pending_capex_projects" not in gs:
            gs["pending_capex_projects"] = []
            
        if resilience_factor > 0:
            gs["pending_capex_projects"].append({
                "type": "resilience_boost",
                "amount": resilience_factor,
                "rounds_remaining": 2,
                "description": "Building Coastal Resilience Infrastructure"
            })
            extra["resilience_project_started"] = True
            
        if ncd_delta != 0:
            gs["pending_capex_projects"].append({
                "type": "ncd_drop",
                "amount": ncd_delta,
                "bu_target": "all",
                "rounds_remaining": 2,
                "description": "Hard Engineering Impact Adjustments"
            })
            extra["ncd_project_started"] = True

    extra["r5_choice"] = choice


# â”€â”€ R6: AI Bias â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r6_ai_bias(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(6, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Option A: +$5M revenue to Software but -20 reputation (contagion spike)
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

    # Option B: treasury cost + social license boost
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    sl_delta = impacts.get("social_license_delta", 0)
    if sl_delta != 0:
        for bu in bus:
            bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))
        extra["social_license_boosted"] = sl_delta

    # Option C: governance risk increase
    gov_delta = impacts.get("governance_risk_delta", 0)
    if gov_delta != 0:
        for bu in bus:
            bu["governance_risk_score"] = max(0, min(100, round(bu["governance_risk_score"] + gov_delta, 2)))

    extra["r6_choice"] = choice


# â”€â”€ R7: Circularity â€” Option C unlocks synergy multiplier â”€â”€â”€â”€â”€â”€â”€
def _post_r7_circularity(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
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

    # Option C: Synergy multiplier boost
    syn_boost = impacts.get("synergy_multiplier_boost", 0)
    if syn_boost > 0:
        gs["synergy_multiplier"] = round(gs["synergy_multiplier"] + syn_boost, 4)
        extra["synergy_multiplier_unlocked"] = True
        extra["synergy_boost_amount"] = syn_boost

    extra["r7_choice"] = choice


# â”€â”€ R8: Blue Stress â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r8_blue_stress(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(8, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # UN SDG: Blockchain Traceability (R3 Option C) prevents Scandal Shock
    all_flags = _collect_all_flags(prev_flags)
    if "blockchain_traceability" in all_flags:
        # Traceability verified â€” no scandal, governance bonus
        extra["scandal_shock_prevented"] = True
        extra["blockchain_traceability_dividend"] = True
        gs["group_reputation"] = min(100, round(
            gs.get("group_reputation", 50) + 5, 2
        ))
        # Skip the negative governance/reputation impacts of the strike
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

    # Option B: severe social licence drop on specific BUs
    if impacts.get("social_license_severe_drop"):
        targets = impacts.get("social_license_drop_targets", [])
        drop_amt = impacts.get("social_license_drop_amount", -25)
        for bu in bus:
            if bu["bu_id"] in targets:
                bu["social_license_score"] = max(0, round(bu["social_license_score"] + drop_amt, 2))
        extra["social_license_severe_drop_applied"] = targets

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

    # Social licence boost (Option A)
    sl_delta = impacts.get("social_license_delta", 0)
    if sl_delta != 0:
        for bu in bus:
            bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))

    extra["r8_choice"] = choice


# â”€â”€ R9: Just Transition â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _post_r9_just_transition(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = _fetch_options_for_industry(9, bus)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Treasury (allow positive impacts to go straight to treasury)
    if "treasury" in impacts:
        if impacts["treasury"] < 0:
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
            gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Reputation & Social License deltas
    rep_delta = impacts.get("reputation_delta", 0)
    if rep_delta != 0:
        gs["group_reputation"] = max(0, min(100, round(gs["group_reputation"] + rep_delta, 2)))

    sl_delta = impacts.get("social_license_delta", 0)
    if sl_delta != 0:
        for bu in bus:
            bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))

    gov_delta = impacts.get("governance_risk_delta", 0)
    if gov_delta != 0:
        for bu in bus:
            bu["governance_risk_score"] = max(0, min(100, round(bu["governance_risk_score"] + gov_delta, 2)))

    # Option A: Strike risk â€” if Social License is low
    if impacts.get("strike_risk"):
        avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 50
        strike_threshold = 50  # "low" social license

        # Calculate Regulatory Friction = 1 / SLO_m (avg social license)
        regulatory_friction = round(1.0 / max(1.0, avg_sl), 4)
        extra["regulatory_friction"] = regulatory_friction

        if avg_sl < strike_threshold:
            # Roll against 75% strike probability
            roll = round(random.random(), 4)
            extra["strike_roll"] = roll
            extra["strike_probability"] = 0.75

            if roll < 0.75:
                # FIX AUDIT-003: Strike hits â€” apply as a treasury deduction
                # rather than zeroing revenue_base, which would permanently
                # corrupt R10's starting state.
                revenue_lost = sum(bu.get("revenue_base", 0) for bu in bus)
                gs["corporate_treasury"] = round(
                    gs["corporate_treasury"] - revenue_lost, 2
                )
                extra["strike_triggered"] = True
                extra["strike_revenue_lost"] = revenue_lost
                extra["strike_message"] = (
                    "Workers have gone on strike! All BU revenue for this "
                    f"round has been lost (âˆ’${revenue_lost:,.0f} from treasury)."
                )
                extra["revenue_zeroed"] = True
            else:
                extra["strike_triggered"] = False
                extra["strike_message"] = "Strike narrowly averted through last-minute negotiations."
        else:
            extra["strike_triggered"] = False
            extra["strike_message"] = "Social licence sufficient â€” no strike risk."

    extra["r9_choice"] = choice


# â”€â”€ R10: Grand Finale â€” Terminal EBITDA, MR, Terminal Valuation â”€â”€â”€â”€
def _post_r10_grand_finale(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    # FIX: Use industry-aware config so healthcare sessions get the correct R10 options.
    is_healthcare = any(b["bu_id"] == "hospitals" for b in bus)



    if is_healthcare:
        from healthcare_configs import get_healthcare_round_config, get_healthcare_round_options
        cfg = get_healthcare_round_config(10)
        cfg_opts = get_healthcare_round_options(10)
    else:
        cfg = get_round_config(10)
        cfg_opts = get_round_options(10)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})
    special = cfg.get("special_rules", {}) if cfg else {}
    all_flags = _collect_all_flags(prev_flags)

    carbon_tax_per_ton = special.get("carbon_tax_per_ton", 250)
    exit_multiple = special.get("exit_multiple", 12.0)

    # â”€â”€ Check for God Mode carbon tax override â”€â”€
    if prev_flags.get("carbon_tax_override_active"):
        carbon_tax_per_ton = prev_flags.get("carbon_tax_per_ton", carbon_tax_per_ton)

    # â”€â”€ Apply Activist Ultimatum choice effects first â”€â”€
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Option A: Resist & Integrate â€” validate synergy gate
    synergy_gate = special.get("synergy_gate_threshold", 80)
    synergy_score = gs.get("synergy_multiplier", 1.0) * 100  # normalise
    if choice == "option_a":
        if synergy_score <= synergy_gate:
            # Should have been blocked by frontend; force fallback to B
            extra["synergy_gate_blocked"] = True
            extra["synergy_gate_message"] = (
                f"Resist & Integrate blocked: Synergy Score "
                f"{synergy_score:.0f} â‰¤ {synergy_gate}. Defaulting to Spin-off."
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

    # Option C: Divest â€” wipe synergy
    if impacts.get("synergy_wipe"):
        gs["synergy_multiplier"] = 1.0
        extra["synergy_wiped"] = True

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

    # +0.3: R7 Synergy achieved (waste_to_energy / synergy_unlock)
    if "synergy_unlock" in all_flags or "waste_to_energy" in all_flags:
        mr += 0.3
        extra["mr_synergy_bonus"] = True

    # +0.2: Survived R5/R8 without bailout
    r5_bailout = "insurance_only" in all_flags
    r8_bailout = "electronics_water_priority" in all_flags
    if not r5_bailout and not r8_bailout:
        mr += 0.2
        extra["mr_resilience_bonus"] = True

    # +0.15: Truth Premium from R6 (chose ethical AI overhaul)
    if "ethical_ai_overhaul" in all_flags:
        mr += 0.15
        extra["mr_truth_premium"] = True

    # âˆ’0.4: Instability Discount if avg Social License < 75
    avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 0
    if avg_sl < 75:
        mr -= 0.4
        extra["mr_instability_discount"] = True
        extra["mr_instability_avg_sl"] = round(avg_sl, 2)

    mr = round(mr, 4)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  TERMINAL VALUE  =  Terminal_EBITDA  Ã—  Exit Multiple  Ã—  M_R
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    terminal_value = round(terminal_ebitda * exit_multiple * mr, 2)

    # ===================================================
    #  Year 3 PROFILE ARCHETYPE
    #  Custom archetypes from god-mode take priority
    # ===================================================
    try:
        from admin_router import _god_mode_settings
        custom_archetypes = _god_mode_settings.get("custom_archetypes", [])
    except ImportError:
        custom_archetypes = []

    profile_icon = None
    profile_gradient = None

    if custom_archetypes:
        sorted_customs = sorted(custom_archetypes, key=lambda a: a.get("mr_threshold", 0), reverse=True)
        matched = next((a for a in sorted_customs if mr >= a.get("mr_threshold", 0)), None)
        if not matched:
            matched = sorted_customs[-1]
        profile = matched["key"]
        profile_title = matched["title"]
        profile_desc = matched.get("description", "")
        profile_icon = matched.get("icon", "\U0001f3c5")
        profile_gradient = matched.get("gradient", "linear-gradient(135deg, #6366f1, #8b5cf6)")
    else:
        thresholds = special.get("profile_thresholds", {})
        if mr >= thresholds.get("regenerative_titan", 1.8):
            profile = "regenerative_titan"
            profile_title = "The Regenerative Titan"
            profile_desc = (
                "A truly regenerative enterprise. Muressons has rebuilt "
                "natural capital, earned deep social trust, and delivered "
                "superior financial returns. This is the gold standard of Year 3."
            )
            profile_icon = "\U0001f331"
            profile_gradient = "linear-gradient(135deg, #10b981, #059669)"
        elif mr >= thresholds.get("derisked_safe_haven", 1.2):
            profile = "derisked_safe_haven"
            profile_title = "The De-risked Safe-Haven"
            profile_desc = (
                "A resilient corporation that avoided the worst tail risks. "
                "Investors value the predictability, but innovation is stalling. "
                "Solid, but not transformational."
            )
            profile_icon = "\U0001f3e6"
            profile_gradient = "linear-gradient(135deg, #3b82f6, #1d4ed8)"
        elif mr >= thresholds.get("fragile_giant", 0.8):
            profile = "fragile_giant"
            profile_title = "The Fragile Giant"
            profile_desc = (
                "Big but brittle. The cracks in social license and natural "
                "capital are visible. One more shock could trigger a cascade "
                "of write-downs and stakeholder defections."
            )
            profile_icon = "\u26a0\ufe0f"
            profile_gradient = "linear-gradient(135deg, #f59e0b, #d97706)"
        else:
            profile = "stranded_relic"
            profile_title = "The Stranded Relic"
            profile_desc = (
                "A cautionary tale. Stranded assets, depleted social capital, "
                "and a brand synonymous with extraction. The Year 3 market has "
                "moved on. Terminal decline is imminent."
            )
            profile_icon = "\U0001f480"
            profile_gradient = "linear-gradient(135deg, #ef4444, #b91c1c)"
    # Populate Extra & Global State
    extra["terminal_ebitda"] = terminal_ebitda
    extra["carbon_tonnage_group"] = carbon_tonnage_group
    extra["carbon_cost"] = carbon_cost
    extra["carbon_tax_per_ton"] = carbon_tax_per_ton
    extra["regenerative_multiple"] = mr
    extra["mr_breakdown"] = {
        "base": 1.0,
        "synergy_bonus": 0.3 if extra.get("mr_synergy_bonus") else 0,
        "resilience_bonus": 0.2 if extra.get("mr_resilience_bonus") else 0,
        "truth_premium": 0.15 if extra.get("mr_truth_premium") else 0,
        "instability_discount": -0.4 if extra.get("mr_instability_discount") else 0,
    }
    extra["terminal_value"] = terminal_value
    extra["exit_multiple"] = exit_multiple
    extra["final_treasury"] = gs["corporate_treasury"]
    extra["profile"] = profile
    extra["profile_title"] = profile_title
    extra["profile_description"] = profile_desc
    extra["profile_icon"] = profile_icon
    extra["profile_gradient"] = profile_gradient
    extra["synergy_score"] = round(synergy_score, 2)
    extra["avg_social_license"] = round(avg_sl, 2)
    extra["r10_choice"] = choice

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
    gs["active_event_flags"]["terminal_value"] = terminal_value
    gs["active_event_flags"]["regenerative_multiple"] = mr
    gs["active_event_flags"]["terminal_ebitda"] = terminal_ebitda
    gs["active_event_flags"]["profile"] = profile
    gs["active_event_flags"]["profile_title"] = profile_title


_POST_TICK_MAP = {
    1: _post_r1_foundations,
    3: _post_r3_scope3,
    5: _post_r5_climate,
    6: _post_r6_ai_bias,
    7: _post_r7_circularity,
    8: _post_r8_blue_stress,
    9: _post_r9_just_transition,
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


def _collect_all_flags(flags_dict: dict) -> set[str]:
    """
    FIX AUDIT-008: Collect boolean keys and specific flag lists (e.g., rX_flags),
    rather than recursively slurping every string value in the event dictionary.
    """
    result = set()
    for key, val in flags_dict.items():
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
):
    """
    Persist the flags_set from the chosen option into the
    active_event_flags on the global state.
    """
    choice = _get_primary_choice(decisions)
    cfg_opts = _fetch_options_for_industry(round_number, bus or [])
    opt = cfg_opts.get(choice, {})
    flags = opt.get("flags_set", [])

    if flags:
        flag_key = f"r{round_number}_flags"
        global_state.setdefault("active_event_flags", {})
        global_state["active_event_flags"][flag_key] = flags
        extra_events[f"flags_set_r{round_number}"] = flags
