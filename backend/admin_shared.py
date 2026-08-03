"""
Muressons Global Corporation — Admin Shared State
Shared in-memory state and utilities used by all admin sub-routers.
Extracted from admin_router.py (ARCH-002) to decouple domain modules.

All other modules that previously imported from admin_router should now
import shared state from this module instead.
"""
from __future__ import annotations

import asyncio
import logging
import os
import json
from datetime import datetime, timezone
from typing import Any, Optional

_shared_logger = logging.getLogger("muressons.admin_shared")

from config import MASTER_PASSWORD

# GOD-004: Protects check_and_increment_cohort_count against concurrent
# session creation racing through the read-check-increment sequence.
_cohort_lock: asyncio.Lock = asyncio.Lock()

# ═════════════════════════════════════════════════════════════════
#  3-TIER ROLE MODEL
# ═════════════════════════════════════════════════════════════════

ROLE_HIERARCHY = {
    # C6: god_mode is the virtual break-glass identity — a DISTINCT top tier,
    # not an alias of super_admin. Level 4 > super_admin(3), so it clears every
    # level-gated super-admin check automatically while remaining a separate
    # role string. It is NOT assignable to a registry facilitator (see
    # _ASSIGNABLE_ROLES) — it is granted only via the signed-token identity.
    "god_mode": 4,
    "super_admin": 3,
    "admin": 3,           # M-5: alias for super_admin — prevents undefined hierarchy level
    "lead_facilitator": 2,
    "facilitator": 1,
    # C4: project_admin provisions facilitators + cohorts but NEVER manages runs.
    # It is a DISTINCT role from facilitator — level 0 places it OFF the run
    # ladder entirely (strictly below facilitator=1 and lead=2, so it can never
    # satisfy require_lead_facilitator). Its provisioning powers are gated by
    # name (require_registry_admin), not by level, and its run exclusion is
    # enforced by require_sim_manager. Level 0 (not the old 1) removes the
    # has_role_level(project_admin,'facilitator')==True inversion.
    #
    # RBAC-F5b (2026-08-01): project_admin exists in TWO forms, both legitimate
    # and identical at every guard — the docs used to say only "virtual":
    #   * VIRTUAL   — the PROJECT_ADMIN_PASSWORD break-glass identity (literal
    #                 id "project_admin", one shared secret, no individual
    #                 accountability; disabled when the env var is unset).
    #   * REGISTRY  — a normal FAC-NNN account carrying role "project_admin",
    #                 assignable by a super_admin. PREFERRED for a named
    #                 programme administrator: per-person, auditable, revocable.
    # Level 0 ranks RUN authority, not provisioning authority — see
    # assignable_roles_for, which is why a level-0 role may still mint leads.
    "project_admin": 0,
}

# Roles that may be ASSIGNED to a registry facilitator. Excludes god_mode, the
# virtual level-4 break-glass identity that is granted only via signed-token
# identity and must never be creatable/settable through the registry API
# (that would be an escalation above super_admin). Used by create_facilitator,
# bulk_create_facilitators and update_facilitator_role.
_ASSIGNABLE_ROLES = {"super_admin", "admin", "lead_facilitator", "facilitator", "project_admin"}


def assignable_roles_for(caller_role: str) -> set[str]:
    """C1/P1: which roles a caller of ``caller_role`` may grant when creating or
    updating a facilitator. A caller may never grant a role above its own tier,
    and god_mode is never assignable by anyone.

    RBAC-F5a (2026-08-01): project_admin is the ONE deliberate exception to the
    'never above your own tier' rule, and it is NOT a level comparison. Its
    level (0) places it OFF the run ladder — a run-authority ranking, not a
    provisioning-authority ranking. As a provisioning role its whole job is to
    stand up facilitators (including leads), so it may grant lead_facilitator
    and facilitator despite sitting below them on the RUN ladder. It may never
    grant super_admin or god_mode, nor another project_admin, so the delegation
    cannot spread.

    RBAC-F5b — THE TRUST MODEL, stated plainly because it is easy to miss:
    whoever provisions an account learns its initial credential (returned once
    at creation, and defaults are the deterministic FAC-NNN@321). A
    project_admin can therefore mint a lead_facilitator and sign in as it
    before the intended owner does, acquiring the run rights its own role is
    denied. That is inherent to delegated provisioning, not a hole in these
    checks: must_change_password makes the takeover VISIBLE (the rightful owner
    finds their default rejected), and the ceiling above stops it reaching
    admin tiers. Give project_admin only to someone you would be willing to
    make a lead facilitator. To make it strictly weaker, return just
    {"facilitator"} here — one line."""
    if caller_role == "project_admin":
        return {"lead_facilitator", "facilitator"}
    caller_level = ROLE_HIERARCHY.get(caller_role, 0)
    # Grant only assignable roles at or below the caller's own level.
    return {r for r in _ASSIGNABLE_ROLES if ROLE_HIERARCHY.get(r, 0) <= caller_level}

# Tabs accessible at each role level
ROLE_ALLOWED_TABS = {
    "facilitator": [
        "dashboard_home", "timeline", "teleprompter", "leaderboard",
        "registry", "session_viewer", "impersonate", "swipe_file",
        "broadcast", "platform_analytics", "cohort_comparison",
        "complexity_feed", "decision_replay", "debrief", "dna_comparison",
        "scorecard_evaluator", "bonuses", "peer_eval", "reports",
        "notes", "annotations", "teaching_journal", "technical_glossary",
        "intervention_config",
        # ESG Leadership Profile rubric editor — moved to the base facilitator
        # dashboard (all run-managing facilitators tune the rubric; project_admin
        # never sees it because its tab set is fixed, not cumulative).
        "esg_weights",
        # DN-1 (UX audit §9): auto-assembled debrief narrative — divergence
        # round, per-player turning points, predicted-vs-actual. Base
        # facilitator tier: it is read-only over completed rounds.
        "debrief_narrative",
    ],
    "lead_facilitator": [
        # All facilitator tabs plus:
        # NOTE: "materiality" (the Materiality Matrix editor) is intentionally
        # NOT here — editing the materiality matrix is super-admin only, so the
        # tab appears only for super_admin ("*") / god_mode. Lead facilitators no
        # longer see or edit it.
        "manual_override", "auto_pause",
        "undo_round", "activity_log",
        # I2 (Workstream C): read-only effective-settings view over owned cohorts.
        "cohort_settings_view",
    ],
    "super_admin": ["*"],  # All tabs
    # project_admin gets a FIXED set (not cumulative with facilitator tabs):
    # cohort creation home + the facilitator registry.
    "project_admin": ["dashboard_home", "facilitator_registry"],
}


def get_role(fac: dict) -> str:
    """Get the role for a facilitator, resolving conflicts to the highest role."""
    role_val = fac.get("role")
    
    # Handle multiple roles if present
    if isinstance(role_val, list):
        roles = role_val
    elif isinstance(role_val, str) and "," in role_val:
        roles = [r.strip() for r in role_val.split(",")]
    elif isinstance(role_val, str):
        return role_val
    else:
        roles = []
        
    if roles:
        # Sort roles by hierarchy (highest first) and return the top operative role
        sorted_roles = sorted(roles, key=lambda r: ROLE_HIERARCHY.get(r, 0), reverse=True)
        return sorted_roles[0]
        
    # Backward compatibility: migrate from is_admin boolean
    if fac.get("is_admin"):
        return "super_admin"
    return "facilitator"
    
