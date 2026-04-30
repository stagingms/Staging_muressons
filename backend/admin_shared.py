"""
Muressons Global Command — Admin Shared State
Shared in-memory state and utilities used by all admin sub-routers.
Extracted from admin_router.py (ARCH-002) to decouple domain modules.

All other modules that previously imported from admin_router should now
import shared state from this module instead.
"""
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any, Optional

from config import MASTER_PASSWORD

# ═════════════════════════════════════════════════════════════════
#  GOD MODE GLOBAL SETTINGS
# ═════════════════════════════════════════════════════════════════

_god_mode_settings: dict = {
    "allow_facilitator_cohort_creation": True,
    "system_frozen": False,
    "freeze_message": "",
    "freeze_started_at": None,
    "simulation_mode": "standard",
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
}


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR REGISTRY (with JSON persistence)
# ═════════════════════════════════════════════════════════════════

_FAC_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "db", "facilitator_registry.json"
)

_DEFAULT_FACILITATOR = {
    "facilitator_id": "Jose",
    "name": "Jose",
    "password": "123",
    "created_at": "2026-01-01T00:00:00+00:00",
    "max_cohorts": 5,
    "cohorts_created": 0,
    "is_admin": True,
    "enabled": True,
}


def _load_facilitator_registry() -> list[dict]:
    """Load facilitator registry from disk. Falls back to default if not found."""
    try:
        if os.path.exists(_FAC_REGISTRY_PATH):
            with open(_FAC_REGISTRY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data:
                print(f"[persistence] Restored {len(data)} facilitator(s) from registry.")
                return data
    except Exception as e:
        print(f"[persistence] Failed to load facilitator registry: {e}")
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


_facilitator_registry: list[dict] = _load_facilitator_registry()
_next_facilitator_id: int = 1


# ═════════════════════════════════════════════════════════════════
#  PLAYER REGISTRY
# ═════════════════════════════════════════════════════════════════

_player_registry: list[dict] = []
_next_player_id: int = 1


# ═════════════════════════════════════════════════════════════════
#  SESSION MESSAGES & INTERVENTIONS
# ═════════════════════════════════════════════════════════════════

_session_messages: dict[str, list[dict]] = {}
_session_interventions: dict[str, dict] = {}


# ═════════════════════════════════════════════════════════════════
#  AUDIT LOG & CRISIS HISTORY
# ═════════════════════════════════════════════════════════════════

_god_mode_audit_log: list[dict] = []
_crisis_trigger_history: list[dict] = []


# ═════════════════════════════════════════════════════════════════
#  PRACTICE MODE
# ═════════════════════════════════════════════════════════════════

_practice_mode: dict[str, bool] = {}


def is_practice_mode(session_id: str) -> bool:
    """Check if a session is in practice mode."""
    return _practice_mode.get(session_id, False)


# ═════════════════════════════════════════════════════════════════
#  ROUND PACING
# ═════════════════════════════════════════════════════════════════

_round_pacing: dict[str, dict] = {}


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
        }
    p = _round_pacing[session_id]
    p.setdefault("schedule", [])
    p.setdefault("_timer_tasks", [])
    return p


def is_round_unlocked(session_id: str, round_number: int) -> bool:
    """Check if a given round is unlocked for progression."""
    pacing = _get_pacing(session_id)
    if pacing["mode"] == "free":
        return True
    return round_number <= pacing["unlocked_round"]


# ═════════════════════════════════════════════════════════════════
#  COHORT MANAGEMENT
# ═════════════════════════════════════════════════════════════════

def check_and_increment_cohort_count(facilitator_id: str) -> bool:
    """Check if facilitator can create another cohort. If yes, increment and return True."""
    if not facilitator_id:
        return True
    if not _god_mode_settings.get("allow_facilitator_cohort_creation", True):
        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
        if not fac or not fac.get("is_admin"):
            return False
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
    if not fac:
        return True
    if not fac.get("enabled", True):
        return False
    max_c = fac.get("max_cohorts", 5)
    created = fac.get("cohorts_created", 0)
    if created >= max_c:
        return False
    fac["cohorts_created"] = created + 1
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
        "icon": "\U0001f331", "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "is_default": True,
    },
    {
        "key": "derisked_safe_haven", "title": "The De-risked Safe-Haven",
        "description": "A resilient corporation that avoided the worst tail risks.",
        "mr_threshold": 1.2, "icon": "\U0001f3e6",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)", "is_default": True,
    },
    {
        "key": "fragile_giant", "title": "The Fragile Giant",
        "description": "Big but brittle.", "mr_threshold": 0.8, "icon": "\u26a0\ufe0f",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)", "is_default": True,
    },
    {
        "key": "stranded_relic", "title": "The Stranded Relic",
        "description": "A cautionary tale.", "mr_threshold": 0.0, "icon": "\U0001f480",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)", "is_default": True,
    },
    {
        "key": "turnaround_manager", "title": "The Turnaround Manager",
        "description": "Rescued from the brink through crisis management.",
        "mr_threshold": 0.0, "icon": "🔧",
        "gradient": "linear-gradient(135deg, #8b5cf6, #6d28d9)", "is_default": True,
    },
]


# ═════════════════════════════════════════════════════════════════
#  SHARED MARKETPLACE — Cross-Cohort Resources (FEATURE 28)
# ═════════════════════════════════════════════════════════════════

_shared_marketplace: dict = {
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


def get_marketplace_state() -> dict:
    """Return current marketplace state with dynamic pricing."""
    mp = _shared_marketplace

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
    """Purchase carbon credits from the shared pool. Returns result."""
    cc = _shared_marketplace["carbon_credit_pool"]
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

    return {
        "success": True,
        "quantity": quantity,
        "total_cost": price,
        "unit_price": round(price / quantity, 2),
        "remaining_in_pool": remaining - quantity,
        "ncd_reduction_per_credit": 5,  # Each credit reduces NCD by 5 points
    }


def hire_green_talent(session_id: str, quantity: int) -> dict:
    """Hire green specialists from the shared pool."""
    gt = _shared_marketplace["green_talent_pool"]
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

    return {
        "success": True,
        "quantity": quantity,
        "total_cost": cost,
        "unit_cost": round(cost / quantity, 2),
        "remaining_in_pool": remaining - quantity,
        "synergy_bonus_per_hire": 0.005,  # Each hire boosts synergy by 0.5%
    }

