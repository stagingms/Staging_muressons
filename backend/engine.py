"""
Muressons Global Command — Mathematical Engine
Pure-function module: no I/O, no database access.
All formulas operate on plain dicts and return new state dicts.
"""

from __future__ import annotations
from typing import Any
import copy
import math
import random as _rng


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


# ── 3. Synergy Engine (with Diminishing Returns) ────────────────
def calc_synergy_opex(
    old_opex: float,
    investment_ratio: float,
    synergy_multiplier: float,
) -> float:
    """
    FEATURE 2 — Diminishing Returns:
    Uses sqrt scaling so first dollars invested yield outsized returns,
    while later dollars hit diminishing marginal efficiency.

    effective_ratio = sqrt(ratio) * 0.7
    New_OPEX = Old_OPEX * (1 - (effective_ratio * Synergy_Multiplier))
    Investment_Ratio is clamped to [0.0, 1.0].
    """
    # FIX VULN-002: Tighten investment_ratio clamp to [0.0, 1.0]
    ratio = max(0.0, min(1.0, investment_ratio))
    # Diminishing returns: sqrt curve with 0.7 dampening
    effective_ratio = math.sqrt(ratio) * 0.7
    factor = 1.0 - (effective_ratio * synergy_multiplier)
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


# ── 6. Talent Brain-Drain Engine (Software & Healthcare BUs) ─────────────
def calc_talent_braindrain(
    opex_base: float,
    group_reputation: float,
    burnout_index: float = 0.0,
) -> tuple[float, float]:
    """
    Talent_Penalty = 1 + MAX(0, (65 - Group_Reputation) / 100) * 1.5 + (Burnout_Index / 100)
    OPEX_Next = OPEX_Current * Talent_Penalty

    Returns (new_opex, penalty_multiplier).
    """
    penalty = 1.0 + max(0.0, (65.0 - group_reputation) / 100.0) * 1.5
    
    # Scale OPEX up aggressively if the unit is suffering severe staff burnout
    if burnout_index > 50.0:
        penalty += ((burnout_index - 50.0) / 100.0) * 2.0  # agency/locum overhead

    new_opex = round(opex_base * penalty, 2)
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


# ── 9. Macroeconomic Inflation Engine ───────────────────────────
def calc_inflation(
    opex: float,
    inflation_index: float,
) -> float:
    """
    FEATURE 5 — Macroeconomic Inflation:
    Every round, baseline OPEX increases by inflation_index %.
    Players must invest just to tread water.

    New_OPEX = OPEX * (1 + inflation_index)
    Default inflation_index = 0.025 (2.5%)
    """
    return round(opex * (1.0 + inflation_index), 2)


# ── 10. Execution Overrun Risk Engine ───────────────────────────
def calc_overrun_risk(
    capex: float,
    threshold: float = 3_000_000,
    overrun_probability: float = 0.25,
    overrun_severity: float = 0.15,
) -> tuple[bool, float]:
    """
    FEATURE 3 — Execution Overrun Risk:
    If CAPEX exceeds threshold, there is a stochastic chance of
    a cost overrun that silently drains extra capital.

    Returns (overrun_triggered: bool, overrun_amount: float).
    """
    if capex <= threshold:
        return False, 0.0
    roll = _rng.random()
    if roll < overrun_probability:
        overrun = round(capex * overrun_severity, 2)
        return True, overrun
    return False, 0.0


# ── 11. Technical Debt Engine ───────────────────────────────────
def calc_technical_debt(
    opex: float,
    consecutive_zero_rounds: int,
    penalty_threshold: int = 2,
    penalty_rate: float = 0.04,
) -> tuple[float, bool]:
    """
    FEATURE 4 — Maintenance vs. Transformation CapEx:
    If a BU has received zero investment for `penalty_threshold`
    consecutive rounds, its OPEX increases by `penalty_rate` (4%)
    to simulate technical debt and deferred maintenance.

    Returns (new_opex, penalty_applied).
    """
    if consecutive_zero_rounds >= penalty_threshold:
        return round(opex * (1.0 + penalty_rate), 2), True
    return opex, False


