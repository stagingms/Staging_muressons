"""
Muressons Global Corporation — Ending Pathway Configurations
Defines alternate R10 crisis scenarios, options, M_R modifiers,
foreshadowing events, and archetype overrides per pathway.

Pathways are selected by facilitator/god-mode at session creation.
Players never see the pathway name — only indirect hints (R5-R8).
"""

from __future__ import annotations
from typing import Any
import copy
import random as _rng


# ═══════════════════════════════════════════════════════════════
#  ALL AVAILABLE ENDING PATHWAYS
# ═══════════════════════════════════════════════════════════════

ALL_PATHWAY_IDS = [
    "activist_ultimatum",
    "climate_black_swan",
    "stakeholder_revolt",
    "hostile_takeover",
    "regulatory_shutdown",
]

# All pathways fully implemented
IMPLEMENTED_PATHWAYS = [
    "activist_ultimatum",
    "climate_black_swan",
    "stakeholder_revolt",
    "hostile_takeover",
    "regulatory_shutdown",
]

PATHWAY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "activist_ultimatum": {
        "name": "Activist Ultimatum",
        "description": "An activist consortium acquires a blocking stake and forces a strategic review. The board must choose between integration, spin-off, or full divestiture.",
    },
    "climate_black_swan": {
        "name": "Climate Black Swan",
        "description": "A cascading climate event triggers stranded asset write-downs and investor flight. The company faces an existential question: can it decarbonise fast enough to survive?",
    },
    "stakeholder_revolt": {
        "name": "Stakeholder Revolt",
        "description": "Community protests, employee strikes, and supplier boycotts converge. Social capital has eroded to the point where the company's social licence to operate is revoked.",
    },
    "hostile_takeover": {
        "name": "Hostile Takeover",
        "description": "A competitor launches an unsolicited bid, exploiting weak governance and low market capitalisation. The board must defend or negotiate.",
    },
    "regulatory_shutdown": {
        "name": "Regulatory Shutdown",
        "description": "A major regulatory authority issues a compliance notice threatening operational shutdown. Years of deferred governance catch up in a single enforcement action.",
    },
}


def resolve_pathway(pathway_id: str) -> str:
    """Resolve 'random' to a concrete pathway, or validate the ID."""
    if pathway_id == "random":
        return _rng.choice(IMPLEMENTED_PATHWAYS)
    if pathway_id in ALL_PATHWAY_IDS:
        return pathway_id
    return "activist_ultimatum"  # fallback


# ═══════════════════════════════════════════════════════════════
#  FORESHADOWING EVENTS (R5–R8)
#  Injected into post_tick events when foreshadowing_enabled=True.
#  Each entry: round → list of news items.
# ═══════════════════════════════════════════════════════════════