def has_role_level(fac: dict, required_role: str) -> bool:
    """Check if facilitator has at least the required role level."""
    fac_role = get_role(fac)
    return ROLE_HIERARCHY.get(fac_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


def is_admin_role(role: str) -> bool:
    """C6: True for roles carrying super-admin authority or above — super_admin,
    its alias admin, AND god_mode (level 4). Level-based so god_mode is included
    automatically. Use this instead of `role == "super_admin"` for the
    admin/is_admin gate so the now-distinct god_mode tier keeps full super-admin
    power (all-tabs, session-ownership bypass, is_admin=True)."""
    return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get("super_admin", 3)


def can_orchestrate_turnaround(role: str, fac_id: str = "") -> bool:
    """P1: True if this caller may orchestrate the post-completion Turnaround
    module for a session they manage.

    Two-key model (mirrors the side-track pool -> per-facilitator grant pattern):
      1. The module must be globally enabled -- even privileged roles cannot
         orchestrate a switched-off module (superadmin flips the switch first).
      2. lead_facilitator and above bypass the per-facilitator grant list (their
         bypass is audited at the call site, exactly like assign_cohort_side_tracks);
         a base facilitator must hold an explicit grant.

    project_admin is level 0 (off the run ladder) so it never qualifies -- and
    orchestration endpoints additionally sit behind require_sim_manager."""
    if not _god_mode_settings.get("turnaround_module_enabled", False):
        return False
    if ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get("lead_facilitator", 2):
        return True
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY.get("facilitator", 1):
        return False  # project_admin / players never orchestrate
    perms = _god_mode_settings.get("turnaround_facilitator_permissions", {})
    return bool(perms.get(fac_id, False))


def get_allowed_tabs(fac: dict) -> list[str]:
    """Return the list of tab IDs this facilitator is allowed to access."""
    role = get_role(fac)
    if is_admin_role(role):
        return ["*"]
    if role == "project_admin":
        # Fixed tab set — deliberately NOT cumulative with facilitator tabs.
        return list(ROLE_ALLOWED_TABS.get("project_admin", []))
    # Build cumulative tabs: facilitator tabs + lead_facilitator extras if applicable
    tabs = list(ROLE_ALLOWED_TABS.get("facilitator", []))
    if ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get("lead_facilitator", 0):
        tabs.extend(ROLE_ALLOWED_TABS.get("lead_facilitator", []))
    # Add any custom allowed_tabs from the facilitator record
    custom_tabs = fac.get("allowed_tabs", [])
    if custom_tabs:
        tabs.extend(custom_tabs)
    return list(set(tabs))


def can_access_tab(fac: dict, tab_id: str) -> bool:
    """Check if a facilitator can access a specific tab."""
    allowed = get_allowed_tabs(fac)
    return "*" in allowed or tab_id in allowed


def owns_session(fac: dict, session: dict) -> bool:
    """Check if a facilitator OWNS a session (multi-tenancy enforcement).
    Super admins (and god_mode) can access all sessions.

    CO-FAC-1 (UX audit #22): ownership stays SINGLE — exactly one facilitator
    is accountable for a run. A co-facilitator/TA is a separate, weaker thing
    (see can_observe_session) and deliberately does NOT satisfy this predicate,
    so every write path that already gates on ownership stays closed to them
    without any of those call sites changing."""
    if is_admin_role(get_role(fac)):
        return True
    fac_id = fac.get("facilitator_id", "")
    session_fac = session.get("facilitator_id", "")
    return session_fac == fac_id


def session_observers(session: dict) -> list[str]:
    """Facilitator ids granted READ-ONLY visibility of this session."""
    raw = (session or {}).get("co_facilitator_ids") or []
    return [str(x) for x in raw if x]


def can_observe_session(fac: dict, session: dict) -> bool:
    """CO-FAC-1 (UX audit #22): may this facilitator SEE this run?

    True for the owner, for admins, and for anyone on the session's
    co_facilitator_ids list. This is a strictly READ predicate — it is used by
    listing/monitoring endpoints only. It must never be substituted for
    owns_session on a write path: the audit's requirement was a TA who can
    watch the room, not a second person who can advance rounds.

    Today a co-facilitator has to be handed the owner's credentials, which
    `must_change_password` actively fights; this makes the real arrangement
    expressible without giving away run control."""
    if owns_session(fac, session):
        return True
    return fac.get("facilitator_id", "") in session_observers(session)


def _migrate_facilitator_roles(registry: list[dict]) -> list[dict]:
    """Migrate facilitator records from is_admin boolean to role string and populate default cohort settings."""
    for fac in registry:
        if "role" not in fac:
            if fac.get("is_admin"):
                fac["role"] = "super_admin"
            else:
                fac["role"] = "facilitator"
            # Keep is_admin for backward compat but role is authoritative
            fac["is_admin"] = fac["role"] == "super_admin"
        if "decision_paradigm" not in fac:
            fac["decision_paradigm"] = "legacy_abc"
        if "ending_pathway" not in fac:
            fac["ending_pathway"] = "activist_ultimatum"
        if "side_tracks" not in fac:
            fac["side_tracks"] = []
        if "simulation_mode" not in fac:
            fac["simulation_mode"] = "conglomerate"
        if "industry_vertical" not in fac:
            fac["industry_vertical"] = ""
        if "bu_substitutions" not in fac:
            fac["bu_substitutions"] = {}
    return registry

# ═════════════════════════════════════════════════════════════════
#  GOD MODE GLOBAL SETTINGS
# ═════════════════════════════════════════════════════════════════

_god_mode_settings: dict = {
    "allow_facilitator_cohort_creation": True,
    "system_frozen": False,
    "freeze_message": "",
    "freeze_started_at": None,
    # C6 (Switchboard settings-resolution): the climate branch now has its own
    # canonical key. `climate_paradigm` ∈ {standard, advanced_climate} is the
    # authoritative Timeline-Branch value written by the Sim Switchboard.
    # `simulation_mode` is retained for backward compatibility (legacy Switchboard
    # payloads still send it) but its *meaning* is scope in the cohort/session
    # layer ({"", single_bu}); readers must use `climate_paradigm` for the climate
    # branch. get_effective_settings() normalises legacy data on read.
    "climate_paradigm": "standard",
    "simulation_mode": "standard",
    "industry_vertical": "",   # NEW — default BU vertical for single-bu cohorts
    "region_id": "",           # NEW — geographic region (mandatory, set at cohort formation)
    "global_carbon_fee": 40,
    "market_hostility_index": 5,
    "scope_3_threshold": 2.5,
    "custom_archetypes": [],
    "overrun_probability": 0.25,
    "overrun_severity": 0.15,
    "currency_symbol": "$",
    "side_tracks_available": [],
    "side_tracks_facilitator_permissions": {},
    # Post-completion Turnaround module (P1). OFF by default: a normal run is
    # complete at R10 and this never changes that. Superadmin must (1) enable
    # globally, then (2) grant named facilitators to orchestrate it.
    "turnaround_module_enabled": False,
    "turnaround_facilitator_permissions": {},   # {fac_id: True} explicit grants
    "default_ending_pathway": "activist_ultimatum",
    "ending_pathways_available": [
        "activist_ultimatum",
        "climate_black_swan",
        "stakeholder_revolt",
    ],
    "allow_pathway_switching": False,
    "foreshadowing_enabled": True,
    "ceo_interview_enabled": False,
    "ceo_interview_voice_gender": "female",
    "ceo_interview_question_count": 5,
    "ceo_interview_pathway_question": True,
    # PHASE-1: Systemic Risk & Black Swan settings
    # NOTE: difficulty_tier is set per-cohort via Experience Level (see admin_router._scenario_presets).
    # Removed from global settings to prevent drift between God Mode and cohort-level ownership.
    "systemic_risk_enabled": True,                # Enable ESG-adjusted WACC + tipping points
    "black_swan_events_enabled": True,            # Enable stochastic Black Swan disruptions
    "npc_cascading_enabled": True,                # Enable NPC stakeholder cascade reactions
    "foreshadowing_signals_enabled": True,        # Show pedagogical foreshadowing hints

    # ── Advanced cohort controls (HIGH-tier setup data points) ──────────────
    # RNG seed (GAME-4): a non-empty seed makes every stochastic roll reproducible
    # and identical across all teams in the cohort — rankings reflect strategy, not
    # luck. Applied by stamping active_event_flags["stochastic_seed"] (see
    # admin_router cohort-settings PATCH). Empty ⇒ legacy non-deterministic.
    "rng_seed": "",

    # Result-visibility controls (granular output gating):
    #   results_reveal_round — hide leaderboard / peer ranks / final valuation from
    #     PLAYERS until this round (0 = always visible; 10 = only at the finale).
    #   redact_peer_identities — anonymise other teams in peer/benchmark views.
    "results_reveal_round": 0,
    "redact_peer_identities": False,

    # Quiz / knowledge-check (uses quiz_banks.py + InlineQuizEngine):
    "quiz_enabled": False,
    "quiz_graded": False,           # count quiz toward the cohort gradebook
    "quiz_pass_threshold": 70,      # percent required to pass (0–100)
    "quiz_max_attempts": 2,         # attempts per quiz (>=1); matches legacy engine default
    # quiz_mandatory — when ON, a round that has a quiz notebook BLOCKS the
    # player's decision/commit until they have taken that round's quiz (at least
    # one recorded attempt; passing is not required so a struggling student is
    # never permanently trapped). Rounds with no quiz notebook are unaffected.
    "quiz_mandatory": False,

    # Team / roster provisioning:
    #   team_count — hard roster cap enforced at join (0 = platform default of 5).
    #   max_team_size — seats per team (0 = unlimited); informational in the
    #     current one-session-per-player model.
    #   join_method — "code" (join code), "open" (anyone with link), "roster"
    #     (pre-provisioned only). join_code empty ⇒ auto-generated on demand.
    "team_count": 0,
    "max_team_size": 0,
    "join_method": "code",
    "join_code": "",

    # ── MEDIUM-tier cohort controls ─────────────────────────────────────────
    # Time & scheduling:
    #   cohort_timezone — IANA zone name (e.g. "Asia/Kolkata") used to render
    #     schedules/timers in the cohort's local time. Empty ⇒ browser-local.
    #     (Per-round timer DURATION reuses the existing engine toggles
    #      decision_timer_enabled / decision_timer_seconds — no duplicate knob.)
    #   late_join_policy — "anytime" (legacy), "before_round_2" (no new joins
    #     once any team is past Round 1), "closed" (no new joins; rejoin still OK).
    "cohort_timezone": "",
    "late_join_policy": "anytime",

    # Reports & data:
    #   report_access — what PLAYERS see of their own final report:
    #     "full" (legacy: everything), "summary" (headline numbers only — the
    #     narrative report bodies are withheld), "facilitator_only" (players get
    #     a locked notice; facilitators view via admin surfaces).
    "report_access": "full",

    # ── LOW-tier / polish cohort controls ───────────────────────────────────
    # Accessibility profile — cohort-level DEFAULTS pushed to every player's
    # cockpit (each player can still adjust locally; these set the baseline for
    # e.g. a cohort with known accessibility requirements).
    "accessibility_defaults": {
        "high_contrast": False,
        "font_scale": 1.0,        # 0.8 – 1.6 multiplier
        "reduced_motion": False,
        "colorblind_safe": False, # colourblind-safe palette for charts/badges
        "screen_reader_mode": False,  # denser aria labels, no canvas-only visuals
    },

    # White-label branding — institution identity on the cockpit + reports.
    "branding_institution": "",      # e.g. "IIM Ahmedabad" (empty = platform default)
    "branding_logo_url": "",         # https URL to the institution logo
    "branding_primary_color": "",    # hex "#RRGGBB" accent (empty = default theme)

    # Data retention & compliance:
    #   data_retention_days — reap the cohort + its player sessions N days after
    #     its end_date (0 = keep forever, legacy behaviour).
    #   consent_required — players must tick consent at join (captured with a
    #     UTC timestamp on their session record).
    #   consent_text — the statement players agree to (empty ⇒ platform default).
    "data_retention_days": 0,
    "consent_required": False,
    "consent_text": "",

    # Webhooks / LMS: POSTed fire-and-forget on lifecycle events (round
    # committed, game over) so LMS/gradebook integrations can sync without
    # polling. https-only; empty = disabled.
    "webhook_url": "",

    # Briefing videos — players get a Read | Watch choice on round briefings.
    # URLs only (YouTube / Vimeo / direct file on the institution's hosting);
    # the media itself never lives in the app.
    #   briefing_video_base — URL pattern; "{round}" is replaced by the round
    #     number (e.g. "https://cdn.x.edu/briefing-{round}.mp4"). Empty = none.
    #   briefing_videos — explicit per-round map {"1": url, ...}; an explicit
    #     entry wins over the pattern for that round.
    "briefing_video_base": "",
    "briefing_videos": {},
}


# ═════════════════════════════════════════════════════════════════
#  PER-COHORT SETTINGS (GOD-012)
# ═════════════════════════════════════════════════════════════════

# Cohort-level overrides indexed by session_id.
# Any key stored here shadows the corresponding key in _god_mode_settings
# for that specific cohort only.  All other cohorts remain unaffected.
cohort_settings: dict[str, dict] = {}

# Allow-list of keys that may be overridden per cohort.
# Global-only administrative keys (e.g. allow_facilitator_cohort_creation)
# are intentionally excluded — they should never differ between cohorts.
COHORT_OVERRIDABLE_KEYS: frozenset[str] = frozenset({
    "max_players",        # per-cohort roster cap (clamped via player_capacity)
    "negotiation_rooms_enabled",  # Slice 5: per-cohort Stakeholder Negotiation Rooms (capability-gated)
    "system_frozen",
    "freeze_message",
    "freeze_started_at",
    "climate_paradigm",   # C6: canonical climate-branch key (per-cohort overridable)
    "simulation_mode",
    "global_carbon_fee",
    "market_hostility_index",
    "scope_3_threshold",
    "overrun_probability",
    "overrun_severity",
    "currency_symbol",
    "default_ending_pathway",
    "ending_pathways_available",
    "allow_pathway_switching",
    "foreshadowing_enabled",
    "ceo_interview_enabled",
    "ceo_interview_voice_gender",
    "ceo_interview_question_count",
    "ceo_interview_pathway_question",
    "systemic_risk_enabled",
    "black_swan_events_enabled",
    "npc_cascading_enabled",
    "foreshadowing_signals_enabled",
    "decision_regret_enabled",
    "decision_timer_enabled",
    "decision_timer_seconds",
    "npc_stakeholders_enabled",
    "board_room_moments_enabled",
    "brsr_ngrbc_enabled",
    "tcfd_scenarios_enabled",
    "industry_vertical",
    "region_id",
    "esg_bs_scholarly_mode",   # Scholarly ESG capitalisation toggle (IAS 38 what-if)
    # Advanced cohort controls (HIGH-tier setup data points)
    "rng_seed",
    "results_reveal_round",
    "redact_peer_identities",
    "quiz_enabled",
    "quiz_graded",
    "quiz_pass_threshold",
    "quiz_max_attempts",
    "quiz_mandatory",
    "team_count",
    "max_team_size",
    "join_method",
    "join_code",
    # MEDIUM-tier cohort controls
    "cohort_timezone",
    "late_join_policy",
    "report_access",
    # LOW-tier / polish cohort controls
    "accessibility_defaults",
    "branding_institution",
    "branding_logo_url",
    "branding_primary_color",
    "data_retention_days",
    "consent_required",
    "consent_text",
    "webhook_url",
    "briefing_video_base",
    "briefing_videos",
    # Stakeholder Packs: which per-SBU matrix bundle this cohort runs.
    # Empty = today's single-set resolution, unchanged.
    "stakeholder_pack_id",
    # Materiality Packs: per-SBU double-materiality matrices. Empty = the
    # pre-existing per-BU / cohort-override resolution, unchanged.
    "materiality_pack_id",
})


# ── Advanced-controls validation / normalisation ────────────────────────────
# Coerce + clamp the HIGH-tier cohort controls to safe ranges before they are
# persisted, so a malformed payload can never poison the effective settings.
_JOIN_METHODS = frozenset({"code", "open", "roster"})
_LATE_JOIN_POLICIES = frozenset({"anytime", "before_round_2", "closed"})
_REPORT_ACCESS_LEVELS = frozenset({"full", "summary", "facilitator_only"})
import re as _re
_HEX_COLOR_RE = _re.compile(r"#[0-9a-fA-F]{6}")


def normalize_advanced_cohort_settings(body: dict) -> dict:
    """Return a copy of `body` with the advanced-control keys coerced/clamped.

    Only touches keys that are present; unknown keys pass through untouched (the
    caller still filters against COHORT_OVERRIDABLE_KEYS afterwards)."""
    out = dict(body)

    def _as_int(key, lo, hi, default):
        if key in out:
            try:
                out[key] = max(lo, min(hi, int(out[key])))
            except (TypeError, ValueError):
                out[key] = default

    _as_int("results_reveal_round", 0, 10, 0)
    _as_int("quiz_pass_threshold", 0, 100, 70)
    _as_int("quiz_max_attempts", 1, 20, 1)
    _as_int("team_count", 0, 500, 0)
    _as_int("max_team_size", 0, 100, 0)

    # Roster cap: clamp on the way IN through the single resolver + hard ceiling
    # (player_capacity). A value above the ceiling can never be honoured, and a
    # zero/negative/non-numeric value falls back to the default.
    if "max_players" in out:
        from player_capacity import clamp_max_players
        out["max_players"] = clamp_max_players(out["max_players"])

    for key in ("redact_peer_identities", "quiz_enabled", "quiz_graded", "quiz_mandatory"):
        if key in out:
            out[key] = bool(out[key])

    if "join_method" in out:
        out["join_method"] = out["join_method"] if out["join_method"] in _JOIN_METHODS else "code"

    if "rng_seed" in out and out["rng_seed"] is not None:
        # Store as a trimmed string; empty ⇒ non-deterministic.
        out["rng_seed"] = str(out["rng_seed"]).strip()[:64]

    if "join_code" in out and out["join_code"] is not None:
        out["join_code"] = str(out["join_code"]).strip()[:32]

    # ── MEDIUM-tier controls ────────────────────────────────────────────────
    # Per-round timer duration reuses the pre-existing engine knob; clamp it to
    # a sane boardroom range when it flows through cohort settings.
    _as_int("decision_timer_seconds", 30, 7200, 300)

    if "late_join_policy" in out:
        out["late_join_policy"] = (
            out["late_join_policy"] if out["late_join_policy"] in _LATE_JOIN_POLICIES
            else "anytime"
        )

    if "report_access" in out:
        out["report_access"] = (
            out["report_access"] if out["report_access"] in _REPORT_ACCESS_LEVELS
            else "full"
        )

    if "cohort_timezone" in out and out["cohort_timezone"] is not None:
        tz = str(out["cohort_timezone"]).strip()[:64]
        if tz:
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(tz)  # raises for unknown zones
            except Exception:
                tz = ""  # unknown zone ⇒ fall back to browser-local
        out["cohort_timezone"] = tz

    # ── LOW-tier / polish controls ──────────────────────────────────────────
    if "accessibility_defaults" in out:
        raw = out["accessibility_defaults"] if isinstance(out["accessibility_defaults"], dict) else {}
        acc = {}
        for bkey in ("high_contrast", "reduced_motion", "colorblind_safe", "screen_reader_mode"):
            acc[bkey] = bool(raw.get(bkey, False))
        try:
            fs = float(raw.get("font_scale", 1.0))
        except (TypeError, ValueError):
            fs = 1.0
        acc["font_scale"] = max(0.8, min(1.6, fs)) if fs == fs else 1.0  # NaN-safe
        out["accessibility_defaults"] = acc

    if "branding_institution" in out and out["branding_institution"] is not None:
        out["branding_institution"] = str(out["branding_institution"]).strip()[:120]

    if "branding_logo_url" in out and out["branding_logo_url"] is not None:
        url = str(out["branding_logo_url"]).strip()[:500]
        # https-only (or empty) — never let a plain-http/js: URL into the cockpit.
        out["branding_logo_url"] = url if url.startswith("https://") else ""

    if "branding_primary_color" in out and out["branding_primary_color"] is not None:
        col = str(out["branding_primary_color"]).strip()
        out["branding_primary_color"] = col if _HEX_COLOR_RE.fullmatch(col) else ""

    _as_int("data_retention_days", 0, 3650, 0)

    if "consent_required" in out:
        out["consent_required"] = bool(out["consent_required"])

    if "consent_text" in out and out["consent_text"] is not None:
        out["consent_text"] = str(out["consent_text"]).strip()[:2000]

    if "webhook_url" in out and out["webhook_url"] is not None:
        wurl = str(out["webhook_url"]).strip()[:500]
        out["webhook_url"] = wurl if wurl.startswith("https://") else ""

    # Briefing videos: URLs only, http(s) schemes only (a javascript:/data: URL
    # must never reach the player's embed iframe). The base pattern may carry
    # the literal "{round}" placeholder; the map is keyed by round number 1–10.
    def _clean_video_url(u) -> str:
        u = str(u or "").strip()[:500]
        return u if (u.startswith("https://") or u.startswith("http://")) else ""

    if "briefing_video_base" in out and out["briefing_video_base"] is not None:
        out["briefing_video_base"] = _clean_video_url(out["briefing_video_base"])

    if "briefing_videos" in out:
        raw_map = out["briefing_videos"] if isinstance(out["briefing_videos"], dict) else {}
        cleaned = {}
        for k, v in raw_map.items():
            try:
                rn = int(str(k).strip())
            except (TypeError, ValueError):
                continue
            if not 1 <= rn <= 10:
                continue
            url = _clean_video_url(v)
            if url:
                cleaned[str(rn)] = url
        out["briefing_videos"] = cleaned

    return out


# ── Cohort settings templates (clone-as-template) ───────────────────────────
# Named, reusable snapshots of a cohort's override layer. A facilitator saves a
# tuned cohort's settings once, then applies them to any number of future
# cohorts — repeatable setups without hand-copying two dozen switches.
# {template_id: {"name", "settings", "created_by", "source_session_id", "created_at"}}
_cohort_templates: dict[str, dict] = {}


def cohort_templates_snapshot() -> dict:
    """JSON-safe copy of the template store (for the memory snapshot)."""
    return {tid: dict(t) for tid, t in _cohort_templates.items()}


def restore_cohort_templates(data: dict) -> None:
    if isinstance(data, dict):
        for tid, t in data.items():
            if isinstance(t, dict) and isinstance(t.get("settings"), dict):
                _cohort_templates[tid] = dict(t)


# ── Durable cohort-settings store (volume-backed, backend-independent) ────────
# The per-cohort settings overlay (pacing, briefing-video URLs, analytics
# visibility, templates, …) previously lived ONLY in this process's dicts.
# Memory mode happened to snapshot them; Postgres mode never persisted them at
# all, so a redeploy silently reset every cohort's configuration. This gives
# them a dedicated JSON home under MURESSONS_DATA_DIR (the mounted Railway
# volume) — durable across redeploys in BOTH backends, on the exact pattern the
# facilitator registry / token-version / virtual-profile stores already use.
# (Multi-worker sharing is out of scope here — WEB_CONCURRENCY=1 per the deploy
# checklist; the volume makes a single instance fully durable.)
# Tests override this to a throwaway path so the suite never writes cohort
# state into the real data dir (same isolation the registry paths use).
_COHORT_STATE_PATH: str | None = None


def _cohort_state_path() -> str:
    # Explicit override wins (tests); otherwise resolve through the durable data
    # dir lazily so it honours MURESSONS_DATA_DIR (the Railway volume) at runtime.
    if _COHORT_STATE_PATH:
        return _COHORT_STATE_PATH
    return str(_data_file("cohort_settings.json"))


def persist_cohort_state() -> None:
    """Atomically write the cohort settings + templates to the durable volume."""
    try:
        path = _cohort_state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "cohort_settings": {sid: dict(o) for sid, o in cohort_settings.items()},
            "cohort_templates": cohort_templates_snapshot(),
        }
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as exc:
        print(f"[cohort-state] Failed to persist: {exc}")


