"""
Muressons Global Corporation — Admin Router (God Mode)
Facilitator-only endpoints for real-time cohort monitoring,
manual state overrides, and message injection.
"""

from __future__ import annotations

import itertools
import json
import asyncio
import hmac
import time
import collections
import importlib
import threading
import copy
import uuid
from typing import Any, Optional
from datetime import datetime, timezone
import random

import os
import shutil
from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status, Body, UploadFile, File
from pydantic import BaseModel, Field, validator
from fastapi import Header, Depends

# ── audit #17: rate limiter extracted to rate_limit.py (behaviour unchanged) ──
# Re-exported so `from admin_router import _check_rate_limit` (router.py) and the
# six in-module _check_rate_limit(...) call sites keep working unchanged.
from rate_limit import (  # noqa: F401  (re-exported for backwards compatibility)
    _RATE_LIMIT_MAX,
    _RATE_LIMIT_WINDOW,
    _ADMIN_ACTION_RATE_MAX,
    _ADMIN_ACTION_PREFIXES,
    _rate_buckets,
    _persistent_bans,
    _load_persistent_bans,
    _save_persistent_bans,
    _TRUSTED_PROXY_IPS,
    _resolve_client_ip,
    _check_rate_limit,
)


# ── Concurrency locks and counters ──────────────────────────────────────────
# GOD-003: Serialises facilitator ID generation so two simultaneous creation
# requests cannot both compute the same next ID and produce duplicate FAC-NNN.
_fac_registry_lock: asyncio.Lock = asyncio.Lock()

# GOD-006: Serialises read-modify-write on decision_overrides.json so two
# super_admins editing different rounds simultaneously cannot corrupt the file.
_config_file_lock: asyncio.Lock = asyncio.Lock()

# GOD-005: Monotonically-increasing audit ID that is safe under concurrent
# coroutines. itertools.count is GIL-atomic in CPython and cooperative-safe
# in asyncio (no yield between next() and the append).
_audit_counter: itertools.count = itertools.count(1)


def get_fac_role(request: Request):
    from auth_jwt import get_facilitator_from_request, decode_facilitator_token, COOKIE_NAME
    fac_id = get_facilitator_from_request(request)
    if not fac_id:
        return 'anonymous'

    # SECURITY-CRIT-002: Only Path 1 (signed JWT cookie) is trusted for
    # privilege resolution. The former "Path 2" that granted super_admin to
    # any request carrying the header value "god_mode" has been removed —
    # it trusted unauthenticated client-controlled input.
    #
    # Path 1: JWT cookie carries a cryptographically signed role claim.
    # god_mode is a virtual account (not in the registry) whose role is ONLY
    # granted here, after the signed token is validated.
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        try:
            payload = decode_facilitator_token(cookie_token)
            token_sub = payload.get("sub")
            token_role = payload.get("role")
            # SEC-1: reject tokens whose version is stale (revoked). Applies to
            # every account, god_mode included — this is the kill-switch.
            if token_sub and int(payload.get("ver", 0)) != get_token_version(token_sub):
                return 'anonymous'
            # god_mode: virtual account resolved entirely from the signed token.
            # C6: god_mode is now its own distinct top tier (level 4), not an
            # alias of super_admin. We no longer constrain token_role here (older
            # cookies carry role="super_admin", newer ones "god_mode") — a
            # signature-verified token whose sub AND fac_id are both "god_mode"
            # is sufficient to grant the god_mode role.
            if token_sub == "god_mode" and fac_id == "god_mode":
                return "god_mode"
            # project_admin: virtual account (not in the registry) — like
            # god_mode, its role is granted ONLY from the signed token claim.
            if token_sub == "project_admin" and token_role == "project_admin" and fac_id == "project_admin":
                return "project_admin"
            if token_sub == fac_id:
                # H-4: Re-validate against registry so demotions and disablements
                # take effect immediately, not just after JWT expiry.
                fac = next(
                    (f for f in _facilitator_registry
                     if f['facilitator_id'] == fac_id and not f.get('deleted_at')),
                    None,
                )
                if fac is None:
                    return 'anonymous'
                if not fac.get('enabled', True):
                    return 'anonymous'
                return get_role(fac)  # registry is authoritative, not JWT claim
        except Exception:
            pass

    # Registry fallback — reached only when JWT library is unavailable.
    fac = next(
        (f for f in _facilitator_registry
         if f['facilitator_id'] == fac_id and not f.get('deleted_at')),
        None,
    )
    return get_role(fac) if fac else 'anonymous'

async def _assert_session_ownership(request: Request, session_id: str) -> None:
    """H-3: Raise 403 if the authenticated facilitator does not own the target session.
    Super admins and god_mode bypass this check automatically."""
    from auth_jwt import get_facilitator_from_request
    fac_id = get_facilitator_from_request(request)
    if not fac_id or fac_id == "god_mode":
        return  # god_mode / unresolvable → already guarded by require_facilitator
    fac = next(
        (f for f in _facilitator_registry
         if f['facilitator_id'] == fac_id and not f.get('deleted_at')),
        None,
    )
    if fac is None or is_admin_role(get_role(fac)):
        return  # super_admin / god_mode can touch any session
    session_info = await db.get_session_info(session_id)
    if session_info and not owns_session(fac, session_info):
        raise HTTPException(
            status_code=403,
            detail="Access denied: you do not own this session",
        )


def require_super_admin(role: str = Depends(get_fac_role)):
    """Allow super_admin only. Uses hierarchy level to handle 'admin' alias correctly."""
    if role == 'anonymous':
        # BUG-2026-07-18: distinguish "not authenticated" (401) from
        # "authenticated but insufficient role" (403), so a dead/absent cookie
        # reads as Session expired rather than a misleading role refusal.
        raise HTTPException(status_code=401, detail='Facilitator authentication required')
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY.get('super_admin', 3):
        raise HTTPException(status_code=403, detail='Super Admin required')

def require_lead_facilitator(role: str = Depends(get_fac_role)):
    """Allow lead_facilitator and super_admin. Blocks base facilitator and anonymous."""
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY.get('lead_facilitator', 2):
        raise HTTPException(status_code=403, detail='Lead Facilitator or higher required')

def require_facilitator(role: str = Depends(get_fac_role)):
    """Allow any authenticated facilitator (any role). Blocks anonymous requests."""
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Facilitator authentication required')


def require_registry_admin(role: str = Depends(get_fac_role)):
    """Super admins (incl. god_mode) and the project_admin registry role —
    facilitator provisioning endpoints (create / bulk / Excel upload).
    C6: uses is_admin_role so the distinct god_mode tier is admitted, not just
    the literal 'super_admin' string."""
    if not (is_admin_role(role) or role == "project_admin"):
        raise HTTPException(status_code=403, detail='Registry-admin access required')


def require_sim_manager(role: str = Depends(get_fac_role)):
    """Any authenticated facilitator (base / lead / super / god_mode) EXCEPT
    project_admin.

    C3: this is the authoritative guard for the *live-run-management* surface —
    round pacing/unlock, player registration & credentials, live interventions
    (inject message, shockwave, broadcast, finale/situation-room consoles),
    grading, notes and annotations. project_admin's charter is 'provisions
    facilitators + cohorts, NEVER manages runs' (admin_shared.py:ROLE_HIERARCHY
    note), so every run-operation endpoint must gate on THIS dependency, not the
    permissive require_facilitator (which admits project_admin). Cohort
    provisioning/config endpoints (bu-composition, side-tracks, cohort pacing
    defaults, pedagogical settings, ending-pathway, CEO-interview) deliberately
    stay on require_facilitator because project_admin performs them while
    provisioning a cohort."""
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Facilitator authentication required')
    if role == 'project_admin':
        raise HTTPException(status_code=403, detail='Project admins provision cohorts but cannot manage simulation runs.')


def _generate_temp_password() -> tuple[str, str]:
    """Return a RANDOM per-user temporary password (QA-2026-07-16 #11).

    Previously returned a fixed 'Muressons123' shared by every new player AND
    facilitator — a predictable initial credential exploitable in the window
    before first login. Now every call yields a fresh 12-char random password;
    must_change_password=True is still set alongside, so it is only valid until
    the user sets their own. The plaintext is returned so the facilitator can
    distribute it once (surfaced per-user in the registry / creation response);
    only the bcrypt hash is stored.

    Returns (plaintext, hashed).
    """
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    plaintext = "".join(secrets.choice(alphabet) for _ in range(12))
    hashed = hash_password(plaintext)
    return plaintext, hashed


import database as db
import materiality_db as mat_db
from config import MASTER_PASSWORD, PROJECT_ADMIN_PASSWORD, SIM_ROUNDS, SIM_INITIAL_BUDGET
from master_credentials import verify_master_password, set_master_password, master_override_active
from password_hashing import hash_password, verify_password, maybe_upgrade_password
from models import MaterialityIssue, InterdependenceLink, MaterialityConfig

# ARCH-002: Import all shared state from admin_shared.py
# Re-export for backward compatibility — external modules that do
# `from admin_router import _god_mode_settings` continue to work.
from admin_shared import (
    _god_mode_settings,
    # GOD-012: Per-cohort settings layer
    cohort_settings, COHORT_OVERRIDABLE_KEYS, get_effective_settings,
    normalize_advanced_cohort_settings,
    _cohort_templates,
    get_virtual_profile,
    mark_cohort_settings_dirty,
    resolve_climate_paradigm, seed_effective_flags,
    project_effective, visible_keys_for_role, bu_scope_source,
    _facilitator_registry, _persist_facilitators, _load_facilitator_registry,
    _FAC_REGISTRY_PATH, _DEFAULT_FACILITATOR,
    _player_registry,
    _session_messages, _session_interventions,
    _god_mode_audit_log, _crisis_trigger_history, _capped_append,
    _practice_mode, is_practice_mode,
    _round_pacing, _get_pacing, is_round_unlocked, is_pacing_set_by_facilitator,
    # Fix #5: publish live-run coordination state (pacing/freeze) so it survives
    # restarts and is shared across workers.
    mark_pacing_dirty, mark_godmode_dirty,
    check_and_increment_cohort_count,
    _get_session_paradigm,
    DEFAULT_ARCHETYPES,
    DEFAULT_ESG_WEIGHTS,
    # 3-tier role model
    ROLE_HIERARCHY, ROLE_ALLOWED_TABS,
    get_role, has_role_level, get_allowed_tabs, can_access_tab, owns_session,
    # C6/C1: god_mode-aware admin check + role-assignment allow-lists
    is_admin_role, _ASSIGNABLE_ROLES, assignable_roles_for,
    # SEC-1: token-version revocation kill-switch
    get_token_version, bump_token_version,
    # Shared marketplace (used by cascade delete cleanup)
    _cohort_marketplaces,
)

admin_router = APIRouter(prefix="/api/admin", tags=["Admin \u2014 God Mode"])

# Module logger. `logging` was only ever imported LOCALLY inside a few
# functions here, so any module-level reference to a logger (`_ar_log`) raised
# NameError \u2014 which the global handler turned into an opaque
# "An internal server error occurred". Declaring it once at module scope means
# the whole file can log without a per-call `import logging`.
import logging
import logging as _ar_logging
_ar_log = _ar_logging.getLogger("muressons.admin")


# _get_session_paradigm imported from admin_shared

# God mode settings, facilitator registry, and archetypes now imported from admin_shared.
# The _next_facilitator_id is kept local since it's only used in this file.
_next_facilitator_id: int = 1


class FacilitatorCreateRequest(BaseModel):
    name: str = Field(..., max_length=200)
    email: str | None = Field(None, max_length=200)
    contact_number: str | None = Field(None, max_length=50)
    programme: str | None = Field(None, max_length=200)
    start_date: str | None = None
    end_date: str | None = None
    max_cohorts: int = 5
    decision_paradigm: str = "legacy_abc"
    ending_pathway: str | None = "activist_ultimatum"
    side_tracks: list[str] | None = None
    simulation_mode: str | None = "conglomerate"
    industry_vertical: str | None = ""
    bu_substitutions: dict | None = None
    permissions: dict | None = None
    created_by: str | None = Field(None, max_length=100)
    date_created: str | None = None
    role: str = "facilitator"
    shockwave_enabled: bool = True   # Feature 6: allow this facilitator to detonate synchronized shockwaves
    trading_floor_enabled: bool = True   # Feature 1: allow this facilitator to run the Trading-Floor finale console
    situation_room_enabled: bool = True   # W-D (W4): allow this facilitator to fire Situation-Room voice bulletins
    negotiation_rooms_enabled: bool = False   # Slice 5: opt-in Stakeholder Negotiation Rooms (default OFF)

class FacilitatorUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    contact_number: str | None = None
    programme: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    max_cohorts: int | None = None
    decision_paradigm: str | None = None
    ending_pathway: str | None = None
    side_tracks: list[str] | None = None
    role: str | None = None
    simulation_mode: str | None = None
    industry_vertical: str | None = None
    bu_substitutions: dict | None = None
    permissions: dict | None = None
    created_by: str | None = None
    date_created: str | None = None
    role: str | None = None
    is_admin: bool | None = None
    shockwave_enabled: bool | None = None   # Feature 6 per-facilitator capability
    trading_floor_enabled: bool | None = None   # Feature 1 per-facilitator capability
    situation_room_enabled: bool | None = None   # W-D (W4) per-facilitator capability
    negotiation_rooms_enabled: bool | None = None   # Slice 5 per-facilitator capability (revoke path)

class FacilitatorBulkCreateRequest(BaseModel):
    facilitators: list[FacilitatorCreateRequest]


class FacilitatorBulkDeleteRequest(BaseModel):
    # Batch counterpart of DELETE /facilitators/{fac_id}. Bounds are enforced
    # manually in the handler (empty / oversize → 400) rather than via Field
    # constraints so validation failures surface as 400, not Pydantic's 422.
    facilitator_ids: list[str]
    hard: bool = False


# ── Global Settings (Sim Switchboard ↔ player sessions) ─────────
from fastapi import Query as _Query

@admin_router.get("/global-settings", summary="Get current global simulation settings")
async def get_global_settings(session_id: str | None = _Query(default=None)):
    """Returns current god-mode settings including simulation_mode.
    Called by player sessions on mount to detect Advanced Climate Engine.

    GOD-012: When a session_id query param is supplied the response merges
    global defaults with any per-cohort overrides stored for that session.
    This lets 30 concurrent workshops each receive their own freeze state,
    simulation_mode, carbon_fee, etc. without affecting each other.
    """
    # GOD-012: resolve effective settings for this cohort (or global if no overrides)
    s = get_effective_settings(session_id)
    return {
        "simulation_mode": s.get("simulation_mode", "standard"),
        # C6: canonical climate branch, normalised so clients never read the
        # ambiguous simulation_mode for the Timeline-Branch toggle.
        "climate_paradigm": resolve_climate_paradigm(s),
        "front_page_enabled": s.get("front_page_enabled", True),  # Feature 5 toggle (player-readable)
        # Briefing videos (Read | Watch on round briefings) — player-readable;
        # cohort-effective via GOD-012. URLs only; empty/{} = text-only briefings.
        "briefing_video_base": s.get("briefing_video_base", ""),
        "briefing_videos": s.get("briefing_videos", {}) or {},
        "consequence_replay_enabled": s.get("consequence_replay_enabled", True),  # WOW-1: post-commit causal chain animation
        "global_carbon_fee": s.get("global_carbon_fee", 40),
        "market_hostility_index": s.get("market_hostility_index", 5),
        "scope_3_threshold": s.get("scope_3_threshold", 2.5),
        "allow_facilitator_cohort_creation": s.get("allow_facilitator_cohort_creation", True),
        "system_frozen": s.get("system_frozen", False),
        "corporate_treasury_start": s.get("corporate_treasury_start", SIM_INITIAL_BUDGET),
        "group_reputation_start": s.get("group_reputation_start", 50.0),
        "synergy_multiplier_start": s.get("synergy_multiplier_start", 1.0),
        "cost_of_capital_start": s.get("cost_of_capital_start", 0.05),
        "loan_interest_rate_start": s.get("loan_interest_rate_start", 0.12),
        "imitation_decay_rate_start": s.get("imitation_decay_rate_start", 0.05),
        "green_transition_fund_start": s.get("green_transition_fund_start", 0.0),
        "industry": s.get("industry", "generic"),
        # Economic complexity engine tunables
        "overrun_probability": s.get("overrun_probability", 0.25),
        "overrun_severity": s.get("overrun_severity", 0.15),
        # Display currency
        "currency_symbol": s.get("currency_symbol", "$"),
        # Ending pathways
        "default_ending_pathway": s.get("default_ending_pathway", "activist_ultimatum"),
        "ending_pathways_available": s.get("ending_pathways_available", ["activist_ultimatum"]),
        "allow_pathway_switching": s.get("allow_pathway_switching", False),
        "foreshadowing_enabled": s.get("foreshadowing_enabled", True),
        # CEO Interview
        "ceo_interview_enabled": s.get("ceo_interview_enabled", False),
        "ceo_interview_voice_gender": s.get("ceo_interview_voice_gender", "female"),
        "ceo_interview_question_count": s.get("ceo_interview_question_count", 5),
        "ceo_interview_pathway_question": s.get("ceo_interview_pathway_question", True),
        # Pedagogical Scaffolding
        # NOTE: difficulty_tier is per-cohort (set via Experience Level at creation), not global.
        # Kept in response for backward compatibility but God Mode no longer owns this value.
        "prediction_gates_enabled": s.get("prediction_gates_enabled", False),
        "board_room_moments_enabled": s.get("board_room_moments_enabled", True),
        # Results-view Decision Consequence Map (ConsequenceTimeline). Player-readable;
        # fail-open (default ON) so existing cohorts keep the map unless turned off.
        "consequence_map_enabled": s.get("consequence_map_enabled", True),
        # ESG Leadership Profile signal weights (facilitator-tunable rubric).
        "esg_profile_weights": s.get("esg_profile_weights", DEFAULT_ESG_WEIGHTS),
        "mental_model_tracker_enabled": s.get("mental_model_tracker_enabled", True),
        "confidence_calibration_enabled": s.get("confidence_calibration_enabled", False),
        "mid_game_checkpoint_enabled": s.get("mid_game_checkpoint_enabled", True),
        "peer_comparison_enabled": s.get("peer_comparison_enabled", True),
        "strategy_memo_enabled": s.get("strategy_memo_enabled", False),
        "what_if_builder_enabled": s.get("what_if_builder_enabled", False),
        "custom_crisis_enabled": s.get("custom_crisis_enabled", False),
        "round_recap_enabled": s.get("round_recap_enabled", False),
        "real_world_cards_enabled": s.get("real_world_cards_enabled", False),
        "real_world_cards_teleprompter": s.get("real_world_cards_teleprompter", True),
        # Player briefing academic framing (theory card + narrative citations). Default OFF for
        # players; facilitators may re-enable per deployment. Pedagogy is always kept in the
        # facilitator teleprompter regardless of this flag.
        "briefing_theory_enabled": s.get("briefing_theory_enabled", False),
        "debrief_protocol_enabled": s.get("debrief_protocol_enabled", False),
        "self_learning_mode": s.get("self_learning_mode", False),
        "flag_diagram_enabled": s.get("flag_diagram_enabled", True),
        "stochastic_labels_enabled": s.get("stochastic_labels_enabled", True),
        "engine_summariser_enabled": s.get("engine_summariser_enabled", True),
        # New Engine Toggles (Batch 1-3)
        "decision_timer_enabled": s.get("decision_timer_enabled", False),
        "decision_timer_seconds": s.get("decision_timer_seconds", 300),
        "peer_learning_prompts_enabled": s.get("peer_learning_prompts_enabled", True),
        "board_governance_enabled": s.get("board_governance_enabled", True),
        "supply_chain_network_enabled": s.get("supply_chain_network_enabled", True),
        "biodiversity_engine_enabled": s.get("biodiversity_engine_enabled", True),
        "market_dynamics_enabled": s.get("market_dynamics_enabled", False),
        "balance_sheet_enabled": s.get("balance_sheet_enabled", True),
        "regulatory_sandbox_enabled": s.get("regulatory_sandbox_enabled", False),
        "dynamic_cases_enabled": s.get("dynamic_cases_enabled", True),
        "branching_enabled": s.get("branching_enabled", True),
        "npc_stakeholders_enabled": s.get("npc_stakeholders_enabled", True),
        "tcfd_scenarios_enabled": s.get("tcfd_scenarios_enabled", True),
        "org_politics_enabled": s.get("org_politics_enabled", True),
        "meadows_leverage_enabled": s.get("meadows_leverage_enabled", True),
        "system_archetypes_enabled": s.get("system_archetypes_enabled", True),
        # BRSR NGRBC Track
        "brsr_ngrbc_enabled": s.get("brsr_ngrbc_enabled", False),
        # Scholarly ESG Capitalisation toggle
        "esg_bs_scholarly_mode": s.get("esg_bs_scholarly_mode", False),
        # Single-BU mode: when set, all player sessions only show this one BU
        "assigned_bu": s.get("assigned_bu", ""),
        # Slice 5: Stakeholder Negotiation Rooms — cohort-effective, capability-gated
        # (default OFF; a lead only turns it on if their profile holds the grant).
        "negotiation_rooms_enabled": s.get("negotiation_rooms_enabled", False) is True,
        # GOD-012: expose whether cohort-level overrides are active
        "_cohort_overrides_active": bool(session_id and session_id in cohort_settings),
    }

class GlobalSettingsPatch(BaseModel):
    # C6: canonical climate-branch key. `simulation_mode` is still accepted for
    # backward compatibility (legacy Switchboard payloads); patch_global_settings
    # dual-writes the two so old and new readers stay consistent.
    climate_paradigm: str | None = None
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
    consequence_map_enabled: bool | None = None  # results-view Decision Consequence Map
    mental_model_tracker_enabled: bool | None = None
    confidence_calibration_enabled: bool | None = None
    mid_game_checkpoint_enabled: bool | None = None
    peer_comparison_enabled: bool | None = None
    strategy_memo_enabled: bool | None = None
    what_if_builder_enabled: bool | None = None
    briefing_theory_enabled: bool | None = None  # player briefing academic framing (default off)
    custom_crisis_enabled: bool | None = None
    round_recap_enabled: bool | None = None
    real_world_cards_enabled: bool | None = None
    real_world_cards_teleprompter: bool | None = None
    front_page_enabled: bool | None = None  # Feature 5: Year-5 front page reveal
    consequence_replay_enabled: bool | None = None  # WOW-1: post-commit causal chain animation
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
    # BRSR NGRBC Track
    brsr_ngrbc_enabled: bool | None = None
    # Scholarly ESG Capitalisation (IAS 38 what-if toggle)
    esg_bs_scholarly_mode: bool | None = None
    # Systemic Risk Engine
    systemic_risk_enabled: bool | None = None
    black_swan_events_enabled: bool | None = None
    npc_cascading_enabled: bool | None = None
    foreshadowing_signals_enabled: bool | None = None
    # Single-BU mode override (empty string = all BUs)
    assigned_bu: str | None = None
    # I5 (Workstream E): free-text justification. REQUIRED when the caller is the
    # god_mode break-glass identity; ignored (optional) for named super_admins.
    reason: str | None = None


def _require_god_mode_reason(request: Request, reason: str | None) -> str:
    """I5: high-impact config writes performed under the god_mode break-glass
    identity must carry a reason, so the audit trail records WHY the platform
    default was changed (god_mode is virtual and not a named human). Returns the
    resolved caller role. No-op for non-god_mode callers."""
    role = get_fac_role(request)
    if role == "god_mode" and not (reason and str(reason).strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="god_mode configuration changes require a non-empty 'reason' for the audit trail.",
        )
    return role


@admin_router.patch("/global-settings", summary="Update global simulation settings (Sim Switchboard)")
async def patch_global_settings(body: GlobalSettingsPatch, request: Request, _guard: None = Depends(require_super_admin)):
    """Sim Switchboard endpoint — updates the climate branch and parameters."""
    # I5: god_mode writes require a reason for the audit trail.
    _caller_role = _require_god_mode_reason(request, body.reason)
    # FIX AUDIT-017: Use Pydantic to validate input types
    update_data = body.model_dump(exclude_unset=True)
    # `reason` is audit metadata, not a persisted setting — strip before write.
    _reason = update_data.pop("reason", None)
    # C6: dual-write the climate branch. Legacy clients send simulation_mode
    # in {standard, advanced_climate}; new clients send climate_paradigm. Keep
    # both in sync so every reader (old and new) resolves the same branch.
    from admin_shared import _CLIMATE_PARADIGM_VALUES
    _cp = update_data.get("climate_paradigm")
    _sm = update_data.get("simulation_mode")
    if _cp in _CLIMATE_PARADIGM_VALUES:
        update_data["simulation_mode"] = _cp
    elif _sm in _CLIMATE_PARADIGM_VALUES:
        update_data["climate_paradigm"] = _sm
    for key, value in update_data.items():
        _god_mode_settings[key] = value
    mark_godmode_dirty()  # Fix #5: publish settings change to workers + snapshot

    import logging
    logging.info(f"[god-mode] Global settings updated: {_god_mode_settings}")
    
    # Event Bus: Broadcast settings change to all connected admin dashboards
    # I5: record the caller role and (god_mode) reason on the audit entry.
    _audit("global_settings_updated", details={**update_data, "_caller_role": _caller_role, "_reason": _reason})
    await manager.broadcast_admin({
        "type": "settings_changed",
        "changed_keys": list(update_data.keys()),
        "settings": {k: _god_mode_settings.get(k) for k in update_data},
    })
    return {"status": "ok", "settings": _god_mode_settings}


# ── Apply-to-existing fan-out (Workstream D / C1 / C4) ───────────────────────
# Pushing a global default out to already-running cohorts is DELIBERATELY an
# explicit, audited action — never a silent side effect of PATCH /global-settings
# (existing cohorts keep their provisioned values by default; precedence is
# cohort_override > cohort_record > global_default). This writes the chosen
# global values into each target cohort's override layer via the same store the
# GOD-012 cohort-settings endpoints use.
class ApplyToExistingRequest(BaseModel):
    session_ids: list[str]
    keys: list[str]  # which global keys to fan out (must be cohort-overridable)


@admin_router.post(
    "/global-settings/apply-to-existing",
    summary="Fan a global setting out to selected existing cohorts (Workstream D)",
)
async def apply_global_to_existing(
    body: ApplyToExistingRequest,
    _guard: None = Depends(require_super_admin),
):
    if not body.session_ids:
        raise HTTPException(400, "session_ids must be a non-empty list")
    invalid_keys = [k for k in body.keys if k not in COHORT_OVERRIDABLE_KEYS]
    if invalid_keys:
        raise HTTPException(
            400,
            f"Keys not cohort-overridable: {sorted(invalid_keys)}. "
            f"Only {sorted(COHORT_OVERRIDABLE_KEYS)} may be fanned out.",
        )
    values = {k: _god_mode_settings.get(k) for k in body.keys if k in _god_mode_settings}
    applied: dict[str, dict] = {}
    for sid in body.session_ids:
        cohort_settings.setdefault(sid, {})
        cohort_settings[sid].update(values)
        applied[sid] = dict(values)
        _audit("global_applied_to_cohort", details={"session_id": sid, "keys": list(values.keys())})
        await manager.push_to_session(sid, {
            "type": "cohort_settings_changed",
            "session_id": sid,
            "changed_keys": list(values.keys()),
            "settings": cohort_settings[sid],
        })
    return {"status": "ok", "applied_values": values, "cohorts": applied}


# ── I3 (Workstream B): Unified role-scoped effective-settings read ───────────
@admin_router.get(
    "/effective-settings",
    summary="Role-scoped effective settings with provenance (unified read)",
)
async def get_effective_settings_projection(
    request: Request,
    session_id: str | None = _Query(default=None),
    caller_role: str = Depends(get_fac_role),
):
    """Return the effective settings for a cohort, filtered to the keys the
    caller's role may see, each annotated with provenance (global vs override).
    Deny-by-default: non-admins receive only their allow-listed keys. Non-admins
    requesting a specific cohort must own it."""
    if caller_role == "anonymous":
        raise HTTPException(401, "Facilitator authentication required")
    # Ownership scope for non-admins requesting a specific cohort.
    if session_id and not is_admin_role(caller_role):
        from auth_jwt import get_facilitator_from_request
        caller_id = get_facilitator_from_request(request)
        caller_fac = next((f for f in _facilitator_registry if f.get("facilitator_id") == caller_id), None)
        session_rec = None
        try:
            session_rec = next((s for s in (await db.fetch_all_sessions() or []) if s.get("session_id") == session_id), None)
        except Exception:
            session_rec = None
        if session_rec and caller_fac and not owns_session(caller_fac, session_rec):
            raise HTTPException(403, "You can only read effective settings for sessions you own.")
    return project_effective(session_id, caller_role)


@admin_router.get(
    "/effective-settings/summary",
    summary="Per-cohort effective climate settings across owned cohorts (Workstream B)",
)
async def get_effective_settings_summary(
    request: Request,
    caller_role: str = Depends(get_fac_role),
):
    """Batch view powering the Switchboard 'which cohorts diverge from global'
    panel: one row per cohort the caller may see, with its effective climate
    values, whether it overrides the global, and its BU-scope source."""
    if caller_role == "anonymous":
        raise HTTPException(401, "Facilitator authentication required")
    is_admin = is_admin_role(caller_role)
    caller_fac = None
    if not is_admin:
        from auth_jwt import get_facilitator_from_request
        caller_id = get_facilitator_from_request(request)
        caller_fac = next((f for f in _facilitator_registry if f.get("facilitator_id") == caller_id), None)
    try:
        sessions = await db.fetch_all_sessions() or []
    except Exception:
        sessions = []
    rows = []
    _climate = ("climate_paradigm", "global_carbon_fee", "market_hostility_index", "scope_3_threshold")
    for s in sessions:
        sid = s.get("session_id")
        if not sid:
            continue
        if not is_admin and (not caller_fac or not owns_session(caller_fac, s)):
            continue
        eff = get_effective_settings(sid)
        override = cohort_settings.get(sid, {})
        rows.append({
            "session_id": sid,
            "cohort_name": s.get("cohort_name", ""),
            "climate": {k: eff.get(k) for k in _climate},
            "overrides_active": bool(override),
            "overridden_keys": [k for k in _climate if k in override],
            "bu_scope_source": bu_scope_source(sid),
        })
    return {"cohorts": rows, "global": {k: _god_mode_settings.get(k) for k in _climate}}


# ── Per-Cohort Settings (GOD-012) ────────────────────────────────────────────
# Three endpoints that manage cohort_settings[session_id] — the override layer
# sitting above the global _god_mode_settings dict.
#
#   GET  /sessions/{session_id}/cohort-settings
#       → Returns the cohort overrides (only the keys set, not the merged view).
#         Any facilitator may call this to inspect a cohort's custom settings.
#
#   PATCH /sessions/{session_id}/cohort-settings
#       → Merges the supplied body into cohort_settings[session_id].
#         Only super_admin may set cohort overrides; lead_facilitator may set
#         a subset (freeze-related keys) for their own sessions.
#
#   DELETE /sessions/{session_id}/cohort-settings
#       → Clears all cohort overrides — the cohort reverts to global defaults.
#         super_admin only.

@admin_router.get(
    "/sessions/{session_id}/cohort-settings",
    summary="Get per-cohort settings overrides (GOD-012)",
)
async def get_cohort_settings(session_id: str, _guard: None = Depends(require_facilitator)):
    """Return the per-cohort override layer for a specific session.

    Returns only the keys that have been *explicitly overridden* for this cohort,
    not the full merged view.  Use GET /global-settings?session_id=... to get
    the effective merged settings as seen by a player session.
    """
    overrides = cohort_settings.get(session_id, {})
    return {
        "session_id": session_id,
        "overrides": overrides,
        "has_overrides": bool(overrides),
        "effective": get_effective_settings(session_id),
    }


