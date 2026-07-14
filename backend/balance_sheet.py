"""
Muressons Global Corporation — Balance Sheet Engine (SE-6)
Provides a simplified corporate balance sheet view alongside the
existing treasury (cash flow) management.

Theory base:
  - IFRS/IAS 1: Statement of Financial Position
  - IAS 16: Property, Plant and Equipment (CAPEX capitalisation, depreciation)
  - IAS 36: Impairment of Assets (goodwill impairment testing)
  - IAS 37: Provisions, Contingent Liabilities (environmental provisions, reversals)
  - IAS 38: Intangible Assets (recognition criteria)
  - IFRS 16: Leases (ROU asset and lease liability amortisation)
  - Integrated Reporting <IR> Framework: 6 capitals model (ESG capitals reported
    as off-balance-sheet disclosures, not on-GAAP-balance-sheet assets per IAS 38)
  - Modigliani-Miller: Capital structure relevance in ESG context
  - Carbon Tracker Initiative: Stranded asset methodology

Architecture:
  Pure-function module. Maintains assets, liabilities, and equity
  as a parallel state dict updated each round.

Key Concepts:
  - Tangible Assets (plant, equipment, inventory)
  - Intangible Assets (brand value, IP, goodwill)
  - ESG Capitals: social licence and reputation reported as off-balance-sheet
    non-GAAP disclosures (IAS 38 prohibits capitalising internally generated assets)
  - Liabilities (debt, provisions, environmental remediation)
  - Debt Covenants (trigger points for lender intervention)
  - Stranded Asset Risk (asset write-downs from transition)

Fixes applied (see balance_sheet_critique.md for full analysis):
  FIX-1:  Opening BS anchored to funding sources (Option B) — A = L + E enforced
  FIX-2:  Brand value uses fixed BASE constant (Option B) — prevents exponential compounding
  FIX-3:  Dividends removed from net income; correctly deducted from retained earnings
  FIX-4:  EBITDA adds back depreciation for covenant ratio (true EBITDA, not gross profit)
  FIX-5:  CAPEX depreciated from next period (IAS 16 §55 — opening PPE as depreciation base)
  FIX-6:  Environmental provisions can decrease when NCD falls (IAS 37 §59 reversal)
  FIX-7:  Inventory updated dynamically each round (60-day stock level model)
  FIX-8:  Social licence & reputation moved to off-BS esg_capitals dict (IAS 38 compliance)
  FIX-9:  Goodwill impairment smoothed + dual trigger: reputation AND EBITDA margin (IAS 36)
  FIX-10: Trade receivables note added re: DSO coordination with engine.py
  FIX-11: Interest expense uses ESG-WACC when available (unified rate)
  FIX-12: Decommissioning obligations accrete at discount rate (IAS 37 / IFRIC 1)
  FIX-13: Fixed items (revolving credit, brand base, goodwill, equity) scale with n_bus
          to ensure model is valid for single-BU and multi-BU configurations
"""

from __future__ import annotations
from typing import Any
import copy
import math
from config import (
    CONSTRAINT_MIN_LIQUIDITY_RATIO,
    FINANCIAL_CORPORATE_TAX_RATE,
    FINANCIAL_WACC_LENDER_THRESHOLD,
    BS_NCD_PROVISION_PER_UNIT,
    BS_NCD_EVENT_PROVISION,
    BS_SLO_CAPITAL_SCALING,
    BS_REP_CAPITAL_SCALING,
    BS_COVENANT_GREEN_RATIO,
    BS_CAPEX_CAPITALISATION_RATE,
    BS_ANNUAL_DEPRECIATION_RATE,
    BS_BRAND_BASE_PER_BU,
    BS_MIN_ENVIRONMENTAL_PROVISION,
    BS_DECOMMISSIONING_ACCRETION,
)



# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

# CAPEX capitalisation rate: % of total player investment that
# becomes PPE (tangible asset).  The remainder is expensed as
# operational improvement through the P&L.
CAPEX_CAPITALISATION_RATE = BS_CAPEX_CAPITALISATION_RATE

# Straight-line depreciation: annual rate for industrial conglomerate.
# Applied as half per 6-month round (10% annual → 5% per round).
ANNUAL_DEPRECIATION_RATE = BS_ANNUAL_DEPRECIATION_RATE
PERIOD_DEPRECIATION_RATE = ANNUAL_DEPRECIATION_RATE / 2

# Effective corporate tax rate for P&L → equity bridge
EFFECTIVE_TAX_RATE = FINANCIAL_CORPORATE_TAX_RATE

# FIX-2: Stable brand valuation BASE per BU.
# Brand value is always computed against this base (not against
# the prior-period value) to prevent exponential compounding.
# $6.25M per BU → $25M for the standard 4-BU configuration.
BRAND_BASE_PER_BU = BS_BRAND_BASE_PER_BU

# FIX-6: Minimum irreducible environmental provision floor.
# Represents baseline decommissioning/monitoring obligations that
# persist even after NCD is reduced. Per IAS 37 §59, provisions
# above this floor may be reversed when the obligating event no longer exists.
MIN_ENVIRONMENTAL_PROVISION = BS_MIN_ENVIRONMENTAL_PROVISION

