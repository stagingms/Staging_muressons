"""
Muressons Global Command — Mathematical Engine
Pure-function module: no I/O, no database access.
All formulas operate on plain dicts and return new state dicts.
"""

from __future__ import annotations
from typing import Any
import copy
import math


# ── 1. Corporate Strategic Fund (CSF) ────────────────────────────
def calc_csf(bu_states: list[dict], dividends_paid: float) -> float:
    """
    CSF = Σ(Revenue_Base - OPEX_Base) - Dividends_Paid
    Returns the net cash added to the corporate treasury this round.
    """
    gross_profit = sum(bu["revenue_base"] - bu["opex_base"] for bu in bu_states)
    return gross_profit - dividends_paid


# ── 2. Contagion Engine ──────────────────────────────────────────
def calc_contagion(bu_states: list[dict], crisis_severity: float) -> float:
    """
    Group_Reputation = Avg(BU Reputation Scores) - (Max_Crisis_Severity * 0.4)
    Result is clamped to [0, 100].
    """
    # FIX VULN-003: Clamp crisis_severity to non-negative
    crisis_severity = max(0.0, crisis_severity)
    avg_rep = sum(bu["reputation_score"] for bu in bu_states) / len(bu_states)
    group_rep = avg_rep - (crisis_severity * 0.4)
    return max(0.0, min(100.0, round(group_rep, 2)))


# ── 3. Synergy Engine ───────────────────────────────────────────
def calc_synergy_opex(
    old_opex: float,
    investment_ratio: float,
    synergy_multiplier: float,
) -> float:
    """
    New_OPEX = Old_OPEX * (1 - (Investment_Ratio * Synergy_Multiplier))
    Investment_Ratio is clamped to [0.0, 1.0].
    """
    # FIX VULN-002: Tighten investment_ratio clamp to [0.0, 1.0]
    ratio = max(0.0, min(1.0, investment_ratio))
    factor = 1.0 - (ratio * synergy_multiplier)
    # Prevent negative OPEX
    return max(0.0, round(old_opex * factor, 2))


# ── 4. Natural Capital Cost of Debt ──────────────────────────────
def calc_natural_capital_interest(
    base_rate: float,
    natural_capital_debt: float,
) -> float:
    """
    Interest_Rate = Base_Rate + (Natural_Capital_Debt * 0.0005)
    Rate is floored at base_rate (no negative surcharge).
    """
    # FIX VULN-004: Floor NCD at 0 to prevent negative interest surcharge
    natural_capital_debt = max(0.0, natural_capital_debt)
    return round(base_rate + (natural_capital_debt * 0.0005), 6)


# ── 5. VRIO Decay Function ──────────────────────────────────────
def calc_vrio_decay(
    advantage_current: float,
    imitation_decay_rate: float,
) -> float:
    """
    Advantage_next = Advantage_current * (1 - Imitation_Decay_Rate)
    """
    return round(advantage_current * (1.0 - imitation_decay_rate), 4)


# ── 6. Talent Brain-Drain Engine (Software BU only) ─────────────
def calc_talent_braindrain(
    software_opex: float,
    group_reputation: float,
) -> tuple[float, float]:
    """
    Talent_Penalty = 1 + MAX(0, (65 - Group_Reputation) / 100) * 1.5
    Software_OPEX_Next = Software_OPEX_Current * Talent_Penalty

    Returns (new_opex, penalty_multiplier).
    """
    penalty = 1.0 + max(0.0, (65.0 - group_reputation) / 100.0) * 1.5
    new_opex = round(software_opex * penalty, 2)
    return new_opex, round(penalty, 4)


# ── 7. Strike Probability Engine ────────────────────────────────
def calc_strike_probability(
    base_risk: float,
    social_license: float,
) -> float:
    """
    P_Strike = Base_Risk + ((1 - (Social_License / 100)) * 0.4)
    Result is clamped to [0.0, 1.0].
    """
    p = base_risk + ((1.0 - (social_license / 100.0)) * 0.4)
    return max(0.0, min(1.0, round(p, 4)))


# ── 8. Natural Decay ────────────────────────────────────────────
def apply_natural_decay(
    reputation: float,
    social_license: float,
    invested: bool,
) -> tuple[float, float]:
    """
    If no investment was made during the tick, both Reputation and
    Social License decay by 2%.
    Returns (new_reputation, new_social_license).
    """
    if invested:
        return reputation, social_license
    decay = 0.98
    return (
        round(reputation * decay, 2),
        round(social_license * decay, 2),
    )