@admin_router.patch(
    "/sessions/{session_id}/cohort-settings",
    summary="Set per-cohort settings overrides (GOD-012)",
)
async def patch_cohort_settings(
    session_id: str,
    body: dict = Body(...),
    request: Request = None,
    _guard: None = Depends(require_lead_facilitator),
):
    """Merge the supplied dict into the cohort override layer for session_id.

    GOD-012: Per-cohort overrides shadow global _god_mode_settings for this
    cohort only.  All other cohorts remain unaffected.

    Access rules:
    - super_admin: may set any COHORT_OVERRIDABLE_KEYS.
    - lead_facilitator: may only set freeze-related keys for sessions they own.
    - facilitator: no write access (403 — blocked by require_lead_facilitator guard).

    Non-overridable keys in the body are silently ignored (not an error), so
    the frontend can safely POST the full settings object.
    """
    # Resolve caller's role
    caller_fac = None
    try:
        from auth_jwt import get_facilitator_from_request
        caller_id = get_facilitator_from_request(request)
        if caller_id:
            caller_fac = next((f for f in _facilitator_registry if f["facilitator_id"] == caller_id), None)
    except Exception:
        pass

    # Resolve on the signed-token LEVEL so virtual identities (god_mode /
    # project_admin) aren't silently demoted to "facilitator" by the absent
    # registry row (CLAUDE.md role convention 1).
    caller_role = get_fac_role(request)

    # HIGH-tier advanced controls: coerce/clamp before any filtering or persistence.
    body = normalize_advanced_cohort_settings(body)

    # Slice 5: Stakeholder Negotiation Rooms are a per-facilitator capability. A
    # lead may only switch the cohort flag ON if their OWN profile holds the
    # grant; god_mode / super_admin (is_admin_role, resolved from the signed
    # token so virtual identities aren't demoted) bypass. Refuse BEFORE any write
    # so a denied toggle leaves the cohort untouched.
    if body.get("negotiation_rooms_enabled") is True and not is_admin_role(caller_role):
        if not (caller_fac and caller_fac.get("negotiation_rooms_enabled") is True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=("Stakeholder Negotiation Rooms are not enabled for your facilitator "
                        "profile. Ask a super admin to grant the capability."),
            )

    # lead_facilitators may only touch freeze keys and specific simulation parameters for sessions they own
    _LEAD_FAC_KEYS = frozenset({
        "system_frozen", "freeze_message", "freeze_started_at",
        "climate_paradigm",  # C6: canonical climate branch (per-cohort, lead-overridable)
        "simulation_mode", "global_carbon_fee", "market_hostility_index", "scope_3_threshold",
        # Slice 5: a lead may toggle Negotiation Rooms on their OWN cohort — the
        # capability gate above already requires the grant to turn it ON.
        "negotiation_rooms_enabled",
    })
    rejected_for_role: list = []
    if caller_role == "lead_facilitator":
        # Ownership check
        session_rec = None
        try:
            import database as _db
            session_rec = (await _db.fetch_all_sessions() or [])
            session_rec = next((s for s in session_rec if s.get("session_id") == session_id), None)
        except Exception:
            pass
        if session_rec and caller_fac and not owns_session(caller_fac, session_rec):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify cohort settings for sessions you own.",
            )
        # Report keys this role may NOT set BEFORE dropping them, so a disallowed
        # toggle surfaces as rejected_for_role rather than vanishing with a 200.
        rejected_for_role = [k for k in body if k not in _LEAD_FAC_KEYS]
        # Restrict to lead facilitator allowed keys
        body = {k: v for k, v in body.items() if k in _LEAD_FAC_KEYS}

    # Filter to allow-listed keys only
    safe_body = {k: v for k, v in body.items() if k in COHORT_OVERRIDABLE_KEYS}
    rejected_keys = [k for k in body if k not in COHORT_OVERRIDABLE_KEYS]

    if session_id not in cohort_settings:
        cohort_settings[session_id] = {}

    # Auto-stamp freeze timestamp when system_frozen transitions True
    if safe_body.get("system_frozen") is True and not cohort_settings[session_id].get("system_frozen"):
        safe_body.setdefault("freeze_started_at", datetime.now(timezone.utc).isoformat())
    elif safe_body.get("system_frozen") is False:
        safe_body["freeze_started_at"] = None

    cohort_settings[session_id].update(safe_body)

    # RNG seed (GAME-4): stamp the cohort's stochastic_seed onto the live game
    # state so every engine roll is reproducible + identical across teams. Mirror
    # the ending_pathway/CEO-interview flag-propagation pattern (parent + children).
    if "rng_seed" in safe_body:
        _seed = (safe_body.get("rng_seed") or "").strip()
        try:
            latest = await db.fetch_latest_state(session_id)
            if latest:
                gs = latest["global_state"]
                flags = gs.setdefault("active_event_flags", {})
                if _seed:
                    flags["stochastic_seed"] = _seed
                else:
                    flags.pop("stochastic_seed", None)  # empty ⇒ back to non-deterministic
                await db.update_latest_global_state(session_id, gs, latest["bu_states"])
                for child in await db.get_child_sessions(session_id):
                    child_state = await db.fetch_latest_state(child["session_id"])
                    if not child_state:
                        continue
                    child_gs = child_state["global_state"]
                    child_flags = child_gs.setdefault("active_event_flags", {})
                    if _seed:
                        child_flags["stochastic_seed"] = _seed
                    else:
                        child_flags.pop("stochastic_seed", None)
                    await db.update_latest_global_state(child["session_id"], child_gs, child_state["bu_states"])
        except Exception as _e:  # never fail the settings write on a stamping hiccup
            print(f"[cohort-settings] rng_seed stamp skipped for {session_id}: {_e}")

    # Durably persist the override to the volume so it survives redeploys /
    # restarts in both memory and Postgres backends.
    mark_cohort_settings_dirty()

    _audit("cohort_settings_patched", details={
        "session_id": session_id,
        "applied": safe_body,
        "rejected_non_overridable": rejected_keys,
        "caller_role": caller_role,
    })

    # Push live update to connected admin clients for this session
    await manager.push_to_session(session_id, {
        "type": "cohort_settings_changed",
        "session_id": session_id,
        "changed_keys": list(safe_body.keys()),
        "settings": cohort_settings[session_id],
    })

    return {
        "status": "ok",
        "session_id": session_id,
        "applied": safe_body,
        "rejected_non_overridable": rejected_keys,
        "rejected_for_role": rejected_for_role,
        "overrides": cohort_settings[session_id],
        "effective": get_effective_settings(session_id),
    }


@admin_router.delete(
    "/sessions/{session_id}/cohort-settings",
    summary="Reset per-cohort settings overrides to global defaults (GOD-012)",
)
async def delete_cohort_settings(
    session_id: str,
    _guard: None = Depends(require_super_admin),
):
    """Clear all per-cohort setting overrides for session_id.

    After this call the cohort reverts to global _god_mode_settings with no
    per-cohort overrides. super_admin only.
    """
    removed = cohort_settings.pop(session_id, {})
    mark_cohort_settings_dirty()  # persist the removal to the durable volume
    _audit("cohort_settings_reset", details={"session_id": session_id, "removed_keys": list(removed.keys())})

    await manager.push_to_session(session_id, {
        "type": "cohort_settings_reset",
        "session_id": session_id,
        "message": "Cohort settings reset to global defaults.",
    })

    return {
        "status": "ok",
        "session_id": session_id,
        "removed_overrides": removed,
        "effective": _god_mode_settings,
    }


# ═════════════════════════════════════════════════════════════════
#  COHORT SETTINGS TEMPLATES — clone-as-template (MEDIUM tier)
#
#  A facilitator tunes one cohort's override layer, saves it under a name,
#  and applies it to any future cohort — repeatable setups without
#  hand-copying two dozen switches. Templates store ONLY overridable,
#  normalised keys, and 'apply' goes through the exact same PATCH path as a
#  manual edit (normalisation, role filtering, RNG-seed stamping, audit).
# ═════════════════════════════════════════════════════════════════

class CohortTemplateCreateRequest(BaseModel):
    name: str
    source_session_id: str
    description: str | None = None


@admin_router.get("/cohort-templates", summary="List saved cohort settings templates")
async def list_cohort_templates(_guard: None = Depends(require_facilitator)):
    return {"templates": [
        {"template_id": tid, "name": t.get("name", ""),
         "description": t.get("description", ""),
         "created_by": t.get("created_by", ""),
         "source_session_id": t.get("source_session_id", ""),
         "created_at": t.get("created_at", ""),
         "keys": sorted(t.get("settings", {}).keys())}
        for tid, t in _cohort_templates.items()
    ]}


@admin_router.post("/cohort-templates", summary="Save a cohort's settings as a reusable template")
async def create_cohort_template(body: CohortTemplateCreateRequest, request: Request,
                                 _guard: None = Depends(require_facilitator)):
    """Snapshot the source cohort's override layer (overridable keys only) under
    a template name. Any facilitator may save templates — provisioning-adjacent,
    so project_admin is deliberately allowed too."""
    name = (body.name or "").strip()[:80]
    if not name:
        raise HTTPException(status_code=422, detail="Template name is required.")
    overrides = cohort_settings.get(body.source_session_id, {})
    settings = {k: v for k, v in normalize_advanced_cohort_settings(dict(overrides)).items()
                if k in COHORT_OVERRIDABLE_KEYS}
    # Never bake transient freeze state into a reusable template.
    for _transient in ("system_frozen", "freeze_message", "freeze_started_at"):
        settings.pop(_transient, None)
    if not settings:
        raise HTTPException(status_code=422,
                            detail="Source cohort has no overrides to save — tune its settings first.")
    template_id = f"tpl-{uuid.uuid4().hex[:10]}"
    try:
        from auth_jwt import get_facilitator_from_request
        created_by = get_facilitator_from_request(request) or ""
    except Exception:
        created_by = ""
    _cohort_templates[template_id] = {
        "name": name,
        "description": (body.description or "").strip()[:300],
        "settings": settings,
        "created_by": created_by,
        "source_session_id": body.source_session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    mark_cohort_settings_dirty()  # persist templates to the durable volume
    _audit("cohort_template_created", details={
        "template_id": template_id, "name": name,
        "source_session_id": body.source_session_id, "keys": sorted(settings.keys()),
    })
    return {"status": "ok", "template_id": template_id, "name": name,
            "settings": settings}


@admin_router.delete("/cohort-templates/{template_id}", summary="Delete a cohort settings template")
async def delete_cohort_template(template_id: str, _guard: None = Depends(require_lead_facilitator)):
    removed = _cohort_templates.pop(template_id, None)
    if removed is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    mark_cohort_settings_dirty()  # persist the removal to the durable volume
    _audit("cohort_template_deleted", details={"template_id": template_id, "name": removed.get("name", "")})
    return {"status": "ok", "template_id": template_id}


@admin_router.post("/cohort-templates/{template_id}/apply/{session_id}",
                   summary="Apply a settings template to a cohort")
async def apply_cohort_template(template_id: str, session_id: str, request: Request,
                                _guard: None = Depends(require_lead_facilitator)):
    """Merge a template's settings into the target cohort's override layer.

    Delegates to the cohort-settings PATCH handler so template application is
    byte-for-byte a manual settings edit: same normalisation, same role/key
    filtering, same RNG-seed stamping and audit trail."""
    tpl = _cohort_templates.get(template_id)
    if tpl is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    result = await patch_cohort_settings(session_id, body=dict(tpl.get("settings", {})), request=request)
    _audit("cohort_template_applied", details={
        "template_id": template_id, "name": tpl.get("name", ""), "session_id": session_id,
    })
    return {"status": "ok", "template_id": template_id, "name": tpl.get("name", ""),
            "session_id": session_id,
            "applied": result.get("applied", {}),
            "effective": result.get("effective", {})}


# ── Briefing videos (Read | Watch on round briefings) ────────────────────────
class BriefingVideosRequest(BaseModel):
    briefing_video_base: str | None = None
    briefing_videos: dict | None = None


@admin_router.post("/sessions/{session_id}/briefing-videos",
                   summary="Set per-cohort briefing video URLs")
async def set_briefing_videos(session_id: str, body: BriefingVideosRequest,
                              _guard: None = Depends(require_facilitator)):
    """Store the cohort's briefing-video config (URL pattern + per-round map)
    in the per-cohort settings layer, through the same normalisation as any
    settings write (http(s)-only URLs, rounds 1–10). Players read it back via
    GET /global-settings?session_id=… and get a Read | Watch choice on each
    round briefing. Facilitator-level access: configuring a cohort's media is
    provisioning work, so project_admin is deliberately allowed too."""
    payload = {}
    if body.briefing_video_base is not None:
        payload["briefing_video_base"] = body.briefing_video_base
    if body.briefing_videos is not None:
        payload["briefing_videos"] = body.briefing_videos
    if not payload:
        raise HTTPException(status_code=422, detail="Nothing to save — provide briefing_video_base and/or briefing_videos.")

    clean = normalize_advanced_cohort_settings(payload)
    cohort_settings.setdefault(session_id, {}).update(
        {k: v for k, v in clean.items() if k in COHORT_OVERRIDABLE_KEYS}
    )
    mark_cohort_settings_dirty()  # durable across redeploys in both backends
    _audit("briefing_videos_updated", details={
        "session_id": session_id,
        "briefing_video_base": clean.get("briefing_video_base"),
        "rounds_configured": sorted((clean.get("briefing_videos") or {}).keys()),
    })
    eff = get_effective_settings(session_id)
    return {
        "status": "ok",
        "session_id": session_id,
        "briefing_video_base": eff.get("briefing_video_base", ""),
        "briefing_videos": eff.get("briefing_videos", {}) or {},
    }


@admin_router.get("/scaffolding-status", summary="Get active pedagogical scaffolding features (read-only)")
async def get_scaffolding_status():
    """Returns which global pedagogical features are currently ON/OFF.
    Used by the Facilitator dashboard to display a read-only summary strip."""
    scaffolding_keys = [
        ("prediction_gates_enabled", "🔮 Predictions", False, "Require students to predict outcomes before seeing results — builds metacognitive awareness"),
        ("confidence_calibration_enabled", "🎰 Confidence", False, "Students rate confidence in their predictions — reveals overconfidence and Dunning-Kruger gaps"),
        ("board_room_moments_enabled", "🏢 Board Room", True, "Board Room Moment — a guided post-round reflection (Noticing → Making Sense → Working with Meaning) shown after results are reviewed"),
        ("consequence_map_enabled", "🗺️ Consequence Map", True, "Decision Consequence Map — the results-view timeline linking each round's decisions to their downstream governance / climate / risk / social / supply-chain / strategic effects"),
        ("round_recap_enabled", "📋 Recap", False, "Auto-generate end-of-round summaries highlighting KPI shifts and causal links"),
        ("real_world_cards_enabled", "🌍 Case Cards", False, "Surface real-world ESG case study cards matched to the current decision context"),
        ("strategy_memo_enabled", "📝 Memo", False, "Prompt students to write a strategy memo justifying their decision before committing"),
        ("debrief_protocol_enabled", "🎭 Debrief", False, "Enable structured post-round debrief protocols with guided reflection prompts"),
        ("briefing_theory_enabled", "📚 Briefing Theory", False, "Show academic framing on PLAYER round briefings (theory card + narrative citations). OFF by default; facilitator teleprompter keeps the pedagogy either way"),
        ("self_learning_mode", "🎓 Self-Learn", False, "Solo/self-paced mode — unlocks all rounds and disables facilitator gating"),
        ("r6_revelation_enabled", "🚨 R6 Twist", True, "Round 6 narrative twist — reveals hidden supply chain consequences from earlier decisions"),
        ("r7_budget_allocation_enabled", "♻️ R7 Budget", True, "Round 7 sustainability budget allocation challenge with constrained capital"),
        ("r8_tribunal_enabled", "⚖️ R8 Tribunal", True, "Round 8 stakeholder tribunal — students defend decisions under cross-examination"),
        # New Engine Toggles
        ("decision_timer_enabled", "⏱️ Timer", False, "Enforce countdown timers on decisions — simulates real boardroom time pressure"),
        ("biodiversity_engine_enabled", "🌿 Biodiversity", True, "Track biodiversity impact scores and natural capital depletion across BUs"),
        ("balance_sheet_enabled", "📊 Balance Sheet", True, "Show full balance sheet view with assets, liabilities, and equity breakdown"),
        ("board_governance_enabled", "🏛️ Board Gov", True, "Simulate board governance dynamics — director independence, committee oversight, voting"),
        ("supply_chain_network_enabled", "🔗 Supply Chain", True, "Model supply chain network effects — disruptions cascade through tier-1/2/3 suppliers"),
        ("npc_stakeholders_enabled", "👥 NPC Agents", True, "Activate NPC stakeholder agents (media, regulators, NGOs) that react to decisions"),
        ("org_politics_enabled", "🤝 Org Politics", True, "Internal politics engine — executive alignment, departmental friction, power dynamics"),
        # Stakeholder realism waves (SPEC F1–F6) — per-cohort, default OFF
        ("stakeholder_memory_enabled", "🧠 Stakeholder Memory", False, "F1 — NPCs accumulate a trust stock (rises slowly, falls fast) with betrayal scars; trust gates escalation and cascades"),
        ("stakeholder_slo_feedback_enabled", "🔁 SLO Feedback", False, "F2 — each stakeholder's escalation tier continuously nudges the SLO of the BUs it's attached to (closes the loop)"),
        ("stakeholder_engagement_enabled", "🤝 Promises", False, "F5 — per-round engagement actions (town hall / pledge / commitment) with a promise ledger; kept promises pay off, broken ones scar"),
        ("stakeholder_coalitions_enabled", "🪧 Coalitions", False, "F3 — ≥2 hostile stakeholders form a coalition that amplifies SLO feedback and strike risk; fired cascades nudge their named targets"),
        ("stakeholder_uncertainty_enabled", "🎲 Uncertain Thresholds", False, "F4 — escalation thresholds jittered per cohort (seeded/fair) plus a patience clock that forces escalation over time"),
        ("stakeholder_intel_ui_enabled", "🔎 Intel Rail", False, "F6 — surfaces demand / leverage / trend cards per stakeholder (numbers kept to the facilitator view)"),
        ("branching_enabled", "🔀 Branching", True, "Enable narrative branching paths based on cumulative decision patterns"),
        ("dynamic_cases_enabled", "📰 Case Studies", True, "Dynamically inject industry case studies relevant to current round themes"),
        ("tcfd_scenarios_enabled", "🌡️ TCFD", True, "Run TCFD climate scenario analysis — physical and transition risk modelling"),
        ("regulatory_sandbox_enabled", "⚖️ Reg Sandbox", False, "Inject Pigou taxes, Coase bargaining, and Ostrom governance instruments live"),
        ("meadows_leverage_enabled", "🎯 Leverage Pts", True, "Highlight Meadows' leverage points — where small interventions create systemic change"),
        ("system_archetypes_enabled", "🔄 Archetypes", True, "Detect and surface Senge's system archetypes (Fixes That Fail, Shifting the Burden, etc.)"),
        # BRSR NGRBC
        ("brsr_ngrbc_enabled", "🇮🇳 BRSR NGRBC", False, "Enable BRSR/NGRBC Indian regulatory compliance side-track for ESG reporting"),
        # Scholarly ESG Capitalisation
        ("esg_bs_scholarly_mode", "📚 ESG on BS (Scholarly)", False,
         "What-if view: recognise Social Licence & Reputation as on-GAAP intangibles. "
         "Explores IAS 38 debate (IIRC <IR> Framework; Barker & Eccles, 2011). "
         "Available to all facilitators — toggle live in the balance sheet view."),
    ]
    features = []
    for key, label, default, description in scaffolding_keys:
        features.append({
            "key": key,
            "label": label,
            "enabled": _god_mode_settings.get(key, default),
            "description": description,
        })
    return {
        "features": features,
        "system_frozen": _god_mode_settings.get("system_frozen", False),
        "simulation_mode": _god_mode_settings.get("simulation_mode", "standard"),
    }


@admin_router.get("/facilitator-role-info/{fac_id}", summary="Get role and permissions for a facilitator")
async def get_facilitator_role_info(fac_id: str, _guard: None = Depends(require_facilitator)):
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
        "is_admin": is_admin_role(role),
    }


@admin_router.put("/facilitators/{fac_id}/role", summary="Change a facilitator's role (God Mode only)")
async def update_facilitator_role(
    fac_id: str,
    body: dict = Body(...),
    request: Request = None,
    _guard: None = Depends(require_super_admin),  # GOD-001: use standard JWT chain
):
    """Change a facilitator's role. Requires an active super_admin JWT session
    AND re-verification of the caller's password (defence-in-depth for
    privilege-escalation operations).
    """
    _check_rate_limit(request, "role_change")   # GOD-001: rate-limit this path too

    # ── Re-verify caller credentials (defence-in-depth) ──────
    # The JWT cookie already proves the caller *was* authenticated, but role
    # changes are high-impact — re-verifying the password guards against
    # unattended-session abuse and adds a deliberate friction step.
    caller_fac_id = body.get("god_mode_fac_id", "").strip()
    caller_password = body.get("god_mode_password", "").strip()
    if not caller_fac_id or not caller_password:
        raise HTTPException(400, "God Mode Facilitator ID and password are required for role changes.")

    # Check against master password first (covers the virtual god_mode account)
    master_ok = verify_master_password(caller_password)
    # M-5: Audit log when master password bypass is used
    if master_ok:
        print(f"[SECURITY] MASTER_PASSWORD used for role change by caller={caller_fac_id}")

    if not master_ok:
        # Look up the facilitator in the registry and verify their bcrypt hash
        caller_fac = next(
            (f for f in _facilitator_registry
             if (f["facilitator_id"].lower() == caller_fac_id.lower() or
                 f.get("name", "").lower() == caller_fac_id.lower())
             and not f.get("deleted_at")),
            None,
        )
        if not caller_fac:
            raise HTTPException(403, "Invalid God Mode credentials.")
        # Caller must have super-admin authority (super_admin/admin/god_mode)
        if not is_admin_role(get_role(caller_fac)):
            raise HTTPException(403, "Only Super Administrators can change roles.")
        if not verify_password(caller_password, caller_fac.get("password", "")):
            raise HTTPException(403, "Invalid God Mode credentials.")

    # ── Apply role change ───────────────────────────────────
    new_role = body.get("role", "").strip()
    # C6/C1: block escalation to the virtual god_mode tier and enforce that the
    # caller may only grant roles within its own scope (assignable_roles_for).
    _caller_role = get_fac_role(request)
    _grantable = assignable_roles_for(_caller_role)
    if new_role not in ROLE_HIERARCHY:
        raise HTTPException(400, f"Invalid role '{new_role}'. Must be one of: {sorted(_ASSIGNABLE_ROLES)}")
    if new_role not in _grantable:
        raise HTTPException(403, f"Your role ('{_caller_role}') may not assign the role '{new_role}'. Allowed: {sorted(_grantable)}.")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    fac["role"] = new_role
    fac["is_admin"] = is_admin_role(new_role)  # backward compat (god_mode-aware)
    _persist_facilitators()
    from auth_jwt import get_facilitator_from_request
    caller = get_facilitator_from_request(request) or caller_fac_id
    _audit("facilitator_role_changed", details={"facilitator_id": fac_id, "new_role": new_role, "changed_by": caller})
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
    treasury_start = settings.get("corporate_treasury_start", SIM_INITIAL_BUDGET)
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
                {"name": "Regenerative Titan", "mr_min": 1.8, "icon": ""},
                {"name": "De-risked Safe Haven", "mr_min": 1.2, "icon": ""},
                {"name": "Fragile Giant", "mr_min": 0.8, "icon": ""},
                {"name": "Stranded Relic", "mr_min": 0.0, "icon": ""},
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
        "icon": body.get("icon", ""),
        "gradient": body.get("gradient", "linear-gradient(135deg, #6366f1, #8b5cf6)"),
        "is_default": False,
        # AR-C: second axis — only award this archetype to a solvent company.
        "requires_solvent": bool(body.get("requires_solvent", False)),
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
    if "requires_solvent" in body:  # AR-C: second axis
        customs[idx]["requires_solvent"] = bool(body["requires_solvent"])
    customs[idx]["is_default"] = False
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    print(f"[god-mode] Archetype updated: {key}")
    return {"status": "ok", "archetype": customs[idx]}