# ── 12. Revenue Cannibalization Engine ──────────────────────────
def calc_revenue_cannibalization(
    bus: list[dict],
    cannibalization_pairs: dict[str, list[str]] | None = None,
    rate: float = 0.03,
) -> dict[str, float]:
    """
    FEATURE 6 — Revenue Cannibalization:
    If a BU's revenue grows significantly (>15% of group avg),
    it cannibalizes related BUs' revenue.

    Default pairs: software cannibalizes electronics,
                   consumer_goods cannibalizes pharma (OTC overlap).
    Healthcare: telehealth cannibalizes clinics.

    Returns {bu_id: cannibalization_amount} (amounts to subtract).
    """
    if cannibalization_pairs is None:
        cannibalization_pairs = {
            "software": ["electronics"],
            "consumer_goods": ["pharma"],
            "telehealth": ["clinics"],
        }
    if not bus:
        return {}

    avg_rev = sum(b["revenue_base"] for b in bus) / len(bus)
    rev_map = {b["bu_id"]: b["revenue_base"] for b in bus}
    penalties: dict[str, float] = {}

    for aggressor_id, victim_ids in cannibalization_pairs.items():
        aggressor_rev = rev_map.get(aggressor_id, 0)
        if aggressor_rev > avg_rev * 1.15:  # 15% above group avg
            for victim_id in victim_ids:
                if victim_id in rev_map:
                    penalty = round(rev_map[victim_id] * rate, 2)
                    penalties[victim_id] = penalties.get(victim_id, 0) + penalty
    return penalties


# ── 13. Stakeholder Fatigue Engine ──────────────────────────────
def calc_stakeholder_fatigue(
    recovery_amount: float,
    crisis_count_lifetime: int,
    fatigue_factor: float = 0.3,
) -> float:
    """
    FEATURE 7 — Stakeholder Fatigue:
    Trust recovery becomes harder after each crisis.
    recovery_efficiency = 1.0 / (1 + fatigue_factor * crisis_count)

    Returns the effective recovery amount (diminished).
    """
    efficiency = 1.0 / (1.0 + fatigue_factor * crisis_count_lifetime)
    return round(recovery_amount * efficiency, 2)


# ── 14. Supply Chain Contagion Engine ───────────────────────────
def calc_supply_chain_contagion(
    bus: list[dict],
    overlap_coefficient: float = 0.002,
) -> dict[str, float]:
    """
    FEATURE 8 — Supply Chain Contagion:
    BUs with high governance_risk contaminate other BUs' OPEX
    through shared supplier networks.

    Returns {bu_id: opex_surcharge} to add to each BU's OPEX.
    """
    if len(bus) < 2:
        return {}
    surcharges: dict[str, float] = {}
    for bu in bus:
        shared_exposure = sum(
            other.get("governance_risk_score", 0) * overlap_coefficient
            for other in bus if other["bu_id"] != bu["bu_id"]
        )
        surcharge = round(bu["opex_base"] * shared_exposure, 2)
        if surcharge > 0:
            surcharges[bu["bu_id"]] = surcharge
    return surcharges


# ── 15. Competitive NPC Index Engine ────────────────────────────
def calc_competitor_pressure(
    competitor_ebitda: float,
    player_ebitda: float,
    competitor_growth_rate: float = 0.03,
) -> tuple[float, float]:
    """
    FEATURE 10 — Competitive Market Dynamics:
    An NPC competitor grows at a steady rate. Player's terminal
    value is adjusted by relative performance.

    Returns (new_competitor_ebitda, relative_advantage).
    relative_advantage is used as a terminal multiplier modifier.
    """
    new_competitor = round(competitor_ebitda * (1.0 + competitor_growth_rate), 2)
    if new_competitor > 0:
        relative = round(player_ebitda / new_competitor, 4)
    else:
        relative = 1.0
    return new_competitor, relative


# ── 16. Working Capital / Cash Conversion Engine ────────────────
def calc_cash_conversion(
    revenue: float,
    governance_risk: float,
    base_efficiency: float = 1.0,
) -> float:
    """
    FEATURE 11 — Working Capital Constraints:
    BUs with high governance_risk have slower cash conversion —
    not all revenue becomes available cash this round.

    cash_efficiency = base_efficiency - (governance_risk / 500)
    Clamped to [0.5, 1.0].

    Returns realized_revenue (the cash that actually arrives).
    """
    efficiency = base_efficiency - (governance_risk / 500.0)
    efficiency = max(0.5, min(1.0, efficiency))
    return round(revenue * efficiency, 2)