def _load_cohort_state() -> None:
    """Rehydrate cohort settings + templates from the durable volume on boot."""
    try:
        path = _cohort_state_path()
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[cohort-state] Failed to load ({exc}); starting empty.")
        return
    if not isinstance(data, dict):
        return
    cs = data.get("cohort_settings")
    if isinstance(cs, dict):
        for sid, overrides in cs.items():
            if isinstance(overrides, dict):
                cohort_settings.setdefault(sid, {}).update(overrides)
    restore_cohort_templates(data.get("cohort_templates") or {})


def mark_cohort_settings_dirty() -> None:
    """Publish a cohort-settings mutation to durable storage.

    Always writes the dedicated volume file (durable in every backend). In
    memory mode ALSO nudges the game-state snapshot so a single restart is
    covered by either artefact — belt and suspenders, both live on the volume."""
    persist_cohort_state()
    if _in_memory_backend_active():
        try:
            import database_memory as _dm
            _dm._persist()
        except Exception:
            pass


def resolve_roster_cap(session_id: str, default: int = 20) -> int:
    """Effective roster cap for a cohort's join flow.

    BUG-2026-07-29 (audit): this read ONLY `team_count`, so the `max_players`
    control — the knob literally named for roster size, clamped to
    MAX_PLAYERS_CEILING (20) and exposed in cohort setup — was silently inert.
    A facilitator could set max_players=20, get HTTP 200, see it saved, and
    still have the 6th student bounced with "roster cap of 5 player(s)". The
    save succeeded; only the join gate disagreed, so nothing surfaced the
    mismatch until a class was already in the room.

    Either knob now raises the cap, and we take the LARGER of the two:
      * setting either one to 20 does what the facilitator plainly meant;
      * an existing cohort configured with team_count only keeps its cap
        (max_players is absent → 0 → ignored), so no run changes behaviour;
      * a stale/low value in one field can never silently shrink a roster the
        other field already widened.

    Neither set → `default`, the legacy platform cap, exactly as before.
    """
    try:
        cfg = get_effective_settings(session_id)
    except Exception:
        return default

    def _as_int(key: str) -> int:
        try:
            return int(cfg.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0

    cap = max(_as_int("team_count"), _as_int("max_players"))
    if cap <= 0:
        # 2026-07-31 (facilitator request): the unconfigured default rose from
        # the legacy 5 to the platform ceiling (20). A forgotten max_players no
        # longer bounces the 6th student mid-class; cohorts that WANT a smaller
        # roster set team_count/max_players explicitly, exactly as before.
        return default
    try:
        from player_capacity import MAX_PLAYERS_CEILING
        return min(cap, MAX_PLAYERS_CEILING)
    except Exception:
        return cap


# C6: keys that carry the climate branch. `simulation_mode` is only treated as
# a climate value at the GLOBAL layer (legacy Switchboard payloads); in the
# cohort/session layer it means scope (single_bu), so it is NEVER read for the
# branch there.
_CLIMATE_PARADIGM_VALUES = frozenset({"standard", "advanced_climate"})


# ═══════════════════════════════════════════════════════════════════════════
#  ESG LEADERSHIP PROFILE — signal weights (facilitator-tunable rubric)
#
#  The end-of-game ESG radar scores five dimensions from real performance
#  signals. These are the DEFAULT weights each signal contributes; lead
#  facilitators / super admins may override them (POST /esg-profile-weights) to
#  reshape the assessment rubric. The frontend keeps an identical copy of these
#  defaults, and both deep-merge any override over them so partial configs are
#  safe. Keep the two in sync when changing.
# ═══════════════════════════════════════════════════════════════════════════
DEFAULT_ESG_WEIGHTS: dict = {
    "climate_resilience": {
        "resilience_factor": 1.0,     # × climate-resilience factor (0-100)
        "resilience_bonus": 100,
        "climate_leader": 70,
        "adaptation_premium": 70,
        "carbon_transition": 60,
    },
    "governance": {
        "base": 48,
        "materiality_governance": 300,
        "truth_premium": 260,
        "materiality_aligned": 10,
        "instability_penalty": 100,   # applied to the (negative) instability discount
        "reputation_blend": 0.3,      # 0-1 share of reputation vs governance-core
    },
    "social_impact": {
        "social_license_blend": 0.6,  # baseline = 0.6·social-licence + 0.4·reputation
        "reputation_blend": 0.4,
        "community_champion": 70,
        "just_transition": 70,
        "workforce": 60,
        "wellbeing": 60,
        "social_regeneration": 55,
        "community_trust": 55,
        "employee_champion": 55,
        "just_transition_passed": 6,
        "burnout_penalty": 0.4,       # per point of burnout above 40
        "social_collapse_penalty": 100,
    },
    "environmental": {
        "decarbonisation": 1.0,       # × (100 − avg carbon intensity)
        "carbon_transition": 70,
        "climate_leader": 40,
        "stranded_asset_penalty": 100,
    },
    "innovation": {
        "base": 30,
        "rd_multiplier": 2,           # × R&D allocation %
        "rd_cap": 40,                 # cap on the R&D contribution
        "synergy": 200,
        "brsr_pioneer": 30,
        "brsr_steward": 30,   # × mr brsr_steward_bonus (Leadership-Indicator tier 2)
        "brsr_laggard": 30,   # × mr brsr_laggard_penalty (score < 40 track outcome)
    },
}


def resolve_climate_paradigm(settings: dict) -> str:
    """C6: single source of truth for the climate branch.

    Prefers the canonical `climate_paradigm`; falls back to a legacy
    `simulation_mode` value ONLY when it holds a climate value
    ({standard, advanced_climate}) — never when it holds a scope value like
    'single_bu'. Defaults to 'standard'.
    """
    cp = settings.get("climate_paradigm")
    if cp in _CLIMATE_PARADIGM_VALUES:
        return cp
    sm = settings.get("simulation_mode")
    if sm in _CLIMATE_PARADIGM_VALUES:
        return sm
    return "standard"


def get_effective_settings(session_id: str | None = None) -> dict:
    """Return the effective settings for a cohort.

    GOD-012: Merges global _god_mode_settings with any per-cohort overrides
    in cohort_settings[session_id].  Per-cohort values shadow their global
    counterparts; absent keys fall back to the global default.

    C6: the merged view always carries a normalised `climate_paradigm` so
    readers never have to disambiguate the overloaded `simulation_mode`.

    When session_id is None or has no overrides, returns the global dict
    directly (no copy overhead for the 99 % case).
    """
    # BUG-2026-07-20: a PLAYER's sub-session has its own id and never carries
    # the cohort's overrides, so every per-cohort setting read with a player id
    # silently resolved to the platform default. That is how Stakeholder
    # Negotiation Rooms stayed 403 ("not enabled for this cohort") after the
    # facilitator had enabled them: the gate is evaluated with the player's
    # session id. resolve_analytics_visibility already walked up to the parent;
    # this did not. Walk up here so EVERY caller gets the cohort's settings.
    #
    # Via the `db` parity API, not database_memory: admin_analytics does this
    # same walk against the memory store, which is exactly the shape that only
    # works in memory mode. resolve_cohort_id_sync exists in both backends.
    if session_id and session_id not in cohort_settings:
        try:
            import database as db
            _parent = db.resolve_cohort_id_sync(session_id)
            if _parent and _parent in cohort_settings:
                session_id = _parent
        except Exception:
            pass  # fail-open to the global view

    if not session_id or session_id not in cohort_settings:
        # Fast path: global default dict already has climate_paradigm set.
        return _god_mode_settings
    # Shallow merge — cohort overrides win over globals
    override = cohort_settings[session_id]
    merged = {**_god_mode_settings, **override}
    # C6: honour an EXPLICIT climate signal in the cohort override (the canonical
    # climate_paradigm, or a legacy climate-valued simulation_mode) over the
    # global default paradigm. Without this, the always-present global default
    # ("standard") would shadow a legacy per-cohort advanced_climate override.
    if (override.get("climate_paradigm") in _CLIMATE_PARADIGM_VALUES
            or override.get("simulation_mode") in _CLIMATE_PARADIGM_VALUES):
        merged["climate_paradigm"] = resolve_climate_paradigm(override)
    else:
        merged["climate_paradigm"] = resolve_climate_paradigm(_god_mode_settings)
    return merged


# C6/C2: keys that are seeded from the resolver into a session's
# active_event_flags so the engine (which reads active_event_flags) always sees
# the effective global/override values without any engine-side change.
_SEEDED_CLIMATE_KEYS = ("global_carbon_fee", "market_hostility_index", "scope_3_threshold")


def seed_effective_flags(session_id: str | None, flags: dict) -> dict:
    """C2: copy the effective climate inputs into a session's active_event_flags.

    The engine reads active_event_flags.get('global_carbon_fee' / ...); this
    helper guarantees those keys reflect get_effective_settings(session_id)
    (global defaults + per-cohort overrides). Called at session creation and
    before each round's post_tick. It seeds *base inputs* only — it never
    overwrites round-computed outputs (those live under different keys, e.g.
    peak_internal_carbon_fee, carbon_fee_per_ton).

    Mutates and returns `flags` for convenience. Safe no-op if flags is falsy.
    """
    if flags is None:
        return flags
    eff = get_effective_settings(session_id)
    for k in _SEEDED_CLIMATE_KEYS:
        v = eff.get(k)
        if v is not None:
            flags[k] = v
    # Mirror the canonical climate branch alongside the numeric inputs so any
    # reader inspecting flags sees a consistent value (decision_paradigm remains
    # the authoritative per-session branch and is unchanged here).
    flags["climate_paradigm"] = resolve_climate_paradigm(eff)
    return flags


# C1/C4/I4 (Workstream D — provisioning inheritance): fill omitted provisioning
# values from the current GLOBAL default (Sim Switchboard) so a super_admin's
# platform setting seeds NEW cohorts, while explicit provisioning choices always
# win. Precedence: explicit request > global default > hard-coded fallback.
# Existing cohorts are never touched by this — it only supplies creation-time
# defaults for fields the request omitted.
def inherited_provisioning_defaults(
    *,
    decision_paradigm: str | None,
    simulation_mode: str | None,
    industry_vertical: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Return (decision_paradigm, simulation_mode, industry_vertical) with any
    omitted (falsy) value inherited from the global default. Truthy inputs are
    returned unchanged, so callers that pass explicit values see no change."""
    g = get_effective_settings(None)

    dp = decision_paradigm
    # Climate branch: only inherit when the global default is advanced_climate
    # (the 'standard' default maps to no specific decision_paradigm, so the
    # caller's own fallback — legacy_abc — is preserved).
    if not dp and resolve_climate_paradigm(g) == "advanced_climate":
        dp = "advanced_climate"

    sm = simulation_mode
    iv = industry_vertical
    # BU scope: a global single-BU deployment is expressed via a non-empty
    # assigned_bu. Inherit it only when the request specified no scope.
    if not sm:
        global_bu = (g.get("assigned_bu") or "").strip()
        if global_bu:
            sm = "single_bu"
            iv = iv or global_bu

    return dp, sm, iv


# ═════════════════════════════════════════════════════════════════
#  I3 (Workstream B) — UNIFIED ROLE-SCOPED SETTINGS READ
# ═════════════════════════════════════════════════════════════════
# One projector produces a role-filtered view of the effective settings, with
# per-key provenance. Deny-by-default: a role sees only the keys in its
# allow-list (super_admin/god_mode see everything). This replaces the ad-hoc
# split between /god/settings (all hidden params) and /scaffolding-status
# (subset) with a single, auditable projection.

_CLIMATE_VIEW_KEYS = frozenset({
    "climate_paradigm", "global_carbon_fee", "market_hostility_index", "scope_3_threshold",
})
_FREEZE_VIEW_KEYS = frozenset({"system_frozen", "freeze_message", "freeze_started_at"})
_SCAFFOLDING_VIEW_KEYS = frozenset({
    "board_room_moments_enabled", "foreshadowing_enabled", "foreshadowing_signals_enabled",
    "systemic_risk_enabled", "black_swan_events_enabled", "npc_cascading_enabled",
    "ceo_interview_enabled",
})
_PROVISIONING_VIEW_KEYS = frozenset({
    "climate_paradigm", "simulation_mode", "assigned_bu", "industry_vertical",
    "region_id", "default_ending_pathway",
})


def visible_keys_for_role(role: str) -> frozenset | None:
    """Return the set of setting keys a role may read, or None for 'all keys'
    (super_admin / god_mode). Unknown/anonymous roles see nothing."""
    if is_admin_role(role):
        return None  # all keys
    if role == "lead_facilitator":
        return _CLIMATE_VIEW_KEYS | _FREEZE_VIEW_KEYS | _SCAFFOLDING_VIEW_KEYS
    if role == "project_admin":
        return _PROVISIONING_VIEW_KEYS
    if role == "facilitator":
        return _SCAFFOLDING_VIEW_KEYS
    return frozenset()


def bu_scope_source(session_id: str | None) -> str:
    """I7: where a cohort's single-BU scope is decided —
    'cohort_record' | 'switchboard_global' | 'none'. (Per-player registry scope
    is resolved at join time and surfaced separately.)"""
    g = get_effective_settings(None)
    sess = None
    if session_id:
        try:
            from database_memory import _sessions
            sess = _sessions.get(session_id)
        except Exception:
            sess = None
    if sess and (sess.get("assigned_bu") or "").strip():
        return "cohort_record"
    if (g.get("assigned_bu") or "").strip():
        return "switchboard_global"
    return "none"


def project_effective(session_id: str | None, role: str) -> dict:
    """Role-filtered projection of the effective settings, with per-key
    provenance {value, source, overridden}. `source` is 'cohort_override' when
    the key is explicitly overridden for this cohort, else 'global'."""
    eff = get_effective_settings(session_id)
    override = cohort_settings.get(session_id, {}) if session_id else {}
    keys = visible_keys_for_role(role)
    projected: dict[str, dict] = {}
    for k, v in eff.items():
        if keys is not None and k not in keys:
            continue
        overridden = k in override
        projected[k] = {
            "value": v,
            "source": "cohort_override" if overridden else "global",
            "overridden": overridden,
        }
    return {
        "session_id": session_id,
        "role": role,
        "overrides_active": bool(override),
        "bu_scope_source": bu_scope_source(session_id),
        "settings": projected,
    }


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR REGISTRY (with JSON persistence)
# ═════════════════════════════════════════════════════════════════

# QA-2026-07-16 #3: routed through runtime_paths so a Railway volume
# (MURESSONS_DATA_DIR) can hold it -- otherwise every redeploy wipes all
# facilitator accounts created in production. Default is unchanged (<repo>/db).
from runtime_paths import data_file as _data_file
_FAC_REGISTRY_PATH = str(_data_file("facilitator_registry.json"))

# ── SEC-1: Token version store (session revocation kill-switch) ──
# Each facilitator (including the virtual god_mode account) has a monotonic
# token_version. It is embedded in every issued JWT as the "ver" claim and
# re-checked on every request. Incrementing a facilitator's version instantly
# invalidates ALL of their outstanding tokens — the missing kill-switch that
# previously left a leaked god_mode cookie usable indefinitely.
# QA-2026-07-16 #3: durable data dir (see _FAC_REGISTRY_PATH note above) --
# a wiped token-version store would silently re-validate revoked sessions.
_TOKEN_VERSION_PATH = str(_data_file("token_versions.json"))
_token_versions: dict[str, int] = {}


def _load_token_versions() -> None:
    global _token_versions
    try:
        with open(_TOKEN_VERSION_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _token_versions = {str(k): int(v) for k, v in data.items()}
    except FileNotFoundError:
        _token_versions = {}
    except Exception as exc:
        print(f"[SEC-1] Failed to load token versions ({exc}); starting empty.")
        _token_versions = {}


def _save_token_versions() -> None:
    try:
        os.makedirs(os.path.dirname(_TOKEN_VERSION_PATH), exist_ok=True)
        with open(_TOKEN_VERSION_PATH, "w", encoding="utf-8") as fh:
            json.dump(_token_versions, fh, indent=2)
    except Exception as exc:
        print(f"[SEC-1] Failed to persist token versions: {exc}")


def get_token_version(facilitator_id: str) -> int:
    """Current token version for a facilitator (0 if never revoked)."""
    return int(_token_versions.get(facilitator_id, 0))


def bump_token_version(facilitator_id: str) -> int:
    """Invalidate all outstanding tokens for a facilitator; returns new version."""
    _token_versions[facilitator_id] = get_token_version(facilitator_id) + 1
    _save_token_versions()
    return _token_versions[facilitator_id]


_load_token_versions()


# ── Virtual-account profiles (god_mode / facilitator / project_admin) ─────────
# The three break-glass accounts are VIRTUAL: they authenticate against env
# passwords and are deliberately NOT rows in the facilitator registry (whose
# entries carry bcrypt hashes, deletion cascades and provisioning semantics).
# But virtual accounts still have mutable per-account state — today a chosen
# display username (the "callsign" first-login flow) — which previously had
# nowhere to live: set-username 404'd ("Facilitator not found") and login
# rebuilt the account dict from scratch each time, re-triggering the
# first-login screen forever. This store gives that state a durable home with
# the same volume-aware persistence as the registry/token stores.
_VIRTUAL_FACILITATOR_IDS = frozenset({"god_mode", "facilitator", "project_admin"})
_VIRTUAL_PROFILES_PATH = str(_data_file("virtual_account_profiles.json"))
_virtual_account_profiles: dict[str, dict] = {}


def _load_virtual_profiles() -> None:
    global _virtual_account_profiles
    try:
        with open(_VIRTUAL_PROFILES_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _virtual_account_profiles = {
                str(k): dict(v) for k, v in data.items()
                if k in _VIRTUAL_FACILITATOR_IDS and isinstance(v, dict)
            }
    except FileNotFoundError:
        _virtual_account_profiles = {}
    except Exception as exc:
        print(f"[virtual-profiles] Failed to load ({exc}); starting empty.")
        _virtual_account_profiles = {}


def _persist_virtual_profiles() -> None:
    try:
        os.makedirs(os.path.dirname(_VIRTUAL_PROFILES_PATH), exist_ok=True)
        tmp_path = _VIRTUAL_PROFILES_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(_virtual_account_profiles, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _VIRTUAL_PROFILES_PATH)
    except Exception as exc:
        print(f"[virtual-profiles] Failed to persist: {exc}")


def is_virtual_facilitator(facilitator_id: str) -> bool:
    return facilitator_id in _VIRTUAL_FACILITATOR_IDS


def get_virtual_profile(facilitator_id: str) -> dict:
    """Stored mutable profile for a virtual account ({} if none set yet)."""
    return dict(_virtual_account_profiles.get(facilitator_id, {}))


def set_virtual_username(facilitator_id: str, username: str) -> None:
    """Durably record a virtual account's chosen display username."""
    if facilitator_id not in _VIRTUAL_FACILITATOR_IDS:
        raise ValueError(f"{facilitator_id!r} is not a virtual account")
    profile = _virtual_account_profiles.setdefault(facilitator_id, {})
    profile["username"] = username.strip()
    _persist_virtual_profiles()


_load_virtual_profiles()

# Rehydrate the durable per-cohort settings overlay + templates from the volume.
_load_cohort_state()


def _generate_emergency_password() -> str:
    """Generate a random 12-char alphanumeric password for the emergency fallback account."""
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))