@admin_router.delete("/archetypes/{key}", summary="Delete a custom archetype")
async def delete_archetype(key: str, _guard: None = Depends(require_super_admin)):
    customs = _god_mode_settings.get("custom_archetypes", [])
    before = len(customs)
    _god_mode_settings["custom_archetypes"] = [a for a in customs if a["key"] != key]
    if len(_god_mode_settings["custom_archetypes"]) == before:
        raise HTTPException(404, f"Custom archetype '{key}' not found (defaults cannot be deleted, only overridden)")
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
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
async def switch_session_ending_pathway(session_id: str, request: Request, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
    """Switch the ending pathway for a live session.
    Requires allow_pathway_switching to be enabled in god-mode settings.
    GOD-012: respects per-cohort overrides if set."""
    await _assert_session_ownership(request, session_id)
    # GOD-012: use effective settings so per-cohort allow_pathway_switching works
    _eff = get_effective_settings(session_id)
    if not _eff.get("allow_pathway_switching", False):
        raise HTTPException(403, "Pathway switching is disabled. Enable 'allow_pathway_switching' in God Mode settings.")

    new_pathway = body.get("ending_pathway", "").strip()
    available = _eff.get("ending_pathways_available", ["activist_ultimatum"])
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
async def configure_cohort_interview(session_id: str, request: Request, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
    """Set per-cohort CEO Interview settings.

    Body fields (all optional):
    - ceo_interview_enabled: bool
    - ceo_interview_voice_gender: "female" | "male"

    Overrides god-mode defaults for this specific cohort and all its player sessions.
    """
    await _assert_session_ownership(request, session_id)
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

    # 2026-07-20: the PARENT write and the CHILD-propagation are now separated,
    # and both surface a MEANINGFUL error instead of the opaque generic 500.
    #
    # Context: this endpoint was reported failing during cohort setup with
    # "An internal server error occurred" — the global handler's message, shown
    # whenever DEBUG=false, which hid the actual cause from the operator AND the
    # logs the operator could see. Two structural problems made that worse:
    #   1. A single malformed CHILD session raised out of the loop and failed
    #      the WHOLE request, even though the parent write had already
    #      succeeded — so the cohort was reported "not configured" when its own
    #      CEO setting had in fact been applied.
    #   2. Every failure looked identical, so it could not be triaged.
    # The parent write is the authoritative one; child propagation is
    # best-effort catch-up and must not be able to fail the operation.
    try:
        await db.update_latest_global_state(session_id, gs, latest["bu_states"])
    except HTTPException:
        raise
    except Exception as exc:
        _ar_log.exception("CEO-interview: parent write failed for %s", session_id)
        raise HTTPException(
            status_code=502,
            detail=f"Could not save the CEO Interview setting for this cohort: {exc}",
        )

    # Propagate to all child player sessions — best-effort, isolated per child.
    children = await db.get_child_sessions(session_id)
    child_ok, child_failed = 0, 0
    for child in children:
        try:
            child_state = await db.fetch_latest_state(child["session_id"])
            if not child_state:
                continue
            child_gs = child_state["global_state"]
            child_flags = child_gs.setdefault("active_event_flags", {})
            if "ceo_interview_enabled" in body:
                child_flags["ceo_interview_enabled"] = flags["ceo_interview_enabled"]
            if "ceo_interview_voice_gender" in body:
                child_flags["ceo_interview_voice_gender"] = flags.get("ceo_interview_voice_gender", "female")
            await db.update_latest_global_state(child["session_id"], child_gs, child_state["bu_states"])
            child_ok += 1
        except Exception:
            # A bad child does not undo the parent write, and does not fail the
            # request. Players read the effective setting from the parent cohort
            # anyway; this loop is an optimisation, not the source of truth.
            child_failed += 1
            _ar_log.warning("CEO-interview: child propagation failed for %s (parent %s)",
                            child.get("session_id"), session_id)

    _ar_log.info("CEO Interview config updated for %s: %s (children %d ok, %d skipped)",
                 session_id, ", ".join(updated_fields) or "no-op", child_ok, child_failed)
    return {
        "status": "ok",
        "session_id": session_id,
        "ceo_interview_enabled": flags.get("ceo_interview_enabled"),
        "ceo_interview_voice_gender": flags.get("ceo_interview_voice_gender"),
        "children_updated": child_ok,
        "children_skipped": child_failed,
    }

@admin_router.get("/facilitators", summary="List all facilitators")
async def list_facilitators(request: Request, _guard: None = Depends(require_facilitator)):
    """List facilitators. Passwords are always masked.
    M-4: non-super-admins receive only their own record to prevent PII leakage."""
    from auth_jwt import get_facilitator_from_request
    caller_id = get_facilitator_from_request(request)
    caller_role = get_fac_role(request)
    is_admin_caller = (caller_role == "super_admin") or (caller_id == "god_mode") or (caller_role == "project_admin")

    result = []
    for f in _facilitator_registry:
        if f.get("deleted_at"):
            continue
        # Non-super-admins may only see their own record
        if not is_admin_caller and f.get("facilitator_id") != caller_id:
            continue
        entry = {**f, "password": "••••••"}
        result.append(entry)
    return {"facilitators": result}


@admin_router.post("/facilitators", summary="Create a new facilitator")
async def create_facilitator(req: FacilitatorCreateRequest, request: Request, _guard: None = Depends(require_registry_admin)):
    import re
    # C1/P1: enforce caller-scoped role grants BEFORE doing any work. Blocks a
    # project_admin (which passes require_registry_admin) from minting a
    # super_admin, and blocks anyone from assigning the virtual god_mode tier.
    _requested_role = req.role or "facilitator"
    _caller_role = get_fac_role(request)
    _grantable = assignable_roles_for(_caller_role)
    if _requested_role not in _grantable:
        raise HTTPException(
            403,
            f"Your role ('{_caller_role}') may not create a facilitator with role "
            f"'{_requested_role}'. Allowed: {sorted(_grantable)}.",
        )
    # GOD-003: Generate password outside the lock — bcrypt is CPU-intensive
    # and does not touch shared state.
    _temp_plain, _temp_hash = _generate_temp_password()

    async with _fac_registry_lock:
        # Recompute max_id inside the lock so two concurrent requests
        # cannot both read the same max and generate the same FAC-NNN.
        max_id = 0
        for f in _facilitator_registry:
            match = re.search(r'\d+', f.get("facilitator_id", ""))
            if match:
                try:
                    max_id = max(max_id, int(match.group()))
                except ValueError:
                    pass
        new_fac_id = f"FAC-{max_id + 1:03d}"
        role = req.role or "facilitator"
        is_fac = role == "facilitator"
        default_perms = {
            "can_undo_rounds": not is_fac,
            "can_override_decisions": not is_fac,
            "can_modify_materiality": not is_fac,
            "can_manage_auto_pause": not is_fac,
            "can_create_cohorts": not is_fac,
            "can_enable_side_tracks": not is_fac,
        }
        fac = {
            "facilitator_id": new_fac_id,
            "name": req.name,
            "email": req.email or "",
            "contact_number": req.contact_number or "",
            "programme": req.programme or "",
            "start_date": req.start_date or "",
            "end_date": req.end_date or "",
            "password": _temp_hash,  # LOW-003: store bcrypt hash, never plaintext
            "must_change_password": True,  # default Muressons123 must be replaced on first login
            "created_at": datetime.now(timezone.utc).isoformat(),
            "max_cohorts": req.max_cohorts,
            "cohorts_created": 0,
            "decision_paradigm": req.decision_paradigm,
            "ending_pathway": req.ending_pathway or "activist_ultimatum",
            "side_tracks": req.side_tracks or [],
            "simulation_mode": req.simulation_mode or "conglomerate",
            "industry_vertical": req.industry_vertical or "",
            "bu_substitutions": req.bu_substitutions or {},
            "role": role,
            "is_admin": is_admin_role(role),
            "enabled": True,
            "shockwave_enabled": req.shockwave_enabled if req.shockwave_enabled is not None else True,  # Feature 6
            "trading_floor_enabled": req.trading_floor_enabled if req.trading_floor_enabled is not None else True,  # Feature 1
            "situation_room_enabled": req.situation_room_enabled if req.situation_room_enabled is not None else True,  # W-D (W4)
            "negotiation_rooms_enabled": req.negotiation_rooms_enabled is True,  # Slice 5: opt-in, default OFF
            "permissions": req.permissions or default_perms,
            "created_by": req.created_by or "",
            "date_created": req.date_created or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        _facilitator_registry.append(fac)

    # Persist outside the lock — file I/O does not need the registry guard
    _persist_facilitators()
    # M-3: Return a clean facilitator record (no bcrypt hash) with the one-time
    # plaintext credential in a clearly-named top-level key so API gateway logs
    # that record response bodies are less likely to capture it inadvertently.
    safe_fac = {k: v for k, v in fac.items() if k != "password"}
    return {
        **safe_fac,
        "one_time_password": _temp_plain,
        "credential_note": "Default password Muressons123 — the facilitator must change it on first login.",
    }


# ── W-PA: Excel bulk upload (project_admin + super_admin) ─────────────────
_BULK_UPLOAD_COLUMNS = [
    "name", "email", "contact_number", "programme", "start_date", "end_date",
    "max_cohorts", "decision_paradigm", "role", "ending_pathway",
    "simulation_mode", "industry_vertical", "side_tracks",
    "shockwave_enabled", "trading_floor_enabled", "situation_room_enabled",
]

# Friendly header aliases accepted in either upload path (case/space tolerant).
_BULK_UPLOAD_ALIASES = {
    "phone": "contact_number", "phone_number": "contact_number", "mobile": "contact_number",
    "contact": "contact_number", "cohorts": "max_cohorts", "paradigm": "decision_paradigm",
    "program": "programme", "course": "programme", "pathway": "ending_pathway",
    "mode": "simulation_mode", "vertical": "industry_vertical", "tracks": "side_tracks",
    "side_track": "side_tracks", "shockwave": "shockwave_enabled",
    "trading_floor": "trading_floor_enabled", "situation_room": "situation_room_enabled",
}


def _bulk_bool(v, default=True):
    """Parse a spreadsheet cell into a bool; blank/None → default."""
    s = str(v).strip().lower()
    if s in ("", "none"):
        return default
    return s in ("1", "true", "yes", "y", "on", "enabled")


def _bulk_list(v):
    """Parse a delimited cell (';', '|' or ',') into a clean list of strings."""
    if not v:
        return []
    s = str(v).replace("|", ";").replace(",", ";")
    return [t.strip() for t in s.split(";") if t.strip()]


@admin_router.get("/facilitators/bulk-upload/template", summary="Download the Excel template for facilitator bulk upload")
async def facilitator_bulk_upload_template(_guard: None = Depends(require_registry_admin)):
    """Generates the .xlsx template in memory: a header row (name is the only
    required column) plus one example row."""
    from io import BytesIO
    from openpyxl import Workbook
    from fastapi.responses import StreamingResponse
    wb = Workbook()
    ws = wb.active
    ws.title = "Facilitators"
    ws.append(_BULK_UPLOAD_COLUMNS)
    ws.append(["Dr. A. Example", "a.example@university.edu", "+91 98xxxxxx", "PGP 2026",
               "2026-08-01", "2026-12-15", 3, "legacy_abc", "facilitator",
               "activist_ultimatum", "conglomerate", "", "", "TRUE", "TRUE", "TRUE"])
    ws.append(["Prof. B. Sample", "b.sample@university.edu", "", "Executive Programme",
               "", "", 5, "healthcare", "lead_facilitator", "stakeholder_revolt",
               "conglomerate", "", "brsr_ngrbc;supply_chain", "TRUE", "FALSE", "TRUE"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="facilitator_bulk_upload_template.xlsx"'},
    )


def _parse_bulk_upload_sheet(raw: bytes):
    """F-4 proper (v3/S5): the parsing half of the Excel bulk upload, shared by
    the CREATE endpoint below and the parse-only PREVIEW endpoint — extracted
    verbatim so the two can never disagree about what a file contains.

    Returns (valid_rows, errors): valid_rows carry every column the create
    path consumes plus the sheet row number; errors are {row, error}. Raises
    the same HTTPExceptions the create path always raised for unreadable
    files / missing headers."""
    from io import BytesIO
    from openpyxl import load_workbook

    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 2 MB)")
    try:
        wb = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(400, "Not a readable .xlsx file. Download the template and try again.")
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(400, "The sheet is empty.")

    # Header mapping — case/space tolerant, friendly aliases resolved, unknowns ignored
    header = [str(c or "").strip().lower().replace(" ", "_") for c in rows[0]]
    header = [_BULK_UPLOAD_ALIASES.get(h, h) for h in header]
    col_idx = {name: header.index(name) for name in _BULK_UPLOAD_COLUMNS if name in header}
    if "name" not in col_idx:
        raise HTTPException(400, f"Header row must contain a 'name' column. Found: {[h for h in header if h]}")

    valid_rows, errors = [], []
    for rownum, row in enumerate(rows[1:], start=2):
        def cell(key, default=""):
            i = col_idx.get(key)
            v = row[i] if i is not None and i < len(row) else None
            return str(v).strip() if v is not None else default
        name = cell("name")
        if not name:
            if any(str(c or "").strip() for c in row):
                errors.append({"row": rownum, "error": "Missing required 'name'"})
            continue  # fully blank rows are skipped silently
        try:
            mc = int(float(cell("max_cohorts", "3") or 3))
        except (ValueError, TypeError):
            mc = 3
        valid_rows.append({
            "row": rownum,
            "name": name,
            "email": cell("email"),
            "contact_number": cell("contact_number"),
            "programme": cell("programme"),
            "start_date": cell("start_date"),
            "end_date": cell("end_date"),
            "max_cohorts": mc,
            "decision_paradigm": cell("decision_paradigm", "legacy_abc") or "legacy_abc",
            "role": (cell("role", "facilitator") or "facilitator").strip().lower(),
            "ending_pathway": cell("ending_pathway", "activist_ultimatum") or "activist_ultimatum",
            "simulation_mode": cell("simulation_mode", "conglomerate") or "conglomerate",
            "industry_vertical": cell("industry_vertical"),
            "side_tracks": _bulk_list(cell("side_tracks")),
            "shockwave_enabled": _bulk_bool(cell("shockwave_enabled", "true")),
            "trading_floor_enabled": _bulk_bool(cell("trading_floor_enabled", "true")),
            "situation_room_enabled": _bulk_bool(cell("situation_room_enabled", "true")),
        })
    return valid_rows, errors


@admin_router.post("/facilitators/bulk-upload/preview", summary="Parse an Excel bulk-upload WITHOUT creating anything")
async def facilitator_bulk_upload_preview(file: UploadFile = File(...), _guard: None = Depends(require_registry_admin)):
    """F-4 proper (v3/S5): parse-only preview so the Excel path gets the same
    review step the CSV path always had. Creates NOTHING — a deliberately
    distinct route (not a dry_run flag on the create endpoint) so an older
    backend answers 404/405 and the frontend falls back safely instead of
    accidentally creating accounts."""
    raw = await file.read()
    valid_rows, errors = _parse_bulk_upload_sheet(raw)
    return {
        "dry_run": True,
        "rows": valid_rows,
        "errors": errors,
        "total_valid": len(valid_rows),
        "total_errors": len(errors),
        "note": "Nothing was created. POST the same file to /facilitators/bulk-upload to create these accounts.",
    }


@admin_router.post("/facilitators/bulk-upload", summary="Bulk-create facilitators from an Excel file")
async def facilitator_bulk_upload(request: Request, file: UploadFile = File(...), _guard: None = Depends(require_registry_admin)):
    """W-PA — parses an .xlsx (header row = column names; only `name` is
    required) and creates one facilitator per data row with the standard
    policy: default password Muressons123 + must_change_password=True.
    Returns per-row results (R3 setup-integrity style): every failed row is
    reported with its row number and reason; valid rows are still created."""
    import re

    raw = await file.read()
    valid_rows, errors = _parse_bulk_upload_sheet(raw)

    # C6/C1: a role from a spreadsheet is caller-scoped — a bulk upload must never
    # be a backdoor to grant a role above the uploader's own tier.
    _grantable = assignable_roles_for(get_fac_role(request))

    created = []
    # One bcrypt hash for the shared default password (bcrypt is ~100ms/call)
    _plain, _hash = _generate_temp_password()

    async with _fac_registry_lock:
        max_id = 0
        for f in _facilitator_registry:
            match = re.search(r'\d+', f.get("facilitator_id", ""))
            if match:
                try:
                    max_id = max(max_id, int(match.group()))
                except ValueError:
                    pass
        for parsed in valid_rows:
            name = parsed["name"]
            mc = parsed["max_cohorts"]
            def cell(key, default=""):
                return parsed.get(key, default) or default
            max_id += 1
            _req_role = parsed.get("role", "facilitator")
            _role = _req_role if _req_role in _grantable else "facilitator"
            fac = {
                "facilitator_id": f"FAC-{max_id:03d}",
                "name": name,
                "email": cell("email"),
                "contact_number": cell("contact_number"),
                "programme": cell("programme"),
                "start_date": cell("start_date"),
                "end_date": cell("end_date"),
                "password": _hash,  # bcrypt of the default; never plaintext
                "must_change_password": True,  # default Muressons123 must be replaced on first login
                "created_at": datetime.now(timezone.utc).isoformat(),
                "max_cohorts": mc,
                "cohorts_created": 0,
                "decision_paradigm": cell("decision_paradigm", "legacy_abc"),
                "ending_pathway": cell("ending_pathway", "activist_ultimatum"),
                "side_tracks": parsed.get("side_tracks", []),
                "simulation_mode": cell("simulation_mode", "conglomerate"),
                "industry_vertical": cell("industry_vertical"),
                "bu_substitutions": {},
                "role": _role,
                "is_admin": is_admin_role(_role),
                "enabled": True,
                "shockwave_enabled": parsed.get("shockwave_enabled", True),
                "trading_floor_enabled": parsed.get("trading_floor_enabled", True),
                "situation_room_enabled": parsed.get("situation_room_enabled", True),
                "negotiation_rooms_enabled": parsed.get("negotiation_rooms_enabled", False) is True,  # Slice 5
                "permissions": {
                    "can_undo_rounds": False,
                    "can_override_decisions": False,
                    "can_modify_materiality": False,
                    "can_manage_auto_pause": False,
                    "can_create_cohorts": False,
                    "can_enable_side_tracks": False,
                },
                "created_by": "bulk_upload",
                "date_created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }
            _facilitator_registry.append(fac)
            created.append({"facilitator_id": fac["facilitator_id"], "name": name, "one_time_password": _plain})
    _persist_facilitators()
    _audit("facilitator_bulk_upload", details={"created": len(created), "errors": len(errors), "filename": file.filename})
    return {
        "created": created,
        "errors": errors,
        "total_created": len(created),
        "total_errors": len(errors),
        "credential_note": "All facilitators start with the default password Muressons123 and must change it on first login.",
    }

@admin_router.put("/facilitators/{fac_id}", summary="Update a facilitator's details")
async def update_facilitator(fac_id: str, req: FacilitatorUpdateRequest, request: Request, _guard: None = Depends(require_super_admin)):
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")

    update_data = req.model_dump(exclude_unset=True)
    # C6/C1: a role change through the generic update must obey the same
    # assignable + caller-scope rules as the dedicated role endpoint — otherwise
    # this is a backdoor to assign god_mode / escalate.
    if update_data.get("role") is not None:
        _new_role = str(update_data["role"]).strip()
        _caller_role = get_fac_role(request)
        _grantable = assignable_roles_for(_caller_role)
        if _new_role not in ROLE_HIERARCHY:
            raise HTTPException(400, f"Invalid role '{_new_role}'. Must be one of: {sorted(_ASSIGNABLE_ROLES)}.")
        if _new_role not in _grantable:
            raise HTTPException(403, f"Your role ('{_caller_role}') may not assign the role '{_new_role}'. Allowed: {sorted(_grantable)}.")
        update_data["role"] = _new_role
    for key, value in update_data.items():
        if key == "permissions" and isinstance(value, dict):
            # merge permissions instead of replacing to preserve unspecified ones
            current_perms = fac.get("permissions", {})
            current_perms.update(value)
            fac["permissions"] = current_perms
        else:
            fac[key] = value
            
    if "role" in update_data:
        fac["is_admin"] = is_admin_role(update_data["role"])

    _persist_facilitators()
    return fac

@admin_router.post("/facilitators/bulk", summary="Create multiple facilitators in batch")
async def bulk_create_facilitators(req: FacilitatorBulkCreateRequest, request: Request, _guard: None = Depends(require_registry_admin)):
    import re
    created_facs = []
    credentials: dict[str, str] = {}  # M-3: one-time plaintext passwords, keyed by fac ID
    # C6/C1: a role in the payload is caller-scoped — never a backdoor to grant
    # a role above the caller's own tier.
    _grantable = assignable_roles_for(get_fac_role(request))

    # GOD-003: Generate all passwords BEFORE acquiring the lock so bcrypt
    # (CPU-intensive, ~100ms/call) does not block other coroutines.
    passwords = [_generate_temp_password() for _ in req.facilitators]

    async with _fac_registry_lock:
        # Recompute max_id inside the lock for collision-free ID assignment.
        max_id = 0
        for f in _facilitator_registry:
            match = re.search(r'\d+', f.get("facilitator_id", ""))
            if match:
                try:
                    max_id = max(max_id, int(match.group()))
                except ValueError:
                    pass

        for fac_req, (_fac_plain, _fac_hash) in zip(req.facilitators, passwords):
            max_id += 1
            _req_role = (fac_req.role or "facilitator").strip().lower()
            _role = _req_role if _req_role in _grantable else "facilitator"
            fac = {
                "facilitator_id": f"FAC-{max_id:03d}",
                "name": fac_req.name,
                "email": fac_req.email or "",
                "contact_number": fac_req.contact_number or "",
                "programme": fac_req.programme or "",
                "start_date": fac_req.start_date or "",
                "end_date": fac_req.end_date or "",
                "password": _fac_hash,  # store bcrypt hash, never plaintext
                "must_change_password": True,  # default Muressons123 must be replaced on first login
                "created_at": datetime.now(timezone.utc).isoformat(),
                "max_cohorts": fac_req.max_cohorts,
                "cohorts_created": 0,
                "decision_paradigm": fac_req.decision_paradigm,
                "ending_pathway": fac_req.ending_pathway or "activist_ultimatum",
                "side_tracks": fac_req.side_tracks or [],
                "simulation_mode": fac_req.simulation_mode or "conglomerate",
                "industry_vertical": fac_req.industry_vertical or "",
                "role": _role,
                "is_admin": is_admin_role(_role),
                "enabled": True,
                "shockwave_enabled": fac_req.shockwave_enabled,
                "trading_floor_enabled": fac_req.trading_floor_enabled,
                "situation_room_enabled": fac_req.situation_room_enabled,
                "negotiation_rooms_enabled": fac_req.negotiation_rooms_enabled is True,  # Slice 5
                "permissions": fac_req.permissions or {
                    "can_undo_rounds": True,
                    "can_override_decisions": True,
                    "can_modify_materiality": True,
                    "can_manage_auto_pause": True,
                },
            }
            _facilitator_registry.append(fac)
            # M-3: keep plaintext out of the main facilitator object
            created_facs.append({k: v for k, v in fac.items() if k != "password"})
            credentials[fac["facilitator_id"]] = _fac_plain

    _persist_facilitators()
    return {
        "status": "success",
        "created": len(created_facs),
        "facilitators": created_facs,
        "credentials": credentials,
        "credentials_note": "Store these securely — they will not be shown again.",
    }


@admin_router.delete("/facilitators/{fac_id}", summary="Delete a facilitator")
async def delete_facilitator(
    fac_id: str,
    hard: bool = False,
    _guard: None = Depends(require_super_admin),
):
    """Delete a facilitator account and cascade-delete all cohorts they own.

    Soft delete (default, hard=False):
      - Stamps deleted_at on the facilitator record.
      - Soft-deletes every top-level cohort the facilitator owns (and their
        child player-sessions) via _cascade_delete_session(hard=False).
      - Bumps the facilitator's JWT token version so their active session
        cookie is immediately invalidated.

    Hard delete (hard=True):
      - Permanently removes the facilitator record from the JSON registry.
      - Hard-deletes every top-level cohort they own (full DB + memory cleanup).
      - Bumps the JWT token version to revoke any outstanding session.

    Returns: { status, facilitator_id, hard, sessions_deleted, players_removed }
    """
    global _facilitator_registry

    # Resolve the facilitator record first (needed by both branches)
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")

    # ── Cascade: delete all top-level cohorts owned by this facilitator ──
    owned_sessions = await db.fetch_sessions_by_facilitator(fac_id)
    total_sessions_deleted = 0
    total_players_removed = 0
    for sess in owned_sessions:
        result = await _cascade_delete_session(sess["session_id"], hard=hard)
        total_sessions_deleted += result["sessions_deleted"]
        total_players_removed += result["players_removed"]
        # Broadcast each deleted session so the admin dashboard updates live
        await manager.broadcast_admin({
            "type": "session_deleted",
            "session_id": sess["session_id"],
        })

    # ── Immediately revoke outstanding JWT tokens for this facilitator ───
    bump_token_version(fac_id)

    # ── Remove / soft-delete the facilitator record ──────────────────────
    if hard:
        _facilitator_registry[:] = [f for f in _facilitator_registry if f["facilitator_id"] != fac_id]
    else:
        fac["deleted_at"] = datetime.now(timezone.utc).isoformat()

    _persist_facilitators()

    _audit(
        "facilitator_deleted",
        actor="god_mode",
        details={
            "facilitator_id": fac_id,
            "hard": hard,
            "sessions_deleted": total_sessions_deleted,
            "players_removed": total_players_removed,
        },
    )

    return {
        "status": "deleted",
        "facilitator_id": fac_id,
        "hard": hard,
        "sessions_deleted": total_sessions_deleted,
        "players_removed": total_players_removed,
    }


_MAX_BULK_DELETE = 200


@admin_router.post("/facilitators/bulk-delete", summary="Delete multiple facilitators in batch")
async def bulk_delete_facilitators(
    req: FacilitatorBulkDeleteRequest,
    request: Request,
    _guard: None = Depends(require_super_admin),
):
    """Batch counterpart of DELETE /facilitators/{fac_id}.

    Applies the exact same per-account semantics as delete_facilitator — soft
    delete (default) stamps deleted_at + cascade-soft-deletes owned cohorts and
    bumps the JWT token version; hard delete removes the registry record and
    cascade-hard-deletes owned cohorts. Each ID is processed independently: an
    unknown or already-deleted ID is reported per-ID and never aborts the batch.

    Self-protection: the caller cannot delete their own account mid-batch
    (skipped_self) — their session token is left untouched so they stay logged
    in. This mirrors why the single-delete UI never targets the current user.

    Body: { facilitator_ids: [str], hard: bool = False }
    Returns: { status, hard, requested, deleted, results: [{facilitator_id, status, ...}] }
    """
    from auth_jwt import get_facilitator_from_request

    # Normalise: trim, drop blanks, de-duplicate while preserving order.
    seen: set[str] = set()
    ids: list[str] = []
    for raw in req.facilitator_ids:
        fid = (raw or "").strip()
        if fid and fid not in seen:
            seen.add(fid)
            ids.append(fid)

    # Input validation — surfaced as 400 (see model note).
    if not ids:
        raise HTTPException(400, "facilitator_ids must contain at least one non-empty ID")
    if len(ids) > _MAX_BULK_DELETE:
        raise HTTPException(
            400,
            f"Too many facilitators in one batch ({len(ids)}); maximum is {_MAX_BULK_DELETE}.",
        )

    hard = req.hard
    caller_id = get_facilitator_from_request(request)

    results: list[dict] = []
    deleted_count = 0

    for fid in ids:
        # Self-protection: never delete the account making the request.
        if caller_id and fid == caller_id:
            results.append({"facilitator_id": fid, "status": "skipped_self"})
            continue

        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fid), None)
        if not fac:
            results.append({"facilitator_id": fid, "status": "not_found"})
            continue

        # Soft delete is idempotent: an already-stamped record is a no-op.
        if not hard and fac.get("deleted_at"):
            results.append({"facilitator_id": fid, "status": "already_deleted"})
            continue

        # ── Cascade: delete all top-level cohorts owned by this facilitator ──
        owned_sessions = await db.fetch_sessions_by_facilitator(fid)
        total_sessions_deleted = 0
        total_players_removed = 0
        for sess in owned_sessions:
            result = await _cascade_delete_session(sess["session_id"], hard=hard)
            total_sessions_deleted += result["sessions_deleted"]
            total_players_removed += result["players_removed"]
            await manager.broadcast_admin({
                "type": "session_deleted",
                "session_id": sess["session_id"],
            })

        # ── Immediately revoke outstanding JWT tokens for this facilitator ───
        bump_token_version(fid)

        # ── Remove / soft-delete the facilitator record ──────────────────────
        if hard:
            _facilitator_registry[:] = [f for f in _facilitator_registry if f["facilitator_id"] != fid]
        else:
            fac["deleted_at"] = datetime.now(timezone.utc).isoformat()

        deleted_count += 1
        results.append({
            "facilitator_id": fid,
            "status": "deleted",
            "hard": hard,
            "sessions_deleted": total_sessions_deleted,
            "players_removed": total_players_removed,
        })

    _persist_facilitators()

    _audit(
        "facilitators_bulk_deleted",
        actor="god_mode",
        details={
            "requested": len(ids),
            "deleted": deleted_count,
            "hard": hard,
            "results": results,
        },
    )

    # A batch that hit no unknown/skipped IDs is "completed"; anything left
    # unresolved (not_found / skipped_self) is "partial".
    unresolved = any(r["status"] in ("not_found", "skipped_self") for r in results)
    overall_status = "partial" if unresolved else "completed"

    return {
        "status": overall_status,
        "hard": hard,
        "requested": len(ids),
        "deleted": deleted_count,
        "results": results,
    }


@admin_router.post("/facilitators/login", summary="Facilitator login")
async def facilitator_login(request: Request, response: Response, body: dict = Body(...)):
    # HIGH-009: Rate-limit login attempts per IP
    _check_rate_limit(request, "fac_login")
    fac_id = body.get("facilitator_id", "").strip()
    password = body.get("password", "").strip()
    if not fac_id or not password:
        raise HTTPException(400, "facilitator_id and password are required")
    fac_id_lower = fac_id.lower()
    fac = next(
        (f for f in _facilitator_registry
         if (f["facilitator_id"].lower() == fac_id_lower or
             f.get("username", "").lower() == fac_id_lower or
             f.get("name", "").lower() == fac_id_lower)
         and not f.get("deleted_at")),
        None,
    )
    # FIX AUDIT-005: Master password from env var, empty = disabled
    master_ok = verify_master_password(password)
    # Project-admin virtual account (registry + cohort creation only)
    project_ok = bool(PROJECT_ADMIN_PASSWORD) and hmac.compare_digest(password, PROJECT_ADMIN_PASSWORD)

    # Enforce god_mode for super admin master access.
    # Virtual accounts are rebuilt per-login by design (no registry row), so
    # their durable profile state — the chosen display username — is hydrated
    # from the virtual-profile store; otherwise every login looked like a first
    # login and the callsign screen re-appeared (then 404'd on save).
    from admin_shared import get_virtual_profile as _gvp
    if master_ok and fac_id_lower == "god_mode":
        fac = {
            "facilitator_id": "god_mode",
            "name": "God Mode Administrator",
            "username": _gvp("god_mode").get("username", ""),
            "role": "god_mode",   # C6: distinct level-4 tier, not super_admin
            "is_admin": True,
            "enabled": True,
        }
    elif master_ok and fac_id_lower == "facilitator":
        fac = {
            "facilitator_id": "facilitator",
            "name": "Master Facilitator",
            "username": _gvp("facilitator").get("username", ""),
            "role": "lead_facilitator",
            "is_admin": False,
            "enabled": True,
        }
    elif project_ok and fac_id_lower == "project_admin":
        fac = {
            "facilitator_id": "project_admin",
            "name": "Project Administrator",
            "username": _gvp("project_admin").get("username", ""),
            "role": "project_admin",
            "is_admin": False,
            "enabled": True,
        }
    elif not fac or (not master_ok and not verify_password(password, fac.get("password", ""))):
        raise HTTPException(403, "Invalid facilitator ID or password")
        
    # Disabled accounts cannot log in
    if not fac.get("enabled", True):
        raise HTTPException(403, "Account is disabled")
        
    # LOW-003: Auto-upgrade plaintext passwords to bcrypt on successful login
    # M-5: Audit log when master password bypass is used
    if master_ok:
        print(f"[SECURITY] MASTER_PASSWORD used to bypass facilitator login for fac_id={fac_id_lower}")
        # SEC-4: durable forensic record of break-glass use.
        _audit("master_password_bypass", actor=fac_id_lower,
               details={"endpoint": "facilitator_login"},
               source_ip=(request.client.host if request.client else "unknown"))
    if not master_ok and fac:
        upgraded = maybe_upgrade_password(password, fac.get("password", ""))
        if upgraded:
            fac["password"] = upgraded
            _persist_facilitators()

    # Compute role and allowed tabs
    role = get_role(fac)
    allowed_tabs = get_allowed_tabs(fac)

    _src_ip = request.client.host if request.client else "unknown"
    _audit("facilitator_login", actor=fac["facilitator_id"], details={"role": role}, source_ip=_src_ip)

    # MED-013/014: Issue JWT and store in HttpOnly cookie
    try:
        from auth_jwt import create_facilitator_token, set_session_cookie
        token = create_facilitator_token(
            fac["facilitator_id"], role,
            token_version=get_token_version(fac["facilitator_id"]),
        )
        set_session_cookie(response, token, facilitator_id=fac["facilitator_id"])
    except Exception:
        pass  # If JWT lib unavailable, fall back to header-only auth

    return {
        "status": "success",
        "facilitator_id": fac["facilitator_id"],
        "name": fac["name"],
        "username": fac.get("username", ""),
        "is_admin": is_admin_role(role),  # backward compat
        "role": role,
        "allowed_tabs": allowed_tabs,
        "permissions": fac.get("permissions", {}),
        # First-login policy: default password must be replaced. Suppressed
        # for master-password bypass logins (admin impersonation shouldn't
        # trigger the facilitator's forced change flow).
        "must_change_password": bool(fac.get("must_change_password", False)) and not master_ok,
        # Live-console capabilities (display-safe booleans; the server-side
        # gates on ring-bell/shockwave/bulletin remain authoritative)
        "shockwave_enabled": fac.get("shockwave_enabled", True) is not False,
        "trading_floor_enabled": fac.get("trading_floor_enabled", True) is not False,
        "situation_room_enabled": fac.get("situation_room_enabled", True) is not False,
        "negotiation_rooms_enabled": fac.get("negotiation_rooms_enabled", False) is True,  # Slice 5 (opt-in)
    }


@admin_router.post("/facilitators/change-password", summary="Change facilitator password")
async def facilitator_change_password(
    request: Request,
    body: dict = Body(...),
    _guard: None = Depends(require_facilitator),  # MED-002: must be authenticated
):
    # M-2: Rate-limit this path — unlimited change attempts enable brute-forcing
    _check_rate_limit(request, "fac_change_pw")
    fac_id = body.get("facilitator_id", "").strip()
    old_password = body.get("old_password", "").strip()
    new_password = body.get("new_password", "").strip()
    if not fac_id or not old_password or not new_password:
        raise HTTPException(400, "facilitator_id, old_password, and new_password are required")
    # H-5: Verify caller identity matches the target account.
    # Only super_admins and god_mode may change other facilitators' passwords.
    from auth_jwt import get_facilitator_from_request as _get_caller_id
    _caller_id = _get_caller_id(request)
    if _caller_id and _caller_id != "god_mode":
        _caller_fac = next(
            (f for f in _facilitator_registry if f['facilitator_id'] == _caller_id and not f.get('deleted_at')),
            None,
        )
        _caller_role = get_role(_caller_fac) if _caller_fac else 'anonymous'
        if not is_admin_role(_caller_role) and _caller_id != fac_id:
            raise HTTPException(403, "You can only change your own password")
    # MED-003: Removed contradictory < 3 check — only the >= 8 guard below applies
    fac = next(
        (f for f in _facilitator_registry
         if f["facilitator_id"] == fac_id and not f.get("deleted_at")),
        None,
    )
    if not fac:
        # M-1: Return the same error as a wrong password so callers cannot
        # determine whether a facilitator_id exists via error differentiation.
        raise HTTPException(403, "Current password is incorrect")
    # FIX AUDIT-005: Use configurable master password
    master_ok = verify_master_password(old_password)
    if not verify_password(old_password, fac.get("password", "")) and not master_ok:
        raise HTTPException(403, "Current password is incorrect")
    # M-5: Audit log when master password bypass is used
    if master_ok:
        print(f"[SECURITY] MASTER_PASSWORD used to bypass facilitator password change for fac={fac.get('facilitator_id', 'unknown')}")
        # SEC-4: durable forensic record.
        _audit("master_password_bypass", actor=fac.get("facilitator_id", "unknown"),
               details={"endpoint": "facilitator_change_password"},
               source_ip=(request.client.host if request.client else "unknown"))
    if len(new_password) < 8:
        raise HTTPException(400, "New password must be at least 8 characters")
    fac["password"] = hash_password(new_password)  # LOW-003: always hash
    fac["must_change_password"] = False  # first-login requirement satisfied
    _persist_facilitators()
    return {"status": "success", "message": "Password updated successfully"}


@admin_router.post("/auth/logout", summary="Logout — clear session cookie")
async def facilitator_logout(response: Response):
    """MED-013/014: Clear the HttpOnly session cookie on logout."""
    from auth_jwt import clear_session_cookie
    clear_session_cookie(response)
    return {"status": "logged_out"}


@admin_router.post("/auth/refresh", summary="Refresh JWT session token")
async def refresh_token(request: Request, response: Response, _guard: None = Depends(require_facilitator)):
    """MED-013/014: Issue a fresh JWT if the current token is still valid.
    Client should call this periodically (e.g., on focus) to extend sessions.
    Returns the current role and permissions so the frontend can sync stale cache."""
    from auth_jwt import get_facilitator_from_request, create_facilitator_token, set_session_cookie, decode_facilitator_token, COOKIE_NAME
    fac_id = get_facilitator_from_request(request)
    if not fac_id:
        raise HTTPException(401, "No valid session to refresh")

    # god_mode is a virtual account — not in the registry, role comes from JWT
    if fac_id == "god_mode":
        # C6: god_mode is its own tier — always re-issue with the god_mode role
        # regardless of what an older cookie carried.
        role = "god_mode"
        try:
            token = create_facilitator_token(
                "god_mode", role, token_version=get_token_version("god_mode"),
            )
            set_session_cookie(response, token, facilitator_id="god_mode")
        except Exception:
            pass
        return {
            "status": "refreshed",
            "expires_in_hours": 8,
            "facilitator_id": "god_mode",
            "name": "God Mode Administrator",
            "username": get_virtual_profile("god_mode").get("username", ""),
            "role": role,
            "is_admin": True,
            "allowed_tabs": ["*"],
            "permissions": {},
        }

    # project_admin is a virtual account — like god_mode it is NOT in the
    # registry, so the registry lookup below would 401 it and its session could
    # never be refreshed (it would have to re-login on JWT expiry). Its role is
    # granted only from the signed token (see get_fac_role), so re-issue here.
    if fac_id == "project_admin":
        _pa_fac = {"role": "project_admin"}
        _pa_tabs = get_allowed_tabs(_pa_fac)
        try:
            token = create_facilitator_token(
                "project_admin", "project_admin",
                token_version=get_token_version("project_admin"),
            )
            set_session_cookie(response, token, facilitator_id="project_admin")
        except Exception:
            pass
        return {
            "status": "refreshed",
            "expires_in_hours": 8,
            "facilitator_id": "project_admin",
            "name": "Project Administrator",
            "username": get_virtual_profile("project_admin").get("username", ""),
            "role": "project_admin",
            "is_admin": False,
            "allowed_tabs": _pa_tabs,
            "permissions": {},
        }

    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id and not f.get("deleted_at")), None)
    if not fac:
        raise HTTPException(401, "Facilitator not found")
    role = get_role(fac)
    allowed_tabs = get_allowed_tabs(fac)
    try:
        token = create_facilitator_token(
            fac_id, role, token_version=get_token_version(fac_id),
        )
        set_session_cookie(response, token, facilitator_id=fac_id)
    except Exception:
        pass
    return {
        "status": "refreshed",
        "expires_in_hours": 8,
        "facilitator_id": fac["facilitator_id"],
        "name": fac.get("name", ""),
        "username": fac.get("username", ""),
        "role": role,
        "is_admin": is_admin_role(role),
        "allowed_tabs": allowed_tabs,
        "permissions": fac.get("permissions", {}),
        "shockwave_enabled": fac.get("shockwave_enabled", True) is not False,
        "trading_floor_enabled": fac.get("trading_floor_enabled", True) is not False,
        "situation_room_enabled": fac.get("situation_room_enabled", True) is not False,
        "negotiation_rooms_enabled": fac.get("negotiation_rooms_enabled", False) is True,  # Slice 5 (opt-in)
    }


@admin_router.post("/facilitators/{fac_id}/revoke-sessions", summary="SEC-1: Revoke all sessions for a facilitator")
async def admin_revoke_facilitator_sessions(
    fac_id: str, request: Request, _guard: None = Depends(require_super_admin)
):
    """SEC-1 kill-switch. Increments the facilitator's token_version, instantly
    invalidating every outstanding JWT for that account (including a leaked
    god_mode cookie) on its next request. Super-admin only.

    Use fac_id='god_mode' to revoke the virtual super-admin account; the caller
    will need to log in again afterwards to obtain a fresh token.
    """
    _check_rate_limit(request, "fac_revoke_sessions")
    # Validate target exists (god_mode is a valid virtual target).
    if fac_id != "god_mode":
        target = next(
            (f for f in _facilitator_registry
             if f["facilitator_id"] == fac_id and not f.get("deleted_at")),
            None,
        )
        if not target:
            raise HTTPException(404, f"Facilitator {fac_id} not found")
    new_version = bump_token_version(fac_id)
    from auth_jwt import get_facilitator_from_request as _caller
    _src_ip = request.client.host if request.client else "unknown"
    _audit(
        "facilitator_sessions_revoked",
        actor=_caller(request) or "unknown",
        details={"target": fac_id, "new_token_version": new_version},
        source_ip=_src_ip,
    )
    return {
        "status": "revoked",
        "facilitator_id": fac_id,
        "token_version": new_version,
        "message": "All outstanding sessions for this account have been invalidated.",
    }


