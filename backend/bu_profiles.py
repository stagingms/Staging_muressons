"""
Muressons Global Corporation — BU Profile Registry
Centralised financial baselines, slot-fit mapping, and market overlap data
for all default BUs and Industry Vertical alternatives.

Slot-Fit Restrictions:
  Each of the 4 default BU "slots" can only be replaced by verticals that
  share industry characteristics (heavy/light, physical/digital).
"""

from __future__ import annotations
from typing import Any

# ═══════════════════════════════════════════════════════════════
#  CORE BU PROFILES
#  Financial baselines for session initialisation.
#  All monetary values in USD.
#
#  carbon_intensity : float  — tCO₂e per $1M revenue (I1: UNIT ANNOTATION)
#    Used in tonnage formula: tonnes = CI × revenue_base / 1_000_000
#    Revenue-weighted group avg CI = Σ(CI×rev) / Σrev (as of I3 upgrade)
#
#  emissions_baseline : int  — LEGACY FIELD (I16)
#    Represents approximate absolute tCO₂e/year at initial scale.
#    NOT used in any engine calculation — superseded by the
#    revenue-intensity approach (CI × revenue / 1M).
#    Retained for reference calibration only; do not read in engine code.
# ═══════════════════════════════════════════════════════════════

BU_PROFILES = {
    # ── Default 4 ──────────────────────────────────────────────
    "pharma": {
        "label": "Muressons Pharma",
        "icon": "💊",
        "slot": "pharma",
        "revenue_base": 18_000_000,
        "opex_base": 12_000_000,
        "carbon_intensity": 35,
        "water_dependency": 82,
        "fx_exposure": 0.60,
        "emissions_baseline": 800,
        "natural_capital_debt": 120,
        "social_license_score": 50,
        "governance_risk_score": 15,
        "reputation_score": 55,
        "description": "Pharmaceutical manufacturing and distribution with high water dependency and regulatory scrutiny.",
    },
    "electronics": {
        "label": "Muressons Electronics",
        "icon": "⚡",
        "slot": "electronics",
        "revenue_base": 16_500_000,
        "opex_base": 11_500_000,
        "carbon_intensity": 72,
        "water_dependency": 58,
        "fx_exposure": 0.75,
        "emissions_baseline": 28_000,
        "natural_capital_debt": 200,
        "social_license_score": 50,
        "governance_risk_score": 20,
        "reputation_score": 55,
        "description": "Electronics manufacturing with complex global supply chains and high carbon intensity.",
    },
    "consumer_goods": {
        "label": "Muressons Consumer Goods",
        "icon": "🛒",
        "slot": "consumer_goods",
        "revenue_base": 10_500_000,
        "opex_base": 7_500_000,
        "carbon_intensity": 48,
        "water_dependency": 65,
        "fx_exposure": 0.40,
        "emissions_baseline": 22_000,
        "natural_capital_debt": 150,
        "social_license_score": 50,
        "governance_risk_score": 10,
        "reputation_score": 55,
        "description": "Consumer packaged goods with significant packaging waste and supply chain complexity.",
    },
    "software": {
        "label": "Muressons Software",
        "icon": "💻",
        "slot": "software",
        "revenue_base": 8_500_000,
        "opex_base": 5_500_000,
        "carbon_intensity": 12,
        "water_dependency": 12,
        "fx_exposure": 0.80,
        "emissions_baseline": 200,
        "natural_capital_debt": 30,
        "social_license_score": 50,
        "governance_risk_score": 25,
        "reputation_score": 55,
        "description": "Enterprise software and AI services with governance sensitivity and talent dependency.",
    },

    # ── Industry Verticals ────────────────────────────────────
    "oil_gas": {
        "label": "Muressons Oil & Gas",
        "icon": "🛢️",
        "slot": "pharma",  # Replaces pharma slot (heavy industry, physical assets)
        "revenue_base": 22_000_000,
        "opex_base": 15_000_000,
        "carbon_intensity": 95,
        "water_dependency": 70,
        "fx_exposure": 0.85,
        "emissions_baseline": 45_000,
        "natural_capital_debt": 350,
        "social_license_score": 40,
        "governance_risk_score": 20,
        "reputation_score": 45,
        "description": "Upstream exploration, midstream pipelines, and downstream refining with extreme carbon intensity and stranded asset risk.",
    },
    "banking_financial_services": {
        "label": "Muressons Banking & Financial Services",
        "icon": "🏦",
        "slot": "software",  # Replaces software slot (asset-light, governance-heavy)
        "revenue_base": 14_000_000,
        "opex_base": 8_000_000,
        "carbon_intensity": 8,
        "water_dependency": 5,
        "fx_exposure": 0.70,
        "emissions_baseline": 150,
        "natural_capital_debt": 15,
        "social_license_score": 50,
        "governance_risk_score": 30,
        "reputation_score": 55,
        "description": "Banking, insurance, and asset management with high financed emissions exposure, systemic risk, and governance complexity.",
    },
    "retail_fmcg": {
        "label": "Muressons Retail/FMCG",
        "icon": "🛍️",
        "slot": "consumer_goods",  # Replaces consumer_goods slot (supply chain, packaging)
        "revenue_base": 12_000_000,
        "opex_base": 9_000_000,
        "carbon_intensity": 42,
        "water_dependency": 55,
        "fx_exposure": 0.35,
        "emissions_baseline": 18_000,
        "natural_capital_debt": 160,
        "social_license_score": 50,
        "governance_risk_score": 12,
        "reputation_score": 55,
        "description": "Fast-moving consumer goods retail with high packaging waste, labour-intensive supply chains, and consumer-facing brand risk.",
    },
    "agriculture": {
        "label": "Muressons Agriculture",
        "icon": "🌾",
        "slot": "consumer_goods",  # Also fits consumer_goods slot (natural resources, supply chain)
        "revenue_base": 9_000_000,
        "opex_base": 6_500_000,
        "carbon_intensity": 55,
        "water_dependency": 90,
        "fx_exposure": 0.45,
        "emissions_baseline": 25_000,
        "natural_capital_debt": 280,
        "social_license_score": 45,
        "governance_risk_score": 15,
        "reputation_score": 50,
        "description": "Industrial agriculture and agri-tech with extreme water dependency, biodiversity impact, and land-use emissions.",
    },
    # ── Electronics-slot verticals ──────────────────────────────
    "semiconductor": {
        "label": "Muressons Semiconductor",
        "icon": "💎",
        "slot": "electronics",   # Capital-intensive precision manufacturing, complex supply chains
        "revenue_base": 20_000_000,
        "opex_base": 15_000_000,
        "carbon_intensity": 85,
        "water_dependency": 92,   # Ultra-pure water for wafer fab is among the highest of any industry
        "fx_exposure": 0.80,
        "emissions_baseline": 35_000,
        "natural_capital_debt": 220,
        "social_license_score": 48,
        "governance_risk_score": 22,
        "reputation_score": 52,
        "description": "Wafer fabrication and chip design with extreme water and energy intensity, rare-mineral supply risk, and geopolitical concentration.",
    },
    "medical_devices": {
        "label": "Muressons Medical Devices",
        "icon": "🩺",
        "slot": "electronics",   # Precision hardware manufacturing with regulatory burden similar to electronics
        "revenue_base": 18_500_000,
        "opex_base": 12_500_000,
        "carbon_intensity": 42,
        "water_dependency": 52,
        "fx_exposure": 0.65,
        "emissions_baseline": 9_000,
        "natural_capital_debt": 130,
        "social_license_score": 55,
        "governance_risk_score": 28,
        "reputation_score": 60,
        "description": "Implantables, diagnostics, and surgical equipment with heavy FDA/CE regulatory burden, IP-intensive R&D, and single-use plastics lifecycle exposure.",
    },
    "automotive": {
        "label": "Muressons Automotive",
        "icon": "🚗",
        "slot": "electronics",   # Heavy manufacturing, complex supply chain, EV transition risk
        "revenue_base": 26_000_000,
        "opex_base": 21_000_000,
        "carbon_intensity": 95,
        "water_dependency": 48,
        "fx_exposure": 0.70,
        "emissions_baseline": 55_000,
        "natural_capital_debt": 310,
        "social_license_score": 45,
        "governance_risk_score": 18,
        "reputation_score": 50,
        "description": "ICE and EV manufacturing with Scope 3 tailpipe dominance, battery mineral dependency, EV transition capex pressure, and labour-intensive assembly.",
    },
    "telecom": {
        "label": "Muressons Telecom",
        "icon": "📶",
        "slot": "electronics",   # Infrastructure-heavy, high governance/spectrum regulation
        "revenue_base": 19_000_000,
        "opex_base": 13_500_000,
        "carbon_intensity": 48,
        "water_dependency": 18,
        "fx_exposure": 0.55,
        "emissions_baseline": 12_000,
        "natural_capital_debt": 175,
        "social_license_score": 50,
        "governance_risk_score": 26,
        "reputation_score": 52,
        "description": "Mobile and fixed-line networks with spectrum licensing risk, e-waste obligations, tower energy intensity, and data privacy regulatory exposure.",
    },

    # ── Pharma-slot verticals ─────────────────────────────────────
    "chemical": {
        "label": "Muressons Chemical",
        "icon": "⚗️",
        "slot": "pharma",   # Process manufacturing, heavy regulatory, physical-asset intensive
        "revenue_base": 17_000_000,
        "opex_base": 12_500_000,
        "carbon_intensity": 115,  # Process heat, feedstock combustion, fugitive emissions
        "water_dependency": 76,
        "fx_exposure": 0.60,
        "emissions_baseline": 42_000,
        "natural_capital_debt": 300,
        "social_license_score": 42,
        "governance_risk_score": 22,
        "reputation_score": 46,
        "description": "Specialty and bulk chemicals with process-heat emissions, toxic discharge liability, REACH/TSCA compliance burden, and community health exposure.",
    },
    "cosmetics": {
        "label": "Muressons Cosmetics & Personal Care",
        "icon": "💄",
        "slot": "pharma",   # Ingredient regulation, testing compliance, similar to pharma licensing risk
        "revenue_base": 13_000_000,
        "opex_base": 8_500_000,
        "carbon_intensity": 28,
        "water_dependency": 62,
        "fx_exposure": 0.50,
        "emissions_baseline": 5_500,
        "natural_capital_debt": 145,
        "social_license_score": 50,
        "governance_risk_score": 20,
        "reputation_score": 55,
        "description": "Beauty and personal care with ingredient sourcing controversy, microplastics liability, animal-testing bans, and consumer-trust sensitivity.",
    },
    "food_beverage": {
        "label": "Muressons Food & Beverage",
        "icon": "🍽️",
        "slot": "pharma",   # Water/land intensive processing; shares regulatory burden and social license profile
        "revenue_base": 15_500_000,
        "opex_base": 11_000_000,
        "carbon_intensity": 58,
        "water_dependency": 88,
        "fx_exposure": 0.45,
        "emissions_baseline": 28_000,
        "natural_capital_debt": 270,
        "social_license_score": 48,
        "governance_risk_score": 14,
        "reputation_score": 52,
        "description": "Food processing and branded beverages with extreme water intensity, deforestation-linked sourcing, food-safety recalls, and packaging sustainability pressure.",
    },
    "power_utilities": {
        "label": "Muressons Power & Utilities",
        "icon": "⚡",
        "slot": "pharma",   # Capital-intensive physical infrastructure; regulatory profile mirrors pharma
        "revenue_base": 23_000_000,
        "opex_base": 16_000_000,
        "carbon_intensity": 155,  # Highest of all verticals; coal/gas generation baseline
        "water_dependency": 82,   # Thermal cooling
        "fx_exposure": 0.35,
        "emissions_baseline": 68_000,
        "natural_capital_debt": 380,
        "social_license_score": 40,
        "governance_risk_score": 25,
        "reputation_score": 44,
        "description": "Electricity generation, transmission, and distribution with the sector's highest carbon intensity, stranded-asset exposure from energy transition, and critical-infrastructure regulatory obligations.",
    },

    # ── Software-slot verticals ───────────────────────────────────
    "technology": {
        "label": "Muressons Technology",
        "icon": "🧠",
        "slot": "software",   # Replaces software slot (digital, talent-dependent)
        "revenue_base": 15_000_000,
        "opex_base": 9_000_000,
        "carbon_intensity": 15,
        "water_dependency": 10,
        "fx_exposure": 0.85,
        "emissions_baseline": 350,
        "natural_capital_debt": 40,
        "social_license_score": 50,
        "governance_risk_score": 28,
        "reputation_score": 55,
        "description": "Cloud infrastructure, AI/ML platforms, and data centres with governance sensitivity, energy growth trajectory, and talent brain-drain risk.",
    },
}