_DEFAULT_FACILITATOR = {
    "facilitator_id": "FAC-EMERGENCY",
    "name": "Emergency Admin",
    "password": _generate_emergency_password(),  # Random — shown once at startup in logs
    "created_at": "2026-01-01T00:00:00+00:00",
    "max_cohorts": 99,
    "cohorts_created": 0,
    "decision_paradigm": "legacy_abc",
    "ending_pathway": "activist_ultimatum",
    "side_tracks": [],
    "simulation_mode": "conglomerate",
    "industry_vertical": "",
    "bu_substitutions": {},
    "role": "super_admin",
    "is_admin": True,  # backward compat — role is authoritative
    "enabled": True,
}


_FAC_IDENTITY_FIELDS = ("facilitator_id", "username", "name")


def _sanitise_facilitator_row(fac: dict) -> dict:
    """Coerce identity fields to strings so the login scan can never crash.

    This is the SELF-HEALING half of the null-identity fix. Blocking the write
    path stops NEW nulls, but a registry file that already contains one keeps
    500-ing every login — including the god_mode break-glass — across restarts,
    because the poisoned value lives on the durable volume. Repairing on load
    means one redeploy restores access without hand-editing JSON on a mounted
    volume during a class.
    """
    for key in _FAC_IDENTITY_FIELDS:
        if key in fac and not isinstance(fac[key], str):
            fac[key] = "" if fac[key] is None else str(fac[key])
    return fac


