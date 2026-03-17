"""
Muressons Global Command — Round Configuration Registry
Centralized definitions for all 10 rounds: crisis scenarios,
decision options, flag triggers, and validation rules.
"""

from __future__ import annotations
from typing import Any
import copy  # FIX VULN-010: return immutable copies
import json
import os
from pathlib import Path

OVERRIDES_FILE = Path(__file__).parent / "decision_overrides.json"

# ═════════════════════════════════════════════════════════════════
#  ROUND CONFIGS
#  Each entry contains:
#    title, theme, crisis, options (A/B/C), flags_triggered,
#    and optional validation_rules.
# ═════════════════════════════════════════════════════════════════

ROUND_CONFIGS: dict[int, dict[str, Any]] = {

    # ── Round 1: Foundations ────────────────────────────────────
    1: {
        "title": "Foundations",
        "theme": "ESG Baseline Assessment",
        "crisis": {
            "id": "r1_foundations",
            "title": "ESG Audit Decision",
            "description": (
                "The board has mandated an initial ESG assessment across "
                "all business units. You must decide the depth and scope "
                "of the audit."
            ),
            "icon": "📋",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Surface-Level Scan",
                "description": (
                    "Run a quick compliance check. Fast and cheap, but "
                    "Electronics BU blind spots will be missed."
                ),
                "flags_set": ["electronics_blindspot"],
                "impacts": {
                    "treasury": 0,
                    "reputation": -2,
                    "carbon_intensity_delta": +2,
                    "revenue_delta": +500_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Deep Forensic Audit",
                "description": (
                    "Commission a full forensic audit across all units. "
                    "Costly but uncovers hidden risks."
                ),
                "flags_set": ["deep_audit_completed"],
                "impacts": {
                    "treasury": -3_000_000,
                    "reputation": +5,
                    "carbon_intensity_delta": -5,
                    "revenue_delta": -200_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Phased Audit Rollout",
                "description": (
                    "Audit Pharma and Consumer Goods now; defer Electronics "
                    "and Software. Balanced cost."
                ),
                "flags_set": ["electronics_blindspot"],
                "impacts": {
                    "treasury": -1_500_000,
                    "reputation": +2,
                    "carbon_intensity_delta": -2,
                    "revenue_delta": 0,
                },
            },
        },
    },

    # ── Round 2: Double Materiality ─────────────────────────────
    2: {
        "title": "Double Materiality",
        "theme": "Materiality-Based Budget Allocation",
        "crisis": {
            "id": "r2_double_materiality",
            "title": "Double Materiality Matrix",
            "description": (
                "The CFO requires all investment proposals to demonstrate "
                "alignment with the High Financial Impact / High ESG Impact "
                "quadrant per the Double Materiality framework."
            ),
            "icon": "📊",
        },
        "validation_rules": {
            "cfo_materiality_gate": True,
            "high_impact_nodes": [
                "round_2_pharma",
                "round_2_electronics",
                "round_2_consumer_goods",
                "round_2_software"
            ],
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Materiality Alignment",
                "description": "Allocate exclusively to high-impact nodes.",
                "flags_set": ["materiality_aligned"],
                "impacts": {"reputation": +5, "governance_risk": -5, "carbon_intensity_delta": -3, "revenue_delta": -300_000},
            },
            "option_b": {
                "label": "B",
                "title": "Strategic Exceptions",
                "description": "Allow limited off-quadrant spending with CFO approval.",
                "flags_set": ["materiality_exceptions"],
                "impacts": {"reputation": +2, "governance_risk": -2, "carbon_intensity_delta": -1, "revenue_delta": 0},
            },
            "option_c": {
                "label": "C",
                "title": "Ignore Materiality Framework",
                "description": "Business-as-usual. No materiality filter.",
                "flags_set": ["materiality_ignored"],
                "impacts": {"reputation": -5, "governance_risk": +10, "carbon_intensity_delta": +3, "revenue_delta": +400_000},
            },
        },
    },

    # ── Round 3: Scope 3 Emissions ──────────────────────────────
    3: {
        "title": "Scope 3 Emissions",
        "theme": "Supply Chain Decarbonisation",
        "crisis": {
            "id": "r3_scope3",
            "title": "Scope 3 Supply Chain Crisis",
            "description": (
                "Regulators have signalled mandatory Scope 3 disclosures. "
                "Your supply chain carbon footprint is 4x your direct "
                "emissions."
            ),
            "icon": "🏭",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Rapid Supplier Switch",
                "description": (
                    "Immediately switch to low-carbon suppliers. Fast "
                    "reduction but high disruption risk."
                ),
                "flags_set": ["supply_chain_disruption_risk"],
                "impacts": {
                    "treasury": -4_000_000,
                    "carbon_intensity_delta": -15,
                    "supply_chain_disruption": True,
                    "revenue_delta": -800_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Green Bond Investment",
                "description": (
                    "Issue a green bond to fund supplier transition. Lowers "
                    "Natural Capital Debt over 3 rounds."
                ),
                "flags_set": ["green_bond_active"],
                "impacts": {
                    "treasury": -2_000_000,
                    "natural_capital_debt_delta": -15,
                    "carbon_intensity_delta": -8,
                    "revenue_delta": +300_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Offset & Defer",
                "description": "Buy carbon offsets and wait for regulation clarity.",
                "flags_set": ["carbon_deferred"],
                "impacts": {
                    "treasury": -1_000_000,
                    "natural_capital_debt_delta": +5,
                    "reputation": -3,
                    "carbon_intensity_delta": -1,
                    "revenue_delta": +100_000,
                },
            },
        },
    },

    # ── Round 4: Contagion ──────────────────────────────────────
    4: {
        "title": "Contagion",
        "theme": "Reputation Crisis Cascade",
        "crisis": {
            "id": "r4_contagion",
            "title": "Electronics Supply Chain Scandal",
            "description": (
                "A labour-rights exposé in your Electronics supply chain "
                "has gone viral. The contagion engine will propagate "
                "reputational damage across all BUs."
            ),
            "icon": "🔥",
        },
        "special_rules": {
            "electronics_blindspot_doubles_crisis": True,
            "base_crisis_severity": 40,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Transparency & Remediation",
                "description": "Public disclosure, factory audits, worker compensation.",
                "flags_set": ["remediation_active"],
                "impacts": {"treasury": -6_000_000, "reputation": +10, "social_license": +8, "carbon_intensity_delta": -4, "revenue_delta": -500_000},
            },
            "option_b": {
                "label": "B",
                "title": "Damage Control PR",
                "description": "Hire crisis PR firm. Contains narrative but doesn't fix root cause.",
                "flags_set": ["pr_containment"],
                "impacts": {"treasury": -2_000_000, "reputation": +2, "social_license": -3, "carbon_intensity_delta": -1, "revenue_delta": 0},
            },
            "option_c": {
                "label": "C",
                "title": "Deny & Deflect",
                "description": "Issue a denial. Cheapest option but highest contagion risk.",
                "flags_set": ["deny_and_deflect"],
                "impacts": {"treasury": 0, "reputation": -15, "social_license": -10, "carbon_intensity_delta": +4, "revenue_delta": -1_000_000},
            },
        },
    },

    # ── Round 5: Climate ────────────────────────────────────────
    5: {
        "title": "Climate",
        "theme": "Physical Climate Risk Event",
        "crisis": {
            "id": "r5_climate",
            "title": "Extreme Weather Event",
            "description": (
                "A Category 4 cyclone is projected to hit your primary "
                "manufacturing corridor. Base damage: $12M. A stochastic "
                "roll determines actual impact."
            ),
            "icon": "🌪️",
        },
        "special_rules": {
            "stochastic_event": True,
            "base_damage": 12_000_000,
            "stochastic_threshold": 0.75,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Hard Engineering Defence",
                "description": (
                    "Build flood walls and reinforced infrastructure. "
                    "Resilience Factor 0.85, but adds 10 Natural Capital Debt."
                ),
                "flags_set": ["hard_engineering"],
                "impacts": {
                    "resilience_factor": 0.85,
                    "natural_capital_debt_delta": +10,
                    "treasury": -8_000_000,
                    "carbon_intensity_delta": +3,
                    "revenue_delta": -600_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Nature-Based Solutions",
                "description": (
                    "Invest in mangrove restoration and natural buffers. "
                    "Resilience Factor 0.60, reduces Natural Capital Debt."
                ),
                "flags_set": ["nature_based_resilience"],
                "impacts": {
                    "resilience_factor": 0.60,
                    "natural_capital_debt_delta": -8,
                    "treasury": -5_000_000,
                    "carbon_intensity_delta": -6,
                    "revenue_delta": +500_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Insurance Only",
                "description": "Buy comprehensive insurance. No resilience factor.",
                "flags_set": ["insurance_only"],
                "impacts": {
                    "resilience_factor": 0.0,
                    "treasury": -2_000_000,
                    "carbon_intensity_delta": +1,
                    "revenue_delta": 0,
                },
            },
        },
    },

    # ── Round 6: AI Bias ────────────────────────────────────────
    6: {
        "title": "AI Bias",
        "theme": "Algorithmic Ethics & Brand Risk",
        "crisis": {
            "id": "r6_ai_bias",
            "title": "AI Hiring Bias Scandal",
            "description": (
                "Your Software BU's AI recruitment tool has been found to "
                "systematically discriminate against minority applicants. "
                "The story has reached mainstream media."
            ),
            "icon": "🤖",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Monetise the Algorithm",
                "description": (
                    "Pivot the AI tool into a commercial product. High revenue "
                    "but massive reputational risk, spiking the contagion factor."
                ),
                "flags_set": ["ai_monetised"],
                "impacts": {
                    "software_revenue_delta": +5_000_000,
                    "reputation_delta": -20,
                    "contagion_spike": True,
                    "carbon_intensity_delta": +2,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Ethical AI Overhaul",
                "description": (
                    "Shut down the tool, hire an ethics board, retrain models. "
                    "Costly but builds social capital."
                ),
                "flags_set": ["ethical_ai_overhaul"],
                "impacts": {
                    "treasury": -8_000_000,
                    "social_license_delta": +15,
                    "reputation_delta": +5,
                    "carbon_intensity_delta": -4,
                    "revenue_delta": +800_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Quiet Patch",
                "description": "Silently fix the algorithm. Low cost but if leaked, devastating.",
                "flags_set": ["quiet_patch"],
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation_delta": -5,
                    "governance_risk_delta": +10,
                    "carbon_intensity_delta": 0,
                    "revenue_delta": -200_000,
                },
            },
        },
    },

    # ── Round 7: Circularity ────────────────────────────────────
    7: {
        "title": "Circularity",
        "theme": "Circular Economy Transition",
        "crisis": {
            "id": "r7_circularity",
            "title": "Waste Regulation Tightening",
            "description": (
                "New EU circular economy regulations mandate 60% waste "
                "diversion by next year. Non-compliance fines: $15M."
            ),
            "icon": "♻️",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Circular Redesign",
                "description": "Redesign products for full disassembly and reuse.",
                "flags_set": ["circular_redesign"],
                "impacts": {
                    "treasury": -10_000_000,
                    "natural_capital_debt_delta": -12,
                    "reputation": +8,
                    "carbon_intensity_delta": -8,
                    "revenue_delta": +1_000_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Extended Producer Responsibility",
                "description": "Fund take-back programs and recycling partnerships.",
                "flags_set": ["epr_program"],
                "impacts": {
                    "treasury": -5_000_000,
                    "natural_capital_debt_delta": -6,
                    "reputation": +4,
                    "carbon_intensity_delta": -5,
                    "revenue_delta": +600_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Waste-to-Energy Partnership",
                "description": (
                    "Build waste-to-energy facility. Unlocks high synergy "
                    "multiplier across BUs."
                ),
                "flags_set": ["waste_to_energy", "synergy_unlock"],
                "impacts": {
                    "treasury": -7_000_000,
                    "synergy_multiplier_boost": 0.35,
                    "natural_capital_debt_delta": -4,
                    "carbon_intensity_delta": -6,
                    "revenue_delta": +400_000,
                },
            },
        },
    },

    # ── Round 8: Blue Stress ────────────────────────────────────
    8: {
        "title": "Blue Stress",
        "theme": "Water Scarcity Emergency",
        "crisis": {
            "id": "r8_blue_stress",
            "title": "Critical Water Shortage",
            "description": (
                "A multi-year drought has depleted the watershed serving "
                "Pharma and Electronics. Government water rationing is "
                "imminent."
            ),
            "icon": "🌊",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Water Efficiency for All BUs",
                "description": "Equitable water-saving upgrades across all units.",
                "flags_set": ["water_efficiency_all"],
                "impacts": {
                    "treasury": -12_000_000,
                    "water_dependency_delta": -20,
                    "social_license_delta": +5,
                    "carbon_intensity_delta": -3,
                    "revenue_delta": +700_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Prioritise Electronics",
                "description": (
                    "Divert water allocation to Electronics (highest margin). "
                    "Pharma and Consumer Goods take severe social licence hit."
                ),
                "flags_set": ["electronics_water_priority"],
                "impacts": {
                    "treasury": -4_000_000,
                    "social_license_severe_drop": True,
                    "social_license_drop_targets": ["pharma", "consumer_goods"],
                    "social_license_drop_amount": -25,
                    "carbon_intensity_delta": +2,
                    "revenue_delta": -400_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Desalination Mega-Project",
                "description": (
                    "Build a desalination plant. Massive cost ($30M) but "
                    "reduces Natural Capital Debt by 30 points."
                ),
                "flags_set": ["desalination_built"],
                "impacts": {
                    "treasury": -30_000_000,
                    "natural_capital_debt_delta": -30,
                    "water_dependency_delta": -40,
                    "carbon_intensity_delta": -5,
                    "revenue_delta": +300_000,
                },
            },
        },
    },

    # ── Round 9: Just Transition ────────────────────────────────
    9: {
        "title": "Just Transition",
        "theme": "Workforce & Community Justice",
        "crisis": {
            "id": "r9_just_transition",
            "title": "Factory Closure & Workforce Crisis",
            "description": (
                "Decarbonisation commitments require closing 3 legacy "
                "factories. 2,000 jobs are at risk. Community protests "
                "are escalating."
            ),
            "icon": "✊",
        },
        "special_rules": {
            "low_social_license_strike_trigger": True,
            "strike_probability_override": 0.75,
            "regulatory_friction_enabled": True,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Immediate Closure",
                "description": (
                    "Close factories now for maximum cost savings. If Social "
                    "License is low, 75% chance of a strike that zeros revenue."
                ),
                "flags_set": ["immediate_closure"],
                "impacts": {
                    "treasury": +5_000_000,
                    "social_license_delta": -20,
                    "reputation_delta": -15,
                    "strike_risk": True,
                    "carbon_intensity_delta": +3,
                    "revenue_delta": -1_200_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Managed Transition",
                "description": "2-year phase-out with retraining and severance packages.",
                "flags_set": ["managed_transition"],
                "impacts": {
                    "treasury": -12_000_000,
                    "social_license_delta": +10,
                    "reputation_delta": +8,
                    "carbon_intensity_delta": -4,
                    "revenue_delta": +600_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Community Investment Fund",
                "description": (
                    "Create a $20M fund for community economic development "
                    "and green job training."
                ),
                "flags_set": ["community_fund"],
                "impacts": {
                    "treasury": -20_000_000,
                    "social_license_delta": +18,
                    "reputation_delta": +12,
                    "governance_risk_delta": -5,
                    "carbon_intensity_delta": -3,
                    "revenue_delta": +400_000,
                },
            },
        },
    },

    # ── Round 10: Grand Finale — Activist Ultimatum ───────────────
    10: {
        "title": "Grand Finale",
        "theme": "2050 Activist Ultimatum & Terminal Valuation",
        "crisis": {
            "id": "r10_grand_finale",
            "title": "Activist Ultimatum",
            "description": (
                "An activist investor consortium has acquired a blocking "
                "stake. They are demanding a strategic restructuring. The "
                "board must decide the company's 2050 trajectory."
            ),
            "icon": "🏛️",
        },
        "special_rules": {
            "carbon_tax_per_ton": 250,
            "exit_multiple": 12.0,
            "synergy_gate_threshold": 80,
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Resist & Integrate",
                "description": (
                    "Fight the activist. Keep all BUs integrated and "
                    "leverage synergy. DISABLED if Synergy Score ≤ 80."
                ),
                "flags_set": ["resist_integrate"],
                "ui_constraints": {"require_synergy_above": 80},
                "impacts": {
                    "synergy_bonus": True,
                    "treasury": -5_000_000,
                    "carbon_intensity_delta": -3,
                    "revenue_delta": +1_000_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Spin-off",
                "description": (
                    "Spin off the weakest-performing BU as a separate "
                    "entity. Moderate risk, unlocks partial value."
                ),
                "flags_set": ["spinoff"],
                "impacts": {
                    "spinoff_weakest_bu": True,
                    "treasury": +10_000_000,
                    "carbon_intensity_delta": -1,
                    "revenue_delta": -500_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Divest",
                "description": (
                    "Full divestiture of non-core assets. Maximum short-term "
                    "cash extraction at the cost of long-term value."
                ),
                "flags_set": ["divest"],
                "impacts": {
                    "divest_all": True,
                    "treasury": +25_000_000,
                    "synergy_wipe": True,
                    "carbon_intensity_delta": +2,
                    "revenue_delta": -2_000_000,
                },
            },
        },
    },
}


def _deep_merge(dict1: dict, dict2: dict) -> dict:
    for k, v in dict2.items():
        if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
            _deep_merge(dict1[k], v)
        else:
            dict1[k] = copy.deepcopy(v)
    return dict1

def _get_merged_round_configs() -> dict[int, dict[str, Any]]:
    base_configs = copy.deepcopy(ROUND_CONFIGS)
    if OVERRIDES_FILE.exists():
        try:
            with open(OVERRIDES_FILE, "r") as f:
                data = json.load(f)
            legacy_overrides = data.get("legacy_abc", {})
            for round_num_str, cfg_override in legacy_overrides.items():
                round_num = int(round_num_str)
                if round_num in base_configs:
                    _deep_merge(base_configs[round_num], cfg_override)
        except Exception as e:
            print(f"Error loading decision overrides: {e}")
    return base_configs

_detailed_cache = None

def _get_detailed_descriptions():
    global _detailed_cache
    if _detailed_cache is None:
        try:
            path = os.path.join(os.path.dirname(__file__), "detailed_descriptions.json")
            with open(path, "r", encoding="utf-8") as f:
                _detailed_cache = json.load(f)
        except Exception as e:
            print("Warning: Could not load detailed_descriptions.json:", e)
            _detailed_cache = {}
    return _detailed_cache

def get_round_config(round_number: int) -> dict[str, Any] | None:
    """Return a deep copy of the config for a specific round, or None if out of range."""
    # FIX VULN-010: Return deep copy to prevent runtime mutation
    cfg = _get_merged_round_configs().get(round_number)
    if not cfg:
        return None
        
    cfg_copy = copy.deepcopy(cfg)
    try:
        detailed = _get_detailed_descriptions().get("narrative", {}).get(str(round_number), {})
        for opt_key, opt_data in cfg_copy.get("options", {}).items():
            if opt_key in detailed:
                opt_data["detailed_description"] = detailed[opt_key]
    except Exception as e:
        print("Failed to inject detailed descriptions:", e)
        
    return cfg_copy

def get_round_options(round_number: int) -> dict[str, Any]:
    """Return a deep copy of just the option definitions for a round."""
    cfg = _get_merged_round_configs().get(round_number, {})
    return copy.deepcopy(cfg.get("options", {}))

def get_round_crisis(round_number: int) -> dict[str, Any] | None:
    """Return a deep copy of the crisis definition for a round."""
    cfg = _get_merged_round_configs().get(round_number)
    return copy.deepcopy(cfg.get("crisis")) if cfg else None