FORESHADOWING: dict[str, dict[int, list[dict]]] = {

    "activist_ultimatum": {
        6: [{"type": "market_intel", "headline": "Activist Fund Files 13D — 4.9% Stake Acquired",
             "body": "Regulatory filings reveal an activist hedge fund has been quietly accumulating shares in Muressons Group."}],
        7: [{"type": "news_release", "headline": "Analyst Note: 'Muressons Ripe for Restructuring'",
             "body": "Goldman Sachs initiates coverage with a note suggesting conglomerate discount could be unlocked through break-up."}],
        8: [{"type": "market_intel", "headline": "Blocking Stake Reached — Board Engagement Imminent",
             "body": "The activist consortium now holds a blocking stake. Proxy fight preparations are underway."}],
    },

    "climate_black_swan": {
        5: [{"type": "news_release", "headline": "IPCC Special Report: 1.5°C Overshoot Now 'Likely'",
             "body": "The latest IPCC assessment indicates a >66% probability of temporary 1.5°C overshoot by 2030. Carbon markets react sharply."}],
        6: [{"type": "market_intel", "headline": "Carbon Futures Surge 40% — EU ETS Hits Record",
             "body": "European carbon allowances breach €120/tonne as speculators price in accelerated phase-out schedules."}],
        7: [{"type": "news_release", "headline": "Insurance Consortium Warns: 'Uninsurable Assets by 2035'",
             "body": "Lloyd's of London publishes a systemic risk report flagging carbon-intensive industrial assets as approaching uninsurability thresholds."}],
        8: [{"type": "market_intel", "headline": "ALERT: 1.5°C Threshold Breached — Carbon Markets in Turmoil",
             "body": "Global mean temperature crosses the 1.5°C threshold. Carbon spot prices triple overnight. Stranded asset write-downs begin across the sector.",
             "flag": "climate_threshold_breached"}],
    },

    "stakeholder_revolt": {
        5: [{"type": "news_release", "headline": "Glassdoor Review: 'Muressons Culture is Toxic'",
             "body": "An anonymous employee review goes viral, citing burnout, lack of career development, and management indifference."}],
        6: [{"type": "news_release", "headline": "Community Coalition Forms Against Industrial Operations",
             "body": "Local councils near Muressons manufacturing sites form a unified coalition demanding environmental and social accountability."}],
        7: [{"type": "market_intel", "headline": "Consumer Boycott Hashtag Gains 2M Impressions",
             "body": "#BoycottMuressons trends on social media after an investigative documentary airs on prime-time television."}],
        8: [{"type": "news_release", "headline": "#MuressonsExposed — Triple Stakeholder Ultimatum",
             "body": "Employees, communities, and consumer groups issue coordinated demands. Union leaders threaten industrial action.",
             "flag": "social_media_campaign"}],
    },

    "hostile_takeover": {
        6: [{"type": "market_intel", "headline": "Unusual Share Volume Detected in Muressons Stock",
             "body": "Trading volume spikes 300% with no public catalyst. Dark pool analysis suggests institutional accumulation."}],
        7: [{"type": "news_release", "headline": "PE Firm 'Cerberus Capital' Denies Acquisition Interest",
             "body": "A carefully worded denial from Cerberus Capital's spokesperson fails to reassure the market."}],
        8: [{"type": "market_intel", "headline": "Cerberus Files Preliminary Offer with Regulator",
             "body": "Cerberus Capital has formally notified the competition authority of its intent to acquire Muressons Group.",
             "flag": "takeover_rumour"}],
    },

    "regulatory_shutdown": {
        5: [{"type": "news_release", "headline": "EU Adopts Corporate Sustainability Due Diligence Directive",
             "body": "The CSDDD enters into force, requiring large companies to identify and address adverse human rights and environmental impacts."}],
        6: [{"type": "market_intel", "headline": "Sector Peers Face €50M+ CSDDD Compliance Costs",
             "body": "Industry analysis reveals compliance costs significantly exceed initial estimates. Several peers issue profit warnings."}],
        7: [{"type": "news_release", "headline": "Whistleblower Contacts Environmental Regulator",
             "body": "A former Muressons employee has filed a formal complaint with the environmental protection agency, triggering an investigation."}],
        8: [{"type": "news_release", "headline": "Regulator Issues Show Cause Notice to Muressons",
             "body": "The environmental agency demands Muressons demonstrate CSDDD compliance within 90 days or face operational restrictions.",
             "flag": "whistleblower_investigation"}],
    },
}


# ═══════════════════════════════════════════════════════════════
#  R10 CRISIS & OPTIONS PER PATHWAY
# ═══════════════════════════════════════════════════════════════

