"""
Muressons Global Corporation — Admin Router (God Mode)
Facilitator-only endpoints for real-time cohort monitoring,
manual state overrides, and message injection.
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Optional
from datetime import datetime, timezone
import random

import os
import shutil
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status, Body, UploadFile, File
from pydantic import BaseModel
from fastapi import Header, Depends

def get_fac_role(x_facilitator_id: str = Header(None)):
    if not x_facilitator_id:
        return 'facilitator'
    fac = next((f for f in _facilitator_registry if f['facilitator_id'] == x_facilitator_id), None)
    return get_role(fac) if fac else 'facilitator'

def require_super_admin(role: str = Depends(get_fac_role)):
    if role != 'super_admin':
        raise HTTPException(status_code=403, detail='Super Admin required')


import database as db
import materiality_db as mat_db
from config import MASTER_PASSWORD
from models import MaterialityIssue, InterdependenceLink, MaterialityConfig

# ARCH-002: Import all shared state from admin_shared.py
# Re-export for backward compatibility — external modules that do
# `from admin_router import _god_mode_settings` continue to work.
from admin_shared import (
    _god_mode_settings,
    _facilitator_registry, _persist_facilitators, _load_facilitator_registry,
    _FAC_REGISTRY_PATH, _DEFAULT_FACILITATOR,
    _player_registry,
    _session_messages, _session_interventions,
    _god_mode_audit_log, _crisis_trigger_history,
    _practice_mode, is_practice_mode,
    _round_pacing, _get_pacing, is_round_unlocked, is_pacing_set_by_facilitator,
    check_and_increment_cohort_count,
    _get_session_paradigm,
    DEFAULT_ARCHETYPES,
    # 3-tier role model
    ROLE_HIERARCHY, ROLE_ALLOWED_TABS,
    get_role, has_role_level, get_allowed_tabs, can_access_tab, owns_session,
)

admin_router = APIRouter(prefix="/api/admin", tags=["Admin \u2014 God Mode"])


# _get_session_paradigm imported from admin_shared

# God mode settings, facilitator registry, and archetypes now imported from admin_shared.
# The _next_facilitator_id is kept local since it's only used in this file.
_next_facilitator_id: int = 1


class FacilitatorCreateRequest(BaseModel):
    name: str
    email: str | None = None
    contact_number: str | None = None
    programme: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    max_cohorts: int = 5
    decision_paradigm: str = "legacy_abc"
    permissions: dict | None = None
    created_by: str | None = None
    date_created: str | None = None

class FacilitatorUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    contact_number: str | None = None
    programme: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    max_cohorts: int | None = None
    decision_paradigm: str | None = None
    permissions: dict | None = None
    created_by: str | None = None
    date_created: str | None = None

class FacilitatorBulkCreateRequest(BaseModel):
    facilitators: list[FacilitatorCreateRequest]


# ── Global Settings (Sim Switchboard ↔ player sessions) ─────────
@admin_router.get("/global-settings", summary="Get current global simulation settings")
async def get_global_settings():
    """Returns current god-mode settings including simulation_mode.
    Called by player sessions on mount to detect Advanced Climate Engine."""
    return {
        "simulation_mode": _god_mode_settings.get("simulation_mode", "standard"),
        "global_carbon_fee": _god_mode_settings.get("global_carbon_fee", 40),
        "market_hostility_index": _god_mode_settings.get("market_hostility_index", 5),
        "scope_3_threshold": _god_mode_settings.get("scope_3_threshold", 2.5),
        "allow_facilitator_cohort_creation": _god_mode_settings.get("allow_facilitator_cohort_creation", True),
        "system_frozen": _god_mode_settings.get("system_frozen", False),
        "corporate_treasury_start": _god_mode_settings.get("corporate_treasury_start", 25_000_000.0),
        "group_reputation_start": _god_mode_settings.get("group_reputation_start", 50.0),
        "synergy_multiplier_start": _god_mode_settings.get("synergy_multiplier_start", 1.0),
        "cost_of_capital_start": _god_mode_settings.get("cost_of_capital_start", 0.05),
        "loan_interest_rate_start": _god_mode_settings.get("loan_interest_rate_start", 0.12),
        "imitation_decay_rate_start": _god_mode_settings.get("imitation_decay_rate_start", 0.05),
        "green_transition_fund_start": _god_mode_settings.get("green_transition_fund_start", 0.0),
        "industry": _god_mode_settings.get("industry", "generic"),
        # Economic complexity engine tunables
        "overrun_probability": _god_mode_settings.get("overrun_probability", 0.25),
        "overrun_severity": _god_mode_settings.get("overrun_severity", 0.15),
        # Display currency
        "currency_symbol": _god_mode_settings.get("currency_symbol", "$"),
        # Ending pathways
        "default_ending_pathway": _god_mode_settings.get("default_ending_pathway", "activist_ultimatum"),
        "ending_pathways_available": _god_mode_settings.get("ending_pathways_available", ["activist_ultimatum"]),
        "allow_pathway_switching": _god_mode_settings.get("allow_pathway_switching", False),
        "foreshadowing_enabled": _god_mode_settings.get("foreshadowing_enabled", True),
        # CEO Interview
        "ceo_interview_enabled": _god_mode_settings.get("ceo_interview_enabled", False),
        "ceo_interview_voice_gender": _god_mode_settings.get("ceo_interview_voice_gender", "female"),
        "ceo_interview_question_count": _god_mode_settings.get("ceo_interview_question_count", 5),
        "ceo_interview_pathway_question": _god_mode_settings.get("ceo_interview_pathway_question", True),
        # Pedagogical Scaffolding
        # NOTE: difficulty_tier is per-cohort (set via Experience Level at creation), not global.
        # Kept in response for backward compatibility but God Mode no longer owns this value.
        "prediction_gates_enabled": _god_mode_settings.get("prediction_gates_enabled", False),
        "board_room_moments_enabled": _god_mode_settings.get("board_room_moments_enabled", True),
        "mental_model_tracker_enabled": _god_mode_settings.get("mental_model_tracker_enabled", True),
        "confidence_calibration_enabled": _god_mode_settings.get("confidence_calibration_enabled", False),
        "mid_game_checkpoint_enabled": _god_mode_settings.get("mid_game_checkpoint_enabled", True),
        "peer_comparison_enabled": _god_mode_settings.get("peer_comparison_enabled", True),
        "strategy_memo_enabled": _god_mode_settings.get("strategy_memo_enabled", False),
        "what_if_builder_enabled": _god_mode_settings.get("what_if_builder_enabled", False),
        "custom_crisis_enabled": _god_mode_settings.get("custom_crisis_enabled", False),
        "round_recap_enabled": _god_mode_settings.get("round_recap_enabled", False),
        "real_world_cards_enabled": _god_mode_settings.get("real_world_cards_enabled", False),
        "real_world_cards_teleprompter": _god_mode_settings.get("real_world_cards_teleprompter", True),
        "debrief_protocol_enabled": _god_mode_settings.get("debrief_protocol_enabled", False),
        "self_learning_mode": _god_mode_settings.get("self_learning_mode", False),
        "flag_diagram_enabled": _god_mode_settings.get("flag_diagram_enabled", True),
        "stochastic_labels_enabled": _god_mode_settings.get("stochastic_labels_enabled", True),
        "engine_summariser_enabled": _god_mode_settings.get("engine_summariser_enabled", True),
        # New Engine Toggles (Batch 1-3)
        "decision_timer_enabled": _god_mode_settings.get("decision_timer_enabled", False),
        "decision_timer_seconds": _god_mode_settings.get("decision_timer_seconds", 300),
        "peer_learning_prompts_enabled": _god_mode_settings.get("peer_learning_prompts_enabled", True),
        "board_governance_enabled": _god_mode_settings.get("board_governance_enabled", True),
        "supply_chain_network_enabled": _god_mode_settings.get("supply_chain_network_enabled", True),
        "biodiversity_engine_enabled": _god_mode_settings.get("biodiversity_engine_enabled", True),
        "market_dynamics_enabled": _god_mode_settings.get("market_dynamics_enabled", False),
        "balance_sheet_enabled": _god_mode_settings.get("balance_sheet_enabled", True),
        "regulatory_sandbox_enabled": _god_mode_settings.get("regulatory_sandbox_enabled", False),
        "dynamic_cases_enabled": _god_mode_settings.get("dynamic_cases_enabled", True),
        "branching_enabled": _god_mode_settings.get("branching_enabled", True),
        "npc_stakeholders_enabled": _god_mode_settings.get("npc_stakeholders_enabled", True),
        "tcfd_scenarios_enabled": _god_mode_settings.get("tcfd_scenarios_enabled", True),
        "org_politics_enabled": _god_mode_settings.get("org_politics_enabled", True),
        "meadows_leverage_enabled": _god_mode_settings.get("meadows_leverage_enabled", True),
        "system_archetypes_enabled": _god_mode_settings.get("system_archetypes_enabled", True),
    }

class GlobalSettingsPatch(BaseModel):
    simulation_mode: str | None = None
    global_carbon_fee: float | None = None
    market_hostility_index: float | None = None
    scope_3_threshold: float | None = None
    allow_facilitator_cohort_creation: bool | None = None
    system_frozen: bool | None = None
    freeze_message: str | None = None
    corporate_treasury_start: float | None = None
    group_reputation_start: float | None = None
    synergy_multiplier_start: float | None = None
    cost_of_capital_start: float | None = None
    loan_interest_rate_start: float | None = None
    imitation_decay_rate_start: float | None = None
    green_transition_fund_start: float | None = None
    industry: str | None = None
    # Economic complexity engine tunables
    overrun_probability: float | None = None
    overrun_severity: float | None = None
    # Display currency
    currency_symbol: str | None = None
    # Ending pathways
    default_ending_pathway: str | None = None
    allow_pathway_switching: bool | None = None
    foreshadowing_enabled: bool | None = None
    # CEO Interview
    ceo_interview_enabled: bool | None = None
    ceo_interview_voice_gender: str | None = None
    ceo_interview_question_count: int | None = None
    ceo_interview_pathway_question: bool | None = None
    # Pedagogical Scaffolding
    difficulty_tier: str | None = None
    prediction_gates_enabled: bool | None = None
    board_room_moments_enabled: bool | None = None
    mental_model_tracker_enabled: bool | None = None
    confidence_calibration_enabled: bool | None = None
    mid_game_checkpoint_enabled: bool | None = None
    peer_comparison_enabled: bool | None = None
    strategy_memo_enabled: bool | None = None
    what_if_builder_enabled: bool | None = None
    custom_crisis_enabled: bool | None = None
    round_recap_enabled: bool | None = None
    real_world_cards_enabled: bool | None = None
    real_world_cards_teleprompter: bool | None = None
    debrief_protocol_enabled: bool | None = None
    self_learning_mode: bool | None = None
    flag_diagram_enabled: bool | None = None
    stochastic_labels_enabled: bool | None = None
    engine_summariser_enabled: bool | None = None
    # New Engine Toggles (Batch 1-3)
    decision_timer_enabled: bool | None = None
    decision_timer_seconds: int | None = None
    peer_learning_prompts_enabled: bool | None = None
    board_governance_enabled: bool | None = None
    supply_chain_network_enabled: bool | None = None
    biodiversity_engine_enabled: bool | None = None
    market_dynamics_enabled: bool | None = None
    balance_sheet_enabled: bool | None = None
    regulatory_sandbox_enabled: bool | None = None
    dynamic_cases_enabled: bool | None = None
    branching_enabled: bool | None = None
    npc_stakeholders_enabled: bool | None = None
    tcfd_scenarios_enabled: bool | None = None
    org_politics_enabled: bool | None = None
    meadows_leverage_enabled: bool | None = None
    system_archetypes_enabled: bool | None = None

@admin_router.patch("/global-settings", summary="Update global simulation settings (Sim Switchboard)")
async def patch_global_settings(body: GlobalSettingsPatch, _guard: None = Depends(require_super_admin)):
    """Sim Switchboard endpoint — updates simulation_mode and climate parameters."""
    # FIX AUDIT-017: Use Pydantic to validate input types
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        _god_mode_settings[key] = value
    
    import logging
    logging.info(f"[god-mode] Global settings updated: {_god_mode_settings}")
    
    # Event Bus: Broadcast settings change to all connected admin dashboards
    _audit("global_settings_updated", details=update_data)
    await manager.broadcast_admin({
        "type": "settings_changed",
        "changed_keys": list(update_data.keys()),
        "settings": {k: _god_mode_settings.get(k) for k in update_data},
    })
    return {"status": "ok", "settings": _god_mode_settings}


@admin_router.get("/scaffolding-status", summary="Get active pedagogical scaffolding features (read-only)")
async def get_scaffolding_status():
    """Returns which global pedagogical features are currently ON/OFF.
    Used by the Facilitator dashboard to display a read-only summary strip."""
    scaffolding_keys = [
        ("prediction_gates_enabled", "🔮 Predictions", False),
        ("confidence_calibration_enabled", "🎰 Confidence", False),
        ("board_room_moments_enabled", "🏢 Board Room", True),
        ("round_recap_enabled", "📋 Recap", False),
        ("real_world_cards_enabled", "🌍 Case Cards", False),
        ("strategy_memo_enabled", "📝 Memo", False),
        ("debrief_protocol_enabled", "🎭 Debrief", False),
        ("self_learning_mode", "🎓 Self-Learn", False),
        ("r6_revelation_enabled", "🚨 R6 Twist", True),
        ("r7_budget_allocation_enabled", "♻️ R7 Budget", True),
        ("r8_tribunal_enabled", "⚖️ R8 Tribunal", True),
        # New Engine Toggles
        ("decision_timer_enabled", "⏱️ Timer", False),
        ("biodiversity_engine_enabled", "🌿 Biodiversity", True),
        ("balance_sheet_enabled", "📊 Balance Sheet", True),
        ("board_governance_enabled", "🏛️ Board Gov", True),
        ("supply_chain_network_enabled", "🔗 Supply Chain", True),
        ("npc_stakeholders_enabled", "👥 NPC Agents", True),
        ("org_politics_enabled", "🤝 Org Politics", True),
        ("branching_enabled", "🔀 Branching", True),
        ("dynamic_cases_enabled", "📰 Case Studies", True),
        ("tcfd_scenarios_enabled", "🌡️ TCFD", True),
        ("regulatory_sandbox_enabled", "⚖️ Reg Sandbox", False),
        ("meadows_leverage_enabled", "🎯 Leverage Pts", True),
        ("system_archetypes_enabled", "🔄 Archetypes", True),
    ]
    features = []
    for key, label, default in scaffolding_keys:
        features.append({
            "key": key,
            "label": label,
            "enabled": _god_mode_settings.get(key, default),
        })
    return {
        "features": features,
        "system_frozen": _god_mode_settings.get("system_frozen", False),
        "simulation_mode": _god_mode_settings.get("simulation_mode", "standard"),
    }


@admin_router.get("/facilitator-role-info/{fac_id}", summary="Get role and permissions for a facilitator")
async def get_facilitator_role_info(fac_id: str):
    """Returns the role, allowed tabs, and permissions for a specific facilitator."""
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    role = get_role(fac)
    return {
        "facilitator_id": fac_id,
        "name": fac.get("name", ""),
        "role": role,
        "allowed_tabs": get_allowed_tabs(fac),
        "permissions": fac.get("permissions", {}),
        "is_admin": role == "super_admin",
    }


@admin_router.put("/facilitators/{fac_id}/role", summary="Change a facilitator's role (God Mode only)")
async def update_facilitator_role(fac_id: str, body: dict = Body(...)):
    """Change a facilitator's role. Requires God Mode password verification.
    Body must include: role, god_mode_fac_id, god_mode_password."""
    # ── God Mode password verification ──────────────────────
    gm_fac_id = (body.get("god_mode_fac_id") or "").strip()
    gm_password = (body.get("god_mode_password") or "").strip()
    if not gm_fac_id or not gm_password:
        raise HTTPException(403, "God Mode credentials required to change roles")
    gm_fac = next((f for f in _facilitator_registry if f["facilitator_id"] == gm_fac_id), None)
    master_ok = bool(MASTER_PASSWORD) and gm_password == MASTER_PASSWORD
    if not gm_fac or (gm_fac["password"] != gm_password and not master_ok):
        raise HTTPException(403, "Invalid God Mode credentials")
    if get_role(gm_fac) != "super_admin":
        raise HTTPException(403, "Only Super Administrators can change facilitator roles")
    # ── Apply role change ───────────────────────────────────
    new_role = body.get("role", "").strip()
    if new_role not in ROLE_HIERARCHY:
        raise HTTPException(400, f"Invalid role '{new_role}'. Must be one of: {list(ROLE_HIERARCHY.keys())}")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    fac["role"] = new_role
    fac["is_admin"] = new_role == "super_admin"  # backward compat
    _persist_facilitators()
    _audit("facilitator_role_changed", details={"facilitator_id": fac_id, "new_role": new_role, "changed_by": gm_fac_id})
    return {"status": "ok", "facilitator_id": fac_id, "role": new_role}

# ── Simulation Master Reference (read-only, live values) ────────
@admin_router.get("/simulation-reference", summary="Live simulation master reference (read-only)")
async def get_simulation_reference():
    """Returns the complete simulation reference with live values from current settings.
    This is a read-only endpoint — no inputs possible. All values are derived from
    the current simulation state, round configs, and God Mode settings."""
    from round_configs import ROUND_CONFIGS

    settings = _god_mode_settings
    sessions = await db.fetch_all_sessions()

    # Live global settings
    treasury_start = settings.get("corporate_treasury_start", 25_000_000)
    reputation_start = settings.get("group_reputation_start", 50.0)
    synergy_start = settings.get("synergy_multiplier_start", 1.0)
    coc_start = settings.get("cost_of_capital_start", 0.05)
    carbon_fee_base = settings.get("global_carbon_fee", 40)
    hostility_index = settings.get("market_hostility_index", 5)
    overrun_prob = settings.get("overrun_probability", 0.25)
    overrun_severity = settings.get("overrun_severity", 0.15)
    loan_rate = settings.get("loan_interest_rate_start", 0.12)
    decay_rate = settings.get("imitation_decay_rate_start", 0.10)
    currency = settings.get("currency_symbol", "$")

    # Compute carbon fee schedule (32.25% per 6-month round, compounded from 15%/quarter)
    carbon_fee_schedule = []
    for r in range(1, 11):
        fee = round(carbon_fee_base * (1.3225 ** (r - 1)), 2)
        carbon_fee_schedule.append({"round": r, "fee_per_ton": fee})

    # SBTi target schedule (8.22% decay per 6-month round, compounded from 4.2%/quarter)
    sbti_schedule = []
    for r in range(1, 11):
        target = round(36.25 * (1 - 0.0822) ** (r - 1), 2)
        sbti_schedule.append({"round": r, "target_ci": target})

    # Build round summaries from configs
    round_summaries = []
    for rn in range(1, 11):
        cfg = ROUND_CONFIGS.get(rn, {})
        options = {}
        for opt_key, opt_data in cfg.get("options", {}).items():
            impacts = opt_data.get("impacts", {})
            options[opt_data.get("label", opt_key)] = {
                "title": opt_data.get("title", ""),
                "description": opt_data.get("description", ""),
                "flags": opt_data.get("flags_set", []),
                "treasury": impacts.get("treasury", 0),
                "ci_delta": impacts.get("carbon_intensity_delta", 0),
                "reputation_delta": impacts.get("reputation", impacts.get("reputation_delta", 0)),
                "ncd_delta": impacts.get("natural_capital_debt_delta", 0),
                "slo_delta": impacts.get("social_license_delta", impacts.get("social_license", 0)),
                "climate_framing": opt_data.get("climate_framing", ""),
            }
        round_summaries.append({
            "round": rn,
            "title": cfg.get("title", ""),
            "theme": cfg.get("theme", ""),
            "crisis_title": cfg.get("crisis", {}).get("title", ""),
            "crisis_description": cfg.get("crisis", {}).get("description", ""),
            "crisis_icon": cfg.get("crisis", {}).get("icon", ""),
            "options": options,
            "special_rules": cfg.get("special_rules", {}),
        })

    # Active sessions summary
    session_count = len(sessions)
    paradigm_counts = {}
    for s in sessions:
        p = s.get("decision_paradigm", "legacy_abc")
        paradigm_counts[p] = paradigm_counts.get(p, 0) + 1

    return {
        "meta": {
            "title": "Muressons Global Corporation — Simulation Master Reference",
            "description": "Live reference document. All values sourced from current simulation state. Read-only.",
            "active_sessions": session_count,
            "paradigm_distribution": paradigm_counts,
            "currency_symbol": currency,
        },
        "starting_state": {
            "corporate_treasury": treasury_start,
            "group_reputation": reputation_start,
            "synergy_multiplier": synergy_start,
            "cost_of_capital": coc_start,
            "loan_interest_rate": loan_rate,
            "vrio_decay_rate": decay_rate,
            "inflation_index": 0.02,
            "standard_bus": [
                {"bu_id": "pharma", "revenue": 18_000_000, "opex": 11_500_000, "ci": 45, "ncd": 5000, "slo": 70, "rep": 72, "gov_risk": 15, "water_dep": 0.6},
                {"bu_id": "electronics", "revenue": 22_000_000, "opex": 14_000_000, "ci": 60, "ncd": 3800, "slo": 65, "rep": 58, "gov_risk": 25, "water_dep": 0.8},
                {"bu_id": "consumer_goods", "revenue": 15_000_000, "opex": 9_000_000, "ci": 30, "ncd": 2100, "slo": 78, "rep": 74, "gov_risk": 10, "water_dep": 0.3},
                {"bu_id": "software", "revenue": 20_000_000, "opex": 8_000_000, "ci": 10, "ncd": 500, "slo": 85, "rep": 82, "gov_risk": 5, "water_dep": 0.1},
            ],
        },
        "engine_formulas": [
            {"id": 1, "name": "Corporate Strategic Fund", "formula": "CSF = Σ(Revenue_i - OPEX_i) - Dividends", "category": "Treasury"},
            {"id": 2, "name": "Synergy OPEX Reduction", "formula": f"New_OPEX = OPEX × max(0, 1 - (sqrt(Inv) × 0.7 × {synergy_start}))", "category": "Operations"},
            {"id": 3, "name": "Contagion Engine", "formula": "Group_Rep = AVG(BU_Rep) - (Crisis × 0.4)", "category": "Reputation"},
            {"id": 4, "name": "Brain Drain", "formula": "IF Rep < 65: Penalty = 1 + (65-Rep)/100 × 1.5", "category": "Software"},
            {"id": 5, "name": "NCD Compounding", "formula": "Rate = Base + (NCD × 0.0005); NCD_new = NCD + NCD × Rate", "category": "Natural Capital"},
            {"id": 6, "name": "NCD OPEX Penalty", "formula": f"penalty = NCD × {currency}50K × hostility / 1M; cap 50% rev", "category": "Natural Capital"},
            {"id": 7, "name": "VRIO Decay", "formula": f"Synergy_new = Synergy × (1 - {decay_rate})", "category": "Strategic"},
            {"id": 8, "name": "Strike Probability", "formula": "P = GovRisk/100 + (1 - SLO/100) × 0.4", "category": "Risk"},
            {"id": 9, "name": "Short-Term Loan", "formula": f"IF CAPEX > 20% Treasury: Interest = Loan × {loan_rate:.0%}", "category": "Treasury"},
            {"id": 10, "name": "Inflation", "formula": "OPEX *= (1 + inflation_index); IF hostility>5: +0.5%", "category": "Operations"},
            {"id": 11, "name": "Regulatory Ratchet", "formula": "CoC = MAX(all historical CoC)", "category": "Governance"},
            {"id": 12, "name": "Fog of War", "formula": "R1-R3: ±10% noise (display only) unless deep_audit", "category": "Information"},
            {"id": 13, "name": "Greenwashing Risk", "formula": "IF green choice AND avg_inv < 15%: SLO -8", "category": "Risk"},
            {"id": 14, "name": "Competitor NPC", "formula": "Competitor EBITDA × 1.03/round; warning if < 1.0×", "category": "Market"},
            {"id": 15, "name": "Tech Lock-In", "formula": f"IF same BU top CAPEX ×3 rounds: others -15% synergy", "category": "Strategic"},
            {"id": 16, "name": "Board Pressure", "formula": "IF dividends < 80% prior: Reputation -5", "category": "Governance"},
            {"id": 17, "name": "Revenue Cannibalization", "formula": "IF overlap > 30%: weaker BU rev × 2%", "category": "Market"},
            {"id": 18, "name": "Supply Chain Contagion", "formula": "IF gov_risk > 40: 3% OPEX surcharge on connected BUs", "category": "Operations"},
            {"id": 19, "name": "Working Capital Drag", "formula": "IF gov_risk > 30: drag = (risk-30) × rev × 0.001", "category": "Treasury"},
            {"id": 20, "name": "CapEx Overrun", "formula": f"IF CAPEX > {currency}3M: {overrun_prob:.0%} chance of +{overrun_severity:.0%} overrun", "category": "Risk"},
        ],
        "ac_mechanics": {
            "enabled": settings.get("simulation_mode") == "advanced_climate",
            "carbon_fee_base": carbon_fee_base,
            "carbon_fee_schedule": carbon_fee_schedule,
            "tipping_thresholds": {"warning": 45, "stressed": 55, "tipped": 65},
            "hostility_multipliers": {"none": 1.0, "warning": 1.25, "stressed": 1.75, "tipped": 2.50},
            "cyclone_escalation": {"none": 0.75, "warning": 0.80, "stressed": 0.85, "tipped": 0.90},
            "loss_damage_levies": {"warning": 0, "stressed": 500_000, "tipped": 2_000_000},
            "ncd_forgiveness_formula": "forgiveness = 2.0 × ln(1 + CapEx_M$)",
            "cbam_formula": "surcharge = (avg_CI - 40) × $100K (R3, R7)",
            "taxonomy_thresholds": {"aligned_ci_max": 25, "green_discount_pct": 60, "brown_penalty_pct": 20},
            "sbti_schedule": sbti_schedule,
            "scope_ratios": {
                "pharma": {"scope_1": 35, "scope_2": 25, "scope_3": 40},
                "electronics": {"scope_1": 10, "scope_2": 15, "scope_3": 75},
                "consumer_goods": {"scope_1": 15, "scope_2": 10, "scope_3": 75},
                "software": {"scope_1": 5, "scope_2": 60, "scope_3": 35},
            },
            "carbon_futures": {"forward_premium_pct": 20, "spot_volatility_pct": 30, "forward_duration_rounds": 3},
        },
        "terminal_valuation": {
            "carbon_tax_per_ton": 250,
            "exit_multiple": 12.0,
            "synergy_gate_threshold": 80,
            "mr_components": [
                {"name": "Base", "value": 1.0, "source": "Default"},
                {"name": "CSRD Governance Premium", "value": 0.10, "source": "R2A materiality_aligned (≥80% Q1 accuracy + not Option C)"},
                {"name": "Resilience Bonus", "value": 0.20, "source": "No insurance_only/electronics_priority flags"},
                {"name": "Synergy Bonus", "value": 0.30, "source": "R7C synergy_unlock"},
                {"name": "Truth Premium", "value": 0.15, "source": "R6B ethical_ai_overhaul"},
                {"name": "Community Champion", "value": 0.18, "source": "R9C community_fund (× JT scaling)"},
                {"name": "Managed Transition", "value": 0.12, "source": "R9B managed_transition (× JT scaling)"},
                {"name": "Workforce Excellence", "value": 0.10, "source": "workforce_readiness ≥ 75"},
                {"name": "Wellbeing Champion", "value": 0.05, "source": "burnout < 20"},
                {"name": "Instability Discount", "value": -0.40, "source": "avg SLO < 75"},
            ],
            "profile_archetypes": [
                {"name": "Regenerative Titan", "mr_min": 1.8, "icon": "🏆"},
                {"name": "De-risked Safe Haven", "mr_min": 1.2, "icon": "🛡️"},
                {"name": "Fragile Giant", "mr_min": 0.8, "icon": "🏢"},
                {"name": "Stranded Relic", "mr_min": 0.0, "icon": "💀"},
            ],
            "formula_standard": "Terminal_EBITDA × 12 × M_R",
            "formula_ac": "(Terminal_EBITDA + Green_Fund) × 12 × M_R",
        },
        "flag_dependencies": [
            {"source": "R1 A/C", "flag": "electronics_blindspot", "target": "R2", "effect": "Degrades metadata for electronics_sensitive issues in DMM"},
            {"source": "R1 A/C", "flag": "electronics_blindspot", "target": "R4", "effect": "Doubles crisis severity to 80"},
            {"source": "R2 A (≥80%)", "flag": "materiality_aligned", "target": "R3", "effect": "Green Bond -$500K discount (option_b)"},
            {"source": "R2 A (≥80%)", "flag": "materiality_aligned", "target": "R10", "effect": "+0.10 CSRD Governance Premium M_R"},
            {"source": "R2 C / <80%", "flag": "materiality_ignored", "target": "R3", "effect": "Green Bond +$1M risk premium (option_b)"},
            {"source": "R3 A", "flag": "early_decarboniser", "target": "R7", "effect": "+0.10 synergy bonus"},
            {"source": "R5 C", "flag": "insurance_only", "target": "R10", "effect": "Blocks +0.20 resilience M_R"},
            {"source": "R6 B", "flag": "ethical_ai_overhaul", "target": "R10", "effect": "+0.15 truth premium M_R"},
            {"source": "R7 C", "flag": "synergy_unlock", "target": "R10", "effect": "+0.30 synergy M_R + enables Opt A"},
            {"source": "R8 B", "flag": "electronics_water_priority", "target": "R10", "effect": "Blocks +0.20 resilience M_R"},
            {"source": "R9 B/C", "flag": "managed_transition/community_fund", "target": "R10", "effect": "+0.12/+0.18 M_R (× JT scaling)"},
        ],
        "rounds": round_summaries,
    }


@admin_router.get("/archetypes", summary="Get all profile archetypes (defaults + custom)")
async def get_archetypes():
    """Returns defaults (read-only) merged with any custom archetypes.
    Custom archetypes overlay defaults if they share the same key."""
    custom = _god_mode_settings.get("custom_archetypes", [])
    # Build a unified list: customs take precedence over defaults
    custom_keys = {a["key"] for a in custom}
    all_archetypes = [a for a in DEFAULT_ARCHETYPES if a["key"] not in custom_keys] + custom
    # Sort descending by threshold so UI renders in logical order
    all_archetypes.sort(key=lambda a: a.get("mr_threshold", 0), reverse=True)
    return {
        "archetypes": all_archetypes,
        "defaults": DEFAULT_ARCHETYPES,
        "custom": custom,
        "using_custom": len(custom) > 0,
    }


@admin_router.post("/archetypes", summary="Add a new custom archetype")
async def add_archetype(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    key = (body.get("key") or "").strip().replace(" ", "_")
    if not key:
        raise HTTPException(400, "'key' is required")
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(400, "'title' is required")
    mr_threshold = body.get("mr_threshold")
    if mr_threshold is None:
        raise HTTPException(400, "'mr_threshold' is required")
    archetype = {
        "key": key,
        "title": title,
        "description": body.get("description", ""),
        "mr_threshold": float(mr_threshold),
        "icon": body.get("icon", "🏅"),
        "gradient": body.get("gradient", "linear-gradient(135deg, #6366f1, #8b5cf6)"),
        "is_default": False,
    }
    customs = _god_mode_settings.setdefault("custom_archetypes", [])
    # Replace if key already exists
    existing_idx = next((i for i, a in enumerate(customs) if a["key"] == key), None)
    if existing_idx is not None:
        customs[existing_idx] = archetype
    else:
        customs.append(archetype)
    print(f"[god-mode] Archetype added/updated: {key}")
    return {"status": "ok", "archetype": archetype}


@admin_router.put("/archetypes/{key}", summary="Update an existing custom archetype")
async def update_archetype(key: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    customs = _god_mode_settings.get("custom_archetypes", [])
    idx = next((i for i, a in enumerate(customs) if a["key"] == key), None)
    if idx is None:
        # Allow editing defaults by promoting them to custom
        default = next((d for d in DEFAULT_ARCHETYPES if d["key"] == key), None)
        if not default:
            raise HTTPException(404, f"Archetype '{key}' not found")
        archetype = {**default, "is_default": False}
        customs.append(archetype)
        idx = len(customs) - 1
        _god_mode_settings["custom_archetypes"] = customs
    # Apply updates
    for field in ("title", "description", "mr_threshold", "icon", "gradient"):
        if field in body:
            customs[idx][field] = body[field]
    customs[idx]["is_default"] = False
    print(f"[god-mode] Archetype updated: {key}")
    return {"status": "ok", "archetype": customs[idx]}


@admin_router.delete("/archetypes/{key}", summary="Delete a custom archetype")
async def delete_archetype(key: str, _guard: None = Depends(require_super_admin)):
    customs = _god_mode_settings.get("custom_archetypes", [])
    before = len(customs)
    _god_mode_settings["custom_archetypes"] = [a for a in customs if a["key"] != key]
    if len(_god_mode_settings["custom_archetypes"]) == before:
        raise HTTPException(404, f"Custom archetype '{key}' not found (defaults cannot be deleted, only overridden)")
    print(f"[god-mode] Archetype deleted: {key}")
    return {"status": "deleted", "key": key}


# ═════════════════════════════════════════════════════════════════
#  ENDING PATHWAY MANAGEMENT
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/ending-pathways", summary="List available ending pathways")
async def list_ending_pathways():
    """Returns all available ending pathways with metadata."""
    from ending_pathways import ALL_PATHWAY_IDS, IMPLEMENTED_PATHWAYS, PATHWAY_R10_CONFIGS, FORESHADOWING
    pathways = []
    for pid in ALL_PATHWAY_IDS:
        pw_cfg = PATHWAY_R10_CONFIGS.get(pid, {})
        crisis = pw_cfg.get("crisis", {})
        archetype_overrides = pw_cfg.get("archetype_overrides", {})
        pathways.append({
            "id": pid,
            "implemented": pid in IMPLEMENTED_PATHWAYS,
            "title": crisis.get("title", pid.replace("_", " ").title()),
            "description": crisis.get("description", ""),
            "icon": crisis.get("icon", "🏛️"),
            "has_foreshadowing": pid in FORESHADOWING,
            "archetype_overrides": archetype_overrides,
        })
    return {
        "pathways": pathways,
        "default": _god_mode_settings.get("default_ending_pathway", "activist_ultimatum"),
        "available": _god_mode_settings.get("ending_pathways_available", ["activist_ultimatum"]),
        "allow_switching": _god_mode_settings.get("allow_pathway_switching", False),
        "foreshadowing_enabled": _god_mode_settings.get("foreshadowing_enabled", True),
    }


@admin_router.get("/sessions/{session_id}/ending-pathway", summary="Get the ending pathway for a session")
async def get_session_ending_pathway(session_id: str):
    """Returns the current ending pathway for a session."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    flags = latest.get("global_state", {}).get("active_event_flags", {})
    return {
        "session_id": session_id,
        "ending_pathway": flags.get("ending_pathway", "activist_ultimatum"),
        "allow_switching": _god_mode_settings.get("allow_pathway_switching", False),
    }


