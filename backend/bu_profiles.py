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
    "technology": {
        "label": "Muressons Technology",
        "icon": "🧠",
        "slot": "software",  # Replaces software slot (digital, talent-dependent)
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
    "pharma":         ["oil_gas"],                      # Heavy industry, physical assets, regulatory
    "electronics":    ["oil_gas"],                      # High carbon, complex supply chain
    "consumer_goods": ["retail_fmcg", "agriculture"],   # Supply chain, natural resources, packaging
    "software":       ["banking_financial_services", "technology"],  # Asset-light, governance-heavy, talent
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
    "pharma": "electronics_blindspot",             # Default uses electronics
    "electronics": "electronics_blindspot",        # Default
    "consumer_goods": "electronics_blindspot",     # Default
    "software": "electronics_blindspot",           # Default
    "oil_gas": "refinery_blindspot",
    "banking_financial_services": "governance_blindspot",
    "retail_fmcg": "supply_chain_blindspot",
    "agriculture": "land_use_blindspot",
    "technology": "data_centre_blindspot",
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
