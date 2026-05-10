"""
Muressons Global Corporation - Terminal Valuation Module
Extracted from round_logic.py (STRAT-001) for independent testability,
What-If mode (STRAT-003), and cross-pathway normalization (STRAT-004).
Pure-function module: no I/O, no database access.
"""
from __future__ import annotations
from typing import Any
import math

# ── M_R Calculation ──
def calculate_mr(flags, avg_slo, avg_burnout, workforce_readiness,
                 synergy_multiplier, hr_investment_rounds=0, pathway_bonuses=None):
    mr = 1.0
    breakdown = {"base": 1.0}
    bonuses = []
    if flags.get("materiality_aligned"):
        mr += 0.10; breakdown["materiality_governance"] = 0.10
        bonuses.append("Materiality Governance (+0.10)")
    if flags.get("synergy_unlock") and synergy_multiplier >= 0.80:
        mr += 0.30; breakdown["synergy_bonus"] = 0.30
        bonuses.append("Synergy Excellence (+0.30)")
    if not flags.get("insurance_only") and not flags.get("electronics_water_priority") and not flags.get("civil_water_priority"):
        mr += 0.20; breakdown["resilience_bonus"] = 0.20
        bonuses.append("Resilience Champion (+0.20)")
    if flags.get("ethical_ai_overhaul"):
        mr += 0.15; breakdown["truth_premium"] = 0.15
        bonuses.append("Truth Premium (+0.15)")
    jt_scaling = 1.0
    if hr_investment_rounds > 0 and (flags.get("community_fund") or flags.get("managed_transition")):
        jt_scaling = round(min(1.5, 1.0 + hr_investment_rounds * 0.10), 2)
    if flags.get("community_fund"):
        b = round(0.18 * jt_scaling, 4); mr += b; breakdown["community_champion_bonus"] = b
        bonuses.append(f"Community Champion (+{b:.2f})")
    elif flags.get("managed_transition"):
        b = round(0.12 * jt_scaling, 4); mr += b; breakdown["just_transition_bonus"] = b
        bonuses.append(f"Just Transition (+{b:.2f})")
    if workforce_readiness >= 75:
        mr += 0.10; breakdown["workforce_bonus"] = 0.10
        bonuses.append("Workforce Excellence (+0.10)")
    if avg_burnout < 20:
        mr += 0.05; breakdown["wellbeing_bonus"] = 0.05
        bonuses.append("Wellbeing Champion (+0.05)")
    if flags.get("planet_expendable"):
        mr -= 0.20; breakdown["planet_expendable_penalty"] = -0.20
        bonuses.append("Planet Expendable Penalty (-0.20)")
    # BRSR NGRBC Track: ESG Alpha Dividend
    brsr_div = flags.get("brsr_net_positive_dividend", 0)
    if brsr_div:
        mr += brsr_div; breakdown["brsr_esg_alpha_dividend"] = brsr_div
        bonuses.append(f"BRSR ESG Alpha Dividend (+{brsr_div:.2f})")
    if avg_slo < 75:
        mr -= 0.40; breakdown["instability_discount"] = -0.40
        bonuses.append("Instability Discount (-0.40)")
    if pathway_bonuses:
        for k, v in pathway_bonuses.items():
            mr += v; breakdown[k] = v
            bonuses.append(f"{k.replace('_',' ').title()} ({v:+.2f})")
    mr = round(max(0.0, mr), 4)
    return {"mr": mr, "breakdown": breakdown, "jt_scaling_factor": jt_scaling,
            "bonuses_earned": bonuses, "max_achievable_mr": 2.33}


# ── SDG Multiplier (M_SDG) ──
def calculate_sdg_multiplier(sdg_impact_score: float = 0.0) -> dict:
    """
    M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25

    SDG Impact Score is accumulated from the Corporate SDG Side Track.
    Range: -11 (all Option C) to 105 (all Option A).
    M_SDG range: 0.97 to 1.26.
    Sessions without the SDG Side Track default to score=0 → M_SDG=1.0 (neutral).
    """
    m_sdg = round(1.0 + (sdg_impact_score / 100.0) * 0.25, 4)
    return {
        "m_sdg": m_sdg,
        "sdg_impact_score": sdg_impact_score,
        "sdg_track_active": sdg_impact_score != 0.0,
    }

