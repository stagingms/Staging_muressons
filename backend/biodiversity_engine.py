"""
Muressons Global Corporation — Biodiversity Engine (SE-4)
Tracks ecosystem health, species risk, habitat integrity, and
ecosystem services as a dimension SEPARATE from Natural Capital Debt.

Theory base:
  - TNFD (Taskforce on Nature-related Financial Disclosures) LEAP approach
  - SBTN (Science Based Targets for Nature) freshwater/land categories
  - Dasgupta Review (2021): Nature as an asset with depreciating stock

Architecture:
  Pure-function module (no I/O). Consumes BU states + decisions,
  returns updated biodiversity state dict.

Metrics:
  1. Ecosystem Health Index (EHI) — 0–100 composite
  2. Species Risk Score — count of threatened species in operational footprint
  3. Habitat Integrity — % of operational land with intact ecosystems
  4. Ecosystem Services Value — $ value of nature's contributions to operations
  5. Biodiversity Dependency Score — how much the company depends on nature
"""

from __future__ import annotations
from typing import Any
import math
from flag_utils import collect_all_flags
from rules import rule_on


# ═══════════════════════════════════════════════════════════════
#  INITIAL STATE
# ═══════════════════════════════════════════════════════════════

def create_initial_biodiversity_state() -> dict[str, Any]:
    """Create the starting biodiversity state for a new session."""
    return {
        "ecosystem_health_index": 65.0,       # 0-100, starts moderate
        "species_risk_score": 12,              # count of threatened species in footprint
        "habitat_integrity": 0.55,             # 0-1, fraction of intact habitat
        "ecosystem_services_value": 8_000_000, # $/round from pollination, water filtration, etc.
        "biodiversity_dependency_score": 0.35,  # 0-1, how much BUs depend on nature
        "deforestation_rate": 2.5,             # hectares/year lost
        "water_stress_index": 0.40,            # 0-1, local watershed stress
        "pollinator_health": 0.60,             # 0-1, critical for pharma (natural compounds)
        "soil_carbon_stock": 45.0,             # tonnes CO2e/hectare
        "marine_impact_score": 30.0,           # 0-100, coastal/ocean impact
        "tnfd_disclosure_level": "none",        # none, partial, aligned, leadership
        "sbtn_targets_set": False,
        "nature_positive_pledge": False,
        "biodiversity_credits_purchased": 0,
        "restoration_projects_active": [],
        "cumulative_habitat_restored_ha": 0.0,
        "biodiversity_history": [],
    }


# ═══════════════════════════════════════════════════════════════
#  CORE CALCULATIONS
# ═══════════════════════════════════════════════════════════════

def calc_ecosystem_health_index(
    current_ehi: float,
    ncd_delta: float,
    carbon_intensity_avg: float,
    habitat_integrity: float,
    restoration_bonus: float = 0.0,
    deforestation_rate: float = 0.0,
) -> tuple[float, dict]:
    """
    Composite Ecosystem Health Index (0-100).

    EHI_new = EHI_old
              - (NCD_delta * 0.5)          # NCD increases degrade ecosystems
              - (deforestation * 2.0)       # land clearance
              + (habitat_integrity * 5.0)   # intact habitat supports health
              + restoration_bonus           # active restoration projects
              - (carbon_intensity * 0.1)    # climate stress on ecosystems

    Based on: Dasgupta Review (2021) — nature's stock depreciates
    without active maintenance.
    """
    ncd_impact = ncd_delta * 0.5  # Positive NCD delta = degradation
    # IMP-01 (audit 2026-09-04, WP-22): deforestation_rate has no writer (a
    # constant 2.5 → −5.0/round) and the −1.5 "entropy" drift charged every
    # team every round, so the greenest and the most extractive team drew the
    # same EHI curve (65 → 2.5 by R10) and paid the same "Nature's Invoice".
    # Neither is a consequence of a decision; both are gone. The index now
    # moves with the levers that exist: this round's NCD change, carbon
    # intensity above 50, habitat integrity, restoration and TNFD disclosure.
    deforest_impact = 0.0
    habitat_support = (habitat_integrity - 0.5) * 5.0  # Positive if > 50% intact
    climate_stress = max(0, (carbon_intensity_avg - 50)) * 0.1

    delta = (
        -ncd_impact
        - deforest_impact
        + habitat_support
        + restoration_bonus
        - climate_stress
    )

    # No unconditional drift (IMP-01)
    natural_drift = 0.0

    new_ehi = max(0.0, min(100.0, round(current_ehi + delta + natural_drift, 2)))

    diagnostics = {
        "previous_ehi": current_ehi,
        "new_ehi": new_ehi,
        "ncd_impact": round(-ncd_impact, 2),
        "deforestation_impact": round(-deforest_impact, 2),
        "habitat_support": round(habitat_support, 2),
        "restoration_bonus": round(restoration_bonus, 2),
        "climate_stress": round(-climate_stress, 2),
        "natural_drift": natural_drift,
        "total_delta": round(new_ehi - current_ehi, 2),
    }

    return new_ehi, diagnostics


