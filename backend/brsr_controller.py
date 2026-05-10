"""
Muressons — BRSR NGRBC Implementation Controller
=================================================
Orchestrates the BRSR track lifecycle:
  1. Prerequisite validation (ethics + reporting tracks)
  2. Track state initialisation per session
  3. Per-round decision routing → BRSRNGRBCTrack.post_tick()
  4. Consequence propagation: ESG Alpha dividend, governance drag
  5. Facilitator status API payload builder

All state is stored inside the main session's global_state dict under
the key "_brsr_track_state", following the same pattern as SDG.
"""

from __future__ import annotations
from typing import Any

from side_tracks.brsr_ngrbc.track import BRSRNGRBCTrack
from side_tracks.brsr_ngrbc.configs import BRSR_ROUND_CONFIGS

# Singleton track instance (stateless methods)
_track = BRSRNGRBCTrack()

# ── Prerequisite flags ───────────────────────────────────────────
BRSR_PREREQUISITE_FLAGS = ["ethics_track_completed", "reporting_track_completed"]

# How many prerequisites are required to unlock BRSR (0 = always open)
BRSR_PREREQ_MINIMUM = 0   # Facilitator can override via god_mode

# ── SEBI Glide Path Thresholds ───────────────────────────────────
# Based on real BRSR Core glide path: top 1000 → top 500 → top 250
BRSR_PIONEER_SCORE_THRESHOLD = 80     # ESG Alpha dividend unlocked
BRSR_CORE_ASSURED_BONUS_REPUTATION = 8  # Reputation boost from BRSR Core assurance
BRSR_FRAGILITY_TREASURY_PENALTY = 2_500_000  # Already in track.py for R5

# ── NCD & Synergy constants ──────────────────────────────────────
BRSR_CIRCULAR_SYMBIOSIS_NCD_REDUCTION = 0.012  # -1.2% NCD rate per round
BRSR_GOVERNANCE_DRAG_RATE = 0.04               # +4% governance risk if fragility active


# ════════════════════════════════════════════════════════════════
#  1. INITIALISATION
# ════════════════════════════════════════════════════════════════

def init_brsr_state(
    main_global: dict,
    main_bus: list[dict],
    completed_tracks: dict,
) -> dict:
    """
    Initialise BRSR track state from the current main sim.
    Seeds starting dimension scores from ethics/reporting cross-track bonuses.
    Idempotent — returns existing state if already initialised.
    """
    if "_brsr_track_state" in main_global:
        return main_global["_brsr_track_state"]

    seed = _track.seed_from_main_state(main_global, main_bus, completed_tracks)
    seed.update({
        "round_choices": {},         # {1: "option_a", ...}
        "round_points": {},          # {1: 80, 2: 50, ...}
        "brsr_round_history": [],    # [{round, choice, dimension_scores, flags_set}]
        "drag_applied_rounds": [],
        "esg_alpha_earned": False,
    })
    main_global["_brsr_track_state"] = seed
    return seed


# ════════════════════════════════════════════════════════════════
#  2. PREREQUISITE CHECK
# ════════════════════════════════════════════════════════════════

def check_brsr_prerequisites(
    main_global: dict,
    god_mode_override: bool = False,
) -> dict:
    """
    Validate whether the BRSR track can be activated.
    Returns a dict with 'eligible', 'met_prerequisites', 'missing'.
    """
    flags = main_global.get("active_event_flags", {})
    met = [p for p in BRSR_PREREQUISITE_FLAGS if flags.get(p)]
    missing = [p for p in BRSR_PREREQUISITE_FLAGS if not flags.get(p)]

    eligible = god_mode_override or len(met) >= BRSR_PREREQ_MINIMUM

    return {
        "eligible": eligible,
        "met_prerequisites": met,
        "missing_prerequisites": missing,
        "god_mode_override": god_mode_override,
        "min_required": BRSR_PREREQ_MINIMUM,
    }


# ════════════════════════════════════════════════════════════════
#  3. PER-ROUND DECISION PROCESSING
# ════════════════════════════════════════════════════════════════