# ── Terminal Value ──
def calculate_terminal_value(bus, mr, carbon_tax_per_ton=250.0,
                             exit_multiple=12.0, green_fund_balance=0.0,
                             is_advanced_climate=False, sdg_impact_score=0.0):
    gross = sum(bu["revenue_base"] - bu["opex_base"] for bu in bus)
    tco2e = round(sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1e6 for bu in bus), 1)
    cc = round(tco2e * carbon_tax_per_ton, 2)
    ebitda = round(gross - cc, 2)
    base = ebitda + (green_fund_balance if is_advanced_climate else 0)
    sdg_result = calculate_sdg_multiplier(sdg_impact_score)
    m_sdg = sdg_result["m_sdg"]
    tv = round(base * exit_multiple * mr * m_sdg, 2)
    return {"gross_profit": round(gross, 2), "tco2e_emissions": tco2e, "carbon_cost": cc,
            "carbon_tax_per_ton": carbon_tax_per_ton, "terminal_ebitda": ebitda,
            "green_fund_included": green_fund_balance if is_advanced_climate else 0,
            "exit_multiple": exit_multiple, "regenerative_multiple": mr,
            "sdg_multiplier": m_sdg, "sdg_impact_score": sdg_impact_score,
            "sdg_track_active": sdg_result["sdg_track_active"],
            "terminal_value": tv}