def calc_species_risk(
    current_risk: int,
    ehi: float,
    habitat_integrity: float,
    supply_chain_audit_active: bool = False,
) -> tuple[int, dict]:
    """
    Species risk score — count of threatened species in operational footprint.

    Low EHI and low habitat integrity increase species risk.
    Supply chain audits can reveal previously hidden risks (paradoxical
    increase that's actually better governance).
    """
    # Base change from ecosystem health
    if ehi < 30:
        risk_delta = 3  # Critically degraded → species threatened
    elif ehi < 50:
        risk_delta = 1
    elif ehi > 75:
        risk_delta = -1  # Healthy ecosystems reduce risk
    else:
        risk_delta = 0

    # Habitat fragmentation effect
    if habitat_integrity < 0.30:
        risk_delta += 2  # Severe fragmentation

    # Audit reveals hidden risk (pedagogically important — transparency ≠ bad)
    audit_discovery = 0
    if supply_chain_audit_active and current_risk < 20:
        audit_discovery = 3
        risk_delta += audit_discovery

    new_risk = max(0, current_risk + risk_delta)

    diagnostics = {
        "previous_risk": current_risk,
        "new_risk": new_risk,
        "ehi_impact": risk_delta - audit_discovery,
        "audit_discovery": audit_discovery,
        "message": (
            f"Supply chain audit revealed {audit_discovery} previously untracked "
            f"threatened species in Tier-2 supplier footprints."
            if audit_discovery > 0
            else None
        ),
    }

    return new_risk, diagnostics


def calc_ecosystem_services_value(
    current_value: float,
    ehi: float,
    pollinator_health: float,
    water_stress_index: float,
    habitat_integrity: float,
) -> tuple[float, dict]:
    """
    Dollar value of ecosystem services the company receives for free
    (pollination, water filtration, soil fertility, flood protection, etc.).

    Based on Costanza et al. (2014) ecosystem services valuation.

    Value = Base × EHI_factor × Pollinator_factor × Water_factor
    where factors are 0.5–1.5 range multipliers.
    """
    ehi_factor = 0.5 + (ehi / 100.0)  # 0.5 at EHI=0, 1.5 at EHI=100
    pollinator_factor = 0.7 + (pollinator_health * 0.6)  # 0.7–1.3
    water_factor = 1.0 - (water_stress_index * 0.3)  # 0.7–1.0
    habitat_factor = 0.6 + (habitat_integrity * 0.8)  # 0.6–1.4

    composite = ehi_factor * pollinator_factor * water_factor * habitat_factor
    new_value = round(current_value * composite, 2)

    # Floor: even degraded ecosystems provide some services
    new_value = max(500_000, new_value)

    diagnostics = {
        "previous_value": current_value,
        "new_value": new_value,
        "ehi_factor": round(ehi_factor, 3),
        "pollinator_factor": round(pollinator_factor, 3),
        "water_factor": round(water_factor, 3),
        "habitat_factor": round(habitat_factor, 3),
        "composite_multiplier": round(composite, 3),
        "services_lost": round(max(0, current_value - new_value), 2),
    }

    return new_value, diagnostics


