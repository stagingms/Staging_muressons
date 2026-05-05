"""
Muressons Global Corporation — Balance Sheet Engine (SE-6)
Provides a simplified corporate balance sheet view alongside the
existing treasury (cash flow) management.

Theory base:
  - IFRS/IAS 1: Statement of Financial Position
  - Integrated Reporting <IR> Framework: 6 capitals model
  - Modigliani-Miller: Capital structure relevance in ESG context

Architecture:
  Pure-function module. Maintains assets, liabilities, and equity
  as a parallel state dict updated each round.

Key Concepts:
  - Tangible Assets (plant, equipment, inventory)
  - Intangible Assets (brand value, IP, goodwill)
  - ESG-Adjusted Intangibles (social licence, reputation as asset)
  - Liabilities (debt, provisions, environmental remediation)
  - Debt Covenants (trigger points for lender intervention)
  - Stranded Asset Risk (asset write-downs from transition)
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

# CAPEX capitalisation rate: % of total player investment that
# becomes PPE (tangible asset).  The remainder is expensed as
# operational improvement through the P&L.
CAPEX_CAPITALISATION_RATE = 0.60

# Straight-line depreciation: annual rate for industrial conglomerate.
# Applied as half per 6-month round (10% annual → 5% per round).
ANNUAL_DEPRECIATION_RATE = 0.10
PERIOD_DEPRECIATION_RATE = ANNUAL_DEPRECIATION_RATE / 2

# Effective corporate tax rate for P&L → equity bridge
EFFECTIVE_TAX_RATE = 0.25


# ═══════════════════════════════════════════════════════════════
#  INITIAL STATE
# ═══════════════════════════════════════════════════════════════

def create_initial_balance_sheet(bus: list[dict]) -> dict[str, Any]:
    """Create opening balance sheet from BU configuration."""
    n_bus = len(bus)
    total_revenue = sum(bu.get("revenue_base", 10_000_000) for bu in bus)

    return {
        # ── ASSETS ──
        "tangible_assets": {
            "property_plant_equipment": round(total_revenue * 2.5, 2),
            "inventory": round(total_revenue * 0.3, 2),
            "right_of_use_assets": round(total_revenue * 0.4, 2),
        },
        "intangible_assets": {
            "brand_value": 25_000_000,
            "intellectual_property": round(15_000_000 + n_bus * 2_000_000, 2),
            "goodwill": 10_000_000,
            "social_licence_asset": 0.0,  # Calculated from SLO scores
            "reputation_asset": 0.0,       # Calculated from reputation
        },
        "current_assets": {
            "cash_and_equivalents": 0.0,   # Synced from corporate_treasury
            "trade_receivables": round(total_revenue * 0.15, 2),
            "prepayments": 1_000_000,
        },

        # ── LIABILITIES ──
        "non_current_liabilities": {
            "revolving_credit_facility": 50_000_000,  # Syndicate banks
            "green_bonds_outstanding": 0.0,
            "environmental_provisions": 5_000_000,
            "decommissioning_obligations": 3_000_000,
            "lease_liabilities": round(total_revenue * 0.35, 2),
        },
        "current_liabilities": {
            "trade_payables": round(total_revenue * 0.12, 2),
            "tax_provisions": round(total_revenue * 0.05, 2),
            "accrued_remediation": 0.0,
            "short_term_debt": 0.0,
        },

        # ── EQUITY ──
        "share_capital": 30_000_000,
        "retained_earnings": 20_000_000,
        "other_reserves": 5_000_000,

        # ── METRICS ──
        "total_assets": 0.0,         # Calculated
        "total_liabilities": 0.0,    # Calculated
        "net_assets": 0.0,           # Calculated (= equity)
        "debt_to_equity": 0.0,       # Leverage ratio
        "net_debt_to_ebitda": 0.0,   # Covenant metric
        "stranded_asset_exposure": 0.0,
        "covenant_status": "green",  # green, amber, red, breached
        "covenant_trigger_ratio": 3.5,  # Net debt / EBITDA trigger

        "balance_sheet_history": [],
    }


# ═══════════════════════════════════════════════════════════════
#  ASSET VALUATION ENGINES
# ═══════════════════════════════════════════════════════════════

def calc_brand_value(
    current_brand: float,
    group_reputation: float,
    avg_slo: float,
) -> tuple[float, dict]:
    """
    Brand value as a function of reputation and social licence.
    Brand = Base × (Rep/50) × (SLO/50)^0.5
    Uses sqrt for SLO to model diminishing returns of community trust on brand.
    """
    rep_factor = max(0.1, group_reputation / 50.0)
    slo_factor = max(0.1, math.sqrt(avg_slo / 50.0))
    new_brand = round(current_brand * rep_factor * slo_factor, 2)
    new_brand = max(1_000_000, new_brand)  # Floor

    return new_brand, {
        "previous": current_brand,
        "new": new_brand,
        "rep_factor": round(rep_factor, 3),
        "slo_factor": round(slo_factor, 3),
        "delta": round(new_brand - current_brand, 2),
    }


def calc_stranded_assets(
    ppe: float,
    carbon_intensity_avg: float,
    tipping_tier: str,
    ending_pathway: str,
) -> tuple[float, dict]:
    """
    Stranded asset exposure: proportion of PPE at risk of write-down
    due to climate transition.

    Based on Carbon Tracker Initiative methodology.
    High carbon intensity + climate pathway = high stranded risk.
    """
    # Base risk from carbon intensity
    ci_risk = min(0.5, carbon_intensity_avg / 200.0)

    # Pathway modifier
    pathway_modifiers = {
        "climate_black_swan": 0.20,
        "activist_ultimatum": 0.10,
        "regulatory_shutdown": 0.15,
        "hostile_takeover": 0.05,
        "stakeholder_revolt": 0.08,
    }
    pathway_risk = pathway_modifiers.get(ending_pathway, 0.10)

    # Tipping tier modifier
    tipping_modifiers = {
        "tipped": 0.15,
        "stressed": 0.10,
        "warning": 0.05,
        "none": 0.0,
    }
    tipping_risk = tipping_modifiers.get(tipping_tier, 0.0)

    total_risk = min(0.80, ci_risk + pathway_risk + tipping_risk)
    exposure = round(ppe * total_risk, 2)

    return exposure, {
        "total_risk_pct": round(total_risk * 100, 1),
        "carbon_intensity_risk": round(ci_risk * 100, 1),
        "pathway_risk": round(pathway_risk * 100, 1),
        "tipping_risk": round(tipping_risk * 100, 1),
        "exposure_value": exposure,
        "risk_level": (
            "critical" if total_risk > 0.40
            else "high" if total_risk > 0.25
            else "moderate" if total_risk > 0.10
            else "low"
        ),
    }


def calc_environmental_provisions(
    current_provisions: float,
    ncd: float,
    remediation_events: list[str],
) -> float:
    """
    Environmental provisions grow with NCD and remediation obligations.
    IAS 37: Provisions are recognised when there is a present obligation.
    """
    # NCD drives provision growth (regulatory anticipation)
    ncd_provision = ncd * 5_000  # $5K per unit of NCD
    event_provision = len(remediation_events) * 2_000_000

    return round(max(current_provisions, ncd_provision + event_provision), 2)


# ═══════════════════════════════════════════════════════════════
#  DEBT COVENANTS
# ═══════════════════════════════════════════════════════════════

def check_covenants(
    bs: dict,
    ebitda: float,
    esg_wacc: float = 0.05,
) -> tuple[str, dict]:
    """
    Check debt covenant compliance.
    Primary covenant: Net Debt / EBITDA ≤ trigger ratio.

    The trigger ratio adjusts dynamically based on ESG-Adjusted WACC:
    - When WACC > 8%, lenders tighten covenants by -0.25× per 1% excess
    - This models the empirical finding that ESG risk increases lender scrutiny
      (El Ghoul et al., 2011; Sharfman & Fernando, 2008)

    Status levels:
      green   — ratio ≤ 2.5× (comfortable headroom)
      amber   — 2.5× < ratio ≤ trigger_ratio (watch list)
      red     — trigger_ratio < ratio ≤ trigger_ratio + 1.0× (technical breach, cure period)
      breached — ratio > trigger_ratio + 1.0× (acceleration rights triggered)
    """
    total_debt = (
        bs["non_current_liabilities"]["revolving_credit_facility"]
        + bs["non_current_liabilities"]["green_bonds_outstanding"]
        + bs["current_liabilities"]["short_term_debt"]
    )
    cash = bs["current_assets"]["cash_and_equivalents"]
    net_debt = total_debt - cash

    if ebitda <= 0:
        ratio = 99.0
    else:
        ratio = round(net_debt / ebitda, 2)

    # Dynamic covenant tightening based on ESG-WACC
    # When WACC > 8%, lenders tighten the trigger by 0.25x per 1% excess
    base_trigger = bs.get("covenant_trigger_ratio", 3.5)
    wacc_excess = max(0, esg_wacc - 0.08)  # Threshold: 8%
    wacc_tightening = round(wacc_excess * 25, 2)  # 25x per 1.0 = 0.25 per 1%
    effective_trigger = round(max(2.0, base_trigger - wacc_tightening), 2)

    if ratio <= 2.5:
        status = "green"
    elif ratio <= effective_trigger:
        status = "amber"
    elif ratio <= effective_trigger + 1.0:
        status = "red"
    else:
        status = "breached"

    diagnostics = {
        "net_debt": round(net_debt, 2),
        "ebitda": round(ebitda, 2),
        "ratio": ratio,
        "trigger_ratio": effective_trigger,
        "base_trigger_ratio": base_trigger,
        "wacc_tightening": wacc_tightening,
        "esg_wacc_used": round(esg_wacc, 4),
        "status": status,
        "message": {
            "green": "Debt covenants comfortably met. Syndicate banks satisfied.",
            "amber": "⚠️ Covenant headroom narrowing. Banks requesting periodic updates.",
            "red": "🔴 COVENANT BREACH: 30-day cure period activated. Banks may restrict facility.",
            "breached": "🚨 COVENANT ACCELERATION: Banks can demand immediate repayment of all facilities.",
        }[status],
    }

    return status, diagnostics


# ═══════════════════════════════════════════════════════════════
#  MAIN PROCESSOR
# ═══════════════════════════════════════════════════════════════

def process_balance_sheet_tick(
    bs: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> tuple[dict, dict]:
    """
    Update balance sheet for this round.
    Called from post_tick in round_logic.py.

    Enhanced with:
    - CAPEX capitalisation into PPE (IAS 16)
    - Straight-line depreciation (IAS 16)
    - Dynamic working capital (trade receivables/payables)
    - Net Income → Retained Earnings (replaces raw CSF)
    - Goodwill impairment testing (IAS 36)
    - Derived income statement diagnostics
    """
    diagnostics: dict[str, Any] = {}

    # ── Step 0: Extract key inputs ──
    total_revenue = sum(bu.get("revenue_base", 0) for bu in bus)
    total_opex = sum(bu.get("opex_base", 0) for bu in bus)
    gross_profit = total_revenue - total_opex
    avg_gov_risk = sum(bu.get("governance_risk_score", 20) for bu in bus) / max(len(bus), 1)

    # Sync cash from treasury
    bs["current_assets"]["cash_and_equivalents"] = gs.get("corporate_treasury", 0)

    # ── Step 1: CAPEX Capitalisation (IAS 16) ──
    # 60% of player's capital allocation → PPE (tangible asset)
    # 40% is expensed through P&L (process improvements, consulting)
    total_capex = events.get("total_capex_allocated", 0)
    capex_capitalised = round(total_capex * CAPEX_CAPITALISATION_RATE, 2)
    capex_expensed = round(total_capex - capex_capitalised, 2)
    bs["tangible_assets"]["property_plant_equipment"] += capex_capitalised
    diagnostics["capex_capitalised"] = capex_capitalised
    diagnostics["capex_expensed"] = capex_expensed

    # ── Step 2: Straight-Line Depreciation (IAS 16) ──
    # 5% per 6-month round (10% annual, ~10-year useful life for industrial)
    ppe_before_dep = bs["tangible_assets"]["property_plant_equipment"]
    depreciation = round(ppe_before_dep * PERIOD_DEPRECIATION_RATE, 2)
    bs["tangible_assets"]["property_plant_equipment"] = round(
        ppe_before_dep - depreciation, 2
    )
    # Also depreciate Right-of-Use assets (IFRS 16, simplified)
    rou_dep = round(bs["tangible_assets"]["right_of_use_assets"] * 0.025, 2)
    bs["tangible_assets"]["right_of_use_assets"] = round(
        bs["tangible_assets"]["right_of_use_assets"] - rou_dep, 2
    )
    total_depreciation = depreciation + rou_dep
    diagnostics["depreciation_charge"] = total_depreciation
    diagnostics["ppe_after_depreciation"] = bs["tangible_assets"]["property_plant_equipment"]

    # ── Step 3: Dynamic Working Capital ──
    # Trade receivables scale with revenue and governance risk (DSO proxy)
    dso_factor = min(0.25, 0.12 + 0.001 * avg_gov_risk)
    bs["current_assets"]["trade_receivables"] = round(total_revenue * dso_factor, 2)
    # Trade payables scale with OPEX
    dpo_factor = min(0.18, 0.10 + 0.0005 * avg_gov_risk)
    bs["current_liabilities"]["trade_payables"] = round(total_opex * dpo_factor, 2)
    # Tax provisions update from actual profit
    bs["current_liabilities"]["tax_provisions"] = round(
        max(0, gross_profit * EFFECTIVE_TAX_RATE * 0.20), 2  # ~20% of annual tax as provision
    )
    diagnostics["working_capital"] = {
        "dso_factor": round(dso_factor, 4),
        "dpo_factor": round(dpo_factor, 4),
        "receivables": bs["current_assets"]["trade_receivables"],
        "payables": bs["current_liabilities"]["trade_payables"],
    }

    # ── Step 4: Intangible Asset Revaluation ──
    # Update brand value
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
    new_brand, brand_diag = calc_brand_value(
        bs["intangible_assets"]["brand_value"],
        gs.get("group_reputation", 50),
        avg_slo,
    )
    bs["intangible_assets"]["brand_value"] = new_brand
    diagnostics["brand_value"] = brand_diag

    # Social licence as intangible asset (novel)
    bs["intangible_assets"]["social_licence_asset"] = round(avg_slo * 200_000, 2)
    bs["intangible_assets"]["reputation_asset"] = round(
        gs.get("group_reputation", 50) * 300_000, 2
    )

    # Goodwill impairment testing (IAS 36) — every 2 rounds (= annual)
    if round_number % 2 == 0:
        group_rep = gs.get("group_reputation", 50)
        survival = gs.get("survival_mode", False)
        if group_rep < 40 or survival:
            impairment_pct = max(0.10, (40 - group_rep) / 100)
            goodwill_impairment = round(
                bs["intangible_assets"]["goodwill"] * impairment_pct, 2
            )
            bs["intangible_assets"]["goodwill"] = round(
                max(0, bs["intangible_assets"]["goodwill"] - goodwill_impairment), 2
            )
            diagnostics["goodwill_impairment"] = goodwill_impairment
        else:
            diagnostics["goodwill_impairment"] = 0

    # ── Step 5: Stranded Asset Exposure ──
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    tipping = gs.get("tipping_tier", events.get("tipping_tier", "none"))
    pathway = gs.get("active_event_flags", {}).get("ending_pathway", "activist_ultimatum")
    exposure, stranded_diag = calc_stranded_assets(
        bs["tangible_assets"]["property_plant_equipment"],
        avg_ci,
        tipping,
        pathway,
    )
    bs["stranded_asset_exposure"] = exposure
    diagnostics["stranded_assets"] = stranded_diag

    # ── Step 6: Liability Updates ──
    # Environmental provisions
    ncd_avg = sum(bu.get("natural_capital_debt", 0) for bu in bus) / max(len(bus), 1)
    bs["non_current_liabilities"]["environmental_provisions"] = calc_environmental_provisions(
        bs["non_current_liabilities"]["environmental_provisions"],
        ncd_avg,
        events.get("remediation_events", []),
    )

    # Green bonds tracking
    if events.get("green_bond_issued"):
        bs["non_current_liabilities"]["green_bonds_outstanding"] += events.get(
            "green_bond_amount", 10_000_000
        )

    # Lease liabilities amortise slowly (IFRS 16 simplified)
    bs["non_current_liabilities"]["lease_liabilities"] = round(
        bs["non_current_liabilities"]["lease_liabilities"] * 0.975, 2
    )

    # ── Step 7: Income Statement → Retained Earnings Bridge ──
    # Derive Net Income for proper equity movement
    total_debt = (
        bs["non_current_liabilities"]["revolving_credit_facility"]
        + bs["non_current_liabilities"]["green_bonds_outstanding"]
        + bs["current_liabilities"]["short_term_debt"]
    )
    interest_rate = gs.get("cost_of_capital", 0.05)
    interest_expense = round(total_debt * interest_rate / 2, 2)  # 6-month period
    taxable_income = gross_profit - interest_expense - total_depreciation - capex_expensed
    tax_charge = round(max(0, taxable_income * EFFECTIVE_TAX_RATE), 2)
    dividends = events.get("dividends_paid", 0)
    net_income = round(taxable_income - tax_charge - dividends, 2)

    bs["retained_earnings"] = round(bs["retained_earnings"] + net_income, 2)

    diagnostics["income_statement"] = {
        "revenue": round(total_revenue, 2),
        "opex": round(total_opex, 2),
        "gross_profit": round(gross_profit, 2),
        "depreciation": total_depreciation,
        "capex_expensed": capex_expensed,
        "interest_expense": interest_expense,
        "taxable_income": round(taxable_income, 2),
        "tax_charge": tax_charge,
        "dividends": dividends,
        "net_income": net_income,
    }

    # ── Step 8: Calculate Totals ──
    total_tangible = sum(bs["tangible_assets"].values())
    total_intangible = sum(bs["intangible_assets"].values())
    total_current = sum(bs["current_assets"].values())
    bs["total_assets"] = round(total_tangible + total_intangible + total_current, 2)

    total_ncl = sum(bs["non_current_liabilities"].values())
    total_cl = sum(bs["current_liabilities"].values())
    bs["total_liabilities"] = round(total_ncl + total_cl, 2)

    bs["net_assets"] = round(bs["total_assets"] - bs["total_liabilities"], 2)

    # Equity check
    total_equity = bs["share_capital"] + bs["retained_earnings"] + bs["other_reserves"]
    diagnostics["equity_check"] = round(total_equity, 2)
    diagnostics["balance_sheet_balanced"] = abs(bs["net_assets"] - total_equity) < 1.0

    # Leverage ratios
    if total_equity > 0:
        bs["debt_to_equity"] = round(bs["total_liabilities"] / total_equity, 2)
    else:
        bs["debt_to_equity"] = 99.0

    # ── Step 9: Covenant Check (ESG-WACC aware) ──
    ebitda = sum(bu.get("revenue_base", 0) - bu.get("opex_base", 0) for bu in bus)
    _esg_wacc_diag = gs.get("active_event_flags", {}).get("esg_adjusted_wacc", {})
    _esg_wacc = _esg_wacc_diag.get("adjusted_wacc", gs.get("cost_of_capital", 0.05)) if isinstance(_esg_wacc_diag, dict) else gs.get("cost_of_capital", 0.05)
    covenant_status, covenant_diag = check_covenants(bs, ebitda, esg_wacc=_esg_wacc)
    bs["covenant_status"] = covenant_status
    bs["net_debt_to_ebitda"] = covenant_diag["ratio"]
    diagnostics["covenants"] = covenant_diag

    # History
    bs["balance_sheet_history"].append({
        "round": round_number,
        "total_assets": bs["total_assets"],
        "total_liabilities": bs["total_liabilities"],
        "net_assets": bs["net_assets"],
        "d_e_ratio": bs["debt_to_equity"],
        "covenant_status": covenant_status,
        "net_income": net_income,
    })

    return bs, diagnostics
