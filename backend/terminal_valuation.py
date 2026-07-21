"""
Muressons Global Corporation - Terminal Valuation Module
Extracted from round_logic.py (STRAT-001) for independent testability,
What-If mode (STRAT-003), and cross-pathway normalization (STRAT-004).
Pure-function module: no I/O, no database access.

VALUATION IMPROVEMENTS (STRAT-010):
  • Dynamic exit multiple derived from WACC + long-run growth (replaces fixed 12×)
  • EV → Equity bridge: Terminal Value − Net Debt + Cash = Equity Value
  • Per-share price: Equity Value / SHARES_OUTSTANDING (100M shares)
  • Market benchmarks: EV/Revenue, Price/Book
  • Synergy M_R double-count: noted in calculate_mr() — synergy already
    reduces OPEX (→ higher EBITDA) AND earns +0.15 M_R (reduced from +0.30
    to account for the EBITDA path, representing strategic optionality premium).
"""
from __future__ import annotations
from typing import Any
import logging
import math
from config import (
    FINANCIAL_SHADOW_CARBON_PRICE,
    FINANCIAL_WACC_LENDER_THRESHOLD,
    TV_SHARES_OUTSTANDING,
    TV_IPO_PRICE,
    TV_LONG_RUN_GROWTH,
    TV_EXIT_MULTIPLE_FLOOR,
    TV_EXIT_MULTIPLE_CEILING,
)

log = logging.getLogger(__name__)

# ── Shares Outstanding (constant for all scenarios) ────────────────────────
SHARES_OUTSTANDING: int = TV_SHARES_OUTSTANDING   # 100 million shares (IPO anchor)
IPO_PRICE_PER_SHARE: float = TV_IPO_PRICE       # Opening price at game start

# ── Share-price floor ──────────────────────────────────────────────────────
# A traded share price can never go negative — a shareholder's residual claim is
# floored at zero by limited liability, and a listed stock has a de-minimis
# (penny-stock) floor rather than a negative quote. We report a $1.00 floor,
# matching the live in-game stock engine (frontend stockValuationEngine already
# floors intraday/round prices at $1). When net debt has wiped out equity the
# honest signal is `equity_value < 0` / `equity_wiped_out`, NOT a negative price.
SHARE_PRICE_FLOOR: float = 1.0

# ── Long-run nominal growth assumption for Gordon Growth exit multiple ───────
_LONG_RUN_GROWTH: float = TV_LONG_RUN_GROWTH          # 2% terminal growth (real GDP + inflation)
_EXIT_MULTIPLE_FLOOR: float = TV_EXIT_MULTIPLE_FLOOR       # Distressed / regulatory-shutdown floor
_EXIT_MULTIPLE_CEILING: float = TV_EXIT_MULTIPLE_CEILING    # Maximum (very low WACC + high growth)

# ── M_R Boundaries — enforced hard limits (WARNING-4 fix) ─────────────────
# MR_FLOOR     : M_R ≤ 0 is economically meaningless (total governance collapse).
# MR_CEILING   : 2.05 — 10bp above the absolute documented maximum of 2.03
#                (1.93 base max + 0.10 JT-scaling headroom) from simulation_config.
#                pathway_bonuses from external callers cannot push M_R beyond this
#                value, preventing unbounded terminal value inflation.
MR_FLOOR:    float = 0.0
MR_CEILING:  float = 2.05


# ── GAME-2: Threshold ramps (remove M_R knife-edges) ─────────────────────────
# Previously, KPI-driven M_R components were hard step-functions: e.g. a team at
# SLO 74.9 took the full −0.40 Instability Discount while a team at 75.0 took
# nothing — 0.40 of terminal multiplier swinging on a hair. These bands replace
# each cliff with a short linear ramp centred on the old threshold. Outside the
# band the values are IDENTICAL to before (so the documented max/min M_R and the
# archetype boundaries are unchanged); inside the band the award/penalty scales
# linearly, so a fraction of a point is never worth a large discrete jump.
_MR_RAMP_BAND_KPI:     float = 10.0   # ±5 points around 0–100 KPI thresholds
_MR_RAMP_BAND_SYNERGY: float = 0.10   # ±0.05 around the 0.80 synergy gate


def _ramp_fraction(value: float, threshold: float, band: float, direction: str) -> float:
    """Linear ramp in [0, 1] replacing a hard threshold comparison.

    direction="above": fraction rises from 0 to 1 as `value` crosses upward
        through the band centred on `threshold` (use for ``value >= threshold``
        style rewards). 1.0 at threshold+band/2, 0.0 at threshold-band/2.
    direction="below": fraction rises from 0 to 1 as `value` crosses downward
        (use for ``value < threshold`` style rewards/penalties). 1.0 at
        threshold-band/2, 0.0 at threshold+band/2.

    Endpoints are preserved: well outside the band the result is exactly 1.0 or
    0.0, matching the previous all-or-nothing behaviour.
    """
    half = band / 2.0
    if band <= 0:
        # Degenerate band → fall back to the original step function.
        if direction == "above":
            return 1.0 if value >= threshold else 0.0
        return 1.0 if value < threshold else 0.0
    if direction == "above":
        if value >= threshold + half:
            return 1.0
        if value <= threshold - half:
            return 0.0
        return (value - (threshold - half)) / band
    else:  # "below"
        if value <= threshold - half:
            return 1.0
        if value >= threshold + half:
            return 0.0
        return ((threshold + half) - value) / band


