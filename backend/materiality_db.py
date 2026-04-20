"""
Muressons Global Command — Admin Materiality Configurator
Manages the dynamic Double Materiality configuration reading/writing to JSON.
Supports both a global (Narrative Crisis) dictionary and 4 BU-specific
(Strategic Pillars) dictionaries.
"""

import json
import os
from pathlib import Path

# We store the config in the backend directory
CONFIG_DIR = Path(__file__).resolve().parent / "db"
CONFIG_FILE = CONFIG_DIR / "materiality_config.json"
BU_REGISTRY_FILE = CONFIG_DIR / "bu_registry.json"

# ── Dynamic BU registry ──────────────────────────────────────────
# These are the default BU IDs; god-mode can add more via the registry.
_DEFAULT_BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

_DEFAULT_BU_META = [
    {"id": "pharma", "label": "Pharma", "icon": "\U0001f48a"},
    {"id": "electronics", "label": "Electronics", "icon": "\u26a1"},
    {"id": "consumer_goods", "label": "Consumer Goods", "icon": "\U0001f6d2"},
    {"id": "software", "label": "Software", "icon": "\U0001f4bb"},
]

def _load_bu_registry() -> list[dict]:
    """Load the BU registry from disk. Falls back to defaults if not found."""
    try:
        if BU_REGISTRY_FILE.exists():
            with open(BU_REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return [dict(m) for m in _DEFAULT_BU_META]

def _save_bu_registry(registry: list[dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BU_REGISTRY_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    os.replace(tmp, BU_REGISTRY_FILE)

# In-memory registry cache
_bu_registry: list[dict] = _load_bu_registry()

def get_bu_registry() -> list[dict]:
    """Returns the full BU registry list."""
    return list(_bu_registry)

def get_bu_ids() -> list[str]:
    """Returns just the BU ID strings."""
    return [b["id"] for b in _bu_registry]

def register_bu(bu_id: str, label: str, icon: str = "\U0001f3e2") -> dict:
    """Register a new custom BU. Idempotent (updates if key already exists)."""
    global _bu_registry, _cached_bu_configs, BU_CONFIG_FILES
    # Normalise: lowercase slug
    bu_id = bu_id.strip().lower().replace(" ", "_")
    existing = next((b for b in _bu_registry if b["id"] == bu_id), None)
    entry = {"id": bu_id, "label": label.strip(), "icon": icon, "is_custom": True}
    if existing:
        idx = _bu_registry.index(existing)
        _bu_registry[idx] = entry
    else:
        _bu_registry.append(entry)
    BU_CONFIG_FILES[bu_id] = CONFIG_DIR / f"materiality_config_{bu_id}.json"
    if bu_id not in _cached_bu_configs:
        _cached_bu_configs[bu_id] = None
    _save_bu_registry(_bu_registry)
    return entry

def unregister_bu(bu_id: str) -> bool:
    """Remove a custom BU from the registry. Cannot remove the 4 defaults."""
    global _bu_registry
    if bu_id in _DEFAULT_BU_IDS:
        raise ValueError(f"Cannot remove default BU '{bu_id}'.")
    before = len(_bu_registry)
    _bu_registry = [b for b in _bu_registry if b["id"] != bu_id]
    if len(_bu_registry) == before:
        return False
    _save_bu_registry(_bu_registry)
    return True

# Legacy alias used in older code
BU_IDS = get_bu_ids()
# BU-specific config files (built dynamically from registry)
BU_CONFIG_FILES = {
    b["id"]: CONFIG_DIR / f"materiality_config_{b['id']}.json"
    for b in _bu_registry
}

# ═══════════════════════════════════════════════════════════════
# GLOBAL (Narrative Crisis / legacy_abc) DEFAULT CONFIG
# ═══════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "consultant_fee_usd": 1500000,
    "issues": [
        {
            "id": "data_privacy_impact",
            "title": "Data Privacy Impact",
            "hover_description": "Data breaches; severe GDPR fines & churn",
            "category": "social",
            "financial_impact": "high",
            "societal_impact": "high",
            "mitigation_cost_usd": 2500000
        },
        {
            "id": "energy_financial_risk",
            "title": "Energy Financial Risk",
            "hover_description": "Massive data-center energy draw",
            "category": "ecological",
            "financial_impact": "high",
            "societal_impact": "medium",
            "mitigation_cost_usd": 4000000
        },
        {
            "id": "api_leakage_impact",
            "title": "API Leakage Impact",
            "hover_description": "Active Pharmaceutical Ingredients in local water",
            "category": "ecological",
            "financial_impact": "high",
            "societal_impact": "high",
            "mitigation_cost_usd": 1800000
        },
        {
            "id": "drug_safety_financial_risk",
            "title": "Drug Safety Financial Risk",
            "hover_description": "Massive liabilities and health crises",
            "category": "social",
            "financial_impact": "high",
            "societal_impact": "high",
            "mitigation_cost_usd": 7500000
        },
        {
            "id": "e_waste_impact",
            "title": "E-Waste Impact",
            "hover_description": "Toxic runoff & future EU bans",
            "category": "ecological",
            "financial_impact": "high",
            "societal_impact": "high",
            "mitigation_cost_usd": 1200000
        },
        {
            "id": "supply_chain_labor_risk",
            "title": "Supply Chain Labor Risk",
            "hover_description": "Boycotts from severe human rights abuses",
            "category": "social",
            "financial_impact": "medium",
            "societal_impact": "high",
            "mitigation_cost_usd": 900000
        },
        {
            "id": "plastic_waste_impact",
            "title": "Plastic Waste Impact",
            "hover_description": "15% EPR tax & ocean microplastics",
            "category": "ecological",
            "financial_impact": "high",
            "societal_impact": "high",
            "mitigation_cost_usd": 3200000
        },
        {
            "id": "biodiversity_financial_risk",
            "title": "Biodiversity Financial Risk",
            "hover_description": "Deforestation and palm-oil dependency",
            "category": "ecological",
            "financial_impact": "medium",
            "societal_impact": "high",
            "mitigation_cost_usd": 500000
        }
    ],
    "interdependencies": []
}


# ═══════════════════════════════════════════════════════════════
# BU-SPECIFIC (Strategic Pillars / multi_toggles) DEFAULT CONFIGS
# ═══════════════════════════════════════════════════════════════

BU_DEFAULT_CONFIGS = {
    "pharma": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "api_leakage", "title": "API Leakage into Water Table", "hover_description": "Active Pharmaceutical Ingredients contaminating groundwater near Deccan Plateau facilities", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 1800000},
            {"id": "drug_safety", "title": "Drug Safety & Pharmacovigilance", "hover_description": "Post-market adverse events and potential product liability lawsuits", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 7500000},
            {"id": "clinical_trial_ethics", "title": "Clinical Trial Ethics", "hover_description": "Informed consent gaps in emerging market trial sites", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3000000},
            {"id": "water_scarcity_pharma", "title": "Water Scarcity for Manufacturing", "hover_description": "High water dependency for pharma ops; Deccan aquifer depletion", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2500000},
            {"id": "generic_access", "title": "Generic Drug Access Barriers", "hover_description": "Patent evergreening blocking affordable medicine access", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1200000},
            {"id": "cold_chain_carbon", "title": "Cold Chain Carbon Footprint", "hover_description": "Refrigerated logistics responsible for 12% of pharma Scope 3", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 800000},
            {"id": "pharma_paper_recycling", "title": "Office Paper Recycling at Labs", "hover_description": "Minor environmental gesture with negligible impact", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 50000},
            {"id": "pharma_earth_day", "title": "Pharma Earth Day Campaign", "hover_description": "Annual PR event with no material ESG impact", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 25000},
        ],
        "interdependencies": []
    },
    "electronics": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "e_waste_runoff", "title": "E-Waste & Toxic Mineral Runoff", "hover_description": "Future EU bans; massive ecological damage from rare earth mining", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 1200000},
            {"id": "conflict_minerals", "title": "Conflict Mineral Sourcing", "hover_description": "Cobalt and tantalum from DRC; forced labour exposure", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000},
            {"id": "semiconductor_volatility", "title": "Semiconductor Price Volatility", "hover_description": "Geopolitical risk from Taiwan/China dependency; supply shocks", "category": "economic", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 2000000},
            {"id": "planned_obsolescence", "title": "Planned Obsolescence", "hover_description": "EU Right-to-Repair regulation non-compliance risk", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3500000},
            {"id": "factory_conditions", "title": "Factory Working Conditions", "hover_description": "Tier-2 supplier labour violations; Foxconn-style scandals", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1500000},
            {"id": "data_center_energy", "title": "Data Center Energy Consumption", "hover_description": "Cloud infrastructure draws massive renewable energy", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 900000},
            {"id": "elec_led_swap", "title": "LED Bulb Swaps in Offices", "hover_description": "Negligible impact office upgrade", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 30000},
            {"id": "elec_ergonomic", "title": "Ergonomic Chairs for Engineers", "hover_description": "Employee comfort; no material ESG relevance", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 40000},
        ],
        "interdependencies": []
    },
    "consumer_goods": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "plastic_packaging", "title": "End-of-Life Plastic Packaging", "hover_description": "15% EPR tax imminent; ocean microplastics crisis", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3200000},
            {"id": "palm_oil_deforestation", "title": "Palm Oil & Deforestation", "hover_description": "Biodiversity collapse; NDPE policy violations", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2800000},
            {"id": "tier3_labor", "title": "Tier-3 Supply Chain Labour", "hover_description": "Child labour and forced labour risks in raw material sourcing", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 1500000},
            {"id": "consumer_health", "title": "Consumer Health & Product Safety", "hover_description": "Chemical safety concerns in personal care products", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2000000},
            {"id": "food_waste", "title": "Food Waste in Supply Chain", "hover_description": "30% spoilage rate in perishable goods distribution", "category": "ecological", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1000000},
            {"id": "water_usage_cg", "title": "Water Usage in Manufacturing", "hover_description": "High water intensity in FMCG production processes", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 700000},
            {"id": "cg_volunteering", "title": "Generic Employee Volunteering", "hover_description": "CSR activity with no measurable ESG outcome", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 35000},
            {"id": "cg_straws", "title": "Replacing Plastic Straws in Cafeteria", "hover_description": "Symbolic gesture; negligible environmental impact", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 15000},
        ],
        "interdependencies": []
    },
    "software": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "ai_bias", "title": "AI Algorithmic Bias & Redlining", "hover_description": "Massive fines; systemic inequality from biased hiring/lending algorithms", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000},
            {"id": "data_privacy", "title": "Data Privacy & Surveillance", "hover_description": "GDPR mega-fines; user trust erosion from data harvesting", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2500000},
            {"id": "cloud_energy", "title": "Cloud Infrastructure Energy Draw", "hover_description": "Massive data center carbon footprint; Scope 2 emissions", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000},
            {"id": "digital_divide", "title": "Digital Divide & Accessibility", "hover_description": "Product inaccessibility for disabled and low-income users", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1200000},
            {"id": "open_source_risk", "title": "Open-Source IP Licensing Risk", "hover_description": "GPL violations and liability from dependency audits", "category": "economic", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 800000},
            {"id": "talent_retention", "title": "Tech Talent Retention", "hover_description": "Developer burnout and attrition driving OpEx inflation", "category": "social", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 600000},
            {"id": "sw_exec_travel", "title": "Executive Travel Carbon Offsets", "hover_description": "Minor offset purchases; no structural change", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 20000},
            {"id": "sw_social_media", "title": "Annual Social Media ESG Campaign", "hover_description": "Marketing activity with no material impact", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 10000},
        ],
        "interdependencies": []
    },
}