# ── Archetype Determination ──
_THRESHOLDS = {"regenerative_titan": 1.8, "derisked_safe_haven": 1.2, "fragile_giant": 0.8}
_ARCHETYPES = {
    "regenerative_titan": {"title": "The Regenerative Titan", "icon": "\U0001f331",
        "gradient": "linear-gradient(135deg, #10b981, #059669)"},
    "derisked_safe_haven": {"title": "The De-risked Safe-Haven", "icon": "\U0001f3e6",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)"},
    "fragile_giant": {"title": "The Fragile Giant", "icon": "\u26a0\ufe0f",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"},
    "stranded_relic": {"title": "The Stranded Relic", "icon": "\U0001f480",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"},
    "turnaround_manager": {"title": "The Turnaround Manager", "icon": "🔧",
        "gradient": "linear-gradient(135deg, #8b5cf6, #6d28d9)"},
}

def determine_archetype(mr, thresholds=None, custom_archetypes=None, survival_mode=False):
    t = thresholds or _THRESHOLDS
    a = custom_archetypes or _ARCHETYPES
    # Survival mode: M_R capped at 0.80, always maps to turnaround_manager
    if survival_mode:
        mr = min(mr, 0.80)
        return {"key": "turnaround_manager", **a.get("turnaround_manager", _ARCHETYPES["turnaround_manager"]),
                "mr_capped": True, "original_mr": mr}
    if mr >= t.get("regenerative_titan", 1.8): key = "regenerative_titan"
    elif mr >= t.get("derisked_safe_haven", 1.2): key = "derisked_safe_haven"
    elif mr >= t.get("fragile_giant", 0.8): key = "fragile_giant"
    else: key = "stranded_relic"
    return {"key": key, **a.get(key, _ARCHETYPES["stranded_relic"])}

# ── STRAT-003: What-If Mode ──
def what_if_terminal(bus, base_flags, flag_overrides, avg_slo, avg_burnout,
                     workforce_readiness, synergy_multiplier, hr_investment_rounds=0,
                     carbon_tax_per_ton=250.0, exit_multiple=12.0,
                     green_fund_balance=0.0, is_advanced_climate=False):
    base_mr = calculate_mr(base_flags, avg_slo, avg_burnout, workforce_readiness,
                           synergy_multiplier, hr_investment_rounds)
    base_tv = calculate_terminal_value(bus, base_mr["mr"], carbon_tax_per_ton,
                                       exit_multiple, green_fund_balance, is_advanced_climate)
    merged = {**base_flags, **flag_overrides}
    wi_mr = calculate_mr(merged, avg_slo, avg_burnout, workforce_readiness,
                         synergy_multiplier, hr_investment_rounds)
    wi_tv = calculate_terminal_value(bus, wi_mr["mr"], carbon_tax_per_ton,
                                     exit_multiple, green_fund_balance, is_advanced_climate)
    return {
        "baseline": {"mr": base_mr["mr"], "mr_breakdown": base_mr["breakdown"],
                     "terminal_value": base_tv["terminal_value"],
                     "archetype": determine_archetype(base_mr["mr"])},
        "what_if": {"mr": wi_mr["mr"], "mr_breakdown": wi_mr["breakdown"],
                    "terminal_value": wi_tv["terminal_value"],
                    "archetype": determine_archetype(wi_mr["mr"]), "flags_changed": flag_overrides},
        "delta": {"mr_change": round(wi_mr["mr"] - base_mr["mr"], 4),
                  "tv_change": round(wi_tv["terminal_value"] - base_tv["terminal_value"], 2),
                  "archetype_changed": determine_archetype(wi_mr["mr"])["key"] != determine_archetype(base_mr["mr"])["key"]},
    }

# ── STRAT-004: Cross-Pathway M_R Normalization ──
PATHWAY_DIFFICULTY = {
    "activist_ultimatum": 1.00, "climate_black_swan": 1.15,
    "stakeholder_revolt": 1.10, "hostile_takeover": 1.20, "regulatory_shutdown": 1.12,
}

def normalize_mr_for_leaderboard(raw_mr, ending_pathway, custom_difficulty=None):
    d = custom_difficulty or PATHWAY_DIFFICULTY
    c = d.get(ending_pathway, 1.0)
    n = round(raw_mr * c, 4)
    return {"raw_mr": raw_mr, "pathway": ending_pathway, "difficulty_coefficient": c,
            "normalized_mr": n, "archetype_raw": determine_archetype(raw_mr)["key"],
            "archetype_normalized": determine_archetype(n)["key"]}

# ── STRAT-002: Flag Dependency Graph ──
FLAG_DEPENDENCY_GRAPH = [
    {"source_round": 1, "flag": "deep_audit_completed", "target_round": 4, "effect": "Halves crisis severity (40 vs 80)", "category": "governance"},
    {"source_round": 1, "flag": "electronics_blindspot", "target_round": 4, "effect": "Doubles crisis severity to 80", "category": "risk"},
    {"source_round": 2, "flag": "materiality_aligned", "target_round": 10, "effect": "+0.10 M_R Governance bonus", "category": "governance"},
    {"source_round": 2, "flag": "blockchain_traceability", "target_round": 8, "effect": "Prevents supply chain scandal", "category": "supply_chain"},
    {"source_round": 3, "flag": "early_decarboniser", "target_round": 7, "effect": "+0.10 synergy multiplier bonus", "category": "climate"},
    {"source_round": 3, "flag": "greenwash_risk", "target_round": 5, "effect": "Triggers greenwash if inv<15%", "category": "risk"},
    {"source_round": 5, "flag": "insurance_only", "target_round": 10, "effect": "BLOCKS +0.20 Resilience M_R bonus", "category": "climate"},
    {"source_round": 6, "flag": "ethical_ai_overhaul", "target_round": 10, "effect": "+0.15 Truth Premium M_R", "category": "governance"},
    {"source_round": 6, "flag": "ai_monetised", "target_round": 7, "effect": "EU AI Act costs from R7+", "category": "risk"},
    {"source_round": 7, "flag": "synergy_unlock", "target_round": 10, "effect": "+0.30 Synergy M_R + enables Opt A", "category": "strategic"},
    {"source_round": 8, "flag": "electronics_water_priority", "target_round": 10, "effect": "BLOCKS +0.20 Resilience M_R bonus", "category": "risk"},
    {"source_round": 9, "flag": "community_fund", "target_round": 10, "effect": "+0.18 Community Champion M_R (xJT)", "category": "social"},
    {"source_round": 9, "flag": "managed_transition", "target_round": 10, "effect": "+0.12 Just Transition M_R (xJT)", "category": "social"},
    # BRSR NGRBC Track
    {"source_round": "BRSR-1", "flag": "brsr_pioneer", "target_round": 10, "effect": "Enables BRSR Pioneer archetype path", "category": "governance"},
    {"source_round": "BRSR-1", "flag": "governance_fragility", "target_round": "BRSR-5", "effect": "Triggers Whistleblower Governance Leak (-$2.5M)", "category": "governance"},
    {"source_round": "BRSR-4", "flag": "brsr_greenwash_risk", "target_round": "BRSR-4", "effect": "Triggers SEBI Show-Cause Notice (-12 Reputation)", "category": "risk"},
    {"source_round": "BRSR-5", "flag": "brsr_net_positive_dividend", "target_round": 10, "effect": "+0.05 ESG Alpha Dividend M_R (BRSR Pioneer)", "category": "governance"},
]

def get_flag_dependency_graph(active_flags=None):
    graph = []
    for dep in FLAG_DEPENDENCY_GRAPH:
        entry = {**dep}
        if active_flags is not None:
            entry["status"] = "active" if dep["flag"] in active_flags else "inactive"
        graph.append(entry)
    cats = {}
    for e in graph:
        cats.setdefault(e.get("category", "other"), []).append(e)
    return {"dependencies": graph, "by_category": cats, "total_flags": len(graph),
            "active_count": sum(1 for e in graph if e.get("status") == "active") if active_flags else None}
