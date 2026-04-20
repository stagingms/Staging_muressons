"""
Muressons Global Command — Admin Router (God Mode)
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

import database as db
import materiality_db as mat_db
from config import MASTER_PASSWORD
from models import MaterialityIssue, InterdependenceLink, MaterialityConfig

admin_router = APIRouter(prefix="/api/admin", tags=["Admin — God Mode"])

# ── In-memory message store for facilitator messages ────────────
_session_messages: dict[str, list[dict]] = {}  # session_id → [message dicts]


def _get_session_paradigm(session_id: str) -> str:
    """Read decision_paradigm directly from the raw in-memory session store,
    bypassing the filtered dict returned by fetch_all_sessions()."""
    from database_memory import _sessions
    raw = _sessions.get(session_id)
    if raw:
        return raw.get("decision_paradigm", "legacy_abc") or "legacy_abc"
    return "legacy_abc"

# ── God Mode global settings ────────────────────────────────────
_god_mode_settings: dict = {
    "allow_facilitator_cohort_creation": True,
    "system_frozen": False,
    "freeze_message": "",
    "freeze_started_at": None,
    # Advanced Climate Engine fields (set by Sim Switchboard)
    "simulation_mode": "standard",          # "standard" | "advanced_climate"
    "global_carbon_fee": 40,
    "market_hostility_index": 5,
    "scope_3_threshold": 2.5,
    # Custom profile archetypes (empty = use hardcoded defaults in round_logic.py)
    "custom_archetypes": [],
    # Economic complexity engine tunables
    "overrun_probability": 0.25,       # 25% chance of overrun on $3M+ CAPEX
    "overrun_severity": 0.15,          # 15% cost overrun when triggered
}

# Default archetypes mirroring round_logic.py — shown as read-only reference in God Mode UI
DEFAULT_ARCHETYPES = [
    {
        "key": "regenerative_titan",
        "title": "The Regenerative Titan",
        "description": (
            "A truly regenerative enterprise. Muressons has rebuilt natural capital, "
            "earned deep social trust, and delivered superior financial returns. "
            "This is the gold standard of Year 3."
        ),
        "mr_threshold": 1.8,
        "icon": "🌱",
        "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "is_default": True,
    },
    {
        "key": "derisked_safe_haven",
        "title": "The De-risked Safe-Haven",
        "description": (
            "A resilient corporation that avoided the worst tail risks. "
            "Investors value the predictability, but innovation is stalling. "
            "Solid, but not transformational."
        ),
        "mr_threshold": 1.2,
        "icon": "🏦",
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
        "is_default": True,
    },
    {
        "key": "fragile_giant",
        "title": "The Fragile Giant",
        "description": (
            "Big but brittle. The cracks in social license and natural capital are visible. "
            "One more shock could trigger a cascade of write-downs and stakeholder defections."
        ),
        "mr_threshold": 0.8,
        "icon": "⚠️",
        "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
        "is_default": True,
    },
    {
        "key": "stranded_relic",
        "title": "The Stranded Relic",
        "description": (
            "A cautionary tale. Stranded assets, depleted social capital, "
            "and a brand synonymous with extraction. The Year 3 market has moved on. "
            "Terminal decline is imminent."
        ),
        "mr_threshold": 0.0,
        "icon": "💀",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)",
        "is_default": True,
    },
]


# ── God Mode audit log ──────────────────────────────────────────
_god_mode_audit_log: list[dict] = []

# ── Crisis trigger history ──────────────────────────────────────
_crisis_trigger_history: list[dict] = []

# ── In-memory facilitator registry (with JSON persistence) ──────
_FAC_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "facilitator_registry.json")

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

@admin_router.patch("/global-settings", summary="Update global simulation settings (Sim Switchboard)")
async def patch_global_settings(body: GlobalSettingsPatch):
    """Sim Switchboard endpoint — updates simulation_mode and climate parameters."""
    # FIX AUDIT-017: Use Pydantic to validate input types
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        _god_mode_settings[key] = value
    
    import logging
    logging.info(f"[god-mode] Global settings updated: {_god_mode_settings}")
    return {"status": "ok", "settings": _god_mode_settings}


# ── Archetype CRUD ───────────────────────────────────────────────

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
async def add_archetype(body: dict = Body(...)):
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
async def update_archetype(key: str, body: dict = Body(...)):
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
async def delete_archetype(key: str):
    customs = _god_mode_settings.get("custom_archetypes", [])
    before = len(customs)
    _god_mode_settings["custom_archetypes"] = [a for a in customs if a["key"] != key]
    if len(_god_mode_settings["custom_archetypes"]) == before:
        raise HTTPException(404, f"Custom archetype '{key}' not found (defaults cannot be deleted, only overridden)")
    print(f"[god-mode] Archetype deleted: {key}")
    return {"status": "deleted", "key": key}


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
        "is_admin": False,
        "enabled": True,
        "permissions": req.permissions or {
            "can_undo_rounds": True,
            "can_override_decisions": True,
            "can_modify_materiality": True,
            "can_manage_auto_pause": True,
        }
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
        }
        _facilitator_registry.append(fac)
        _persist_facilitators()
    if not fac or (not master_ok and fac["password"] != password):
        raise HTTPException(403, "Invalid facilitator ID or password")
    
    return {
        "status": "success", 
        "facilitator_id": fac["facilitator_id"], 
        "name": fac["name"], 
        "username": fac.get("username", ""),
        "is_admin": fac.get("is_admin", False)
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


def check_and_increment_cohort_count(facilitator_id: str) -> bool:
    """Check if facilitator can create another cohort. If yes, increment and return True."""
    if not facilitator_id:
        return True  # No facilitator specified — no limit enforced
    # Global toggle: if disabled, only admin facilitators may create
    if not _god_mode_settings.get("allow_facilitator_cohort_creation", True):
        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
        if not fac or not fac.get("is_admin"):
            return False
    fac = next((f for f in _facilitator_registry if f["facilitator_id"] == facilitator_id), None)
    if not fac:
        return True  # Unknown facilitator — allow (auto-created via master password)
    # Per-facilitator enabled check
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
#  PRACTICE MODE — Dry-run up to Round 2, then reset
# ═════════════════════════════════════════════════════════════════

# In-memory practice mode flags: {session_id: True}
_practice_mode: dict[str, bool] = {}


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


def is_practice_mode(session_id: str) -> bool:
    """Check if a session (or its parent cohort) is in practice mode."""
    return _practice_mode.get(session_id, False)



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
_round_pacing: dict[str, dict] = {}


def _get_pacing(session_id: str) -> dict:
    """Get or create default pacing config for a session."""
    if session_id not in _round_pacing:
        _round_pacing[session_id] = {
            "mode": "free",
            "unlocked_round": 999,   # free = all rounds unlocked
            "interval_seconds": 300,
            "next_unlock_at": None,
            "schedule": [],           # list of ISO datetimes, one per round
            "_timer_tasks": [],       # list of asyncio Tasks (one per scheduled round)
            "_timer_task": None,      # legacy single-shot task
        }
    p = _round_pacing[session_id]
    # Back-fill new fields for old in-memory entries
    p.setdefault("schedule", [])
    p.setdefault("_timer_tasks", [])
    return p


def is_round_unlocked(session_id: str, round_number: int) -> bool:
    """Check if a given round is unlocked for progression."""
    pacing = _get_pacing(session_id)
    if pacing["mode"] == "free":
        return True
    return round_number <= pacing["unlocked_round"]


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
                if latest and latest["round_number"] <= current_unlocked:
                    # Player hasn't committed yet — auto-commit
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

    # Broadcast mode change
    await manager.push_to_session(session_id, {
        "type": "pacing_mode_changed",
        "mode": pacing["mode"],
        "unlocked_round": pacing["unlocked_round"],
        "interval_seconds": pacing["interval_seconds"],
        "schedule": pacing.get("schedule", []),
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

_player_registry: list[dict] = []
_next_player_id: int = 1

_session_interventions: dict[str, dict] = {}

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
            "quarters. Immediate cost reduction or capital raise required."
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
    """Toggle Year 3 Carbon Tax from $250/ton to $400/ton."""
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

        leaderboard.append({
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
        })

    # Sort by terminal value descending
    leaderboard.sort(key=lambda x: x["terminal_value"], reverse=True)
    return {"leaderboard": leaderboard}


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
    return {"categories": registry, "total": len(registry)}


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
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    selected_bu = global_state.get("r2_selected_bu")

    if selected_bu is None:
        # Auto-select if not yet chosen
        import random
        VALID_BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]
        selected_bu = random.choice(VALID_BU_IDS)
        global_state["r2_selected_bu"] = selected_bu
        await db.update_latest_global_state(session_id, global_state, current["bu_states"])

    BU_LABELS = {
        "pharma": "Muressons Pharma",
        "electronics": "Muressons Electronics",
        "consumer_goods": "Muressons Consumer Goods",
        "software": "Muressons Software"
    }
    return {
        "selected_bu": selected_bu,
        "bu_label": BU_LABELS.get(selected_bu, selected_bu),
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

    return {
        "session_id": session_id,
        "cohort_name": session_info.get("cohort_name", "Unknown"),
        "current_round": best_history[-1]["round_number"] if best_history else 1,
        "rounds": debrief_rounds,
        "trend_history": trend_history,
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
    count = await db.delete_all_sessions()

    # Notify admin dashboard
    await manager.broadcast_admin({
        "type": "all_sessions_reset",
        "count": count,
    })

    return {"status": "all_deleted", "sessions_removed": count}


# ═════════════════════════════════════════════════════════════════
#  RESOURCE LIBRARY — Master Library + Per-Session Unlock Control
# ═════════════════════════════════════════════════════════════════

class ResourceUnlockCondition(BaseModel):
    metric: str = ""           # e.g. "Investment_E5", "G1_Score", "BU_Sustainability_Score"
    operator: str = ">="       # ">=", "<=", "==", ">", "<"
    value: float = 0
    min_round: int = 1         # Minimum round before condition can trigger

class ResourceEffect(BaseModel):
    target: str = ""           # e.g. "Electronics_OpEx", "S2_Financial_Risk"
    modifier: float = 0        # e.g. -0.10 for 10% reduction

class ResourceItem(BaseModel):
    id: str
    title: str
    type: str  # "PDF" | "Video" | "Weblink" | "Memo" | "NotebookLM"
    url: str = ""
    tags: list[str] = []
    category: str = "General"  # "Ecological" | "Social" | "Economic" | "General"
    facilitator_default_round: int = 1
    impact_link: str = ""
    visibility: str = "Standard"  # "Standard" | "Hidden"
    unlock_condition: Optional[dict] = None  # {metric, operator, value, min_round}
    effect: Optional[dict] = None            # {target, modifier}
    facilitator_strategy: str = ""           # Deployment hint for facilitator cheat sheet

class ResourceLibraryUpload(BaseModel):
    Resource_Library: list[ResourceItem]

class ResourceUnlockRequest(BaseModel):
    resource_ids: list[str]
    round_number: int

# ── In-memory stores ────────────────────────────────────────────

_resource_library: list[dict] = [
    # ── Standard Resources ──────────────────────────────────────
    {
        "id": "RES_001",
        "title": "The ESRS Double Materiality Handbook",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/esrs_handbook.pdf",
        "tags": ["General", "CSRD"],
        "category": "General",
        "facilitator_default_round": 1,
        "impact_link": "",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Baseline: Drop immediately. Sets the rules. Players who skip this will fail to understand the Volatility factor.",
    },
    {
        "id": "RES_002",
        "title": "Pharma Wastewater Standards 2026",
        "type": "Weblink",
        "url": "https://epa.gov/pharma-standards",
        "tags": ["Pharma", "E2"],
        "category": "Ecological",
        "facilitator_default_round": 4,
        "impact_link": "E2 (Pharma)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "Drop in Round 4 to coincide with ESG Contagion Crisis. Forces Pharma BU investment decisions.",
    },
    {
        "id": "RES_003",
        "title": "Global Carbon Tax Forecast (2026-2030)",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/carbon_tax_forecast.pdf",
        "tags": ["General", "E1", "Climate"],
        "category": "Ecological",
        "facilitator_default_round": 3,
        "impact_link": "E1 (All BUs)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Warning: Drop in Round 3 to force players to choose between short-term dividends and E1 (Climate) investments.",
    },
    {
        "id": "RES_004",
        "title": "Gobi Region Mineral Conflict Map",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gobi_conflict_map.pdf",
        "tags": ["Electronics", "S2", "Labor"],
        "category": "Social",
        "facilitator_default_round": 5,
        "impact_link": "S2 (Electronics)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Crisis Catalyst: Drop 1 turn before the embargo. If they don't act on this info, they deserve the 30% COGS hike.",
    },
    {
        "id": "RES_005",
        "title": "GDPR 2026 Compliance Brief",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gdpr_2026.pdf",
        "tags": ["Software", "S4", "Privacy"],
        "category": "Social",
        "facilitator_default_round": 3,
        "impact_link": "S4 (Software)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_006",
        "title": "The Business of Urban Mining",
        "type": "Video",
        "url": "https://youtube.com/antigravity_urban_mining",
        "tags": ["Electronics", "E5", "Circularity"],
        "category": "Ecological",
        "facilitator_default_round": 6,
        "impact_link": "E5 (Conglomerate)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_007",
        "title": "API Effluent Technical Guide",
        "type": "Weblink",
        "url": "https://antigravity-sim.com/docs/api_effluent_guide",
        "tags": ["Pharma", "E2", "Pollution"],
        "category": "Ecological",
        "facilitator_default_round": 4,
        "impact_link": "E2 (Pharma)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_008",
        "title": "Gobi Region Human Rights Map",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gobi_human_rights.pdf",
        "tags": ["Electronics", "S2", "Labor"],
        "category": "Social",
        "facilitator_default_round": 5,
        "impact_link": "S2 (Electronics)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    # ── Hidden Resources (Auto-Unlock via Conditions) ───────────
    {
        "id": "HIDDEN_RES_001",
        "title": "The Urban Mining Efficiency Secret",
        "type": "Video",
        "url": "https://antigravity-sim.com/hidden/urban_mining_secret",
        "tags": ["Electronics", "E5", "Circularity"],
        "category": "Ecological",
        "facilitator_default_round": 0,
        "impact_link": "E5 (Electronics)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Investment_E5", "operator": ">=", "value": 150_000_000, "min_round": 1},
        "effect": {"target": "Electronics_OpEx", "modifier": -0.10},
        "facilitator_strategy": "Investment reward: Unlocks when team invests $150M+ in Electronics. Reduces future Electronics BU upgrade costs by 10%.",
    },
    {
        "id": "HIDDEN_RES_002",
        "title": "Whistleblower Brief: Gobi Mine Ethics",
        "type": "Memo",
        "url": "",
        "tags": ["Electronics", "S2", "Governance"],
        "category": "Social",
        "facilitator_default_round": 0,
        "impact_link": "S2 (Electronics)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "G1_Score", "operator": "==", "value": 10, "min_round": 1},
        "effect": {"target": "S2_Financial_Risk", "modifier": -0.50},
        "facilitator_strategy": "Governance reward: Unlocks when G1 Ethics Score reaches 10. Halves financial risk from S2 labor issues.",
    },
    {
        "id": "HIDDEN_RES_003",
        "title": "Bio-Safe API Manufacturing Patent",
        "type": "PDF",
        "url": "https://antigravity-sim.com/hidden/biosafe_patent.pdf",
        "tags": ["Pharma", "E2"],
        "category": "Ecological",
        "facilitator_default_round": 0,
        "impact_link": "E2 (Pharma)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Pharma_E2_Score", "operator": ">=", "value": 8.5, "min_round": 4},
        "effect": {"target": "Pharma_Contract", "modifier": 200_000_000},
        "facilitator_strategy": "Sustainability reward: Unlocks when Pharma E2 score reaches 8.5+. Grants access to a $200M government contract in Round 8.",
    },
    {
        "id": "HIDDEN_RES_004",
        "title": "The Ethical AI Advantage",
        "type": "Memo",
        "url": "",
        "tags": ["Software", "G1", "AI"],
        "category": "Economic",
        "facilitator_default_round": 0,
        "impact_link": "G1 (Software)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Software_G1_Score", "operator": "==", "value": 10, "min_round": 1},
        "effect": {"target": "Data_Breach_Prevention", "modifier": 1},
        "facilitator_strategy": "Risk mitigation: Unlocks when Software G1 score reaches 10. Prevents the Data Breach event from triggering.",
    },
]

# session_id → list of {resource_id, unlocked_at_round, unlocked_at_time, is_strategic_drop, trigger}
_session_resource_state: dict[str, list[dict]] = {}


# ── Hidden Resource Trigger Engine ──────────────────────────────

def _extract_metric_value(metric: str, global_state: dict, bu_states: list[dict]) -> Optional[float]:
    """Extract a metric value from game state for hidden resource condition evaluation."""
    # Investment-based metrics (cumulative capex allocated to a BU category)
    if metric.startswith("Investment_"):
        bu_key = metric.replace("Investment_", "").lower()
        # Map E5 → electronics, etc.
        bu_map = {"e5": "electronics", "e1": "pharma", "e2": "pharma", "s2": "electronics", "g1": "software"}
        target_bu = bu_map.get(bu_key, bu_key)
        bu = next((b for b in bu_states if b["bu_id"] == target_bu), None)
        if bu:
            # Use cumulative investment tracked in active_event_flags
            flags = global_state.get("active_event_flags", {})
            return flags.get(f"cumulative_investment_{target_bu}", 0)
        return 0

    # BU-specific sustainability/score metrics
    if metric == "G1_Score":
        sw = next((b for b in bu_states if b["bu_id"] == "software"), None)
        return (10 - sw.get("governance_risk_score", 10)) if sw else 0

    if metric == "Software_G1_Score":
        sw = next((b for b in bu_states if b["bu_id"] == "software"), None)
        return (10 - sw.get("governance_risk_score", 10)) if sw else 0

    if metric == "Pharma_E2_Score":
        pharma = next((b for b in bu_states if b["bu_id"] == "pharma"), None)
        if pharma:
            # Derive E2 score from social license and natural capital debt inversely
            sl = pharma.get("social_license_score", 50)
            return sl / 10.0  # Normalize 0-100 → 0-10 scale
        return 0

    if metric == "BU_Sustainability_Score":
        avg_sl = sum(b.get("social_license_score", 50) for b in bu_states) / len(bu_states) if bu_states else 50
        return avg_sl / 10.0  # Normalize to 0-10 scale

    # Generic global state lookup
    return global_state.get(metric, 0)


def _evaluate_condition(actual: float, operator: str, target: float) -> bool:
    """Evaluate a single condition: actual <op> target."""
    if operator == ">=": return actual >= target
    if operator == "<=": return actual <= target
    if operator == "==": return actual == target
    if operator == ">":  return actual > target
    if operator == "<":  return actual < target
    return False


async def check_hidden_resource_triggers(
    session_id: str,
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
) -> list[dict]:
    """
    Evaluate all hidden resources against current game state.
    Auto-unlocks any that meet their conditions.
    Returns list of newly unlocked hidden resources.
    """
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    newly_triggered = []

    for res in _resource_library:
        if res.get("visibility") != "Hidden":
            continue
        if res["id"] in existing_ids:
            continue  # Already unlocked

        cond = res.get("unlock_condition")
        if not cond:
            continue

        # Check min_round
        if round_number < cond.get("min_round", 1):
            continue

        # Extract and evaluate
        actual = _extract_metric_value(cond["metric"], global_state, bu_states)
        if actual is None:
            continue

        if _evaluate_condition(actual, cond["operator"], cond["value"]):
            entry = {
                "resource_id": res["id"],
                "unlocked_at_round": round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": False,
                "trigger": "auto_condition",
            }
            _session_resource_state[session_id].append(entry)
            newly_triggered.append(res)

    # Notify facilitator and players about auto-unlocked hidden resources
    if newly_triggered:
        await manager.push_to_session(session_id, {
            "type": "resource_unlocked",
            "resources": newly_triggered,
            "round": round_number,
            "is_hidden_unlock": True,
        })
        await manager.broadcast_admin({
            "type": "hidden_resource_triggered",
            "session_id": session_id,
            "resources": [{"id": r["id"], "title": r["title"], "effect": r.get("effect")} for r in newly_triggered],
            "round": round_number,
        })

    return newly_triggered


# ── Facilitator Deployment Guide ────────────────────────────────

FACILITATOR_DEPLOYMENT_GUIDE = [
    {"round": 1, "resource_id": "RES_001", "strategy": "The Baseline: Drop immediately. It sets the rules. If players don't read this, they will fail to understand the Volatility factor."},
    {"round": 3, "resource_id": "RES_003", "strategy": "The Warning: Drop to force players to choose between short-term dividends and E1 (Climate) investments."},
    {"round": 3, "resource_id": "RES_005", "strategy": "Supplement the Decision Tab. GDPR compliance context for Software BU decisions."},
    {"round": 4, "resource_id": "RES_002", "strategy": "Coincides with ESG Contagion Crisis. Forces Pharma BU investment decisions."},
    {"round": 4, "resource_id": "RES_007", "strategy": "Technical context for Pharma pollution decisions."},
    {"round": 5, "resource_id": "RES_004", "strategy": "The Crisis Catalyst: Drop 1 turn before the embargo. If they don't act on this info, they deserve the 30% COGS hike."},
    {"round": 5, "resource_id": "RES_008", "strategy": "Supplement the Gobi crisis with human rights context."},
    {"round": 6, "resource_id": "RES_006", "strategy": "Circular Economy context for Round 6 pivot decisions."},
]

@admin_router.get("/resources/deployment-guide", summary="Get the facilitator deployment guide")
async def get_deployment_guide():
    """Returns the round-by-round resource deployment cheat sheet."""
    # Enrich with resource titles
    guide = []
    for entry in FACILITATOR_DEPLOYMENT_GUIDE:
        res = next((r for r in _resource_library if r["id"] == entry["resource_id"]), None)
        guide.append({
            **entry,
            "title": res["title"] if res else "Unknown",
            "type": res["type"] if res else "",
        })

    # Add hidden resource guide
    hidden_guide = []
    for res in _resource_library:
        if res.get("visibility") == "Hidden":
            hidden_guide.append({
                "resource_id": res["id"],
                "title": res["title"],
                "unlock_condition": res.get("unlock_condition"),
                "effect": res.get("effect"),
                "strategy": res.get("facilitator_strategy", ""),
            })

    return {
        "round_deployment": guide,
        "hidden_resources": hidden_guide,
    }



# ── Master Library CRUD ─────────────────────────────────────────

@admin_router.get("/resources/library", summary="Get the master resource library")
async def get_resource_library():
    return {"resources": _resource_library}


@admin_router.put("/resources/library", summary="Upload / replace the master resource library")
async def upload_resource_library(body: ResourceLibraryUpload):
    global _resource_library
    _resource_library = [r.dict() for r in body.Resource_Library]
    return {"status": "uploaded", "count": len(_resource_library)}


@admin_router.post("/resources/library/item", summary="Add or update a single resource")
async def upsert_resource_item(item: ResourceItem):
    global _resource_library
    _resource_library = [r for r in _resource_library if r["id"] != item.id]
    _resource_library.append(item.dict())
    return item


@admin_router.delete("/resources/library/item/{resource_id}", summary="Delete a resource from the master library")
async def delete_resource_item(resource_id: str):
    global _resource_library
    _resource_library = [r for r in _resource_library if r["id"] != resource_id]
    return {"status": "deleted", "resource_id": resource_id}


@admin_router.post("/resources/upload", summary="Upload a physical resource file (PDF, image, etc)")
async def upload_resource_file(file: UploadFile = File(...)):
    """Uploads a file to the static assets directory and returns its public URL."""
    # Ensure uploads directory exists in the Next.js frontend/public folder
    project_root = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(project_root, "frontend", "public", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return the URL path
    file_url = f"/uploads/{file.filename}"
    return {"status": "uploaded", "url": file_url}


# ── Per-Session Resource State ──────────────────────────────────

@admin_router.get("/sessions/{session_id}/resources", summary="Get resource state for a session")
async def get_session_resources(session_id: str):
    """Returns the master library annotated with unlock status for this session."""
    unlocked = _session_resource_state.get(session_id, [])
    unlocked_ids = {u["resource_id"] for u in unlocked}

    annotated = []
    for res in _resource_library:
        unlock_info = next((u for u in unlocked if u["resource_id"] == res["id"]), None)
        annotated.append({
            **res,
            "unlocked": res["id"] in unlocked_ids,
            "unlocked_at_round": unlock_info["unlocked_at_round"] if unlock_info else None,
            "unlocked_at_time": unlock_info["unlocked_at_time"] if unlock_info else None,
            "is_strategic_drop": unlock_info.get("is_strategic_drop", False) if unlock_info else False,
        })
    return {"resources": annotated}


@admin_router.post("/sessions/{session_id}/resources/unlock", summary="Unlock resources for a session")
async def unlock_session_resources(session_id: str, body: ResourceUnlockRequest):
    """Unlock specific resources for a session at a given round."""
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    newly_unlocked = []
    for rid in body.resource_ids:
        if rid not in existing_ids:
            entry = {
                "resource_id": rid,
                "unlocked_at_round": body.round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": False,
            }
            _session_resource_state[session_id].append(entry)
            newly_unlocked.append(rid)

    # Build full resource objects for the push
    unlocked_resources = [r for r in _resource_library if r["id"] in newly_unlocked]

    # Push to players via WebSocket
    if newly_unlocked:
        await manager.push_to_session(session_id, {
            "type": "resource_unlocked",
            "resources": unlocked_resources,
            "round": body.round_number,
        })

    return {"status": "unlocked", "newly_unlocked": newly_unlocked, "total_unlocked": len(_session_resource_state[session_id])}


@admin_router.post("/sessions/{session_id}/resources/drop", summary="Strategic drop — reveal a resource mid-round")
async def strategic_drop_resource(session_id: str, body: ResourceUnlockRequest):
    """Drops resources mid-round as a 'breaking news' event. Marks them as strategic drops."""
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    dropped = []
    for rid in body.resource_ids:
        if rid not in existing_ids:
            entry = {
                "resource_id": rid,
                "unlocked_at_round": body.round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": True,
            }
            _session_resource_state[session_id].append(entry)
            dropped.append(rid)

    dropped_resources = [r for r in _resource_library if r["id"] in dropped]

    if dropped:
        await manager.push_to_session(session_id, {
            "type": "resource_dropped",
            "resources": dropped_resources,
            "round": body.round_number,
            "is_breaking_news": True,
        })
        await manager.broadcast_admin({
            "type": "resource_strategic_drop",
            "session_id": session_id,
            "resources": dropped_resources,
        })

    return {"status": "dropped", "dropped": dropped}


@admin_router.post("/sessions/{session_id}/resources/lock", summary="Re-lock a resource for a session")
async def lock_session_resource(session_id: str, body: dict = Body(...)):
    """Re-lock a mistakenly unlocked resource."""
    resource_id = body.get("resource_id")
    if not resource_id:
        raise HTTPException(400, "resource_id required")
    if session_id in _session_resource_state:
        _session_resource_state[session_id] = [
            u for u in _session_resource_state[session_id] if u["resource_id"] != resource_id
        ]
    return {"status": "locked", "resource_id": resource_id}


# ═════════════════════════════════════════════════════════════════
#  NOTEBOOKLM INTEGRATION — Linked Notebooks for Learners
# ═════════════════════════════════════════════════════════════════

class NotebookLMItem(BaseModel):
    id: str
    title: str
    share_url: str = ""
    description: str = ""
    content_types: list[str] = ["review"]  # "podcast" | "review" | "quiz"
    target_round: int = 1  # Round this notebook becomes available
    category: str = "General"  # "General" | "Ecological" | "Social" | "Economic"
    podcast_transcript: list[dict] = []  # [{speaker, text}, ...]
    review_content: str = ""  # Markdown-style review content
    quiz_questions: list[dict] = []  # [{question, options, correct, explanation}, ...]

# In-memory store for linked NotebookLM notebooks
from quiz_banks import (
    NLM_001_REVIEW, NLM_001_QUESTIONS,
    NLM_002_REVIEW, NLM_002_QUESTIONS,
    NLM_003_REVIEW, NLM_003_QUESTIONS,
)

_notebooklm_notebooks: list[dict] = [
    {
        "id": "NLM_001",
        "title": "ESG Fundamentals Deep Dive",
        "share_url": "",
        "description": "Interactive review of ESG concepts, CSRD requirements, and double materiality. Includes an AI-generated podcast overview.",
        "content_types": ["podcast", "review", "quiz"],
        "target_round": 1,
        "category": "General",
        "podcast_transcript": [
            {"speaker": "Dr. Priya Sharma", "text": "Welcome to the ESG Fundamentals podcast. Today we're breaking down what every executive needs to know about Environmental, Social, and Governance factors."},
            {"speaker": "Prof. James Walker", "text": "Great to be here, Priya. Let's start with the basics. ESG isn't just a compliance checkbox — it's become a core driver of corporate value creation."},
            {"speaker": "Dr. Priya Sharma", "text": "Exactly. The E stands for Environmental — think carbon emissions, water usage, waste management, and biodiversity impact. Companies like Muressons with mining and manufacturing operations face significant environmental scrutiny."},
            {"speaker": "Prof. James Walker", "text": "The S covers Social factors — labour practices, community relations, diversity, supply chain ethics. For a conglomerate operating across regions like Gobi and Deccan, this is critical."},
            {"speaker": "Dr. Priya Sharma", "text": "And G — Governance — covers board composition, executive pay, transparency, and anti-corruption measures. Strong governance is the foundation that makes E and S credible."},
            {"speaker": "Prof. James Walker", "text": "Now, let's talk about Double Materiality. Under the EU's CSRD directive, companies must report on two dimensions: how sustainability issues affect the company financially, AND how the company impacts society and the environment."},
            {"speaker": "Dr. Priya Sharma", "text": "This is a paradigm shift. Traditional financial materiality only asked 'does this risk affect our bottom line?' Double materiality also asks 'does our business affect the planet and people?'"},
            {"speaker": "Prof. James Walker", "text": "For Muressons, this means mapping every business unit — Pharma, Electronics, Consumer Goods, Software — against both dimensions. The ESG audit in Round 1 is your first step."},
            {"speaker": "Dr. Priya Sharma", "text": "Key takeaway: ESG integration isn't optional anymore. Investors, regulators, and consumers are all demanding it. The companies that lead on ESG will have a competitive advantage in the 2030s."},
            {"speaker": "Prof. James Walker", "text": "Absolutely. And remember — the depth of your initial audit determines what risks you catch early versus what surprises you later. Choose wisely."},
        ],
        "review_content": NLM_001_REVIEW,
        "quiz_questions": NLM_001_QUESTIONS,
    },
    {
        "id": "NLM_002",
        "title": "Carbon Markets & Climate Risk",
        "share_url": "",
        "description": "Deep dive into carbon pricing mechanisms, EU ETS, emission scopes, and corporate climate strategy.",
        "content_types": ["quiz", "review"],
        "target_round": 3,
        "category": "Ecological",
        "podcast_transcript": [],
        "review_content": NLM_002_REVIEW,
        "quiz_questions": NLM_002_QUESTIONS,
    },
    {
        "id": "NLM_003",
        "title": "Supply Chain Ethics & Labour Rights",
        "share_url": "",
        "description": "Explore the Gobi region conflict, modern slavery legislation, and due diligence frameworks through AI-guided review.",
        "content_types": ["podcast", "review", "quiz"],
        "target_round": 5,
        "category": "Social",
        "podcast_transcript": [
            {"speaker": "Dr. Priya Sharma", "text": "Today we're tackling one of the most challenging aspects of ESG — supply chain ethics and labour rights. This is deeply relevant to Muressons' operations in the Gobi region."},
            {"speaker": "Prof. James Walker", "text": "Absolutely. The Gobi region represents a classic ethical dilemma in global supply chains. Rich mineral resources, but significant human rights concerns."},
            {"speaker": "Dr. Priya Sharma", "text": "Let's frame the issue. Modern slavery affects an estimated 50 million people globally. Forced labour generates $150 billion in illegal profits annually. And it's not just in developing countries — it exists in every sector."},
            {"speaker": "Prof. James Walker", "text": "For mining operations like those in the Gobi region, the risks include: forced labour in artisanal mining, child labour, dangerous working conditions, and community displacement."},
            {"speaker": "Dr. Priya Sharma", "text": "Several key pieces of legislation now require companies to act. The UK Modern Slavery Act, the French Duty of Vigilance Law, and the proposed EU Corporate Sustainability Due Diligence Directive."},
            {"speaker": "Prof. James Walker", "text": "The EU CSDDD is particularly important. It requires companies to identify, prevent, and mitigate adverse human rights and environmental impacts throughout their value chains."},
            {"speaker": "Dr. Priya Sharma", "text": "So what should Muressons do? First, conduct thorough supply chain mapping. Know every tier of your suppliers. Second, implement robust due diligence processes. Third, establish grievance mechanisms for workers."},
            {"speaker": "Prof. James Walker", "text": "And critically, don't just cut and run from problematic suppliers. Responsible disengagement means working with suppliers to improve, not abandoning workers to worse conditions."},
            {"speaker": "Dr. Priya Sharma", "text": "The business case is clear too. Companies with strong supply chain ethics see fewer disruptions, better brand reputation, and increasingly, better access to capital."},
            {"speaker": "Prof. James Walker", "text": "Bottom line: in the Muressons simulation, your choices about the Gobi region and Tier-3 mine workers aren't just ethical decisions — they're strategic ones that affect your reputation score, regulatory risk, and long-term viability."},
        ],
        "review_content": NLM_003_REVIEW,
        "quiz_questions": NLM_003_QUESTIONS,
    },
]


@admin_router.get("/resources/notebooklm", summary="Get all linked NotebookLM notebooks")
async def get_notebooklm_notebooks():
    return {"notebooks": _notebooklm_notebooks}


@admin_router.post("/resources/notebooklm", summary="Add or update a NotebookLM notebook link")
async def upsert_notebooklm_notebook(item: NotebookLMItem):
    global _notebooklm_notebooks
    _notebooklm_notebooks = [n for n in _notebooklm_notebooks if n["id"] != item.id]
    _notebooklm_notebooks.append(item.dict())
    return item


@admin_router.delete("/resources/notebooklm/{notebook_id}", summary="Remove a NotebookLM notebook link")
async def delete_notebooklm_notebook(notebook_id: str):
    global _notebooklm_notebooks
    _notebooklm_notebooks = [n for n in _notebooklm_notebooks if n["id"] != notebook_id]
    return {"status": "deleted", "notebook_id": notebook_id}


# ── Quiz Difficulty Setting ─────────────────────────────────────

_quiz_difficulty: str = "medium"  # "easy" | "medium" | "hard"


@admin_router.get("/quiz-difficulty", summary="Get current quiz difficulty level")
async def get_quiz_difficulty():
    return {"difficulty": _quiz_difficulty}


@admin_router.put("/quiz-difficulty", summary="Set quiz difficulty level")
async def set_quiz_difficulty(body: dict = Body(...)):
    global _quiz_difficulty
    level = body.get("difficulty", "medium").lower()
    if level not in ("easy", "medium", "hard"):
        raise HTTPException(400, "Difficulty must be 'easy', 'medium', or 'hard'")
    _quiz_difficulty = level
    return {"status": "updated", "difficulty": _quiz_difficulty}


# ── Per-Cohort Quiz Enabled State ────────────────────────────────

_quiz_enabled: dict[str, bool] = {}  # session_id → enabled (default True)


@admin_router.get("/quiz-enabled/{session_id}", summary="Check if quiz is enabled for a cohort")
async def get_quiz_enabled(session_id: str):
    enabled = _quiz_enabled.get(session_id, True)  # Default: enabled
    return {"session_id": session_id, "quiz_enabled": enabled}


@admin_router.put("/quiz-enabled/{session_id}", summary="Enable or disable quiz for a cohort")
async def set_quiz_enabled(session_id: str, body: dict = Body(...)):
    enabled = body.get("quiz_enabled", True)
    _quiz_enabled[session_id] = bool(enabled)
    return {"status": "updated", "session_id": session_id, "quiz_enabled": _quiz_enabled[session_id]}


# ── Per-Cohort Consultant Allowed State ──────────────────────────

_consultant_allowed: dict[str, bool] = {}  # session_id → allowed (default True)


@admin_router.get("/consultant-allowed/{session_id}", summary="Check if ESG consultant is allowed for a cohort")
async def get_consultant_allowed(session_id: str):
    allowed = _consultant_allowed.get(session_id, True)  # Default: allowed
    return {"session_id": session_id, "consultant_allowed": allowed}


@admin_router.put("/consultant-allowed/{session_id}", summary="Enable or disable ESG consultant for a cohort")
async def set_consultant_allowed(session_id: str, body: dict = Body(...)):
    allowed = body.get("consultant_allowed", True)
    _consultant_allowed[session_id] = bool(allowed)
    return {"status": "updated", "session_id": session_id, "consultant_allowed": _consultant_allowed[session_id]}


# ═════════════════════════════════════════════════════════════════
#  MASTER INTERVENTIONS DATABASE (God Mode)
# ═════════════════════════════════════════════════════════════════


_master_overrides: list[dict] = [
    {
        "id": "carbon_tax",
        "icon": "🌍",
        "title": "Global Macro Shift",
        "description": "Toggle Year 3 Carbon Tax from $250/ton → $400/ton mid-game.",
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

    for sid, sess in all_sessions.items():
        if sess.get("player_id"):
            total_players += 1
        else:
            total_cohorts += 1
        gs = sess.get("global_state")
        if gs:
            r = gs.get("current_round", 1)
            round_distribution[f"R{r}"] = round_distribution.get(f"R{r}", 0) + 1
            total_treasury += gs.get("treasury_balance", 0)
            total_reputation += gs.get("reputation_score", 0)
            session_count_with_state += 1

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

@admin_router.post("/god/universal-broadcast", summary="Broadcast to ALL connected clients")
async def universal_broadcast(body: dict = Body(...)):
    title = body.get("title", "System Announcement")
    message = body.get("message", "")
    priority = body.get("priority", "info")  # info, warning, critical
    payload = {
        "type": "universal_broadcast",
        "title": title,
        "message": message,
        "priority": priority,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(payload)
    _audit("universal_broadcast", details={"title": title, "priority": priority})
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


# ═════════════════════════════════════════════════════════════════
#  GOD MODE — Platform Analytics (#15)
# ═════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════
#  ANALYTICS VISIBILITY — God Mode controls what facilitators/players see
# ═════════════════════════════════════════════════════════════════

_analytics_visibility: dict = {
    "facilitator": {
        "decision_heatmap": True,
        "time_to_decision": True,
        "cohort_comparison": True,
        "convergence_analysis": True,
        "learning_outcomes": True,
        "risk_exposure": True,
        "materiality_matrix": True,
        "technical_reference": True,
    },
    "player": {
        "peer_benchmarking": True,
        "decision_impact": True,
        "what_if_simulator": False,
    }
}


@admin_router.get("/god/analytics-visibility", summary="Get analytics visibility settings")
async def get_analytics_visibility():
    return _analytics_visibility


@admin_router.put("/god/analytics-visibility", summary="Update analytics visibility settings")
async def set_analytics_visibility(body: dict = Body(...)):
    for role in ("facilitator", "player"):
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    _analytics_visibility[role][key] = bool(val)
    return _analytics_visibility


# ── Per-Cohort Analytics Visibility ─────────────────────────────
# Stored on session dict as session["analytics_visibility"] = {facilitator: {...}, player: {...}}
# Global defaults apply when a cohort has no overrides.

def resolve_analytics_visibility(session_id: str) -> dict:
    """Merge global defaults with per-cohort overrides. Cohort overrides win."""
    import copy as _copy
    merged = _copy.deepcopy(_analytics_visibility)
    sess = database_memory._sessions.get(session_id)
    if not sess:
        return merged
    # Walk up to parent cohort if this is a player sub-session
    if sess.get("parent_cohort_id"):
        parent = database_memory._sessions.get(sess["parent_cohort_id"])
        if parent:
            sess = parent
    cohort_vis = sess.get("analytics_visibility")
    if cohort_vis:
        for role in ("facilitator", "player"):
            if role in cohort_vis:
                for key, val in cohort_vis[role].items():
                    if key in merged.get(role, {}):
                        merged[role][key] = bool(val)
    return merged


@admin_router.get("/cohort/{session_id}/analytics-visibility", summary="Get per-cohort analytics visibility")
async def get_cohort_analytics_visibility(session_id: str):
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    cohort_overrides = sess.get("analytics_visibility")
    return {
        "global_defaults": _analytics_visibility,
        "cohort_overrides": cohort_overrides,
        "effective": resolve_analytics_visibility(session_id),
    }


@admin_router.put("/cohort/{session_id}/analytics-visibility", summary="Set per-cohort analytics visibility overrides")
async def set_cohort_analytics_visibility(session_id: str, body: dict = Body(...)):
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    overrides = sess.setdefault("analytics_visibility", {"facilitator": {}, "player": {}})
    for role in ("facilitator", "player"):
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    overrides.setdefault(role, {})[key] = bool(val)
    sess["analytics_visibility"] = overrides
    database_memory._persist()
    return {
        "cohort_overrides": overrides,
        "effective": resolve_analytics_visibility(session_id),
    }


# ═════════════════════════════════════════════════════════════════
#  PLATFORM-WIDE ANALYTICS (God Mode + Facilitator)
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/god/analytics", summary="Platform-wide analytics")
async def get_platform_analytics():
    """
    Compute all analytics from _global_states, _bu_states, _decision_log.
    Returns decision heatmap, time-to-decision, cohort trajectories,
    convergence, learning outcomes, and risk exposure.
    """
    import math
    from collections import defaultdict

    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states = getattr(db, '_bu_states', {})
    decision_log = getattr(db, '_decision_log', [])

    # ── Summary counts ────────────────────────────────────────
    cohort_sessions = {sid: s for sid, s in all_sessions.items() if not s.get("parent_cohort_id")}
    player_sessions = {sid: s for sid, s in all_sessions.items() if s.get("parent_cohort_id")}

    # ── 1. Decision Heatmap: choice distribution per round ────
    decision_heatmap = defaultdict(lambda: defaultdict(int))
    for d in decision_log:
        rn = d.get("round_number", 0)
        choice = d.get("choice_selected", "")
        if choice:
            decision_heatmap[f"R{rn}"][choice] += 1

    # ── 2. Time-to-Decision: per round timing stats ───────────
    time_by_round = defaultdict(list)
    for d in decision_log:
        rn = d.get("round_number", 0)
        ttd = d.get("time_to_decision_seconds", 0)
        if ttd > 0:
            time_by_round[f"R{rn}"].append(ttd)

    time_to_decision = {}
    for rkey, times in sorted(time_by_round.items()):
        st = sorted(times)
        n = len(st)
        median = st[n // 2] if n % 2 == 1 else round((st[n // 2 - 1] + st[n // 2]) / 2, 1)
        time_to_decision[rkey] = {
            "avg_seconds": round(sum(st) / n, 1),
            "median_seconds": median,
            "min": st[0],
            "max": st[-1],
            "count": n,
        }

    # ── 3. Cohort Trajectories: KPI over rounds per cohort ────
    cohort_trajectories = {}
    for sid, sess in cohort_sessions.items():
        cname = sess.get("cohort_name", sid[:12])
        rounds = global_states.get(sid, [])
        trajectory = []
        for grs in rounds:
            rn = grs.get("round_number", 1)
            bus = bu_states.get(sid, {}).get(rn, [])
            avg_sl = sum(b.get("social_license_score", 50) for b in bus) / max(len(bus), 1)
            trajectory.append({
                "round": rn,
                "treasury": round(float(grs.get("corporate_treasury", 0)) / 1_000_000, 2),
                "reputation": round(float(grs.get("group_reputation", 50)), 1),
                "synergy": round(float(grs.get("synergy_multiplier", 1.0)), 3),
                "ebitda": round(float(grs.get("historical_ebitda", 0)) / 1_000_000, 2),
            })
        cohort_trajectories[cname] = trajectory

    # ── 4. Convergence Analysis ───────────────────────────────
    # Measure strategy similarity: CapEx StdDev and choice entropy per round
    capex_by_round = defaultdict(list)
    choices_by_round = defaultdict(list)
    for d in decision_log:
        rn = d.get("round_number", 0)
        capex_by_round[f"R{rn}"].append(d.get("capex_allocated", 0))
        ch = d.get("choice_selected", "")
        if ch:
            choices_by_round[f"R{rn}"].append(ch)

    capex_std_by_round = {}
    for rkey, vals in sorted(capex_by_round.items()):
        if len(vals) > 1:
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            capex_std_by_round[rkey] = round(math.sqrt(variance), 0)
        else:
            capex_std_by_round[rkey] = 0

    choice_entropy_by_round = {}
    for rkey, choices in sorted(choices_by_round.items()):
        n = len(choices)
        if n == 0:
            choice_entropy_by_round[rkey] = 0
            continue
        freq = defaultdict(int)
        for c in choices:
            freq[c] += 1
        entropy = 0
        for count in freq.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)
        choice_entropy_by_round[rkey] = round(entropy, 3)

    # Convergence index: 0 = everyone same, 1 = maximum diversity
    all_entropies = list(choice_entropy_by_round.values())
    max_entropy = math.log2(3) if all_entropies else 1  # 3 choices max
    convergence_index = round(
        1 - (sum(all_entropies) / max(len(all_entropies), 1) / max_entropy), 3
    ) if all_entropies else 0.5

    # ── 5. Learning Outcomes ──────────────────────────────────
    total_bonuses = 0
    bonuses_breakdown = defaultdict(int)
    for sid, rounds in global_states.items():
        if not rounds:
            continue
        latest = rounds[-1]
        lb = latest.get("learning_bonuses_awarded", {})
        if isinstance(lb, dict):
            for category, val in lb.items():
                if isinstance(val, (int, float)):
                    total_bonuses += val
                    bonuses_breakdown[category] += 1

    # Student bonus awards
    badges_awarded = defaultdict(int)
    total_student_bonuses = 0
    for sid_bonuses in _student_bonuses.values():
        for b in sid_bonuses:
            total_student_bonuses += 1
            bk = b.get("badge_key", "")
            if bk:
                badges_awarded[bk] += 1

    # ── 6. Risk Exposure: per cohort risk trends ──────────────
    risk_exposure = {}
    for sid, sess in cohort_sessions.items():
        cname = sess.get("cohort_name", sid[:12])
        rounds_data = global_states.get(sid, [])
        risk_trend = []
        for grs in rounds_data:
            rn = grs.get("round_number", 1)
            bus = bu_states.get(sid, {}).get(rn, [])
            if not bus:
                continue
            n = len(bus)
            avg_carbon = round(sum(b.get("carbon_intensity", 0) for b in bus) / n, 2)
            avg_ncd = round(sum(b.get("natural_capital_debt", 0) for b in bus) / n, 2)
            avg_sl = round(sum(b.get("social_license_score", 50) for b in bus) / n, 2)
            avg_gov = round(sum(b.get("governance_risk_score", 0) for b in bus) / n, 2)
            risk_trend.append({
                "round": rn,
                "avg_carbon_intensity": avg_carbon,
                "avg_natural_capital_debt": avg_ncd,
                "avg_social_license": avg_sl,
                "avg_governance_risk": avg_gov,
            })
        risk_exposure[cname] = risk_trend

    return {
        "total_cohorts": len(cohort_sessions),
        "total_players": len(player_sessions),
        "total_facilitators": len(_facilitator_registry),
        "total_decisions": len(decision_log),
        "decision_heatmap": {k: dict(v) for k, v in sorted(decision_heatmap.items())},
        "time_to_decision": dict(sorted(time_to_decision.items())),
        "cohort_trajectories": cohort_trajectories,
        "convergence": {
            "capex_std_by_round": capex_std_by_round,
            "choice_entropy_by_round": choice_entropy_by_round,
            "convergence_index": convergence_index,
        },
        "learning_outcomes": {
            "learning_bonuses_total": total_bonuses,
            "bonuses_by_category": dict(bonuses_breakdown),
            "badges_awarded": dict(badges_awarded),
            "student_bonus_count": total_student_bonuses,
        },
        "risk_exposure": risk_exposure,
        "visibility": _analytics_visibility,
    }


# ═════════════════════════════════════════════════════════════════
#  PLAYER-SCOPED ANALYTICS
# ═════════════════════════════════════════════════════════════════

@admin_router.get("/analytics/player/{session_id}", summary="Player-scoped analytics")
async def get_player_analytics(session_id: str):
    """
    Compute peer benchmarking, decision impact attribution, and
    what-if counterfactual analysis for a specific player session.
    """
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states = getattr(db, '_bu_states', {})
    decision_log = getattr(db, '_decision_log', [])

    sess = all_sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    player_rounds = global_states.get(session_id, [])
    if not player_rounds:
        raise HTTPException(404, "No round data for this session")

    latest = player_rounds[-1]
    player_treasury = float(latest.get("corporate_treasury", 0))
    player_reputation = float(latest.get("group_reputation", 50))
    player_synergy = float(latest.get("synergy_multiplier", 1.0))

    # ── 1. Peer Benchmarking ──────────────────────────────────
    # Compute percentiles across all sessions at the same round
    player_round = latest.get("round_number", 1)
    all_treasuries = []
    all_reputations = []
    all_synergies = []

    for sid, rounds in global_states.items():
        if not rounds:
            continue
        # Find the state at the same round number
        for grs in rounds:
            if grs.get("round_number") == player_round:
                all_treasuries.append(float(grs.get("corporate_treasury", 0)))
                all_reputations.append(float(grs.get("group_reputation", 50)))
                all_synergies.append(float(grs.get("synergy_multiplier", 1.0)))
                break

    def percentile(value, population):
        if not population:
            return 50
        below = sum(1 for v in population if v < value)
        return round(below / len(population) * 100, 1)

    cohort_avg_treasury = round(sum(all_treasuries) / max(len(all_treasuries), 1), 2)
    cohort_avg_reputation = round(sum(all_reputations) / max(len(all_reputations), 1), 1)

    peer_benchmarking = {
        "treasury_percentile": percentile(player_treasury, all_treasuries),
        "reputation_percentile": percentile(player_reputation, all_reputations),
        "synergy_percentile": percentile(player_synergy, all_synergies),
        "player_count": len(all_treasuries),
        "cohort_avg": {
            "treasury": cohort_avg_treasury,
            "reputation": cohort_avg_reputation,
        },
        "player": {
            "treasury": round(player_treasury, 2),
            "reputation": round(player_reputation, 1),
            "synergy": round(player_synergy, 3),
        },
    }

    # ── 2. Decision Impact Attribution ────────────────────────
    # For each round, show the KPI deltas caused by the player's choice
    decision_impact = []
    player_decisions = [
        d for d in decision_log if d.get("session_id") == session_id
    ]
    # Group by round
    from collections import defaultdict
    dec_by_round = defaultdict(list)
    for d in player_decisions:
        dec_by_round[d.get("round_number", 0)].append(d)

    for i in range(1, len(player_rounds)):
        prev = player_rounds[i - 1]
        curr = player_rounds[i]
        rn = prev.get("round_number", i)
        treasury_delta = float(curr.get("corporate_treasury", 0)) - float(prev.get("corporate_treasury", 0))
        reputation_delta = float(curr.get("group_reputation", 50)) - float(prev.get("group_reputation", 50))
        synergy_delta = float(curr.get("synergy_multiplier", 1.0)) - float(prev.get("synergy_multiplier", 1.0))

        round_decs = dec_by_round.get(rn, []) or dec_by_round.get(curr.get("round_number", 0), [])
        choice = round_decs[0].get("choice_selected", "—") if round_decs else "—"
        total_capex = sum(d.get("capex_allocated", 0) for d in round_decs)

        # Generate narrative
        parts = []
        if treasury_delta > 0:
            parts.append(f"Treasury grew by ${abs(treasury_delta/1_000_000):.1f}M")
        elif treasury_delta < 0:
            parts.append(f"Treasury fell by ${abs(treasury_delta/1_000_000):.1f}M")
        if reputation_delta > 0:
            parts.append(f"reputation rose {reputation_delta:.1f} pts")
        elif reputation_delta < 0:
            parts.append(f"reputation dropped {abs(reputation_delta):.1f} pts")

        decision_impact.append({
            "round": rn,
            "choice": choice,
            "total_capex": round(total_capex, 0),
            "treasury_delta": round(treasury_delta, 2),
            "reputation_delta": round(reputation_delta, 2),
            "synergy_delta": round(synergy_delta, 4),
            "narrative": " — ".join(parts) if parts else "Minimal change this round",
        })

    # ── 3. What-If Simulator ──────────────────────────────────
    # Simple counterfactual: show what the average player chose at each
    # round and compare KPI trajectory
    what_if = []
    # Gather avg choice per round across all sessions
    from collections import Counter
    choices_per_round = defaultdict(list)
    for d in decision_log:
        ch = d.get("choice_selected", "")
        if ch:
            choices_per_round[d.get("round_number", 0)].append(ch)

    for impact in decision_impact:
        rn = impact["round"]
        player_choice = impact["choice"]
        round_choices = choices_per_round.get(rn, [])
        if not round_choices:
            continue
        counter = Counter(round_choices)
        most_popular = counter.most_common(1)[0][0] if counter else player_choice

        if most_popular != player_choice:
            # Find avg KPI delta for sessions that chose the popular option
            pop_deltas_t = []
            pop_deltas_r = []
            for sid, rounds in global_states.items():
                if sid == session_id:
                    continue
                sid_decs = [d for d in decision_log if d.get("session_id") == sid and d.get("round_number") == rn]
                sid_choice = sid_decs[0].get("choice_selected", "") if sid_decs else ""
                if sid_choice == most_popular and len(rounds) > rn:
                    for idx in range(len(rounds) - 1):
                        if rounds[idx].get("round_number") == rn:
                            dt = float(rounds[idx + 1].get("corporate_treasury", 0)) - float(rounds[idx].get("corporate_treasury", 0))
                            dr = float(rounds[idx + 1].get("group_reputation", 50)) - float(rounds[idx].get("group_reputation", 50))
                            pop_deltas_t.append(dt)
                            pop_deltas_r.append(dr)
                            break

            if pop_deltas_t:
                avg_t = sum(pop_deltas_t) / len(pop_deltas_t)
                avg_r = sum(pop_deltas_r) / len(pop_deltas_r)
                what_if.append({
                    "round": rn,
                    "actual_choice": player_choice,
                    "alternative": most_popular,
                    "alternative_popularity": f"{counter[most_popular]}/{len(round_choices)}",
                    "projected_treasury_diff": round(avg_t - impact["treasury_delta"], 2),
                    "projected_reputation_diff": round(avg_r - impact["reputation_delta"], 2),
                })

    return {
        "peer_benchmarking": peer_benchmarking,
        "decision_impact": decision_impact,
        "what_if": what_if,
        "visibility": _analytics_visibility.get("player", {}),
    }


# ══════════════════════════════════════════════════════════════
# ── Glossary CRUD ─────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

_glossary_terms: list = [
    {"id": "ebitda", "term": "EBITDA", "definition": "Earnings Before Interest, Taxes, Depreciation, and Amortization — measures operational profitability.", "tags": ["finance", "profitability", "earnings"], "weblink": ""},
    {"id": "csf_pool", "term": "CSF Pool", "definition": "Capital Sustainability Fund — 20% of corporate treasury available for ESG investment allocation.", "tags": ["finance", "investment", "treasury", "esg"], "weblink": ""},
    {"id": "vrio", "term": "VRIO Radar", "definition": "Strategic resource analysis: Value, Rarity, Imitability, Organization — measures competitive advantage.", "tags": ["strategy", "competitive advantage", "resources"], "weblink": ""},
    {"id": "ncd", "term": "Natural Capital Debt", "definition": "Accumulated environmental liability from unsustainable resource extraction or pollution.", "tags": ["environment", "liability", "sustainability", "esg"], "weblink": ""},
    {"id": "social_license", "term": "Social License Score", "definition": "Community and stakeholder approval level for business operations (0-100 scale).", "tags": ["social", "stakeholder", "reputation", "esg"], "weblink": ""},
    {"id": "synergy", "term": "Synergy Multiplier", "definition": "Cross-BU collaboration bonus applied to combined strategic outcomes.", "tags": ["strategy", "collaboration", "business unit"], "weblink": ""},
    {"id": "cost_of_capital", "term": "Cost of Capital", "definition": "Rate of return required by investors — affects treasury deductions each round.", "tags": ["finance", "treasury", "investors"], "weblink": ""},
    {"id": "governance_risk", "term": "Governance Risk", "definition": "Risk from poor corporate governance — regulatory fines, board conflicts, compliance failures.", "tags": ["governance", "risk", "compliance", "esg"], "weblink": ""},
    {"id": "carbon_intensity", "term": "Carbon Intensity", "definition": "CO₂ emissions per unit of revenue — lower is better for ESG compliance.", "tags": ["environment", "emissions", "carbon", "esg"], "weblink": ""},
    {"id": "water_dependency", "term": "Water Dependency", "definition": "Business unit reliance on water resources — higher means greater exposure to water stress crises.", "tags": ["environment", "resources", "risk"], "weblink": ""},
    {"id": "double_materiality", "term": "Double Materiality", "definition": "EU CSRD requirement: assess both impact OF the company on environment AND impact of environment ON the company.", "tags": ["governance", "csrd", "regulation", "esg"], "weblink": ""},
    {"id": "scope3", "term": "Scope 3 Emissions", "definition": "Indirect emissions from supply chain, transportation, and product lifecycle — hardest to measure and control.", "tags": ["environment", "emissions", "supply chain", "carbon"], "weblink": ""},
    {"id": "stakeholder_map", "term": "Stakeholder Map", "definition": "Mendelow's Matrix classifying stakeholders by Power (influence) and Interest (engagement level).", "tags": ["strategy", "stakeholder", "governance"], "weblink": ""},
    {"id": "treasury", "term": "Treasury", "definition": "Corporate cash reserves — main financial health indicator. Depleted by investments, crises, and operating costs.", "tags": ["finance", "cash", "investment"], "weblink": ""},
    {"id": "reputation", "term": "Reputation Score", "definition": "Public perception of the company (0-100) — influences customer loyalty, talent retention, and regulatory leniency.", "tags": ["social", "reputation", "brand"], "weblink": ""},
    {"id": "brand_equity", "term": "Brand Equity", "definition": "Intangible asset value from brand recognition and loyalty — built through reputation and stakeholder trust.", "tags": ["social", "reputation", "brand", "strategy"], "weblink": ""},
    {"id": "strategic_pillars", "term": "Strategic Pillars", "definition": "Decision paradigm where players choose specific actions across multiple ESG categories (Energy, Operations, Supply Chain, Offsetting).", "tags": ["strategy", "decisions", "esg"], "weblink": ""},
    {"id": "cfo_override", "term": "CFO Override", "definition": "Emergency mechanism to bypass materiality gate — incurs a reputation penalty.", "tags": ["governance", "finance", "risk"], "weblink": ""},
    {"id": "round_pacing", "term": "Round Pacing", "definition": "Facilitator-controlled timing mode: Self-paced (players advance freely), Timed (automatic countdown), or Manual (facilitator unlocks).", "tags": ["system", "facilitator", "timing"], "weblink": ""},
    {"id": "bu", "term": "Business Unit (BU)", "definition": "One of four Muressons divisions: Pharma, Electronics, Consumer Goods, Software — each with unique risk profiles.", "tags": ["strategy", "organization", "business unit"], "weblink": ""},
    {"id": "esg", "term": "ESG", "definition": "Environmental, Social, and Governance — three pillars for measuring corporate sustainability and ethical impact.", "tags": ["esg", "sustainability", "environment", "social", "governance"], "weblink": ""},
]


class GlossaryItem(BaseModel):
    id: str = ""
    term: str
    definition: str
    tags: list = []
    weblink: str = ""


@admin_router.get("/glossary", summary="Get all glossary terms")
async def get_glossary():
    return {"terms": _glossary_terms}


@admin_router.post("/glossary", summary="Add or update a glossary term")
async def upsert_glossary_term(item: GlossaryItem):
    global _glossary_terms
    # Auto-generate ID if empty
    term_id = item.id or item.term.lower().replace(" ", "_").replace("(", "").replace(")", "")
    entry = item.dict()
    entry["id"] = term_id
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    _glossary_terms.append(entry)
    return entry


@admin_router.delete("/glossary/{term_id}", summary="Delete a glossary term")
async def delete_glossary_term(term_id: str):
    global _glossary_terms
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    return {"status": "deleted", "term_id": term_id}


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
        "name": "Classroom (Easy)",
        "description": "Gentle settings for introductory classes. Low volatility, forgiving penalties.",
        "icon": "🎓",
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
        "name": "Workshop (Standard)",
        "description": "Balanced settings for corporate workshops. Moderate complexity.",
        "icon": "🏢",
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
        "name": "Executive (Hard)",
        "description": "Aggressive parameters for experienced executives. High stakes, punishing penalties.",
        "icon": "💼",
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
        "description": "Maximum volatility. Every engine cranked to extreme. Only for stress-testing.",
        "icon": "🔥",
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
        if sess.get("player_id"):
            continue  # Skip player sub-sessions

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


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR TELEPROMPTER — Round-by-round teaching script
# ═════════════════════════════════════════════════════════════════

_TELEPROMPTER_SCRIPTS = {
    1: {
        "title": "Round 1: Setting the Stage",
        "talking_points": [
            "Welcome teams to their first strategic decision cycle",
            "Explain the Fog of War: metrics are noisy in early rounds — teams must decide with imperfect information",
            "Emphasize: there are NO risk-free choices — every option has trade-offs",
            "Highlight: the inflation engine means doing nothing still costs money",
        ],
        "engines_likely": ["fog_of_war_active", "inflation_index_applied"],
        "discussion_prompts": [
            "How did you prioritize between BUs without full information?",
            "What assumptions did you make about the reliability of the data?",
        ],
    },
    2: {
        "title": "Round 2: First Consequences",
        "talking_points": [
            "Deferred synergy investments from Round 1 are now landing",
            "Technical debt counters may begin ticking for neglected BUs",
            "Cash conversion drag should be visible for high-governance-risk BUs",
            "Ask teams to explain their capital allocation rationale",
        ],
        "engines_likely": ["cash_conversion_drag", "implementation_lag", "supply_chain_contagion"],
        "discussion_prompts": [
            "Which BUs did you neglect, and why?",
            "Did the implementation lag surprise you? How does this change your planning horizon?",
        ],
    },
    3: {
        "title": "Round 3: Fog Lifts",
        "talking_points": [
            "Fog of War clears after this round — true metrics become visible",
            "Competitive NPC is growing at 3%/round — are teams keeping pace?",
            "Revenue cannibalization may be visible if one BU dominates",
            "Technology lock-in streaks are building — are teams diversifying?",
        ],
        "engines_likely": ["fog_of_war_active", "competitor_warning", "revenue_cannibalized"],
        "discussion_prompts": [
            "Now that you can see true metrics, would you have changed your Round 1 decisions?",
            "How does the NPC competitor change your strategy?",
        ],
    },
    4: {
        "title": "Round 4: Strategic Inflection Point",
        "talking_points": [
            "Technology lock-in may trigger if teams haven't diversified (3-round streak)",
            "Greenwashing risk is real — green rhetoric without matching investment will be punished",
            "Regulatory ratchet means cost of capital may be permanently elevated",
            "This is the mid-game — long-term strategy should now be clear",
        ],
        "engines_likely": ["technology_lockin_penalty", "greenwashing_scandal", "regulatory_ratchet_active"],
        "discussion_prompts": [
            "Is your strategy sustainable for 6 more rounds?",
            "How do you balance short-term EBITDA vs long-term resilience?",
        ],
    },
    5: {
        "title": "Round 5: The Real Test Begins",
        "talking_points": [
            "Halfway mark — compounding effects are now unavoidable",
            "Stakeholder fatigue factor means crises are getting harder to recover from",
            "Dividend ratchet is live — cutting dividends has consequences",
            "Climate tipping point may activate in advanced_climate paradigm",
        ],
        "engines_likely": ["stakeholder_fatigue_applied", "dividend_ratchet_triggered", "tipping_point_reached"],
        "discussion_prompts": [
            "What would a Board of Directors think of your performance?",
            "How has your strategy evolved since Round 1?",
        ],
    },
    6: {
        "title": "Round 6: Compounding Pressures",
        "talking_points": [
            "Inflation is now 6 rounds deep — OPEX has grown significantly",
            "Supply chain contagion amplifies if governance risk hasn't been addressed",
            "Talent allocation pressure penalizes chronically underfunded BUs",
            "This is where poor early decisions create cascading failures",
        ],
        "engines_likely": ["supply_chain_contagion", "talent_neglect_surcharge", "technical_debt_penalty"],
        "discussion_prompts": [
            "Are you fighting fires or executing a strategy?",
            "Which complexity engine has hurt you the most, and could you have prevented it?",
        ],
    },
    7: {
        "title": "Round 7: Terminal Strategy",
        "talking_points": [
            "Three rounds left — terminal value calculations are becoming critical",
            "Teams should be thinking about their final position versus the competitor",
            "Encourage teams to calculate: will my EBITDA beat the NPC at Round 10?",
        ],
        "engines_likely": ["competitor_warning", "regulatory_ratchet_active"],
        "discussion_prompts": [
            "What metrics matter most for your final score?",
            "If you could undo one decision from the entire game, which would it be?",
        ],
    },
    8: {
        "title": "Round 8: Late-Game Optimization",
        "talking_points": [
            "Two rounds left — marginal decisions now have outsized impact",
            "Greenwashing risk is still active — don't make promises you can't fund",
            "Dividend policies should be locked in — the ratchet doesn't forgive",
        ],
        "engines_likely": ["greenwashing_scandal", "dividend_ratchet_triggered"],
        "discussion_prompts": [
            "How are you positioning for the debrief?",
            "What have you learned about the relationship between ESG and financial performance?",
        ],
    },
    9: {
        "title": "Round 9: The Finish Line Approaches",
        "talking_points": [
            "Final substantive round — next round is endgame",
            "Encourage teams to maximize terminal value while maintaining ESG scores",
            "All complexity engines are running — the full system is in play",
        ],
        "engines_likely": ["inflation_index_applied", "competitor_warning"],
        "discussion_prompts": [
            "What surprised you most about the simulation?",
            "How does this experience change how you think about real corporate strategy?",
        ],
    },
    10: {
        "title": "Round 10: Endgame",
        "talking_points": [
            "Final round — terminal values are computed",
            "Prepare teams for the debrief and final report",
            "Highlight: the simulation mirrors real-world complexity — no perfect answers exist",
            "Celebrate the journey, not just the outcome",
        ],
        "engines_likely": [],
        "discussion_prompts": [
            "What was your biggest strategic mistake, and when did you realize it?",
            "How would you advise the next cohort playing this simulation?",
            "What real-world parallel does this simulation remind you of?",
        ],
    },
}


@admin_router.get("/teleprompter/{round_number}", summary="Get facilitator teleprompter script")
async def get_teleprompter(round_number: int):
    script = _TELEPROMPTER_SCRIPTS.get(round_number, {
        "title": f"Round {round_number}",
        "talking_points": ["Continue guiding teams through their decisions."],
        "engines_likely": [],
        "discussion_prompts": ["What patterns are emerging in your strategy?"],
    })
    return {"round": round_number, "script": script}


@admin_router.get("/teleprompter", summary="Get all teleprompter scripts")
async def get_all_teleprompter():
    return {"scripts": _TELEPROMPTER_SCRIPTS}


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
        })

    comparisons.sort(key=lambda c: -c["treasury_m"])
    return {"cohorts": comparisons, "total": len(comparisons)}
