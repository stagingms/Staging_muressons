"""
Muressons Global Corporation — Mathematical Engine
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


# ── 2. Contagion Engine (Sigmoid Model) ──────────────────────────
def calc_contagion(bu_states: list[dict], crisis_severity: float) -> float:
    """
    UPGRADED: Sigmoid contagion model replaces linear.
    Uses S-curve centered at severity=30 to model realistic crisis propagation:
    - Low severity (<15): minimal reputation impact (slow start)
    - Medium severity (20-40): rapid reputation erosion (inflection point)
    - High severity (>50): saturating damage (diminishing marginal harm)

    Formula: Group_Rep = Avg_Rep - 50 × sigmoid((severity - 30) / 15)
    where sigmoid(x) = 1 / (1 + e^(-x))
    Result is clamped to [0, 100].
    """
    # FIX VULN-003: Clamp crisis_severity to non-negative
    crisis_severity = max(0.0, crisis_severity)
    # FIX BUG-001: Guard against empty BU list (ZeroDivisionError)
    if not bu_states:
        return 50.0
    avg_rep = sum(bu["reputation_score"] for bu in bu_states) / len(bu_states)
    # Sigmoid S-curve: slow-fast-slow damage propagation
    sigmoid_input = (crisis_severity - 30.0) / 15.0
    sigmoid_value = 1.0 / (1.0 + math.exp(-sigmoid_input))
    group_rep = avg_rep - (50.0 * sigmoid_value)
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
    Interest_Rate = Base_Rate + (Natural_Capital_Debt * 0.0001)
    Rate is floored at base_rate (no negative surcharge).
    Coefficient calibrated to produce meaningful compounding at typical game NCD levels:
    At NCD=100: rate ≈ 6.0%. At NCD=500: rate ≈ 10.0%. At NCD=1000: rate ≈ 15.0%.
    """
    # FIX VULN-004: Floor NCD at 0 to prevent negative interest surcharge
    natural_capital_debt = max(0.0, natural_capital_debt)
    return round(base_rate + (natural_capital_debt * 0.0001), 6)


# ── 5. VRIO Decay Function ──────────────────────────────────────
def calc_vrio_decay(
    advantage_current: float,
    imitation_decay_rate: float,
) -> float:
    """
    Advantage_next = Advantage_current * (1 - Imitation_Decay_Rate)
    """
    return round(advantage_current * (1.0 - imitation_decay_rate), 4)


# ── 5b. Burnout Accumulation Engine (All BUs) ────────────────────
def calc_burnout_accumulation(
    current_burnout: float,
    burnout_delta: float,
    natural_drift: float = 6.0,
) -> tuple[float, dict]:
    """
    Apply HR-driven burnout changes and natural drift to a BU's burnout index.

    Parameters:
        current_burnout: Current staff_burnout_index (0-100)
        burnout_delta: Delta from HR pillar choice (negative = reduces burnout)
        natural_drift: Per-round passive burnout increase when no HR investment
                       is made (default +6.0 for 6-month rounds). Set to 0 when HR was invested.

    Returns:
        (new_burnout, diagnostics)

    Mechanics:
        - burnout_delta from positive HR actions: typically -16 to -30
        - burnout_delta from negative HR actions (overtime_push): +24 to +30
        - Natural drift: +6/round if no HR action taken (workforce entropy, 6-month period)
        - Clamped to [0, 100]
        - OPEX penalty threshold: burnout > 40 → +0.3% OPEX per burnout point above 40
        - Critical threshold: burnout > 70 → additional governance risk
    """
    # Apply HR-driven delta + natural drift
    new_burnout = current_burnout + burnout_delta + natural_drift
    new_burnout = round(max(0.0, min(100.0, new_burnout)), 2)

    diagnostics = {
        "previous_burnout": round(current_burnout, 2),
        "burnout_delta_applied": burnout_delta,
        "natural_drift_applied": natural_drift,
        "new_burnout": new_burnout,
        "opex_penalty_active": new_burnout > 20.0,
        "critical_burnout": new_burnout > 70.0,
    }

    # Calculate OPEX penalty rate (graded quadratic curve from 20 onwards)
    if new_burnout > 20.0:
        # Smooth quadratic curve: 0% at 20 -> 18% at 100
        # Formula maintains same maximum penalty but removes the hard cliff
        penalty_rate = round(((new_burnout - 20.0) ** 2) * 0.000028125, 4)
        diagnostics["opex_penalty_rate"] = penalty_rate
    else:
        diagnostics["opex_penalty_rate"] = 0.0

    return new_burnout, diagnostics


