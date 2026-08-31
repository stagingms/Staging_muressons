"""
Muressons Global Corporation — Impact Engine (ARCH-001)
Physically extracted from round_logic.py to reduce monolith size.

Contains:
  - R5:  _post_r5_climate        (155 lines) — Stochastic climate event
  - R9:  _post_r9_just_transition (170 lines) — Just transition / strike

These handlers mutate global_state / bu_states in-place (same contract
as round_logic handlers). They are registered in round_logic._POST_TICK_MAP.

R10 (_post_r10_grand_finale, 650 lines) remains in round_logic.py
due to heavy cross-dependencies. It is the next extraction target.

Dependencies:
  - _get_primary_choice from round_logic
  - _fetch_options_for_industry from round_logic
  - _apply_treasury_with_green_fund from round_logic
  - get_round_config from round_configs
"""
from __future__ import annotations

import random
from typing import Any

from round_configs import get_round_config


# These are imported at call time to avoid circular imports.
# The functions are injected by round_logic.py after import.
_get_primary_choice = None
_fetch_options_for_industry = None
_apply_treasury_with_green_fund = None


def _inject_dependencies(primary_choice_fn, fetch_options_fn, treasury_fn):
    """Called by round_logic.py after import to break circular dependency."""
    global _get_primary_choice, _fetch_options_for_industry, _apply_treasury_with_green_fund
    _get_primary_choice = primary_choice_fn
    _fetch_options_for_industry = fetch_options_fn
    _apply_treasury_with_green_fund = treasury_fn


# ═════════════════════════════════════════════════════════════════
#  R5: STOCHASTIC CLIMATE EVENT
# ═════════════════════════════════════════════════════════════════