def _load_facilitator_registry() -> list[dict]:
    """Load facilitator registry from disk. Falls back to default if not found.
    Applies role migration for backward compatibility."""
    try:
        if os.path.exists(_FAC_REGISTRY_PATH):
            with open(_FAC_REGISTRY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data:
                data = _migrate_facilitator_roles(data)
                # Deduplicate by facilitator_id, keeping first occurrence
                seen: set = set()
                deduped = []
                for fac in data:
                    fid = fac.get("facilitator_id")
                    if fid and fid not in seen:
                        seen.add(fid)
                        deduped.append(_sanitise_facilitator_row(fac))
                data = deduped
                print(f"[persistence] Restored {len(data)} facilitator(s) from registry.")
                return data
    except Exception as e:
        print(f"[persistence] Failed to load facilitator registry: {e}")
    # audit #18: Emergency fallback banner. The plaintext emergency password is
    # NO LONGER written to the logs in production — Railway (and any log
    # forwarder) captures stdout/stderr, so a secret there is effectively public.
    # In prod we log only the recovery INSTRUCTION; recover via the god_mode
    # MASTER_PASSWORD break-glass or by restoring the registry file. The
    # plaintext is shown only under DEBUG (local development) for convenience.
    try:
        from config import DEBUG as _DEBUG
    except Exception:
        _DEBUG = False
    if _DEBUG:
        _shared_logger.warning(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║  EMERGENCY — Registry unavailable. Fallback active.  ║\n"
            "║  DEBUG build — credential shown for local recovery.  ║\n"
            "╠══════════════════════════════════════════════════════╣\n"
            "║  ID       : %s\n"
            "║  Password : %s\n"
            "║  Role     : %s\n"
            "║  ACTION   : Restore db/facilitator_registry.json     ║\n"
            "╚══════════════════════════════════════════════════════╝",
            _DEFAULT_FACILITATOR["facilitator_id"],
            _DEFAULT_FACILITATOR["password"],
            _DEFAULT_FACILITATOR["role"],
        )
    else:
        _shared_logger.error(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║  EMERGENCY — Facilitator registry unavailable.       ║\n"
            "║  A fallback emergency account (id below) is active.  ║\n"
            "║  Its password is NOT logged (secrets must not reach  ║\n"
            "║  log forwarders). Recover by either:                 ║\n"
            "║    • signing in with the god_mode MASTER_PASSWORD,   ║\n"
            "║      or                                              ║\n"
            "║    • restoring db/facilitator_registry.json.         ║\n"
            "╠══════════════════════════════════════════════════════╣\n"
            "║  ID   : %s\n"
            "║  Role : %s\n"
            "╚══════════════════════════════════════════════════════╝",
            _DEFAULT_FACILITATOR["facilitator_id"],
            _DEFAULT_FACILITATOR["role"],
        )
    return [{**_DEFAULT_FACILITATOR}]


def _persist_facilitators():
    """Save current facilitator registry to disk."""
    try:
        os.makedirs(os.path.dirname(_FAC_REGISTRY_PATH), exist_ok=True)
        tmp_path = _FAC_REGISTRY_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(_facilitator_registry, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _FAC_REGISTRY_PATH)
    except Exception as e:
        print(f"[persistence] Failed to save facilitator registry: {e}")


_facilitator_registry = _load_facilitator_registry()
_next_facilitator_id: int = 1


# ═════════════════════════════════════════════════════════════════
#  PLAYER REGISTRY
# ═════════════════════════════════════════════════════════════════

_player_registry = []
_next_player_id: int = 1


# ═════════════════════════════════════════════════════════════════
#  SESSION MESSAGES & INTERVENTIONS
# ═════════════════════════════════════════════════════════════════

_session_messages = {}
_session_interventions = {}
_session_journey_responses: dict[str, dict] = {}  # {session_id: {key: data}}


# ═════════════════════════════════════════════════════════════════
#  AUDIT LOG & CRISIS HISTORY
# ═════════════════════════════════════════════════════════════════

_god_mode_audit_log = []
_crisis_trigger_history = []

# H-4 security fix: Prevent unbounded in-memory list growth.
# In multi-day deployments, audit logs and event histories can grow
# indefinitely. _capped_append evicts the oldest entries when the list
# exceeds MAX_LIST_ENTRIES. The JSONL audit file on disk is the permanent
# record; these in-memory lists are for the dashboard UI only.
MAX_LIST_ENTRIES = 10_000

def _capped_append(target_list: list, entry, cap: int = MAX_LIST_ENTRIES):
    """Append to a list with FIFO eviction to prevent memory leaks."""
    target_list.append(entry)
    if len(target_list) > cap:
        # Remove oldest 10% to avoid trimming on every single append
        trim_count = cap // 10
        del target_list[:trim_count]


# ═════════════════════════════════════════════════════════════════
#  PRACTICE MODE
# ═════════════════════════════════════════════════════════════════

_practice_mode = {}


def is_practice_mode(session_id: str) -> bool:
    """Check if a session is in practice mode."""
    return _practice_mode.get(session_id, False)


# ═════════════════════════════════════════════════════════════════
#  ROUND PACING (with facilitator ownership protection)
# ═════════════════════════════════════════════════════════════════

_round_pacing = {}


def _get_pacing(session_id: str) -> dict:
    """Get or create default pacing config for a session."""
    if session_id not in _round_pacing:
        _round_pacing[session_id] = {
            "mode": "free",
            "unlocked_round": 999,
            "interval_seconds": 300,
            "next_unlock_at": None,
            "schedule": [],
            "_timer_tasks": [],
            "_timer_task": None,
            "set_by": None,  # Track who set the pacing
            # Free-advance auto-release: in "free" mode the cohort still waits for
            # every team to commit before advancing. 0 = wait indefinitely (legacy
            # behaviour). >0 = after this many seconds from when a round opens for
            # the cohort, release the barrier and auto-commit any team that has not
            # committed (using its saved decisions). Prevents one absent team from
            # deadlocking everyone. Transient _fa_* fields track the live deadline.
            "free_advance_timeout_seconds": 0,
            "_fa_round": None,        # the cohort round the current deadline applies to
            "_fa_deadline_at": None,  # ISO datetime the barrier auto-releases
            "_fa_force": False,       # facilitator "Force Advance Now" one-shot flag
        }
    p = _round_pacing[session_id]
    p.setdefault("schedule", [])
    p.setdefault("_timer_tasks", [])
    p.setdefault("set_by", None)
    p.setdefault("free_advance_timeout_seconds", 0)
    p.setdefault("_fa_round", None)
    p.setdefault("_fa_deadline_at", None)
    p.setdefault("_fa_force", False)
    return p


def _effective_unlocked_round(pacing: dict) -> int:
    """QA-2026-07-16 #6: the unlocked round accounting for elapsed wall-clock,
    not just the in-process ``unlocked_round`` counter.

    Timed/scheduled pacing bumps ``unlocked_round`` from an asyncio timer whose
    handle is per-process and is NOT restored on restart (see
    _PACING_LOCAL_FIELDS). So a countdown that was running when the container
    redeployed would never fire and the round would stall. The durable fields
    ``schedule`` / ``next_unlock_at`` DO survive (snapshot + coordination store),
    so we derive the unlock from them here — a pure, read-only evaluation that
    makes the gate correct even when the timer never re-armed.
    """
    base = int(pacing.get("unlocked_round", 999) or 0)
    now = datetime.now(timezone.utc)

    def _parse(iso):
        try:
            t = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
            return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    # Multi-round schedule: schedule[i] is the ISO unlock time for round i+1.
    schedule = pacing.get("schedule") or []
    if schedule:
        highest = base
        for idx, iso in enumerate(schedule):
            if not iso:
                continue
            t = _parse(iso)
            if t is not None and t <= now:
                highest = max(highest, idx + 1)
        return highest

    # Single-shot interval mode: one pending unlock at next_unlock_at.
    nxt = pacing.get("next_unlock_at")
    if nxt:
        t = _parse(nxt)
        if t is not None and t <= now:
            return base + 1
    return base


def is_round_unlocked(session_id: str, round_number: int) -> bool:
    """Check if a given round is unlocked for progression."""
    pacing = _get_pacing(session_id)
    if pacing["mode"] == "free":
        return True
    # QA-2026-07-16 #6: time-aware so a scheduled/timed unlock still opens the
    # round after a restart even though the in-process timer is gone.
    return round_number <= _effective_unlocked_round(pacing)


def is_pacing_set_by_facilitator(session_id: str) -> bool:
    """Check if pacing for a session was explicitly set by a facilitator.
    If True, God Mode cannot override it."""
    pacing = _get_pacing(session_id)
    return pacing.get("set_by") is not None and pacing["mode"] != "free"


# ═════════════════════════════════════════════════════════════════
#  SHARED COORDINATION STATE (audit Fix #5)
#
#  Round pacing and the God-Mode freeze flag must survive a restart AND be
#  shared across uvicorn workers/replicas (audit §1.1/§1.2). The persistence
#  itself lives in coordination_store (Postgres) and, for single-process/offline
#  runs, in database_memory's JSON snapshot. The helpers below (a) expose a
#  JSON-safe view of the in-process dicts — excluding the per-process asyncio
#  timer handles, which must NOT be shared — and (b) publish local mutations so
#  other workers converge. Callers mutate the dict as before, then call
#  mark_pacing_dirty()/mark_godmode_dirty() to publish.
# ═════════════════════════════════════════════════════════════════

# Fields on a pacing dict that are per-process and must never be serialised or
# shipped to another worker (they hold live asyncio.Task handles).
_PACING_LOCAL_FIELDS = frozenset({"_timer_tasks", "_timer_task"})


def pacing_policy_snapshot(session_id: str) -> dict:
    """JSON-safe subset of a session's pacing policy (no asyncio handles)."""
    p = _round_pacing.get(session_id)
    if not p:
        return {}
    return {k: v for k, v in p.items()
            if k not in _PACING_LOCAL_FIELDS and not callable(v)}


def all_pacing_policies() -> dict:
    """{session_id: policy} for every session with pacing set — used by the
    snapshot writer so pacing survives a restart in memory mode."""
    return {sid: pacing_policy_snapshot(sid) for sid in list(_round_pacing.keys())}


def restore_pacing_policy(session_id: str, policy: dict) -> None:
    """Merge a shared/persisted pacing policy into the local dict, preserving
    this process's own timer handles."""
    if not isinstance(policy, dict):
        return
    p = _get_pacing(session_id)  # ensures defaults + local timer fields exist
    for k, v in policy.items():
        if k in _PACING_LOCAL_FIELDS:
            continue
        p[k] = v


def godmode_settings_snapshot() -> dict:
    """Full God-Mode settings dict (all values are JSON-safe)."""
    return dict(_god_mode_settings)


def restore_godmode_settings(data: dict) -> None:
    if isinstance(data, dict):
        _god_mode_settings.update(data)


def _in_memory_backend_active() -> bool:
    """True when the durable store is the in-memory snapshot (not Postgres)."""
    try:
        import coordination_store as _cs
        return not _cs.is_shared()
    except Exception:
        return True


def _schedule_publish(coro) -> None:
    """Fire-and-forget an async publish when an event loop is running; a no-op
    in synchronous contexts (e.g. unit tests) so callers stay sync-safe."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        coro.close()
        return
    loop.create_task(coro)


def mark_pacing_dirty(session_id: str) -> None:
    """Publish a session's current pacing policy after a local mutation.
    • Postgres mode → upsert into coordination_state (shared across workers).
    • Memory mode   → trigger a snapshot so the policy survives a restart."""
    if _in_memory_backend_active():
        try:
            import database_memory as _dm
            _dm._persist()
        except Exception:
            pass
        return
    try:
        import coordination_store as _cs
        _schedule_publish(_cs.publish_pacing(session_id, pacing_policy_snapshot(session_id)))
    except Exception:
        pass


def mark_godmode_dirty() -> None:
    """Publish God-Mode settings (incl. the freeze flag) after a local mutation."""
    if _in_memory_backend_active():
        try:
            import database_memory as _dm
            _dm._persist()
        except Exception:
            pass
        return
    try:
        import coordination_store as _cs
        _schedule_publish(_cs.publish_godmode_settings(godmode_settings_snapshot()))
    except Exception:
        pass


# ═════════════════════════════════════════════════════════════════
#  COHORT MANAGEMENT
# ═════════════════════════════════════════════════════════════════

def may_create_cohort(role: str) -> tuple[bool, str]:
    """RBAC-F2/R2 (2026-08-01): THE single rule for "may this caller create a
    cohort?" — returns (allowed, reason_if_denied).

    Before this, one capability had THREE answers: the dashboard button read a
    permission flag that enforced nothing, the Registry tab's button read the
    role string, and POST /simulations/start enforced neither (any
    authenticated facilitator with quota could create, including via a direct
    API call that both UIs appeared to forbid). This function is now the only
    place the question is answered; the server enforces it and both UI
    surfaces render whatever it returns.

    The rule, in role order:
      * god_mode / super_admin / admin — always (platform administration).
      * project_admin                  — always (its charter IS provisioning
                                          facilitators and cohorts).
      * lead_facilitator               — always (runs workshops).
      * facilitator (base)             — governed by the platform switch
                                          `allow_facilitator_cohort_creation`,
                                          which is exactly what its name says.
                                          Default True preserves the behaviour
                                          the server has always had; a
                                          super_admin turns it off to make
                                          cohort creation lead-and-above only.
      * anonymous / unknown            — never.

    NOTE the division of labour with check_and_increment_cohort_count: THIS
    decides policy for the ACTOR (the authenticated caller). That one enforces
    the per-facilitator quota of the TARGET the cohort is created for — which
    may be a different person, since registry admins may create on another
    facilitator's behalf. Conflating them is what produced the misleading
    "has reached the maximum cohort limit" error for what was actually a
    policy denial.
    """
    if not role or role == "anonymous":
        return False, "Facilitator authentication required to create a cohort."
    if is_admin_role(role) or role == "project_admin":
        return True, ""
    if ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get("lead_facilitator", 2):
        return True, ""
    if role == "facilitator":
        if _god_mode_settings.get("allow_facilitator_cohort_creation", True):
            return True, ""
        return False, (
            "Cohort creation is currently restricted to lead facilitators and "
            "administrators. Ask your administrator to enable it for facilitators."
        )
    return False, "Your role may not create cohorts."


async def check_and_increment_cohort_count(facilitator_id: str) -> bool:
    """Check if facilitator can create another cohort. If yes, increment and return True.

    GOD-004: The read-check-increment sequence is protected by _cohort_lock to
    prevent two simultaneous session-creation requests from both passing the
    limit check and both being granted a slot, causing the facilitator to exceed
    their max_cohorts quota.
    """
    if not facilitator_id:
        return True
    async with _cohort_lock:
        # RBAC-R2: the `allow_facilitator_cohort_creation` policy check that
        # used to live here has moved to may_create_cohort(), which the /start
        # endpoint applies to the CALLER before this runs. Two reasons it was
        # wrong here: (1) it tested the TARGET facilitator rather than the
        # actor, so a registry admin creating on someone's behalf was judged by
        # the wrong identity; (2) it demanded super_admin, which silently
        # blocked LEAD FACILITATORS — the very people who run workshops —
        # whenever the switch was off. This function is now purely the quota.
        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
        if not fac:
            return True
        if fac.get("deleted_at"):
            return True
        if not fac.get("enabled", True):
            return False
        max_c = fac.get("max_cohorts", 5)
        created = fac.get("cohorts_created", 0)
        if created >= max_c:
            return False
        fac["cohorts_created"] = created + 1
    # Persist outside the lock — I/O doesn't need the shared-state guard
    _persist_facilitators()
    return True


# ═════════════════════════════════════════════════════════════════
#  SESSION PARADIGM LOOKUP
# ═════════════════════════════════════════════════════════════════

def _get_session_paradigm(session_id: str) -> str:
    """Read decision_paradigm directly from the raw in-memory session store."""
    from database_memory import _sessions
    raw = _sessions.get(session_id)
    if raw:
        return raw.get("decision_paradigm", "legacy_abc") or "legacy_abc"
    return "legacy_abc"


# ═════════════════════════════════════════════════════════════════
#  DEFAULT ARCHETYPES
# ═════════════════════════════════════════════════════════════════

# AR-B/AR-C: the terminal archetype is a TWO-AXIS classification —
#   axis 1: M_R (regenerative-strategy quality)   → `mr_threshold`
#   axis 2: realized value / solvency (outcome)    → `requires_solvent`
# `requires_solvent=True` means the label is only awarded to a company that
# ended solvent (Double-Materiality Adjusted Value = final_treasury x M_R − NCD
# > 0); an insolvent company is downgraded into the failure band regardless of
# M_R. The full matrix (matching round_logic's R10 resolver):
#
#                        │ solvent (DMAV > 0)          │ value-destroyed (DMAV ≤ 0)
#   ─────────────────────┼─────────────────────────────┼───────────────────────────
#   M_R ≥ 1.8            │ Regenerative Titan          │ Hollow Idealist
#   1.2 ≤ M_R < 1.8      │ De-risked Safe-Haven        │ Hollow Idealist
#   0.8 ≤ M_R < 1.2      │ Fragile Giant               │ Stranded Relic
#   M_R < 0.8            │ Pragmatic Operator          │ Stranded Relic
#
# The Turnaround Manager is awarded only via the post-R10 survival/turnaround
# arc (see turnaround_engine.py), not by the M_R ladder. Ordering matters:
# within an M_R-threshold tie the solvency-gated (requires_solvent) entry must
# precede the non-gated one so the custom matcher resolves solvent → gated
# label and insolvent → failure label. Custom archetypes carry the same fields
# (default requires_solvent False).
DEFAULT_ARCHETYPES = [
    {
        "key": "regenerative_titan", "title": "The Regenerative Titan",
        "description": "A truly regenerative enterprise.", "mr_threshold": 1.8,
        "icon": "", "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "is_default": True, "requires_solvent": True,
    },
    {
        "key": "derisked_safe_haven", "title": "The De-risked Safe-Haven",
        "description": "A resilient corporation that avoided the worst tail risks.",
        "mr_threshold": 1.2, "icon": "",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)", "is_default": True,
        "requires_solvent": True,
    },
    {
        "key": "fragile_giant", "title": "The Fragile Giant",
        "description": "Big but brittle.", "mr_threshold": 0.8, "icon": "",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)", "is_default": True,
        "requires_solvent": True,
    },
    {
        # AR-B: solvent but low-M_R — kept the lights on, unremarkable. Reserving
        # "Stranded Relic" for value destruction stops a solvent, cautious
        # operator being mislabelled a failure.
        "key": "pragmatic_operator", "title": "The Pragmatic Operator",
        "description": "Kept the lights on — solvent and steady, but the strategy "
                       "left regenerative value on the table.",
        "mr_threshold": 0.0, "icon": "",
        "gradient": "linear-gradient(135deg, #475569, #334155)", "is_default": True,
        "requires_solvent": True,
    },
    {
        # AR-B: strong ESG story on an insolvent balance sheet — the honest label
        # for a high-M_R company that still destroyed enterprise value.
        "key": "hollow_idealist", "title": "The Hollow Idealist",
        "description": "A regenerative story the balance sheet couldn't fund — "
                       "enterprise value turned negative.",
        "mr_threshold": 1.2, "icon": "",
        "gradient": "linear-gradient(135deg, #a855f7, #7e22ce)", "is_default": True,
        "requires_solvent": False,
    },
    {
        "key": "stranded_relic", "title": "The Stranded Relic",
        "description": "A cautionary tale.", "mr_threshold": 0.0, "icon": "",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)", "is_default": True,
        "requires_solvent": False,
    },
    {
        "key": "turnaround_manager", "title": "The Turnaround Manager",
        "description": "Rescued from the brink through crisis management.",
        "mr_threshold": 0.0, "icon": "",
        "gradient": "linear-gradient(135deg, #8b5cf6, #6d28d9)", "is_default": True,
        "requires_solvent": False,
    },
]


# ═════════════════════════════════════════════════════════════════
#  SHARED MARKETPLACE — Cross-Cohort Resources (FEATURE 28)
# ═════════════════════════════════════════════════════════════════

_cohort_marketplaces: dict[str, dict] = {
    "default": {
        "carbon_credit_pool": {
            "total_available": 500,       # Total carbon credits in the market
            "price_per_credit": 50_000,   # Base price per credit ($50K)
            "purchased": {},              # {session_id: quantity}
            "price_history": [50_000],    # Track price changes
        },
        "green_talent_pool": {
            "total_available": 100,       # Total green specialists available
            "cost_per_hire": 200_000,     # Base cost per hire ($200K)
            "hired": {},                  # {session_id: quantity}
            "cost_history": [200_000],    # Track cost changes
        },
    }
}

# Maintain backward compatibility with unit tests referencing _shared_marketplace directly
_shared_marketplace: dict = _cohort_marketplaces["default"]


def _get_cohort_key(session_id: str) -> str:
    """Determine the top-level cohort key for a session_id."""
    try:
        from database_memory import _sessions
        sess = _sessions.get(session_id)
        if sess:
            return sess.get("parent_cohort_id") or session_id
    except Exception:
        pass
    return "default"


def get_marketplace_for_cohort(cohort_key: str) -> dict:
    """Get or initialize the marketplace pool dict for a given cohort."""
    if cohort_key not in _cohort_marketplaces:
        _cohort_marketplaces[cohort_key] = {
            "carbon_credit_pool": {
                "total_available": 500,
                "price_per_credit": 50_000,
                "purchased": {},
                "price_history": [50_000],
            },
            "green_talent_pool": {
                "total_available": 100,
                "cost_per_hire": 200_000,
                "hired": {},
                "cost_history": [200_000],
            },
        }
    return _cohort_marketplaces[cohort_key]


def _persist_marketplace_state():
    """Trigger snapshot persistence inside database_memory."""
    try:
        from database_memory import _persist
        _persist()
    except Exception:
        pass


def get_marketplace_state(session_id: str = "default") -> dict:
    """Return current marketplace state with dynamic pricing for a cohort."""
    cohort_key = _get_cohort_key(session_id)
    mp = get_marketplace_for_cohort(cohort_key)

    # Dynamic pricing: scarcity drives prices up
    cc = mp["carbon_credit_pool"]
    total_purchased_cc = sum(cc["purchased"].values())
    remaining_cc = max(0, cc["total_available"] - total_purchased_cc)
    # Price increases 2% for every 10 credits sold (scarcity premium)
    scarcity_factor_cc = 1.0 + (total_purchased_cc / 10) * 0.02
    current_cc_price = round(cc["price_per_credit"] * scarcity_factor_cc, 2)

    gt = mp["green_talent_pool"]
    total_hired = sum(gt["hired"].values())
    remaining_gt = max(0, gt["total_available"] - total_hired)
    scarcity_factor_gt = 1.0 + (total_hired / 5) * 0.03
    current_gt_cost = round(gt["cost_per_hire"] * scarcity_factor_gt, 2)

    return {
        "carbon_credits": {
            "remaining": remaining_cc,
            "total": cc["total_available"],
            "current_price": current_cc_price,
            "scarcity_factor": round(scarcity_factor_cc, 3),
            "purchases_by_team": dict(cc["purchased"]),
        },
        "green_talent": {
            "remaining": remaining_gt,
            "total": gt["total_available"],
            "current_cost": current_gt_cost,
            "scarcity_factor": round(scarcity_factor_gt, 3),
            "hires_by_team": dict(gt["hired"]),
        },
    }


def purchase_carbon_credits(session_id: str, quantity: int) -> dict:
    """Purchase carbon credits from the cohort-isolated pool. Returns result."""
    cohort_key = _get_cohort_key(session_id)
    mp = get_marketplace_for_cohort(cohort_key)
    cc = mp["carbon_credit_pool"]
    total_purchased = sum(cc["purchased"].values())
    remaining = cc["total_available"] - total_purchased

    if quantity <= 0:
        return {"success": False, "error": "Quantity must be positive"}
    if quantity > remaining:
        return {"success": False, "error": f"Only {remaining} credits remaining",
                "remaining": remaining}

    scarcity = 1.0 + (total_purchased / 10) * 0.02
    price = round(cc["price_per_credit"] * scarcity * quantity, 2)
    cc["purchased"][session_id] = cc["purchased"].get(session_id, 0) + quantity
    cc["price_history"].append(round(cc["price_per_credit"] * scarcity, 2))

    _persist_marketplace_state()

    return {
        "success": True,
        "quantity": quantity,
        "total_cost": price,
        "unit_price": round(price / quantity, 2),
        "remaining_in_pool": remaining - quantity,
        "ncd_reduction_per_credit": 5,  # Each credit reduces NCD by 5 points
    }


def hire_green_talent(session_id: str, quantity: int) -> dict:
    """Hire green specialists from the cohort-isolated pool."""
    cohort_key = _get_cohort_key(session_id)
    mp = get_marketplace_for_cohort(cohort_key)
    gt = mp["green_talent_pool"]
    total_hired = sum(gt["hired"].values())
    remaining = gt["total_available"] - total_hired

    if quantity <= 0:
        return {"success": False, "error": "Quantity must be positive"}
    if quantity > remaining:
        return {"success": False, "error": f"Only {remaining} specialists remaining",
                "remaining": remaining}

    scarcity = 1.0 + (total_hired / 5) * 0.03
    cost = round(gt["cost_per_hire"] * scarcity * quantity, 2)
    gt["hired"][session_id] = gt["hired"].get(session_id, 0) + quantity
    gt["cost_history"].append(round(gt["cost_per_hire"] * scarcity, 2))

    _persist_marketplace_state()

    return {
        "success": True,
        "quantity": quantity,
        "total_cost": cost,
        "unit_cost": round(cost / quantity, 2),
        "remaining_in_pool": remaining - quantity,
        "synergy_bonus_per_hire": 0.005,  # Each hire boosts synergy by 0.5%
    }

# C6/C2 settings-resolution unification implemented (see climate_paradigm,
# resolve_climate_paradigm, seed_effective_flags above).

