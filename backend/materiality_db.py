"""
Muressons Global Corporation — Admin Materiality Configurator
Manages the dynamic Double Materiality configuration reading/writing to JSON.
Supports both a global (Narrative Crisis) dictionary and 4 BU-specific
(Strategic Pillars) dictionaries.
"""

import json
import os
from pathlib import Path

# DURABILITY-2026-07-30: this was backend/db — a SECOND in-image location,
# separate from <repo>/db. On Railway the container filesystem is ephemeral, so
# every edit an admin made to a materiality matrix was lost on the next deploy.
# It failed in two different ways depending on the file:
#
#   * materiality_config.json and materiality_config_<bu>.json SHIP in git (31
#     files), so an edit did not vanish — it silently REVERTED to the shipped
#     version. Nastier than deletion: it saves, it reads back correctly, and
#     days later a deploy quietly restores the original with nothing logged.
#     Reproduced: edit "ADMIN EDITED THIS" -> reads back -> gone after redeploy.
#   * bu_registry.json is NOT tracked, so a newly registered BU disappeared
#     outright.
#
# Now resolved onto the mounted volume, migrating the existing files across
# once. `legacy` is passed explicitly because these never lived under
# <repo>/db, and without it the migration would find nothing and the volume
# would start empty — resetting every matrix to defaults, the very failure
# this fixes. With MURESSONS_DATA_DIR unset (local dev, CI) the path is
# byte-identical to before.
#
# Note the seeds alongside them — industry_configs/ and
# industry_master_materiality.xlsx — deliberately STAY in the image. They are
# read-only templates, referenced by no Python code, and belong with the build.
_SEED_DIR = Path(__file__).resolve().parent / "db"


def _resolve_config_dir() -> Path:
    """The volume when one is configured; otherwise backend/db, untouched.

    The no-volume branch is deliberate. An earlier cut migrated
    unconditionally, which on a developer machine created
    <repo>/db/materiality_configs and left the 31 git-TRACKED files in
    backend/db stale and ignored — a confusing split with untracked copies
    shadowing tracked ones. Off Railway there is nothing to fix: backend/db is
    as durable as the host disk. So migrate only where the bug actually exists.
    """
    import os
    if not os.getenv("MURESSONS_DATA_DIR", "").strip():
        return _SEED_DIR
    try:
        from runtime_paths import data_subdir
        return data_subdir("materiality_configs", legacy=_SEED_DIR)
    except Exception:
        return _SEED_DIR


CONFIG_DIR = _resolve_config_dir()
CONFIG_FILE = CONFIG_DIR / "materiality_config.json"
BU_REGISTRY_FILE = CONFIG_DIR / "bu_registry.json"

# ── Dynamic BU registry ──────────────────────────────────────────
# All 9 default BU IDs — protected from deletion via unregister_bu().
# The 4 Muressons core BUs are also tagged is_industry_vertical=True so that
# the Materiality Matrix UI places them in the Industry Verticals row rather
# than the legacy tab strip.  The simulation engine (bu_profiles.py) is
# unaffected — DEFAULT_SLOTS / BU_PROFILES there remain the source of truth
# for active gameplay BUs.
_DEFAULT_BU_IDS = [
    "pharma", "electronics", "consumer_goods", "software",
    # ── Industry Vertical Blueprints ──────────────────────────────────────────
    "oil_gas", "banking_financial_services", "retail_fmcg",
    "agriculture", "technology",
]

_DEFAULT_BU_META = [
    # ── Muressons Core BUs — now classified as Industry Verticals in the UI ──
    # is_industry_vertical=True moves them from the BU tab strip into the
    # dedicated Industry Verticals row, enabling Apply Blueprint workflows.
    # The simulation engine uses bu_profiles.DEFAULT_SLOTS independently.
    {"id": "pharma",         "label": "Pharma",         "icon": "\U0001f48a", "is_industry_vertical": True},
    {"id": "electronics",    "label": "Electronics",    "icon": "\u26a1",     "is_industry_vertical": True},
    {"id": "consumer_goods", "label": "Consumer Goods", "icon": "\U0001f6d2", "is_industry_vertical": True},
    {"id": "software",       "label": "Software",       "icon": "\U0001f4bb", "is_industry_vertical": True},
    # ── Additional Industry Vertical Blueprints ───────────────────────────────
    # These power the god-mode "Industry Vertical" selector in the admin dashboard.
    # Each can be loaded into any session via the Materiality Override endpoint.
    {"id": "oil_gas",                    "label": "Oil & Gas",                   "icon": "\U0001f6e2", "is_industry_vertical": True},
    {"id": "banking_financial_services", "label": "Banking & Financial Services", "icon": "\U0001f3e6", "is_industry_vertical": True},
    {"id": "retail_fmcg",               "label": "Retail / FMCG",               "icon": "\U0001f6cd", "is_industry_vertical": True},
    {"id": "agriculture",               "label": "Agriculture",                 "icon": "\U0001f33e", "is_industry_vertical": True},
    {"id": "technology",                "label": "Technology",                  "icon": "\U0001f9e0", "is_industry_vertical": True},
]


