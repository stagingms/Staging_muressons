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
    "super_admin": 3,
    "admin": 3,           # M-5: alias for super_admin — prevents undefined hierarchy level
    "lead_facilitator": 2,
    "facilitator": 1,
}

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
    ],
    "lead_facilitator": [
        # All facilitator tabs plus:
        "manual_override", "auto_pause",
        "undo_round", "materiality", "activity_log",
    ],
    "super_admin": ["*"],  # All tabs
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


def get_allowed_tabs(fac: dict) -> list[str]:
    """Return the list of tab IDs this facilitator is allowed to access."""
    role = get_role(fac)
    if role == "super_admin":
        return ["*"]
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
    """Check if a facilitator owns a session (multi-tenancy enforcement).
    Super admins can access all sessions."""
    if get_role(fac) == "super_admin":
        return True
    fac_id = fac.get("facilitator_id", "")
    session_fac = session.get("facilitator_id", "")
    return session_fac == fac_id


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
    "system_frozen",
    "freeze_message",
    "freeze_started_at",
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
})


def get_effective_settings(session_id: str | None = None) -> dict:
    """Return the effective settings for a cohort.

    GOD-012: Merges global _god_mode_settings with any per-cohort overrides
    in cohort_settings[session_id].  Per-cohort values shadow their global
    counterparts; absent keys fall back to the global default.

    When session_id is None or has no overrides, returns the global dict
    directly (no copy overhead for the 99 % case).
    """
    if not session_id or session_id not in cohort_settings:
        return _god_mode_settings
    # Shallow merge — cohort overrides win over globals
    return {**_god_mode_settings, **cohort_settings[session_id]}


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR REGISTRY (with JSON persistence)
# ═════════════════════════════════════════════════════════════════

_FAC_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "db", "facilitator_registry.json"
)

# ── SEC-1: Token version store (session revocation kill-switch) ──
# Each facilitator (including the virtual god_mode account) has a monotonic
# token_version. It is embedded in every issued JWT as the "ver" claim and
# re-checked on every request. Incrementing a facilitator's version instantly
# invalidates ALL of their outstanding tokens — the missing kill-switch that
# previously left a leaked god_mode cookie usable indefinitely.
_TOKEN_VERSION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "db", "token_versions.json"
)
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
                        deduped.append(fac)
                data = deduped
                print(f"[persistence] Restored {len(data)} facilitator(s) from registry.")
                return data
    except Exception as e:
        print(f"[persistence] Failed to load facilitator registry: {e}")
    # LOW-003: Emergency fallback — log credentials via the logging subsystem
    # (not raw print/stdout) so that log-routing rules can gate who sees this.
    # The plaintext password is intentionally included because it is the ONLY
    # recovery path when the registry file is absent; keep this log line out of
    # publicly-accessible log forwarders in production environments.
    _shared_logger.warning(
        "\n"
        "╔══════════════════════════════════════════════════════╗\n"
        "║  EMERGENCY — Registry unavailable. Fallback active.  ║\n"
        "║  SENSITIVE: do not forward to public log collectors. ║\n"
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
        }
    p = _round_pacing[session_id]
    p.setdefault("schedule", [])
    p.setdefault("_timer_tasks", [])
    p.setdefault("set_by", None)
    return p


def is_round_unlocked(session_id: str, round_number: int) -> bool:
    """Check if a given round is unlocked for progression."""
    pacing = _get_pacing(session_id)
    if pacing["mode"] == "free":
        return True
    return round_number <= pacing["unlocked_round"]


def is_pacing_set_by_facilitator(session_id: str) -> bool:
    """Check if pacing for a session was explicitly set by a facilitator.
    If True, God Mode cannot override it."""
    pacing = _get_pacing(session_id)
    return pacing.get("set_by") is not None and pacing["mode"] != "free"


# ═════════════════════════════════════════════════════════════════
#  COHORT MANAGEMENT
# ═════════════════════════════════════════════════════════════════

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
        if not _god_mode_settings.get("allow_facilitator_cohort_creation", True):
            fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
            if not fac or ROLE_HIERARCHY.get(get_role(fac), 0) < ROLE_HIERARCHY.get("super_admin", 3):
                return False
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

DEFAULT_ARCHETYPES = [
    {
        "key": "regenerative_titan", "title": "The Regenerative Titan",
        "description": "A truly regenerative enterprise.", "mr_threshold": 1.8,
        "icon": "", "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "is_default": True,
    },
    {
        "key": "derisked_safe_haven", "title": "The De-risked Safe-Haven",
        "description": "A resilient corporation that avoided the worst tail risks.",
        "mr_threshold": 1.2, "icon": "",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)", "is_default": True,
    },
    {
        "key": "fragile_giant", "title": "The Fragile Giant",
        "description": "Big but brittle.", "mr_threshold": 0.8, "icon": "",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)", "is_default": True,
    },
    {
        "key": "stranded_relic", "title": "The Stranded Relic",
        "description": "A cautionary tale.", "mr_threshold": 0.0, "icon": "",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)", "is_default": True,
    },
    {
        "key": "turnaround_manager", "title": "The Turnaround Manager",
        "description": "Rescued from the brink through crisis management.",
        "mr_threshold": 0.0, "icon": "",
        "gradient": "linear-gradient(135deg, #8b5cf6, #6d28d9)", "is_default": True,
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