# ── 17. Dividend Ratchet Engine ─────────────────────────────────
def calc_dividend_ratchet(
    dividends_this_round: float,
    dividends_last_round: float,
    reputation_penalty: float = 5.0,
    cut_threshold: float = 0.8,
) -> tuple[bool, float]:
    """
    FEATURE 12 — Board Pressure / Dividend Ratchet:
    If dividends are cut by more than (1 - cut_threshold) from
    last round, a reputation penalty is applied.

    Returns (penalty_triggered, penalty_amount).
    """
    if dividends_last_round <= 0:
        return False, 0.0
    if dividends_this_round < dividends_last_round * cut_threshold:
        return True, reputation_penalty
    return False, 0.0


# ── 18. Talent Allocation Pressure Engine ───────────────────────
def calc_talent_allocation_pressure(
    bus: list[dict],
    decisions: list[dict],
    neglect_threshold: float = 0.15,
    penalty_rate: float = 0.02,
) -> dict[str, float]:
    """
    FEATURE 13 — Talent Poaching War:
    BUs receiving less than neglect_threshold share of total CAPEX
    suffer a talent leakage OPEX premium.

    Returns {bu_id: opex_surcharge} for neglected BUs.
    """
    total_capex = sum(d.get("capex_allocated", 0) for d in decisions)
    if total_capex <= 0:
        return {}
    decision_map = {d["bu_id"]: d for d in decisions}
    surcharges: dict[str, float] = {}
    for bu in bus:
        dec = decision_map.get(bu["bu_id"], {})
        bu_capex = dec.get("capex_allocated", 0)
        share = bu_capex / total_capex
        if share < neglect_threshold:
            surcharge = round(bu["opex_base"] * penalty_rate, 2)
            surcharges[bu["bu_id"]] = surcharge
    return surcharges


# ── 19. Technology Lock-In Engine ───────────────────────────────
def calc_technology_lockin(
    bus: list[dict],
    decisions: list[dict],
    lockin_threshold: int = 3,
    penalty_rate: float = 0.15,
) -> tuple[str | None, dict[str, float]]:
    """
    FEATURE 15 — Path-Dependent Technology Lock-In:
    If the same BU receives the highest investment for lockin_threshold
    consecutive rounds, other BUs suffer reduced synergy efficiency.

    Tracking is via risk_factors.top_investment_streak on each BU.

    Returns (locked_bu_id or None, {other_bu_id: synergy_penalty_multiplier}).
    """
    if not decisions or not bus:
        return None, {}

    # Find which BU got the most investment this round
    top_bu = max(decisions, key=lambda d: d.get("capex_allocated", 0))
    top_bu_id = top_bu["bu_id"]
    top_capex = top_bu.get("capex_allocated", 0)
    if top_capex <= 0:
        return None, {}

    # Check streak for the top BU
    bu_map = {b["bu_id"]: b for b in bus}
    top = bu_map.get(top_bu_id, {})
    streak = top.get("risk_factors", {}).get("top_investment_streak", 0)

    if streak >= lockin_threshold:
        penalties = {}
        for bu in bus:
            if bu["bu_id"] != top_bu_id:
                penalties[bu["bu_id"]] = round(1.0 - penalty_rate, 4)
        return top_bu_id, penalties
    return None, {}


