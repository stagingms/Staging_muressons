from __future__ import annotations
"""
Muressons Global Corporation — Healthcare Edition Round Configurations
"""

from typing import Any
import copy

HEALTHCARE_ROUND_CONFIGS = {
    # ── Round 1: Foundations ────────────────────────────────────
    1: {
        "title": "Foundations",
        "theme": "Compliance Baseline",
        "crisis": {
            "id": "r1_healthcare",
            "title": "Medical Waste Compliance Review",
            "description": (
                "Regulators have highlighted gaps in our medical waste disposal protocols across the hospital network. "
                "We must choose our compliance and expansion posture."
            ),
            "icon": "🏥",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Fast-Track Bed Expansion",
                "description": "Ignore the waste review and funnel all capital into adding 500 new clinic beds. Triggers regulatory scrutiny.",
                "flags_set": ["waste_compliance_gap", "compliance_gap"],
                "impacts": {
                    "treasury": -2_500_000,
                    "reputation": -5,
                    "carbon_intensity_delta": +5,
                    "revenue_delta": +2_000_000,
                    "bed_capacity_increase": +5.0,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Strict Compliance Audit",
                "description": "Halt expansion to overhaul sterilisation and waste protocols. Lowers risk but delays revenue.",
                "flags_set": ["deep_audit_completed"],
                "impacts": {
                    "treasury": -5_000_000,
                    "reputation": +5,
                    "carbon_intensity_delta": -2,
                    "revenue_delta": -500_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Outsource Waste Management",
                "description": "Hire a low-cost third-party vendor to handle disposal. Cheap, but risks supply chain opacity.",
                "flags_set": ["outsource_opacity"],
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation": 0,
                    "carbon_intensity_delta": +2,
                    "revenue_delta": +500_000,
                },
            },
        },
    },

    # ── Round 2: Materiality Gate ────────────────────────────────
    2: {
        "title": "Double Materiality",
        "theme": "Capital Allocation",
        "crisis": {
            "id": "r2_healthcare",
            "title": "The Strategic Crossroads",
            "description": "Patient inflow is surging. Do we dedicate capital towards physical ICU infrastructure or digital health triage (Telehealth)?",
            "icon": "⚖️",
        },
        "validation_rules": {
            "cfo_materiality_gate": True,
            "high_impact_nodes": [
                "round_2_hospitals",
                "round_2_clinics",
                "round_2_specialised_care",
                "round_2_telehealth"
            ],
        },
        "special_rules": {
            "materiality_accuracy_treasury_bonus": True,
            "accuracy_threshold": 90,
            "accuracy_bonus_amount": 2_000_000,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Heavy ICU Expansion",
                "description": "Massive capital into physical hospital beds. Increases natural capital debt and water usage.",
                "flags_set": ["heavy_icu_capex"],
                "impacts": {
                    "treasury": -8_000_000,
                    "natural_capital_debt_delta": +8,
                    "carbon_intensity_delta": +8,
                    "revenue_delta": +1_500_000,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Digital Triage Pilot",
                "description": "Shift funding to Muressons Digital Health to divert non-critical patients. Asset-light but risks misdiagnosis.",
                "flags_set": ["digital_triage_active"],
                "impacts": {
                    "treasury": -3_000_000,
                    "natural_capital_debt_delta": +2,
                    "carbon_intensity_delta": -1,
                    "revenue_delta": +500_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Balanced Regional Clinics",
                "description": "Build decentralized satellite clinics. Moderate costs, good community impact.",
                "flags_set": ["regional_clinics_built"],
                "impacts": {
                    "treasury": -5_000_000,
                    "natural_capital_debt_delta": +5,
                    "carbon_intensity_delta": +3,
                    "revenue_delta": +800_000,
                },
            },
        },
    },

    # ── Round 3: Scope 3 Epidemic ────────────────────────────────
    3: {
        "title": "Supply Chain Fragility",
        "theme": "Scope 3 Crisis",
        "crisis": {
            "id": "r3_healthcare",
            "title": "PPE & Plastics Shortage",
            "description": "A major disruption in Southeast Asia has severed our supply of single-use surgical plastics.",
            "icon": "📦",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Air-Freight Emergency Supply",
                "description": "Charter jets to fly in emergency stock. Huge carbon spike and massive short-term cost.",
                "flags_set": ["air_freight_emergency"],
                "impacts": {
                    "treasury": -7_500_000,
                    "reputation": +2,
                    "carbon_intensity_delta": +12,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Triage & Rationing",
                "description": "Ration existing supplies, canceling elective surgeries. Hospitals and Specialised Care lose revenue; Telehealth surges as patients divert digitally.",
                "flags_set": ["cancelled_electives"],
                "impacts": {
                    "treasury": 0,
                    "reputation": -8,
                    "carbon_intensity_delta": -2,
                    "elective_surgery_cancel": True,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Local Sterile Manufacturing",
                "description": "Fund an expensive local initiative to sterilize and reuse equipment. High capex, immense long-term resilience.",
                "flags_set": ["local_sterile_resilience", "early_decarboniser"],
                "impacts": {
                    "treasury": -10_000_000,
                    "reputation": +10,
                    "natural_capital_debt_delta": -5,
                    "carbon_intensity_delta": -5,
                },
            },
        },
    },

    # ── Round 4: The Blindspot ──────────────────────────────────
    4: {
        "title": "The Blindspot",
        "theme": "Algorithmic Triage Failure",
        "crisis": {
            "id": "r4_healthcare",
            "title": "Digital Health Malpractice",
            "description": "Telehealth's AI triage system systematically deprioritized high-risk groups, leading to severe clinical outcomes.",
            "icon": "⚠️",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Deny & Litigate",
                "description": "Fight the PR battle in court to protect the algorithm. Triggers a massive contagion spike in hospital trust.",
                "flags_set": ["telehealth_litigation"],
                "impacts": {
                    "treasury": -2_000_000,
                    "reputation": -15,
                    "contagion_spike": True,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Algorithmic Recall & Settlement",
                "description": "Pull the system offline for overhaul and settle with affected families. Very costly upfront. ⚠️ NOTE: This settlement does NOT earn the Truth Premium (+0.15 M_R) at terminal valuation — that requires the full Transparent AI Overhaul in Round 6.",
                "flags_set": ["telehealth_overhaul"],
                "impacts": {
                    "treasury": -12_000_000,
                    "reputation": -2,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Human-in-the-Loop Downgrade",
                "description": "Revert to human clinician overrides on all AI flags. Skyrockets staff burnout and OPEX.",
                "flags_set": ["human_triage_override"],
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation": -5,
                    "telehealth_opex_delta": +2_500_000,
                    "burnout_spike": True,
                    "burnout_spike_amount": 10,
                },
            },
        },
    },

    # ── Round 5: Climate Stochastic ─────────────────────────────
    5: {
        "title": "Climate Stress Test",
        "theme": "Infrastructure Resilience",
        "crisis": {
            "id": "r5_healthcare",
            "title": "Extreme Weather Impact",
            "description": "A category 4 cyclone is approaching our densest network of hospitals.",
            "icon": "🌪️",
        },
        # FACILITATOR NOTE: In Healthcare, Option A is insurance-only (cheapest).
        # In Narrative Crisis (corporate), Option C is insurance-only.
        # The flag 'insurance_only' is set on the SAME mechanic (reactive-only posture)
        # but the option LETTER is inverted. When running mixed HC + NC cohorts,
        # explain that the options are ordered by healthcare triage priority
        # (reactive → evacuate → harden) rather than by cost.
        "facilitator_note": (
            "⚠️ FLAG INVERSION vs Corporate: In NC, insurance_only is Option C (cheapest). "
            "In Healthcare, it is Option A. The flag targets the same mechanic (no resilience investment) "
            "but the letter ordering reflects clinical triage priority. When debriefing mixed cohorts, "
            "emphasize the MECHANIC not the letter."
        ),
        "options": {
            "option_a": {
                "label": "A",
                "title": "Reactive Insurance Only",
                "description": (
                    "Rely completely on our insurance premiums. Zero resilience protection if a direct hit occurs. "
                    "⚠️ This BLOCKS the Resilience M_R bonus (+0.20) at terminal valuation."
                ),
                "flags_set": ["insurance_only"],
                "impacts": {
                    "treasury": 0,
                    "resilience_factor": 0.0,
                    "carbon_intensity_delta": +1,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Emergency Evacuations",
                "description": "Pre-emptively evacuate vulnerable patients to specialized care centers. High immediate cost, moderate resilience.",
                "flags_set": ["patient_evacuation"],
                "impacts": {
                    "treasury": -4_500_000,
                    "resilience_factor": 0.50,
                    "carbon_intensity_delta": +2,
                    "natural_capital_debt_delta": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Hardened Grid Continuity",
                "description": "Invest deeply in microgrids and storm-grade infrastructure. Maximum physical protection.",
                "flags_set": ["hardened_hospital_grid"],
                "impacts": {
                    "treasury": -8_000_000,
                    "resilience_factor": 0.85,
                    "carbon_intensity_delta": +3,
                    "natural_capital_debt_delta": +8,
                },
            },
        },
        "special_rules": {
            "base_damage": 18_000_000,
            "stochastic_threshold": 0.75,
        }
    },

    # ── Round 6: AI Bias ────────────────────────────────────────
    6: {
        "title": "Digital Transformation",
        "theme": "AI Ethics in Oncology",
        "crisis": {
            "id": "r6_healthcare",
            "title": "Oncology Predictive Bias",
            "description": "Specialised Care's predictive diagnostic AI is showing a 22% false-negative rate for minority patients.",
            "icon": "🤖",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Quiet Patching",
                "description": "Silently alter the weights over 6 months to avoid inciting panic.",
                "flags_set": ["quiet_patch_oncology"],
                "impacts": {
                    "treasury": 0,
                    "reputation": -18,
                    "governance_risk_delta": +15,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Transparent AI Overhaul",
                "description": "Publicly disclose the flaw, halt the system, and collaborate with ethical AI boards. Expensive but builds immense trust.",
                "flags_set": ["ethical_ai_overhaul"],
                "impacts": {
                    "treasury": -8_000_000,
                    "social_license_delta": +15,
                    "governance_risk_delta": -10,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Scrap & Replace Vendor",
                "description": "Fire the software vendor and buy a competitor's module. ⚠️ Governance risk increases (+5) due to vendor transition risk: migration complexity, data portability gaps, and new vendor due diligence overhead.",
                "flags_set": ["vendor_replacement"],
                "impacts": {
                    "treasury": -4_500_000,
                    "governance_risk_delta": +5,
                },
            },
        },
    },

    # ── Round 7: Circularity ────────────────────────────────────
    7: {
        "title": "Resource Circularity",
        "theme": "Waste Innovation",
        "crisis": {
            "id": "r7_healthcare",
            "title": "The Sterile Waste Mountain",
            "description": "Regulators propose a punitive tax on medical incinerators. Our hospitals are the largest polluters in 3 states.",
            "icon": "♻️",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Lobby Against Tax",
                "description": "Fund a massive lobbying campaign to exempt healthcare facilities. Increases NCD and destroys social license.",
                "flags_set": ["incinerator_lobbying"],
                "impacts": {
                    "treasury": -2_000_000,
                    "natural_capital_debt_delta": +20,
                    "social_license_delta": -12,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Pay the Tax",
                "description": "Absorb the incoming OPEX hit without changing operations.",
                "flags_set": [],
                "impacts": {
                    "treasury": 0,
                    "natural_capital_debt_delta": +10,
                    "opex_penalty": +3_500_000,
                    "opex_penalty_targets": ["hospitals", "specialised_care"],
                },
            },
            "option_c": {
                "label": "C",
                "title": "Circular Instrument Hubs",
                "description": "Fund 'circular hubs' that autoclave and remanufacture instruments at scale. (Unlocks synergy multiplier)",
                "flags_set": ["circular_hubs", "synergy_unlock"],
                "impacts": {
                    "treasury": -14_000_000,
                    "natural_capital_debt_delta": -25,
                    "reputation": +12,
                    "synergy_multiplier_boost": +0.30,
                },
            },
        },
    },

    # ── Round 8: Blue Stress ────────────────────────────────────
    8: {
        "title": "Blue Stress",
        "theme": "Water Security",
        "crisis": {
            "id": "r8_healthcare",
            "title": "Municipal Water Collapse",
            "description": "A severe drought has forced municipal water shut-offs. Hospitals cannot run sterilisation or HVAC cooling.",
            "icon": "💧",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Truck In Private Water",
                "description": "Pay exorbitant surge pricing to tanker in water simply to keep operating rooms open.",
                "flags_set": ["water_trucking"],
                "impacts": {
                    "treasury": -9_000_000,
                    "carbon_intensity_delta": +4,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Invoke Emergency Priority",
                "description": "Use our legal standing as critical infrastructure to force the city to cut residential water in our favor. ⚠️ Blocks the Resilience M_R bonus (+0.20) at terminal valuation.",
                "flags_set": ["civil_water_priority"],
                "impacts": {
                    "treasury": 0,
                    "reputation": -15,
                    "social_license_delta": -12,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Closed-Loop Retrofit",
                "description": "Expedite retrofitting hospitals with closed-loop greywater reclamation. Massive upfront cost.",
                "flags_set": ["closed_loop_water"],
                "impacts": {
                    "treasury": -16_000_000,
                    "natural_capital_debt_delta": -15,
                    "water_dependency_delta": -30,
                },
            },
        },
    },

    # ── Round 9: Just Transition ────────────────────────────────
    9: {
        "title": "Just Transition",
        "theme": "Workforce Automation",
        "crisis": {
            "id": "r9_healthcare",
            "title": "The Nursing Strike",
            "description": "In response to mass robotic-pharmacy deployments, the nursing union threatens a total strike across the primary network.",
            "icon": "🤝",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Bust the Strike",
                "description": "Hire incredibly expensive agency lock-out staff to break the union. Destroys morale.",
                "flags_set": ["union_busted"],
                "impacts": {
                    "treasury": -8_000_000,
                    "reputation": -10,
                    "burnout_spike": True,
                    "burnout_spike_amount": 10,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Halt Automation",
                "description": "Scrap the robotics deployment to appease the union. A colossal waste of prior R&D capital. Earns +0.12 M_R (Just Transition bonus).",
                "flags_set": ["managed_transition"],
                "impacts": {
                    "treasury": -6_000_000,
                    "revenue_delta": -2_500_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Clinician Retraining Hub",
                "description": "Fund a massive retraining program elevating nurses into tech-triage and oversight roles. Earns +0.18 M_R (Community Champion bonus).",
                "flags_set": ["clinician_retraining", "community_fund"],
                "impacts": {
                    "treasury": -12_000_000,
                    "reputation": +15,
                    "burnout_recovery": True,
                },
            },
        },
    },

    # ── Round 10: Grand Finale ──────────────────────────────────
    10: {
        "title": "Grand Finale",
        "theme": "The Regenerative Multiple",
        "crisis": {
            "id": "r10_healthcare",
            "title": "Legacy & Terminal Valuation",
            "description": "The board requires a definitive choice on our final market posture before going public with the acquisition.",
            "icon": "🏁",
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Aggressive Consolidation",
                "description": "Slash OPEX across the board to pad EBITDA. Grants +10% treasury boost but devastates patient outcomes (-15) and spikes staff burnout (+20).",
                "flags_set": ["consolidation"],
                "impacts": {
                    "opex_slash": True,
                    "opex_slash_pct": 0.15,
                    "treasury_bonus_pct": 0.10,
                    "patient_outcomes_penalty": -15,
                    "burnout_spike": True,
                    "burnout_spike_amount": 20,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Divest the Clinics",
                "description": "Spin off the weakest primary-care clinics down to zero, boosting group margin percentages.",
                "flags_set": ["divest_weakest"],
                "impacts": {
                    "spinoff_weakest_bu": True,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Universal Care Mandate",
                "description": "Codify patient outcome standards above margins into the corporate charter. Explicitly preserves synergy multiplier and boosts social license. No immediate cash, but maximum multiple protection at terminal valuation.",
                "flags_set": ["universal_care_charter"],
                "impacts": {
                    "synergy_preserve": True,
                    "social_license_boost": +5,
                },
            },
        },
        # Healthcare terminal valuation uses higher exit multiples (premium M&A sector)
        # and lower carbon tax per tonne (regulated infrastructure exemptions)
        "special_rules": {
            "carbon_tax_per_ton": 180,       # Lower than generic ($250) — healthcare regulatory exemptions
            "exit_multiple": 14.0,           # Higher than generic (12×) — premium healthcare M&A
            "synergy_gate_threshold": 80,
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
            "healthcare_archetypes": {
                "regenerative_titan": {
                    "title": "Community Health Champion",
                    "icon": "💚",
                    "description": "A beacon of regenerative healthcare. Your network has rebuilt community trust, achieved clinical excellence, and delivered sustainable patient outcomes.",
                    "gradient": "linear-gradient(135deg, #10b981, #059669)",
                },
                "derisked_safe_haven": {
                    "title": "Resilient Care System",
                    "icon": "🛡️",
                    "description": "A well-managed healthcare network with solid fundamentals. You balanced financial sustainability with patient care, though bold innovation was sacrificed.",
                    "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)",
                },
                "fragile_giant": {
                    "title": "Profit-First Network",
                    "icon": "💰",
                    "description": "A financially viable but brittle system. Short-term margins were prioritised over long-term resilience, leaving the network vulnerable to future shocks.",
                    "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
                },
                "stranded_relic": {
                    "title": "Fragile Ward",
                    "icon": "🏚️",
                    "description": "A healthcare system in structural decline. Chronic underinvestment, staff burnout, and community distrust have eroded the foundation of care delivery.",
                    "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)",
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

import json
from pathlib import Path
import os

from runtime_paths import config_file as _config_file
OVERRIDES_FILE = _config_file("decision_overrides.json")  # 3.1: durable location
_merged_configs_cache = None
_overrides_mtime = None

def _get_merged_healthcare_configs() -> dict[int, dict[str, Any]]:
    global _merged_configs_cache, _overrides_mtime
    
    current_mtime = OVERRIDES_FILE.stat().st_mtime if OVERRIDES_FILE.exists() else 0
    
    if _merged_configs_cache is not None and current_mtime == _overrides_mtime:
        return _merged_configs_cache
        
    base_configs = copy.deepcopy(HEALTHCARE_ROUND_CONFIGS)
    if OVERRIDES_FILE.exists():
        try:
            with open(OVERRIDES_FILE, "r") as f:
                data = json.load(f)
            legacy_overrides = data.get("healthcare", {})
            for round_num_str, cfg_override in legacy_overrides.items():
                round_num = int(round_num_str)
                if round_num in base_configs:
                    _deep_merge(base_configs[round_num], cfg_override)
        except Exception as e:
            print(f"Error loading decision overrides: {e}")
            
    _merged_configs_cache = base_configs
    _overrides_mtime = current_mtime
    return base_configs

def get_healthcare_round_config(round_number: int) -> dict[str, Any] | None:
    cfg = _get_merged_healthcare_configs().get(round_number)
    return copy.deepcopy(cfg) if cfg else None

def get_healthcare_round_options(round_number: int) -> dict[str, Any]:
    cfg = _get_merged_healthcare_configs().get(round_number, {})
    return copy.deepcopy(cfg.get("options", {}))