def _post_r5_climate(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    # Determine resilience factor and base damage from config or pillar aggregate
    from healthcare_configs import get_healthcare_round_config
    if any(b["bu_id"] == "hospitals" for b in bus):
        cfg = get_healthcare_round_config(5)
    else:
        cfg = get_round_config(5)
    special = cfg.get("special_rules", {}) if cfg else {}
    base_damage = special.get("base_damage", 12_000_000)
    threshold = special.get("stochastic_threshold", 0.75)

    if pillar_mode:
        # Rec 4: Read resilience_factor from pillar aggregate impacts
        agg_impacts = events.get("pillar_aggregate_impacts", {})
        resilience_factor = agg_impacts.get("resilience_factor", 0.0)
        extra["r5_pillar_bypass"] = True
    else:
        cfg_opts = _fetch_options_for_industry(5, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})
        resilience_factor = impacts.get("resilience_factor", 0.0)

    # ── Stochastic dice roll (runs for BOTH paradigms) ──
    # Physical risk escalation: cyclone probability increases with climate state
    tipping_tier = gs.get("tipping_tier", events.get("tipping_tier", "none"))
    if tipping_tier == "tipped":
        threshold = min(threshold + 0.15, 0.95)
        extra["cyclone_probability_escalated"] = True
        extra["cyclone_escalation_reason"] = "Tipping point (tipped): +15% probability"
    elif tipping_tier == "stressed":
        threshold = min(threshold + 0.10, 0.95)
        extra["cyclone_probability_escalated"] = True
        extra["cyclone_escalation_reason"] = "Climate stressed: +10% probability"
    elif tipping_tier == "warning":
        threshold = min(threshold + 0.05, 0.95)
        extra["cyclone_probability_escalated"] = True
        extra["cyclone_escalation_reason"] = "Climate warning: +5% probability"

    # B-4 (2026-08-31 audit): the roll now actually reads the special_rules
    # switch that has always documented it. Default True preserves behaviour.
    stochastic_enabled = bool(special.get("stochastic_event", True))
    roll = round(random.random(), 4)
    extra["stochastic_roll"] = roll
    extra["stochastic_threshold"] = threshold
    if not stochastic_enabled:
        roll = 1.0  # switch off: the cyclone can never strike
        extra["stochastic_event_disabled"] = True

    active_resilience_factor = events.get("active_resilience_factor", 0.0)
    effective_resilience = active_resilience_factor

    if roll < threshold:
        actual_damage = round(base_damage * (1 - effective_resilience), 2)

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

    # Treasury cost of the option (legacy only — pillar already applied by router)
    if not pillar_mode:
        if "treasury" in impacts:
            _apply_treasury_with_green_fund(gs, abs(impacts["treasury"]) if impacts["treasury"] < 0 else -impacts["treasury"], extra)
        ncd_delta = impacts.get("natural_capital_debt_delta", 0)
    else:
        ncd_delta = 0  # Already applied by router in pillar mode

    # Deferred CapEx project for resilience infrastructure
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
            extra["resilience_deferred_notice"] = True
            extra["resilience_deferred_rounds"] = 2
            extra["resilience_currently_effective"] = 0.0
            extra["resilience_deferred_amount"] = resilience_factor
            extra["resilience_deferred_message"] = (
                f"\u26a0\ufe0f DEFERRED RESILIENCE: Your chosen climate defence (factor "
                f"{resilience_factor:.0%}) requires 2 rounds of construction time. "
                f"It provides ZERO protection against a cyclone strike THIS round. "
                f"Effective protection right now: 0%. Infrastructure will be "
                f"operational from Round {gs.get('round_number', 5) + 2}."
            )

        if ncd_delta != 0:
            gs["pending_capex_projects"].append({
                "type": "ncd_drop",
                "amount": ncd_delta,
                "bu_target": "all",
                "rounds_remaining": 2,
                "description": "Hard Engineering Impact Adjustments"
            })
            extra["ncd_project_started"] = True
            # Guard: R5 defers NCD as a pending project — the generic
            # applier must not ALSO apply it immediately.
            extra["natural_capital_debt_applied_r5"] = ncd_delta

    # ── ITEM 15: Nature-Based Solution Uncertainty ────────────
    # Option B (mangrove restoration) has stochastic success rate
    if choice == "option_b":
        nbs_success_rate = 0.75  # 75% chance of full establishment
        nbs_roll = random.random()
        nbs_succeeded = nbs_roll < nbs_success_rate
        gs.setdefault("active_event_flags", {})["nbs_roll"] = round(nbs_roll, 4)
        gs["active_event_flags"]["nbs_succeeded"] = nbs_succeeded
        if not nbs_succeeded:
            # Partial establishment: reduce resilience from 0.60 to 0.35
            for proj in gs.get("pending_capex_projects", []):
                if proj.get("type") == "resilience_boost" and proj.get("amount", 0) > 0.5:
                    proj["amount"] = 0.35
                    proj["description"] = "Partial Mangrove Restoration (ecosystem establishment uncertain)"
            extra["nbs_uncertainty"] = {
                "roll": round(nbs_roll, 4),
                "threshold": nbs_success_rate,
                "succeeded": False,
                "original_resilience": 0.60,
                "adjusted_resilience": 0.35,
                "message": (
                    "\U0001f33f Nature-Based Solution Setback: Mangrove seedlings struggled "
                    "in the coastal conditions. Only 60% of planted area established. "
                    "Resilience reduced from 60% to 35%. Ecological restoration "
                    "has inherent uncertainty."
                ),
            }
        else:
            extra["nbs_uncertainty"] = {
                "roll": round(nbs_roll, 4),
                "threshold": nbs_success_rate,
                "succeeded": True,
                "message": (
                    "\U0001f33f Nature-Based Solution Success: Mangrove restoration fully "
                    "established. Ecosystem services providing coastal protection "
                    "and carbon sequestration as planned."
                ),
            }

    extra["r5_choice"] = choice


# ═════════════════════════════════════════════════════════════════
#  R9: JUST TRANSITION
# ═════════════════════════════════════════════════════════════════