def _load_bu_registry() -> list[dict]:
    """Load the BU registry from disk, merging any missing defaults and
    forward-migrating the ``is_industry_vertical`` flag where needed.

    Migration rules (applied on every startup):
    - Entries not yet in the file are appended from ``_DEFAULT_BU_META``.
    - Existing entries whose ``is_industry_vertical`` value differs from the
      canonical ``_DEFAULT_BU_META`` definition are updated in-place so that
      the flag is always authoritative from code (not a stale JSON value).
    - If any change is detected the file is atomically re-persisted.
    """
    registry = None
    try:
        if BU_REGISTRY_FILE.exists():
            with open(BU_REGISTRY_FILE, "r", encoding="utf-8") as f:
                registry = json.load(f)
    except Exception:
        pass

    if registry is None:
        return [dict(m) for m in _DEFAULT_BU_META]

    # Build a lookup of canonical flags keyed by BU id
    _canonical_flags: dict[str, bool] = {
        m["id"]: m.get("is_industry_vertical", False)
        for m in _DEFAULT_BU_META
    }

    changed = False

    # 1. Merge any missing defaults
    existing_ids = {b["id"] for b in registry}
    missing = [dict(m) for m in _DEFAULT_BU_META if m["id"] not in existing_ids]
    if missing:
        registry.extend(missing)
        changed = True

    # 2. Forward-migrate is_industry_vertical flag for existing entries
    for entry in registry:
        canonical_flag = _canonical_flags.get(entry["id"])
        if canonical_flag is not None:
            current_flag = entry.get("is_industry_vertical", False)
            if current_flag != canonical_flag:
                if canonical_flag:
                    entry["is_industry_vertical"] = True
                else:
                    entry.pop("is_industry_vertical", None)
                changed = True

    if changed:
        # Re-persist so future loads reflect the updated state
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            tmp = BU_REGISTRY_FILE.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2)
            os.replace(tmp, BU_REGISTRY_FILE)
        except Exception:
            pass  # Non-fatal — in-memory registry is already correct

    return registry