def calc_biodiversity_dependency(
    bus: list[dict],
) -> tuple[float, dict]:
    """
    How much the company depends on biodiversity for its operations.
    Higher dependency = more exposure to nature-related financial risks.

    Pharma depends on natural compounds (high).
    Software has low direct dependency.
    Consumer goods depend on agricultural inputs (medium-high).
    Electronics depend on mineral extraction (medium).
    """
    DEPENDENCY_BY_BU = {
        "pharma": 0.65,
        "electronics": 0.30,
        "consumer_goods": 0.55,
        "software": 0.10,
        # Healthcare
        "hospitals": 0.20,
        "clinics": 0.15,
        "specialised_care": 0.25,
        "telehealth": 0.05,
    }

    total_dep = 0.0
    for bu in bus:
        bu_dep = DEPENDENCY_BY_BU.get(bu.get("bu_id", ""), 0.25)
        total_dep += bu_dep

    avg_dep = round(total_dep / max(len(bus), 1), 3)

    diagnostics = {
        "average_dependency": avg_dep,
        "bu_dependencies": {
            bu["bu_id"]: DEPENDENCY_BY_BU.get(bu.get("bu_id", ""), 0.25)
            for bu in bus
        },
        "risk_level": (
            "critical" if avg_dep > 0.50
            else "high" if avg_dep > 0.35
            else "moderate" if avg_dep > 0.20
            else "low"
        ),
    }

    return avg_dep, diagnostics


# ═══════════════════════════════════════════════════════════════
#  TNFD DISCLOSURE LEVELS
# ═══════════════════════════════════════════════════════════════

TNFD_LEVELS = {
    "none": {
        "label": "No Disclosure",
        "ehi_modifier": 0.0,
        "reputation_modifier": -2.0,
        "mr_bonus": 0.0,
    },
    "partial": {
        "label": "Partial Disclosure (LEAP started)",
        "ehi_modifier": 1.0,
        "reputation_modifier": 0.0,
        "mr_bonus": 0.01,
    },
    "aligned": {
        "label": "TNFD-Aligned Disclosure",
        "ehi_modifier": 2.0,
        "reputation_modifier": 3.0,
        "mr_bonus": 0.03,
    },
    "leadership": {
        "label": "Nature-Positive Leadership",
        "ehi_modifier": 4.0,
        "reputation_modifier": 5.0,
        "mr_bonus": 0.05,
    },
}


def get_tnfd_modifiers(level: str) -> dict:
    """Return modifiers for a given TNFD disclosure level."""
    return TNFD_LEVELS.get(level, TNFD_LEVELS["none"])


# ═══════════════════════════════════════════════════════════════
#  RESTORATION PROJECTS
# ═══════════════════════════════════════════════════════════════

RESTORATION_TYPES = {
    "mangrove_restoration": {
        "label": "Coastal Mangrove Restoration",
        "cost_per_round": 500_000,
        "ehi_bonus_per_round": 2.0,
        "habitat_restoration_ha": 50,
        "co_benefits": ["flood_protection", "carbon_sequestration", "fisheries"],
        "maturity_rounds": 3,
        "theory_note": "Nature-based solutions (NbS) — IUCN Global Standard",
    },
    "rewilding_corridor": {
        "label": "Wildlife Corridor Rewilding",
        "cost_per_round": 750_000,
        "ehi_bonus_per_round": 3.0,
        "habitat_restoration_ha": 100,
        "co_benefits": ["species_connectivity", "genetic_diversity"],
        "maturity_rounds": 4,
        "theory_note": "Landscape ecology — habitat connectivity (Hanski 1999)",
    },
    "soil_regeneration": {
        "label": "Agricultural Soil Regeneration",
        "cost_per_round": 300_000,
        "ehi_bonus_per_round": 1.5,
        "habitat_restoration_ha": 200,
        "co_benefits": ["carbon_sequestration", "food_security", "water_retention"],
        "maturity_rounds": 2,
        "theory_note": "Regenerative agriculture — Rodale Institute principles",
    },
    "wetland_creation": {
        "label": "Constructed Wetland for Water Treatment",
        "cost_per_round": 400_000,
        "ehi_bonus_per_round": 2.5,
        "habitat_restoration_ha": 30,
        "co_benefits": ["water_purification", "flood_attenuation", "biodiversity_habitat"],
        "maturity_rounds": 2,
        "theory_note": "Ecosystem-based adaptation (EbA) — CBD guidelines",
    },
}