def _post_r9_just_transition(
    gs: dict, bus: list[dict], decs: list[dict],
    events: dict, extra: dict, prev_flags: dict,
):
    choice = _get_primary_choice(decs)
    pillar_mode = events.get("pillar_cost_applied") is not None

    if not pillar_mode:
        cfg_opts = _fetch_options_for_industry(9, bus)
        opt = cfg_opts.get(choice, {})
        impacts = opt.get("impacts", {})

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

        rep_delta = impacts.get("reputation", impacts.get("reputation_delta", 0))
        if rep_delta != 0:
            gs["group_reputation"] = max(0, min(100, round(gs["group_reputation"] + rep_delta, 2)))
            # Guard for the generic applier — and the read the ITEM 20
            # retraining clawback has always depended on (it was a dead read
            # before this line existed: the clawback could never fire).
            extra["reputation_applied_r9"] = rep_delta

        sl_delta = impacts.get("social_license_delta", 0)
        if sl_delta != 0:
            for bu in bus:
                bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))
            extra["social_license_applied_r9"] = sl_delta  # guard: generic applier must skip R9

        gov_delta = impacts.get("governance_risk_delta", 0)
        if gov_delta != 0:
            for bu in bus:
                bu["governance_risk_score"] = max(0, min(100, round(bu["governance_risk_score"] + gov_delta, 2)))
            extra["governance_risk_applied_r9"] = gov_delta
    else:
        extra["r9_pillar_bypass"] = True
        impacts = {}  # Standard impacts already applied by router

    # ── Round-specific logic (runs for BOTH paradigms) ──
    # Determine if strike risk is active
    has_strike_risk = impacts.get("strike_risk")
    if pillar_mode:
        pillar_flags = set(events.get("pillar_flags", []))
        has_strike_risk = "immediate_closure" in pillar_flags
    if has_strike_risk:
        avg_sl = sum(bu["social_license_score"] for bu in bus) / len(bus) if bus else 50
        strike_threshold = 50
        # B-4 (2026-08-31 audit): both R9 switches are now actually read.
        # Defaults True preserve shipped behaviour when the keys are absent.
        _r9_rules = (get_round_config(9) or {}).get("special_rules", {})
        _friction_on = bool(_r9_rules.get("regulatory_friction_enabled", True))
        _strike_on = bool(_r9_rules.get("low_social_license_strike_trigger", True))

        # Calculate Regulatory Friction = 1 / SLO_m (avg social license)
        regulatory_friction = round(1.0 / max(1.0, avg_sl), 4)
        extra["regulatory_friction"] = regulatory_friction

        # Fix #6: Wire regulatory_friction as a concrete OPEX surcharge.
        if _friction_on and avg_sl < strike_threshold and regulatory_friction > 0.02:
            friction_penalty_rate = regulatory_friction * 0.08
            for bu in bus:
                friction_penalty = round(bu["opex_base"] * friction_penalty_rate, 2)
                bu["opex_base"] = round(bu["opex_base"] + friction_penalty, 2)
            extra["regulatory_friction_opex_applied"] = True
            extra["regulatory_friction_opex_rate"] = round(friction_penalty_rate * 100, 2)
            extra["regulatory_friction_message"] = (
                f"Low Social Licence (avg {avg_sl:.1f}) is generating regulatory friction. "
                f"OPEX surcharge of {friction_penalty_rate * 100:.1f}% applied across all BUs."
            )

        if _strike_on and avg_sl < strike_threshold:
            cfg = get_round_config(9)
            sp_rules = cfg.get("special_rules", {}) if cfg else {}
            strike_prob = sp_rules.get("strike_probability_override", 0.50)

            # ── Burnout -> Strike Interdependency ──
            avg_burnout = sum(bu.get("staff_burnout_index", 0.0) for bu in bus) / len(bus) if bus else 0.0
            burnout_strike_boost = 0.0
            if avg_burnout > 50.0:
                burnout_strike_boost = round(min(0.20, (avg_burnout - 50.0) / 100.0 * 0.40), 4)
                strike_prob = min(0.95, round(strike_prob + burnout_strike_boost, 4))
                extra["burnout_strike_boost"] = burnout_strike_boost
                extra["burnout_strike_message"] = (
                    f"\u26a0\ufe0f HIGH WORKFORCE BURNOUT ({avg_burnout:.0f}/100): "
                    f"Strike probability increased by +{burnout_strike_boost:.0%}. "
                    f"Consistent HR investment would have mitigated this risk."
                )

            roll = round(random.random(), 4)
            extra["strike_roll"] = roll
            extra["strike_probability"] = strike_prob

            if roll < strike_prob:
                # HARD-002: Scale minimum strike penalty to 5% of treasury
                MINIMUM_STRIKE_PENALTY = max(
                    1_000_000,
                    round(gs.get("corporate_treasury", 0) * 0.05, 2),
                )
                revenue_lost = max(
                    MINIMUM_STRIKE_PENALTY,
                    sum(bu.get("revenue_base", 0) for bu in bus),
                )
                gs["corporate_treasury"] = round(
                    gs["corporate_treasury"] - revenue_lost, 2
                )
                extra["strike_triggered"] = True
                extra["strike_revenue_lost"] = revenue_lost
                extra["strike_floor_applied"] = revenue_lost == MINIMUM_STRIKE_PENALTY
                extra["strike_message"] = (
                    "Workers have gone on strike! All BU revenue for this "
                    f"round has been lost (\u2014${revenue_lost:,.0f} from treasury)."
                )
                extra["revenue_zeroed"] = True

            else:
                extra["strike_triggered"] = False
                extra["strike_message"] = "Strike narrowly averted through last-minute negotiations."
        else:
            extra["strike_triggered"] = False
            extra["strike_message"] = "Social licence sufficient \u2014 no strike risk."

    extra["r9_choice"] = choice

    # ── ITEM 20: Workforce Retraining Success Rate ───────────
    if choice in ("option_b", "option_c"):
        avg_sl = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
        success_rate = min(1.0, 0.7 + 0.003 * avg_sl)
        retrain_roll = random.random()
        retrain_succeeded = retrain_roll < success_rate
        # B-3 fix (2026-08-31 full-course audit): persist the outcome flag —
        # the facilitator dashboard (admin_router) reads retraining_succeeded
        # exactly as it reads nbs_succeeded, but only the NBS half of the
        # stochastic-outcome pair was ever written.
        gs.setdefault("active_event_flags", {})["retraining_succeeded"] = retrain_succeeded
        gs["active_event_flags"]["retraining_roll"] = round(retrain_roll, 4)
        extra["retraining_assessment"] = {
            "success_rate": round(success_rate * 100, 1),
            "roll": round(retrain_roll, 4),
            "succeeded": retrain_succeeded,
            "social_license_factor": round(avg_sl, 1),
        }
        if not retrain_succeeded:
            clawback_pct = 0.30
            r9_rep_gain = extra.get(f"reputation_applied_r9", 0) or extra.get("reputation_applied_r9", 0)
            if r9_rep_gain > 0:
                lost_rep = round(r9_rep_gain * clawback_pct, 2)
                gs["group_reputation"] = max(0, round(gs["group_reputation"] - lost_rep, 2))
                extra["retraining_clawback"] = lost_rep
            extra["retraining_message"] = (
                f"\u26a0\ufe0f Retraining Programme Partial Failure: Only {round(success_rate*100)}% "
                f"of displaced workers completed the programme (social licence: {avg_sl:.0f}). "
                f"30% of transition benefits have been clawed back."
            )
        else:
            extra["retraining_message"] = (
                f"\u2705 Retraining Programme Success: {round(success_rate*100)}% completion rate. "
                f"Strong community engagement (SL: {avg_sl:.0f}) supported programme uptake."
            )
