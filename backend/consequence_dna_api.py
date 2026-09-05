"""
Consequence DNA Visualizer — Backend Data Aggregation
Builds the complete Sankey diagram data model by combining:
  - FLAG_DEPENDENCY_GRAPH (terminal_valuation.py)
  - Meadows leverage point analysis (meadows_leverage.py)
  - Autonomous agent state (autonomous_agents.py)
  - Shadow board audit state
  - Live M_R projection
"""
from __future__ import annotations
from typing import Any

from terminal_valuation import (
    FLAG_DEPENDENCY_GRAPH,
    calculate_mr,
    determine_archetype,
    get_flag_dependency_graph,
    max_achievable_mr_for,
)


# ── Decision labels per round (human-readable for Sankey Col 1) ──
DECISION_LABELS = {
    1: {"option_a": "R1: Comprehensive Audit", "option_b": "R1: Deep Supply Chain Audit", "option_c": "R1: Surface Scan (Phased)"},
    2: {"option_a": "R2: Full Double Materiality", "option_b": "R2: Partial CSRD Compliance", "option_c": "R2: Minimal Compliance"},
    3: {"option_a": "R3: Internal Decarbonisation", "option_b": "R3: Green Bond Financing", "option_c": "R3: Carbon Offsets Only"},
    4: {"option_a": "R4: Industry Coalition", "option_b": "R4: Solo Recovery", "option_c": "R4: Aggressive Cost Cut"},
    5: {"option_a": "R5: Hard Engineering", "option_b": "R5: Nature-Based Solutions", "option_c": "R5: Insurance Only"},
    6: {"option_a": "R6: Monetise AI Data", "option_b": "R6: Ethical AI Overhaul", "option_c": "R6: Hybrid AI Approach"},
    7: {"option_a": "R7: Full Circular Economy", "option_b": "R7: Industrial Symbiosis", "option_c": "R7: Waste-to-Energy"},
    8: {"option_a": "R8: Community Water Priority", "option_b": "R8: Factory Water Priority", "option_c": "R8: Balanced Water Strategy"},
    9: {"option_a": "R9: Immediate Closure", "option_b": "R9: Managed Transition", "option_c": "R9: Community Trust Fund"},
    10: {"option_a": "R10: Universal Care Mandate", "option_b": "R10: Targeted Restructure", "option_c": "R10: Status Quo"},
}

# SDG Side Track decision labels
SDG_DECISION_LABELS = {
    1: {"option_a": "ST1: Forensic PAI Audit", "option_b": "ST1: Materiality Review", "option_c": "ST1: Standard Disclosure"},
    2: {"option_a": "ST2: Living Wage Commitment", "option_b": "ST2: Phased Parity", "option_c": "ST2: Operational Hardball"},
    3: {"option_a": "ST3: Full Circular Transform", "option_b": "ST3: Targeted Sourcing", "option_c": "ST3: Spot-Market Compliance"},
    4: {"option_a": "ST4: Nature-Positive Transform", "option_b": "ST4: Targeted Conservation", "option_c": "ST4: Market Deferral"},
    5: {"option_a": "ST5: Integrated Value Creation", "option_b": "ST5: Strategic Integration", "option_c": "ST5: Separate Supplement"},
}

# BRSR NGRBC Side Track decision labels
BRSR_DECISION_LABELS = {
    1: {"option_a": "BRSR1: Radical Transparency", "option_b": "BRSR1: Standard Compliance", "option_c": "BRSR1: Reactive Disclosure"},
    2: {"option_a": "BRSR2: Living Wage Standard", "option_b": "BRSR2: Safety & POSH Focus", "option_c": "BRSR2: Statutory Minimums"},
    3: {"option_a": "BRSR3: Circular Symbiosis & ZLD", "option_b": "BRSR3: Efficiency Upgrades", "option_c": "BRSR3: Regulatory Minimums"},
    4: {"option_a": "BRSR4: Multi-Tier Assurance", "option_b": "BRSR4: Tier-1 Screening", "option_c": "BRSR4: Self-Assessment Only"},
    5: {"option_a": "BRSR5: Integrated Report", "option_b": "BRSR5: Strategic BRSR", "option_c": "BRSR5: Compliance File"},
}


