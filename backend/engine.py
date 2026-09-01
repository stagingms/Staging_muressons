"""
Muressons Global Corporation — Mathematical Engine
Pure-function module: no I/O, no database access.
All formulas operate on plain dicts and return new state dicts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import copy
import math
import random as _rng
from rng_util import event_rng, event_seed  # GAME-4: deterministic per-cohort RNG
from config import (
    ECONOMIC_CARBON_PRICE_BASE,
    ECONOMIC_CARBON_PRICE_GROWTH,
    CONSTRAINT_MAX_CARBON_EMISSIONS,
    CONSTRAINT_MIN_LIQUIDITY_RATIO,
    # Layer-2 Config Isolation: Financial
    FINANCIAL_SHADOW_CARBON_PRICE,
    FINANCIAL_CORPORATE_TAX_RATE,
    FINANCIAL_FREE_CSF_PCT,
    FINANCIAL_CAPEX_CAP_MULTIPLE,
    FINANCIAL_EMERGENCY_CREDIT_AMOUNT,
    FINANCIAL_DEFAULT_LOAN_RATE,
    FINANCIAL_EMERGENCY_RATE_SPREAD,
    FINANCIAL_INSOLVENCY_THRESHOLD,
    FINANCIAL_TREASURY_FLOOR,
    FINANCIAL_WACC_LENDER_THRESHOLD,
    # Layer-2 Config Isolation: NCD
    NCD_HARD_CAP,
    NCD_WARN_THRESHOLD,
    NCD_OPEX_SCALING_FACTOR,
    # Layer-2 Config Isolation: Climate
    CLIMATE_LOSS_DAMAGE_LEVY_TIPPED,
    CLIMATE_LOSS_DAMAGE_LEVY_STRESSED,
    # Layer-2 Config Isolation: Contagion
    CONTAGION_MAX_DROP,
    CONTAGION_MIDPOINT,
    CONTAGION_STEEPNESS,
    # Layer-2 Config Isolation: Engine magic numbers
    SYNERGY_DAMPENING_FACTOR, NCD_INTEREST_COEFFICIENT, NATURAL_DECAY_FACTOR,
    BURNOUT_NATURAL_DRIFT, BURNOUT_OPEX_THRESHOLD, BURNOUT_CRITICAL_THRESHOLD, BURNOUT_OPEX_PENALTY_COEFF,
    BURNOUT_PASSIVE_DECAY_HEALTHCARE, BURNOUT_PASSIVE_DECAY_DEFAULT,
    READINESS_DELTA_HIGH, READINESS_DELTA_MEDIUM, READINESS_DELTA_NONE,
    READINESS_LOW_THRESHOLD, READINESS_HIGH_THRESHOLD,
    BRAINDRAIN_REPUTATION_THRESHOLD, BRAINDRAIN_PENALTY_MULTIPLIER,
    BRAINDRAIN_BURNOUT_THRESHOLD, BRAINDRAIN_BURNOUT_OVERHEAD,
    OVERRUN_CAPEX_THRESHOLD, OVERRUN_DEFAULT_PROBABILITY, OVERRUN_DEFAULT_SEVERITY,
    TECH_DEBT_ROUNDS_THRESHOLD, TECH_DEBT_PENALTY_RATE,
    LOCKIN_ROUNDS_THRESHOLD, LOCKIN_PENALTY_RATE,
    STRIKE_SOCIAL_LICENSE_WEIGHT, COALITION_STRIKE_GAIN, CANNIBALIZATION_BASE_RATE, CANNIBALIZATION_AGGRESSOR_MULT,
    DIVIDEND_CUT_REP_PENALTY, DIVIDEND_CUT_THRESHOLD,
    TALENT_NEGLECT_THRESHOLD, TALENT_NEGLECT_PENALTY_RATE,
    STAKEHOLDER_FATIGUE_FACTOR, SUPPLY_CHAIN_OVERLAP_COEFF, COMPETITOR_GROWTH_RATE,
    GREENWASH_INVESTMENT_THRESHOLD, GREENWASH_SLO_PENALTY,
    GREENWASH_MODERATE_THRESHOLD_SCALE, GREENWASH_MODERATE_PENALTY_SCALE, GREENWASH_BU_REP_PENALTY,
    CASH_CONVERSION_GOV_DIVISOR, CASH_CONVERSION_EFFICIENCY_FLOOR,
    DSO_BASELINE_FACTOR, DSO_GOV_RISK_SCALING, DSO_MAX_CAP,
    MACRO_NOISE_INFLATION_BAND, MACRO_NOISE_CARBON_BAND,
    MICRO_STRIKE_PROBABILITY, MICRO_STRIKE_OPEX_RATE,
    FX_MOVEMENT_BAND, FX_DEFAULT_EXPOSURE,
    SBTI_BASELINE_CI, SBTI_ANNUAL_REDUCTION_RATE, SBTI_MISALIGNMENT_ROUNDS, SBTI_COC_SURCHARGE, SBTI_CREDIBILITY_PER_ROUND,
    EU_TAXONOMY_CI_THRESHOLD, EU_TAXONOMY_GREEN_THRESHOLD, EU_TAXONOMY_BROWN_THRESHOLD,
    EU_TAXONOMY_COC_BENEFIT, EU_TAXONOMY_COC_SURCHARGE,
    CBAM_CI_THRESHOLD, CBAM_SCOPE12_FRACTION, CBAM_SURCHARGE_RATE,
    REG_RATCHET_BASELINE, REG_RATCHET_ROUND_INCREMENT, REG_RATCHET_FINE_PER_POINT,
    SUPPLIER_DEFECTION_INV_THRESHOLD, SUPPLIER_DEFECTION_OPEX_MULT, SUPPLIER_DEFECTION_REV_MULT,
    CFO_AUSTERITY_LOAN_RATIO,
    EMISSIONS_BREACH_REP_PENALTY,
    STRANDED_ASSET_CI_THRESHOLD, STRANDED_ASSET_COC_SURCHARGE,
    TIPPING_HOSTILITY_TIPPED, TIPPING_HOSTILITY_STRESSED, TIPPING_HOSTILITY_WARNING,
    NCD_FORGIVENESS_LOG_COEFF,
    IMPLEMENTATION_LAG_INV_THRESHOLD,
    EMPLOYER_BRAND_PENALTY_THRESHOLD, EMPLOYER_BRAND_MAX_PENALTY_RATE,
    PATIENT_OUTCOMES_BASELINE, PATIENT_OUTCOMES_DIVISOR, PATIENT_OUTCOMES_MOD_MIN, PATIENT_OUTCOMES_MOD_MAX,
    UTILIZATION_OVERLOAD_THRESHOLD, UTILIZATION_OVERLOAD_BURNOUT_INC, UTILIZATION_DRIFT_RATE,
    DEFAULT_IMITATION_DECAY_RATE,
    SEVERITY_ROUTINE_CEILING, SEVERITY_NOTEWORTHY_CEILING, SEVERITY_MATERIAL_CEILING,
    SDG_GRADE_A_PLUS, SDG_GRADE_A, SDG_GRADE_B, SDG_GRADE_C, SDG_GRADE_D,
    CAROIC_GRADE_A_PLUS, CAROIC_GRADE_A, CAROIC_GRADE_B, CAROIC_GRADE_C,
    CRI_WEIGHT_GOV_RISK, CRI_WEIGHT_SLO_DEFICIT, CRI_WEIGHT_REP_DEFICIT, CRI_WEIGHT_CARBON,
    CRI_TIER_LOW, CRI_TIER_MODERATE, CRI_TIER_HIGH,
    MOMENTUM_WEIGHT_TREASURY, MOMENTUM_WEIGHT_REP, MOMENTUM_WEIGHT_NCD,
    MOMENTUM_HIGH_THRESHOLD, MOMENTUM_COMEBACK_MR_BONUS,
    MOMENTUM_TREASURY_NORM, MOMENTUM_REP_MULTIPLIER, MOMENTUM_NCD_MULTIPLIER,
    INSOLVENCY_WARNING_ROUNDS, TIME_TO_IMPACT_HORIZON,
    BRAINDRAIN_REP_THRESHOLD, STRIKE_WARNING_THRESHOLD, STRIKE_CRITICAL_THRESHOLD,
    CONTAGION_RISK_WARNING, TREASURY_DROP_REFLECTION_PCT,
    CYCLONE_PROB_BASE, CYCLONE_PROB_TIPPED, CYCLONE_PROB_STRESSED, CYCLONE_PROB_WARNING,
    PHYSICAL_VAR_DAMAGE_BASE,
    TIPPING_CI_WARNING, TIPPING_CI_STRESSED, TIPPING_CI_TIPPED,
    TRANSITION_VAR_CI_THRESHOLD, TRANSITION_VAR_STRANDED_MULT, TRANSITION_VAR_FEE_YEARS,
    TURNAROUND_CRISIS_ENTRY_TREASURY, TURNAROUND_CRISIS_ENTRY_REP, TURNAROUND_CRISIS_BAILOUT,
    TURNAROUND_CRISIS_CAPEX_CAP, TURNAROUND_CRISIS_MR_CAP,
    TURNAROUND_STAB_EXIT_TREASURY, TURNAROUND_STAB_EXIT_REP, TURNAROUND_STAB_CAPEX_CAP, TURNAROUND_STAB_MR_CAP,
    TURNAROUND_RECOVERY_EXIT_TREASURY, TURNAROUND_RECOVERY_EXIT_REP, TURNAROUND_RECOVERY_CAPEX_CAP, TURNAROUND_RECOVERY_MR_CAP,
    TURNAROUND_EXIT_TREASURY, TURNAROUND_EXIT_REP, TURNAROUND_EXIT_MR_BONUS,
    TURNAROUND_ARC_MAX_ROUNDS, TURNAROUND_ARC_MR_THRESHOLD, TURNAROUND_ARC_ENTRY_BAILOUT,
)




# ═══════════════════════════════════════════════════════════════
#  CARBON ACCOUNTING HELPERS  (I1, I2, I3, I5, I13, I15)
#  Centralised carbon calculation utilities used throughout the engine.
#
#  carbon_intensity units: tCO₂e per $1M revenue (I1)
#  Group tonnage formula: Σ(CI × revenue_base / 1_000_000)  [units: tCO₂e]
# ═══════════════════════════════════════════════════════════════

# I5 — Scope 1/2/3 ratios for ALL BU types (GHG Protocol aligned)
# Format: {bu_id: {scope_1: float, scope_2: float, scope_3: float}}  (must sum to 1.0)
# Used for scope decomposition AND scope-weighted CI delta routing (I2, I13).
_ALL_BU_SCOPE_RATIOS: dict[str, dict[str, float]] = {
    # ─ Default 4 BUs ──────────────────────────────────────────────
    "pharma":          {"scope_1": 0.35, "scope_2": 0.25, "scope_3": 0.40},
    "electronics":     {"scope_1": 0.10, "scope_2": 0.15, "scope_3": 0.75},
    "consumer_goods":  {"scope_1": 0.15, "scope_2": 0.10, "scope_3": 0.75},
    "software":        {"scope_1": 0.05, "scope_2": 0.60, "scope_3": 0.35},
    # ─ Industry Verticals (I5) ───────────────────────────────────
    # Oil & Gas: Scope 1 dominant — combustion, flaring, fugitive methane
    "oil_gas":                    {"scope_1": 0.65, "scope_2": 0.15, "scope_3": 0.20},
    # Banking: Scope 3 dominant — financed emissions (PCAF, ESRS E1 AR40)
    "banking_financial_services": {"scope_1": 0.01, "scope_2": 0.04, "scope_3": 0.95},
    # Retail/FMCG: Scope 3 dominant — product lifecycle, consumer use
    "retail_fmcg":                {"scope_1": 0.10, "scope_2": 0.15, "scope_3": 0.75},
    # Agriculture: Scope 1 dominant — enteric fermentation (CH4), soil N₂O
    "agriculture":                {"scope_1": 0.70, "scope_2": 0.10, "scope_3": 0.20},
    # Technology: Scope 2 dominant — data centre grid electricity
    "technology":                 {"scope_1": 0.05, "scope_2": 0.55, "scope_3": 0.40},
    # ─ Healthcare verticals ─────────────────────────────────────
    "hospitals":        {"scope_1": 0.25, "scope_2": 0.40, "scope_3": 0.35},
    "clinics":          {"scope_1": 0.10, "scope_2": 0.50, "scope_3": 0.40},
    "specialised_care": {"scope_1": 0.20, "scope_2": 0.45, "scope_3": 0.35},
    "telehealth":       {"scope_1": 0.05, "scope_2": 0.65, "scope_3": 0.30},
}
_DEFAULT_SCOPE_RATIOS: dict[str, float] = {"scope_1": 0.20, "scope_2": 0.15, "scope_3": 0.65}


def get_scope_ratios(bu_id: str) -> dict[str, float]:
    """I5: Return GHG Protocol scope ratios for a BU, with fallback to default."""
    return _ALL_BU_SCOPE_RATIOS.get(bu_id, _DEFAULT_SCOPE_RATIOS)


def calc_revenue_weighted_avg_ci(bus: list[dict]) -> float:
    """
    I3 — Revenue-weighted average carbon intensity.
    Replaces the previous simple arithmetic mean, which flatters the group
    profile when a large high-CI BU is present.

    Formula: avg_CI = Σ(CI_i × Rev_i) / Σ(Rev_i)
    Units: tCO₂e per $1M revenue (matches carbon_intensity field).
    Falls back to simple mean if all revenues are zero.
    """
    total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
    if total_rev <= 0:
        n = max(len(bus), 1)
        return sum(bu.get("carbon_intensity", 0) for bu in bus) / n
    return sum(
        bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) for bu in bus
    ) / total_rev


def _calc_rw_avg_ci(bus: list[dict]) -> float:
    """I3: Concise internal alias for revenue-weighted avg CI."""
    total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
    if total_rev <= 0:
        n = max(len(bus), 1)
        return sum(bu.get("carbon_intensity", 0) for bu in bus) / n
    return sum(
        bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) for bu in bus
    ) / total_rev


# ── CIDeltaResult: typed return value for the pure CI-delta helper ──
from dataclasses import dataclass, field as dc_field


@dataclass(frozen=True)
class CIDeltaResult:
    """
    Pure-function return type for apply_ci_delta_to_bus().

    applied_deltas        — {bu_id: effective_delta_applied}   (for event logging)
    new_carbon_intensities — {bu_id: new_ci_value}             (caller applies to state)

    The input `bus` list is NEVER mutated.  Caller is responsible for
    writing new_carbon_intensities back to their own BU state dicts.
    """
    applied_deltas: dict[str, float]
    new_carbon_intensities: dict[str, float]


def apply_ci_delta_to_bus(
    bus: list[dict],
    ci_delta: float,
    routing: str = "uniform",
) -> CIDeltaResult:
    """
    I2/I13 — PURE FUNCTION. Computes carbon_intensity deltas per BU with
    optional Scope 3-weighted routing. Does NOT mutate the input list.

    routing="uniform"         — identical delta to every BU (legacy behaviour)
    routing="scope3_weighted" — delta scales by (0.5 + scope_3_ratio) per BU:
        - High-Scope3 BU (electronics 0.75): factor = 1.25 × delta
        - Low-Scope3 BU (oil_gas 0.20):      factor = 0.70 × delta
        - Default BU (0.65):                 factor = 1.15 × delta
    For positive deltas (emission increase), uses (0.5 + scope_1_ratio)
    so direct emitters (agriculture, oil_gas) bear more of the burden.

    Returns CIDeltaResult with:
        applied_deltas         — {bu_id: effective_delta}   (for transparency events)
        new_carbon_intensities — {bu_id: new_ci}            (caller must apply to state)

    Caller pattern:
        result = apply_ci_delta_to_bus(bus, ci_delta)
        for bu in bus:
            if bu["bu_id"] in result.new_carbon_intensities:
                bu["carbon_intensity"] = result.new_carbon_intensities[bu["bu_id"]]
    """
    applied: dict[str, float] = {}
    new_cis: dict[str, float] = {}
    for bu in bus:
        bu_id = bu.get("bu_id", "")
        if routing == "scope3_weighted":
            ratios = get_scope_ratios(bu_id)
            if ci_delta < 0:
                # Emission reduction: Scope3-heavy BUs benefit most
                factor = round(0.5 + ratios["scope_3"], 3)
            else:
                # Emission increase: Scope1-heavy BUs bear most
                factor = round(0.5 + ratios["scope_1"], 3)
            effective = round(ci_delta * factor, 2)
        else:
            effective = ci_delta
        old_ci = bu.get("carbon_intensity", 0.0)
        new_cis[bu_id] = max(0.0, round(old_ci + effective, 2))
        applied[bu_id] = effective
    return CIDeltaResult(applied_deltas=applied, new_carbon_intensities=new_cis)


def apply_ci_delta_in_place(bus: list[dict], ci_delta: float,
                            routing: str = "uniform") -> dict[str, float]:
    """Convenience wrapper both real call sites actually wanted.

    BUG-2026-07-20 (round 7 stall): both callers of the PURE helper above —
    round_logic._apply_option_impacts and side_tracks.base_track — treated it
    like the old mutating version. Two consequences:
      1. new_carbon_intensities was never written back, so option-driven CI
         deltas were silently DROPPED whenever the real engine was importable
         (the test-context fallback shim mutates, masking this in some suites).
      2. The raw CIDeltaResult dataclass was stored into active_event_flags.
         The memory store's serializer tolerates dataclasses; Postgres
         json.dumps does not → "Failed to persist round: Object of type
         CIDeltaResult is not JSON serializable" at scope3_weighted rounds
         (R3/R7), stalling the cohort.

    This wrapper applies the new CIs to `bus` and returns a PLAIN dict of
    applied deltas — safe to store in flags on every backend.
    """
    result = apply_ci_delta_to_bus(bus, ci_delta, routing=routing)
    for bu in bus:
        bu_id = bu.get("bu_id", "")
        if bu_id in result.new_carbon_intensities:
            bu["carbon_intensity"] = result.new_carbon_intensities[bu_id]
    return dict(result.applied_deltas)


# ── Data Bridge State Applicator ────────────────────────────────────────────
# PURE FUNCTION — never mutates the input `state` dict.
# Enforces the Delta vs Override contract for DataBridgeOutput payloads.
#
# Contract (immutable order of operations):
#   STEP 1 — Apply kpi_deltas  (additive math)
#   STEP 2 — Apply kpi_overrides (absolute assignments), overwriting delta
#             results ONLY where the override field is not None.
#
# Mapping: DataBridgeOutput field  →  main-sim global_state key
# ─────────────────────────────────────────────────────────────────────────────
_KPI_DELTA_MAP: dict[str, str] = {
    "treasury_delta":          "corporate_treasury",
    "reputation_delta":        "group_reputation",
    "carbon_intensity_delta":  "avg_carbon_intensity",
    "ncd_delta":               "total_ncd",
    "governance_risk_delta":   "avg_governance_risk",
    "social_license_delta":    "avg_social_license",
}

_KPI_OVERRIDE_MAP: dict[str, str] = {
    "corporate_treasury":   "corporate_treasury",
    "group_reputation":     "group_reputation",
    "avg_carbon_intensity": "avg_carbon_intensity",
    "total_ncd":            "total_ncd",
    "synergy_multiplier":   "synergy_multiplier",
    "group_social_license": "avg_social_license",
}

# Bounds for clamping after write (matches engine invariants)
_KPI_BOUNDS: dict[str, tuple[float, float]] = {
    "group_reputation":    (0.0,   100.0),
    "avg_governance_risk": (0.0,   100.0),
    "avg_social_license":  (0.0,   100.0),
    "avg_carbon_intensity":(0.0,   float("inf")),
    "total_ncd":           (0.0,   float("inf")),
    "corporate_treasury":  (float("-inf"), float("inf")),
    "synergy_multiplier":  (0.0,   float("inf")),
}


def apply_side_track_results(
    state: dict[str, Any],
    payload: "DataBridgeOutput",          # noqa: F821 — forward ref; import below
    *,
    apply_flags: bool = True,
) -> dict[str, Any]:
    """
    PURE FUNCTION — Data Bridge state applicator.

    Applies a DataBridgeOutput payload to ``state`` and returns a CLEAN COPY
    of the updated state.  The original ``state`` dict is NEVER mutated.

    Order of operations (strictly enforced):
        1. Deep-copy ``state`` to produce ``new_state``.
        2. Apply ``payload.kpi_deltas`` (additive): new_state[key] += delta.
        3. Apply ``payload.kpi_overrides`` (absolute): new_state[key] = value
           for every non-None override field.
        4. Clamp all written KPIs to their engine-defined bounds.
        5. If ``apply_flags`` is True, merge ``payload.flags_to_set`` into
           ``new_state["active_event_flags"]`` and process ``flags_to_remove``.

    Args:
        state        : Current main-sim global_state dict (read-only source).
        payload      : Validated DataBridgeOutput from a completing side track.
        apply_flags  : If False, skip flag merging (useful for KPI-only tests).

    Returns:
        A new dict — a modified copy of ``state``.  Never the same object.

    Raises:
        TypeError  : If ``payload`` is not a DataBridgeOutput instance.
    """
    # Lazy import to avoid circular dependency at module-parse time.
    # engine.py ← bridge_schemas.py would be circular if at top-level.
    from side_tracks.bridge_schemas import DataBridgeOutput as _DBO  # noqa: F401

    if not isinstance(payload, _DBO):
        raise TypeError(
            f"apply_side_track_results expects DataBridgeOutput, got {type(payload).__name__}"
        )

    # STEP 0: Deep-copy — pure function guarantee
    new_state: dict[str, Any] = copy.deepcopy(state)

    # ── STEP 1: Apply kpi_deltas (additive) ──────────────────────────────────
    deltas = payload.kpi_deltas.model_dump()
    for delta_field, state_key in _KPI_DELTA_MAP.items():
        delta_val = deltas.get(delta_field, 0.0)
        if delta_val == 0.0:
            continue  # no-op; skip to keep state clean
        current = new_state.get(state_key, 0.0)
        if current is None:
            current = 0.0
        new_state[state_key] = round(current + delta_val, 6)

    # ── STEP 2: Apply kpi_overrides (absolute assignment, non-None only) ─────
    overrides = payload.kpi_overrides.model_dump()
    for override_field, state_key in _KPI_OVERRIDE_MAP.items():
        override_val = overrides.get(override_field)
        if override_val is None:
            continue  # None = "no opinion" — leave the delta result intact
        new_state[state_key] = override_val

    # ── STEP 3: Clamp all written KPIs to engine-invariant bounds ────────────
    all_written_keys = set(_KPI_DELTA_MAP.values()) | set(_KPI_OVERRIDE_MAP.values())
    for state_key in all_written_keys:
        if state_key not in new_state:
            continue
        lo, hi = _KPI_BOUNDS.get(state_key, (float("-inf"), float("inf")))
        val = new_state[state_key]
        if isinstance(val, (int, float)):
            new_state[state_key] = round(max(lo, min(hi, val)), 6)

    # ── STEP 4: Flag merging (optional) ──────────────────────────────────────
    if apply_flags:
        flags = new_state.setdefault("active_event_flags", {})
        flags.update(payload.flags_to_set)
        for key in payload.flags_to_remove:
            flags.pop(key, None)

    return new_state


# ── 1. Corporate Strategic Fund (CSF) ────────────────────────────
def calc_csf(bu_states: list[dict], dividends_paid: float) -> float:
    """
    CSF = Σ(Revenue_Base - OPEX_Base) - Dividends_Paid
    Returns the net cash added to the corporate treasury this round.
    """
    gross_profit = sum(bu["revenue_base"] - bu["opex_base"] for bu in bu_states)
    return gross_profit - dividends_paid


# ── 2. Contagion Engine (Sigmoid Model) ──────────────────────────
def calc_contagion(
    bu_states: list[dict],
    crisis_severity: float,
    *,
    max_drop:   float = CONTAGION_MAX_DROP,
    midpoint:   float = CONTAGION_MIDPOINT,
    steepness:  float = CONTAGION_STEEPNESS,
) -> float:
    """
    Pure function: Sigmoid contagion model mapping crisis_severity → group reputation.

    Uses an S-curve centred at `midpoint` (default 30) to model realistic crisis
    propagation without cliff-edge discontinuities:

        sigmoid_input = (crisis_severity − midpoint) / steepness
        sigmoid_value = 1 / (1 + e^(−sigmoid_input))
        group_rep     = avg_rep − max_drop × sigmoid_value

    Behaviour by severity tier (defaults):
        < 15  — minimal impact   (sigmoid ≈ 0.07 → drop ≤ 3.5 pts)
        = 30  — inflection point (sigmoid = 0.50 → drop = 25 pts)
        > 50  — saturating harm  (sigmoid ≈ 0.88 → drop ≤ 44 pts)

    Parameters
    ----------
    bu_states       : list of BU state dicts, each containing "reputation_score".
    crisis_severity : Raw crisis severity score in [0, 100]. Clamped to ≥ 0.
    max_drop        : Maximum reputation points erasable at sigmoid saturation.
                      Sourced from CONTAGION_MAX_DROP (config-routed).
    midpoint        : Severity at which 50% of max_drop is applied.
                      Sourced from CONTAGION_MIDPOINT (config-routed).
    steepness       : Sigmoid denominator — controls S-curve slope.
                      Smaller ⇒ steeper. Sourced from CONTAGION_STEEPNESS.

    Returns
    -------
    float : New group reputation clamped to [0.0, 100.0].

    Safety
    ------
    - ZeroDivisionError: guarded by empty bu_states check (returns 50.0).
    - OverflowError: guarded by try/except around math.exp(); extreme negative
      sigmoid inputs (very low severity) floor sigmoid_value to 0.0, extreme
      positive inputs (very high severity) ceil to 1.0.
    - Negative reputation: floored at 0.0 after computation.
    - Steepness = 0: guarded; treated as steepness = 1.0 to prevent ZeroDivisionError.
    """
    # Guard: non-negative severity
    crisis_severity = max(0.0, crisis_severity)

    # Guard: empty BU list → neutral default
    if not bu_states:
        return 50.0

    avg_rep: float = sum(bu["reputation_score"] for bu in bu_states) / len(bu_states)

    # Guard: steepness == 0 would cause ZeroDivisionError
    safe_steepness: float = steepness if steepness != 0.0 else 1.0

    sigmoid_input: float = (crisis_severity - midpoint) / safe_steepness

    # Guard: math.exp() overflows for large positive inputs
    try:
        sigmoid_value: float = 1.0 / (1.0 + math.exp(-sigmoid_input))
    except OverflowError:
        # exp(-sigmoid_input) overflows when sigmoid_input is very large negative
        # (i.e. crisis_severity << midpoint) → e^∞ → sigmoid → 0.0
        # For very large positive sigmoid_input → e^(-∞) → sigmoid → 1.0
        sigmoid_value = 0.0 if sigmoid_input < 0 else 1.0

    rep_drop: float  = max_drop * sigmoid_value
    group_rep: float = avg_rep - rep_drop

    # Floor at 0.0: reputation cannot go negative
    return round(max(0.0, min(100.0, group_rep)), 2)


# ── 3. Synergy Engine (with Diminishing Returns) ────────────────
# BALANCE FIX (Risk-Radar authenticity audit, 2026-07-18): calc_synergy_opex
# applies its efficiency factor as a COMPOUNDING multiplier every round with no
# floor, so any sustained investment ratcheted opex toward zero by late game
# (real dev sessions hit ₹13K opex on ₹7.5M revenue → ~100% margins, inflated
# EBITDA/valuation, and Risk Radar bubbles pinned to the left axis). Synergy
# reductions now floor at this fraction of the BU's FIRST-SEEN opex baseline —
# "you still have to run the business." The baseline is stamped into
# risk_factors (the JSON catch-all persisted by both DB backends), so sessions
# already below the floor keep their current value but stop falling.
SYNERGY_OPEX_FLOOR_FRACTION = 0.35


def synergy_opex_floor(bu: dict) -> float:
    """Absolute opex floor for synergy reductions on this BU (35% of the
    first opex this helper ever saw for it — stamped on first use)."""
    rf = bu.setdefault("risk_factors", {})
    base = rf.get("initial_opex_base")
    if not base or base <= 0:
        base = float(bu.get("opex_base", 0.0) or 0.0)
        rf["initial_opex_base"] = base
    return round(base * SYNERGY_OPEX_FLOOR_FRACTION, 2)


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
    effective_ratio = math.sqrt(ratio) * SYNERGY_DAMPENING_FACTOR
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
    return round(base_rate + (natural_capital_debt * NCD_INTEREST_COEFFICIENT), 6)


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
    natural_drift: float = BURNOUT_NATURAL_DRIFT,
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
        "opex_penalty_active": new_burnout > BURNOUT_OPEX_THRESHOLD,
        "critical_burnout": new_burnout > BURNOUT_CRITICAL_THRESHOLD,
    }

    # Calculate OPEX penalty rate (graded quadratic curve from 20 onwards)
    if new_burnout > BURNOUT_OPEX_THRESHOLD:
        # Smooth quadratic curve: 0% at 20 -> 18% at 100
        # Formula maintains same maximum penalty but removes the hard cliff
        penalty_rate = round(((new_burnout - BURNOUT_OPEX_THRESHOLD) ** 2) * BURNOUT_OPEX_PENALTY_COEFF, 4)
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
        delta = READINESS_DELTA_HIGH
    elif hr_quality_tier == "medium":
        delta = READINESS_DELTA_MEDIUM
    else:
        delta = READINESS_DELTA_NONE  # skills atrophy (6-month period)

    new_readiness = round(max(0.0, min(100.0, current_readiness + delta)), 2)

    diagnostics = {
        "previous_readiness": round(current_readiness, 2),
        "readiness_delta": delta,
        "hr_quality_tier": hr_quality_tier,
        "new_readiness": new_readiness,
        "low_readiness_penalty": new_readiness < READINESS_LOW_THRESHOLD,
        "high_readiness_bonus": new_readiness > READINESS_HIGH_THRESHOLD,
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
    penalty = 1.0 + max(0.0, (BRAINDRAIN_REPUTATION_THRESHOLD - group_reputation) / 100.0) * BRAINDRAIN_PENALTY_MULTIPLIER
    
    # Scale OPEX up aggressively if the unit is suffering severe staff burnout
    if burnout_index > BRAINDRAIN_BURNOUT_THRESHOLD:
        penalty += ((burnout_index - BRAINDRAIN_BURNOUT_THRESHOLD) / 100.0) * BRAINDRAIN_BURNOUT_OVERHEAD  # agency/locum overhead

    new_opex = round(opex_base * penalty, 2)
    return new_opex, round(penalty, 4)


# ── 7. Strike Probability Engine ────────────────────────────────
def calc_strike_probability(
    base_risk: float,
    social_license: float,
    coalition_multiplier: float = 1.0,
) -> float:
    """
    P_Strike = Base_Risk + ((1 - (Social_License / 100)) * 0.4 * coalition_multiplier)
    Result is clamped to [0.0, 1.0].

    `coalition_multiplier` (SPEC F3) defaults to 1.0 (no coalition) so every
    existing caller is unchanged; a coalition passes (1 + coalition_pressure·k)
    to make hostile social license bite harder.
    """
    p = base_risk + ((1.0 - (social_license / 100.0)) * STRIKE_SOCIAL_LICENSE_WEIGHT * coalition_multiplier)
    return max(0.0, min(1.0, round(p, 4)))


# ── 8. Natural Decay ────────────────────────────────────────────
def apply_natural_decay(
    reputation: float,
    social_license: float,
    invested: bool,
    investment_ratio: float = 0.0,
) -> tuple[float, float]:
    """
    FIX-B: Gradated SLO/reputation decay based on investment_ratio.
    - investment_ratio >= 0.30 → SLO GROWS by +3/round (community rewards ESG)
    - investment_ratio >= 0.15 → No decay (treading water)
    - investment_ratio <  0.15 → Full 4% decay (neglect erodes trust)
    Reputation always decays when not invested (harder to rebuild brand).
    """
    decay = NATURAL_DECAY_FACTOR  # ~0.96
    if investment_ratio >= 0.30:
        # Active ESG commitment → SLO grows, reputation stabilises
        slo_growth = 3.0 + (investment_ratio - 0.30) * 10  # +3 to +10
        return (
            reputation,  # reputation stable
            round(min(100.0, social_license + slo_growth), 2),
        )
    elif investment_ratio >= 0.15 or invested:
        # Moderate investment → treading water (no decay, no growth)
        return reputation, social_license
    else:
        # Neglect → full decay
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
    threshold: float = OVERRUN_CAPEX_THRESHOLD,
    overrun_probability: float = OVERRUN_DEFAULT_PROBABILITY,
    overrun_severity: float = OVERRUN_DEFAULT_SEVERITY,
    rng: "_rng.Random | None" = None,
) -> tuple[bool, float]:
    """
    FEATURE 3 — Execution Overrun Risk:
    If CAPEX exceeds threshold, there is a stochastic chance of
    a cost overrun that silently drains extra capital.

    GAME-4: pass a seeded `rng` (per-cohort) so all teams face the same roll.
    Falls back to the module RNG when none is supplied.

    Returns (overrun_triggered: bool, overrun_amount: float).
    """
    if capex <= threshold:
        return False, 0.0
    roll = (rng or _rng).random()
    if roll < overrun_probability:
        overrun = round(capex * overrun_severity, 2)
        return True, overrun
    return False, 0.0


# ── 11. Technical Debt Engine ───────────────────────────────────
def calc_technical_debt(
    opex: float,
    consecutive_zero_rounds: int,
    penalty_threshold: int = TECH_DEBT_ROUNDS_THRESHOLD,
    penalty_rate: float = TECH_DEBT_PENALTY_RATE,
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
    rate: float = CANNIBALIZATION_BASE_RATE,
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
        if aggressor_rev <= avg_rev * CANNIBALIZATION_AGGRESSOR_MULT:
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
    fatigue_factor: float = STAKEHOLDER_FATIGUE_FACTOR,
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
    overlap_coefficient: float = SUPPLY_CHAIN_OVERLAP_COEFF,
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
    competitor_growth_rate: float = COMPETITOR_GROWTH_RATE,
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
    efficiency = base_efficiency - (governance_risk / CASH_CONVERSION_GOV_DIVISOR)
    efficiency = max(CASH_CONVERSION_EFFICIENCY_FLOOR, min(1.0, efficiency))
    return round(revenue * efficiency, 2)


# ── 17. Dividend Ratchet Engine ─────────────────────────────────
def calc_dividend_ratchet(
    dividends_this_round: float,
    dividends_last_round: float,
    reputation_penalty: float = DIVIDEND_CUT_REP_PENALTY,
    cut_threshold: float = DIVIDEND_CUT_THRESHOLD,
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
    neglect_threshold: float = TALENT_NEGLECT_THRESHOLD,
    penalty_rate: float = TALENT_NEGLECT_PENALTY_RATE,
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
    lockin_threshold: int = LOCKIN_ROUNDS_THRESHOLD,
    penalty_rate: float = LOCKIN_PENALTY_RATE,
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
def resolve_green_claim(
    round_number: int,
    choice: str,
    bus: list[dict],
    decision_paradigm: str | None = None,
) -> str | None:
    """DEEP-6 (2026-08-31 deep engine audit): which options make a public
    green/ESG claim is CONFIG, not position. Returns the chosen option's
    `green_claim` value — "full" (checked at the 15% investment threshold,
    full SLO penalty), "moderate" (10%, half penalty) — or None for options
    that make no green claim and are never greenwash-checked. Industry-aware
    (healthcare/BRSR configs carry their own tags)."""
    try:
        if decision_paradigm == "brsr_ngrbc":
            from side_tracks.brsr_ngrbc.configs import get_brsr_round_options as _g
        elif any(b.get("bu_id") == "hospitals" for b in (bus or [])):
            from healthcare_configs import get_healthcare_round_options as _g
        else:
            from round_configs import get_round_options as _g
        opt = (_g(round_number) or {}).get(choice) or {}
        level = opt.get("green_claim")
        return level if level in ("full", "moderate") else None
    except Exception:
        return None


def calc_greenwashing_risk(
    choice: str,
    decisions: list[dict],
    green_investment_threshold: float = GREENWASH_INVESTMENT_THRESHOLD,
    penalty: float = GREENWASH_SLO_PENALTY,
    claim_level: str | None = None,
) -> tuple[bool, float]:
    """
    FEATURE 16 — ESG Greenwashing Risk:
    If a player selects an option that makes a green/ESG claim but their
    actual average investment ratio does not back it, a greenwashing
    scandal is triggered.

    DEEP-6 (2026-08-31): classification is config-driven via `claim_level`
    (from resolve_green_claim). The old positional heuristic treated EVERY
    option_a/option_c as green — so Deny & Deflect, CEO-Only Sign-Off,
    Immediate Closure and Divest could fire a *greenwashing* scandal for
    teams that made no green claim at all. claim_level=None → never checked.

    "full"     → 15% threshold, full penalty (SDG-ORCH: 15.0)
    "moderate" → 10% threshold, half penalty
    Returns (scandal_triggered, social_license_penalty).
    """
    if claim_level not in ("full", "moderate"):
        return False, 0.0
    ratios = [d.get("investment_ratio", 0.0) for d in decisions]
    avg_ratio = sum(ratios) / max(len(ratios), 1)
    if claim_level == "full":
        if avg_ratio < green_investment_threshold:
            return True, penalty
    else:
        moderate_threshold = green_investment_threshold * GREENWASH_MODERATE_THRESHOLD_SCALE  # ~10% for default 15%
        if avg_ratio < moderate_threshold:
            return True, round(penalty * GREENWASH_MODERATE_PENALTY_SCALE, 2)
    return False, 0.0


# ── 20b. (removed 2026-09-01) check_bu_greenwash_scandal had zero callers
#     since the DEEP-6 config-driven green_claim rewrite — ruled dead code.


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
    rng = _rng if seed is None else _rng.Random()
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
    dso_factor = DSO_BASELINE_FACTOR + DSO_GOV_RISK_SCALING * governance_risk
    dso_factor = max(0.0, min(DSO_MAX_CAP, dso_factor))  # Cap at 15%
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

    inflation_noise = round(rng.uniform(-MACRO_NOISE_INFLATION_BAND, MACRO_NOISE_INFLATION_BAND), 4)
    carbon_price_pct = round(rng.uniform(-MACRO_NOISE_CARBON_BAND, MACRO_NOISE_CARBON_BAND), 4)
    # 6% chance of a localized micro-strike in any given 6-month round
    micro_strike = rng.random() < MICRO_STRIKE_PROBABILITY
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
        "entry_treasury": TURNAROUND_CRISIS_ENTRY_TREASURY, "entry_reputation": TURNAROUND_CRISIS_ENTRY_REP,
        "bailout": TURNAROUND_CRISIS_BAILOUT, "capex_cap": TURNAROUND_CRISIS_CAPEX_CAP, "mr_cap": TURNAROUND_CRISIS_MR_CAP,
        "narrative_enter": (
            "🚨 EMERGENCY BOARD SESSION: Your company is in critical distress. "
            "The creditors' committee has imposed an immediate spending freeze. "
            "A court-appointed Turnaround Manager has been assigned. "
            "Emergency credit line: +$3M. ALL capital expenditure frozen. "
            "Your only path forward is to survive."
        ),
    },
    "stabilisation": {
        "exit_treasury": TURNAROUND_STAB_EXIT_TREASURY, "exit_reputation": TURNAROUND_STAB_EXIT_REP,
        "capex_cap": TURNAROUND_STAB_CAPEX_CAP, "mr_cap": TURNAROUND_STAB_MR_CAP,
        "narrative_enter": (
            "📋 STABILISATION APPROVED: The board is cautiously optimistic. "
            "Your restructuring plan has been approved by the creditors' committee. "
            "Limited capital expenditure restored (50% cap). Dividend payments "
            "remain suspended. The market is watching — prove you can rebuild."
        ),
    },
    "recovery": {
        "exit_treasury": TURNAROUND_RECOVERY_EXIT_TREASURY, "exit_reputation": TURNAROUND_RECOVERY_EXIT_REP,
        "capex_cap": TURNAROUND_RECOVERY_CAPEX_CAP, "mr_cap": TURNAROUND_RECOVERY_MR_CAP,
        "narrative_enter": (
            "📈 RECOVERY PHASE: Financial stability is returning. Credit rating "
            "upgraded one notch. Full capital expenditure restored. "
            "The Turnaround Manager retains oversight but the board has resumed "
            "strategic authority. One more phase to complete the comeback."
        ),
    },
    "exit": {
        "exit_treasury": TURNAROUND_EXIT_TREASURY, "exit_reputation": TURNAROUND_EXIT_REP,
        "mr_bonus": TURNAROUND_EXIT_MR_BONUS,
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
    deliberate_entry: bool = False,
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
    # P3: deliberate post-completion entry — drop straight into Crisis,
    # bypassing the auto-trigger condition and the R2 grace guard. The
    # mid-sim auto path (deliberate_entry=False) is unchanged.
    if deliberate_entry and current_phase == "none":
        _crisis = _TURNAROUND_PHASES["crisis"]
        return {
            "distress_detected": True, "survival_mode": True,
            "turnaround_phase": "crisis", "phase_transition": True,
            "bailout_amount": _crisis["bailout"],
            "capex_cap_multiplier": _crisis["capex_cap"], "mr_cap": _crisis["mr_cap"],
            "archetype_override": "turnaround_manager",
            "message": _crisis["narrative_enter"],
        }

    if round_number < 2 and not deliberate_entry:
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


# ── 25b. Turnaround MODULE — post-completion eligibility (P2) ────
# Pure helpers for the optional, superadmin-gated post-completion Turnaround
# arc. They READ state but never mutate it; the module-enabled flag is passed in
# by the caller (router) to avoid an engine->admin import cycle.

def turnaround_score_eligible(mr) -> bool:
    """True when a completed run's Regenerative Multiple sits below the arc entry
    threshold (a 'Stranded Relic'-range result a comeback would target)."""
    try:
        return float(mr) < TURNAROUND_ARC_MR_THRESHOLD
    except (TypeError, ValueError):
        return False


def record_canonical_completion(gs: dict, *, terminal_value, regenerative_multiple,
                                archetype, profile=None, profile_title=None) -> dict:
    """Write the immutable R10 completion snapshot exactly once (setdefault). The
    Turnaround module reads but never mutates this, so a normal run's 'completed
    at R10' result is always recoverable even after an arc runs."""
    return gs.setdefault("final_report_canonical", {
        "terminal_value": terminal_value,
        "regenerative_multiple": regenerative_multiple,
        "archetype": archetype,
        "profile": profile,
        "profile_title": profile_title,
        "source": "r10",
    })