def process_restoration_projects(
    bio_state: dict,
    gs: dict,
) -> tuple[dict, dict]:
    """
    Advance all active restoration projects by one round.
    Returns updated bio_state and diagnostics.
    """
    projects = bio_state.get("restoration_projects_active", [])
    total_ehi_bonus = 0.0
    total_habitat_restored = 0.0
    completed = []
    ongoing = []

    for project in projects:
        project["rounds_elapsed"] = project.get("rounds_elapsed", 0) + 1
        ptype = RESTORATION_TYPES.get(project["type"], {})

        # Deduct cost
        cost = ptype.get("cost_per_round", 0)
        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - cost, 2)

        # EHI bonus (scaled by maturity — immature projects give partial benefit)
        maturity = ptype.get("maturity_rounds", 3)
        maturity_factor = min(1.0, project["rounds_elapsed"] / maturity)
        ehi_bonus = ptype.get("ehi_bonus_per_round", 0) * maturity_factor
        total_ehi_bonus += ehi_bonus

        # Habitat restoration
        ha_per_round = ptype.get("habitat_restoration_ha", 0) * maturity_factor
        total_habitat_restored += ha_per_round

        if project["rounds_elapsed"] >= maturity:
            completed.append(project)
        else:
            ongoing.append(project)

    bio_state["restoration_projects_active"] = ongoing
    bio_state["cumulative_habitat_restored_ha"] = round(
        bio_state.get("cumulative_habitat_restored_ha", 0) + total_habitat_restored, 1
    )

    diagnostics = {
        "projects_processed": len(projects),
        "projects_completed": [p["type"] for p in completed],
        "projects_ongoing": [p["type"] for p in ongoing],
        "total_ehi_bonus": round(total_ehi_bonus, 2),
        "total_habitat_restored_this_round": round(total_habitat_restored, 1),
        "total_cost_this_round": sum(
            RESTORATION_TYPES.get(p["type"], {}).get("cost_per_round", 0)
            for p in projects
        ),
    }

    return bio_state, diagnostics


# ═══════════════════════════════════════════════════════════════
#  MAIN ROUND PROCESSOR
# ═══════════════════════════════════════════════════════════════

def _deep_audit_in_force(events: dict) -> bool:
    """Whether the R1 deep forensic audit is in force, for the species-risk gate.

    SHAPE E — STRING CONTAINMENT OVER THE REPR OF A NESTED DICT, and the only one
    of the five shapes that FAILS OPEN. The others (Appendix B §B.0, remediation
    plan §1.2) always return False, so their mechanic is simply absent. This one
    returns True on unrelated grounds. The 2026.09 line is

        "deep_audit" in str(events.get("active_event_flags", {}))

    which asks whether the eleven characters "deep_audit" appear anywhere in the
    STRINGIFIED flag bag — keys, values, and the insides of nested dicts and
    lists alike — against a name no configuration declares (the flag is
    deep_audit_completed). Measured across the golden matrix on the deep-audit
    paths, it is True at exactly three rounds and for three different reasons:

        R1   matches the repr of the r1_flags LIST, "['deep_audit_completed']"
        R4   matches the KEY `deep_audit_protected` — a pre_tick pre_event, a
             different flag entirely, set when the team took NEITHER the blindspot
             nor the deferred audit
        R10  matches inside the stringified `_finale_inputs` blob (the R10
             finale's re-run record; it is storage, not flags, and str() does
             not honour the private prefix that hides it from collect_all_flags)

    and False in every other round. So turning the switch ON also turns the gate
    OFF at R4 and R10: this is a behaviour change in both directions, which is
    why it is versioned like the rest rather than fixed outright.

    2026.10 asks the flattened reader for the flag by its real name, over a bag
    that carries the history (round_logic passes previous_flags into the engine
    batch for this), so the audit stays in force for the rest of the game as the
    mechanic reads as though it always intended.
    """
    flags = events.get("active_event_flags") if isinstance(events, dict) else None
    if not isinstance(flags, dict):
        flags = {}
    if rule_on(flags, "biodiversity_audit_gate_reads_flags"):
        return "deep_audit_completed" in collect_all_flags(flags)
    return "deep_audit" in str(flags)