@admin_router.post("/master-password", summary="Change the master password (God Mode)")
async def change_master_password(request: Request, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """Runtime master-password change from God Mode.

    Requires the CURRENT master password as confirmation (a hijacked admin
    session alone cannot rotate the break-glass credential). The new value
    is stored as a bcrypt hash in backend/db/master_password.json
    (gitignored), takes effect IMMEDIATELY for every master-bypass surface
    (god_mode login, facilitator bypass, password-change bypass, role
    verification, player master unlock) and survives restarts — the
    override supersedes the MASTER_PASSWORD env/.env value.
    """
    _check_rate_limit(request, "master_pw_change")
    current = (body.get("current_password") or "").strip()
    new = (body.get("new_password") or "").strip()
    if not verify_master_password(current):
        raise HTTPException(403, "Current master password is incorrect")
    if len(new) < 8:
        raise HTTPException(400, "New master password must be at least 8 characters")
    from auth_jwt import get_facilitator_from_request
    actor = get_facilitator_from_request(request) or "god_mode"
    set_master_password(new, changed_by=actor)
    _audit("master_password_changed", actor=actor,
           details={"override_active": True},
           source_ip=(request.client.host if request.client else "unknown"))
    print(f"[SECURITY] Master password rotated by {actor}")
    return {
        "status": "success",
        "note": "Effective immediately on all master-bypass logins and persists across restarts (override supersedes .env).",
    }


@admin_router.post("/facilitators/{fac_id}/reset-password", summary="Admin reset facilitator password")
async def admin_reset_facilitator_password(fac_id: str, request: Request, _guard: None = Depends(require_super_admin)):
    """God Mode one-click password reset. Generates a new random password
    and optionally emails it to the facilitator."""
    # M-2: Rate-limit admin resets to prevent abuse of the super-admin path
    _check_rate_limit(request, "fac_reset_pw")
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")
    # Reset to the fixed default (same policy as creation): the facilitator
    # must set a personal password on their next login.
    new_pw, _new_hash = _generate_temp_password()  # "Muressons123"
    fac["password"] = _new_hash
    fac["must_change_password"] = True
    _persist_facilitators()

    # ── Email the new password to the facilitator ────────────
    email_sent = False
    email_to = fac.get("email", "").strip() or None
    if email_to:
        try:
            from email_service import send_password_reset_email, is_configured
            send_password_reset_email(
                to=email_to,
                facilitator_id=fac_id,
                facilitator_name=fac.get("name", fac_id),
                new_password=new_pw,
            )
            email_sent = is_configured()  # True only if SMTP is actually set up
        except Exception as exc:
            import logging
            logging.getLogger("muressons.admin").warning("Email send failed for %s: %s", fac_id, exc)

    return {
        "status": "success",
        "new_password": new_pw,
        "facilitator_id": fac_id,
        "email_sent": email_sent,
        "email_to": email_to,
    }


@admin_router.put("/facilitators/{fac_id}/cohort-limit", summary="Update facilitator cohort limit")
async def update_cohort_limit(fac_id: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def toggle_facilitator_enabled(fac_id: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def enable_practice_mode(session_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    await _assert_session_ownership(request, session_id)
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
async def disable_practice_mode(session_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    await _assert_session_ownership(request, session_id)
    _practice_mode.pop(session_id, None)
    return {"status": "disabled", "session_id": session_id, "practice_mode": False}


@admin_router.get("/sessions/{session_id}/practice-mode", summary="Get practice mode status")
async def get_practice_mode(session_id: str):
    return {"practice_mode": _practice_mode.get(session_id, False)}


# is_practice_mode imported from admin_shared



# ═════════════════════════════════════════════════════════════════
#  WEBSOCKET CONNECTION MANAGER
# ═════════════════════════════════════════════════════════════════

# audit #17: ConnectionManager + the shared `manager` singleton were extracted to
# admin_ws.py (behaviour unchanged). Re-exported so the websocket endpoints below
# and `from admin_router import manager` (admin_resources.py, router.py) keep
# working unchanged.
from admin_ws import ConnectionManager, manager  # noqa: F401
# ═════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═════════════════════════════════════════════════════════════════

class OverrideRequest(BaseModel):
    override_type: str   # "carbon_tax", "omni_tech_poach", "force_strike"
    parameters: dict = {}


class MessageInjectRequest(BaseModel):
    session_id: str | None = None  # path param already provides this
    message_type: str = ""         # filled from preset if preset_id given
    title: str = Field("", max_length=200)
    body: str = Field("", max_length=5000)
    preset_id: str | None = None


class PlayerRegisterRequest(BaseModel):
    player_name: str = Field(..., max_length=100)
    team_name: str = Field("", max_length=100)

class PlayerInductRequest(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=200)
    programme: str = Field("", max_length=200)  # optional programme/cohort label (parity with bulk upload)
    session_id: str = Field(..., max_length=100)
    assigned_bu: str = Field(..., max_length=100)
    region_id: str = Field("", max_length=50)  # NEW — geographic region for single-BU localisation

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
async def get_decision_configs(_guard: None = Depends(require_facilitator)):
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
async def update_decision_config(req: OverridesUpdateRequest, _guard: None = Depends(require_super_admin)):
    """
    Saves a single field override to decision_overrides.json.
    Updates in-memory dict dicts then flushes to disk.

    GOD-006: The entire read-modify-write is protected by _config_file_lock so
    two simultaneous super_admin edits (e.g. trainer + co-facilitator) cannot
    interleave their reads and corrupt the JSON file.
    """
    async with _config_file_lock:
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

        # Save back to disk (atomic: write tmp then rename)
        tmp_path = str(ROUND_OVERRIDES_FILE) + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(raw_overrides, f, indent=4)
        import os as _os
        _os.replace(tmp_path, ROUND_OVERRIDES_FILE)

    return {"status": "success", "raw_overrides": raw_overrides}


# ═════════════════════════════════════════════════════════════════
#  ROUND PACING — Facilitator-controlled round gating
# ═════════════════════════════════════════════════════════════════

class RoundPacingRequest(BaseModel):
    mode: str = "free"              # "free" | "manual" | "timed"
    interval_seconds: int = 300     # WOW-11: 180-1800 (3-30 minutes). Clamped if out of range.
    scheduled_at: str | None = None # ISO datetime for single scheduled unlock
    schedule: list[str | None] = [] # ISO datetimes for each round (index 0 = round 1)
    # Free-advance auto-release timeout (seconds). 0 = wait indefinitely for all
    # teams (legacy). >0 = release the "waiting for other teams" barrier and
    # auto-commit stragglers this many seconds after a round opens for the cohort.
    free_advance_timeout_seconds: int = 0

    @validator("free_advance_timeout_seconds")
    def clamp_fa_timeout(cls, v):
        if not v or v <= 0:
            return 0
        return max(30, min(7200, int(v)))  # 30s – 2h

    @validator("interval_seconds")
    def clamp_interval(cls, v):
        """WOW-11: Ensure timer stays within 3-30 minute range."""
        if v <= 0:
            return 0  # 0 = immediate unlock, special case
        return max(180, min(1800, v))  # 3 min – 30 min

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

        # C2: re-seed effective climate inputs (global + per-cohort override)
        # into the round flags before the engine reads them (admin advance path).
        try:
            new_global.setdefault("active_event_flags", {})
            seed_effective_flags(player_session_id, new_global["active_event_flags"])
        except Exception:
            pass

        # Post-tick
        post_events = post_tick(
            round_number=current_round,
            global_state=new_global,
            bu_states=new_bus,
            decisions=decisions_raw,
            events=events,
            previous_flags=current_global.get("active_event_flags", {}),
            decision_paradigm=paradigm,
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
        mark_pacing_dirty(session_id)  # Fix #5: share timed unlock across workers

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
        mark_pacing_dirty(session_id)  # Fix #5: share scheduled unlock across workers

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
        "free_advance_timeout_seconds": pacing.get("free_advance_timeout_seconds", 0),
    }


@admin_router.post("/sessions/{session_id}/force-advance", summary="Force-advance the cohort now")
async def force_advance_cohort(session_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    """Facilitator 'Force Advance Now': release the free-advance barrier for the
    whole cohort immediately, regardless of the timer or how many teams have
    committed. Any team still behind is auto-committed with its saved decisions
    on the next dashboard poll (within ~1-2s), so the cohort advances together.
    Sets a one-shot flag on the cohort's pacing; the commit itself runs through
    the normal engine path in the player router."""
    await _assert_session_ownership(request, session_id)
    # Pacing is keyed by the cohort id; resolve it whether called with the cohort
    # id or one of its team sub-session ids.
    info = await db.get_session_info(session_id)
    cohort_id = (info or {}).get("parent_cohort_id") or session_id
    pacing = _get_pacing(cohort_id)
    pacing["_fa_force"] = True
    pacing["_fa_round"] = None
    pacing["_fa_deadline_at"] = None
    return {
        "status": "ok",
        "cohort": cohort_id,
        "message": "Barrier releasing — any uncommitted team will be auto-committed from its saved decisions.",
    }


# ── ESG Leadership Profile weights (facilitator dashboard; no project_admin) ─
class EsgWeightsRequest(BaseModel):
    weights: dict
    reason: str | None = None


def _sanitize_esg_weights(incoming: dict) -> dict:
    """Deep-merge the incoming weights over the canonical defaults, keeping only
    known dimensions/signals and coercing values to finite numbers. Guarantees a
    complete, well-formed rubric regardless of what the client sends."""
    out = {dim: dict(sig) for dim, sig in DEFAULT_ESG_WEIGHTS.items()}
    if isinstance(incoming, dict):
        for dim, sigs in incoming.items():
            if dim not in out or not isinstance(sigs, dict):
                continue
            for k, v in sigs.items():
                if k not in out[dim]:
                    continue
                try:
                    fv = float(v)
                    if fv == fv and fv not in (float("inf"), float("-inf")):  # not NaN/inf
                        # Blend shares are convex weights by contract — clamp to
                        # [0, 1] so a hostile/typo'd payload can't invert or
                        # amplify a dimension (e.g. reputation_blend: 5).
                        if k.endswith("_blend"):
                            fv = min(1.0, max(0.0, fv))
                        out[dim][k] = fv
                except (TypeError, ValueError):
                    continue
    return out


@admin_router.get("/esg-profile-weights", summary="Get ESG Leadership Profile signal weights")
async def get_esg_profile_weights():
    return {"esg_profile_weights": _god_mode_settings.get("esg_profile_weights", DEFAULT_ESG_WEIGHTS),
            "defaults": DEFAULT_ESG_WEIGHTS}


@admin_router.post("/esg-profile-weights", summary="Set ESG Leadership Profile signal weights")
async def set_esg_profile_weights(body: EsgWeightsRequest, request: Request,
                                  _guard: None = Depends(require_sim_manager)):
    """Run-managing facilitators (base and up) tune the ESG assessment rubric —
    the weight each performance signal carries in the five ESG dimensions.
    Moved to the facilitator dashboard: any facilitator may edit; project_admin
    (provisioning-only charter) is rejected by require_sim_manager. Global
    default rubric; unknown keys are dropped, values coerced to numbers, and
    blend shares clamped to [0, 1]."""
    caller = get_fac_role(request)
    clean = _sanitize_esg_weights(body.weights)
    _god_mode_settings["esg_profile_weights"] = clean
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    _audit("esg_profile_weights_updated", details={"_caller_role": caller, "_reason": body.reason})
    return {"status": "ok", "esg_profile_weights": clean}


@admin_router.post("/esg-profile-weights/reset", summary="Reset ESG Profile weights to defaults")
async def reset_esg_profile_weights(request: Request, _guard: None = Depends(require_sim_manager)):
    _god_mode_settings["esg_profile_weights"] = {dim: dict(sig) for dim, sig in DEFAULT_ESG_WEIGHTS.items()}
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    _audit("esg_profile_weights_reset", details={"_caller_role": get_fac_role(request)})
    return {"status": "ok", "esg_profile_weights": DEFAULT_ESG_WEIGHTS}


@admin_router.post("/sessions/{session_id}/pacing", summary="Set round pacing mode")
async def set_pacing(session_id: str, body: RoundPacingRequest, request: Request, _guard: None = Depends(require_sim_manager)):
    await _assert_session_ownership(request, session_id)
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
    # Free-advance auto-release timeout (applies only in "free" mode). Reset the
    # live deadline so it re-arms cleanly against the current round.
    pacing["free_advance_timeout_seconds"] = int(getattr(body, "free_advance_timeout_seconds", 0) or 0)
    pacing["_fa_round"] = None
    pacing["_fa_deadline_at"] = None

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

    mark_pacing_dirty(session_id)  # Fix #5: share the new pacing policy across workers + snapshot

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
async def unlock_next_round(session_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    await _assert_session_ownership(request, session_id)
    pacing = _get_pacing(session_id)
    pacing["unlocked_round"] = pacing["unlocked_round"] + 1
    mark_pacing_dirty(session_id)  # Fix #5: share the unlock across workers + snapshot

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
async def set_session_interventions(
    session_id: str,
    req: SessionInterventionsRequest,
    request: Request = None,
    _guard: None = Depends(require_facilitator),
):
    # Ownership: lead_facilitators may only configure interventions for their own sessions.
    if request is not None:
        await _assert_session_ownership(request, session_id)
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
async def save_decade_plan(session_id: str, req: DecadePlanRequest, _guard: None = Depends(require_sim_manager)):
    ok = await db.save_decade_plan(session_id, req.boardroom_choice, req.decade_forward_plan)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "saved", "boardroom_choice": req.boardroom_choice}

@admin_router.get("/{session_id}/decade-plan", summary="Get decade forward plan")
async def get_decade_plan(session_id: str, _guard: None = Depends(require_facilitator)):
    result = await db.get_decade_plan(session_id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@admin_router.get("/players", summary="List all registered players")
async def list_players(_guard: None = Depends(require_facilitator)):
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
            p_dict.pop("password", None)   # H-2: never expose bcrypt hashes to callers
            p_dict["is_orphan"] = p_dict.get("session_id") not in active_ids
            # ── Resolve display name from multiple sources ──
            # Priority: name (from induct/login) → username (from set-username) → player_name
            if not p_dict.get("name"):
                p_dict["name"] = p_dict.get("username") or p_dict.get("player_name") or ""
            active_players.append(p_dict)
            
    return {"players": active_players}


@admin_router.put("/{session_id}/public-status", summary="Toggle session public visibility")
async def toggle_public_status(session_id: str, req: dict = Body(...), _guard: None = Depends(require_facilitator)):
    is_public = req.get("is_public", False)
    success = await db.set_session_public(session_id, is_public)
    if not success:
        raise HTTPException(404, "Session not found")
    # Broadcast to admin so leaderboards update in real time
    await manager.broadcast_admin({"type": "session_public_toggled", "session_id": session_id, "is_public": is_public})
    return {"status": "updated", "is_public": is_public}


@admin_router.patch("/sessions/{session_id}/metadata", summary="Edit cohort metadata (pre-game only)")
async def patch_session_metadata(
    session_id: str,
    body: dict = Body(...),
    _guard: None = Depends(require_lead_facilitator),
):
    """
    Allows lead_facilitator / super_admin to update a cohort's core metadata
    before the game has begun (round == 1 AND no players inducted).
    """
    # ── Guard: only allow edits before the game starts ──────────────
    from database_memory import _sessions
    session = _sessions.get(session_id)
    if session is None:
        session = await db.get_session_info(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    round_num = session.get("round_number", 1)
    inducted = session.get("allowed_player_ids", [])
    if round_num > 1:
        raise HTTPException(409, "Cannot edit cohort: game has already begun (round > 1)")
    if inducted and len(inducted) > 0:
        raise HTTPException(409, "Cannot edit cohort: players have already been inducted")

    # ── Allowed editable fields ──────────────────────────────────────
    EDITABLE = {
        "cohort_name", "facilitator_id", "decision_paradigm", "ending_pathway",
        "start_date", "end_date", "created_by", "created_when",
        "simulation_mode", "industry_vertical", "region_id",
        "currency_symbol", "scenario_preset", "experience_level", "difficulty_tier",
    }
    updates = {k: v for k, v in body.items() if k in EDITABLE and v is not None}
    if not updates:
        return {"status": "no_changes"}


    success = await db.update_session_metadata(session_id, updates)
    if not success:
        raise HTTPException(404, "Session not found")


    # Broadcast so leaderboards refresh
    await manager.broadcast_admin({
        "type": "sessions_refresh",
        "session_id": session_id,
        "changed": list(updates.keys()),
    })
    return {"status": "updated", "session_id": session_id, "updated_fields": list(updates.keys())}


class MaterialityDictionaryOverrideRequest(BaseModel):
    issues: list[dict]
    interdependencies: list[dict]
    consultant_fee_usd: Optional[int] = 1500000

@admin_router.put("/{session_id}/materiality-dictionary", summary="Override the full materiality dictionary for a cohort")
async def override_materiality_dictionary(
    session_id: str,
    req: MaterialityDictionaryOverrideRequest,
    request: Request,
    _guard: None = Depends(require_super_admin),  # Materiality Matrix editing is super-admin only
):
    """
    Saves a complete sandboxed copy of the materiality dictionary for this session.
    Overrides global settings dynamically for this cohort.
    """
    await _assert_session_ownership(request, session_id)
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
async def revert_materiality_dictionary(
    session_id: str,
    request: Request,
    _guard: None = Depends(require_super_admin),  # Materiality Matrix editing is super-admin only
):
    """
    Removes the sandbox dictionary, reverting the cohort to God Mode defaults.
    """
    await _assert_session_ownership(request, session_id)
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
async def register_player(req: PlayerRegisterRequest, _guard: None = Depends(require_sim_manager)):
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
async def induct_player(req: PlayerInductRequest, _guard: None = Depends(require_sim_manager)):
    global _next_player_id

    # Enforce the per-cohort roster cap (single resolver, clamp-on-read).
    from player_capacity import resolve_max_players, capacity_error
    _cap = resolve_max_players(get_effective_settings(req.session_id))
    existing_in_cohort = [p for p in _player_registry if p.get("session_id") == req.session_id]
    if len(existing_in_cohort) >= _cap:
        raise HTTPException(status_code=400, detail=capacity_error(_cap))

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
    
    # SEC-3: random per-player temp password (was hardcoded "Welcome123").
    # Shown once to the facilitator via registered_players.plaintext_password;
    # must_change_password forces a reset on first login.
    generated_password, generated_password_hash = _generate_temp_password()

    # Fetch cohort_name from session so login response can return it
    _cohort_name = ""
    try:
        _sess_info = await db.get_session_info(req.session_id)
        if _sess_info:
            _cohort_name = _sess_info.get("cohort_name", "")
    except Exception:
        pass

    player = {
        "player_id": generated_id,
        "name": req.name,
        "email": req.email,
        "programme": req.programme,
        "assigned_bu": req.assigned_bu,
        "region_id": req.region_id,
        "session_id": req.session_id,
        "cohort_name": _cohort_name,
        "password": generated_password_hash,  # L-4: store bcrypt hash, never plaintext
        "plaintext_password": generated_password,  # revealable temp credential; erased on personal change
        "must_change_password": True,  # Force player to change on first login
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "playing",
    }

    _player_registry.append(player)

    # Register the player ID in the session's allowed list and persist to disk
    try:
        sess = await db.get_session_info(req.session_id)
        if sess:
            allowed = sess.get("allowed_player_ids", [])
            if generated_id not in allowed:
                allowed.append(generated_id)
            # Also persist in registered_players so login survives server restart
            registered = sess.get("registered_players") or []
            if not any(rp["player_id"] == generated_id for rp in registered):
                display_entry = player.copy()
                display_entry["plaintext_password"] = generated_password
                registered.append(display_entry)
            # Fix #6: single durable write through the db interface (Postgres
            # metadata + mirror) instead of mutating the memory dict directly.
            await db.update_session_metadata(req.session_id, {
                "allowed_player_ids": allowed,
                "registered_players": registered,
            })
    except Exception:
        pass  # Non-critical

    # Broadcast to admin
    await manager.broadcast_admin({
        "type": "player_registered",
        "player": player,
    })

    # L-4: Return plaintext password once for admin to distribute — hash is stored, not this
    return {**player, "password": generated_password}




@admin_router.post("/players/{player_id}/assign", summary="Assign a player to a session")
async def assign_player_to_session(player_id: str, session_id: str, _guard: None = Depends(require_sim_manager)):
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
async def remove_player(player_id: str, _guard: None = Depends(require_sim_manager)):
    global _player_registry
    before = len(_player_registry)
    _player_registry[:] = [p for p in _player_registry if p["player_id"] != player_id]
    if len(_player_registry) == before:
        raise HTTPException(404, f"Player {player_id} not found")
    await manager.broadcast_admin({
        "type": "player_removed",
        "player_id": player_id,
    })
    return {"status": "removed", "player_id": player_id}


@admin_router.delete("/players", summary="Clear all registered players")
async def clear_all_players(_guard: None = Depends(require_super_admin)):
    global _player_registry, _next_player_id
    count = len(_player_registry)
    _player_registry[:] = []
    _next_player_id = 1
    await manager.broadcast_admin({"type": "players_cleared"})
    return {"status": "cleared", "players_removed": count}




# ─────────────────────────────────────────────────────────────────────────────
# CASCADE DELETE HELPER
# Centralises full cleanup of one cohort (session) and everything under it.
# Both the DELETE /sessions/{id} endpoint and the facilitator-delete cascade
# call this so the logic is never duplicated.
# ─────────────────────────────────────────────────────────────────────────────

async def _cascade_delete_session(session_id: str, hard: bool = False) -> dict:
    """Full cascade delete/soft-delete of one cohort and every child session.

    Soft delete (hard=False):
      - Stamps deleted_at on the cohort and each child player session in DB.
      - Marks matching _player_registry entries with deleted_at.
      - All in-memory admin data is LEFT in place (it is keyed by session_id
        and the session still exists in the DB; it will be repopulated on
        next access if the session is un-deleted).

    Hard delete (hard=True):
      - Permanently removes cohort + child sessions from DB (with explicit
        child-table cascade and immutability trigger disable via db.delete_session).
      - Removes ALL matching _player_registry entries.
      - Purges all in-memory admin data for the cohort and children:
          _session_messages, _session_interventions, _practice_mode,
          _round_pacing, _facilitator_notes, _student_bonuses,
          _peer_evaluations, _annotations, cohort_settings,
          _cohort_marketplaces, _session_players.

    Returns {"sessions_deleted": N, "players_removed": M}.
    """
    from router import _session_players

    # Resolve all session IDs to clean up (parent + children)
    children = await db.get_child_sessions(session_id)
    child_ids = [c["session_id"] for c in children]
    all_ids = [session_id] + child_ids

    now_str = datetime.now(timezone.utc).isoformat()
    sessions_deleted = 0
    players_removed = 0

    # ── DB deletions ──────────────────────────────────────────────────────
    # Delete children first (they reference parent via parent_cohort_id)
    for cid in child_ids:
        ok = await db.delete_session(cid, hard=hard)
        if ok:
            sessions_deleted += 1

    # Delete the parent cohort itself
    ok = await db.delete_session(session_id, hard=hard)
    if ok:
        sessions_deleted += 1

    # ── Player registry ───────────────────────────────────────────────────
    global _player_registry
    if hard:
        before = len(_player_registry)
        _player_registry[:] = [
            p for p in _player_registry
            if p.get("session_id") not in all_ids
        ]
        players_removed = before - len(_player_registry)
    else:
        for p in _player_registry:
            if p.get("session_id") in all_ids and not p.get("deleted_at"):
                p["deleted_at"] = now_str
                players_removed += 1

    # ── In-memory admin data (hard delete only) ───────────────────────────
    if hard:
        def _purge(sid):
            _session_messages.pop(sid, None)
            _session_interventions.pop(sid, None)
            _practice_mode.pop(sid, None)
            _round_pacing.pop(sid, None)
            cohort_settings.pop(sid, None)
            _cohort_marketplaces.pop(sid, None)
            _session_players.pop(sid, None)
            # These stores are defined later in the file; use globals() to
            # avoid forward-reference errors at module parse time.
            g = globals()
            for store_name in (
                "_facilitator_notes", "_student_bonuses",
                "_peer_evaluations", "_annotations",
            ):
                store = g.get(store_name)
                if isinstance(store, dict):
                    store.pop(sid, None)

        for sid in all_ids:
            _purge(sid)

        # QA-2026-07-16 #14: also drop the session's SHARED coordination rows
        # (pacing + overrides) so they do not accumulate in Postgres forever and
        # cannot be re-hydrated onto a worker after the session is gone.
        try:
            import coordination_store as _cs
            for sid in all_ids:
                await _cs.delete_pacing(sid)
                await _cs.delete_session_override(sid)
        except Exception:
            pass

    # Persist the cohort-settings removals to the durable volume so a deleted
    # cohort's overrides don't resurrect from the last snapshot on restart.
    mark_cohort_settings_dirty()

    return {"sessions_deleted": sessions_deleted, "players_removed": players_removed}


@admin_router.delete("/sessions/{session_id}", summary="Delete a session/cohort")
async def delete_session(
    session_id: str,
    hard: bool = False,
    request: Request = None,
    _guard: None = Depends(require_super_admin),
):
    """Remove a cohort and all associated data.

    Soft delete (default, hard=False):
      Marks the cohort and its child player-sessions as deleted in the DB.
      Player registry entries are stamped with deleted_at.
      In-memory admin data is preserved (session still exists in DB).

    Hard delete (hard=True):
      Permanently removes the cohort, all child player-sessions, all DB rows
      (global_round_states, bu_round_states, decision_audit_log), all player
      registry entries, and all in-memory admin data for those sessions.

    Access:
      super_admin / god_mode: may delete any cohort.
      lead_facilitator: may only delete cohorts they own.
    """
    # Lead facilitators may only delete their own cohorts
    fac_role = get_fac_role(request) if request else "super_admin"
    if ROLE_HIERARCHY.get(fac_role, 0) < ROLE_HIERARCHY.get("super_admin", 3):
        session_info = await db.get_session_info(session_id)
        if session_info:
            from auth_jwt import get_facilitator_from_request
            caller_id = get_facilitator_from_request(request) if request else None
            if session_info.get("facilitator_id") != caller_id:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: you may only delete your own cohorts",
                )

    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(404, "Session not found")

    result = await _cascade_delete_session(session_id, hard=hard)

    await manager.broadcast_admin({"type": "session_deleted", "session_id": session_id})
    return {
        "status": "deleted",
        "session_id": session_id,
        "hard": hard,
        "sessions_deleted": result["sessions_deleted"],
        "players_removed": result["players_removed"],
    }


@admin_router.delete("/players/orphans", summary="Clear orphaned players whose session no longer exists")
async def clear_orphan_players(_guard: None = Depends(require_super_admin)):
    """Remove all players whose session_id doesn't match any active session."""
    global _player_registry
    active_sessions = await db.fetch_all_sessions()
    active_ids = {s["session_id"] for s in active_sessions}
    before = len(_player_registry)
    _player_registry[:] = [p for p in _player_registry if p.get("session_id") in active_ids or p.get("session_id") == ""]
    removed = before - len(_player_registry)
    return {"status": "cleared", "orphans_removed": removed}


@admin_router.put("/players/set-password", summary="Set or update a player's password")
async def set_player_password(body: dict = Body(...), _guard: None = Depends(require_sim_manager)):
    """Fallback for setting a player password when it's generated client-side."""
    player_id = body.get("player_id")
    password = body.get("password")
    if not player_id or not password:
        raise HTTPException(400, "player_id and password are required")
    
    player = next((p for p in _player_registry if p["player_id"] == player_id), None)
    hashed = hash_password(password)  # L-4: always store bcrypt hash
    if player:
        player["password"] = hashed
    else:
        # Create a minimal registry entry
        _player_registry.append({
            "player_id": player_id,
            "name": "",
            "email": "",
            "assigned_bu": "",
            "session_id": "",
            "password": hashed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "id_generated",
        })
    return {"status": "success"}


@admin_router.post("/players/{player_id}/reset-password", summary="Reset a player's password to a new random temp password")
async def reset_player_password(player_id: str, _guard: None = Depends(require_sim_manager)):
    """
    Generates a new random temp password for a player and returns the plaintext to the facilitator.
    Sets must_change_password=True so the player is required to change it on first login.
    Updates both the _player_registry and the session's registered_players so the
    facilitator panel immediately shows the new password.
    """
    player_id_upper = player_id.strip().upper()

    # Find in registry
    player = next((p for p in _player_registry if p["player_id"] == player_id_upper), None)

    # Search session registered_players if not in registry
    if not player:
        all_sessions = await db.fetch_all_sessions()
        for sess in all_sessions:
            for rp in sess.get("registered_players", []):
                if rp.get("player_id") == player_id_upper:
                    player = rp
                    if not any(p["player_id"] == player_id_upper for p in _player_registry):
                        _player_registry.append(rp)
                    break
            if player:
                break

    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id_upper} not found.")

    # Generate a new random temp password
    new_plaintext, new_hash = _generate_temp_password()
    player["password"] = new_hash
    player["must_change_password"] = True

    # QA-2026-07-16 #4: write the new hash DURABLY through the db interface for
    # every session whose registered_players names this player. The old path
    # mutated throwaway copies from fetch_all_sessions() and called _dm._persist()
    # — a no-op against Postgres — so a reset worked on one worker and was
    # rejected on the rest / after a restart.
    try:
        all_sess = await db.fetch_all_sessions()
        for sess in all_sess:
            reg = list(sess.get("registered_players", []) or [])
            touched = False
            for rp in reg:
                if rp.get("player_id") == player_id_upper:
                    rp["password"] = new_hash
                    rp["must_change_password"] = True
                    rp["plaintext_password"] = new_plaintext  # facilitator display
                    touched = True
            if touched:
                await db.update_session_metadata(sess["session_id"], {"registered_players": reg})
    except Exception:
        pass  # Non-critical — the in-memory _player_registry entry is already updated

    return {
        "status": "success",
        "player_id": player_id_upper,
        "new_password": new_plaintext,
        "message": f"Password reset for {player_id_upper}. Share the new password with the player."
    }


# ═════════════════════════════════════════════════════════════════
#  SWIPE FILE PRESETS
# ═════════════════════════════════════════════════════════════════

SWIPE_FILE_PRESETS = [
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

OVERRIDE_HANDLERS = {}


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
async def list_sessions(facilitator_id: Optional[str] = None, _guard: None = Depends(require_facilitator)):
    """Returns all sessions with their latest state for the leaderboard."""
    sessions = await db.fetch_all_sessions()

    if facilitator_id:
        sessions = [
            s for s in sessions
            if s.get("facilitator_id") == facilitator_id
        ]

    # Enrich each cohort with its EFFECTIVE climate settings (global default +
    # any per-cohort override) so UI surfaces like the Cohort Summary hover can
    # display the climate branch, carbon fee, hostility and Scope-3 without a
    # second round-trip. Operates on shallow COPIES so the shared in-memory
    # session store is never mutated; additive (setdefault) so an explicit
    # per-session value is never clobbered.
    enriched = []
    for _s in sessions:
        _e = dict(_s)
        try:
            _eff = get_effective_settings(_e.get("session_id"))
            _e.setdefault("climate_paradigm", resolve_climate_paradigm(_eff))
            for _k in ("global_carbon_fee", "market_hostility_index", "scope_3_threshold"):
                _e.setdefault(_k, _eff.get(_k))
        except Exception:
            pass
        enriched.append(_e)

    return {"sessions": enriched}




@admin_router.post(
    "/{session_id}/generate-player",
    summary="Generate a new allowed player ID and password",
)
async def generate_player_id(session_id: str, _guard: None = Depends(require_sim_manager)):
    # Enforce the per-cohort roster cap at ID generation time.
    from player_capacity import resolve_max_players, capacity_error
    sess_check = await db.get_session_info(session_id)
    if not sess_check:
        raise HTTPException(status_code=404, detail="Session not found.")
    _cap = resolve_max_players(get_effective_settings(session_id))
    existing_count = len(sess_check.get("registered_players", []))
    if existing_count >= _cap:
        raise HTTPException(status_code=400, detail=capacity_error(_cap))

    player_id = await db.generate_player_id(session_id)
    if not player_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # SEC-3: random per-player temp password (was hardcoded "Welcome123").
    generated_password, _generated_password_hash = _generate_temp_password()


    player_entry = {
        "player_id": player_id,
        "name": "",
        "email": "",
        "programme": "",
        "assigned_bu": "",
        "session_id": session_id,
        "password": hash_password(generated_password),  # L-4: store bcrypt hash
        "plaintext_password": generated_password,  # revealable temp credential; erased on personal change
        "must_change_password": True,  # Force player to change on first login
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "id_generated",
    }

    # Register in player registry for password validation
    global _player_registry
    _player_registry.append(player_entry.copy())

    # QA-2026-07-16 #4: persist the credential DURABLY through the db interface
    # (Postgres metadata + mirror), not just into the throwaway dict returned by
    # get_session_info. Previously the bcrypt hash lived only in this process's
    # _player_registry, so after a restart / on another worker join_session found
    # no record and the password check was silently skipped.
    sess = await db.get_session_info(session_id)
    registered = list((sess or {}).get("registered_players", []) or [])
    if not any(rp.get("player_id") == player_id for rp in registered):
        display_entry = player_entry.copy()
        display_entry["plaintext_password"] = generated_password  # for facilitator display
        registered.append(display_entry)
    await db.update_session_metadata(session_id, {"registered_players": registered})

    # Return plaintext password once for admin to distribute — hash is stored
    return {"status": "success", "player_id": player_id, "password": generated_password}


async def _create_players_bulk(session_id: str, players: list[dict]) -> list[dict]:
    """Shared bulk player-creation path (used by the bulk-upload endpoints).

    `players` is parser output (player_bulk_excel.parse_player_sheet): dicts with
    name / email / programme / assigned_bu / region_id. Each is created with a
    per-player temp password, writing the SAME record shape as induct_player and
    generate_player_id (kept congruent by test_player_record_shape), and persisted
    durably (registry + registered_players via the db interface) so the credential
    works across workers / Postgres. Returns the created credentials for one-time
    facilitator display.

    Capacity + ownership are enforced by the CALLER before this runs, so the
    endpoint boundary stays all-or-nothing.
    """
    global _next_player_id
    _cohort_name = ""
    try:
        _sess_info = await db.get_session_info(session_id)
        if _sess_info:
            _cohort_name = _sess_info.get("cohort_name", "")
    except Exception:
        pass

    created: list[dict] = []
    new_records: list[dict] = []
    for p in players:
        pid = f"MUR-{_next_player_id:03d}"
        _next_player_id += 1
        temp, temp_hash = _generate_temp_password()
        player = {
            "player_id": pid,
            "name": p.get("name", ""),
            "email": p.get("email", ""),
            "programme": p.get("programme", ""),
            "assigned_bu": p.get("assigned_bu", ""),
            "region_id": p.get("region_id", ""),
            "session_id": session_id,
            "cohort_name": _cohort_name,
            "password": temp_hash,  # L-4: store bcrypt hash, never plaintext
            "plaintext_password": temp,  # revealable temp credential; erased on personal change
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "playing",
        }
        _player_registry.append(player)
        new_records.append(player)
        created.append({
            "player_id": pid,
            "name": player["name"],
            "email": player["email"],
            "programme": player["programme"],
            "temp_password": temp,
        })

    # Durable persist: extend allowed_player_ids + registered_players in one write.
    try:
        sess = await db.get_session_info(session_id)
        if sess is not None:
            allowed = list(sess.get("allowed_player_ids", []) or [])
            registered = list(sess.get("registered_players", []) or [])
            existing_ids = {rp.get("player_id") for rp in registered}
            for rec in new_records:
                if rec["player_id"] not in allowed:
                    allowed.append(rec["player_id"])
                if rec["player_id"] not in existing_ids:
                    registered.append(rec.copy())
            await db.update_session_metadata(session_id, {
                "allowed_player_ids": allowed,
                "registered_players": registered,
            })
    except Exception:
        pass
    return created


# ── Slice 4: single-cohort player bulk upload + master provisioning ──────────
# Wires the already-tested parsers in player_bulk_excel over the shared
# _create_players_bulk path. Two shapes: a facilitator uploads a flat roster for
# ONE cohort they run; a registry admin uploads a master workbook that
# provisions facilitators, cohorts and players together, all-or-nothing.

async def _cohort_remaining_capacity(session_id: str):
    """(session_info, cap, remaining) for a cohort, or raise 404.

    `remaining` is the effective cap minus the players already registered, so the
    parser rejects an oversized sheet BEFORE any player is created."""
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
    from player_capacity import resolve_max_players
    cap = resolve_max_players(get_effective_settings(session_id))
    used = len(sess.get("registered_players", []) or [])
    return sess, cap, max(0, cap - used)


@admin_router.get(
    "/players/bulk-template",
    summary="Download the single-cohort player roster .xlsx template",
)
async def players_bulk_template(_guard: None = Depends(require_facilitator)):
    import os, tempfile
    from fastapi.responses import FileResponse
    from player_bulk_excel import build_player_template
    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix="player_template_")
    os.close(fd)
    build_player_template(path)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="player_roster_template.xlsx",
    )


@admin_router.post(
    "/{session_id}/players/bulk-preview",
    summary="Validate a player roster sheet WITHOUT creating anything",
)
async def players_bulk_preview(
    session_id: str,
    file: UploadFile = File(...),
    _guard: None = Depends(require_sim_manager),
):
    """Parse-only: every error at once, nothing created. A deliberately distinct
    route from bulk-upload so an older backend answers 404/405 and the frontend
    falls back safely instead of accidentally creating players."""
    from player_bulk_excel import parse_player_sheet, BulkPlayerError
    _sess, cap, remaining = await _cohort_remaining_capacity(session_id)
    raw = await file.read()
    try:
        players = parse_player_sheet(raw, limit=remaining)
    except BulkPlayerError as e:
        return {"ok": False, "errors": e.errors, "total": 0,
                "remaining": remaining, "max_players": cap}
    return {
        "ok": True,
        "total": len(players),
        "remaining": remaining,
        "max_players": cap,
        "players": [
            {k: p.get(k, "") for k in ("name", "email", "programme", "assigned_bu", "region_id")}
            for p in players
        ],
        "note": "Nothing was created. POST the same file to /players/bulk-upload to create these players.",
    }


@admin_router.post(
    "/{session_id}/players/bulk-upload",
    summary="Create players in one cohort from an .xlsx roster (all-or-nothing)",
)
async def players_bulk_upload(
    session_id: str,
    file: UploadFile = File(...),
    _guard: None = Depends(require_sim_manager),
):
    """All-or-nothing: the parser validates the whole sheet (shape, duplicates,
    capacity) before a single player is created, so a rejected file leaves the
    roster untouched. Returns the created credentials for one-time display."""
    from player_bulk_excel import parse_player_sheet, BulkPlayerError
    _sess, cap, remaining = await _cohort_remaining_capacity(session_id)
    raw = await file.read()
    try:
        players = parse_player_sheet(raw, limit=remaining)
    except BulkPlayerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    created = await _create_players_bulk(session_id, players)
    return {"ok": True, "created": created, "total": len(created), "max_players": cap}


@admin_router.get(
    "/provisioning/master-template",
    summary="Download the three-sheet master provisioning .xlsx template",
)
async def provisioning_master_template(_guard: None = Depends(require_registry_admin)):
    import os, tempfile
    from fastapi.responses import FileResponse
    from player_bulk_excel import build_master_template
    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix="master_template_")
    os.close(fd)
    build_master_template(path)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="master_provisioning_template.xlsx",
    )


async def _validate_master_workbook(raw: bytes, request: Request) -> dict:
    """Parse + the endpoint-level checks the parser cannot do (existing-facilitator
    resolution, cohort-name collisions), returning the fully-resolved plan or
    raising HTTPException(400) with everything wrong at once. Creates NOTHING, so
    preview and upload run the IDENTICAL gate."""
    from player_bulk_excel import parse_master_workbook, BulkPlayerError
    try:
        plan = parse_master_workbook(raw)
    except BulkPlayerError as e:
        raise HTTPException(status_code=400, detail=str(e))

    errors: list = []

    # A cohort may cite an EXISTING facilitator id instead of a workbook ref; the
    # parser flagged those (facilitator_is_new=False) but cannot know the
    # registry — verify here so a dangling id fails before any write.
    existing_ids = {f.get("facilitator_id") for f in _facilitator_registry}
    for c in plan["cohorts"]:
        if not c["facilitator_is_new"] and c["facilitator_ref"] not in existing_ids:
            errors.append(
                f"Cohorts row {c['row']}: facilitator_ref '{c['facilitator_ref']}' "
                f"is neither a Facilitators.ref in this workbook nor an existing facilitator id."
            )

    # Cohort names are globally unique among top-level sessions; a collision would
    # make db.create_session raise mid-import, so catch it up front to keep the
    # whole upload all-or-nothing.
    try:
        existing_names = {
            (s.get("cohort_name") or "").strip().lower()
            for s in (await db.fetch_all_sessions() or [])
            if not s.get("parent_cohort_id")
        }
    except Exception:
        existing_names = set()
    seen_names: set = set()
    for c in plan["cohorts"]:
        nm = c["cohort_name"].strip().lower()
        if nm in existing_names or nm in seen_names:
            errors.append(f"Cohorts row {c['row']}: a cohort named '{c['cohort_name']}' already exists.")
        seen_names.add(nm)

    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    return plan


@admin_router.post(
    "/provisioning/master-preview",
    summary="Validate a master workbook WITHOUT creating anything",
)
async def provisioning_master_preview(
    request: Request,
    file: UploadFile = File(...),
    _guard: None = Depends(require_registry_admin),
):
    raw = await file.read()
    plan = await _validate_master_workbook(raw, request)
    return {
        "ok": True,
        "totals": {
            "facilitators": len(plan["facilitators"]),
            "cohorts": len(plan["cohorts"]),
            "players": len(plan["players"]),
        },
        "facilitators": [
            {"ref": f["ref"], "name": f["name"], "role": f["role"]} for f in plan["facilitators"]
        ],
        "cohorts": [
            {"ref": c["ref"], "cohort_name": c["cohort_name"],
             "max_players": c["max_players"], "player_count": c.get("player_count", 0)}
            for c in plan["cohorts"]
        ],
        "note": "Nothing was created. POST the same file to /provisioning/master-upload to provision everything.",
    }


@admin_router.post(
    "/provisioning/master-upload",
    summary="Provision facilitators + cohorts + players from a master workbook (all-or-nothing)",
)
async def provisioning_master_upload(
    request: Request,
    file: UploadFile = File(...),
    _guard: None = Depends(require_registry_admin),
):
    """Provision an entire programme in one atomic upload. The plan is validated
    in full (parser + existing-facilitator resolution + name-collision) before a
    single record is written, so a workbook that fails validation leaves NO
    facilitator, NO cohort and NO player behind."""
    from player_capacity import clamp_max_players
    raw = await file.read()
    plan = await _validate_master_workbook(raw, request)

    # 1) Facilitators — a role the caller may not grant is downgraded to
    #    'facilitator' (never an error), matching the workbook contract.
    caller_role = get_fac_role(request)
    grantable = assignable_roles_for(caller_role)
    ref_to_fac_id: dict = {}
    created_facilitators: list = []
    for f in plan["facilitators"]:
        role = f["role"] if f["role"] in grantable else "facilitator"
        req = FacilitatorCreateRequest(
            name=f["name"],
            email=f["email"] or None,
            contact_number=f["contact_number"] or None,
            programme=f["programme"] or None,
            max_cohorts=f["max_cohorts"],
            role=role,
        )
        res = await create_facilitator(req, request)
        ref_to_fac_id[f["ref"].strip().lower()] = res["facilitator_id"]
        created_facilitators.append({
            "ref": f["ref"], "facilitator_id": res["facilitator_id"],
            "name": res.get("name", f["name"]), "role": res.get("role", role),
            "one_time_password": res.get("one_time_password", ""),
        })

    # 2) Cohorts — resolve the facilitator (new ref or existing id), seed the
    #    session (round-1 state) and record max_players as a per-cohort override
    #    so the leaderboard + capacity checks read it back through
    #    get_effective_settings.
    ref_to_session_id: dict = {}
    created_cohorts: list = []
    for c in plan["cohorts"]:
        fref = c["facilitator_ref"].strip().lower()
        fac_id = ref_to_fac_id.get(fref, c["facilitator_ref"])  # existing id passes through
        result = await db.create_session(
            c["cohort_name"],
            fac_id,
            decision_paradigm=c["decision_paradigm"],
            simulation_mode=c["simulation_mode"],
            industry_vertical=c["industry_vertical"] or None,
            region_id=c["region_id"] or None,
        )
        sid = str(result["session_id"])
        ref_to_session_id[c["ref"].strip().lower()] = sid
        cap = clamp_max_players(c["max_players"])
        cohort_settings.setdefault(sid, {})["max_players"] = cap
        created_cohorts.append({
            "ref": c["ref"], "session_id": sid, "cohort_name": c["cohort_name"],
            "facilitator_id": fac_id, "max_players": cap,
        })
    mark_cohort_settings_dirty()

    # 3) Players — grouped per cohort, created through the shared durable path.
    from collections import defaultdict
    by_cohort: dict = defaultdict(list)
    for p in plan["players"]:
        by_cohort[p["cohort_ref"].strip().lower()].append(p)
    created_players: list = []
    for cref, group in by_cohort.items():
        sid = ref_to_session_id.get(cref)
        if not sid:
            continue  # unreachable: parser guarantees every player ref resolves
        created_players.extend(await _create_players_bulk(sid, group))

    return {
        "ok": True,
        "totals": {
            "facilitators": len(created_facilitators),
            "cohorts": len(created_cohorts),
            "players": len(created_players),
        },
        "facilitators": created_facilitators,
        "cohorts": created_cohorts,
        "players": created_players,
    }


# Facilitator-safe roster projection allow-list. An allow-list (not a deny-list)
# means a field added to the player record later cannot leak by default.
_ROSTER_PUBLIC_FIELDS = (
    "player_id", "name", "username", "email", "programme",
    "assigned_bu", "status", "created_at",
)
# `temp_password` (the live temp credential) and `must_change_password` are
# added by _roster_view; the bcrypt hash ("password") and "plaintext_password"
# are NEVER projected.


@admin_router.get(
    "/leaderboard",
    summary="Get leaderboard data for all active sessions",
)
async def get_leaderboard(facilitator_id: Optional[str] = None, _guard: None = Depends(require_facilitator)):
    """
    Returns computed leaderboard metrics for each player session:
    terminal value projection, total cash, synergy, risk heatmap,
    talent flight risk, and individual player scores.
    """
    from player_capacity import resolve_max_players
    sessions = await db.fetch_all_sessions()
    leaderboard = []

    def _roster_view(rp: dict) -> dict:
        """Facilitator-safe projection of a registered_players entry.

        Carries `temp_password` (the generated credential) for as long as it is
        still the live one (must_change_password) so the facilitator can read it
        out at any point during setup — it disappears the moment the player sets
        a personal password. The bcrypt hash is NEVER serialized (H-2)."""
        active = bool(rp.get("must_change_password", False))
        out = {k: rp.get(k, "") for k in _ROSTER_PUBLIC_FIELDS}
        out["must_change_password"] = active
        out["temp_password"] = (rp.get("plaintext_password") or "") if active else ""
        return out

    # Build player name lookup from registry
    player_name_map = {}
    for p in _player_registry:
        pid = p.get("player_id", "")
        name = p.get("name") or p.get("username") or p.get("player_name") or ""
        if pid and name:
            player_name_map[pid] = name

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

        flags = gs.get("active_event_flags", {})
        active_traps = []
        if flags.get("cfo_austerity_active"): active_traps.append("🛑 Austerity")
        if flags.get("supplier_defection", {}).get("active"): active_traps.append("🏭 Defection")
        if flags.get("green_premium_squeeze", {}).get("active"): active_traps.append("📉 Squeeze")
        if flags.get("regulatory_ratchet", {}).get("active"): active_traps.append("⚖️ Ratchet")

        # ── Individual player score fields ───────────────────────
        stakeholder_accuracy = gs.get("stakeholder_map_accuracy", 0)
        stakeholder_completed = gs.get("stakeholder_map_completed", False)
        learning_bonuses = gs.get("learning_bonuses_awarded", {})
        learning_bonus_count = len(learning_bonuses)
        learning_bonus_total = sum(
            entry.get("points", 0) if isinstance(entry, dict) else 0
            for entry in learning_bonuses.values()
        )
        csrd_completed = gs.get("csrd_completed", False)
        materiality_accuracy = gs.get("materiality_full_accuracy", 0)

        # Resolve player name from registry
        player_name = ""
        if player_id:
            player_name = player_name_map.get(player_id, "")

        leaderboard.append({
            "sparkline": sparkline_data,
            "session_id": sid,
            "short_code": sess.get("short_code"),
            "cohort_name": sess.get("cohort_name", "Unknown"),
            "facilitator_id": sess.get("facilitator_id"),
            "player_id": player_id,
            "player_name": player_name,
            "parent_cohort_id": sess.get("parent_cohort_id"),
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
            "active_flags": list(flags.keys()),
            "active_traps": active_traps,
            "shadow_board_archetype": flags.get("shadow_board_archetype"),
            "shadow_board_rejection": flags.get("shadow_board_rejection"),
            # Individual player scores
            "stakeholder_map_accuracy": round(stakeholder_accuracy, 1),
            "stakeholder_map_completed": stakeholder_completed,
            "learning_bonus_count": learning_bonus_count,
            "learning_bonus_total": learning_bonus_total,
            "csrd_completed": csrd_completed,
            "materiality_accuracy": round(materiality_accuracy, 1),
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
            "max_unlocked_round": sess.get("max_unlocked_round", SIM_ROUNDS),
            "start_time": sess.get("start_time"),
            # Roster data for the Player Registry panel: generated ids + the
            # live temp credential (facilitator-safe projection; no hashes).
            # Without these the frontend rebuilt its credential rows as
            # "— (reset to reveal)" on every refresh even though the password
            # was generated server-side and is still the active one.
            "allowed_player_ids": sess.get("allowed_player_ids", []),
            # Slice 4: report the EFFECTIVE cap (global default + per-cohort
            # override, clamped to the ceiling) rather than the raw stored value,
            # which is None for cohorts that never set it and un-clamped for ones
            # persisted by an older build. Mirrors the resolver the two capacity
            # enforcement sites (generate_player_id / induct_player) already use.
            "max_players": resolve_max_players(get_effective_settings(sid)),
            "registered_players": [_roster_view(rp) for rp in (sess.get("registered_players") or [])],
            "simulation_mode": sess.get("simulation_mode", "conglomerate"),
            "industry_vertical": sess.get("industry_vertical", ""),
            "region_id": sess.get("region_id", ""),
            # P5: labelled, non-authoritative turnaround annotation (canonical
            # R10 result stays the leaderboard figure).
            "turnaround": __import__("turnaround_engine").leaderboard_annotation(gs),
        })

    # Sort: group player sessions under their parent cohort, then by terminal value
    # 1. Separate cohort parents and player sub-sessions
    cohorts = [e for e in leaderboard if not e.get("parent_cohort_id")]
    players = [e for e in leaderboard if e.get("parent_cohort_id")]

    # 2. Sort cohorts by terminal value
    cohorts.sort(key=lambda x: x["terminal_value"], reverse=True)

    # 3. Build ordered list: each cohort followed by its player sessions (sorted by terminal value)
    ordered = []
    cohort_ids = {c["session_id"] for c in cohorts}
    for cohort in cohorts:
        ordered.append(cohort)
        children = [p for p in players if p["parent_cohort_id"] == cohort["session_id"]]
        children.sort(key=lambda x: x["terminal_value"], reverse=True)
        ordered.extend(children)

    # 4. Append any orphan player sessions (shouldn't happen, but be safe)
    orphans = [p for p in players if p["parent_cohort_id"] not in cohort_ids]
    orphans.sort(key=lambda x: x["terminal_value"], reverse=True)
    ordered.extend(orphans)

    return {"leaderboard": ordered}


# ─────────────────────────────────────────────────────────────────
#  WAR-MAP / SITUATION-ROOM AGGREGATE
#  One cohort-wide "situation" for the projector map: per-BU health,
#  per-stakeholder worst escalation, the cohort's current round, and a
#  real events list. Read-only; safe defaults when data is sparse.
# ─────────────────────────────────────────────────────────────────
_WARMAP_STAGE_RANK = {"dormant": 0, "watching": 1, "agitated": 2, "hostile": 3, "triggered": 4}


@admin_router.get("/war-map", summary="Cohort-aggregate operations & stakeholder map state")
async def get_war_map(facilitator_id: Optional[str] = None, _guard: None = Depends(require_facilitator)):
    from autonomous_agents import AGENT_PROFILES
    from collections import Counter
    sessions = await db.fetch_all_sessions()
    bu_acc: dict = {}       # bu_id -> running sums
    agent_acc: dict = {}    # agent_id -> {stages, tol, hostile}
    rounds: list = []
    team_n = 0

    for sess in sessions:
        if facilitator_id and sess.get("facilitator_id") != facilitator_id:
            continue
        if not (sess.get("player_id") or sess.get("parent_cohort_id")):
            continue  # skip cohort templates / solo shells
        latest = await db.fetch_latest_state(sess["session_id"])
        if not latest:
            continue
        gs = latest["global_state"]
        bus = latest["bu_states"]
        if not bus:
            continue
        team_n += 1
        rounds.append(latest.get("round_number") or gs.get("round_number") or 1)
        for bu in bus:
            bid = bu.get("bu_id")
            if not bid:
                continue
            a = bu_acc.setdefault(bid, {"slo": 0.0, "ci": 0.0, "burn": 0.0, "rev": 0.0, "n": 0})
            a["slo"] += float(bu.get("social_license_score", 50) or 50)
            a["ci"] += float(bu.get("carbon_intensity", 50) or 50)
            a["burn"] += float(bu.get("staff_burnout_index", 0) or 0)
            a["rev"] += float(bu.get("revenue_base", 0) or 0)
            a["n"] += 1
        agents = (gs.get("autonomous_agents") or {}).get("agents") or {}
        for aid, st in agents.items():
            g = agent_acc.setdefault(aid, {"stages": [], "tol": [], "hostile": 0})
            stage = st.get("escalation_stage", "dormant")
            g["stages"].append(stage)
            g["tol"].append(float(st.get("tolerance", 100) or 100))
            if _WARMAP_STAGE_RANK.get(stage, 0) >= 3:
                g["hostile"] += 1

    def _bu_health(slo, ci, burn):
        return max(0, min(100, round(0.5 * slo + 0.25 * (100 - ci) + 0.25 * (100 - burn))))

    business_units = []
    for bid, a in bu_acc.items():
        n = max(1, a["n"])
        slo, ci, burn, rev = a["slo"] / n, a["ci"] / n, a["burn"] / n, a["rev"] / n
        business_units.append({
            "bu_id": bid, "slo": round(slo, 1), "carbon_intensity": round(ci, 1),
            "burnout": round(burn, 1), "revenue": round(rev), "teams": a["n"],
            "health": _bu_health(slo, ci, burn),
        })

    stakeholders = []
    for aid, prof in AGENT_PROFILES.items():
        g = agent_acc.get(aid)
        if g and g["stages"]:
            worst = max(g["stages"], key=lambda s: _WARMAP_STAGE_RANK.get(s, 0))
            avg_tol = round(sum(g["tol"]) / len(g["tol"]), 1)
            hostile = g["hostile"]
        else:
            worst, avg_tol, hostile = "dormant", float(prof.get("initial_tolerance", 100)), 0
        stakeholders.append({
            "agent_id": aid, "name": prof.get("name", aid),
            "stage": worst, "avg_tolerance": avg_tol, "teams_hostile": hostile,
        })

    cohort_round = Counter(rounds).most_common(1)[0][0] if rounds else 0

    events = []
    for s in stakeholders:
        if _WARMAP_STAGE_RANK.get(s["stage"], 0) >= 2:
            events.append({"kind": "stakeholder", "name": s["name"], "stage": s["stage"], "teams": s["teams_hostile"]})
    for b in business_units:
        if b["health"] < 40:
            events.append({"kind": "bu", "bu_id": b["bu_id"], "health": b["health"]})

    # Crisis name/icon from the round catalog — the SINGLE source of truth
    # (Railway audit §3.2: the client-side name copy had drifted and was
    # removed; the frontend contributes coordinates only and renders no marker
    # unless this key is present). Decision rounds have no crisis → None.
    _crisis = None
    try:
        from round_configs import get_round_crisis
        _cfg = get_round_crisis(cohort_round) if cohort_round else None
        if _cfg:
            _crisis = {"name": _cfg.get("title", ""), "icon": _cfg.get("icon", "")}
    except Exception:
        _crisis = None

    return {
        "team_count": team_n,
        "cohort_round": cohort_round,
        "business_units": business_units,
        "stakeholders": stakeholders,
        "events": events,
        "crisis": _crisis,
    }


# ─────────────────────────────────────────────────────────────────
#  SESSION REPORT ENDPOINT
#  Full per-session analytics aggregation for the Reports tab.
#  Includes KPIs, CEO scores, sandbox burden, side-tracks, history.
# ─────────────────────────────────────────────────────────────────

@admin_router.get(
    "/session-report/{session_id}",
    summary="Full performance analytics for a single session",
)
async def get_session_report(session_id: str, _guard: None = Depends(require_facilitator)):
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
    # For completed games (R10), use the engine's authoritative terminal value;
    # for in-progress sessions use a quick proxy so the leaderboard stays live.
    authoritative_tv = flags.get("terminal_value")
    if authoritative_tv is not None:
        terminal_value = round(float(authoritative_tv), 2)
    else:
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
        "turnaround": __import__("turnaround_engine").leaderboard_annotation(gs),
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
async def apply_override(session_id: str, body: OverrideRequest, request: Request, _guard: None = Depends(require_lead_facilitator)):
    """
    Applies a God Mode override to a specific session.
    Types: carbon_tax, omni_tech_poach, force_strike
    """
    await _assert_session_ownership(request, session_id)
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
_custom_black_swan_log = []


@admin_router.post(
    "/{session_id}/inject-custom-event",
    summary="Inject a custom Black Swan event into a player session",
    status_code=status.HTTP_200_OK,
)
async def inject_custom_event(session_id: str, body: CustomBlackSwanRequest, request: Request, _guard: None = Depends(require_lead_facilitator)):
    """
    Immediately mutates the session's game state with the specified deltas,
    injects a mailbox message, and pushes a WebSocket alert to the player.
    """
    await _assert_session_ownership(request, session_id)
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
    _capped_append(_god_mode_audit_log, {
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


# ── Feature 6: Synchronized Shockwave ────────────────────────────────────────
# Preset dramatic events. Same impact model as inject_custom_event (treasury +
# reputation deltas), applied identically to EVERY team in the cohort so the
# debrief is a clean comparison of crisis leadership.
_SHOCKWAVE_EVENTS = {
    "pandemic":       {"title": "Global Pandemic Shockwave",  "narrative": "A novel pathogen halts supply chains overnight. Every division must respond — now.",        "financial_impact": -6000000, "reputation_impact": -6},
    "carbon_tax":     {"title": "Emergency Carbon Tax",       "narrative": "Regulators impose an emergency carbon levy, effective immediately. Brown assets bleed cash.", "financial_impact": -5000000, "reputation_impact": -3},
    "supply_collapse":{"title": "Supply-Chain Collapse",      "narrative": "A critical logistics corridor is severed. Costs spike across the entire group.",             "financial_impact": -4500000, "reputation_impact": -4},
    "cyber_attack":   {"title": "Coordinated Cyber Attack",   "narrative": "A ransomware wave locks systems sector-wide. Operations stall and trust is shaken.",          "financial_impact": -4000000, "reputation_impact": -7},
}


def _require_console_capability(request: Request, flag: str, label: str) -> None:
    """Per-facilitator capability gate for the live consoles (Trading Floor /
    Shockwave). god_mode always passes; the caller is already authenticated by
    require_facilitator — this only rejects a registry record whose flag was
    explicitly switched off at facilitator setup."""
    from auth_jwt import get_facilitator_from_request
    _fid = get_facilitator_from_request(request)
    if _fid == "project_admin":
        raise HTTPException(status_code=403, detail=f"{label} is not available to project admins.")
    if _fid and _fid != "god_mode":
        _fac = next((f for f in _facilitator_registry if f.get("facilitator_id") == _fid and not f.get("deleted_at")), None)
        if _fac is not None and _fac.get(flag, True) is False:
            raise HTTPException(status_code=403, detail=f"{label} is disabled for your facilitator profile.")


@admin_router.get("/shockwave/events", summary="Shockwave crisis catalog (single source of truth)")
async def get_shockwave_events(_guard: None = Depends(require_facilitator)):
    """G-3 (v3/S5): serve the crisis catalog so the Shockwave console renders
    the ENGINE's numbers instead of a hand-copied frontend duplicate. Additive
    and read-only; the console feature-detects this endpoint and falls back to
    its local copy (guarded by the drift-tripwire jest test) when absent."""
    return {"events": [{"id": k, **v} for k, v in _SHOCKWAVE_EVENTS.items()]}


@admin_router.post("/{cohort_id}/shockwave", summary="Feature 6: detonate a synchronized black-swan across a cohort")
async def detonate_shockwave(cohort_id: str, request: Request, body: dict = Body(default={}), _guard: None = Depends(require_sim_manager)):
    """Applies an identical black-swan impact (treasury + reputation) to every
    team in the cohort and broadcasts a dramatic full-screen 'shockwave' alert.
    Reuses the same impact model as inject_custom_event; deterministic by
    construction (forced, not rolled). Gated by the caller's per-profile
    `shockwave_enabled` capability (Feature 6 toggle set at facilitator setup).

    WOW-4E: Pass `rehearsal: true` in the body to preview the event on the
    facilitator's screen only — NO game state changes, NO student broadcast.
    """
    # Per-facilitator capability check (god_mode always allowed).
    _require_console_capability(request, "shockwave_enabled", "Shockwave")

    event_id = (body or {}).get("event_id", "pandemic")
    countdown = int((body or {}).get("countdown", 60))
    rehearsal = bool((body or {}).get("rehearsal", False))
    ev = _SHOCKWAVE_EVENTS.get(event_id) or _SHOCKWAVE_EVENTS["pandemic"]

    # ── WOW-4E: Rehearsal mode — facilitator-only preview, no state changes ──
    if rehearsal:
        await manager.broadcast_admin({
            "type": "shockwave_rehearsal",
            "cohort_id": cohort_id,
            "event": {"id": event_id, "title": ev["title"], "narrative": ev["narrative"],
                      "financial_impact": ev["financial_impact"], "reputation_impact": ev["reputation_impact"]},
            "countdown": countdown,
        })
        _audit("shockwave_rehearsal", details={"cohort_id": cohort_id, "event_id": event_id})
        return {"status": "rehearsal", "event_id": event_id, "event": ev, "message": "Rehearsal only — students NOT affected"}

    all_sessions = await db.fetch_all_sessions()
    children = [s["session_id"] for s in all_sessions if s.get("parent_cohort_id") == cohort_id]
    applied = 0
    for sid in children:
        cur = await db.fetch_latest_state(sid)
        if not cur:
            continue
        gs = cur["global_state"]; bus = cur["bu_states"]
        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) + ev["financial_impact"], 2)
        gs["group_reputation"] = max(0, min(100, round(gs.get("group_reputation", 50) + ev["reputation_impact"], 2)))
        rec = {
            "type": "shockwave", "event_id": event_id, "title": ev["title"], "narrative": ev["narrative"],
            "financial_impact": ev["financial_impact"], "reputation_impact": ev["reputation_impact"],
            "injected_at": datetime.now(timezone.utc).isoformat(),
        }
        gs.setdefault("active_event_flags", {})
        if not isinstance(gs["active_event_flags"], dict):
            gs["active_event_flags"] = {}
        sw = gs["active_event_flags"].get("custom_black_swans", [])
        sw.append(rec)
        gs["active_event_flags"]["custom_black_swans"] = sw
        await db.update_latest_global_state(sid, gs, bus)
        msg = {
            "id": f"shockwave_{datetime.now(timezone.utc).timestamp():.0f}_{sid[:6]}",
            "round": cur["round_number"], "type": "crisis", "title": f"🌊 {ev['title']}",
            "body": ev["narrative"], "read": False, "source": "god_mode",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _session_messages.setdefault(sid, []).append(msg)
        applied += 1

    await manager.broadcast_students({
        "type": "shockwave",
        "event": {"id": event_id, "title": ev["title"], "narrative": ev["narrative"],
                  "financial_impact": ev["financial_impact"], "reputation_impact": ev["reputation_impact"]},
        "countdown": countdown, "cohort_id": cohort_id,
    })
    await manager.broadcast_admin({"type": "shockwave_detonated", "cohort_id": cohort_id, "event_id": event_id, "applied": applied})
    _audit("shockwave_detonated", details={"cohort_id": cohort_id, "event_id": event_id, "applied": applied})
    return {"status": "detonated", "event_id": event_id, "teams_hit": applied, "event": ev}


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
async def inject_message(session_id: str, body: MessageInjectRequest, request: Request, _guard: None = Depends(require_sim_manager)):
    """
    Pushes a facilitator message directly into a session's mailbox.
    Can use a preset_id or custom title/body.
    """
    await _assert_session_ownership(request, session_id)
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
    summary="Get the dynamic materiality configuration"
)
async def get_materiality_config():
    """
    Returns the current materiality issues, interdependencies, fee, plus:
      - panel_group_config: per-group fee/color/label data for the multi-survey UI
      - panel_recommendations: per-issue, per-group quadrant recommendations
        (deterministic, bias-aware per ESRS §1.47 group mandates)
    """
    from round2_csrd import (
        ROUND_2_DEFAULT_CONFIG,
        compute_panel_recommendations,
    )
    config = mat_db.get_current_config()
    issues = config.get("issues", [])
    panel_group_config = (
        ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"].get("groups", {})
    )
    panel_recommendations = compute_panel_recommendations(issues)
    return {
        **config,
        "panel_group_config": panel_group_config,
        "panel_recommendations": panel_recommendations,
    }


@admin_router.put(
    "/materiality-config",
    response_model=MaterialityConfig,
    summary="Update the entire materiality configuration"
)
async def update_materiality_config(config: MaterialityConfig, _guard: None = Depends(require_super_admin)):
    """Overwrites the entire materiality config and stores it in JSON."""
    mat_db.update_current_config(config.model_dump())
    return mat_db.get_current_config()


@admin_router.post(
    "/materiality-config/issues",
    response_model=MaterialityConfig,
    summary="Add a new materiality issue"
)
async def add_materiality_issue(issue: MaterialityIssue, _guard: None = Depends(require_super_admin)):
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
async def delete_materiality_issue(issue_id: str, _guard: None = Depends(require_super_admin)):
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
async def update_consultant_fee(fee_usd: int = Body(..., embed=True), _guard: None = Depends(require_super_admin)):
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
async def add_bu_category(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def delete_bu_category(bu_id: str, _guard: None = Depends(require_super_admin)):
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

    # Build bu_regions: slot → region for players in single-BU mode
    bu_regions: dict = {}
    try:
        from admin_shared import _player_registry as _pr
        for _p in _pr:
            if _p.get("session_id") == session_id and _p.get("assigned_bu") and _p.get("region_id"):
                bu_regions[_p["assigned_bu"]] = _p["region_id"]
    except Exception:
        pass

    return {
        "session_id": session_id,
        "active_bus": active_bus,
        "substitutions": subs,
        "locked": locked,
        "lock_reason": "BU composition is locked after Round 1 is committed." if locked else None,
        "slots": slots,
        "bu_regions": bu_regions,
    }


@admin_router.put(
    "/{session_id}/bu-composition",
    summary="Set BU composition (swap verticals)",
)
async def set_bu_composition(session_id: str, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
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

    # Persist to cohort session
    await db.update_latest_global_state(session_id, global_state, new_bu_states)

    # Cascade to all child player sessions
    children = await db.get_child_sessions(session_id)
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state:
            child_gs = child_state["global_state"]
            child_gs["bu_substitutions"] = substitutions
            await db.update_latest_global_state(
                child["session_id"], child_gs, new_bu_states
            )

    # Audit log
    _capped_append(_god_mode_audit_log, {
        "action": "bu_composition_changed",
        "session_id": session_id,
        "substitutions": substitutions,
        "active_bus": get_active_bus(substitutions),
        "children_updated": len(children),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    active_bus = get_active_bus(substitutions)
    labels = [BU_PROFILES.get(b, {}).get("label", b) for b in active_bus]
    print(f"[god-mode] BU composition updated for {session_id} + {len(children)} children: {labels}")

    return {
        "status": "ok",
        "active_bus": active_bus,
        "substitutions": substitutions,
        "bu_labels": labels,
        "children_updated": len(children),
    }


# ═════════════════════════════════════════════════════════════════
#  BU-SPECIFIC MATERIALITY CONFIGURATOR (Strategic Pillars)
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/materiality-config/bu/{bu_id}",
    summary="Get the BU-specific materiality configuration"
)
async def get_bu_materiality_config(bu_id: str):
    """
    Returns the materiality issues dictionary for a specific Business Unit,
    plus panel_group_config and panel_recommendations (same as global endpoint).
    """
    from round2_csrd import (
        ROUND_2_DEFAULT_CONFIG,
        compute_panel_recommendations,
    )
    valid = mat_db.get_bu_ids()
    if bu_id not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid BU ID: {bu_id}. Valid: {valid}")
    config = mat_db.get_bu_config(bu_id)
    issues = config.get("issues", [])
    panel_group_config = (
        ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"].get("groups", {})
    )
    panel_recommendations = compute_panel_recommendations(issues)
    return {
        **config,
        "panel_group_config": panel_group_config,
        "panel_recommendations": panel_recommendations,
    }


@admin_router.put(
    "/materiality-config/bu/{bu_id}",
    summary="Update the BU-specific materiality configuration"
)
async def update_bu_materiality_config(bu_id: str, config: MaterialityConfig, _guard: None = Depends(require_super_admin)):
    """Overwrites the entire BU-specific materiality dictionary."""
    valid = mat_db.get_bu_ids()
    if bu_id not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid BU ID: {bu_id}. Valid: {valid}")
    mat_db.update_bu_config(bu_id, config.model_dump())
    return mat_db.get_bu_config(bu_id)


# ═════════════════════════════════════════════════════════════════
#  MATERIALITY CONFIG — EXCEL UPLOAD / DOWNLOAD
# ═════════════════════════════════════════════════════════════════

@admin_router.post(
    "/materiality-config/upload",
    summary="Upload an Excel (.xlsx) file to replace the materiality config",
    status_code=status.HTTP_200_OK,
)
async def upload_materiality_excel(
    file: UploadFile = File(...),
    scope: str = _Query("global", description="'global' or a BU ID like 'pharma'"),
    _guard: None = Depends(require_super_admin),
):
    """
    Accepts a .xlsx file with 'Issues' and 'Interdependencies' sheets.
    Validates all data, computes a diff against the current config,
    and persists the new config.
    """
    import tempfile, os
    from pathlib import Path
    from materiality_config_excel import import_materiality_from_excel

    # ── MIME / extension check ────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are accepted.",
        )

    # ── Size limit: 5 MB ─────────────────────────────────────
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5 MB.",
        )

    # ── Write to temp file ────────────────────────────────────
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / f"mat_upload_{os.getpid()}.xlsx"
    try:
        tmp_path.write_bytes(contents)

        # ── Validate & parse ──────────────────────────────────
        try:
            new_config = import_materiality_from_excel(tmp_path)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # ── Load old config for diff ──────────────────────────
        if scope == "global":
            old_config = mat_db.get_current_config()
        else:
            valid_bus = mat_db.get_bu_ids()
            if scope not in valid_bus:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid scope '{scope}'. Valid BU IDs: {valid_bus}",
                )
            old_config = mat_db.get_bu_config(scope)

        # ── Compute diff ──────────────────────────────────────
        old_ids = {i["id"] for i in old_config.get("issues", [])}
        new_ids = {i["id"] for i in new_config.get("issues", [])}

        added   = sorted(new_ids - old_ids)
        removed = sorted(old_ids - new_ids)

        # Issues that exist in both but have changed
        old_map = {i["id"]: i for i in old_config.get("issues", [])}
        modified = []
        for issue in new_config["issues"]:
            if issue["id"] in old_ids and issue["id"] in new_ids:
                old_issue = old_map.get(issue["id"], {})
                if issue != old_issue:
                    modified.append(issue["id"])

        # ── Persist ───────────────────────────────────────────
        if scope == "global":
            mat_db.update_current_config(new_config)
        else:
            mat_db.update_bu_config(scope, new_config)

        return {
            "status": "ok",
            "scope": scope,
            "issues_count": len(new_config["issues"]),
            "interdependencies_count": len(new_config["interdependencies"]),
            "consultant_fee_usd": new_config.get("consultant_fee_usd"),
            "diff": {
                "added": added,
                "removed": removed,
                "modified": modified,
            },
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@admin_router.get(
    "/materiality-config/download",
    summary="Download the materiality config as an Excel (.xlsx) file",
)
async def download_materiality_excel(
    scope: str = _Query("global", description="'global' or a BU ID like 'pharma'"),
    _guard: None = Depends(require_facilitator),
):
    """
    Generates a formatted Excel workbook from the current materiality
    config and returns it as a streaming download.
    """
    import tempfile, os
    from pathlib import Path
    from fastapi.responses import StreamingResponse
    from materiality_config_excel import export_materiality_to_excel

    # ── Load config ───────────────────────────────────────────
    if scope == "global":
        config = mat_db.get_current_config()
    else:
        valid_bus = mat_db.get_bu_ids()
        if scope not in valid_bus:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scope '{scope}'. Valid BU IDs: {valid_bus}",
            )
        config = mat_db.get_bu_config(scope)

    # ── Generate Excel to temp file ───────────────────────────
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / f"mat_download_{os.getpid()}.xlsx"
    try:
        export_materiality_to_excel(config, tmp_path)
        file_bytes = tmp_path.read_bytes()
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    filename = f"materiality_config_{scope}.xlsx"

    import io
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


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
#  REGIONAL STAKEHOLDER CONFIG (Single-BU Localisation)
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/stakeholder-config/regions",
    summary="List all region stakeholder config files",
)
async def list_stakeholder_region_configs(_guard: None = Depends(require_facilitator)):
    """Returns a list of region_ids for which a stakeholder override JSON exists."""
    from stakeholder_db import list_region_configs
    return {"regions": list_region_configs()}


@admin_router.get(
    "/stakeholder-config/regions/{region_id}",
    summary="Get the stakeholder overrides for a region",
)
async def get_stakeholder_region_config(
    region_id: str, _guard: None = Depends(require_facilitator)
):
    """Returns the raw stakeholder override list for the given region_id.
    Returns 404 if no config exists yet.
    """
    from stakeholder_db import get_region_config_raw
    data = get_region_config_raw(region_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stakeholder config found for region '{region_id}'.",
        )
    return {"region_id": region_id, "overrides": data}


@admin_router.put(
    "/stakeholder-config/regions/{region_id}",
    summary="Create or update the stakeholder overrides for a region",
)
async def set_stakeholder_region_config(
    region_id: str,
    body: dict = Body(...),
    _guard: None = Depends(require_super_admin),
):
    """Overwrite the stakeholder override list for a region.

    Body: ``{"overrides": [ {stakeholder partial objects} ]}``

    Each entry is matched by ``id`` to the canonical STAKEHOLDERS list and
    merged (partial override). Entries with unknown ``id`` values are appended
    as new stakeholders specific to this region.

    Requires super_admin role. Cache is invalidated on successful write.
    """
    from stakeholder_db import save_region_config
    overrides = body.get("overrides")
    if not isinstance(overrides, list):
        raise HTTPException(
            status_code=400,
            detail="Body must contain an 'overrides' array of stakeholder objects.",
        )
    success = save_region_config(region_id, overrides)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to save config for region '{region_id}'. Check that region_id is a valid slug.",
        )
    return {
        "status": "ok",
        "region_id": region_id,
        "overrides_count": len(overrides),
    }


@admin_router.delete(
    "/stakeholder-config/regions/{region_id}",
    summary="Delete the stakeholder overrides for a region",
)
async def delete_stakeholder_region_config(
    region_id: str, _guard: None = Depends(require_super_admin)
):
    """Delete the region-specific stakeholder override file.
    The canonical STAKEHOLDERS will be used for this region after deletion.
    """
    from stakeholder_db import delete_region_config
    deleted = delete_region_config(region_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No stakeholder config found for region '{region_id}'.",
        )
    return {"status": "deleted", "region_id": region_id}


# ── Stakeholder Matrix Excel Upload / Download ───────────────

@admin_router.post(
    "/stakeholder-config/upload/{config_id}",
    summary="Upload stakeholder config from Excel (.xlsx)",
)
async def upload_stakeholder_excel(
    config_id: str,
    file: UploadFile = File(...),
    _guard: None = Depends(require_super_admin),
):
    """Upload an Excel file containing stakeholder definitions.

    ``config_id`` may be:
      - A region ID (e.g. ``asean``, ``europe``)
      - A vertical ID prefixed with ``vertical_`` (e.g. ``vertical_technology``)
      - ``canonical`` to overwrite the canonical default set (stored as region "canonical")

    Validates all rows before persisting. Returns the list of stakeholder IDs
    on success.
    """
    import os
    import tempfile

    # ── MIME / extension check ────────────────────────────
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are accepted. Please upload a valid Excel file.",
        )

    # ── Size limit (5 MB) ────────────────────────────────
    max_size = 5 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents):,} bytes). Maximum size is 5 MB.",
        )

    # ── Write to temp file, validate, and persist ─────────
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    try:
        os.write(tmp_fd, contents)
        os.close(tmp_fd)

        from stakeholder_config_excel import import_stakeholders_from_excel
        try:
            stakeholders = import_stakeholders_from_excel(tmp_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        from stakeholder_db import save_region_config
        success = save_region_config(config_id, stakeholders)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to save config for '{config_id}'. "
                       "Ensure config_id is a valid slug (lowercase alphanumeric + underscores, max 50 chars).",
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    ids = [s["id"] for s in stakeholders]
    print(f"[god-mode] Stakeholder Excel uploaded for '{config_id}': {len(ids)} stakeholders")
    return {
        "status": "ok",
        "config_id": config_id,
        "stakeholder_count": len(ids),
        "stakeholder_ids": ids,
    }


@admin_router.get(
    "/stakeholder-config/download/{config_id}",
    summary="Download stakeholder config as Excel (.xlsx)",
)
async def download_stakeholder_excel(
    config_id: str,
    _guard: None = Depends(require_facilitator),
):
    """Generate and download a stakeholder matrix Excel file.

    ``config_id`` may be:
      - A region ID — returns the merged (canonical + region overrides) set
      - A vertical ID prefixed with ``vertical_`` — returns vertical stakeholders
      - ``canonical`` — returns the canonical default set
    """
    import os
    import tempfile
    from fastapi.responses import StreamingResponse

    # ── Resolve which stakeholders to export ──────────────
    stakeholders = None

    if config_id == "canonical":
        from stakeholder_map import STAKEHOLDERS
        stakeholders = STAKEHOLDERS
    else:
        # Try region / vertical override from DB
        from stakeholder_db import get_region_config_raw
        raw = get_region_config_raw(config_id)
        if raw:
            stakeholders = raw
        elif config_id.startswith("vertical_"):
            # Try Python-defined vertical
            v_id = config_id[len("vertical_"):]
            try:
                from vertical_stakeholders import get_stakeholders_for_vertical
                stakeholders = get_stakeholders_for_vertical(v_id)
            except ImportError:
                pass
        else:
            # Try as a region (merged canonical + overrides)
            from stakeholder_db import get_stakeholders_for_region
            merged = get_stakeholders_for_region(config_id)
            if merged:
                stakeholders = merged

    if not stakeholders:
        raise HTTPException(
            status_code=404,
            detail=f"No stakeholder data found for config_id '{config_id}'.",
        )

    # ── Generate Excel ────────────────────────────────────
    from stakeholder_config_excel import export_stakeholders_to_excel

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    try:
        export_stakeholders_to_excel(stakeholders, tmp_path)

        def _iter_file():
            with open(tmp_path, "rb") as f:
                yield from iter(lambda: f.read(8192), b"")
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        safe_name = config_id.replace("/", "_").replace("\\", "_")
        return StreamingResponse(
            _iter_file(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="stakeholder_matrix_{safe_name}.xlsx"',
            },
        )
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise




@admin_router.get(
    "/{session_id}/audit-trail",
    summary="Get the decision audit trail for a cohort",
)
async def get_audit_trail(session_id: str, _guard: None = Depends(require_facilitator)):  # QA-2026-07-16 #13: was unauthenticated — guard facilitator/admin-only data.
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
async def get_player_sessions(session_id: str, _guard: None = Depends(require_facilitator)):  # QA-2026-07-16 #13: was unauthenticated — guard facilitator/admin-only data.
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
async def impersonate_player(player_session_id: str, _guard: None = Depends(require_sim_manager)):
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
async def reset_session(session_id: str, _guard: None = Depends(require_super_admin)):
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
    _player_registry[:] = [p for p in _player_registry if p.get("session_id") != session_id]

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
async def reset_all_sessions(
    reset_facilitators: bool = False,  # GOD-011: must be explicitly opted in
    _guard: None = Depends(require_super_admin),
):
    """Deletes ALL sessions and all data. Cannot be undone.

    GOD-011: Facilitator accounts are NOT wiped unless ?reset_facilitators=true
    is explicitly supplied. Separating these operations prevents accidental
    deletion of all 30 facilitator accounts during a routine session cleanup.

    GOD-007: The in-memory audit log is preserved — it is forensic evidence and
    must not be erased by a session reset. A 'sessions_reset' audit entry is
    appended instead so the action itself is on record.
    """
    count = await db.delete_all_sessions(hard=True)

    # Clear operational state (NOT the audit log — GOD-007)
    _crisis_trigger_history.clear()
    _session_messages.clear()
    _session_interventions.clear()

    from admin_shared import _DEFAULT_FACILITATOR, _persist_facilitators, _practice_mode, _round_pacing, _shared_marketplace

    # GOD-011: Only reset facilitator registry when explicitly requested
    if reset_facilitators:
        global _facilitator_registry
        _facilitator_registry[:] = [{**_DEFAULT_FACILITATOR}]
        _persist_facilitators()

    # Reset other transient states
    _practice_mode.clear()
    _round_pacing.clear()
    _shared_marketplace["carbon_credit_pool"]["purchased"].clear()
    _shared_marketplace["carbon_credit_pool"]["price_history"] = [50000]
    _shared_marketplace["green_talent_pool"]["hired"].clear()
    _shared_marketplace["green_talent_pool"]["cost_history"] = [200000]

    # GOD-007: Audit the reset (log survives; this entry proves the action happened)
    _audit("sessions_reset", details={
        "sessions_removed": count,
        "facilitators_reset": reset_facilitators,
    })

    # Notify admin dashboard
    await manager.broadcast_admin({
        "type": "all_sessions_reset",
        "count": count,
    })

    return {
        "status": "all_deleted",
        "sessions_removed": count,
        "facilitators_reset": reset_facilitators,
    }



# ARCH-002: Resources extracted to admin_resources.py (19 endpoints)
# Mounted in main.py via app.include_router(resources_router)


# ═════════════════════════════════════════════════════════════════
#  MASTER INTERVENTIONS DATABASE (God Mode)
# ═════════════════════════════════════════════════════════════════


_master_overrides = [
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

_master_swipes = [
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
async def upsert_master_override(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def upsert_master_swipe(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def delete_master_override(override_id: str, _guard: None = Depends(require_super_admin)):
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
async def delete_master_swipe(swipe_id: str, _guard: None = Depends(require_super_admin)):
    global _master_swipes
    before = len(_master_swipes)
    _master_swipes = [s for s in _master_swipes if s["id"] != swipe_id]
    if len(_master_swipes) == before:
        raise HTTPException(404, f"Swipe '{swipe_id}' not found")
    return {"status": "deleted", "id": swipe_id}


def _sanitise_upload_name(filename: str | None) -> str:
    """Reduce an uploaded filename to a safe bare name on ANY OS.

    CRIT-005: os.path.basename alone does NOT strip Windows-style backslash
    separators on POSIX hosts (our Docker/Railway target), so we additionally
    strip '..', both separators, and null bytes explicitly. The caller still
    performs a realpath containment check as defence-in-depth.
    """
    bare_name = os.path.basename(filename or "upload")
    bare_name = bare_name.replace("..", "").replace("/", "").replace("\\", "").replace("\x00", "")
    return bare_name or "upload"


@admin_router.post(
    "/interventions/upload-media",
    summary="Upload media (audio/video) for an intervention",
)
async def upload_intervention_media(file: UploadFile = File(...), _guard: None = Depends(require_sim_manager)):
    """Upload an audio or video file for attachment to an override or swipe file.
    CRIT-005: Path traversal fix — filename is sanitized; MIME type and size are validated."""
    # ── MIME type allowlist ──────────────────────────────────────
    ALLOWED_MIME_TYPES = {
        "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm",
        "video/mp4", "video/webm", "video/ogg",
        "image/png", "image/jpeg", "image/gif", "image/webp",
        "application/pdf",
    }
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' is not allowed. Permitted types: audio, video, image, PDF."
        )

    # ── Path traversal: strip to bare filename only (cross-platform) ──
    bare_name = _sanitise_upload_name(file.filename)
    # Prepend timestamp to prevent collisions
    safe_name = f"{int(datetime.now(timezone.utc).timestamp())}_{bare_name}"

    project_root = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(project_root, "frontend", "public", "uploads", "interventions")
    os.makedirs(upload_dir, exist_ok=True)

    # Resolve absolute path and verify it stays within upload_dir
    file_path = os.path.realpath(os.path.join(upload_dir, safe_name))
    if not file_path.startswith(os.path.realpath(upload_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # ── Size limit: stream and count bytes ───────────────────────
    total = 0
    chunks = []
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds 25 MB limit.")
        chunks.append(chunk)

    with open(file_path, "wb") as buffer:
        for chunk in chunks:
            buffer.write(chunk)

    file_url = f"/uploads/interventions/{safe_name}"
    return {"status": "uploaded", "url": file_url, "filename": safe_name}


# ═════════════════════════════════════════════════════════════════
#  SIMULATION CONFIG UPLOAD & HOT-RELOAD
# ═════════════════════════════════════════════════════════════════

# Concurrency guard: prevents config reload while a simulation tick is running.
# Acquire with blocking=False from process_tick call paths; blocking from upload.
_sim_config_reload_lock = threading.Lock()


def _deep_diff(old: dict, new: dict, path_prefix: str = "") -> list[dict]:
    """Recursively diff two nested dicts, returning changed leaf values."""
    changes = []
    all_keys = set(list(old.keys()) + list(new.keys()))
    for key in sorted(all_keys):
        if key.startswith("_"):
            continue  # skip _comment fields
        full_path = f"{path_prefix}.{key}" if path_prefix else key
        old_val = old.get(key)
        new_val = new.get(key)
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            changes.extend(_deep_diff(old_val, new_val, full_path))
        elif old_val != new_val:
            # Parse path into section/subsection/parameter
            parts = full_path.split(".")
            section = parts[0] if len(parts) >= 1 else ""
            subsection = parts[1] if len(parts) >= 3 else ""
            parameter = parts[-1]
            changes.append({
                "section": section,
                "subsection": subsection,
                "parameter": parameter,
                "old_value": old_val,
                "new_value": new_val,
            })
    return changes


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_CONFIG_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@admin_router.post(
    "/config/upload",
    summary="Upload simulation config Excel and hot-reload (God Mode)",
    tags=["Admin — Simulation Config"],
)
async def upload_simulation_config(
    request: Request,
    file: UploadFile = File(...),
    reason: str | None = None,
    _guard: None = Depends(require_super_admin),
):
    """Upload a simulation_config.xlsx file, convert to JSON, and hot-reload
    all config constants without a server restart.

    Security: require_super_admin + MIME validation + size limit.
    Concurrency: rejects with 409 if a simulation tick is in progress.
    Rollback: backs up JSON before write; restores on any failure.
    I5: god_mode callers must supply a 'reason' (query param) for the audit trail.
    """
    _require_god_mode_reason(request, reason)
    from pathlib import Path

    # ── MIME validation ─────────────────────────────────────────
    if file.content_type and file.content_type != _XLSX_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type: {file.content_type}. Expected .xlsx ({_XLSX_MIME})",
        )
    if file.filename and not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=415,
            detail="Invalid file extension. Expected .xlsx",
        )

    # ── Size validation (stream and count) ──────────────────────
    total = 0
    chunks = []
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > _CONFIG_MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")
        chunks.append(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # ── Concurrency guard ───────────────────────────────────────
    acquired = _sim_config_reload_lock.acquire(blocking=False)
    if not acquired:
        raise HTTPException(
            status_code=409,
            detail="Config upload rejected: simulation tick in progress. "
                   "Try again after the current round completes.",
        )

    try:
        # ── Paths ───────────────────────────────────────────────
        backend_dir = Path(__file__).resolve().parent
        project_root = backend_dir.parent
        json_path = project_root / "simulation_config.json"
        json_bak = project_root / "simulation_config.json.bak"
        temp_xlsx = project_root / "simulation_config_upload.xlsx"
        live_xlsx = project_root / "simulation_config.xlsx"

        # ── Save upload to temp file ────────────────────────────
        with open(temp_xlsx, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

        # ── Validate Excel structure ────────────────────────────
        try:
            from openpyxl import load_workbook
            wb = load_workbook(str(temp_xlsx), read_only=True, data_only=True)
            ws = wb.active
            if ws is None:
                raise ValueError("No active sheet found")

            # Check header row
            headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
            required = {"Section", "Parameter", "Value", "Type"}
            found = set(h for h in headers if h)
            missing = required - found
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

            # Check for empty rows with Parameters
            errors = []
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if row is None or all(cell is None for cell in row):
                    continue
                section_raw, subsection, parameter, value, type_label, *_ = (
                    list(row) + [None] * 7
                )[:7]
                # Skip section header rows
                if parameter is None or str(parameter).strip() == "":
                    continue
                if value is None:
                    errors.append(f"Row {row_idx}: parameter '{parameter}' has no value")

            if errors:
                raise ValueError(f"Validation errors: {'; '.join(errors[:10])}")

            wb.close()
        except ValueError as ve:
            # Clean up temp file
            if temp_xlsx.exists():
                temp_xlsx.unlink()
            raise HTTPException(status_code=422, detail=str(ve))
        except Exception as e:
            if temp_xlsx.exists():
                temp_xlsx.unlink()
            raise HTTPException(
                status_code=422,
                detail=f"Failed to read Excel file: {str(e)}",
            )

        # ── Snapshot current config for diff ────────────────────
        import config as _config_mod
        old_config = copy.deepcopy(_config_mod.SIMULATION_CONFIG)

        # ── Backup current JSON ─────────────────────────────────
        if json_path.exists():
            shutil.copy2(str(json_path), str(json_bak))

        # ── Convert Excel → JSON ───────────────────────────────
        try:
            from config_excel import import_from_excel
            import_from_excel(temp_xlsx, json_path)
        except Exception as e:
            # Rollback: restore backup
            if json_bak.exists():
                shutil.copy2(str(json_bak), str(json_path))
            if temp_xlsx.exists():
                temp_xlsx.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Excel-to-JSON conversion failed: {str(e)}. Config restored from backup.",
            )

        # ── Validate the generated JSON loads ───────────────────
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                new_config = json.load(f)
        except Exception as e:
            # Rollback
            if json_bak.exists():
                shutil.copy2(str(json_bak), str(json_path))
            if temp_xlsx.exists():
                temp_xlsx.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Generated JSON is invalid: {str(e)}. Config restored from backup.",
            )

        # ── Hot-reload chain ────────────────────────────────────
        try:
            import config
            importlib.reload(config)
            import engine
            importlib.reload(engine)
            import balance_sheet
            importlib.reload(balance_sheet)
            import terminal_valuation
            importlib.reload(terminal_valuation)
            import black_swan_registry
            importlib.reload(black_swan_registry)
        except Exception as e:
            # Rollback: restore backup and re-reload
            if json_bak.exists():
                shutil.copy2(str(json_bak), str(json_path))
                try:
                    import config as _cfg_rollback
                    importlib.reload(_cfg_rollback)
                except Exception:
                    pass
            if temp_xlsx.exists():
                temp_xlsx.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Hot-reload failed: {str(e)}. Config restored from backup.",
            )

        # ── Move temp xlsx to live path ─────────────────────────
        shutil.move(str(temp_xlsx), str(live_xlsx))

        # ── Compute full parameter diff ─────────────────────────
        changes = _deep_diff(old_config, new_config)

        # ── Audit trail ─────────────────────────────────────────
        _audit("simulation_config_uploaded", details={
            "parameters_loaded": sum(
                1 for _ in _iter_leaf_params(new_config)
            ),
            "changes_count": len(changes),
            "backup": "simulation_config.json.bak",
        })

        return {
            "status": "ok",
            "parameters_loaded": sum(
                1 for _ in _iter_leaf_params(new_config)
            ),
            "changes": changes,
            "changes_count": len(changes),
            "reload": "complete",
            "backup": "simulation_config.json.bak",
        }

    finally:
        _sim_config_reload_lock.release()


def _iter_leaf_params(config: dict):
    """Yield every leaf parameter in a nested config dict (for counting)."""
    for key, val in config.items():
        if key.startswith("_"):
            continue
        if isinstance(val, dict):
            yield from _iter_leaf_params(val)
        else:
            yield (key, val)


@admin_router.get(
    "/config/current",
    summary="Get current simulation config (read-only)",
    tags=["Admin — Simulation Config"],
)
async def get_current_config(
    _guard: None = Depends(require_facilitator),
):
    """Returns the full in-memory simulation_config.json as JSON.
    Any authenticated facilitator can read this (super_admin not required).
    """
    import config as _config_mod
    return {
        "status": "ok",
        "config": _config_mod.SIMULATION_CONFIG,
    }


# ═════════════════════════════════════════════════════════════════
#  WEBSOCKET ENDPOINTS
# ═════════════════════════════════════════════════════════════════

def _ws_authenticate_facilitator(websocket: "WebSocket", token: str | None) -> bool:
    """MED-004: Validate a WebSocket connection as an authenticated facilitator.

    Priority order:
    1. JWT in HttpOnly cookie (mur_session) — preferred path; set by login endpoint.
    2. JWT passed as ?token= query parameter — fallback for WS clients that cannot
       send cookies (e.g. native mobile apps, curl-based tooling).
    3. Legacy facilitator_id string match — kept only for the migration window;
       remove once all clients have been updated to JWT-based auth.

    Returns True if any path succeeds, False otherwise.
    """
    from auth_jwt import decode_facilitator_token, COOKIE_NAME

    # ── 1. JWT cookie ───────────────────────────────────────────────────
    cookie_token = websocket.cookies.get(COOKIE_NAME, "")
    if cookie_token:
        try:
            payload = decode_facilitator_token(cookie_token)
            fac_id = payload.get("sub", "")
            if fac_id == "god_mode":
                return True
            return any(
                f["facilitator_id"] == fac_id and not f.get("deleted_at")
                for f in _facilitator_registry
            )
        except Exception:
            pass  # Invalid or expired cookie — try next path

    # ── 2. JWT as query parameter (?token=<signed-jwt>) ────────────────
    if token:
        # First, try to decode it as a JWT
        try:
            payload = decode_facilitator_token(token)
            fac_id = payload.get("sub", "")
            if fac_id == "god_mode":
                return True
            return any(
                f["facilitator_id"] == fac_id and not f.get("deleted_at")
                for f in _facilitator_registry
            )
        except Exception:
            pass  # Not a valid JWT — no further fallback

        # H-2 security fix: Legacy facilitator_id string match REMOVED.
        # Previously a bare facilitator_id was accepted without crypto verification.
        # Now only signed JWTs (cookie or query param) are accepted.

    return False


@admin_router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket, facilitator_id: str = None, token: str = None):
    """WebSocket for admin dashboard real-time updates.
    MED-004: Authenticates via JWT cookie, JWT query param, or legacy facilitator_id."""
    # Accept the effective token from either ?token= or legacy ?facilitator_id=
    effective_token = token or facilitator_id
    if not _ws_authenticate_facilitator(websocket, effective_token):
        await websocket.close(code=4001, reason="Unauthorized: valid facilitator token required")
        return
    await manager.connect_admin(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Admin can request a leaderboard refresh
            if data == "refresh":
                if effective_token:
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
async def session_websocket(websocket: WebSocket, session_id: str, token: str = None):
    """WebSocket for player session — receives God Mode pushes.
    SEC/HIGH-001: The player must present a signed, session-scoped ws ticket
    (issued at login via auth_jwt.create_player_ws_ticket). The raw session_id
    is no longer accepted as a bearer credential. Facilitators observing the
    session authenticate with their normal JWT. This is a receive-only push
    channel; when a client cannot present a ticket it simply degrades to REST
    polling, so the classroom flow is unaffected."""
    from auth_jwt import verify_player_ws_ticket
    is_facilitator = _ws_authenticate_facilitator(websocket, token)
    is_player = verify_player_ws_ticket(token or "", session_id)
    if not is_facilitator and not is_player:
        await websocket.close(code=4001, reason="Unauthorized: valid session token required")
        return
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
async def undo_round(
    session_id: str,
    request: Request,
    cohort_wide: bool = False,
    target_round: int = None,
    _guard: None = Depends(require_lead_facilitator),
):
    """
    Deletes round state(s) reverting the session back.
    Ownership-enforced: lead_facilitators may only undo rounds in their own sessions.

    - No target_round → reverts exactly one round (previous behaviour).
    - target_round=N  → keeps undoing until current_round == N (multi-round rollback).
    """
    await _assert_session_ownership(request, session_id)
    targets = [session_id]
    if cohort_wide:
        all_sessions = await db.fetch_all_sessions()
        children = [s["session_id"] for s in all_sessions if s.get("parent_cohort_id") == session_id]
        targets.extend(children)

    last_res = None

    for tgt in set(targets):
        # Parity API: latest round via fetch_latest_round (works under Postgres;
        # a direct _global_states read returns {} there).
        current = await db.fetch_latest_round(tgt)
        if current is None:
            continue
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
            current = await db.fetch_latest_round(tgt)
            if current is None:
                break
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

_facilitator_notes = {}  # session_id → notes
_next_note_id: int = 1


class FacilitatorNoteRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    round_number: Optional[int] = None
    visible_to_players: bool = False


@admin_router.get(
    "/{session_id}/notes",
    summary="List facilitator notes for a session",
)
async def list_notes(session_id: str, _guard: None = Depends(require_facilitator)):
    # LOW-003: Guard added — notes may contain private facilitator observations
    # (round tactics, player struggles) not intended for public access.
    # Player-visible notes are pushed via WebSocket on creation; players do not
    # need to poll this endpoint.
    return {"notes": _facilitator_notes.get(session_id, [])}


@admin_router.post(
    "/{session_id}/notes",
    summary="Add a facilitator note",
)
async def add_note(
    session_id: str,
    req: FacilitatorNoteRequest,
    request: Request,
    _guard: None = Depends(require_sim_manager),
):
    from auth_jwt import get_facilitator_from_request
    global _next_note_id
    author = get_facilitator_from_request(request) or "unknown"
    note = {
        "note_id": f"NOTE-{_next_note_id:04d}",
        "text": req.text,
        "round_number": req.round_number,
        "visible_to_players": req.visible_to_players,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": author,  # GOD-009: track who wrote this note for delete-auth
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
async def delete_note(
    session_id: str,
    note_id: str,
    request: Request,
    _guard: None = Depends(require_sim_manager),
):
    # GOD-009: Only the note's author or a super_admin may delete a note.
    # This prevents one of 30 facilitators from silently erasing a colleague's
    # teaching annotations.
    from auth_jwt import get_facilitator_from_request
    caller = get_facilitator_from_request(request) or ""
    caller_role = get_fac_role(request)

    notes = _facilitator_notes.get(session_id, [])
    target = next((n for n in notes if n["note_id"] == note_id), None)
    if target is None:
        raise HTTPException(404, f"Note {note_id} not found")

    note_author = target.get("author", "")
    if not is_admin_role(caller_role) and note_author and note_author != caller:
        raise HTTPException(
            403,
            f"Only the note's author ({note_author}) or a super_admin may delete this note.",
        )

    _facilitator_notes[session_id] = [n for n in notes if n["note_id"] != note_id]
    return {"status": "deleted", "note_id": note_id}


# ═════════════════════════════════════════════════════════════════
#  STUDENT BONUSES / AWARDS
# ═════════════════════════════════════════════════════════════════

_student_bonuses = {}  # session_id → bonus records
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
async def award_bonus(session_id: str, req: StudentBonusRequest, _guard: None = Depends(require_sim_manager)):
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
async def revoke_bonus(session_id: str, bonus_id: str, _guard: None = Depends(require_sim_manager)):
    bonuses = _student_bonuses.get(session_id, [])
    before = len(bonuses)
    _student_bonuses[session_id] = [b for b in bonuses if b["bonus_id"] != bonus_id]
    if len(_student_bonuses[session_id]) == before:
        raise HTTPException(404, f"Bonus {bonus_id} not found")
    return {"status": "revoked", "bonus_id": bonus_id}


# ═════════════════════════════════════════════════════════════════
#  PEER EVALUATIONS
# ═════════════════════════════════════════════════════════════════

_peer_evaluations = {}  # session_id → evaluations
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
async def submit_peer_evaluation(
    session_id: str,
    req: PeerEvaluationRequest,
    # QA-2026-07-16 #2: was completely unguarded — anyone holding a session id
    # could submit evaluations that feed grading. The only frontend caller is
    # the facilitator dashboard (PeerEvaluation.js in admin/facilitator), so
    # gate it like its sibling DELETE endpoint below.
    _guard: None = Depends(require_sim_manager),
):
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
async def delete_peer_evaluation(session_id: str, eval_id: str, _guard: None = Depends(require_sim_manager)):
    evals = _peer_evaluations.get(session_id, [])
    before = len(evals)
    _peer_evaluations[session_id] = [e for e in evals if e["eval_id"] != eval_id]
    if len(_peer_evaluations[session_id]) == before:
        raise HTTPException(404, f"Evaluation {eval_id} not found")
    return {"status": "deleted", "eval_id": eval_id}


# ═════════════════════════════════════════════════════════════════
#  BULK MESSAGING / BROADCAST
# ═════════════════════════════════════════════════════════════════

_broadcast_history = []
_next_broadcast_id: int = 1
_scheduled_broadcasts = {}  # round_number → broadcast to send


class BroadcastRequest(BaseModel):
    title: str = Field(..., max_length=200)
    body: str = Field(..., max_length=5000)
    target_sessions: list[str] = []  # Empty = all sessions
    scheduled_round: Optional[int] = None  # None = send immediately


@admin_router.post(
    "/broadcast",
    summary="Broadcast a message to all or selected sessions",
)
async def broadcast_message(req: BroadcastRequest, request: Request, _guard: None = Depends(require_sim_manager)):
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
        _capped_append(_broadcast_history, broadcast)
        return broadcast

    # N6: Ownership scoping — non-super_admin facilitators may only broadcast
    # to sessions they own. Super admins retain broadcast-to-all capability.
    from auth_jwt import get_facilitator_from_request
    caller_id = get_facilitator_from_request(request)
    caller_fac = next(
        (f for f in _facilitator_registry if f["facilitator_id"] == caller_id and not f.get("deleted_at")),
        None,
    ) if caller_id else None
    # Virtual identities (god_mode / project_admin) have no registry row, so
    # deriving the role from caller_fac silently demoted them to "facilitator"
    # and the ownership filter below then matched NOTHING — God Mode's Universal
    # Broadcast returned 200 "sent" but delivered to zero cohorts. Resolve on the
    # signed-token LEVEL instead (CLAUDE.md role convention 1).
    caller_role = get_fac_role(request)
    is_super = is_admin_role(caller_role)

    # Send immediately
    all_sessions = await db.fetch_all_sessions()

    if req.target_sessions:
        # Explicit target list — filter to owned sessions for non-super_admin
        if is_super:
            targets = req.target_sessions
        else:
            owned_ids = {
                s["session_id"] for s in all_sessions
                if caller_fac and owns_session(caller_fac, s)
            }
            targets = [sid for sid in req.target_sessions if sid in owned_ids]
    else:
        # Broadcast all — restrict to own sessions for non-super_admin
        if is_super:
            targets = [s["session_id"] for s in all_sessions]
        else:
            targets = [
                s["session_id"] for s in all_sessions
                if caller_fac and owns_session(caller_fac, s)
            ]

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
    _capped_append(_broadcast_history, broadcast)
    return broadcast


@admin_router.get(
    "/broadcast/history",
    summary="Get broadcast history",
)
async def get_broadcast_history(_guard: None = Depends(require_facilitator)):  # QA-2026-07-16 #13: was unauthenticated — guard facilitator/admin-only data.
    return {"broadcasts": _broadcast_history}


def get_scheduled_broadcasts_for_round(round_number: int) -> Optional[dict]:
    """Called by round processing to check if a broadcast should be sent."""
    return _scheduled_broadcasts.pop(round_number, None)


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Global Settings  (#1, #6, #7)
# ═════════════════════════════════════════════════════════════════

def _audit(action: str, actor: str = "god_mode", details: dict = None, source_ip: str = None):
    """Append an entry to the god mode audit log and persist to a rotating log file.
    MED-015: All admin mutations write a tamper-evident JSON record so there
    is a forensic trail for facilitator actions."""
    entry = {
        "id": f"AUD-{next(_audit_counter):04d}",  # GOD-005: monotonic, no collision
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "source_ip": source_ip or "unknown",
        "action": action,
        "details": details or {},
    }
    _capped_append(_god_mode_audit_log, entry)
    # Persist to a newline-delimited JSON log file (survives server restarts;
    # QA-2026-07-16 #3: in the durable data dir so it also survives redeploys).
    from runtime_paths import data_dir as _data_dir
    _log_file = _data_dir() / "admin_audit.jsonl"
    try:
        with open(_log_file, "a", encoding="utf-8") as _f:
            import json as _json
            _f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # Never let audit logging failure crash a request


# audit #17: GET/PUT /god/settings and POST /god/freeze|/god/unfreeze were
# extracted VERBATIM to admin_god_controls.py (god_router, mounted in main.py).
# Paths/prefix are identical, so behaviour is unchanged. _audit and
# require_super_admin remain here and are imported by that module.


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Audit Log (#4)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/audit-log", summary="Get god mode audit log")
async def get_audit_log(_guard: None = Depends(require_super_admin)):
    # SECURITY-HIGH-001: Audit log contains source IPs, actor IDs, and operation
    # details — restrict to super_admin only.
    return {"entries": list(reversed(_god_mode_audit_log))}


# ═════════════════════════════════════════════════════════════════
#  BRSR NGRBC — Implementation Controller Endpoints
# ═════════════════════════════════════════════════════════════════
# Import lazily to avoid circular deps at module load
def _get_brsr_controller():
    from brsr_controller import (
        init_brsr_state, check_brsr_prerequisites,
        process_brsr_round, finalise_brsr_track,
        build_brsr_facilitator_status,
    )
    return (init_brsr_state, check_brsr_prerequisites,
            process_brsr_round, finalise_brsr_track,
            build_brsr_facilitator_status)


@admin_router.get(
    "/{session_id}/brsr/status",
    summary="Get BRSR NGRBC track status for a session (Facilitator Monitor)",
)
async def get_brsr_status(session_id: str, _guard: None = Depends(require_facilitator)):
    # SECURITY-HIGH-001: Session track status is facilitator-only information.
    """Returns the full BRSR facilitator monitor payload for one session."""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    _, _, _, _, build_status = _get_brsr_controller()
    gs = session.get("global_state", {})
    payload = build_status(gs)
    payload["session_id"] = session_id
    payload["brsr_enabled_globally"] = _god_mode_settings.get("brsr_ngrbc_enabled", False)
    return payload


@admin_router.get(
    "/{session_id}/brsr/prerequisites",
    summary="Check BRSR track prerequisite eligibility for a session",
)
async def check_brsr_prereqs(session_id: str, _guard: None = Depends(require_facilitator)):
    # SECURITY-HIGH-001: Prerequisite eligibility is facilitator-only information.
    """Returns eligibility, met/missing prerequisites, and god-mode override status."""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    _, check_prereqs, _, _, _ = _get_brsr_controller()
    gs = session.get("global_state", {})
    god_override = _god_mode_settings.get("brsr_ngrbc_enabled", False)
    result = check_prereqs(gs, god_mode_override=god_override)
    result["session_id"] = session_id
    return result


class BRSRRoundRequest(BaseModel):
    brsr_round: int        # 1–5
    choice: str            # "option_a" | "option_b" | "option_c"
    god_mode_override: bool = False


@admin_router.post(
    "/{session_id}/brsr/decide",
    summary="Process a BRSR round decision (Facilitator-controlled)",
)
async def process_brsr_decision(
    session_id: str,
    req: BRSRRoundRequest,
    # QA-2026-07-16 #2: the docstring says "Facilitator-controlled" but the
    # route was unguarded — any caller could apply BRSR consequences to a
    # team's state (and flip god_mode_override). Enforce the stated contract.
    _guard: None = Depends(require_sim_manager),
):
    """
    Submit a BRSR track round decision for a session.
    Applies all BRSR consequences to BU states, global_state, and flags.
    Finalises the track automatically after round 5.
    """
    if req.brsr_round < 1 or req.brsr_round > 5:
        raise HTTPException(400, "brsr_round must be 1–5")
    if req.choice not in ("option_a", "option_b", "option_c"):
        raise HTTPException(400, "choice must be option_a, option_b, or option_c")

    if not _god_mode_settings.get("brsr_ngrbc_enabled", False) and not req.god_mode_override:
        raise HTTPException(403, "BRSR NGRBC track is not enabled. Toggle brsr_ngrbc_enabled in God Mode.")

    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    init_state, _, process_round, finalise, build_status = _get_brsr_controller()

    gs = session.get("global_state", {})
    bus = session.get("bu_states", []) or gs.get("bu_states", [])

    # Initialise if needed
    completed_tracks = gs.get("active_event_flags", {})
    init_state(gs, bus, completed_tracks)

    # Process the round
    extra = process_round(
        round_number=req.brsr_round,
        choice=req.choice,
        global_state=gs,
        bu_states=bus,
    )

    # If round 5 complete, finalise and write back
    track_state = gs.get("_brsr_track_state", {})
    rounds_done = len(track_state.get("round_choices", {}))
    finalised = False
    if rounds_done >= 5:
        wb = finalise(gs)
        extra["brsr_track_finalised"] = True
        extra["write_back_flags"] = list(wb.keys())
        finalised = True

    # Persist session changes
    session["global_state"] = gs
    if bus:
        session["bu_states"] = bus
    await db.save_session(session_id, session)

    # Broadcast update to facilitator dashboards
    status = build_status(gs)
    await manager.broadcast_admin({
        "type": "brsr_round_processed",
        "session_id": session_id,
        "brsr_round": req.brsr_round,
        "choice": req.choice,
        "status": status,
        "finalised": finalised,
    })

    _audit("brsr_decision", details={
        "session_id": session_id,
        "brsr_round": req.brsr_round,
        "choice": req.choice,
        "finalised": finalised,
    })

    return {
        "session_id": session_id,
        "brsr_round": req.brsr_round,
        "choice": req.choice,
        "extra_events": extra,
        "current_status": status,
        "finalised": finalised,
    }


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — System Status / Overview (#5)
# ═════════════════════════════════════════════════════════════════

def _aggregate_brsr_intelligence(all_sessions: dict):
    """Aggregate BRSR NGRBC track intelligence across all sessions."""
    if not _god_mode_settings.get("brsr_ngrbc_enabled", False):
        return None
    completions = 0
    pioneer_count = 0
    greenwash_count = 0
    fragility_count = 0
    crises_injected = 0
    brsr_scores = []
    for sid, sess in all_sessions.items():
        gs = sess.get("global_state")
        if not gs:
            continue
        flags = gs.get("active_event_flags", {})
        if flags.get("brsr_track_completed"):
            completions += 1
        if flags.get("brsr_pioneer"):
            pioneer_count += 1
        if flags.get("brsr_greenwash_risk"):
            greenwash_count += 1
        if flags.get("governance_fragility"):
            fragility_count += 1
        if flags.get("brsr_greenwash_crisis"):
            crises_injected += 1
        if flags.get("brsr_governance_crisis"):
            crises_injected += 1
        if flags.get("spcb_show_cause"):
            crises_injected += 1
        score = flags.get("brsr_performance_score")
        if score is not None:
            brsr_scores.append(score)
    return {
        "brsr_track_completions": completions,
        "pioneer_count": pioneer_count,
        "greenwash_risk_count": greenwash_count,
        "governance_fragility_count": fragility_count,
        "crises_injected": crises_injected,
        "avg_brsr_score": sum(brsr_scores) / max(len(brsr_scores), 1) if brsr_scores else None,
    }


@admin_router.get("/god/system-status", summary="System-wide status overview")
async def get_system_status(_guard: None = Depends(require_facilitator)):
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

    # FIX: total_cohorts/total_players were counted from db._sessions, which only
    # exists in the in-memory backend — under Postgres it fell back to {} and the
    # God Mode overview always showed 0 cohorts / 0 players. count_sessions() is
    # mode-agnostic, so the counts are now correct in both backends.
    try:
        _sc = await db.count_sessions()
        total_cohorts = _sc.get("cohorts", total_cohorts)
        total_players = _sc.get("players", total_players)
    except Exception as _e:
        logging.warning(f"[god] count_sessions failed, using in-loop counts: {_e}")

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
            # BRSR NGRBC intelligence
            "brsr_intelligence": _aggregate_brsr_intelligence(all_sessions),
        },
    }


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — RBAC / Admin toggle (#6)
# ═════════════════════════════════════════════════════════════════

@admin_router.put("/facilitators/{fac_id}/admin", summary="Toggle admin flag")
async def toggle_facilitator_admin(fac_id: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def universal_broadcast(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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


@admin_router.post("/{cohort_id}/finale/ring-bell", summary="Trading-Floor Finale: broadcast market close to the room")
async def finale_ring_bell(cohort_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    """Feature 1 — Trading-Floor Finale. Broadcasts a 'market_close' signal so
    every player screen shows the close overlay and the projector view freezes
    and reveals the final ranking. Presentation-only: touches no game state.
    Gated by the caller's per-profile `trading_floor_enabled` capability
    (set at facilitator setup, mirroring the Shockwave gate)."""
    _require_console_capability(request, "trading_floor_enabled", "Trading Floor")
    payload = {
        "type": "market_close",
        "cohort_id": cohort_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast_students(payload)
    await manager.broadcast_admin(payload)
    _audit("finale_ring_bell", details={"cohort_id": cohort_id})
    return {"status": "bell_rung", "cohort_id": cohort_id}


@admin_router.post("/{cohort_id}/situation-room/bulletin", summary="Situation Room: synthesize a market-news voice bulletin")
async def situation_room_bulletin(cohort_id: str, request: Request, _guard: None = Depends(require_sim_manager)):
    """W-D (W4) — Situation-Room bulletin. Assembles a ~15-second market-news
    script from the cohort's REAL state (biggest EBITDA mover, live crisis
    flags, the Nordhaven NPC print) and synthesizes it through the same
    ElevenLabs plumbing the CEO interview owns. Facilitator-screen theatre
    only: reads state, writes nothing, broadcasts nothing to players.
    Gated by the caller's per-profile `situation_room_enabled` capability
    (403 when off), mirroring the Shockwave/Trading-Floor gates.
    Returns the script plus base64 MP3; audio_b64 is null when synthesis
    is unavailable (no key / API error) and the console falls back to a
    chyron-only bulletin."""
    _require_console_capability(request, "situation_room_enabled", "Situation Room")

    # Parity API: read sessions + round history via db.* (direct _sessions /
    # _global_states reads return {} under Postgres).
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}
    has_children = any(s.get("parent_cohort_id") == cohort_id for s in all_sessions.values())

    teams = []
    round_number = 1
    for sid, sess in all_sessions.items():
        is_child = sess.get("parent_cohort_id") == cohort_id
        is_self = sid == cohort_id
        if not (is_child or is_self):
            continue
        if is_self and has_children:
            continue  # prefer player sub-sessions over the parent shell
        gs_list = await db.fetch_round_history(sid)
        if not gs_list:
            continue
        latest = gs_list[-1].get("global_state", {})
        prev = gs_list[-2].get("global_state", {}) if len(gs_list) > 1 else None
        flags = latest.get("active_event_flags", {}) or {}
        round_number = max(round_number, int(gs_list[-1].get("round_number", 1) or 1))
        teams.append({
            "name": sess.get("player_name") or sess.get("cohort_name") or sid[:8],
            "ebitda": float(latest.get("historical_ebitda", 0) or 0),
            "prev_ebitda": float(prev.get("historical_ebitda", 0) or 0) if prev else None,
            "flags": [k for k, v in flags.items() if v],
            "competitor_ebitda": float(latest.get("competitor_ebitda", 0) or 0),
        })
    if not teams:
        raise HTTPException(status_code=404, detail="No active sessions found for this cohort.")

    from situation_room import assemble_bulletin_text
    text = assemble_bulletin_text(teams, round_number)

    audio_b64 = None
    try:
        from elevenlabs_tts import synthesize_speech
        audio_b64 = await synthesize_speech(text=text, voice_id="21m00Tcm4TlvDq8ikWAM")
    except Exception:
        audio_b64 = None

    _audit("situation_room_bulletin", details={"cohort_id": cohort_id, "chars": len(text), "voiced": audio_b64 is not None})
    return {"text": text, "audio_b64": audio_b64, "cohort_id": cohort_id, "round_number": round_number}


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Batch Facilitator Create (#9)
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/facilitators/batch", summary="Batch create facilitators")
async def batch_create_facilitators(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    names = body.get("names", [])
    if not names:
        raise HTTPException(400, "Provide a list of names")

    # GOD-002 + GOD-003: Generate passwords outside the lock (bcrypt is slow)
    # then assign IDs atomically inside the lock.
    passwords = [_generate_temp_password() for _ in names]  # list of (plain, hash) tuples

    created = []
    async with _fac_registry_lock:
        max_id = 0
        for f in _facilitator_registry:
            fid = f.get("facilitator_id", "")
            if fid.startswith("FAC-"):
                try:
                    max_id = max(max_id, int(fid[4:]))
                except ValueError:
                    pass
        existing_ids = {f["facilitator_id"] for f in _facilitator_registry}

        # M-3: credentials dict — plaintext passwords separate from the main object
        # so API gateway logs that record the response body don't capture all passwords.
        credentials: dict[str, str] = {}
        for name, (_plain, _hash) in zip(names, passwords):
            max_id += 1
            while f"FAC-{max_id:03d}" in existing_ids:
                max_id += 1
            new_fac_id = f"FAC-{max_id:03d}"
            fac = {
                "facilitator_id": new_fac_id,
                "name": name.strip(),
                "password": _hash,           # GOD-002 fix: store hash, not tuple
                "created_at": datetime.now(timezone.utc).isoformat(),
                "max_cohorts": 5,
                "cohorts_created": 0,
                "role": "facilitator",
                "is_admin": False,
                "enabled": True,
            }
            existing_ids.add(new_fac_id)
            _facilitator_registry.append(fac)
            created.append({k: v for k, v in fac.items() if k != "password"})
            credentials[new_fac_id] = _plain

    _audit("batch_facilitators_created", details={"count": len(created)})
    _persist_facilitators()
    return {
        "created": created,
        "credentials": credentials,
        "credentials_note": "Store these securely — they will not be shown again.",
        "total_facilitators": len(_facilitator_registry),
    }


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — System Export & Backup (#10)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/export", summary="Export full system state as JSON")
async def export_system(_guard: None = Depends(require_super_admin)):
    # SECURITY-CRIT-001: This endpoint dumps the entire system state including
    # facilitator records and audit logs. Super-admin auth required.
    # Passwords are stripped from the export payload to prevent offline cracking
    # even for authenticated callers — they serve no restore purpose.
    all_sessions = db._sessions if hasattr(db, '_sessions') else {}
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "facilitators": [
            {k: v for k, v in f.items() if k != "password"}
            for f in _facilitator_registry
        ],
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
async def import_system(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """Restore sessions and facilitators from a backup.
    Merge mode: existing session IDs are skipped, new ones are created.
    """
    sessions_imported = 0
    facilitators_imported = 0
    skipped = []

    # Import facilitators
    # GOD-010: Sanitise each imported record — never blindly trust the payload.
    # Passwords are dropped (force a reset), roles are validated against the
    # allowlist, and integer fields are clamped to safe ranges.
    incoming_facs = body.get("facilitators", [])
    existing_ids = {f.get("facilitator_id") for f in _facilitator_registry}
    for fac in incoming_facs:
        fid = fac.get("facilitator_id")
        if not fid:
            continue
        if fid in existing_ids:
            skipped.append(f"facilitator:{fid}")
            continue
        raw_role = fac.get("role", "facilitator")
        safe_fac = {
            "facilitator_id": str(fid)[:100],
            "name": str(fac.get("name", fid))[:200],
            "email": str(fac.get("email", ""))[:200],
            "contact_number": str(fac.get("contact_number", ""))[:50],
            "programme": str(fac.get("programme", ""))[:200],
            "start_date": str(fac.get("start_date", ""))[:20],
            "end_date": str(fac.get("end_date", ""))[:20],
            # Never import password hashes — all imported accounts must reset
            "password": "",
            "role": raw_role if raw_role in ROLE_HIERARCHY else "facilitator",
            "is_admin": is_admin_role(raw_role),
            "enabled": bool(fac.get("enabled", True)),
            "max_cohorts": max(0, min(int(fac.get("max_cohorts", 5)), 9999)),
            "cohorts_created": max(0, int(fac.get("cohorts_created", 0))),
            "created_at": str(fac.get("created_at", datetime.now(timezone.utc).isoformat()))[:40],
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "password_reset_required": True,  # signal to UI that a reset is needed
        }
        _facilitator_registry.append(safe_fac)
        existing_ids.add(fid)
        facilitators_imported += 1

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

    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot

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
async def gdpr_export(player_id: str, _guard: None = Depends(require_super_admin)):
    # SECURITY-CRIT-003: Full player PII, game decisions, and interview data.
    # Super-admin auth required — a separate player-facing self-service
    # endpoint (GET /api/simulations/{session_id}/my-data) is the correct
    # channel for data-subject access requests.
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
async def get_crisis_history(_guard: None = Depends(require_facilitator)):
    # SECURITY-HIGH-001: Crisis history reveals facilitator operational patterns.
    return {"history": list(reversed(_crisis_trigger_history))}


@admin_router.post("/god/crisis-fire", summary="Fire a crisis with history tracking")
async def fire_crisis_with_history(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    crisis_type = body.get("type", "unknown")
    target = body.get("target", "global")
    entry = {
        "id": f"CRS-{len(_crisis_trigger_history)+1:04d}",
        "type": crisis_type,
        "target": target,
        "fired_at": datetime.now(timezone.utc).isoformat(),
        "fired_by": "god_mode",
    }
    _capped_append(_crisis_trigger_history, entry)
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
async def update_engine_tunables(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    changed = {}
    for key, val in body.items():
        if key in _engine_tunables:
            old = _engine_tunables[key]
            _engine_tunables[key] = val
            changed[key] = {"old": old, "new": val}
    # Sync to god_mode_settings for backward compat
    _god_mode_settings["overrun_probability"] = _engine_tunables["overrun_probability"]
    _god_mode_settings["overrun_severity"] = _engine_tunables["overrun_severity"]
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    _audit("engine_tunables_updated", details=changed)
    return {"tunables": _engine_tunables, "changed": changed}


# ═════════════════════════════════════════════════════════════════
#  SCENARIO PRESETS — Pre-configured difficulty templates
# ═════════════════════════════════════════════════════════════════

_scenario_presets = [
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
async def save_cohort_pedagogical_settings(session_id: str, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
    """Store experience level, difficulty tier, and pedagogical toggles per-cohort."""
    from database_memory import _sessions as _dm_sessions
    session = _dm_sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Store per-cohort settings
    if "experience_level" in body:
        session["experience_level"] = body["experience_level"]
    if "difficulty_tier" in body:
        session["difficulty_tier"] = body["difficulty_tier"]
    
    # Store pedagogical toggle overrides on the session
    # Any recognised pedagogical toggle may be overridden per cohort. We derive
    # the allow-list from DEFAULT_PEDAGOGICAL_TOGGLES rather than hand-maintaining
    # a copy: that fixes a latent drift where engine-module toggles the cohort
    # modal sends (biodiversity, board governance, NPC agents, supply chain, …)
    # were silently dropped because they weren't in the old hard-coded set — so a
    # facilitator could never actually turn them OFF. This also keeps the
    # stakeholder-realism waves (F1–F6) and any future toggle in sync
    # automatically. get_pedagogical_toggles already ignores unknown keys, so
    # anything else in the body is harmlessly skipped.
    from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES
    pedagogical_keys = set(DEFAULT_PEDAGOGICAL_TOGGLES)
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
async def save_cohort_pacing(session_id: str, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
    """Store pacing mode and max unlocked round per-cohort.
    Once a facilitator sets pacing, God Mode cannot override it."""
    session = await db.get_session_info(session_id)
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

    # Fix #6: collect session-field changes and write them durably via the db
    # interface (Postgres metadata + mirror) in one call.
    _sess_updates = {}
    if "pacing_mode" in body:
        _sess_updates["pacing_mode"] = body["pacing_mode"]  # free_play | manual | scheduled
    if "max_unlocked_round" in body:
        _sess_updates["max_unlocked_round"] = int(body["max_unlocked_round"])
    if "round_schedules" in body:
        _sess_updates["round_schedules"] = body["round_schedules"]
    if _sess_updates:
        await db.update_session_metadata(session_id, _sess_updates)
        session.update(_sess_updates)

    # Update pacing ownership tracking in shared state
    pacing = _get_pacing(session_id)
    if source == "facilitator" and body.get("pacing_mode", "free_play") != "free_play":
        pacing["set_by"] = set_by or "unknown_facilitator"
    pacing["mode"] = body.get("pacing_mode", pacing.get("mode", "free"))
    mark_pacing_dirty(session_id)  # Fix #5: share pacing policy across workers + snapshot

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
        "max_unlocked_round": session.get("max_unlocked_round", SIM_ROUNDS),
        "set_by": pacing.get("set_by"),
    }

@admin_router.post("/scenario-presets/apply/{preset_id}", summary="Apply a scenario preset")
async def apply_scenario_preset(preset_id: str, _guard: None = Depends(require_super_admin)):
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
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    _audit("scenario_preset_applied", details={"preset": preset_id, "changed_count": len(changed)})
    return {"applied": preset_id, "name": preset["name"], "tunables": _engine_tunables, "changed": changed}


@admin_router.post("/scenario-presets", summary="Save a custom scenario preset")
async def save_custom_preset(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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
async def delete_custom_preset(preset_id: str, _guard: None = Depends(require_super_admin)):
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
    # Parity API: fetch_round_history reads the round history under BOTH the
    # memory and Postgres stores; a direct _global_states read returns {} under
    # Postgres. Each item is {round_number, global_state:{active_event_flags,…}}.
    rounds = await db.fetch_round_history(session_id)
    if not rounds:
        raise HTTPException(404, "No round data")

    feed = []
    for grs in rounds:
        rn = grs.get("round_number", 1)
        flags = grs.get("global_state", {}).get("active_event_flags", {})
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


@admin_router.get("/complexity-events-all", summary="Get complexity engine events for ALL cohorts")
async def get_complexity_events_all(_guard: None = Depends(require_facilitator)):
    """Aggregate complexity events across every cohort for cross-cohort comparison."""
    # Parity API (see get_complexity_events): read via fetch_all_sessions_raw /
    # fetch_round_history so this works under Postgres, not just the memory store.
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}

    cohorts = []
    for sid, sess in all_sessions.items():
        # Skip player sub-sessions and deleted sessions
        if sess.get("player_id") or sess.get("deleted_at"):
            continue

        rounds = await db.fetch_round_history(sid)
        if not rounds:
            continue

        feed = []
        for grs in rounds:
            rn = grs.get("round_number", 1)
            flags = grs.get("global_state", {}).get("active_event_flags", {})
            round_events = []
            for key, value in flags.items():
                if key in _COMPLEXITY_EVENT_LABELS and value:
                    icon, label, severity = _COMPLEXITY_EVENT_LABELS[key]
                    round_events.append({
                        "key": key, "icon": icon, "label": label,
                        "severity": severity, "value": value, "round": rn,
                    })
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
                if key == "competitor_warning" and value:
                    round_events.append({
                        "key": key, "icon": "🏆", "label": "Competitor Warning",
                        "severity": "warning", "value": value, "round": rn,
                    })
            if round_events:
                feed.append({"round": rn, "events": round_events})

        if feed:
            latest_gs = rounds[-1] if rounds else {}
            cohorts.append({
                "session_id": sid,
                "cohort_name": sess.get("cohort_name", sid[:12]),
                "round": latest_gs.get("round_number", 1),
                "total_events": sum(len(r["events"]) for r in feed),
                "feed": feed,
            })

    cohorts.sort(key=lambda c: -c["total_events"])
    return {"cohorts": cohorts, "total_cohorts": len(cohorts)}


# ═════════════════════════════════════════════════════════════════
#  SESSION HEALTH MONITOR — Live heatmap data
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/session-health", summary="Get health status of all sessions")
async def get_session_health(_guard: None = Depends(require_facilitator)):
    """
    Returns compact health indicators for each cohort.
    Status: active, idle, stuck, disconnected.
    """
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}
    now = datetime.now(timezone.utc)
    health = []

    for sid, sess in all_sessions.items():
        if sess.get("player_id") or sess.get("deleted_at"):
            continue  # Skip player sub-sessions and deleted sessions

        # Parity API: latest state via fetch_latest_state — its global_state
        # carries all unpacked fields under both stores; a direct _global_states
        # read returns {} under Postgres.
        latest = await db.fetch_latest_state(sid)
        latest_gs = latest["global_state"] if latest else {}
        round_num = latest["round_number"] if latest else 1

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
async def clone_session(session_id: str, body: dict = Body(...), _guard: None = Depends(require_facilitator)):
    """Deep-clone a cohort's current state into a new session."""
    import copy
    from admin_shared import _in_memory_backend_active
    # Cloning deep-copies round/BU state by writing into the in-memory dicts. That
    # is memory-store-only: under Postgres, round state lives in tables, so a dict
    # write would create a hollow clone with no state. Fail loudly rather than
    # silently forking an empty cohort. (A durable Postgres clone is a follow-up.)
    if not _in_memory_backend_active():
        raise HTTPException(
            status_code=501,
            detail="Session cloning (what-if fork) is only available with the in-memory "
                   "store, not the Postgres backend.",
        )
    all_sessions = getattr(db, '_sessions', {})  # tripwire-allow: memory-only feature, guarded above
    global_states = getattr(db, '_global_states', {})  # tripwire-allow
    bu_states_store = getattr(db, '_bu_states', {})  # tripwire-allow

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
#  AUTO-PAUSE TRIGGERS — Per-session configurable pause-on-event rules
#
#  Design: Each session has its own auto-pause config stored in
#  _auto_pause_triggers[session_id]. The _auto_pause_default is a
#  platform template used when a session has no config of its own;
#  changing the default does NOT retroactively affect existing sessions.
#  Super-admins may update the platform default via PUT /auto-pause.
#  Lead-facilitators configure their own sessions via:
#      GET/PUT /sessions/{session_id}/auto-pause
# ═════════════════════════════════════════════════════════════════

_AUTO_PAUSE_TRIGGER_KEYS = frozenset({
    "greenwashing_scandal",
    "technology_lockin_penalty",
    "tipping_point_reached",
    "dividend_ratchet_triggered",
    "stakeholder_fatigue_applied",
    "treasury_negative",
    "reputation_below_20",
})

# Platform default — used as a TEMPLATE for new sessions only.
# Does NOT apply globally to any running session.
_auto_pause_default: dict = {
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
    "pause_message": "\u23f8\ufe0f Simulation paused by facilitator for discussion.",
}

# Per-session configs: { session_id: { enabled, triggers, pause_message } }
_auto_pause_triggers: dict[str, dict] = {}


def _get_session_auto_pause(session_id: str) -> dict:
    """Return the auto-pause config for a specific session.
    Falls back to a deep copy of the platform default if the session
    has no config yet (so writes are always isolated per-session)."""
    import copy
    if session_id not in _auto_pause_triggers:
        _auto_pause_triggers[session_id] = copy.deepcopy(_auto_pause_default)
    return _auto_pause_triggers[session_id]


# ── Platform default endpoint (super_admin only) ──────────────────
@admin_router.get("/auto-pause", summary="Get platform auto-pause default template (super_admin)")
async def get_auto_pause_default(_guard: None = Depends(require_super_admin)):
    """Read the platform default template used when creating new session configs.
    Does not affect any currently running session."""
    return {"type": "platform_default", **_auto_pause_default}


@admin_router.put("/auto-pause", summary="Update platform auto-pause default template (super_admin)")
async def set_auto_pause_default(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """Update the platform default template. Only affects NEW sessions that have not
    yet been individually configured. Running sessions are unaffected."""
    if "enabled" in body:
        _auto_pause_default["enabled"] = bool(body["enabled"])
    if "triggers" in body:
        for key, val in body["triggers"].items():
            if key in _AUTO_PAUSE_TRIGGER_KEYS:
                _auto_pause_default["triggers"][key] = bool(val)
    if "pause_message" in body:
        _auto_pause_default["pause_message"] = str(body["pause_message"])
    _audit("auto_pause_default_updated", details=_auto_pause_default)
    return {"type": "platform_default", **_auto_pause_default}


# ── Per-session endpoints (lead_facilitator, own sessions only) ────
@admin_router.get(
    "/sessions/{session_id}/auto-pause",
    summary="Get auto-pause config for a specific session",
)
async def get_session_auto_pause(
    session_id: str,
    request: Request,
    _guard: None = Depends(require_facilitator),
):
    """Returns the auto-pause config for this session (or the platform default
    template if it has not been individually configured yet).
    Any facilitator who owns this session may read the config."""
    await _assert_session_ownership(request, session_id)
    config = _get_session_auto_pause(session_id)
    return {"session_id": session_id, **config}


@admin_router.put(
    "/sessions/{session_id}/auto-pause",
    summary="Configure auto-pause triggers for a specific session",
)
async def set_session_auto_pause(
    session_id: str,
    body: dict = Body(...),
    request: Request = None,
    _guard: None = Depends(require_lead_facilitator),
):
    """Set or update the auto-pause config for a specific session.
    Only affects this session — no other cohorts are changed.
    lead_facilitator may only configure sessions they own;
    super_admin may configure any session."""
    await _assert_session_ownership(request, session_id)
    cfg = _get_session_auto_pause(session_id)
    if "enabled" in body:
        cfg["enabled"] = bool(body["enabled"])
    if "triggers" in body:
        for key, val in body["triggers"].items():
            if key in _AUTO_PAUSE_TRIGGER_KEYS:
                cfg["triggers"][key] = bool(val)
    if "pause_message" in body:
        cfg["pause_message"] = str(body["pause_message"])
    _audit("auto_pause_updated", details={"session_id": session_id, **cfg})
    return {"session_id": session_id, **cfg}


@admin_router.delete(
    "/sessions/{session_id}/auto-pause",
    summary="Reset session auto-pause config to platform defaults",
)
async def reset_session_auto_pause(
    session_id: str,
    request: Request,
    _guard: None = Depends(require_lead_facilitator),
):
    """Removes the per-session config so this session falls back to the
    platform default template on next access."""
    await _assert_session_ownership(request, session_id)
    _auto_pause_triggers.pop(session_id, None)
    _audit("auto_pause_reset", details={"session_id": session_id})
    return {"session_id": session_id, "reset": True, **_auto_pause_default}


def check_auto_pause_triggers(session_id: str, events: dict, global_state: dict) -> Optional[str]:
    """Called by process_tick for a specific session to check if auto-pause should fire.
    Uses the per-session config; falls back to the platform default template."""
    cfg = _get_session_auto_pause(session_id)
    if not cfg["enabled"]:
        return None
    triggers = cfg["triggers"]
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
async def get_decision_history(session_id: str, _guard: None = Depends(require_facilitator)):
    """Reconstruct the complete decision history with state snapshots."""
    # Parity API: read rounds and decisions via db.* so the timeline populates
    # under Postgres (direct _global_states/_bu_states/_decision_log → {}/[] there).
    rounds = await db.fetch_round_history(session_id)
    if not rounds:
        raise HTTPException(404, "No history for this session")

    decision_log = await db.fetch_all_decisions()
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
        gs = grs.get("global_state", {})
        flags = gs.get("active_event_flags", {})
        bus = grs.get("business_units", [])

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
            "treasury_m": round(float(gs.get("corporate_treasury", 0)) / 1_000_000, 2),
            "reputation": round(float(gs.get("group_reputation", 50)), 1),
            "synergy": round(float(gs.get("synergy_multiplier", 1.0)), 3),
            "ebitda_m": round(float(gs.get("historical_ebitda", 0)) / 1_000_000, 2),
            "inflation": round(float(gs.get("inflation_index", 0.025)), 4),
            "cost_of_capital": round(float(gs.get("cost_of_capital", 0.05)), 4),
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

_annotations = {}  # session_id → [annotation dicts]


@admin_router.get("/annotations/{session_id}", summary="Get annotations for a session")
async def get_annotations(session_id: str):
    return {"annotations": _annotations.get(session_id, [])}


@admin_router.post("/annotations/{session_id}", summary="Add an annotation")
async def add_annotation(session_id: str, body: dict = Body(...), _guard: None = Depends(require_sim_manager)):
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
async def delete_annotation(session_id: str, annotation_id: str, _guard: None = Depends(require_sim_manager)):
    if session_id in _annotations:
        _annotations[session_id] = [a for a in _annotations[session_id] if a["id"] != annotation_id]
    return {"deleted": annotation_id}


@admin_router.put("/annotations/{session_id}/visibility", summary="Toggle student visibility of annotations")
async def set_annotations_visibility(session_id: str, body: dict = Body(...), _guard: None = Depends(require_sim_manager)):
    """Enable or disable student visibility of facilitator annotations for a cohort."""
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    player_visible = bool(body.get("player_visible", False))
    # Fix #6: durable write via the db interface (Postgres metadata + mirror).
    await db.update_session_metadata(session_id, {"annotations_player_visible": player_visible})
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
async def get_cross_paradigm_comparison(_guard: None = Depends(require_facilitator)):
    """
    Compare cohorts across different paradigms by normalizing Terminal Values.
    Adjusts for exit multiple and carbon tax differences so HC and NC cohorts
    can be fairly compared on strategic quality rather than structural advantages.

    Normalized_TV = Raw_TV × (ref_exit / paradigm_exit)
    """
    # Parity API: sessions + latest state via db.* (direct reads → {} on Postgres).
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}

    comparisons = []
    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            continue

        paradigm = sess.get("decision_paradigm", "legacy_abc")
        norms = _PARADIGM_NORMALIZATION.get(paradigm, _REFERENCE_PARADIGM)
        ref = _REFERENCE_PARADIGM

        _ls = await db.fetch_latest_state(sid)
        latest = _ls["global_state"] if _ls else {}
        _round = _ls["round_number"] if _ls else 1
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
            "round": _round,
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
async def get_cohort_comparison(facilitator_id: str = None, _guard: None = Depends(require_facilitator)):
    """Compare all cohorts (or a facilitator's cohorts) side by side."""
    # Parity API: sessions + latest state via db.* (direct reads → {} on Postgres).
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}

    comparisons = []
    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            continue
        if facilitator_id and sess.get("facilitator_id") != facilitator_id:
            continue

        _ls = await db.fetch_latest_state(sid)
        latest = _ls["global_state"] if _ls else {}
        _round = _ls["round_number"] if _ls else 1
        flags = latest.get("active_event_flags", {})

        comparisons.append({
            "session_id": sid,
            "cohort_name": sess.get("cohort_name", sid[:12]),
            "paradigm": sess.get("decision_paradigm", "legacy_abc"),
            "round": _round,
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
    # Parity API: sessions + round history via db.* (direct _sessions /
    # _global_states / _bu_states reads return {} under Postgres).
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}

    teams = []
    for sid, sess in all_sessions.items():
        # Only player sessions whose parent cohort matches, or the cohort session itself
        parent = sess.get("parent_cohort_id")
        if parent == cohort_id or sid == cohort_id:
            gs_list = await db.fetch_round_history(sid)
            history = {}
            cumulative_carbon_fee = 0.0

            for gs in gs_list:
                r = gs.get("round_number", 1)
                _g = gs.get("global_state", {})
                flags = _g.get("active_event_flags") or {}
                fee_this_round = flags.get("internal_carbon_fee_deducted", 0) or 0
                cumulative_carbon_fee += fee_this_round
                # Compute average SLO from BU states for this round
                buses_for_round = gs.get("business_units", [])
                avg_slo = (
                    sum(b.get("social_license_score", 50) for b in buses_for_round) / len(buses_for_round)
                    if buses_for_round else 50
                )
                history[r] = {
                    "treasury": _g.get("corporate_treasury", 0),
                    "reputation": _g.get("group_reputation", 50),
                    "carbon": _g.get("tco2e_emissions", 0),
                    "social_license": round(avg_slo, 1),
                    "synergy": _g.get("synergy_multiplier", 1.0),
                    # Climate-specific fields
                    "green_fund": _g.get("green_transition_fund", 0),
                    "cost_of_capital": _g.get("cost_of_capital", 0.05),
                    "carbon_fee_paid": cumulative_carbon_fee,
                }

            latest_item = gs_list[-1] if gs_list else {}
            latest = latest_item.get("global_state", {})
            latest_rn = latest_item.get("round_number", 1)
            flags = latest.get("active_event_flags", {}) or {}
            total_fee = sum(
                (gs.get("global_state", {}).get("active_event_flags", {}) or {}).get("internal_carbon_fee_deducted", 0) or 0
                for gs in gs_list
            )
            # Average SLO for the latest round
            latest_bus = latest_item.get("business_units", [])
            latest_slo = (
                sum(b.get("social_license_score", 50) for b in latest_bus) / len(latest_bus)
                if latest_bus else 50
            )
            
            # Extract real-world scenario traps
            active_traps = []
            if flags.get("cfo_austerity_active"): active_traps.append("🛑 Austerity")
            if flags.get("supplier_defection", {}).get("active"): active_traps.append("🏭 Defection")
            if flags.get("green_premium_squeeze", {}).get("active"): active_traps.append("📉 Squeeze")
            if flags.get("regulatory_ratchet", {}).get("active"): active_traps.append("⚖️ Ratchet")

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
                    "active_traps": active_traps,
                },
                "round": latest_rn,
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
async def set_cohort_pulse_visibility(cohort_id: str, body: dict = Body(...), _guard: None = Depends(require_sim_manager)):
    """
    Persists whether the CohortPulse KPI heatmap is visible to players.
    Called by the CohortPulse.js toggle switch.
    """
    sess = await db.get_session_info(cohort_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")
    player_visible = bool(body.get("player_visible", False))
    # Fix #6: durable write via the db interface (Postgres metadata + mirror).
    await db.update_session_metadata(cohort_id, {"cohort_pulse_player_visible": player_visible})
    return {"cohort_id": cohort_id, "player_visible": player_visible, "status": "saved"}


# ═════════════════════════════════════════════════════════════════
#  SIDE TRACK MANAGEMENT (God Mode → Facilitator → Cohort)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/side-tracks/catalog", summary="Get all registered side tracks")
async def get_side_track_catalog(caller_role: str = Depends(get_fac_role)):
    """Returns the full catalog of registered side tracks with metadata.
    This is a read-only endpoint showing what tracks are available in the codebase.

    Role-aware response (resolved via the canonical get_fac_role dependency —
    the same path used by require_super_admin/require_facilitator, which correctly
    handles god_mode virtual identity and registry re-validation):
    - super_admin / lead_facilitator: facilitator_can_assign=True for all tracks
      (they may assign any registered track to their cohort regardless of the
       global enabled list — no God Mode pre-authorization required).
    - facilitator: facilitator_can_assign=True only for globally enabled tracks.
    """
    from side_tracks import get_track_catalog

    catalog = get_track_catalog()
    available = _god_mode_settings.get("side_tracks_available", [])
    available_set = set(available)

    is_privileged = ROLE_HIERARCHY.get(caller_role, 0) >= ROLE_HIERARCHY.get("lead_facilitator", 2)

    for entry in catalog:
        entry["enabled_globally"] = entry["track_id"] in available_set
        # lead_facilitators and super_admins can always assign any registered track
        entry["facilitator_can_assign"] = is_privileged or (entry["track_id"] in available_set)

    return {
        "catalog": catalog,
        "caller_role": caller_role,
        "globally_enabled": available,
    }


@admin_router.put("/side-tracks/global", summary="Set the default side-track pool for base facilitators (God Mode)")
async def update_global_side_tracks(request: Request, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """God Mode master control: set the DEFAULT side-track pool.

    C5/I6 (Workstream E) — one authoritative statement of the rule, mirrored in
    assign_cohort_side_tracks: this pool gates BASE facilitators only. Lead
    facilitators and above may assign any registered track regardless of this
    pool (their bypass is audited in assign_cohort_side_tracks). So this control
    is the default pool for base facilitators, not a hard platform-wide gate.

    I5: god_mode callers must supply a 'reason' for the audit trail.
    """
    _caller_role = _require_god_mode_reason(request, body.get("reason"))
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
    mark_godmode_dirty()  # QA-2026-07-16 #5: publish god-mode change to workers + snapshot
    _audit("side_tracks_global_updated", details={
        "available_tracks": available, "_caller_role": _caller_role, "_reason": body.get("reason"),
    })
    return {"status": "ok", "available_tracks": available}


@admin_router.get("/side-tracks/facilitator-permissions", summary="Get per-facilitator side track permissions")
async def get_facilitator_side_track_permissions():
    """Returns the mapping of facilitator IDs to their permitted side tracks."""
    perms = _god_mode_settings.get("side_tracks_facilitator_permissions", {})
    available = _god_mode_settings.get("side_tracks_available", [])
    return {"permissions": perms, "globally_available": available}


@admin_router.put("/side-tracks/facilitator-permissions/{fac_id}", summary="Set side track permissions for a facilitator")
async def set_facilitator_side_track_permissions(fac_id: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
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


# =================================================================
#  TURNAROUND MODULE -- permission spine (God Mode -> Facilitator grant)
#  P1: the module is a post-completion, optional add-on. A normal run is
#  complete at R10; this never changes that. Two keys are required before any
#  facilitator can orchestrate it: (1) global enable, (2) per-facilitator grant.
#  Mirrors the side-track global-pool / per-facilitator-permission pattern above.
#  Orchestration + player endpoints (open/commit/advance) are P3 and gate on
#  require_sim_manager -- project_admin is excluded there by design.
# =================================================================

@admin_router.put("/turnaround/global", summary="Enable/disable the post-completion Turnaround module (God Mode)")
async def update_turnaround_global(request: Request, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """God Mode master switch for the Turnaround module. OFF by default.

    I5: god_mode callers must supply a 'reason' for the audit trail.
    Disabling globally does not delete per-facilitator grants; it simply makes
    them inert (can_orchestrate_turnaround returns False while disabled)."""
    _caller_role = _require_god_mode_reason(request, body.get("reason"))
    enabled = body.get("enabled")
    if not isinstance(enabled, bool):
        raise HTTPException(400, "'enabled' must be a boolean")

    _god_mode_settings["turnaround_module_enabled"] = enabled
    mark_godmode_dirty()  # publish god-mode change to workers + snapshot
    _audit("turnaround_module_global_updated", details={
        "enabled": enabled, "_caller_role": _caller_role, "_reason": body.get("reason"),
    })
    return {"status": "ok", "turnaround_module_enabled": enabled}


@admin_router.get("/turnaround/facilitator-permissions", summary="Get per-facilitator turnaround orchestration grants")
async def get_turnaround_permissions(_guard: None = Depends(require_super_admin)):
    """Returns the module's global switch and the set of facilitators granted
    orchestration rights."""
    perms = _god_mode_settings.get("turnaround_facilitator_permissions", {})
    return {
        "module_enabled": _god_mode_settings.get("turnaround_module_enabled", False),
        "permissions": perms,
    }


@admin_router.put("/turnaround/facilitator-permissions/{fac_id}", summary="Grant/revoke turnaround orchestration for a facilitator")
async def set_turnaround_permission(fac_id: str, body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    """God Mode: grant or revoke Turnaround orchestration for a specific
    facilitator. A grant is rejected unless the module is globally enabled first
    (parity with side-track permissions)."""
    granted = body.get("granted")
    if not isinstance(granted, bool):
        raise HTTPException(400, "'granted' must be a boolean")
    if granted and not _god_mode_settings.get("turnaround_module_enabled", False):
        raise HTTPException(400, "Turnaround module not globally enabled. Enable it first via PUT /turnaround/global")

    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == fac_id), None)
    if not fac:
        raise HTTPException(404, f"Facilitator {fac_id} not found")

    perms = _god_mode_settings.setdefault("turnaround_facilitator_permissions", {})
    if granted:
        perms[fac_id] = True
    else:
        perms.pop(fac_id, None)
    mark_godmode_dirty()
    _persist_facilitators()
    _audit("turnaround_permission_updated", details={"facilitator_id": fac_id, "granted": granted})
    return {"status": "ok", "facilitator_id": fac_id, "granted": granted}


@admin_router.get("/turnaround/eligibility/{session_id}", summary="Check if a completed session may enter the Turnaround arc")
async def turnaround_eligibility(session_id: str, request: Request,
                                 role: str = Depends(get_fac_role),
                                 _guard: None = Depends(require_sim_manager)):
    """Facilitator-facing eligibility for the post-completion Turnaround module.
    Combines the two-key permission check (can_orchestrate_turnaround) with the
    score-based gate (canonical M_R < threshold) and completion state. Ownership
    is enforced so a facilitator only sees their own sessions."""
    from admin_shared import can_orchestrate_turnaround
    from auth_jwt import get_facilitator_from_request
    from config import TURNAROUND_ARC_MR_THRESHOLD, TURNAROUND_ARC_MAX_ROUNDS
    from engine import turnaround_score_eligible

    await _assert_session_ownership(request, session_id)
    fac_id = get_facilitator_from_request(request) or ""

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]
    flags = gs.get("active_event_flags", {})
    rn = latest.get("round_number", gs.get("round_number", 1))
    completed = rn >= 10 or bool(gs.get("game_over"))

    canonical = gs.get("final_report_canonical") or {}
    mr = canonical.get("regenerative_multiple",
                       flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)))

    module_on = _god_mode_settings.get("turnaround_module_enabled", False)
    permitted = can_orchestrate_turnaround(role, fac_id)
    already = bool(flags.get("turnaround_status")) or bool(gs.get("turnaround_mode"))
    score_ok = completed and turnaround_score_eligible(mr)
    eligible = bool(module_on and permitted and score_ok and not already)

    return {
        "session_id": session_id,
        "eligible": eligible,
        "module_enabled": module_on,
        "caller_permitted": permitted,
        "completed": completed,
        "score_eligible": score_ok,
        "already_run": already,
        "current_mr": round(float(mr), 3) if isinstance(mr, (int, float)) else mr,
        "threshold": TURNAROUND_ARC_MR_THRESHOLD,
        "max_rounds": TURNAROUND_ARC_MAX_ROUNDS,
    }


# ═════════════════════════════════════════════════════════════════
#  TURNAROUND MODULE — orchestration (P3). Facilitator-driven; every
#  endpoint gates on require_sim_manager (project_admin excluded) + session
#  ownership + the two-key can_orchestrate_turnaround permission. A normal run
#  stays complete at R10; these only ever append turnaround state and the
#  amended report — final_report_canonical is never mutated.
# ═════════════════════════════════════════════════════════════════

@admin_router.post("/turnaround/{session_id}/open", summary="Open the post-completion Turnaround arc (facilitator)")
async def turnaround_open(session_id: str, request: Request,
                          role: str = Depends(get_fac_role),
                          _guard: None = Depends(require_sim_manager)):
    from admin_shared import can_orchestrate_turnaround
    from auth_jwt import get_facilitator_from_request
    from config import TURNAROUND_ARC_MR_THRESHOLD
    from engine import turnaround_score_eligible
    import turnaround_engine as te

    await _assert_session_ownership(request, session_id)
    fac_id = get_facilitator_from_request(request) or ""
    if not _god_mode_settings.get("turnaround_module_enabled", False):
        raise HTTPException(403, "Turnaround module is not enabled")
    if not can_orchestrate_turnaround(role, fac_id):
        raise HTTPException(403, "You are not permitted to orchestrate the Turnaround module")

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]; bus = latest["bu_states"]
    flags = gs.get("active_event_flags", {})
    if gs.get("turnaround_mode"):
        raise HTTPException(409, "Turnaround already active for this session")
    if flags.get("turnaround_status") in ("graduated", "expired"):
        raise HTTPException(409, "Turnaround has already been run for this session")
    rn = latest.get("round_number", gs.get("round_number", 1))
    if not (rn >= 10 or gs.get("game_over")):
        raise HTTPException(409, "Session has not completed its 10 rounds")
    canon = gs.get("final_report_canonical") or {}
    mr = canon.get("regenerative_multiple",
                   flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)))
    if not turnaround_score_eligible(mr):
        raise HTTPException(409, f"Not eligible: M_R {mr} is not below {TURNAROUND_ARC_MR_THRESHOLD}")

    result = te.enter_arc(gs, bus)
    await db.update_latest_global_state(session_id, gs, bus)
    _audit("turnaround_opened", details={"session_id": session_id, "by": fac_id})
    return {"ok": True, **result}


@admin_router.post("/turnaround/{session_id}/commit", summary="Commit a Turnaround round decision (facilitator)")
async def turnaround_commit(session_id: str, request: Request, body: dict = Body(...),
                            role: str = Depends(get_fac_role),
                            _guard: None = Depends(require_sim_manager)):
    import turnaround_engine as te
    await _assert_session_ownership(request, session_id)
    choice = body.get("choice")

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]; bus = latest["bu_states"]
    if not gs.get("turnaround_mode"):
        raise HTTPException(409, "Session is not in turnaround mode")
    cfg = te.get_turnaround_round_config(int(gs.get("turnaround_round", 1)))
    if not cfg or choice not in cfg["options"]:
        raise HTTPException(400, f"Invalid choice; expected one of {list((cfg or {}).get('options', {}))}")
    try:
        result = te.apply_commit(gs, bus, choice)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await db.update_latest_global_state(session_id, gs, bus)
    _audit("turnaround_committed", details={
        "session_id": session_id, "choice": choice,
        "round": result.get("turnaround_round"), "phase": result.get("phase"),
        "arc_complete": result.get("arc_complete"),
    })
    return {"ok": True, **result}


@admin_router.post("/turnaround/{session_id}/abort", summary="Abort an in-flight Turnaround arc (facilitator)")
async def turnaround_abort(session_id: str, request: Request,
                           role: str = Depends(get_fac_role),
                           _guard: None = Depends(require_sim_manager)):
    import turnaround_engine as te
    await _assert_session_ownership(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]; bus = latest["bu_states"]
    if not gs.get("turnaround_mode"):
        raise HTTPException(409, "No active turnaround to abort")
    result = te.abort_arc(gs, bus)
    await db.update_latest_global_state(session_id, gs, bus)
    _audit("turnaround_aborted", details={"session_id": session_id})
    return {"ok": True, **result}


@admin_router.get("/turnaround/{session_id}/state", summary="Current Turnaround arc state (facilitator)")
async def turnaround_state(session_id: str, request: Request,
                           role: str = Depends(get_fac_role),
                           _guard: None = Depends(require_sim_manager)):
    import turnaround_engine as te
    await _assert_session_ownership(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")
    gs = latest["global_state"]
    return {"session_id": session_id, **te.arc_state(gs)}


@admin_router.put("/cohorts/{session_id}/side-tracks", summary="Assign side tracks to a cohort (Facilitator)")
async def assign_cohort_side_tracks(
    session_id: str,
    body: dict = Body(...),
    caller_role: str = Depends(get_fac_role),
    _guard: None = Depends(require_facilitator),
):
    """Facilitator endpoint: assign side tracks to a specific cohort.

    Permission model (enforced via the canonical get_fac_role dependency —
    the same path used by all other privileged endpoints, which correctly
    handles god_mode virtual identity, registry re-validation, and disabled
    accounts; no ad-hoc role lookup needed here):

    - super_admin / lead_facilitator / god_mode: may assign ANY registered
      track without God Mode pre-authorization.
    - facilitator: may only assign tracks that God Mode has enabled globally
      OR that have been explicitly granted to their facilitator account.

    Includes timing configuration (unlock_after_round)."""
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    tracks = body.get("tracks", [])
    timing = body.get("timing", {})
    if not isinstance(tracks, list):
        raise HTTPException(400, "'tracks' must be a list of track IDs")

    # Privileged roles (super_admin, lead_facilitator, god_mode) bypass
    # per-facilitator track restrictions — they may assign any registered track.
    is_privileged = ROLE_HIERARCHY.get(caller_role, 0) >= ROLE_HIERARCHY.get("lead_facilitator", 2)

    # C5/I6 (Workstream E): make the deliberate pool bypass OBSERVABLE. When a
    # privileged caller assigns tracks outside the global default pool, record it
    # so "what is enabled" stays auditable across roles (the pool gates base
    # facilitators only; leads+ legitimately bypass it).
    _pool = set(_god_mode_settings.get("side_tracks_available", []))
    _off_pool = set(tracks) - _pool
    if is_privileged and _off_pool:
        _audit("sidetrack_pool_bypassed", details={
            "session_id": session_id,
            "off_pool_tracks": sorted(_off_pool),
            "caller_role": caller_role,
        })

    # Validate against facilitator permissions (skipped for privileged roles)
    if not is_privileged:
        fac_id = sess.get("facilitator_id")
        if fac_id:
            perms = _god_mode_settings.get("side_tracks_facilitator_permissions", {})
            permitted = set(perms.get(fac_id, []))
            # If no explicit permissions set, fall back to globally available
            if not permitted:
                permitted = set(_god_mode_settings.get("side_tracks_available", []))
            # Also allow tracks pre-configured on the facilitator's own profile
            # (set by super_admin at account creation time — implicit authorization)
            fac_rec = next((f for f in _facilitator_registry if f.get("facilitator_id") == fac_id), None)
            if fac_rec and fac_rec.get("side_tracks"):
                permitted |= set(fac_rec["side_tracks"])
            unauthorized = set(tracks) - permitted
            if unauthorized:
                raise HTTPException(
                    403,
                    f"Facilitator {fac_id} not permitted to assign: {sorted(unauthorized)}. "
                    f"Ask a super_admin to enable them globally, or use a lead_facilitator account.",
                )


    # Validate track IDs exist
    from side_tracks import get_all_tracks
    registered = set(get_all_tracks().keys())
    invalid = set(tracks) - registered
    if invalid:
        raise HTTPException(400, f"Unknown track IDs: {sorted(invalid)}")

    # Auto-derive timing from track available_window if not explicitly provided.
    # Hard floor: side tracks may never unlock before Round 2 is complete
    # (i.e., unlock_after_round must be >= 2).
    SIDE_TRACK_MIN_UNLOCK_AFTER = 2
    from side_tracks import get_track as _get_st
    for tid in tracks:
        raw_unlock = None
        if tid in timing:
            raw_unlock = timing[tid].get("unlock_after_round")
        else:
            t = _get_st(tid)
            if t:
                raw_unlock = t.available_window[0] - 1
        if raw_unlock is not None:
            timing[tid] = {"unlock_after_round": max(SIDE_TRACK_MIN_UNLOCK_AFTER, raw_unlock)}
        else:
            timing[tid] = {"unlock_after_round": SIDE_TRACK_MIN_UNLOCK_AFTER}

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

    # Fix #6: store all side-track fields via one durable db write (Postgres
    # metadata + mirror) instead of mutating the memory dict directly.
    await db.update_session_metadata(session_id, {
        "active_side_tracks": tracks,
        "side_track_timing": timing,  # e.g. {"supply_chain": {"unlock_after_round": 3}}
        "side_track_states": existing_states,
    })

    # Auto-enable God Mode flag for BRSR when the track is assigned
    if "brsr_ngrbc" in tracks and not _god_mode_settings.get("brsr_ngrbc_enabled"):
        _god_mode_settings["brsr_ngrbc_enabled"] = True
        mark_godmode_dirty()  # Fix #5: publish/persist the freeze/settings change

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
async def what_if_replay(session_id: str, body: dict = Body(...), _guard: None = Depends(require_sim_manager)):
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
async def normalized_leaderboard(_guard: None = Depends(require_facilitator)):
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
async def apply_industry_vertical(vertical_id: str, session_id: str, request: Request, _guard: None = Depends(require_facilitator)):
    """Injects the selected industry vertical's materiality config into the session's
    global_state as 'materiality_dictionary_override'. This causes Round 2 to use
    the vertical's issues instead of the default global dictionary.

    Also stamps 'industry_vertical_applied' flag in active_event_flags so the
    teleprompter can surface industry-specific teaching notes.
    Propagates to all child player sessions."""
    # SAFETY GATE: a facilitator may apply a vertical ONLY to a cohort they
    # own — never to another facilitator's session. (The write below is
    # already session-scoped: it sets materiality_dictionary_override on the
    # target session and NEVER touches the global dictionary.)
    await _assert_session_ownership(request, session_id)

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
async def submit_mod4_crisis_choices(session_id: str, request: Request, body: dict = Body(...)):
    """Processes per-BU CBAM/ETS crisis choices submitted by RegulatoryShockModule.js.

    Body:
        choices: dict[bu_id, 'eat' | 'pass' | 'abate']
        effective_fee: float   (carbon price at submission, e.g. 90)

    Stamps 'cbam_crisis_choices' into active_event_flags, applies treasury/SLO
    deltas to each matching BU state, and records 'mod4_completed' flag.
    Propagates to all child player sessions."""
    # QA-2026-07-16 #2: this is a PLAYER-facing route (called from the player
    # cockpit) that was unguarded — anyone holding another team's session id
    # could submit crisis choices for them. Bind the caller to the session it
    # mutates, same contract as every /api/simulations state-changing route:
    # solo/unowned sessions pass; owned sessions require the matching
    # X-Player-Id or an authenticated facilitator JWT. (Function-level import:
    # router.py imports from admin_router at module load, so a top-level
    # import here would be circular.)
    from router import _assert_player_owns_session
    await _assert_player_owns_session(request, session_id)

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


# ═════════════════════════════════════════════════════════════════
#  PILLAR CONFIG ENDPOINTS (Phase 4.1.5)
#  GET/POST/PUT/DELETE for vertical-specific pillar areas.
#  Access: god_mode and lead_facilitator.
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/pillar-config/{bu_id}",
    summary="Get full pillar config for a vertical (standard + overrides + custom)",
)
async def get_pillar_config(
    bu_id: str,
    _guard: None = Depends(require_facilitator),
):
    """Returns the combined pillar summary for a given vertical."""
    from pillar_configs import get_pillar_summary
    return get_pillar_summary(bu_id)


@admin_router.post(
    "/pillar-config/{bu_id}/custom-areas",
    summary="Add a new custom pillar area for a vertical",
)
async def add_custom_pillar_area(
    bu_id: str,
    body: dict = Body(...),
    _guard: None = Depends(require_facilitator),
):
    """Append a new custom pillar area to the vertical's overrides JSON."""
    from pillar_configs import _load_pillar_overrides, _save_pillar_overrides

    area_key = body.get("area_key", "").strip()
    if not area_key:
        raise HTTPException(status_code=400, detail="area_key is required.")
    if not body.get("label"):
        raise HTTPException(status_code=400, detail="label is required.")
    if len(body.get("options", {})) < 2:
        raise HTTPException(status_code=400, detail="At least 2 options are required.")

    data = _load_pillar_overrides(bu_id)
    custom_areas = data.get("custom_areas", [])

    if any(ca.get("area_key") == area_key for ca in custom_areas):
        raise HTTPException(status_code=409, detail=f"Custom area '{area_key}' already exists.")

    new_area = {
        "area_key": area_key,
        "label": body["label"],
        "icon": body.get("icon", "⭐"),
        "order": body.get("order", len(custom_areas) + 6),
        "options": body.get("options", {}),
    }
    custom_areas.append(new_area)
    data["custom_areas"] = custom_areas
    data["bu_id"] = bu_id
    _save_pillar_overrides(bu_id, data)

    return {"status": "ok", "bu_id": bu_id, "area_key": area_key, "custom_areas": custom_areas}


@admin_router.put(
    "/pillar-config/{bu_id}/custom-areas/{area_key}",
    summary="Edit a custom pillar area",
)
async def edit_custom_pillar_area(
    bu_id: str,
    area_key: str,
    body: dict = Body(...),
    _guard: None = Depends(require_facilitator),
):
    """Update a custom pillar area by area_key."""
    from pillar_configs import _load_pillar_overrides, _save_pillar_overrides

    data = _load_pillar_overrides(bu_id)
    custom_areas = data.get("custom_areas", [])

    idx = next((i for i, ca in enumerate(custom_areas) if ca.get("area_key") == area_key), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Custom area '{area_key}' not found.")

    custom_areas[idx].update({k: v for k, v in body.items() if k != "area_key"})
    data["custom_areas"] = custom_areas
    _save_pillar_overrides(bu_id, data)

    return {"status": "ok", "bu_id": bu_id, "area_key": area_key, "updated": custom_areas[idx]}


@admin_router.delete(
    "/pillar-config/{bu_id}/custom-areas/{area_key}",
    summary="Delete a custom pillar area",
)
async def delete_custom_pillar_area(
    bu_id: str,
    area_key: str,
    _guard: None = Depends(require_facilitator),
):
    """Remove a custom pillar area by area_key."""
    from pillar_configs import _load_pillar_overrides, _save_pillar_overrides

    data = _load_pillar_overrides(bu_id)
    custom_areas = data.get("custom_areas", [])
    before = len(custom_areas)
    data["custom_areas"] = [ca for ca in custom_areas if ca.get("area_key") != area_key]

    if len(data["custom_areas"]) == before:
        raise HTTPException(status_code=404, detail=f"Custom area '{area_key}' not found.")

    _save_pillar_overrides(bu_id, data)
    return {"status": "deleted", "bu_id": bu_id, "area_key": area_key}


@admin_router.put(
    "/pillar-config/{bu_id}/order",
    summary="Reorder custom pillar areas",
)
async def reorder_pillar_areas(
    bu_id: str,
    body: dict = Body(...),
    _guard: None = Depends(require_facilitator),
):
    """
    Reorder custom areas.
    Body: { "order": ["area_key_1", "area_key_2", ...] }
    """
    from pillar_configs import _load_pillar_overrides, _save_pillar_overrides

    ordered_keys = body.get("order", [])
    data = _load_pillar_overrides(bu_id)
    custom_areas = data.get("custom_areas", [])

    key_to_order = {k: i + 6 for i, k in enumerate(ordered_keys)}
    for ca in custom_areas:
        ak = ca.get("area_key", "")
        if ak in key_to_order:
            ca["order"] = key_to_order[ak]

    data["custom_areas"] = sorted(custom_areas, key=lambda x: x.get("order", 99))
    _save_pillar_overrides(bu_id, data)

    return {"status": "ok", "bu_id": bu_id, "new_order": [ca["area_key"] for ca in data["custom_areas"]]}


# ═════════════════════════════════════════════════════════════════
#  REGIONAL ESG REPORT ENDPOINT (Phase 4.2)
# ═════════════════════════════════════════════════════════════════

@admin_router.get(
    "/{session_id}/regional-esg-report",
    summary="Generate a framework-aligned ESG report for a session",
)
async def get_regional_esg_report(
    session_id: str,
    _guard: None = Depends(require_facilitator),
):
    """Generate a region-appropriate ESG report shell based on session metadata."""
    from regional_reporting import generate_regional_report
    from datetime import datetime, timezone

    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session_meta = current.get("global_state", {}).get("metadata", {})
    session_meta["session_id"] = session_id

    final_state = {
        "global_state": current.get("global_state", {}),
        "bu_states": current.get("bu_states", []),
    }

    report = generate_regional_report(session_meta, final_state)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return report


# ═════════════════════════════════════════════════════════════════
#  INDUSTR