# ── Red DNA: Option C Consequence Nodes (Constriction/Leak) ──
# These create visually distinct red nodes in the Consequence DNA visualizer
# when players choose Option C paths that create material risk.
OPTION_C_RED_DNA = {
    # Core simulation Option C consequences
    "electronics_blindspot": {"type": "constriction", "label": "⛔ Audit Blindspot", "icon": "⛔"},
    "materiality_ignored":   {"type": "leak", "label": "💧 Budget Clawback", "icon": "💧"},
    "greenwash_risk":        {"type": "leak", "label": "💧 Greenwash Exposure", "icon": "💧"},
    "deny_and_deflect":      {"type": "constriction", "label": "⛔ Brain Drain", "icon": "⛔"},
    "insurance_only":        {"type": "constriction", "label": "⛔ Resilience Void", "icon": "⛔"},
    "ai_monetised":          {"type": "leak", "label": "💧 AI Monetisation Risk", "icon": "💧"},
    "immediate_closure":     {"type": "constriction", "label": "⛔ Community Revolt", "icon": "⛔"},
    # SDG Side Track Option C consequences
    "pai_blindspot":         {"type": "constriction", "label": "⛔ PAI Blindspot", "icon": "⛔"},
    "operational_hardball":   {"type": "constriction", "label": "⛔ Strike Risk Spike", "icon": "⛔"},
    "credibility_gap_penalty": {"type": "leak", "label": "💧 Credibility Gap", "icon": "💧"},
    # BRSR Side Track Option C consequences
    "governance_fragility":  {"type": "constriction", "label": "⛔ Governance Fragility", "icon": "⛔"},
    "brsr_greenwash_risk":   {"type": "leak", "label": "💧 Value Chain Risk Write-down", "icon": "💧"},
}

# Leverage point levels per decision (from meadows_leverage.py round_lp_map)
DECISION_LP_MAP = {
    1: {"option_a": 5, "option_b": 5, "option_c": 12},
    2: {"option_a": 3, "option_b": 5, "option_c": 12},
    3: {"option_a": 8, "option_b": 5, "option_c": 12},
    5: {"option_a": 10, "option_b": 4, "option_c": 11},
    7: {"option_a": 7, "option_b": 10, "option_c": 7},
    9: {"option_a": 12, "option_b": 2, "option_c": 2},
}