@admin_router.put("/sessions/{session_id}/ending-pathway", summary="Switch the ending pathway for a session")
async def switch_session_ending_pathway(session_id: str, body: dict = Body(...)):
    """Switch the ending pathway for a live session.
    Requires allow_pathway_switching to be enabled in god-mode settings."""
    if not _god_mode_settings.get("allow_pathway_switching", False):
        raise HTTPException(403, "Pathway switching is disabled. Enable 'allow_pathway_switching' in God Mode settings.")

    new_pathway = body.get("ending_pathway", "").strip()
    available = _god_mode_settings.get("ending_pathways_available", ["activist_ultimatum"])
    if new_pathway == "random":
        from ending_pathways import resolve_pathway
        new_pathway = resolve_pathway("random")
    elif new_pathway not in available:
        raise HTTPException(400, f"Pathway '{new_pathway}' is not available. Choose from: {available}")

    # Update the session's active_event_flags
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    gs = latest["global_state"]
    gs.setdefault("active_event_flags", {})["ending_pathway"] = new_pathway
    await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    # Also update all child player sessions
    children = await db.get_child_sessions(session_id)
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state:
            child_gs = child_state["global_state"]
            child_gs.setdefault("active_event_flags", {})["ending_pathway"] = new_pathway
            await db.update_latest_global_state(child["session_id"], child_gs, child_state["bu_states"])

    print(f"[god-mode] Ending pathway switched to '{new_pathway}' for session {session_id}")
    return {
        "status": "ok",
        "session_id": session_id,
        "ending_pathway": new_pathway,
        "children_updated": len(children),
    }


@admin_router.put("/sessions/{session_id}/ceo-interview", summary="Configure CEO Interview per cohort")
async def configure_cohort_interview(session_id: str, body: dict = Body(...)):
    """Set per-cohort CEO Interview settings.
    
    Body fields (all optional):
    - ceo_interview_enabled: bool
    - ceo_interview_voice_gender: "female" | "male"
    
    Overrides god-mode defaults for this specific cohort and all its player sessions.
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    gs = latest["global_state"]
    flags = gs.setdefault("active_event_flags", {})

    updated_fields = []
    if "ceo_interview_enabled" in body:
        flags["ceo_interview_enabled"] = bool(body["ceo_interview_enabled"])
        updated_fields.append(f"enabled={flags['ceo_interview_enabled']}")
    if "ceo_interview_voice_gender" in body:
        gender = body["ceo_interview_voice_gender"]
        if gender in ("female", "male"):
            flags["ceo_interview_voice_gender"] = gender
            updated_fields.append(f"voice={gender}")

    await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    # Propagate to all child player sessions
    children = await db.get_child_sessions(session_id)
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state:
            child_gs = child_state["global_state"]
            child_flags = child_gs.setdefault("active_event_flags", {})
            if "ceo_interview_enabled" in body:
                child_flags["ceo_interview_enabled"] = flags["ceo_interview_enabled"]
            if "ceo_interview_voice_gender" in body:
                child_flags["ceo_interview_voice_gender"] = flags.get("ceo_interview_voice_gender", "female")
            await db.update_latest_global_state(child["session_id"], child_gs, child_state["bu_states"])

    print(f"[god-mode] CEO Interview config updated for session {session_id}: {', '.join(updated_fields)}")
    return {
        "status": "ok",
        "session_id": session_id,
        "ceo_interview_enabled": flags.get("ceo_interview_enabled"),
        "ceo_interview_voice_gender": flags.get("ceo_interview_voice_gender"),
        "children_updated": len(children),
    }

@admin_router.get("/facilitators", summary="List all facilitators")
async def list_facilitators(unmask: bool = False):
    """List facilitators. Passwords are masked unless ?unmask=true."""
    result = []
    for f in _facilitator_registry:
        if f.get("deleted_at"): continue
        entry = {**f, "password": f["password"] if unmask else "••••••"}
        result.append(entry)
    return {"facilitators": result}


@admin_router.post("/facilitators", summary="Create a new facilitator")
async def create_facilitator(req: FacilitatorCreateRequest):
    global _next_facilitator_id
    
    # Dynamically find the highest FAC-XXX to ensure no collisions
    max_id = 0
    for f in _facilitator_registry:
        if f["facilitator_id"].startswith("FAC-"):
            try:
                max_id = max(max_id, int(f["facilitator_id"].split("-")[1]))
            except ValueError:
                pass
    _next_facilitator_id = max_id + 1

    fac = {
        "facilitator_id": f"FAC-{_next_facilitator_id:03d}",
        "name": req.name,
        "email": req.email or "",
        "contact_number": req.contact_number or "",
        "programme": req.programme or "",
        "start_date": req.start_date or "",
        "end_date": req.end_date or "",
        "password": "123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "max_cohorts": req.max_cohorts,
        "cohorts_created": 0,
        "decision_paradigm": req.decision_paradigm,
        "role": "facilitator",  # Default new facilitators to base role
        "is_admin": False,  # backward compat
        "enabled": True,
        "permissions": req.permissions or {
            "can_undo_rounds": True,
            "can_override_decisions": True,
            "can_modify_materiality": True,
            "can_manage_auto_pause": True,
            "can_create_cohorts": True,
        },
        "created_by": req.created_by or "",
        "date_created": req.date_created or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    _next_facilitator_id += 1
    _facilitator_registry.append(fac)
    _persist_facilitators()
    return fac

@admin_router.put("/facilitators/{fac_id}", summary="Update a facilitator's details")
async def update_facilitator(fac_id: str, req: FacilitatorUpdateRequest):
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "permissions" and isinstance(value, dict):
            # merge permissions instead of replacing to preserve unspecified ones
            current_perms = fac.get("permissions", {})
            current_perms.update(value)
            fac["permissions"] = current_perms
        else:
            fac[key] = value
            
    _persist_facilitators()
    return fac

@admin_router.post("/facilitators/bulk", summary="Create multiple facilitators in batch")
async def bulk_create_facilitators(req: FacilitatorBulkCreateRequest):
    global _next_facilitator_id
    created_facs = []
    
    # Calculate starting ID
    max_id = 0
    for f in _facilitator_registry:
        if f["facilitator_id"].startswith("FAC-"):
            try:
                max_id = max(max_id, int(f["facilitator_id"].split("-")[1]))
            except ValueError:
                pass
    _next_facilitator_id = max_id + 1

    for fac_req in req.facilitators:
        fac = {
            "facilitator_id": f"FAC-{_next_facilitator_id:03d}",
            "name": fac_req.name,
            "email": fac_req.email or "",
            "contact_number": fac_req.contact_number or "",
            "programme": fac_req.programme or "",
            "start_date": fac_req.start_date or "",
            "end_date": fac_req.end_date or "",
            "password": "123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "max_cohorts": fac_req.max_cohorts,
            "cohorts_created": 0,
            "decision_paradigm": fac_req.decision_paradigm,
            "role": "facilitator",
            "is_admin": False,
            "enabled": True,
            "permissions": fac_req.permissions or {
                "can_undo_rounds": True,
                "can_override_decisions": True,
                "can_modify_materiality": True,
                "can_manage_auto_pause": True,
            }
        }
        _next_facilitator_id += 1
        _facilitator_registry.append(fac)
        created_facs.append(fac)
        
    _persist_facilitators()
    return {"status": "success", "created": len(created_facs), "facilitators": created_facs}


@admin_router.delete("/facilitators/{fac_id}", summary="Delete a facilitator")
async def delete_facilitator(fac_id: str, hard: bool = False):
    global _facilitator_registry
    if hard:
        before = len(_facilitator_registry)
        # BUG-05 FIX: Find the fac first so we
        # can decrement the parent facilitator's cohort count if needed
        fac_being_deleted = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
        _facilitator_registry = [f for f in _facilitator_registry if f["facilitator_id"] != fac_id]
        if len(_facilitator_registry) == before:
            raise HTTPException(404, f"Facilitator {fac_id} not found")
        # Reset the cohort count since the facilitator is permanently gone
        # (any future recreated account starts fresh)
    else:
        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
        if not fac:
            raise HTTPException(404, f"Facilitator {fac_id} not found")
        fac["deleted_at"] = datetime.now(timezone.utc).isoformat()
        
    _persist_facilitators()
    return {"status": "deleted", "facilitator_id": fac_id}


@admin_router.post("/facilitators/login", summary="Facilitator login")
async def facilitator_login(body: dict = Body(...)):
    fac_id = body.get("facilitator_id", "").strip()
    password = body.get("password", "").strip()
    if not fac_id or not password:
        raise HTTPException(400, "facilitator_id and password are required")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    # FIX AUDIT-005: Master password from env var, empty = disabled
    master_ok = bool(MASTER_PASSWORD) and password == MASTER_PASSWORD
    if not fac and master_ok:
        fac = {
            "facilitator_id": fac_id,
            "name": fac_id,
            "password": MASTER_PASSWORD,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "role": "facilitator",  # Master password creates base-level facilitator
            "is_admin": False,
            "enabled": True,
            "max_cohorts": 5,
            "cohorts_created": 0,
        }
        _facilitator_registry.append(fac)
        _persist_facilitators()
    if not fac or (not master_ok and fac["password"] != password):
        raise HTTPException(403, "Invalid facilitator ID or password")
    
    # Compute role and allowed tabs
    role = get_role(fac)
    allowed_tabs = get_allowed_tabs(fac)
    
    return {
        "status": "success", 
        "facilitator_id": fac["facilitator_id"], 
        "name": fac["name"], 
        "username": fac.get("username", ""),
        "is_admin": role == "super_admin",  # backward compat
        "role": role,
        "allowed_tabs": allowed_tabs,
        "permissions": fac.get("permissions", {}),
    }


@admin_router.post("/facilitators/change-password", summary="Change facilitator password")
async def facilitator_change_password(body: dict = Body(...)):
    fac_id = body.get("facilitator_id", "").strip()
    old_password = body.get("old_password", "").strip()
    new_password = body.get("new_password", "").strip()
    if not fac_id or not old_password or not new_password:
        raise HTTPException(400, "facilitator_id, old_password, and new_password are required")
    if len(new_password) < 3:
        raise HTTPException(400, "New password must be at least 3 characters")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    # FIX AUDIT-005: Use configurable master password
    master_ok = bool(MASTER_PASSWORD) and old_password == MASTER_PASSWORD
    if fac["password"] != old_password and not master_ok:
        raise HTTPException(403, "Current password is incorrect")
    fac["password"] = new_password
    _persist_facilitators()
    return {"status": "success", "message": "Password updated successfully"}


@admin_router.post("/facilitators/{fac_id}/reset-password", summary="Admin reset facilitator password")
async def admin_reset_facilitator_password(fac_id: str):
    """God Mode one-click password reset. Generates a new random password."""
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    import random, string
    new_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    fac["password"] = new_pw
    _persist_facilitators()
    return {"status": "success", "new_password": new_pw, "facilitator_id": fac_id}


@admin_router.put("/facilitators/{fac_id}/cohort-limit", summary="Update facilitator cohort limit")
async def update_cohort_limit(fac_id: str, body: dict = Body(...)):
    max_cohorts = body.get("max_cohorts")
    if max_cohorts is None or not isinstance(max_cohorts, int) or max_cohorts < 0:
        raise HTTPException(400, "max_cohorts must be a non-negative integer")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    fac["max_cohorts"] = max_cohorts
    _persist_facilitators()
    return fac


@admin_router.put("/facilitators/{fac_id}/enabled", summary="Enable or disable a facilitator")
async def toggle_facilitator_enabled(fac_id: str, body: dict = Body(...)):
    enabled = body.get("enabled")
    if enabled is None or not isinstance(enabled, bool):
        raise HTTPException(400, "'enabled' must be a boolean")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    fac["enabled"] = enabled
    _persist_facilitators()
    return fac


# check_and_increment_cohort_count imported from admin_shared


# ═════════════════════════════════════════════════════════════════
#  PRACTICE MODE — Dry-run up to Round 2, then reset
# ═════════════════════════════════════════════════════════════════

# In-memory practice mode flags: {session_id: True}
# _practice_mode imported from admin_shared


@admin_router.post("/sessions/{session_id}/practice-mode", summary="Enable practice mode for a cohort")
async def enable_practice_mode(session_id: str):
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    _practice_mode[session_id] = True
    # Broadcast to players
    await manager.push_to_session(session_id, {
        "type": "practice_mode_changed",
        "practice_mode": True,
    })
    return {"status": "enabled", "session_id": session_id, "practice_mode": True}


@admin_router.delete("/sessions/{session_id}/practice-mode", summary="Disable practice mode for a cohort")
async def disable_practice_mode(session_id: str):
    _practice_mode.pop(session_id, None)
    return {"status": "disabled", "session_id": session_id, "practice_mode": False}


@admin_router.get("/sessions/{session_id}/practice-mode", summary="Get practice mode status")
async def get_practice_mode(session_id: str):
    return {"practice_mode": _practice_mode.get(session_id, False)}


# is_practice_mode imported from admin_shared



# ═════════════════════════════════════════════════════════════════
#  WEBSOCKET CONNECTION MANAGER
# ═════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manages WebSocket connections for real-time push to players."""

    def __init__(self):
        # session_id → list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Admin connections for dashboard updates
        self.admin_connections: list[WebSocket] = []

    async def connect_player(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.setdefault(session_id, []).append(websocket)

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)

    def disconnect_player(self, websocket: WebSocket, session_id: str):
        conns = self.active_connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def push_to_session(self, session_id: str, message: dict):
        """Push a message to all player connections in a session."""
        payload = json.dumps(message)
        conns = self.active_connections.get(session_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)

    async def broadcast_admin(self, message: dict):
        """Broadcast to all admin dashboard connections."""
        payload = json.dumps(message)
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.admin_connections.remove(ws)

    async def broadcast_students(self, message: dict):
        """Broadcast to all player connections."""
        payload = json.dumps(message)
        for session_id, conns in list(self.active_connections.items()):
            dead = []
            for ws in conns:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                conns.remove(ws)

    async def broadcast(self, message: dict):
        """Broadcast to ALL connected clients (players + admins)."""
        payload = json.dumps(message)
        # Send to all player sessions
        for session_id, conns in list(self.active_connections.items()):
            dead = []
            for ws in conns:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                conns.remove(ws)
        # Send to all admin connections
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.admin_connections.remove(ws)

manager = ConnectionManager()
# ═════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═════════════════════════════════════════════════════════════════

class OverrideRequest(BaseModel):
    override_type: str   # "carbon_tax", "omni_tech_poach", "force_strike"
    parameters: dict = {}


class MessageInjectRequest(BaseModel):
    session_id: str | None = None  # path param already provides this
    message_type: str = ""         # filled from preset if preset_id given
    title: str = ""
    body: str = ""
    preset_id: str | None = None


class PlayerRegisterRequest(BaseModel):
    player_name: str
    team_name: str = ""

class PlayerInductRequest(BaseModel):
    name: str
    email: str
    session_id: str
    assigned_bu: str

class MasterOverride(BaseModel):
    id: str
    icon: str
    title: str
    description: str
    color: str
    dangerLevel: str
    params: dict = {}
    scheduled_round: Optional[int] = None  # None = any round
    media_type: str = "text"   # "text" | "audio" | "video"
    media_url: str = ""

class MasterSwipe(BaseModel):
    id: str
    icon: str = "📢"
    label: str
    trigger: str
    title: str = ""
    body: str = ""
    color: str = "#6366f1"
    scheduled_round: Optional[int] = None  # None = any round
    media_type: str = "text"   # "text" | "audio" | "video"
    media_url: str = ""

# ═════════════════════════════════════════════════════════════════
#  DECISION MATRIX OVERRIDES (God Mode)
# ═════════════════════════════════════════════════════════════════

from round_configs import _get_merged_round_configs, OVERRIDES_FILE as ROUND_OVERRIDES_FILE
from pillar_configs import _get_merged_pillar_options
from healthcare_configs import _get_merged_healthcare_configs

@admin_router.get("/decision_configs", summary="Fetch merged decision configs and raw overrides")
async def get_decision_configs():
    """Returns the fully merged configuration alongside the raw JSON overrides for God Mode editing."""
    merged_narrative = _get_merged_round_configs()
    merged_pillars = _get_merged_pillar_options()
    merged_healthcare = _get_merged_healthcare_configs()
    
    raw_overrides = {"legacy_abc": {}, "multi_toggles": {}, "healthcare": {}}
    if ROUND_OVERRIDES_FILE.exists():
        try:
            with open(ROUND_OVERRIDES_FILE, "r") as f:
                raw_overrides = json.load(f)
        except Exception:
            pass
            
    return {
        "merged_narrative": merged_narrative,
        "merged_pillars": merged_pillars,
        "merged_healthcare": merged_healthcare,
        "raw_overrides": raw_overrides
    }

class OverridesUpdateRequest(BaseModel):
    paradigm: str # 'legacy_abc', 'multi_toggles', 'healthcare', 'un_sdg'
    round_number: str
    option_key: str
    area_key: str | None = None # Required for multi_toggles
    field_name: str # e.g. 'cost', 'treasury', 'revenue_delta', 'reputation'
    new_value: Any

@admin_router.put("/decision_configs", summary="Save a specific decision override")
async def update_decision_config(req: OverridesUpdateRequest):
    """
    Saves a single field override to decision_overrides.json.
    Updates in-memory dict dicts then flushes to disk.
    """
    raw_overrides = {"legacy_abc": {}, "multi_toggles": {}, "healthcare": {}}
    if ROUND_OVERRIDES_FILE.exists():
        try:
            with open(ROUND_OVERRIDES_FILE, "r") as f:
                raw_overrides = json.load(f)
        except Exception:
            pass
            
    # Drill down into the tree
    pd_dict = raw_overrides.setdefault(req.paradigm, {})
    rnd_dict = pd_dict.setdefault(str(req.round_number), {})
    
    if req.paradigm == "multi_toggles" and req.area_key:
        areas_dict = rnd_dict.setdefault("areas", {})
        area_node = areas_dict.setdefault(req.area_key, {})
        opts_dict = area_node.setdefault("options", {})
        target_dict = opts_dict.setdefault(req.option_key, {})
    elif req.paradigm in ["legacy_abc", "healthcare"]:
        opts_dict = rnd_dict.setdefault("options", {})
        target_dict = opts_dict.setdefault(req.option_key, {})
    else:
        raise HTTPException(400, "Invalid paradigm or missing area_key")
        
    # If it's an impact field, nest it inside 'impacts'
    impact_fields = ["treasury", "revenue_delta", "carbon_intensity_delta", "reputation", "resilience_factor", "natural_capital_debt_delta", "social_license_delta", "social_license_score"]
    
    if req.field_name in impact_fields:
        impacts_dict = target_dict.setdefault("impacts", {})
        impacts_dict[req.field_name] = req.new_value
    else:
        target_dict[req.field_name] = req.new_value
        
    # Save back to disk
    with open(ROUND_OVERRIDES_FILE, "w") as f:
        json.dump(raw_overrides, f, indent=4)
        
    return {"status": "success", "raw_overrides": raw_overrides}


# ═════════════════════════════════════════════════════════════════
#  ROUND PACING — Facilitator-controlled round gating
# ═════════════════════════════════════════════════════════════════

class RoundPacingRequest(BaseModel):
    mode: str = "free"              # "free" | "manual" | "timed"
    interval_seconds: int = 300     # Used when mode = "timed" (0 = immediate)
    scheduled_at: str | None = None # ISO datetime for single scheduled unlock
    schedule: list[str | None] = [] # ISO datetimes for each round (index 0 = round 1)

# Per-session pacing config: {session_id: {mode, unlocked_round, interval_seconds, timer_task}}
# _round_pacing imported from admin_shared


# _get_pacing imported from admin_shared


# is_round_unlocked imported from admin_shared