def turnaround_offer_for(gs: dict, module_enabled: bool):
    """Return the score-based Turnaround offer dict for a COMPLETED session, or
    None. This is the non-privileged half (module flag + completion + M_R
    threshold + not-already-run); per-facilitator authorisation is applied
    separately by the admin eligibility endpoint via can_orchestrate_turnaround()."""
    if not module_enabled:
        return None
    flags = gs.get("active_event_flags", {}) or {}
    if flags.get("turnaround_status") or gs.get("turnaround_mode"):
        return None  # already run or in-flight
    round_number = gs.get("round_number", flags.get("round_number", 0)) or 0
    completed = bool(gs.get("game_over")) or round_number >= 10
    if not completed:
        return None
    canonical = gs.get("final_report_canonical") or {}
    mr = canonical.get("regenerative_multiple",
                       flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)))
    if not turnaround_score_eligible(mr):
        return None
    return {
        "eligible": True,
        "current_mr": round(float(mr), 3),
        "threshold": TURNAROUND_ARC_MR_THRESHOLD,
        "max_rounds": TURNAROUND_ARC_MAX_ROUNDS,
        "premium_if_graduated": TURNAROUND_EXIT_MR_BONUS,
    }



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

    if pct < SEVERITY_ROUTINE_CEILING:
        tier = "routine"
        label = "🟢 Market friction"
    elif pct < SEVERITY_NOTEWORTHY_CEILING:
        tier = "noteworthy"
        label = "🟡 Emerging pressure"
    elif pct < SEVERITY_MATERIAL_CEILING:
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
    norm_velocity = max(-50, min(50, delta_velocity / max(abs(curr_treasury), 1) * MOMENTUM_TREASURY_NORM))
    norm_rep = max(-50, min(50, delta_rep * MOMENTUM_REP_MULTIPLIER))
    norm_ncd = max(-50, min(50, delta_ncd * MOMENTUM_NCD_MULTIPLIER))

    raw = 50 + (MOMENTUM_WEIGHT_TREASURY * norm_velocity + MOMENTUM_WEIGHT_REP * norm_rep + MOMENTUM_WEIGHT_NCD * norm_ncd)
    score = round(max(0, min(100, raw)), 1)

    # Track consecutive high momentum
    prev_momentum_history = current_global.get("momentum_history", [])
    consecutive = 0
    for h in reversed(prev_momentum_history):
        if h > MOMENTUM_HIGH_THRESHOLD:
            consecutive += 1
        else:
            break
    if score > MOMENTUM_HIGH_THRESHOLD:
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
        "comeback_kid_mr_bonus": MOMENTUM_COMEBACK_MR_BONUS if comeback_kid else 0.0,
    }




