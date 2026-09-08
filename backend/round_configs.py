"""
Muressons Global Corporation — Round Configuration Registry
Centralized definitions for all 10 rounds: crisis scenarios,
decision options, flag triggers, and validation rules.
"""

from __future__ import annotations
from typing import Any
import copy  # FIX VULN-010: return immutable copies
import json
import os
from pathlib import Path

from runtime_paths import config_file as _config_file
# 3.1: durable location. admin_router imports THIS constant as
# ROUND_OVERRIDES_FILE for its read-modify-write, so all four sites agree.
OVERRIDES_FILE = _config_file("decision_overrides.json")

# ═════════════════════════════════════════════════════════════════
#  ROUND CONFIGS
#  Each entry contains:
#    title, theme, crisis, options (A/B/C), flags_triggered,
#    and optional validation_rules.
# ═════════════════════════════════════════════════════════════════

ROUND_CONFIGS = {

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
            "option_a": {"green_claim": "full", 
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
                    "social_license_delta": -3,
                    "governance_risk_delta": +5,
                    "natural_capital_debt_delta": 0,
                },
            },
            "option_b": {"green_claim": "moderate", 
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
                    "social_license_delta": +5,
                    "governance_risk_delta": -5,
                    "natural_capital_debt_delta": 0,
                },
            },
            "option_c": {"green_claim": "moderate", 
                "label": "C",
                "title": "Phased Audit Rollout",
                "description": (
                    "Audit Pharma and Consumer Goods now; defer Electronics "
                    "and Software to next period. Balanced cost, but "
                    "partial blind spots remain."
                ),
                "flags_set": ["deferred_audit"],
                "impacts": {
                    "treasury": -1_500_000,
                    "reputation": +2,
                    "carbon_intensity_delta": -2,
                    "revenue_delta": 0,
                    "social_license_delta": +2,
                    "governance_risk_delta": 0,
                    "natural_capital_debt_delta": 0,
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
        "special_rules": {
            # F-4: the keys that used to sit here (accuracy_threshold: 90 and a
            # $2M accuracy_bonus_amount treasury bonus) described a mechanic
            # that never existed anywhere in the code — they were the source of
            # the documentation drift. These are the REAL numbers, and the
            # engine reads them (router accuracy bonus; _post_r2_materiality
            # tier threshold).
            "accuracy_threshold_pct": 80,
            "accuracy_bonus_points": 1000,
        },
        "options": {
            "option_a": {"green_claim": "full", 
                "label": "A",
                "title": "Full Materiality Alignment",
                "description": (
                    "Allocate exclusively to high-impact nodes. Genuine CSRD compliance: "
                    "assurance-ready report, stakeholder panel, full ESRS disclosure. "
                    "In Advanced Climate mode: unlocks CSRD/ESRS climate materiality bonus "
                    "(NCD forgiveness +25%). Compliance cost is real."
                ),
                # F-2: no tier flag here. materiality_aligned / materiality_partial /
                # materiality_ignored are written ONLY by round_logic._post_r2_materiality,
                # which combines this choice with the matrix accuracy at post-tick.
                # full_materiality_alignment records WHAT was chosen, never whether
                # the premium was earned — but it is NOT unconsumed. Corrected
                # 2026-09-08: engine.py:3787 scales NCD forgiveness by the
                # ac_bonus multiplier on the line below, in the advanced_climate
                # paradigm only (the gate is engine.py:3763). On the default
                # legacy_abc path the flag is inert, which is what the old wording
                # was reaching for and stated too broadly. Measured: NCD
                # forgiveness 1.23 -> 1.54 with the flag under advanced_climate,
                # unchanged under legacy_abc.
                "flags_set": ["full_materiality_alignment"],
                "ac_bonus": {"ncd_forgiveness_multiplier": 1.25, "note": "CSRD climate materiality alignment"},
                "impacts": {
                    "treasury": -2_500_000,   # the documented compliance cost — keep
                    "reputation": +5,
                    "governance_risk_delta": -5,
                    "carbon_intensity_delta": -3,
                    # F-7: WAS -2_500_000 — but revenue_delta is applied PER
                    # business unit by _apply_common_impacts and revenue_base
                    # persists, so the group-sized figure cost -$12.5M of
                    # permanent group revenue (-29% for the smallest unit) on
                    # top of the treasury charge: ~$15M for an option every
                    # document prices at $2.5M. Compliance spend is a cash
                    # cost, not a revenue reduction. If a revenue effect is
                    # ever wanted, it must be per-unit-scaled (e.g. -500_000
                    # ≈ -$2.5M group) and a deliberate design decision.
                    "revenue_delta": 0,
                    "social_license_delta": +5,
                    "natural_capital_debt_delta": -3,
                },
            },
            "option_b": {"green_claim": "moderate", 
                "label": "B",
                "title": "Strategic Exceptions",
                "description": "Allow limited off-quadrant spending with CFO approval. Partial compliance.",
                "flags_set": ["materiality_exceptions"],
                "impacts": {"treasury": 0, "reputation": +2, "governance_risk_delta": -2, "carbon_intensity_delta": -1, "revenue_delta": 0, "social_license_delta": +2, "natural_capital_debt_delta": 0},
            },
            "option_c": {
                "label": "C",
                "title": "CEO-Only Sign-Off (No Board Committee Oversight)",
                "description": (
                    "CEO approves capital allocation without board committee review or endorsement. "
                    "⚠️ ESRS 1 §1.51 Violation: The standard requires the management body (board level) "
                    "to oversee and endorse the materiality assessment process. CEO-only sign-off breaches "
                    "this requirement. Institutional investors apply a risk premium to your Green Bond — "
                    "40% of your materiality budget will be clawed back. Governance posture must match "
                    "investment rationale under ESRS 2 GOV-1."
                ),
                # F-2: tier flag owned by round_logic._post_r2_materiality (see option_a).
                # ceo_only_signoff is a choice marker with no consumer.
                "flags_set": ["ceo_only_signoff"],
                # budget_clawback_pct is read by round_logic._post_r2_materiality
                # to retroactively reduce the materiality fund released this round.
                "budget_clawback_pct": 0.40,
                "impacts": {"treasury": 0, "reputation": -5, "governance_risk_delta": +10, "carbon_intensity_delta": +3, "revenue_delta": +400_000, "social_license_delta": -5, "natural_capital_debt_delta": +3},
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
            "option_a": {"green_claim": "full", 
                "label": "A",
                "title": "Rapid Supplier Switch",
                "description": (
                    "Immediately switch to low-carbon suppliers. Fast "
                    "reduction but high disruption risk. Early movers "
                    "gain a strategic advantage in circular economy."
                ),
                "flags_set": ["supply_chain_disruption_risk", "early_decarboniser"],
                "ci_routing": "scope3_weighted",  # I2: affects Scope3-heavy BUs most
                "impacts": {
                    "treasury": -4_000_000,
                    "carbon_intensity_delta": -15,
                    "supply_chain_disruption": True,
                    "revenue_delta": -800_000,
                    "reputation": +3,
                    "social_license_delta": +4,
                    "governance_risk_delta": -3,
                    "natural_capital_debt_delta": -10,
                },
            },
            "option_b": {"green_claim": "full", 
                "label": "B",
                "title": "Green Bond Investment",
                "description": (
                    "Issue a green bond to fund supplier transition. Lowers "
                    "Natural Capital Debt by 15 over 3 rounds (5 per round, R3–R5)."
                ),
                "flags_set": ["green_bond_active"],
                "ci_routing": "scope3_weighted",  # I2: green bond targets supply chain
                "impacts": {
                    "treasury": -2_000_000,
                    "natural_capital_debt_delta": -15,
                    # FLAG-10.3 (WP-24): spread over three ticks via ncd_drop
                    # projects (round_logic._post_r3_scope3), as the text says.
                    "natural_capital_debt_rounds": 3,
                    "carbon_intensity_delta": -8,
                    "revenue_delta": +300_000,
                    "reputation": +4,
                    "social_license_delta": +3,
                    "governance_risk_delta": -2,
                },
            },
            "option_c": {"green_claim": "full", 
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
                    "social_license_delta": -4,
                    "governance_risk_delta": +3,
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
            "option_a": {"green_claim": "moderate", 
                "label": "A",
                "title": "Full Transparency & Remediation",
                "description": "Public disclosure, factory audits, worker compensation.",
                "flags_set": ["remediation_active"],
                "impacts": {"treasury": -6_000_000, "reputation": +10, "social_license_delta": +8, "carbon_intensity_delta": -4, "revenue_delta": -500_000, "governance_risk_delta": -5, "natural_capital_debt_delta": 0},
            },
            "option_b": {"green_claim": "moderate", 
                "label": "B",
                "title": "Damage Control PR",
                "description": "Hire crisis PR firm. Contains narrative but doesn't fix root cause.",
                "flags_set": ["pr_containment"],
                "impacts": {"treasury": -2_000_000, "reputation": +2, "social_license_delta": -3, "carbon_intensity_delta": -1, "revenue_delta": 0, "governance_risk_delta": +3, "natural_capital_debt_delta": 0},
            },
            "option_c": {
                "label": "C",
                "title": "Deny & Deflect",
                "description": "Issue a denial. Cheapest option but highest contagion risk.",
                "flags_set": ["deny_and_deflect"],
                "impacts": {"treasury": 0, "reputation": -15, "social_license_delta": -10, "carbon_intensity_delta": +4, "revenue_delta": -1_000_000, "governance_risk_delta": +8, "natural_capital_debt_delta": +5},
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
            "option_a": {"green_claim": "moderate", 
                "label": "A",
                "title": "Hard Engineering Defence",
                "description": (
                    "Build flood walls and reinforced infrastructure. "
                    "Resilience Factor 0.85 — but construction takes 2 rounds. "
                    "⚠️ NO PROTECTION THIS ROUND. Infrastructure completes in Round 7. "
                    "Adds 10 Natural Capital Debt (concrete/steel environmental cost). "
                    "🌡️ CLIMATE WARNING: +3 Carbon Intensity contributes to the "
                    "Climate Tipping Point (avg CI > 70). In Advanced Climate mode, "
                    "crossing this threshold doubles NCD costs permanently."
                ),
                "flags_set": ["hard_engineering"],
                "climate_framing": "ADAPTATION (physical infrastructure)",
                "impacts": {
                    "resilience_factor": 0.85,
                    "natural_capital_debt_delta": +10,
                    "treasury": -8_000_000,
                    "carbon_intensity_delta": +3,
                    "revenue_delta": -600_000,
                    "reputation": +3,
                },
            },
            "option_b": {"green_claim": "full", 
                "label": "B",
                "title": "Nature-Based Solutions",
                "description": (
                    "Invest in mangrove restoration and natural buffers. "
                    "Resilience Factor 0.60 — but ecosystem establishment takes 2 rounds. "
                    "⚠️ NO PROTECTION THIS ROUND. Buffers mature by Round 7. "
                    "Reduces Natural Capital Debt (nature-positive infrastructure)."
                ),
                "flags_set": ["nature_based_resilience"],
                "climate_framing": "ADAPTATION + MITIGATION (nature-positive)",
                "impacts": {
                    "resilience_factor": 0.60,
                    "natural_capital_debt_delta": -8,
                    "treasury": -5_000_000,
                    "carbon_intensity_delta": -6,
                    "revenue_delta": +500_000,
                    "reputation": +6,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Insurance Only",
                "description": (
                    "Buy comprehensive insurance. No physical resilience built — "
                    "full damage if cyclone strikes this round or any future round. "
                    "⚠️ Blocks the Resilience Bonus at terminal valuation (−0.20 M_R)."
                ),
                "flags_set": ["insurance_only"],
                "climate_framing": "RISK TRANSFER (no physical adaptation)",
                "warning_badge": "⚠️ This option provides ZERO physical protection. Full damage if cyclone strikes.",
                "impacts": {
                    "resilience_factor": 0.0,
                    "treasury": -2_000_000,
                    "carbon_intensity_delta": +1,
                    "revenue_delta": 0,
                    "reputation": -5,
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
                    "software_revenue_delta": +10_000_000,
                    "reputation": -20,
                    "contagion_spike": True,
                    "carbon_intensity_delta": +2,
                    "social_license_delta": -15,
                    "governance_risk_delta": +8,
                    "natural_capital_debt_delta": 0,
                },
            },
            "option_b": {"green_claim": "moderate", 
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
                    "reputation": +5,
                    "carbon_intensity_delta": -4,
                    "revenue_delta": +800_000,
                    "governance_risk_delta": -5,
                    "natural_capital_debt_delta": 0,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Quiet Patch",
                "description": "Silently fix the algorithm. Low cost but if leaked, devastating.",
                "flags_set": ["quiet_patch"],
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation": -5,
                    "governance_risk_delta": +10,
                    "carbon_intensity_delta": 0,
                    "revenue_delta": -200_000,
                    "social_license_delta": -3,
                    "natural_capital_debt_delta": 0,
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
            "option_a": {"green_claim": "full", 
                "label": "A",
                "title": "Full Circular Redesign",
                "description": "Redesign products for full disassembly and reuse.",
                "flags_set": ["circular_redesign"],
                "ci_routing": "scope3_weighted",  # I2: circular design reduces product-lifecycle (Scope3)
                "impacts": {
                    "treasury": -10_000_000,
                    "natural_capital_debt_delta": -12,
                    "reputation": +8,
                    "carbon_intensity_delta": -8,
                    "revenue_delta": +1_000_000,
                    "social_license_delta": +6,
                    "governance_risk_delta": -3,
                },
            },
            "option_b": {"green_claim": "full", 
                "label": "B",
                "title": "Extended Producer Responsibility",
                "description": "Fund take-back programs and recycling partnerships.",
                "flags_set": ["epr_program"],
                "ci_routing": "scope3_weighted",  # I2: EPR targets product-end-of-life Scope3
                "impacts": {
                    "treasury": -5_000_000,
                    "natural_capital_debt_delta": -6,
                    "reputation": +4,
                    "carbon_intensity_delta": -5,
                    "revenue_delta": +600_000,
                    "social_license_delta": +3,
                    "governance_risk_delta": -2,
                },
            },
            "option_c": {"green_claim": "moderate", 
                "label": "C",
                "title": "Waste-to-Energy Partnership",
                "description": (
                    "Build waste-to-energy facility. Unlocks high synergy "
                    "multiplier across BUs."
                ),
                "flags_set": ["waste_to_energy", "synergy_unlock"],
                "ci_routing": "scope3_weighted",  # I2: waste-to-energy primarily reduces operational Scope3
                "impacts": {
                    "treasury": -7_000_000,
                    # 0.30 is the SYNERGY MULTIPLIER boost and is current. The
                    # trailing claim that it is "harmonised to match M_R +0.30"
                    # went stale at STRAT-010, which cut the Synergy Strategic
                    # Premium to +0.15 (terminal_valuation.py:216) because the
                    # synergy OPEX saving already flows through terminal_ebitda.
                    # The two numbers are different quantities and are no longer
                    # meant to match. Corrected 2026-09-08.
                    "synergy_multiplier_boost": 0.30,
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
            "option_a": {"green_claim": "full", 
                "label": "A",
                "title": "Water Efficiency for All BUs",
                "description": "Equitable water-saving upgrades across all units.",
                "flags_set": ["water_efficiency_all"],
                "climate_framing": "ADAPTATION (equitable water resilience)",
                "impacts": {
                    "treasury": -12_000_000,
                    "water_dependency_delta": -20,
                    "social_license_delta": +5,
                    "carbon_intensity_delta": -3,
                    "revenue_delta": +700_000,
                    "reputation": +5,
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
                "climate_framing": "MALADAPTATION (inequitable resource allocation)",
                "impacts": {
                    "treasury": -4_000_000,
                    "social_license_severe_drop": True,
                    "social_license_drop_targets": ["pharma", "consumer_goods"],
                    "social_license_drop_amount": -25,
                    "carbon_intensity_delta": +2,
                    "revenue_delta": -400_000,
                    "reputation": -8,
                },
            },
            "option_c": {"green_claim": "moderate", 
                "label": "C",
                "title": "Desalination Mega-Project",
                "description": (
                    "Build a desalination plant. Massive cost ($30M) with a "
                    "2-round construction delay: the plant completes at the "
                    "Round 10 tick, when it reduces Natural Capital Debt by 30 "
                    "points and credits a single $5M revenue payment. Its "
                    "later operating years fall outside this game. Water "
                    "dependency falls by 40 immediately."
                ),
                "flags_set": ["desalination_built"],
                "climate_framing": "ADAPTATION (energy-intensive infrastructure)",
                "impacts": {
                    "treasury": -30_000_000,
                    "natural_capital_debt_delta": -30,
                    "water_dependency_delta": -40,
                    "carbon_intensity_delta": +5,  # Desalination is energy-intensive (~3-4 kWh/m³)
                    "revenue_delta": +300_000,
                    # Audit F-05: was 3. pending_capex_projects mature when
                    # rounds_remaining reaches 0 (engine._process_pending_projects)
                    # and the game ends at round 10, so a project queued at R8
                    # with 3 rounds to run matured never — the $5M promised in
                    # the copy was never credited. 2 matures at the R10 tick,
                    # exactly like the NCD drop queued beside it.
                    "generates_revenue": 5_000_000,
                    "payback_rounds": 2,
                    "reputation": +3,
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
            "strike_probability_override": 0.50,
            "regulatory_friction_enabled": True,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Immediate Closure",
                "description": (
                    "Close factories now for maximum cost savings. If Social "
                    "License is low, 50% chance of a strike that zeros revenue."
                ),
                "flags_set": ["immediate_closure"],
                "climate_framing": "MALADAPTATION (short-term extraction)",
                "impacts": {
                    "treasury": +5_000_000,
                    "social_license_delta": -20,
                    "reputation": -15,
                    "strike_risk": True,
                    "carbon_intensity_delta": +3,
                    "revenue_delta": -1_200_000,
                },
            },
            "option_b": {"green_claim": "moderate", 
                "label": "B",
                "title": "Managed Transition",
                "description": "2-year phase-out with retraining and severance packages.",
                "flags_set": ["managed_transition"],
                "climate_framing": "JUST TRANSITION (company-led)",
                "impacts": {
                    "treasury": -12_000_000,
                    "social_license_delta": +10,
                    "reputation": +8,
                    "carbon_intensity_delta": -4,
                    "revenue_delta": +600_000,
                },
            },
            "option_c": {"green_claim": "moderate", 
                "label": "C",
                "title": "Community Investment Fund",
                "description": (
                    "Create a $20M fund for community economic development "
                    "and green job training."
                ),
                "flags_set": ["community_fund"],
                "climate_framing": "JUST TRANSITION (community-led transformation)",
                "impacts": {
                    "treasury": -20_000_000,
                    "social_license_delta": +18,
                    "reputation": +12,
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
        "theme": "Year 5 Activist Ultimatum & Terminal Valuation",
        "crisis": {
            "id": "r10_grand_finale",
            "title": "Activist Ultimatum",
            "description": (
                "An activist investor consortium has acquired a blocking "
                "stake. They are demanding a strategic restructuring. The "
                "board must decide the company's Year 5 trajectory."
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
            "option_a": {"green_claim": "moderate", 
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
                    "reputation": +5,
                    "social_license_delta": +3,
                    "governance_risk_delta": -3,
                    "natural_capital_debt_delta": 0,
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
                    "reputation": +2,
                    "social_license_delta": -5,
                    "governance_risk_delta": +3,
                    "natural_capital_debt_delta": 0,
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
                    # C-6 (2026-08-31 audit): divest_all has NO consumer — by
                    # design ruling it stays declared but inert until its
                    # mechanics are specified (allow-listed in
                    # tests/test_engine_invariants.py). The Divest ending is
                    # carried by synergy_wipe, treasury, revenue_delta, the
                    # -12 social_license_delta and the +8 NCD below.
                    "divest_all": True,
                    "treasury": +25_000_000,
                    "synergy_wipe": True,
                    "carbon_intensity_delta": +2,
                    # §5.3: -2M PER UNIT = -$10M group (13.2%) — plausibly intentional for a
                    # divestment; awaiting design-owner confirmation. Allow-listed in
                    # tests/test_r2_materiality_audit.py (per-unit sanity sweep).
                    "revenue_delta": -2_000_000,
                    "reputation": -10,
                    "social_license_delta": -12,
                    "governance_risk_delta": +5,
                    "natural_capital_debt_delta": +8,
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

_merged_configs_cache = None
_overrides_mtime = None

def _get_merged_round_configs() -> dict[int, dict[str, Any]]:
    global _merged_configs_cache, _overrides_mtime
    
    # FIX AUDIT-019: Cache merged configs and only rebuild if the file changed
    current_mtime = OVERRIDES_FILE.stat().st_mtime if OVERRIDES_FILE.exists() else 0
    
    if _merged_configs_cache is not None and current_mtime == _overrides_mtime:
        return _merged_configs_cache
        
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
            
    _merged_configs_cache = base_configs
    _overrides_mtime = current_mtime
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


# ═════════════════════════════════════════════════════════════════
#  REC-5: TURNAROUND OPTION T
#  Dynamically injected when a team is in Survival Mode (Phase 1/2).
#  Trades short-term pain for accelerated recovery.
# ═════════════════════════════════════════════════════════════════

TURNAROUND_OPTION_T = {
    "label": "T",
    "title": "Emergency Restructuring",
    "description": (
        "Divest the worst-performing BU (lowest EBITDA margin) at 60% book value. "
        "All remaining BUs get a -15% OPEX haircut (forced efficiency). "
        "Reputation +10 (market rewards decisive action). "
        "Synergy multiplier drops 20% (fewer cross-selling opportunities). "
        "Sets turnaround_restructuring flag, enabling Phase 2 transition."
    ),
    "flags_set": ["turnaround_restructuring"],
    "is_turnaround_option": True,
    "impacts": {
        "divest_worst_bu": True,
        "divest_book_value_pct": 0.60,
        "opex_haircut_pct": -0.15,
        "reputation": +10,
        "synergy_multiplier_penalty": -0.20,
    },
    "visual_style": {
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
        "border_color": "#f59e0b",
        "badge": "⚡ TURNAROUND",
        "is_emergency": True,
    },
}


def get_round_config_with_turnaround(
    round_number: int,
    turnaround_phase: str = "none",
) -> dict[str, Any] | None:
    """
    Return round config with Option T injected if team is in survival mode.
    Option T is available during 'crisis' and 'stabilisation' phases.
    """
    cfg = get_round_config(round_number)
    if cfg is None:
        return None

    if turnaround_phase in ("crisis", "stabilisation"):
        cfg["options"]["option_t"] = copy.deepcopy(TURNAROUND_OPTION_T)
        cfg["turnaround_active"] = True
        cfg["turnaround_phase"] = turnaround_phase

    return cfg