def process_brsr_round(
    round_number: int,
    choice: str,
    global_state: dict,
    bu_states: list[dict],
    events: dict | None = None,
    extra_events: dict | None = None,
    previous_flags: dict | None = None,
) -> dict:
    """
    Process one BRSR round decision.

    Args:
        round_number:   BRSR track round (1–5)
        choice:         "option_a" | "option_b" | "option_c"
        global_state:   Main session global state dict (mutated in place)
        bu_states:      List of BU state dicts (mutated in place)
        events/extra_events/previous_flags: forwarded to post_tick

    Returns:
        extra dict with all consequences, narrative events, and metric deltas.
    """
    events = events or {}
    extra_events = extra_events or {}
    previous_flags = previous_flags or {}

    # Ensure track state is initialised
    track_state = global_state.setdefault("_brsr_track_state", {})
    if not track_state:
        track_state = init_brsr_state(global_state, bu_states, {})

    # Idempotency: skip if this BRSR round already processed
    if round_number in track_state.get("round_choices", {}):
        return {"brsr_already_processed": True, "round": round_number}

    # Route via BaseSideTrack — decisions must use 'choice_selected' key
    decisions = [{"choice_selected": choice}]

    extra = _track.post_tick(
        round_number=round_number,
        global_state=global_state,
        bu_states=bu_states,
        decisions=decisions,
        events=events,
        extra_events=extra_events,
        previous_flags=track_state,
    )

    # Update round tracking
    track_state.setdefault("round_choices", {})[round_number] = choice
    cfg = BRSR_ROUND_CONFIGS.get(round_number, {})
    opt = cfg.get("options", {}).get(choice, {})
    flags_set = opt.get("flags_set", [])

    # Recalculate dimension scores from extra keys
    for dim in ["governance_ethics", "human_capital", "environmental", "value_chain", "reporting_quality"]:
        custom_key = f"st_brsr_ngrbc_custom_{dim}"
        if custom_key in extra:
            track_state[dim] = extra[custom_key]

    # Merge accumulated flags
    acc = list(set(track_state.get("accumulated_flags", []) + flags_set))
    track_state["accumulated_flags"] = acc
    extra[f"st_brsr_ngrbc_accumulated_flags"] = acc

    # Append to history for facilitator trend view
    current_score = _track.calculate_score(track_state)
    track_state.setdefault("brsr_round_history", []).append({
        "brsr_round": round_number,
        "choice": choice,
        "flags_set": flags_set,
        "dimension_scores": current_score["dimensions"],
        "total_score": current_score["total_score"],
        "grade": current_score["grade"],
    })

    # Apply round-by-round deep integration consequences
    _apply_brsr_consequences(
        round_number, choice, flags_set, acc,
        global_state, bu_states, track_state, extra
    )

    # Sync track state back
    global_state["_brsr_track_state"] = track_state

    # Surface round summary
    extra["brsr_round_processed"] = {
        "brsr_round": round_number,
        "choice": choice,
        "dimension_scores": current_score["dimensions"],
        "total_score": current_score["total_score"],
        "grade": current_score["grade"],
        "archetype": current_score["archetype"]["title"],
        "flags_active": acc,
        "rounds_remaining": 5 - round_number,
    }

    return extra


# ════════════════════════════════════════════════════════════════
#  4. DEEP CONSEQUENCE ENGINE
# ════════════════════════════════════════════════════════════════