# ═══════════════════════════════════════════════════════════════
#  SLOT-FIT MAPPING
#  Each default BU slot can only be replaced by specific verticals
#  sharing industry characteristics.
# ═══════════════════════════════════════════════════════════════

SLOT_FIT_MAP = {
    # Heavy-industry / physical-asset / regulated manufacturing
    "pharma":         ["oil_gas", "chemical", "cosmetics", "food_beverage", "power_utilities"],
    # Precision hardware / capital-intensive manufacturing / complex supply chains
    "electronics":    ["semiconductor", "medical_devices", "automotive", "telecom"],
    # Consumer supply chain / natural resources / packaging
    "consumer_goods": ["retail_fmcg", "agriculture"],
    # Asset-light / governance-heavy / digital / talent-driven
    "software":       ["banking_financial_services", "technology"],
}

# Reverse lookup: vertical_id → list of compatible slots
VERTICAL_SLOT_COMPATIBILITY = {}
for _slot, _verticals in SLOT_FIT_MAP.items():
    for _v in _verticals:
        VERTICAL_SLOT_COMPATIBILITY.setdefault(_v, []).append(_slot)


# ═══════════════════════════════════════════════════════════════
#  DEFAULT BU COMPOSITION (the standard 4-slot lineup)
# ═══════════════════════════════════════════════════════════════