async def _auto_commit_player(player_session_id: str, current_round: int):
    """Auto-commit a single player session with default option_b."""
    try:
        import database as db
        from engine import process_tick
        from round_logic import pre_tick, post_tick, get_round_config

        current = await db.fetch_latest_state(player_session_id)
        if current is None:
            return False

        # Only auto-commit if player is still on the expected round
        if current["round_number"] != current_round:
            return False  # Already committed or ahead

        current_global = {
            "round_number": current_round,
            **current["global_state"],
        }
        current_bus = current["bu_states"]

        # Build default decisions: option_b, minimal investment
        # WARN-02 FIX: Derive BU IDs dynamically from actual session state
        # instead of hardcoding legacy_abc BUs — critical for SDG/healthcare paradigms
        bu_ids = [bu["bu_id"] for bu in current_bus] if current_bus else [
            "pharma", "electronics", "consumer_goods", "software"
        ]
        decisions_raw = [
            {
                "bu_id": bu_id,
                "investment_ratio": 0,
                "capex_allocated": 1,
                "choice_selected": "option_b",
                "decision_node_id": f"auto_round_{current_round}_{bu_id}",
                "time_to_decision_seconds": 0,
                "team_consensus": "auto_default",
                "player_id": "",
            }
            for bu_id in bu_ids
        ]

        # Pre-tick
        pre_result = pre_tick(
            round_number=current_round,
            current_global=current_global,
            current_bus=current_bus,
            decisions=decisions_raw,
            crisis_severity=0,
        )
        if "validation_error" in pre_result:
            # Skip validation errors (e.g., R2 CFO gate) — just advance
            pass

        effective_crisis = pre_result.get("crisis_severity", 0)

        # FIX AUDIT-007: Was referencing undefined `session_id` — must use `player_session_id`
        session_info = await db.get_session_info(player_session_id)
        paradigm = (session_info or {}).get("decision_paradigm", "legacy_abc")

        # Run tick engine
        tick_result = process_tick(
            current_global=current_global,
            current_bus=current_bus,
            decisions=decisions_raw,
            dividends_paid=0,
            crisis_severity=effective_crisis,
            imitation_decay_rate=0.05,
            decision_paradigm=paradigm,
        )

        new_round = tick_result["global_state"]["round_number"]
        new_global = tick_result["global_state"]
        new_bus = tick_result["bu_states"]
        events = tick_result["events"]
        events.update(pre_result.get("pre_events", {}))

        # Post-tick
        post_events = post_tick(
            round_number=current_round,
            global_state=new_global,
            bu_states=new_bus,
            decisions=decisions_raw,
            events=events,
            previous_flags=current_global.get("active_event_flags", {}),
        )
        events.update(post_events)
        events["auto_committed"] = True
        events["auto_committed_reason"] = "Scheduled timer expired — default option_b applied"
        new_global["active_event_flags"] = events

        # Clear saved decisions
        new_global.pop("saved_allocations", None)
        new_global.pop("saved_decision_choice", None)

        # Persist
        await db.insert_next_round(
            session_id=player_session_id,
            round_number=new_round,
            global_state=new_global,
            bu_states=new_bus,
            decisions=decisions_raw,
        )

        # Push notification to player
        await manager.push_to_session(player_session_id, {
            "type": "auto_committed",
            "new_round_number": new_round,
            "message": "Time expired — your turn was auto-committed with default choices.",
        })

        print(f"[AUTO-COMMIT] Player session {player_session_id[:8]}… auto-committed R{current_round}→R{new_round}")
        return True

    except Exception as exc:
        print(f"[AUTO-COMMIT ERROR] {player_session_id[:8]}…: {exc}")
        return False


async def _scheduled_unlock_task(session_id: str, delay_seconds: int):
    """Background task: auto-commit lagging players, then unlock next round after `delay_seconds`."""
    try:
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        pacing = _round_pacing.get(session_id)
        if not pacing or pacing["mode"] != "timed":
            return

        current_unlocked = pacing["unlocked_round"]

        # ── Auto-commit lagging players ──────────────────────────
        # Find all player sub-sessions for this cohort
        from router import _session_players
        import database as db

        player_entries = _session_players.get(session_id, [])
        auto_committed_count = 0

        for player_entry in player_entries:
            player_sid = player_entry.get("player_session_id")
            if not player_sid:
                continue

            # Check if this player is still on the current round
            try:
                latest = await db.fetch_latest_state(player_sid)
                if latest and latest["round_number"] == current_unlocked:
                    # NEW-11: Only auto-commit players who are STILL on the current round
                    # (== current_unlocked). Players who already committed have round_number
                    # > current_unlocked and must NOT be auto-committed again.
                    success = await _auto_commit_player(player_sid, latest["round_number"])
                    if success:
                        auto_committed_count += 1
            except Exception as exc:
                print(f"[AUTO-COMMIT] Failed to check/commit {player_sid[:8]}…: {exc}")

        if auto_committed_count > 0:
            print(f"[SCHEDULED] Auto-committed {auto_committed_count} player(s) for cohort {session_id[:8]}…")

        # ── Now unlock next round ────────────────────────────────
        pacing["unlocked_round"] = current_unlocked + 1
        pacing["next_unlock_at"] = None

        # Broadcast to players
        await manager.push_to_session(session_id, {
            "type": "round_unlocked",
            "unlocked_round": pacing["unlocked_round"],
            "mode": "timed",
            "auto_committed": auto_committed_count,
        })
        await manager.broadcast_admin({
            "type": "pacing_update",
            "session_id": session_id,
            "unlocked_round": pacing["unlocked_round"],
            "mode": "timed",
            "auto_committed": auto_committed_count,
        })
    except asyncio.CancelledError:
        pass


async def _multi_round_unlock_task(session_id: str, round_number: int, delay_seconds: float):
    """Background task: unlock a specific round at a scheduled time."""
    try:
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        pacing = _round_pacing.get(session_id)
        if not pacing or pacing["mode"] != "timed":
            return

        # Only advance if we haven't already passed this round
        if pacing["unlocked_round"] >= round_number:
            return

        pacing["unlocked_round"] = round_number

        # Broadcast unlock to players and admin
        await manager.push_to_session(session_id, {
            "type": "round_unlocked",
            "unlocked_round": round_number,
            "mode": "timed",
        })
        await manager.broadcast_admin({
            "type": "pacing_update",
            "session_id": session_id,
            "unlocked_round": round_number,
            "mode": "timed",
        })
        print(f"[SCHEDULED] Round {round_number} unlocked for session {session_id[:8]}…")
    except asyncio.CancelledError:
        pass


@admin_router.get("/sessions/{session_id}/pacing", summary="Get round pacing config")
async def get_pacing(session_id: str):
    pacing = _get_pacing(session_id)
    return {
        "mode": pacing["mode"],
        "unlocked_round": pacing["unlocked_round"],
        "interval_seconds": pacing["interval_seconds"],
        "next_unlock_at": pacing.get("next_unlock_at"),
        "schedule": pacing.get("schedule", []),
    }


@admin_router.post("/sessions/{session_id}/pacing", summary="Set round pacing mode")
async def set_pacing(session_id: str, body: RoundPacingRequest):
    pacing = _get_pacing(session_id)

    # Cancel existing single-shot timer if any
    if pacing.get("_timer_task") and not pacing["_timer_task"].done():
        pacing["_timer_task"].cancel()
        pacing["_timer_task"] = None

    # Cancel all multi-round timer tasks
    for task in pacing.get("_timer_tasks", []):
        if task and not task.done():
            task.cancel()
    pacing["_timer_tasks"] = []

    pacing["mode"] = body.mode
    pacing["interval_seconds"] = body.interval_seconds

    if body.mode == "free":
        pacing["unlocked_round"] = 999
        pacing["next_unlock_at"] = None
        pacing["schedule"] = []
    elif body.mode == "manual":
        pacing["unlocked_round"] = max(pacing["unlocked_round"], 1)
        pacing["next_unlock_at"] = None
        pacing["schedule"] = []
    elif body.mode == "timed":
        pacing["unlocked_round"] = max(pacing["unlocked_round"], 1)

        # ── Multi-round schedule (new feature) ──────────────────
        if body.schedule:
            pacing["schedule"] = list(body.schedule)
            now = datetime.now(timezone.utc)
            for round_idx, scheduled_iso in enumerate(body.schedule):
                if not scheduled_iso:
                    continue
                round_number = round_idx + 1
                try:
                    target = datetime.fromisoformat(scheduled_iso.replace("Z", "+00:00"))
                    if target.tzinfo is None:
                        target = target.replace(tzinfo=timezone.utc)
                    delay = max(0.0, (target - now).total_seconds())
                    task = asyncio.create_task(
                        _multi_round_unlock_task(session_id, round_number, delay)
                    )
                    pacing["_timer_tasks"].append(task)
                except Exception as exc:
                    print(f"[PACING] Could not schedule round {round_number}: {exc}")
            # Set next_unlock_at to the first future datetime in the schedule
            first_future = next(
                (s for s in body.schedule if s), None
            )
            pacing["next_unlock_at"] = first_future

        # ── Single-shot (legacy) ────────────────────────────────
        elif body.interval_seconds == 0:
            pacing["unlocked_round"] += 1
            pacing["next_unlock_at"] = None
            pacing["schedule"] = []
        else:
            from datetime import timedelta
            if body.scheduled_at:
                pacing["next_unlock_at"] = body.scheduled_at
            else:
                unlock_time = datetime.now(timezone.utc) + timedelta(seconds=body.interval_seconds)
                pacing["next_unlock_at"] = unlock_time.isoformat()
            pacing["schedule"] = []
            pacing["_timer_task"] = asyncio.create_task(
                _scheduled_unlock_task(session_id, body.interval_seconds)
            )

    # Broadcast mode change to player sessions
    await manager.push_to_session(session_id, {
        "type": "pacing_mode_changed",
        "mode": pacing["mode"],
        "unlocked_round": pacing["unlocked_round"],
        "interval_seconds": pacing["interval_seconds"],
        "schedule": pacing.get("schedule", []),
    })
    # Event Bus: Notify all connected admin dashboards of pacing override
    await manager.broadcast_admin({
        "type": "pacing_override",
        "session_id": session_id,
        "new_mode": pacing["mode"],
        "unlocked_round": pacing["unlocked_round"],
        "source": "god_mode",
    })

    return {
        "mode": pacing["mode"],
        "unlocked_round": pacing["unlocked_round"],
        "interval_seconds": pacing["interval_seconds"],
        "next_unlock_at": pacing.get("next_unlock_at"),
        "schedule": pacing.get("schedule", []),
    }


@admin_router.post("/sessions/{session_id}/pacing/unlock", summary="Manually unlock next round")
async def unlock_next_round(session_id: str):
    pacing = _get_pacing(session_id)
    pacing["unlocked_round"] = pacing["unlocked_round"] + 1

    # Broadcast to players
    await manager.push_to_session(session_id, {
        "type": "round_unlocked",
        "unlocked_round": pacing["unlocked_round"],
        "mode": pacing["mode"],
    })
    await manager.broadcast_admin({
        "type": "pacing_update",
        "session_id": session_id,
        "unlocked_round": pacing["unlocked_round"],
        "mode": pacing["mode"],
    })

    return {
        "unlocked_round": pacing["unlocked_round"],
        "mode": pacing["mode"],
    }


# ═════════════════════════════════════════════════════════════════
#  PLAYER REGISTRY & MASTER INTERVENTIONS
# ═════════════════════════════════════════════════════════════════

# _player_registry imported from admin_shared
_next_player_id: int = 1

# _session_interventions imported from admin_shared

class SessionInterventionsRequest(BaseModel):
    allowed_overrides: list[str]
    allowed_swipes: list[str]
    override_rounds: dict[str, Optional[int]] = {}  # {override_id: round_number or null}
    swipe_rounds: dict[str, Optional[int]] = {}      # {swipe_id: round_number or null}

@admin_router.get("/{session_id}/interventions", summary="Get permitted interventions for a session")
async def get_session_interventions(session_id: str):
    # If not cached in-memory, try to recover from persisted global_state
    if session_id not in _session_interventions:
        try:
            latest = await db.fetch_latest_state(session_id)
            if latest:
                flags = latest.get("global_state", {}).get("active_event_flags", {})
                persisted_ovs = flags.get("allowed_overrides")
                persisted_sws = flags.get("allowed_swipes")
                if persisted_ovs is not None or persisted_sws is not None:
                    # Re-hydrate the in-memory cache from persisted state
                    _session_interventions[session_id] = {
                        "allowed_overrides": persisted_ovs or [],
                        "allowed_swipes": persisted_sws or [],
                    }
        except Exception:
            pass  # Fall through to default

    # Still not found → default: everything is allowed (backwards compat)
    if session_id not in _session_interventions:
        return {
            "overrides": _master_overrides,
            "swipes": _master_swipes
        }

    perms = _session_interventions[session_id]

    # Return full objects for allowed IDs
    allowed_ovs = [o for o in _master_overrides if o["id"] in perms.get("allowed_overrides", [])]
    allowed_sws = [s for s in _master_swipes if s["id"] in perms.get("allowed_swipes", [])]
    return {
        "overrides": allowed_ovs,
        "swipes": allowed_sws,
        "override_rounds": perms.get("override_rounds", {}),
        "swipe_rounds": perms.get("swipe_rounds", {}),
    }

@admin_router.put("/{session_id}/interventions", summary="Set permitted interventions for a session")
async def set_session_interventions(session_id: str, req: SessionInterventionsRequest):
    _session_interventions[session_id] = {
        "allowed_overrides": req.allowed_overrides,
        "allowed_swipes": req.allowed_swipes,
        "override_rounds": req.override_rounds,
        "swipe_rounds": req.swipe_rounds,
    }

    # Persist into global_state so it survives server restarts
    try:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            gs = latest["global_state"]
            flags = gs.get("active_event_flags", {})
            flags["allowed_overrides"] = req.allowed_overrides
            flags["allowed_swipes"] = req.allowed_swipes
            flags["override_rounds"] = req.override_rounds
            flags["swipe_rounds"] = req.swipe_rounds
            gs["active_event_flags"] = flags
            await db.update_latest_global_state(session_id, gs, latest["bu_states"])
    except Exception:
        pass  # Non-critical: in-memory cache is still set

    return _session_interventions[session_id]


# ── Decade Forward Plan ─────────────────────────────────────────

class DecadePlanRequest(BaseModel):
    boardroom_choice: str  # "resist_integrate" | "strategic_spinoff" | "aggressive_divestment"
    decade_forward_plan: str

@admin_router.post("/{session_id}/decade-plan", summary="Save boardroom choice and decade forward plan")
async def save_decade_plan(session_id: str, req: DecadePlanRequest):
    ok = await db.save_decade_plan(session_id, req.boardroom_choice, req.decade_forward_plan)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "saved", "boardroom_choice": req.boardroom_choice}

@admin_router.get("/{session_id}/decade-plan", summary="Get decade forward plan")
async def get_decade_plan(session_id: str):
    result = await db.get_decade_plan(session_id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@admin_router.get("/players", summary="List all registered players")
async def list_players():
    global _player_registry
    # If registry is empty but sessions have registered_players, rebuild it
    if not _player_registry:
        all_sessions = await db.fetch_all_sessions()
        for sess in all_sessions:
            for p in sess.get("registered_players", []):
                if not any(r["player_id"] == p["player_id"] for r in _player_registry):
                    _player_registry.append(p)
                    
    all_sessions_now = await db.fetch_all_sessions()
    active_ids = {s["session_id"] for s in all_sessions_now}
    
    active_players = []
    for p in _player_registry:
        if not p.get("deleted_at"):
            p_dict = dict(p)
            p_dict["is_orphan"] = p_dict.get("session_id") not in active_ids
            # ── Resolve display name from multiple sources ──
            # Priority: name (from induct/login) → username (from set-username) → player_name
            if not p_dict.get("name"):
                p_dict["name"] = p_dict.get("username") or p_dict.get("player_name") or ""
            active_players.append(p_dict)
            
    return {"players": active_players}


@admin_router.put("/{session_id}/public-status", summary="Toggle session public visibility")
async def toggle_public_status(session_id: str, req: dict = Body(...)):
    is_public = req.get("is_public", False)
    success = await db.set_session_public(session_id, is_public)
    if not success:
        raise HTTPException(404, "Session not found")
    # Broadcast to admin so leaderboards update in real time
    await manager.broadcast_admin({"type": "session_public_toggled", "session_id": session_id, "is_public": is_public})
    return {"status": "updated", "is_public": is_public}


class MaterialityDictionaryOverrideRequest(BaseModel):
    issues: list[dict]
    interdependencies: list[dict]
    consultant_fee_usd: Optional[int] = 1500000

@admin_router.put("/{session_id}/materiality-dictionary", summary="Override the full materiality dictionary for a cohort")
async def override_materiality_dictionary(session_id: str, req: MaterialityDictionaryOverrideRequest):
    """
    Saves a complete sandboxed copy of the materiality dictionary for this session.
    Overrides global settings dynamically for this cohort.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    global_state = current["global_state"]
    bu_states = current["bu_states"]
    
    global_state["materiality_dictionary_override"] = req.dict()
    
    # Clean up the old deprecated field if it exists
    if "materiality_cost_overrides" in global_state:
        del global_state["materiality_cost_overrides"]
        
    await db.update_latest_global_state(session_id, global_state, bu_states)
    return {"status": "success", "message": "Cohort-specific dictionary enabled."}

@admin_router.delete("/{session_id}/materiality-dictionary", summary="Revert cohort to God Mode dictionary")
async def revert_materiality_dictionary(session_id: str):
    """
    Removes the sandbox dictionary, reverting the cohort to God Mode defaults.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    global_state = current["global_state"]
    bu_states = current["bu_states"]
    
    if "materiality_dictionary_override" in global_state:
        del global_state["materiality_dictionary_override"]
        
    await db.update_latest_global_state(session_id, global_state, bu_states)
    return {"status": "success", "message": "Reverted to God Mode defaults."}


@admin_router.post("/players/register", summary="Register a new player")
async def register_player(req: PlayerRegisterRequest):
    global _next_player_id
    player = {
        "player_id": f"P{_next_player_id:03d}",
        "player_name": req.player_name,
        "team_name": req.team_name,
        "session_id": None,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "status": "waiting",
    }
    _next_player_id += 1
    _player_registry.append(player)
    # Broadcast to admin
    await manager.broadcast_admin({
        "type": "player_registered",
        "player": player,
    })
    return player

_ADJECTIVES = ["blue", "swift", "brave", "quiet", "lucky", "bold", "calm", "proud", "wild", "smart"]
_NOUNS = ["rhino", "eagle", "tiger", "panda", "fox", "bear", "wolf", "lion", "hawk", "owl"]

@admin_router.post("/players/induct", summary="Induct a player directly into a session")
async def induct_player(req: PlayerInductRequest):
    global _next_player_id
    
    # Check for duplicate name within the same cohort
    existing_names = [
        p["name"].strip().lower()
        for p in _player_registry
        if p.get("session_id") == req.session_id
    ]
    if req.name.strip().lower() in existing_names:
        raise HTTPException(
            status_code=400,
            detail=f"A player named '{req.name}' is already registered in this cohort. Please use a different name."
        )
    
    # Generate MUR-XXX ID
    generated_id = f"MUR-{_next_player_id:03d}"
    _next_player_id += 1
    
    # Default password
    generated_password = "123"
    
    player = {
        "player_id": generated_id,
        "name": req.name,
        "email": req.email,
        "assigned_bu": req.assigned_bu,
        "session_id": req.session_id,
        "password": generated_password, # Stored temporarily for the admin to copy
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "playing",
    }
    
    _player_registry.append(player)
    
    # Register the player ID in the session's allowed list
    try:
        sess = await db.get_session_info(req.session_id)
        if sess:
            allowed = sess.get("allowed_player_ids", [])
            if generated_id not in allowed:
                allowed.append(generated_id)
                sess["allowed_player_ids"] = allowed
    except Exception:
        pass  # Non-critical
    
    # Broadcast to admin
    await manager.broadcast_admin({
        "type": "player_registered",
        "player": player,
    })
    
    return player




@admin_router.post("/players/{player_id}/assign", summary="Assign a player to a session")
async def assign_player_to_session(player_id: str, session_id: str):
    player = next((p for p in _player_registry if p["player_id"] == player_id), None)
    if not player:
        raise HTTPException(404, f"Player {player_id} not found")
    player["session_id"] = session_id
    player["status"] = "playing"
    await manager.broadcast_admin({
        "type": "player_assigned",
        "player_id": player_id,
        "session_id": session_id,
    })
    return player


@admin_router.delete("/players/{player_id}", summary="Remove a player")
async def remove_player(player_id: str):
    global _player_registry
    before = len(_player_registry)
    _player_registry = [p for p in _player_registry if p["player_id"] != player_id]
    if len(_player_registry) == before:
        raise HTTPException(404, f"Player {player_id} not found")
    await manager.broadcast_admin({
        "type": "player_removed",
        "player_id": player_id,
    })
    return {"status": "removed", "player_id": player_id}


@admin_router.delete("/players", summary="Clear all registered players")
async def clear_all_players():
    global _player_registry, _next_player_id
    count = len(_player_registry)
    _player_registry = []
    _next_player_id = 1
    await manager.broadcast_admin({"type": "players_cleared"})
    return {"status": "cleared", "players_removed": count}


@admin_router.delete("/sessions/{session_id}", summary="Delete a session/cohort")
async def delete_session(session_id: str, hard: bool = False):
    """Remove a session and all associated players from the registry."""
    global _player_registry
    deleted = await db.delete_session(session_id, hard=hard)
    if not deleted:
        raise HTTPException(404, "Session not found")
        
    children = await db.get_child_sessions(session_id)
    for child in children:
        await db.delete_session(child["session_id"], hard=hard)
        
    # Remove associated players if hard delete, otherwise soft delete them
    if hard:
        before = len(_player_registry)
        _player_registry = [p for p in _player_registry if p.get("session_id") != session_id]
        removed_players = before - len(_player_registry)
    else:
        now_str = datetime.now(timezone.utc).isoformat()
        removed_players = 0
        for p in _player_registry:
            if p.get("session_id") == session_id and not p.get("deleted_at"):
                p["deleted_at"] = now_str
                removed_players += 1
                
    await manager.broadcast_admin({"type": "session_deleted", "session_id": session_id})
    return {"status": "deleted", "session_id": session_id, "players_removed": removed_players}


@admin_router.delete("/players/orphans", summary="Clear orphaned players whose session no longer exists")
async def clear_orphan_players():
    """Remove all players whose session_id doesn't match any active session."""
    global _player_registry
    active_sessions = await db.fetch_all_sessions()
    active_ids = {s["session_id"] for s in active_sessions}
    before = len(_player_registry)
    _player_registry = [p for p in _player_registry if p.get("session_id") in active_ids or p.get("session_id") == ""]
    removed = before - len(_player_registry)
    return {"status": "cleared", "orphans_removed": removed}


@admin_router.put("/players/set-password", summary="Set or update a player's password")
async def set_player_password(body: dict = Body(...)):
    """Fallback for setting a player password when it's generated client-side."""
    player_id = body.get("player_id")
    password = body.get("password")
    if not player_id or not password:
        raise HTTPException(400, "player_id and password are required")
    
    player = next((p for p in _player_registry if p["player_id"] == player_id), None)
    if player:
        player["password"] = password
    else:
        # Create a minimal registry entry
        _player_registry.append({
            "player_id": player_id,
            "name": "",
            "email": "",
            "assigned_bu": "",
            "session_id": "",
            "password": password,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "id_generated",
        })
    return {"status": "success"}


# ═════════════════════════════════════════════════════════════════
#  SWIPE FILE PRESETS
# ═════════════════════════════════════════════════════════════════

SWIPE_FILE_PRESETS: list[dict[str, Any]] = [
    {
        "id": "activist_threat",
        "label": "🗡️ The Activist Threat",
        "trigger": "Hoarding Cash",
        "type": "warning",
        "title": "⚠️ Activist Investor Notice",
        "body": (
            "An activist fund has acquired 8% of outstanding shares. They "
            "are publicly demanding a special dividend or strategic "
            "acquisition. The board is meeting in 48 hours."
        ),
    },
    {
        "id": "cfo_liquidity_panic",
        "label": "💸 CFO Liquidity Panic",
        "trigger": "Draining Cash",
        "type": "warning",
        "title": "🏦 CFO Emergency Briefing",
        "body": (
            "Our credit facility covenant requires maintaining a 1.5x "
            "coverage ratio. Current projections show breach within 2 "
            "periods. Immediate cost reduction or capital raise required."
        ),
    },
    {
        "id": "chro_resignation",
        "label": "🚪 CHRO Resignation",
        "trigger": "Low Reputation",
        "type": "admin",
        "title": "📋 CHRO Resignation Letter",
        "body": (
            "The Chief Human Resources Officer has submitted their "
            "resignation, citing 'irreconcilable differences in people "
            "strategy.' Talent pipelines across all BUs are at risk."
        ),
    },
    {
        "id": "regulatory_probe",
        "label": "🔍 Regulatory Probe",
        "trigger": "High Governance Risk",
        "type": "warning",
        "title": "⚖️ Regulatory Investigation Notice",
        "body": (
            "The Competition Authority has opened a formal investigation "
            "into pricing practices in the Electronics division. Legal "
            "costs are estimated at $3M–$7M."
        ),
    },
    {
        "id": "media_expose",
        "label": "📰 Media Exposé",
        "trigger": "Low Social License",
        "type": "warning",
        "title": "📡 Breaking: Investigative Report",
        "body": (
            "A major newspaper is running a Sunday front-page exposé on "
            "working conditions in your supply chain. Social media "
            "sentiment has turned sharply negative."
        ),
    },
    {
        "id": "partnership_offer",
        "label": "🤝 Strategic Partnership",
        "trigger": "God Mode Positive",
        "type": "narrative",
        "title": "🌍 UN Global Compact Invitation",
        "body": (
            "The UN has invited Muressons to join the Global Compact "
            "Leadership Circle. Acceptance would boost reputation by +10 "
            "but requires a public commitment to science-based targets."
        ),
    },
    {
        "id": "black_swan_pandemic",
        "label": "🦠 Black Swan: Pandemic",
        "trigger": "God Mode Chaos",
        "type": "warning",
        "title": "🦠 Pandemic Supply Shock",
        "body": (
            "A novel pathogen has triggered port closures across SE Asia. "
            "Pharma revenue may spike +20% but Electronics supply chain "
            "is disrupted. Consumer Goods logistics frozen for 1 round."
        ),
    },
    {
        "id": "whistleblower",
        "label": "🔔 Whistleblower",
        "trigger": "Ethics Violation",
        "type": "admin",
        "title": "🔔 Anonymous Whistleblower Report",
        "body": (
            "An internal whistleblower has filed a report alleging "
            "systematic underreporting of Scope 1 emissions at the "
            "Electronics facility. External auditors have been notified."
        ),
    },
]


# ═════════════════════════════════════════════════════════════════
#  OVERRIDE LOGIC
# ═════════════════════════════════════════════════════════════════

OVERRIDE_HANDLERS: dict[str, Any] = {}


def _apply_carbon_tax_override(global_state: dict, params: dict) -> dict[str, Any]:
    """Toggle Year 5 Carbon Tax from $250/ton to $400/ton."""
    new_rate = params.get("new_rate", 400)
    flags = global_state.get("active_event_flags", {})
    flags["carbon_tax_per_ton"] = new_rate
    flags["carbon_tax_override_active"] = True
    global_state["active_event_flags"] = flags
    # Apply immediate cost increase proportional to carbon intensity
    return {
        "override": "carbon_tax",
        "new_rate": new_rate,
        "message": f"Global Macro Shift: Carbon tax raised to ${new_rate}/ton",
    }


def _apply_omni_tech_poach(global_state: dict, params: dict) -> dict[str, Any]:
    """Raise Rep_Threshold from 65 to 75, forcing brain-drain spike."""
    new_threshold = params.get("new_threshold", 75)
    flags = global_state.get("active_event_flags", {})
    flags["brain_drain_threshold"] = new_threshold
    flags["omni_tech_poach_active"] = True
    global_state["active_event_flags"] = flags
    return {
        "override": "omni_tech_poach",
        "new_threshold": new_threshold,
        "message": (
            f"Omni-Tech Poach: Talent retention threshold raised to "
            f"{new_threshold}. Software BU OPEX penalty will spike."
        ),
    }


def _apply_force_strike(
    global_state: dict, bu_states: list[dict], params: dict
) -> dict[str, Any]:
    """Force a guaranteed labour strike — zero out all BU revenue."""
    flags = global_state.get("active_event_flags", {})
    flags["force_strike_active"] = True
    global_state["active_event_flags"] = flags

    revenue_before = {}
    for bu in bu_states:
        revenue_before[bu["bu_id"]] = bu["revenue_base"]
        bu["revenue_base"] = 0

    return {
        "override": "force_strike",
        "revenue_zeroed": revenue_before,
        "message": (
            "Forced Strike: All BU revenue zeroed for the current round. "
            "Workers have walked out across all facilities."
        ),
    }


# ═════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/sessions",
    summary="List all active sessions for leaderboard",
)
async def list_sessions(facilitator_id: Optional[str] = None):
    """Returns all sessions with their latest state for the leaderboard."""
    sessions = await db.fetch_all_sessions()
    
    if facilitator_id:
        sessions = [
            s for s in sessions 
            if s.get("facilitator_id") == facilitator_id
        ]
        
    return {"sessions": sessions}