# ── 5c. Workforce Readiness Engine ───────────────────────────────
def calc_workforce_readiness(
    current_readiness: float,
    hr_investment_made: bool,
    hr_quality_tier: str = "none",
) -> tuple[float, dict]:
    """
    Track global workforce competence level.

    Parameters:
        current_readiness: Current workforce_readiness score (0-100, starts at 50)
        hr_investment_made: Whether any HR pillar investment was made this round
        hr_quality_tier: "high", "medium", or "none"

    Returns:
        (new_readiness, diagnostics)

    Mechanics (6-month rounds):
        - High HR investment: +16 readiness
        - Medium HR investment: +8 readiness
        - No investment: -10 readiness (skills atrophy / brain drain)
        - Clamped to [0, 100]

    Interdependencies (applied in round_logic):
        - readiness < 40: Strategic pillar effectiveness reduced by 20%
        - readiness > 75: Synergy multiplier gets +0.05 bonus at terminal valuation
    """
    if hr_quality_tier == "high":
        delta = 16.0
    elif hr_quality_tier == "medium":
        delta = 8.0
    else:
        delta = -10.0  # skills atrophy (6-month period)

    new_readiness = round(max(0.0, min(100.0, current_readiness + delta)), 2)

    diagnostics = {
        "previous_readiness": round(current_readiness, 2),
        "readiness_delta": delta,
        "hr_quality_tier": hr_quality_tier,
        "new_readiness": new_readiness,
        "low_readiness_penalty": new_readiness < 40.0,
        "high_readiness_bonus": new_readiness > 75.0,
    }

    return new_readiness, diagnostics


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
    Social License decay by ~4% (compounded from 2%/quarter over 6 months).
    Returns (new_reputation, new_social_license).
    """
    if invested:
        return reputation, social_license
    decay = 0.96  # 1 - (1 - 0.98²) ≈ 0.9604, rounded to 0.96 for 6-month period
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
    Every round (6 months), baseline OPEX increases by inflation_index %.
    Players must invest just to tread water.

    New_OPEX = OPEX * (1 + inflation_index)
    Default inflation_index = 0.05 (5% per 6-month period, ~10% annualized)
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


# ── 12. Revenue Cannibalization Engine (Dynamic Market Overlap) ──

# Market overlap matrix: 0.0 = no overlap, 1.0 = full overlap
# Derived from customer segment similarity + shared distribution channels
_MARKET_OVERLAP = {
    ("software", "electronics"): 0.65,       # Shared tech customers
    ("software", "consumer_goods"): 0.15,    # Some digital retail
    ("consumer_goods", "pharma"): 0.40,      # OTC/wellness overlap
    ("electronics", "consumer_goods"): 0.25, # IoT/smart home
    ("telehealth", "clinics"): 0.70,         # Direct substitution
    ("telehealth", "hospitals"): 0.20,       # Triage diversion
    ("hospitals", "specialised_care"): 0.30,  # Referral competition
    # ── Industry Verticals ──
    ("technology", "electronics"): 0.40,     # Hardware / semiconductor
    ("technology", "software"): 0.75,        # Direct substitution
    ("banking_financial_services", "software"): 0.50,  # Enterprise SaaS
    ("banking_financial_services", "technology"): 0.55, # Fintech
    ("oil_gas", "electronics"): 0.20,        # Petrochemicals for plastics
    ("oil_gas", "agriculture"): 0.30,        # Energy inputs, fertiliser
    ("retail_fmcg", "consumer_goods"): 0.70, # Direct substitution
    ("retail_fmcg", "agriculture"): 0.50,    # Food supply chain
    ("agriculture", "consumer_goods"): 0.45, # Food & beverage inputs
    ("agriculture", "pharma"): 0.25,         # Biotech / nutraceuticals
}

def calc_revenue_cannibalization(
    bus: list[dict],
    cannibalization_pairs: dict[str, list[str]] | None = None,
    rate: float = 0.03,
) -> dict[str, float]:
    """
    FEATURE 6 — Revenue Cannibalization (Dynamic):
    Uses market-overlap matrix to determine cannibalization intensity.
    Any BU with revenue >15% above group avg cannibalizes all BUs
    it has market overlap with, proportional to overlap score.

    Returns {bu_id: cannibalization_amount} (amounts to subtract).
    """
    if not bus:
        return {}

    avg_rev = sum(b["revenue_base"] for b in bus) / len(bus)
    rev_map = {b["bu_id"]: b["revenue_base"] for b in bus}
    penalties: dict[str, float] = {}

    for aggressor in bus:
        aggressor_id = aggressor["bu_id"]
        aggressor_rev = aggressor["revenue_base"]
        if aggressor_rev <= avg_rev * 1.15:
            continue
        # Check overlap with every other BU
        for victim in bus:
            victim_id = victim["bu_id"]
            if victim_id == aggressor_id:
                continue
            overlap = _MARKET_OVERLAP.get(
                (aggressor_id, victim_id),
                _MARKET_OVERLAP.get((victim_id, aggressor_id), 0.0)
            )
            if overlap > 0:
                penalty = round(rev_map[victim_id] * rate * overlap, 2)
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
    competitor_growth_rate: float = 0.06,
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
    penalty: float = 15.0,
) -> tuple[bool, float]:
    """
    FEATURE 16 — ESG Greenwashing Risk:
    If a player selects a "green" option (A or C) but their actual
    average investment ratio is below green_investment_threshold,
    a greenwashing scandal is triggered.

    SDG-ORCH Enhancement: Penalty upgraded from 8.0 to 15.0 (Group Reputation).
    Returns (scandal_triggered, social_license_penalty).
    """
    # Green options (A/C) are checked against the standard 15% threshold.
    # Option B (moderate) is also checked but with a more lenient 10% threshold —
    # even moderate choices should be backed by *some* investment to avoid
    # greenwashing allegations.
    green_choices = ("option_a", "option_c")
    moderate_choices = ("option_b",)
    if choice in green_choices:
        ratios = [d.get("investment_ratio", 0.0) for d in decisions]
        avg_ratio = sum(ratios) / max(len(ratios), 1)
        if avg_ratio < green_investment_threshold:
            return True, penalty
    elif choice in moderate_choices:
        ratios = [d.get("investment_ratio", 0.0) for d in decisions]
        avg_ratio = sum(ratios) / max(len(ratios), 1)
        moderate_threshold = green_investment_threshold * 0.67  # ~10% for default 15%
        if avg_ratio < moderate_threshold:
            return True, round(penalty * 0.5, 2)  # Half penalty for moderate choices
    return False, 0.0


# ── 20b. Per-BU Greenwash Scandal Detection (SDG-ORCH) ─────────
def check_bu_greenwash_scandal(
    choice: str,
    bu_investment_ratios: dict[str, float],
    threshold: float = 0.15,
) -> tuple[bool, dict]:
    """
    SDG-ORCH Enhancement — Per-BU Greenwash Detection:
    If a player selects a high-impact 'A' option (Remediation, Ethical Overhaul,
    Circularity) but maintains Average Investment Ratio < 15% for that BU,
    trigger the Greenwashing Scandal.

    Consequences:
      - Group Reputation: -15
      - Consequence DNA: Credibility Impairment (Leak Node, red)
      - Auditor tolerance: set to 'Hostile' (tolerance = 0)

    Args:
        choice: The option selected (e.g., "option_a")
        bu_investment_ratios: {bu_id: average_investment_ratio_pct}
        threshold: Minimum ratio to avoid scandal (default 15%)

    Returns:
        (scandal_triggered, {bu_id: ratio, offending_bus: [...], penalty_details: {...}})
    """
    if choice != "option_a":
        return False, {}

    offending_bus = []
    for bu_id, ratio in bu_investment_ratios.items():
        if ratio < threshold:
            offending_bus.append({
                "bu_id": bu_id,
                "investment_ratio": round(ratio, 4),
                "gap": round(threshold - ratio, 4),
            })

    if offending_bus:
        return True, {
            "scandal_type": "greenwash_hypocrisy",
            "offending_bus": offending_bus,
            "penalty_details": {
                "reputation_delta": -15,
                "auditor_tolerance_override": 0,  # Set to Hostile
                "credibility_impairment": True,    # Red DNA leak node
                "consequence_dna_node": "credibility_impairment",
            },
            "narrative": (
                "📰 GREENWASH SCANDAL: Independent analysis reveals that despite "
                f"choosing the highest-impact option, {len(offending_bus)} Business "
                f"Unit(s) maintained investment ratios below the {threshold*100:.0f}% "
                "threshold. Market credibility collapses. Auditor moves to Hostile."
            ),
        }

    return False, {}



# ── 21. Macro Interest Rate Environment ─────────────────────────
_MACRO_RATE_CYCLES = {
    # R1-R2: Central bank easing (accommodative policy) — 1 year
    1: -0.010, 2: -0.010,
    # R3-R5: Neutral stance (inflation stabilising) — 1.5 years
    3: 0.0, 4: 0.0, 5: 0.0,
    # R6-R8: Tightening cycle (inflation pressures) — 1.5 years
    6: 0.010, 7: 0.010, 8: 0.010,
    # R9-R10: Crisis premium — 1 year
    9: 0.015, 10: 0.020,
}

def calc_macro_rate_environment(round_number: int) -> dict:
    """
    FEATURE 21 — Macro Interest Rate Environment:
    Models central bank policy cycles over 6-month rounds. Returns a CoC modifier
    and a descriptive label for the current rate regime.
    """
    modifier = _MACRO_RATE_CYCLES.get(round_number, 0.0)
    if round_number <= 2:
        regime = "easing"
        label = "🕊️ Accommodative — Central banks maintain low rates to stimulate growth"
    elif round_number <= 5:
        regime = "neutral"
        label = "⚖️ Neutral — Rates stable as inflation targets are met"
    elif round_number <= 8:
        regime = "tightening"
        label = "🦅 Hawkish — Central banks raise rates to combat inflation"
    else:
        regime = "crisis"
        label = "🔥 Crisis Premium — Market uncertainty drives risk-free rates higher"
    return {
        "coc_modifier": modifier,
        "regime": regime,
        "label": label,
        "modifier_pct": round(modifier * 100, 2),
    }


# ── 22. FX Risk Engine ──────────────────────────────────────────

# Geographic revenue exposure (% of revenue from foreign markets)
_BU_FX_EXPOSURE = {
    "pharma": 0.60,           # 60% export (global clinical trials + API exports)
    "electronics": 0.75,      # 75% (global supply chain, Asian manufacturing)
    "consumer_goods": 0.40,   # 40% (domestic-heavy but growing exports)
    "software": 0.80,         # 80% (SaaS is borderless)
    "hospitals": 0.10,        # 10% (local service delivery)
    "clinics": 0.05,          # 5% (neighbourhood-level)
    "specialised_care": 0.15, # 15% (some medical tourism)
    "telehealth": 0.50,       # 50% (cross-border digital health)
    # ── Industry Verticals ──
    "oil_gas": 0.85,                       # 85% (global commodity, USD-denominated)
    "banking_financial_services": 0.70,    # 70% (cross-border banking, FX trading)
    "retail_fmcg": 0.35,                   # 35% (domestic-heavy retail)
    "agriculture": 0.45,                   # 45% (commodity exports)
    "technology": 0.85,                    # 85% (cloud is borderless)
}

def calc_fx_impact(
    bus: list[dict],
    round_number: int,
    seed: int | None = None,
) -> dict:
    """
    FEATURE 22 — FX Risk Engine:
    Stochastic currency movement ±7% per round. Impact proportional
    to each BU's geographic revenue exposure.
    Returns {adjustments: {bu_id: revenue_delta}, fx_index, details}.
    """
    rng = _rng if seed is None else type(_rng)()
    if seed is not None:
        rng.seed(seed)
    # FX index: -0.07 to +0.07 (7% band for 6-month period, ≈ sqrt(2) × 5%)
    fx_movement = round(rng.uniform(-0.07, 0.07), 4)
    adjustments: dict[str, float] = {}
    details: dict[str, dict] = {}
    for bu in bus:
        exposure = _BU_FX_EXPOSURE.get(bu["bu_id"], 0.20)
        rev = bu["revenue_base"]
        delta = round(rev * fx_movement * exposure, 2)
        adjustments[bu["bu_id"]] = delta
        details[bu["bu_id"]] = {
            "exposure_pct": round(exposure * 100, 1),
            "fx_movement_pct": round(fx_movement * 100, 2),
            "revenue_impact": delta,
        }
    direction = "strengthened" if fx_movement > 0 else "weakened"
    return {
        "adjustments": adjustments,
        "fx_index": fx_movement,
        "fx_direction": direction,
        "fx_message": (
            f"Currency {direction} by {abs(fx_movement)*100:.1f}%. "
            f"BUs with high foreign revenue exposure are "
            f"{'benefiting' if fx_movement > 0 else 'impacted negatively'}."
        ),
        "bu_details": details,
    }


# ── 23. DSO / Working Capital Timing ────────────────────────────
def calc_dso_lag(
    revenue: float,
    governance_risk: float,
    round_number: int,
) -> dict:
    """
    FEATURE 23 — Days Sales Outstanding / Working Capital:
    Models the delay between revenue recognition and cash receipt.
    High governance risk → longer DSO → more revenue deferred.

    DSO factor = 0.02 + 0.001 × governance_risk
    At gov_risk=0:  2% deferred (best-in-class collections)
    At gov_risk=50: 7% deferred (average)
    At gov_risk=100: 12% deferred (poor controls)

    Returns {deferred_amount, dso_days_approx, dso_factor}.
    """
    dso_factor = 0.02 + 0.001 * governance_risk
    dso_factor = max(0.0, min(0.15, dso_factor))  # Cap at 15%
    deferred = round(revenue * dso_factor, 2)
    # Approximate DSO in days (1 round ≈ 180 days / 6-month semester)
    dso_days = round(180 * dso_factor / 0.10, 0)  # Normalised to 180-day semester
    return {
        "deferred_amount": deferred,
        "dso_days_approx": dso_days,
        "dso_factor": round(dso_factor, 4),
    }


# ── 24. Macro-Economic Noise ────────────────────────────────────
def calc_macro_noise(round_number: int, seed: int | None = None) -> dict:
    """
    FEATURE 24 — Macro-Economic Noise:
    Adds minor stochastic volatility to baseline economic conditions each round.
    Prevents players from reverse-engineering the deterministic math engine.

    Returns per-round noise deltas for inflation, carbon pricing, and strikes:
    - inflation_noise: ±0.2% (±0.002 as decimal)
    - carbon_price_noise: ±5% of baseline
    - localized_strike_chance: 6% per round (random micro-disruption)
    """
    if seed is not None:
        rng = _rng.Random(seed)
    else:
        rng = _rng

    inflation_noise = round(rng.uniform(-0.004, 0.004), 4)
    carbon_price_pct = round(rng.uniform(-0.07, 0.07), 4)
    # 6% chance of a localized micro-strike in any given 6-month round
    micro_strike = rng.random() < 0.06
    # Pick a random BU index for the micro-strike target
    micro_strike_bu_idx = rng.randint(0, 3)

    return {
        "inflation_noise": inflation_noise,
        "carbon_price_noise_pct": carbon_price_pct,
        "micro_strike_triggered": micro_strike,
        "micro_strike_bu_idx": micro_strike_bu_idx,
        "noise_message": (
            f"Macro noise R{round_number}: inflation {inflation_noise*100:+.2f}%, "
            f"carbon {carbon_price_pct*100:+.1f}%"
            + (", ⚡ localized micro-strike!" if micro_strike else "")
        ),
    }


# ── 25. Turnaround Pathway — 3-Act Distress Arc ─────────────────
# Phase definitions for the turnaround narrative
_TURNAROUND_PHASES = {
    "crisis": {
        "entry_treasury": 0, "entry_reputation": 30,
        "bailout": 3_000_000, "capex_cap": 0.0, "mr_cap": 0.60,
        "narrative_enter": (
            "🚨 EMERGENCY BOARD SESSION: Your company is in critical distress. "
            "The creditors' committee has imposed an immediate spending freeze. "
            "A court-appointed Turnaround Manager has been assigned. "
            "Emergency credit line: +$3M. ALL capital expenditure frozen. "
            "Your only path forward is to survive."
        ),
    },
    "stabilisation": {
        "exit_treasury": 0, "exit_reputation": 20,
        "capex_cap": 0.50, "mr_cap": 0.80,
        "narrative_enter": (
            "📋 STABILISATION APPROVED: The board is cautiously optimistic. "
            "Your restructuring plan has been approved by the creditors' committee. "
            "Limited capital expenditure restored (50% cap). Dividend payments "
            "remain suspended. The market is watching — prove you can rebuild."
        ),
    },
    "recovery": {
        "exit_treasury": 10_000_000, "exit_reputation": 45,
        "capex_cap": 1.0, "mr_cap": 1.20,
        "narrative_enter": (
            "📈 RECOVERY PHASE: Financial stability is returning. Credit rating "
            "upgraded one notch. Full capital expenditure restored. "
            "The Turnaround Manager retains oversight but the board has resumed "
            "strategic authority. One more phase to complete the comeback."
        ),
    },
    "exit": {
        "exit_treasury": 20_000_000, "exit_reputation": 55,
        "mr_bonus": 0.10,
        "narrative_enter": (
            "✅ TURNAROUND COMPLETE: Against all odds, you rebuilt this company "
            "from the brink of insolvency. The Turnaround Manager has been "
            "released. Credit agencies have restored your investment-grade rating. "
            "Your resilience earns a +0.10 Turnaround Premium on terminal valuation."
        ),
    },
}

def detect_distress(
    treasury: float,
    group_reputation: float,
    round_number: int,
    already_in_survival: bool = False,
    current_phase: str = "none",
) -> dict:
    """
    FEATURE 25 — 3-Act Turnaround Arc:
    Replaces binary survival mode with Crisis → Stabilisation → Recovery → Exit.
    Each phase has its own constraints, bailout terms, and narrative tone.

    Phase 1 (Crisis):       Treasury ≤ $0 AND Rep < 30 → CapEx frozen, $3M credit, M_R ≤ 0.60
    Phase 2 (Stabilisation): Treasury > $0 AND Rep > 20 → CapEx 50%, M_R ≤ 0.80
    Phase 3 (Recovery):      Treasury > $10M AND Rep > 45 → Full CapEx, M_R ≤ 1.20
    Exit:                    Treasury > $20M AND Rep > 55 → All caps lifted, +0.10 M_R bonus

    Only triggers from Round 2 onward (too early = normal volatility, ~1 year grace).
    """
    if round_number < 2:
        return {"distress_detected": False, "survival_mode": already_in_survival,
                "turnaround_phase": current_phase}

    # ── Phase progression (already in turnaround)
    if current_phase == "crisis":
        stab = _TURNAROUND_PHASES["stabilisation"]
        if treasury > stab["exit_treasury"] and group_reputation > stab["exit_reputation"]:
            return {
                "distress_detected": False, "survival_mode": True,
                "turnaround_phase": "stabilisation",
                "phase_transition": True,
                "capex_cap_multiplier": stab["capex_cap"],
                "mr_cap": stab["mr_cap"],
                "message": stab["narrative_enter"],
            }
        crisis = _TURNAROUND_PHASES["crisis"]
        return {
            "distress_detected": False, "survival_mode": True,
            "turnaround_phase": "crisis",
            "capex_cap_multiplier": crisis["capex_cap"],
            "mr_cap": crisis["mr_cap"],
            "message": "⏳ Crisis phase active. Spending frozen. Stabilise treasury and reputation.",
        }

    if current_phase == "stabilisation":
        rec = _TURNAROUND_PHASES["recovery"]
        if treasury > rec["exit_treasury"] and group_reputation > rec["exit_reputation"]:
            return {
                "distress_detected": False, "survival_mode": True,
                "turnaround_phase": "recovery",
                "phase_transition": True,
                "capex_cap_multiplier": rec["capex_cap"],
                "mr_cap": rec["mr_cap"],
                "message": rec["narrative_enter"],
            }
        stab = _TURNAROUND_PHASES["stabilisation"]
        return {
            "distress_detected": False, "survival_mode": True,
            "turnaround_phase": "stabilisation",
            "capex_cap_multiplier": stab["capex_cap"],
            "mr_cap": stab["mr_cap"],
            "message": "⏳ Stabilisation phase active. CapEx capped at 50%. Dividends suspended.",
        }

    if current_phase == "recovery":
        ex = _TURNAROUND_PHASES["exit"]
        if treasury > ex["exit_treasury"] and group_reputation > ex["exit_reputation"]:
            return {
                "distress_detected": False, "survival_mode": False,
                "turnaround_phase": "exit",
                "phase_transition": True,
                "recovered": True,
                "mr_bonus": ex.get("mr_bonus", 0.10),
                "message": ex["narrative_enter"],
            }
        rec = _TURNAROUND_PHASES["recovery"]
        return {
            "distress_detected": False, "survival_mode": True,
            "turnaround_phase": "recovery",
            "capex_cap_multiplier": rec["capex_cap"],
            "mr_cap": rec["mr_cap"],
            "message": "📈 Recovery phase active. Full CapEx restored. Push for exit conditions.",
        }

    if current_phase == "exit":
        return {"distress_detected": False, "survival_mode": False,
                "turnaround_phase": "exit", "recovered": True}

    # ── Initial distress detection (not yet in turnaround)
    crisis = _TURNAROUND_PHASES["crisis"]
    is_distressed = treasury <= crisis["entry_treasury"] and \
                    group_reputation < crisis["entry_reputation"]

    if is_distressed and not already_in_survival:
        return {
            "distress_detected": True,
            "survival_mode": True,
            "turnaround_phase": "crisis",
            "phase_transition": True,
            "bailout_amount": crisis["bailout"],
            "capex_cap_multiplier": crisis["capex_cap"],
            "mr_cap": crisis["mr_cap"],
            "archetype_override": "turnaround_manager",
            "message": crisis["narrative_enter"],
        }

    return {"distress_detected": False, "survival_mode": False, "turnaround_phase": "none"}


# ── 28. Severity Classification ─────────────────────────────────
def classify_severity(amount: float, treasury: float) -> dict:
    """
    REC-7 — Classify a financial event by its proportional impact on treasury.
    Returns a severity tier and label for frontend rendering.

    Tiers: routine (<1%), noteworthy (1-5%), material (5-15%), critical (>15%).
    """
    if treasury <= 0:
        pct = 100.0 if amount > 0 else 0.0
    else:
        pct = abs(amount) / treasury * 100

    if pct < 1:
        tier = "routine"
        label = "🟢 Market friction"
    elif pct < 5:
        tier = "noteworthy"
        label = "🟡 Emerging pressure"
    elif pct < 15:
        tier = "material"
        label = "🟠 Strategic impact"
    else:
        tier = "critical"
        label = "🔴 Existential threat"

    return {"severity_tier": tier, "severity_label": label,
            "impact_pct": round(pct, 2), "amount": round(amount, 2)}


# ── 29. Momentum Score ──────────────────────────────────────────
def calc_momentum_score(
    current_global: dict,
    history: list[dict],
) -> dict:
    """
    REC-6 — Measures rate of improvement over a 3-round rolling window.
    Rewards teams that are improving regardless of absolute position.

    Momentum = 0.4 × Δ(treasury_velocity) + 0.3 × Δ(reputation) + 0.3 × Δ(NCD_reduction)
    Scaled to 0-100. Two consecutive rounds at >70 earns Comeback Kid bonus.
    """
    if len(history) < 2:
        return {"momentum_score": 50.0, "trend": "insufficient_data",
                "consecutive_high": 0, "comeback_kid": False}

    prev = history[-1]
    prev2 = history[-2] if len(history) >= 2 else prev

    # Treasury velocity change (positive = improving)
    curr_treasury = current_global.get("corporate_treasury", 0)
    prev_treasury = prev.get("corporate_treasury", curr_treasury)
    prev2_treasury = prev2.get("corporate_treasury", prev_treasury)
    delta_velocity = (curr_treasury - prev_treasury) - (prev_treasury - prev2_treasury)

    # Reputation change
    curr_rep = current_global.get("group_reputation", 50)
    prev_rep = prev.get("group_reputation", curr_rep)
    delta_rep = curr_rep - prev_rep

    # NCD change (negative = improving)
    curr_ncd = sum(current_global.get("active_event_flags", {}).get("ncd_transparency", {}).get(bu, {}).get("new_ncd", 0) for bu in current_global.get("active_event_flags", {}).get("ncd_transparency", {}).keys()) if current_global.get("active_event_flags", {}).get("ncd_transparency") else 0
    prev_ncd = sum(prev.get("active_event_flags", {}).get("ncd_transparency", {}).get(bu, {}).get("new_ncd", 0) for bu in prev.get("active_event_flags", {}).get("ncd_transparency", {}).keys()) if prev.get("active_event_flags", {}).get("ncd_transparency") else 0
    delta_ncd = prev_ncd - curr_ncd  # Positive = NCD is reducing (good)

    # Normalize components to ~[-50, +50] range then shift to 0-100
    norm_velocity = max(-50, min(50, delta_velocity / max(abs(curr_treasury), 1) * 500))
    norm_rep = max(-50, min(50, delta_rep * 5))
    norm_ncd = max(-50, min(50, delta_ncd * 10))

    raw = 50 + (0.4 * norm_velocity + 0.3 * norm_rep + 0.3 * norm_ncd)
    score = round(max(0, min(100, raw)), 1)

    # Track consecutive high momentum
    prev_momentum_history = current_global.get("momentum_history", [])
    consecutive = 0
    for h in reversed(prev_momentum_history):
        if h > 70:
            consecutive += 1
        else:
            break
    if score > 70:
        consecutive += 1

    comeback_kid = consecutive >= 2

    if score >= 70:
        trend = "accelerating"
    elif score >= 50:
        trend = "stable"
    elif score >= 30:
        trend = "decelerating"
    else:
        trend = "declining"

    return {
        "momentum_score": score,
        "trend": trend,
        "components": {
            "treasury_velocity_delta": round(norm_velocity, 1),
            "reputation_delta": round(norm_rep, 1),
            "ncd_reduction_delta": round(norm_ncd, 1),
        },
        "consecutive_high": consecutive,
        "comeback_kid": comeback_kid,
        "comeback_kid_mr_bonus": 0.05 if comeback_kid else 0.0,
    }


# ── 26. Predictive Forecast Engine ──────────────────────────────
# ── Forecast Caching Layer ──────────────────────────────────────
# calc_forecast is called on every dashboard render. Since it's pure
# (deterministic given the same gs/bus), we cache by session+round.
_forecast_cache = {}

def calc_forecast_cached(
    session_id: str,
    round_number: int,
    current_global: dict,
    current_bus: list[dict],
) -> dict:
    """
    Round-keyed cached wrapper for calc_forecast().
    Returns cached result if available for this session+round,
    otherwise computes, caches, and returns.
    """
    key = f"{session_id}_{round_number}"
    if key not in _forecast_cache:
        _forecast_cache[key] = calc_forecast(current_global, current_bus)
    return _forecast_cache[key]

def invalidate_forecast_cache(session_id: str = None):
    """
    Invalidate forecast cache entries.
    If session_id is provided, only invalidate that session's entries.
    If None, flush the entire cache.
    """
    global _forecast_cache
    if session_id is None:
        _forecast_cache.clear()
    else:
        keys_to_remove = [k for k in _forecast_cache if k.startswith(f"{session_id}_")]
        for k in keys_to_remove:
            del _forecast_cache[k]


def calc_forecast(
    current_global: dict,
    current_bus: list[dict],
) -> dict:
    """
    FEATURE 26 — Predictive Dashboard Data:
    Computes rate-of-change (derivatives) for key metrics to help players
    understand trajectory, not just current state.

    Returns derivatives and risk indices that the frontend can display
    as trend arrows, sparklines, and forecast warnings.
    """
    flags = current_global.get("active_event_flags", {})
    n = max(len(current_bus), 1)

    # ── Treasury velocity (change per round estimate)
    treasury = current_global.get("corporate_treasury", 0)
    ebitda = sum(bu["revenue_base"] - bu["opex_base"] for bu in current_bus)
    treasury_velocity = round(ebitda, 2)  # Net cash flow direction

    # ── NCD acceleration (compounding rate)
    total_ncd = sum(bu.get("natural_capital_debt", 0) for bu in current_bus)
    coc = current_global.get("cost_of_capital", 0.05)
    ncd_interest_proj = round(total_ncd * (coc + total_ncd * 0.0001 / n), 2)

    # ── Reputation trend
    avg_rep = sum(bu.get("reputation_score", 50) for bu in current_bus) / n
    avg_slo = sum(bu.get("social_license_score", 50) for bu in current_bus) / n

    # ── Contagion Risk Index (composite leading indicator)
    avg_gov_risk = sum(bu.get("governance_risk_score", 20) for bu in current_bus) / n
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in current_bus) / n
    # Higher = more dangerous. Scale 0-100.
    contagion_risk_index = round(min(100, max(0,
        (avg_gov_risk * 0.3) +
        ((100 - avg_slo) * 0.3) +
        ((100 - avg_rep) * 0.2) +
        (avg_ci * 0.2)
    )), 1)

    # ── Insolvency countdown (rounds until treasury hits zero at current burn)
    if treasury_velocity < 0:
        rounds_to_insolvency = max(1, round(abs(treasury / treasury_velocity), 1))
    else:
        rounds_to_insolvency = None  # Not heading toward insolvency

    # ── NCD projection (rounds until NCD doubles)
    if ncd_interest_proj > 0 and total_ncd > 0:
        ncd_doubling_rounds = round(total_ncd / max(ncd_interest_proj, 1), 1)
    else:
        ncd_doubling_rounds = None

    # ── REC-3: Time-to-Impact Leading Indicators ──────────────────
    # NCD credit downgrade countdown (threshold: 500K per BU)
    max_ncd_bu = max((bu.get("natural_capital_debt", 0) for bu in current_bus), default=0)
    ncd_growth_rate = ncd_interest_proj / max(n, 1) if total_ncd > 0 else 0
    if max_ncd_bu < 500_000 and ncd_growth_rate > 0:
        rounds_to_ncd_downgrade = round((500_000 - max_ncd_bu) / max(ncd_growth_rate, 1), 1)
    else:
        rounds_to_ncd_downgrade = 0 if max_ncd_bu >= 500_000 else None

    # Brain drain countdown (reputation < 25 threshold)
    rep_decay_rate = (100 - avg_rep) * 0.02  # Natural decay rate
    if avg_rep > 25 and rep_decay_rate > 0:
        rounds_to_braindrain = round((avg_rep - 25) / max(rep_decay_rate, 0.1), 1)
    elif avg_rep <= 25:
        rounds_to_braindrain = 0  # Already in brain drain zone
    else:
        rounds_to_braindrain = None

    # Max strike probability across BUs
    max_strike_prob = 0.0
    max_strike_bu = ""
    for bu in current_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        slo = bu.get("social_license_score", 50)
        base_risk = gov_risk / 100.0
        p = round(base_risk + (1 - slo / 100.0) * 0.4, 4)
        if p > max_strike_prob:
            max_strike_prob = p
            max_strike_bu = bu["bu_id"]

    # Death spiral countdown (distress trigger: treasury ≤ 0 AND rep < 30)
    if treasury_velocity < 0 and treasury > 0:
        rounds_to_distress_treasury = round(treasury / abs(treasury_velocity), 1)
    elif treasury <= 0:
        rounds_to_distress_treasury = 0
    else:
        rounds_to_distress_treasury = None

    # Build time-to-impact warnings list (only warnings within 5 rounds)
    time_to_impact_warnings = []
    if rounds_to_ncd_downgrade is not None and rounds_to_ncd_downgrade <= 5:
        time_to_impact_warnings.append({
            "indicator": "NCD Credit Downgrade",
            "rounds": rounds_to_ncd_downgrade,
            "message": f"At current trajectory, NCD will trigger credit downgrade in {rounds_to_ncd_downgrade:.0f} round(s)",
            "severity": "critical" if rounds_to_ncd_downgrade <= 2 else "material",
        })
    if rounds_to_braindrain is not None and rounds_to_braindrain <= 5:
        time_to_impact_warnings.append({
            "indicator": "Brain Drain Activation",
            "rounds": rounds_to_braindrain,
            "message": f"Reputation declining. Brain drain penalty activates in {rounds_to_braindrain:.0f} round(s)",
            "severity": "critical" if rounds_to_braindrain <= 2 else "material",
        })
    if max_strike_prob > 0.20:
        time_to_impact_warnings.append({
            "indicator": "Strike Risk",
            "rounds": 1,
            "message": f"{max_strike_bu} has a {max_strike_prob*100:.0f}% chance of industrial action next round",
            "severity": "critical" if max_strike_prob > 0.40 else "material",
        })
    if rounds_to_distress_treasury is not None and rounds_to_distress_treasury <= 5:
        time_to_impact_warnings.append({
            "indicator": "Death Spiral Entry",
            "rounds": rounds_to_distress_treasury,
            "message": f"At current burn rate, Treasury hits $0 in {rounds_to_distress_treasury:.0f} round(s) — Survival Mode will activate",
            "severity": "critical",
        })

    return {
        "treasury_velocity": treasury_velocity,
        "treasury_trend": "improving" if treasury_velocity > 0 else "declining",
        "ncd_acceleration": ncd_interest_proj,
        "ncd_total": round(total_ncd, 2),
        "ncd_doubling_rounds": ncd_doubling_rounds,
        "avg_reputation": round(avg_rep, 1),
        "avg_social_license": round(avg_slo, 1),
        "contagion_risk_index": contagion_risk_index,
        "contagion_risk_label": (
            "🟢 Low" if contagion_risk_index < 25 else
            "🟡 Moderate" if contagion_risk_index < 50 else
            "🟠 High" if contagion_risk_index < 75 else
            "🔴 Critical"
        ),
        "rounds_to_insolvency": rounds_to_insolvency,
        "insolvency_warning": rounds_to_insolvency is not None and rounds_to_insolvency <= 3,
        # REC-3: Time-to-Impact
        "time_to_impact": {
            "ncd_downgrade_rounds": rounds_to_ncd_downgrade,
            "braindrain_rounds": rounds_to_braindrain,
            "max_strike_probability": round(max_strike_prob, 3),
            "max_strike_bu": max_strike_bu,
            "distress_treasury_rounds": rounds_to_distress_treasury,
            "warnings": time_to_impact_warnings,
            "warning_count": len(time_to_impact_warnings),
        },
    }


# ── 27. SDG Impact Scoring ──────────────────────────────────────
_SDG_MAPPING = {
    1:  {"label": "No Poverty",              "metric": "social_license_score", "weight": 0.4, "threshold": 70},
    2:  {"label": "Zero Hunger",             "metric": "social_license_score", "weight": 0.3, "threshold": 60},
    3:  {"label": "Good Health",             "metric": "reputation_score",     "weight": 0.5, "threshold": 65},
    4:  {"label": "Quality Education",        "metric": "reputation_score",     "weight": 0.3, "threshold": 60},
    5:  {"label": "Gender Equality",          "metric": "social_license_score", "weight": 0.3, "threshold": 65},
    6:  {"label": "Clean Water",             "metric": "water_dependency",     "weight": 1.0, "threshold": 0.4, "invert": True},
    7:  {"label": "Affordable Energy",        "metric": "carbon_intensity",     "weight": 0.5, "threshold": 30, "invert": True},
    8:  {"label": "Decent Work",             "metric": "social_license_score", "weight": 0.8, "threshold": 70},
    9:  {"label": "Industry & Innovation",    "metric": "revenue_base",        "weight": 0.3, "threshold": 15_000_000},
    10: {"label": "Reduced Inequalities",     "metric": "social_license_score", "weight": 0.4, "threshold": 65},
    11: {"label": "Sustainable Cities",       "metric": "governance_risk_score","weight": 0.5, "threshold": 25, "invert": True},
    12: {"label": "Responsible Consumption",  "metric": "natural_capital_debt", "weight": 0.8, "threshold": 3000, "invert": True},
    13: {"label": "Climate Action",          "metric": "carbon_intensity",     "weight": 1.0, "threshold": 25, "invert": True},
    14: {"label": "Life Below Water",         "metric": "water_dependency",     "weight": 0.6, "threshold": 0.3, "invert": True},
    15: {"label": "Life on Land",            "metric": "natural_capital_debt", "weight": 0.7, "threshold": 2000, "invert": True},
    16: {"label": "Peace & Justice",         "metric": "governance_risk_score","weight": 0.8, "threshold": 20, "invert": True},
    17: {"label": "Partnerships",            "metric": "reputation_score",     "weight": 0.4, "threshold": 70},
}

def calc_sdg_impact(bus: list[dict], flags: dict) -> dict:
    """
    FEATURE 27 — SDG Impact Report:
    Maps simulation BU-level variables to all 17 UN SDGs.
    Returns a score (0-100) per SDG and an aggregate SDG Index.

    Scoring: For each SDG, the avg BU metric is compared against
    a threshold. Meeting/exceeding = 100 pts × weight.
    Inverted metrics (lower = better) are scored inversely.
    """
    n = max(len(bus), 1)
    sdg_scores = {}

    for sdg_num, cfg in _SDG_MAPPING.items():
        metric_key = cfg["metric"]
        threshold = cfg["threshold"]
        invert = cfg.get("invert", False)
        weight = cfg["weight"]

        avg_val = sum(bu.get(metric_key, 0) for bu in bus) / n

        if invert:
            # Lower is better: score = 100 if avg ≤ threshold, scaled down above
            if threshold == 0:
                raw_score = 100.0 if avg_val == 0 else max(0, 100 - avg_val)
            else:
                raw_score = max(0, min(100, (1 - avg_val / (threshold * 2)) * 100))
        else:
            # Higher is better: score = 100 if avg ≥ threshold, scaled below
            if threshold == 0:
                raw_score = 100.0
            else:
                raw_score = max(0, min(100, (avg_val / threshold) * 100))

        weighted = round(raw_score * weight, 1)
        sdg_scores[sdg_num] = {
            "sdg": sdg_num,
            "label": cfg["label"],
            "raw_score": round(raw_score, 1),
            "weight": weight,
            "weighted_score": weighted,
            "metric_key": metric_key,
            "avg_value": round(avg_val, 2),
            "threshold": threshold,
            "status": "on_track" if weighted >= 60 else ("at_risk" if weighted >= 30 else "off_track"),
        }

    # Aggregate SDG Index (0-100)
    total_weight = sum(cfg["weight"] for cfg in _SDG_MAPPING.values())
    aggregate = round(
        sum(s["weighted_score"] for s in sdg_scores.values()) / max(total_weight, 1), 1
    )

    # Flag-based bonuses
    bonus_sdgs = []
    if flags.get("community_fund"):
        sdg_scores[1]["weighted_score"] = min(100, sdg_scores[1]["weighted_score"] + 10)
        bonus_sdgs.append("SDG 1: Community Fund bonus +10")
    if flags.get("ethical_ai_overhaul"):
        sdg_scores[16]["weighted_score"] = min(100, sdg_scores[16]["weighted_score"] + 15)
        bonus_sdgs.append("SDG 16: Ethical AI bonus +15")
    if flags.get("circular_redesign"):
        sdg_scores[12]["weighted_score"] = min(100, sdg_scores[12]["weighted_score"] + 15)
        bonus_sdgs.append("SDG 12: Circular Redesign bonus +15")

    return {
        "sdg_scores": sdg_scores,
        "sdg_index": aggregate,
        "sdg_grade": (
            "A+" if aggregate >= 80 else
            "A" if aggregate >= 70 else
            "B" if aggregate >= 55 else
            "C" if aggregate >= 40 else
            "D" if aggregate >= 25 else "F"
        ),
        "bonus_sdgs": bonus_sdgs,
        "total_sdgs_on_track": sum(1 for s in sdg_scores.values() if s["status"] == "on_track"),
        "total_sdgs_at_risk": sum(1 for s in sdg_scores.values() if s["status"] == "at_risk"),
        "total_sdgs_off_track": sum(1 for s in sdg_scores.values() if s["status"] == "off_track"),
    }


# ── 30. Carbon-Adjusted Return on Invested Capital (CAROIC) ─────
def calc_caroic(
    ebitda: float,
    invested_capital: float,
    carbon_tonnage: float,
    tax_rate: float = 0.25,
    shadow_carbon_price: float = 250.0,
) -> dict:
    """
    CAROIC = EBITDA × (1 − Tax Rate) / (Invested Capital + (Carbon Tonnage × Shadow Carbon Price))

    Measures not just return on capital, but the *efficiency* of carbon usage.
    Carbon-heavy companies face a higher effective capital base, reducing their
    CAROIC score — a pedagogical bridge between financial and environmental KPIs.

    Parameters
    ----------
    ebitda : float
        Group-level EBITDA (Revenue - OPEX across all BUs).
    invested_capital : float
        Total capital deployed (corporate treasury as proxy for total capital base).
        Floored at 0 to prevent sign-flip distortions.
    carbon_tonnage : float
        Group carbon tonnage: Σ(carbon_intensity × revenue / 1M) across BUs.
    tax_rate : float
        Effective corporate tax rate, clamped to [0.0, 1.0]. Default 25%.
    shadow_carbon_price : float
        Internal shadow price of carbon per ton, default $250
        (aligned with terminal valuation carbon_tax_per_ton).

    Returns
    -------
    dict with keys:
        "caroic"               : float — the CAROIC ratio (0.0 if denominator ≤ 0)
        "caroic_pct"           : float — CAROIC as percentage
        "nopat"                : float — Net Operating Profit After Tax
        "carbon_capital_charge": float — Carbon Tonnage × Shadow Carbon Price
        "adjusted_capital"     : float — Invested Capital + Carbon Capital Charge
        "grade"                : str   — Letter grade (A+ to F)
        "interpretation"       : str   — Human-readable interpretation
    """
    # Clamp tax_rate to valid range
    tax_rate = max(0.0, min(1.0, tax_rate))

    # NOPAT: Net Operating Profit After Tax
    nopat = ebitda * (1.0 - tax_rate)

    # Carbon capital charge: tonnage × shadow price
    carbon_tonnage = max(0.0, carbon_tonnage)
    shadow_carbon_price = max(0.0, shadow_carbon_price)
    carbon_capital_charge = carbon_tonnage * shadow_carbon_price

    # Adjusted capital base: invested capital + carbon capital charge
    # Floor invested_capital at 0 (negative treasury means company is insolvent,
    # but we still want a meaningful ratio from the carbon charge alone)
    invested_capital_floored = max(0.0, invested_capital)
    adjusted_capital = invested_capital_floored + carbon_capital_charge

    # Guard against division by zero
    if adjusted_capital <= 0:
        caroic = 0.0
    else:
        caroic = nopat / adjusted_capital

    caroic = round(caroic, 6)
    caroic_pct = round(caroic * 100, 2)

    # Grade based on CAROIC percentage (pedagogical thresholds)
    if caroic_pct >= 25:
        grade = "A+"
        interpretation = "Exceptional capital-carbon efficiency. Minimal carbon drag on returns."
    elif caroic_pct >= 15:
        grade = "A"
        interpretation = "Strong carbon-adjusted returns. Carbon transition well-managed."
    elif caroic_pct >= 10:
        grade = "B"
        interpretation = "Solid returns despite carbon drag. Room for decarbonisation gains."
    elif caroic_pct >= 5:
        grade = "C"
        interpretation = "Moderate returns eroded by carbon intensity. Transition urgency rising."
    elif caroic_pct >= 0:
        grade = "D"
        interpretation = "Carbon burden severely depresses returns. Stranded asset risk."
    else:
        grade = "F"
        interpretation = "Negative CAROIC: operating losses compounded by carbon liability."

    return {
        "caroic": caroic,
        "caroic_pct": caroic_pct,
        "nopat": round(nopat, 2),
        "carbon_capital_charge": round(carbon_capital_charge, 2),
        "adjusted_capital": round(adjusted_capital, 2),
        "invested_capital_raw": round(invested_capital, 2),
        "carbon_tonnage": round(carbon_tonnage, 2),
        "shadow_carbon_price": shadow_carbon_price,
        "tax_rate": tax_rate,
        "grade": grade,
        "interpretation": interpretation,
    }


# ═════════════════════════════════════════════════════════════════
#  TICK ORCHESTRATOR
# ═════════════════════════════════════════════════════════════════

def process_tick(
    current_global: dict,
    current_bus: list[dict],
    decisions: list[dict],
    dividends_paid: float = 0.0,
    crisis_severity: float = 0.0,
    imitation_decay_rate: float = 0.10,  # 6-month compounded: 1-(1-0.05)² ≈ 0.0975
    decision_paradigm: str = "legacy_abc",
    emergency_credit_used: bool = False,
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

    # ── REAL-WORLD SCENARIO MECHANICS (Austerity Clamp) ──────────
    if current_global.get("active_event_flags", {}).get("cfo_austerity_active", False):
        for d in decisions:
            d["investment_ratio"] = 0.0
            d["capex_allocated"] = 0.0
            
    # Build a decision lookup  {bu_id: decision_dict}
    decision_map: dict[str, dict] = {d["bu_id"]: d for d in decisions}

    # FIX AUDIT-006: Capture synergy_multiplier BEFORE pending project
    # processing, so VRIO decay operates on the pre-mutation baseline.
    pre_tick_synergy = current_global["synergy_multiplier"]

    # Deep-copy BU states so we mutate freely
    new_bus: list[dict] = copy.deepcopy(current_bus)

    events: dict[str, Any] = {}

    # ── PHASE-1: Black Swan Evaluation — stochastic disruptions ──
    try:
        from black_swan_registry import evaluate_black_swans, apply_black_swan_impacts
        _session_tier = current_global.get("active_event_flags", {}).get("difficulty_tier", "standard")
        _active_swans = current_global.get("active_event_flags", {}).get("active_black_swans", [])
        _forced_swan = current_global.get("active_event_flags", {}).get("forced_black_swan", None)
        _swan_result = evaluate_black_swans(
            current_global, new_bus, current_global["round_number"],
            difficulty_tier=_session_tier,
            active_black_swans=_active_swans,
            forced_event_id=_forced_swan,
        )
        if _swan_result["total_new_events"] > 0:
            _swan_diag = apply_black_swan_impacts(current_global, new_bus, _swan_result["events_triggered"])
            events["black_swan_events"] = _swan_result["events_triggered"]
            events["black_swan_narratives"] = _swan_result["narratives"]
            events["black_swan_diagnostics"] = _swan_diag
            events.setdefault("custom_black_swans", []).extend([
                {"title": e["title"], "narrative": e["narrative"], "icon": e["icon"], "severity": "critical"}
                for e in _swan_result["events_triggered"]
            ])
        # Persist active swans (continuing multi-round events)
        _all_active = _swan_result.get("events_continuing", []) + _swan_result.get("events_triggered", [])
        events["active_black_swans"] = [e for e in _all_active if e.get("rounds_remaining", 0) > 0]
        # Clear forced injection after use
        if _forced_swan:
            events["forced_black_swan"] = None
    except ImportError:
        pass  # Graceful degradation if black_swan_registry not available

    # ── REC-1: Consequence Waterfall Tracker ─────────────────────
    # Snapshot initial values to track deltas through the tick
    initial_treasury = current_global.get("corporate_treasury", 0)
    waterfall: list[dict] = []  # Ordered list of {label, amount, running_total}
    running_total = initial_treasury

    def _wf(label: str, amount: float, because: str = "", counterfactual: str = ""):
        """Record a waterfall entry and optional 'because' annotation."""
        nonlocal running_total
        if abs(amount) < 0.01:
            return
        running_total = round(running_total + amount, 2)
        entry = {
            "label": label, "amount": round(amount, 2),
            "running_total": running_total,
            "severity": classify_severity(abs(amount), max(abs(initial_treasury), 1)),
        }
        if because:
            entry["because"] = because
        if counterfactual:
            entry["counterfactual"] = counterfactual
        waterfall.append(entry)

    # Accumulator for deferred synergy lag projects (Feature 1)
    new_synergy_lag_projects: list[dict] = []

    # ── FEATURE 6: Revenue Cannibalization — before inflation ────
    cannibalization = calc_revenue_cannibalization(new_bus)
    for bu_id, penalty in cannibalization.items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["revenue_base"] = round(bu["revenue_base"] - penalty, 2)
                events[f"revenue_cannibalized_{bu_id}"] = penalty
                events[f"revenue_cannibalized_{bu_id}_because"] = (
                    f"{bu_id} revenue reduced by ${penalty:,.0f} due to market overlap "
                    f"with sibling BUs. When one BU dominates revenue share, "
                    f"it cannibalizes demand from adjacent divisions."
                )
                break

    # ── FEATURE 8: Supply Chain Contagion — OPEX surcharges ─────
    sc_surcharges = calc_supply_chain_contagion(new_bus)
    for bu_id, surcharge in sc_surcharges.items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["opex_base"] = round(bu["opex_base"] + surcharge, 2)
                events[f"supply_chain_contagion_{bu_id}"] = surcharge
                break

    # ── FEATURE 21: Macro Interest Rate Environment ─────────────
    macro_rate = calc_macro_rate_environment(current_global["round_number"])
    events["macro_rate_environment"] = macro_rate

    # ── FEATURE 22: FX Risk — stochastic currency impact ────────
    fx_result = calc_fx_impact(new_bus, current_global["round_number"])
    for bu_id, fx_delta in fx_result["adjustments"].items():
        for bu in new_bus:
            if bu["bu_id"] == bu_id:
                bu["revenue_base"] = round(bu["revenue_base"] + fx_delta, 2)
                break
    events["fx_risk"] = {
        "fx_index": fx_result["fx_index"],
        "fx_direction": fx_result["fx_direction"],
        "fx_message": fx_result["fx_message"],
        "bu_details": fx_result["bu_details"],
    }

    # ── FEATURE 23: DSO / Working Capital Timing ────────────────
    dso_transparency: dict[str, dict] = {}
    total_deferred = 0.0
    for bu in new_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        dso = calc_dso_lag(bu["revenue_base"], gov_risk, current_global["round_number"])
        deferred_amt = dso["deferred_amount"]
        if deferred_amt > 0:
            bu["revenue_base"] = round(bu["revenue_base"] - deferred_amt, 2)
            total_deferred += deferred_amt
            # Queue deferred revenue as a 1-round project
            new_synergy_lag_projects.append({
                "type": "revenue_generation",
                "amount": deferred_amt,
                "rounds_remaining": 1,
                "description": f"Working capital collection for {bu['bu_id']} (DSO: {dso['dso_days_approx']:.0f} days)",
            })
        dso_transparency[bu["bu_id"]] = dso
    events["dso_working_capital"] = {
        "total_deferred": round(total_deferred, 2),
        "bu_details": dso_transparency,
        "note": "Revenue deferred to next round due to cash collection cycle",
    }

    # ── FEATURE 11: Working Capital / Cash Conversion ───────────
    for bu in new_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        old_rev = bu["revenue_base"]
        bu["revenue_base"] = calc_cash_conversion(old_rev, gov_risk)
        if bu["revenue_base"] < old_rev:
            events[f"cash_conversion_drag_{bu['bu_id']}"] = round(old_rev - bu["revenue_base"], 2)

    # ── FEATURE 5: Macroeconomic Inflation — apply BEFORE synergy ──
    inflation_index = current_global.get("inflation_index", 0.05)

    # ── FEATURE 24: Macro-Economic Noise — stochastic volatility ──
    macro_noise = calc_macro_noise(current_global["round_number"])
    inflation_index = round(inflation_index + macro_noise["inflation_noise"], 4)
    events["macro_noise"] = macro_noise
    # Apply micro-strike: random BU gets a 5% OPEX spike
    if macro_noise["micro_strike_triggered"] and new_bus:
        strike_idx = macro_noise["micro_strike_bu_idx"] % len(new_bus)
        target_bu = new_bus[strike_idx]
        micro_penalty = round(target_bu["opex_base"] * 0.05, 2)
        target_bu["opex_base"] = round(target_bu["opex_base"] + micro_penalty, 2)
        events["micro_strike_applied"] = {
            "bu_id": target_bu["bu_id"],
            "opex_penalty": micro_penalty,
            "message": f"⚡ Localized disruption at {target_bu['bu_id']}: +${micro_penalty:,.0f} OPEX",
        }

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
        from admin_shared import _god_mode_settings
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

    # ── Emergency Credit Line: +$1M at prevailing rate + 2% ────
    # When the regular CSF pool is exhausted and max credit is utilised,
    # teams may opt-in to an additional $1M emergency credit at a premium.
    emergency_credit_interest = 0.0
    EMERGENCY_CREDIT_AMOUNT = 1_000_000
    if emergency_credit_used:
        base_loan_rate = current_global.get("active_event_flags", {}).get("loan_interest_rate", 0.12)
        emergency_rate = base_loan_rate + 0.02  # +2% premium
        emergency_credit_interest = round(EMERGENCY_CREDIT_AMOUNT * emergency_rate, 2)
        events["emergency_credit_used"] = True
        events["emergency_credit_amount"] = EMERGENCY_CREDIT_AMOUNT
        events["emergency_credit_rate"] = emergency_rate
        events["emergency_credit_interest"] = emergency_credit_interest

    if loan_principal > 0:
        loan_interest_rate = current_global.get("active_event_flags", {}).get("loan_interest_rate", 0.12)
        loan_interest_payment = round(loan_principal * loan_interest_rate, 2)
        events["loan_principal"] = round(loan_principal, 2)
        events["loan_interest_rate"] = loan_interest_rate
        events["loan_interest_payment"] = loan_interest_payment

    # Total interest = regular loan + emergency credit premium
    total_interest = loan_interest_payment + emergency_credit_interest

    # Treasury next round: Base + Operational Profit - All Interest Penalties
    new_treasury = round(base_treasury + csf - total_interest, 2)

    # ── REC-1: Waterfall entries for core treasury movement ─────
    _wf("Gross Profit (CSF)", csf,
        because="Revenue minus OPEX across all BUs, net of dividends paid.",
        counterfactual="Higher synergy investment would have reduced OPEX and increased CSF.")
    if loan_interest_payment > 0:
        _wf("Loan Interest", -loan_interest_payment,
            because=f"You borrowed ${loan_principal:,.0f} at {loan_interest_rate*100:.0f}% to fund CapEx exceeding free CSF.",
            counterfactual="If total CapEx stayed below CSF, no loan interest would be charged.")
    if emergency_credit_interest > 0:
        _wf("Emergency Credit Interest", -emergency_credit_interest,
            because=f"Emergency credit line of $1M activated at {events.get('emergency_credit_rate', 0)*100:.0f}% (prevailing rate + 2%).",
            counterfactual="Without the emergency credit line, this interest charge would not apply.")

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
            # Revenue generation projects (e.g. desalination payback)
            elif proj.get("type") == "revenue_generation":
                rev_amount = proj.get("amount", 0)
                new_treasury = round(new_treasury + rev_amount, 2)
                events["revenue_generation_completed"] = rev_amount
                events[f"revenue_generation_desc"] = proj.get("description", "Revenue Generation")
            # Education lag projects (SDG)
            elif proj.get("type") == "education_lag":
                events["education_lag_matured"] = proj.get("amount", 0)
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
        # ── Universal Burnout Passive Decay ──
        # All BUs experience natural burnout recovery through staff rotation.
        # HC BUs decay faster (−5/round) due to shift-based staffing.
        # NC/AC BUs decay slower (−2/round) — reflects corporate turnover cycle.
        current_burnout = bu.get("staff_burnout_index", 0.0)
        if bu["bu_id"] in ("hospitals", "clinics", "specialised_care", "telehealth"):
            # Healthcare: faster passive decay simulates shift rotation
            if current_burnout > 0:
                bu["staff_burnout_index"] = max(0.0, current_burnout - 10.0)
                events[f"burnout_passive_decay_{bu['bu_id']}"] = 10.0
        else:
            # NC/AC: slower passive decay prevents permanent burnout spirals
            if current_burnout > 0:
                bu["staff_burnout_index"] = max(0.0, current_burnout - 4.0)
                events[f"burnout_passive_decay_{bu['bu_id']}"] = 4.0

        if bu["bu_id"] in ("software", "hospitals", "clinics"):
            
            # Healthcare: Utilization Overload Fatigue
            if bu["bu_id"] in ("hospitals", "clinics"):
                utilization = bu.get("bed_capacity_utilization", 0.0)
                if utilization > 85.0:
                    bu["staff_burnout_index"] = min(100.0, bu.get("staff_burnout_index", 0.0) + 10.0)
                    events[f"utilization_overload_fatigue_{bu['bu_id']}"] = True

            # Healthcare: Logarithmic bed capacity utilization drift
            # Uses diminishing approach to 100%: Δ = (100 - current) × 0.05
            # At 50%: +2.5/round. At 80%: +1.0/round. At 95%: +0.25/round.
            # More realistic than linear — beds fill fast early, slow near capacity.
            if bu["bu_id"] in ("hospitals", "clinics"):
                current_util = bu.get("bed_capacity_utilization", 0.0)
                utilization_drift = round((100.0 - current_util) * 0.10, 2)
                bu["bed_capacity_utilization"] = min(100.0, round(current_util + utilization_drift, 2))
                events[f"bed_utilization_drift_{bu['bu_id']}"] = utilization_drift

            old_opex = bu["opex_base"]
            bu["opex_base"], talent_penalty = calc_talent_braindrain(
                bu["opex_base"], group_reputation, bu.get("staff_burnout_index", 0.0)
            )
            events[f"talent_penalty_applied_{bu['bu_id']}"] = talent_penalty
            # Mathematical transparency: show the OPEX impact of brain-drain
            if talent_penalty:
                events[f"braindrain_opex_impact_{bu['bu_id']}"] = {
                    "old_opex": old_opex,
                    "new_opex": bu["opex_base"],
                    "penalty_pct": round(((bu["opex_base"] - old_opex) / max(old_opex, 1)) * 100, 1),
                    "trigger": f"Group reputation ({group_reputation:.0f}) below brain-drain threshold (25)",
                }
            # Keep legacy single key for software if expected by dashboard
            if bu["bu_id"] == "software":
                events["talent_penalty_applied"] = talent_penalty

    # ── 4. Natural Capital Cost of Debt — per BU ────────────────
    interest_rates: dict[str, float] = {}
    corporate_cost_of_capital = current_global.get("cost_of_capital", 0.05)

    # ── FEATURE 21: Apply macro rate environment to CoC ──────────
    corporate_cost_of_capital = round(
        corporate_cost_of_capital + macro_rate["coc_modifier"], 4
    )
    events["coc_macro_rate_applied"] = macro_rate["coc_modifier"]

    # ── PHASE-1: ESG-Adjusted WACC — dynamic cost of capital ─────
    # Replaces static CoC with ESG-sensitive WACC (El Ghoul 2011)
    try:
        from systemic_risk_engine import calc_esg_adjusted_wacc, calc_supply_chain_transparency, calc_employer_brand, get_foreshadowing_for_round
        n_bu = max(len(new_bus), 1)
        _avg_ci = sum(bu.get("carbon_intensity", 50) for bu in new_bus) / n_bu
        _avg_gov = sum(bu.get("governance_risk_score", 20) for bu in new_bus) / n_bu
        _avg_slo = sum(bu.get("social_license_score", 50) for bu in new_bus) / n_bu
        _avg_water = sum(bu.get("water_dependency", 0) for bu in new_bus) / n_bu
        _sct = current_global.get("active_event_flags", {}).get("supply_chain_transparency", 30)

        esg_wacc, esg_wacc_diag = calc_esg_adjusted_wacc(
            corporate_cost_of_capital, _avg_ci, _avg_gov, _avg_slo, _avg_water, _sct
        )
        corporate_cost_of_capital = esg_wacc
        events["esg_adjusted_wacc"] = esg_wacc_diag

        # Update Supply Chain Transparency metric
        _sct_new, _sct_diag = calc_supply_chain_transparency(
            _sct, current_global.get("active_event_flags", {}), current_global["round_number"]
        )
        events["supply_chain_transparency"] = _sct_new
        events["supply_chain_transparency_diag"] = _sct_diag

        # Employer Brand Score
        _avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in new_bus) / n_bu
        _workforce_readiness = current_global.get("active_event_flags", {}).get("workforce_readiness", 50)
        _eb, _eb_diag = calc_employer_brand(group_reputation, _avg_burnout, _workforce_readiness)
        events["employer_brand"] = _eb_diag

        # ── Employer Brand OPEX Penalty (All BUs) ──
        # When employer brand score drops below 40, ALL BUs face recruitment cost
        # escalation: turnover increases, replacement hiring is expensive, and
        # institutional knowledge drains. This extends the talent flight mechanic
        # from Software/HC-only to the entire organisation.
        if _eb < 40:
            # Graded penalty: 0% at 40, max 8% at 0
            eb_opex_multiplier = round(((40 - _eb) / 40) * 0.08, 4)
            eb_total_penalty = 0.0
            for bu in new_bus:
                bu_opex = bu.get("opex_base", 0)
                penalty = round(bu_opex * eb_opex_multiplier, 2)
                bu["opex_base"] = round(bu_opex + penalty, 2)
                eb_total_penalty += penalty
            events["employer_brand_opex_penalty"] = {
                "multiplier": eb_opex_multiplier,
                "total_penalty": round(eb_total_penalty, 2),
                "employer_brand_score": _eb,
                "affected_bus": len(new_bus),
                "narrative": (
                    f"⚠️ TALENT CRISIS: Employer brand score has fallen to {_eb:.0f}/100. "
                    f"Recruitment costs surging across all divisions — "
                    f"${eb_total_penalty/1_000_000:.1f}M in additional OPEX."
                ),
            }

        # Foreshadowing Signals
        _foreshadowing = get_foreshadowing_for_round(
            current_global["round_number"], current_global.get("active_event_flags", {})
        )
        if _foreshadowing:
            events["foreshadowing_signals"] = _foreshadowing
    except ImportError:
        pass  # Graceful degradation if systemic_risk_engine not available
    
    # Stranded Asset Decay: Cost of Capital Spike
    if decision_paradigm == "advanced_climate":
        stranded_assets = [bu for bu in new_bus if bu.get("carbon_intensity", 0) > 120]
        if stranded_assets:
            corporate_cost_of_capital = round(corporate_cost_of_capital + 0.015, 4)
            events["stranded_asset_penalty_applied"] = True
            events["stranded_asset_bu_ids"] = [bu["bu_id"] for bu in stranded_assets]
            # Divestment Pressure: inbox event when stranded assets detected
            events["divestment_pressure_active"] = True
            events["divestment_pressure_message"] = (
                f"INVESTOR ALERT: {len(stranded_assets)} business unit(s) have carbon intensity "
                f"above 120 — classified as stranded assets by climate-aware investors. "
                f"Institutional shareholders are demanding a credible decarbonisation pathway "
                f"or forced divestiture. Cost of capital increased by +1.5%."
            )
    
    # If treasury is negative, deduct interest
    if new_treasury < 0:
        # Compute debt-service interest first (on the pre-clamp balance)
        debt_service = round(abs(new_treasury) * corporate_cost_of_capital, 2)
        new_treasury = round(new_treasury - debt_service, 2)
        # Prevent unbound negative geometry — hard floor AFTER interest (true absolute bound)
        new_treasury = max(new_treasury, -500_000_000.0)

        events["negative_treasury_interest_applied"] = debt_service
        events["negative_treasury_interest_because"] = (
            f"Your treasury is negative. Creditors charge {corporate_cost_of_capital*100:.1f}% "
            f"interest on the outstanding debt of ${abs(new_treasury):,.0f}."
        )
        _wf("Debt Service Interest", -debt_service,
            because=f"Negative treasury incurs {corporate_cost_of_capital*100:.1f}% interest on ${abs(new_treasury+debt_service):,.0f} debt.",
            counterfactual="A positive treasury eliminates debt servicing costs entirely.")

        # Insolvency mechanic: Red Card at -$100M
        if new_treasury < -100_000_000:
            events["insolvency_active"] = True
            events["insolvency_message"] = (
                "CREDIT DOWNGRADE: Treasury has breached -$100M. "
                "Mandatory austerity: all discretionary CapEx capped at 50%, "
                "dividend suspension in effect."
            )
            events["capex_cap_multiplier"] = 0.50
            events["dividend_suspended"] = True

    ncd_transparency: dict[str, dict] = {}
    for bu in new_bus:
        old_ncd = bu.get("natural_capital_debt", 0)
        rate = calc_natural_capital_interest(
            corporate_cost_of_capital,
            old_ncd,
        )
        interest_rates[bu["bu_id"]] = rate
        # Accrue a simple interest charge on the debt
        debt_charge = round(old_ncd * rate, 2)
        new_ncd = round(old_ncd + debt_charge, 2)
        # FIX VULN-007: Cap NCD at 1,000,000 to prevent float overflow
        bu["natural_capital_debt"] = min(new_ncd, 1_000_000)
        # HARD-001: NCD soft-cap warning at 500,000 (credit downgrade event)
        if bu["natural_capital_debt"] >= 500_000 and old_ncd < 500_000:
            events[f"ncd_credit_downgrade_{bu['bu_id']}"] = True
            events.setdefault("custom_black_swans", []).append({
                "title": f"\U0001f4c9 CREDIT DOWNGRADE: {bu['bu_id']} NCD Critical",
                "narrative": (
                    f"Natural Capital Debt for {bu['bu_id']} has reached "
                    f"${bu['natural_capital_debt']:,.0f} \u2014 50% of the hard cap. "
                    f"Investors are repricing ecological risk. Urgent NCD reduction "
                    f"required within 1\u20132 rounds to prevent environmental write-off."
                ),
                "icon": "\U0001f4c9",
                "severity": "critical",
            })
        # Mathematical transparency: show NCD compounding per BU
        ncd_transparency[bu["bu_id"]] = {
            "old_ncd": old_ncd,
            "interest_rate_pct": round(rate * 100, 2),
            "interest_charge": debt_charge,
            "new_ncd": bu["natural_capital_debt"],
        }
    events["interest_rates"] = interest_rates
    events["ncd_transparency"] = ncd_transparency

    # Toxic OPEX Penalty (Natural Capital Debt Multiplier)
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in new_bus) / max(len(new_bus), 1)
    hostility_multiplier = current_global.get("active_event_flags", {}).get("market_hostility_index", 5)
    tipping_tier = current_global.get("tipping_tier", "none")  # none/warning/stressed/tipped
    if decision_paradigm == "advanced_climate":
        # Graduated Tipping Point — 3-tier hostility escalation (replaces binary)
        # Tier 1 (warning):  hostility × 1.25 — early regulatory pressure
        # Tier 2 (stressed): hostility × 1.75 — significant market repricing
        # Tier 3 (tipped):   hostility × 2.50 — irreversible regime shift
        if tipping_tier == "tipped":
            hostility_multiplier = round(hostility_multiplier * 2.5, 2)
            events["tipping_tier_active"] = "tipped"
        elif tipping_tier == "stressed":
            hostility_multiplier = round(hostility_multiplier * 1.75, 2)
            events["tipping_tier_active"] = "stressed"
        elif tipping_tier == "warning":
            hostility_multiplier = round(hostility_multiplier * 1.25, 2)
            events["tipping_tier_active"] = "warning"
        # Legacy flag compat
        if current_global.get("tipping_point_active", False):
            if avg_ci < 50:
                events["tipping_point_managed_retreat"] = True

        # NCD Forgiveness: logarithmic curve (easy gains first, diminishing returns)
        # Formula: forgiveness = 2.0 × ln(1 + green_capex_M) — models ecological restoration
        total_green_capex = sum(d.get("capex_allocated", 0) for d in decisions)
        if total_green_capex > 0:
            import math
            green_capex_m = total_green_capex / 1_000_000
            forgiveness_per_bu = round(2.0 * math.log(1 + green_capex_m), 2)
            for bu in new_bus:
                old_ncd = bu.get("natural_capital_debt", 0)
                if old_ncd > 0 and forgiveness_per_bu > 0:
                    bu["natural_capital_debt"] = max(0, round(old_ncd - forgiveness_per_bu, 2))
            if forgiveness_per_bu > 0:
                events["ncd_forgiveness_applied"] = forgiveness_per_bu
                events["ncd_forgiveness_formula"] = "2.0 × ln(1 + CapEx_M$)"

        # CBAM Border Adjustment: supply chain rounds (R3, R7) face import surcharge
        # if avg CI remains high — models EU Carbon Border Adjustment Mechanism
        round_number = current_global.get("round_number", 1)
        if round_number in (2, 5) and avg_ci > 40:
            cbam_surcharge = round((avg_ci - 40) * 100_000, 2)  # $100K per CI point above 40
            new_treasury = round(new_treasury - cbam_surcharge, 2)
            events["cbam_surcharge_applied"] = cbam_surcharge
            events["cbam_message"] = (
                f"EU CBAM border adjustment: avg CI {avg_ci:.0f} exceeds 40 threshold. "
                f"Import carbon surcharge: -${cbam_surcharge:,.0f}"
            )

        for bu in new_bus:
            ncd = max(0, bu.get("natural_capital_debt", 0))
            ncd_opex_penalty = round((ncd * 50_000 * hostility_multiplier) / 1_000_000, 2)
            # Post-tipping: stricter cap at 75% revenue (was 50%) to make consequences dramatic
            if tipping_tier == "tipped":
                max_penalty = bu.get("revenue_base", 0) * 0.75
            else:
                max_penalty = bu.get("revenue_base", 0) * 0.50
            ncd_opex_penalty = min(ncd_opex_penalty, max_penalty)
            if ncd_opex_penalty > 0:
                bu["opex_base"] = round(bu["opex_base"] + ncd_opex_penalty, 2)
                events[f"{bu['bu_id']}_opex_ncd_penalty"] = ncd_opex_penalty

        # Scope 1/2/3 as ACTUAL BU state variables — DYNAMIC per-BU industry ratios
        # Real GHG Protocol profiles: manufacturing = high Scope 1, tech = high Scope 2,
        # consumer/electronics = high Scope 3 (supply chain dominant)
        _BU_SCOPE_RATIOS = {
            "pharma":         {"scope_1": 0.35, "scope_2": 0.25, "scope_3": 0.40},  # Chemical processes, lab energy
            "electronics":    {"scope_1": 0.10, "scope_2": 0.15, "scope_3": 0.75},  # Supply chain dominant
            "consumer_goods": {"scope_1": 0.15, "scope_2": 0.10, "scope_3": 0.75},  # Product lifecycle
            "software":       {"scope_1": 0.05, "scope_2": 0.60, "scope_3": 0.35},  # Data centre energy
            "hospitals":            {"scope_1": 0.25, "scope_2": 0.40, "scope_3": 0.35},  # HVAC, medical gases, intensive 24/7 power
            "clinics":              {"scope_1": 0.10, "scope_2": 0.50, "scope_3": 0.40},  # General electricity and supply chain
            "specialised_care":     {"scope_1": 0.20, "scope_2": 0.45, "scope_3": 0.35},  # Specialised equipment power and supply chain
            "telehealth":           {"scope_1": 0.05, "scope_2": 0.65, "scope_3": 0.30},  # Data centre and remote tech dominant
        }
        _DEFAULT_RATIOS = {"scope_1": 0.20, "scope_2": 0.15, "scope_3": 0.65}
        scope_details = {}
        for bu in new_bus:
            ci = bu.get("carbon_intensity", 0)
            ratios = _BU_SCOPE_RATIOS.get(bu["bu_id"], _DEFAULT_RATIOS)
            bu["scope_1_ci"] = round(ci * ratios["scope_1"], 2)
            bu["scope_2_ci"] = round(ci * ratios["scope_2"], 2)
            bu["scope_3_ci"] = round(ci * ratios["scope_3"], 2)
            scope_details[bu["bu_id"]] = {
                "scope_1_pct": round(ratios["scope_1"] * 100),
                "scope_2_pct": round(ratios["scope_2"] * 100),
                "scope_3_pct": round(ratios["scope_3"] * 100),
                "scope_1_ci": bu["scope_1_ci"],
                "scope_2_ci": bu["scope_2_ci"],
                "scope_3_ci": bu["scope_3_ci"],
            }
        events["scope_transparency"] = {
            "bu_scope_details": scope_details,
            "total_ci": round(avg_ci, 2),
            "note": "Scope 1/2/3 ratios are now DYNAMIC per BU industry profile (GHG Protocol)",
        }

        # EU Taxonomy Alignment Gate — % of revenue from taxonomy-aligned activities
        # Revenue from BUs with CI < 25 counts as taxonomy-aligned (simplified proxy)
        taxonomy_aligned_rev = sum(bu["revenue_base"] for bu in new_bus if bu.get("carbon_intensity", 100) < 25)
        total_rev = sum(bu["revenue_base"] for bu in new_bus) or 1
        taxonomy_pct = round((taxonomy_aligned_rev / total_rev) * 100, 1)
        events["eu_taxonomy_alignment_pct"] = taxonomy_pct
        # Taxonomy bonus: if > 60% aligned, reduce CoC by 0.5% (green finance discount)
        if taxonomy_pct > 60:
            events["taxonomy_green_finance_discount"] = True
            events["taxonomy_coc_benefit"] = -0.005
        # Taxonomy penalty: if < 20% aligned, CoC surcharge 0.5% (brown penalty)
        elif taxonomy_pct < 20:
            events["taxonomy_brown_penalty"] = True
            events["taxonomy_coc_surcharge"] = 0.005

        # Climate VaR — composite Value at Risk from physical + transition risk
        active_resilience = events.get("active_resilience_factor", 0.0)
        cyclone_prob = 0.75
        tipping_tier_local = current_global.get("tipping_tier", "none")
        if tipping_tier_local == "tipped": cyclone_prob = 0.90
        elif tipping_tier_local == "stressed": cyclone_prob = 0.85
        elif tipping_tier_local == "warning": cyclone_prob = 0.80
        physical_var = round(cyclone_prob * 12_000_000 * (1 - active_resilience), 2)
        stranded_exposure = sum(bu["revenue_base"] for bu in new_bus if bu.get("carbon_intensity", 0) > 80)
        
        # Calculate local carbon fee estimate for VaR
        base_fee = current_global.get("active_event_flags", {}).get("global_carbon_fee", 40)
        fee_per_ton = round(base_fee * (1 + 0.15) ** (current_global.get("round_number", 1) - 1), 2)
        local_tco2e = sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000 for bu in new_bus)
        local_carbon_fee = round(local_tco2e * fee_per_ton, 2)
        
        transition_var = round(stranded_exposure * 0.15 + local_carbon_fee * 5, 2)
        climate_var_total = round(physical_var + transition_var, 2)
        events["climate_var"] = {
            "physical_var": physical_var,
            "transition_var": transition_var,
            "total_var": climate_var_total,
            "physical_components": f"P(cyclone)={cyclone_prob:.0%} × $12M × (1-{active_resilience:.2f})",
            "transition_components": f"Stranded exposure: ${stranded_exposure:,.0f} + Carbon fee 5yr: ${local_carbon_fee*5:,.0f}",
        }

        # SBTi Pathway Validation — with multi-round history for dashboard visualization
        import math
        round_num = current_global.get("round_number", 1)
        sbti_target_ci = round(36.25 * (1 - 0.0822) ** (round_num - 1), 2)
        sbti_aligned = avg_ci <= sbti_target_ci
        # Build cumulative pathway history from previous rounds
        sbti_history = list(current_global.get("sbti_pathway_history", []))
        sbti_history.append({
            "round": round_num,
            "target_ci": sbti_target_ci,
            "actual_ci": round(avg_ci, 2),
            "aligned": sbti_aligned,
            "gap": round(avg_ci - sbti_target_ci, 2),
        })
        # Calculate consecutive aligned rounds for credibility score
        consecutive_aligned = 0
        for entry in reversed(sbti_history):
            if entry["aligned"]:
                consecutive_aligned += 1
            else:
                break
        events["sbti_pathway"] = {
            "target_ci": sbti_target_ci,
            "actual_ci": round(avg_ci, 2),
            "aligned": sbti_aligned,
            "consecutive_aligned_rounds": consecutive_aligned,
            "credibility_score": min(100, consecutive_aligned * 15),  # 15 pts per aligned round
            "history": sbti_history,
            "message": (
                f"SBTi 1.5°C target for R{round_num}: CI ≤ {sbti_target_ci:.1f}. "
                f"Actual: {avg_ci:.1f}. {'✅ ON TRACK' if sbti_aligned else '❌ OFF TRACK'}. "
                f"Credibility: {min(100, consecutive_aligned * 15)}%"
            ),
        }

        # Carbon Credit Futures Market — spot + forward contracts
        # Teams can "lock in" offset prices via forward contracts (3-round duration)
        # Forward premium: 20% above spot (insurance against volatility)
        if "carbon_deferred" in current_global.get("active_event_flags", {}):
            import random as _offset_rng
            # Spot market: base $500K ± 30% volatility
            spot_volatility = _offset_rng.uniform(-0.30, 0.30)
            spot_price = round(500_000 * (1 + spot_volatility), 2)
            # Check for active forward contracts
            active_forwards = list(current_global.get("carbon_forwards", []))
            forward_payment = 0
            remaining_forwards = []
            for fwd in active_forwards:
                if fwd["rounds_remaining"] > 0:
                    forward_payment += fwd["locked_price"]
                    remaining_fwd = dict(fwd)
                    remaining_fwd["rounds_remaining"] -= 1
                    if remaining_fwd["rounds_remaining"] > 0:
                        remaining_forwards.append(remaining_fwd)
            if forward_payment > 0:
                # Use forward contract price (locked in)
                offset_actual = forward_payment
                events["carbon_forward_used"] = True
                savings = spot_price - forward_payment
                events["carbon_forward_savings"] = savings
            else:
                # Pay spot price
                offset_actual = spot_price
            new_treasury = round(new_treasury - offset_actual, 2)
            # Offer new forward contract for next rounds
            forward_offer_price = round(500_000 * 1.20, 2)  # 20% premium
            events["carbon_offset_market"] = {
                "spot_price": spot_price,
                "spot_volatility_pct": round(spot_volatility * 100, 1),
                "actual_cost_paid": offset_actual,
                "forward_offer_price": forward_offer_price,
                "forward_duration": 3,
                "active_forwards": len(remaining_forwards),
                "message": (
                    f"Carbon Market: Spot ${spot_price:,.0f} ({spot_volatility*100:+.1f}%). "
                    f"Paid: ${offset_actual:,.0f}. "
                    f"Forward contract available: ${forward_offer_price:,.0f}/round for 3 rounds."
                ),
            }

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

    # ── CAROIC: Carbon-Adjusted Return on Invested Capital ───────
    # Uses the same carbon tonnage as terminal valuation for consistency.
    # Shadow carbon price defaults to $250/ton (aligned with R10 carbon tax).
    _shadow_carbon_price = current_global.get("active_event_flags", {}).get(
        "carbon_tax_per_ton",
        current_global.get("active_event_flags", {}).get("shadow_carbon_price", 250.0),
    )
    caroic_result = calc_caroic(
        ebitda=historical_ebitda,
        invested_capital=new_treasury,
        carbon_tonnage=tco2e_emissions,
        tax_rate=0.25,
        shadow_carbon_price=_shadow_carbon_price,
    )
    events["caroic"] = caroic_result

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
    # Fix #10: Always emit greenwashing diagnostics (transparent to players/facilitators)
    avg_inv_ratio = (
        sum(d.get("investment_ratio", 0) for d in decisions) / max(len(decisions), 1)
    )
    events["greenwashing_checked"] = True
    events["greenwashing_avg_investment_ratio"] = round(avg_inv_ratio, 4)
    events["greenwashing_threshold"] = 0.15
    events["greenwashing_risk_active"] = greenwash_hit
    if greenwash_hit:
        for bu in new_bus:
            bu["social_license_score"] = max(0.0, round(
                bu["social_license_score"] - greenwash_penalty, 2
            ))
        events["greenwashing_scandal"] = True
        events["greenwashing_penalty"] = greenwash_penalty
        events["greenwashing_message"] = (
            "Greenwashing scandal! Your green rhetoric doesn't match "
            "your actual investment allocation. Public trust plummets. "
            f"Avg investment ratio: {avg_inv_ratio:.1%} vs. required 15%."
        )
        events["greenwashing_because"] = (
            f"You chose a green option but allocated only {avg_inv_ratio:.1%} average "
            f"investment. The market requires ≥15% to back a green claim. "
            f"SLO penalty: −{greenwash_penalty:.0f} per BU."
        )
        events["greenwashing_counterfactual"] = (
            f"If you had allocated ≥15% average investment, this scandal "
            f"would not have fired. Alternatively, choosing a non-green option "
            f"avoids the greenwashing check entirely."
        )
    else:
        events["greenwashing_scandal"] = False
        events["greenwashing_message"] = (
            f"Greenwashing check passed. Avg investment ratio: {avg_inv_ratio:.1%} "
            f"({'above' if avg_inv_ratio >= 0.15 else 'below — no green option selected, hence no penalty'} "
            f"the 15% threshold)."
        )

    # ── FEATURE 25: Turnaround Pathway — 3-Act Distress Arc ─────
    already_survival = current_global.get("active_event_flags", {}).get("survival_mode", False)
    current_phase = current_global.get("active_event_flags", {}).get("turnaround_phase", "none")
    distress = detect_distress(
        new_treasury, group_reputation,
        current_global["round_number"], already_survival, current_phase,
    )
    events["distress_detection"] = distress
    events["turnaround_phase"] = distress.get("turnaround_phase", "none")

    if distress.get("distress_detected") and distress.get("bailout_amount"):
        bailout = distress["bailout_amount"]
        new_treasury = round(new_treasury + bailout, 2)
        events["survival_mode"] = True
        events["bailout_applied"] = bailout
        _wf("Emergency Bailout", bailout,
            because="Board-appointed Turnaround Manager activates emergency credit line.",
            counterfactual="Maintaining treasury > $0 and reputation > 30 prevents Survival Mode.")
        events.setdefault("custom_black_swans", []).append({
            "title": "🚨 CRISIS — Turnaround Manager Appointed",
            "narrative": distress["message"],
            "icon": "🚨",
            "severity": "critical",
        })
    elif distress.get("phase_transition"):
        # Phase transition within the turnaround arc
        events["survival_mode"] = distress.get("survival_mode", True)
        events.setdefault("custom_black_swans", []).append({
            "title": f"📋 TURNAROUND PHASE: {distress['turnaround_phase'].upper()}",
            "narrative": distress["message"],
            "icon": "📋" if distress["turnaround_phase"] != "exit" else "✅",
            "severity": "info" if distress.get("recovered") else "noteworthy",
        })
    elif distress.get("recovered"):
        events["survival_mode"] = False
        events.setdefault("custom_black_swans", []).append({
            "title": "✅ TURNAROUND COMPLETE — Comeback Achieved",
            "narrative": distress["message"],
            "icon": "✅",
            "severity": "info",
        })
    else:
        events["survival_mode"] = distress.get("survival_mode", False)

    # ── FEATURE 9: Regulatory Ratchet — cost_of_capital never drops ─
    historical_coc_max = current_global.get("active_event_flags", {}).get(
        "regulatory_floor_coc", current_global.get("cost_of_capital", 0.05)
    )
    if corporate_cost_of_capital < historical_coc_max:
        corporate_cost_of_capital = historical_coc_max
        events["regulatory_ratchet_active"] = True
    events["regulatory_floor_coc"] = max(historical_coc_max, corporate_cost_of_capital)

    # ── FEATURE 14: Fog of War — metric noise for undiscovered BUs ──
    fog_active = current_global.get("round_number", 1) <= 2
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

    # \u2500\u2500 HARD-004: Boundary Rounding Normalization \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # Final precision pass: round all financial fields to 2dp at the
    # persistence boundary to prevent floating-point drift over 10 rounds.
    for bu in new_bus:
        bu["revenue_base"] = round(bu["revenue_base"], 2)
        bu["opex_base"] = round(bu["opex_base"], 2)
        bu["natural_capital_debt"] = round(bu.get("natural_capital_debt", 0), 2)
        bu["social_license_score"] = round(bu.get("social_license_score", 50.0), 2)
        bu["governance_risk_score"] = round(bu.get("governance_risk_score", 20.0), 2)
        bu["carbon_intensity"] = round(bu.get("carbon_intensity", 50.0), 2)
        bu["reputation_score"] = round(bu.get("reputation_score", 50.0), 2)
        bu["staff_burnout_index"] = round(bu.get("staff_burnout_index", 0.0), 2)
    new_treasury = round(new_treasury, 2)
    new_green_fund_balance = round(new_green_fund_balance, 2)
    new_synergy = round(new_synergy, 4)

    # ── Internal Carbon Pricing — Escalating per Paris Ratchet ────
    # Base $40/ton escalating 32.25%/round (compounded from 15%/quarter × 2) to model Article 4 ratchet
    # R1:$40 → R3:$70 → R5:$122 → R7:$214 → R10:$495
    if decision_paradigm == "advanced_climate":
        base_carbon_fee = current_global.get("active_event_flags", {}).get("global_carbon_fee", 40)
        escalation_rate = 0.3225  # 32.25% per 6-month round (1.15² = 1.3225)
        round_number = current_global.get("round_number", 1)
        carbon_fee_per_ton = round(base_carbon_fee * (1 + escalation_rate) ** (round_number - 1), 2)
        round_carbon_fee_total = round(tco2e_emissions * carbon_fee_per_ton, 2)
        # Deduct from treasury and move to Green Fund
        new_treasury = round(new_treasury - round_carbon_fee_total, 2)
        new_green_fund_balance = round(new_green_fund_balance + round_carbon_fee_total, 2)
        events["internal_carbon_fee_per_ton"] = carbon_fee_per_ton
        events["internal_carbon_fee_deducted"] = round_carbon_fee_total
        events["internal_carbon_fee_because"] = (
            f"Internal carbon price of ${carbon_fee_per_ton:,.0f}/tCO₂e applied to "
            f"{tco2e_emissions:,.0f} tonnes total emissions. Fee escalates 32.25% per "
            f"6-month round under Paris Agreement ratchet mechanism."
        )
        _wf("Internal Carbon Fee", -round_carbon_fee_total,
            because=f"${carbon_fee_per_ton:,.0f}/tCO₂e × {tco2e_emissions:,.0f}t = ${round_carbon_fee_total:,.0f} transferred to Green Fund.",
            counterfactual="Reducing carbon intensity across BUs lowers this fee proportionally.")
        events["carbon_fee_escalation_message"] = (
            f"Internal carbon fee: ${carbon_fee_per_ton:.0f}/tCO2e "
            f"(base $40 × 1.15^{round_number-1}). Total levy: ${round_carbon_fee_total:,.0f}"
        )

    # ── Graduated Tipping Point — 3 tiers (replaces binary on/off) ──
    # Tier thresholds (avg CI): Warning > 45, Stressed > 55, Tipped > 65
    # Lowered from 50/60/70 to ensure procrastinator paths face consequences
    # Once a tier is reached, it NEVER drops back (hysteresis/ratchet)
    tipping_point_active = current_global.get("tipping_point_active", False)
    tipping_tier = current_global.get("tipping_tier", "none")
    if decision_paradigm == "advanced_climate" and current_global["round_number"] >= 3:
        # Tier 1: Warning (avg CI > 45)
        if tipping_tier == "none" and avg_ci > 45:
            tipping_tier = "warning"
            events["tipping_tier_escalated"] = "warning"
            events["custom_black_swans"] = events.get("custom_black_swans", []) + [{
                "title": "⚠️ CLIMATE WARNING THRESHOLD",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has exceeded 45. "
                    "Early warning: regulatory pressure is building. NCD costs "
                    "will increase by 25%. Decarbonise now or face escalating penalties."
                ),
                "icon": "⚠️",
                "severity": "warning",
            }]
        # Tier 2: Stressed (avg CI > 55)
        if tipping_tier == "warning" and avg_ci > 55:
            tipping_tier = "stressed"
            events["tipping_tier_escalated"] = "stressed"
            events["custom_black_swans"] = events.get("custom_black_swans", []) + [{
                "title": "🔶 CLIMATE STRESS THRESHOLD BREACHED",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has exceeded 55. "
                    "Markets are repricing climate risk. NCD costs compound at "
                    "1.75× hostility. The window for voluntary action is narrowing."
                ),
                "icon": "🔶",
                "severity": "high",
            }]
        # Tier 3: Tipped (avg CI > 65) — IRREVERSIBLE
        if tipping_tier in ("warning", "stressed") and avg_ci > 65:
            tipping_tier = "tipped"
            tipping_point_active = True
            events["tipping_point_reached"] = True
            events["tipping_tier_escalated"] = "tipped"
            events["custom_black_swans"] = events.get("custom_black_swans", []) + [{
                "title": "🌡️ CLIMATE TIPPING POINT BREACHED — IRREVERSIBLE",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has crossed the irreversible "
                    "threshold (65). Natural capital debt costs now compound at 2.5× the rate. "
                    "Loss & damage levies are now mandatory. The era of voluntary "
                    "decarbonisation is over — every future round amplifies the cost of inaction."
                ),
                "icon": "🌡️",
                "severity": "critical",
            }]
        # Also check direct entry to tipped (for backward compat)
        if not tipping_point_active and current_global["round_number"] >= 4 and avg_ci > 55:
            if tipping_tier == "none":
                tipping_tier = "stressed"
            tipping_point_active = True
            events["tipping_point_reached"] = True

        # ── Loss & Damage Levy — post-tipping mandatory contribution ──
        # Models UNFCCC Loss & Damage Fund (COP27/28)
        if tipping_tier == "tipped":
            loss_damage_levy = 4_000_000  # $4M/6-month round (doubled from quarterly $2M)
            new_treasury = round(new_treasury - loss_damage_levy, 2)
            events["loss_damage_levy_applied"] = loss_damage_levy
            events["loss_damage_message"] = (
                "UNFCCC Loss & Damage Fund contribution: -$4M. "
                "Post-tipping economies bear the cost of climate inaction "
                "through mandatory contributions to developing-economy adaptation."
            )
        elif tipping_tier == "stressed":
            loss_damage_levy = 1_000_000  # $1M/6-month round (doubled from quarterly $500K)
            new_treasury = round(new_treasury - loss_damage_levy, 2)
            events["loss_damage_levy_applied"] = loss_damage_levy
            events["loss_damage_message"] = (
                "Climate adaptation contribution: -$500K. "
                "Pre-tipping regulatory pressure mandates partial climate liability."
            )

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
        new_inflation_index = round(inflation_index + 0.010, 4)  # +1.0% per hostile 6-month round
        events["inflation_index_increased"] = new_inflation_index
        events["inflation_drift_hostile"] = True
        events["inflation_drift_message"] = (
            f"Hostile regulatory environment is driving inflation above baseline. "
            f"OPEX inflation increased to {new_inflation_index * 100:.1f}%."
        )

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

    # ── FEATURE 26: Predictive Forecast ────────────────────────────
    forecast = calc_forecast(current_global, new_bus)
    events["forecast"] = forecast

    # ── FEATURE 27: SDG Impact Report ────────────────────────────
    sdg_report = calc_sdg_impact(new_bus, events)
    events["sdg_impact"] = sdg_report

    # ── REC-1: Consequence Waterfall — finalize and attach ───────
    events["consequence_waterfall"] = {
        "initial_treasury": round(initial_treasury, 2),
        "final_treasury": round(new_treasury, 2),
        "net_change": round(new_treasury - initial_treasury, 2),
        "entries": waterfall,
        "entry_count": len(waterfall),
    }

    # ── REC-6: Momentum Score ────────────────────────────────────
    momentum_history = list(current_global.get("momentum_history", []))
    prev_states = current_global.get("_prev_global_states", [])
    momentum = calc_momentum_score(
        {"corporate_treasury": new_treasury, "group_reputation": group_reputation,
         "active_event_flags": events, "momentum_history": momentum_history},
        prev_states if prev_states else [current_global],
    )
    events["momentum"] = momentum
    momentum_history.append(momentum["momentum_score"])
    if len(momentum_history) > 10:
        momentum_history = momentum_history[-10:]

    # ── REC-8: Board Room Reflection Prompt ──────────────────────
    treasury_change_pct = abs(new_treasury - initial_treasury) / max(abs(initial_treasury), 1) * 100
    contagion_risk = forecast.get("contagion_risk_index", 0)
    is_midpoint = current_global["round_number"] == 5
    in_survival = events.get("survival_mode", False)

    reflection_trigger = None
    if treasury_change_pct > 20 and new_treasury < initial_treasury:
        # Treasury dropped > 20%
        top_causes = sorted(waterfall, key=lambda e: abs(e["amount"]))[:3]
        cause_lines = "\n".join(
            f"  {i+1}. {e['label']} ({'+' if e['amount']>0 else ''}${e['amount']:,.0f})"
            for i, e in enumerate(reversed(top_causes))
        )
        reflection_trigger = {
            "type": "treasury_drop",
            "severity": "critical",
            "prompt": (
                f"🪞 **Board Room Moment**\n"
                f"Your treasury dropped by {treasury_change_pct:.0f}% this round. "
                f"The three largest contributors were:\n{cause_lines}\n\n"
                f"**Before proceeding, your team must agree on one sentence:**\n"
                f"*\"The single most important thing we need to change next round is ___\"*"
            ),
        }
    elif in_survival and distress.get("phase_transition"):
        reflection_trigger = {
            "type": "survival_entry",
            "severity": "critical",
            "prompt": (
                f"🪞 **Board Room Moment — Emergency Session**\n"
                f"Your company has entered {distress.get('turnaround_phase', 'crisis')} phase. "
                f"The Turnaround Manager requires your team to answer:\n\n"
                f"**1.** What were the 2 decisions that led us here?\n"
                f"**2.** What is our single priority for the next round?\n"
                f"**3.** What metric must improve for us to advance to the next phase?"
            ),
        }
    elif is_midpoint:
        reflection_trigger = {
            "type": "midpoint_review",
            "severity": "noteworthy",
            "prompt": (
                f"🪞 **Midpoint Board Review — Round 5 of 10**\n"
                f"Half your journey is complete. Current position:\n"
                f"• Treasury: ${new_treasury:,.0f}\n"
                f"• Reputation: {group_reputation:.0f}\n"
                f"• Contagion Risk: {forecast.get('contagion_risk_label', 'Unknown')}\n"
                f"• SDG Grade: {sdg_report.get('sdg_grade', '?')}\n\n"
                f"**Your team must answer:** *\"If we could undo one decision from "
                f"Rounds 1-5, which would it be and why?\"*"
            ),
        }
    elif contagion_risk > 60:
        reflection_trigger = {
            "type": "contagion_warning",
            "severity": "material",
            "prompt": (
                f"🪞 **Board Room Moment — Risk Committee Alert**\n"
                f"Your Contagion Risk Index is {contagion_risk:.0f}/100 "
                f"({forecast.get('contagion_risk_label', '')}). "
                f"This is a composite of governance risk, SLO gaps, reputation erosion, "
                f"and carbon intensity.\n\n"
                f"**Your team must identify:** *\"Which single risk factor should we "
                f"prioritize reducing, and how?\"*"
            ),
        }

    if reflection_trigger:
        events["reflection_required"] = True
        events["reflection_prompt"] = reflection_trigger
    else:
        events["reflection_required"] = False

    # ── PHASE-1: Systemic Tipping Point Evaluation ────────────────
    systemic_tipping_state = {}
    try:
        from systemic_risk_engine import evaluate_tipping_points, evaluate_materiality_shocks
        _current_tipped = current_global.get("active_event_flags", {}).get("systemic_tipping_state", {})
        _tp_result = evaluate_tipping_points(current_global, new_bus, _current_tipped)
        systemic_tipping_state = _tp_result["tipping_state"]
        events["systemic_tipping"] = _tp_result
        if _tp_result["transitions"]:
            for trans in _tp_result["transitions"]:
                events.setdefault("custom_black_swans", []).append({
                    "title": f"⚠️ SYSTEMIC TIPPING — {trans['dimension'].upper()}",
                    "narrative": trans["message"],
                    "icon": "⚠️",
                    "severity": "critical",
                })
        # Materiality Shocks
        _session_tier_ms = current_global.get("active_event_flags", {}).get("difficulty_tier", "standard")
        _shocks = evaluate_materiality_shocks(current_global["round_number"], _session_tier_ms)
        if _shocks:
            events["materiality_shocks"] = _shocks
            for shock in _shocks:
                events.setdefault("custom_black_swans", []).append({
                    "title": f"📊 MATERIALITY SHOCK — {shock['issue']}",
                    "narrative": shock["narrative"],
                    "icon": "📊",
                    "severity": "critical",
                })
    except ImportError:
        pass

    # ── REAL-WORLD SCENARIO MECHANICS ────────────────────────────
    # 1. Regulatory Ratchet
    regulatory_baseline = 10.0 + (current_global["round_number"] // 2) * 5.0
    avg_gov_risk = sum(bu.get("governance_risk_score", 0) for bu in new_bus) / max(len(new_bus), 1)
    if avg_gov_risk > regulatory_baseline:
        fine = (avg_gov_risk - regulatory_baseline) * 500_000
        new_treasury -= fine
        events["regulatory_ratchet"] = {
            "active": True, 
            "baseline": regulatory_baseline, 
            "fine": fine,
            "message": f"⚖️ Regulatory Ratchet: Average governance risk ({avg_gov_risk:.1f}) exceeds the shifting industry baseline ({regulatory_baseline:.1f}). Compliance fine: ${fine:,.0f}."
        }
    else:
        events["regulatory_ratchet"] = {"active": False, "baseline": regulatory_baseline, "fine": 0}

    # 2. Supplier Defection & 3. Green Premium Squeeze
    supplier_defections = []
    green_premium_squeezes = []
    
    for dec in decisions:
        bu_id = dec["bu_id"]
        bu = next((b for b in new_bus if b["bu_id"] == bu_id), None)
        if not bu: continue
        
        inv_ratio = dec.get("investment_ratio", 0.0)
        
        # Supplier Defection (Check if strict mandate but low subsidy)
        pillar_decisions = dec.get("pillar_decisions", {})
        supply_chain_choice = pillar_decisions.get("supply_chain", "")
        if supply_chain_choice in ["audit_suppliers", "strict_mandates", "living_wage_mandate"] and inv_ratio < 0.15:
            bu["opex_base"] = round(bu["opex_base"] * 1.10, 2)  # 10% penalty
            bu["revenue_base"] = round(bu["revenue_base"] * 0.95, 2) # 5% stockout loss
            bu["supplier_defection_active"] = True
            supplier_defections.append(bu_id)
        else:
            bu["supplier_defection_active"] = False
            
        # Green Premium Squeeze (High cost pass-through but low social license)
        if inv_ratio > 0.25 and bu.get("social_license_score", 50) < 60:
            penalty_pct = (60 - bu["social_license_score"]) * 0.005 # 0.5% per point below 60
            penalty_val = round(bu["revenue_base"] * penalty_pct, 2)
            bu["revenue_base"] -= penalty_val
            bu["green_premium_squeeze"] = penalty_val
            green_premium_squeezes.append({"bu_id": bu_id, "penalty": penalty_val})
        else:
            bu["green_premium_squeeze"] = 0.0

    if supplier_defections:
        events["supplier_defection"] = {
            "active": True, 
            "affected_bus": supplier_defections,
            "message": f"🏭 Supplier Defection: You mandated strict supply chain ESG rules without providing financial subsidies (investment ratio < 15%) for {len(supplier_defections)} BU(s). Suppliers dropped you. +10% OPEX shock, -5% Revenue."
        }
    else:
        events["supplier_defection"] = {"active": False}

    if green_premium_squeezes:
        total_squeeze = sum(s["penalty"] for s in green_premium_squeezes)
        events["green_premium_squeeze"] = {
            "active": True, 
            "penalty": total_squeeze,
            "message": f"📉 Green Premium Squeeze: You invested heavily (>25%) but lacked the Social License (<60) to pass costs to consumers. The market rejected the premium pricing. Revenue lost: ${total_squeeze:,.0f}."
        }
    else:
        events["green_premium_squeeze"] = {"active": False}

    # 4. Valley of Death (CFO Austerity Trap)
    # Check if treasury is < 0 OR if the player took out a massive loan (exceeding 50% of base treasury) to fund CAPEX
    if new_treasury < 0 or loan_principal > base_treasury * 0.5:
        events["cfo_austerity_active"] = True
        events["cfo_austerity_message"] = "🛑 CFO Austerity Override: Heavy ESG investments drained free cash flow. The CFO has frozen all sustainability budgets for the next round."
    else:
        events["cfo_austerity_active"] = False

    # ── FIX-QA-005: Final bounds-clamping pass for all BU state variables ──
    # Prevents logic leaks where compound penalties (cannibalization, FX,
    # NCD penalties, talent surcharges) could push variables past logical bounds.
    for bu in new_bus:
        bu["revenue_base"] = max(0.0, bu.get("revenue_base", 0.0))
        bu["opex_base"] = max(0.0, bu.get("opex_base", 0.0))
        bu["reputation_score"] = max(0.0, min(100.0, bu.get("reputation_score", 50.0)))
        bu["social_license_score"] = max(0.0, min(100.0, bu.get("social_license_score", 50.0)))
        bu["natural_capital_debt"] = max(0.0, min(1_000_000, bu.get("natural_capital_debt", 0.0)))
        bu["carbon_intensity"] = max(0.0, bu.get("carbon_intensity", 0.0))
        bu["staff_burnout_index"] = max(0.0, min(100.0, bu.get("staff_burnout_index", 0.0)))

    # ── Assemble new immutable global state ─────────────────────
    new_global: dict[str, Any] = {
        "round_number": next_round,
        "corporate_treasury": new_treasury,
        "group_reputation": group_reputation,
        "synergy_multiplier": new_synergy,
        "cost_of_capital": corporate_cost_of_capital,
        "inflation_index": new_inflation_index,
        "competitor_ebitda": new_competitor,
        "green_transition_fund": max(0.0, new_green_fund_balance),
        "tipping_point_active": tipping_point_active,
        "tipping_tier": tipping_tier,
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
        "sbti_pathway_history": events.get("sbti_pathway", {}).get("history", []),
        "carbon_forwards": events.get("carbon_offset_market", {}).get("remaining_forwards", current_global.get("carbon_forwards", [])),
        "momentum_history": momentum_history,
        "_prev_global_states": (prev_states + [current_global])[-3:],
    }

    return {
        "global_state": new_global,
        "bu_states": new_bus,
        "events": events,
    }
