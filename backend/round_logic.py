"""
Muressons Global Command — Round-Specific State Mutation Logic
Dispatches to per-round handlers that apply conditional mutations
BEFORE and AFTER the generic tick engine runs.

Architecture:
  1. pre_tick(round, state, decisions)  → validates, modifies crisis_severity
  2. engine.process_tick()              → runs the 8 generic formulas
  3. post_tick(round, state, decisions) → applies round-specific mutations
"""

from __future__ import annotations
import random
from typing import Any

from round_configs import get_round_config, get_round_options


# ═════════════════════════════════════════════════════════════════
#  PRE-TICK HOOKS
#  Run BEFORE the generic engine.  Can modify crisis_severity,
#  reject invalid inputs (raise ValueError), or set flags.
# ═════════════════════════════════════════════════════════════════

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
      - "crisis_severity"  → overridden value
      - "validation_error" → string message (will become 400)
      - "pre_events"       → dict of events to merge
    """
    result: dict[str, Any] = {"crisis_severity": crisis_severity, "pre_events": {}}
    handler = _PRE_TICK_MAP.get(round_number)
    if handler:
        if round_number == 2:
            handler(result, current_global, current_bus, decisions, force_override_cfo=force_override_cfo)
        else:
            handler(result, current_global, current_bus, decisions)
    return result


# ── R2: CFO Materiality Gate ─────────────────────────────────────
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

    high_impact_nodes = set(rules.get("high_impact_nodes", []))

    for dec in decisions:
        capex = dec.get("capex_allocated", 0)
        node = dec.get("decision_node_id", "")
        if capex > 0 and node and node not in high_impact_nodes:
            if force_override_cfo:
               # Apply executive bypass -> penalize group reputation!
               result["pre_events"]["cfo_override_used"] = True
               current_global["group_reputation"] = max(0, current_global.get("group_reputation", 50) - 5.0)
               return # bypass validation return!
            else:
                result["validation_error"] = (
                    f"CFO Override: Proposed initiative '{node}' lacks material "
                    f"justification. Budget allocation denied per Double "
                    f"Materiality framework."
                )
                return


# ── R4: Electronics Blindspot doubles crisis ─────────────────────
def _pre_r4_contagion(
    result: dict, current_global: dict, current_bus: list[dict], decisions: list[dict]
):
    """If electronics_blindspot flag is active, double crisis severity."""
    flags = current_global.get("active_event_flags", {})
    # Walk history flags — check any flag list that might contain it
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


# ═════════════════════════════════════════════════════════════════
#  POST-TICK HOOKS
#  Run AFTER the generic engine.  Mutate the already-computed
#  next-round state in place.
# ═════════════════════════════════════════════════════════════════

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
    handler = _POST_TICK_MAP.get(round_number)
    if handler:
        handler(global_state, bu_states, decisions, events, extra_events, previous_flags)

    # Apply generic impacts (carbon_intensity_delta, revenue_delta) for ALL rounds
    _apply_common_impacts(round_number, global_state, bu_states, decisions, extra_events)

    # Persist new flags from chosen option into active_event_flags
    _apply_option_flags(round_number, decisions, global_state, extra_events)

    return extra_events


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
    cfg_opts = get_round_options(round_number)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Carbon intensity delta — applied to all BUs
    ci_delta = impacts.get("carbon_intensity_delta", 0)
    if ci_delta != 0 and f"carbon_intensity_applied_r{round_number}" not in extra:
        for bu in bus:
            old_ci = bu.get("carbon_intensity", 0)
            bu["carbon_intensity"] = max(0, round(old_ci + ci_delta, 2))
        extra[f"carbon_intensity_applied_r{round_number}"] = ci_delta

    # Revenue delta — applied to all BUs equally
    rev_delta = impacts.get("revenue_delta", 0)
    if rev_delta != 0:
        for bu in bus:
            old_rev = bu.get("revenue_base", 0)
            bu["revenue_base"] = max(0, round(old_rev + rev_delta, 2))
        extra[f"revenue_delta_applied_r{round_number}"] = rev_delta


# ── R1: Set foundation flags ────────────────────────────────────
def _post_r1_foundations(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    """Apply reputation impacts from R1 option choice."""
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(1)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)
    if "reputation" in impacts:
        gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))

    extra["r1_choice"] = choice
    extra["r1_flags_set"] = opt.get("flags_set", [])


# ── R3: Scope 3 mutations ──────────────────────────────────────
def _post_r3_scope3(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(3)
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

    # Option A: supply chain disruption risk → increase governance risk
    if impacts.get("supply_chain_disruption"):
        for bu in bus:
            if bu["bu_id"] in ("electronics", "pharma"):
                bu["governance_risk_score"] = min(100, bu["governance_risk_score"] + 10)
        extra["supply_chain_disruption_applied"] = True

    # Reputation impact
    if "reputation" in impacts:
        gs["group_reputation"] = max(0, min(100, gs["group_reputation"] + impacts["reputation"]))

    extra["r3_choice"] = choice


# ── R5: Stochastic Climate Event ────────────────────────────────
def _post_r5_climate(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(5)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    cfg = get_round_config(5)
    special = cfg.get("special_rules", {}) if cfg else {}
    base_damage = special.get("base_damage", 12_000_000)
    threshold = special.get("stochastic_threshold", 0.75)

    resilience_factor = impacts.get("resilience_factor", 0.0)

    # Stochastic dice roll
    roll = round(random.random(), 4)
    extra["stochastic_roll"] = roll
    extra["stochastic_threshold"] = threshold

    if roll < threshold:
        # Event strikes — apply damage mitigated by resilience
        actual_damage = round(base_damage * (1 - resilience_factor), 2)
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - actual_damage, 2)
        extra["climate_event_struck"] = True
        extra["base_damage"] = base_damage
        extra["resilience_factor"] = resilience_factor
        extra["actual_damage"] = actual_damage
    else:
        extra["climate_event_struck"] = False
        extra["climate_event_message"] = "The cyclone changed course. No damage."

    # Treasury cost of the option itself
    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Natural capital debt from hard engineering
    ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    if ncd_delta != 0:
        for bu in bus:
            bu["natural_capital_debt"] = max(0, round(bu["natural_capital_debt"] + ncd_delta, 2))

    extra["r5_choice"] = choice


# ── R6: AI Bias ─────────────────────────────────────────────────
def _post_r6_ai_bias(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(6)
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


# ── R7: Circularity — Option C unlocks synergy multiplier ───────
def _post_r7_circularity(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(7)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

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


# ── R8: Blue Stress ─────────────────────────────────────────────
def _post_r8_blue_stress(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(8)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    if "treasury" in impacts:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] + impacts["treasury"], 2)

    # Option B: severe social licence drop on specific BUs
    if impacts.get("social_license_severe_drop"):
        targets = impacts.get("social_license_drop_targets", [])
        drop_amt = impacts.get("social_license_drop_amount", -25)
        for bu in bus:
            if bu["bu_id"] in targets:
                bu["social_license_score"] = max(0, round(bu["social_license_score"] + drop_amt, 2))
        extra["social_license_severe_drop_applied"] = targets

    # Option C: NCD reduction
    ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    if ncd_delta != 0:
        for bu in bus:
            bu["natural_capital_debt"] = max(0, round(bu["natural_capital_debt"] + ncd_delta, 2))

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


# ── R9: Just Transition ─────────────────────────────────────────
def _post_r9_just_transition(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    cfg_opts = get_round_options(9)
    opt = cfg_opts.get(choice, {})
    impacts = opt.get("impacts", {})

    # Treasury
    if "treasury" in impacts:
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

    # Option A: Strike risk — if Social License is low
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
                # Strike hits — zero out revenue for this round
                for bu in bus:
                    bu["revenue_base"] = 0
                extra["strike_triggered"] = True
                extra["strike_message"] = (
                    "Workers have gone on strike! All BU revenue for this "
                    "round has been zeroed out."
                )
                # Recalculate treasury impact
                revenue_lost = sum(
                    bu_orig.get("revenue_base", 0)
                    for bu_orig in bus
                )
                extra["revenue_zeroed"] = True
            else:
                extra["strike_triggered"] = False
                extra["strike_message"] = "Strike narrowly averted through last-minute negotiations."
        else:
            extra["strike_triggered"] = False
            extra["strike_message"] = "Social licence sufficient — no strike risk."

    extra["r9_choice"] = choice


# ── R10: Grand Finale — EBITDA 2050, MR, Terminal Valuation ────
def _post_r10_grand_finale(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
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

    # ═══════════════════════════════════════════════════════════
    #  EBITDA_2050 = Σ(Revenue_i − OPEX_i) − (Carbon_Tonnage × $250/ton)
    # ═══════════════════════════════════════════════════════════
    total_revenue = sum(bu["revenue_base"] for bu in bus)
    total_opex = sum(bu["opex_base"] for bu in bus)

    # Carbon tonnage: sum of carbon_intensity across all BUs (units = abstract tonnes)
    carbon_tonnage_group = sum(bu.get("carbon_intensity", 0) for bu in bus)
    carbon_cost = round(carbon_tonnage_group * carbon_tax_per_ton, 2)

    ebitda_2050 = round(
        (total_revenue - total_opex) - carbon_cost,
        2,
    )

    # ═══════════════════════════════════════════════════════════
    #  REGENERATIVE MULTIPLE (M_R)
    #  Base = 1.0
    #  +0.30  if synergy achieved in R7  (synergy_unlock flag)
    #  +0.20  if survived R5/R8 without bailout
    #  +0.15  Truth Premium from R6 (ethical_ai_overhaul flag)
    #  −0.40  Instability Discount if Social License < 75
    # ═══════════════════════════════════════════════════════════
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

    # −0.4: Instability Discount if avg Social License < 75
    avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 0
    if avg_sl < 75:
        mr -= 0.4
        extra["mr_instability_discount"] = True
        extra["mr_instability_avg_sl"] = round(avg_sl, 2)

    mr = round(mr, 4)

    # ═══════════════════════════════════════════════════════════
    #  TERMINAL VALUE  =  EBITDA_2050  ×  Exit Multiple  ×  M_R
    # ═══════════════════════════════════════════════════════════
    terminal_value = round(ebitda_2050 * exit_multiple * mr, 2)

    # ═══════════════════════════════════════════════════════════
    #  2050 PROFILE ARCHETYPE
    # ═══════════════════════════════════════════════════════════
    thresholds = special.get("profile_thresholds", {})
    if mr >= thresholds.get("regenerative_titan", 1.8):
        profile = "regenerative_titan"
        profile_title = "The Regenerative Titan"
        profile_desc = (
            "A truly regenerative enterprise. Muressons has rebuilt "
            "natural capital, earned deep social trust, and delivered "
            "superior financial returns. This is the gold standard of 2050."
        )
    elif mr >= thresholds.get("derisked_safe_haven", 1.2):
        profile = "derisked_safe_haven"
        profile_title = "The De-risked Safe-Haven"
        profile_desc = (
            "A resilient corporation that avoided the worst tail risks. "
            "Investors value the predictability, but innovation is stalling. "
            "Solid, but not transformational."
        )
    elif mr >= thresholds.get("fragile_giant", 0.8):
        profile = "fragile_giant"
        profile_title = "The Fragile Giant"
        profile_desc = (
            "Big but brittle. The cracks in social license and natural "
            "capital are visible. One more shock could trigger a cascade "
            "of write-downs and stakeholder defections."
        )
    else:
        profile = "stranded_relic"
        profile_title = "The Stranded Relic"
        profile_desc = (
            "A cautionary tale. Stranded assets, depleted social capital, "
            "and a brand synonymous with extraction. The 2050 market has "
            "moved on. Terminal decline is imminent."
        )

    # Populate Extra & Global State
    extra["ebitda_2050"] = ebitda_2050
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
    extra["synergy_score"] = round(synergy_score, 2)
    extra["avg_social_license"] = round(avg_sl, 2)
    extra["r10_choice"] = choice

    # Additional KPIs for the TBL-BSC 4×3 Grid
    extra["total_revenue"] = total_revenue
    extra["total_opex"] = total_opex
    extra["instability_discount_applied"] = bool(extra.get("mr_instability_discount"))
    # R&D allocation: sum capex_allocated across all BU decisions ÷ total_revenue
    total_capex = sum(d.get("capex_allocated", 0) for d in decs) if decs else 0
    extra["rd_allocation_pct"] = round(total_capex / max(total_revenue, 1) * 100, 2)
    # Climate resilience factor
    extra["climate_resilience_factor"] = round(gs.get("climate_resilience", 0.5), 2)
    # Talent penalty from software BU
    sw_bu = next((b for b in bus if b["bu_id"] == "software"), None)
    extra["talent_penalty"] = round(sw_bu.get("talent_penalty", 0), 2) if sw_bu else 0
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
    gs["active_event_flags"]["ebitda_2050"] = ebitda_2050
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


# ═════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════

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
    Recursively collect all string values that look like flags
    from the active_event_flags (which may be nested from prior rounds).
    """
    result = set()
    for key, val in flags_dict.items():
        if isinstance(val, list):
            result.update(str(v) for v in val)
        elif isinstance(val, str):
            result.add(val)
        elif isinstance(val, bool) and val:
            result.add(key)
        elif isinstance(val, dict):
            result.update(_collect_all_flags(val))
    # Also check for specific flag keys
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
):
    """
    Persist the flags_set from the chosen option into the
    active_event_flags on the global state.
    """
    choice = _get_primary_choice(decisions)
    cfg_opts = get_round_options(round_number)
    opt = cfg_opts.get(choice, {})
    flags = opt.get("flags_set", [])

    if flags:
        flag_key = f"r{round_number}_flags"
        global_state.setdefault("active_event_flags", {})
        global_state["active_event_flags"][flag_key] = flags
        extra_events[f"flags_set_r{round_number}"] = flags