# ── Metric shift descriptors for Sankey Col 3 ──
FLAG_METRIC_SHIFTS = {
    "electronics_blindspot": [{"metric": "crisis_severity", "label": "Crisis Severity ×2", "delta": 40}],
    "materiality_aligned": [{"metric": "governance", "label": "Governance Credibility ↑", "delta": 10}],
    "materiality_partial": [{"metric": "governance", "label": "Governance Credibility ↑ (partial)", "delta": 5}],
    "greenwash_risk": [{"metric": "reputation", "label": "Greenwash Vulnerability", "delta": -8}],
    "early_decarboniser": [{"metric": "carbon_intensity", "label": "Carbon Intensity < 35", "delta": -15}],
    "insurance_only": [{"metric": "resilience", "label": "Resilience Locked Out", "delta": -20}],
    "ethical_ai_overhaul": [{"metric": "governance", "label": "AI Governance ↑", "delta": 15}],
    "ai_monetised": [{"metric": "compliance", "label": "EU AI Act Costs ↑", "delta": -10}],
    "synergy_unlock": [{"metric": "synergy", "label": "Synergy Excellence", "delta": 30}],
    "community_fund": [{"metric": "social_license", "label": "Community SLO ↑", "delta": 18}],
    "managed_transition": [{"metric": "social_license", "label": "Just Transition SLO ↑", "delta": 12}],
    "shareholder_alienated": [{"metric": "investor_confidence", "label": "Investor Confidence ↓", "delta": -15}],
    "planet_expendable": [{"metric": "ecosystem", "label": "Ecosystem Resilience ↓", "delta": -12}],
    "governance_fragility": [{"metric": "regulatory", "label": "Regulatory Scrutiny ↑", "delta": -10}],
    "civil_water_priority": [{"metric": "social_license", "label": "Social License Protected", "delta": 10}],
    "electronics_water_priority": [{"metric": "production", "label": "Production Continuity", "delta": 5}],
    "blockchain_traceability": [{"metric": "supply_chain", "label": "Supply Chain Transparency", "delta": 10}],
    # SDG Side Track flags
    "sdg_integrity_unlocked": [{"metric": "governance", "label": "SDG Integrity Verified", "delta": 10}],
    "pai_blindspot": [{"metric": "crisis_severity", "label": "PAI Blindspot → R2 Severity ×2", "delta": 40}],
    "sdg_living_wage": [{"metric": "social_license", "label": "Living Wage SLO ↑", "delta": 15}],
    "circular_leader": [{"metric": "natural_capital", "label": "Circular Economy Leader", "delta": -15}],
    "nature_positive": [{"metric": "natural_capital", "label": "Nature-Positive Commitment", "delta": -15}],
    "operational_hardball": [{"metric": "workforce", "label": "Strike Risk ↑ / Burnout ↑", "delta": -20}],
    "sdg_integrated_reporting": [{"metric": "governance", "label": "Integrated Reporting (+0.35 M_R)", "delta": 35}],
    "credibility_gap_penalty": [{"metric": "reputation", "label": "ESG Credibility Gap", "delta": -8}],
    # BRSR Track flags
    "brsr_pioneer": [{"metric": "governance", "label": "BRSR Governance ↑", "delta": 15}],
    "brsr_core_assured": [{"metric": "supply_chain", "label": "Supply Visibility +40", "delta": 40}],
    "brsr_living_wage": [{"metric": "social_license", "label": "Living Wage SLO ↑", "delta": 20}],
    "sdg_12_leadership": [{"metric": "natural_capital", "label": "NCD ↓", "delta": -15}],
    "brsr_circular_symbiosis": [{"metric": "natural_capital", "label": "ZLD Implemented", "delta": -20}],
    "brsr_net_positive_dividend": [{"metric": "terminal_value", "label": "ESG Alpha Dividend (+0.05 M_R)", "delta": 5}],
    "brsr_greenwash_crisis": [{"metric": "reputation", "label": "SEBI Show-Cause Notice (-12 Rep)", "delta": -12}],
    "brsr_governance_crisis": [{"metric": "treasury", "label": "Governance Leak (-$2.5M)", "delta": -2500000}],
    "spcb_show_cause": [{"metric": "regulatory", "label": "SPCB Closure Notice (Pharma BU)", "delta": -15}],
    # Shadow Board SDG-enhanced penalties
    "planet_expendable": [{"metric": "ecosystem", "label": "Ecosystem Resilience ↓ (M_R -0.20)", "delta": -20}],
}

# Agent → flow mapping for constriction nodes
AGENT_FLOW_MAP = {
    "the_regulator": {"flow_source": "governance", "flow_target": "treasury", "leak_label": "⚖️ Regulatory Fine: 4% Revenue"},
    "the_journalist": {"flow_source": "strategy", "flow_target": "revenue", "leak_label": "📰 Viral Exposé: Reputation Drain"},
    "the_institutional_investor": {"flow_source": "financial", "flow_target": "terminal_value", "leak_label": "📉 Divestment: CoC Increase"},
    "the_community_activist": {"flow_source": "social_license", "flow_target": "operations", "leak_label": "🏘️ Court Injunction: $3M Treasury"},
    "the_gen_z_employee": {"flow_source": "hr", "flow_target": "productivity", "leak_label": "✊ Talent Exodus: 15% OPEX Surge"},
}


def compute_per_decision_impact(decision_history: list[dict]) -> list[dict]:
    """
    For each decision, compute:
      Impact = Base_Decision_Value × (13 - Leverage_Point_Level)

    Shallow (LP 12–10): 'Tweaking Parameters'
    Medium  (LP 9–4):   'Adjusting Feedback Loops'
    Deep    (LP 3–1):   'Shifting Organizational Goals'
    """
    results = []
    for decision in decision_history:
        rnum = decision.get("round_number", 0)
        choice = decision.get("primary_choice", "")
        if not choice or rnum not in DECISION_LP_MAP:
            lp_level = 12
        else:
            lp_level = DECISION_LP_MAP.get(rnum, {}).get(choice, 12)

        base_value = decision.get("capex_total", 1_000_000) / 1_000_000
        impact = round(base_value * (13 - lp_level), 2)

        if lp_level <= 3:
            category = "deep"
            category_label = "Shifting Organizational Goals"
        elif lp_level <= 9:
            category = "medium"
            category_label = "Adjusting Feedback Loops"
        else:
            category = "shallow"
            category_label = "Tweaking Parameters"

        label = DECISION_LABELS.get(rnum, {}).get(choice, f"R{rnum}: {choice}")

        results.append({
            "round": rnum,
            "choice": choice,
            "label": label,
            "leverage_level": lp_level,
            "impact_score": impact,
            "category": category,
            "category_label": category_label,
        })
    return results