def _save_bu_registry(registry: list[dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BU_REGISTRY_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    os.replace(tmp, BU_REGISTRY_FILE)

# In-memory registry cache
_bu_registry = _load_bu_registry()

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
    """Remove a custom BU from the registry. Cannot remove any of the 9 default BUs
    (includes both the 4 Muressons core BUs and the 5 additional verticals)."""
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
        {"id": "data_privacy_impact", "title": "Data Privacy Impact",
         "hover_description": "Data breaches; GDPR fines up to 4% global revenue & customer churn",
         "category": "social", "financial_impact": "high", "societal_impact": "high",
         "mitigation_cost_usd": 2500000, "esrs_topic": "S4", "value_chain_scope": "own_ops",
         "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
        {"id": "energy_financial_risk", "title": "Energy Financial Risk",
         "hover_description": "Massive data-center energy draw; Scope 2 cost exposure at $250/tCO2",
         "category": "ecological", "financial_impact": "high", "societal_impact": "medium",
         "mitigation_cost_usd": 4000000, "esrs_topic": "E1", "value_chain_scope": "own_ops",
         "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
        {"id": "api_leakage_impact", "title": "API Leakage Impact",
         "hover_description": "Active Pharmaceutical Ingredients contaminating groundwater — irreversible ecological damage",
         "category": "ecological", "financial_impact": "high", "societal_impact": "high",
         "mitigation_cost_usd": 1800000, "esrs_topic": "E3", "value_chain_scope": "own_ops",
         "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
        {"id": "drug_safety_financial_risk", "title": "Drug Safety Financial Risk",
         "hover_description": "Post-market adverse events; massive liabilities and patient health crises",
         "category": "social", "financial_impact": "high", "societal_impact": "high",
         "mitigation_cost_usd": 7500000, "esrs_topic": "S4", "value_chain_scope": "own_ops",
         "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
        {"id": "e_waste_impact", "title": "E-Waste Impact",
         "hover_description": "Toxic runoff from rare earth mining & future EU Right-to-Repair/WEEE bans",
         "category": "ecological", "financial_impact": "high", "societal_impact": "high",
         "mitigation_cost_usd": 1200000, "esrs_topic": "E5", "value_chain_scope": "downstream",
         "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
        {"id": "supply_chain_labor_risk", "title": "Supply Chain Labor Risk",
         "hover_description": "Tier-3 forced labour & child labour; CSDDD civil liability + boycott risk",
         "category": "social", "financial_impact": "medium", "societal_impact": "high",
         "mitigation_cost_usd": 900000, "esrs_topic": "S2", "value_chain_scope": "upstream",
         "time_horizon": "medium", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": False,
         "disclosure_required": True},
        {"id": "plastic_waste_impact", "title": "Plastic Waste Impact",
         "hover_description": "15% EPR levy imminent; ocean microplastics and PPWR non-compliance",
         "category": "ecological", "financial_impact": "high", "societal_impact": "high",
         "mitigation_cost_usd": 3200000, "esrs_topic": "E5", "value_chain_scope": "downstream",
         "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
        {"id": "biodiversity_financial_risk", "title": "Biodiversity Financial Risk",
         "hover_description": "Deforestation and palm-oil dependency; EUDR non-compliance = market access ban. AMBIGUOUS: financial impact depends on EUDR enforcement timeline.",
         "category": "ecological", "financial_impact": "medium", "societal_impact": "high",
         "mitigation_cost_usd": 500000, "esrs_topic": "E4", "value_chain_scope": "upstream",
         "time_horizon": "long", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": True,
         "disclosure_required": True}
    ],
    "interdependencies": [
        {"source": "supply_chain_labor_risk", "target": "biodiversity_financial_risk",
         "severity": "medium", "description": "Same upstream sourcing regions concentrate both social and biodiversity risks"}
    ]
}


# ═══════════════════════════════════════════════════════════════
# BU-SPECIFIC (Strategic Pillars / multi_toggles) DEFAULT CONFIGS
# ═══════════════════════════════════════════════════════════════

BU_DEFAULT_CONFIGS = {
    "pharma": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "api_leakage", "title": "API Leakage into Water Table",
             "hover_description": "Active Pharmaceutical Ingredients contaminating groundwater near Deccan Plateau facilities — irreversible E3 harm",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 1800000, "esrs_topic": "E3", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "drug_safety", "title": "Drug Safety & Pharmacovigilance",
             "hover_description": "Post-market adverse events and product liability; FDA/EMA recall risk",
             "category": "social", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 7500000, "esrs_topic": "S4", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "clinical_trial_ethics", "title": "Clinical Trial Ethics",
             "hover_description": "Informed consent gaps in emerging market trial sites; ESRS S3 affected communities",
             "category": "social", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 3000000, "esrs_topic": "S3", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "water_scarcity_pharma", "title": "Water Scarcity for Manufacturing",
             "hover_description": "High water dependency; Deccan aquifer depletion creates operational continuity risk (ESRS E3)",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 2500000, "esrs_topic": "E3", "value_chain_scope": "own_ops",
             "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "generic_access", "title": "Generic Drug Access Barriers",
             "hover_description": "Patent evergreening blocking affordable medicine — AMBIGUOUS: High societal harm (S4) but financial impact depends on WIPO enforcement.",
             "category": "social", "financial_impact": "medium", "societal_impact": "high",
             "mitigation_cost_usd": 1200000, "esrs_topic": "S4", "value_chain_scope": "downstream",
             "time_horizon": "long", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "cold_chain_carbon", "title": "Cold Chain Carbon Footprint",
             "hover_description": "Refrigerated logistics = 12% of pharma Scope 3; SBTi target gap",
             "category": "ecological", "financial_impact": "medium", "societal_impact": "medium",
             "mitigation_cost_usd": 800000, "esrs_topic": "E1", "value_chain_scope": "upstream",
             "time_horizon": "medium", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "pharma_paper_recycling", "title": "Office Paper Recycling at Labs",
             "hover_description": "Minor environmental gesture with negligible impact — classic immaterial distractor",
             "category": "ecological", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 50000, "esrs_topic": "E5", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "pharma_earth_day", "title": "Pharma Earth Day Campaign",
             "hover_description": "Annual PR event — no material ESG impact; greenwashing risk if structural issues unresolved",
             "category": "social", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 25000, "esrs_topic": "G1", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "api_leakage", "target": "water_scarcity_pharma",
             "severity": "high", "description": "Contaminated aquifer compounds water scarcity — both E3 risks amplify each other"},
            {"source": "drug_safety", "target": "clinical_trial_ethics",
             "severity": "high", "description": "Weak trial ethics creates future pharmacovigilance gaps (S4 → S3 cascade)"}
        ]
    },
    "electronics": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "e_waste_runoff", "title": "E-Waste & Toxic Mineral Runoff",
             "hover_description": "Future EU WEEE/Right-to-Repair bans; rare earth mining causes irreversible E5 damage",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 1200000, "esrs_topic": "E5", "value_chain_scope": "downstream",
             "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "conflict_minerals", "title": "Conflict Mineral Sourcing",
             "hover_description": "Cobalt and tantalum from DRC; child labour and forced labour — CSDDD civil liability",
             "category": "social", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 4000000, "esrs_topic": "S2", "value_chain_scope": "upstream",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "semiconductor_volatility", "title": "Semiconductor Price Volatility",
             "hover_description": "Geopolitical risk from Taiwan/China dependency — AMBIGUOUS: pure financial risk (G1 SBM-3) or supply chain S2 issue?",
             "category": "governance", "financial_impact": "high", "societal_impact": "medium",
             "mitigation_cost_usd": 2000000, "esrs_topic": "G1", "value_chain_scope": "upstream",
             "time_horizon": "medium", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "planned_obsolescence", "title": "Planned Obsolescence",
             "hover_description": "EU Right-to-Repair regulation + WEEE — design for durability mandatory from 2025",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 3500000, "esrs_topic": "E5", "value_chain_scope": "downstream",
             "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "factory_conditions", "title": "Factory Working Conditions",
             "hover_description": "Tier-2 supplier labour violations; Foxconn-style scandals destroy SLO overnight",
             "category": "social", "financial_impact": "medium", "societal_impact": "high",
             "mitigation_cost_usd": 1500000, "esrs_topic": "S2", "value_chain_scope": "upstream",
             "time_horizon": "short", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "data_center_energy", "title": "Data Center Energy Consumption",
             "hover_description": "Cloud infrastructure Scope 2 — RE100 commitment gap; carbon tax exposure",
             "category": "ecological", "financial_impact": "medium", "societal_impact": "medium",
             "mitigation_cost_usd": 900000, "esrs_topic": "E1", "value_chain_scope": "own_ops",
             "time_horizon": "medium", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "elec_led_swap", "title": "LED Bulb Swaps in Offices",
             "hover_description": "Saves ~8 tCO2/yr — negligible at manufacturing scale; classic immaterial distractor",
             "category": "ecological", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 30000, "esrs_topic": "E1", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "elec_ergonomic", "title": "Ergonomic Chairs for Engineers",
             "hover_description": "Employee comfort — not ESRS-material at group level",
             "category": "social", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 40000, "esrs_topic": "S1", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "conflict_minerals", "target": "factory_conditions",
             "severity": "high", "description": "DRC cobalt sourcing and Tier-2 factory violations often occur in same supplier network (S2 cascade)"},
            {"source": "planned_obsolescence", "target": "e_waste_runoff",
             "severity": "high", "description": "Short product lifecycles directly amplify e-waste volumes and downstream E5 damage"}
        ]
    },
    "consumer_goods": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "plastic_packaging", "title": "End-of-Life Plastic Packaging",
             "hover_description": "15% EPR levy on non-recyclable packaging; ocean microplastics; PPWR non-compliance risk",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 3200000, "esrs_topic": "E5", "value_chain_scope": "downstream",
             "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "palm_oil_deforestation", "title": "Palm Oil & Deforestation",
             "hover_description": "EUDR enforcement Dec 2024; biodiversity collapse; NDPE policy violations (E4)",
             "category": "ecological", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 2800000, "esrs_topic": "E4", "value_chain_scope": "upstream",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "tier3_labor", "title": "Tier-3 Supply Chain Labour",
             "hover_description": "Child labour and forced labour risks in raw material sourcing — CSDDD civil liability + boycott risk",
             "category": "social", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 1500000, "esrs_topic": "S2", "value_chain_scope": "upstream",
             "time_horizon": "medium", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "consumer_health", "title": "Consumer Health & Product Safety",
             "hover_description": "SVHC chemical safety in personal care products; REACH violations; recall liability",
             "category": "social", "financial_impact": "high", "societal_impact": "high",
             "mitigation_cost_usd": 2000000, "esrs_topic": "S4", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "food_waste", "title": "Food Waste in Supply Chain",
             "hover_description": "30% spoilage in perishable distribution — AMBIGUOUS: E5 waste or S3 food security impact on communities?",
             "category": "ecological", "financial_impact": "medium", "societal_impact": "high",
             "mitigation_cost_usd": 1000000, "esrs_topic": "E5", "value_chain_scope": "upstream",
             "time_horizon": "medium", "severity_score": 3, "likelihood_score": 4, "is_ambiguous": True},
            {"id": "water_usage_cg", "title": "Water Usage in Manufacturing",
             "hover_description": "High water intensity in FMCG production; aquifer stress in sourcing regions",
             "category": "ecological", "financial_impact": "medium", "societal_impact": "medium",
             "mitigation_cost_usd": 700000, "esrs_topic": "E3", "value_chain_scope": "own_ops",
             "time_horizon": "medium", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "cg_volunteering", "title": "Generic Employee Volunteering",
             "hover_description": "CSR activity with no measurable ESG outcome — greenwashing risk if structural issues unresolved",
             "category": "social", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 35000, "esrs_topic": "S1", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "cg_straws", "title": "Replacing Plastic Straws in Cafeteria",
             "hover_description": "Symbolic gesture — diverts ~50kg plastic/yr; negligible at group scale",
             "category": "ecological", "financial_impact": "low", "societal_impact": "low",
             "mitigation_cost_usd": 15000, "esrs_topic": "E5", "value_chain_scope": "own_ops",
             "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "palm_oil_deforestation", "target": "tier3_labor",
             "severity": "high", "description": "Same upstream sourcing regions (W. Africa, SE Asia) concentrate both biodiversity (E4) and child labour (S2) risk"},
            {"source": "plastic_packaging", "target": "food_waste",
             "severity": "medium", "description": "Reducing packaging creates food spoilage risk — genuine trade-off between E5 streams"}
        ]
    },
    "software": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "ai_bias", "title": "AI Algorithmic Bias & Redlining", "hover_description": "Massive fines; systemic inequality from biased hiring/lending algorithms", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "data_privacy", "title": "Data Privacy & Surveillance", "hover_description": "GDPR mega-fines; user trust erosion from data harvesting", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2500000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "cloud_energy", "title": "Cloud Infrastructure Energy Draw", "hover_description": "Massive data center carbon footprint; Scope 2 emissions", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "digital_divide", "title": "Digital Divide & Accessibility", "hover_description": "Product inaccessibility for disabled and low-income users", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1200000, "esrs_topic": "S4", "value_chain_scope": "downstream", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "open_source_risk", "title": "Open-Source IP Licensing Risk", "hover_description": "GPL violations and liability from dependency audits", "category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 800000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "talent_retention", "title": "Tech Talent Retention", "hover_description": "Developer burnout and attrition driving OpEx inflation", "category": "social", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 600000, "esrs_topic": "S1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 3, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "sw_exec_travel", "title": "Executive Travel Carbon Offsets", "hover_description": "Minor offset purchases; no structural change", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 20000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "sw_social_media", "title": "Annual Social Media ESG Campaign", "hover_description": "Marketing activity with no material impact", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 10000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "ai_bias", "target": "data_privacy", "severity": "high", "description": "EU AI Act high-risk classification amplifies GDPR obligations"},
            {"source": "cloud_energy", "target": "ai_bias", "severity": "medium", "description": "AI compute energy creates both E1 and S4 exposure"}
        ]
    },
    "oil_gas": {
        "consultant_fee_usd": 1500000,
        "issues": [
            {"id": "methane_leakage", "title": "Methane Leakage (OGMP 2.0)", "hover_description": "Scope 1 fugitive emissions; OGMP 2.0 Level 5 reporting mandatory by 2025. 80x more potent than CO2 over 20yr. ESRS E1 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 8000000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "stranded_asset_risk", "title": "Stranded Asset Risk (Proven Reserves)", "hover_description": "AMBIGUOUS: For a company in denial this is Q3. For one that has read the IEA NZE 2050 report, unextracted reserves face write-down risk making this Q1. Where do you stand?", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "long", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": True},
            {"id": "just_transition_refinery", "title": "Just Transition for Refinery Workforce", "hover_description": "2,400 workers at 3 refineries face redundancy. ILO Just Transition Guidelines; ESRS S1 mandatory. Retraining cost vs. long-term SLO preservation.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 12000000, "esrs_topic": "S1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "water_contamination", "title": "Water Contamination from Fracking", "hover_description": "Groundwater incidents at 2 shale sites. Community litigation risk; EPA enforcement. Severity HIGH, irreversible. ESRS E3 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6000000, "esrs_topic": "E3", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "indigenous_land", "title": "Indigenous Land Rights Consultations", "hover_description": "FPIC (Free Prior Informed Consent) required under UNDRIP. Low financial impact if managed; catastrophic if ignored. ESRS S3 mandatory.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 2000000, "esrs_topic": "S3", "value_chain_scope": "upstream", "time_horizon": "short", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "lng_price_volatility", "title": "LNG Spot Price Volatility", "hover_description": "Q3 issue — pure financial risk from geopolitical supply disruption. No direct societal harm. ESRS 2 SBM-3.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1500000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "og_exec_offsets", "title": "Executive Carbon Offset Purchases", "hover_description": "Symbolic gesture. <0.01% of total Scope 1 emissions. Classic greenwashing distractor if material issues unresolved.", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 50000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "og_csr_scholarships", "title": "CSR Scholarship Programme", "hover_description": "Community goodwill. Financially and environmentally immaterial. Not ESRS-material at group level.", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 200000, "esrs_topic": "S3", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "stranded_asset_risk", "target": "methane_leakage", "severity": "high", "description": "IEA NZE pathway requires aggressive methane cuts alongside reserve write-downs"}
        ]
    },
    "banking_financial_services": {
        "consultant_fee_usd": 1200000,
        "issues": [
            {"id": "financed_emissions", "title": "Financed Emissions (Scope 3 Cat.15)", "hover_description": "Largest carbon footprint — upstream lending portfolio. PCAF standard mandates measurement. At $250/tCO2, material. ESRS E1 + SFDR mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000, "esrs_topic": "E1", "value_chain_scope": "upstream", "time_horizon": "medium", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "ai_credit_discrimination", "title": "AI Credit Scoring Discrimination", "hover_description": "Algorithmic lending bias against ethnic minorities. EU AI Act High-Risk classification. CRD VI governance exposure. Fines + class action risk.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 7000000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "climate_credit_risk", "title": "Climate Credit Risk (Physical + Transition)", "hover_description": "Mortgage book exposure to flood-prone assets. ECB climate stress test failure risk. Transition risk in fossil-heavy loan book. ESRS E1 + EBA guidelines.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": True},
            {"id": "sfdr_greenwashing_risk", "title": "SFDR Greenwashing in ESG Fund Labelling", "hover_description": "Q1 ISSUE: EU SFDR Article 8/9 fund mislabelling. Regulator scrutiny escalating — fund outflows + fines up to 10% AUM. High financial AND societal (investor deception) materiality. ESRS G1 mandatory.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3500000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "financial_inclusion", "title": "Financial Inclusion for Unbanked Communities", "hover_description": "17% of served regions lack access to basic accounts. High societal impact; low near-term financial return. ESRS S3 disclosure mandatory.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 2000000, "esrs_topic": "S3", "value_chain_scope": "downstream", "time_horizon": "long", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "cybersecurity_resilience", "title": "Cybersecurity & Operational Resilience", "hover_description": "DORA (Digital Operational Resilience Act) compliance mandatory by Jan 2025. High financial risk; societal impact moderate. ESRS G1.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 8000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "fs_charity_gala", "title": "Annual Charity Gala", "hover_description": "PR event. Financially and materially immaterial. Classic greenwashing distractor.", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 150000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "fs_ergonomic", "title": "Ergonomic Workstations", "hover_description": "Employee comfort. Not ESRS-material at group level.", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 80000, "esrs_topic": "S1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "climate_credit_risk", "target": "financed_emissions", "severity": "high", "description": "Loan book stranded asset exposure amplifies Scope 3 Cat.15 financed emissions"},
            {"source": "ai_credit_discrimination", "target": "sfdr_greenwashing_risk", "severity": "medium", "description": "AI governance failures undermine ESG fund credibility"}
        ]
    },
    "retail_fmcg": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "eudr_deforestation", "title": "Palm Oil & Deforestation (EUDR)", "hover_description": "EU Deforestation Regulation (EUDR) enforcement from Dec 2024. Palm oil, cocoa, soy supply chains must prove deforestation-free. Non-compliance = market access ban. ESRS E4 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4500000, "esrs_topic": "E4", "value_chain_scope": "upstream", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "epr_plastic", "title": "End-of-Life Plastic Packaging (EPR)", "hover_description": "15% EPR levy on non-recyclable packaging. 4,200 tonnes/yr exposure. Ocean microplastics reputational risk. ESRS E5 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3200000, "esrs_topic": "E5", "value_chain_scope": "downstream", "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "child_labour_cocoa", "title": "Child Labour in Cocoa/Cotton Supply Chains", "hover_description": "ILO estimates 1.56M children in cocoa farming. EU CSDDD civil liability. Boycott risk is existential. Severity: HIGH. ESRS S2 mandatory.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6000000, "esrs_topic": "S2", "value_chain_scope": "upstream", "time_horizon": "medium", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "product_safety_reach", "title": "Product Safety & Chemical Compliance (REACH)", "hover_description": "SVHC substances in personal care and household products. Recall risk + regulatory fines. ESRS E2 + consumer safety disclosure.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2800000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "living_wage_tier4", "title": "Living Wage for Tier-4 Agricultural Workers", "hover_description": "Gap between minimum and living wage affects 80,000+ workers in sourcing regions. High societal impact. ESRS S2 disclosure mandatory.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 3000000, "esrs_topic": "S2", "value_chain_scope": "upstream", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "consumer_spending_risk", "title": "Consumer Spending Power / Inflation", "hover_description": "Pure financial risk — macroeconomic demand compression. No direct ESG harm. ESRS 2 SBM-3 financial risk disclosure.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "retail_seasonal_csr", "title": "Seasonal CSR Campaigns", "hover_description": "Christmas food bank donations. Good PR; immaterial at group scale. Greenwashing risk if material issues unaddressed.", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 100000, "esrs_topic": "S1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "retail_composting", "title": "Office Composting Programme", "hover_description": "Diverts ~2 tonnes of food waste/yr from landfill. Immaterial at group scale. Not ESRS-material.", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 20000, "esrs_topic": "E5", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "eudr_deforestation", "target": "child_labour_cocoa", "severity": "high", "description": "Same W.Africa/SE Asia sourcing regions concentrate E4 deforestation and S2 child labour risk"},
            {"source": "epr_plastic", "target": "product_safety_reach", "severity": "medium", "description": "Packaging changes expose product formulation REACH compliance gaps"}
        ]
    },
    "agriculture": {
        "consultant_fee_usd": 1000000,
        "issues": [
            {"id": "tnfd_nature_disclosure", "title": "TNFD Nature-Related Financial Disclosure", "hover_description": "Agriculture IS the nature risk. TNFD (Taskforce on Nature-related Financial Disclosures) framework requires disclosure of dependencies on pollinators, soil health, and freshwater. Nature loss = production collapse. Q1 because financial AND societal impact are both existential. ESRS E4 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3000000, "esrs_topic": "E4", "value_chain_scope": "own_ops", "time_horizon": "long", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": False},
            {"id": "soil_degradation", "title": "Soil Degradation & Carbon Sequestration", "hover_description": "Topsoil lost at 10x regeneration rate. Each 1% drop in organic matter = 8% yield reduction. Regenerative agriculture investment protects long-term asset value. ESRS E4.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000, "esrs_topic": "E4", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "water_depletion", "title": "Water Depletion & Nitrate Runoff", "hover_description": "Aquifer over-extraction + nitrogen runoff causing algal blooms. EU Nitrates Directive violation risk. Water is both the biggest cost AND the biggest impact. ESRS E3 mandatory.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000, "esrs_topic": "E3", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "smallholder_livelihoods", "title": "Smallholder Farmer Livelihoods", "hover_description": "3,200 contract smallholders earning below living income. Cascading supply risk + ESRS S2 mandatory disclosure. Long-term sourcing security depends on farmer viability.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2500000, "esrs_topic": "S2", "value_chain_scope": "upstream", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "biodiversity_loss", "title": "Biodiversity Restoration Commitments", "hover_description": "30x30 target (CBD Kunming-Montreal). High societal impact — pollinator collapse threatens food security. Financial impact: medium (regulatory + market access). ESRS E4.", "category": "ecological", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 2000000, "esrs_topic": "E4", "value_chain_scope": "own_ops", "time_horizon": "long", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "pesticide_competitor", "title": "Competitor Crop Protection Technology", "hover_description": "New biopesticide entrants threatening market share. Pure financial risk. No direct ESG harm. ESRS 2 SBM-3.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 800000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 2, "likelihood_score": 2, "is_ambiguous": False},
            {"id": "ag_led_offices", "title": "LED Retrofits in Admin Buildings", "hover_description": "Saves 12 tCO2/yr. Negligible at farm scale. Classic immaterial distractor.", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 35000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "ag_exec_offsets", "title": "Executive Carbon Offset Purchases", "hover_description": "Symbolic. Farm Scope 1 emissions are orders of magnitude larger. Greenwashing risk.", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 40000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "tnfd_nature_disclosure", "target": "soil_degradation", "severity": "high", "description": "TNFD assessment reveals soil depletion as primary nature dependency"},
            {"source": "water_depletion", "target": "smallholder_livelihoods", "severity": "medium", "description": "Water scarcity hits smallholder farmers hardest — cascading S2 risk"}
        ]
    },
    "technology": {
        "consultant_fee_usd": 1200000,
        "issues": [
            {"id": "eu_ai_act_compliance", "title": "EU AI Act Compliance (High-Risk Systems)", "hover_description": "EU AI Act in force from Aug 2024, phased enforcement through 2026-2027. High-risk AI systems (recruitment, credit, biometrics) require conformity assessment, human oversight, and transparency documentation. Fines up to €30M or 3% global revenue. Both high financial AND high societal (fundamental rights) materiality. ESRS S1 + EU AI Act Art. 9.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6000000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "data_privacy_surveillance", "title": "Data Privacy & Surveillance Risk", "hover_description": "GDPR mega-fines (up to 4% global revenue). User data harvesting for ad targeting. EU Data Act 2025 creates additional portability obligations. ESRS S4 + G1 mandatory.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4500000, "esrs_topic": "S4", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "cloud_energy_scope2", "title": "Cloud Infrastructure Energy & Scope 2", "hover_description": "Data centres consume 1-2% of global electricity. Hyperscaler dependency creates Scope 2 exposure. RE100 commitments require 100% renewable matching. Carbon tax at $250/ton makes this financially material. ESRS E1.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 8000000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "digital_divide", "title": "Digital Divide & Accessibility Gap", "hover_description": "Product inaccessibility for 1.3B disabled users globally. EU Web Accessibility Directive + EAA (European Accessibility Act) enforcement. High societal; medium financial. ESRS S4.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 1500000, "esrs_topic": "S4", "value_chain_scope": "downstream", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 3, "is_ambiguous": True},
            {"id": "cybersecurity_resilience_tech", "title": "Cybersecurity & Operational Resilience", "hover_description": "NIS2 Directive mandatory from Oct 2024. Ransomware exposure. High financial risk (operational disruption + fines). Societal impact: moderate. ESRS G1.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 5000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False},
            {"id": "competitor_ai_platform", "title": "Competitor AI Platform Market Share", "hover_description": "Pure competitive/financial risk. No direct ESG harm. Rapid AI commoditisation. ESRS 2 SBM-3.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 2000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 2, "likelihood_score": 2, "is_ambiguous": False},
            {"id": "tech_social_media", "title": "Annual Social Media ESG Campaign", "hover_description": "Marketing spend. No material ESG outcome. Greenwashing risk if structural issues unresolved.", "category": "social", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 15000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
            {"id": "tech_exec_travel", "title": "Executive Travel Carbon Offsets", "hover_description": "Symbolic. Cloud energy is orders of magnitude larger. Greenwashing red flag.", "category": "ecological", "financial_impact": "low", "societal_impact": "low", "mitigation_cost_usd": 25000, "esrs_topic": "E1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 1, "likelihood_score": 1, "is_ambiguous": False},
        ],
        "interdependencies": [
            {"source": "eu_ai_act_compliance", "target": "data_privacy_surveillance", "severity": "high", "description": "AI Act high-risk classification amplifies GDPR data processing obligations"}
        ]
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

_cached_bu_configs = {b["id"]: None for b in _bu_registry}  # type: dict

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

def _regional_path(bu_id: str, region_id: str) -> Path:
    """Where a REGION-specific matrix for this BU lives."""
    return CONFIG_DIR / f"materiality_config_{bu_id}__{region_id}.json"


def get_regional_bu_config(bu_id: str, region_id: str) -> dict | None:
    """A BU's matrix for one market, or None to fall through.

    PHASE 2 (2026-07-31). Materiality had NO region dimension at all — a grep
    for "region" in this module returned only prose inside issue descriptions.
    But double materiality genuinely differs by market: CSRD in Europe and BRSR
    in India weight the same issue differently, which is much of the point of
    teaching it. Stakeholders already expressed this as
    vertical_<bu>__<region>; this is the same idea, same naming shape.

    Returns None — never {} or a default — when no regional file exists, so the
    caller falls through to the plain per-BU config exactly as before. A cohort
    that has never heard of regions is unaffected.
    """
    if not bu_id or not region_id:
        return None
    path = _regional_path(str(bu_id), str(region_id).strip().lower())
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        # A corrupt regional file must not take down a running class; the plain
        # BU matrix is a correct, complete fallback.
        return None
    return cfg if isinstance(cfg, dict) and cfg.get("issues") is not None else None


def save_regional_bu_config(bu_id: str, region_id: str, config_dict: dict) -> bool:
    """Persist a BU x region matrix. Atomic, like save_bu_config."""
    import re as _re
    rid = str(region_id or "").strip().lower()
    if not bu_id or not _re.match(r"^[a-z0-9_]{1,50}$", rid):
        return False
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _regional_path(str(bu_id), rid)
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
        os.replace(tmp, path)
    except OSError:
        return False
    return True


def resolve_bu_config(bu_id: str, region_id: str = "") -> dict:
    """The read the simulation should use: region-specific if present, else the
    BU's own matrix. One function so callers cannot forget the region step."""
    regional = get_regional_bu_config(bu_id, region_id)
    if regional is not None:
        return regional
    return get_bu_config(bu_id)


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