# ── 20. ESG Greenwashing Risk Engine ───────────────────────────
def calc_greenwashing_risk(
    choice: str,
    decisions: list[dict],
    green_investment_threshold: float = 0.15,
    penalty: float = 8.0,
) -> tuple[bool, float]:
    """
    FEATURE 16 — ESG Greenwashing Risk:
    If a player selects a "green" option (A or C) but their actual
    average investment ratio is below green_investment_threshold,
    a greenwashing scandal is triggered.

    Returns (scandal_triggered, social_license_penalty).
    """
    green_choices = ("option_a", "option_c")
    if choice not in green_choices:
        return False, 0.0

    # Check if actual investment backs up the rhetoric
    ratios = [d.get("investment_ratio", 0.0) for d in decisions]
    avg_ratio = sum(ratios) / max(len(ratios), 1)
    if avg_ratio < green_investment_threshold:
        return True, penalty
    return False, 0.0


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

    # FIX AUDIT-001: Deep-copy current_global to prevent input mutation.
    # The original dict must remain untouched for the caller (router).
    current_global = copy.deepcopy(current_global)

    next_round = current_global["round_number"] + 1

    # Build a decision lookup  {bu_id: decision_dict}
    decision_map: dict[str, dict] = {d["bu_id"]: d for d in decisions}

    # FIX AUDIT-006: Capture synergy_multiplier BEFORE pending project
    # processing, so VRIO decay operates on the pre-mutation baseline.
    pre_tick_synergy = current_global["synergy_multiplier"]

    # Deep-copy BU states so we mutate freely
    new_bus: list[dict] = copy.deepcopy(current_bus)

    events: dict[str, Any] = {}

    # Accumulator for deferred synergy lag projects (Feature 1)
    new_synergy_lag_projects: list[dict] = []

    # ── FEATURE 6: Revenue Cannibalization — before inflation ────
    cannibalization = calc_revenue_cannibalization(new_bus)
    for bu_id, penalty in cannibalization.items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["revenue_base"] = round(bu["revenue_base"] - penalty, 2)
                events[f"revenue_cannibalized_{bu_id}"] = penalty
                break

    # ── FEATURE 8: Supply Chain Contagion — OPEX surcharges ─────
    sc_surcharges = calc_supply_chain_contagion(new_bus)
    for bu_id, surcharge in sc_surcharges.items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["opex_base"] = round(bu["opex_base"] + surcharge, 2)
                events[f"supply_chain_contagion_{bu_id}"] = surcharge
                break

    # ── FEATURE 11: Working Capital / Cash Conversion ───────────
    for bu in new_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        old_rev = bu["revenue_base"]
        bu["revenue_base"] = calc_cash_conversion(old_rev, gov_risk)
        if bu["revenue_base"] < old_rev:
            events[f"cash_conversion_drag_{bu['bu_id']}"] = round(old_rev - bu["revenue_base"], 2)

    # ── FEATURE 5: Macroeconomic Inflation — apply BEFORE synergy ──
    inflation_index = current_global.get("inflation_index", 0.025)
    for bu in new_bus:
        old_opex = bu["opex_base"]
        bu["opex_base"] = calc_inflation(old_opex, inflation_index)
    events["inflation_index_applied"] = inflation_index

    # ── 3. Synergy Engine & Healthcare Revenue Modifiers ──
    for bu in new_bus:
        # Healthcare: Dynamic Patient Outcomes Score Revenue Modifier (Value-based care penalties)
        if bu["bu_id"] in ("hospitals", "clinics"):
            outcomes = bu.get("patient_outcomes_score", 50.0)
            # +/- 0.5% revenue swing per point deviation from 50 (max +/- 25%)
            rev_modifier = 1.0 + ((outcomes - 50.0) / 200.0)
            # Clamp to prevent extreme anomalies
            rev_modifier = max(0.75, min(1.25, rev_modifier))
            bu["revenue_base"] = round(bu["revenue_base"] * rev_modifier, 2)
            events[f"patient_outcomes_billing_multiplier_{bu['bu_id']}"] = round(rev_modifier, 4)

        dec = decision_map.get(bu["bu_id"], {})
        inv_ratio = dec.get("investment_ratio", 0.0)

        # ── FEATURE 1: Implementation Lag — defer large synergy investments ──
        if inv_ratio > 0.10:
            # Queue the synergy reduction as a pending capex project (1-round delay)
            deferred_opex_reduction = calc_synergy_opex(
                bu["opex_base"], inv_ratio, current_global["synergy_multiplier"]
            )
            reduction_amount = bu["opex_base"] - deferred_opex_reduction
            if reduction_amount > 0:
                new_synergy_lag_projects.append({
                    "type": "synergy_lag",
                    "bu_target": bu["bu_id"],
                    "amount": reduction_amount,
                    "rounds_remaining": 1,
                    "description": f"Synergy implementation completing for {bu['bu_id']}",
                })
                events[f"implementation_lag_deferred_{bu['bu_id']}"] = round(reduction_amount, 2)
            # Don't apply synergy reduction this round — it's deferred
        else:
            # Small investments (≤10%) apply immediately (minor operational tweaks)
            bu["opex_base"] = calc_synergy_opex(
                bu["opex_base"],
                inv_ratio,
                current_global["synergy_multiplier"],
            )

    # ── 1. Corporate Strategic Fund & Short-Term Loan Logic ───────
    # FIX VULN-001: Clamp dividends to treasury (prevent draining below zero)
    base_treasury = current_global["corporate_treasury"]
    clamped_dividends = min(dividends_paid, max(0.0, base_treasury))

    # ── FEATURE 12: Dividend Ratchet — penalize dividend cuts ────
    last_dividends = current_global.get("active_event_flags", {}).get("last_dividends_paid", 0.0)
    ratchet_hit, ratchet_penalty = calc_dividend_ratchet(clamped_dividends, last_dividends)
    if ratchet_hit:
        # Apply reputation penalty to all BUs
        for bu in new_bus:
            bu["reputation_score"] = max(0.0, round(bu["reputation_score"] - ratchet_penalty, 2))
        events["dividend_ratchet_triggered"] = True
        events["dividend_ratchet_penalty"] = ratchet_penalty
    events["last_dividends_paid"] = clamped_dividends

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
    
    # ── FEATURE 3: Execution Overrun Risk ────────────────────────
    # Read tunables from god-mode settings (facilitator can override)
    try:
        from admin_router import _god_mode_settings
        _overrun_prob = _god_mode_settings.get("overrun_probability", 0.25)
        _overrun_sev = _god_mode_settings.get("overrun_severity", 0.15)
    except ImportError:
        _overrun_prob, _overrun_sev = 0.25, 0.15
    overrun_triggered, overrun_amount = calc_overrun_risk(
        total_capex_requested,
        overrun_probability=_overrun_prob,
        overrun_severity=_overrun_sev,
    )
    if overrun_triggered:
        total_capex_requested = round(total_capex_requested + overrun_amount, 2)
        events["capex_overrun_triggered"] = True
        events["capex_overrun_amount"] = overrun_amount
        events["capex_overrun_message"] = (
            f"Execution overrun! Project scope creep added "
            f"${overrun_amount:,.0f} to your capital expenditure."
        )

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

    # ── FEATURE 13: Talent Allocation Pressure ───────────────────
    talent_surcharges = calc_talent_allocation_pressure(new_bus, decisions)
    for bu_id, surcharge in talent_surcharges.items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["opex_base"] = round(bu["opex_base"] + surcharge, 2)
                events[f"talent_neglect_surcharge_{bu_id}"] = surcharge
                break

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
            # FEATURE 1: Deferred synergy lag projects completing
            elif proj.get("type") == "synergy_lag":
                target_bu_id = proj.get("bu_target")
                reduction = proj.get("amount", 0)
                for bu in new_bus:
                    if bu["bu_id"] == target_bu_id:
                        bu["opex_base"] = max(0.0, round(bu["opex_base"] - reduction, 2))
                        events[f"synergy_lag_completed_{target_bu_id}"] = reduction
                        break
        else:
            new_pending_projects.append(proj)

    # Merge synergy lag projects from this tick into the pending queue
    new_pending_projects.extend(new_synergy_lag_projects)

    for bu in new_bus:
        dec = decision_map.get(bu["bu_id"], {})
        invested = dec.get("capex_allocated", 0) > 0
        bu["reputation_score"], bu["social_license_score"] = apply_natural_decay(
            bu["reputation_score"],
            bu["social_license_score"],
            invested,
        )

        # ── FEATURE 4: Technical Debt — penalise neglected BUs ──────
        inv_ratio = dec.get("investment_ratio", 0.0)
        risk = bu.get("risk_factors", {})
        streak = risk.get("zero_investment_streak", 0)
        if inv_ratio == 0.0:
            streak += 1
        else:
            streak = 0
        risk["zero_investment_streak"] = streak
        bu["risk_factors"] = risk

        new_opex, debt_hit = calc_technical_debt(bu["opex_base"], streak)
        if debt_hit:
            bu["opex_base"] = new_opex
            events[f"technical_debt_penalty_{bu['bu_id']}"] = True
            events[f"technical_debt_streak_{bu['bu_id']}"] = streak

    # ── FEATURE 15: Technology Lock-In streak tracking ───────────
    # Determine which BU got the most CAPEX this round
    if decisions:
        top_dec = max(decisions, key=lambda d: d.get("capex_allocated", 0))
        top_bu_id = top_dec["bu_id"]
        top_capex = top_dec.get("capex_allocated", 0)
        for bu in new_bus:
            risk = bu.get("risk_factors", {})
            if top_capex > 0 and bu["bu_id"] == top_bu_id:
                risk["top_investment_streak"] = risk.get("top_investment_streak", 0) + 1
            else:
                risk["top_investment_streak"] = 0
            bu["risk_factors"] = risk

    # ── FEATURE 15: Apply Technology Lock-In penalties ───────────
    locked_bu, lockin_penalties = calc_technology_lockin(new_bus, decisions)
    if locked_bu:
        events["technology_lockin_bu"] = locked_bu
        events["technology_lockin_penalty"] = True
        # Reduce synergy effectiveness for non-locked BUs
        for bu_id, multiplier in lockin_penalties.items():
            events[f"lockin_synergy_penalty_{bu_id}"] = multiplier

    # ── 2. Contagion Engine ─────────────────────────────────────
    group_reputation = calc_contagion(new_bus, crisis_severity)

    # ── FEATURE 7: Stakeholder Fatigue — diminish recovery ──────
    crisis_count = current_global.get("active_event_flags", {}).get("crisis_count_lifetime", 0)
    if crisis_severity > 0:
        crisis_count += 1
    events["crisis_count_lifetime"] = crisis_count
    # Fatigue applies: the reputation loss from contagion is harder to recover from
    # (This manifests as a dampened group_reputation floor after repeated crises)
    if crisis_count > 0:
        old_rep = sum(bu["reputation_score"] for bu in new_bus) / max(len(new_bus), 1)
        recovery_gap = max(0, group_reputation - old_rep)
        if recovery_gap > 0:
            fatigued_recovery = calc_stakeholder_fatigue(recovery_gap, crisis_count)
            group_reputation = round(old_rep + fatigued_recovery, 2)
            group_reputation = max(0.0, min(100.0, group_reputation))
            events["stakeholder_fatigue_applied"] = True
            events["stakeholder_fatigue_efficiency"] = round(1.0 / (1.0 + 0.3 * crisis_count), 4)

    # ── 6. Talent Brain-Drain (Software, Hospitals, Clinics) ────────────────
    for bu in new_bus:
        if bu["bu_id"] in ("software", "hospitals", "clinics"):
            
            # Healthcare: Utilization Overload Fatigue
            if bu["bu_id"] in ("hospitals", "clinics"):
                utilization = bu.get("bed_capacity_utilization", 0.0)
                if utilization > 85.0:
                    bu["staff_burnout_index"] = min(100.0, bu.get("staff_burnout_index", 0.0) + 5.0)
                    events[f"utilization_overload_fatigue_{bu['bu_id']}"] = True

            bu["opex_base"], talent_penalty = calc_talent_braindrain(
                bu["opex_base"], group_reputation, bu.get("staff_burnout_index", 0.0)
            )
            events[f"talent_penalty_applied_{bu['bu_id']}"] = talent_penalty
            # Keep legacy single key for software if expected by dashboard
            if bu["bu_id"] == "software":
                events["talent_penalty_applied"] = talent_penalty

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
            # FIX AUDIT-013: Cap NCD OPEX penalty at 50% of revenue_base
            # to prevent an infinite negative margin death spiral.
            max_penalty = bu.get("revenue_base", 0) * 0.5
            ncd_opex_penalty = min(ncd_opex_penalty, max_penalty)
            if ncd_opex_penalty > 0:
                bu["opex_base"] = round(bu["opex_base"] + ncd_opex_penalty, 2)
                events[f"{bu['bu_id']}_opex_ncd_penalty"] = ncd_opex_penalty

    # ── 5. VRIO Decay ───────────────────────────────────────────
    # Apply to the synergy multiplier as a proxy for group advantage
    # FIX AUDIT-006: Use pre_tick_synergy to avoid decaying a value
    # that was already mutated by pending capex project processing.
    new_synergy = calc_vrio_decay(
        pre_tick_synergy,
        imitation_decay_rate,
    )
    events["synergy_decayed_from"] = pre_tick_synergy

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
    # FIX AUDIT-023: Apply precision of 1 to keep small float values from becoming 0
    tco2e_emissions = round(
        sum(
            bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000
            for bu in new_bus
        ), 1
    )

    # HARD CLAMP on all BU sub-scores to prevent math logic from breaking in edge cases
    for bu in new_bus:
        bu["social_license_score"] = max(0.0, min(100.0, bu.get("social_license_score", 50.0)))
        bu["governance_risk_score"] = max(0.0, min(100.0, bu.get("governance_risk_score", 20.0)))
        bu["carbon_intensity"] = max(0.0, bu.get("carbon_intensity", 50.0))

    # ── FEATURE 16: ESG Greenwashing Risk ────────────────────────
    primary_choice = ""
    for dec in decisions:
        c = dec.get("choice_selected", "")
        if c.startswith("option_"):
            primary_choice = c
            break
    greenwash_hit, greenwash_penalty = calc_greenwashing_risk(primary_choice, decisions)
    if greenwash_hit:
        for bu in new_bus:
            bu["social_license_score"] = max(0.0, round(
                bu["social_license_score"] - greenwash_penalty, 2
            ))
        events["greenwashing_scandal"] = True
        events["greenwashing_penalty"] = greenwash_penalty
        events["greenwashing_message"] = (
            "Greenwashing scandal! Your green rhetoric doesn't match "
            "your actual investment allocation. Public trust plummets."
        )

    # ── FEATURE 9: Regulatory Ratchet — cost_of_capital never drops ─
    historical_coc_max = current_global.get("active_event_flags", {}).get(
        "regulatory_floor_coc", current_global.get("cost_of_capital", 0.05)
    )
    if corporate_cost_of_capital < historical_coc_max:
        corporate_cost_of_capital = historical_coc_max
        events["regulatory_ratchet_active"] = True
    events["regulatory_floor_coc"] = max(historical_coc_max, corporate_cost_of_capital)

    # ── FEATURE 14: Fog of War — metric noise for undiscovered BUs ──
    fog_active = current_global.get("round_number", 1) <= 3
    deep_audit = "deep_audit_completed" in current_global.get("active_event_flags", {})
    if fog_active and not deep_audit:
        events["fog_of_war_active"] = True
        # Add ±10% noise to reported metrics (actual values are untouched,
        # noise is in events for the frontend to apply as display-only)
        fog_noise: dict[str, dict] = {}
        for bu in new_bus:
            noise_factor = _rng.uniform(-0.10, 0.10)
            fog_noise[bu["bu_id"]] = {
                "natural_capital_debt_noise": round(noise_factor, 4),
                "social_license_noise": round(_rng.uniform(-0.10, 0.10), 4),
                "governance_risk_noise": round(_rng.uniform(-0.10, 0.10), 4),
            }
        events["fog_noise"] = fog_noise
    else:
        events["fog_of_war_active"] = False
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

    # ── UN SDG Non-Linear Feedback & Hooks ──────────────────────
    # Compute SDG-specific metrics that are CONSUMED by round_logic.py
    sdg_political_capital = current_global.get("political_capital", 50.0)
    sdg_community_trust = current_global.get("community_trust_score", 50.0)

    if decision_paradigm == "un_sdg":
        # ─── 1. VRIO Institutional Capacity Constraint (SDG 16 Governance) ───
        for bu in new_bus:
            gov = bu.get("governance", 50)
            if gov < 40:
                bu["institutional_leakage_multiplier"] = 0.60
                events[f"institutional_leakage_{bu['bu_id']}"] = True
            else:
                bu["institutional_leakage_multiplier"] = 1.0

        # ─── 2. Non-Linear Feedback: Sanitation Miracle ──────────────────
        for bu in new_bus:
            bn = bu.get("basic_needs", 0)
            hc = bu.get("human_capital", 0)
            if bn > 75 and hc > 75:
                bu["sanitation_miracle_bonus"] = 2.0
                events[f"sanitation_miracle_{bu['bu_id']}"] = True
            else:
                bu["sanitation_miracle_bonus"] = 1.0

        # ─── 3. SDG Interlinkage Matrix Application ──────────────────────
        from sdg_configs import get_sdg_interlinkage_matrix
        matrix = get_sdg_interlinkage_matrix()
        sdg_clusters = ["basic_needs", "human_capital", "sustainable_growth",
                        "planet", "governance", "partnerships"]

        for bu in new_bus:
            spillover_deltas = {c: 0.0 for c in sdg_clusters}
            for (source, target), multiplier in matrix.items():
                source_val = bu.get(source, 0)
                spillover_deltas[target] += multiplier * (source_val / 100.0)

            for cluster in sdg_clusters:
                old_val = bu.get(cluster, 0)
                spillover = max(-5.0, min(5.0, spillover_deltas[cluster] * 10.0))
                decay = old_val * 0.02
                new_val = round(max(0, min(100, old_val + spillover - decay)), 2)
                bu[cluster] = new_val

            events[f"interlinkage_applied_{bu['bu_id']}"] = True

        # ─── 4. Carbon Retribution Hook ──────────────────────────────────
        global_emissions = current_global.get("global_emissions_intensity", 0.0)
        if current_global["round_number"] <= 5 and global_emissions > 100:
            events["carbon_retribution_multiplier"] = 3.0
            events["carbon_retribution_triggered"] = True

        # ─── 5. Migration Contagion (Wealth Gradients) ───────────────────
        if len(new_bus) > 1:
            highest_sg_bu = max(new_bus, key=lambda x: x.get("sustainable_growth", 0))
            events["migration_contagion_target"] = highest_sg_bu["bu_id"]
            total_pressure = sum(
                bu.get("migration_pressure", 0) for bu in new_bus
                if bu["bu_id"] != highest_sg_bu["bu_id"]
            )
            if total_pressure > 0:
                penalty = round(min(15.0, total_pressure * 0.3), 2)
                highest_sg_bu["basic_needs"] = max(0, round(highest_sg_bu.get("basic_needs", 0) - penalty, 2))
                highest_sg_bu["human_capital"] = max(0, round(highest_sg_bu.get("human_capital", 0) - penalty * 0.5, 2))
                events["migration_service_penalty"] = penalty
                events["migration_target_affected"] = highest_sg_bu["bu_id"]

        # ─── 6. Pro-cyclical Donor Fatigue Engine (Asymmetric) ───────────
        avg_gov = sum(bu.get("governance", 0) for bu in new_bus) / max(len(new_bus), 1)
        avg_part = sum(bu.get("partnerships", 0) for bu in new_bus) / max(len(new_bus), 1)
        sdg_political_capital = round((avg_gov + avg_part) / 2.0, 2)
        if sdg_political_capital < 30:
            budget_multiplier = 0.60
        elif sdg_political_capital < 50:
            budget_multiplier = 0.80
        else:
            budget_multiplier = round(1.0 + (sdg_political_capital - 50) / 200.0, 4)
        events["donor_fatigue_budget_multiplier"] = budget_multiplier
        events["political_capital_score"] = sdg_political_capital
        sdg_community_trust = round(avg_gov * 0.6 + avg_part * 0.4, 2)
        events["community_trust_score"] = sdg_community_trust

        # ─── 7. Education Lag Maturation ─────────────────────────────────
        for proj in new_pending_projects:
            if proj.get("type") == "education_lag" and proj.get("rounds_remaining", 1) <= 0:
                events["education_lag_mature"] = True
                boost = proj.get("amount", 0.8)
                for bu in new_bus:
                    old_sg = bu.get("sustainable_growth", 0)
                    bu["sustainable_growth"] = min(100, round(old_sg + boost * 10, 2))
                events["sdg_8_work_multiplier"] = 1.0 + boost

        # ─── 8. Update Global Emissions Intensity ────────────────────────
        global_emissions = round(sum(bu.get("carbon_intensity", 0) for bu in new_bus) / max(len(new_bus), 1), 2)

    # ── Inflation drift: hostility increases inflation ───────────
    new_inflation_index = inflation_index
    if hostility_multiplier > 5:
        new_inflation_index = round(inflation_index + 0.005, 4)  # +0.5% per hostile round
        events["inflation_index_increased"] = new_inflation_index

    # ── FEATURE 10: Competitive NPC Index ────────────────────────
    competitor_ebitda = current_global.get("competitor_ebitda",
        current_global.get("historical_ebitda", historical_ebitda))
    new_competitor, relative_advantage = calc_competitor_pressure(
        competitor_ebitda, historical_ebitda
    )
    events["competitor_ebitda"] = new_competitor
    events["relative_market_advantage"] = relative_advantage
    if relative_advantage < 1.0:
        events["competitor_warning"] = (
            f"Market competitor EBITDA (${new_competitor:,.0f}) exceeds yours. "
            f"Relative advantage: {relative_advantage:.2f}x"
        )

    # ── Assemble new immutable global state ─────────────────────
    new_global: dict[str, Any] = {
        "round_number": next_round,
        "corporate_treasury": new_treasury,
        "group_reputation": group_reputation,
        "synergy_multiplier": new_synergy,
        "cost_of_capital": corporate_cost_of_capital,
        "inflation_index": new_inflation_index,
        "competitor_ebitda": new_competitor,
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
        "political_capital": sdg_political_capital,
        "community_trust_score": sdg_community_trust,
        "global_emissions_intensity": current_global.get("global_emissions_intensity", 0.0),
    }

    return {
        "global_state": new_global,
        "bu_states": new_bus,
        "events": events,
    }