@admin_router.post(
    "/{session_id}/generate-player",
    summary="Generate a new allowed player ID and password",
)
async def generate_player_id(session_id: str):
    player_id = await db.generate_player_id(session_id)
    if not player_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # Default password
    generated_password = "123"
    
    player_entry = {
        "player_id": player_id,
        "name": "",
        "email": "",
        "assigned_bu": "",
        "session_id": session_id,
        "password": generated_password,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "id_generated",
    }
    
    # Register in player registry for password validation
    global _player_registry
    _player_registry.append(player_entry.copy())
    
    # Also persist in the session metadata so it survives page refreshes
    sess = await db.get_session_info(session_id)
    if sess:
        if "registered_players" not in sess:
            sess["registered_players"] = []
        sess["registered_players"].append(player_entry.copy())
    
    return {"status": "success", "player_id": player_id, "password": generated_password}


@admin_router.get(
    "/leaderboard",
    summary="Get leaderboard data for all active sessions",
)
async def get_leaderboard(facilitator_id: Optional[str] = None):
    """
    Returns computed leaderboard metrics for each player session:
    terminal value projection, total cash, synergy, risk heatmap,
    and talent flight risk.
    """
    sessions = await db.fetch_all_sessions()
    leaderboard = []

    for sess in sessions:
        sid = sess["session_id"]
        latest = await db.fetch_latest_state(sid)
        if not latest:
            continue

        # Skip cohort template sessions (those without a player_id)
        # unless they have no parent (legacy solo sessions)
        player_id = sess.get("player_id")

        if facilitator_id and sess.get("facilitator_id") != facilitator_id:
            continue

        gs = latest["global_state"]
        bus = latest["bu_states"]

        # Compute metrics
        total_revenue = sum(bu["revenue_base"] for bu in bus)
        total_opex = sum(bu["opex_base"] for bu in bus)
        synergy = gs.get("synergy_multiplier", 1.0)

        # Terminal Value projection: Treasury + (Rev - OPEX) * Synergy * 5
        terminal_value = round(
            gs.get("corporate_treasury", 0)
            + (total_revenue - total_opex) * synergy * 5,
            2,
        )

        # Risk heatmap values
        avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus) / len(bus) if bus else 0
        avg_sl = sum(bu.get("social_license_score", 50) for bu in bus) / len(bus) if bus else 50

        # Brain-drain talent flight risk
        software_bu = next((bu for bu in bus if bu["bu_id"] == "software"), None)
        talent_penalty = 1.0
        if software_bu:
            threshold = gs.get("active_event_flags", {}).get("brain_drain_threshold", 65)
            rep = gs.get("group_reputation", 50)
            talent_penalty = round(1.0 + max(0.0, (threshold - rep) / 100.0) * 1.5, 4)

        # Fetch history for inline sparkline
        history = await db.fetch_round_history(sid)
        sparkline_data = []
        if history:
            for h in sorted(history, key=lambda x: x.get('round_number', 0)):
                h_gs = h.get('global_state', {})
                h_bus = h.get('bu_states', [])
                h_rev = sum(bu.get('revenue_base', 0) for bu in h_bus)
                h_op = sum(bu.get('opex_base', 0) for bu in h_bus)
                h_syn = h_gs.get('synergy_multiplier', 1.0)
                h_tv = round(h_gs.get('corporate_treasury', 0) + (h_rev - h_op) * h_syn * 5, 2)
                sparkline_data.append(h_tv)
        if not sparkline_data:
            sparkline_data = [terminal_value]

        leaderboard.append({
            "sparkline": sparkline_data,
            "session_id": sid,
            "short_code": sess.get("short_code"),
            "cohort_name": sess.get("cohort_name", "Unknown"),
            "facilitator_id": sess.get("facilitator_id"),
            "player_id": player_id,
            "decision_paradigm": _get_session_paradigm(sid),
            "round_number": latest["round_number"],
            "terminal_value": terminal_value,
            "total_cash": gs.get("corporate_treasury", 0),
            "group_synergy": synergy,
            "group_reputation": gs.get("group_reputation", 50),
            "bonus_score": gs.get("bonus_score", 0),
            "avg_natural_capital_debt": round(avg_ncd, 2),
            "avg_social_license": round(avg_sl, 2),
            "talent_flight_risk": talent_penalty > 1.25,
            "talent_penalty_multiplier": talent_penalty,
            "active_flags": list(gs.get("active_event_flags", {}).keys()),
            # Cohort configuration fields for SimulationManager dropdown
            "experience_level": sess.get("experience_level"),
            "scenario_preset": sess.get("scenario_preset"),
            "currency_symbol": sess.get("currency_symbol", "$"),
            "difficulty_tier": sess.get("difficulty_tier", "advanced"),
            "ending_pathway": gs.get("active_event_flags", {}).get("ending_pathway"),
            "pedagogical_overrides": sess.get("pedagogical_overrides", {}),
            "ceo_interview_enabled": sess.get("ceo_interview_enabled", False),
            "ceo_interview_voice_gender": sess.get("ceo_interview_voice_gender", "female"),
            "side_tracks": sess.get("side_tracks", []),
            "created_by": sess.get("created_by"),
            "created_when": sess.get("created_when"),
            "start_date": sess.get("start_date"),
            "end_date": sess.get("end_date"),
            "pacing_mode": sess.get("pacing_mode", "free_play"),
            "max_unlocked_round": sess.get("max_unlocked_round", 10),
        })

    # Sort by terminal value descending
    leaderboard.sort(key=lambda x: x["terminal_value"], reverse=True)
    return {"leaderboard": leaderboard}


# ─────────────────────────────────────────────────────────────────
#  SESSION REPORT ENDPOINT
#  Full per-session analytics aggregation for the Reports tab.
#  Includes KPIs, CEO scores, sandbox burden, side-tracks, history.
# ─────────────────────────────────────────────────────────────────

@admin_router.get(
    "/session-report/{session_id}",
    summary="Full performance analytics for a single session",
)
async def get_session_report(session_id: str):
    """
    Returns a comprehensive analytics report for a session:
    - Final KPIs (treasury, reputation, CO2, SLO, NCD, synergy, M_R)
    - CEO interview scores (all 6 dimensions) if completed
    - Regulatory sandbox compliance burden history
    - Side-track completion and scores
    - Round-by-round KPI history for sparklines / trend analysis
    - Archetype classification and ending pathway
    """
    from fastapi import HTTPException  # noqa (local import — avoids circular at module level)

    session_info = await db.get_session_info(session_id)
    if session_info is None:
        raise HTTPException(status_code=404, detail="Session not found")

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No state found for session")


    gs = latest.get("global_state", {})
    bus = latest.get("bu_states", [])
    flags = gs.get("active_event_flags", {})
    round_number = latest.get("round_number", 1)

    # ── Core KPIs ─────────────────────────────────────────────────
    total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
    total_opex = sum(bu.get("opex_base", 0) for bu in bus)
    synergy = gs.get("synergy_multiplier", 1.0)
    treasury = gs.get("corporate_treasury", 0)
    reputation = gs.get("group_reputation", 50)
    terminal_value = round(treasury + (total_rev - total_opex) * synergy * 5, 2)
    avg_slo = round(sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1), 2)
    avg_ncd = round(sum(bu.get("natural_capital_debt", 0) for bu in bus) / max(len(bus), 1), 2)
    avg_ci = round(sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1), 2)
    total_tco2 = round(sum(bu.get("tco2e_emissions", 0) for bu in bus), 2)
    mr = round(flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)), 4)
    archetype = flags.get("profile_title", gs.get("profile_title", "In Progress"))
    ending_pathway = flags.get("ending_pathway", "N/A")

    # ── BU-level breakdown ─────────────────────────────────────────
    bu_summary = []
    for bu in bus:
        bu_summary.append({
            "bu_id": bu.get("bu_id"),
            "bu_name": bu.get("bu_name", bu.get("bu_id", "Unknown")),
            "revenue": bu.get("revenue_base", 0),
            "opex": bu.get("opex_base", 0),
            "margin_pct": round((bu.get("revenue_base", 0) - bu.get("opex_base", 0)) / max(bu.get("revenue_base", 1), 1) * 100, 1),
            "carbon_intensity": bu.get("carbon_intensity", 50),
            "tco2e_emissions": bu.get("tco2e_emissions", 0),
            "social_license_score": bu.get("social_license_score", 50),
            "natural_capital_debt": bu.get("natural_capital_debt", 0),
            "governance_risk_score": bu.get("governance_risk_score", 20),
            "staff_burnout_index": bu.get("staff_burnout_index", 0),
        })

    # ── CEO Interview ──────────────────────────────────────────────
    ceo_interview = None
    if flags.get("ceo_interview_completed"):
        ceo_interview = {
            "completed": True,
            "final_scores": flags.get("ceo_interview_scores", {}),
            "data_scores": flags.get("ceo_interview_data_scores", {}),
            "response_scores": flags.get("ceo_interview_response_scores", {}),
            "overall_avg": round(
                sum(flags.get("ceo_interview_scores", {}).values()) /
                max(len(flags.get("ceo_interview_scores", {}) or {}), 1), 2
            ),
        }

    # ── Regulatory Sandbox ─────────────────────────────────────────
    sandbox = gs.get("regulatory_sandbox", {})
    sandbox_summary = None
    if sandbox:
        sandbox_summary = {
            "active_regulations": len(sandbox.get("active_regulations", [])),
            "instruments": [r.get("name") for r in sandbox.get("active_regulations", [])],
            "cumulative_compliance_burden": sandbox.get("compliance_burden_total", 0),
            "complexity_index": sandbox.get("regulatory_complexity_index", 0),
            "capture_risk": sandbox.get("regulatory_capture_risk", 0),
            "rounds_of_history": len(sandbox.get("audit_log", [])),
        }

    # ── Side Tracks ────────────────────────────────────────────────
    side_track_results = []
    st_states = session_info.get("side_track_states", {})
    if st_states:
        from side_tracks import get_all_tracks
        all_tracks = get_all_tracks()
        for tid, track_obj in all_tracks.items():
            st = st_states.get(tid)
            if st and st.get("current_round", 0) > 0:
                score = st.get("final_score") or track_obj.calculate_score(st.get("state", {}))
                side_track_results.append({
                    "track_id": tid,
                    "display_name": track_obj.display_name,
                    "completed": st.get("completed", False),
                    "rounds_done": st.get("current_round", 0),
                    "total_score": score.get("total_score", 0),
                    "grade": score.get("grade", "?"),
                    "archetype": score.get("archetype", {}).get("title", ""),
                })

    # ── Round-by-round history ─────────────────────────────────────
    history = await db.fetch_round_history(session_id)
    round_history = []
    if history:
        for h in sorted(history, key=lambda x: x.get("round_number", 0)):
            h_gs = h.get("global_state", {})
            h_bus = h.get("bu_states", [])
            h_rev = sum(bu.get("revenue_base", 0) for bu in h_bus)
            h_op = sum(bu.get("opex_base", 0) for bu in h_bus)
            h_syn = h_gs.get("synergy_multiplier", 1.0)
            h_tv = round(h_gs.get("corporate_treasury", 0) + (h_rev - h_op) * h_syn * 5, 2)
            round_history.append({
                "round": h.get("round_number", 0),
                "treasury": h_gs.get("corporate_treasury", 0),
                "reputation": h_gs.get("group_reputation", 50),
                "synergy": h_gs.get("synergy_multiplier", 1.0),
                "terminal_value": h_tv,
                "avg_slo": round(
                    sum(bu.get("social_license_score", 50) for bu in h_bus) / max(len(h_bus), 1), 2
                ),
                "avg_ci": round(
                    sum(bu.get("carbon_intensity", 50) for bu in h_bus) / max(len(h_bus), 1), 2
                ),
                "total_tco2": round(sum(bu.get("tco2e_emissions", 0) for bu in h_bus), 2),
            })

    return {
        "session_id": session_id,
        "cohort_name": session_info.get("cohort_name", "Unknown"),
        "player_id": session_info.get("player_id", ""),
        "facilitator_id": session_info.get("facilitator_id", ""),
        "difficulty_tier": session_info.get("difficulty_tier", "advanced"),
        "scenario_preset": session_info.get("scenario_preset", "default"),
        "pacing_mode": session_info.get("pacing_mode", "free_play"),
        "round_number": round_number,
        "game_complete": round_number > 10 or bool(flags.get("profile")),
        "kpis": {
            "treasury": treasury,
            "terminal_value": terminal_value,
            "reputation": reputation,
            "avg_slo": avg_slo,
            "avg_ncd": avg_ncd,
            "avg_carbon_intensity": avg_ci,
            "total_tco2e": total_tco2,
            "synergy_multiplier": round(synergy, 4),
            "regenerative_multiple": mr,
            "bonus_score": gs.get("bonus_score", 0),
        },
        "archetype": archetype,
        "ending_pathway": ending_pathway,
        "bu_breakdown": bu_summary,
        "ceo_interview": ceo_interview,
        "sandbox": sandbox_summary,
        "side_tracks": side_track_results,
        "round_history": round_history,
    }