DEFAULT_SLOTS = ["pharma", "electronics", "consumer_goods", "software"]


# ═══════════════════════════════════════════════════════════════
#  MARKET OVERLAP MATRIX (extends engine._MARKET_OVERLAP)
#  0.0 = no overlap, 1.0 = full overlap
# ═══════════════════════════════════════════════════════════════

VERTICAL_MARKET_OVERLAP = {
    # Oil & Gas overlaps
    ("oil_gas", "agriculture"): 0.30,      # Energy inputs, fertiliser feedstock
    ("oil_gas", "electronics"): 0.20,      # Petrochemicals for plastics
    ("oil_gas", "consumer_goods"): 0.15,   # Packaging feedstock
    ("oil_gas", "retail_fmcg"): 0.15,      # Fuel logistics

    # Banking & Financial Services overlaps
    ("banking_financial_services", "technology"): 0.55,    # Fintech convergence
    ("banking_financial_services", "software"): 0.50,      # Enterprise SaaS overlap
    ("banking_financial_services", "pharma"): 0.10,        # Insurance / clinical trial financing

    # Retail/FMCG overlaps
    ("retail_fmcg", "agriculture"): 0.50,   # Food supply chain vertical integration
    ("retail_fmcg", "consumer_goods"): 0.70,  # Direct substitution
    ("retail_fmcg", "electronics"): 0.20,   # Smart retail / IoT

    # Agriculture overlaps
    ("agriculture", "pharma"): 0.25,        # Biotech / nutraceuticals
    ("agriculture", "consumer_goods"): 0.45, # Food & beverage inputs

    # Technology overlaps
    ("technology", "software"): 0.75,       # Direct substitution
    ("technology", "electronics"): 0.40,    # Hardware / semiconductor
    ("technology", "banking_financial_services"): 0.55,  # Fintech
}