# ── M_R Calculation ─────────────────────────────────────────────────────────
def calculate_mr(
    flags: dict[str, Any],
    avg_slo: float,
    avg_burnout: float,
    workforce_readiness: float,
    synergy_multiplier: float,
    hr_investment_rounds: int = 0,
    pathway_bonuses: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Regenerative Multiple (M_R) — ESG quality / risk modifier for terminal valuation.

    Args:
        flags:               active_event_flags dict — keys are flag names, values are
                             truthy (bool/int/float). MUST be a dict; passing a list
                             will be normalised to an empty dict with a warning logged.
        avg_slo:             Group-average Social License to Operate score (0–100).
        avg_burnout:         Group-average staff burnout index (0–100, lower is better).
        workforce_readiness: Workforce readiness score (0–100).
        synergy_multiplier:  Current VRIO synergy multiplier (1.0 at start; decays 10%/
                             round, boosted +0.35 by R7 option_c Resist & Integrate).
        hr_investment_rounds: Rounds with sustained HR investment (scales JT bonus).
        pathway_bonuses:     Optional dict of {label: delta} additional M_R adjustments
                             from the ending pathway (STRAT-004).

    Returns:
        dict with: mr (clamped), mr_raw, breakdown, bonuses_earned, and diagnostic fields.

    Synergy gate contract:
        The +0.15 Synergy Strategic Premium requires BOTH:
          (a) flags["synergy_unlock"] is truthy  — R7 option_c "Resist & Integrate"
          (b) synergy_multiplier >= 0.80         — the unlock must have been earned
              while the VRIO multiplier was still above the threshold.
        If only the flag is present but synergy_multiplier has decayed below 0.80,
        the premium is NOT applied (the integration was too fragmented to generate
        true strategic optionality).

    SYNERGY NOTE (STRAT-010 fix): The original +0.30 synergy bonus was reduced to
    +0.15. Reason: synergy_unlock already lowers OPEX via the synergy engine (higher
    terminal EBITDA). Adding the full +0.30 M_R on top multiplied a benefit already
    captured in EBITDA. The reduced +0.15 represents the *strategic optionality premium*
    — what an investor pays for integrated BUs beyond pure cash-flow benefit.

    FIX WARNING-4: Hard floor MR_FLOOR=0.0 and hard ceiling MR_CEILING=2.05 are
    applied after all bonus/penalty accumulation, including pathway_bonuses.
    """
    # ── Type-safety guard ───────────────────────────────────────────────────
    # Some callers (legacy code paths, tests) pass a list of flag strings.
    # Normalise to dict so .get() calls below are always safe.
    if not isinstance(flags, dict):
        log.warning(
            "calculate_mr: flags argument is %s, expected dict. "
            "Normalising to empty dict — all flag bonuses will be skipped. "
            "Caller must pass active_event_flags dict, not a list.",
            type(flags).__name__,
        )
        flags = {}

    # ── Collect active flag names for logging ────────────────────────────────
    active_flag_names: list[str] = [k for k, v in flags.items() if v]
    log.info(
        "calculate_mr | avg_slo=%.1f avg_burnout=%.1f workforce_readiness=%.1f "
        "synergy_multiplier=%.4f hr_investment_rounds=%d | "
        "active_flags=%s",
        avg_slo, avg_burnout, workforce_readiness,
        synergy_multiplier, hr_investment_rounds,
        active_flag_names,
    )

    mr = 1.0
    breakdown = {"base": 1.0}
    bonuses = []
    if flags.get("materiality_aligned"):
        mr += 0.10; breakdown["materiality_governance"] = 0.10
        bonuses.append("Materiality Governance (+0.10)")

    # ── Synergy Strategic Premium gate ──────────────────────────────────────
    # Condition A: R7 option_c "Resist & Integrate" set the synergy_unlock flag.
    # Condition B: synergy_multiplier >= 0.80 — VRIO integration threshold.
    # BOTH must be satisfied; a flag earned while synergy had already decayed
    # below threshold does not qualify for the strategic optionality premium.
    synergy_flag_present: bool = bool(flags.get("synergy_unlock"))
    synergy_threshold_met: bool = synergy_multiplier >= 0.80
    # GAME-2: ramp the 0.80 synergy gate instead of a hard cutoff.
    synergy_frac: float = _ramp_fraction(synergy_multiplier, 0.80, _MR_RAMP_BAND_SYNERGY, "above") if synergy_flag_present else 0.0
    synergy_bonus_applied: bool = synergy_flag_present and synergy_frac > 0.0
    if synergy_bonus_applied:
        # STRAT-010: Reduced from +0.30 → +0.15.
        # Synergy OPEX savings already flow through terminal_ebitda.
        # +0.15 captures the strategic optionality / integration premium.
        b = round(0.15 * synergy_frac, 4)
        mr += b; breakdown["synergy_bonus"] = b
        bonuses.append(f"Synergy Strategic Premium (+{b:.2f})")

    log.info(
        "calculate_mr | synergy_unlock_flag=%s synergy_threshold_met=%s "
        "(synergy_multiplier=%.4f >= 0.80) => synergy_bonus_applied=%s",
        synergy_flag_present, synergy_threshold_met,
        synergy_multiplier, synergy_bonus_applied,
    )

    if not flags.get("insurance_only") and not flags.get("electronics_water_priority") and not flags.get("civil_water_priority"):
        mr += 0.20; breakdown["resilience_bonus"] = 0.20
        bonuses.append("Resilience Champion (+0.20)")
    if flags.get("ethical_ai_overhaul"):
        mr += 0.15; breakdown["truth_premium"] = 0.15
        bonuses.append("Truth Premium (+0.15)")
    jt_scaling = 1.0
    if hr_investment_rounds > 0 and (flags.get("community_fund") or flags.get("managed_transition")):
        jt_scaling = round(min(1.5, 1.0 + hr_investment_rounds * 0.10), 2)
    if flags.get("community_fund"):
        b = round(0.18 * jt_scaling, 4); mr += b; breakdown["community_champion_bonus"] = b
        bonuses.append(f"Community Champion (+{b:.2f})")
    elif flags.get("managed_transition"):
        b = round(0.12 * jt_scaling, 4); mr += b; breakdown["just_transition_bonus"] = b
        bonuses.append(f"Just Transition (+{b:.2f})")
    # GAME-2: ramped (was a hard >= 75 cutoff).
    _wf_frac = _ramp_fraction(workforce_readiness, 75.0, _MR_RAMP_BAND_KPI, "above")
    if _wf_frac > 0:
        b = round(0.10 * _wf_frac, 4); mr += b; breakdown["workforce_bonus"] = b
        bonuses.append(f"Workforce Excellence (+{b:.2f})")
    # GAME-2: ramped (was a hard < 20 cutoff).
    _wb_frac = _ramp_fraction(avg_burnout, 20.0, _MR_RAMP_BAND_KPI, "below")
    if _wb_frac > 0:
        b = round(0.05 * _wb_frac, 4); mr += b; breakdown["wellbeing_bonus"] = b
        bonuses.append(f"Wellbeing Champion (+{b:.2f})")
    if flags.get("planet_expendable"):
        mr -= 0.20; breakdown["planet_expendable_penalty"] = -0.20
        bonuses.append("Planet Expendable Penalty (-0.20)")
    # BRSR NGRBC Track: ESG Alpha Dividend
    brsr_div = flags.get("brsr_net_positive_dividend", 0)
    if brsr_div:
        mr += brsr_div; breakdown["brsr_esg_alpha_dividend"] = brsr_div
        bonuses.append(f"BRSR ESG Alpha Dividend (+{brsr_div:.2f})")
    # GAME-2: ramped (was a hard < 75 cutoff worth a full -0.40 swing).
    _slo_frac = _ramp_fraction(avg_slo, 75.0, _MR_RAMP_BAND_KPI, "below")
    if _slo_frac > 0:
        b = round(-0.40 * _slo_frac, 4); mr += b; breakdown["instability_discount"] = b
        bonuses.append(f"Instability Discount ({b:+.2f})")
    if pathway_bonuses:
        for k, v in pathway_bonuses.items():
            if not isinstance(v, (int, float)):  # VUL-017: TypeError guard — skip non-numeric values
                breakdown[k] = f"invalid_type:{type(v).__name__}"
                continue
            mr += v; breakdown[k] = v
            bonuses.append(f"{k.replace('_',' ').title()} ({v:+.2f})")

    # FIX WARNING-4: Enforce floor and ceiling AFTER all accumulation.
    # raw_mr is preserved in the return dict for auditability.
    raw_mr: float = round(mr, 4)
    mr = round(max(MR_FLOOR, min(MR_CEILING, mr)), 4)
    mr_ceiling_clamped: bool = raw_mr > MR_CEILING
    mr_floor_clamped:   bool = raw_mr < MR_FLOOR

    log.info(
        "calculate_mr | result: mr_raw=%.4f mr_clamped=%.4f bonuses=%s",
        raw_mr, mr, bonuses,
    )

    # Max achievable: 1.0+0.10+0.15+0.20+0.15+0.18+0.10+0.05 = 1.93 (2.03 with JT-scaling)
    return {
        "mr":                 mr,
        "mr_raw":             raw_mr,               # pre-clamp value for diagnostics
        "mr_ceiling_clamped": mr_ceiling_clamped,   # True → pathway_bonuses exceeded ceiling
        "mr_floor_clamped":   mr_floor_clamped,     # True → deep penalty scenario
        "mr_ceiling":         MR_CEILING,
        "mr_floor":           MR_FLOOR,
        "breakdown":          breakdown,
        "jt_scaling_factor":  jt_scaling,
        "bonuses_earned":     bonuses,
        "max_achievable_mr":  1.93,
        # diagnostic fields for OI-1 / synergy gate audit
        "synergy_flag_present":   synergy_flag_present,
        "synergy_threshold_met":  synergy_threshold_met,
        "synergy_bonus_applied":  synergy_bonus_applied,
        "synergy_multiplier_in":  synergy_multiplier,
        "active_flags_seen":      active_flag_names,
    }


# ── Dynamic Exit Multiple ────────────────────────────────────────────────────
def calculate_dynamic_exit_multiple(
    wacc: float = FINANCIAL_WACC_LENDER_THRESHOLD,
    growth_rate: float = _LONG_RUN_GROWTH,
    floor: float = _EXIT_MULTIPLE_FLOOR,
    ceiling: float = _EXIT_MULTIPLE_CEILING,
) -> dict:
    """
    STRAT-010: Gordon Growth Model exit multiple.
        Exit_Multiple = (1 + g) / (WACC − g)
    This links the exit multiple directly to the cost-of-capital engine,
    so teams that accumulate ESG risk (higher WACC) pay a valuation penalty.

    Args:
        wacc: Weighted average cost of capital (default 8%).
        growth_rate: Long-run nominal terminal growth (default 2%).
        floor / ceiling: Hard limits for unrealistic extremes.

    Returns:
        dict with multiple, wacc, growth_rate, basis.
    """
    if wacc <= growth_rate:
        # Degenerate case (WACC ≤ g) → cap at ceiling
        multiple = ceiling
        basis = "wacc_below_growth_rate_ceiling_applied"
    else:
        multiple = (1.0 + growth_rate) / (wacc - growth_rate)

    multiple = round(max(floor, min(ceiling, multiple)), 2)
    return {
        "exit_multiple": multiple,
        "wacc_used": round(wacc, 4),
        "growth_rate_used": round(growth_rate, 4),
        "floor": floor,
        "ceiling": ceiling,
        "basis": f"Gordon Growth: (1+{growth_rate:.2f})/(WACC({wacc:.3f})−g({growth_rate:.2f}))",
        "wacc_penalty_active": wacc > FINANCIAL_WACC_LENDER_THRESHOLD + 0.01,   # flag for UI callout
    }


# ── SDG Multiplier (M_SDG) ─────────────────────────────────────────────────
def calculate_sdg_multiplier(sdg_impact_score: float = 0.0) -> dict:
    """
    M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25

    SDG Impact Score is accumulated from the Corporate SDG Side Track.
    Range: -11 (all Option C) to 105 (all Option A).
    M_SDG range: 0.97 to 1.26.
    Sessions without the SDG Side Track default to score=0 → M_SDG=1.0 (neutral).
    """
    m_sdg = round(1.0 + (sdg_impact_score / 100.0) * 0.25, 4)
    return {
        "m_sdg": m_sdg,
        "sdg_impact_score": sdg_impact_score,
        "sdg_track_active": sdg_impact_score != 0.0,
    }


# ── Equity Bridge ───────────────────────────────────────────────────────────
def calculate_equity_bridge(
    enterprise_value: float,
    net_debt: float,                 # total financial debt − cash
    shares_outstanding: int = SHARES_OUTSTANDING,
    book_equity: float = 0.0,        # net_assets from balance sheet
    total_revenue: float = 0.0,      # for EV/Revenue benchmark
) -> dict:
    """
    STRAT-010: Bridge Enterprise Value (TV) → Equity Value → Price Per Share.

    Formula:
        Equity_Value = Enterprise_Value − Net_Debt
        Price_Per_Share = Equity_Value / Shares_Outstanding

    Also computes market multiples:
        EV/Revenue = Enterprise_Value / Total_Revenue
        Price/Book  = Equity_Value / Book_Equity (net assets)

    Args:
        enterprise_value: Terminal Value computed as EBITDA × Exit × M_R
        net_debt: Total financial debt − cash (can be negative = net cash)
        shares_outstanding: Fixed at 100M for this simulation
        book_equity: Balance sheet net_assets (IAS 1)
        total_revenue: For EV/Revenue multiple

    Returns:
        dict with equity_value, price_per_share, market multiples, bridge detail
    """
    equity_value = round(enterprise_value - net_debt, 2)
    # Raw per-share residual claim (can be negative when net debt exceeds EV) —
    # kept for transparency/audit, but the REPORTED price floors at $1.00: a
    # traded share price is never negative. `equity_wiped_out` carries the honest
    # insolvency signal, decoupled from the (now non-negative) price.
    raw_price_per_share = round(equity_value / max(1, shares_outstanding), 4)
    price_per_share = max(SHARE_PRICE_FLOOR, raw_price_per_share)
    equity_wiped_out = equity_value < 0
    ipo_price = IPO_PRICE_PER_SHARE

    # Market multiples
    ev_over_revenue = round(enterprise_value / total_revenue, 2) if total_revenue > 0 else None
    price_to_book = round(equity_value / book_equity, 2) if book_equity > 0 else None

    # Benchmark signals (sector: diversified industrials with ESG lens)
    ev_rev_benchmark = 2.5    # sector median EV/Revenue
    pb_benchmark = 1.5        # sector median Price/Book at fair value
    # Share-price change is measured against the REPORTED (floored) price so the
    # headline stat and this percentage stay internally consistent.
    sp_change_pct = round((price_per_share - ipo_price) / ipo_price * 100, 1) if ipo_price > 0 else 0

    ev_rev_signal = None
    if ev_over_revenue is not None:
        ev_rev_signal = (
            "premium" if ev_over_revenue > ev_rev_benchmark * 1.2 else
            "fair" if ev_over_revenue >= ev_rev_benchmark * 0.8 else
            "discount"
        )

    pb_signal = None
    if price_to_book is not None:
        pb_signal = (
            "premium" if price_to_book > pb_benchmark * 1.2 else
            "fair" if price_to_book >= pb_benchmark * 0.8 else
            "below_book"
        )

    return {
        "enterprise_value": round(enterprise_value, 2),
        "net_debt": round(net_debt, 2),
        "equity_value": equity_value,
        "equity_wiped_out": equity_wiped_out,
        "shares_outstanding": shares_outstanding,
        "price_per_share": round(price_per_share, 2),
        "price_per_share_raw": round(raw_price_per_share, 2),  # pre-floor, audit only
        "share_price_floored": price_per_share > raw_price_per_share,
        "ipo_price_per_share": ipo_price,
        "share_price_change_pct": sp_change_pct,
        "share_price_vs_ipo": "gain" if price_per_share >= ipo_price else "loss",
        "ev_over_revenue": ev_over_revenue,
        "price_to_book": price_to_book,
        "ev_revenue_benchmark": ev_rev_benchmark,
        "pb_benchmark": pb_benchmark,
        "ev_revenue_signal": ev_rev_signal,
        "pb_signal": pb_signal,
        "bridge_note": (
            f"EV ${enterprise_value/1e6:.1f}M − Net Debt ${net_debt/1e6:.1f}M "
            f"= Equity ${equity_value/1e6:.1f}M ÷ {shares_outstanding//1_000_000}M shares "
            f"= ${raw_price_per_share:.2f}/share"
            + (f" → floored to ${SHARE_PRICE_FLOOR:.2f} (equity wiped out)"
               if price_per_share > raw_price_per_share else "")
        ),
    }


# ── Terminal Value ──────────────────────────────────────────────────────────
# ── EBITDA boundary (WARNING-3 fix) ─────────────────────────────────────────────
# When carbon_tax > gross_profit the raw EBITDA goes negative.
# A negative EBITDA times a positive exit_multiple produces a negative
# Enterprise Value, which is not meaningful in this educational simulation.
# The floor is 0.0 (liquidation value, not distressed M&A).
# The raw (un-floored) value is always returned as terminal_ebitda so the
# dashboard can surface a carbon-burden warning to players.
EBITDA_FLOOR: float = 0.0


def calculate_terminal_value(bus, mr, carbon_tax_per_ton=FINANCIAL_SHADOW_CARBON_PRICE,
                             exit_multiple=12.0, green_fund_balance=0.0,
                             is_advanced_climate=False, sdg_impact_score=0.0,
                             # STRAT-010 additions
                             wacc: float = FINANCIAL_WACC_LENDER_THRESHOLD,
                             use_dynamic_multiple: bool = False,
                             net_debt: float = 0.0,
                             book_equity: float = 0.0):
    """
    Compute Terminal Value (Enterprise Value) and full equity bridge.

    Formula:
        Terminal_EBITDA = Σ(Rev − OPEX) − (Carbon_Tons × Carbon_Tax)
        TV (EV)         = (EBITDA + Green_Fund) × Exit_Multiple × M_R × M_SDG
        Equity_Value    = TV − Net_Debt
        Price/Share     = Equity_Value / SHARES_OUTSTANDING

    STRAT-010 enhancement: when use_dynamic_multiple=True, exit_multiple is
    overridden by the Gordon Growth result, linking WACC to the multiple.

    FIX WARNING-3: EBITDA is floored at EBITDA_FLOOR (0.0) before being used
    in the TV formula.  When the carbon tax burden exceeds gross profit, the
    raw EBITDA would be negative, producing a mathematically impossible negative
    Enterprise Value.  The floor is a pedagogical liquidation-value signal: the
    company generates no cash value, but it is not worth negative money.
    The raw_ebitda is still returned as terminal_ebitda for full transparency.

    FIX WARNING-4: The mr parameter is clamped to [MR_FLOOR, MR_CEILING] here
    as a defensive guard, separate from the primary enforcement in calculate_mr().
    This protects against callers that pass a raw float instead of using the
    calculate_mr() return dict.
    """
    gross = sum(bu["revenue_base"] - bu["opex_base"] for bu in bus)
    total_revenue = sum(bu["revenue_base"] for bu in bus)
    tco2e = round(sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1e6 for bu in bus), 1)
    cc = round(tco2e * carbon_tax_per_ton, 2)

    # ── WARNING-3: EBITDA floor ──────────────────────────────────────────
    raw_ebitda: float = round(gross - cc, 2)
    ebitda_floored: bool = raw_ebitda < EBITDA_FLOOR
    ebitda: float = max(EBITDA_FLOOR, raw_ebitda)   # floored value used in TV formula

    # ── WARNING-4: M_R defensive clamp (secondary enforcement) ─────────────
    # Primary enforcement is in calculate_mr(). This guard catches raw floats.
    mr_raw_input: float = mr
    mr = round(max(MR_FLOOR, min(MR_CEILING, mr)), 4)
    mr_input_clamped: bool = mr_raw_input != mr

    base = ebitda + (green_fund_balance if is_advanced_climate else 0)
    sdg_result = calculate_sdg_multiplier(sdg_impact_score)
    m_sdg = sdg_result["m_sdg"]

    # Dynamic exit multiple (STRAT-010)
    dynamic_multiple_result = calculate_dynamic_exit_multiple(wacc=wacc)
    effective_multiple = dynamic_multiple_result["exit_multiple"] if use_dynamic_multiple else exit_multiple

    tv = round(base * effective_multiple * mr * m_sdg, 2)

    # Equity bridge (STRAT-010)
    bridge = calculate_equity_bridge(
        enterprise_value=tv,
        net_debt=net_debt,
        shares_outstanding=SHARES_OUTSTANDING,
        book_equity=book_equity,
        total_revenue=total_revenue,
    )

    return {
        "gross_profit":           round(gross, 2),
        "total_revenue":          round(total_revenue, 2),
        "tco2e_emissions":        tco2e,
        "carbon_cost":            cc,
        "carbon_tax_per_ton":     carbon_tax_per_ton,
        # WARNING-3 transparency fields
        "terminal_ebitda":        raw_ebitda,          # true un-floored EBITDA (for reporting)
        "ebitda_used_for_tv":     ebitda,              # floored value actually used in formula
        "ebitda_floored":         ebitda_floored,      # True ⇒ carbon burden exceeded gross profit
        "ebitda_floor_note": (
            "⚠️ Carbon tax exceeded gross profit. "
            "EBITDA floored at $0 for TV calculation. "
            "Your carbon burden is destroying operating value — decarbonise urgently."
        ) if ebitda_floored else None,
        "green_fund_included":    green_fund_balance if is_advanced_climate else 0,
        "exit_multiple":          effective_multiple,
        "exit_multiple_source":   "dynamic_wacc_gordon_growth" if use_dynamic_multiple else "fixed",
        "dynamic_exit_multiple_detail": dynamic_multiple_result,
        # WARNING-4 transparency fields
        "regenerative_multiple":  mr,                 # clamped M_R used in formula
        "mr_input_clamped":       mr_input_clamped,   # True ⇒ caller passed out-of-bounds raw float
        "mr_ceiling":             MR_CEILING,
        "mr_floor":               MR_FLOOR,
        "sdg_multiplier":         m_sdg,
        "sdg_impact_score":       sdg_impact_score,
        "sdg_track_active":       sdg_result["sdg_track_active"],
        "terminal_value":         tv,
        # STRAT-010 equity bridge fields
        "equity_value":           bridge["equity_value"],
        "price_per_share":        bridge["price_per_share"],          # floored at $1
        "equity_wiped_out":       bridge["equity_wiped_out"],         # honest insolvency signal
        "equity_bridge":          bridge,
        "net_debt":               net_debt,
        "shares_outstanding":     SHARES_OUTSTANDING,
    }

# ── Archetype Determination ─────────────────────────────────────────────────
_THRESHOLDS = {"regenerative_titan": 1.8, "derisked_safe_haven": 1.2, "fragile_giant": 0.8}
_ARCHETYPES = {
    "regenerative_titan": {"title": "The Regenerative Titan", "icon": "\U0001f331",
        "gradient": "linear-gradient(135deg, #10b981, #059669)"},
    "derisked_safe_haven": {"title": "The De-risked Safe-Haven", "icon": "\U0001f3e6",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)"},
    "fragile_giant": {"title": "The Fragile Giant", "icon": "\u26a0\ufe0f",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"},
    "stranded_relic": {"title": "The Stranded Relic", "icon": "\U0001f480",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"},
    # AR-B: two-axis matrix labels. `determine_archetype` classifies on M_R
    # alone (used by what-if projections + the turnaround re-valuation, where the
    # solvency axis is out of frame); the authoritative two-axis R10 mapping —
    # which actually awards these two — lives in
    # round_logic.solvency_gated_profile. They are mirrored here so any label
    # lookup by key resolves to a title/gradient.
    "pragmatic_operator": {"title": "The Pragmatic Operator", "icon": "\U0001f9ed",
        "gradient": "linear-gradient(135deg, #475569, #334155)"},
    "hollow_idealist": {"title": "The Hollow Idealist", "icon": "\U0001f573️",
        "gradient": "linear-gradient(135deg, #a855f7, #7e22ce)"},
    "turnaround_manager": {"title": "The Turnaround Manager", "icon": "🔧",
        "gradient": "linear-gradient(135deg, #8b5cf6, #6d28d9)"},
}

def determine_archetype(mr, thresholds=None, custom_archetypes=None, survival_mode=False):
    t = thresholds or _THRESHOLDS
    a = custom_archetypes or _ARCHETYPES
    # Survival mode: M_R capped at 0.80, always maps to turnaround_manager
    if survival_mode:
        mr = min(mr, 0.80)
        return {"key": "turnaround_manager", **a.get("turnaround_manager", _ARCHETYPES["turnaround_manager"]),
                "mr_capped": True, "original_mr": mr}
    if mr >= t.get("regenerative_titan", 1.8): key = "regenerative_titan"
    elif mr >= t.get("derisked_safe_haven", 1.2): key = "derisked_safe_haven"
    elif mr >= t.get("fragile_giant", 0.8): key = "fragile_giant"
    else: key = "stranded_relic"
    return {"key": key, **a.get(key, _ARCHETYPES["stranded_relic"])}

# ── STRAT-003: What-If Mode ─────────────────────────────────────────────────
def what_if_terminal(bus, base_flags, flag_overrides, avg_slo, avg_burnout,
                     workforce_readiness, synergy_multiplier, hr_investment_rounds=0,
                     carbon_tax_per_ton=FINANCIAL_SHADOW_CARBON_PRICE, exit_multiple=12.0,
                     green_fund_balance=0.0, is_advanced_climate=False,
                     wacc: float = FINANCIAL_WACC_LENDER_THRESHOLD, use_dynamic_multiple: bool = False,
                     net_debt: float = 0.0, book_equity: float = 0.0):
    base_mr = calculate_mr(base_flags, avg_slo, avg_burnout, workforce_readiness,
                           synergy_multiplier, hr_investment_rounds)
    base_tv = calculate_terminal_value(bus, base_mr["mr"], carbon_tax_per_ton,
                                       exit_multiple, green_fund_balance, is_advanced_climate,
                                       wacc=wacc, use_dynamic_multiple=use_dynamic_multiple,
                                       net_debt=net_debt, book_equity=book_equity)
    merged = {**base_flags, **flag_overrides}
    wi_mr = calculate_mr(merged, avg_slo, avg_burnout, workforce_readiness,
                         synergy_multiplier, hr_investment_rounds)
    wi_tv = calculate_terminal_value(bus, wi_mr["mr"], carbon_tax_per_ton,
                                     exit_multiple, green_fund_balance, is_advanced_climate,
                                     wacc=wacc, use_dynamic_multiple=use_dynamic_multiple,
                                     net_debt=net_debt, book_equity=book_equity)
    return {
        "baseline": {"mr": base_mr["mr"], "mr_breakdown": base_mr["breakdown"],
                     "terminal_value": base_tv["terminal_value"],
                     "equity_value": base_tv["equity_value"],
                     "price_per_share": base_tv["price_per_share"],
                     "archetype": determine_archetype(base_mr["mr"])},
        "what_if": {"mr": wi_mr["mr"], "mr_breakdown": wi_mr["breakdown"],
                    "terminal_value": wi_tv["terminal_value"],
                    "equity_value": wi_tv["equity_value"],
                    "price_per_share": wi_tv["price_per_share"],
                    "archetype": determine_archetype(wi_mr["mr"]), "flags_changed": flag_overrides},
        "delta": {"mr_change": round(wi_mr["mr"] - base_mr["mr"], 4),
                  "tv_change": round(wi_tv["terminal_value"] - base_tv["terminal_value"], 2),
                  "equity_change": round(wi_tv["equity_value"] - base_tv["equity_value"], 2),
                  "price_change": round(wi_tv["price_per_share"] - base_tv["price_per_share"], 2),
                  "archetype_changed": determine_archetype(wi_mr["mr"])["key"] != determine_archetype(base_mr["mr"])["key"]},
    }

# ── STRAT-004 / GAME-3: Cross-Pathway M_R Normalization ─────────────────────
# Coefficients now load from simulation_config.json (terminal_valuation.
# pathway_difficulty) so they can be recalibrated without code changes via
# scripts/calibrate_pathway_difficulty.py. The import fallback keeps the
# previous values if config is unavailable.
try:
    from config import TV_PATHWAY_DIFFICULTY as PATHWAY_DIFFICULTY
except Exception:
    PATHWAY_DIFFICULTY = {
        "activist_ultimatum": 1.00, "climate_black_swan": 1.15,
        "stakeholder_revolt": 1.10, "hostile_takeover": 1.20, "regulatory_shutdown": 1.12,
    }

def normalize_mr_for_leaderboard(raw_mr, ending_pathway, custom_difficulty=None):
    d = custom_difficulty or PATHWAY_DIFFICULTY
    c = d.get(ending_pathway, 1.0)
    n = round(raw_mr * c, 4)
    return {"raw_mr": raw_mr, "pathway": ending_pathway, "difficulty_coefficient": c,
            "normalized_mr": n, "archetype_raw": determine_archetype(raw_mr)["key"],
            "archetype_normalized": determine_archetype(n)["key"]}

# ── STRAT-002: Flag Dependency Graph ────────────────────────────────────────
FLAG_DEPENDENCY_GRAPH = [
    {"source_round": 1, "flag": "deep_audit_completed", "target_round": 4, "effect": "Halves crisis severity (40 vs 80)", "category": "governance"},
    {"source_round": 1, "flag": "electronics_blindspot", "target_round": 4, "effect": "Doubles crisis severity to 80", "category": "risk"},
    {"source_round": 2, "flag": "materiality_aligned", "target_round": 10, "effect": "+0.10 M_R Governance bonus", "category": "governance"},
    {"source_round": 2, "flag": "blockchain_traceability", "target_round": 8, "effect": "Prevents supply chain scandal", "category": "supply_chain"},
    {"source_round": 3, "flag": "early_decarboniser", "target_round": 7, "effect": "+0.10 synergy multiplier bonus", "category": "climate"},
    {"source_round": 3, "flag": "greenwash_risk", "target_round": 5, "effect": "Triggers greenwash if inv<15%", "category": "risk"},
    {"source_round": 5, "flag": "insurance_only", "target_round": 10, "effect": "BLOCKS +0.20 Resilience M_R bonus", "category": "climate"},
    {"source_round": 6, "flag": "ethical_ai_overhaul", "target_round": 10, "effect": "+0.15 Truth Premium M_R", "category": "governance"},
    {"source_round": 6, "flag": "ai_monetised", "target_round": 7, "effect": "EU AI Act costs from R7+", "category": "risk"},
    {"source_round": 7, "flag": "synergy_unlock", "target_round": 10, "effect": "+0.15 Synergy M_R (strategic premium; OPEX savings already in EBITDA)", "category": "strategic"},
    {"source_round": 8, "flag": "electronics_water_priority", "target_round": 10, "effect": "BLOCKS +0.20 Resilience M_R bonus", "category": "risk"},
    {"source_round": 9, "flag": "community_fund", "target_round": 10, "effect": "+0.18 Community Champion M_R (xJT)", "category": "social"},
    {"source_round": 9, "flag": "managed_transition", "target_round": 10, "effect": "+0.12 Just Transition M_R (xJT)", "category": "social"},
    # BRSR NGRBC Track
    {"source_round": "BRSR-1", "flag": "brsr_pioneer", "target_round": 10, "effect": "Enables BRSR Pioneer archetype path", "category": "governance"},
    {"source_round": "BRSR-1", "flag": "governance_fragility", "target_round": "BRSR-5", "effect": "Triggers Whistleblower Governance Leak (-$2.5M)", "category": "governance"},
    {"source_round": "BRSR-4", "flag": "brsr_greenwash_risk", "target_round": "BRSR-4", "effect": "Triggers SEBI Show-Cause Notice (-12 Reputation)", "category": "risk"},
    {"source_round": "BRSR-5", "flag": "brsr_net_positive_dividend", "target_round": 10, "effect": "+0.05 ESG Alpha Dividend M_R (BRSR Pioneer)", "category": "governance"},
]

def get_flag_dependency_graph(active_flags=None):
    graph = []
    for dep in FLAG_DEPENDENCY_GRAPH:
        entry = {**dep}
        if active_flags is not None:
            entry["status"] = "active" if dep["flag"] in active_flags else "inactive"
        graph.append(entry)
    cats = {}
    for e in graph:
        cats.setdefault(e.get("category", "other"), []).append(e)
    return {"dependencies": graph, "by_category": cats, "total_flags": len(graph),
            "active_count": sum(1 for e in graph if e.get("status") == "active") if active_flags else None}