@admin_router.post(
    "/{session_id}/override",
    summary="Apply a manual override to a session",
    status_code=status.HTTP_200_OK,
)
async def apply_override(session_id: str, body: OverrideRequest):
    """
    Applies a God Mode override to a specific session.
    Types: carbon_tax, omni_tech_poach, force_strike
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = current["global_state"]
    bus = current["bu_states"]

    if body.override_type == "carbon_tax":
        result = _apply_carbon_tax_override(gs, body.parameters)
    elif body.override_type == "omni_tech_poach":
        result = _apply_omni_tech_poach(gs, body.parameters)
    elif body.override_type == "force_strike":
        result = _apply_force_strike(gs, bus, body.parameters)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown override type: {body.override_type}",
        )

    # Persist the mutated state
    await db.update_latest_global_state(session_id, gs, bus)

    # Auto-inject a mailbox message so the player sees the override in their inbox
    override_msg = {
        "id": f"override_{body.override_type}_{datetime.now(timezone.utc).timestamp():.0f}",
        "round": current["round_number"],
        "type": "admin",
        "title": f"⚡ Facilitator Override: {body.override_type.replace('_', ' ').title()}",
        "body": result.get("message", f"A {body.override_type.replace('_', ' ')} override has been applied to your session by the facilitator."),
        "read": False,
        "source": "god_mode",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(override_msg)

    # Also store under all player sub-sessions if this is a cohort session
    all_sessions = await db.fetch_all_sessions()
    for s in all_sessions:
        if s.get("parent_cohort_id") == session_id:
            child_id = s["session_id"]
            if child_id not in _session_messages:
                _session_messages[child_id] = []
            _session_messages[child_id].append(override_msg)

    # Push override notification to player session via WebSocket
    await manager.push_to_session(session_id, {
        "type": "god_mode_override",
        "override": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Notify admin dashboard
    await manager.broadcast_admin({
        "type": "override_applied",
        "session_id": session_id,
        "result": result,
    })

    return {"status": "applied", "result": result}


# ═════════════════════════════════════════════════════════════════
#  CUSTOM BLACK SWAN INJECTOR
# ═════════════════════════════════════════════════════════════════

class CustomBlackSwanRequest(BaseModel):
    title: str
    narrative: str
    target_scope: str = "Global"          # "Global" | "pharma" | "electronics" | "consumer_goods" | "software"
    financial_impact: float = 0           # Treasury delta (negative = deduction)
    reputation_impact: float = 0          # Reputation delta
    social_license_impact: float = 0      # Social License delta
    natural_debt_impact: float = 0        # Natural Capital Debt delta

# In-memory history of injected custom events
_custom_black_swan_log: list[dict] = []


@admin_router.post(
    "/{session_id}/inject-custom-event",
    summary="Inject a custom Black Swan event into a player session",
    status_code=status.HTTP_200_OK,
)
async def inject_custom_event(session_id: str, body: CustomBlackSwanRequest):
    """
    Immediately mutates the session's game state with the specified deltas,
    injects a mailbox message, and pushes a WebSocket alert to the player.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = current["global_state"]
    bus = current["bu_states"]
    valid_bus = {"pharma", "electronics", "consumer_goods", "software"}
    is_global = body.target_scope.lower() == "global" or body.target_scope not in valid_bus

    # ── Apply financial impact (always global) ──
    if body.financial_impact != 0:
        gs["corporate_treasury"] = round(
            gs.get("corporate_treasury", 0) + body.financial_impact, 2
        )

    # ── Apply reputation impact (always global) ──
    if body.reputation_impact != 0:
        gs["group_reputation"] = max(0, min(100, round(
            gs.get("group_reputation", 50) + body.reputation_impact, 2
        )))

    # ── Apply social license impact ──
    if body.social_license_impact != 0:
        for bu in bus:
            if is_global or bu["bu_id"] == body.target_scope:
                bu["social_license_score"] = max(0, min(100, round(
                    bu.get("social_license_score", 50) + body.social_license_impact, 2
                )))

    # ── Apply natural capital debt impact ──
    if body.natural_debt_impact != 0:
        for bu in bus:
            if is_global or bu["bu_id"] == body.target_scope:
                bu["natural_capital_debt"] = max(0, round(
                    bu.get("natural_capital_debt", 0) + body.natural_debt_impact, 2
                ))

    # ── Append to active_event_flags ──
    event_record = {
        "type": "custom_black_swan",
        "title": body.title,
        "narrative": body.narrative,
        "target_scope": body.target_scope,
        "financial_impact": body.financial_impact,
        "reputation_impact": body.reputation_impact,
        "social_license_impact": body.social_license_impact,
        "natural_debt_impact": body.natural_debt_impact,
        "injected_at": datetime.now(timezone.utc).isoformat(),
    }
    gs.setdefault("active_event_flags", {})
    if not isinstance(gs["active_event_flags"], dict):
        gs["active_event_flags"] = {}
    # Store as a list under custom_black_swans key
    existing_swans = gs["active_event_flags"].get("custom_black_swans", [])
    existing_swans.append(event_record)
    gs["active_event_flags"]["custom_black_swans"] = existing_swans

    # ── Persist mutated state ──
    await db.update_latest_global_state(session_id, gs, bus)

    # ── Inject mailbox message ──
    message = {
        "id": f"black_swan_{datetime.now(timezone.utc).timestamp():.0f}",
        "round": current["round_number"],
        "type": "crisis",
        "title": f"🦢 {body.title}",
        "body": body.narrative,
        "read": False,
        "source": "god_mode",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(message)

    # Propagate to child sessions
    all_sessions = await db.fetch_all_sessions()
    for s in all_sessions:
        if s.get("parent_cohort_id") == session_id:
            child_id = s["session_id"]
            if child_id not in _session_messages:
                _session_messages[child_id] = []
            _session_messages[child_id].append(message)

    # ── WebSocket push ──
    ws_payload = {
        "type": "custom_black_swan",
        "event": event_record,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.push_to_session(session_id, ws_payload)
    # Also push to child sessions
    for s in all_sessions:
        if s.get("parent_cohort_id") == session_id:
            await manager.push_to_session(s["session_id"], ws_payload)

    # ── Notify admin dashboard ──
    await manager.broadcast_admin({
        "type": "black_swan_injected",
        "session_id": session_id,
        "event": event_record,
    })

    # ── Audit log ──
    _god_mode_audit_log.append({
        "action": "custom_black_swan_injected",
        "session_id": session_id,
        "details": event_record,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # ── Persist to in-memory log ──
    _custom_black_swan_log.append({
        "session_id": session_id,
        **event_record,
    })

    return {"status": "injected", "event": event_record, "message": message}


@admin_router.get(
    "/custom-black-swan-log",
    summary="Get history of all injected custom Black Swan events",
)
async def get_custom_black_swan_log():
    return {"events": _custom_black_swan_log}

@admin_router.post(
    "/{session_id}/inject-message",
    summary="Inject a message into a player's Executive Mailbox",
    status_code=status.HTTP_200_OK,
)
async def inject_message(session_id: str, body: MessageInjectRequest):
    """
    Pushes a facilitator message directly into a session's mailbox.
    Can use a preset_id or custom title/body.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # If preset_id provided, overlay preset data
    if body.preset_id:
        preset = next(
            (p for p in SWIPE_FILE_PRESETS if p["id"] == body.preset_id), None
        )
        # Also check dynamically-added master swipes
        if not preset:
            preset = next(
                (p for p in _master_swipes if p["id"] == body.preset_id), None
            )
        if preset:
            body.title = body.title or preset.get("title", "")
            body.body = body.body or preset.get("body", "")
            body.message_type = body.message_type or preset.get("type", "narrative")

    message = {
        "id": f"god_{body.preset_id or 'custom'}_{datetime.now(timezone.utc).timestamp():.0f}",
        "round": current["round_number"],
        "type": body.message_type,
        "title": body.title,
        "body": body.body,
        "read": False,
        "source": "god_mode",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Persist message server-side for HTTP polling
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(message)

    # Also propagate to player sub-sessions so individual player polling picks it up
    all_sessions = await db.fetch_all_sessions()
    for s in all_sessions:
        if s.get("parent_cohort_id") == session_id:
            child_id = s["session_id"]
            if child_id not in _session_messages:
                _session_messages[child_id] = []
            _session_messages[child_id].append(message)

    # Push to player session via WebSocket
    await manager.push_to_session(session_id, {
        "type": "mailbox_inject",
        "message": message,
    })

    # Notify admin
    await manager.broadcast_admin({
        "type": "message_injected",
        "session_id": session_id,
        "message": message,
    })

    return {"status": "injected", "message": message}


@admin_router.get(
    "/{session_id}/messages",
    summary="Get all facilitator messages for a session",
    status_code=status.HTTP_200_OK,
)
async def get_session_messages(session_id: str):
    """Return all facilitator-injected messages for a session (for frontend polling)."""
    return {"messages": _session_messages.get(session_id, [])}


@admin_router.get(
    "/swipe-presets",
    summary="Get all swipe file presets",
)
async def get_swipe_presets():
    """Returns the list of preset messages for the Swipe File UI."""
    return {"presets": SWIPE_FILE_PRESETS}


async def auto_inject_scheduled_interventions(
    session_id: str,
    new_round: int,
):
    """
    Auto-injects swipe files and override messages into a player's inbox
    when they reach a round that has scheduled interventions.
    Called from commit-turn after the round advances.
    """
    # Determine the cohort session that owns the intervention config
    session_info = await db.get_session_info(session_id)
    cohort_id = session_id
    if session_info and session_info.get("parent_cohort_id"):
        cohort_id = session_info["parent_cohort_id"]

    # Look up scheduled interventions for this cohort
    perms = _session_interventions.get(cohort_id)
    if not perms:
        # Try to recover from persisted global_state on cohort
        try:
            latest = await db.fetch_latest_state(cohort_id)
            if latest:
                flags = latest.get("global_state", {}).get("active_event_flags", {})
                if flags.get("swipe_rounds") or flags.get("override_rounds"):
                    perms = {
                        "allowed_overrides": flags.get("allowed_overrides", []),
                        "allowed_swipes": flags.get("allowed_swipes", []),
                        "override_rounds": flags.get("override_rounds", {}),
                        "swipe_rounds": flags.get("swipe_rounds", {}),
                    }
                    _session_interventions[cohort_id] = perms
        except Exception:
            pass
    if not perms:
        return []

    injected = []

    # Track already-injected interventions to avoid duplicates
    already_injected_key = f"_auto_injected_r{new_round}"
    existing_messages = _session_messages.get(session_id, [])
    already_injected_ids = {
        m.get("preset_id") for m in existing_messages
        if m.get("auto_injected") and m.get("round") == new_round
    }

    # ── Auto-inject scheduled swipe files ────────────────────
    swipe_rounds = perms.get("swipe_rounds", {})
    allowed_swipes = perms.get("allowed_swipes", [])
    for swipe_id, scheduled_round in swipe_rounds.items():
        if scheduled_round is None or scheduled_round != new_round:
            continue
        if swipe_id not in allowed_swipes:
            continue
        if swipe_id in already_injected_ids:
            continue

        # Find the preset
        preset = next((p for p in SWIPE_FILE_PRESETS if p["id"] == swipe_id), None)
        if not preset:
            continue

        message = {
            "id": f"auto_swipe_{swipe_id}_{new_round}_{datetime.now(timezone.utc).timestamp():.0f}",
            "round": new_round,
            "type": preset.get("type", "narrative"),
            "title": preset.get("title", preset.get("label", "Swipe File")),
            "body": preset.get("body", ""),
            "read": False,
            "source": "god_mode",
            "auto_injected": True,
            "preset_id": swipe_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if session_id not in _session_messages:
            _session_messages[session_id] = []
        _session_messages[session_id].append(message)
        injected.append(message)

        # Push via WebSocket
        try:
            await manager.push_to_session(session_id, {
                "type": "mailbox_inject",
                "message": message,
            })
        except Exception:
            pass

    return injected


# ═════════════════════════════════════════════════════════════════
#  MATERIALITY CONFIGURATOR (DYNAMIC)
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/materiality-config",
    response_model=MaterialityConfig,
    summary="Get the dynamic materiality configuration"
)
async def get_materiality_config():
    """Returns the current materiality issues, interdependencies, and fee."""
    return mat_db.get_current_config()


@admin_router.put(
    "/materiality-config",
    response_model=MaterialityConfig,
    summary="Update the entire materiality configuration"
)
async def update_materiality_config(config: MaterialityConfig):
    """Overwrites the entire materiality config and stores it in JSON."""
    mat_db.update_current_config(config.model_dump())
    return mat_db.get_current_config()


@admin_router.post(
    "/materiality-config/issues",
    response_model=MaterialityConfig,
    summary="Add a new materiality issue"
)
async def add_materiality_issue(issue: MaterialityIssue):
    config = mat_db.get_current_config()
    for idx, ex_issue in enumerate(config["issues"]):
        if ex_issue["id"] == issue.id:
            config["issues"][idx] = issue.model_dump()
            mat_db.update_current_config(config)
            return config
    
    config["issues"].append(issue.model_dump())
    mat_db.update_current_config(config)
    return config


@admin_router.delete(
    "/materiality-config/issues/{issue_id}",
    response_model=MaterialityConfig,
    summary="Delete a materiality issue by ID"
)
async def delete_materiality_issue(issue_id: str):
    config = mat_db.get_current_config()
    config["issues"] = [i for i in config["issues"] if i["id"] != issue_id]
    config["interdependencies"] = [
        link for link in config["interdependencies"]
        if link["source_issue_id"] != issue_id and link["target_issue_id"] != issue_id
    ]
    mat_db.update_current_config(config)
    return config


@admin_router.put(
    "/materiality-config/fee",
    response_model=MaterialityConfig,
    summary="Update the Consultant Fee"
)
async def update_consultant_fee(fee_usd: int = Body(..., embed=True)):
    config = mat_db.get_current_config()
    config["consultant_fee_usd"] = fee_usd
    mat_db.update_current_config(config)
    return config


# ═════════════════════════════════════════════════════════════════
#  BU REGISTRY — God-mode configurable BU categories
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/bu-categories", summary="List all BU categories (defaults + custom)")
async def list_bu_categories():
    """Returns all registered BU categories including any god-mode additions."""
    registry = mat_db.get_bu_registry()
    # Exclude industry verticals — they have their own dedicated UI row
    # via /api/admin/industry-verticals
    categories = [b for b in registry if not b.get("is_industry_vertical")]
    return {"categories": categories, "total": len(categories)}


@admin_router.post("/bu-categories", summary="Add a new custom BU category")
async def add_bu_category(body: dict = Body(...)):
    """Register a new BU category and initialise an empty materiality config for it."""
    bu_id = (body.get("id") or body.get("bu_id") or "").strip().lower().replace(" ", "_")
    label = (body.get("label") or "").strip()
    icon = body.get("icon", "\U0001f3e2")
    if not bu_id:
        raise HTTPException(400, "'id' (or 'bu_id') is required")
    if not label:
        raise HTTPException(400, "'label' is required")
    entry = mat_db.register_bu(bu_id, label, icon)
    print(f"[god-mode] BU category registered: {bu_id} ({label})")
    return {"status": "ok", "category": entry}


@admin_router.delete("/bu-categories/{bu_id}", summary="Remove a custom BU category")
async def delete_bu_category(bu_id: str):
    """Remove a custom BU category. The 4 default BUs cannot be removed."""
    try:
        removed = mat_db.unregister_bu(bu_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not removed:
        raise HTTPException(404, f"Custom BU category '{bu_id}' not found")
    print(f"[god-mode] BU category removed: {bu_id}")
    return {"status": "deleted", "bu_id": bu_id}


# ═════════════════════════════════════════════════════════════════
#  BU COMPOSITION TOGGLE (Industry Vertical Substitution)
#  God Mode + Advanced Facilitator can swap default BUs with
#  industry vertical alternatives before Round 1 is committed.
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/{session_id}/bu-composition",
    summary="Get the active BU composition for a session",
)
async def get_bu_composition(session_id: str):
    """Returns the current BU lineup with any active substitutions."""
    from bu_profiles import BU_PROFILES, DEFAULT_SLOTS, SLOT_FIT_MAP, get_active_bus

    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    subs = global_state.get("bu_substitutions", {})
    active_bus = get_active_bus(subs)
    locked = current["round_number"] > 1

    # Build slot info with available alternatives
    slots = []
    for slot_id in DEFAULT_SLOTS:
        current_bu = subs.get(slot_id, slot_id)
        profile = BU_PROFILES.get(current_bu, {})
        alternatives = [
            {
                "bu_id": v,
                "label": BU_PROFILES.get(v, {}).get("label", v),
                "icon": BU_PROFILES.get(v, {}).get("icon", "🏢"),
            }
            for v in SLOT_FIT_MAP.get(slot_id, [])
        ]
        slots.append({
            "slot_id": slot_id,
            "default_bu": slot_id,
            "current_bu": current_bu,
            "current_label": profile.get("label", current_bu),
            "current_icon": profile.get("icon", "🏢"),
            "is_substituted": current_bu != slot_id,
            "available_alternatives": alternatives,
        })

    return {
        "session_id": session_id,
        "active_bus": active_bus,
        "substitutions": subs,
        "locked": locked,
        "lock_reason": "BU composition is locked after Round 1 is committed." if locked else None,
        "slots": slots,
    }


@admin_router.put(
    "/{session_id}/bu-composition",
    summary="Set BU composition (swap verticals)",
)
async def set_bu_composition(session_id: str, body: dict = Body(...)):
    """
    Swap default BUs with industry vertical alternatives.
    Must be called before Round 1 is committed.

    Body: {"substitutions": {"pharma": "oil_gas", "software": "technology"}}
    """
    from bu_profiles import (
        BU_PROFILES, DEFAULT_SLOTS, validate_substitution,
        get_active_bus, build_bu_states,
    )

    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Lock check — cannot change after R1
    if current["round_number"] > 1:
        raise HTTPException(
            status_code=400,
            detail="BU composition is locked after Round 1 is committed.",
        )

    substitutions = body.get("substitutions", {})

    # Validate each substitution
    for slot_id, vertical_id in substitutions.items():
        is_valid, error_msg = validate_substitution(slot_id, vertical_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    # Apply substitutions to global_state
    global_state = current["global_state"]
    global_state["bu_substitutions"] = substitutions

    # Rebuild bu_states with new profiles
    new_bu_states = build_bu_states(substitutions)

    # Persist
    await db.update_latest_global_state(session_id, global_state, new_bu_states)

    # Audit log
    _god_mode_audit_log.append({
        "action": "bu_composition_changed",
        "session_id": session_id,
        "substitutions": substitutions,
        "active_bus": get_active_bus(substitutions),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    active_bus = get_active_bus(substitutions)
    labels = [BU_PROFILES.get(b, {}).get("label", b) for b in active_bus]
    print(f"[god-mode] BU composition updated for {session_id}: {labels}")

    return {
        "status": "ok",
        "active_bus": active_bus,
        "substitutions": substitutions,
        "bu_labels": labels,
    }


# ═════════════════════════════════════════════════════════════════
#  BU-SPECIFIC MATERIALITY CONFIGURATOR (Strategic Pillars)
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/materiality-config/bu/{bu_id}",
    summary="Get the BU-specific materiality configuration"
)
async def get_bu_materiality_config(bu_id: str):
    """Returns the materiality issues dictionary for a specific Business Unit."""
    valid = mat_db.get_bu_ids()
    if bu_id not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid BU ID: {bu_id}. Valid: {valid}")
    return mat_db.get_bu_config(bu_id)


@admin_router.put(
    "/materiality-config/bu/{bu_id}",
    summary="Update the BU-specific materiality configuration"
)
async def update_bu_materiality_config(bu_id: str, config: MaterialityConfig):
    """Overwrites the entire BU-specific materiality dictionary."""
    valid = mat_db.get_bu_ids()
    if bu_id not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid BU ID: {bu_id}. Valid: {valid}")
    mat_db.update_bu_config(bu_id, config.model_dump())
    return mat_db.get_bu_config(bu_id)


@admin_router.get(
    "/{session_id}/r2-bu-selection",
    summary="Get the randomly selected BU for Round 2 materiality matrix"
)
async def get_r2_bu_selection(session_id: str):
    """Returns the BU selected for Round 2 materiality analysis (Strategic Pillars mode)."""
    from bu_profiles import BU_PROFILES, get_active_bus

    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    selected_bu = global_state.get("r2_selected_bu")

    if selected_bu is None:
        # Auto-select from active BU composition (respects substitutions)
        import random
        subs = global_state.get("bu_substitutions", {})
        active_bus = get_active_bus(subs)
        selected_bu = random.choice(active_bus)
        global_state["r2_selected_bu"] = selected_bu
        await db.update_latest_global_state(session_id, global_state, current["bu_states"])

    # Dynamic label lookup from profiles
    profile = BU_PROFILES.get(selected_bu, {})
    bu_label = profile.get("label", selected_bu)

    return {
        "selected_bu": selected_bu,
        "bu_label": bu_label,
    }


# ═════════════════════════════════════════════════════════════════
#  AUDIT TRAIL & PLAYER IMPERSONATION
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/{session_id}/audit-trail",
    summary="Get the decision audit trail for a cohort",
)
async def get_audit_trail(session_id: str):
    """
    Returns all decisions made by players in this cohort,
    including child player sessions. Grouped by round.
    """
    decisions = await db.get_decision_log(session_id)

    # Group by round
    by_round: dict[int, list] = {}
    for d in decisions:
        r = d.get("round_number", 0)
        if r not in by_round:
            by_round[r] = []
        by_round[r].append(d)

    return {
        "session_id": session_id,
        "total_decisions": len(decisions),
        "rounds": {
            str(r): entries for r, entries in sorted(by_round.items())
        },
    }


@admin_router.get(
    "/{session_id}/debrief",
    summary="Get round-by-round debrief report for a cohort",
)
async def get_debrief(session_id: str):
    """
    Compiles a structured debrief for the facilitator.
    For each completed round: crisis context, decision made,
    metric snapshots with deltas, triggered flags, and per-BU capex.
    Aggregates across all child player sessions.
    """
    from round_configs import get_round_config

    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Gather all related session IDs (parent + children)
    children = await db.get_child_sessions(session_id)
    related_ids = [session_id] + [c["session_id"] for c in children]

    # Get full round history for the primary session
    # Use the session that has the most rounds (parent or first child that played)
    best_history = []
    best_sid = session_id
    for sid in related_ids:
        hist = await db.fetch_round_history(sid)
        if len(hist) > len(best_history):
            best_history = hist
            best_sid = sid

    if not best_history:
        return {
            "session_id": session_id,
            "cohort_name": session_info.get("cohort_name", "Unknown"),
            "current_round": 1,
            "rounds": [],
        }

    # Get all decisions
    decisions = await db.get_decision_log(session_id)

    # Group decisions by round
    decisions_by_round: dict[int, list] = {}
    for d in decisions:
        r = d.get("round_number", 0)
        decisions_by_round.setdefault(r, []).append(d)

    # Build debrief rounds
    debrief_rounds = []
    prev_snapshot = None

    for snapshot in best_history:
        rn = snapshot["round_number"]
        if rn <= 1:
            # Round 1 is the seed — save as baseline for deltas
            prev_snapshot = snapshot
            continue

        # The decision was made in (rn - 1), producing state at rn
        decision_round = rn - 1
        rcfg = get_round_config(decision_round)
        if not rcfg:
            prev_snapshot = snapshot
            continue

        gs = snapshot.get("global_state", {})
        bus = snapshot.get("business_units", [])

        # Compute current metrics
        avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus) / max(len(bus), 1)
        avg_sl = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)

        current_metrics = {
            "corporate_treasury": gs.get("corporate_treasury", 0),
            "group_reputation": gs.get("group_reputation", 50),
            "synergy_multiplier": gs.get("synergy_multiplier", 1.0),
            "avg_natural_capital_debt": round(avg_ncd, 2),
            "avg_social_license": round(avg_sl, 2),
        }

        # Compute deltas
        deltas = {}
        if prev_snapshot:
            prev_gs = prev_snapshot.get("global_state", {})
            prev_bus = prev_snapshot.get("business_units", [])
            prev_avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in prev_bus) / max(len(prev_bus), 1)
            prev_avg_sl = sum(bu.get("social_license_score", 50) for bu in prev_bus) / max(len(prev_bus), 1)

            prev_metrics = {
                "corporate_treasury": prev_gs.get("corporate_treasury", 0),
                "group_reputation": prev_gs.get("group_reputation", 50),
                "synergy_multiplier": prev_gs.get("synergy_multiplier", 1.0),
                "avg_natural_capital_debt": round(prev_avg_ncd, 2),
                "avg_social_license": round(prev_avg_sl, 2),
            }

            for key in current_metrics:
                deltas[key] = round(current_metrics[key] - prev_metrics[key], 2)

        # Extract decision info from this round
        round_decisions = decisions_by_round.get(rn, [])
        # Determine choice made (primary choice from first decision)
        choice_selected = ""
        players = []
        capex_by_bu = {}
        for d in round_decisions:
            if d.get("choice_selected") and not choice_selected:
                choice_selected = d["choice_selected"]
            pid = d.get("player_id", "")
            if pid and pid != "unknown" and pid not in players:
                players.append(pid)
            if d.get("bu_id"):
                capex_by_bu[d["bu_id"]] = d.get("capex_allocated", 0)

        # Lookup option details
        options = rcfg.get("options", {})
        choice_info = options.get(choice_selected, {})

        # Determine newly triggered flags
        current_flags = set(gs.get("active_event_flags", {}).keys())
        prev_flags = set()
        if prev_snapshot:
            prev_flags = set(prev_snapshot.get("global_state", {}).get("active_event_flags", {}).keys())
        raw_new_flags = sorted(current_flags - prev_flags)
        # Only keep recognizable game flags (from round config flags_set)
        # Filter out engine internals like strike_probabilities, synergy_decayed_from, etc.
        known_game_flags = set()
        for rnum in range(1, 11):
            rc = get_round_config(rnum)
            if rc:
                for opt in rc.get("options", {}).values():
                    known_game_flags.update(opt.get("flags_set", []))
        new_flags = [f for f in raw_new_flags if f in known_game_flags]

        crisis = rcfg.get("crisis", {})

        debrief_rounds.append({
            "round_number": decision_round,
            "title": rcfg.get("title", f"Round {decision_round}"),
            "theme": rcfg.get("theme", ""),
            "crisis_title": crisis.get("title", ""),
            "crisis_description": crisis.get("description", ""),
            "crisis_icon": crisis.get("icon", "📋"),
            "choice_selected": choice_selected,
            "choice_title": choice_info.get("title", ""),
            "choice_description": choice_info.get("description", ""),
            "choice_label": choice_info.get("label", ""),
            "players": players,
            "capex_by_bu": capex_by_bu,
            "snapshot": current_metrics,
            "deltas": deltas,
            "new_flags": new_flags,
        })

        prev_snapshot = snapshot

    # Build trend history from all snapshots for charts
    trend_history = []
    for snapshot in best_history:
        rn = snapshot["round_number"]
        gs = snapshot.get("global_state", {})
        bus = snapshot.get("business_units", [])
        avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus) / max(len(bus), 1)
        avg_sl = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
        trend_history.append({
            "round": rn,
            "year": 2040 + rn,
            "treasury": gs.get("corporate_treasury", 0),
            "reputation": gs.get("group_reputation", 50),
            "synergy": gs.get("synergy_multiplier", 1.0),
            "ncd": round(avg_ncd, 2),
            "social_license": round(avg_sl, 2),
        })

    # Extract any active regulatory sandbox instruments from latest state
    regulatory_instruments = []
    if best_history:
        latest_gs = best_history[-1].get("global_state", {})
        sandbox_state = latest_gs.get("active_event_flags", {}).get("regulatory_sandbox", {})
        if isinstance(sandbox_state, dict):
            active_regs = sandbox_state.get("active_regulations", [])
            for reg in active_regs:
                regulatory_instruments.append({
                    "id": reg.get("instrument_id", ""),
                    "name": reg.get("name", reg.get("instrument_id", "")),
                    "activated_round": reg.get("activated_round"),
                    "treasury_impact": reg.get("treasury_impact_usd", 0),
                    "theory": reg.get("theory", ""),
                })

    return {
        "session_id": session_id,
        "cohort_name": session_info.get("cohort_name", "Unknown"),
        "current_round": best_history[-1]["round_number"] if best_history else 1,
        "rounds": debrief_rounds,
        "trend_history": trend_history,
        "regulatory_instruments": regulatory_instruments,
    }


@admin_router.get(
    "/{session_id}/player-sessions",
    summary="List all player sub-sessions for a cohort",
)
async def get_player_sessions(session_id: str):
    """Returns all child player sessions under a parent cohort."""
    children = await db.get_child_sessions(session_id)
    # Enrich with current round info
    enriched = []
    for child in children:
        latest = await db.fetch_latest_state(child["session_id"])
        child["current_round"] = latest["round_number"] if latest else 1
        enriched.append(child)
    return {"players": enriched}


@admin_router.post(
    "/impersonate/{player_session_id}",
    summary="Get impersonation link for a player session",
)
async def impersonate_player(player_session_id: str):
    """
    Returns the session ID and URL path for the facilitator
    to open a player's console in a new browser tab.
    """
    session_info = await db.get_session_info(player_session_id)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player session {player_session_id} not found.",
        )

    latest = await db.fetch_latest_state(player_session_id)
    return {
        "session_id": player_session_id,
        "player_id": session_info.get("player_id", "unknown"),
        "current_round": latest["round_number"] if latest else 1,
        "url": f"/?session={player_session_id}&impersonate=true",
    }


# ═════════════════════════════════════════════════════════════════
#  SESSION RESET ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@admin_router.delete(
    "/{session_id}/reset",
    summary="Reset (delete) a single session",
    status_code=status.HTTP_200_OK,
)
async def reset_session(session_id: str):
    """Deletes a session and all its round data. Cannot be undone.
    - If the session is a cohort template, cascade-deletes all player sessions under it.
    - If the session is a player session, removes it from the parent cohort's player list."""
    from router import _session_players
    session_info = await db.get_session_info(session_id)

    players_removed = 0

    if session_info and session_info.get("parent_cohort_id"):
        # This is a player session — clean up the parent's player list
        parent_id = session_info["parent_cohort_id"]
        players = _session_players.get(parent_id, [])
        _session_players[parent_id] = [
            p for p in players if p.get("player_session_id") != session_id
        ]
        players_removed = 1
    else:
        # This is a cohort template — cascade-delete all player sessions
        player_entries = _session_players.get(session_id, [])
        for p in player_entries:
            psid = p.get("player_session_id")
            if psid:
                await db.delete_session(psid)
                players_removed += 1
        _session_players.pop(session_id, None)

    found = await db.delete_session(session_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # Purge all session-keyed admin data for deleted sessions
    def _purge_admin_data(sid):
        _session_messages.pop(sid, None)
        _session_interventions.pop(sid, None)
        _practice_mode.pop(sid, None)
        _round_pacing.pop(sid, None)
        _facilitator_notes.pop(sid, None)
        _student_bonuses.pop(sid, None)
        _peer_evaluations.pop(sid, None)
        _annotations.pop(sid, None)

    _purge_admin_data(session_id)
    # Also purge data for cascade-deleted player sessions
    if players_removed > 0 and not (session_info and session_info.get("parent_cohort_id")):
        for p in _session_players.get(session_id, []):
            psid = p.get("player_session_id")
            if psid:
                _purge_admin_data(psid)

    # Remove associated players from registry
    global _player_registry
    _player_registry = [p for p in _player_registry if p.get("session_id") != session_id]

    # Notify admin dashboard
    await manager.broadcast_admin({
        "type": "session_reset",
        "session_id": session_id,
    })

    return {"status": "deleted", "session_id": session_id, "players_removed": players_removed}


@admin_router.delete(
    "/reset-all",
    summary="Reset ALL sessions (nuclear option)",
    status_code=status.HTTP_200_OK,
)
async def reset_all_sessions():
    """Deletes ALL sessions and all data. Cannot be undone."""
    count = await db.delete_all_sessions(hard=True)

    # Clear logs and history
    _god_mode_audit_log.clear()
    _crisis_trigger_history.clear()
    _session_messages.clear()
    _session_interventions.clear()

    # Reset facilitators to default
    global _facilitator_registry
    from admin_shared import _DEFAULT_FACILITATOR, _persist_facilitators, _practice_mode, _round_pacing, _shared_marketplace
    _facilitator_registry[:] = [{**_DEFAULT_FACILITATOR}]
    _persist_facilitators()

    # Reset other transient states
    _practice_mode.clear()
    _round_pacing.clear()
    _shared_marketplace["carbon_credit_pool"]["purchased"].clear()
    _shared_marketplace["carbon_credit_pool"]["price_history"] = [50000]
    _shared_marketplace["green_talent_pool"]["hired"].clear()
    _shared_marketplace["green_talent_pool"]["cost_history"] = [200000]

    # Notify admin dashboard
    await manager.broadcast_admin({
        "type": "all_sessions_reset",
        "count": count,
    })

    return {"status": "all_deleted", "sessions_removed": count}



# ARCH-002: Resources extracted to admin_resources.py (19 endpoints)
# Mounted in main.py via app.include_router(resources_router)


# ═════════════════════════════════════════════════════════════════
#  MASTER INTERVENTIONS DATABASE (God Mode)
# ═════════════════════════════════════════════════════════════════


_master_overrides: list[dict] = [
    {
        "id": "carbon_tax",
        "icon": "🌍",
        "title": "Global Macro Shift",
        "description": "Toggle Year 5 Carbon Tax from $250/ton → $400/ton mid-game.",
        "color": "#3b82f6",
        "dangerLevel": "HIGH",
        "params": {"new_rate": 400},
        "scheduled_round": None,
        "media_type": "text",
        "media_url": "",
    },
    {
        "id": "omni_tech_poach",
        "icon": "🧲",
        "title": "Omni-Tech Poach",
        "description": "Raise Rep Threshold 65 → 75, forcing sudden Brain-Drain OPEX spike for Software BU.",
        "color": "#f59e0b",
        "dangerLevel": "HIGH",
        "params": {"new_threshold": 75},
        "scheduled_round": None,
        "media_type": "text",
        "media_url": "",
    },
    {
        "id": "force_strike",
        "icon": "🪧",
        "title": "Force Strike",
        "description": "Override probability engine. Guarantee a labor strike — zeroes all BU revenue.",
        "color": "#ef4444",
        "dangerLevel": "CRITICAL",
        "params": {},
        "scheduled_round": None,
        "media_type": "text",
        "media_url": "",
    },
]

_master_swipes: list[dict] = [
    {
        **preset,
        "icon": preset["label"].split(" ")[0] if preset["label"] else "📢",
        "color": "#6366f1",
        "scheduled_round": None,
        "media_type": "text",
        "media_url": "",
    }
    for preset in SWIPE_FILE_PRESETS
]


@admin_router.get(
    "/interventions/master",
    summary="Get all master overrides and swipe file presets",
)
async def get_master_interventions():
    """Returns the global master database of overrides and swipe files."""
    return {"overrides": _master_overrides, "swipes": _master_swipes}


@admin_router.post(
    "/interventions/master/override",
    summary="Create or update a master override",
)
async def upsert_master_override(body: dict = Body(...)):
    """Create a new master override or update an existing one by ID."""
    ov_id = body.get("id")
    if not ov_id:
        raise HTTPException(400, "Override 'id' is required")

    # Ensure media fields exist
    body.setdefault("media_type", "text")
    body.setdefault("media_url", "")

    existing = next((i for i, o in enumerate(_master_overrides) if o["id"] == ov_id), None)
    if existing is not None:
        _master_overrides[existing] = body
    else:
        _master_overrides.append(body)
    return {"status": "saved", "override": body}



@admin_router.post(
    "/interventions/master/swipe",
    summary="Create or update a master swipe file preset",
)
async def upsert_master_swipe(body: dict = Body(...)):
    """Create a new master swipe file or update an existing one by ID."""
    sw_id = body.get("id")
    if not sw_id:
        raise HTTPException(400, "Swipe 'id' is required")

    # Ensure media fields exist
    body.setdefault("media_type", "text")
    body.setdefault("media_url", "")

    existing = next((i for i, s in enumerate(_master_swipes) if s["id"] == sw_id), None)
    if existing is not None:
        _master_swipes[existing] = body
    else:
        _master_swipes.append(body)
    return {"status": "saved", "swipe": body}


@admin_router.delete(
    "/interventions/master/override/{override_id}",
    summary="Delete a master override",
)
async def delete_master_override(override_id: str):
    global _master_overrides
    before = len(_master_overrides)
    _master_overrides = [o for o in _master_overrides if o["id"] != override_id]
    if len(_master_overrides) == before:
        raise HTTPException(404, f"Override '{override_id}' not found")
    return {"status": "deleted", "id": override_id}


@admin_router.delete(
    "/interventions/master/swipe/{swipe_id}",
    summary="Delete a master swipe file preset",
)
async def delete_master_swipe(swipe_id: str):
    global _master_swipes
    before = len(_master_swipes)
    _master_swipes = [s for s in _master_swipes if s["id"] != swipe_id]
    if len(_master_swipes) == before:
        raise HTTPException(404, f"Swipe '{swipe_id}' not found")
    return {"status": "deleted", "id": swipe_id}


@admin_router.post(
    "/interventions/upload-media",
    summary="Upload media (audio/video) for an intervention",
)
async def upload_intervention_media(file: UploadFile = File(...)):
    """Upload an audio or video file for attachment to an override or swipe file."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(project_root, "frontend", "public", "uploads", "interventions")
    os.makedirs(upload_dir, exist_ok=True)

    # Sanitise filename with timestamp
    safe_name = f"{int(datetime.now(timezone.utc).timestamp())}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/uploads/interventions/{safe_name}"
    return {"status": "uploaded", "url": file_url, "filename": safe_name}


# ═════════════════════════════════════════════════════════════════
#  WEBSOCKET ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@admin_router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket, facilitator_id: str = None):
    """WebSocket for admin dashboard real-time updates."""
    await manager.connect_admin(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Admin can request a leaderboard refresh
            if data == "refresh":
                if facilitator_id:
                    # Instruct facilitator frontend to fetch securely scoped leaderboard
                    await websocket.send_text(json.dumps({
                        "type": "sessions_refresh_trigger",
                    }))
                else:
                    sessions = await db.fetch_all_sessions()
                    await websocket.send_text(json.dumps({
                        "type": "sessions_refresh",
                        "sessions": sessions,
                    }))
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)


@admin_router.websocket("/ws/session/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for player session — receives God Mode pushes."""
    await manager.connect_player(websocket, session_id)
    try:
        while True:
            # Player connections are mostly receive-only from admin
            data = await websocket.receive_text()
            # Can be used for player pings / heartbeat
    except WebSocketDisconnect:
        manager.disconnect_player(websocket, session_id)


# ═════════════════════════════════════════════════════════════════
#  UNDO ROUND / ROLLBACK
# ═════════════════════════════════════════════════════════════════

@admin_router.post(
    "/{session_id}/undo-round",
    summary="Undo round(s) — optionally roll back to a specific target round",
)
async def undo_round(session_id: str, cohort_wide: bool = False, target_round: int = None):
    """
    Deletes round state(s) reverting the session back.

    - No target_round → reverts exactly one round (previous behaviour).
    - target_round=N  → keeps undoing until current_round == N (multi-round rollback).
    """
    targets = [session_id]
    if cohort_wide:
        all_sessions = await db.fetch_all_sessions()
        children = [s["session_id"] for s in all_sessions if s.get("parent_cohort_id") == session_id]
        targets.extend(children)

    last_res = None

    for tgt in set(targets):
        rounds_data = _global_states.get(tgt, [])
        if not rounds_data:
            continue
        current = rounds_data[-1]["round_number"]
        stop_at = max(1, target_round) if target_round is not None else current - 1

        if stop_at >= current:
            if tgt == session_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Target round {stop_at} must be less than current round {current}."
                )
            continue

        # Loop: undo one round at a time until we reach stop_at
        while True:
            rounds_data = _global_states.get(tgt, [])
            if not rounds_data:
                break
            current = rounds_data[-1]["round_number"]
            if current <= stop_at:
                break

            result = await db.undo_latest_round(tgt)
            if not result.get("success"):
                if tgt == session_id:
                    raise HTTPException(status_code=400, detail=result.get("reason", "Undo failed"))
                break

            last_res = result

            await manager.push_to_session(tgt, {
                "type": "round_undone",
                "deleted_round": result["deleted_round"],
                "new_current_round": result["new_current_round"],
            })
            await manager.broadcast_admin({
                "type": "round_undone",
                "session_id": tgt,
                "deleted_round": result["deleted_round"],
                "new_current_round": result["new_current_round"],
            })

    if not last_res:
        raise HTTPException(status_code=400, detail="Undo failed — nothing to roll back")

    return last_res



# ═════════════════════════════════════════════════════════════════
#  FACILITATOR NOTES / COMMENTS
# ═════════════════════════════════════════════════════════════════

_facilitator_notes: dict[str, list[dict]] = {}  # session_id → notes
_next_note_id: int = 1


class FacilitatorNoteRequest(BaseModel):
    text: str
    round_number: Optional[int] = None
    visible_to_players: bool = False


@admin_router.get(
    "/{session_id}/notes",
    summary="List facilitator notes for a session",
)
async def list_notes(session_id: str):
    return {"notes": _facilitator_notes.get(session_id, [])}


@admin_router.post(
    "/{session_id}/notes",
    summary="Add a facilitator note",
)
async def add_note(session_id: str, req: FacilitatorNoteRequest):
    global _next_note_id
    note = {
        "note_id": f"NOTE-{_next_note_id:04d}",
        "text": req.text,
        "round_number": req.round_number,
        "visible_to_players": req.visible_to_players,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _next_note_id += 1
    _facilitator_notes.setdefault(session_id, []).append(note)

    # If visible to players, push via WebSocket
    if req.visible_to_players:
        await manager.push_to_session(session_id, {
            "type": "facilitator_note",
            "note": note,
        })

    return note


@admin_router.delete(
    "/{session_id}/notes/{note_id}",
    summary="Delete a facilitator note",
)
async def delete_note(session_id: str, note_id: str):
    notes = _facilitator_notes.get(session_id, [])
    before = len(notes)
    _facilitator_notes[session_id] = [n for n in notes if n["note_id"] != note_id]
    if len(_facilitator_notes[session_id]) == before:
        raise HTTPException(404, f"Note {note_id} not found")
    return {"status": "deleted", "note_id": note_id}


# ═════════════════════════════════════════════════════════════════
#  STUDENT BONUSES / AWARDS
# ═════════════════════════════════════════════════════════════════

_student_bonuses: dict[str, list[dict]] = {}  # session_id → bonus records
_next_bonus_id: int = 1

BADGE_PRESETS = {
    "mvp": {"icon": "🏆", "label": "MVP"},
    "sustainability": {"icon": "🌍", "label": "Sustainability Champion"},
    "innovation": {"icon": "💡", "label": "Innovation Award"},
    "collaboration": {"icon": "🤝", "label": "Best Collaboration"},
    "strategy": {"icon": "🎯", "label": "Strategic Thinker"},
    "resilience": {"icon": "🛡️", "label": "Resilience Award"},
}


class StudentBonusRequest(BaseModel):
    player_name: str
    points: int = 10
    reason: str = ""
    badge: Optional[str] = None  # badge key from BADGE_PRESETS


@admin_router.get(
    "/{session_id}/bonuses",
    summary="List bonuses for a session",
)
async def list_bonuses(session_id: str):
    return {
        "bonuses": _student_bonuses.get(session_id, []),
        "badge_presets": BADGE_PRESETS,
    }


@admin_router.post(
    "/{session_id}/bonuses",
    summary="Award a bonus to a player",
)
async def award_bonus(session_id: str, req: StudentBonusRequest):
    global _next_bonus_id
    badge_info = BADGE_PRESETS.get(req.badge) if req.badge else None
    bonus = {
        "bonus_id": f"BONUS-{_next_bonus_id:04d}",
        "player_name": req.player_name,
        "points": req.points,
        "reason": req.reason,
        "badge": badge_info,
        "badge_key": req.badge,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _next_bonus_id += 1
    _student_bonuses.setdefault(session_id, []).append(bonus)

    # Notify players
    await manager.push_to_session(session_id, {
        "type": "bonus_awarded",
        "bonus": bonus,
    })

    return bonus


@admin_router.delete(
    "/{session_id}/bonuses/{bonus_id}",
    summary="Revoke a bonus",
)
async def revoke_bonus(session_id: str, bonus_id: str):
    bonuses = _student_bonuses.get(session_id, [])
    before = len(bonuses)
    _student_bonuses[session_id] = [b for b in bonuses if b["bonus_id"] != bonus_id]
    if len(_student_bonuses[session_id]) == before:
        raise HTTPException(404, f"Bonus {bonus_id} not found")
    return {"status": "revoked", "bonus_id": bonus_id}


# ═════════════════════════════════════════════════════════════════
#  PEER EVALUATIONS
# ═════════════════════════════════════════════════════════════════

_peer_evaluations: dict[str, list[dict]] = {}  # session_id → evaluations
_next_eval_id: int = 1


class PeerEvaluationRequest(BaseModel):
    evaluator_name: str
    target_name: str
    contribution: int = 3      # 1–5 scale
    communication: int = 3     # 1–5 scale
    leadership: int = 3        # 1–5 scale
    comment: str = ""


@admin_router.get(
    "/{session_id}/peer-evaluations",
    summary="List peer evaluations for a session",
)
async def list_peer_evaluations(session_id: str):
    evals = _peer_evaluations.get(session_id, [])

    # Compute averages per target
    from collections import defaultdict
    totals = defaultdict(lambda: {"contribution": [], "communication": [], "leadership": [], "count": 0})
    for e in evals:
        t = totals[e["target_name"]]
        t["contribution"].append(e["contribution"])
        t["communication"].append(e["communication"])
        t["leadership"].append(e["leadership"])
        t["count"] += 1

    averages = {}
    for name, data in totals.items():
        averages[name] = {
            "contribution_avg": round(sum(data["contribution"]) / len(data["contribution"]), 1) if data["contribution"] else 0,
            "communication_avg": round(sum(data["communication"]) / len(data["communication"]), 1) if data["communication"] else 0,
            "leadership_avg": round(sum(data["leadership"]) / len(data["leadership"]), 1) if data["leadership"] else 0,
            "total_reviews": data["count"],
        }

    return {"evaluations": evals, "averages": averages}


@admin_router.post(
    "/{session_id}/peer-evaluations",
    summary="Submit a peer evaluation",
)
async def submit_peer_evaluation(session_id: str, req: PeerEvaluationRequest):
    global _next_eval_id
    # Validate scores 1-5
    for field in ["contribution", "communication", "leadership"]:
        val = getattr(req, field)
        if val < 1 or val > 5:
            raise HTTPException(400, f"{field} must be between 1 and 5")

    evaluation = {
        "eval_id": f"EVAL-{_next_eval_id:04d}",
        "evaluator_name": req.evaluator_name,
        "target_name": req.target_name,
        "contribution": req.contribution,
        "communication": req.communication,
        "leadership": req.leadership,
        "comment": req.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _next_eval_id += 1
    _peer_evaluations.setdefault(session_id, []).append(evaluation)
    return evaluation


@admin_router.delete(
    "/{session_id}/peer-evaluations/{eval_id}",
    summary="Delete a peer evaluation",
)
async def delete_peer_evaluation(session_id: str, eval_id: str):
    evals = _peer_evaluations.get(session_id, [])
    before = len(evals)
    _peer_evaluations[session_id] = [e for e in evals if e["eval_id"] != eval_id]
    if len(_peer_evaluations[session_id]) == before:
        raise HTTPException(404, f"Evaluation {eval_id} not found")
    return {"status": "deleted", "eval_id": eval_id}


# ═════════════════════════════════════════════════════════════════
#  BULK MESSAGING / BROADCAST
# ═════════════════════════════════════════════════════════════════

_broadcast_history: list[dict] = []
_next_broadcast_id: int = 1
_scheduled_broadcasts: dict[int, dict] = {}  # round_number → broadcast to send


class BroadcastRequest(BaseModel):
    title: str
    body: str
    target_sessions: list[str] = []  # Empty = all sessions
    scheduled_round: Optional[int] = None  # None = send immediately


@admin_router.post(
    "/broadcast",
    summary="Broadcast a message to all or selected sessions",
)
async def broadcast_message(req: BroadcastRequest):
    global _next_broadcast_id

    broadcast = {
        "broadcast_id": f"BC-{_next_broadcast_id:04d}",
        "title": req.title,
        "body": req.body,
        "target_sessions": req.target_sessions,
        "scheduled_round": req.scheduled_round,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "delivered_to": [],
    }
    _next_broadcast_id += 1

    if req.scheduled_round:
        # Schedule for later
        _scheduled_broadcasts[req.scheduled_round] = broadcast
        broadcast["status"] = "scheduled"
        _broadcast_history.append(broadcast)
        return broadcast

    # Send immediately
    all_sessions = await db.fetch_all_sessions()
    targets = req.target_sessions if req.target_sessions else [s["session_id"] for s in all_sessions]

    message_payload = {
        "type": "broadcast_message",
        "broadcast_id": broadcast["broadcast_id"],
        "title": req.title,
        "body": req.body,
    }

    for sid in targets:
        await manager.push_to_session(sid, message_payload)
        broadcast["delivered_to"].append(sid)

    broadcast["status"] = "sent"
    _broadcast_history.append(broadcast)
    return broadcast


@admin_router.get(
    "/broadcast/history",
    summary="Get broadcast history",
)
async def get_broadcast_history():
    return {"broadcasts": _broadcast_history}


def get_scheduled_broadcasts_for_round(round_number: int) -> Optional[dict]:
    """Called by round processing to check if a broadcast should be sent."""
    return _scheduled_broadcasts.pop(round_number, None)


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Global Settings  (#1, #6, #7)
# ═════════════════════════════════════════════════════════════════

def _audit(action: str, actor: str = "god_mode", details: dict = None):
    """Append an entry to the god mode audit log."""
    _god_mode_audit_log.append({
        "id": f"AUD-{len(_god_mode_audit_log)+1:04d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "details": details or {},
    })


@admin_router.get("/god/settings", summary="Get god mode global settings")
async def get_god_settings():
    return _god_mode_settings


@admin_router.put("/god/settings", summary="Update god mode global settings")
async def update_god_settings(body: dict = Body(...)):
    changed = {}
    for key in ("allow_facilitator_cohort_creation",):
        if key in body:
            old = _god_mode_settings.get(key)
            _god_mode_settings[key] = body[key]
            changed[key] = {"old": old, "new": body[key]}
    _audit("settings_updated", details=changed)
    return _god_mode_settings


# ── Emergency Freeze (#7) ───────────────────────────────────────

@admin_router.post("/god/freeze", summary="Freeze all simulations")
async def freeze_system(body: dict = Body(...)):
    msg = body.get("message", "System maintenance in progress.")
    _god_mode_settings["system_frozen"] = True
    _god_mode_settings["freeze_message"] = msg
    _god_mode_settings["freeze_started_at"] = datetime.now(timezone.utc).isoformat()
    _audit("system_frozen", details={"message": msg})
    # Broadcast to all connected WS clients
    await manager.broadcast({
        "type": "system_freeze",
        "frozen": True,
        "message": msg,
    })
    return {"status": "frozen", "message": msg}


@admin_router.post("/god/unfreeze", summary="Unfreeze all simulations")
async def unfreeze_system():
    _god_mode_settings["system_frozen"] = False
    _god_mode_settings["freeze_message"] = ""
    _god_mode_settings["freeze_started_at"] = None
    _audit("system_unfrozen")
    await manager.broadcast({
        "type": "system_freeze",
        "frozen": False,
        "message": "",
    })
    return {"status": "unfrozen"}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Audit Log (#4)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/audit-log", summary="Get god mode audit log")
async def get_audit_log():
    return {"entries": list(reversed(_god_mode_audit_log))}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — System Status / Overview (#5)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/system-status", summary="System-wide status overview")
async def get_system_status():
    """Aggregate stats across all sessions for the God Mode overview."""
    all_sessions = db._sessions if hasattr(db, '_sessions') else {}
    total_cohorts = 0
    total_players = 0
    round_distribution = {}
    total_treasury = 0.0
    total_reputation = 0.0
    session_count_with_state = 0

    # ── Hardening Phase aggregates ──────────────────────────────
    macro_rate_distribution = {}    # regime → count
    pathway_distribution = {}      # pathway → count
    nbs_outcomes = {"succeeded": 0, "failed": 0, "not_triggered": 0}
    scope3_completeness_vals = []
    ai_monetised_count = 0
    retraining_triggered = {"succeeded": 0, "failed": 0}

    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            total_players += 1
        else:
            total_cohorts += 1
        gs = sess.get("global_state")
        if not gs:
            continue
        r = gs.get("current_round", 1)
        round_distribution[f"R{r}"] = round_distribution.get(f"R{r}", 0) + 1
        total_treasury += gs.get("treasury_balance", 0)
        total_reputation += gs.get("reputation_score", 0)
        session_count_with_state += 1

        # Hardening: flags-based aggregation
        flags = gs.get("active_event_flags", {})
        # Macro rate
        rn = gs.get("round_number", 1)
        from engine import calc_macro_rate_environment
        regime = calc_macro_rate_environment(rn).get("regime", "neutral")
        macro_rate_distribution[regime] = macro_rate_distribution.get(regime, 0) + 1
        # Pathways
        ep = flags.get("ending_pathway")
        if ep:
            pathway_distribution[ep] = pathway_distribution.get(ep, 0) + 1
        # NBS
        if "nbs_succeeded" in flags:
            if flags["nbs_succeeded"]:
                nbs_outcomes["succeeded"] += 1
            else:
                nbs_outcomes["failed"] += 1
        else:
            nbs_outcomes["not_triggered"] += 1
        # Scope 3
        s3 = gs.get("scope3_data_completeness")
        if s3 is not None:
            scope3_completeness_vals.append(s3)
        # AI monetisation
        if flags.get("ai_monetised"):
            ai_monetised_count += 1
        # Retraining
        if "retraining_succeeded" in flags:
            if flags["retraining_succeeded"]:
                retraining_triggered["succeeded"] += 1
            else:
                retraining_triggered["failed"] += 1

    # System memory (MB) — used by SystemContextBar health indicator
    try:
        import psutil
        mem_mb = round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
    except Exception:
        import os
        mem_mb = round(os.popen('tasklist /fi "pid eq %d" /fo csv /nh' % os.getpid()).read().count('K') * 0.001, 1) if os.name == 'nt' else 0

    return {
        "total_facilitators": len(_facilitator_registry),
        "total_cohorts": total_cohorts,
        "total_players": total_players,
        "round_distribution": round_distribution,
        "avg_treasury": round(total_treasury / max(session_count_with_state, 1), 2),
        "avg_reputation": round(total_reputation / max(session_count_with_state, 1), 2),
        "system_frozen": _god_mode_settings["system_frozen"],
        "recent_audit": list(reversed(_god_mode_audit_log))[:10],
        "active_ws_connections": sum(len(v) for v in manager.active_connections.values()) if hasattr(manager, 'active_connections') else 0,
        "system_memory_mb": mem_mb,
        # ── Hardening Phase ──
        "hardening": {
            "macro_rate_distribution": macro_rate_distribution,
            "pathway_distribution": pathway_distribution,
            "nbs_outcomes": nbs_outcomes,
            "avg_scope3_completeness": round(sum(scope3_completeness_vals) / max(len(scope3_completeness_vals), 1), 1) if scope3_completeness_vals else None,
            "ai_monetised_count": ai_monetised_count,
            "retraining_outcomes": retraining_triggered,
        },
    }


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — RBAC / Admin toggle (#6)
# ═════════════════════════════════════════════════════════════════

@admin_router.put("/facilitators/{fac_id}/admin", summary="Toggle admin flag")
async def toggle_facilitator_admin(fac_id: str, body: dict = Body(...)):
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, "Facilitator not found")
    is_admin = body.get("is_admin", False)
    fac["is_admin"] = is_admin
    _audit("admin_toggled", details={"facilitator_id": fac_id, "is_admin": is_admin})
    return {"status": "ok", "facilitator_id": fac_id, "is_admin": is_admin}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Universal Broadcast (#8)
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/god/universal-broadcast", summary="Broadcast to clients")
async def universal_broadcast(body: dict = Body(...)):
    title = body.get("title", "System Announcement")
    message = body.get("message", "")
    priority = body.get("priority", "info")  # info, warning, critical
    target = body.get("target", "all")  # all, students, facilitators
    payload = {
        "type": "universal_broadcast",
        "title": title,
        "message": message,
        "priority": priority,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": target,
    }
    
    if target == "students":
        await manager.broadcast_students(payload)
    elif target == "facilitators":
        await manager.broadcast_admin(payload)
    else:
        await manager.broadcast(payload)
        
    _audit("universal_broadcast", details={"title": title, "priority": priority, "target": target})
    return {"status": "sent", "payload": payload}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Batch Facilitator Create (#9)
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/facilitators/batch", summary="Batch create facilitators")
async def batch_create_facilitators(body: dict = Body(...)):
    global _next_facilitator_id
    names = body.get("names", [])
    if not names:
        raise HTTPException(400, "Provide a list of names")
    created = []
    for name in names:
        fac = {
            "facilitator_id": f"FAC-{_next_facilitator_id:03d}",
            "name": name.strip(),
            "password": "123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "max_cohorts": 5,
            "cohorts_created": 0,
            "is_admin": False,
        }
        _next_facilitator_id += 1
        _facilitator_registry.append(fac)
        created.append(fac)
    _audit("batch_facilitators_created", details={"count": len(created)})
    _persist_facilitators()
    return {"created": created, "total_facilitators": len(_facilitator_registry)}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — System Export & Backup (#10)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/export", summary="Export full system state as JSON")
async def export_system():
    all_sessions = db._sessions if hasattr(db, '_sessions') else {}
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "facilitators": _facilitator_registry,
        "sessions": {sid: {
            "cohort_name": s.get("cohort_name", ""),
            "current_round": s.get("global_state", {}).get("current_round", 1),
            "treasury": s.get("global_state", {}).get("treasury_balance", 0),
            "reputation": s.get("global_state", {}).get("reputation_score", 0),
            "player_id": s.get("player_id"),
            "parent_cohort_id": s.get("parent_cohort_id"),
        } for sid, s in all_sessions.items()},
        "god_mode_settings": _god_mode_settings,
        "audit_log": _god_mode_audit_log,
        "total_sessions": len(all_sessions),
    }
    _audit("system_export")
    return export_data


# ── Import / Restore ──
@admin_router.post("/god/import", summary="Import/restore from a backup JSON snapshot (merge mode)")
async def import_system(body: dict = Body(...)):
    """Restore sessions and facilitators from a backup.
    Merge mode: existing session IDs are skipped, new ones are created.
    """
    sessions_imported = 0
    facilitators_imported = 0
    skipped = []

    # Import facilitators
    incoming_facs = body.get("facilitators", [])
    existing_ids = {f.get("facilitator_id") for f in _facilitator_registry}
    for fac in incoming_facs:
        fid = fac.get("facilitator_id")
        if fid and fid not in existing_ids:
            _facilitator_registry.append(fac)
            facilitators_imported += 1
        else:
            skipped.append(f"facilitator:{fid}")

    # Import sessions
    incoming_sessions = body.get("sessions", {})
    all_sessions = db._sessions if hasattr(db, '_sessions') else {}
    for sid, sdata in incoming_sessions.items():
        if sid not in all_sessions:
            all_sessions[sid] = {
                "cohort_name": sdata.get("cohort_name", "Imported"),
                "global_state": {
                    "current_round": sdata.get("current_round", 1),
                    "treasury_balance": sdata.get("treasury", 0),
                    "reputation_score": sdata.get("reputation", 0),
                },
                "player_id": sdata.get("player_id"),
                "parent_cohort_id": sdata.get("parent_cohort_id"),
                "imported_at": datetime.now(timezone.utc).isoformat(),
            }
            sessions_imported += 1
        else:
            skipped.append(f"session:{sid}")

    # Import god mode settings (merge, don't overwrite)
    incoming_settings = body.get("god_mode_settings", {})
    for key, val in incoming_settings.items():
        if key not in _god_mode_settings:
            _god_mode_settings[key] = val

    _audit("system_import", details={
        "sessions_imported": sessions_imported,
        "facilitators_imported": facilitators_imported,
        "skipped": len(skipped),
    })
    await manager.broadcast_admin({
        "type": "system_imported",
        "sessions_imported": sessions_imported,
        "facilitators_imported": facilitators_imported,
    })
    return {
        "status": "ok",
        "sessions_imported": sessions_imported,
        "facilitators_imported": facilitators_imported,
        "skipped": skipped,
    }


# ── GDPR Compliance Export ──
@admin_router.get("/god/gdpr-export/{player_id}", summary="GDPR Article 15 — export all data held for a player")
async def gdpr_export(player_id: str):
    """Export all personal data held for a specific player.
    Gathers session state, decisions, KPIs, and any stored personal data.
    """
    all_sessions = db._sessions if hasattr(db, '_sessions') else {}
    player_sessions = {}
    for sid, s in all_sessions.items():
        if s.get("player_id") == player_id:
            player_sessions[sid] = {
                "cohort_name": s.get("cohort_name", ""),
                "parent_cohort_id": s.get("parent_cohort_id"),
                "current_round": s.get("global_state", {}).get("current_round", 1),
                "treasury": s.get("global_state", {}).get("treasury_balance", 0),
                "reputation": s.get("global_state", {}).get("reputation_score", 0),
                "global_state": s.get("global_state", {}),
                "flags": s.get("flags", {}),
                "round_history": s.get("round_history", []),
                "decisions": s.get("decisions", []),
                "interview_data": s.get("interview_data", {}),
            }

    if not player_sessions:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No data found for player '{player_id}'")

    _audit("gdpr_export", details={"player_id": player_id, "sessions_found": len(player_sessions)})
    return {
        "gdpr_export": True,
        "player_id": player_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "data_categories": [
            "Session state", "Game decisions", "KPI history",
            "Interview responses", "Round history", "Flags"
        ],
        "sessions": player_sessions,
        "total_sessions": len(player_sessions),
    }

# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Crisis Trigger History (#13)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/crisis-history", summary="Get crisis trigger fire history")
async def get_crisis_history():
    return {"history": list(reversed(_crisis_trigger_history))}


@admin_router.post("/god/crisis-fire", summary="Fire a crisis with history tracking")
async def fire_crisis_with_history(body: dict = Body(...)):
    crisis_type = body.get("type", "unknown")
    target = body.get("target", "global")
    entry = {
        "id": f"CRS-{len(_crisis_trigger_history)+1:04d}",
        "type": crisis_type,
        "target": target,
        "fired_at": datetime.now(timezone.utc).isoformat(),
        "fired_by": "god_mode",
    }
    _crisis_trigger_history.append(entry)
    _audit("crisis_fired", details=entry)
    return entry



# ARCH-002: Analytics + Glossary extracted to admin_analytics.py (9 endpoints)
# Mounted in main.py via app.include_router(analytics_router)


# ═════════════════════════════════════════════════════════════════
#  ECONOMIC ENGINE TUNABLES — All 16 engine constants
# ═════════════════════════════════════════════════════════════════

_engine_tunables: dict = {
    # Phase 1
    "inflation_rate": 0.025,
    "technical_debt_threshold": 2,
    "technical_debt_penalty": 0.04,
    "overrun_probability": 0.25,
    "overrun_severity": 0.15,
    "overrun_capex_floor": 3_000_000,
    "implementation_lag_threshold": 0.10,
    "vrio_imitation_decay_rate": 0.05,
    # Phase 2
    "cannibalization_rate": 0.03,
    "stakeholder_fatigue_factor": 0.3,
    "supply_chain_overlap_coeff": 0.002,
    "competitor_growth_rate": 0.03,
    "cash_conversion_base": 1.0,
    "dividend_cut_threshold": 0.80,
    "dividend_reputation_penalty": 5.0,
    "talent_neglect_threshold": 0.15,
    "talent_neglect_penalty": 0.02,
    "lockin_streak_threshold": 3,
    "lockin_synergy_penalty": 0.15,
    "greenwashing_investment_threshold": 0.15,
    "greenwashing_penalty": 8.0,
    "fog_of_war_rounds": 3,
    "fog_noise_range": 0.10,
}


@admin_router.get("/engine-tunables", summary="Get all economic engine tunables")
async def get_engine_tunables():
    return {"tunables": _engine_tunables, "descriptions": {
        "inflation_rate": "Annual OPEX inflation applied each round (0.025 = 2.5%)",
        "technical_debt_threshold": "Rounds of zero investment before penalty kicks in",
        "technical_debt_penalty": "OPEX multiplier penalty for neglected BUs",
        "overrun_probability": "Chance of cost overrun on large CAPEX (0-1)",
        "overrun_severity": "Cost overrun magnitude when triggered (0-1)",
        "overrun_capex_floor": "Minimum CAPEX ($) to trigger overrun risk",
        "implementation_lag_threshold": "Investment ratio above which synergy is deferred 1 round",
        "vrio_imitation_decay_rate": "Rate at which synergy decays per round (0-1)",
        "cannibalization_rate": "Revenue stolen from victim BU when aggressor dominates",
        "stakeholder_fatigue_factor": "Trust recovery decay factor per crisis (higher = harsher)",
        "supply_chain_overlap_coeff": "Cross-BU governance risk contagion coefficient",
        "competitor_growth_rate": "NPC competitor annual EBITDA growth rate",
        "cash_conversion_base": "Base revenue-to-cash efficiency (1.0 = perfect)",
        "dividend_cut_threshold": "% of prior dividends below which ratchet triggers",
        "dividend_reputation_penalty": "Reputation points lost when dividend ratchet fires",
        "talent_neglect_threshold": "CAPEX share below which BU suffers talent penalty",
        "talent_neglect_penalty": "OPEX surcharge rate for neglected BUs",
        "lockin_streak_threshold": "Consecutive rounds of top investment before lock-in",
        "lockin_synergy_penalty": "Synergy penalty on non-locked BUs when lock-in active",
        "greenwashing_investment_threshold": "Avg investment ratio below which green rhetoric = scandal",
        "greenwashing_penalty": "Social license points lost in greenwashing scandal",
        "fog_of_war_rounds": "Number of early rounds with metric noise active",
        "fog_noise_range": "Max ±noise factor for fog of war metrics",
    }}


@admin_router.patch("/engine-tunables", summary="Update economic engine tunables")
async def update_engine_tunables(body: dict = Body(...)):
    changed = {}
    for key, val in body.items():
        if key in _engine_tunables:
            old = _engine_tunables[key]
            _engine_tunables[key] = val
            changed[key] = {"old": old, "new": val}
    # Sync to god_mode_settings for backward compat
    _god_mode_settings["overrun_probability"] = _engine_tunables["overrun_probability"]
    _god_mode_settings["overrun_severity"] = _engine_tunables["overrun_severity"]
    _audit("engine_tunables_updated", details=changed)
    return {"tunables": _engine_tunables, "changed": changed}


# ═════════════════════════════════════════════════════════════════
#  SCENARIO PRESETS — Pre-configured difficulty templates
# ═════════════════════════════════════════════════════════════════

_scenario_presets: list[dict] = [
    {
        "id": "classroom_easy",
        "name": "Classroom",
        "description": "Gentle settings for introductory classes. Reduced complexity, forgiving penalties, core engines only.",
        "icon": "🎓",
        "subtitle": "Easy · Foundation Visibility",
        "color": "#10b981",
        "difficulty_tier": "foundation",
        "target_audience": "Undergraduates, non-business learners",
        "default_pedagogy": {
            "round_recap_enabled": True,
            "real_world_cards_enabled": True,
            "debrief_protocol_enabled": True,
            "prediction_gates_enabled": False,
            "confidence_calibration_enabled": False,
            "strategy_memo_enabled": False,
            "self_learning_mode": False,
        },
        "tunables": {
            "inflation_rate": 0.015,
            "overrun_probability": 0.10,
            "overrun_severity": 0.10,
            "technical_debt_threshold": 3,
            "technical_debt_penalty": 0.02,
            "stakeholder_fatigue_factor": 0.15,
            "greenwashing_penalty": 4.0,
            "dividend_reputation_penalty": 2.0,
            "fog_of_war_rounds": 1,
            "competitor_growth_rate": 0.02,
        }
    },
    {
        "id": "workshop_standard",
        "name": "Workshop",
        "description": "Balanced settings for corporate workshops. Progressive engine disclosure, moderate penalties.",
        "icon": "🏢",
        "subtitle": "Standard · Progressive Disclosure",
        "color": "#6366f1",
        "difficulty_tier": "advanced",
        "target_audience": "MBA, sustainability professionals",
        "default_pedagogy": {
            "round_recap_enabled": True,
            "real_world_cards_enabled": False,
            "debrief_protocol_enabled": False,
            "prediction_gates_enabled": False,
            "confidence_calibration_enabled": True,
            "strategy_memo_enabled": False,
            "self_learning_mode": False,
        },
        "tunables": {
            "inflation_rate": 0.025,
            "overrun_probability": 0.25,
            "overrun_severity": 0.15,
            "technical_debt_threshold": 2,
            "technical_debt_penalty": 0.04,
            "stakeholder_fatigue_factor": 0.3,
            "greenwashing_penalty": 8.0,
            "dividend_reputation_penalty": 5.0,
            "fog_of_war_rounds": 3,
            "competitor_growth_rate": 0.03,
        }
    },
    {
        "id": "executive_hard",
        "name": "Executive",
        "description": "Aggressive parameters for experienced executives. All engines visible, punishing penalties.",
        "icon": "💼",
        "subtitle": "Hard · Full Visibility + Audit Trail",
        "color": "#f59e0b",
        "difficulty_tier": "expert",
        "target_audience": "Senior leadership, doctoral, consultants",
        "default_pedagogy": {
            "round_recap_enabled": False,
            "real_world_cards_enabled": False,
            "debrief_protocol_enabled": False,
            "prediction_gates_enabled": True,
            "confidence_calibration_enabled": True,
            "strategy_memo_enabled": True,
            "self_learning_mode": False,
        },
        "tunables": {
            "inflation_rate": 0.040,
            "overrun_probability": 0.35,
            "overrun_severity": 0.20,
            "technical_debt_threshold": 1,
            "technical_debt_penalty": 0.06,
            "stakeholder_fatigue_factor": 0.5,
            "greenwashing_penalty": 12.0,
            "dividend_reputation_penalty": 8.0,
            "fog_of_war_rounds": 4,
            "competitor_growth_rate": 0.05,
        }
    },
    {
        "id": "chaos_mode",
        "name": "Chaos Mode",
        "description": "Maximum volatility. Every engine cranked to extreme. All scaffolding disabled. Stress-testing only.",
        "icon": "🔥",
        "subtitle": "Extreme · No Scaffolding",
        "color": "#ef4444",
        "difficulty_tier": "expert",
        "target_audience": "Stress-testing and advanced research",
        "default_pedagogy": {
            "round_recap_enabled": False,
            "real_world_cards_enabled": False,
            "debrief_protocol_enabled": False,
            "prediction_gates_enabled": False,
            "confidence_calibration_enabled": False,
            "strategy_memo_enabled": False,
            "self_learning_mode": False,
        },
        "tunables": {
            "inflation_rate": 0.060,
            "overrun_probability": 0.50,
            "overrun_severity": 0.25,
            "technical_debt_threshold": 1,
            "technical_debt_penalty": 0.08,
            "stakeholder_fatigue_factor": 0.7,
            "greenwashing_penalty": 15.0,
            "dividend_reputation_penalty": 10.0,
            "fog_of_war_rounds": 5,
            "competitor_growth_rate": 0.07,
            "cannibalization_rate": 0.06,
            "lockin_streak_threshold": 2,
            "lockin_synergy_penalty": 0.25,
        }
    },
]


@admin_router.get("/scenario-presets", summary="Get available scenario presets")
async def get_scenario_presets():
    return {"presets": _scenario_presets, "current_tunables": _engine_tunables}


@admin_router.put("/cohort/{session_id}/pedagogical-settings", summary="Save per-cohort pedagogical settings")
async def save_cohort_pedagogical_settings(session_id: str, body: dict = Body(...)):
    """Store experience level, difficulty tier, and pedagogical toggles per-cohort."""
    session = db._sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Store per-cohort settings
    if "experience_level" in body:
        session["experience_level"] = body["experience_level"]
    if "difficulty_tier" in body:
        session["difficulty_tier"] = body["difficulty_tier"]
    
    # Store pedagogical toggle overrides on the session
    pedagogical_keys = {
        "prediction_gates_enabled", "confidence_calibration_enabled",
        "round_recap_enabled", "real_world_cards_enabled",
        "strategy_memo_enabled", "debrief_protocol_enabled",
        "self_learning_mode",
    }
    cohort_pedagogy = session.get("pedagogical_overrides", {})
    for key in pedagogical_keys:
        if key in body:
            cohort_pedagogy[key] = body[key]
    session["pedagogical_overrides"] = cohort_pedagogy
    
    from database_memory import _persist
    _persist()
    
    _audit("cohort_pedagogical_settings_saved", details={
        "session_id": session_id,
        "experience_level": body.get("experience_level"),
        "difficulty_tier": body.get("difficulty_tier"),
    })
    
    return {
        "status": "ok",
        "session_id": session_id,
        "experience_level": session.get("experience_level"),
        "difficulty_tier": session.get("difficulty_tier"),
        "pedagogical_overrides": cohort_pedagogy,
    }


@admin_router.put("/cohort/{session_id}/pacing", summary="Save per-cohort round pacing settings")
async def save_cohort_pacing(session_id: str, body: dict = Body(...)):
    """Store pacing mode and max unlocked round per-cohort.
    Once a facilitator sets pacing, God Mode cannot override it."""
    session = db._sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Track who is setting pacing
    set_by = body.get("facilitator_id", "")
    source = body.get("source", "facilitator")  # "facilitator" or "god_mode"
    
    # Protection: If a facilitator already set pacing, god-mode cannot override
    if source == "god_mode" and is_pacing_set_by_facilitator(session_id):
        raise HTTPException(
            403,
            "Pacing was set by a facilitator and cannot be overridden by God Mode. "
            "Only the owning facilitator can change pacing for this cohort."
        )
    
    if "pacing_mode" in body:
        session["pacing_mode"] = body["pacing_mode"]  # free_play | manual | scheduled
    if "max_unlocked_round" in body:
        session["max_unlocked_round"] = int(body["max_unlocked_round"])
    if "round_schedules" in body:
        session["round_schedules"] = body["round_schedules"]
    
    # Update pacing ownership tracking in shared state
    pacing = _get_pacing(session_id)
    if source == "facilitator" and body.get("pacing_mode", "free_play") != "free_play":
        pacing["set_by"] = set_by or "unknown_facilitator"
    pacing["mode"] = body.get("pacing_mode", pacing.get("mode", "free"))
    
    from database_memory import _persist
    _persist()
    
    _audit("cohort_pacing_saved", details={
        "session_id": session_id,
        "pacing_mode": body.get("pacing_mode"),
        "max_unlocked_round": body.get("max_unlocked_round"),
        "set_by": set_by,
        "source": source,
    })
    
    return {
        "status": "ok",
        "session_id": session_id,
        "pacing_mode": session.get("pacing_mode", "free_play"),
        "max_unlocked_round": session.get("max_unlocked_round", 10),
        "set_by": pacing.get("set_by"),
    }

@admin_router.post("/scenario-presets/apply/{preset_id}", summary="Apply a scenario preset")
async def apply_scenario_preset(preset_id: str):
    preset = next((p for p in _scenario_presets if p["id"] == preset_id), None)
    if not preset:
        raise HTTPException(404, f"Preset '{preset_id}' not found")
    changed = {}
    for key, val in preset["tunables"].items():
        if key in _engine_tunables:
            old = _engine_tunables[key]
            _engine_tunables[key] = val
            changed[key] = {"old": old, "new": val}
    _god_mode_settings["overrun_probability"] = _engine_tunables["overrun_probability"]
    _god_mode_settings["overrun_severity"] = _engine_tunables["overrun_severity"]
    _audit("scenario_preset_applied", details={"preset": preset_id, "changed_count": len(changed)})
    return {"applied": preset_id, "name": preset["name"], "tunables": _engine_tunables, "changed": changed}


@admin_router.post("/scenario-presets", summary="Save a custom scenario preset")
async def save_custom_preset(body: dict = Body(...)):
    preset_id = body.get("id", f"custom_{len(_scenario_presets)+1}")
    preset = {
        "id": preset_id,
        "name": body.get("name", "Custom Preset"),
        "description": body.get("description", ""),
        "icon": body.get("icon", "⚙️"),
        "tunables": body.get("tunables", dict(_engine_tunables)),
        "is_custom": True,
    }
    _scenario_presets.append(preset)
    _audit("custom_preset_created", details={"preset_id": preset_id})
    return preset


@admin_router.delete("/scenario-presets/{preset_id}", summary="Delete a custom scenario preset")
async def delete_custom_preset(preset_id: str):
    global _scenario_presets
    preset = next((p for p in _scenario_presets if p["id"] == preset_id), None)
    if not preset:
        raise HTTPException(404, "Preset not found")
    if not preset.get("is_custom"):
        raise HTTPException(403, "Cannot delete built-in presets")
    _scenario_presets = [p for p in _scenario_presets if p["id"] != preset_id]
    return {"deleted": preset_id}


# ═════════════════════════════════════════════════════════════════
#  COMPLEXITY EVENT FEED — Surface engine events as human-readable
# ═════════════════════════════════════════════════════════════════

_COMPLEXITY_EVENT_LABELS = {
    "greenwashing_scandal": ("🌿🚨", "Greenwashing Scandal", "critical"),
    "dividend_ratchet_triggered": ("📉", "Dividend Ratchet Triggered", "warning"),
    "technology_lockin_penalty": ("🔒", "Technology Lock-In Active", "warning"),
    "fog_of_war_active": ("🌫️", "Fog of War Active", "info"),
    "stakeholder_fatigue_applied": ("😰", "Stakeholder Fatigue Hit", "warning"),
    "regulatory_ratchet_active": ("📜", "Regulatory Ratchet Floor Active", "info"),
    "inflation_index_increased": ("📈", "Inflation Index Increased", "info"),
    "tipping_point_reached": ("🌡️", "Climate Tipping Point Reached!", "critical"),
    "stranded_asset_penalty_applied": ("🏭", "Stranded Asset Penalty", "warning"),
    "institutional_leakage": ("🏛️", "Institutional Leakage (SDG)", "warning"),
    "sanitation_miracle": ("🚰", "Sanitation Miracle Bonus!", "success"),
    "carbon_retribution_triggered": ("⚡", "Carbon Retribution Active", "critical"),
    "migration_service_penalty": ("🚶", "Migration Contagion Penalty", "warning"),
    "education_lag_mature": ("📚", "Education Investment Matured", "success"),
}


@admin_router.get("/complexity-events/{session_id}", summary="Get complexity engine events for a session")
async def get_complexity_events(session_id: str):
    """Surface the 16 engine events from a session's latest state as human-readable cards."""
    global_states = getattr(db, '_global_states', {})
    rounds = global_states.get(session_id, [])
    if not rounds:
        raise HTTPException(404, "No round data")

    feed = []
    for grs in rounds:
        rn = grs.get("round_number", 1)
        flags = grs.get("active_event_flags", {})
        round_events = []
        for key, value in flags.items():
            if key in _COMPLEXITY_EVENT_LABELS and value:
                icon, label, severity = _COMPLEXITY_EVENT_LABELS[key]
                round_events.append({
                    "key": key,
                    "icon": icon,
                    "label": label,
                    "severity": severity,
                    "value": value,
                    "round": rn,
                })
            # Dynamic per-BU events
            for prefix, (picon, plabel, psev) in [
                ("technical_debt_penalty_", ("🛠️", "Technical Debt", "warning")),
                ("revenue_cannibalized_", ("🍽️", "Revenue Cannibalized", "warning")),
                ("supply_chain_contagion_", ("🔗", "Supply Chain Contagion", "info")),
                ("cash_conversion_drag_", ("💸", "Cash Conversion Drag", "info")),
                ("talent_neglect_surcharge_", ("🧑‍💼", "Talent Neglect", "warning")),
                ("overrun_penalty_", ("💥", "Cost Overrun!", "critical")),
            ]:
                if key.startswith(prefix) and value:
                    bu_id = key[len(prefix):]
                    round_events.append({
                        "key": key, "icon": picon,
                        "label": f"{plabel}: {bu_id}",
                        "severity": psev,
                        "value": value if isinstance(value, (int, float, str)) else True,
                        "round": rn,
                    })
            # Competitor warning
            if key == "competitor_warning" and value:
                round_events.append({
                    "key": key, "icon": "🏆", "label": "Competitor Warning",
                    "severity": "warning", "value": value, "round": rn,
                })
        if round_events:
            feed.append({"round": rn, "events": round_events})

    return {"session_id": session_id, "feed": feed}


# ═════════════════════════════════════════════════════════════════
#  SESSION HEALTH MONITOR — Live heatmap data
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/session-health", summary="Get health status of all sessions")
async def get_session_health():
    """
    Returns compact health indicators for each cohort.
    Status: active, idle, stuck, disconnected.
    """
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    now = datetime.now(timezone.utc)
    health = []

    for sid, sess in all_sessions.items():
        if sess.get("player_id") or sess.get("deleted_at"):
            continue  # Skip player sub-sessions and deleted sessions

        gs_list = global_states.get(sid, [])
        latest_gs = gs_list[-1] if gs_list else {}
        round_num = latest_gs.get("round_number", 1)

        # Compute health metrics
        treasury = float(latest_gs.get("corporate_treasury", 0))
        reputation = float(latest_gs.get("group_reputation", 50))
        synergy = float(latest_gs.get("synergy_multiplier", 1.0))
        ebitda = float(latest_gs.get("historical_ebitda", 0))
        inflation = float(latest_gs.get("inflation_index", 0.025))
        competitor = float(latest_gs.get("competitor_ebitda", 0))

        # Count active events
        flags = latest_gs.get("active_event_flags", {})
        crisis_count = sum(1 for k, v in flags.items()
                          if v and k in _COMPLEXITY_EVENT_LABELS)

        # Determine health status
        if round_num >= 10:
            status = "completed"
            status_color = "#8b5cf6"
        elif treasury < 0:
            status = "critical"
            status_color = "#ef4444"
        elif reputation < 25:
            status = "warning"
            status_color = "#f59e0b"
        elif crisis_count >= 3:
            status = "stressed"
            status_color = "#f97316"
        else:
            status = "healthy"
            status_color = "#22c55e"

        # Relative advantage vs competitor
        relative_advantage = round(ebitda / competitor, 2) if competitor > 0 else 1.0

        health.append({
            "session_id": sid,
            "cohort_name": sess.get("cohort_name", sid[:12]),
            "facilitator_id": sess.get("facilitator_id", "—"),
            "paradigm": sess.get("decision_paradigm", "legacy_abc"),
            "round": round_num,
            "status": status,
            "status_color": status_color,
            "treasury_m": round(treasury / 1_000_000, 2),
            "reputation": round(reputation, 1),
            "synergy": round(synergy, 3),
            "ebitda_m": round(ebitda / 1_000_000, 2),
            "inflation": round(inflation, 4),
            "active_crises": crisis_count,
            "relative_advantage": relative_advantage,
            "caroic": flags.get("caroic", {}),
        })

    # Sort: critical first, then by round
    health.sort(key=lambda h: (
        {"critical": 0, "warning": 1, "stressed": 2, "healthy": 3, "completed": 4}.get(h["status"], 5),
        -h["round"]
    ))

    return {"sessions": health, "total": len(health)}


# ═════════════════════════════════════════════════════════════════
#  SESSION CLONING — Fork a cohort for what-if exploration
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/sessions/{session_id}/clone", summary="Clone a session for what-if scenarios")
async def clone_session(session_id: str, body: dict = Body(...)):
    """Deep-clone a cohort's current state into a new session."""
    import copy
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states_store = getattr(db, '_bu_states', {})

    source = all_sessions.get(session_id)
    if not source:
        raise HTTPException(404, "Source session not found")

    clone_name = body.get("name", f"{source.get('cohort_name', 'Clone')} (Fork)")
    new_sid = f"clone-{session_id[:8]}-{datetime.now(timezone.utc).strftime('%H%M%S')}"

    # Deep copy session
    cloned_session = copy.deepcopy(source)
    cloned_session["cohort_name"] = clone_name
    cloned_session["cloned_from"] = session_id
    cloned_session["cloned_at"] = datetime.now(timezone.utc).isoformat()
    all_sessions[new_sid] = cloned_session

    # Deep copy global states
    if session_id in global_states:
        global_states[new_sid] = copy.deepcopy(global_states[session_id])

    # Deep copy BU states
    if session_id in bu_states_store:
        bu_states_store[new_sid] = copy.deepcopy(bu_states_store[session_id])

    _audit("session_cloned", details={
        "source": session_id,
        "clone_id": new_sid,
        "clone_name": clone_name,
    })

    return {
        "clone_id": new_sid,
        "clone_name": clone_name,
        "source_id": session_id,
        "round": cloned_session.get("global_state", {}).get("round_number", 1),
    }


# ═════════════════════════════════════════════════════════════════
#  AUTO-PAUSE TRIGGERS — Configurable pause-on-event rules
# ═════════════════════════════════════════════════════════════════

_auto_pause_triggers: dict = {
    "enabled": False,
    "triggers": {
        "greenwashing_scandal": True,
        "technology_lockin_penalty": True,
        "tipping_point_reached": True,
        "dividend_ratchet_triggered": False,
        "stakeholder_fatigue_applied": False,
        "treasury_negative": True,
        "reputation_below_20": True,
    },
    "pause_message": "⏸️ Simulation paused by facilitator for discussion.",
}


@admin_router.get("/auto-pause", summary="Get auto-pause trigger configuration")
async def get_auto_pause():
    return _auto_pause_triggers


@admin_router.put("/auto-pause", summary="Update auto-pause trigger configuration")
async def set_auto_pause(body: dict = Body(...)):
    if "enabled" in body:
        _auto_pause_triggers["enabled"] = bool(body["enabled"])
    if "triggers" in body:
        for key, val in body["triggers"].items():
            if key in _auto_pause_triggers["triggers"]:
                _auto_pause_triggers["triggers"][key] = bool(val)
    if "pause_message" in body:
        _auto_pause_triggers["pause_message"] = str(body["pause_message"])
    _audit("auto_pause_updated", details=_auto_pause_triggers)
    return _auto_pause_triggers


def check_auto_pause_triggers(events: dict, global_state: dict) -> Optional[str]:
    """Called by process_tick to check if auto-pause should fire."""
    if not _auto_pause_triggers["enabled"]:
        return None
    triggers = _auto_pause_triggers["triggers"]
    for event_key, enabled in triggers.items():
        if not enabled:
            continue
        if event_key == "treasury_negative" and global_state.get("corporate_treasury", 0) < 0:
            return f"Treasury went negative (${global_state['corporate_treasury']:,.0f})"
        if event_key == "reputation_below_20" and global_state.get("group_reputation", 50) < 20:
            return f"Reputation dropped to {global_state['group_reputation']:.1f}"
        if event_key in events and events[event_key]:
            label = _COMPLEXITY_EVENT_LABELS.get(event_key, ("", event_key, ""))[1]
            return f"{label} triggered"
    return None


# ═════════════════════════════════════════════════════════════════
#  DECISION HISTORY REPLAY — Full decision timeline per session
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/decision-history/{session_id}", summary="Full decision timeline for a session")
async def get_decision_history(session_id: str):
    """Reconstruct the complete decision history with state snapshots."""
    global_states = getattr(db, '_global_states', {})
    bu_states_store = getattr(db, '_bu_states', {})
    decision_log = getattr(db, '_decision_log', [])

    rounds = global_states.get(session_id, [])
    if not rounds:
        raise HTTPException(404, "No history for this session")

    session_decisions = [d for d in decision_log if d.get("session_id") == session_id]
    dec_by_round = {}
    for d in session_decisions:
        rn = d.get("round_number", 0)
        if rn not in dec_by_round:
            dec_by_round[rn] = []
        dec_by_round[rn].append(d)

    timeline = []
    for i, grs in enumerate(rounds):
        rn = grs.get("round_number", 1)
        flags = grs.get("active_event_flags", {})
        bus = bu_states_store.get(session_id, {}).get(rn, [])

        # Extract complexity events for this round
        round_complexity = []
        for key, value in flags.items():
            if key in _COMPLEXITY_EVENT_LABELS and value:
                icon, label, sev = _COMPLEXITY_EVENT_LABELS[key]
                round_complexity.append({"icon": icon, "label": label, "severity": sev})

        # Get decisions for this round
        round_decs = dec_by_round.get(rn, [])
        choices = [d.get("choice_selected", "") for d in round_decs if d.get("choice_selected")]
        total_capex = sum(d.get("capex_allocated", 0) for d in round_decs)

        timeline.append({
            "round": rn,
            "treasury_m": round(float(grs.get("corporate_treasury", 0)) / 1_000_000, 2),
            "reputation": round(float(grs.get("group_reputation", 50)), 1),
            "synergy": round(float(grs.get("synergy_multiplier", 1.0)), 3),
            "ebitda_m": round(float(grs.get("historical_ebitda", 0)) / 1_000_000, 2),
            "inflation": round(float(grs.get("inflation_index", 0.025)), 4),
            "cost_of_capital": round(float(grs.get("cost_of_capital", 0.05)), 4),
            "choices": choices,
            "total_capex": round(total_capex, 0),
            "complexity_events": round_complexity,
            "bu_summary": [{
                "bu_id": b.get("bu_id", ""),
                "revenue_m": round(float(b.get("revenue_base", 0)) / 1_000_000, 2),
                "opex_m": round(float(b.get("opex_base", 0)) / 1_000_000, 2),
                "social_license": round(float(b.get("social_license_score", 50)), 1),
                "governance_risk": round(float(b.get("governance_risk_score", 0)), 1),
            } for b in bus],
        })

    return {"session_id": session_id, "timeline": timeline}


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR ANNOTATIONS — Tag sessions with teaching notes
# ═════════════════════════════════════════════════════════════════

_annotations: dict[str, list[dict]] = {}  # session_id → [annotation dicts]


@admin_router.get("/annotations/{session_id}", summary="Get annotations for a session")
async def get_annotations(session_id: str):
    return {"annotations": _annotations.get(session_id, [])}


@admin_router.post("/annotations/{session_id}", summary="Add an annotation")
async def add_annotation(session_id: str, body: dict = Body(...)):
    if session_id not in _annotations:
        _annotations[session_id] = []
    annotation = {
        "id": f"ANN-{len(_annotations[session_id])+1:04d}",
        "round": body.get("round", 0),
        "text": body.get("text", ""),
        "tag": body.get("tag", "general"),  # general, teaching_moment, warning, insight
        "visible_to_students": body.get("visible_to_students", True),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": body.get("author", "facilitator"),
    }
    _annotations[session_id].append(annotation)
    return annotation


@admin_router.delete("/annotations/{session_id}/{annotation_id}", summary="Delete an annotation")
async def delete_annotation(session_id: str, annotation_id: str):
    if session_id in _annotations:
        _annotations[session_id] = [a for a in _annotations[session_id] if a["id"] != annotation_id]
    return {"deleted": annotation_id}


@admin_router.put("/annotations/{session_id}/visibility", summary="Toggle student visibility of annotations")
async def set_annotations_visibility(session_id: str, body: dict = Body(...)):
    """Enable or disable student visibility of facilitator annotations for a cohort."""
    import database_memory as db_mem
    sess = db_mem._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    player_visible = bool(body.get("player_visible", False))
    sess["annotations_player_visible"] = player_visible
    db_mem._persist()
    return {"session_id": session_id, "annotations_player_visible": player_visible, "status": "saved"}



# ARCH-002: Teleprompter extracted to admin_teleprompter.py
from admin_teleprompter import teleprompter_router

# ═════════════════════════════════════════════════════════════════
#  CROSS-PARADIGM NORMALIZED COMPARISON
# ═════════════════════════════════════════════════════════════════

_PARADIGM_NORMALIZATION = {
    "legacy_abc":       {"exit_multiple": 12.0, "max_mr": 1.98, "carbon_tax": 250},
    "multi_toggles":    {"exit_multiple": 12.0, "max_mr": 1.98, "carbon_tax": 250},
    "advanced_climate": {"exit_multiple": 12.0, "max_mr": 1.98, "carbon_tax": 250},
    "healthcare":       {"exit_multiple": 14.0, "max_mr": 1.98, "carbon_tax": 180},
}

# Reference paradigm for normalization
_REFERENCE_PARADIGM = _PARADIGM_NORMALIZATION["legacy_abc"]


@admin_router.get("/cross-paradigm-comparison", summary="Normalized cross-paradigm cohort comparison")
async def get_cross_paradigm_comparison():
    """
    Compare cohorts across different paradigms by normalizing Terminal Values.
    Adjusts for exit multiple and carbon tax differences so HC and NC cohorts
    can be fairly compared on strategic quality rather than structural advantages.

    Normalized_TV = Raw_TV × (ref_exit / paradigm_exit)
    """
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})

    comparisons = []
    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            continue

        paradigm = sess.get("decision_paradigm", "legacy_abc")
        norms = _PARADIGM_NORMALIZATION.get(paradigm, _REFERENCE_PARADIGM)
        ref = _REFERENCE_PARADIGM

        gs_list = global_states.get(sid, [])
        latest = gs_list[-1] if gs_list else {}
        flags = latest.get("active_event_flags", {})

        raw_tv = float(latest.get("terminal_value", 0))
        raw_mr = float(latest.get("regenerative_multiple", 1.0))
        raw_ebitda = float(latest.get("historical_ebitda", 0))

        # Normalize TV: adjust for exit multiple difference
        exit_ratio = ref["exit_multiple"] / norms["exit_multiple"] if norms["exit_multiple"] > 0 else 1.0
        normalized_tv = round(raw_tv * exit_ratio, 2)

        # Strategic efficiency: M_R as % of max achievable
        mr_efficiency = round((raw_mr / norms["max_mr"]) * 100, 1) if norms["max_mr"] > 0 else 0

        comparisons.append({
            "session_id": sid,
            "cohort_name": sess.get("cohort_name", sid[:12]),
            "paradigm": paradigm,
            "round": latest.get("round_number", 1),
            "raw_terminal_value_m": round(raw_tv / 1_000_000, 2),
            "normalized_terminal_value_m": round(normalized_tv / 1_000_000, 2),
            "normalization_factor": round(exit_ratio, 4),
            "regenerative_multiple": round(raw_mr, 4),
            "mr_efficiency_pct": mr_efficiency,
            "max_achievable_mr": norms["max_mr"],
            "exit_multiple": norms["exit_multiple"],
            "carbon_tax": norms["carbon_tax"],
            "ebitda_m": round(raw_ebitda / 1_000_000, 2),
            "treasury_m": round(float(latest.get("corporate_treasury", 0)) / 1_000_000, 2),
            "reputation": round(float(latest.get("group_reputation", 50)), 1),
            "tipping_point": bool(latest.get("tipping_point_active", False)),
        })

    comparisons.sort(key=lambda c: -c["normalized_terminal_value_m"])
    return {"comparisons": comparisons, "total": len(comparisons), "reference_paradigm": "legacy_abc"}


# ═════════════════════════════════════════════════════════════════
#  COHORT COMPARISON — Side-by-side analytics
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/cohort-comparison", summary="Side-by-side cohort comparison")
async def get_cohort_comparison(facilitator_id: str = None):
    """Compare all cohorts (or a facilitator's cohorts) side by side."""
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})

    comparisons = []
    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            continue
        if facilitator_id and sess.get("facilitator_id") != facilitator_id:
            continue

        gs_list = global_states.get(sid, [])
        latest = gs_list[-1] if gs_list else {}
        flags = latest.get("active_event_flags", {})

        comparisons.append({
            "session_id": sid,
            "cohort_name": sess.get("cohort_name", sid[:12]),
            "paradigm": sess.get("decision_paradigm", "legacy_abc"),
            "round": latest.get("round_number", 1),
            "treasury_m": round(float(latest.get("corporate_treasury", 0)) / 1_000_000, 2),
            "reputation": round(float(latest.get("group_reputation", 50)), 1),
            "synergy": round(float(latest.get("synergy_multiplier", 1.0)), 3),
            "ebitda_m": round(float(latest.get("historical_ebitda", 0)) / 1_000_000, 2),
            "inflation": round(float(latest.get("inflation_index", 0.025)), 4),
            "competitor_ebitda_m": round(float(latest.get("competitor_ebitda", 0)) / 1_000_000, 2),
            "cost_of_capital": round(float(latest.get("cost_of_capital", 0.05)), 4),
            "active_crises": sum(1 for k, v in flags.items() if k in _COMPLEXITY_EVENT_LABELS and v),
            "greenwashing": bool(flags.get("greenwashing_scandal")),
            "lockin": bool(flags.get("technology_lockin_penalty")),
            "fog": bool(flags.get("fog_of_war_active")),
            "caroic_pct": float(flags.get("caroic", {}).get("caroic_pct", 0)),
            "caroic_grade": flags.get("caroic", {}).get("grade", "—"),
        })

    comparisons.sort(key=lambda c: -c["treasury_m"])
    return {"cohorts": comparisons, "total": len(comparisons)}


# ── Cohort Pulse — real-time KPI heatmap for CohortPulse.js ──────────────────
@admin_router.get("/cohort-pulse/{cohort_id}", summary="Real-time KPI heatmap for cohort")
async def get_cohort_pulse(cohort_id: str):
    """
    Returns per-team KPI history and current state for the CohortPulse heatmap.
    Includes climate-engine fields: green_fund, cost_of_capital, carbon_fee_paid.
    """
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states_store = getattr(db, '_bu_states', {})

    teams = []
    for sid, sess in all_sessions.items():
        # Only player sessions whose parent cohort matches, or the cohort session itself
        parent = sess.get("parent_cohort_id")
        if parent == cohort_id or sid == cohort_id:
            gs_list = global_states.get(sid, [])
            history = {}
            cumulative_carbon_fee = 0.0

            for gs in gs_list:
                r = gs.get("round_number", 1)
                flags = gs.get("active_event_flags") or {}
                fee_this_round = flags.get("internal_carbon_fee_deducted", 0) or 0
                cumulative_carbon_fee += fee_this_round
                # Compute average SLO from BU states for this round
                buses_for_round = bu_states_store.get(sid, {}).get(r, [])
                avg_slo = (
                    sum(b.get("social_license_score", 50) for b in buses_for_round) / len(buses_for_round)
                    if buses_for_round else 50
                )
                history[r] = {
                    "treasury": gs.get("corporate_treasury", 0),
                    "reputation": gs.get("group_reputation", 50),
                    "carbon": gs.get("tco2e_emissions", 0),
                    "social_license": round(avg_slo, 1),
                    "synergy": gs.get("synergy_multiplier", 1.0),
                    # Climate-specific fields
                    "green_fund": gs.get("green_transition_fund", 0),
                    "cost_of_capital": gs.get("cost_of_capital", 0.05),
                    "carbon_fee_paid": cumulative_carbon_fee,
                }

            latest = gs_list[-1] if gs_list else {}
            latest_rn = latest.get("round_number", 1)
            flags = latest.get("active_event_flags", {}) or {}
            total_fee = sum(
                (gs.get("active_event_flags", {}) or {}).get("internal_carbon_fee_deducted", 0) or 0
                for gs in gs_list
            )
            # Average SLO for the latest round
            latest_bus = bu_states_store.get(sid, {}).get(latest_rn, [])
            latest_slo = (
                sum(b.get("social_license_score", 50) for b in latest_bus) / len(latest_bus)
                if latest_bus else 50
            )

            teams.append({
                "name": sess.get("cohort_name") or sess.get("player_name") or sid[:10],
                "session_id": sid,
                "history": history,
                "current": {
                    "treasury": latest.get("corporate_treasury", 0),
                    "reputation": latest.get("group_reputation", 50),
                    "carbon": latest.get("tco2e_emissions", 0),
                    "social_license": round(latest_slo, 1),
                    "synergy": latest.get("synergy_multiplier", 1.0),
                    "green_fund": latest.get("green_transition_fund", 0),
                    "cost_of_capital": latest.get("cost_of_capital", 0.05),
                    "carbon_fee_paid": total_fee,
                },
                "round": latest.get("round_number", 1),
                "tipping_point": bool(latest.get("tipping_point_active", False)),
            })

    teams.sort(key=lambda t: -t["current"]["treasury"])
    return {
        "teams": teams,
        "cohort_id": cohort_id,
        "total_teams": len(teams),
        "player_visible": all_sessions.get(cohort_id, {}).get("cohort_pulse_player_visible", False),
    }


@admin_router.post("/cohort-pulse/{cohort_id}/visibility", summary="Set player-visibility of the CohortPulse heatmap")
async def set_cohort_pulse_visibility(cohort_id: str, body: dict = Body(...)):
    """
    Persists whether the CohortPulse KPI heatmap is visible to players.
    Called by the CohortPulse.js toggle switch.
    """
    import database_memory as db_mem
    sess = db_mem._sessions.get(cohort_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")
    player_visible = bool(body.get("player_visible", False))
    sess["cohort_pulse_player_visible"] = player_visible
    db_mem._persist()
    return {"cohort_id": cohort_id, "player_visible": player_visible, "status": "saved"}


# ═════════════════════════════════════════════════════════════════
#  SIDE TRACK MANAGEMENT (God Mode → Facilitator → Cohort)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/side-tracks/catalog", summary="Get all registered side tracks")
async def get_side_track_catalog():
    """Returns the full catalog of registered side tracks with metadata.
    This is a read-only endpoint showing what tracks are available in the codebase."""
    from side_tracks import get_track_catalog
    catalog = get_track_catalog()
    available = _god_mode_settings.get("side_tracks_available", [])
    for entry in catalog:
        entry["enabled_globally"] = entry["track_id"] in available
    return {"catalog": catalog}


@admin_router.put("/side-tracks/global", summary="Enable/disable side tracks globally (God Mode)")
async def update_global_side_tracks(body: dict = Body(...)):
    """God Mode master control: set which side tracks are available platform-wide.
    Facilitators can only assign tracks from this enabled pool."""
    available = body.get("available_tracks", [])
    if not isinstance(available, list):
        raise HTTPException(400, "'available_tracks' must be a list of track IDs")

    # Validate track IDs exist in registry
    from side_tracks import get_all_tracks
    registered = set(get_all_tracks().keys())
    invalid = set(available) - registered
    if invalid:
        raise HTTPException(400, f"Unknown track IDs: {sorted(invalid)}. Registered: {sorted(registered)}")

    _god_mode_settings["side_tracks_available"] = available
    return {"status": "ok", "available_tracks": available}


@admin_router.get("/side-tracks/facilitator-permissions", summary="Get per-facilitator side track permissions")
async def get_facilitator_side_track_permissions():
    """Returns the mapping of facilitator IDs to their permitted side tracks."""
    perms = _god_mode_settings.get("side_tracks_facilitator_permissions", {})
    available = _god_mode_settings.get("side_tracks_available", [])
    return {"permissions": perms, "globally_available": available}


@admin_router.put("/side-tracks/facilitator-permissions/{fac_id}", summary="Set side track permissions for a facilitator")
async def set_facilitator_side_track_permissions(fac_id: str, body: dict = Body(...)):
    """God Mode: grant/revoke side track access for a specific facilitator.
    Tracks must be globally enabled first."""
    tracks = body.get("permitted_tracks", [])
    if not isinstance(tracks, list):
        raise HTTPException(400, "'permitted_tracks' must be a list of track IDs")

    available = set(_god_mode_settings.get("side_tracks_available", []))
    not_available = set(tracks) - available
    if not_available:
        raise HTTPException(400, f"Track(s) not globally enabled: {sorted(not_available)}. Enable them first via PUT /side-tracks/global")

    # Validate facilitator exists
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")

    perms = _god_mode_settings.setdefault("side_tracks_facilitator_permissions", {})
    perms[fac_id] = tracks
    _persist_facilitators()
    return {"status": "ok", "facilitator_id": fac_id, "permitted_tracks": tracks}


@admin_router.put("/cohorts/{session_id}/side-tracks", summary="Assign side tracks to a cohort (Facilitator)")
async def assign_cohort_side_tracks(session_id: str, body: dict = Body(...)):
    """Facilitator endpoint: assign side tracks to a specific cohort.
    Only tracks permitted by God Mode for this facilitator can be assigned.
    Includes timing configuration (unlock_after_round)."""
    from database_memory import _sessions, _persist

    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    tracks = body.get("tracks", [])
    timing = body.get("timing", {})
    if not isinstance(tracks, list):
        raise HTTPException(400, "'tracks' must be a list of track IDs")

    # Validate against facilitator permissions
    fac_id = sess.get("facilitator_id")
    if fac_id:
        perms = _god_mode_settings.get("side_tracks_facilitator_permissions", {})
        permitted = set(perms.get(fac_id, []))
        # If no explicit permissions set, fall back to globally available
        if not permitted:
            permitted = set(_god_mode_settings.get("side_tracks_available", []))
        unauthorized = set(tracks) - permitted
        if unauthorized:
            raise HTTPException(403, f"Facilitator {fac_id} not permitted to assign: {sorted(unauthorized)}")

    # Validate track IDs exist
    from side_tracks import get_all_tracks
    registered = set(get_all_tracks().keys())
    invalid = set(tracks) - registered
    if invalid:
        raise HTTPException(400, f"Unknown track IDs: {sorted(invalid)}")

    # Store on the session
    sess["active_side_tracks"] = tracks
    sess["side_track_timing"] = timing  # e.g. {"supply_chain": {"unlock_after_round": 3}}

    # Initialize side_track_states for new tracks
    existing_states = sess.get("side_track_states", {})
    for tid in tracks:
        if tid not in existing_states:
            existing_states[tid] = {
                "current_round": 0,  # 0 = not started
                "completed": False,
                "state": {},
                "bu_states": [],
                "round_history": [],
                "accumulated_flags": [],
            }
    sess["side_track_states"] = existing_states
    _persist()

    return {
        "status": "ok",
        "session_id": session_id,
        "active_side_tracks": tracks,
        "timing": timing,
    }


@admin_router.get("/cohorts/{session_id}/side-tracks", summary="Get side track status for a cohort")
async def get_cohort_side_tracks(session_id: str):
    """Returns the assigned side tracks, their progress, and timing for a cohort."""
    from database_memory import _sessions

    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    active = sess.get("active_side_tracks", [])
    timing = sess.get("side_track_timing", {})
    states = sess.get("side_track_states", {})

    # Enrich with track metadata
    from side_tracks import get_track
    track_status = []
    for tid in active:
        track = get_track(tid)
        st = states.get(tid, {})
        track_status.append({
            "track_id": tid,
            "display_name": track.display_name if track else tid,
            "icon": track.icon if track else "📦",
            "num_rounds": track.num_rounds if track else 0,
            "current_round": st.get("current_round", 0),
            "completed": st.get("completed", False),
            "timing": timing.get(tid, {}),
        })

    return {
        "session_id": session_id,
        "side_tracks": track_status,
    }


# ═════════════════════════════════════════════════════════════════
#  STRAT-002: FLAG DEPENDENCY VIEWER
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/flag-dependencies", summary="Get the cross-round flag dependency graph")
async def get_flag_dependencies(session_id: str | None = None):
    """STRAT-002: Returns the flag dependency graph with optional session overlay."""
    from terminal_valuation import get_flag_dependency_graph
    active_flags = None
    if session_id:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            active_flags = latest.get("global_state", {}).get("active_event_flags", {})
    return get_flag_dependency_graph(active_flags)


# ═════════════════════════════════════════════════════════════════
#  STRAT-003: WHAT-IF MODE
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/what-if/{session_id}", summary="What-If M_R replay with flag overrides")
async def what_if_replay(session_id: str, body: dict = Body(...)):
    """STRAT-003: Replay R10 terminal valuation with modified flags."""
    from terminal_valuation import what_if_terminal
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]
    bus = latest["bu_states"]
    flags = gs.get("active_event_flags", {})
    overrides = body.get("flag_overrides", {})
    paradigm = _get_session_paradigm(session_id)
    n = len(bus) or 1
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / n
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / n
    result = what_if_terminal(
        bus=bus, base_flags=flags, flag_overrides=overrides,
        avg_slo=avg_slo, avg_burnout=avg_burnout,
        workforce_readiness=flags.get("workforce_readiness_score", 50),
        synergy_multiplier=gs.get("synergy_multiplier", 1.0),
        hr_investment_rounds=flags.get("hr_roi_investment_rounds", 0),
        carbon_tax_per_ton=250.0, exit_multiple=12.0,
        green_fund_balance=gs.get("green_transition_fund", 0.0),
        is_advanced_climate=paradigm == "advanced_climate",
    )
    return {"session_id": session_id, **result}


# ═════════════════════════════════════════════════════════════════
#  STRAT-004: CROSS-PATHWAY NORMALIZED LEADERBOARD
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/leaderboard/normalized", summary="Cross-pathway normalized leaderboard")
async def normalized_leaderboard():
    """STRAT-004: Normalized M_R leaderboard for fair cross-pathway ranking."""
    from terminal_valuation import normalize_mr_for_leaderboard
    sessions = await db.fetch_all_sessions()
    entries = []
    for s in sessions:
        sid = s.get("session_id", "")
        latest = await db.fetch_latest_state(sid)
        if not latest:
            continue
        gs = latest.get("global_state", {})
        flags = gs.get("active_event_flags", {})
        raw_mr = flags.get("final_mr")
        if raw_mr is None:
            continue
        pathway = flags.get("ending_pathway", "activist_ultimatum")
        norm = normalize_mr_for_leaderboard(raw_mr, pathway)
        entries.append({"session_id": sid, "team_name": s.get("team_name", sid),
                        "paradigm": s.get("decision_paradigm", "legacy_abc"), **norm})
    entries.sort(key=lambda e: e.get("normalized_mr", 0), reverse=True)
    return {"leaderboard": entries, "count": len(entries)}


# ═════════════════════════════════════════════════════════════════
#  INDUSTRY VERTICAL BLUEPRINTS
#  GET  /api/admin/industry-verticals          → list all verticals
#  POST /api/admin/industry-verticals/{id}/apply/{session_id}
#       → inject vertical's materiality config into a live session
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/industry-verticals", summary="List all ESRS industry vertical blueprints")
async def list_industry_verticals():
    """Returns all registered industry vertical blueprints from materiality_db.
    Each entry includes: id, label, icon, issue_count, q1_count, q1_titles, regulatory_triggers.
    Used by the God Mode Materiality Config panel to allow facilitators to preview
    and apply industry-specific materiality paradigms to live sessions."""
    all_bu = mat_db.get_bu_registry()
    verticals = []
    for bu in all_bu:
        if not bu.get("is_industry_vertical"):
            continue
        cfg = mat_db.get_bu_config(bu["id"])
        issues = cfg.get("issues", [])
        q1_issues = [i for i in issues if i.get("financial_impact") == "high" and i.get("societal_impact") == "high"]
        verticals.append({
            "id": bu["id"],
            "label": bu["label"],
            "icon": bu.get("icon", "🏢"),
            "issue_count": len(issues),
            "q1_count": len(q1_issues),
            "q1_titles": [i["title"] for i in q1_issues[:5]],
            "regulatory_triggers": [
                i.get("esrs_reference", "") for i in issues
                if i.get("esrs_reference") and i.get("financial_impact") == "high"
            ][:4],
            "consultant_fee_usd": cfg.get("consultant_fee_usd", 1_500_000),
        })
    return {"verticals": verticals, "count": len(verticals)}


@admin_router.post(
    "/industry-verticals/{vertical_id}/apply/{session_id}",
    summary="Apply an industry vertical blueprint to a live session"
)
async def apply_industry_vertical(vertical_id: str, session_id: str):
    """Injects the selected industry vertical's materiality config into the session's
    global_state as 'materiality_dictionary_override'. This causes Round 2 to use
    the vertical's issues instead of the default global dictionary.

    Also stamps 'industry_vertical_applied' flag in active_event_flags so the
    teleprompter can surface industry-specific teaching notes.
    Propagates to all child player sessions."""
    # Validate vertical exists
    all_bu = mat_db.get_bu_registry()
    vertical = next((b for b in all_bu if b["id"] == vertical_id and b.get("is_industry_vertical")), None)
    if not vertical:
        raise HTTPException(404, f"Industry vertical '{vertical_id}' not found.")

    # Fetch the vertical's materiality config
    cfg = mat_db.get_bu_config(vertical_id)
    if not cfg or not cfg.get("issues"):
        raise HTTPException(422, f"Vertical '{vertical_id}' has no materiality issues configured.")

    # Fetch the session
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, f"Session '{session_id}' not found.")

    gs = latest["global_state"]
    gs["materiality_dictionary_override"] = cfg
    gs.setdefault("active_event_flags", {})["industry_vertical_applied"] = vertical_id
    gs["industry_vertical_label"] = vertical["label"]
    gs["industry_vertical_icon"] = vertical.get("icon", "🏢")

    await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    # Propagate to child player sessions
    children = await db.get_child_sessions(session_id)
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state:
            cgs = child_state["global_state"]
            cgs["materiality_dictionary_override"] = cfg
            cgs.setdefault("active_event_flags", {})["industry_vertical_applied"] = vertical_id
            cgs["industry_vertical_label"] = vertical["label"]
            cgs["industry_vertical_icon"] = vertical.get("icon", "🏢")
            await db.update_latest_global_state(child["session_id"], cgs, child_state["bu_states"])

    issues = cfg.get("issues", [])
    q1_issues = [i for i in issues if i.get("financial_impact") == "high" and i.get("societal_impact") == "high"]

    _audit("industry_vertical_applied", details={
        "session_id": session_id,
        "vertical_id": vertical_id,
        "label": vertical["label"],
        "issue_count": len(issues),
        "q1_count": len(q1_issues),
        "children_updated": len(children),
    })

    return {
        "status": "ok",
        "session_id": session_id,
        "vertical_id": vertical_id,
        "label": vertical["label"],
        "icon": vertical.get("icon", "🏢"),
        "issue_count": len(issues),
        "q1_count": len(q1_issues),
        "children_updated": len(children),
        "message": (
            f"✅ {vertical['label']} blueprint applied to session {session_id[:8]}. "
            f"Round 2 will now use {len(issues)} industry-specific issues "
            f"({len(q1_issues)} doubly-material Q1 issues)."
        ),
    }


# ═════════════════════════════════════════════════════════════════
#  MODULE 4 — CBAM/ETS REGULATORY SHOCK CRISIS CHOICES
#  POST /api/admin/sessions/{session_id}/mod4-crisis-choices
#  Called by RegulatoryShockModule.js after the student selects
#  a crisis-response strategy per BU at the effective carbon fee.
# ═════════════════════════════════════════════════════════════════

# Per-choice P&L impact model (applied per distressed BU)
_MOD4_CHOICE_IMPACTS = {
    "eat": {
        "label": "💸 Eat the Cost",
        "treasury_pct_revenue": -0.12,     # -12% of BU revenue hit
        "slo_delta": -5,                   # board penalty → SLO drop
        "governance_risk_delta": +4,
        "reputation_delta": -3,
        "flag": "cbam_cost_absorbed",
    },
    "pass": {
        "label": "📈 Pass to Consumers",
        "treasury_pct_revenue": -0.04,     # limited direct hit
        "slo_delta": -10,                  # -20% market share → SLO
        "governance_risk_delta": +2,
        "reputation_delta": -6,
        "flag": "cbam_passed_to_consumer",
    },
    "abate": {
        "label": "⚙️ Emergency Abatement",
        "treasury_pct_revenue": -0.08,     # capex ×1.3 premium
        "slo_delta": +3,                   # proactive → SLO boost
        "governance_risk_delta": -3,
        "reputation_delta": +4,
        "flag": "cbam_emergency_abatement",
    },
}

@admin_router.post(
    "/sessions/{session_id}/mod4-crisis-choices",
    summary="Submit CBAM/ETS crisis responses for Module 4 Regulatory Shock"
)
async def submit_mod4_crisis_choices(session_id: str, body: dict = Body(...)):
    """Processes per-BU CBAM/ETS crisis choices submitted by RegulatoryShockModule.js.

    Body:
        choices: dict[bu_id, 'eat' | 'pass' | 'abate']
        effective_fee: float   (carbon price at submission, e.g. 90)

    Stamps 'cbam_crisis_choices' into active_event_flags, applies treasury/SLO
    deltas to each matching BU state, and records 'mod4_completed' flag.
    Propagates to all child player sessions."""
    choices: dict = body.get("choices", {})
    effective_fee: float = float(body.get("effective_fee", 90))

    if not choices:
        raise HTTPException(400, "No BU choices provided.")

    # Validate choice values
    for bu_id, choice in choices.items():
        if choice not in _MOD4_CHOICE_IMPACTS:
            raise HTTPException(400, f"Invalid choice '{choice}' for BU '{bu_id}'. Must be eat | pass | abate.")

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, f"Session '{session_id}' not found.")

    gs = latest["global_state"]
    bu_states = latest["bu_states"]
    flags = gs.setdefault("active_event_flags", {})

    # --- Apply impacts per BU ---
    applied_impacts = {}
    total_treasury_delta = 0.0

    for bu in bu_states:
        bu_id = bu.get("bu_id", "")
        choice = choices.get(bu_id)
        if not choice:
            continue  # green BU — no action required

        impacts = _MOD4_CHOICE_IMPACTS[choice]
        revenue = bu.get("revenue", 10_000_000)
        treasury_delta = revenue * impacts["treasury_pct_revenue"]

        # Apply SLO, governance risk, reputation
        bu["social_license"] = max(0, min(100, (bu.get("social_license", 75) + impacts["slo_delta"])))
        bu["governance_risk"] = max(0, min(100, (bu.get("governance_risk", 20) + impacts["governance_risk_delta"])))
        bu["reputation"] = max(0, min(100, (bu.get("reputation", 70) + impacts["reputation_delta"])))

        # Per-BU flag
        bu.setdefault("event_flags", [])
        if impacts["flag"] not in bu["event_flags"]:
            bu["event_flags"].append(impacts["flag"])

        total_treasury_delta += treasury_delta
        applied_impacts[bu_id] = {
            "choice": choice,
            "label": impacts["label"],
            "treasury_delta": round(treasury_delta),
            "slo_delta": impacts["slo_delta"],
        }

    # Apply treasury impact
    gs["corporate_treasury"] = (gs.get("corporate_treasury", 25_000_000) + total_treasury_delta)

    # Stamp summary flags
    flags["cbam_crisis_choices"] = choices
    flags["cbam_effective_fee"] = effective_fee
    flags["mod4_completed"] = True
    flags["mod4_total_treasury_delta"] = round(total_treasury_delta)

    # Recalculate group reputation
    if bu_states:
        gs["group_reputation"] = round(
            sum(b.get("reputation", 70) for b in bu_states) / len(bu_states), 1
        )

    await db.update_latest_global_state(session_id, gs, bu_states)

    # Propagate to child player sessions
    children = await db.get_child_sessions(session_id)
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state:
            cgs = child_state["global_state"]
            cbu = child_state["bu_states"]
            cgs.setdefault("active_event_flags", {}).update({
                "cbam_crisis_choices": choices,
                "cbam_effective_fee": effective_fee,
                "mod4_completed": True,
            })
            # Apply same BU impacts to child
            for bu in cbu:
                bu_id = bu.get("bu_id", "")
                choice = choices.get(bu_id)
                if not choice:
                    continue
                impacts = _MOD4_CHOICE_IMPACTS[choice]
                revenue = bu.get("revenue", 10_000_000)
                bu["social_license"] = max(0, min(100, (bu.get("social_license", 75) + impacts["slo_delta"])))
                bu["governance_risk"] = max(0, min(100, (bu.get("governance_risk", 20) + impacts["governance_risk_delta"])))
                bu["reputation"] = max(0, min(100, (bu.get("reputation", 70) + impacts["reputation_delta"])))
            await db.update_latest_global_state(child["session_id"], cgs, cbu)

    _audit("mod4_crisis_submitted", details={
        "session_id": session_id,
        "effective_fee": effective_fee,
        "choices": choices,
        "total_treasury_delta": round(total_treasury_delta),
        "children_updated": len(children),
    })

    return {
        "status": "ok",
        "session_id": session_id,
        "effective_fee": effective_fee,
        "applied_impacts": applied_impacts,
        "total_treasury_delta": round(total_treasury_delta),
        "children_updated": len(children),
        "message": (
            f"✅ Module 4 CBAM crisis recorded at ${effective_fee}/t. "
            f"Net treasury impact: ${total_treasury_delta / 1_000_000:.2f}M across "
            f"{len(applied_impacts)} distressed BU(s)."
        ),
    }


# ═════════════════════════════════════════════════════════════════
#  SIDE TRACK BLUEPRINTS — God Mode Preview
#  GET /api/admin/side-tracks/blueprints
#  Returns all 4 side track round configs as a structured preview,
#  enabling facilitators to inspect options/impacts before assigning.
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/side-tracks/blueprints", summary="Full side track round configs for God Mode preview")
async def get_side_track_blueprints():
    """Returns all registered side track configs with full round details.
    Used by the God Mode Side Track panel to display option trees,
    flag dependencies, and impact previews before assigning to cohorts."""
    from side_tracks.supply_chain.configs import SUPPLY_CHAIN_ROUND_CONFIGS
    from side_tracks.stakeholder_management.configs import STAKEHOLDER_ROUND_CONFIGS
    from side_tracks.sustainability_reporting.configs import REPORTING_ROUND_CONFIGS
    try:
        from side_tracks.ethics_sustainability.configs import ETHICS_ROUND_CONFIGS
    except ImportError:
        ETHICS_ROUND_CONFIGS = {}

    def _summarise_track(track_id: str, display_name: str, icon: str, configs: dict) -> dict:
        rounds = []
        for rn, cfg in configs.items():
            options_summary = []
            for opt_key, opt in cfg.get("options", {}).items():
                impacts = opt.get("impacts", {})
                options_summary.append({
                    "key": opt_key,
                    "title": opt.get("title", ""),
                    "flags_set": opt.get("flags_set", []),
                    "treasury": impacts.get("treasury", 0),
                    "reputation": impacts.get("reputation", 0),
                    "slo_delta": impacts.get("social_license_delta", 0),
                    "gov_risk_delta": impacts.get("governance_risk_delta", 0),
                })
            rounds.append({
                "round": rn,
                "title": cfg.get("title", ""),
                "theme": cfg.get("theme", cfg.get("crisis_title", "")),
                "crisis_title": cfg.get("crisis", {}).get("title", cfg.get("crisis_title", "")),
                "icon": cfg.get("crisis", {}).get("icon", "📋"),
                "special_rules": list(cfg.get("special_rules", {}).keys()),
                "options": options_summary,
            })
        return {
            "track_id": track_id,
            "display_name": display_name,
            "icon": icon,
            "num_rounds": len(configs),
            "rounds": rounds,
        }

    blueprints = [
        _summarise_track("supply_chain",           "Supply Chain",             "🔗", SUPPLY_CHAIN_ROUND_CONFIGS),
        _summarise_track("stakeholder_management", "Stakeholder Management",   "🤝", STAKEHOLDER_ROUND_CONFIGS),
        _summarise_track("sustainability_reporting","Sustainability Reporting", "📋", REPORTING_ROUND_CONFIGS),
    ]
    if ETHICS_ROUND_CONFIGS:
        blueprints.append(
            _summarise_track("ethics_sustainability", "Ethics & Sustainability", "⚖️", ETHICS_ROUND_CONFIGS)
        )

    return {
        "blueprints": blueprints,
        "track_count": len(blueprints),
        "globally_enabled": _god_mode_settings.get("side_tracks_available", []),
    }