# ═══════════════════════════════════════════════════════════════
# GLOBAL CONFIG FUNCTIONS (unchanged API)
# ═══════════════════════════════════════════════════════════════

def load_config() -> dict:
    """Reads the JSON config. Creates default if it doesn't exist."""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Fallback in case of corruption
        return DEFAULT_CONFIG

def save_config(config_dict: dict) -> None:
    """Writes the JSON config atomically."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = CONFIG_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    os.replace(temp_file, CONFIG_FILE)

# In-memory cache to avoid disk reads on every tick
_cached_config = None

def get_current_config() -> dict:
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config

def update_current_config(new_config: dict) -> None:
    global _cached_config
    _cached_config = new_config
    save_config(new_config)


# ═══════════════════════════════════════════════════════════════
# BU-SPECIFIC CONFIG FUNCTIONS
# ═══════════════════════════════════════════════════════════════

_cached_bu_configs: dict[str, dict | None] = {b["id"]: None for b in _bu_registry}

def load_bu_config(bu_id: str) -> dict:
    """Reads the BU-specific JSON config. Creates default if it doesn't exist."""
    current_ids = get_bu_ids()
    if bu_id not in current_ids:
        raise ValueError(f"Unknown BU: {bu_id}. Valid: {current_ids}")

    # Ensure file mapping exists for dynamically added BUs
    if bu_id not in BU_CONFIG_FILES:
        BU_CONFIG_FILES[bu_id] = CONFIG_DIR / f"materiality_config_{bu_id}.json"

    filepath = BU_CONFIG_FILES[bu_id]
    if not filepath.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        default = BU_DEFAULT_CONFIGS.get(bu_id, {"consultant_fee_usd": 1500000, "issues": [], "interdependencies": []})
        save_bu_config(bu_id, default)
        return default

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return BU_DEFAULT_CONFIGS.get(bu_id, {"consultant_fee_usd": 1500000, "issues": [], "interdependencies": []})

def save_bu_config(bu_id: str, config_dict: dict) -> None:
    """Writes BU-specific JSON config atomically."""
    current_ids = get_bu_ids()
    if bu_id not in current_ids:
        raise ValueError(f"Unknown BU: {bu_id}. Valid: {current_ids}")
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = BU_CONFIG_FILES[bu_id]
    temp_file = filepath.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    os.replace(temp_file, filepath)

def get_bu_config(bu_id: str) -> dict:
    global _cached_bu_configs
    if _cached_bu_configs.get(bu_id) is None:
        _cached_bu_configs[bu_id] = load_bu_config(bu_id)
    return _cached_bu_configs[bu_id]

def update_bu_config(bu_id: str, new_config: dict) -> None:
    global _cached_bu_configs
    _cached_bu_configs[bu_id] = new_config
    save_bu_config(bu_id, new_config)
# Force reload
