"""
admin_god_controls.py — God-Mode settings + emergency freeze endpoints (audit #17).

Behaviour-preserving extraction from admin_router.py following the established
ARCH-002 sub-router pattern (see admin_teleprompter / admin_resources /
admin_analytics). The four endpoints — GET/PUT /god/settings and POST
/god/freeze|/god/unfreeze — are moved here VERBATIM onto their own router, which
main.py mounts alongside the others. Paths and prefix are identical
(/api/admin/...), so every existing HTTP caller and test is unaffected.

Shared helpers stay in their homes and are imported: require_super_admin + _audit
from admin_router, _god_mode_settings + mark_godmode_dirty from admin_shared, and
the WebSocket `manager` singleton from admin_ws (via admin_router's re-export).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends

from admin_shared import _god_mode_settings, mark_godmode_dirty
from admin_ws import manager
# require_super_admin (dependency) and _audit (audit-log helper) remain in
# admin_router; import them here. main.py imports admin_router before this
# module, so there is no import cycle (admin_router does not import this module).
from admin_router import require_super_admin, _audit

god_router = APIRouter(prefix="/api/admin", tags=["Admin — God Mode"])


@god_router.get("/god/settings", summary="Get god mode global settings")
async def get_god_settings(_guard: None = Depends(require_super_admin)):
    # SECURITY-HIGH-001: Restricted to super_admin — contains hidden simulation
    # parameters (market_hostility_index, global_carbon_fee, black_swan toggles, etc.)
    # that must not be visible to facilitators. Facilitators read from
    # GET /scaffolding-status instead for the subset they need.
    return _god_mode_settings


@god_router.put("/god/settings", summary="Update god mode global settings")
async def update_god_settings(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    changed = {}
    for key in ("allow_facilitator_cohort_creation",):
        if key in body:
            old = _god_mode_settings.get(key)
            _god_mode_settings[key] = body[key]
            changed[key] = {"old": old, "new": body[key]}
    if changed:
        mark_godmode_dirty()  # Fix #5: publish settings change to workers + snapshot
    _audit("settings_updated", details=changed)
    return _god_mode_settings


# ── Emergency Freeze (#7) ───────────────────────────────────────

@god_router.post("/god/freeze", summary="Freeze all simulations")
async def freeze_system(body: dict = Body(...), _guard: None = Depends(require_super_admin)):
    msg = body.get("message", "System maintenance in progress.")
    _god_mode_settings["system_frozen"] = True
    _god_mode_settings["freeze_message"] = msg
    _god_mode_settings["freeze_started_at"] = datetime.now(timezone.utc).isoformat()
    mark_godmode_dirty()  # Fix #5: freeze must be shared across workers + survive restart
    _audit("system_frozen", details={"message": msg})
    # Broadcast to all connected WS clients
    await manager.broadcast({
        "type": "system_freeze",
        "frozen": True,
        "message": msg,
    })
    return {"status": "frozen", "message": msg}


@god_router.post("/god/unfreeze", summary="Unfreeze all simulations")
async def unfreeze_system(_guard: None = Depends(require_super_admin)):
    _god_mode_settings["system_frozen"] = False
    _god_mode_settings["freeze_message"] = ""
    _god_mode_settings["freeze_started_at"] = None
    mark_godmode_dirty()  # Fix #5: publish the unfreeze to other workers + snapshot
    _audit("system_unfrozen")
    await manager.broadcast({
        "type": "system_freeze",
        "frozen": False,
        "message": "",
    })
    return {"status": "unfrozen"}