# ═════════════════════════════════════════════════════════════════
#  TICK ORCHESTRATOR
# ═════════════════════════════════════════════════════════════════

def process_tick(
    current_global: dict,
    current_bus: list[dict],
    decisions: list[dict],
    dividends_paid: float = 0.0,
    crisis_severity: float = 0.0,
    imitation_decay_rate: float = 0.05,
    decision_paradigm: str = "legacy_abc",
) -> dict[str, Any]:
    """
    Master tick function. Receives the current round state and player
    decisions, runs every engine in sequence, and returns a complete
    next-round state dict (ready to be persisted as an immutable row).

    Parameters
    ----------
    current_global : dict
        Keys: corporate_treasury, group_reputation, synergy_multiplier,
              cost_of_capital, active_event_flags, round_number,
              green_transition_fund, tipping_point_active
    current_bus : list[dict]
        One dict per BU with all BU-level metrics.
    decisions : list[dict]
        One per BU: bu_id, investment_ratio, capex_allocated,
        choice_selected, decision_node_id, ...
    dividends_paid : float
        Dividends declared this round.
    crisis_severity : float
        Max crisis severity score for the contagion engine (0–100).
    imitation_decay_rate : float
        Decay rate for the VRIO function (default 5%).
    decision_paradigm : str
        Used to strictly isolate `advanced_climate` mechanics.

    Returns
    -------
    dict with keys:
        "global_state" : dict   — next-round global metrics
        "bu_states"    : list   — next-round BU snapshots
        "events"       : dict   — computed events / flags
    """

    next_round = current_global["round_number"] + 1

    # Build a decision lookup  {bu_id: decision_dict}
    decision_map: dict[str, dict] = {d["bu_id"]: d for d in decisions}

    # Deep-copy BU states so we mutate freely
    new_bus: list[dict] = copy.deepcopy(current_bus)

    events: dict[str, Any] = {}

    # ── 3. Synergy Engine — update OPEX per BU ──────────────────
    for bu in new_bus:
        dec = decision_map.get(bu["bu_id"], {})
        inv_ratio = dec.get("investment_ratio", 0.0)
        bu["opex_base"] = calc_synergy_opex(
            bu["opex_base"],
            inv_ratio,
            current_global["synergy_multiplier"],
        )

    # ── 1. Corporate Strategic Fund & Short-Term Loan Logic ───────
    # FIX VULN-001: Clamp dividends to treasury (prevent draining below zero)
    base_treasury = current_global["corporate_treasury"]
    clamped_dividends = min(dividends_paid, max(0.0, base_treasury))
    csf = calc_csf(new_bus, clamped_dividends)
    if clamped_dividends < dividends_paid:
        events["dividends_clamped"] = True
        events["dividends_requested"] = dividends_paid
        events["dividends_paid"] = clamped_dividends
    
    # Calculate free capital allowance (20% of starting treasury)
    free_csf_limit = base_treasury * 0.20
    
    # Advanced Climate Engine: Check available Green Fund for CapEx offsets
    green_fund_balance = current_global.get("green_transition_fund", 0.0)
    total_capex_requested = sum(dec.get("capex_allocated", 0) for dec in decisions)
    
    green_fund_used = 0.0
    if decision_paradigm == "advanced_climate" and total_capex_requested > 0 and green_fund_balance > 0:
        green_fund_used = min(total_capex_requested, green_fund_balance)
        total_capex_requested -= green_fund_used
        events["green_fund_used"] = green_fund_used
    
    new_green_fund_balance = round(green_fund_balance - green_fund_used, 2)
    
    # FIX VULN-006: Cap total CAPEX at 2× treasury to prevent absurd loans
    capex_cap = base_treasury * 2.0
    if total_capex_requested > capex_cap:
        total_capex_requested = capex_cap
        events["capex_capped"] = True
        events["capex_cap_limit"] = capex_cap
    
    # Determine if a short term loan was triggered
    loan_interest_payment = 0.0
    loan_principal = max(0.0, total_capex_requested - free_csf_limit)
    
    if loan_principal > 0:
        loan_interest_rate = current_global.get("active_event_flags", {}).get("loan_interest_rate", 0.12)
        loan_interest_payment = round(loan_principal * loan_interest_rate, 2)
        events["loan_principal"] = round(loan_principal, 2)
        events["loan_interest_rate"] = loan_interest_rate
        events["loan_interest_payment"] = loan_interest_payment

    # Treasury next round: Base + Operational Profit - Any Loan Interest Penalties
    new_treasury = round(base_treasury + csf - loan_interest_payment, 2)

    # ── 8. Natural Decay & Pending CapEx — per BU ───────────────────
    pending_projects = current_global.get("pending_capex_projects", [])
    new_pending_projects = []
    
    # Process maturing CapEx projects
    for proj in pending_projects:
        proj["rounds_remaining"] -= 1
        if proj["rounds_remaining"] <= 0:
            events["capex_project_completed"] = proj
            # Apply the effects
            if proj.get("type") == "ncd_drop":
                for bu in new_bus:
                    if proj.get("bu_target") == "all" or bu["bu_id"] == proj.get("bu_target"):
                        bu["natural_capital_debt"] = max(0, bu.get("natural_capital_debt", 0) + proj.get("amount", 0))
            elif proj.get("type") == "resilience_boost":
                events["active_resilience_factor"] = proj.get("amount", 0.0)
            elif proj.get("type") == "synergy_boost":
                current_global["synergy_multiplier"] += proj.get("amount", 0.0)
            elif proj.get("type") == "truth_premium":
                events["truth_premium_active"] = True
        else:
            new_pending_projects.append(proj)

    for bu in new_bus:
        dec = decision_map.get(bu["bu_id"], {})
        invested = dec.get("capex_allocated", 0) > 0
        bu["reputation_score"], bu["social_license_score"] = apply_natural_decay(
            bu["reputation_score"],
            bu["social_license_score"],
            invested,
        )

    # ── 2. Contagion Engine ─────────────────────────────────────
    group_reputation = calc_contagion(new_bus, crisis_severity)

    # ── 6. Talent Brain-Drain (Software BU only) ────────────────
    for bu in new_bus:
        if bu["bu_id"] == "software":
            bu["opex_base"], talent_penalty = calc_talent_braindrain(
                bu["opex_base"], group_reputation
            )
            events["talent_penalty_applied"] = talent_penalty
            break

    # ── 4. Natural Capital Cost of Debt — per BU ────────────────
    interest_rates: dict[str, float] = {}
    corporate_cost_of_capital = current_global.get("cost_of_capital", 0.05)
    
    # Stranded Asset Decay: Cost of Capital Spike
    if decision_paradigm == "advanced_climate":
        stranded_assets = [bu for bu in new_bus if bu.get("carbon_intensity", 0) > 120]
        if stranded_assets:
            corporate_cost_of_capital = round(corporate_cost_of_capital + 0.015, 4)
            events["stranded_asset_penalty_applied"] = True
            events["stranded_asset_bu_ids"] = [bu["bu_id"] for bu in stranded_assets]
    
    # If treasury is negative, deduct interest
    if new_treasury < 0:
        # Prevent unbound negative geometry (insolvency floor at -$500M)
        new_treasury = max(new_treasury, -500_000_000.0)
        debt_service = round(abs(new_treasury) * corporate_cost_of_capital, 2)
        new_treasury = round(new_treasury - debt_service, 2)
        events["negative_treasury_interest_applied"] = debt_service

    for bu in new_bus:
        rate = calc_natural_capital_interest(
            corporate_cost_of_capital,
            bu.get("natural_capital_debt", 0),
        )
        interest_rates[bu["bu_id"]] = rate
        # Accrue a simple interest charge on the debt
        debt_charge = round(bu.get("natural_capital_debt", 0) * rate, 2)
        new_ncd = round(bu.get("natural_capital_debt", 0) + debt_charge, 2)
        # FIX VULN-007: Cap NCD at 1,000,000 to prevent float overflow
        bu["natural_capital_debt"] = min(new_ncd, 1_000_000)
    events["interest_rates"] = interest_rates

    # Toxic OPEX Penalty (Natural Capital Debt Multiplier)
    hostility_multiplier = current_global.get("active_event_flags", {}).get("market_hostility_index", 5)
    if decision_paradigm == "advanced_climate":
        if current_global.get("tipping_point_active", False):
            hostility_multiplier *= 2

        for bu in new_bus:
            ncd = max(0, bu.get("natural_capital_debt", 0))
            ncd_opex_penalty = round((ncd * 50_000 * hostility_multiplier) / 1_000_000, 2) # Represented in millions
            if ncd_opex_penalty > 0:
                bu["opex_base"] = round(bu["opex_base"] + ncd_opex_penalty, 2)
                events[f"{bu['bu_id']}_opex_ncd_penalty"] = ncd_opex_penalty

    # ── 5. VRIO Decay ───────────────────────────────────────────
    # Apply to the synergy multiplier as a proxy for group advantage
    new_synergy = calc_vrio_decay(
        current_global["synergy_multiplier"],
        imitation_decay_rate,
    )
    events["synergy_decayed_from"] = current_global["synergy_multiplier"]

    # ── 7. Strike Probability — per BU ──────────────────────────
    strike_probs: dict[str, float] = {}
    for bu in new_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        base_risk = gov_risk / 100.0  # normalise to [0,1]
        p = calc_strike_probability(base_risk, bu["social_license_score"])
        strike_probs[bu["bu_id"]] = p
    events["strike_probabilities"] = strike_probs

    # ── Compute Derived Dashboard Metrics ───────────────────────
    # EBITDA proxy: group-level gross profit
    historical_ebitda = round(
        sum(bu["revenue_base"] - bu["opex_base"] for bu in new_bus), 2
    )

    # Carbon tonnage: intensity × revenue scale (tCO2e)
    tco2e_emissions = round(
        sum(
            bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000
            for bu in new_bus
        )
    )

    # HARD CLAMP on all BU sub-scores to prevent math logic from breaking in edge cases
    for bu in new_bus:
        bu["social_license_score"] = max(0.0, min(100.0, bu.get("social_license_score", 50.0)))
        bu["governance_risk_score"] = max(0.0, min(100.0, bu.get("governance_risk_score", 20.0)))
        bu["carbon_intensity"] = max(0.0, bu.get("carbon_intensity", 50.0))

    # VRIO capabilities (0-100 each)
    n = len(new_bus) or 1
    avg_sl = sum(bu.get("social_license_score", 50) for bu in new_bus) / n
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in new_bus) / n
    avg_gr = sum(bu.get("governance_risk_score", 20) for bu in new_bus) / n
    vrio_capabilities = {
        "value": round(max(0, min(100, avg_sl)), 1),
        "rarity": round(max(0, min(100, 100 - avg_ci)), 1),
        "imitability": round(max(0, min(100, new_synergy * 100)), 1),
        "organization": round(max(0, min(100, 100 - avg_gr)), 1),
    }

    # Internal Carbon Pricing (Green Transition Fund) feedback loop
    if decision_paradigm == "advanced_climate":
        carbon_fee_per_ton = current_global.get("active_event_flags", {}).get("global_carbon_fee", 40)
        round_carbon_fee_total = round(tco2e_emissions * carbon_fee_per_ton, 2)
        # Deduct from treasury and move to Green Fund
        new_treasury = round(new_treasury - round_carbon_fee_total, 2)
        new_green_fund_balance = round(new_green_fund_balance + round_carbon_fee_total, 2)
        events["internal_carbon_fee_deducted"] = round_carbon_fee_total

    # Global Exponential Tipping Point
    tipping_point_active = current_global.get("tipping_point_active", False)
    if decision_paradigm == "advanced_climate":
        if not tipping_point_active and current_global["round_number"] >= 5 and avg_ci > 100:
            tipping_point_active = True
            events["tipping_point_reached"] = True

    # ── Assemble new immutable global state ─────────────────────
    new_global: dict[str, Any] = {
        "round_number": next_round,
        "corporate_treasury": new_treasury,
        "group_reputation": group_reputation,
        "synergy_multiplier": new_synergy,
        "cost_of_capital": corporate_cost_of_capital,
        "green_transition_fund": new_green_fund_balance,
        "tipping_point_active": tipping_point_active,
        "active_event_flags": events,
        "historical_ebitda": historical_ebitda,
        "tco2e_emissions": tco2e_emissions,
        "vrio_capabilities": vrio_capabilities,
        "bonus_score": current_global.get("bonus_score", 0),
        "learning_bonuses_awarded": current_global.get("learning_bonuses_awarded", {}),
        "stakeholder_map_completed": current_global.get("stakeholder_map_completed", False),
        "stakeholder_map_accuracy": current_global.get("stakeholder_map_accuracy", 0),
        "saved_allocations": current_global.get("saved_allocations"),
        "saved_decision_choice": current_global.get("saved_decision_choice"),
        "materiality_budget_allocated": current_global.get("materiality_budget_allocated"),
        "materiality_bu_id": current_global.get("materiality_bu_id"),
        "pending_capex_projects": new_pending_projects,
    }

    return {
        "global_state": new_global,
        "bu_states": new_bus,
        "events": events,
    }
