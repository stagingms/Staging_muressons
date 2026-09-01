"""
Muressons Global Corporation — Corporate SDG Side Track: Round Configurations

Five-round deep-dive track running parallel to core operations.
Each round focuses on a specific SDG alignment challenge with three options
mapped to the Principled Prioritization framework.

Point System (SDG Impact Score):
  - Option A: High investment, maximum SDG alignment (+20 to +25 pts)
  - Option B: Moderate investment, partial alignment (+6 to +12 pts)
  - Option C: Minimal/negative investment, compliance-only (-5 to +2 pts)
  Max Total: 105 (all A) | Min Total: -11 (all C)
"""

from __future__ import annotations
from typing import Any


SDG_ROUND_CONFIGS: dict[int, dict[str, Any]] = {
    # ── ST-R1: Principal Adverse Impact (PAI) Audit ─────────────
    1: {
        "round_number": 1,
        "title": "Principal Adverse Impact (PAI) Audit",
        "subtitle": "Map all BU harm pathways to their material SDGs",
        "icon": "🔍",
        "sdg_focus": [3, 6, 8, 9, 10, 12, 15],
        "briefing_text": (
            "The EU Sustainable Finance Disclosure Regulation (SFDR) mandates "
            "Principal Adverse Impact reporting. Your BUs generate externalities "
            "across multiple SDGs — but how deep should you look? A forensic "
            "audit maps every harm pathway. A standard disclosure checks the boxes. "
            "The gap between the two determines whether you see the risks "
            "before they see you."
        ),
        "options": {
            "option_a": {
                "label": "Forensic PAI Audit",
                "description": (
                    "Commission a full forensic audit mapping all BU harm "
                    "pathways to their material SDGs. Expensive but exhaustive."
                ),
                "cost_label": "-$3M",
                "sdg_points": 20,
                "impacts": {
                    "treasury": -3_000_000,
                    "reputation": 10,
                    "governance_risk_delta": -8,
                },
                "flags": {"sdg_integrity_unlocked": True},
            },
            "option_b": {
                "label": "Materiality Review",
                "description": (
                    "Focus only on High Impact areas using existing data. "
                    "Cost-effective but leaves blind spots in lower-priority BUs."
                ),
                "cost_label": "-$1.5M",
                "sdg_points": 10,
                "impacts": {
                    "treasury": -1_500_000,
                    "reputation": 5,
                    "governance_risk_delta": -3,
                },
                "flags": {},
            },
            "option_c": {
                "label": "Standard Disclosure",
                "description": (
                    "Minimum SFDR compliance. Publish template disclosures "
                    "without investigative depth. Sets PAI blindspot."
                ),
                "cost_label": "$0",
                "sdg_points": 2,
                "impacts": {
                    "treasury": 0,
                    "reputation": 0,
                    "governance_risk_delta": 0,
                },
                "flags": {"pai_blindspot": True},
                "warning": "⚠️ Sets pai_blindspot — doubles Round 2 Living Wage Strike severity",
            },
        },
    },

    # ── ST-R2: The Living Wage Strike (SDG 8 & 10) ──────────────
    2: {
        "round_number": 2,
        "title": "The Living Wage Strike",
        "subtitle": "Supply chain labor justice across Tier-1 suppliers",
        "icon": "✊",
        "sdg_focus": [8, 10],
        "briefing_text": (
            "Workers across your Tier-1 supply chain are demanding living wage "
            "parity. The International Labour Organization defines a living wage "
            "as one sufficient to afford a decent standard of living. Your "
            "Electronics and Consumer Goods BUs rely on suppliers where wages "
            "fall 40% below this threshold. How you respond will define your "
            "SDG 8 (Decent Work) and SDG 10 (Reduced Inequalities) credentials."
        ),
        "options": {
            "option_a": {
                "label": "Living Wage Commitment",
                "description": (
                    "Full legal parity across all Tier-1 suppliers. "
                    "Immediate compliance with ILO living wage standards."
                ),
                "cost_label": "-$2.5M",
                "sdg_points": 25,
                "impacts": {
                    "treasury": -2_500_000,
                    "reputation": 15,
                    "social_license_delta": 8,
                },
                "flags": {"sdg_living_wage": True, "community_fund": True},
                "strike_risk_modifier": -0.30,
            },
            "option_b": {
                "label": "Phased Wage Parity",
                "description": (
                    "3-year escalation plan with annual benchmarks. "
                    "Moderate cost, builds workforce readiness over time."
                ),
                "cost_label": "$0",
                "sdg_points": 12,
                "impacts": {
                    "treasury": 0,
                    "reputation": 6,
                },
                "flags": {"managed_transition": True},
                "custom_metrics": {"workforce_readiness_delta": 10},
            },
            "option_c": {
                "label": "Operational Hardball",
                "description": (
                    "Automation-driven response. Break the strike through "
                    "technology substitution. Short-term savings, long-term risk."
                ),
                "cost_label": "$0",
                "sdg_points": -5,
                "impacts": {
                    "treasury": 0,
                    "reputation": -20,
                },
                "flags": {"operational_hardball": True},
                "custom_metrics": {"burnout_delta": 20, "base_strike_risk": 0.50},
                "warning": "⚠️ Reputation -20, Burnout +20, Strike Risk set to 50%",
            },
        },
        "pai_blindspot_multiplier": 2.0,  # If pai_blindspot, double severity
    },

    # ── ST-R3: Circular Procurement Transformation (SDG 12) ─────
    3: {
        "round_number": 3,
        "title": "Circular Procurement Transformation",
        "subtitle": "Redesign procurement for closed-loop material flows",
        "icon": "♻️",
        "sdg_focus": [12],
        "briefing_text": (
            "The EU Circular Economy Action Plan requires 65% municipal waste "
            "recycling by 2035. Your Consumer Goods and Electronics BUs generate "
            "140,000 tonnes of packaging waste annually. A full circular redesign "
            "eliminates waste at source. Targeted sourcing tackles high-volume "
            "streams. Spot-market compliance buys credits — but doesn't change "
            "the underlying material flow."
        ),
        "options": {
            "option_a": {
                "label": "Full Circular Transformation",
                "description": (
                    "Closed-loop redesign of all product lines. "
                    "Design for disassembly, remanufacturing, and material recovery."
                ),
                "cost_label": "-$4M",
                "sdg_points": 20,
                "impacts": {
                    "treasury": -4_000_000,
                    "natural_capital_debt_delta": -15,
                },
                "flags": {"circular_leader": True},
                "custom_metrics": {"synergy_bonus": 0.35},
            },
            "option_b": {
                "label": "Targeted Sourcing",
                "description": (
                    "Switch to recycled plastics and metals for high-volume BUs. "
                    "Partial circularity with manageable disruption."
                ),
                "cost_label": "-$2M",
                "sdg_points": 10,
                "impacts": {
                    "treasury": -2_000_000,
                    "natural_capital_debt_delta": -6,
                    "reputation": 4,
                },
                "flags": {},
            },
            "option_c": {
                "label": "Spot-Market Compliance",
                "description": (
                    "Purchase circularity credits on the open market. "
                    "Meet regulatory thresholds without operational change."
                ),
                "cost_label": "-$1M",
                "sdg_points": -3,
                "impacts": {
                    "treasury": -1_000_000,
                    "natural_capital_debt_delta": 3,
                    "governance_risk_delta": 5,
                },
                "flags": {"greenwash_risk": True},
                "warning": "⚠️ Sets greenwash_risk — NCD +3, Governance Risk +5",
            },
        },
    },

    # ── ST-R4: Biodiversity Net-Gain (SDG 15) ───────────────────
    4: {
        "round_number": 4,
        "title": "Biodiversity Net-Gain Commitment",
        "subtitle": "SBTN alignment and TNFD disclosure for nature-positive operations",
        "icon": "🌿",
        "sdg_focus": [15],
        "briefing_text": (
            "The Taskforce on Nature-related Financial Disclosures (TNFD) "
            "and Science Based Targets for Nature (SBTN) are becoming the "
            "standard for biodiversity accountability. Your Consumer Goods BU "
            "sources palm oil from regions with critical habitat loss. Your "
            "Pharma BU depends on biodiverse ecosystems for active pharmaceutical "
            "ingredients. How aggressively will you pursue nature-positive status?"
        ),
        "options": {
            "option_a": {
                "label": "Nature-Positive Transformation",
                "description": (
                    "Full SBTN No-Net-Loss commitment with TNFD disclosure. "
                    "Restore 2,000 hectares of degraded habitat. "
                    "Sets nature_positive flag for terminal valuation."
                ),
                "cost_label": "-$6M",
                "sdg_points": 20,
                "impacts": {
                    "treasury": -6_000_000,
                    "natural_capital_debt_delta": -15,
                    "reputation": 10,
                },
                "flags": {"nature_positive": True},
            },
            "option_b": {
                "label": "Targeted Conservation",
                "description": (
                    "Reforestation of 1,000 hectares in critical supply chain "
                    "corridors. Partial biodiversity recovery with TNFD alignment."
                ),
                "cost_label": "-$2M",
                "sdg_points": 10,
                "impacts": {
                    "treasury": -2_000_000,
                    "natural_capital_debt_delta": -6,
                    "reputation": 4,
                },
                "flags": {},
            },
            "option_c": {
                "label": "Market-Based Deferral",
                "description": (
                    "Purchase biodiversity credits and defer TNFD compliance. "
                    "Buy time, but NCD compounds and governance risk increases."
                ),
                "cost_label": "$0",
                "sdg_points": -2,
                "impacts": {
                    "treasury": 0,
                    "natural_capital_debt_delta": 5,
                    "governance_risk_delta": 3,
                },
                "flags": {},
                "warning": "⚠️ NCD +5, Governance Risk +3 — deferral compounds over time",
            },
        },
    },

    # ── ST-R5: Integrated Reporting & Final Valuation ───────────
    5: {
        "round_number": 5,
        "title": "Integrated Reporting & Value Creation",
        "subtitle": "Codify the Universal Care Mandate into corporate DNA",
        "icon": "📊",
        "sdg_focus": [3, 6, 8, 9, 10, 12, 15],
        "briefing_text": (
            "The final SDG track decision determines how your sustainability "
            "commitments are embedded into corporate reporting. An Integrated "
            "Value Creation report codifies the Universal Care Mandate — making "
            "SDG alignment a permanent governance structure. A separate supplement "
            "keeps sustainability as an appendix. The market will read between "
            "the lines."
        ),
        "options": {
            "option_a": {
                "label": "Integrated Value Creation",
                "description": (
                    "Codify the Universal Care Mandate into annual reporting. "
                    "SDG alignment becomes a board-level governance obligation — "
                    "the track's strongest SDG-score and reputation reward."
                ),
                "cost_label": "-$8M",
                "sdg_points": 20,
                "impacts": {
                    "treasury": -8_000_000,
                    "reputation": 15,
                },
                "flags": {"sdg_integrated_reporting": True},
                "custom_metrics": {"mr_bonus": 0.35},
            },
            "option_b": {
                "label": "Strategic Integration",
                "description": (
                    "Enhanced Management Discussion & Analysis with SDG mapping. "
                    "Demonstrates strategic intent without full codification."
                ),
                "cost_label": "-$5M",
                "sdg_points": 10,
                "impacts": {
                    "treasury": -5_000_000,
                    "reputation": 6,
                },
                "flags": {},
                "custom_metrics": {"mr_bonus": 0.15},
            },
            "option_c": {
                "label": "Separate Supplement",
                "description": (
                    "Publish a standalone ESG report separate from financial "
                    "statements. Signals that sustainability is not core strategy."
                ),
                "cost_label": "-$2M",
                "sdg_points": -3,
                "impacts": {
                    "treasury": -2_000_000,
                    "reputation": -3,
                },
                "flags": {"credibility_gap_penalty": True},
                "warning": "⚠️ Sets credibility_gap_penalty — signals ESG is not core strategy",
            },
        },
    },
}


# ── SDG Impact Point Awards ─────────────────────────────────────
SDG_POINTS_MAP = {
    rnd: {
        opt_key: opt_cfg["sdg_points"]
        for opt_key, opt_cfg in cfg["options"].items()
    }
    for rnd, cfg in SDG_ROUND_CONFIGS.items()
}


def get_sdg_round_config(round_number: int) -> dict[str, Any] | None:
    """Return the configuration for a specific SDG track round."""
    import copy
    cfg = SDG_ROUND_CONFIGS.get(round_number)
    return copy.deepcopy(cfg) if cfg else None


def get_sdg_round_options(round_number: int) -> dict[str, Any]:
    """Return just the options dict for a specific SDG track round."""
    import copy
    cfg = SDG_ROUND_CONFIGS.get(round_number, {})
    return copy.deepcopy(cfg.get("options", {}))