def process_biodiversity_tick(
    bio_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> tuple[dict, dict]:
    """
    Main entry point: process biodiversity state for this round.
    Called from post_tick in round_logic.py.
    Returns (updated_bio_state, diagnostics).
    """
    diagnostics: dict[str, Any] = {}

    # Get NCD delta from events
    ncd_delta = events.get("natural_capital_debt_delta", 0)
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)

    # Process restoration projects
    bio_state, restore_diag = process_restoration_projects(bio_state, gs)
    diagnostics["restoration"] = restore_diag
    restoration_bonus = restore_diag["total_ehi_bonus"]

    # TNFD modifiers
    tnfd_mods = get_tnfd_modifiers(bio_state.get("tnfd_disclosure_level", "none"))
    restoration_bonus += tnfd_mods["ehi_modifier"]

    # 1. Ecosystem Health Index
    new_ehi, ehi_diag = calc_ecosystem_health_index(
        bio_state["ecosystem_health_index"],
        ncd_delta,
        avg_ci,
        bio_state["habitat_integrity"],
        restoration_bonus,
        bio_state.get("deforestation_rate", 0),
    )
    bio_state["ecosystem_health_index"] = new_ehi
    diagnostics["ehi"] = ehi_diag

    # 2. Species Risk
    audit_active = _deep_audit_in_force(events)
    new_risk, risk_diag = calc_species_risk(
        bio_state["species_risk_score"],
        new_ehi,
        bio_state["habitat_integrity"],
        audit_active,
    )
    bio_state["species_risk_score"] = new_risk
    diagnostics["species_risk"] = risk_diag

    # 3. Ecosystem Services Value
    new_esv, esv_diag = calc_ecosystem_services_value(
        bio_state["ecosystem_services_value"],
        new_ehi,
        bio_state.get("pollinator_health", 0.5),
        bio_state.get("water_stress_index", 0.4),
        bio_state["habitat_integrity"],
    )
    bio_state["ecosystem_services_value"] = new_esv
    diagnostics["ecosystem_services"] = esv_diag

    # 4. Biodiversity Dependency
    dep_score, dep_diag = calc_biodiversity_dependency(bus)
    bio_state["biodiversity_dependency_score"] = dep_score
    diagnostics["dependency"] = dep_diag

    # 5. Financial impact: Ecosystem services loss hits OPEX
    if new_esv < bio_state.get("_prev_esv", 8_000_000):
        services_lost = bio_state.get("_prev_esv", 8_000_000) - new_esv
        # Companies must replace lost ecosystem services commercially
        replacement_cost = round(services_lost * dep_score * 0.3, 2)
        if replacement_cost > 0:
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - replacement_cost, 2)
            diagnostics["nature_replacement_cost"] = replacement_cost
            diagnostics["nature_cost_message"] = (
                f"🌿 Nature's Invoice: Ecosystem services declined by "
                f"${services_lost:,.0f}. Commercial replacement of water "
                f"purification, pollination, and flood protection costs "
                f"${replacement_cost:,.0f} this round."
            )

    bio_state["_prev_esv"] = new_esv

    # 6. TNFD disclosure credit (IMP-17: was labelled an M_R bonus that no
    # M_R arbiter ever read — reported as what it is, a disclosure credit)
    diagnostics["tnfd_disclosure_credit"] = tnfd_mods["mr_bonus"]
    diagnostics["tnfd_level"] = bio_state.get("tnfd_disclosure_level", "none")

    # History tracking
    bio_state["biodiversity_history"].append({
        "round": round_number,
        "ehi": new_ehi,
        "species_risk": new_risk,
        "esv": new_esv,
        "habitat_integrity": bio_state["habitat_integrity"],
    })

    return bio_state, diagnostics