def _apply_brsr_consequences(
    round_number: int,
    choice: str,
    flags_set: list[str],
    accumulated: list[str],
    global_state: dict,
    bu_states: list[dict],
    track_state: dict,
    extra: dict,
) -> None:
    """
    Apply mechanically consequential BRSR effects to the main simulation:

    R1: Leadership → governance_risk reduction; option_c → fragility drag
    R2: Living Wage → staff_burnout across all BUs; statutory min → strike risk
    R3: Circular Symbiosis → NCD rate reduction + synergy boost; min → NCD interest hike
    R4: BRSR Core Assured → reputation bonus + audit tolerance protection
    R5: Integrated Report → ESG Alpha dividend (brsr_net_positive_dividend)
         + what-if narrative for non-completers
    """
    active_flags = global_state.setdefault("active_event_flags", {})
    drag_done = track_state.get("drag_applied_rounds", [])
    if round_number in drag_done:
        return

    # ── Round 1: Governance & Transparency ──────────────────────
    if round_number == 1:
        if "brsr_pioneer" in flags_set:
            # Leadership indicator: reduce governance risk across all BUs
            for bu in bu_states:
                old_gr = bu.get("governance_risk_score", 20)
                bu["governance_risk_score"] = round(max(0, old_gr - 8), 2)
            extra["brsr_governance_risk_reduced_all_bus"] = True
        elif "governance_fragility" in flags_set:
            # Mark for cumulative drag in later rounds
            active_flags["brsr_governance_fragility_active"] = True
            extra["brsr_governance_fragility_warning"] = (
                "⚠️ Governance Fragility: Reactive disclosure has created a structural "
                "weakness. Regulatory ratchet risk elevated from Round 3 onwards."
            )

    # ── Round 2: Workforce & Human Rights ───────────────────────
    elif round_number == 2:
        if "brsr_living_wage" in flags_set:
            # Living Wage Leadership: reduce burnout + set readiness
            for bu in bu_states:
                bu["staff_burnout_index"] = max(0, bu.get("staff_burnout_index", 25) - 12)
                bu["workforce_readiness"] = min(100, bu.get("workforce_readiness", 50) + 8)
            extra["brsr_living_wage_applied_all_bus"] = True
        elif "brsr_statutory_minimums" in flags_set:
            # Statutory minimum: raise strike probability
            current_risk = active_flags.get("base_strike_risk", 0.2)
            active_flags["base_strike_risk"] = round(min(0.6, current_risk + 0.15), 3)
            active_flags["brsr_labor_unrest_risk"] = True
            extra["brsr_statutory_minimums_strike_risk_elevated"] = True

    # ── Round 3: Environment & Circularity ──────────────────────
    elif round_number == 3:
        if "brsr_circular_symbiosis" in flags_set:
            # ZLD + EPR → reduce NCD interest rate
            current_ncd_rate = global_state.get("ncd_interest_rate", 0.05)
            global_state["ncd_interest_rate"] = round(
                max(0.01, current_ncd_rate - BRSR_CIRCULAR_SYMBIOSIS_NCD_REDUCTION), 4
            )
            # Synergy multiplier boost (already in track.py but enforce floor here)
            current_synergy = global_state.get("synergy_multiplier", 1.0)
            global_state["synergy_multiplier"] = round(min(1.5, current_synergy + 0.30), 4)
            active_flags["brsr_circular_economy_active"] = True
            extra["brsr_circular_symbiosis_ncd_rate"] = global_state["ncd_interest_rate"]
            extra["brsr_circular_symbiosis_synergy"] = global_state["synergy_multiplier"]
        elif "brsr_regulatory_minimum" in flags_set:
            # Regulatory minimum: NCD rate increases (CPCB penalties compound)
            current_ncd_rate = global_state.get("ncd_interest_rate", 0.05)
            global_state["ncd_interest_rate"] = round(min(0.12, current_ncd_rate + 0.01), 4)
            active_flags["brsr_cpcb_penalty_active"] = True
            extra["brsr_regulatory_minimum_ncd_hike"] = global_state["ncd_interest_rate"]

        # Governance fragility compounding: ratchet activates from R3
        if active_flags.get("brsr_governance_fragility_active"):
            current_gov_risk = global_state.get("governance_risk_score", 20)
            drag = round(current_gov_risk * BRSR_GOVERNANCE_DRAG_RATE, 2)
            global_state["governance_risk_score"] = round(min(100, current_gov_risk + drag), 2)
            extra["brsr_fragility_governance_drag_r3"] = drag

    # ── Round 4: Value Chain & BRSR Core ────────────────────────
    elif round_number == 4:
        if "brsr_core_assured" in flags_set:
            # Big 4 assurance → reputation bonus + audit tolerance reset
            current_rep = global_state.get("group_reputation", 50)
            global_state["group_reputation"] = round(
                min(100, current_rep + BRSR_CORE_ASSURED_BONUS_REPUTATION), 2
            )
            active_flags["brsr_auditor_tolerance_protected"] = True
            active_flags["audit_tolerance"] = max(
                active_flags.get("audit_tolerance", 50),
                65  # minimum 65 tolerance for BRSR Core assured firms
            )
            extra["brsr_core_assured_reputation_boost"] = BRSR_CORE_ASSURED_BONUS_REPUTATION
            extra["brsr_core_assured_audit_protected"] = True
        elif "brsr_greenwash_risk" in flags_set:
            # Self-assessment: wire into main greenwash scanner
            active_flags["greenwash_detected"] = True
            active_flags["greenwash_scandal_source"] = "brsr_self_assessment_unverifiable"
            extra["brsr_greenwash_crisis_activated"] = True
            extra["brsr_greenwash_narrative"] = (
                "📰 SEBI SHOW-CAUSE: Muressons' BRSR Core self-assessment cannot be verified. "
                "Reasonable assurance failure exposes Scope 3 Greenwash allegations. "
                "Reputation penalty applied; auditor tolerance set to Hostile."
            )
            active_flags["audit_tolerance"] = min(active_flags.get("audit_tolerance", 50), 20)

    # ── Round 5: Integrated Disclosure & ESG Alpha ───────────────
    elif round_number == 5:
        if "brsr_integrated_report" in flags_set:
            # ESG Alpha dividend: M_R uplift at terminal valuation
            active_flags["brsr_net_positive_dividend"] = 0.05
            active_flags["brsr_integrated_report_complete"] = True
            track_state["esg_alpha_earned"] = True
            extra["brsr_esg_alpha_dividend_unlocked"] = 0.05
            extra["brsr_esg_alpha_narrative"] = (
                "💎 ESG ALPHA UNLOCKED: Six Capitals Integrated Report accepted by CRISIL ESG. "
                "Sustainalytics upgrades Muressons from 'Medium Risk' to 'Low Risk'. "
                "M_R terminal multiplier receives +5% ESG Alpha dividend."
            )
        elif "brsr_compliance_only" in flags_set:
            # Compliance file: blocks Truth Premium; exit multiple haircut risk
            active_flags["brsr_truth_premium_blocked"] = True
            extra["brsr_truth_premium_blocked_narrative"] = (
                "📋 COMPLIANCE FILE ONLY: Institutional investors note the absence of an "
                "Integrated Report. CRISIL ESG score remains flat. "
                "Exit Multiple Truth Premium bonus is blocked for this session."
            )

        # Final governance fragility consequence
        if active_flags.get("brsr_governance_fragility_active"):
            # Whistleblower crisis (mirror of track.py R5 consequence)
            current_gov_risk = global_state.get("governance_risk_score", 20)
            global_state["governance_risk_score"] = round(min(100, current_gov_risk + 15), 2)
            extra["brsr_whistleblower_crisis_r5"] = (
                "🔔 WHISTLEBLOWER LEAK: Unreported political contributions from Governance "
                "Fragility phase now under SEBI scrutiny. Confidence severely impacted."
            )

    drag_done.append(round_number)
    track_state["drag_applied_rounds"] = drag_done