# FIX-12: Discount rate for decommissioning obligation accretion (IAS 37 / IFRIC 1).
# Represents the risk-free rate applied to unwind the provision's time-value component.
DECOMMISSIONING_ACCRETION_RATE = BS_DECOMMISSIONING_ACCRETION  # 3% annual → 1.5% per 6-month round


# ═══════════════════════════════════════════════════════════════
#  INITIAL STATE
# ═══════════════════════════════════════════════════════════════

def create_initial_balance_sheet(bus: list[dict]) -> dict[str, Any]:
    """
    Create opening balance sheet from BU configuration.

    FIX-1 (Option B): All asset and liability lines are first set to
    economically grounded values. PPE is anchored to long-term funding
    sources (long-term liabilities + equity) rather than an arbitrary
    revenue multiple. Retained earnings are then DERIVED as the closing
    figure to enforce A = L + E from Round 1.

    FIX-13: Fixed items (revolving credit, brand base, goodwill, equity
    seed components) scale linearly with n_bus so the model is valid for
    both single-BU and multi-BU simulations.
    """
    n_bus = max(1, len(bus))
    total_revenue = sum(bu.get("revenue_base", 10_000_000) for bu in bus)
    total_opex = sum(bu.get("opex_base", 8_000_000) for bu in bus)

    # ── Scale fixed monetary items by BU count ──────────────────────────────
    # Calibrated to $50M / 4 BUs = $12.5M per BU for revolving credit, etc.
    revolving_credit      = round(12_500_000 * n_bus, 2)   # $12.5M / BU → $50M for 4 BUs
    brand_base            = round(BRAND_BASE_PER_BU * n_bus, 2)  # $6.25M / BU → $25M for 4 BUs
    goodwill_seed         = round(2_500_000 * n_bus, 2)    # $2.5M / BU  → $10M for 4 BUs
    env_provisions_seed   = round(1_250_000 * n_bus, 2)    # $1.25M / BU → $5M for 4 BUs
    decommissioning_seed  = round(750_000 * n_bus, 2)      # $0.75M / BU → $3M for 4 BUs
    share_capital_seed    = round(7_500_000 * n_bus, 2)    # $7.5M / BU  → $30M for 4 BUs
    other_reserves_seed   = round(1_250_000 * n_bus, 2)    # $1.25M / BU → $5M for 4 BUs

    # IP scales with both a base and per-BU component (unchanged from original)
    ip_value = round(15_000_000 + n_bus * 2_000_000, 2)

    # ── Non-PPE asset lines ─────────────────────────────────────────────────
    # FIX-7: Inventory uses OPEX-based 60-day stock model (not fixed revenue multiple).
    # At seed, we use the BU OPEX as proxy for cost of goods.
    inventory_days = 60
    inventory = round((total_opex / 365) * inventory_days, 2)

    rou_assets         = round(total_revenue * 0.40, 2)   # IFRS 16: 40% revenue as lease base
    trade_receivables  = round(total_revenue * 0.12, 2)   # DSO ~44 days at seed (no gov risk premium)
    prepayments        = round(250_000 * n_bus, 2)         # $250K/BU → $1M for 4 BUs

    # ── Liability lines ─────────────────────────────────────────────────────
    # FIX-1: Tax provisions are zero at opening — no earnings have been recognised yet.
    lease_liabilities  = round(total_revenue * 0.35, 2)
    # Note: trade payables at seed use revenue proxy (opex not yet in scope at initialisation)
    trade_payables     = round(total_revenue * 0.12, 2)

    # ── Derive PPE to close the accounting equation (Option B) ─────────────
    # PPE = long-term funding (LT liabilities + equity) - other LT assets (ROU, intangibles)
    # Since retained_earnings is unknown, we instead:
    #   Step A: sum all non-PPE assets
    #   Step B: sum all liabilities
    #   Step C: set PPE = total_liabilities + share_capital + other_reserves - non_ppe_assets
    #   Step D: retained_earnings is then derived from the closing identity:
    #           retained_earnings = total_assets - total_liabilities - share_capital - other_reserves
    #
    # This guarantees A = L + E at initialisation with no residual imbalance.

    non_ppe_assets = (
        inventory + rou_assets + brand_base + ip_value + goodwill_seed
        + 0.0             # cash (synced later)
        + trade_receivables + prepayments
    )

    total_liabilities_seed = (
        revolving_credit + 0.0  # green bonds = 0
        + env_provisions_seed + decommissioning_seed + lease_liabilities
        + trade_payables + 0.0  # tax provisions = 0 at opening
        + 0.0  # accrued remediation, short term debt = 0
    )

    fixed_equity = share_capital_seed + other_reserves_seed

    # PPE anchored to long-term funding sources
    ppe_seed = round(
        total_liabilities_seed + fixed_equity - non_ppe_assets, 2
    )

    # Ensure PPE is positive; if not (very small single-BU cases), floor at minimal tangible base
    ppe_seed = max(round(total_revenue * 0.30, 2), ppe_seed)

    total_assets_seed = non_ppe_assets + ppe_seed
    retained_earnings_seed = round(
        total_assets_seed - total_liabilities_seed - fixed_equity, 2
    )

    return {
        # ── ASSETS ──
        "tangible_assets": {
            "property_plant_equipment": ppe_seed,
            "inventory": inventory,
            "right_of_use_assets": rou_assets,
        },
        "intangible_assets": {
            "brand_value": brand_base,
            "intellectual_property": ip_value,
            "goodwill": goodwill_seed,
            # FIX-8: Social licence and reputation are NOT on-GAAP assets (IAS 38).
            # They are recorded in esg_capitals as non-GAAP disclosures only.
        },
        "current_assets": {
            "cash_and_equivalents": 0.0,    # Synced from corporate_treasury each round
            "trade_receivables": trade_receivables,
            "prepayments": prepayments,
        },

        # ── LIABILITIES ──
        "non_current_liabilities": {
            "revolving_credit_facility": revolving_credit,
            "green_bonds_outstanding": 0.0,
            "environmental_provisions": env_provisions_seed,
            "decommissioning_obligations": decommissioning_seed,
            "lease_liabilities": lease_liabilities,
        },
        "current_liabilities": {
            "trade_payables": trade_payables,
            "tax_provisions": 0.0,          # FIX-1: Zero at opening — no P&L yet recognised
            "accrued_remediation": 0.0,
            "short_term_debt": 0.0,
        },

        # ── EQUITY ──
        "share_capital": share_capital_seed,
        "retained_earnings": retained_earnings_seed,   # FIX-1: Derived to close A = L + E
        "other_reserves": other_reserves_seed,

        # ── ESG CAPITALS (off-balance-sheet non-GAAP disclosures) ──────────
        # FIX-8: Per IAS 38, internally generated intangibles cannot be recognised
        # on the GAAP balance sheet. Social licence and reputation are reported here
        # as <IR> Framework capitals and are excluded from total_assets.
        "esg_capitals": {
            "social_licence_capital": 0.0,    # Updated each round: avg_slo × $200K
            "reputation_capital": 0.0,         # Updated each round: group_rep × $300K
            "esg_note": (
                "Non-GAAP ESG capitals per <IR> Framework Six Capitals model. "
                "Excluded from IFRS total assets per IAS 38 (internally generated assets). "
                "Disclosed for integrated reporting purposes only."
            ),
        },

        # ── BRAND BASE (internal reference for FIX-2) ──────────────────────
        # The stable base against which brand is always revalued. Never changes.
        "_brand_value_base": brand_base,

        # ── METRICS ──
        "total_assets": 0.0,           # Calculated each round
        "total_liabilities": 0.0,      # Calculated each round
        "net_assets": 0.0,             # Calculated (= total equity)
        "debt_to_equity": 0.0,         # Leverage ratio
        "net_debt_to_ebitda": 0.0,     # Covenant metric (true EBITDA with D&A addback)
        "stranded_asset_exposure": 0.0,
        "covenant_status": "green",    # green, amber, red, breached
        "covenant_trigger_ratio": 3.5, # Net debt / EBITDA trigger

        "balance_sheet_history": [],
    }