def _extract_decision_history(global_state: dict, history: list[dict]) -> list[dict]:
    """Extract decision history from round snapshots."""
    decisions = []
    flags = global_state.get("active_event_flags", {})

    for snap in history:
        rnum = snap.get("round_number", 0)
        snap_decs = snap.get("decisions", [])
        choice = ""
        capex = 1_000_000
        
        if snap_decs:
            choice = snap_decs[0].get("choice_selected", "")
            capex = sum(d.get("capex", 0) for d in snap_decs)

        if not choice:
            gs = snap.get("global_state", {})
            snap_flags = gs.get("active_event_flags", {})
            choice = snap_flags.get(f"r{rnum}_choice", "")
            capex = snap_flags.get(f"r{rnum}_total_capex", 1_000_000)

        decisions.append({
            "round_number": rnum,
            "primary_choice": choice,
            "capex_total": capex,
        })
    return decisions


def build_consequence_dna_data(
    session_id: str,
    global_state: dict,
    bu_states: list[dict],
    history: list[dict],
) -> dict[str, Any]:
    """
    Build the complete Sankey diagram data model.
    Returns JSON-serializable dict for the frontend.
    """
    flags = global_state.get("active_event_flags", {})
    current_round = global_state.get("round_number", 1)

    # ── 1. Ignition check (Shadow Board Audit) ──
    shadow_board_completed = bool(flags.get("shadow_board_completed"))
    ignited = shadow_board_completed and current_round >= 5

    # ── 2. Decision history → leverage impact scores ──
    decision_history = _extract_decision_history(global_state, history)
    impact_data = compute_per_decision_impact(decision_history)

    # ── 3. Build Sankey nodes ──
    decision_nodes = []
    for imp in impact_data:
        decision_nodes.append({
            "id": f"r{imp['round']}_decision",
            "round": imp["round"],
            "label": imp["label"],
            "leverage_level": imp["leverage_level"],
            "impact_score": imp["impact_score"],
            "category": imp["category"],
            "category_label": imp["category_label"],
            "type": "decision",
        })

    # Flag nodes from FLAG_DEPENDENCY_GRAPH
    dep_graph = get_flag_dependency_graph(flags)
    
    # Inject BRSR side track flags into dep_graph for visualizer
    brsr_flags = [
        ("brsr_pioneer", "BRSR-R1", "governance"),
        ("governance_fragility", "BRSR-R1", "risk"),
        ("brsr_living_wage", "BRSR-R2", "social_license"),
        ("brsr_circular_symbiosis", "BRSR-R3", "natural_capital"),
        ("sdg_12_leadership", "BRSR-R3", "natural_capital"),
        ("brsr_core_assured", "BRSR-R4", "supply_chain"),
        ("brsr_greenwash_risk", "BRSR-R4", "risk"),
        ("brsr_integrated_report", "BRSR-R5", "governance"),
    ]
    for flag_id, src_rnd, cat in brsr_flags:
        if flags.get(flag_id):
            dep_graph["dependencies"].append({
                "flag": flag_id,
                "status": "active",
                "category": cat,
                "source_round": 5, # Treat as mid-game
                "target_round": 5,
                "effect": f"{flag_id} active"
            })

    flag_nodes = []
    for dep in dep_graph["dependencies"]:
        sr = dep["source_round"]
        if (isinstance(sr, int) and sr <= current_round) or isinstance(sr, str):
            flag_nodes.append({
                "id": dep["flag"],
                "label": dep["flag"].replace("_", " ").title(),
                "active": dep.get("status") == "active",
                "category": dep.get("category", "other"),
                "source_round": dep["source_round"],
                "target_round": dep["target_round"],
                "effect": dep["effect"],
                "type": "flag",
            })

    # Metric shift nodes
    metric_nodes = []
    for flag_id, shifts in FLAG_METRIC_SHIFTS.items():
        if any(f["id"] == flag_id for f in flag_nodes):
            for shift in shifts:
                metric_nodes.append({
                    "id": f"{flag_id}_{shift['metric']}",
                    "label": shift["label"],
                    "metric": shift["metric"],
                    "delta": shift["delta"],
                    "source_flag": flag_id,
                    "type": "metric",
                })

    # Projection nodes (M_R components)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bu_states) / max(len(bu_states), 1)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bu_states) / max(len(bu_states), 1)
    workforce_readiness = global_state.get("workforce_readiness", 50)
    synergy = global_state.get("synergy_multiplier", 1.0)
    # F-15 (audit 2026-09-04): the same flag reading and HR-round count the
    # finale uses (list-held flags were invisible to the raw dict here).
    from flag_utils import mr_input_from_state
    _mr_flags, hr_rounds = mr_input_from_state(global_state)

    # If the engine already computed the authoritative M_R (stored at R10 commit),
    # use it directly so the DNA Visualizer matches the Scorecard.  Only fall back
    # to recomputing via calculate_mr for in-progress (pre-R10) sessions where
    # active_event_flags.regenerative_multiple has not yet been written.
    authoritative_mr = flags.get("regenerative_multiple")
    if authoritative_mr is not None:
        mr_breakdown = flags.get("mr_breakdown", {})
        mr_result = {
            "mr": float(authoritative_mr),
            "breakdown": mr_breakdown,
            "bonuses_earned": [],
            "max_achievable_mr": max_achievable_mr_for(_mr_flags, hr_rounds),  # VAL-11 (WP-28): the published table, not a stale literal
        }
    else:
        mr_result = calculate_mr(_mr_flags, avg_slo, avg_burnout, workforce_readiness, synergy, hr_rounds)
    projection_nodes = []
    for key, value in mr_result["breakdown"].items():
        if key == "base":
            continue
        projection_nodes.append({
            "id": f"proj_{key}",
            "label": key.replace("_", " ").title(),
            "mr_delta": value,
            "active": True,
            "type": "projection",
        })

    # ── 4a. Red DNA nodes (Option C consequences) ──
    red_dna_nodes = []
    for flag_key, red_info in OPTION_C_RED_DNA.items():
        if flags.get(flag_key):
            red_dna_nodes.append({
                "id": f"red_dna_{flag_key}",
                "label": red_info["label"],
                "type": "red_dna",
                "subtype": red_info["type"],  # "constriction" or "leak"
                "risk_flag": flag_key,
                "icon": red_info["icon"],
                "color": "#ef4444",  # Red
            })

    # ── 4b. SDG projection node ──
    sdg_score = flags.get("sdg_impact_score", 0)
    sdg_track_active = flags.get("sdg_track_completed", False)
    sdg_projection = None
    if sdg_track_active or sdg_score != 0:
        from terminal_valuation import calculate_sdg_multiplier
        sdg_result = calculate_sdg_multiplier(sdg_score)
        sdg_projection = {
            "id": "proj_sdg_multiplier",
            "label": f"M_SDG: {sdg_result['m_sdg']:.4f}",
            "m_sdg": sdg_result["m_sdg"],
            "sdg_impact_score": sdg_score,
            "type": "projection",
        }
        projection_nodes.append(sdg_projection)

    # ── 4c. Conflict nodes (agent constriction/leak) ──
    conflict_nodes = []
    agent_summaries = []
    cascade_events = []

    aa_state = global_state.get("autonomous_agents", {})
    if aa_state:
        try:
            from autonomous_agents import get_agent_summary, AGENT_PROFILES, INTERFERENCE_PAIRS
            summary_raw = get_agent_summary(aa_state)
            # get_agent_summary returns a list of agent dicts (or a dict with 'agents')
            agents_list = summary_raw if isinstance(summary_raw, list) else summary_raw.get("agents", [])
            for agent in agents_list:
                aid = agent["agent_id"]
                profile = AGENT_PROFILES.get(aid, {})
                initial_tol = profile.get("initial_tolerance", 75)
                current_tol = agent.get("tolerance", initial_tol)
                constriction = round(1 - (current_tol / max(initial_tol, 1)), 4)
                stage = agent.get("stage", "dormant")
                flow_map = AGENT_FLOW_MAP.get(aid, {})

                conflict_nodes.append({
                    "agent_id": aid,
                    "name": agent.get("name", aid),
                    "icon": profile.get("icon", ""),
                    "color": profile.get("color", "#666"),
                    "stage": stage,
                    "constriction_factor": max(0, constriction),
                    "leak_active": stage == "triggered",
                    "leak_label": flow_map.get("leak_label", ""),
                    "flow_source": flow_map.get("flow_source", ""),
                    "flow_target": flow_map.get("flow_target", ""),
                })

                agent_summaries.append({
                    "agent_id": aid,
                    "name": agent.get("name", aid),
                    "icon": profile.get("icon", ""),
                    "tolerance": current_tol,
                    "max_tolerance": initial_tol,
                    "stage": stage,
                    "trend": agent.get("trend", "stable"),
                    "triggered_round": agent.get("triggered_round"),
                })

            # Cascade events from interference pairs
            cascade_log = aa_state.get("cascade_log", [])
            for entry in cascade_log:
                cascade_events.append({
                    "source": entry.get("source_agent", ""),
                    "target": entry.get("target_agent", ""),
                    "round": entry.get("round", 0),
                    "tolerance_hit": entry.get("tolerance_hit", 0),
                })

            # Interference pairs for visualization
            interference_pairs = []
            for pair in INTERFERENCE_PAIRS:
                interference_pairs.append({
                    "agent_a": pair.get("agent_a", ""),
                    "agent_b": pair.get("agent_b", ""),
                    "label": pair.get("label", ""),
                    "threshold": pair.get("activation_threshold", "agitated"),
                })
        except Exception as exc:
            print(f"[WARN] Consequence DNA agent data failed: {exc}")
            interference_pairs = []
    else:
        interference_pairs = []

    # ── 5. Build Sankey links ──
    links = []
    for dep in dep_graph["dependencies"]:
        sr = dep["source_round"]
        if isinstance(sr, int) and sr > current_round:
            continue
        is_active = dep.get("status") == "active"
        # Decision → Flag link
        imp_match = next((i for i in impact_data if i["round"] == dep["source_round"]), None)
        impact_val = imp_match["impact_score"] if imp_match else 1
        lp_level = imp_match["leverage_level"] if imp_match else 12
        
        color_override = None
        if dep["flag"] in ["brsr_pioneer", "brsr_living_wage", "brsr_circular_symbiosis", "sdg_12_leadership", "brsr_core_assured", "brsr_integrated_report"]:
            color_override = "#10b981"

        links.append({
            "source": f"r{dep['source_round']}_decision" if isinstance(dep["source_round"], int) else f"r5_decision",
            "target": dep["flag"],
            "value": impact_val,
            "leverage_level": lp_level,
            "active": is_active,
            "color_override": color_override,
            "brsr_indicator": "leadership" if color_override else None,
        })

        # Flag → Metric link
        if dep["flag"] in FLAG_METRIC_SHIFTS:
            for shift in FLAG_METRIC_SHIFTS[dep["flag"]]:
                links.append({
                    "source": dep["flag"],
                    "target": f"{dep['flag']}_{shift['metric']}",
                    "value": impact_val * 0.8,
                    "leverage_level": lp_level,
                    "active": is_active,
                })

        # Flag → Projection link
        flag_to_proj = _get_flag_projection_mapping(dep["flag"])
        if flag_to_proj:
            links.append({
                "source": dep["flag"],
                "target": flag_to_proj,
                "value": impact_val * 0.6,
                "leverage_level": lp_level,
                "active": is_active,
            })

    # Agent Links
    for agent_node in conflict_nodes:
        source_flags = [f for f in flag_nodes if f["active"] and (f["category"] == agent_node["flow_source"] or f["effect"] == agent_node["flow_source"])]
        if not source_flags:
            source_flags = [f for f in flag_nodes if f["active"]]
        if not source_flags:
            source_flags = [f for f in flag_nodes if f["category"] == agent_node["flow_source"] or f["effect"] == agent_node["flow_source"]]
        if not source_flags:
            source_flags = flag_nodes
            
        is_agent_active = agent_node["stage"] != "dormant"
        
        for src in source_flags[:2]:
            links.append({
                "source": src["id"],
                "target": agent_node["agent_id"],
                "value": 0.8,
                "leverage_level": 8,
                "active": is_agent_active,
                "is_leak": agent_node["leak_active"]
            })
            
        target_proj = f"proj_{agent_node['flow_target']}"
        if any(p["id"] == target_proj for p in projection_nodes):
            links.append({
                "source": agent_node["agent_id"],
                "target": target_proj,
                "value": 0.8,
                "leverage_level": 8,
                "active": is_agent_active,
                "is_leak": agent_node["leak_active"]
            })

    # ── 6. Senge archetype badges ──
    archetype_badges = []
    try:
        from meadows_leverage import detect_archetypes
        archetypes = detect_archetypes(global_state, bu_states, flags)
        for arch in (archetypes or []):
            archetype_badges.append({
                "id": arch.get("id", ""),
                "name": arch.get("name", ""),
                "description": arch.get("description", ""),
                "related_flags": arch.get("related_flags", []),
                "severity": arch.get("severity", "warning"),
            })
    except Exception:
        pass

    # ── 7. Leverage summary ──
    deep_count = sum(1 for i in impact_data if i["category"] == "deep")
    shallow_count = sum(1 for i in impact_data if i["category"] == "shallow")

    try:
        from meadows_leverage import analyse_session_leverage_points
        # IMP-03 (audit 2026-09-04, WP-22): the call passed one argument to a
        # three-argument function; the TypeError was swallowed and every
        # session's "System Effectiveness" read 0%.
        lp_analysis = analyse_session_leverage_points(decision_history, global_state, bu_states)
    except Exception:
        lp_analysis = {"effectiveness_score": 0, "dominant_leverage_point": 12}

    archetype_result = determine_archetype(mr_result["mr"])
    # If the engine stored a pathway-specific profile title/icon, honour it.
    if flags.get("profile_title"):
        archetype_result = {**archetype_result, "title": flags["profile_title"]}
    if flags.get("profile"):
        archetype_result = {**archetype_result, "key": flags["profile"]}

    return {
        "ignited": ignited,
        "ignition_round": 5 if ignited else None,
        "shadow_board_completed": shadow_board_completed,
        "current_round": current_round,
        "sankey_nodes": {
            "decisions": decision_nodes,
            "flags": flag_nodes,
            "metrics": metric_nodes,
            "projections": projection_nodes,
            "conflict_nodes": conflict_nodes,
        },
        "sankey_links": links,
        "cascade_events": cascade_events,
        "interference_pairs": interference_pairs,
        "agents": agent_summaries,
        "mr_projection": {
            "mr": mr_result["mr"],
            "breakdown": mr_result["breakdown"],
            "bonuses_earned": mr_result["bonuses_earned"],
            "archetype": archetype_result,
        },
        "leverage_summary": {
            "dominant_level": lp_analysis.get("dominant_leverage_point", 12),
            "effectiveness_score": lp_analysis.get("effectiveness_score", 0),
            "deep_intervention_count": deep_count,
            "shallow_intervention_count": shallow_count,
        },
        "archetype_badges": archetype_badges,
        "red_dna_nodes": red_dna_nodes,
        "sdg_projection": sdg_projection,
        "sdg_track_active": sdg_track_active,
    }


def _get_flag_projection_mapping(flag: str) -> str | None:
    """Map a flag to its M_R projection node ID."""
    mapping = {
        "materiality_aligned": "proj_materiality_governance",
        "materiality_partial": "proj_materiality_governance",
        "synergy_unlock": "proj_synergy_bonus",
        "ethical_ai_overhaul": "proj_truth_premium",
        "community_fund": "proj_community_champion_bonus",
        "managed_transition": "proj_just_transition_bonus",
        "insurance_only": "proj_resilience_bonus",
        "electronics_water_priority": "proj_resilience_bonus",
        "planet_expendable": "proj_planet_expendable_penalty",
        "sdg_integrated_reporting": "proj_sdg_multiplier",
        "circular_leader": "proj_sdg_multiplier",
        "nature_positive": "proj_sdg_multiplier",
        "brsr_net_positive_dividend": "proj_brsr_dividend",
        "brsr_integrated_report": "proj_brsr_dividend",
    }
    return mapping.get(flag)