# ════════════════════════════════════════════════════════════════
#  5. WRITE-BACK TO MAIN FLAGS
# ════════════════════════════════════════════════════════════════

def finalise_brsr_track(
    global_state: dict,
) -> dict:
    """
    Called when all 5 BRSR rounds are complete.
    Merges the final score and flags into active_event_flags for
    terminal valuation and GameOverSummary consumption.
    """
    track_state = global_state.get("_brsr_track_state", {})
    if not track_state:
        return {}

    wb = _track.write_back_to_main(track_state, global_state)

    # Apply write-back to active_event_flags
    active_flags = global_state.setdefault("active_event_flags", {})
    for k, v in wb.items():
        active_flags[k] = v

    # Expose round history for sparkline
    active_flags["brsr_round_history"] = track_state.get("brsr_round_history", [])

    return wb


# ════════════════════════════════════════════════════════════════
#  6. FACILITATOR MONITOR PAYLOAD
# ════════════════════════════════════════════════════════════════

def build_brsr_facilitator_status(global_state: dict) -> dict:
    """
    Build the full BRSR status payload for the Facilitator monitor panel.
    Includes: dimension scores, grade, flags, round history, consequence log.
    """
    track_state = global_state.get("_brsr_track_state")
    active_flags = global_state.get("active_event_flags", {})

    if not track_state:
        return {
            "brsr_active": False,
            "brsr_track_completed": False,
            "initialised": False,
        }

    score_data = _track.calculate_score(track_state)
    rounds_done = len(track_state.get("round_choices", {}))
    accumulated = track_state.get("accumulated_flags", [])

    # Key consequence flags in a readable format
    consequence_flags = {
        "Governance Fragility Active": active_flags.get("brsr_governance_fragility_active", False),
        "BRSR Core Assured": "brsr_core_assured" in accumulated,
        "Labor Unrest Risk": active_flags.get("brsr_labor_unrest_risk", False),
        "Greenwash Crisis": active_flags.get("greenwash_detected") and
                            active_flags.get("greenwash_scandal_source", "").startswith("brsr"),
        "NCD Rate Reduced": active_flags.get("brsr_circular_economy_active", False),
        "ESG Alpha Earned": track_state.get("esg_alpha_earned", False),
        "Truth Premium Blocked": active_flags.get("brsr_truth_premium_blocked", False),
        "Auditor Tolerance Protected": active_flags.get("brsr_auditor_tolerance_protected", False),
    }

    # M_R impact from ESG Alpha
    esg_alpha = active_flags.get("brsr_net_positive_dividend", 0)

    return {
        "brsr_active": True,
        "initialised": True,
        "brsr_track_completed": active_flags.get("brsr_track_completed", False),
        "rounds_completed": rounds_done,
        "rounds_total": 5,
        "total_score": score_data["total_score"],
        "grade": score_data["grade"],
        "archetype": score_data["archetype"],
        "dimension_scores": score_data["dimensions"],
        "accumulated_flags": accumulated,
        "consequence_flags": consequence_flags,
        "esg_alpha_dividend": esg_alpha,
        "esg_alpha_mr_impact": f"+{int(esg_alpha * 100)}% M_R" if esg_alpha else None,
        "round_history": track_state.get("brsr_round_history", []),
        "inherited": {
            "governance_risk": track_state.get("inherited_governance_risk"),
            "reputation": track_state.get("inherited_reputation"),
        },
    }