# ═══════════════════════════════════════════════════════════════
#  BLINDSPOT FLAG MAPPING
#  Each vertical has its own "blindspot" flag equivalent to
#  electronics_blindspot in the default narrative.
# ═══════════════════════════════════════════════════════════════

VERTICAL_BLINDSPOT_FLAGS = {
    "pharma":                       "electronics_blindspot",
    "electronics":                  "electronics_blindspot",
    "consumer_goods":               "electronics_blindspot",
    "software":                     "electronics_blindspot",
    "oil_gas":                      "refinery_blindspot",
    "banking_financial_services":   "governance_blindspot",
    "retail_fmcg":                  "supply_chain_blindspot",
    "agriculture":                  "land_use_blindspot",
    "technology":                   "data_centre_blindspot",
    # New electronics-slot verticals
    "semiconductor":                "supply_chain_blindspot",  # Rare mineral / fab concentration
    "medical_devices":              "governance_blindspot",    # Regulatory / clinical compliance
    "automotive":                   "refinery_blindspot",      # Scope 3 tailpipe dominance
    "telecom":                      "data_centre_blindspot",   # Network energy / e-waste
    # New pharma-slot verticals
    "chemical":                     "refinery_blindspot",      # Process heat / toxic discharge
    "cosmetics":                    "supply_chain_blindspot",  # Ingredient sourcing
    "food_beverage":                "land_use_blindspot",      # Agricultural sourcing / water
    "power_utilities":              "refinery_blindspot",      # Carbon-intensive generation
}


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_profile(bu_id: str) -> dict[str, Any] | None:
    """Return the full profile for a BU ID, or None if not found."""
    return BU_PROFILES.get(bu_id)


def get_active_bus(substitutions: dict[str, str] | None = None) -> list[str]:
    """
    Return the list of 4 active BU IDs, with substitutions applied.
    substitutions: {"pharma": "oil_gas", "software": "technology"}
    """
    subs = substitutions or {}
    return [subs.get(slot, slot) for slot in DEFAULT_SLOTS]