# ── 26. Predictive Forecast Engine ──────────────────────────────
# ── Forecast Caching Layer ──────────────────────────────────────
# calc_forecast() takes unhashable dict args so it cannot be decorated
# directly.  Instead, results are cached by (session_id, round_number)
# in an explicit module-level dict.
#
# FIX CRITICAL-1 (AUDIT): Replaced @lru_cache mutable singleton pattern
# with a plain dict.  The previous implementation used @lru_cache on a
# no-arg function returning a mutable dict — this created a hidden
# module-level singleton that was written to at runtime, violating the
# pure-function contract.  The new design makes the cache an explicit
# module-level dict that is clearly mutable by design, with a bounded
# eviction strategy and a clean invalidation API.
#
# Thread-safety: dict operations under CPython's GIL are atomic for
# single key read/write.  No external locking required.
#
# Eviction: _FORECAST_CACHE_MAXSIZE limits the store size.  When the
# limit is reached, the oldest entries are evicted (FIFO). In practice
# round numbers are monotonically increasing so stale entries are never
# re-requested.

_FORECAST_CACHE_MAXSIZE: int = 128
_forecast_cache: dict[tuple[str, int], dict] = {}


def calc_forecast_cached(
    session_id: str,
    round_number: int,
    current_global: dict,
    current_bus: list[dict],
) -> dict:
    """
    Round-keyed cached wrapper for calc_forecast().

    Uses (session_id, round_number) as the primary cache key.  Since round
    numbers are monotonically increasing within a session, a completed round
    will never be requested again — the bounded eviction handles cleanup
    with no explicit invalidation needed.

    Public API is unchanged from the previous implementation.
    """
    cache_key = (session_id, round_number)
    if cache_key in _forecast_cache:
        return _forecast_cache[cache_key]

    result = calc_forecast(current_global, current_bus)

    # Bounded eviction: if over limit, remove oldest entries (FIFO)
    if len(_forecast_cache) >= _FORECAST_CACHE_MAXSIZE:
        # Remove the oldest ~25% of entries to avoid evicting on every insert
        keys_to_evict = list(_forecast_cache.keys())[:_FORECAST_CACHE_MAXSIZE // 4]
        for k in keys_to_evict:
            _forecast_cache.pop(k, None)

    _forecast_cache[cache_key] = result
    return result


def invalidate_forecast_cache(session_id: str = None) -> None:
    """
    Flush forecast cache entries.

    If session_id is provided, only entries for that session are removed.
    If session_id is None, all entries are flushed.

    FIX CRITICAL-1: Now supports per-session invalidation (previously
    only full flush was possible with the @lru_cache pattern).
    """
    if session_id is None:
        _forecast_cache.clear()
    else:
        keys_to_remove = [k for k in _forecast_cache if k[0] == session_id]
        for k in keys_to_remove:
            _forecast_cache.pop(k, None)


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
    avg_ci = _calc_rw_avg_ci(current_bus)  # I3: revenue-weighted avg CI
    # Higher = more dangerous. Scale 0-100.
    contagion_risk_index = round(min(100, max(0,
        (avg_gov_risk * CRI_WEIGHT_GOV_RISK) +
        ((100 - avg_slo) * CRI_WEIGHT_SLO_DEFICIT) +
        ((100 - avg_rep) * CRI_WEIGHT_REP_DEFICIT) +
        (avg_ci * CRI_WEIGHT_CARBON)
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
    if max_ncd_bu < NCD_WARN_THRESHOLD and ncd_growth_rate > 0:
        rounds_to_ncd_downgrade = round((NCD_WARN_THRESHOLD - max_ncd_bu) / max(ncd_growth_rate, 1), 1)
    else:
        rounds_to_ncd_downgrade = 0 if max_ncd_bu >= NCD_WARN_THRESHOLD else None

    # Brain drain countdown (reputation < BRAINDRAIN_REP_THRESHOLD threshold)
    rep_decay_rate = (100 - avg_rep) * 0.02  # Natural decay rate
    if avg_rep > BRAINDRAIN_REP_THRESHOLD and rep_decay_rate > 0:
        rounds_to_braindrain = round((avg_rep - BRAINDRAIN_REP_THRESHOLD) / max(rep_decay_rate, 0.1), 1)
    elif avg_rep <= BRAINDRAIN_REP_THRESHOLD:
        rounds_to_braindrain = 0  # Already in brain drain zone
    else:
        rounds_to_braindrain = None

    # Max strike probability across BUs
    max_strike_prob = 0.0
    max_strike_bu = ""
    # SPEC F3: a coalition formed last round raises this round's strike risk. The
    # scalar is carried on the persistent npc_stakeholders sub-dict; default 0
    # (and multiplier 1.0) means no behaviour change when coalitions are off.
    _coalition_pressure = current_global.get("npc_stakeholders", {}).get("coalition_pressure", 0.0) or 0.0
    _coalition_mult = 1.0 + _coalition_pressure * COALITION_STRIKE_GAIN
    for bu in current_bus:
        gov_risk = bu.get("governance_risk_score", 0)
        slo = bu.get("social_license_score", 50)
        base_risk = gov_risk / 100.0
        p = calc_strike_probability(base_risk, slo, coalition_multiplier=_coalition_mult)
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
    if rounds_to_ncd_downgrade is not None and rounds_to_ncd_downgrade <= TIME_TO_IMPACT_HORIZON:
        time_to_impact_warnings.append({
            "indicator": "NCD Credit Downgrade",
            "rounds": rounds_to_ncd_downgrade,
            "message": f"At current trajectory, NCD will trigger credit downgrade in {rounds_to_ncd_downgrade:.0f} round(s)",
            "severity": "critical" if rounds_to_ncd_downgrade <= 2 else "material",
        })
    if rounds_to_braindrain is not None and rounds_to_braindrain <= TIME_TO_IMPACT_HORIZON:
        time_to_impact_warnings.append({
            "indicator": "Brain Drain Activation",
            "rounds": rounds_to_braindrain,
            "message": f"Reputation declining. Brain drain penalty activates in {rounds_to_braindrain:.0f} round(s)",
            "severity": "critical" if rounds_to_braindrain <= 2 else "material",
        })
    if max_strike_prob > STRIKE_WARNING_THRESHOLD:
        time_to_impact_warnings.append({
            "indicator": "Strike Risk",
            "rounds": 1,
            "message": f"{max_strike_bu} has a {max_strike_prob*100:.0f}% chance of industrial action next round",
            "severity": "critical" if max_strike_prob > STRIKE_CRITICAL_THRESHOLD else "material",
        })
    if rounds_to_distress_treasury is not None and rounds_to_distress_treasury <= TIME_TO_IMPACT_HORIZON:
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
            "🟢 Low" if contagion_risk_index < CRI_TIER_LOW else
            "🟡 Moderate" if contagion_risk_index < CRI_TIER_MODERATE else
            "🟠 High" if contagion_risk_index < CRI_TIER_HIGH else
            "🔴 Critical"
        ),
        "rounds_to_insolvency": rounds_to_insolvency,
        "insolvency_warning": rounds_to_insolvency is not None and rounds_to_insolvency <= INSOLVENCY_WARNING_ROUNDS,
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

# ── Flag-bonus registry for SDG scoring (add new entries here, not in the function) ──
# Format: {flag_key: {sdg_num: bonus_points, label: str}}
# Keeping this as data prevents the post-aggregation mutation bug (CRITICAL-5 fix).
_SDG_FLAG_BONUSES: dict[str, dict] = {
    "community_fund":    {"sdg": 1,  "bonus": 10.0, "label": "SDG 1: Community Fund bonus +10"},
    "ethical_ai_overhaul": {"sdg": 16, "bonus": 15.0, "label": "SDG 16: Ethical AI bonus +15"},
    "circular_redesign": {"sdg": 12, "bonus": 15.0, "label": "SDG 12: Circular Redesign bonus +15"},
}


def calc_sdg_impact(bus: list[dict], flags: dict) -> dict:
    """
    FEATURE 27 — SDG Impact Report:
    Maps simulation BU-level variables to all 17 UN SDGs.
    Returns a score (0-100) per SDG and an aggregate SDG Index.

    Scoring: For each SDG, the avg BU metric is compared against
    a threshold. Meeting/exceeding = 100 pts × weight.
    Inverted metrics (lower = better) are scored inversely.

    FIX CRITICAL-5: Flag-based bonuses are now applied to each SDG's
    weighted_score BEFORE the aggregate is computed.  Previously the
    bonuses mutated scores after aggregation, causing sdg_index to be
    understated by up to 40 points relative to the individual scores.

    Operation order (all three phases complete before any reads):
      Phase 1 — Compute base weighted_score for every SDG from BU metrics.
      Phase 2 — Apply _SDG_FLAG_BONUSES to the relevant dimensions.
      Phase 3 — Aggregate over the post-bonus weighted_scores → sdg_index.
    """
    n = max(len(bus), 1)

    # ── Phase 1: Base scores from BU metrics ─────────────────────
    # Raw weighted scores keyed by SDG number; no bonuses yet.
    base_weighted: dict[int, float] = {}
    sdg_meta: dict[int, dict] = {}  # non-score metadata carried forward

    for sdg_num, cfg in _SDG_MAPPING.items():
        metric_key: str = cfg["metric"]
        threshold: float = cfg["threshold"]
        invert: bool = cfg.get("invert", False)
        weight: float = cfg["weight"]

        avg_val: float = sum(bu.get(metric_key, 0) for bu in bus) / n

        if invert:
            # Lower is better: score = 100 if avg ≤ threshold, scaled down above
            if threshold == 0:
                raw_score: float = 100.0 if avg_val == 0 else max(0.0, 100.0 - avg_val)
            else:
                raw_score = max(0.0, min(100.0, (1.0 - avg_val / (threshold * 2)) * 100.0))
        else:
            # Higher is better: score = 100 if avg ≥ threshold, scaled below
            if threshold == 0:
                raw_score = 100.0
            else:
                raw_score = max(0.0, min(100.0, (avg_val / threshold) * 100.0))

        base_weighted[sdg_num] = round(raw_score * weight, 1)
        sdg_meta[sdg_num] = {
            "raw_score": round(raw_score, 1),
            "weight": weight,
            "metric_key": metric_key,
            "avg_value": round(avg_val, 2),
            "threshold": threshold,
            "label": cfg["label"],
        }

    # ── Phase 2: Apply flag bonuses BEFORE aggregation ────────────
    # Each bonus modifies a local copy of the score; no external state touched.
    bonus_sdgs: list[str] = []
    flag_bonus_applied: dict[int, float] = {}  # {sdg_num: total_bonus} for transparency

    for flag_key, bonus_cfg in _SDG_FLAG_BONUSES.items():
        if flags.get(flag_key):
            sdg_num: int = bonus_cfg["sdg"]
            bonus_pts: float = bonus_cfg["bonus"]
            pre_bonus = base_weighted[sdg_num]
            base_weighted[sdg_num] = round(min(100.0, pre_bonus + bonus_pts), 1)
            flag_bonus_applied[sdg_num] = flag_bonus_applied.get(sdg_num, 0.0) + bonus_pts
            bonus_sdgs.append(bonus_cfg["label"])

    # ── Phase 3: Aggregate over post-bonus scores ─────────────────
    # sdg_index is now mathematically consistent with every weighted_score value.
    total_weight: float = sum(cfg["weight"] for cfg in _SDG_MAPPING.values())
    aggregate: float = round(
        sum(base_weighted.values()) / max(total_weight, 1.0), 1
    )

    # ── Build final per-SDG output dict ──────────────────────────
    sdg_scores: dict[int, dict] = {}
    for sdg_num, cfg in _SDG_MAPPING.items():
        w_score = base_weighted[sdg_num]
        sdg_scores[sdg_num] = {
            "sdg": sdg_num,
            "label": sdg_meta[sdg_num]["label"],
            "raw_score": sdg_meta[sdg_num]["raw_score"],
            "weight": sdg_meta[sdg_num]["weight"],
            "weighted_score": w_score,
            "flag_bonus_applied": flag_bonus_applied.get(sdg_num, 0.0),
            "metric_key": sdg_meta[sdg_num]["metric_key"],
            "avg_value": sdg_meta[sdg_num]["avg_value"],
            "threshold": sdg_meta[sdg_num]["threshold"],
            # status derived from the post-bonus score (consistent with sdg_index)
            "status": "on_track" if w_score >= 60.0 else ("at_risk" if w_score >= 30.0 else "off_track"),
        }

    return {
        "sdg_scores": sdg_scores,
        "sdg_index": aggregate,
        "sdg_grade": (
            "A+" if aggregate >= SDG_GRADE_A_PLUS else
            "A"  if aggregate >= SDG_GRADE_A else
            "B"  if aggregate >= SDG_GRADE_B else
            "C"  if aggregate >= SDG_GRADE_C else
            "D"  if aggregate >= SDG_GRADE_D else "F"
        ),
        "bonus_sdgs": bonus_sdgs,
        "total_sdgs_on_track":  sum(1 for s in sdg_scores.values() if s["status"] == "on_track"),
        "total_sdgs_at_risk":   sum(1 for s in sdg_scores.values() if s["status"] == "at_risk"),
        "total_sdgs_off_track": sum(1 for s in sdg_scores.values() if s["status"] == "off_track"),
    }


# ── 30. Carbon-Adjusted Return on Invested Capital (CAROIC) ─────
def calc_caroic(
    ebitda: float,
    invested_capital: float,
    carbon_tonnage: float,
    tax_rate: float = FINANCIAL_CORPORATE_TAX_RATE,
    shadow_carbon_price: float = FINANCIAL_SHADOW_CARBON_PRICE,
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
    if caroic_pct >= CAROIC_GRADE_A_PLUS:
        grade = "A+"
        interpretation = "Exceptional capital-carbon efficiency. Minimal carbon drag on returns."
    elif caroic_pct >= CAROIC_GRADE_A:
        grade = "A"
        interpretation = "Strong carbon-adjusted returns. Carbon transition well-managed."
    elif caroic_pct >= CAROIC_GRADE_B:
        grade = "B"
        interpretation = "Solid returns despite carbon drag. Room for decarbonisation gains."
    elif caroic_pct >= CAROIC_GRADE_C:
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
#  PENDING PROJECT DELTA  (pure helper — no I/O, no mutation)
# ═════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PendingProjectDelta:
    """
    Pure-function return type for _process_pending_projects().

    All effects that were previously applied in-place inside the
    pending-project loop are now encoded as typed fields here.
    The orchestrator reads these fields and applies them explicitly,
    preserving a clear, testable boundary between "what fired" and
    "how state changes".

    Fields
    ------
    remaining_projects   : Projects still in-flight (rounds_remaining > 0).
                           Written verbatim to new_global["pending_capex_projects"].
    completed_projects   : Snapshot of every project that matured this tick
                           (for event logging only — not persisted).
    synergy_boost_total  : Sum of all synergy_boost amounts that fired.
                           Added to new_synergy AFTER VRIO decay — NOT written
                           to current_global (fixes CRITICAL-3).
    ncd_drops            : List of {bu_target, amount} dicts for ncd_drop projects.
                           Caller writes new_ncd = max(0, old_ncd + amount) per BU.
    resilience_factor    : Value of the first resilience_boost that fired (0.0 if none).
    truth_premium        : True if any truth_premium project matured.
    revenue_generation_total : Sum of all revenue_generation amounts.
                           Added to new_treasury with a _wf() entry (fixes CRITICAL-4).
    revenue_generation_desc  : Description string for the waterfall label.
    synergy_lag_completions  : {bu_id: opex_reduction} for synergy_lag maturations.
    education_lag_total      : Sum of education_lag amounts that fired (SDG track).
    """
    remaining_projects:       list[dict]
    completed_projects:       list[dict]
    synergy_boost_total:      float
    ncd_drops:                list[dict]          # [{bu_target, amount}, ...]
    resilience_factor:        float
    truth_premium:            bool
    revenue_generation_total: float
    revenue_generation_desc:  str
    synergy_lag_completions:  dict[str, float]    # {bu_id: opex_reduction}
    education_lag_total:      float


def _process_pending_projects(
    pending_projects: list[dict],
    new_this_tick:    list[dict] | None = None,
) -> PendingProjectDelta:
    """
    PURE FUNCTION — Advance the pending-project queue by one tick.

    Parameters
    ----------
    pending_projects : list[dict]
        Projects currently tracked in global_state["pending_capex_projects"].
        Each dict must contain at minimum: {type, rounds_remaining}.
        This list is NEVER mutated — every project dict is shallow-copied
        before decrementing rounds_remaining.
    new_this_tick : list[dict] | None
        New projects generated during this tick (DSO deferrals, synergy lag
        deferrals) that should be appended to the surviving queue before
        returning. Defaults to an empty list.

    Returns
    -------
    PendingProjectDelta
        A frozen dataclass describing all effects and the updated queue.
        The orchestrator is responsible for writing these effects to state.

    Project type catalogue
    ----------------------
    "ncd_drop"          — Reduce natural_capital_debt on target BU(s).
    "resilience_boost"  — Activate climate resilience factor for this round.
    "synergy_boost"     — Add to the group synergy multiplier.
    "truth_premium"     — Unlock Truth Premium M_R flag.
    "synergy_lag"       — Complete a deferred OPEX reduction on a target BU.
    "revenue_generation"— Release deferred revenue back into treasury.
    "education_lag"     — Mature an SDG education investment.
    """
    if new_this_tick is None:
        new_this_tick = []

    remaining:          list[dict]       = []
    completed:          list[dict]       = []
    ncd_drops:          list[dict]       = []
    synergy_lag_comps:  dict[str, float] = {}
    synergy_boost_total: float           = 0.0
    resilience_factor:  float            = 0.0
    truth_premium:      bool             = False
    rev_gen_total:      float            = 0.0
    rev_gen_desc:       str              = ""
    edu_lag_total:      float            = 0.0

    for proj in pending_projects:
        # Shallow-copy so the caller's original dict is untouched
        p = {**proj, "rounds_remaining": proj["rounds_remaining"] - 1}

        if p["rounds_remaining"] <= 0:
            # Project matured — decode its effect into the delta
            completed.append(p)
            t = p.get("type", "")

            if t == "ncd_drop":
                ncd_drops.append({
                    "bu_target": p.get("bu_target", "all"),
                    "amount":    p.get("amount", 0.0),
                })

            elif t == "resilience_boost":
                # Last writer wins if multiple resilience projects fire same tick
                resilience_factor = p.get("amount", 0.0)

            elif t == "synergy_boost":
                # Accumulate; orchestrator adds to new_synergy AFTER VRIO decay
                synergy_boost_total += p.get("amount", 0.0)

            elif t == "truth_premium":
                truth_premium = True

            elif t == "synergy_lag":
                bu_id     = p.get("bu_target", "")
                reduction = p.get("amount", 0.0)
                # Multiple lag projects for the same BU accumulate
                synergy_lag_comps[bu_id] = synergy_lag_comps.get(bu_id, 0.0) + reduction

            elif t == "revenue_generation":
                amount = p.get("amount", 0.0)
                rev_gen_total += amount
                # Use the most recent description for the waterfall label
                rev_gen_desc = p.get("description", "Deferred Revenue Collection")

            elif t == "education_lag":
                edu_lag_total += p.get("amount", 0.0)

            # Unknown types are silently completed (logged via completed_projects)

        else:
            remaining.append(p)

    # New projects generated this tick join the surviving queue
    remaining.extend(new_this_tick)

    return PendingProjectDelta(
        remaining_projects       = remaining,
        completed_projects       = completed,
        synergy_boost_total      = round(synergy_boost_total, 4),
        ncd_drops                = ncd_drops,
        resilience_factor        = round(resilience_factor, 4),
        truth_premium            = truth_premium,
        revenue_generation_total = round(rev_gen_total, 2),
        revenue_generation_desc  = rev_gen_desc,
        synergy_lag_completions  = {k: round(v, 2) for k, v in synergy_lag_comps.items()},
        education_lag_total      = round(edu_lag_total, 4),
    )


# ═════════════════════════════════════════════════════════════════
#  TICK ORCHESTRATOR — TickContext + 4-Stage Pipeline
# ═════════════════════════════════════════════════════════════════
#
#  Architecture:
#    1. TickContext  — dataclass carrying all cross-stage mutable state.
#    2. _run_stochastic_layer  — Black Swans, FX, DSO, inflation noise.
#    3. _run_financial_layer   — CSF, loans, projects, contagion, burnout.
#    4. _run_operational_layer — NCD, SBTi, tipping points, SDG, carbon fee.
#    5. _run_reporting_layer   — greenwashing, distress, waterfall, sentiment.
#    6. _assemble_global_state — builds the final immutable output dict.
#    7. process_tick           — thin orchestrator (~50 lines).
#
#  All computation is identical to the previous monolithic implementation.
#  Only the structural grouping has changed.
# ═════════════════════════════════════════════════════════════════


# ── TickContext ──────────────────────────────────────────────────

@dataclass
class TickContext:
    """
    Mutable working state shared across all pipeline stages within a single
    call to process_tick().  Each stage receives this context, updates the
    relevant fields in-place, and passes it to the next stage.

    Fields are intentionally NOT frozen so pipeline stages can mutate them
    directly — immutability is enforced at the *boundary* (inputs are
    deep-copied before the context is created; output is assembled from
    context fields into a fresh dict).
    """
    # ── Read-only inputs (copied before context creation) ──────
    current_global:            dict
    decision_map:              dict[str, dict]
    decisions:                 list[dict]
    decision_paradigm:         str
    dividends_paid:            float
    crisis_severity:           float
    imitation_decay_rate:      float
    emergency_credit_used:     bool
    pre_tick_synergy:          float
    next_round:                int

    # ── Working BU list (mutated freely within pipeline) ───────
    new_bus:                   list[dict]

    # ── Accumulator dicts ──────────────────────────────────────
    events:                    dict[str, Any]
    waterfall:                 list[dict]

    # ── Treasury waterfall running total ───────────────────────
    _waterfall_running_total:  float
    _waterfall_initial:        float          # snapshot for severity math

    # ── Evolving scalar state ──────────────────────────────────
    new_treasury:              float
    new_synergy:               float
    new_green_fund_balance:    float
    new_inflation_index:       float
    corporate_cost_of_capital: float
    group_reputation:          float

    # ── Project queues ─────────────────────────────────────────
    new_pending_projects:      list[dict]
    new_synergy_lag_projects:  list[dict]

    # ── Derived metrics (populated in _run_financial_layer) ────
    historical_ebitda:         float = 0.0
    tco2e_emissions:           float = 0.0
    vrio_capabilities:         dict  = field(default_factory=dict)

    # ── Internal: SDG state ────────────────────────────────────
    sdg_political_capital:     float = 50.0
    sdg_community_trust:       float = 50.0

    def record_waterfall(
        self,
        label: str,
        amount: float,
        because: str = "",
        counterfactual: str = "",
    ) -> None:
        """
        Record a treasury waterfall entry.

        Replaces the old nonlocal _wf() closure.  running_total is stored
        on the context so any stage can add entries in the correct order.
        Entries below $0.01 are silently ignored (same rule as before).
        """
        if abs(amount) < 0.01:
            return
        self._waterfall_running_total = round(self._waterfall_running_total + amount, 2)
        entry: dict[str, Any] = {
            "label":         label,
            "amount":        round(amount, 2),
            "running_total": self._waterfall_running_total,
            "severity":      classify_severity(
                abs(amount), max(abs(self._waterfall_initial), 1)
            ),
        }
        if because:
            entry["because"] = because
        if counterfactual:
            entry["counterfactual"] = counterfactual
        self.waterfall.append(entry)


# ── Stage 1: Stochastic Layer ────────────────────────────────────
# Black Swans → Revenue Cannibalization → Supply Chain Contagion →
# Macro Rate → FX Risk → DSO / Working Capital → Cash Conversion →
# Macroeconomic Inflation + Macro Noise

def _run_stochastic_layer(ctx: TickContext) -> None:
    """
    Stage 1 — stochastic market forces that adjust BU revenue/OPEX
    before any financial or operational calculations run.
    """
    current_global = ctx.current_global

    # ── PHASE-1: Black Swan Evaluation — stochastic disruptions ──
    try:
        from black_swan_registry import evaluate_black_swans, apply_black_swan_impacts
        _session_tier = current_global.get("active_event_flags", {}).get("difficulty_tier", "standard")
        _active_swans = current_global.get("active_event_flags", {}).get("active_black_swans", [])
        _forced_swan  = current_global.get("active_event_flags", {}).get("forced_black_swan", None)
        _region_id    = (
            current_global.get("region_id", "")
            or current_global.get("active_event_flags", {}).get("region_id", "")
            or ""
        )
        _swan_result = evaluate_black_swans(
            current_global, ctx.new_bus, current_global["round_number"],
            difficulty_tier=_session_tier,
            active_black_swans=_active_swans,
            forced_event_id=_forced_swan,
            region_id=_region_id or None,
        )
        if _swan_result["total_new_events"] > 0:
            _swan_diag = apply_black_swan_impacts(current_global, ctx.new_bus, _swan_result["events_triggered"])
            ctx.events["black_swan_events"]      = _swan_result["events_triggered"]
            ctx.events["black_swan_narratives"]  = _swan_result["narratives"]
            ctx.events["black_swan_diagnostics"] = _swan_diag
            ctx.events.setdefault("custom_black_swans", []).extend([
                {"title": e["title"], "narrative": e["narrative"], "icon": e["icon"], "severity": "critical"}
                for e in _swan_result["events_triggered"]
            ])
        _all_active = _swan_result.get("events_continuing", []) + _swan_result.get("events_triggered", [])
        ctx.events["active_black_swans"] = [e for e in _all_active if e.get("rounds_remaining", 0) > 0]
        if _forced_swan:
            ctx.events["forced_black_swan"] = None
    except ImportError:
        pass  # Graceful degradation if black_swan_registry not available

    # ── FEATURE 6: Revenue Cannibalization — before inflation ────
    cannibalization = calc_revenue_cannibalization(ctx.new_bus)
    for bu_id, penalty in cannibalization.items():
        for bu in ctx.new_bus:
            if bu["bu_id"] == bu_id:
                bu["revenue_base"] = round(bu["revenue_base"] - penalty, 2)
                ctx.events[f"revenue_cannibalized_{bu_id}"] = penalty
                ctx.events[f"revenue_cannibalized_{bu_id}_because"] = (
                    f"{bu_id} revenue reduced by ${penalty:,.0f} due to market overlap "
                    f"with sibling BUs. When one BU dominates revenue share, "
                    f"it cannibalizes demand from adjacent divisions."
                )
                break

    # ── FEATURE 8: Supply Chain Contagion — OPEX surcharges ─────
    sc_surcharges = calc_supply_chain_contagion(ctx.new_bus)
    for bu_id, surcharge in sc_surcharges.items():
        for bu in ctx.new_bus:
            if bu["bu_id"] == bu_id:
                bu["opex_base"] = round(bu["opex_base"] + surcharge, 2)
                ctx.events[f"supply_chain_contagion_{bu_id}"] = surcharge
                break

    # ── FEATURE 21: Macro Interest Rate Environment ─────────────
    macro_rate = calc_macro_rate_environment(current_global["round_number"])
    ctx.events["macro_rate_environment"] = macro_rate

    # ── FEATURE 22: FX Risk — stochastic currency impact ────────
    fx_result = calc_fx_impact(
        ctx.new_bus, current_global["round_number"],
        seed=event_seed(current_global.get("active_event_flags", {}),
                        current_global["round_number"], "fx_risk"),
    )
    for bu_id, fx_delta in fx_result["adjustments"].items():
        for bu in ctx.new_bus:
            if bu["bu_id"] == bu_id:
                bu["revenue_base"] = round(bu["revenue_base"] + fx_delta, 2)
                break
    ctx.events["fx_risk"] = {
        "fx_index":     fx_result["fx_index"],
        "fx_direction": fx_result["fx_direction"],
        "fx_message":   fx_result["fx_message"],
        "bu_details":   fx_result["bu_details"],
    }

    # ── FEATURE 23: DSO / Working Capital Timing ────────────────
    dso_transparency: dict[str, dict] = {}
    total_deferred = 0.0
    for bu in ctx.new_bus:
        gov_risk     = bu.get("governance_risk_score", 0)
        dso          = calc_dso_lag(bu["revenue_base"], gov_risk, current_global["round_number"])
        deferred_amt = dso["deferred_amount"]
        if deferred_amt > 0:
            bu["revenue_base"] = round(bu["revenue_base"] - deferred_amt, 2)
            total_deferred    += deferred_amt
            ctx.new_synergy_lag_projects.append({
                "type":             "revenue_generation",
                "amount":           deferred_amt,
                "rounds_remaining": 1,
                "description":      f"Working capital collection for {bu['bu_id']} (DSO: {dso['dso_days_approx']:.0f} days)",
            })
        dso_transparency[bu["bu_id"]] = dso
    ctx.events["dso_working_capital"] = {
        "total_deferred": round(total_deferred, 2),
        "bu_details":     dso_transparency,
        "note":           "Revenue deferred to next round due to cash collection cycle",
    }

    # ── FEATURE 11: Working Capital / Cash Conversion ───────────
    for bu in ctx.new_bus:
        gov_risk       = bu.get("governance_risk_score", 0)
        old_rev        = bu["revenue_base"]
        bu["revenue_base"] = calc_cash_conversion(old_rev, gov_risk)
        if bu["revenue_base"] < old_rev:
            ctx.events[f"cash_conversion_drag_{bu['bu_id']}"] = round(old_rev - bu["revenue_base"], 2)

    # ── FEATURE 5: Macroeconomic Inflation + FEATURE 24 Noise ───
    inflation_index = current_global.get("inflation_index", 0.05)
    macro_noise     = calc_macro_noise(
        current_global["round_number"],
        seed=event_seed(current_global.get("active_event_flags", {}),
                        current_global["round_number"], "macro_noise"),
    )
    inflation_index = round(inflation_index + macro_noise["inflation_noise"], 4)
    ctx.events["macro_noise"] = macro_noise
    # Apply micro-strike: random BU gets a 5% OPEX spike
    if macro_noise["micro_strike_triggered"] and ctx.new_bus:
        # 4.1: resolve the target through the canonical slot order rather than
        # trusting whatever order storage handed us. Belt and braces with the
        # sort in both database modules: this line is the one that actually
        # decided which company took a 5% OPEX hit, and it must not depend on
        # an ORDER BY clause in a query three modules away.
        from bu_profiles import sort_bu_states_canonically
        _ordered    = sort_bu_states_canonically(list(ctx.new_bus), current_global)
        strike_idx  = macro_noise["micro_strike_bu_idx"] % len(_ordered)
        _target_id  = _ordered[strike_idx].get("bu_id")
        # Mutate the object in ctx.new_bus, not the sorted copy's element — they
        # are the same dicts, but resolve by identity to make that explicit.
        target_bu   = next(b for b in ctx.new_bus if b.get("bu_id") == _target_id)
        micro_penalty = round(target_bu["opex_base"] * MICRO_STRIKE_OPEX_RATE, 2)
        target_bu["opex_base"] = round(target_bu["opex_base"] + micro_penalty, 2)
        ctx.events["micro_strike_applied"] = {
            "bu_id":        target_bu["bu_id"],
            "opex_penalty": micro_penalty,
            "message":      f"⚡ Localized disruption at {target_bu['bu_id']}: +${micro_penalty:,.0f} OPEX",
        }
    for bu in ctx.new_bus:
        bu["opex_base"] = calc_inflation(bu["opex_base"], inflation_index)
    ctx.events["inflation_index_applied"] = inflation_index
    # Store inflation_index so _run_operational_layer can produce the drift event
    ctx.new_inflation_index = inflation_index


# ── Stage 2: Financial Layer ─────────────────────────────────────
# Synergy → CSF / Dividends → Green Fund → Loans → Pending Projects →
# Natural Decay → Technical Debt → Lock-In → Contagion → Burnout →
# NCD compounding → VRIO Decay → Strike probabilities → EBITDA / tCO₂e

def _run_financial_layer(ctx: TickContext) -> None:
    """
    Stage 2 — deterministic financial calculations: cash flows, project
    completions, contagion, burnout, NCD interest, VRIO decay.
    """
    current_global = ctx.current_global

    # ── 3. Synergy Engine & Healthcare Revenue Modifiers ────────
    for bu in ctx.new_bus:
        # Healthcare: Dynamic Patient Outcomes Score Revenue Modifier
        if bu["bu_id"] in ("hospitals", "clinics"):
            outcomes     = bu.get("patient_outcomes_score", PATIENT_OUTCOMES_BASELINE)
            rev_modifier = 1.0 + ((outcomes - PATIENT_OUTCOMES_BASELINE) / PATIENT_OUTCOMES_DIVISOR)
            rev_modifier = max(PATIENT_OUTCOMES_MOD_MIN, min(PATIENT_OUTCOMES_MOD_MAX, rev_modifier))
            bu["revenue_base"] = round(bu["revenue_base"] * rev_modifier, 2)
            ctx.events[f"patient_outcomes_billing_multiplier_{bu['bu_id']}"] = round(rev_modifier, 4)

        dec       = ctx.decision_map.get(bu["bu_id"], {})
        inv_ratio = dec.get("investment_ratio", 0.0)

        # ── FEATURE 1: Implementation Lag ───────────────────────
        if inv_ratio > IMPLEMENTATION_LAG_INV_THRESHOLD:
            deferred_opex_reduction = calc_synergy_opex(
                bu["opex_base"], inv_ratio, current_global["synergy_multiplier"]
            )
            reduction_amount = bu["opex_base"] - deferred_opex_reduction
            if reduction_amount > 0:
                ctx.new_synergy_lag_projects.append({
                    "type":             "synergy_lag",
                    "bu_target":        bu["bu_id"],
                    "amount":           reduction_amount,
                    "rounds_remaining": 1,
                    "description":      f"Synergy implementation completing for {bu['bu_id']}",
                })
                ctx.events[f"implementation_lag_deferred_{bu['bu_id']}"] = round(reduction_amount, 2)
        else:
            # BALANCE FIX: synergy efficiencies floor at 35% of the BU's
            # first-seen opex baseline (see synergy_opex_floor).
            bu["opex_base"] = max(
                min(synergy_opex_floor(bu), bu["opex_base"]),  # never RAISE opex, only stop the fall
                calc_synergy_opex(
                    bu["opex_base"], inv_ratio, current_global["synergy_multiplier"],
                ),
            )

    # ── 1. Corporate Strategic Fund & Short-Term Loan Logic ─────
    # FIX VULN-001: Clamp dividends to treasury
    base_treasury     = current_global["corporate_treasury"]
    clamped_dividends = min(ctx.dividends_paid, max(0.0, base_treasury))

    # ── FEATURE 12: Dividend Ratchet ────────────────────────────
    last_dividends = current_global.get("active_event_flags", {}).get("last_dividends_paid", 0.0)
    ratchet_hit, ratchet_penalty = calc_dividend_ratchet(clamped_dividends, last_dividends)
    if ratchet_hit:
        for bu in ctx.new_bus:
            bu["reputation_score"] = max(0.0, round(bu["reputation_score"] - ratchet_penalty, 2))
        ctx.events["dividend_ratchet_triggered"] = True
        ctx.events["dividend_ratchet_penalty"]   = ratchet_penalty
    ctx.events["last_dividends_paid"] = clamped_dividends

    csf = calc_csf(ctx.new_bus, clamped_dividends)
    if clamped_dividends < ctx.dividends_paid:
        ctx.events["dividends_clamped"]    = True
        ctx.events["dividends_requested"]  = ctx.dividends_paid
        ctx.events["dividends_paid"]       = clamped_dividends

    # Free capital allowance (FINANCIAL_FREE_CSF_PCT of starting treasury)
    free_csf_limit = base_treasury * FINANCIAL_FREE_CSF_PCT

    # Advanced Climate Engine: Green Fund CapEx offset
    green_fund_balance     = current_global.get("green_transition_fund", 0.0)
    total_capex_requested  = sum(dec.get("capex_allocated", 0) for dec in ctx.decisions)
    green_fund_used        = 0.0
    if ctx.decision_paradigm == "advanced_climate" and total_capex_requested > 0 and green_fund_balance > 0:
        green_fund_used        = min(total_capex_requested, green_fund_balance)
        total_capex_requested -= green_fund_used
        ctx.events["green_fund_used"] = green_fund_used
    ctx.new_green_fund_balance = round(green_fund_balance - green_fund_used, 2)

    # ── F-3: Materiality restricted fund — CapEx offset (any paradigm) ───────
    # Round 2 releases total_materiality_budget × Q1 recall into a ring-fenced
    # fund (router.submit_materiality_matrix). The fund is spendable only as
    # ESG CapEx on the issues the team identified: it offsets requested CapEx
    # ahead of the overrun/loan/interest machinery, exactly like the Advanced
    # Climate green fund above. Unspent balance carries forward, restricted —
    # it is never returned to treasury. _post_r2_materiality claws 40% of the
    # released amount back from this balance when Option C is chosen.
    mat_fund_balance = float(current_global.get("materiality_restricted_fund", 0.0) or 0.0)
    if mat_fund_balance > 0 and total_capex_requested > 0:
        mat_fund_used = round(min(total_capex_requested, mat_fund_balance), 2)
        total_capex_requested = round(total_capex_requested - mat_fund_used, 2)
        ctx.events["materiality_fund_used"] = mat_fund_used
        ctx.events["materiality_restricted_fund"] = round(mat_fund_balance - mat_fund_used, 2)
        ctx.events["materiality_fund_message"] = (
            f"🏦 Materiality Fund: ${mat_fund_used:,.0f} of this round's ESG CapEx was "
            f"drawn from your ring-fenced materiality fund "
            f"(${ctx.events['materiality_restricted_fund']:,.0f} remaining)."
        )

    # ── FEATURE 3: Execution Overrun Risk ───────────────────────
    try:
        from admin_shared import _god_mode_settings
        _overrun_prob = _god_mode_settings.get("overrun_probability", 0.25)
        _overrun_sev  = _god_mode_settings.get("overrun_severity", 0.15)
    except ImportError:
        _overrun_prob, _overrun_sev = 0.25, 0.15
    overrun_triggered, overrun_amount = calc_overrun_risk(
        total_capex_requested,
        overrun_probability=_overrun_prob,
        overrun_severity=_overrun_sev,
        rng=event_rng(current_global.get("active_event_flags", {}),
                      current_global["round_number"], "execution_overrun"),
    )
    if overrun_triggered:
        total_capex_requested = round(total_capex_requested + overrun_amount, 2)
        ctx.events["capex_overrun_triggered"] = True
        ctx.events["capex_overrun_amount"]    = overrun_amount
        ctx.events["capex_overrun_message"]   = (
            f"Execution overrun! Project scope creep added "
            f"${overrun_amount:,.0f} to your capital expenditure."
        )

    # FIX VULN-006: Cap total CAPEX at FINANCIAL_CAPEX_CAP_MULTIPLE × treasury
    capex_cap = base_treasury * FINANCIAL_CAPEX_CAP_MULTIPLE
    if total_capex_requested > capex_cap:
        total_capex_requested      = capex_cap
        ctx.events["capex_capped"]     = True
        ctx.events["capex_cap_limit"]  = capex_cap

    # Loan / Emergency Credit
    loan_interest_payment = 0.0
    loan_principal        = max(0.0, total_capex_requested - free_csf_limit)

    emergency_credit_interest = 0.0
    _EMERGENCY_CREDIT_AMOUNT  = FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    if ctx.emergency_credit_used:
        base_loan_rate            = current_global.get("active_event_flags", {}).get("loan_interest_rate", FINANCIAL_DEFAULT_LOAN_RATE)
        emergency_rate            = base_loan_rate + FINANCIAL_EMERGENCY_RATE_SPREAD
        emergency_credit_interest = round(_EMERGENCY_CREDIT_AMOUNT * emergency_rate, 2)
        ctx.events["emergency_credit_used"]     = True
        ctx.events["emergency_credit_amount"]   = _EMERGENCY_CREDIT_AMOUNT
        ctx.events["emergency_credit_rate"]     = emergency_rate
        ctx.events["emergency_credit_interest"] = emergency_credit_interest

    if loan_principal > 0:
        loan_interest_rate    = current_global.get("active_event_flags", {}).get("loan_interest_rate", FINANCIAL_DEFAULT_LOAN_RATE)
        loan_interest_payment = round(loan_principal * loan_interest_rate, 2)
        ctx.events["loan_principal"]        = round(loan_principal, 2)
        ctx.events["loan_interest_rate"]    = loan_interest_rate
        ctx.events["loan_interest_payment"] = loan_interest_payment

    total_interest   = loan_interest_payment + emergency_credit_interest
    ctx.new_treasury = round(base_treasury + csf - total_interest, 2)

    # ── REC-1: Waterfall entries for core treasury movement ─────
    ctx.record_waterfall(
        "Gross Profit (CSF)", csf,
        because="Revenue minus OPEX across all BUs, net of dividends paid.",
        counterfactual="Higher synergy investment would have reduced OPEX and increased CSF.",
    )
    if loan_interest_payment > 0:
        ctx.record_waterfall(
            "Loan Interest", -loan_interest_payment,
            because=f"You borrowed ${loan_principal:,.0f} at {loan_interest_rate*100:.0f}% to fund CapEx exceeding free CSF.",
            counterfactual="If total CapEx stayed below CSF, no loan interest would be charged.",
        )
    if emergency_credit_interest > 0:
        ctx.record_waterfall(
            "Emergency Credit Interest", -emergency_credit_interest,
            because=f"Emergency credit line of $1M activated at {ctx.events.get('emergency_credit_rate', 0)*100:.0f}% (prevailing rate + 2%).",
            counterfactual="Without the emergency credit line, this interest charge would not apply.",
        )

    # ── FEATURE 13: Talent Allocation Pressure ───────────────────
    talent_surcharges = calc_talent_allocation_pressure(ctx.new_bus, ctx.decisions)
    for bu_id, surcharge in talent_surcharges.items():
        for bu in ctx.new_bus:
            if bu["bu_id"] == bu_id:
                bu["opex_base"] = round(bu["opex_base"] + surcharge, 2)
                ctx.events[f"talent_neglect_surcharge_{bu_id}"] = surcharge
                break

    # ── 8. Pending Projects ─────────────────────────────────────
    # FIX CRITICAL-3 + CRITICAL-4
    _proj_delta = _process_pending_projects(
        pending_projects=current_global.get("pending_capex_projects", []),
        new_this_tick=ctx.new_synergy_lag_projects,
    )
    ctx.new_pending_projects = _proj_delta.remaining_projects

    if _proj_delta.completed_projects:
        ctx.events["capex_project_completed"] = _proj_delta.completed_projects

    for drop in _proj_delta.ncd_drops:
        bu_target = drop["bu_target"]
        amount    = drop["amount"]
        for bu in ctx.new_bus:
            if bu_target == "all" or bu["bu_id"] == bu_target:
                bu["natural_capital_debt"] = max(
                    0.0, round(bu.get("natural_capital_debt", 0.0) + amount, 2)
                )

    if _proj_delta.resilience_factor:
        ctx.events["active_resilience_factor"] = _proj_delta.resilience_factor

    if _proj_delta.synergy_boost_total:
        ctx.events["synergy_boost_pending"] = _proj_delta.synergy_boost_total

    if _proj_delta.truth_premium:
        ctx.events["truth_premium_active"] = True

    for lag_bu_id, opex_reduction in _proj_delta.synergy_lag_completions.items():
        for bu in ctx.new_bus:
            if bu["bu_id"] == lag_bu_id:
                # BALANCE FIX: deferred synergy completions honour the same
                # opex floor as immediate reductions (synergy_opex_floor).
                bu["opex_base"] = max(
                    min(synergy_opex_floor(bu), bu["opex_base"]),
                    round(bu["opex_base"] - opex_reduction, 2),
                )
                ctx.events[f"synergy_lag_completed_{lag_bu_id}"] = opex_reduction
                break

    if _proj_delta.revenue_generation_total > 0:
        ctx.new_treasury = round(ctx.new_treasury + _proj_delta.revenue_generation_total, 2)
        ctx.events["revenue_generation_completed"] = _proj_delta.revenue_generation_total
        ctx.events["revenue_generation_desc"]      = _proj_delta.revenue_generation_desc
        ctx.record_waterfall(
            "Deferred Revenue Collection",
            _proj_delta.revenue_generation_total,
            because=(
                f"{_proj_delta.revenue_generation_desc} — working capital from "
                f"prior-round DSO cycle has been collected."
            ),
            counterfactual="Lower governance risk reduces DSO deferral and accelerates cash collection.",
        )

    if _proj_delta.education_lag_total:
        ctx.events["education_lag_matured"] = _proj_delta.education_lag_total

    # ── Natural Decay + Technical Debt + Technology Lock-In ──────
    for bu in ctx.new_bus:
        dec     = ctx.decision_map.get(bu["bu_id"], {})
        # FIX BUG-1C + FIX-B: SLO investment sensitivity with gradated decay
        _inv_ratio = ctx.events.get("_pre_austerity_avg_invest", dec.get("investment_ratio", 0))
        invested = _inv_ratio >= 0.15 or dec.get("capex_allocated", 0) > 0
        bu["reputation_score"], bu["social_license_score"] = apply_natural_decay(
            bu["reputation_score"], bu["social_license_score"], invested,
            investment_ratio=_inv_ratio,
        )

        # ── FEATURE 4: Technical Debt ───────────────────────────
        inv_ratio = dec.get("investment_ratio", 0.0)
        risk      = bu.get("risk_factors", {})
        streak    = risk.get("zero_investment_streak", 0)
        streak    = streak + 1 if inv_ratio == 0.0 else 0
        risk["zero_investment_streak"] = streak
        bu["risk_factors"] = risk

        new_opex, debt_hit = calc_technical_debt(bu["opex_base"], streak)
        if debt_hit:
            bu["opex_base"] = new_opex
            ctx.events[f"technical_debt_penalty_{bu['bu_id']}"] = True
            ctx.events[f"technical_debt_streak_{bu['bu_id']}"]  = streak

    # ── FEATURE 15: Technology Lock-In ───────────────────────────
    if ctx.decisions:
        top_dec    = max(ctx.decisions, key=lambda d: d.get("capex_allocated", 0))
        top_bu_id  = top_dec["bu_id"]
        top_capex  = top_dec.get("capex_allocated", 0)
        for bu in ctx.new_bus:
            risk = bu.get("risk_factors", {})
            if top_capex > 0 and bu["bu_id"] == top_bu_id:
                risk["top_investment_streak"] = risk.get("top_investment_streak", 0) + 1
            else:
                risk["top_investment_streak"] = 0
            bu["risk_factors"] = risk

    locked_bu, lockin_penalties = calc_technology_lockin(ctx.new_bus, ctx.decisions)
    if locked_bu:
        ctx.events["technology_lockin_bu"]      = locked_bu
        ctx.events["technology_lockin_penalty"] = True
        for bu_id, multiplier in lockin_penalties.items():
            ctx.events[f"lockin_synergy_penalty_{bu_id}"] = multiplier

    # ── 2. Contagion Engine ──────────────────────────────────────
    ctx.group_reputation = calc_contagion(ctx.new_bus, ctx.crisis_severity)

    # ── FEATURE 7: Stakeholder Fatigue ──────────────────────────
    crisis_count = current_global.get("active_event_flags", {}).get("crisis_count_lifetime", 0)
    if ctx.crisis_severity > 0:
        crisis_count += 1
    ctx.events["crisis_count_lifetime"] = crisis_count
    if crisis_count > 0:
        old_rep       = sum(bu["reputation_score"] for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)
        recovery_gap  = max(0, ctx.group_reputation - old_rep)
        if recovery_gap > 0:
            fatigued_recovery    = calc_stakeholder_fatigue(recovery_gap, crisis_count)
            ctx.group_reputation = round(old_rep + fatigued_recovery, 2)
            ctx.group_reputation = max(0.0, min(100.0, ctx.group_reputation))
            ctx.events["stakeholder_fatigue_applied"]    = True
            ctx.events["stakeholder_fatigue_efficiency"] = round(1.0 / (1.0 + 0.3 * crisis_count), 4)

    # ── 6. Talent Brain-Drain & Burnout ─────────────────────────
    for bu in ctx.new_bus:
        # Universal Burnout Passive Decay
        current_burnout = bu.get("staff_burnout_index", 0.0)
        if bu["bu_id"] in ("hospitals", "clinics", "specialised_care", "telehealth"):
            if current_burnout > 0:
                bu["staff_burnout_index"] = max(0.0, current_burnout - BURNOUT_PASSIVE_DECAY_HEALTHCARE)
                ctx.events[f"burnout_passive_decay_{bu['bu_id']}"] = BURNOUT_PASSIVE_DECAY_HEALTHCARE
        else:
            if current_burnout > 0:
                bu["staff_burnout_index"] = max(0.0, current_burnout - BURNOUT_PASSIVE_DECAY_DEFAULT)
                ctx.events[f"burnout_passive_decay_{bu['bu_id']}"] = BURNOUT_PASSIVE_DECAY_DEFAULT

        if bu["bu_id"] in ("software", "hospitals", "clinics"):
            if bu["bu_id"] in ("hospitals", "clinics"):
                utilization = bu.get("bed_capacity_utilization", 0.0)
                if utilization > UTILIZATION_OVERLOAD_THRESHOLD:
                    bu["staff_burnout_index"] = min(100.0, bu.get("staff_burnout_index", 0.0) + UTILIZATION_OVERLOAD_BURNOUT_INC)
                    ctx.events[f"utilization_overload_fatigue_{bu['bu_id']}"] = True
                current_util       = bu.get("bed_capacity_utilization", 0.0)
                utilization_drift  = round((100.0 - current_util) * UTILIZATION_DRIFT_RATE, 2)
                bu["bed_capacity_utilization"] = min(100.0, round(current_util + utilization_drift, 2))
                ctx.events[f"bed_utilization_drift_{bu['bu_id']}"] = utilization_drift

            old_opex = bu["opex_base"]
            bu["opex_base"], talent_penalty = calc_talent_braindrain(
                bu["opex_base"], ctx.group_reputation, bu.get("staff_burnout_index", 0.0)
            )
            ctx.events[f"talent_penalty_applied_{bu['bu_id']}"] = talent_penalty
            if talent_penalty:
                ctx.events[f"braindrain_opex_impact_{bu['bu_id']}"] = {
                    "old_opex":    old_opex,
                    "new_opex":    bu["opex_base"],
                    "penalty_pct": round(((bu["opex_base"] - old_opex) / max(old_opex, 1)) * 100, 1),
                    "trigger":     f"Group reputation ({ctx.group_reputation:.0f}) below brain-drain threshold (25)",
                }
            if bu["bu_id"] == "software":
                ctx.events["talent_penalty_applied"] = talent_penalty

    # ── 4. Natural Capital Cost of Debt — per BU ────────────────
    interest_rates: dict[str, float] = {}
    # Start from the field (may have been modified in stochastic stage via macro_rate)
    corporate_cost_of_capital = ctx.corporate_cost_of_capital

    # ── FEATURE 21: Apply macro rate to CoC ─────────────────────
    macro_rate = ctx.events.get("macro_rate_environment", {})
    corporate_cost_of_capital = round(
        corporate_cost_of_capital + macro_rate.get("coc_modifier", 0.0), 4
    )
    ctx.events["coc_macro_rate_applied"] = macro_rate.get("coc_modifier", 0.0)
    ctx.corporate_cost_of_capital        = corporate_cost_of_capital

    ncd_transparency: dict[str, dict] = {}
    for bu in ctx.new_bus:
        old_ncd    = bu.get("natural_capital_debt", 0)
        rate       = calc_natural_capital_interest(corporate_cost_of_capital, old_ncd)
        interest_rates[bu["bu_id"]] = rate
        debt_charge = round(old_ncd * rate, 2)
        new_ncd     = round(old_ncd + debt_charge, 2)
        # FIX VULN-007: Cap NCD at NCD_HARD_CAP
        bu["natural_capital_debt"] = min(new_ncd, NCD_HARD_CAP)
        # HARD-001: NCD soft-cap warning
        if bu["natural_capital_debt"] >= NCD_WARN_THRESHOLD and old_ncd < NCD_WARN_THRESHOLD:
            ctx.events[f"ncd_credit_downgrade_{bu['bu_id']}"] = True
            ctx.events.setdefault("custom_black_swans", []).append({
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
        # FIX BUG-1D: NCD accumulation based on investment_ratio
        # Low investment = deferred environmental maintenance → NCD grows
        # High investment = active remediation → NCD shrinks
        _bu_dec = ctx.decision_map.get(bu["bu_id"], {})
        _bu_inv = _bu_dec.get("investment_ratio", 0)
        if _bu_inv < 0.20:
            _ncd_accum = (0.20 - _bu_inv) * bu.get("carbon_intensity", 30) * 0.5
            bu["natural_capital_debt"] = min(
                bu["natural_capital_debt"] + _ncd_accum, NCD_HARD_CAP
            )
        elif _bu_inv >= 0.30:
            _ncd_reduction = (_bu_inv - 0.25) * 10
            bu["natural_capital_debt"] = max(0, bu["natural_capital_debt"] - _ncd_reduction)
        ncd_transparency[bu["bu_id"]] = {
            "old_ncd":          old_ncd,
            "interest_rate_pct": round(rate * 100, 2),
            "interest_charge":  debt_charge,
            "new_ncd":          bu["natural_capital_debt"],
        }
    ctx.events["interest_rates"]     = interest_rates
    ctx.events["ncd_transparency"]   = ncd_transparency

    # ── 5. VRIO Decay ────────────────────────────────────────────
    # FIX AUDIT-006 + FIX CRITICAL-3: decay uses pre_tick_synergy baseline;
    # synergy_boost from completed projects is added AFTER decay.
    # FIX BUG-1B: Investment-responsive synergy decay — continuous reinvestment
    # slows imitation (VRIO theory: sustained advantage requires reinvestment)
    # Use pre-austerity ratio so austerity doesn't negate ESG commitment
    _avg_invest_syn = ctx.events.get("_pre_austerity_avg_invest", 0)
    # 0% invest → full decay; 50% invest → half decay; floor at 20% of base rate
    _effective_decay = ctx.imitation_decay_rate * max(0.2, 1.0 - _avg_invest_syn)
    new_synergy = calc_vrio_decay(ctx.pre_tick_synergy, _effective_decay)
    ctx.events["synergy_decayed_from"] = ctx.pre_tick_synergy
    if _proj_delta.synergy_boost_total:
        new_synergy = round(new_synergy + _proj_delta.synergy_boost_total, 4)
        ctx.events["synergy_boost_applied"] = _proj_delta.synergy_boost_total
    ctx.new_synergy = new_synergy

    # ── 7. Strike Probability — per BU ──────────────────────────
    strike_probs: dict[str, float] = {}
    for bu in ctx.new_bus:
        gov_risk  = bu.get("governance_risk_score", 0)
        base_risk = gov_risk / 100.0
        p         = calc_strike_probability(base_risk, bu["social_license_score"])
        strike_probs[bu["bu_id"]] = p
    ctx.events["strike_probabilities"] = strike_probs

    # ── Derived Dashboard Metrics ────────────────────────────────
    ctx.historical_ebitda = round(
        sum(bu["revenue_base"] - bu["opex_base"] for bu in ctx.new_bus), 2
    )
    ctx.tco2e_emissions = round(
        sum(
            bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000
            for bu in ctx.new_bus
        ), 1
    )
    # I4: Absolute emissions per BU
    for bu in ctx.new_bus:
        bu["absolute_emissions"] = round(
            bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000, 2
        )

    # Carbon emissions constraint
    if ctx.tco2e_emissions > CONSTRAINT_MAX_CARBON_EMISSIONS:
        ctx.events["emissions_limit_breached"] = True
        ctx.events.setdefault("custom_black_swans", []).append({
            "title": "⚠️ CARBON EMISSIONS LIMIT BREACHED",
            "narrative": (
                f"Total carbon emissions ({ctx.tco2e_emissions:,.0f} tCO₂e) have exceeded "
                f"the maximum constraint of {CONSTRAINT_MAX_CARBON_EMISSIONS:,.0f} tCO₂e. "
                "Investor pressure and regulatory scrutiny are rising."
            ),
            "icon": "⚠️",
            "severity": "high",
        })
        _rep_before_penalty   = ctx.group_reputation
        ctx.group_reputation  = max(0.0, round(ctx.group_reputation - EMISSIONS_BREACH_REP_PENALTY, 2))
        ctx.events["emissions_rep_penalty"] = {
            "rep_before": _rep_before_penalty,
            "rep_after":  ctx.group_reputation,
            "deduction":  round(_rep_before_penalty - ctx.group_reputation, 2),
        }

    # ── CAROIC ──────────────────────────────────────────────────
    _shadow_carbon_price = current_global.get("active_event_flags", {}).get(
        "carbon_tax_per_ton",
        current_global.get("active_event_flags", {}).get("shadow_carbon_price", FINANCIAL_SHADOW_CARBON_PRICE),
    )
    _ic_proxy    = max(0.0, sum(bu.get("revenue_base", 0) for bu in ctx.new_bus) * 0.5)
    caroic_result = calc_caroic(
        ebitda=ctx.historical_ebitda,
        invested_capital=_ic_proxy,
        carbon_tonnage=ctx.tco2e_emissions,
        tax_rate=FINANCIAL_CORPORATE_TAX_RATE,
        shadow_carbon_price=_shadow_carbon_price,
    )
    caroic_result["invested_capital_method"] = "revenue_proxy_0.5x"
    ctx.events["caroic"] = caroic_result

    # ── Negative-Treasury Debt Service + Insolvency ──────────────
    if ctx.new_treasury < 0:
        debt_service     = round(abs(ctx.new_treasury) * corporate_cost_of_capital, 2)
        ctx.new_treasury = round(ctx.new_treasury - debt_service, 2)
        # FIX BUG-1A: Dynamic treasury floor — ESG-committed firms have better credit lines
        # Use pre-austerity investment ratio so austerity clamp doesn't zero the floor
        _avg_invest_floor = ctx.events.get("_pre_austerity_avg_invest", 0)
        # Better investors get a less punitive floor (lenders trust ESG-committed firms)
        # Up to +$200M floor relief at 100% investment ratio
        _floor_adjustment = _avg_invest_floor * 200_000_000
        _adjusted_floor = FINANCIAL_TREASURY_FLOOR + _floor_adjustment
        # DEEP-8 term 8 (2026-09-01): event the clamp so the treasury ledger
        # can account for the money the floor forgave. Diagnostics only — the
        # clamped value itself is unchanged.
        _pre_clamp = ctx.new_treasury
        ctx.new_treasury = max(ctx.new_treasury, _adjusted_floor)
        _clamp_credit = round(ctx.new_treasury - _pre_clamp, 2)
        if _clamp_credit > 0:
            ctx.events["treasury_floor_clamp_applied"] = round(
                float(ctx.events.get("treasury_floor_clamp_applied", 0.0)) + _clamp_credit, 2
            )
            ctx.record_waterfall(
                "Insolvency Floor Relief", _clamp_credit,
                because=(
                    f"Creditors will not extend losses below the treasury floor "
                    f"(${_adjusted_floor:,.0f}); ${_clamp_credit:,.0f} of this round's "
                    f"losses were absorbed by the floor."
                ),
                counterfactual="A higher ESG investment ratio raises the floor (better credit lines).",
            )
        ctx.events["negative_treasury_interest_applied"] = debt_service
        ctx.events["negative_treasury_interest_because"] = (
            f"Your treasury is negative. Creditors charge {corporate_cost_of_capital*100:.1f}% "
            f"interest on the outstanding debt of ${abs(ctx.new_treasury):,.0f}."
        )
        ctx.record_waterfall(
            "Debt Service Interest", -debt_service,
            because=f"Negative treasury incurs {corporate_cost_of_capital*100:.1f}% interest on ${abs(ctx.new_treasury+debt_service):,.0f} debt.",
            counterfactual="A positive treasury eliminates debt servicing costs entirely.",
        )
        if ctx.new_treasury < FINANCIAL_INSOLVENCY_THRESHOLD:
            ctx.events["insolvency_active"]  = True
            ctx.events["insolvency_message"] = (
                f"CREDIT DOWNGRADE: Treasury has breached ${FINANCIAL_INSOLVENCY_THRESHOLD/1e6:.0f}M. "
                "Mandatory austerity: all discretionary CapEx capped at 50%, "
                "dividend suspension in effect."
            )
            ctx.events["capex_cap_multiplier"] = 0.50
            ctx.events["dividend_suspended"]   = True

    # Store loan_principal on ctx so the reporting layer can check CFO austerity
    ctx.events["_loan_principal_internal"] = loan_principal
    ctx.events["_base_treasury_internal"]  = base_treasury


# ── Stage 3: Operational Layer ───────────────────────────────────
# ESG WACC → Scope 1/2/3 → SBTi → EU Taxonomy → Climate VaR →
# Tipping Point → Loss & Damage → SDG Non-Linear Feedback →
# Carbon Fee → Inflation Drift

def _run_operational_layer(ctx: TickContext) -> None:
    """
    Stage 3 — long-run sustainability, ESG, climate tipping points,
    SDG feedback loops, and the internal carbon fee mechanism.
    """
    current_global = ctx.current_global
    avg_ci         = _calc_rw_avg_ci(ctx.new_bus)

    # Hard-clamp all BU sub-scores before ESG calculations
    _pre_aust_inv_op = ctx.events.get("_pre_austerity_avg_invest", 0)
    for bu in ctx.new_bus:
        bu["social_license_score"]  = max(0.0, min(100.0, bu.get("social_license_score", 50.0)))
        bu["governance_risk_score"] = max(0.0, min(100.0, bu.get("governance_risk_score", 20.0)))
        bu["carbon_intensity"]      = max(0.0, bu.get("carbon_intensity", 50.0))

        # FIX-E: Investment-driven carbon reduction
        # High investment → active decarbonization (ESG CAPEX reduces emissions)
        # Low investment → emissions creep from deferred maintenance
        if _pre_aust_inv_op >= 0.25:
            bu["carbon_intensity"] *= (1.0 - _pre_aust_inv_op * 0.10)  # up to -5%/round
        elif _pre_aust_inv_op < 0.10:
            bu["carbon_intensity"] *= 1.02  # +2% emissions creep

        # FIX-F: Option-driven emissions impact
        _bu_dec_op = ctx.decision_map.get(bu["bu_id"], {})
        _choice = _bu_dec_op.get("choice_selected", "")
        if _choice == "option_a":
            bu["carbon_intensity"] = max(0, bu["carbon_intensity"] - 3)  # Green tech
        elif _choice == "option_c":
            bu["carbon_intensity"] += 2  # Cost-cutting = dirtier ops

        bu["carbon_intensity"] = round(max(0.0, bu["carbon_intensity"]), 2)

    # ── PHASE-1: ESG-Adjusted WACC ───────────────────────────────
    try:
        from systemic_risk_engine import calc_esg_adjusted_wacc, calc_supply_chain_transparency, calc_employer_brand, get_foreshadowing_for_round
        n_bu      = max(len(ctx.new_bus), 1)
        _avg_ci   = avg_ci
        _avg_gov  = sum(bu.get("governance_risk_score", 20) for bu in ctx.new_bus) / n_bu
        _avg_slo  = sum(bu.get("social_license_score", 50) for bu in ctx.new_bus) / n_bu
        _avg_water = sum(bu.get("water_dependency", 0) for bu in ctx.new_bus) / n_bu
        _sct       = current_global.get("active_event_flags", {}).get("supply_chain_transparency", 30)

        esg_wacc, esg_wacc_diag = calc_esg_adjusted_wacc(
            ctx.corporate_cost_of_capital, _avg_ci, _avg_gov, _avg_slo, _avg_water, _sct
        )
        ctx.corporate_cost_of_capital  = esg_wacc
        ctx.events["esg_adjusted_wacc"] = esg_wacc_diag

        _sct_new, _sct_diag = calc_supply_chain_transparency(
            _sct, current_global.get("active_event_flags", {}), current_global["round_number"]
        )
        ctx.events["supply_chain_transparency"]      = _sct_new
        ctx.events["supply_chain_transparency_diag"] = _sct_diag

        _avg_burnout       = sum(bu.get("staff_burnout_index", 0) for bu in ctx.new_bus) / n_bu
        _workforce_readiness = current_global.get("active_event_flags", {}).get("workforce_readiness", 50)
        _eb, _eb_diag = calc_employer_brand(ctx.group_reputation, _avg_burnout, _workforce_readiness)
        ctx.events["employer_brand"] = _eb_diag

        if _eb < EMPLOYER_BRAND_PENALTY_THRESHOLD:
            eb_opex_multiplier = round(((EMPLOYER_BRAND_PENALTY_THRESHOLD - _eb) / EMPLOYER_BRAND_PENALTY_THRESHOLD) * EMPLOYER_BRAND_MAX_PENALTY_RATE, 4)
            eb_total_penalty   = 0.0
            for bu in ctx.new_bus:
                bu_opex  = bu.get("opex_base", 0)
                penalty  = round(bu_opex * eb_opex_multiplier, 2)
                bu["opex_base"] = round(bu_opex + penalty, 2)
                eb_total_penalty += penalty
            ctx.events["employer_brand_opex_penalty"] = {
                "multiplier":        eb_opex_multiplier,
                "total_penalty":     round(eb_total_penalty, 2),
                "employer_brand_score": _eb,
                "affected_bus":      len(ctx.new_bus),
                "narrative": (
                    f"⚠️ TALENT CRISIS: Employer brand score has fallen to {_eb:.0f}/100. "
                    f"Recruitment costs surging across all divisions — "
                    f"${eb_total_penalty/1_000_000:.1f}M in additional OPEX."
                ),
            }

        _foreshadowing = get_foreshadowing_for_round(
            current_global["round_number"], current_global.get("active_event_flags", {})
        )
        if _foreshadowing:
            ctx.events["foreshadowing_signals"] = _foreshadowing
    except ImportError:
        pass

    # Stranded Asset Decay
    if ctx.decision_paradigm == "advanced_climate":
        stranded_assets = [bu for bu in ctx.new_bus if bu.get("carbon_intensity", 0) > STRANDED_ASSET_CI_THRESHOLD]
        if stranded_assets:
            ctx.corporate_cost_of_capital = round(ctx.corporate_cost_of_capital + STRANDED_ASSET_COC_SURCHARGE, 4)
            ctx.events["stranded_asset_penalty_applied"] = True
            ctx.events["stranded_asset_bu_ids"]          = [bu["bu_id"] for bu in stranded_assets]
            ctx.events["divestment_pressure_active"]     = True
            ctx.events["divestment_pressure_message"]    = (
                f"INVESTOR ALERT: {len(stranded_assets)} business unit(s) have carbon intensity "
                f"above {STRANDED_ASSET_CI_THRESHOLD} — classified as stranded assets by climate-aware investors. "
                f"Institutional shareholders are demanding a credible decarbonisation pathway "
                f"or forced divestiture. Cost of capital increased by +1.5%."
            )

    # ── Toxic OPEX Penalty (NCD Multiplier) ─────────────────────
    hostility_multiplier = current_global.get("active_event_flags", {}).get("market_hostility_index", 5)
    tipping_tier         = current_global.get("tipping_tier", "none")
    if ctx.decision_paradigm == "advanced_climate":
        if tipping_tier == "tipped":
            hostility_multiplier = round(hostility_multiplier * TIPPING_HOSTILITY_TIPPED, 2)
            ctx.events["tipping_tier_active"] = "tipped"
        elif tipping_tier == "stressed":
            hostility_multiplier = round(hostility_multiplier * TIPPING_HOSTILITY_STRESSED, 2)
            ctx.events["tipping_tier_active"] = "stressed"
        elif tipping_tier == "warning":
            hostility_multiplier = round(hostility_multiplier * TIPPING_HOSTILITY_WARNING, 2)
            ctx.events["tipping_tier_active"] = "warning"
        if current_global.get("tipping_point_active", False) and avg_ci < 50:
            ctx.events["tipping_point_managed_retreat"] = True

        # NCD Forgiveness (logarithmic, green capex)
        total_green_capex = sum(d.get("capex_allocated", 0) for d in ctx.decisions)
        if total_green_capex > 0:
            green_capex_m     = total_green_capex / 1_000_000
            forgiveness_per_bu = round(NCD_FORGIVENESS_LOG_COEFF * math.log(1 + green_capex_m), 2)
            for bu in ctx.new_bus:
                old_ncd = bu.get("natural_capital_debt", 0)
                if old_ncd > 0 and forgiveness_per_bu > 0:
                    bu["natural_capital_debt"] = max(0, round(old_ncd - forgiveness_per_bu, 2))
            if forgiveness_per_bu > 0:
                ctx.events["ncd_forgiveness_applied"] = forgiveness_per_bu
                ctx.events["ncd_forgiveness_formula"] = "2.0 × ln(1 + CapEx_M$)"

        # CBAM Border Adjustment (rounds 3 & 7, Scope1+2 only)
        round_number = current_global.get("round_number", 1)
        if round_number in (3, 7) and avg_ci > CBAM_CI_THRESHOLD:
            cbam_tco2e = sum(
                (bu.get("scope_1_ci", 0) + bu.get("scope_2_ci", 0))
                * bu["revenue_base"] / 1_000_000
                for bu in ctx.new_bus
            )
            cbam_avg_ci_12 = round(
                sum((bu.get("scope_1_ci", 0) + bu.get("scope_2_ci", 0)) for bu in ctx.new_bus)
                / max(len(ctx.new_bus), 1), 2
            )
            if cbam_avg_ci_12 > CBAM_CI_THRESHOLD * CBAM_SCOPE12_FRACTION:
                cbam_surcharge        = round(cbam_tco2e * CBAM_SURCHARGE_RATE, 2)
                ctx.new_treasury      = round(ctx.new_treasury - cbam_surcharge, 2)
                ctx.events["cbam_surcharge_applied"] = cbam_surcharge
                ctx.events["cbam_message"] = (
                    f"EU CBAM border adjustment (R{round_number} supply chain/circularity): "
                    f"Scope1+2 avg CI {cbam_avg_ci_12:.1f} | Total Scope1+2 tCO₂e: {cbam_tco2e:.0f}. "
                    f"Import carbon surcharge: -${cbam_surcharge:,.0f} (I11: rounds 3&7; I15: Scope1+2 only)"
                )

        for bu in ctx.new_bus:
            ncd              = max(0, bu.get("natural_capital_debt", 0))
            ncd_opex_penalty = round((ncd * NCD_OPEX_SCALING_FACTOR * hostility_multiplier) / 1_000_000, 2)
            max_penalty      = bu.get("revenue_base", 0) * (0.75 if tipping_tier == "tipped" else 0.50)
            ncd_opex_penalty = min(ncd_opex_penalty, max_penalty)
            if ncd_opex_penalty > 0:
                bu["opex_base"] = round(bu["opex_base"] + ncd_opex_penalty, 2)
                ctx.events[f"{bu['bu_id']}_opex_ncd_penalty"] = ncd_opex_penalty

        # Scope 1/2/3 tagging (I5)
        scope_details = {}
        for bu in ctx.new_bus:
            ci     = bu.get("carbon_intensity", 0)
            ratios = get_scope_ratios(bu["bu_id"])
            bu["scope_1_ci"] = round(ci * ratios["scope_1"], 2)
            bu["scope_2_ci"] = round(ci * ratios["scope_2"], 2)
            bu["scope_3_ci"] = round(ci * ratios["scope_3"], 2)
            scope_details[bu["bu_id"]] = {
                "scope_1_pct": round(ratios["scope_1"] * 100),
                "scope_2_pct": round(ratios["scope_2"] * 100),
                "scope_3_pct": round(ratios["scope_3"] * 100),
                "scope_1_ci":  bu["scope_1_ci"],
                "scope_2_ci":  bu["scope_2_ci"],
                "scope_3_ci":  bu["scope_3_ci"],
            }
        ctx.events["scope_transparency"] = {
            "bu_scope_details": scope_details,
            "total_ci":         round(avg_ci, 2),
            "note": "Scope 1/2/3 ratios cover ALL BU types incl. verticals (I5 upgrade). Banking=95% Scope3 financed.",
        }

        # SBTi Pathway (I3, I12, I14)
        round_num      = current_global.get("round_number", 1)
        sbti_target_ci = round(SBTI_BASELINE_CI * (1 - SBTI_ANNUAL_REDUCTION_RATE) ** (round_num - 1), 2)
        sbti_aligned   = avg_ci <= sbti_target_ci
        per_bu_sbti    = {}
        for bu in ctx.new_bus:
            bu_baseline_ci = bu.get("ci_baseline_r1", bu.get("carbon_intensity", 50.0))
            bu_sbti_target = round(bu_baseline_ci * (1 - SBTI_ANNUAL_REDUCTION_RATE) ** (round_num - 1), 2)
            bu_aligned     = bu.get("carbon_intensity", 0) <= bu_sbti_target
            per_bu_sbti[bu["bu_id"]] = {
                "target_ci": bu_sbti_target,
                "actual_ci": bu.get("carbon_intensity", 0),
                "aligned":   bu_aligned,
            }
        sbti_history = list(current_global.get("sbti_pathway_history", []))
        sbti_history.append({
            "round":     round_num,
            "target_ci": sbti_target_ci,
            "actual_ci": round(avg_ci, 2),
            "aligned":   sbti_aligned,
            "gap":       round(avg_ci - sbti_target_ci, 2),
        })
        consecutive_aligned    = sum(1 for _ in
            __import__("itertools").takewhile(lambda e: e["aligned"],    reversed(sbti_history)))
        consecutive_misaligned = sum(1 for _ in
            __import__("itertools").takewhile(lambda e: not e["aligned"], reversed(sbti_history)))
        if consecutive_misaligned >= SBTI_MISALIGNMENT_ROUNDS:
            sbti_coc_surcharge                = SBTI_COC_SURCHARGE
            ctx.corporate_cost_of_capital     = round(ctx.corporate_cost_of_capital + sbti_coc_surcharge, 4)
            ctx.events["sbti_coc_surcharge_applied"] = sbti_coc_surcharge
            ctx.events["sbti_coc_surcharge_message"] = (
                f"SBTi misalignment for {consecutive_misaligned} consecutive rounds. "
                f"Institutional investors apply +0.5% CoC surcharge (I12). "
                f"Decarbonise to reverse."
            )
        ctx.events["sbti_pathway"] = {
            "target_ci":                   sbti_target_ci,
            "actual_ci":                   round(avg_ci, 2),
            "aligned":                     sbti_aligned,
            "consecutive_aligned_rounds":  consecutive_aligned,
            "consecutive_misaligned_rounds": consecutive_misaligned,
            "credibility_score":           min(100, consecutive_aligned * SBTI_CREDIBILITY_PER_ROUND),
            "history":                     sbti_history,
            "per_bu_targets":              per_bu_sbti,
            "message": (
                f"SBTi 1.5°C target for R{round_num}: CI \u2264 {sbti_target_ci:.1f} (rev-weighted). "
                f"Actual: {avg_ci:.1f}. {'✅ ON TRACK' if sbti_aligned else '❌ OFF TRACK'}. "
                f"Credibility: {min(100, consecutive_aligned * SBTI_CREDIBILITY_PER_ROUND)}%"
            ),
        }

        # EU Taxonomy Alignment
        taxonomy_aligned_rev = sum(bu["revenue_base"] for bu in ctx.new_bus if bu.get("carbon_intensity", 100) < EU_TAXONOMY_CI_THRESHOLD)
        total_rev            = sum(bu["revenue_base"] for bu in ctx.new_bus)
        # VUL-014 FIX: `or 1` guard produces misleading % when total_rev=0 but
        # taxonomy_aligned_rev is nonzero. Use explicit guard instead.
        taxonomy_pct         = round((taxonomy_aligned_rev / total_rev) * 100, 1) if total_rev > 0 else 0.0
        ctx.events["eu_taxonomy_alignment_pct"] = taxonomy_pct
        if taxonomy_pct > EU_TAXONOMY_GREEN_THRESHOLD:
            ctx.events["taxonomy_green_finance_discount"] = True
            ctx.events["taxonomy_coc_benefit"]            = EU_TAXONOMY_COC_BENEFIT
        elif taxonomy_pct < EU_TAXONOMY_BROWN_THRESHOLD:
            ctx.events["taxonomy_brown_penalty"]    = True
            ctx.events["taxonomy_coc_surcharge"]    = EU_TAXONOMY_COC_SURCHARGE

        # Climate VaR
        active_resilience   = ctx.events.get("active_resilience_factor", 0.0)
        cyclone_prob        = CYCLONE_PROB_BASE
        tipping_tier_local  = current_global.get("tipping_tier", "none")
        if tipping_tier_local == "tipped":   cyclone_prob = CYCLONE_PROB_TIPPED
        elif tipping_tier_local == "stressed": cyclone_prob = CYCLONE_PROB_STRESSED
        elif tipping_tier_local == "warning":  cyclone_prob = CYCLONE_PROB_WARNING
        physical_var        = round(cyclone_prob * PHYSICAL_VAR_DAMAGE_BASE * (1 - active_resilience), 2)
        stranded_exposure   = sum(bu["revenue_base"] for bu in ctx.new_bus if bu.get("carbon_intensity", 0) > TRANSITION_VAR_CI_THRESHOLD)
        base_fee            = current_global.get("active_event_flags", {}).get("global_carbon_fee", ECONOMIC_CARBON_PRICE_BASE)
        fee_per_ton         = round(base_fee * (1 + ECONOMIC_CARBON_PRICE_GROWTH) ** (current_global.get("round_number", 1) - 1), 2)
        local_tco2e         = sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000 for bu in ctx.new_bus)
        local_carbon_fee    = round(local_tco2e * fee_per_ton, 2)
        transition_var      = round(stranded_exposure * TRANSITION_VAR_STRANDED_MULT + local_carbon_fee * TRANSITION_VAR_FEE_YEARS, 2)
        climate_var_total   = round(physical_var + transition_var, 2)
        ctx.events["climate_var"] = {
            "physical_var":          physical_var,
            "transition_var":        transition_var,
            "total_var":             climate_var_total,
            "physical_components":   f"P(cyclone)={cyclone_prob:.0%} × $12M × (1-{active_resilience:.2f})",
            "transition_components": f"Stranded exposure: ${stranded_exposure:,.0f} + Carbon fee 5yr: ${local_carbon_fee*5:,.0f}",
        }

        # Carbon Credit Futures Market
        if "carbon_deferred" in current_global.get("active_event_flags", {}):
            # FIX CRITICAL-2 (AUDIT): Use an independent Random instance
            # instead of re-importing the global random module.  This ensures
            # the carbon offset volatility does not depend on or perturb the
            # global PRNG state, and is reproducible when seeded externally.
            # GAME-4: seeded per-cohort stream so all teams see the same spot price.
            _offset_rng = event_rng(current_global.get("active_event_flags", {}),
                                    current_global["round_number"], "carbon_offset_volatility")
            spot_volatility  = _offset_rng.uniform(-0.30, 0.30)
            spot_price       = round(500_000 * (1 + spot_volatility), 2)
            active_forwards  = list(current_global.get("carbon_forwards", []))
            forward_payment  = 0
            remaining_forwards = []
            for fwd in active_forwards:
                if fwd["rounds_remaining"] > 0:
                    forward_payment += fwd["locked_price"]
                    remaining_fwd    = dict(fwd)
                    remaining_fwd["rounds_remaining"] -= 1
                    if remaining_fwd["rounds_remaining"] > 0:
                        remaining_forwards.append(remaining_fwd)
            if forward_payment > 0:
                offset_actual = forward_payment
                ctx.events["carbon_forward_used"]    = True
                ctx.events["carbon_forward_savings"] = spot_price - forward_payment
            else:
                offset_actual = spot_price
            ctx.new_treasury     = round(ctx.new_treasury - offset_actual, 2)
            forward_offer_price  = round(500_000 * 1.20, 2)
            ctx.events["carbon_offset_market"] = {
                "spot_price":          spot_price,
                "spot_volatility_pct": round(spot_volatility * 100, 1),
                "actual_cost_paid":    offset_actual,
                "forward_offer_price": forward_offer_price,
                "forward_duration":    3,
                "active_forwards":     len(remaining_forwards),
                "message": (
                    f"Carbon Market: Spot ${spot_price:,.0f} ({spot_volatility*100:+.1f}%). "
                    f"Paid: ${offset_actual:,.0f}. "
                    f"Forward contract available: ${forward_offer_price:,.0f}/round for 3 rounds."
                ),
            }

    # ── Internal Carbon Pricing (advanced_climate, I17) ─────────
    if ctx.decision_paradigm == "advanced_climate":
        base_carbon_fee      = current_global.get("active_event_flags", {}).get("global_carbon_fee", ECONOMIC_CARBON_PRICE_BASE)
        escalation_rate      = ECONOMIC_CARBON_PRICE_GROWTH
        round_number         = current_global.get("round_number", 1)
        carbon_fee_per_ton   = round(base_carbon_fee * (1 + escalation_rate) ** (round_number - 1), 2)
        round_carbon_fee_total = round(ctx.tco2e_emissions * carbon_fee_per_ton, 2)
        ctx.new_treasury       = round(ctx.new_treasury - round_carbon_fee_total, 2)
        ctx.new_green_fund_balance = round(ctx.new_green_fund_balance + round_carbon_fee_total, 2)
        prev_peak_fee        = current_global.get("active_event_flags", {}).get("peak_internal_carbon_fee", 0)
        ctx.events["peak_internal_carbon_fee"]     = max(prev_peak_fee, carbon_fee_per_ton)
        ctx.events["internal_carbon_fee_per_ton"]  = carbon_fee_per_ton
        ctx.events["internal_carbon_fee_deducted"] = round_carbon_fee_total
        ctx.events["internal_carbon_fee_because"]  = (
            f"Internal carbon price of ${carbon_fee_per_ton:,.0f}/tCO₂e applied to "
            f"{ctx.tco2e_emissions:,.0f} tonnes total emissions. Fee escalates {escalation_rate * 100:.1f}% per "
            f"6-month round."
        )
        ctx.record_waterfall(
            "Internal Carbon Fee", -round_carbon_fee_total,
            because=f"${carbon_fee_per_ton:,.0f}/tCO₂e × {ctx.tco2e_emissions:,.0f}t = ${round_carbon_fee_total:,.0f} transferred to Green Fund.",
            counterfactual="Reducing carbon intensity across BUs lowers this fee proportionally.",
        )
        ctx.events["carbon_fee_escalation_message"] = (
            f"Internal carbon fee: ${carbon_fee_per_ton:.0f}/tCO2e "
            f"(base ${base_carbon_fee:.0f} × {1 + escalation_rate}^{round_number-1}). Total levy: ${round_carbon_fee_total:,.0f}"
        )

    # ── Graduated Tipping Point ──────────────────────────────────
    tipping_point_active = current_global.get("tipping_point_active", False)
    tipping_tier         = current_global.get("tipping_tier", "none")
    if ctx.decision_paradigm == "advanced_climate" and current_global["round_number"] >= 3:
        if tipping_tier == "none" and avg_ci > TIPPING_CI_WARNING:
            tipping_tier = "warning"
            ctx.events["tipping_tier_escalated"] = "warning"
            ctx.events["custom_black_swans"] = ctx.events.get("custom_black_swans", []) + [{
                "title": "⚠️ CLIMATE WARNING THRESHOLD",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has exceeded 45. "
                    "Early warning: regulatory pressure is building. NCD costs "
                    "will increase by 25%. Decarbonise now or face escalating penalties."
                ),
                "icon": "⚠️", "severity": "warning",
            }]
        if tipping_tier == "warning" and avg_ci > TIPPING_CI_STRESSED:
            tipping_tier = "stressed"
            ctx.events["tipping_tier_escalated"] = "stressed"
            ctx.events["custom_black_swans"] = ctx.events.get("custom_black_swans", []) + [{
                "title": "🔶 CLIMATE STRESS THRESHOLD BREACHED",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has exceeded 55. "
                    "Markets are repricing climate risk. NCD costs compound at "
                    "1.75× hostility. The window for voluntary action is narrowing."
                ),
                "icon": "🔶", "severity": "high",
            }]
        if tipping_tier in ("warning", "stressed") and avg_ci > TIPPING_CI_TIPPED:
            tipping_tier         = "tipped"
            tipping_point_active = True
            ctx.events["tipping_point_reached"]    = True
            ctx.events["tipping_tier_escalated"]   = "tipped"
            ctx.events["custom_black_swans"] = ctx.events.get("custom_black_swans", []) + [{
                "title": "🌡️ CLIMATE TIPPING POINT BREACHED — IRREVERSIBLE",
                "narrative": (
                    f"Average carbon intensity ({avg_ci:.0f}) has crossed the irreversible "
                    "threshold (65). Natural capital debt costs now compound at 2.5× the rate. "
                    "Loss & damage levies are now mandatory. The era of voluntary "
                    "decarbonisation is over — every future round amplifies the cost of inaction."
                ),
                "icon": "🌡️", "severity": "critical",
            }]
        if not tipping_point_active and current_global["round_number"] >= 4 and avg_ci > TIPPING_CI_STRESSED:
            if tipping_tier == "none":
                tipping_tier = "stressed"
            tipping_point_active = True
            ctx.events["tipping_point_reached"] = True

        # Loss & Damage Levy
        if tipping_tier == "tipped":
            loss_damage_levy     = CLIMATE_LOSS_DAMAGE_LEVY_TIPPED
            ctx.new_treasury     = round(ctx.new_treasury - loss_damage_levy, 2)
            ctx.events["loss_damage_levy_applied"] = loss_damage_levy
            ctx.events["loss_damage_message"]      = (
                f"UNFCCC Loss & Damage Fund contribution: -${CLIMATE_LOSS_DAMAGE_LEVY_TIPPED/1e6:.0f}M. "
                "Post-tipping economies bear the cost of climate inaction "
                "through mandatory contributions to developing-economy adaptation."
            )
        elif tipping_tier == "stressed":
            loss_damage_levy     = CLIMATE_LOSS_DAMAGE_LEVY_STRESSED
            ctx.new_treasury     = round(ctx.new_treasury - loss_damage_levy, 2)
            ctx.events["loss_damage_levy_applied"] = loss_damage_levy
            ctx.events["loss_damage_message"]      = (
                "Climate adaptation contribution: -$500K. "
                "Pre-tipping regulatory pressure mandates partial climate liability."
            )

    # Store for final assembly
    ctx.events["_tipping_point_active_internal"] = tipping_point_active
    ctx.events["_tipping_tier_internal"]         = tipping_tier

    # ── UN SDG Non-Linear Feedback ───────────────────────────────
    if ctx.decision_paradigm == "un_sdg":
        for bu in ctx.new_bus:
            gov = bu.get("governance", 50)
            bu["institutional_leakage_multiplier"] = 0.60 if gov < 40 else 1.0
            if gov < 40:
                ctx.events[f"institutional_leakage_{bu['bu_id']}"] = True

        for bu in ctx.new_bus:
            bn = bu.get("basic_needs", 0)
            hc = bu.get("human_capital", 0)
            bu["sanitation_miracle_bonus"] = 2.0 if (bn > 75 and hc > 75) else 1.0
            if bn > 75 and hc > 75:
                ctx.events[f"sanitation_miracle_{bu['bu_id']}"] = True

        from sdg_configs import get_sdg_interlinkage_matrix
        matrix      = get_sdg_interlinkage_matrix()
        sdg_clusters = ["basic_needs", "human_capital", "sustainable_growth",
                        "planet", "governance", "partnerships"]
        for bu in ctx.new_bus:
            spillover_deltas = {c: 0.0 for c in sdg_clusters}
            for (source, target), multiplier in matrix.items():
                source_val = bu.get(source, 0)
                spillover_deltas[target] += multiplier * (source_val / 100.0)
            for cluster in sdg_clusters:
                old_val  = bu.get(cluster, 0)
                spillover = max(-5.0, min(5.0, spillover_deltas[cluster] * 10.0))
                decay     = old_val * 0.02
                bu[cluster] = round(max(0, min(100, old_val + spillover - decay)), 2)
            ctx.events[f"interlinkage_applied_{bu['bu_id']}"] = True

        global_emissions = _calc_rw_avg_ci(ctx.new_bus)
        ctx.events["global_emissions_intensity"] = round(global_emissions, 2)
        if current_global["round_number"] <= 5 and global_emissions > 100:
            retribution_penalty     = round(ctx.tco2e_emissions * 3.0 * 1000, 2)
            ctx.new_treasury        = round(ctx.new_treasury - retribution_penalty, 2)
            ctx.events["carbon_retribution_multiplier"] = 3.0
            ctx.events["carbon_retribution_triggered"]  = True
            ctx.events["carbon_retribution_penalty"]    = retribution_penalty
            ctx.events["carbon_retribution_message"]    = (
                f"UN SDG Carbon Retribution: group CI ({global_emissions:.0f}) exceeds 100. "
                f"Emergency climate levy: -${retribution_penalty:,.0f} (3× penalty on {ctx.tco2e_emissions:.0f} tCO₂e)."
            )

        if len(ctx.new_bus) > 1:
            highest_sg_bu = max(ctx.new_bus, key=lambda x: x.get("sustainable_growth", 0))
            ctx.events["migration_contagion_target"] = highest_sg_bu["bu_id"]
            total_pressure = sum(
                bu.get("migration_pressure", 0) for bu in ctx.new_bus
                if bu["bu_id"] != highest_sg_bu["bu_id"]
            )
            if total_pressure > 0:
                penalty = round(min(15.0, total_pressure * 0.3), 2)
                highest_sg_bu["basic_needs"]   = max(0, round(highest_sg_bu.get("basic_needs", 0) - penalty, 2))
                highest_sg_bu["human_capital"] = max(0, round(highest_sg_bu.get("human_capital", 0) - penalty * 0.5, 2))
                ctx.events["migration_service_penalty"]  = penalty
                ctx.events["migration_target_affected"]  = highest_sg_bu["bu_id"]

        avg_gov  = sum(bu.get("governance", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)
        avg_part = sum(bu.get("partnerships", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)
        ctx.sdg_political_capital = round((avg_gov + avg_part) / 2.0, 2)
        if ctx.sdg_political_capital < 30:
            budget_multiplier = 0.60
        elif ctx.sdg_political_capital < 50:
            budget_multiplier = 0.80
        else:
            budget_multiplier = round(1.0 + (ctx.sdg_political_capital - 50) / 200.0, 4)
        ctx.events["donor_fatigue_budget_multiplier"] = budget_multiplier
        ctx.events["political_capital_score"]         = ctx.sdg_political_capital
        ctx.sdg_community_trust = round(avg_gov * 0.6 + avg_part * 0.4, 2)
        ctx.events["community_trust_score"]           = ctx.sdg_community_trust

        for proj in ctx.new_pending_projects:
            if proj.get("type") == "education_lag" and proj.get("rounds_remaining", 1) <= 0:
                ctx.events["education_lag_mature"] = True
                boost = proj.get("amount", 0.8)
                for bu in ctx.new_bus:
                    old_sg = bu.get("sustainable_growth", 0)
                    bu["sustainable_growth"] = min(100, round(old_sg + boost * 10, 2))
                ctx.events["sdg_8_work_multiplier"] = 1.0 + boost

        ctx.events["global_emissions_intensity"] = round(_calc_rw_avg_ci(ctx.new_bus), 2)

    # ── Inflation drift ──────────────────────────────────────────
    hostility_multiplier = current_global.get("active_event_flags", {}).get("market_hostility_index", 5)
    if hostility_multiplier > 5:
        ctx.new_inflation_index = round(ctx.new_inflation_index + 0.010, 4)
        ctx.events["inflation_index_increased"]  = ctx.new_inflation_index
        ctx.events["inflation_drift_hostile"]    = True
        ctx.events["inflation_drift_message"]    = (
            f"Hostile regulatory environment is driving inflation above baseline. "
            f"OPEX inflation increased to {ctx.new_inflation_index * 100:.1f}%."
        )


# ── Stage 4: Reporting Layer ─────────────────────────────────────
# ESG Greenwashing → Turnaround / Distress → Regulatory Ratchet →
# Fog of War → VRIO Capabilities → Boundary Rounding →
# Competitor Pressure → Forecast → SDG Report → Waterfall →
# Momentum → Board Reflection → Systemic Tipping →
# Real-World Scenarios → Final Bounds Clamp → Stakeholder Sentiment

def _run_reporting_layer(ctx: TickContext) -> None:
    """
    Stage 4 — output metrics, governance mechanics, compliance checks,
    and stakeholder reporting.  No BU-level financial mutations after
    the bounds-clamp pass at the end of this stage.
    """
    current_global = ctx.current_global
    avg_ci         = _calc_rw_avg_ci(ctx.new_bus)

    # ── FEATURE 16: ESG Greenwashing Risk ────────────────────────
    primary_choice = ""
    for dec in ctx.decisions:
        c = dec.get("choice_selected", "")
        if c.startswith("option_"):
            primary_choice = c
            break
    _claim_level = resolve_green_claim(
        current_global.get("round_number", 1), primary_choice,
        ctx.new_bus, ctx.decision_paradigm,
    )
    greenwash_hit, greenwash_penalty = calc_greenwashing_risk(
        primary_choice, ctx.decisions, claim_level=_claim_level)
    # FIX-A: Use pre-austerity investment ratio for greenwashing check.
    # Without this, good players entering austerity are falsely punished for
    # greenwashing every round (austerity zeroes their investment_ratio).
    avg_inv_ratio = ctx.events.get("_pre_austerity_avg_invest", 0)
    if avg_inv_ratio == 0:  # fallback for tests without pre-austerity tracking
        avg_inv_ratio = sum(d.get("investment_ratio", 0) for d in ctx.decisions) / max(len(ctx.decisions), 1)
    # Override greenwash_hit: if pre-austerity investment was above threshold,
    # the team genuinely invested — austerity shouldn't trigger a false scandal
    if avg_inv_ratio >= GREENWASH_INVESTMENT_THRESHOLD:
        greenwash_hit = False
        greenwash_penalty = 0.0
    ctx.events["greenwashing_checked"]              = True
    ctx.events["greenwashing_avg_investment_ratio"] = round(avg_inv_ratio, 4)
    ctx.events["greenwashing_threshold"]            = 0.15
    ctx.events["greenwashing_risk_active"]          = greenwash_hit
    if greenwash_hit:
        for bu in ctx.new_bus:
            bu["social_license_score"] = max(0.0, round(bu["social_license_score"] - greenwash_penalty, 2))
        ctx.events["greenwashing_scandal"]      = True
        ctx.events["greenwashing_penalty"]      = greenwash_penalty
        ctx.events["greenwashing_message"]      = (
            "Greenwashing scandal! Your green rhetoric doesn't match "
            "your actual investment allocation. Public trust plummets. "
            f"Avg investment ratio: {avg_inv_ratio:.1%} vs. required 15%."
        )
        ctx.events["greenwashing_because"]      = (
            f"You chose a green option but allocated only {avg_inv_ratio:.1%} average "
            f"investment. The market requires ≥15% to back a green claim. "
            f"SLO penalty: −{greenwash_penalty:.0f} per BU."
        )
        ctx.events["greenwashing_counterfactual"] = (
            f"If you had allocated ≥15% average investment, this scandal "
            f"would not have fired. Alternatively, choosing a non-green option "
            f"avoids the greenwashing check entirely."
        )
    else:
        ctx.events["greenwashing_scandal"] = False
        ctx.events["greenwashing_message"] = (
            f"Greenwashing check passed. Avg investment ratio: {avg_inv_ratio:.1%} "
            f"({'above' if avg_inv_ratio >= 0.15 else 'below — no green option selected, hence no penalty'} "
            f"the 15% threshold)."
        )

    # ── FEATURE 25: Turnaround Pathway ──────────────────────────
    already_survival = current_global.get("active_event_flags", {}).get("survival_mode", False)
    current_phase    = current_global.get("active_event_flags", {}).get("turnaround_phase", "none")
    distress         = detect_distress(
        ctx.new_treasury, ctx.group_reputation,
        current_global["round_number"], already_survival, current_phase,
    )
    ctx.events["distress_detection"] = distress
    ctx.events["turnaround_phase"]   = distress.get("turnaround_phase", "none")

    if distress.get("distress_detected") and distress.get("bailout_amount"):
        bailout              = distress["bailout_amount"]
        ctx.new_treasury     = round(ctx.new_treasury + bailout, 2)
        ctx.events["survival_mode"]    = True
        ctx.events["bailout_applied"]  = bailout
        ctx.record_waterfall(
            "Emergency Bailout", bailout,
            because="Board-appointed Turnaround Manager activates emergency credit line.",
            counterfactual="Maintaining treasury > $0 and reputation > 30 prevents Survival Mode.",
        )
        ctx.events.setdefault("custom_black_swans", []).append({
            "title": "🚨 CRISIS — Turnaround Manager Appointed",
            "narrative": distress["message"],
            "icon": "🚨", "severity": "critical",
        })
    elif distress.get("phase_transition"):
        ctx.events["survival_mode"] = distress.get("survival_mode", True)
        ctx.events.setdefault("custom_black_swans", []).append({
            "title":     f"📋 TURNAROUND PHASE: {distress['turnaround_phase'].upper()}",
            "narrative": distress["message"],
            "icon":      "📋" if distress["turnaround_phase"] != "exit" else "✅",
            "severity":  "info" if distress.get("recovered") else "noteworthy",
        })
    elif distress.get("recovered"):
        ctx.events["survival_mode"] = False
        ctx.events.setdefault("custom_black_swans", []).append({
            "title": "✅ TURNAROUND COMPLETE — Comeback Achieved",
            "narrative": distress["message"],
            "icon": "✅", "severity": "info",
        })
    else:
        ctx.events["survival_mode"] = distress.get("survival_mode", False)

    # ── FEATURE 9: Regulatory Ratchet ───────────────────────────
    historical_coc_max = current_global.get("active_event_flags", {}).get(
        "regulatory_floor_coc", current_global.get("cost_of_capital", 0.05)
    )
    # FIX-D: Allow regulatory floor erosion for sustained ESG improvers.
    # If current ESG-adjusted CoC is significantly below the ratchet floor,
    # the team has genuinely improved — erode the floor by 0.5% per round.
    _pre_aust_inv = ctx.events.get("_pre_austerity_avg_invest", 0)
    if ctx.corporate_cost_of_capital < historical_coc_max * 0.95 and _pre_aust_inv >= 0.20:
        historical_coc_max = max(0.05, historical_coc_max - 0.005)
        ctx.events["regulatory_floor_eroded"] = True
    if ctx.corporate_cost_of_capital < historical_coc_max:
        ctx.corporate_cost_of_capital = historical_coc_max
        ctx.events["regulatory_ratchet_active"] = True
    ctx.events["regulatory_floor_coc"] = max(historical_coc_max, ctx.corporate_cost_of_capital)

    # ── FEATURE 14: Fog of War ───────────────────────────────────
    fog_active  = current_global.get("round_number", 1) <= 2
    deep_audit  = "deep_audit_completed" in current_global.get("active_event_flags", {})
    if fog_active and not deep_audit:
        ctx.events["fog_of_war_active"] = True
        fog_noise: dict[str, dict] = {}
        for bu in ctx.new_bus:
            # GAME-4: per-BU seeded stream (fog of war noise identical per cohort).
            _fog_rng = event_rng(current_global.get("active_event_flags", {}),
                                 current_global["round_number"], f"fog:{bu['bu_id']}")
            fog_noise[bu["bu_id"]] = {
                "natural_capital_debt_noise": round(_fog_rng.uniform(-0.10, 0.10), 4),
                "social_license_noise":       round(_fog_rng.uniform(-0.10, 0.10), 4),
                "governance_risk_noise":      round(_fog_rng.uniform(-0.10, 0.10), 4),
            }
        ctx.events["fog_noise"] = fog_noise
    else:
        ctx.events["fog_of_war_active"] = False

    # ── VRIO Capabilities ────────────────────────────────────────
    n      = len(ctx.new_bus) or 1
    avg_sl = sum(bu.get("social_license_score", 50) for bu in ctx.new_bus) / n
    avg_gr = sum(bu.get("governance_risk_score", 20) for bu in ctx.new_bus) / n
    avg_ci_v = _calc_rw_avg_ci(ctx.new_bus)
    ctx.vrio_capabilities = {
        "value":         round(max(0, min(100, avg_sl)), 1),
        "rarity":        round(max(0, min(100, 100 - avg_ci_v)), 1),
        "imitability":   round(max(0, min(100, ctx.new_synergy * 100)), 1),
        "organization":  round(max(0, min(100, 100 - avg_gr)), 1),
    }

    # ── HARD-004: Boundary Rounding Normalisation ────────────────
    for bu in ctx.new_bus:
        bu["revenue_base"]          = round(bu["revenue_base"], 2)
        bu["opex_base"]             = round(bu["opex_base"], 2)
        bu["natural_capital_debt"]  = round(bu.get("natural_capital_debt", 0), 2)
        bu["social_license_score"]  = round(bu.get("social_license_score", 50.0), 2)
        bu["governance_risk_score"] = round(bu.get("governance_risk_score", 20.0), 2)
        bu["carbon_intensity"]      = round(bu.get("carbon_intensity", 50.0), 2)
        bu["reputation_score"]      = round(bu.get("reputation_score", 50.0), 2)
        bu["staff_burnout_index"]   = round(bu.get("staff_burnout_index", 0.0), 2)
    ctx.new_treasury           = round(ctx.new_treasury, 2)
    # FIX BUG-1A (final gate): Re-apply dynamic treasury floor after all operational
    # layer penalties (carbon fees, CBAM, fines) to maintain ESG-adjusted floor
    if ctx.new_treasury < 0:
        _avg_inv_final = ctx.events.get("_pre_austerity_avg_invest", 0)
        _final_floor = FINANCIAL_TREASURY_FLOOR + (_avg_inv_final * 200_000_000)
        # DEEP-8 term 8 (2026-09-01): event the final-gate clamp too (see the
        # debt-service clamp above) — accumulate, both gates can fire in one round.
        _pre_clamp_final = ctx.new_treasury
        ctx.new_treasury = max(ctx.new_treasury, _final_floor)
        _clamp_credit_final = round(ctx.new_treasury - _pre_clamp_final, 2)
        if _clamp_credit_final > 0:
            ctx.events["treasury_floor_clamp_applied"] = round(
                float(ctx.events.get("treasury_floor_clamp_applied", 0.0)) + _clamp_credit_final, 2
            )
            ctx.record_waterfall(
                "Insolvency Floor Relief", _clamp_credit_final,
                because=(
                    f"Creditors will not extend losses below the treasury floor "
                    f"(${_final_floor:,.0f}); ${_clamp_credit_final:,.0f} of this round's "
                    f"losses were absorbed by the floor."
                ),
                counterfactual="A higher ESG investment ratio raises the floor (better credit lines).",
            )
    ctx.new_green_fund_balance = round(ctx.new_green_fund_balance, 2)
    ctx.new_synergy            = round(ctx.new_synergy, 4)

    # ── FEATURE 10: Competitive NPC Index ────────────────────────
    competitor_ebitda    = current_global.get("competitor_ebitda",
        current_global.get("historical_ebitda", ctx.historical_ebitda))
    new_competitor, relative_advantage = calc_competitor_pressure(competitor_ebitda, ctx.historical_ebitda)
    ctx.events["competitor_ebitda"]        = new_competitor
    ctx.events["relative_market_advantage"] = relative_advantage
    if relative_advantage < 1.0:
        ctx.events["competitor_warning"] = (
            f"Market competitor EBITDA (${new_competitor:,.0f}) exceeds yours. "
            f"Relative advantage: {relative_advantage:.2f}x"
        )

    # ── FEATURE 26: Predictive Forecast ─────────────────────────
    forecast = calc_forecast(current_global, ctx.new_bus)
    ctx.events["forecast"] = forecast

    # ── FEATURE 27: SDG Impact Report ────────────────────────────
    sdg_report = calc_sdg_impact(ctx.new_bus, ctx.events)
    ctx.events["sdg_impact"] = sdg_report

    # ── REC-1: Consequence Waterfall — finalise ──────────────────
    ctx.events["consequence_waterfall"] = {
        "initial_treasury": round(ctx._waterfall_initial, 2),
        "final_treasury":   round(ctx.new_treasury, 2),
        "net_change":       round(ctx.new_treasury - ctx._waterfall_initial, 2),
        "entries":          ctx.waterfall,
        "entry_count":      len(ctx.waterfall),
    }

    # ── REC-6: Momentum Score ────────────────────────────────────
    momentum_history = list(current_global.get("momentum_history", []))
    prev_states      = current_global.get("_prev_global_states", [])
    momentum         = calc_momentum_score(
        {
            "corporate_treasury": ctx.new_treasury,
            "group_reputation":   ctx.group_reputation,
            "active_event_flags": ctx.events,
            "momentum_history":   momentum_history,
        },
        prev_states if prev_states else [current_global],
    )
    ctx.events["momentum"] = momentum
    momentum_history.append(momentum["momentum_score"])
    if len(momentum_history) > 10:
        momentum_history = momentum_history[-10:]
    ctx.events["_momentum_history_internal"] = momentum_history
    ctx.events["_new_competitor_internal"]   = new_competitor

    # ── REC-8: Board Room Reflection Prompt ─────────────────────
    initial_treasury    = ctx._waterfall_initial
    treasury_change_pct = abs(ctx.new_treasury - initial_treasury) / max(abs(initial_treasury), 1) * 100
    contagion_risk      = forecast.get("contagion_risk_index", 0)
    is_midpoint         = current_global["round_number"] == 5
    in_survival         = ctx.events.get("survival_mode", False)

    reflection_trigger = None
    if ctx.decision_paradigm == "brsr_ngrbc":
        pass
    elif treasury_change_pct > TREASURY_DROP_REFLECTION_PCT and ctx.new_treasury < initial_treasury:
        top_causes  = sorted(ctx.waterfall, key=lambda e: abs(e["amount"]))[:3]
        cause_lines = "\n".join(
            f"  {i+1}. {e['label']} ({'+' if e['amount']>0 else ''}${e['amount']:,.0f})"
            for i, e in enumerate(reversed(top_causes))
        )
        reflection_trigger = {
            "type":     "treasury_drop",
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
            "type":     "survival_entry",
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
            "type":     "midpoint_review",
            "severity": "noteworthy",
            "prompt": (
                f"🪞 **Midpoint Board Review — Round 5 of 10**\n"
                f"Half your journey is complete. Current position:\n"
                f"• Treasury: ${ctx.new_treasury:,.0f}\n"
                f"• Reputation: {ctx.group_reputation:.0f}\n"
                f"• Contagion Risk: {forecast.get('contagion_risk_label', 'Unknown')}\n"
                f"• SDG Grade: {sdg_report.get('sdg_grade', '?')}\n\n"
                f"**Your team must answer:** *\"If we could undo one decision from "
                f"Rounds 1-5, which would it be and why?\"*"
            ),
        }
    elif contagion_risk > CONTAGION_RISK_WARNING:
        reflection_trigger = {
            "type":     "contagion_warning",
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
        ctx.events["reflection_required"] = True
        ctx.events["reflection_prompt"]   = reflection_trigger
    else:
        ctx.events["reflection_required"] = False

    # ── PHASE-1: Systemic Tipping Point Evaluation ───────────────
    systemic_tipping_state = {}
    try:
        from systemic_risk_engine import evaluate_tipping_points, evaluate_materiality_shocks
        _current_tipped = current_global.get("active_event_flags", {}).get("systemic_tipping_state", {})
        _tp_result      = evaluate_tipping_points(current_global, ctx.new_bus, _current_tipped)
        systemic_tipping_state = _tp_result["tipping_state"]
        ctx.events["systemic_tipping"] = _tp_result
        if _tp_result["transitions"]:
            for trans in _tp_result["transitions"]:
                ctx.events.setdefault("custom_black_swans", []).append({
                    "title":     f"⚠️ SYSTEMIC TIPPING — {trans['dimension'].upper()}",
                    "narrative": trans["message"],
                    "icon": "⚠️", "severity": "critical",
                })
        _session_tier_ms = current_global.get("active_event_flags", {}).get("difficulty_tier", "standard")
        _active_flags_ms = current_global.get("active_event_flags", {})
        _shocks          = evaluate_materiality_shocks(
            current_global["round_number"],
            _session_tier_ms,
            active_event_flags=_active_flags_ms,   # OI-2: enables once-per-session gate & config routing
        )
        if _shocks:
            ctx.events["materiality_shocks"] = _shocks
            for shock in _shocks:
                ctx.events.setdefault("custom_black_swans", []).append({
                    "title":     f"📊 MATERIALITY SHOCK — {shock['issue']}",
                    "narrative": shock["narrative"],
                    "icon": "📊", "severity": "critical",
                })
    except ImportError:
        pass
    ctx.events["_systemic_tipping_state_internal"] = systemic_tipping_state

    # ── REAL-WORLD SCENARIO MECHANICS ───────────────────────────
    # 1. Regulatory Ratchet Fine
    regulatory_baseline = REG_RATCHET_BASELINE + (current_global["round_number"] // 2) * REG_RATCHET_ROUND_INCREMENT
    avg_gov_risk        = sum(bu.get("governance_risk_score", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)
    if avg_gov_risk > regulatory_baseline:
        fine             = (avg_gov_risk - regulatory_baseline) * REG_RATCHET_FINE_PER_POINT
        ctx.new_treasury -= fine
        ctx.events["regulatory_ratchet"] = {
            "active":   True,
            "baseline": regulatory_baseline,
            "fine":     fine,
            "message":  f"⚖️ Regulatory Ratchet: Average governance risk ({avg_gov_risk:.1f}) exceeds the shifting industry baseline ({regulatory_baseline:.1f}). Compliance fine: ${fine:,.0f}.",
        }
    else:
        ctx.events["regulatory_ratchet"] = {"active": False, "baseline": regulatory_baseline, "fine": 0}

    # 2. Supplier Defection & 3. Green Premium Squeeze
    supplier_defections    = []
    green_premium_squeezes = []
    for dec in ctx.decisions:
        bu_id = dec["bu_id"]
        bu    = next((b for b in ctx.new_bus if b["bu_id"] == bu_id), None)
        if not bu:
            continue
        inv_ratio        = dec.get("investment_ratio", 0.0)
        pillar_decisions = dec.get("pillar_decisions") or {}
        supply_chain_choice = pillar_decisions.get("supply_chain", "")
        if supply_chain_choice in ["audit_suppliers", "strict_mandates", "living_wage_mandate"] and inv_ratio < SUPPLIER_DEFECTION_INV_THRESHOLD:
            bu["opex_base"]                  = round(bu["opex_base"] * SUPPLIER_DEFECTION_OPEX_MULT, 2)
            bu["revenue_base"]               = round(bu["revenue_base"] * SUPPLIER_DEFECTION_REV_MULT, 2)
            bu["supplier_defection_active"]  = True
            supplier_defections.append(bu_id)
        else:
            bu["supplier_defection_active"] = False
        if inv_ratio > 0.25 and bu.get("social_license_score", 50) < 60:
            penalty_pct  = (60 - bu["social_license_score"]) * 0.005
            penalty_val  = round(bu["revenue_base"] * penalty_pct, 2)
            bu["revenue_base"]        -= penalty_val
            bu["green_premium_squeeze"] = penalty_val
            green_premium_squeezes.append({"bu_id": bu_id, "penalty": penalty_val})
        else:
            bu["green_premium_squeeze"] = 0.0

    if supplier_defections:
        ctx.events["supplier_defection"] = {
            "active":       True,
            "affected_bus": supplier_defections,
            "message":      f"🏭 Supplier Defection: You mandated strict supply chain ESG rules without providing financial subsidies (investment ratio < 15%) for {len(supplier_defections)} BU(s). Suppliers dropped you. +10% OPEX shock, -5% Revenue.",
        }
    else:
        ctx.events["supplier_defection"] = {"active": False}

    if green_premium_squeezes:
        total_squeeze = sum(s["penalty"] for s in green_premium_squeezes)
        ctx.events["green_premium_squeeze"] = {
            "active":  True,
            "penalty": total_squeeze,
            "message": f"📉 Green Premium Squeeze: You invested heavily (>25%) but lacked the Social License (<60) to pass costs to consumers. The market rejected the premium pricing. Revenue lost: ${total_squeeze:,.0f}.",
        }
    else:
        ctx.events["green_premium_squeeze"] = {"active": False}

    # 4. Valley of Death (CFO Austerity Trap)
    loan_principal = ctx.events.pop("_loan_principal_internal", 0.0)
    base_treasury  = ctx.events.pop("_base_treasury_internal", 0.0)
    if ctx.new_treasury < 0 or loan_principal > base_treasury * CFO_AUSTERITY_LOAN_RATIO:
        ctx.events["cfo_austerity_active"]  = True
        ctx.events["cfo_austerity_message"] = "🛑 CFO Austerity Override: Heavy ESG investments drained free cash flow. The CFO has frozen all sustainability budgets for the next round."
    else:
        ctx.events["cfo_austerity_active"] = False

    # ── FIX-QA-005: Final bounds-clamping pass ───────────────────
    for bu in ctx.new_bus:
        bu["revenue_base"]          = max(0.0, bu.get("revenue_base", 0.0))
        bu["opex_base"]             = max(0.0, bu.get("opex_base", 0.0))
        bu["reputation_score"]      = max(0.0, min(100.0, bu.get("reputation_score", 50.0)))
        bu["social_license_score"]  = max(0.0, min(100.0, bu.get("social_license_score", 50.0)))
        bu["natural_capital_debt"]  = max(0.0, min(NCD_HARD_CAP, bu.get("natural_capital_debt", 0.0)))
        bu["carbon_intensity"]      = max(0.0, bu.get("carbon_intensity", 0.0))
        bu["staff_burnout_index"]   = max(0.0, min(100.0, bu.get("staff_burnout_index", 0.0)))

    # ── Stakeholder Sentiment Update ─────────────────────────────
    try:
        from stakeholder_sentiment import update_stakeholder_sentiment, initialise_sentiment
        from stakeholder_map import get_stakeholders_for_session
        # BUGFIX 2026-07-31: this passed current_global["metadata"] — a key
        # that does not exist on round state — so the resolver ALWAYS saw an
        # empty dict and sentiment initialised from the default stakeholder
        # set, ignoring the cohort's vertical/region/pack scope that the rest
        # of play resolves. Pass the global state itself, which carries the
        # scope (seeded at creation and hydrated at the read boundaries).
        _sh_list       = current_global.get("sentiment_stakeholders", [])
        if not _sh_list:
            _raw_stakeholders = get_stakeholders_for_session(current_global)
            if _raw_stakeholders:
                _sh_list = initialise_sentiment(_raw_stakeholders)
        if _sh_list:
            _flags_this_round = []
            for _d in ctx.decisions:
                _flags_this_round.extend(_d.get("flags_set", []))
            _flags_this_round.extend([k for k, v in ctx.events.items() if v is True])
            _swans = [
                {"event_id": e.get("id", e.get("event_id", "")), "title": e.get("title", "")}
                for e in ctx.events.get("black_swan_events", [])
            ]
            _updated_sh = update_stakeholder_sentiment(
                stakeholders=_sh_list,
                flags_set_this_round=_flags_this_round,
                round_number=current_global.get("round_number", 1),
                black_swans_triggered=_swans,
            )
            ctx.events["sentiment_stakeholders"] = _updated_sh
            _hist = current_global.get("sentiment_history", {})
            _hist[str(ctx.next_round)] = [
                {
                    "id":             s["id"],
                    "name":           s.get("name", s["id"]),
                    "attitude_score": s.get("attitude_score", 0),
                    "attitude_delta": s.get("attitude_delta_this_round", 0),
                    "salience_label": s.get("salience_label", "Latent"),
                    "narrative":      s.get("sentiment_narrative", ""),
                }
                for s in _updated_sh
            ]
            ctx.events["sentiment_history"] = _hist
    except Exception:
        pass  # Non-fatal: sentiment failure must never block the simulation tick


# ── Final State Assembly ─────────────────────────────────────────

# ── Stateful engine sub-dicts that must survive the process_tick boundary ─────
# _assemble_global_state rebuilds global_state from an explicit whitelist, which
# historically DROPPED these engine sub-dicts — so run_new_engines re-initialised
# them every round (they were effectively memoryless). Carry them forward
# explicitly. See SPEC §1.7.
#
# INTENTIONALLY only `npc_stakeholders` for now: this is the F1 (stakeholder
# memory) prerequisite. Adding the other engine states (board_governance,
# org_politics, supply_chain, autonomous_agents) also changes THEIR cross-round
# behaviour and must land in separate, individually golden-diffed commits.
# STATE-CARRY FIX (balance-sheet year-by-year audit, 2026-07-18): every
# stateful engine ledger round_logic maintains on global_state must be listed
# here, or _assemble_global_state silently drops it at the tick boundary and
# the engine re-initialises EVERY round. Only npc_stakeholders was listed —
# so the balance sheet rebuilt fresh each round (its year-by-year history
# never spanned more than the final round), the autonomous stakeholder agents
# lost grievance memory / patience each tick (decay re-applied from initial
# values instead of accumulating), and biodiversity / board / org-politics /
# supply-chain / regulatory-sandbox state reset likewise.
ENGINE_STATE_KEYS: tuple[str, ...] = (
    "npc_stakeholders",
    "autonomous_agents",
    "balance_sheet",
    "biodiversity_state",
    "board_governance",
    "org_politics",
    "supply_chain",
    "regulatory_sandbox",
)


def _slim_prev_state(g: dict) -> dict:
    """Momentum-sized snapshot of a global state for _prev_global_states.

    calc_momentum_score reads corporate_treasury, group_reputation and
    scalar event flags from prior rounds. Keeping only those (and dropping
    nested engine ledgers, plus any older _prev chain) makes the history
    O(1) per round instead of tripling each tick.
    """
    flags = g.get("active_event_flags") or {}
    return {
        "round_number":       g.get("round_number"),
        "corporate_treasury": g.get("corporate_treasury"),
        "group_reputation":   g.get("group_reputation"),
        "active_event_flags": {k: v for k, v in flags.items()
                               if isinstance(v, (bool, int, float, str))},
    }


def _assemble_global_state(ctx: TickContext, initial_treasury: float) -> dict[str, Any]:
    """
    Build the immutable next-round global state dict from the fully-evolved
    TickContext.  This is a pure data-assembly step — no calculations here.

    Engine sub-states listed in ENGINE_STATE_KEYS are carried forward from
    current_global so stateful engines (e.g. NPC stakeholders) are not
    re-initialised every round (SPEC §1.7).
    """
    events = ctx.events
    return {
        "round_number":       ctx.next_round,
        "corporate_treasury": ctx.new_treasury,
        "group_reputation":   ctx.group_reputation,
        "synergy_multiplier": ctx.new_synergy,
        "cost_of_capital":    ctx.corporate_cost_of_capital,
        "inflation_index":    ctx.new_inflation_index,
        "competitor_ebitda":  events.pop("_new_competitor_internal", 0.0),
        "green_transition_fund": max(0.0, ctx.new_green_fund_balance),
        "tipping_point_active":  events.pop("_tipping_point_active_internal", False),
        "tipping_tier":          events.pop("_tipping_tier_internal", "none"),
        "active_event_flags":    events,

        "historical_ebitda":   ctx.historical_ebitda,
        "tco2e_emissions":     ctx.tco2e_emissions,
        "vrio_capabilities":   ctx.vrio_capabilities,
        "bonus_score":         ctx.current_global.get("bonus_score", 0),
        "learning_bonuses_awarded":   ctx.current_global.get("learning_bonuses_awarded", {}),
        "stakeholder_map_completed":  ctx.current_global.get("stakeholder_map_completed", False),
        "stakeholder_map_accuracy":   ctx.current_global.get("stakeholder_map_accuracy", 0),
        "saved_allocations":          ctx.current_global.get("saved_allocations"),
        "saved_decision_choice":      ctx.current_global.get("saved_decision_choice"),
        "materiality_budget_allocated": ctx.current_global.get("materiality_budget_allocated"),
        "materiality_bu_id":          ctx.current_global.get("materiality_bu_id"),
        "csrd_completed":             ctx.current_global.get("csrd_completed", False),
        "pending_capex_projects":     ctx.new_pending_projects,
        "political_capital":          ctx.sdg_political_capital,
        "community_trust_score":      ctx.sdg_community_trust,
        "global_emissions_intensity": ctx.current_global.get("global_emissions_intensity", 0.0),
        "sbti_pathway_history":       events.get("sbti_pathway", {}).get("history", []),
        "carbon_forwards":            events.get("carbon_offset_market", {}).get("remaining_forwards",
                                          ctx.current_global.get("carbon_forwards", [])),
        "momentum_history":           events.pop("_momentum_history_internal", []),
        # PERF FIX (10-round playthrough audit): push a SLIM snapshot, not the
        # full current_global. The full dict contains its own _prev list plus
        # (post STATE-CARRY fix) every engine ledger, so each round's payload
        # tripled — 58KB at R2 grew to 122MB by R9 and commits crawled. The
        # only consumer is calc_momentum_score, which reads treasury,
        # reputation and scalar event flags; nested ledgers are dropped.
        "_prev_global_states":        (ctx.current_global.get("_prev_global_states", []) + [_slim_prev_state(ctx.current_global)])[-3:],
        # Preserve systemic tipping state across rounds
        "systemic_tipping_state":     events.pop("_systemic_tipping_state_internal", {}),
        # SPEC §1.7 — carry forward stateful engine sub-dicts (NPC stakeholders)
        # so they persist across the tick boundary instead of resetting each round.
        # is-not-None guard: the memory store's explicit columns can hold None
        # before an engine's first tick; carrying the key with a None value
        # would defeat round_logic's `if key not in global_state` init check
        # and crash the engine (NoneType is not subscriptable).
        **{k: ctx.current_global[k] for k in ENGINE_STATE_KEYS if ctx.current_global.get(k) is not None},
    }


# ═════════════════════════════════════════════════════════════════
#  TICK ORCHESTRATOR — Lean Entry Point
# ═════════════════════════════════════════════════════════════════

def process_tick(
    current_global: dict,
    current_bus: list[dict],
    decisions: list[dict],
    dividends_paid: float = 0.0,
    crisis_severity: float = 0.0,
    imitation_decay_rate: float = DEFAULT_IMITATION_DECAY_RATE,  # 6-month compounded: 1-(1-0.05)² ≈ 0.0975
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

    # ── 1. Defensive copies ──────────────────────────────────────
    # FIX AUDIT-001: Deep-copy current_global to prevent input mutation.
    current_global = copy.deepcopy(current_global)

    # FIX CRITICAL-2: Deep-copy decisions so the caller's list is NEVER mutated.
    decisions: list[dict] = copy.deepcopy(decisions)

    # ── 2. Austerity Clamp (pre-processing guard) ────────────────
    # Operates on the local deep-copied decisions — caller's original is untouched.
    # FIX BUG-1A: Save pre-austerity investment ratio for dynamic floor calculation
    _pre_austerity_avg_invest = sum(
        d.get("investment_ratio", 0) for d in decisions
    ) / max(len(decisions), 1)
    if current_global.get("active_event_flags", {}).get("cfo_austerity_active", False):
        for d in decisions:
            d["investment_ratio"] = 0.0
            d["capex_allocated"]  = 0.0

    # ── 3. Build TickContext ─────────────────────────────────────
    initial_treasury = current_global.get("corporate_treasury", 0.0)

    ctx = TickContext(
        # Read-only inputs
        current_global         = current_global,
        decisions              = decisions,
        decision_map           = {d["bu_id"]: d for d in decisions},
        decision_paradigm      = decision_paradigm,
        dividends_paid         = dividends_paid,
        crisis_severity        = crisis_severity,
        imitation_decay_rate   = imitation_decay_rate,
        emergency_credit_used  = emergency_credit_used,
        # FIX AUDIT-006: capture synergy BEFORE project processing
        pre_tick_synergy       = current_global["synergy_multiplier"],
        next_round             = current_global["round_number"] + 1,
        # Working state
        new_bus                = copy.deepcopy(current_bus),
        events                 = {},
        waterfall              = [],
        _waterfall_running_total = initial_treasury,
        _waterfall_initial       = initial_treasury,
        # Scalars initialised from current state
        new_treasury           = initial_treasury,
        new_synergy            = current_global["synergy_multiplier"],
        new_green_fund_balance = current_global.get("green_transition_fund", 0.0),
        new_inflation_index    = current_global.get("inflation_index", 0.05),
        corporate_cost_of_capital = current_global.get("cost_of_capital", 0.05),
        group_reputation       = 0.0,
        # Project queues
        new_pending_projects     = [],
        new_synergy_lag_projects = [],
        # SDG state carried from previous round
        sdg_political_capital  = current_global.get("political_capital", 50.0),
        sdg_community_trust    = current_global.get("community_trust_score", 50.0),
    )

    # ── 4. Run the four pipeline stages ─────────────────────────
    # FIX BUG-1A: Store pre-austerity investment ratio for floor calculations
    ctx.events["_pre_austerity_avg_invest"] = _pre_austerity_avg_invest
    _run_stochastic_layer(ctx)
    _run_financial_layer(ctx)
    _run_operational_layer(ctx)
    _run_reporting_layer(ctx)

    # ── 5. Assemble and return immutable output ──────────────────
    new_global = _assemble_global_state(ctx, initial_treasury)
    return {
        "global_state": new_global,
        "bu_states":    ctx.new_bus,
        "events":       ctx.events,
    }