# ═══════════════════════════════════════════════════════════════
#  ASSET VALUATION ENGINES
# ═══════════════════════════════════════════════════════════════

def calc_brand_value(
    brand_base: float,
    group_reputation: float,
    avg_slo: float,
) -> tuple[float, dict]:
    """
    FIX-2 (Option B): Brand value is always computed against the stable
    OPENING BASE (stored as bs["_brand_value_base"]), not the prior-period
    value. This prevents exponential compounding.

    Formula: Brand = Base × (Rep/50) × sqrt(SLO/50)

    Bounds:
      - Rep=100, SLO=100: Brand = Base × 2.0 × 1.414 = 2.83× base (~floor: ×0.01)
      - Rep=50,  SLO=50:  Brand = Base × 1.0 × 1.0   = 1.00× base (neutral)
      - Rep=10,  SLO=10:  Brand = Base × 0.2 × 0.447 = 0.09× base
      - Floor at $1M to preserve residual brand value.

    The sqrt dampening on SLO reflects diminishing returns: community trust
    is necessary but not sufficient to drive brand premium alone.
    """
    rep_factor = max(0.1, group_reputation / 50.0)
    slo_factor = max(0.1, math.sqrt(avg_slo / 50.0))
    new_brand = round(brand_base * rep_factor * slo_factor, 2)
    new_brand = max(1_000_000, new_brand)  # Floor: brand always has some residual value

    return new_brand, {
        "base_used": brand_base,
        "new": new_brand,
        "rep_factor": round(rep_factor, 3),
        "slo_factor": round(slo_factor, 3),
        "delta_from_base": round(new_brand - brand_base, 2),
        "compounding_prevented": True,   # Diagnostic flag confirming FIX-2 is active
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
    min_provision: float = MIN_ENVIRONMENTAL_PROVISION,
) -> float:
    """
    FIX-6 (IAS 37 §59 — Provision reversal allowed):
    Environmental provisions are updated based on current NCD and active
    remediation obligations. The old max() ratchet is removed — provisions
    can now DECREASE when NCD is reduced (e.g. after nature-based solutions),
    subject to a minimum irreducible floor.

    This correctly models IAS 37: provisions are reviewed at each balance
    sheet date and reversed if the obligating event no longer exists.

    Parameters:
        current_provisions: Prior-period provision (kept for diagnostic only)
        ncd: Current average Natural Capital Debt per BU
        remediation_events: Active remediation obligation events
        min_provision: Irreducible floor (decommissioning / monitoring minimum)
    """
    ncd_provision   = ncd * BS_NCD_PROVISION_PER_UNIT    # $BS_NCD_PROVISION_PER_UNIT per unit of NCD (regulatory anticipation)
    event_provision = len(remediation_events) * BS_NCD_EVENT_PROVISION

    new_provision = ncd_provision + event_provision
    # IAS 37 §59: reversals are permitted; floor at minimum irreducible obligation
    return round(max(min_provision, new_provision), 2)


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

    FIX-4: ebitda parameter must be TRUE EBITDA (gross profit + depreciation).
           Caller is responsible for passing the correct value.

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
        # VUL-016 FIX: distinguish true distress (no earnings + debt) from
        # net-cash position (no earnings but also no debt).
        # net_debt <= 0 means company holds more cash than debt — no breach risk.
        ratio = 99.0 if net_debt > 0 else 0.0
    else:
        ratio = round(net_debt / ebitda, 2)

    # Dynamic covenant tightening based on ESG-WACC
    # When WACC > FINANCIAL_WACC_LENDER_THRESHOLD, lenders tighten the trigger by 0.25x per 1% excess
    base_trigger = bs.get("covenant_trigger_ratio", 3.5)
    wacc_excess = max(0, esg_wacc - FINANCIAL_WACC_LENDER_THRESHOLD)  # Threshold from config
    wacc_tightening = round(wacc_excess * 25, 2)   # 25x per 1.0 = 0.25 per 1%
    effective_trigger = round(max(2.0, base_trigger - wacc_tightening), 2)

    if ratio <= BS_COVENANT_GREEN_RATIO:
        status = "green"
    elif ratio <= effective_trigger:
        status = "amber"
    elif ratio <= effective_trigger + 1.0:
        status = "red"
    else:
        status = "breached"

    # Surcharge on treasury for red / breached covenants (annualised, halved for 6-month period)
    surcharge = 0.0
    if status == "red":
        surcharge = round(max(0, net_debt) * 0.02 / 2, 2)
    elif status == "breached":
        surcharge = round(max(0, net_debt) * 0.05 / 2, 2)

    diagnostics = {
        "net_debt": round(net_debt, 2),
        "ebitda": round(ebitda, 2),
        "ratio": ratio,
        "trigger_ratio": effective_trigger,
        "base_trigger_ratio": base_trigger,
        "wacc_tightening": wacc_tightening,
        "esg_wacc_used": round(esg_wacc, 4),
        "status": status,
        "treasury_surcharge": surcharge,
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
    include_esg_on_bs: bool = False,
) -> tuple[dict, dict]:
    """
    Update balance sheet for one 6-month round.
    Called from run_new_engines() in round_logic.py after each player turn.

    Implements (with fix references):
    - FIX-5: CAPEX capitalisation timed correctly (IAS 16 §55)
    - FIX-4: True EBITDA = gross profit + depreciation for covenant ratio
    - FIX-3: Dividends correctly treated as equity distribution, not P&L expense
    - FIX-2: Brand revalued against stable base (no compounding)
    - FIX-8: ESG capitals as non-GAAP disclosures (not in total_assets)
    - FIX-9: Goodwill impairment — dual trigger + smooth impairment percentage
    - FIX-6: Environmental provisions reversible (IAS 37 §59)
    - FIX-7: Inventory updated dynamically each round
    - FIX-11: Interest expense uses ESG-WACC when available (unified rate)
    - FIX-12: Decommissioning obligations accrete at discount rate (IFRIC 1)

    Scholarly toggle (include_esg_on_bs):
    - When True: Social Licence Capital and Reputation Capital are moved
      from the non-GAAP esg_capitals dict onto the IFRS balance sheet as
      Intangible Assets (keys: esg_social_licence_capital, esg_reputation_capital).
      The closing identity in Step 8 automatically absorbs the increase into
      Retained Earnings — A = L + E is maintained without any extra logic.
      This is a pedagogical what-if mode; the scholarly debate is documented
      in diagnostics["esg_bs_mode"].
    - When False (default): IAS 38-compliant view — ESG capitals remain in
      esg_capitals only. Any residual esg_ intangible keys from a prior
      scholarly tick are cleared so the toggle is fully reversible.
    """
    diagnostics: dict[str, Any] = {}

    # ── Step 0: Extract key inputs ──────────────────────────────────────────
    n_bus = max(1, len(bus))
    total_revenue  = sum(bu.get("revenue_base", 0) for bu in bus)
    total_opex     = sum(bu.get("opex_base", 0) for bu in bus)
    gross_profit   = total_revenue - total_opex
    avg_gov_risk   = sum(bu.get("governance_risk_score", 20) for bu in bus) / n_bus
    ebitda_margin  = gross_profit / total_revenue if total_revenue > 0 else 0.0

    # Sync cash from corporate treasury (single source of truth for cash)
    bs["current_assets"]["cash_and_equivalents"] = gs.get("corporate_treasury", 0)

    # ── Step 1: CAPEX Capitalisation (IAS 16) ──────────────────────────────
    # FIX-5: Record opening PPE BEFORE adding new CAPEX so depreciation in
    # Step 2 is applied only to the opening balance (IAS 16 §55: depreciation
    # begins when the asset is available for use — i.e., the NEXT period).
    ppe_opening = bs["tangible_assets"]["property_plant_equipment"]

    total_capex      = events.get("total_capex_allocated", 0)
    capex_capitalised = round(total_capex * CAPEX_CAPITALISATION_RATE, 2)
    capex_expensed    = round(total_capex - capex_capitalised, 2)
    # New CAPEX added to PPE; will be depreciated starting next round
    bs["tangible_assets"]["property_plant_equipment"] = round(ppe_opening + capex_capitalised, 2)

    diagnostics["capex_capitalised"] = capex_capitalised
    diagnostics["capex_expensed"]    = capex_expensed

    # ── Step 2: Straight-Line Depreciation (IAS 16 + IFRS 16) ─────────────
    # FIX-5: Depreciate only ppe_opening (captured before CAPEX addition).
    # 5% per 6-month round (10% annual, ~10-year useful life for industrial equipment).
    depreciation = round(ppe_opening * PERIOD_DEPRECIATION_RATE, 2)
    bs["tangible_assets"]["property_plant_equipment"] = round(
        bs["tangible_assets"]["property_plant_equipment"] - depreciation, 2
    )

    # IFRS 16: Right-of-Use assets — 2.5% per round (5% annual, ~20-year property lease)
    rou_dep = round(bs["tangible_assets"]["right_of_use_assets"] * 0.025, 2)
    bs["tangible_assets"]["right_of_use_assets"] = round(
        bs["tangible_assets"]["right_of_use_assets"] - rou_dep, 2
    )

    total_depreciation = depreciation + rou_dep
    diagnostics["depreciation_charge"]      = total_depreciation
    diagnostics["ppe_after_depreciation"]   = bs["tangible_assets"]["property_plant_equipment"]

    # ── Step 3: Dynamic Working Capital ────────────────────────────────────
    # FIX-7: Inventory updated each round using 60-day stock model based on OPEX.
    # Note on FIX-10: The DSO factor below is a balance-sheet presentation proxy.
    # The engine.py cash-timing model (calc_dso_lag) is a separate cash-flow mechanism.
    # They represent different aspects: BS receivables (balance date stock) vs.
    # cash-flow timing (in-period collection lag).
    inventory_days = 60
    bs["tangible_assets"]["inventory"] = round((total_opex / 365) * inventory_days, 2)

    # Trade receivables: DSO-based balance sheet proxy (governance risk → longer DSO)
    dso_factor = min(0.25, 0.12 + 0.001 * avg_gov_risk)
    bs["current_assets"]["trade_receivables"] = round(total_revenue * dso_factor, 2)

    # Trade payables: DPO-based (governance risk → longer payment terms to suppliers)
    dpo_factor = min(0.18, 0.10 + 0.0005 * avg_gov_risk)
    bs["current_liabilities"]["trade_payables"] = round(total_opex * dpo_factor, 2)

    # Tax provisions: quarterly prepayment (~20% of annual tax liability)
    bs["current_liabilities"]["tax_provisions"] = round(
        max(0, gross_profit * EFFECTIVE_TAX_RATE * 0.20), 2
    )

    diagnostics["working_capital"] = {
        "dso_factor":   round(dso_factor, 4),
        "dpo_factor":   round(dpo_factor, 4),
        "receivables":  bs["current_assets"]["trade_receivables"],
        "payables":     bs["current_liabilities"]["trade_payables"],
        "inventory":    bs["tangible_assets"]["inventory"],
    }

    # ── Step 4: Intangible Asset Revaluation ───────────────────────────────
    avg_slo    = sum(bu.get("social_license_score", 50) for bu in bus) / n_bus
    group_rep  = gs.get("group_reputation", 50)

    # FIX-2: Pass the stable base (_brand_value_base) instead of current brand.
    brand_base = bs.get("_brand_value_base", BRAND_BASE_PER_BU * n_bus)
    new_brand, brand_diag = calc_brand_value(brand_base, group_rep, avg_slo)
    bs["intangible_assets"]["brand_value"] = new_brand
    diagnostics["brand_value"] = brand_diag

    # FIX-8: Social licence and reputation are non-GAAP <IR> Framework capitals.
    # Updated each round but stored in esg_capitals — NOT in intangible_assets —
    # so they do not inflate IFRS total_assets.
    if "esg_capitals" not in bs:
        bs["esg_capitals"] = {}
    _slc_value = round(avg_slo * BS_SLO_CAPITAL_SCALING, 2)
    _rep_value  = round(group_rep * BS_REP_CAPITAL_SCALING, 2)
    bs["esg_capitals"]["social_licence_capital"] = _slc_value
    bs["esg_capitals"]["reputation_capital"]     = _rep_value

    # ── Scholarly ESG Capitalisation Toggle ────────────────────────────────
    # When include_esg_on_bs is True, the facilitator/god-mode has activated
    # the pedagogical "what-if" view that recognises ESG capitals as GAAP
    # Intangible Assets (contra the IAS 38 prohibition on internally generated
    # intangibles). The esg_ prefix keys allow the frontend to distinguish them
    # from standard GAAP intangibles and render the appropriate scholarly banner.
    #
    # Scholarly references:
    #   - IIRC <IR> Framework (2013, 2021): advocates six-capitals recognition
    #   - Barker & Eccles (2011): critiques IAS 38 scope for knowledge assets
    #   - Gleeson-White (2014): Six Capitals — natural & social capital on BS
    if include_esg_on_bs:
        bs["intangible_assets"]["esg_social_licence_capital"] = _slc_value
        bs["intangible_assets"]["esg_reputation_capital"]     = _rep_value
        diagnostics["esg_bs_mode"] = {
            "active": True,
            "social_licence_on_bs": _slc_value,
            "reputation_on_bs": _rep_value,
            "total_esg_on_bs": round(_slc_value + _rep_value, 2),
            "note": (
                "SCHOLARLY VIEW: ESG capitals recognised as GAAP intangible assets. "
                "IAS 38 prohibits this in standard IFRS — pedagogical what-if only. "
                "Retained Earnings increases by the same amount (closing identity). "
                "References: IIRC <IR> Framework; Barker & Eccles (2011); Gleeson-White (2014)."
            ),
        }
    else:
        # Remove any residual esg_ keys from a prior scholarly tick (toggle reversal)
        bs["intangible_assets"].pop("esg_social_licence_capital", None)
        bs["intangible_assets"].pop("esg_reputation_capital", None)
        diagnostics["esg_bs_mode"] = {"active": False}

    # FIX-9: Goodwill impairment (IAS 36) — tested every 2 rounds (annual equivalent).
    # Dual trigger: reputation decline OR low EBITDA margin (proxy for recoverable amount).
    # Smooth impairment percentage (no cliff at rep=40 → min 10% hard floor removed).
    if round_number % 2 == 0:
        survival = gs.get("survival_mode", False)
        rep_impaired    = group_rep < 40
        margin_impaired = ebitda_margin < 0.10    # EBITDA margin < 10% → IAS 36 indicator
        if rep_impaired or margin_impaired or survival:
            # Smooth continuous impairment rate (no hard cliff):
            # From reputation: max(0, (40 - rep) / 200) → 0% at rep=40, 20% at rep=0
            # From margin: max(0, 0.10 - margin) × 0.5 → up to 5% additional
            rep_impairment_rate    = max(0.0, (40 - group_rep) / 200.0)
            margin_impairment_rate = max(0.0, (0.10 - ebitda_margin) * 0.5)
            impairment_pct         = min(0.30, rep_impairment_rate + margin_impairment_rate)
            goodwill_impairment    = round(bs["intangible_assets"]["goodwill"] * impairment_pct, 2)
            bs["intangible_assets"]["goodwill"] = round(
                max(0, bs["intangible_assets"]["goodwill"] - goodwill_impairment), 2
            )
            diagnostics["goodwill_impairment"] = {
                "amount": goodwill_impairment,
                "pct": round(impairment_pct * 100, 2),
                "trigger": "reputation" if rep_impaired else "ebitda_margin" if margin_impaired else "survival",
                "rep_rate": round(rep_impairment_rate * 100, 2),
                "margin_rate": round(margin_impairment_rate * 100, 2),
            }
        else:
            diagnostics["goodwill_impairment"] = {"amount": 0, "pct": 0.0, "trigger": "none"}

    # ── Step 5: Stranded Asset Exposure ────────────────────────────────────
    avg_ci  = sum(bu.get("carbon_intensity", 50) for bu in bus) / n_bus
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

    # ── Step 6: Liability Updates ───────────────────────────────────────────
    # FIX-6: Environmental provisions — reversible per IAS 37 §59.
    ncd_avg = sum(bu.get("natural_capital_debt", 0) for bu in bus) / n_bus
    bs["non_current_liabilities"]["environmental_provisions"] = calc_environmental_provisions(
        bs["non_current_liabilities"]["environmental_provisions"],
        ncd_avg,
        events.get("remediation_events", []),
    )

    # Green bonds tracking (issued by player decision, e.g. Round 3 Scope 3 option)
    if events.get("green_bond_issued"):
        bs["non_current_liabilities"]["green_bonds_outstanding"] += events.get(
            "green_bond_amount", 10_000_000
        )

    # IFRS 16: Lease liabilities amortise at 2.5%/round (~5% annual, 20-year lease)
    bs["non_current_liabilities"]["lease_liabilities"] = round(
        bs["non_current_liabilities"]["lease_liabilities"] * 0.975, 2
    )

    # FIX-12: Decommissioning obligation accretion (IAS 37 / IFRIC 1).
    # The present value of the decommissioning provision is unwound at the discount rate
    # each period (accretion = time-value cost of the obligation).
    # Accretion is treated as a finance cost (charged to interest expense in Step 7).
    decomm_accretion = round(
        bs["non_current_liabilities"]["decommissioning_obligations"] * DECOMMISSIONING_ACCRETION_RATE / 2, 2
    )
    bs["non_current_liabilities"]["decommissioning_obligations"] = round(
        bs["non_current_liabilities"]["decommissioning_obligations"] + decomm_accretion, 2
    )
    diagnostics["decommissioning_accretion"] = decomm_accretion

    # ── Step 7: Income Statement → Retained Earnings Bridge ────────────────
    # FIX-11: Use ESG-adjusted WACC for interest expense when available.
    # This unifies the rate used for the income statement and for covenant tightening,
    # eliminating the inconsistency between the two calculations.
    _esg_wacc_diag = gs.get("active_event_flags", {}).get("esg_adjusted_wacc", {})
    _esg_wacc = (
        _esg_wacc_diag.get("adjusted_wacc", gs.get("cost_of_capital", 0.05))
        if isinstance(_esg_wacc_diag, dict)
        else gs.get("cost_of_capital", 0.05)
    )

    total_debt = (
        bs["non_current_liabilities"]["revolving_credit_facility"]
        + bs["non_current_liabilities"]["green_bonds_outstanding"]
        + bs["current_liabilities"]["short_term_debt"]
    )

    # FIX-11: interest computed with unified ESG-WACC; also includes decommissioning accretion
    interest_expense  = round(total_debt * _esg_wacc / 2, 2)  # 6-month period
    interest_expense  = round(interest_expense + decomm_accretion, 2)  # FIX-12: accretion added

    taxable_income = gross_profit - interest_expense - total_depreciation - capex_expensed
    tax_charge     = round(max(0, taxable_income * EFFECTIVE_TAX_RATE), 2)

    # FIX-3: Net income EXCLUDES dividends — they are a distribution of profits, not an expense.
    # Net income = earnings available to shareholders; dividends reduce equity separately.
    # NOTE: retained_earnings is NOT updated here directly. Step 8 derives RE as a closing
    # figure (net_assets - share_capital - other_reserves) to enforce A = L + E.
    # net_income is preserved in diagnostics for income statement reporting and scoring.
    net_income = round(taxable_income - tax_charge, 2)
    dividends = events.get("dividends_paid", 0)
    # (No direct bs["retained_earnings"] update here — Step 8 closes the equation)

    diagnostics["income_statement"] = {
        "revenue":          round(total_revenue, 2),
        "opex":             round(total_opex, 2),
        "gross_profit":     round(gross_profit, 2),
        "depreciation":     total_depreciation,
        "capex_expensed":   capex_expensed,
        "interest_expense": interest_expense,
        "decomm_accretion_in_interest": decomm_accretion,
        "taxable_income":   round(taxable_income, 2),
        "tax_charge":       tax_charge,
        "net_income":       net_income,
        # FIX-3: dividends shown as equity movement, not P&L line
        "dividends_as_equity_distribution": dividends,
        "retained_earnings_movement": round(net_income - dividends, 2),
        "interest_rate_used": round(_esg_wacc, 4),
    }

    # ── Step 8: Calculate Totals and Close A = L + E ─────────────────────────
    # FIX-8: Only GAAP balance sheet items count toward total_assets.
    # esg_capitals dict is excluded (non-GAAP disclosure).
    total_tangible   = sum(bs["tangible_assets"].values())
    total_intangible = sum(bs["intangible_assets"].values())
    total_current    = sum(bs["current_assets"].values())
    bs["total_assets"] = round(total_tangible + total_intangible + total_current, 2)

    total_ncl = sum(bs["non_current_liabilities"].values())
    total_cl  = sum(bs["current_liabilities"].values())
    bs["total_liabilities"] = round(total_ncl + total_cl, 2)

    bs["net_assets"] = round(bs["total_assets"] - bs["total_liabilities"], 2)

    # ── Closing identity: re-derive retained earnings to enforce A = L + E ──
    # This simulation uses a hybrid cash-flow + accrual model. The income
    # statement (Step 7) derives net_income from BU revenue/opex (accrual
    # basis), but operational cash flows are managed externally by the treasury
    # engine. Adding raw net_income to RE each tick creates an unmatched equity
    # increase with no corresponding new asset on the balance sheet.
    #
    # Resolution (consistent with initialization approach): treat retained
    # earnings as the CLOSING / RESIDUAL equity figure. After all asset and
    # liability lines are updated, RE is set to the amount required to balance:
    #   retained_earnings = net_assets - share_capital - other_reserves
    #
    # The net_income figure computed in Step 7 is preserved in diagnostics
    # and history as an INCOME STATEMENT metric (it still drives performance
    # scoring and teaches P&L mechanics). It does NOT directly update RE;
    # instead, RE reflects the cumulative net asset position each period.
    fixed_equity = bs["share_capital"] + bs["other_reserves"]
    bs["retained_earnings"] = round(bs["net_assets"] - fixed_equity, 2)
    total_equity = round(bs["net_assets"], 2)  # Always equals net_assets by construction

    diagnostics["equity_check"]           = round(total_equity, 2)
    diagnostics["balance_sheet_balanced"] = True   # Always true after closing derivation
    diagnostics["imbalance"]              = 0.0
    diagnostics["net_income_p_and_l"]     = net_income   # Income statement figure (preserved)

    # Leverage ratios
    if total_equity > 0:
        bs["debt_to_equity"] = round(bs["total_liabilities"] / total_equity, 2)
    else:
        bs["debt_to_equity"] = 99.0

    # ── Step 9: Covenant Check (ESG-WACC aware, true EBITDA) ───────────────
    # FIX-4: True EBITDA = gross profit + depreciation (D&A added back).
    # Previously this was just gross profit, understating EBITDA and overstating the ratio.
    true_ebitda = round(gross_profit + total_depreciation, 2)

    covenant_status, covenant_diag = check_covenants(bs, true_ebitda, esg_wacc=_esg_wacc)
    bs["covenant_status"]    = covenant_status
    bs["net_debt_to_ebitda"] = covenant_diag["ratio"]
    diagnostics["covenants"] = covenant_diag

    # Liquidity Ratio check
    cash = bs["current_assets"]["cash_and_equivalents"]
    total_assets = bs["total_assets"]
    liquidity_ratio = round(cash / total_assets, 4) if total_assets > 0 else 0.0
    bs["liquidity_ratio"] = liquidity_ratio
    if liquidity_ratio < CONSTRAINT_MIN_LIQUIDITY_RATIO:
        if bs["covenant_status"] == "green":
            bs["covenant_status"] = "amber"
        diagnostics["liquidity_ratio_warning"] = (
            f"⚠️ Liquidity Ratio ({liquidity_ratio:.1%}) is below the required "
            f"minimum of {CONSTRAINT_MIN_LIQUIDITY_RATIO:.1%}."
        )


    # Apply covenant surcharge to treasury (lender penalty for red/breached status)
    surcharge = covenant_diag.get("treasury_surcharge", 0.0)
    if surcharge > 0 and "corporate_treasury" in gs:
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - surcharge, 2)
        bs["current_assets"]["cash_and_equivalents"] = gs["corporate_treasury"]
        diagnostics["covenant_surcharge_applied"] = surcharge

        # ── Recalculate totals after cash mutation ──────────────────────
        # The surcharge reduced cash_and_equivalents after Step 8 had already
        # finalised total_assets/net_assets/retained_earnings.  Re-derive all
        # downstream figures so the accounting equation (A = L + E) holds and
        # the frontend subtotals reconcile to the displayed total.
        bs["total_assets"] = round(
            sum(bs["tangible_assets"].values())
            + sum(bs["intangible_assets"].values())
            + sum(bs["current_assets"].values()), 2
        )
        bs["total_liabilities"] = round(
            sum(bs["non_current_liabilities"].values())
            + sum(bs["current_liabilities"].values()), 2
        )
        bs["net_assets"] = round(bs["total_assets"] - bs["total_liabilities"], 2)
        fixed_equity = bs["share_capital"] + bs["other_reserves"]
        bs["retained_earnings"] = round(bs["net_assets"] - fixed_equity, 2)

    # ── History ─────────────────────────────────────────────────────────────
    # Summary figures (kept flat for backward compatibility) PLUS a deep-copied
    # full line-item snapshot so a year-by-year Statement of Financial Position
    # can reproduce every asset / liability / equity line per round — not just
    # the totals. deepcopy is essential: the nested group dicts are mutated in
    # place each round, so a shallow reference would make every historical entry
    # show the final year's values. `full_statement` lets the UI detect snapshots
    # that predate this change and fall back to the summary rows.
    bs["balance_sheet_history"].append({
        "round":              round_number,
        "total_assets":       bs["total_assets"],
        "total_liabilities":  bs["total_liabilities"],
        "net_assets":         bs["net_assets"],
        "total_equity":       round(total_equity, 2),
        "d_e_ratio":          bs["debt_to_equity"],
        "covenant_status":    covenant_status,
        "net_income":         net_income,
        "dividends":          dividends,
        "retained_earnings":  bs["retained_earnings"],
        "ebitda":             true_ebitda,
        "balance_sheet_balanced": diagnostics["balance_sheet_balanced"],
        # ── Full line-item snapshot ──
        "full_statement":     True,
        "tangible_assets":         copy.deepcopy(bs.get("tangible_assets", {})),
        "intangible_assets":       copy.deepcopy(bs.get("intangible_assets", {})),
        "current_assets":          copy.deepcopy(bs.get("current_assets", {})),
        "non_current_liabilities": copy.deepcopy(bs.get("non_current_liabilities", {})),
        "current_liabilities":     copy.deepcopy(bs.get("current_liabilities", {})),
        "esg_capitals":            copy.deepcopy(bs.get("esg_capitals", {})),
        "share_capital":           bs.get("share_capital", 0),
        "other_reserves":          bs.get("other_reserves", 0),
        "net_debt_to_ebitda":      bs.get("net_debt_to_ebitda"),
        "liquidity_ratio":         bs.get("liquidity_ratio"),
        "stranded_asset_exposure": bs.get("stranded_asset_exposure"),
    })

    return bs, diagnostics