def validate_substitution(slot: str, vertical_id: str) -> tuple[bool, str]:
    """
    Validate that a vertical can be placed in a given slot.
    Returns (is_valid, error_message).
    """
    if slot not in DEFAULT_SLOTS:
        return False, f"Invalid slot: {slot}. Valid slots: {DEFAULT_SLOTS}"
    if vertical_id == slot:
        return True, ""  # Resetting to default is always valid
    allowed = SLOT_FIT_MAP.get(slot, [])
    if vertical_id not in allowed:
        return False, (
            f"Vertical '{vertical_id}' is not compatible with slot '{slot}'. "
            f"Compatible verticals: {allowed}"
        )
    if vertical_id not in BU_PROFILES:
        return False, f"Unknown vertical: '{vertical_id}'"
    return True, ""


def build_bu_states(substitutions: dict[str, str] | None = None) -> list[dict]:
    """
    Build the initial bu_states array for session creation,
    applying any BU substitutions.
    """
    active_ids = get_active_bus(substitutions)
    bu_states = []
    for bu_id in active_ids:
        profile = BU_PROFILES.get(bu_id)
        if not profile:
            continue
        bu_states.append({
            "bu_id": bu_id,
            "bu_label": profile["label"],
            "bu_icon": profile.get("icon", "🏢"),
            "revenue_base": profile["revenue_base"],
            "opex_base": profile["opex_base"],
            "carbon_intensity": profile["carbon_intensity"],
            "water_dependency": profile["water_dependency"],
            "natural_capital_debt": profile.get("natural_capital_debt", 100),
            "social_license_score": profile.get("social_license_score", 50),
            "governance_risk_score": profile.get("governance_risk_score", 15),
            "reputation_score": profile.get("reputation_score", 55),
            "staff_burnout_index": 10.0,
            "vrio_advantage": 0.80,
            "consecutive_zero_investment_rounds": 0,
            "risk_factors": {
                "top_investment_streak": 0,
                "crisis_count_lifetime": 0,
            },
        })
    return bu_states


def canonical_bu_order(substitutions: dict[str, str] | None = None) -> list[str]:
    """The authoritative left-to-right BU order for a composition.

    Identical to get_active_bus(); named separately because the two callers
    mean different things by it. get_active_bus() answers "which BUs are in
    play". This answers "in what ORDER does anything that indexes a BU list
    have to see them" — a contract, not a lookup.
    """
    return get_active_bus(substitutions)


def sort_bu_states_canonically(bu_states: list[dict], global_state: dict | None = None) -> list[dict]:
    """Return bu_states in canonical slot order, whatever order storage gave us.

    4.1 (2026-08-03). THE DEFECT THIS CLOSES
        The two storage backends handed the engine the same four business units
        in DIFFERENT ORDERS, and the engine indexes into that list positionally:

            database_memory  ->  pharma, electronics, consumer_goods, software
            database (PG)    ->  consumer_goods, electronics, pharma, software

        Postgres sorts `ORDER BY bu_id`, which is alphabetical; the memory store
        returns creation order, which is slot order. engine.py's micro-strike
        does `micro_strike_bu_idx % len(new_bus)`, so a draw of 0 struck pharma
        in every test ever run and consumer_goods in production. Two of the four
        possible draws targeted a different company in the deployment than in
        the suite that was supposedly validating it.

    WHY SLOT ORDER AND NOT ALPHABETICAL
        Alphabetical is an accident of the ORDER BY clause. Slot order is what
        build_bu_states() creates, what the UI renders, what the Excel importer
        writes and what the god-mode sliders address. It is also the ONLY order
        that survives substitution: a cohort running oil & gas has bu_id
        "oil_gas" occupying the "pharma" slot, so the slot is recoverable from
        POSITION alone. Sorting by bu_id destroys it.

    WHY NO SCHEMA CHANGE
        The substitution map already rides in global_state["bu_substitutions"],
        persisted per round alongside these very rows, so the canonical order is
        reconstructible from data already on disk. Existing cohorts get correct
        ordering on the next read with no migration and no backfill of rows that
        sit behind an immutability trigger.

    Unknown ids (a vertical no longer in the map) sort last, by bu_id, so the
    result is total and stable rather than dependent on Python's sort being
    stable over an undefined key.
    """
    order = canonical_bu_order((global_state or {}).get("bu_substitutions") or {})
    position = {bu_id: i for i, bu_id in enumerate(order)}
    unknown = len(position)
    return sorted(bu_states, key=lambda b: (position.get(b.get("bu_id"), unknown), str(b.get("bu_id") or "")))