PATHWAY_R10_CONFIGS: dict[str, dict[str, Any]] = {

    # ── Climate Black Swan ──────────────────────────────────────
    "climate_black_swan": {
        "crisis": {
            "id": "r10_climate_black_swan",
            "title": "The Stranded Asset Reckoning",
            "description": (
                "The world has entered a climate emergency. Carbon pricing has "
                "tripled. Insurance markets are refusing to underwrite high-exposure "
                "assets. A cascading climate catastrophe — mega-drought, Arctic "
                "methane release, and a carbon Minsky Moment — demands an "
                "immediate strategic response."
            ),
            "icon": "🌋",
        },
        "special_rules": {
            "carbon_tax_per_ton": 750,  # Tripled from standard 250
            "exit_multiple": 12.0,      # Modified by avg CI (see logic)
            "synergy_gate_threshold": 80,
            "exit_multiple_ci_haircut": True,  # Enable CI-based haircut
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Emergency Decarbonisation",
                "description": (
                    "Accelerated transition to net-zero operations. All BU carbon "
                    "intensities halved. NCD reduced by 50%. Early movers (avg CI < 25) "
                    "earn the Climate Leader bonus (+0.30 M_R)."
                ),
                "flags_set": ["emergency_decarb"],
                "impacts": {
                    "treasury": -20_000_000,
                    "carbon_intensity_halve": True,
                    "ncd_halve": True,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Climate Adaptation Portfolio",
                "description": (
                    "Restructure around climate-resilient BUs only. BUs with CI > 40 "
                    "are divested at fire-sale prices (50% book value). Remaining BUs "
                    "receive reallocation capital."
                ),
                "flags_set": ["climate_adaptation"],
                "impacts": {
                    "divest_high_ci": True,
                    "ci_divest_threshold": 40,
                    "reallocation_per_bu": 3_000_000,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Deny & Delay",
                "description": (
                    "Lobby against carbon regulation. Avoid transition costs but "
                    "carbon tax triples, NCD doubles, and exit multiple drops to 6×. "
                    "A bet against the climate consensus."
                ),
                "flags_set": ["climate_deny"],
                "impacts": {
                    "treasury": +5_000_000,
                    "carbon_tax_triple": True,
                    "ncd_double": True,
                    "exit_multiple_override": 6.0,
                    "mr_penalty": -0.40,
                },
            },
        },
        "archetype_overrides": {
            "regenerative_titan": {
                "title": "The Climate Pioneer", "icon": "🌍",
                "gradient": "linear-gradient(135deg, #059669, #047857)",
            },
            "derisked_safe_haven": {
                "title": "The Adapted Enterprise", "icon": "🛡️",
                "gradient": "linear-gradient(135deg, #0ea5e9, #0284c7)",
            },
            "fragile_giant": {
                "title": "The Stranded Giant", "icon": "🏭",
                "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
            },
            "stranded_relic": {
                "title": "The Fossil Relic", "icon": "🦴",
                "gradient": "linear-gradient(135deg, #78716c, #57534e)",
            },
        },
    },

    # ── Stakeholder Revolt ──────────────────────────────────────
    "stakeholder_revolt": {
        "crisis": {
            "id": "r10_stakeholder_revolt",
            "title": "The Social Reckoning",
            "description": (
                "Employees, communities, and consumers have issued simultaneous "
                "ultimatums. Unionised workers demand burnout protections. Local "
                "councils threaten to revoke operating licences. A consumer boycott "
                "is reducing revenue. The board must respond to the triple "
                "stakeholder revolt."
            ),
            "icon": "🪧",
        },
        "special_rules": {
            "carbon_tax_per_ton": 250,
            "exit_multiple": 12.0,
            "synergy_gate_threshold": 80,
            "social_collapse_threshold_slo": 40,
            "social_collapse_threshold_burnout": 70,
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Total Stakeholder Compact",
                "description": (
                    "Sign a legally binding stakeholder charter: guaranteed living "
                    "wages, community benefit agreements, and product quality "
                    "standards. If avg SLO ≥ 70 AND avg burnout < 30: +0.35 M_R "
                    "Social Regeneration bonus. Revenue +15% (brand loyalty)."
                ),
                "flags_set": ["stakeholder_compact"],
                "impacts": {
                    "treasury": -18_000_000,
                    "revenue_boost_pct": 0.15,
                    "social_regeneration_gate": True,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Selective Appeasement",
                "description": (
                    "Address the loudest stakeholder group only (auto-selects "
                    "based on worst metric). Fixes one dimension but remaining "
                    "groups escalate (−10 SLO for unaddressed)."
                ),
                "flags_set": ["selective_appeasement"],
                "impacts": {
                    "treasury": -8_000_000,
                    "selective_fix": True,
                    "unaddressed_slo_penalty": -10,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Corporate Hardball",
                "description": (
                    "Threaten to relocate operations overseas. All BU SLO: −25. "
                    "All BU burnout: +20. If any BU SLO hits 0, that BU is "
                    "shuttered. Short-term treasury gain but devastating social cost."
                ),
                "flags_set": ["corporate_hardball"],
                "impacts": {
                    "treasury": +10_000_000,
                    "slo_all_penalty": -25,
                    "burnout_all_increase": +20,
                    "shutter_zero_slo": True,
                    "mr_penalty": -0.30,
                },
            },
        },
        "archetype_overrides": {
            "regenerative_titan": {
                "title": "The People's Corporation", "icon": "🤝",
                "gradient": "linear-gradient(135deg, #8b5cf6, #7c3aed)",
            },
            "derisked_safe_haven": {
                "title": "The Responsible Employer", "icon": "🏢",
                "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
            },
            "fragile_giant": {
                "title": "The Contested Enterprise", "icon": "⚡",
                "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
            },
            "stranded_relic": {
                "title": "The Social Pariah", "icon": "🚫",
                "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)",
            },
        },
    },

    # ── Hostile Takeover ────────────────────────────────────────
    "hostile_takeover": {
        "crisis": {
            "id": "r10_hostile_takeover",
            "title": "The Corporate Raider",
            "description": (
                "Cerberus Capital has launched a hostile tender offer for "
                "Muressons Group at a 15% premium to current share price. "
                "The PE firm plans to break up the conglomerate and sell "
                "individual BUs. The board has 48 hours to respond. Your "
                "strategic track record will determine whether shareholders "
                "side with management or the raider."
            ),
            "icon": "🦈",
        },
        "special_rules": {
            "carbon_tax_per_ton": 250,
            "exit_multiple": 12.0,
            "synergy_gate_threshold": 80,
            "takeover_premium": 0.15,
            "defence_synergy_threshold": 1.3,  # Synergy ≥ 1.3 → defence viable
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "White Knight Defence",
                "description": (
                    "Seek a friendly acquirer (strategic partner) who will "
                    "preserve the integrated strategy. If synergy_multiplier ≥ 1.3 "
                    "AND treasury > $30M: +0.25 M_R Strategic Integration bonus. "
                    "Revenue −5% (integration friction)."
                ),
                "flags_set": ["white_knight_defence"],
                "impacts": {
                    "treasury": -15_000_000,
                    "revenue_drag_pct": -0.05,
                    "white_knight": True,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Poison Pill + Crown Jewel Lock-Up",
                "description": (
                    "Deploy anti-takeover defences: dilutive share issuance "
                    "and lock-up agreements on top-performing BUs. Preserves "
                    "independence but increases debt. Treasury −$25M, exit "
                    "multiple reduced to 10× (debt overhang)."
                ),
                "flags_set": ["poison_pill"],
                "impacts": {
                    "treasury": -25_000_000,
                    "exit_multiple_override": 10.0,
                    "poison_pill": True,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Accept the Bid",
                "description": (
                    "Accept Cerberus's offer. Shareholders get the premium, "
                    "but the conglomerate will be broken up. Exit multiple "
                    "locked at 8× (breakup discount). M_R capped at 1.0 "
                    "(no regenerative value recognised)."
                ),
                "flags_set": ["bid_accepted"],
                "impacts": {
                    "treasury": +20_000_000,
                    "exit_multiple_override": 8.0,
                    "mr_cap": 1.0,
                    "mr_penalty": -0.50,
                },
            },
        },
        "archetype_overrides": {
            "regenerative_titan": {
                "title": "The Untouchable Fortress", "icon": "🏰",
                "gradient": "linear-gradient(135deg, #6366f1, #4f46e5)",
            },
            "derisked_safe_haven": {
                "title": "The Defended Platform", "icon": "🛡️",
                "gradient": "linear-gradient(135deg, #0ea5e9, #0284c7)",
            },
            "fragile_giant": {
                "title": "The Vulnerable Target", "icon": "🎯",
                "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
            },
            "stranded_relic": {
                "title": "The Broken Conglomerate", "icon": "💔",
                "gradient": "linear-gradient(135deg, #78716c, #57534e)",
            },
        },
    },

    # ── Regulatory Shutdown ─────────────────────────────────────
    "regulatory_shutdown": {
        "crisis": {
            "id": "r10_regulatory_shutdown",
            "title": "The Compliance Reckoning",
            "description": (
                "The environmental regulator has completed its investigation "
                "triggered by the whistleblower complaint. Muressons faces "
                "a Notice of Violation under the CSDDD, citing systematic "
                "failures in supply chain due diligence. The regulator has "
                "the power to impose operational restrictions, heavy fines, "
                "or a consent decree requiring third-party monitoring."
            ),
            "icon": "⚖️",
        },
        "special_rules": {
            "carbon_tax_per_ton": 350,  # Elevated regulatory scrutiny
            "exit_multiple": 12.0,
            "synergy_gate_threshold": 80,
            "compliance_cost_per_bu": 4_000_000,
            "fine_base": 30_000_000,
            "profile_thresholds": {
                "regenerative_titan": 1.8,
                "derisked_safe_haven": 1.2,
                "fragile_giant": 0.8,
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Remediation Programme",
                "description": (
                    "Voluntarily exceed CSDDD requirements: implement full "
                    "supply chain traceability, publish impact assessments, "
                    "and establish a community remediation fund. If ethical "
                    "score > 7 AND no scandal flags: +0.30 M_R Regulatory "
                    "Exemplar bonus. Heavy upfront cost ($4M per BU)."
                ),
                "flags_set": ["full_remediation"],
                "impacts": {
                    "compliance_cost_all_bus": True,
                    "regulatory_exemplar_gate": True,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Negotiate Consent Decree",
                "description": (
                    "Negotiate a settlement with the regulator: accept a "
                    "$30M fine and third-party monitoring for 3 years. "
                    "Operations continue but exit multiple reduced to 10× "
                    "(governance discount). Carbon tax increases to $350/t."
                ),
                "flags_set": ["consent_decree"],
                "impacts": {
                    "treasury": -30_000_000,
                    "exit_multiple_override": 10.0,
                    "consent_decree": True,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Contest the Ruling",
                "description": (
                    "Challenge the regulator in court. If successful (low "
                    "chance if ethical score < 5): no fine. If "
                    "unsuccessful: double fine ($60M), operations suspended "
                    "for worst-performing BU, exit multiple to 7×. "
                    "Reputation −30."
                ),
                "flags_set": ["contest_ruling"],
                "impacts": {
                    "legal_challenge": True,
                    "legal_costs": -10_000_000,
                    "mr_penalty": -0.35,
                },
            },
        },
        "archetype_overrides": {
            "regenerative_titan": {
                "title": "The Compliance Champion", "icon": "🏅",
                "gradient": "linear-gradient(135deg, #059669, #047857)",
            },
            "derisked_safe_haven": {
                "title": "The Regulated Enterprise", "icon": "📋",
                "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
            },
            "fragile_giant": {
                "title": "The Monitored Entity", "icon": "👁️",
                "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
            },
            "stranded_relic": {
                "title": "The Suspended Operation", "icon": "🚫",
                "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)",
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  PATHWAY-SPECIFIC M_R BONUS CALCULATORS
# ═══════════════════════════════════════════════════════════════

def calc_climate_black_swan_mr(
    bus: list[dict], gs: dict, all_flags: set, extra: dict,
    baseline_ci: float | None = None,
) -> float:
    """
    Calculate additional M_R bonuses/penalties for Climate Black Swan pathway.

    Returns the total M_R modifier (positive or negative) to ADD to the
    standard M_R calculation.
    """
    mr_delta = 0.0
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)

    # +0.30: Climate Leader — avg CI < 25 at R10
    if avg_ci < 25:
        mr_delta += 0.30
        extra["mr_climate_leader_bonus"] = True
        extra["mr_climate_leader_avg_ci"] = round(avg_ci, 2)

    # +0.20: Adaptation Premium — nature_based_resilience AND early_decarboniser
    if "nature_based_resilience" in all_flags and "early_decarboniser" in all_flags:
        mr_delta += 0.20
        extra["mr_adaptation_premium"] = True

    # +0.15: Carbon Transition Bonus — CI reduced ≥ 40% from R1 baseline
    if baseline_ci and baseline_ci > 0:
        ci_reduction_pct = (baseline_ci - avg_ci) / baseline_ci
        if ci_reduction_pct >= 0.40:
            mr_delta += 0.15
            extra["mr_carbon_transition_bonus"] = True
            extra["mr_carbon_transition_pct"] = round(ci_reduction_pct * 100, 1)

    # −0.40: Stranded Asset Penalty — avg CI > 50 at R10
    if avg_ci > 50:
        mr_delta -= 0.40
        extra["mr_stranded_asset_penalty"] = True
        extra["mr_stranded_asset_avg_ci"] = round(avg_ci, 2)

    # −0.20: Shadow Board — planet_expendable flag (R5 rejection)
    if "planet_expendable" in all_flags:
        mr_delta -= 0.20
        extra["mr_shadow_board_planet_expendable"] = True
        extra["mr_shadow_board_penalty_note"] = (
            "Ecosystem resilience undermined: R5 Shadow Board rejection of "
            "environmental logic increased climate vulnerability cascade."
        )

    extra["pathway_mr_delta"] = round(mr_delta, 4)
    extra["pathway_avg_ci"] = round(avg_ci, 2)
    return round(mr_delta, 4)


def calc_climate_exit_multiple(bus: list[dict], base_multiple: float = 12.0) -> float:
    """
    Climate Black Swan: Exit multiple is haircut based on avg CI.
    Exit_Multiple = 12 × (1 - max(0, (avg_CI - 25) × 0.01))
    """
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)
    haircut = max(0.0, (avg_ci - 25) * 0.01)
    return round(base_multiple * (1.0 - haircut), 2)


def calc_stakeholder_revolt_mr(
    bus: list[dict], gs: dict, all_flags: set, extra: dict,
) -> float:
    """
    Calculate additional M_R bonuses/penalties for Stakeholder Revolt pathway.
    """
    mr_delta = 0.0
    avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)
    readiness = gs.get("workforce_readiness", 50.0)

    # +0.35: Social Regeneration — avg SLO ≥ 70 AND avg burnout < 30
    if avg_slo >= 70 and avg_burnout < 30:
        mr_delta += 0.35
        extra["mr_social_regeneration_bonus"] = True

    # +0.15: Employee Champion — avg burnout < 25 AND readiness ≥ 70
    if avg_burnout < 25 and readiness >= 70:
        mr_delta += 0.15
        extra["mr_employee_champion_bonus"] = True

    # +0.15: Community Trust — avg SLO ≥ 80
    if avg_slo >= 80:
        mr_delta += 0.15
        extra["mr_community_trust_bonus"] = True

    # −0.50: Social Collapse — avg SLO < 40 OR avg burnout > 70
    if avg_slo < 40 or avg_burnout > 70:
        mr_delta -= 0.50
        extra["mr_social_collapse_penalty"] = True

    extra["pathway_mr_delta"] = round(mr_delta, 4)
    extra["pathway_avg_slo"] = round(avg_slo, 2)
    extra["pathway_avg_burnout"] = round(avg_burnout, 2)
    return round(mr_delta, 4)


def calc_hostile_takeover_mr(
    bus: list[dict], gs: dict, all_flags: set, extra: dict,
) -> float:
    """
    Calculate additional M_R bonuses/penalties for Hostile Takeover pathway.
    """
    mr_delta = 0.0
    synergy = gs.get("synergy_multiplier", 1.0)
    treasury = gs.get("corporate_treasury", 0)
    total_revenue = sum(bu.get("revenue_base", 0) for bu in bus)
    total_opex = sum(bu.get("opex_base", 0) for bu in bus)
    ebitda_margin = (total_revenue - total_opex) / max(total_revenue, 1)

    # +0.25: Strategic Integration — synergy ≥ 1.3 AND treasury > $30M
    if synergy >= 1.3 and treasury > 30_000_000:
        mr_delta += 0.25
        extra["mr_strategic_integration_bonus"] = True
        extra["mr_strategic_integration_synergy"] = round(synergy, 3)

    # +0.20: Fortress Premium — EBITDA margin > 20% AND no scandal flags
    scandal_flags = {"scandal_erupted", "whistleblower_investigation", "greenwash_exposed"}
    if ebitda_margin > 0.20 and not all_flags.intersection(scandal_flags):
        mr_delta += 0.20
        extra["mr_fortress_premium"] = True
        extra["mr_fortress_ebitda_margin"] = round(ebitda_margin * 100, 1)

    # +0.15: Shareholder Value — synergy ≥ 1.5 (conglomerate premium)
    if synergy >= 1.5:
        mr_delta += 0.15
        extra["mr_conglomerate_premium"] = True

    # −0.40: Vulnerable Target — synergy < 1.1 AND treasury < $10M
    if synergy < 1.1 and treasury < 10_000_000:
        mr_delta -= 0.40
        extra["mr_vulnerable_target_penalty"] = True

    # −0.20: Shadow Board — shareholder_alienated flag (R5 rejection)
    if "shareholder_alienated" in all_flags:
        mr_delta -= 0.20
        extra["mr_shadow_board_shareholder_alienated"] = True
        extra["mr_shadow_board_penalty_note"] = (
            "Investor confidence eroded: R5 Shadow Board rejection of "
            "shareholder logic accelerated hostile acquisition thesis."
        )

    extra["pathway_mr_delta"] = round(mr_delta, 4)
    extra["pathway_synergy"] = round(synergy, 3)
    extra["pathway_ebitda_margin"] = round(ebitda_margin * 100, 1)
    return round(mr_delta, 4)


def calc_regulatory_shutdown_mr(
    bus: list[dict], gs: dict, all_flags: set, extra: dict,
) -> float:
    """
    Calculate additional M_R bonuses/penalties for Regulatory Shutdown pathway.
    """
    mr_delta = 0.0
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)
    avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
    group_rep = gs.get("group_reputation", 50.0)

    # Calculate ethical score: combination of CI, SLO, reputation
    ethical_score = (avg_slo * 0.3 + (100 - avg_ci) * 0.3 + group_rep * 0.4) / 10
    extra["pathway_ethical_score"] = round(ethical_score, 2)

    # +0.30: Regulatory Exemplar — ethical_score > 7 AND no scandal flags
    scandal_flags = {"scandal_erupted", "greenwash_exposed", "whistleblower_investigation"}
    if ethical_score > 7 and not all_flags.intersection(scandal_flags):
        mr_delta += 0.30
        extra["mr_regulatory_exemplar_bonus"] = True

    # +0.20: Supply Chain Transparency — scope_3_transparency flag set
    if "scope_3_transparency" in all_flags or "full_remediation" in all_flags:
        mr_delta += 0.20
        extra["mr_supply_chain_transparency"] = True

    # +0.15: Proactive Compliance — ethical_score > 6 AND avg SLO > 60
    if ethical_score > 6 and avg_slo > 60:
        mr_delta += 0.15
        extra["mr_proactive_compliance"] = True

    # −0.45: Regulatory Failure — ethical_score < 4
    if ethical_score < 4:
        mr_delta -= 0.45
        extra["mr_regulatory_failure_penalty"] = True

    # −0.25: Shadow Board — governance_fragility flag (R5 rejection)
    if "governance_fragility" in all_flags:
        mr_delta -= 0.25
        extra["mr_shadow_board_governance_fragility"] = True
        extra["mr_shadow_board_penalty_note"] = (
            "Governance risk amplified: R5 Shadow Board rejection of "
            "governance logic increased regulatory scrutiny cascade."
        )

    extra["pathway_mr_delta"] = round(mr_delta, 4)
    extra["pathway_avg_ci"] = round(avg_ci, 2)
    extra["pathway_group_rep"] = round(group_rep, 2)
    return round(mr_delta, 4)


# ═══════════════════════════════════════════════════════════════
#  FORESHADOWING KPI CALCULATORS
# ═══════════════════════════════════════════════════════════════

def calc_stranded_asset_exposure(bus: list[dict]) -> float:
    """SAE = avg(carbon_intensity) × total_NCD / 1000"""
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)
    total_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus)
    return round(avg_ci * total_ncd / 1000, 2)


def calc_social_capital_index(bus: list[dict], gs: dict) -> float:
    """SCI = (avg_SLO × 0.4) + ((100 - avg_burnout) × 0.3) + (group_reputation × 0.3)"""
    avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)
    group_rep = gs.get("group_reputation", 50.0)
    return round(avg_slo * 0.4 + (100 - avg_burnout) * 0.3 + group_rep * 0.3, 2)


def calc_takeover_vulnerability(bus: list[dict], gs: dict) -> float:
    """TVI = 100 - (synergy_multiplier × 30) - (treasury_M × 5) - (EBITDA_margin × 50)"""
    synergy = gs.get("synergy_multiplier", 1.0)
    treasury_m = gs.get("corporate_treasury", 0) / 1_000_000
    total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
    total_opex = sum(bu.get("opex_base", 0) for bu in bus)
    margin = (total_rev - total_opex) / max(total_rev, 1)
    tvi = 100 - (synergy * 30) - (min(treasury_m, 10) * 5) - (margin * 50)
    return round(max(0, min(100, tvi)), 1)


def calc_compliance_risk_index(bus: list[dict], gs: dict) -> float:
    """CRI = (avg_CI × 0.4) + ((100 - avg_SLO) × 0.3) + ((100 - group_reputation) × 0.3)"""
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bus) / max(len(bus), 1)
    avg_slo = sum(bu.get("social_license_score", 0) for bu in bus) / max(len(bus), 1)
    group_rep = gs.get("group_reputation", 50.0)
    return round(avg_ci * 0.4 + (100 - avg_slo) * 0.3 + (100 - group_rep) * 0.3, 1)


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

def get_pathway_r10_config(pathway_id: str) -> dict[str, Any] | None:
    """Return a deep copy of the R10 config for a given pathway."""
    cfg = PATHWAY_R10_CONFIGS.get(pathway_id)
    return copy.deepcopy(cfg) if cfg else None


def get_pathway_r10_options(pathway_id: str) -> dict[str, Any]:
    """Return a deep copy of just the R10 options for a pathway."""
    cfg = PATHWAY_R10_CONFIGS.get(pathway_id, {})
    return copy.deepcopy(cfg.get("options", {}))


def get_pathway_archetype_overrides(pathway_id: str) -> dict[str, dict]:
    """Return archetype overrides for a pathway."""
    cfg = PATHWAY_R10_CONFIGS.get(pathway_id, {})
    return copy.deepcopy(cfg.get("archetype_overrides", {}))


def get_foreshadowing_events(
    pathway_id: str, round_number: int,
) -> list[dict]:
    """Return foreshadowing events for a pathway at a given round."""
    pathway_events = FORESHADOWING.get(pathway_id, {})
    return copy.deepcopy(pathway_events.get(round_number, []))
