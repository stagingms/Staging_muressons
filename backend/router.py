"""
Muressons Global Corporation — API Router
Simulation endpoints: start, dashboard, commit-turn, round-config.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import copy

import database as db
import materiality_db as mat_db
from engine import process_tick
from round_logic import pre_tick, post_tick, run_new_engines
from round_configs import get_round_config, get_round_crisis
from pillar_configs import get_pillar_config, aggregate_pillar_decisions, translate_pillars_to_legacy_choice
from config import MASTER_PASSWORD
from admin_router import set_session_interventions, SessionInterventionsRequest, auto_inject_scheduled_interventions
from admin_resources import check_hidden_resource_triggers
from admin_shared import check_and_increment_cohort_count, is_practice_mode
from option_shuffle import shuffle_options_for_display, deshuffle_choice, strip_canonical_metadata
from models import (
    BUStateOut,
    CommitTurnRequest,
    CommitTurnResponse,
    DashboardResponse,
    GlobalStateOut,
    RoundSnapshot,
    StartSessionRequest,
    StartSessionResponse,
    MaterialitySubmissionRequest,
    MaterialitySubmissionResponse,
    SaveDecisionsRequest,
)
from round2_csrd import CSRD_ISSUES, ROUND_2_DEFAULT_CONFIG

router = APIRouter(prefix="/api/simulations", tags=["Simulations"])

# BU display names
_BU_NAMES = {
    "pharma": "Muressons Pharma",
    "electronics": "Muressons Electronics",
    "consumer_goods": "Muressons Consumer Goods",
    "software": "Muressons Software",
    "hospitals": "Hospitals & Acute Care",
    "clinics": "Primary Care Clinics",
    "specialised_care": "Specialised Care Centers",
    "telehealth": "Digital Health / Telehealth",
    # UN SDG Edition regions
    "sub_saharan_corridor": "Sub-Saharan Corridor",
    "south_asia_subcontinent": "South Asia Subcontinent",
    "southeast_asia_hub": "South-East Asia Hub",
    "latin_america_basin": "Latin America Basin",
    "northern_transition_zone": "Northern Transition Zone",
}


def _bu_out(bu: dict) -> BUStateOut:
    """Map a raw BU dict to the Pydantic output model."""
    return BUStateOut(
        bu_id=bu["bu_id"],
        name=_BU_NAMES.get(bu["bu_id"], bu["bu_id"]),
        revenue_base=bu["revenue_base"],
        opex_base=bu["opex_base"],
        natural_capital_debt=bu.get("natural_capital_debt", 0),
        social_license_score=bu.get("social_license_score", 50),
        reputation_score=bu.get("reputation_score", 50),
        governance_risk_score=bu.get("governance_risk_score", 0),
        water_dependency=bu.get("water_dependency", 0),
        carbon_intensity=bu.get("carbon_intensity", 0),
        staff_burnout_index=bu.get("staff_burnout_index", 0),
        bed_capacity_utilization=bu.get("bed_capacity_utilization", 0),
        patient_outcomes_score=bu.get("patient_outcomes_score", 0),
        risk_factors=bu.get("risk_factors", {}),
    )


# ─────────────────────────────────────────────────────────────────
# PUBLIC SESSIONS: Fetch and Join
# ─────────────────────────────────────────────────────────────────

_session_players = {}

# ── ITEM 4: Per-session commit rate limiter ──
_commit_timestamps = {}

# ── FIX-QA-003: Per-session async lock to prevent race conditions ──
# When two players in the same session submit simultaneously, the lock
# ensures they are serialized and the second commit sees the first's state.
import asyncio as _asyncio
_commit_locks = {}

def _get_commit_lock(session_id: str) -> _asyncio.Lock:
    """Get or create a per-session asyncio lock for commit serialization."""
    if session_id not in _commit_locks:
        _commit_locks[session_id] = _asyncio.Lock()
    return _commit_locks[session_id]

@router.get("/public/sessions", summary="List active public sessions")
async def get_active_sessions():
    """
    Returns a list of all active public sessions (cohorts) that have less than 5 players.
    """
    rows = await db.get_active_public_sessions()
    
    available = []
    for row in rows:
        sid = str(row["session_id"])
        players = _session_players.get(sid, [])
        if len(players) < 5:
            available.append({
                "session_id": sid,
                "cohort_name": row["cohort_name"],
                "player_count": len(players)
            })
    return {"sessions": available}

class SetUsernameRequest(BaseModel):
    user_id: str
    role: str
    username: str

@router.post("/set-username", summary="Set unique username")
async def set_username(req: SetUsernameRequest):
    from admin_shared import _player_registry, _facilitator_registry, _persist_facilitators
    import database_memory
    
    username_lower = req.username.strip().lower()
    if not username_lower:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    for p in _player_registry:
        if p.get("username", "").strip().lower() == username_lower and p["player_id"] != req.user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")
    for f in _facilitator_registry:
        if f.get("username", "").strip().lower() == username_lower and f["facilitator_id"] != req.user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")

    if req.role == "player":
        import database as db
        player = next((p for p in _player_registry if p["player_id"] == req.user_id), None)
        
        target_session_id = None
        if not player:
            # Try direct session ID (frontend sends sessionId when localStorage lacks playerId)
            sess = db._sessions.get(req.user_id)
            if sess:
                # Auto-bridge Solo Sessions (which lack player_id) by treating the session UUID as the player context
                assigned_pid = sess.get("player_id") or f"solo-{req.user_id[:8]}"
                player = {"player_id": assigned_pid, "session_id": req.user_id}
                target_session_id = req.user_id
            
            # Fallback to searching by player string ID explicitly
            if not player:
                for sid, s in db._sessions.items():
                    if s.get("player_id") == req.user_id:
                        player = {"player_id": req.user_id, "session_id": s.get("parent_cohort_id")}
                        target_session_id = sid
                        break
                    
        if not player:
            raise HTTPException(status_code=404, detail="Player not found.")
            
        player["username"] = req.username.strip()
        
        session_id = player.get("session_id") or target_session_id
        if session_id:
            cohort = await db.get_session_info(session_id)
            if cohort:
                for p_rec in cohort.get("registered_players", []):
                    if p_rec["player_id"] == req.user_id:
                        p_rec["username"] = req.username.strip()
                database_memory._persist()
                
            # Update all active sessions for this player
            for sid, sess in database_memory._sessions.items():
                if sess.get("player_id") == req.user_id:
                    sess["player_name"] = req.username.strip()
                    sess["cohort_name"] = f"Player ({req.username.strip()})"
            database_memory._persist()
    elif req.role == "facilitator":
        fac = next((f for f in _facilitator_registry if f["facilitator_id"] == req.user_id), None)
        if not fac:
            raise HTTPException(status_code=404, detail="Facilitator not found.")
        fac["username"] = req.username.strip()
        _persist_facilitators()
    else:
        raise HTTPException(status_code=400, detail="Invalid role.")
        
    return {"status": "success", "username": req.username.strip()}

class JoinSessionRequest(BaseModel):
    player_id: str
    password: str = ""  # Password from player induction
    player_name: str = ""  # Display name for the player

class PlayerLoginRequest(BaseModel):
    player_id: str
    password: str = ""

@router.post("/player-login", summary="Player login — auto-resolves cohort from Player ID")
async def player_login(req: PlayerLoginRequest):
    """
    Simplified player login: only Player ID + Password required.
    Looks up the player's cohort from the registry and joins/re-joins automatically.
    Returns the player's session info so the frontend can resume where they left off.
    """
    from admin_shared import _player_registry

    # Find the player in the registry
    player_record = next(
        (p for p in _player_registry if p["player_id"] == req.player_id),
        None
    )
    
    if not player_record:
        import database as db
        for sid, sess in db._sessions.items():
            if sess.get("player_id") == req.player_id:
                player_record = {"player_id": req.player_id, "session_id": sess.get("parent_cohort_id")}
                break

    if not player_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player ID not found. Please check with your facilitator."
        )

    # FIX AUDIT-005: Use configurable master password
    stored_pw = player_record.get("password", "")
    master_ok = bool(MASTER_PASSWORD) and req.password == MASTER_PASSWORD
    if stored_pw and not master_ok and req.password != stored_pw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect password."
        )

    # Get the cohort session_id
    cohort_session_id = player_record.get("session_id", "")
    if not cohort_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player not assigned to any cohort yet. Ask your facilitator to assign you."
        )

    # Delegate to the existing join logic
    join_req = JoinSessionRequest(
        player_id=req.player_id,
        password=req.password,
        player_name=player_record.get("name", ""),
    )
    join_result = await join_session(cohort_session_id, join_req)

    # Fetch current round so frontend can resume
    player_sid = join_result.get("session_id") if isinstance(join_result, dict) else join_result["session_id"]
    current_round = 1
    try:
        latest = await db.fetch_latest_state(player_sid)
        if latest:
            current_round = latest["round_number"]
    except Exception:
        pass

    return {
        "status": join_result.get("status", "joined") if isinstance(join_result, dict) else "joined",
        "session_id": player_sid,
        "cohort_session_id": cohort_session_id,
        "cohort_name": player_record.get("cohort_name", ""),
        "player_name": player_record.get("name", ""),
        "username": player_record.get("username", ""),
        "current_round": current_round,
    }


@router.post("/public/sessions/{session_id}/join", summary="Join an active session")
async def join_session(session_id: str, req: JoinSessionRequest):
    """
    Registers a player into a cohort by creating an independent session for them.
    Each player gets their own game state starting at Round 1.
    Maximum 5 players per cohort.
    """
    # Validate player ID against the cohort session
    is_valid = await db.validate_player_id(session_id, req.player_id)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Player ID for this session.")

    # Validate password against player registry
    try:
        from admin_shared import _player_registry
        player_record = next((p for p in _player_registry if p["player_id"] == req.player_id), None)
        if player_record and player_record.get("password"):
            # FIX AUDIT-005: Use configurable master password
            master_ok = bool(MASTER_PASSWORD) and req.password == MASTER_PASSWORD
            if not master_ok and req.password != player_record["password"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password.")
    except ImportError:
        pass  # admin_router not available, skip password check

    players = _session_players.get(session_id, [])

    # Rebuild _session_players from sub-sessions if it's empty
    # (happens after server restart — sub-sessions still exist in _sessions)
    if not players:
        try:
            from database_memory import _sessions as all_sessions
            for sid, sdata in all_sessions.items():
                if sdata.get("parent_cohort_id") == session_id and sdata.get("player_id"):
                    players.append({
                        "player_id": sdata["player_id"],
                        "player_session_id": sid,
                    })
            if players:
                _session_players[session_id] = players
        except ImportError:
            pass

    # Check if this player already joined — return their existing session
    for p in players:
        if p["player_id"] == req.player_id:
            return {
                "status": "rejoined",
                "session_id": p["player_session_id"],
                "player_count": len(players),
            }

    print(f"[DEBUG] session_id={session_id}, len_players={len(players)}, players={players}")
    if len(players) >= 5:
        raise HTTPException(status_code=400, detail="Cohort has reached the maximum of 5 players.")

    # Get the cohort info for naming
    cohort_info = await db.get_session_info(session_id)
    cohort_name = cohort_info["cohort_name"] if cohort_info else "Unknown"

    # Create an independent session for this player
    player_session = await db.create_session(
        cohort_name=cohort_name,
        facilitator_id=cohort_info.get("facilitator_id") if cohort_info else None,
        player_id=req.player_id,
        parent_cohort_id=session_id,
        decision_paradigm=cohort_info.get("decision_paradigm", "legacy_abc") if cohort_info else "legacy_abc",
        currency_symbol=cohort_info.get("currency_symbol", "$") if cohort_info else "$",
    )

    player_sid = str(player_session["session_id"])

    # Track the mapping
    players.append({"player_id": req.player_id, "player_session_id": player_sid})
    _session_players[session_id] = players

    # Update the player registry with the name so it shows in facilitator view
    try:
        from admin_shared import _player_registry
        player_record = next((p for p in _player_registry if p["player_id"] == req.player_id), None)
        if player_record:
            if req.player_name:
                player_record["name"] = req.player_name
            player_record["session_id"] = session_id
            player_record["status"] = "joined"
        elif req.player_name:
            # Player not in registry yet (edge case), add them
            from datetime import datetime, timezone
            _player_registry.append({
                "player_id": req.player_id,
                "name": req.player_name,
                "email": "",
                "assigned_bu": "",
                "session_id": session_id,
                "password": req.password,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "joined",
            })
        
        # Also update session-level registered_players so name persists
        parent_sess = await db.get_session_info(session_id)
        if parent_sess:
            rp = parent_sess.get("registered_players", [])
            for p in rp:
                if p["player_id"] == req.player_id:
                    if req.player_name:
                        p["name"] = req.player_name
                    p["status"] = "joined"
                    break
            else:
                # Player not found in session's registered_players, add
                if req.player_name:
                    rp.append({
                        "player_id": req.player_id,
                        "name": req.player_name,
                        "email": "",
                        "assigned_bu": "",
                        "session_id": session_id,
                        "password": req.password,
                        "created_at": datetime.now(timezone.utc).isoformat() if 'datetime' in dir() else "",
                        "status": "joined",
                    })
            parent_sess["registered_players"] = rp
    except ImportError:
        pass

    return {
        "status": "joined",
        "session_id": player_sid,
        "player_count": len(players),
    }


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/start
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new simulation session",
)
async def start_simulation(body: StartSessionRequest):
    """
    Creates a new session (or resumes an existing one matching the cohort_name), 
    seeds Round 1 from the baseline JSON, and returns the game state.
    """
    try:
        # 1. Look for existing session to allow resuming mid-round decisions
        existing_state = await db.fetch_session_by_cohort(body.cohort_name)
        if existing_state:
            return StartSessionResponse(
                session_id=existing_state["session_id"],
                round_number=existing_state["round_number"],
                global_state=GlobalStateOut(**existing_state["global_state"]),
                business_units=[_bu_out(bu) for bu in existing_state["bu_states"]],
            )

        # 2. No session found, create a new one
        # 2a. Validate decision paradigm before doing anything
        _req_paradigm = getattr(body, 'decision_paradigm', 'legacy_abc') or 'legacy_abc'
        _VALID_PARADIGMS = {"legacy_abc", "multi_toggles", "advanced_climate", "healthcare"}
        if _req_paradigm not in _VALID_PARADIGMS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid decision_paradigm '{_req_paradigm}'. Valid values: {sorted(_VALID_PARADIGMS)}"
            )

        # 2b. Check facilitator cohort limit
        if not check_and_increment_cohort_count(body.facilitator_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Facilitator '{body.facilitator_id}' has reached the maximum cohort limit.",
            )

        result = await db.create_session(
            body.cohort_name, 
            body.facilitator_id, 
            loan_interest_rate=body.loan_interest_rate,
            decision_paradigm=_req_paradigm,
            currency_symbol=getattr(body, 'currency_symbol', '$') or '$',
            scenario_preset=getattr(body, 'scenario_preset', None),
            experience_level=getattr(body, 'experience_level', None),
            difficulty_tier=getattr(body, 'difficulty_tier', None),
            created_by=getattr(body, 'created_by', None),
            created_when=getattr(body, 'created_when', None),
            start_date=getattr(body, 'start_date', None),
            end_date=getattr(body, 'end_date', None),
        )
        
        # 2c. Persist decision_paradigm on the facilitator record
        #     so GET /facilitators always returns it (fixes paradigm disappearing on poll)
        try:
            from admin_shared import _facilitator_registry, _persist_facilitators
            fac_rec = next((f for f in _facilitator_registry if f["facilitator_id"] == body.facilitator_id), None)
            if fac_rec:
                fac_rec["decision_paradigm"] = _req_paradigm
                _persist_facilitators()
        except Exception:
            pass  # Non-critical

        # 3. Store allowed interventions natively for this session
        overrides = body.allowed_overrides or []
        swipes = body.allowed_swipes or []
        await set_session_interventions(str(result["session_id"]), SessionInterventionsRequest(
            allowed_overrides=overrides,
            allowed_swipes=swipes
        ))

        # 4. Apply ending pathway to the session's initial state
        _ending_pathway = getattr(body, 'ending_pathway', None)
        if _ending_pathway:
            try:
                if _ending_pathway == "random":
                    from ending_pathways import resolve_pathway
                    _ending_pathway = resolve_pathway("random")
                # Write directly to the session's active_event_flags
                gs = result["global_state"]
                gs.setdefault("active_event_flags", {})["ending_pathway"] = _ending_pathway
                await db.update_latest_global_state(
                    str(result["session_id"]), gs, result["business_units"]
                )
                print(f"[session-start] Ending pathway set to '{_ending_pathway}' for {result['session_id']}")
            except Exception as exc:
                print(f"[WARN] Failed to set ending pathway: {exc}")
        
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve),
        )
    except HTTPException:
        raise  # Re-raise 403 (cohort limit) etc. as-is
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {exc}",
        )

    return StartSessionResponse(
        session_id=str(result["session_id"]),
        round_number=1,
        global_state=GlobalStateOut(**result["global_state"]),
        business_units=[_bu_out(bu) for bu in result["business_units"]],
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/solo-start
# Creates a self-contained solo/demo session for self-paced study.
# Bypasses facilitator gating and auto-seeds all 10 round configs.
# ─────────────────────────────────────────────────────────────────

class SoloStartRequest(BaseModel):
    player_name: str = "Solo Player"
    decision_paradigm: str = "legacy_abc"
    currency_symbol: str = "$"

@router.post(
    "/solo-start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a self-contained solo/demo session (no facilitator required)",
)
async def solo_start_simulation(body: SoloStartRequest):
    """
    Creates a fully self-contained solo session for self-paced learners.

    Key differences from /start:
    - No facilitator_id required — bypasses all facilitator gating.
    - No cohort-count limit check.
    - All 10 rounds are pre-unlocked (free pacing).
    - Round options are auto-seeded so the Strategic Options panel is never empty.
    - Session is tagged is_solo=True and expires in 24 hours.
    """
    from datetime import date, timedelta

    _req_paradigm = (body.decision_paradigm or "legacy_abc").strip()
    _VALID_PARADIGMS = {"legacy_abc", "multi_toggles", "advanced_climate", "healthcare", "un_sdg"}
    if _req_paradigm not in _VALID_PARADIGMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid decision_paradigm '{_req_paradigm}'. Valid: {sorted(_VALID_PARADIGMS)}",
        )

    # Use a unique name so duplicate-name guard doesn't block repeated solo starts
    import uuid as _uuid
    cohort_name = f"Solo — {body.player_name} ({_uuid.uuid4().hex[:6].upper()})"
    end_date_str = (date.today() + timedelta(days=1)).isoformat()

    try:
        result = await db.create_session(
            cohort_name=cohort_name,
            facilitator_id=None,          # No facilitator required
            loan_interest_rate=0.12,
            player_id=None,
            parent_cohort_id=None,
            decision_paradigm=_req_paradigm,
            currency_symbol=body.currency_symbol or "$",
            end_date=end_date_str,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create solo session: {exc}",
        )

    session_id = str(result["session_id"])

    # ── Tag session as solo + set free-play pacing (all rounds unlocked) ──
    import database_memory as _dm
    sess = _dm._sessions.get(session_id)
    if sess:
        sess["is_solo"] = True
        sess["pacing_mode"] = "free_play"
        sess["player_name"] = body.player_name
        _dm._persist()

    # ── Pre-unlock all rounds for this solo session ──
    from admin_shared import _round_pacing
    _round_pacing[session_id] = {
        "mode": "free",
        "unlocked_round": 999,
        "interval_seconds": 0,
        "next_unlock_at": None,
        "schedule": [],
        "_timer_tasks": [],
        "_timer_task": None,
        "set_by": None,
    }

    # ── Pre-seed round configs so the Strategic Options panel is never empty ──
    # We fetch all 10 rounds and store them on the session for the frontend
    # to retrieve via GET /api/simulations/{session_id}/solo-round-configs
    try:
        all_round_configs = {}
        for rnum in range(1, 11):
            if _req_paradigm == "un_sdg":
                from sdg_configs import get_sdg_round_config
                rcfg = get_sdg_round_config(rnum)
            elif _req_paradigm == "healthcare":
                from healthcare_configs import get_healthcare_round_config
                rcfg = get_healthcare_round_config(rnum)
            elif _req_paradigm == "multi_toggles":
                from pillar_configs import get_pillar_config
                rcfg = get_pillar_config(rnum) or get_round_config(rnum)
            else:
                rcfg = get_round_config(rnum)
            if rcfg:
                # Apply option shuffle for solo sessions too
                _solo_options = rcfg.get("options", {})
                if sess and _req_paradigm in ("legacy_abc", "advanced_climate"):
                    _solo_seed = sess.get("shuffle_seed")
                    if _solo_seed:
                        _solo_options = shuffle_options_for_display(_solo_options, _solo_seed, rnum)
                        _solo_options = strip_canonical_metadata(_solo_options)
                all_round_configs[str(rnum)] = {
                    "round_number": rnum,
                    "title": rcfg.get("title"),
                    "theme": rcfg.get("theme"),
                    "crisis": rcfg.get("crisis"),
                    "options": _solo_options,
                    "special_rules": rcfg.get("special_rules", {}),
                    "paradigm": _req_paradigm,
                }
        if sess:
            sess["_solo_round_configs"] = all_round_configs
            _dm._persist()
    except Exception as rc_exc:
        print(f"[WARN] solo-start: failed to pre-seed round configs: {rc_exc}")

    print(f"[solo-start] Created solo session {session_id} for '{body.player_name}' paradigm={_req_paradigm}")

    return StartSessionResponse(
        session_id=session_id,
        round_number=1,
        global_state=GlobalStateOut(**result["global_state"]),
        business_units=[_bu_out(bu) for bu in result["business_units"]],
    )


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/solo-round-configs
# Returns all pre-seeded round configs for a solo session
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/solo-round-configs",
    summary="Get all pre-seeded round configs for a solo session",
)
async def get_solo_round_configs(session_id: str):
    """
    Returns all 10 rounds' option sets pre-seeded at solo session creation.
    Used by the player cockpit to populate DecisionModal without extra fetches.
    """
    import database_memory as _dm
    sess = _dm._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if not sess.get("is_solo"):
        raise HTTPException(status_code=400, detail="Not a solo session")
    return {
        "session_id": session_id,
        "round_configs": sess.get("_solo_round_configs", {}),
        "is_solo": True,
    }



# Returns per-session metadata: currency_symbol, scenario_preset, paradigm
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/session-info", summary="Get session metadata (currency, preset, paradigm)")
async def get_session_info(session_id: str):
    session = await db.get_session_info(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If this is a player sub-session, also pull parent cohort's settings
    parent_id = session.get("parent_cohort_id")
    parent_currency = None
    if parent_id:
        parent = await db.get_session_info(parent_id)
        if parent:
            parent_currency = parent.get("currency_symbol", "$")

    # Read ending pathway from the session's latest state
    ending_pathway = "activist_ultimatum"
    try:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            ending_pathway = latest.get("global_state", {}).get(
                "active_event_flags", {}
            ).get("ending_pathway", "activist_ultimatum")
    except Exception:
        pass

    return {
        "session_id": session_id,
        "cohort_name": session.get("cohort_name"),
        "decision_paradigm": session.get("decision_paradigm", "legacy_abc"),
        "currency_symbol": session.get("currency_symbol") or parent_currency or "$",
        "parent_currency_symbol": parent_currency,
        "scenario_preset": session.get("scenario_preset"),
        "experience_level": session.get("experience_level"),
        "difficulty_tier": session.get("difficulty_tier", "advanced"),
        "parent_cohort_id": parent_id,
        "ending_pathway": ending_pathway,
        "pacing_mode": (parent.get("pacing_mode", "free_play") if parent_id and parent else session.get("pacing_mode", "free_play")),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/dashboard
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/dashboard",
    response_model=DashboardResponse,
    summary="Retrieve the current dashboard state",
)
async def get_dashboard(session_id: str):
    """
    Returns the latest round state plus full history for the session.
    """
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    history_raw = await db.fetch_round_history(session_id)

    history = [
        RoundSnapshot(
            round_number=h["round_number"],
            global_state=GlobalStateOut(**h["global_state"]),
            business_units=[_bu_out(bu) for bu in h["business_units"]],
        )
        for h in history_raw
    ]

    return DashboardResponse(
        session_id=session_id,
        current_round=latest["round_number"],
        global_state=GlobalStateOut(**latest["global_state"]),
        business_units=[_bu_out(bu) for bu in latest["bu_states"]],
        history=history,
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/commit-turn
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/commit-turn",
    response_model=CommitTurnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Commit decisions and advance to the next round",
)
async def commit_turn(session_id: str, body: CommitTurnRequest):
    """
    1. Fetches the current round state.
    2. Validates the round is < 10 (simulation cap).
    3. Runs pre-tick hooks (validation, crisis overrides).
    4. Runs the mathematical engine (process_tick).
    5. Runs post-tick hooks (round-specific state mutations).
    6. Persists the new immutable state and audit log.
    7. Returns the next-round state.
    """
    # ── FIX-QA-003: Per-session commit mutex (prevents race conditions) ──
    # Reject concurrent commits for the same session outright.
    commit_lock = _get_commit_lock(session_id)
    if commit_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another commit is in progress for this session. Please wait.",
        )
    await commit_lock.acquire()
    # ── ITEM 4: Per-session rate limiting (5s cooldown) ───────
    import time as _time
    now = _time.time()
    last_commit = _commit_timestamps.get(session_id, 0)
    if now - last_commit < 5.0:
        commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limited. Wait 5 seconds between commits.",
        )
    _commit_timestamps[session_id] = now

    # ── Fetch current state ──────────────────────────────────
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # ── Cohort end-date lockout ──────────────────────────────
    session_meta = await db.get_session_info(session_id)
    if session_meta:
        end_date_str = session_meta.get("end_date")
        if end_date_str:
            from datetime import date
            try:
                cohort_end = date.fromisoformat(end_date_str)
                if date.today() > cohort_end:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"This cohort expired on {end_date_str}. The game is locked and no further rounds can be played.",
                    )
            except ValueError:
                pass  # Malformed date — skip check

    current_round = current["round_number"]
    if current_round > 10:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already completed all 10 rounds.",
        )

    # ── ITEM 1: Optimistic locking — expected_round guard ────
    expected_round = getattr(body, 'expected_round', None)
    if expected_round is not None and expected_round != current_round:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stale round: expected round {expected_round} but "
                f"current is {current_round}. Refresh your dashboard."
            ),
        )

    # ── ITEM 5: Cohort pace lock — max_round enforcement ─────
    session_info_for_pace = await db.get_session_info(session_id)
    parent_id_for_pace = (session_info_for_pace or {}).get("parent_cohort_id")
    pace_session_id = parent_id_for_pace or session_id
    pace_session = await db.get_session_info(pace_session_id)
    max_round = (pace_session or {}).get("max_round")
    if max_round is not None and current_round > max_round:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cohort pace lock: maximum round is {max_round}. Wait for facilitator.",
        )

    # ── Round pacing gate ────────────────────────────────────
    from admin_shared import is_round_unlocked
    if not is_round_unlocked(session_id, current_round):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Round is locked. Waiting for facilitator to unlock.",
        )

    # ── Build engine inputs ──────────────────────────────────
    current_global = {
        "round_number": current_round,
        **current["global_state"],
    }
    current_bus = current["bu_states"]
    decisions_raw = [d.model_dump() for d in body.decisions]

    # ── Determine decision paradigm (fall back to parent cohort) ──
    session_info = await db.get_session_info(session_id)
    paradigm = (session_info or {}).get("decision_paradigm", "legacy_abc")
    if paradigm == "legacy_abc" and session_info and session_info.get("parent_cohort_id"):
        parent_info = await db.get_session_info(session_info["parent_cohort_id"])
        if parent_info:
            paradigm = parent_info.get("decision_paradigm", "legacy_abc")

    # ── Pillar-mode: aggregate multi-toggle decisions ─────────
    pillar_aggregation = None
    if paradigm == "multi_toggles":
        # Extract pillar_decisions from the first decision that has them
        pillar_choices = None
        for d in decisions_raw:
            if d.get("pillar_decisions"):
                pillar_choices = d["pillar_decisions"]
                break

        if pillar_choices:
            pillar_aggregation = aggregate_pillar_decisions(current_round, pillar_choices)

            # Translate to legacy choice for round_logic compatibility
            legacy_choice = translate_pillars_to_legacy_choice(current_round, pillar_choices)
            for d in decisions_raw:
                d["choice_selected"] = legacy_choice
        else:
            # Fallback: no pillar_decisions provided, treat as legacy
            paradigm = "legacy_abc"

    # ── ANTI-GAMING: Deshuffle displayed choice → canonical key ──
    # The frontend sends back option_a/b/c based on the shuffled
    # display order. We reverse-map to the real canonical key here
    # so all downstream logic (engine, round_logic, flags) is unaffected.
    _shuffle_seed = (session_info or {}).get("shuffle_seed")
    if _shuffle_seed and paradigm == "legacy_abc":
        for d in decisions_raw:
            raw_choice = d.get("choice_selected", "")
            if raw_choice:
                d["choice_selected"] = deshuffle_choice(raw_choice, _shuffle_seed, current_round)

    # ── FIX VULN-005/008/009: Input validation ────────────────
    valid_choices = {"option_a", "option_b", "option_c", ""}
    valid_bu_ids = {bu["bu_id"] for bu in current_bus}
    submitted_bu_ids = [d["bu_id"] for d in decisions_raw]

    # VULN-005: Reject duplicate BU IDs
    if len(submitted_bu_ids) != len(set(submitted_bu_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate BU IDs in decisions. Each BU must appear exactly once.",
        )

    # VULN-009: Require decisions for all active BUs
    missing = valid_bu_ids - set(submitted_bu_ids)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing decisions for BU(s): {', '.join(sorted(missing))}.",
        )

    # VULN-008: Validate choice_selected (only for legacy_abc paradigm)
    if paradigm == "legacy_abc":
        for d in decisions_raw:
            choice = d.get("choice_selected", "")
            if choice and choice not in valid_choices:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid choice_selected '{choice}'. Must be option_a, option_b, or option_c.",
                )

    # VULN-009: Enforce minimum investment of $1 per BU
    for d in decisions_raw:
        if d.get("capex_allocated", 0) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BU '{d['bu_id']}' must receive a minimum investment of $1.",
            )

    # ── PRE-TICK: Round-specific validation & overrides ───────
    pre_result = pre_tick(
        round_number=current_round,
        current_global=current_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        crisis_severity=body.crisis_severity,
    )

    # Check for validation errors (e.g. R2 CFO gate)
    if "validation_error" in pre_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pre_result["validation_error"],
        )

    # Use potentially overridden crisis severity
    effective_crisis = pre_result.get("crisis_severity", body.crisis_severity)

    # ── Crisis Multiplier KPI: expose severity source for UI display ──
    # Allows the frontend to show a visible "Crisis Multiplier" KPI panel.
    # Base crisis severity for this paradigm is 40 (from round_config special_rules).
    _BASE_CRISIS = 40
    _crisis_multiplier = round(effective_crisis / _BASE_CRISIS, 2) if _BASE_CRISIS else 1.0
    _pre_evts = pre_result.get("pre_events", {})
    if _pre_evts.get("electronics_blindspot_triggered"):
        _crisis_source = "electronics_blindspot"
        _crisis_label = "⚡ DOUBLED — Electronics audit skipped in Round 1"
    elif _pre_evts.get("deferred_audit_penalty") or _pre_evts.get("compliance_gap_triggered"):
        _crisis_source = "deferred_audit"
        _crisis_label = "⚠️ +50% — Audit deferred in Round 1"
    elif effective_crisis != body.crisis_severity:
        _crisis_source = "custom_override"
        _crisis_label = f"Custom: {effective_crisis}"
    else:
        _crisis_source = "baseline"
        _crisis_label = "✅ Baseline — Full audit completed"
    # ── PHASE-1: Inject difficulty tier into engine input ─────
    _session_difficulty = (session_info or {}).get("difficulty_tier", "standard")
    current_global.setdefault("active_event_flags", {})["difficulty_tier"] = _session_difficulty
    # ── Run the tick engine ──────────────────────────────────
    tick_result = process_tick(
        current_global=current_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        dividends_paid=body.dividends_paid,
        crisis_severity=effective_crisis,
        imitation_decay_rate=body.imitation_decay_rate,
        decision_paradigm=paradigm,
        emergency_credit_used=body.emergency_credit_used,
    )

    new_round = tick_result["global_state"]["round_number"]
    # ── CAP: After Round 10, do NOT advance to Round 11 ──
    if current_round == 10:
        new_round = 10
        tick_result["global_state"]["round_number"] = 10
    new_global = tick_result["global_state"]
    new_bus = tick_result["bu_states"]
    events = tick_result["events"]

    # ── Crisis Multiplier KPI: expose severity source for UI display ──
    events["crisis_severity_effective"] = effective_crisis
    events["crisis_multiplier"] = _crisis_multiplier
    events["crisis_multiplier_source"] = _crisis_source
    events["crisis_multiplier_label"] = _crisis_label

    # Merge pre-tick events
    events.update(pre_result.get("pre_events", {}))

    # ── PILLAR MODE: Apply aggregated impacts ────────────────
    if pillar_aggregation:
        agg_impacts = pillar_aggregation.get("impacts", {})
        agg_cost = pillar_aggregation.get("total_cost", 0)

        # Apply treasury cost from pillar selections (NOT modified by effectiveness — cost is always owed)
        if agg_cost != 0:
            new_global["corporate_treasury"] = round(new_global["corporate_treasury"] + agg_cost, 2)
            events["pillar_cost_applied"] = agg_cost

        # ── Workforce Readiness → Pillar Effectiveness ──
        # Low readiness reduces the magnitude of strategic impacts (not costs)
        effectiveness = new_global.get("pillar_effectiveness_modifier", 1.0)
        if effectiveness != 1.0:
            events["pillar_effectiveness_modifier_applied"] = effectiveness

        # Apply reputation delta (scaled by effectiveness)
        rep_delta = round(agg_impacts.get("reputation", 0) * effectiveness, 2)
        if rep_delta != 0:
            new_global["group_reputation"] = max(0, min(100, round(new_global["group_reputation"] + rep_delta, 2)))

        # Calculate BU revenue weights for proportional delta application
        total_revenue = sum(bu.get("revenue_base", 0) for bu in new_bus)
        num_bus = len(new_bus)

        def _get_weight(bu_data: dict) -> float:
            if total_revenue <= 0 or num_bus == 0:
                return 1.0 / max(1, num_bus)
            return bu_data.get("revenue_base", 0) / total_revenue

        # Apply NCD delta proportionally across BUs (scaled by effectiveness)
        ncd_delta = round(agg_impacts.get("natural_capital_debt_delta", 0) * effectiveness, 2)
        if ncd_delta != 0:
            for bu in new_bus:
                proportional_ncd = ncd_delta * _get_weight(bu) * num_bus
                bu["natural_capital_debt"] = max(0, round(bu.get("natural_capital_debt", 0) + proportional_ncd, 2))

        # Apply carbon intensity delta proportionally across BUs (scaled by effectiveness)
        ci_delta = round(agg_impacts.get("carbon_intensity_delta", 0) * effectiveness, 2)
        if ci_delta != 0:
            for bu in new_bus:
                proportional_ci = ci_delta * _get_weight(bu) * num_bus
                bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + proportional_ci, 2))

        # Apply social license delta proportionally across BUs (scaled by effectiveness)
        sl_delta = round(agg_impacts.get("social_license_delta", 0) * effectiveness, 2)
        if sl_delta != 0:
            for bu in new_bus:
                proportional_sl = sl_delta * _get_weight(bu) * num_bus
                bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + proportional_sl, 2)))

        # Apply governance risk delta proportionally across BUs (scaled by effectiveness)
        gov_delta = round(agg_impacts.get("governance_risk_delta", 0) * effectiveness, 2)
        if gov_delta != 0:
            for bu in new_bus:
                proportional_gov = gov_delta * _get_weight(bu) * num_bus
                bu["governance_risk_score"] = max(0, min(100, round(bu.get("governance_risk_score", 0) + proportional_gov, 2)))

        # Apply water dependency delta proportionally across BUs (scaled by effectiveness)
        wd_delta = round(agg_impacts.get("water_dependency_delta", 0) * effectiveness, 2)
        if wd_delta != 0:
            for bu in new_bus:
                proportional_wd = wd_delta * _get_weight(bu) * num_bus
                bu["water_dependency"] = max(0, round(bu.get("water_dependency", 0) + proportional_wd, 2))

        # Apply burnout delta across all BUs (from HR pillar visible impacts)
        burnout_delta = agg_impacts.get("burnout_delta", 0)
        if burnout_delta != 0:
            for bu in new_bus:
                current_bo = bu.get("staff_burnout_index", 0.0)
                bu["staff_burnout_index"] = max(0.0, min(100.0, round(current_bo + burnout_delta, 2)))
            events["pillar_burnout_delta_applied"] = burnout_delta

        # Store pillar metadata in events
        events["decision_paradigm"] = "multi_toggles"
        events["pillar_selections"] = pillar_aggregation.get("per_area", {})
        events["pillar_flags"] = pillar_aggregation.get("flags_set", [])
        events["pillar_exclusivity_warnings"] = pillar_aggregation.get("exclusivity_warnings", [])
        # Rec 5: Expose aggregate impacts for post-tick handlers to read
        events["pillar_aggregate_impacts"] = agg_impacts

        # Persist pillar flags into active_event_flags
        flag_key = f"r{current_round}_pillar_flags"
        new_global.setdefault("active_event_flags", {})
        new_global["active_event_flags"][flag_key] = pillar_aggregation.get("flags_set", [])
    else:
        events["decision_paradigm"] = "legacy_abc"

    # ── POST-TICK: Round-specific state mutations ────────────
    post_events = post_tick(
        round_number=current_round,
        global_state=new_global,
        bu_states=new_bus,
        decisions=decisions_raw,
        events=events,
        previous_flags=current_global.get("active_event_flags", {}),
    )
    events.update(post_events)

    # ── NEW ENGINES: Process all improvement modules ──────────
    # Inject data needed by balance sheet engine (CAPEX & dividends)
    events["decisions_raw"] = decisions_raw
    events["dividends_paid"] = body.dividends_paid
    try:
        new_engine_events = run_new_engines(
            round_number=current_round,
            global_state=new_global,
            bu_states=new_bus,
            events=events,
        )
        events.update(new_engine_events)
    except Exception as exc:
        print(f"[WARN] New engines batch failed: {exc}")

    # Ensure active_event_flags contains everything
    new_global["active_event_flags"] = events

    # ── CHECK HIDDEN RESOURCE TRIGGERS ───────────────────────
    try:
        triggered = await check_hidden_resource_triggers(
            session_id=session_id,
            round_number=new_round,
            global_state=new_global,
            bu_states=new_bus,
        )
        if triggered:
            events["hidden_resources_unlocked"] = [
                {"id": r["id"], "title": r["title"], "effect": r.get("effect")}
                for r in triggered
            ]
    except Exception as exc:
        # Non-critical — don't block the turn commit
        print(f"[WARN] Hidden resource trigger check failed: {exc}")

    # Clear saved decisions since turn was committed
    if "saved_allocations" in new_global:
        del new_global["saved_allocations"]
    if "saved_decision_choice" in new_global:
        del new_global["saved_decision_choice"]

    # FIX AUDIT-002: Removed duplicate R10 terminal valuation block.
    # The authoritative R10 calculation lives in round_logic.py →
    # _post_r10_grand_finale(), which uses flag-based MR accounting,
    # config-driven exit multiples, and correct carbon tonnage units.
    # The previous block here used a divergent formula (continuous MR,
    # dynamic exit multiple, different profile thresholds) that silently
    # overwrote the round_logic.py values in the events dict.

    # ── Enrich decisions for audit trail ─────────────────────
    # Populate decision_node_id from round config (crisis ID)
    round_cfg = get_round_config(current_round)
    crisis_id = round_cfg.get("crisis", {}).get("id", "") if round_cfg else ""
    crisis_title = round_cfg.get("crisis", {}).get("title", "") if round_cfg else ""
    # Populate player_id from session metadata
    audit_player_id = (session_info or {}).get("player_id") or ""
    for d in decisions_raw:
        if not d.get("decision_node_id"):
            d["decision_node_id"] = crisis_title or crisis_id
        if not d.get("player_id"):
            d["player_id"] = audit_player_id

    # ── Persist ──────────────────────────────────────────────
    # ── R10 SYSTEM FREEZE: Capture DNA snapshot ──────────────
    if current_round == 10:
        try:
            from consequence_dna_api import build_consequence_dna_data
            history_raw = await db.fetch_round_history(session_id)
            history_for_dna = [
                {"round_number": h["round_number"], "global_state": h["global_state"], "decisions": h.get("decisions", [])}
                for h in history_raw
            ]
            dna_snapshot = build_consequence_dna_data(
                session_id=session_id,
                global_state=new_global,
                bu_states=new_bus,
                history=history_for_dna,
            )
            new_global.setdefault("active_event_flags", {})["consequence_dna_snapshot"] = dna_snapshot
        except Exception as exc:
            print(f"[WARN] Consequence DNA snapshot capture failed: {exc}")

    try:
        if current_round == 10:
            # R10: Update existing state in-place (don't insert new round 11)
            await db.update_latest_global_state(
                session_id=session_id,
                global_state=new_global,
                bu_states=new_bus,
            )
            # Still log R10 decisions to the audit trail
            for dec in decisions_raw:
                pass  # decisions are logged inline by insert_next_round; for R10 update we skip
        else:
            await db.insert_next_round(
                session_id=session_id,
                round_number=new_round,
                global_state=new_global,
                bu_states=new_bus,
                decisions=decisions_raw,
            )
    except Exception as exc:
        # Unique constraint → duplicate round
        if "uq_session_round" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Round {new_round} has already been committed for this session.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist round: {exc}",
        )

    # ── AUTO-INJECT SCHEDULED INTERVENTIONS ───────────────────
    try:
        auto_injected = await auto_inject_scheduled_interventions(
            session_id=session_id,
            new_round=new_round,
        )
        if auto_injected:
            events["auto_injected_messages"] = [
                {"id": m["id"], "title": m["title"], "preset_id": m.get("preset_id")}
                for m in auto_injected
            ]
    except Exception as exc:
        print(f"[WARN] Auto-inject scheduled interventions failed: {exc}")

    # ── MP-01: Update cohort commit count in globalState ─────────────
    try:
        parent_cohort_id = (session_info or {}).get("parent_cohort_id")
        if parent_cohort_id:
            siblings = _session_players.get(parent_cohort_id, [])
            total_teams = len(siblings)
            committed_count = 0
            for sibling in siblings:
                sib_sid = sibling.get("player_session_id")
                if sib_sid:
                    sib_state = await db.fetch_latest_state(sib_sid)
                    if sib_state and sib_state.get("round_number", 1) == new_round:
                        committed_count += 1
            new_global["team_commits_this_round"] = committed_count
            new_global["cohort_team_count"] = total_teams
            await db.update_latest_global_state(session_id, new_global, new_bus)
    except Exception as exc:
        print(f"[WARN] Cohort commit count update failed: {exc}")

    # ── PRACTICE MODE: Reset after Round 2 ────────────────────
    # Check if this session or its parent is in practice mode
    practice_session_id = session_id
    if session_info and session_info.get("parent_cohort_id"):
        practice_session_id = session_info["parent_cohort_id"]

    if is_practice_mode(practice_session_id) and current_round >= 2:
        # Reset the cohort session and all child sessions back to Round 1
        await db.reset_session_to_round1(practice_session_id)
        # Disable practice mode after reset
        from admin_shared import _practice_mode
        _practice_mode.pop(practice_session_id, None)

        # Notify all players of the practice reset
        from admin_router import manager as ws_manager
        await ws_manager.push_to_session(practice_session_id, {
            "type": "practice_reset",
            "message": "Practice round completed! Session has been reset to Round 1.",
        })

        # Return a special response with practice_reset event
        reset_state = await db.fetch_latest_state(session_id)
        reset_events = {"practice_reset": True, "practice_message": "Practice complete — session reset to Round 1."}
        return CommitTurnResponse(
            session_id=session_id,
            new_round_number=1,
            global_state=GlobalStateOut(**(reset_state["global_state"] if reset_state else new_global)),
            business_units=[_bu_out(bu) for bu in (reset_state["bu_states"] if reset_state else new_bus)],
            events=reset_events,
        )

    # ── ENGAGEMENT 7.2: CEO Diary ──────────────────────────────
    try:
        from ceo_diary import generate_ceo_diary
        primary_choice = ""
        for d in decisions_raw:
            c = d.get("choice_selected", "")
            if c.startswith("option_"):
                primary_choice = c
                break
        diary_entry = generate_ceo_diary(current_round, primary_choice, events)
        events["ceo_diary"] = diary_entry
    except Exception as exc:
        print(f"[WARN] CEO Diary generation failed: {exc}")

    # ── ENGAGEMENT 7.4: Board Pressure Events (R3, R6, R9) ───
    if current_round in (3, 6, 9):
        try:
            baseline_ebitda = current_global.get("historical_ebitda", 0)
            current_ebitda = sum(bu["revenue_base"] - bu["opex_base"] for bu in new_bus)
            target_ebitda = baseline_ebitda * 1.05  # 5% improvement target
            if current_ebitda < target_ebitda:
                shortfall_pct = round(((target_ebitda - current_ebitda) / max(target_ebitda, 1)) * 100, 1)
                events["board_pressure"] = {
                    "triggered": True,
                    "target_ebitda": target_ebitda,
                    "actual_ebitda": current_ebitda,
                    "shortfall_pct": shortfall_pct,
                    "message": (
                        f"⚠️ BOARD WARNING: EBITDA (${current_ebitda:,.0f}) is "
                        f"{shortfall_pct}% below the board's target of ${target_ebitda:,.0f}. "
                        f"The Chairman expects a credible improvement plan by next period. "
                        f"Failure to deliver may result in a leadership review."
                    ),
                    "reputation_penalty": -3,
                }
                # Apply reputation penalty
                new_global["group_reputation"] = max(0, round(
                    new_global.get("group_reputation", 50) - 3, 2
                ))
            else:
                events["board_pressure"] = {
                    "triggered": False,
                    "message": "✅ Board satisfied — EBITDA meets or exceeds target.",
                }
        except Exception as exc:
            print(f"[WARN] Board pressure calculation failed: {exc}")

    # ── ENGAGEMENT 7.1: Decision Regret (Shadow Ticks) ────────
    try:
        from admin_shared import _god_mode_settings
        if _god_mode_settings.get("decision_regret_enabled", True):
            regret_analysis = {}
            all_options = ["option_a", "option_b", "option_c"]
            for alt_option in all_options:
                if alt_option == primary_choice:
                    continue
                # Create shadow decisions with alternative choice
                shadow_decisions = copy.deepcopy(decisions_raw)
                for d in shadow_decisions:
                    d["choice_selected"] = alt_option
                try:
                    import copy as _copy
                    shadow_result = process_tick(
                        current_global=_copy.deepcopy(current_global),
                        current_bus=_copy.deepcopy(current_bus),
                        decisions=shadow_decisions,
                        dividends_paid=body.dividends_paid,
                        crisis_severity=effective_crisis,
                        imitation_decay_rate=body.imitation_decay_rate,
                        decision_paradigm=paradigm,
                    )
                    shadow_gs = shadow_result["global_state"]
                    shadow_bus = shadow_result["bu_states"]
                    shadow_ebitda = sum(b["revenue_base"] - b["opex_base"] for b in shadow_bus)
                    actual_ebitda = sum(b["revenue_base"] - b["opex_base"] for b in new_bus)
                    regret_analysis[alt_option] = {
                        "treasury_delta": round(shadow_gs["corporate_treasury"] - new_global["corporate_treasury"], 2),
                        "reputation_delta": round(shadow_gs["group_reputation"] - new_global.get("group_reputation", 50), 2),
                        "ebitda_delta": round(shadow_ebitda - actual_ebitda, 2),
                    }
                except Exception:
                    pass  # Shadow tick failed — skip this option
            if regret_analysis:
                events["decision_regret"] = {
                    "your_choice": primary_choice,
                    "alternatives": regret_analysis,
                    "note": "What would have happened if you chose differently?",
                }
    except Exception as exc:
        print(f"[WARN] Decision Regret analysis failed: {exc}")

    # ── ITEM 24: Facilitator commit notification ─────────────
    try:
        parent_cohort_id = (session_info or {}).get("parent_cohort_id")
        if parent_cohort_id:
            import time as _time_notify
            notification = {
                "player_id": (session_info or {}).get("player_id", "unknown"),
                "round": new_round,
                "timestamp": _time_notify.time(),
                "choice": primary_choice,
            }
            parent_sess = await db.get_session_info(parent_cohort_id)
            if parent_sess:
                commit_log = parent_sess.setdefault("commit_notifications", [])
                commit_log.append(notification)
                # Keep only last 100 notifications
                if len(commit_log) > 100:
                    parent_sess["commit_notifications"] = commit_log[-100:]
    except Exception as exc:
        print(f"[WARN] Facilitator notification failed: {exc}")

    # ── FIX-QA-003: Release commit lock after all processing ──
    commit_lock.release()

    return CommitTurnResponse(
        session_id=session_id,
        new_round_number=new_round,
        global_state=GlobalStateOut(**new_global),
        business_units=[_bu_out(bu) for bu in new_bus],
        events=events,
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/save-decisions
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/save-decisions",
    status_code=status.HTTP_200_OK,
    summary="Save uncommitted UI allocations and decisions mid-round",
)
async def save_decisions(session_id: str, body: SaveDecisionsRequest):
    """
    Saves the user's current slider allocations and chosen decision
    to the global_state so they can resume after leaving the page.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found."
        )

    global_state = current["global_state"]
    bu_states = current["bu_states"]

    global_state["saved_allocations"] = body.allocations
    global_state["saved_decision_choice"] = body.decision_choice

    # Update latest state in DB
    await db.update_latest_global_state(session_id, global_state, bu_states)

    return {"status": "success", "message": "Decisions saved successfully."}


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/consequence-dna-data
# Consequence DNA Visualizer — full Sankey diagram data model
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/consequence-dna-data",
    summary="Get Consequence DNA Sankey data for the visualizer",
)
async def get_consequence_dna_data(session_id: str):
    """
    Returns the complete data model for the Consequence DNA Visualizer:
    decision nodes, causal flags, metric shifts, M_R projections,
    agent conflict/constriction nodes, cascade events, and Senge badges.
    """
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    history_raw = await db.fetch_round_history(session_id)
    history = [
        {"round_number": h["round_number"], "global_state": h["global_state"], "decisions": h.get("decisions", [])}
        for h in history_raw
    ]

    from consequence_dna_api import build_consequence_dna_data
    dna_data = build_consequence_dna_data(
        session_id=session_id,
        global_state=latest["global_state"],
        bu_states=latest["bu_states"],
        history=history,
    )
    return dna_data


# ─────────────────────────────────────────────────────────────────
# SHADOW BOARD AUDIT — Round 5 Reflective Middleware
# ─────────────────────────────────────────────────────────────────

class ShadowBoardRejectionRequest(BaseModel):
    rejection_target: str  # 'shareholder' | 'activist' | 'auditor'

@router.get(
    "/{session_id}/shadow-board-audit",
    summary="Get Shadow Board Audit personas and state (R5 middleware)",
)
async def get_shadow_board_audit(session_id: str):
    """
    Returns the three Shadow Board personas with their scripts and the
    current audit state for this session. Called when Round 5 briefing
    is dismissed to determine if the audit modal should be shown.
    """
    from shadow_board_audit import (
        get_shadow_board_personas,
        get_shadow_board_state,
        check_shadow_board_required,
    )

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = latest["global_state"]
    round_number = latest["round_number"]

    return {
        "session_id": session_id,
        "round_number": round_number,
        "audit_required": check_shadow_board_required(round_number, gs),
        "audit_state": get_shadow_board_state(gs),
        "personas": get_shadow_board_personas(),
    }


@router.post(
    "/{session_id}/shadow-board-audit/reject",
    status_code=status.HTTP_200_OK,
    summary="Submit Shadow Board public rejection (R5 middleware)",
)
async def submit_shadow_board_rejection(
    session_id: str, body: ShadowBoardRejectionRequest
):
    """
    Records the player's public rejection of one of the three Shadow Board
    personas. This:
    1. Sets hidden flags evaluated at Round 10 for ending pathway cascades
    2. Adjusts the corresponding stakeholder agent's tolerance (-10)
    3. Classifies the firm's strategic archetype
    4. Returns consequence DNA chain for UI traceability
    """
    from shadow_board_audit import process_rejection
    from autonomous_agents import AGENT_PROFILES

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = latest["global_state"]
    bus = latest["bu_states"]

    # Check if already completed
    flags = gs.get("active_event_flags", {})
    if flags.get("shadow_board_completed"):
        return {
            "status": "already_completed",
            "message": "Shadow Board Audit has already been completed for this session.",
            "rejection_target": flags.get("shadow_board_rejection"),
            "archetype": flags.get("shadow_board_archetype"),
        }

    # Validate rejection target
    valid_targets = {"shareholder", "activist", "auditor"}
    if body.rejection_target not in valid_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rejection_target '{body.rejection_target}'. "
                   f"Must be one of: {sorted(valid_targets)}",
        )

    # Load autonomous agent state from global_state
    agent_state = gs.get("autonomous_agents")
    if not agent_state:
        # Try to initialize if missing
        try:
            from autonomous_agents import create_initial_agent_state
            agent_state = create_initial_agent_state()
        except Exception:
            agent_state = None

    # Process the rejection
    result = process_rejection(
        rejection_target=body.rejection_target,
        global_state=gs,
        agent_master_state=agent_state,
    )

    # Persist agent state back
    if agent_state:
        gs["autonomous_agents"] = agent_state

    # Persist updated global state
    await db.update_latest_global_state(session_id, gs, bus)

    print(
        f"[shadow-board] Session {session_id}: "
        f"Rejected '{body.rejection_target}' -> "
        f"flag='{result['hidden_flag']['name']}', "
        f"archetype='{result['strategic_archetype']['archetype']}'"
    )

    return result


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/round-config/{round_number}
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/round-config/{round_number}",
    summary="Get crisis and options for a specific round",
)
async def get_round_config_endpoint(round_number: int, session_id: str | None = None):
    """
    Returns the crisis definition, decision options, special rules,
    and UI constraints for a round.
    Used by the frontend to populate the DecisionModal.
    
    If session_id is provided, returns paradigm-specific config
    (e.g. SDG or Healthcare) when applicable.
    """
    paradigm = None
    if session_id:
        try:
            state = await db.get_session_info(session_id)
            if state:
                paradigm = state.get("decision_paradigm")
                if (paradigm is None or paradigm == "legacy_abc") and state.get("parent_cohort_id"):
                    parent_state = await db.get_session_info(state["parent_cohort_id"])
                    if parent_state:
                        paradigm = parent_state.get("decision_paradigm")
        except Exception as e:
            print(f"[WARN] Error fetching session paradigm for round-config: {e}")
            pass

    # Select the correct config based on paradigm
    if paradigm == "un_sdg":
        from sdg_configs import get_sdg_round_config
        cfg = get_sdg_round_config(round_number)
    elif paradigm == "healthcare":
        from healthcare_configs import get_healthcare_round_config
        cfg = get_healthcare_round_config(round_number)
    else:
        cfg = get_round_config(round_number)

    # ── Ending Pathway: overlay R10 crisis/options if non-default ──
    ending_pathway = None
    if round_number == 10 and session_id and paradigm not in ("un_sdg", "healthcare"):
        try:
            latest = await db.fetch_latest_state(session_id)
            if latest:
                ending_pathway = latest.get("global_state", {}).get(
                    "active_event_flags", {}
                ).get("ending_pathway", "activist_ultimatum")
            if ending_pathway and ending_pathway not in ("activist_ultimatum", ""):
                from ending_pathways import get_pathway_r10_config
                pw_cfg = get_pathway_r10_config(ending_pathway)
                if pw_cfg and cfg:
                    cfg["crisis"] = pw_cfg["crisis"]
                    cfg["options"] = pw_cfg["options"]
                    cfg["special_rules"] = pw_cfg.get("special_rules", cfg.get("special_rules", {}))
        except Exception as e:
            print(f"[WARN] Error loading pathway R10 config: {e}")

    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration for round {round_number}.",
        )

    # ── ANTI-GAMING: Shuffle option presentation order ────────
    # Randomizes A/B/C labels per session so the letter carries no
    # signal about option quality. Backend logic is unaffected.
    options_out = cfg.get("options", {})
    if session_id and (paradigm or "legacy_abc") in ("legacy_abc", "advanced_climate"):
        try:
            sess_meta = await db.get_session_info(session_id)
            _shuffle_seed = (sess_meta or {}).get("shuffle_seed")
            if _shuffle_seed:
                options_out = shuffle_options_for_display(options_out, _shuffle_seed, round_number)
                options_out = strip_canonical_metadata(options_out)

                # R10 synergy gate: apply disabled state to whichever display
                # position now holds the "Resist & Integrate" option
                if round_number == 10:
                    try:
                        latest_state = await db.fetch_latest_state(session_id)
                        if latest_state:
                            _synergy = latest_state["global_state"].get("synergy_multiplier", 1.0) * 100
                            for opt_key, opt_val in options_out.items():
                                ui_c = opt_val.get("ui_constraints", {})
                                threshold = ui_c.get("require_synergy_above")
                                if threshold is not None and _synergy <= threshold:
                                    opt_val["disabled"] = True
                                    opt_val["disabled_reason"] = (
                                        f"Requires Synergy Score > {threshold} (current: {_synergy:.0f})"
                                    )
                    except Exception as e:
                        print(f"[WARN] R10 synergy gate check failed: {e}")
        except Exception as e:
            print(f"[WARN] Option shuffle failed, serving unshuffled: {e}")

    # Build UI constraints from options for frontend gating
    ui_constraints = {}
    for opt_key, opt_val in options_out.items():
        if isinstance(opt_val, dict) and opt_val.get("ui_constraint"):
            ui_constraints[opt_key] = opt_val["ui_constraint"]

    return {
        "round_number": round_number,
        "title": cfg.get("title"),
        "theme": cfg.get("theme"),
        "crisis": cfg.get("crisis"),
        "options": options_out,
        "special_rules": cfg.get("special_rules", {}),
        "ui_constraints": ui_constraints,
        "paradigm": paradigm or "legacy_abc",
        "ending_pathway": ending_pathway,
        "options_shuffled": bool(session_id),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/pillar-config/{round_number}
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/pillar-config/{round_number}",
    summary="Get strategic pillar options for a specific round (multi-toggles mode)",
)
async def get_pillar_config_endpoint(round_number: int):
    """
    Returns the 5-area strategic pillar options for a round.
    Used by the frontend StrategicPillarsWorkspace in multi_toggles mode.
    """
    cfg = get_pillar_config(round_number)
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pillar configuration for round {round_number}.",
        )

    return {
        "round_number": round_number,
        "title": cfg.get("title"),
        "description": cfg.get("description"),
        "areas": cfg.get("areas", {}),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/paradigm
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/paradigm",
    summary="Get the decision paradigm for a session",
)
async def get_session_paradigm(session_id: str):
    """Returns which decision paradigm (legacy_abc or multi_toggles) a session uses.
    Falls back to the parent cohort's paradigm for child player sessions."""
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found.")
    paradigm = session_info.get("decision_paradigm", "legacy_abc")
    # If this is a child player session, inherit from parent cohort
    if paradigm == "legacy_abc" and session_info.get("parent_cohort_id"):
        parent_info = await db.get_session_info(session_info["parent_cohort_id"])
        if parent_info:
            paradigm = parent_info.get("decision_paradigm", "legacy_abc")
    return {
        "session_id": session_id,
        "decision_paradigm": paradigm,
        "paradigm_locked": bool(session_info.get("paradigm_locked", False)),
    }


# ─────────────────────────────────────────────────────────────────
# PUT /api/simulations/{session_id}/paradigm
# ─────────────────────────────────────────────────────────────────

class UpdateParadigmRequest(BaseModel):
    decision_paradigm: str  # 'legacy_abc', 'multi_toggles', or 'advanced_climate'

@router.put(
    "/{session_id}/paradigm",
    summary="Update the decision paradigm for a session",
)
async def update_session_paradigm(session_id: str, body: UpdateParadigmRequest):
    """Set the decision paradigm for a session. Propagates to child player sessions."""
    if body.decision_paradigm not in ("legacy_abc", "multi_toggles", "advanced_climate", "healthcare"):
        raise HTTPException(status_code=400, detail="Invalid paradigm. Must be 'legacy_abc', 'multi_toggles', 'advanced_climate', or 'healthcare'.")

    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Once set, the paradigm is locked for this cohort
    if session_info.get("paradigm_locked"):
        raise HTTPException(
            status_code=409,
            detail="Decision paradigm has already been set for this cohort and cannot be changed."
        )

    session_info["decision_paradigm"] = body.decision_paradigm
    session_info["paradigm_locked"] = True

    # Propagate to all child player sessions
    try:
        import copy
        from database_memory import _sessions, _bu_states, _global_states, _load_seed
        
        # If healthcare is chosen, we must rewrite the business units to healthcare ones.
        # This assumes the configuration is done at Round 1 before significant progression.
        if body.decision_paradigm == "healthcare":
            seed = _load_seed(industry="healthcare")
            # Overwrite the parent cohort BUs
            _bu_states[session_id] = {1: copy.deepcopy(seed["business_units"])}
            _bu_states[session_id] = {1: copy.deepcopy(seed["business_units"])}
            # Also overwrite global state with SDG-specific treasury ($500M)
            states = _global_states.get(session_id, [])
            if states:
                states[-1]["corporate_treasury"] = seed["global_state"]["corporate_treasury_usd"]
                states[-1]["political_capital"] = seed["global_state"].get("political_capital", 50.0)
                states[-1]["community_trust_score"] = seed["global_state"].get("community_trust_score", 50.0)
                states[-1]["global_emissions_intensity"] = seed["global_state"].get("global_emissions_intensity", 60.0)

        for sid, sdata in _sessions.items():
            if sdata.get("parent_cohort_id") == session_id:
                sdata["decision_paradigm"] = body.decision_paradigm
                if body.decision_paradigm == "healthcare":
                    _bu_states[sid] = {1: copy.deepcopy(seed["business_units"])}
                elif body.decision_paradigm == "un_sdg":
                    _bu_states[sid] = {1: copy.deepcopy(seed["business_units"])}
                    child_states = _global_states.get(sid, [])
                    if child_states:
                        child_states[-1]["corporate_treasury"] = seed["global_state"]["corporate_treasury_usd"]
                        child_states[-1]["political_capital"] = seed["global_state"].get("political_capital", 50.0)
                        child_states[-1]["community_trust_score"] = seed["global_state"].get("community_trust_score", 50.0)
                        child_states[-1]["global_emissions_intensity"] = seed["global_state"].get("global_emissions_intensity", 60.0)
    except ImportError:
        pass

    return {
        "status": "success",
        "session_id": session_id,
        "decision_paradigm": body.decision_paradigm,
    }


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/materiality
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/materiality",
    response_model=MaterialitySubmissionResponse,
    summary="Submit Double Materiality matrix and receive capital allocation",
)
async def submit_materiality_matrix(session_id: str, body: MaterialitySubmissionRequest):
    """
    1. Fetches current state and dynamic materiality config.
    2. If bu_id is provided (Strategic Pillars mode), loads BU-specific dictionary.
    3. Deducts stakeholder panel fee if used (tiered: 1-4 issues=$250K each; 5-8=$500K each).
    4. Validates CFO Rule: NO non-material (Q2/Q3/Q4) issues allowed in Q1 Top Right.
    5. Calculates M_acc (valid Q1 issues placed correctly / Total True Q1).
    6. Applies Option C budget clawback (40%) if materiality_ignored flag is active.
    7. Allocates disclosure_investment_budget for Q2 issues placed correctly.
    8. Persists the new treasury state and emits ESRS debrief card.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    bu_states = current["bu_states"]

    # Load dynamic Materiality Config
    # Priority: 1) BU-specific dict (if bu_id), 2) Cohort sandbox, 3) Global
    if body.bu_id:
        bu_override_key = f"materiality_dictionary_override_{body.bu_id}"
        if bu_override_key in global_state:
            mat_config = global_state[bu_override_key]
        else:
            mat_config = mat_db.get_bu_config(body.bu_id)
    elif "materiality_dictionary_override" in global_state:
        mat_config = global_state["materiality_dictionary_override"]
    else:
        mat_config = mat_db.get_current_config()

    all_issues = mat_config.get("issues", [])
    from round2_csrd import ROUND_2_DEFAULT_CONFIG
    panel_config = ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"]

    # ── R1 Intelligence Modulation ─────────────────────────────────────────────
    # If electronics_blindspot flag is active (R1A Surface Scan chosen),
    # degrade hover_description for electronics_sensitive issues.
    # The frontend receives this via the issues list — we annotate them here
    # so the materiality config endpoint can surface the degraded descriptions.
    prev_flags = global_state.get("active_event_flags", {})
    has_blindspot = "electronics_blindspot" in _collect_flags_from_state(prev_flags)
    if has_blindspot:
        all_issues = [
            {**issue, "hover_description": issue.get("blindspot_description") or issue["hover_description"]}
            if issue.get("electronics_sensitive")
            else issue
            for issue in all_issues
        ]
        global_state["r1_blindspot_active_in_r2"] = True

    # ── R1 Stakeholder Voice Boost ─────────────────────────────────────────────
    # If player correctly classified a stakeholder in R1 Mendelow matrix,
    # mark that stakeholder's linked issues as "stakeholder_confirmed" so
    # the frontend can show a confirmation badge on those issue chips.
    # FIX C1/C18/C22: Keys match stakeholder_map.py IDs, all 10 mapped.
    stakeholder_accuracy = global_state.get("stakeholder_accuracy", {})
    stakeholder_boosts = set()
    stakeholder_boost_map = {
        "activist_fund": ["shareholder_activism", "executive_compensation"],
        "eu_regulators": ["csrd_compliance", "carbon_disclosure", "scope3_reporting"],
        "local_communities": ["water_scarcity", "plastic_packaging", "philanthropy"],
        "tier3_miners": ["tier3_labor", "living_wage", "conflict_minerals"],
        "factory_employees": ["ai_bias", "employee_volunteering", "just_transition"],
        "syndicate_banks": ["green_bonds", "esg_lending_criteria"],
        "national_gov": ["carbon_tax", "environmental_fines"],
        "cafeteria_vendors": [],
        "gen_public": [],
        "local_media": [],
    }
    for stakeholder_key, issue_ids in stakeholder_boost_map.items():
        # Check if this stakeholder was correctly placed in "Manage Closely" quadrant
        if stakeholder_accuracy.get(stakeholder_key) == "manage_closely":
            stakeholder_boosts.update(issue_ids)
    global_state["stakeholder_boosted_issues"] = list(stakeholder_boosts)

    # Pre-compute the target Q1 (High Fin + High Impact)
    q1_target_issue_ids = set()
    for issue in all_issues:
        if issue["financial_impact"] == "high" and issue["societal_impact"] == "high":
            q1_target_issue_ids.add(issue["id"])

    total_budget = ROUND_2_DEFAULT_CONFIG["round_2_config"]["total_materiality_budget"]
    disclosure_budget = ROUND_2_DEFAULT_CONFIG["round_2_config"]["disclosure_investment_budget"]

    # ── Stakeholder Panel Survey Fee (tiered pricing) ──────────────────────────
    if body.consultant_used:
        panel_issue_count = max(1, min(8, body.panel_issue_count))
        tier_break = panel_config.get("tier_break", 4)
        base_fee = panel_config.get("base_fee_per_issue_usd", 250_000)
        extended_fee = panel_config.get("extended_fee_per_issue_usd", 500_000)
        if panel_issue_count <= tier_break:
            panel_fee = panel_issue_count * base_fee
        else:
            panel_fee = (tier_break * base_fee) + ((panel_issue_count - tier_break) * extended_fee)
        global_state["corporate_treasury"] -= panel_fee
        global_state["stakeholder_panel_fee_paid"] = panel_fee
        global_state["stakeholder_panel_issues_rated"] = panel_issue_count

    # ── CFO Override Validation (Strict) ──────────────────────────────────────
    q1_submission = set(body.matrix_submission.quadrant_1_top_right)
    invalid_q1_issues = q1_submission - q1_target_issue_ids

    if invalid_q1_issues:
        if body.force_override_cfo:
            # Executive override: penalize reputation (−10, doubled from −5 to reflect governance gravity)
            global_state["group_reputation"] = max(0, global_state.get("group_reputation", 50) - 10)
            global_state["cfo_override_used_r2"] = True
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "CFO Override: Proposed initiatives include non-material or low-impact issues. "
                    "Budget allocation denied per Double Materiality framework. "
                    "Review your Quadrant 1 classification and resubmit."
                )
            )

    # ── Accuracy Scoring & Capital Release ────────────────────────────────────
    if not q1_target_issue_ids:
        m_acc = 1.0
    else:
        correct_q1_count = len(q1_submission.intersection(q1_target_issue_ids))
        m_acc = correct_q1_count / len(q1_target_issue_ids)

    allocated_budget = int(total_budget * m_acc)

    # ── Option C Budget Clawback ───────────────────────────────────────────────
    # If player chose Option C (Ignore Materiality Framework), the A/B/C governance
    # decision retroactively reduces the materiality capital unlocked.
    # This couples governance posture to materiality outcome.
    from round_configs import get_round_options
    r2_opts = get_round_options(2)
    r2_choice = global_state.get("r2_governance_choice", None)
    clawback_applied = 0
    if r2_choice == "option_c":
        clawback_pct = r2_opts.get("option_c", {}).get("budget_clawback_pct", 0.40)
        clawback_applied = int(allocated_budget * clawback_pct)
        allocated_budget -= clawback_applied
        global_state["r2_budget_clawback"] = clawback_applied
        global_state["r2_budget_clawback_message"] = (
            f"⚠️ CFO Governance Review: Option C (Ignore Framework) triggered a "
            f"${clawback_applied:,} ({int(clawback_pct*100)}%) clawback on your materiality budget. "
            f"Governance posture must be consistent with capital allocation rationale."
        )

    # ── Full-Quadrant Accuracy Bonus ──────────────────────────────────────────
    def _correct_quadrant(issue):
        h_fin = issue["financial_impact"] == "high"
        h_imp = issue["societal_impact"] == "high"
        if h_fin and h_imp: return "q1"
        if not h_fin and h_imp: return "q2"
        if h_fin and not h_imp: return "q3"
        return "q4"

    issue_lookup = {i["id"]: i for i in all_issues}
    total_placed = 0
    correct_placed = 0
    q2_disclosure_correct = 0
    for qname in ("q1", "q2", "q3", "q4"):
        submission_attr = {
            "q1": "quadrant_1_top_right",
            "q2": "quadrant_2_top_left",
            "q3": "quadrant_3_bottom_right",
            "q4": "quadrant_4_bottom_left",
        }[qname]
        placed_ids = getattr(body.matrix_submission, submission_attr, [])
        for iid in placed_ids:
            issue = issue_lookup.get(iid)
            if not issue:
                continue  # custom factor — skip accuracy check
            total_placed += 1
            if _correct_quadrant(issue) == qname:
                correct_placed += 1
                # Count correctly placed Q2 disclosure issues
                if qname == "q2" and issue.get("disclosure_required"):
                    q2_disclosure_correct += 1

    full_accuracy = (correct_placed / total_placed) if total_placed > 0 else 0
    accuracy_bonus = 0
    if full_accuracy >= 0.80:
        accuracy_bonus = 1000
        global_state["bonus_score"] = global_state.get("bonus_score", 0) + accuracy_bonus

    global_state["materiality_full_accuracy"] = round(full_accuracy * 100, 1)

    # ── Q2 Disclosure Investment Budget ───────────────────────────────────────
    # Players who correctly placed Q2 issues receive the disclosure_investment_budget
    # to cover data collection, assurance, and stakeholder engagement costs.
    # This teaches: impact materiality requires disclosure investment, not capex.
    disclosure_allocated = 0
    if q2_disclosure_correct > 0:
        # Pro-rata: each correct Q2 issue unlocks a portion of disclosure budget
        from round2_csrd import Q2_DISCLOSURE_ISSUES
        max_q2 = max(len(Q2_DISCLOSURE_ISSUES), 1)
        disclosure_allocated = int(disclosure_budget * (q2_disclosure_correct / max_q2))
        global_state["q2_disclosure_budget_unlocked"] = disclosure_allocated
        global_state["q2_disclosure_message"] = (
            f"📋 ESRS Disclosure Budget: {q2_disclosure_correct} Q2 impact-material issues correctly "
            f"identified. ${disclosure_allocated:,} disclosure investment budget unlocked for "
            f"data collection, assurance, and stakeholder engagement (ESRS S1/S2/E1-E5)."
        )

    # Deduct allocation from treasury
    global_state["corporate_treasury"] -= allocated_budget
    global_state["materiality_budget_allocated"] = list(q1_submission)

    # Store BU context if applicable
    if body.bu_id:
        global_state["materiality_bu_id"] = body.bu_id

    # Unlock the module gate
    global_state["csrd_completed"] = True

    # ── Set materiality_aligned / materiality_ignored flags ────────────────────
    # These are read by:
    #   - _post_r10_grand_finale  → +0.10 M_R bonus for materiality_aligned
    #   - _post_r3_scope3         → Green Bond pricing (-$500K / +$1M)
    # Aligned = ≥80% Q1 accuracy AND did not choose Option C governance posture
    r2_gov = global_state.get("r2_governance_choice", "")
    is_aligned = (full_accuracy >= 0.80) and (r2_gov != "option_c")
    flags = global_state.setdefault("active_event_flags", {})
    if is_aligned:
        flags["materiality_aligned"] = True
        flags.pop("materiality_ignored", None)
        global_state["materiality_status"] = "aligned"
    else:
        flags["materiality_ignored"] = True
        flags.pop("materiality_aligned", None)
        global_state["materiality_status"] = "ignored"

    # ── ESRS Debrief Card ─────────────────────────────────────────────────────
    # Post-submission regulatory literacy card explaining the scoring rationale.
    q1_correct_ids = list(q1_submission.intersection(q1_target_issue_ids))
    q1_missed_ids = list(q1_target_issue_ids - q1_submission)
    global_state["r2_esrs_debrief"] = {
        "esrs_reference": "ESRS 1 §1.51-1.61 — Impact Materiality Threshold",
        "q1_correct": q1_correct_ids,
        "q1_missed": q1_missed_ids,
        "scoring_rationale": (
            "Under ESRS 1, issues are doubly material if they meet BOTH: "
            "(a) financial materiality threshold (enterprise value impact) AND "
            "(b) impact materiality threshold (severity × scale × irremediability). "
            f"Your Q1 recall: {len(q1_correct_ids)}/{len(q1_target_issue_ids)} issues correctly prioritised."
        ),
        "q2_insight": (
            "Q2 issues (High Impact / Low Financial) are not capital-intensive, but "
            "ESRS S1, S2, and E1-E5 require mandatory disclosure. They require "
            "disclosure investment (data collection, assurance) — not silence."
        ),
        "spectrum_note": (
            "Note: ESRS 1 does not use binary High/Low classification. Real-world "
            "assessment requires continuous severity/likelihood/time-horizon weighting. "
            "This simulation uses a simplified 2×2 matrix — real practice is more granular."
        ),
        "time_horizon_note": (
            "Time horizons matter: Scope 3 Carbon is long-term but compounds; "
            "Water Scarcity is short-term and irreversible. Both are Q1 — but "
            "sequencing and prioritisation differ in your ESRS transition plan."
        ),
        "full_accuracy_pct": round(full_accuracy * 100, 1),
        "q2_disclosure_allocated": disclosure_allocated,
        "clawback_applied": clawback_applied,
    }

    # Persist the updated treasury back to the database for this round
    await db.update_latest_global_state(session_id, global_state, bu_states)

    msg_parts = [f"Materiality Matrix accepted. Accuracy: {round(full_accuracy*100)}%."]
    if accuracy_bonus:
        msg_parts.append("+1000 bonus points!")
    if clawback_applied:
        msg_parts.append(f"Option C clawback: −${clawback_applied:,}.")
    if disclosure_allocated:
        msg_parts.append(f"Q2 disclosure budget: +${disclosure_allocated:,}.")

    return MaterialitySubmissionResponse(
        success=True,
        allocated_budget=allocated_budget,
        corporate_treasury=global_state["corporate_treasury"],
        message=" ".join(msg_parts),
        debrief=global_state["r2_esrs_debrief"],
    )


def _collect_flags_from_state(flags_dict: dict) -> set:
    """Thin helper to collect flag names from the active_event_flags dict."""
    result = set()
    for key, val in flags_dict.items():
        if isinstance(val, list):
            result.update(str(v) for v in val)
        elif isinstance(val, bool) and val:
            result.add(key)
        elif isinstance(val, str):
            result.add(val)
    return result




# ─────────────────────────────────────────────────────────────────
# Stakeholder Power-Interest Grid (Round 1 Minigame)
# ─────────────────────────────────────────────────────────────────

from stakeholder_map import evaluate_stakeholder_map, get_stakeholder_list, get_master_config, evaluate_stakeholder_map_for_session, get_stakeholders_for_session


class StakeholderMapSubmission(BaseModel):
    """Player's mapping of stakeholder IDs to quadrant IDs."""
    mapping: dict[str, str]  # {stakeholder_id: quadrant_id}


@router.get(
    "/stakeholder-map/stakeholders",
    tags=["Simulation"],
    summary="Get stakeholder list for the drag-and-drop bank",
)
async def get_stakeholders(session_id: str = None):
    """Returns the stakeholder bank. If session_id is provided and has
    BU substitutions, returns the vertical-specific stakeholder set."""
    if session_id:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            gs = latest["global_state"]
            stakeholders = get_stakeholders_for_session(gs)
            return {"stakeholders": [
                {
                    "id": s["id"], "name": s["name"], "icon": s["icon"],
                    "description": s["description"],
                    "intel_dossier": s.get("intel_dossier", []),
                }
                for s in stakeholders
            ]}
    return {"stakeholders": get_stakeholder_list()}


@router.post(
    "/{session_id}/stakeholder-map",
    tags=["Simulation"],
    summary="Submit stakeholder power-interest grid mapping",
)
async def submit_stakeholder_map(session_id: str, body: StakeholderMapSubmission):
    # Evaluate against master (C4: graduated scoring, C12: treasury penalty)
    # Session-aware: uses vertical stakeholders if BU substitutions are active
    latest_for_eval = await db.fetch_latest_state(session_id)
    if latest_for_eval:
        result = evaluate_stakeholder_map_for_session(
            body.mapping, latest_for_eval["global_state"]
        )
    else:
        result = evaluate_stakeholder_map(body.mapping)

    latest = await db.fetch_latest_state(session_id)
    if latest:
        gs = latest["global_state"]
        gs["bonus_score"] = gs.get("bonus_score", 0) + result["points_awarded"]
        gs["stakeholder_map_completed"] = True
        gs["stakeholder_map_accuracy"] = result["accuracy_percentage"]
        # C18: Persist per-stakeholder accuracy for R2 Voice Boost
        gs["stakeholder_accuracy"] = body.mapping  # {stakeholder_id: quadrant_id}
        # C12: Treasury penalty for poor analysis (<60%)
        if result.get("treasury_penalty", 0) != 0:
            gs["corporate_treasury"] = gs.get("corporate_treasury", 0) + result["treasury_penalty"]
            gs["stakeholder_penalty_applied"] = result["treasury_penalty"]
        # C4: Reputation penalty for failing (<80%)
        if result.get("reputation_penalty", 0) != 0:
            gs["group_reputation"] = max(0, gs.get("group_reputation", 50) + result["reputation_penalty"])
        await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    return {
        "accuracy_percentage": result["accuracy_percentage"],
        "passed": result["passed"],
        "points_awarded": result["points_awarded"],
        "correct_count": result["correct_count"],
        "total_count": result["total_count"],
        "details": result["details"],
        "master_mapping": result["master_mapping"],
        "treasury_penalty": result.get("treasury_penalty", 0),
        "reputation_penalty": result.get("reputation_penalty", 0),
        "scoring_tier": result.get("scoring_tier", ""),
        "urgency_debrief": result.get("urgency_debrief", []),
        "engagement_tactics": result.get("engagement_tactics", []),
    }


@router.get(
    "/stakeholder-map/master",
    tags=["Admin"],
    summary="God Mode: Get full master stakeholder config",
)
async def get_stakeholder_master():
    return get_master_config()


# ─────────────────────────────────────────────────────────────────
# Player Password Change
# ─────────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    player_id: str
    old_password: str
    new_password: str

@router.post(
    "/api/simulations/change-password",
    tags=["Simulation"],
    summary="Allow a player to change their password",
)
async def change_password(body: ChangePasswordRequest):
    try:
        from admin_shared import _player_registry
    except ImportError:
        raise HTTPException(500, "Player registry not available")

    player = next((p for p in _player_registry if p["player_id"] == body.player_id), None)
    if not player:
        raise HTTPException(404, "Player ID not found")

    if player.get("password") != body.old_password:
        raise HTTPException(403, "Current password is incorrect")

    if len(body.new_password.strip()) < 3:
        raise HTTPException(400, "New password must be at least 3 characters")

    player["password"] = body.new_password.strip()
    return {"status": "success", "message": "Password updated successfully"}


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/learning-bonus  — Award points
# ─────────────────────────────────────────────────────────────────

class LearningBonusRequest(BaseModel):
    activity_type: str  # "podcast_complete" | "quiz_complete"
    notebook_id: str
    score_percent: int = 0  # Only for quiz_complete

@router.post(
    "/{session_id}/learning-bonus",
    summary="Award bonus points for completing podcast or quiz",
)
async def award_learning_bonus(session_id: str, body: LearningBonusRequest):
    """
    Awards bonus points:
    - podcast_complete: 1000 pts (one-time only)
    - quiz_complete: 60-80% = 1500, 80-90% = 2000, 90-100% = 3000
      Retakes allowed — only the *incremental* improvement is awarded.
    Tracks attempt count so frontend can reveal answers after attempt 2.
    """
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    gs = latest["global_state"]
    bu_states = latest["bu_states"]

    awarded_key = "learning_bonuses_awarded"
    awarded = gs.get(awarded_key, {})
    claim_key = f"{body.activity_type}_{body.notebook_id}"

    def _quiz_points(pct: int) -> int:
        if pct >= 90: return 3000
        if pct >= 80: return 2000
        if pct >= 60: return 1500
        return 0

    # ── Podcast: one-time 1000 pts ─────────────────────────────
    if body.activity_type == "podcast_complete":
        if claim_key in awarded:
            return {
                "status": "already_claimed",
                "points_awarded": 0,
                "bonus_score": gs.get("bonus_score", 0),
                "message": "Podcast bonus already claimed.",
                "attempt": awarded[claim_key].get("attempt", 1),
            }
        points = 1000
        gs["bonus_score"] = gs.get("bonus_score", 0) + points
        awarded[claim_key] = {"points": points, "attempt": 1}
        gs[awarded_key] = awarded
        await db.update_latest_global_state(session_id, gs, bu_states)
        return {
            "status": "success",
            "points_awarded": points,
            "bonus_score": gs["bonus_score"],
            "message": f"+{points} bonus points!",
            "attempt": 1,
        }

    # ── Quiz: max 2 attempts, higher score kept ────────────────
    new_points = _quiz_points(body.score_percent)
    prev = awarded.get(claim_key, {})
    prev_points = prev.get("points", 0)
    prev_attempt = prev.get("attempt", 0)
    current_attempt = prev_attempt + 1

    MAX_QUIZ_ATTEMPTS = 2

    if prev_attempt >= MAX_QUIZ_ATTEMPTS:
        return {
            "status": "max_attempts_reached",
            "points_awarded": 0,
            "total_earned": prev_points,
            "bonus_score": gs.get("bonus_score", 0),
            "message": f"Maximum {MAX_QUIZ_ATTEMPTS} attempts reached. Your best score: {prev.get('best_score_percent', 0)}% ({prev_points} pts).",
            "attempt": prev_attempt,
            "max_attempts": MAX_QUIZ_ATTEMPTS,
            "show_answers": True,
        }

    incremental = max(0, new_points - prev_points)

    if incremental > 0:
        gs["bonus_score"] = gs.get("bonus_score", 0) + incremental

    awarded[claim_key] = {
        "points": max(new_points, prev_points),
        "score_percent": body.score_percent,
        "attempt": current_attempt,
        "best_score_percent": max(body.score_percent, prev.get("best_score_percent", 0)),
    }
    gs[awarded_key] = awarded
    await db.update_latest_global_state(session_id, gs, bu_states)

    attempts_remaining = MAX_QUIZ_ATTEMPTS - current_attempt

    if incremental > 0:
        msg = f"+{incremental} bonus points! (improved from {prev_points} → {max(new_points, prev_points)})"
    elif new_points > 0:
        msg = f"Score: {body.score_percent}% — already at best tier ({prev_points} pts)."
    else:
        msg = "Score below 60% — no bonus this time."

    if attempts_remaining > 0:
        msg += f" {attempts_remaining} retake{'s' if attempts_remaining > 1 else ''} remaining."
    else:
        msg += " No more retakes available."

    return {
        "status": "success",
        "points_awarded": incremental,
        "total_earned": max(new_points, prev_points),
        "bonus_score": gs.get("bonus_score", 0),
        "message": msg,
        "attempt": current_attempt,
        "max_attempts": MAX_QUIZ_ATTEMPTS,
        "attempts_remaining": attempts_remaining,
        "show_answers": current_attempt >= MAX_QUIZ_ATTEMPTS,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/quiz/{notebook_id}  — Generate random quiz
# ─────────────────────────────────────────────────────────────────

import random as _random

@router.get(
    "/quiz/{notebook_id}",
    summary="Get 10 random quiz questions for a notebook, filtered by difficulty",
)
async def get_quiz_questions(notebook_id: str):
    """
    Returns 10 randomly selected questions from the notebook's question bank.
    Questions are filtered by the facilitator's current difficulty setting.
    Falls back to all difficulties if not enough at the target level.
    Question and option order are shuffled for each request.
    """
    from admin_resources import _notebooklm_notebooks, _quiz_difficulty

    nb = next((n for n in _notebooklm_notebooks if n["id"] == notebook_id), None)
    if not nb:
        raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found.")

    all_questions = nb.get("quiz_questions", [])
    if not all_questions:
        raise HTTPException(status_code=404, detail="No quiz questions available for this notebook.")

    # Filter by difficulty
    filtered = [q for q in all_questions if q.get("difficulty") == _quiz_difficulty]

    # Fallback: if fewer than 10 at target difficulty, supplement from other levels
    if len(filtered) < 10:
        remaining = [q for q in all_questions if q not in filtered]
        _random.shuffle(remaining)
        filtered.extend(remaining[:10 - len(filtered)])

    # Select 10 random questions
    _random.shuffle(filtered)
    selected = filtered[:10]

    # Shuffle option order for each question (adjusting correct index)
    result = []
    for q in selected:
        options = list(q["options"])
        correct_text = options[q["correct"]]
        _random.shuffle(options)
        new_correct = options.index(correct_text)
        result.append({
            "question": q["question"],
            "options": options,
            "correct": new_correct,
            "explanation": q["explanation"],
            "difficulty": q.get("difficulty", "medium"),
        })

    return {
        "notebook_id": notebook_id,
        "difficulty": _quiz_difficulty,
        "question_count": len(result),
        "questions": result,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/resources  — Player-facing
# ─────────────────────────────────────────────────────────────────


@router.get(
    "/{session_id}/resources",
    summary="Get unlocked resources for a player session",
)
async def get_player_resources(session_id: str):
    """
    Returns resources available to the player:
    1. Standard resources whose facilitator_default_round <= current round (auto-available)
    2. Explicitly unlocked resources (facilitator-unlocked or hidden resources unlocked by triggers)
    Splits them into 'new_this_round' and 'archive'.
    """
    from admin_resources import _resource_library, _session_resource_state, _notebooklm_notebooks, _quiz_enabled

    # Get current round
    latest = await db.fetch_latest_state(session_id)
    current_round = latest["round_number"] if latest else 1

    # Also check parent cohort for unlocked resources
    session_info = await db.get_session_info(session_id)
    parent_id = session_info.get("parent_cohort_id") if session_info else None

    # Quiz enabled check — check session and parent cohort
    quiz_enabled = _quiz_enabled.get(session_id, True)
    if parent_id:
        quiz_enabled = _quiz_enabled.get(parent_id, quiz_enabled)

    unlocked = _session_resource_state.get(session_id, [])
    if parent_id:
        unlocked = unlocked + _session_resource_state.get(parent_id, [])
    unlocked_ids = {u["resource_id"]: u for u in unlocked}

    seen_ids = set()
    new_this_round = []
    archive = []

    for res in _resource_library:
        rid = res["id"]
        if rid in seen_ids:
            continue

        visibility = res.get("visibility", "Standard")
        default_round = res.get("facilitator_default_round")

        # Explicitly unlocked resources (hidden or manual)
        if rid in unlocked_ids:
            seen_ids.add(rid)
            unlock_info = unlocked_ids[rid]
            enriched = {
                **res,
                "unlocked_at_round": unlock_info["unlocked_at_round"],
                "unlocked_at_time": unlock_info["unlocked_at_time"],
                "is_strategic_drop": unlock_info.get("is_strategic_drop", False),
                "trigger": unlock_info.get("trigger", "manual"),
            }
            if unlock_info["unlocked_at_round"] == current_round:
                new_this_round.append(enriched)
            else:
                archive.append(enriched)
            continue

        # Standard resources auto-available at their designated round
        if visibility == "Standard" and default_round is not None and default_round <= current_round:
            seen_ids.add(rid)
            enriched = {
                **res,
                "unlocked_at_round": default_round,
                "unlocked_at_time": None,
                "is_strategic_drop": False,
                "trigger": "auto_round",
            }
            if default_round == current_round:
                new_this_round.append(enriched)
            else:
                archive.append(enriched)

    # Filter NotebookLM notebooks available for current round
    notebooklm_available = [
        nb for nb in _notebooklm_notebooks
        if nb.get("target_round", 1) <= current_round
    ]

    return {
        "current_round": current_round,
        "new_this_round": new_this_round,
        "archive": archive,
        "total_unlocked": len(new_this_round) + len(archive),
        "notebooklm_notebooks": notebooklm_available,
        "quiz_enabled": quiz_enabled,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/peer-leaderboard
# ─────────────────────────────────────────────────────────────────

TEAM_NAMES = [
    "Team Alpha", "Team Bravo", "Team Charlie", "Team Delta",
    "Team Echo", "Team Foxtrot", "Team Golf", "Team Hotel",
    "Team India", "Team Juliet", "Team Kilo", "Team Lima",
]

@router.get(
    "/{session_id}/peer-leaderboard",
    summary="Get anonymized peer leaderboard for a player session",
)
async def get_peer_leaderboard(session_id: str):
    """
    Returns an anonymized leaderboard of all players in the same cohort.
    The requesting player is highlighted with isYou=True.
    For solo/demo sessions, generates AI benchmark players for comparison.
    """
    # Get session info to find parent cohort
    session_info = await db.get_session_info(session_id)
    if not session_info:
        return {"leaderboard": [], "message": "Session not found"}

    parent_id = session_info.get("parent_cohort_id")

    # ── Solo session: Generate AI benchmark players ──────────────
    if not parent_id:
        latest = await db.fetch_latest_state(session_id)
        if not latest:
            return {"leaderboard": [], "message": "No simulation data yet"}
        gs = latest["global_state"]
        player_treasury = float(gs.get("corporate_treasury", 25_000_000))
        player_rep = float(gs.get("group_reputation", 50))
        player_round = gs.get("round_number", 1)
        player_carbon = int(gs.get("tco2e_emissions", 0))
        player_synergy = float(gs.get("synergy_multiplier", 1.0))
        player_bonus = gs.get("bonus_score", 0)
        player_name = session_info.get("player_name", "Your Team") if session_info else "Your Team"

        import random as _rng
        # Seed with session_id hash so AI players are consistent across refreshes
        seed = hash(session_id) & 0xFFFFFFFF
        _rng.seed(seed + player_round)

        # Generate 3 AI benchmark players with varied strategies
        ai_profiles = [
            {"name": "🤖 AI Strategist (Balanced)", "treasury_mult": 1.08, "rep_mult": 0.95, "carbon_mult": 0.85, "synergy_mult": 1.05},
            {"name": "🤖 AI Optimizer (Growth)", "treasury_mult": 1.20, "rep_mult": 0.80, "carbon_mult": 1.15, "synergy_mult": 0.90},
            {"name": "🤖 AI Guardian (ESG)", "treasury_mult": 0.85, "rep_mult": 1.15, "carbon_mult": 0.70, "synergy_mult": 1.10},
        ]

        leaderboard = []
        # Add player first
        leaderboard.append({
            "rank": 0,
            "name": player_name or "Your Team",
            "treasury": player_treasury,
            "reputation": player_rep,
            "co2": player_carbon,
            "bonus_score": player_bonus,
            "trend": "→",
            "isYou": True,
        })

        for prof in ai_profiles:
            noise_t = _rng.uniform(-0.05, 0.05)
            noise_r = _rng.uniform(-3, 3)
            ai_treasury = round(player_treasury * prof["treasury_mult"] + noise_t * player_treasury, 2)
            ai_rep = round(min(100, max(5, player_rep * prof["rep_mult"] + noise_r)), 1)
            ai_carbon = max(0, int(player_carbon * prof["carbon_mult"] + _rng.randint(-50, 50)))
            ai_bonus = max(0, player_bonus + _rng.randint(-500, 500))

            leaderboard.append({
                "rank": 0,
                "name": prof["name"],
                "treasury": ai_treasury,
                "reputation": ai_rep,
                "co2": ai_carbon,
                "bonus_score": ai_bonus,
                "trend": _rng.choice(["↑", "→", "↓"]),
                "isYou": False,
                "isAI": True,
            })

        # Sort by treasury descending and assign ranks
        leaderboard.sort(key=lambda x: x["treasury"], reverse=True)
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return {"leaderboard": leaderboard, "ai_benchmark": True}

    # ── Multiplayer: Real peer leaderboard ──────────────────────
    # Find all sibling sessions (same parent)
    try:
        from database_memory import _sessions, _global_states
    except ImportError:
        return {"leaderboard": [], "message": "Peer comparison unavailable"}

    siblings = []
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_id:
            latest_states = _global_states.get(sid, [])
            if latest_states:
                gs = latest_states[-1]
                siblings.append({
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "treasury": float(gs.get("corporate_treasury", 0)),
                    "reputation": float(gs.get("group_reputation", 50)),
                    "carbon": int(gs.get("tco2e_emissions", 0)),
                    "bonus_score": gs.get("bonus_score", 0),
                    "round_number": gs.get("round_number", 1),
                    "synergy": float(gs.get("synergy_multiplier", 1.0)),
                    "stakeholder_accuracy": gs.get("stakeholder_map_accuracy", None),  # C21
                })

    # Sort by treasury descending
    siblings.sort(key=lambda x: x["treasury"], reverse=True)

    # Anonymize and mark current player
    leaderboard = []
    for i, s in enumerate(siblings):
        team_name = TEAM_NAMES[i] if i < len(TEAM_NAMES) else f"Team {i + 1}"
        is_you = s["session_id"] == session_id

        # Determine trend based on round number
        trend = "→"
        if s["round_number"] > 1:
            prev_states = _global_states.get(s["session_id"], [])
            if len(prev_states) >= 2:
                prev_treasury = float(prev_states[-2].get("corporate_treasury", 0))
                if s["treasury"] > prev_treasury:
                    trend = "↑"
                elif s["treasury"] < prev_treasury:
                    trend = "↓"

        entry = {
            "rank": i + 1,
            "name": s.get("player_name") or ("Your Team" if is_you else team_name),
            "treasury": s["treasury"],
            "reputation": s["reputation"],
            "co2": s["carbon"],
            "bonus_score": s["bonus_score"],
            "trend": trend,
            "isYou": is_you,
        }
        leaderboard.append(entry)

    return {"leaderboard": leaderboard}


# ═════════════════════════════════════════════════════════════════
#  SIDE TRACK ENDPOINTS (Player-Facing)
#  Sequential model: main sim pauses while side track is active.
#  Full process_tick() engine used for side track rounds.
# ═════════════════════════════════════════════════════════════════

def _get_active_side_track_for_session(session_id: str) -> tuple[str | None, dict | None]:
    """
    Check if a session (or its parent cohort) has an active, incomplete side track.
    Returns (track_id, track_state) if a side track is blocking main sim progression,
    or (None, None) if no side track is active.
    """
    from database_memory import _sessions
    sess = _sessions.get(session_id)
    if not sess:
        return None, None

    # Check parent cohort if this is a player sub-session
    parent_id = sess.get("parent_cohort_id")
    if parent_id:
        parent = _sessions.get(parent_id)
        if parent:
            sess = parent

    active_tracks = sess.get("active_side_tracks", [])
    if not active_tracks:
        return None, None

    states = sess.get("side_track_states", {})
    timing = sess.get("side_track_timing", {})

    # Get current main sim round
    from database_memory import _global_states
    player_states = _global_states.get(session_id, [])
    current_main_round = player_states[-1]["round_number"] if player_states else 1

    for tid in active_tracks:
        st = states.get(tid, {})
        if st.get("completed"):
            continue

        # Check timing: has the unlock round been reached?
        track_timing = timing.get(tid, {})
        unlock_after = track_timing.get("unlock_after_round", 0)
        if current_main_round <= unlock_after:
            continue

        # This track is active, unlocked, and not completed — it blocks main sim
        if st.get("current_round", 0) > 0 or current_main_round > unlock_after:
            return tid, st

    return None, None


@router.get("/{session_id}/side-tracks", summary="Get active side tracks for this session")
async def get_session_side_tracks(session_id: str):
    """
    Returns all side tracks assigned to this session (via cohort),
    their current progress, and whether the main sim is blocked.
    """
    from database_memory import _sessions

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Resolve parent cohort for player sub-sessions
    parent_id = session.get("parent_cohort_id")
    cohort = _sessions.get(parent_id) if parent_id else session
    if not cohort:
        cohort = session

    active_tracks = cohort.get("active_side_tracks", [])
    timing = cohort.get("side_track_timing", {})

    # Use player-level side track states if they exist, otherwise cohort level
    states = session.get("side_track_states") or cohort.get("side_track_states", {})

    # Get current main sim round
    latest = await db.fetch_latest_state(session_id)
    current_main_round = latest["round_number"] if latest else 1

    from side_tracks import get_track
    tracks_out = []
    blocking_track_id = None

    for tid in active_tracks:
        track = get_track(tid)
        if not track:
            continue

        st = states.get(tid, {})
        track_timing = timing.get(tid, {})
        unlock_after = track_timing.get("unlock_after_round", 0)
        is_unlocked = current_main_round > unlock_after
        is_completed = st.get("completed", False)
        current_track_round = st.get("current_round", 0)

        # Determine if this track is blocking
        is_blocking = is_unlocked and not is_completed and current_track_round >= 0
        if is_blocking and not blocking_track_id:
            blocking_track_id = tid

        # Get round config for current round if in progress
        round_config = None
        if current_track_round > 0 and not is_completed:
            round_config = track.get_round_config(current_track_round)

        tracks_out.append({
            "track_id": tid,
            "display_name": track.display_name,
            "description": track.description,
            "icon": track.icon,
            "num_rounds": track.num_rounds,
            "current_round": current_track_round,
            "completed": is_completed,
            "is_unlocked": is_unlocked,
            "is_blocking": is_blocking,
            "unlock_after_round": unlock_after,
            "scoring_dimensions": track.scoring_dimensions,
            "track_state": st.get("state", {}),
            "round_config": round_config,
        })

    return {
        "session_id": session_id,
        "side_tracks": tracks_out,
        "main_sim_blocked": blocking_track_id is not None,
        "blocking_track_id": blocking_track_id,
        "current_main_round": current_main_round,
    }


class SideTrackCommitRequest(BaseModel):
    decisions: list[dict]
    crisis_severity: float = 40.0
    dividends_paid: float = 0.0
    imitation_decay_rate: float = 0.05


@router.post("/{session_id}/side-tracks/{track_id}/commit", summary="Commit a side track round")
async def commit_side_track_turn(session_id: str, track_id: str, body: SideTrackCommitRequest):
    """
    Processes one round of a side track using the FULL process_tick() engine.

    Flow:
      1. Resolve cohort & validate track is active/unlocked
      2. If round 0 (not started), seed from main state via data bridge
      3. Run pre_tick → process_tick → post_tick
      4. Persist track state
      5. If final round, write back to main sim via data bridge
      6. Return new track state
    """
    from database_memory import _sessions, _persist
    from side_tracks import get_track
    import copy

    # Resolve session & cohort
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    parent_id = session.get("parent_cohort_id")
    cohort = _sessions.get(parent_id) if parent_id else session
    if not cohort:
        cohort = session

    # Validate track
    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Side track '{track_id}' not found")

    active = cohort.get("active_side_tracks", [])
    if track_id not in active:
        raise HTTPException(status_code=403, detail=f"Side track '{track_id}' not assigned to this cohort")

    # Get or create player-level track states
    if "side_track_states" not in session:
        session["side_track_states"] = copy.deepcopy(cohort.get("side_track_states", {}))
    
    states = session["side_track_states"]
    if track_id not in states:
        states[track_id] = {
            "current_round": 0,
            "completed": False,
            "state": {},
            "bu_states": [],
            "round_history": [],
            "accumulated_flags": [],
        }

    track_data = states[track_id]
    if track_data.get("completed"):
        raise HTTPException(status_code=409, detail=f"Side track '{track_id}' already completed")

    # Check timing: is this track unlocked?
    timing = cohort.get("side_track_timing", {})
    track_timing = timing.get(track_id, {})
    unlock_after = track_timing.get("unlock_after_round", 0)

    latest_main = await db.fetch_latest_state(session_id)
    current_main_round = latest_main["round_number"] if latest_main else 1
    if current_main_round <= unlock_after:
        raise HTTPException(
            status_code=403,
            detail=f"Side track '{track_id}' unlocks after main Round {unlock_after}. Currently on Round {current_main_round}."
        )

    current_track_round = track_data.get("current_round", 0)

    # ── SEED: If round 0, initialize from main state ─────────
    if current_track_round == 0:
        main_global = latest_main["global_state"] if latest_main else {}
        main_bus = latest_main["bu_states"] if latest_main else []

        # Collect completed track states for cross-track dependencies
        completed_tracks = {}
        for tid, tst in states.items():
            if tst.get("completed") and tid != track_id:
                completed_tracks[tid] = tst.get("state", {})

        seed_state = track.seed_from_main_state(main_global, main_bus, completed_tracks)
        track_data["state"] = seed_state
        track_data["bu_states"] = copy.deepcopy(main_bus)
        current_track_round = 1
        track_data["current_round"] = 1

    # ── BUILD ENGINE INPUTS ──────────────────────────────────
    track_global = {
        "round_number": current_track_round,
        "corporate_treasury": track_data["state"].get("inherited_treasury", 50_000_000),
        "group_reputation": track_data["state"].get("inherited_reputation", 50.0),
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "active_event_flags": {
            f"side_track_{track_id}": True,
            **{f: True for f in track_data.get("accumulated_flags", [])},
        },
        "bonus_score": 0,
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "vrio_capabilities": {},
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "competitor_ebitda": 0,
    }

    # Merge persisted treasury/reputation if track has progressed past R1
    if current_track_round > 1:
        track_global["corporate_treasury"] = track_data["state"].get(
            "current_treasury", track_global["corporate_treasury"]
        )
        track_global["group_reputation"] = track_data["state"].get(
            "current_reputation", track_global["group_reputation"]
        )

    current_bus = copy.deepcopy(track_data.get("bu_states", []))
    decisions_raw = [d if isinstance(d, dict) else d.model_dump() for d in body.decisions]

    # ── PRE-TICK ─────────────────────────────────────────────
    pre_result = track.pre_tick(
        round_number=current_track_round,
        track_state=track_data["state"],
        bus=current_bus,
        decisions=decisions_raw,
        crisis_severity=body.crisis_severity,
    )
    effective_crisis = pre_result.get("crisis_severity", body.crisis_severity)
    pre_events = pre_result.get("pre_events", {})

    # ── PROCESS TICK (Full 8-formula engine) ──────────────────
    # Determine paradigm from session (side tracks use the same paradigm)
    session_info = await db.get_session_info(session_id)
    paradigm = (session_info or {}).get("decision_paradigm", "legacy_abc")

    tick_result = process_tick(
        current_global=track_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        dividends_paid=body.dividends_paid,
        crisis_severity=effective_crisis,
        imitation_decay_rate=body.imitation_decay_rate,
        decision_paradigm=paradigm,
    )

    new_global = tick_result["global_state"]
    new_bus = tick_result["bu_states"]
    events = tick_result["events"]
    events.update(pre_events)

    # ── POST-TICK (Track-specific) ───────────────────────────
    post_events = track.post_tick(
        round_number=current_track_round,
        global_state=new_global,
        bu_states=new_bus,
        decisions=decisions_raw,
        events=events,
        extra_events={},
        previous_flags={"accumulated_flags": track_data.get("accumulated_flags", [])},
    )
    events.update(post_events)

    # ── UPDATE TRACK STATE ───────────────────────────────────
    # Accumulate flags from the chosen option
    choice = track._get_primary_choice(decisions_raw)
    round_opts = track.get_round_options(current_track_round)
    opt = round_opts.get(choice, {})
    new_flags = opt.get("flags_set", [])
    track_data["accumulated_flags"] = list(
        set(track_data.get("accumulated_flags", []) + new_flags)
    )

    # Update custom track metrics from events
    for key, val in events.items():
        prefix = f"st_{track_id}_custom_"
        if key.startswith(prefix):
            metric_name = key[len(prefix):]
            if isinstance(val, (int, float)):
                current_val = track_data["state"].get(metric_name, 0)
                track_data["state"][metric_name] = round(current_val + val, 2)
            else:
                track_data["state"][metric_name] = val

    # Persist treasury & reputation
    track_data["state"]["current_treasury"] = new_global["corporate_treasury"]
    track_data["state"]["current_reputation"] = new_global["group_reputation"]

    # Store round snapshot in history
    track_data["round_history"].append({
        "round_number": current_track_round,
        "choice": choice,
        "events": events,
        "treasury_after": new_global["corporate_treasury"],
        "reputation_after": new_global["group_reputation"],
        "track_state_snapshot": copy.deepcopy(track_data["state"]),
    })

    track_data["bu_states"] = copy.deepcopy(new_bus)

    # ── CHECK COMPLETION ─────────────────────────────────────
    is_final = current_track_round >= track.num_rounds
    if is_final:
        track_data["completed"] = True
        track_data["current_round"] = current_track_round

        # Calculate final score
        score = track.calculate_score(track_data["state"])
        track_data["final_score"] = score

        # DATA BRIDGE (WRITE): merge flags into main sim
        main_state = await db.fetch_latest_state(session_id)
        if main_state:
            write_back = track.write_back_to_main(track_data["state"], main_state["global_state"])
            main_gs = main_state["global_state"]
            main_gs.setdefault("active_event_flags", {})
            main_gs["active_event_flags"].update(write_back)
            await db.update_latest_global_state(
                session_id=session_id,
                global_state=main_gs,
                bu_states=main_state["bu_states"],
            )
            events["write_back_flags"] = write_back
            events["side_track_completed"] = True
            events["side_track_score"] = score
    else:
        track_data["current_round"] = current_track_round + 1

    _persist()

    # ── BUILD RESPONSE ───────────────────────────────────────
    # Get next round config if not completed
    next_round_config = None
    if not is_final:
        next_round_config = track.get_round_config(current_track_round + 1)

    return {
        "session_id": session_id,
        "track_id": track_id,
        "round_completed": current_track_round,
        "next_round": None if is_final else current_track_round + 1,
        "is_final": is_final,
        "track_state": track_data["state"],
        "accumulated_flags": track_data["accumulated_flags"],
        "events": events,
        "next_round_config": next_round_config,
        "final_score": track_data.get("final_score"),
        "global_state": {
            "corporate_treasury": new_global["corporate_treasury"],
            "group_reputation": new_global["group_reputation"],
        },
    }


@router.get("/{session_id}/side-tracks/{track_id}/history", summary="Get side track round history")
async def get_side_track_history(session_id: str, track_id: str):
    """Returns the round-by-round history for a specific side track."""
    from database_memory import _sessions

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    states = session.get("side_track_states", {})
    track_data = states.get(track_id)
    if not track_data:
        # Try parent cohort
        parent_id = session.get("parent_cohort_id")
        if parent_id:
            parent = _sessions.get(parent_id)
            if parent:
                states = parent.get("side_track_states", {})
                track_data = states.get(track_id)

    if not track_data:
        raise HTTPException(status_code=404, detail=f"No data for side track '{track_id}'")

    return {
        "session_id": session_id,
        "track_id": track_id,
        "current_round": track_data.get("current_round", 0),
        "completed": track_data.get("completed", False),
        "round_history": track_data.get("round_history", []),
        "final_score": track_data.get("final_score"),
        "accumulated_flags": track_data.get("accumulated_flags", []),
    }


@router.get("/{session_id}/side-tracks/{track_id}/leaderboard", summary="Side track leaderboard")
async def get_side_track_leaderboard(session_id: str, track_id: str):
    """
    Returns the separate leaderboard for a side track across all players in the cohort.
    Scores are independent of the main simulation leaderboard.
    """
    from database_memory import _sessions
    from side_tracks import get_track

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Side track '{track_id}' not found")

    # Find parent cohort
    parent_id = session.get("parent_cohort_id")
    if not parent_id:
        parent_id = session_id  # Solo session

    # Collect all sibling sessions
    entries = []
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_id or sid == parent_id:
            st = sess.get("side_track_states", {}).get(track_id)
            if st and st.get("current_round", 0) > 0:
                score = st.get("final_score") or track.calculate_score(st.get("state", {}))
                entries.append({
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "total_score": score.get("total_score", 0),
                    "grade": score.get("grade", "?"),
                    "archetype": score.get("archetype", {}).get("title", ""),
                    "completed": st.get("completed", False),
                    "rounds_done": st.get("current_round", 0),
                    "num_rounds": track.num_rounds,
                    "is_you": sid == session_id,
                })

    entries.sort(key=lambda e: -e["total_score"])
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return {
        "track_id": track_id,
        "display_name": track.display_name,
        "leaderboard": entries,
    }


@router.get("/{session_id}/side-tracks/aggregate-leaderboard", summary="Cross-track aggregated leaderboard")
async def get_aggregate_side_track_leaderboard(session_id: str):
    """
    Returns an aggregated leaderboard across ALL completed side tracks.
    Each player gets a composite score (average of completed track scores)
    plus per-track breakdowns. Useful for facilitator debrief dashboards.
    """
    from database_memory import _sessions
    from side_tracks import get_all_tracks

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    all_tracks = get_all_tracks()
    parent_id = session.get("parent_cohort_id") or session_id

    # Collect all sibling sessions
    player_data: dict = {}  # session_id → {name, tracks: {track_id: score_dict}}
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_id or sid == parent_id:
            st_states = sess.get("side_track_states", {})
            if not st_states:
                continue

            tracks_done = {}
            for tid, track_obj in all_tracks.items():
                st = st_states.get(tid)
                if st and st.get("current_round", 0) > 0:
                    score = st.get("final_score") or track_obj.calculate_score(st.get("state", {}))
                    tracks_done[tid] = {
                        "total_score": score.get("total_score", 0),
                        "grade": score.get("grade", "?"),
                        "archetype": score.get("archetype", {}).get("title", ""),
                        "completed": st.get("completed", False),
                        "rounds_done": st.get("current_round", 0),
                        "num_rounds": track_obj.num_rounds,
                        "mr_bonus": score.get("total_score", 0),
                    }

            if tracks_done:
                player_data[sid] = {
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "tracks": tracks_done,
                    "is_you": sid == session_id,
                }

    # Calculate composite scores
    entries = []
    for sid, pd in player_data.items():
        track_scores = [t["total_score"] for t in pd["tracks"].values()]
        composite = round(sum(track_scores) / len(track_scores), 1) if track_scores else 0

        # Grade the composite
        if composite >= 85: grade = "A+"
        elif composite >= 75: grade = "A"
        elif composite >= 65: grade = "B"
        elif composite >= 50: grade = "C"
        elif composite >= 35: grade = "D"
        else: grade = "F"

        entries.append({
            "session_id": pd["session_id"],
            "player_id": pd["player_id"],
            "player_name": pd["player_name"],
            "composite_score": composite,
            "composite_grade": grade,
            "tracks_completed": sum(1 for t in pd["tracks"].values() if t["completed"]),
            "tracks_started": len(pd["tracks"]),
            "tracks_available": len(all_tracks),
            "track_details": pd["tracks"],
            "is_you": pd["is_you"],
        })

    entries.sort(key=lambda e: -e["composite_score"])
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return {
        "available_tracks": [
            {"track_id": tid, "display_name": t.display_name, "icon": t.icon, "num_rounds": t.num_rounds}
            for tid, t in all_tracks.items()
        ],
        "aggregate_leaderboard": entries,
    }


# ═════════════════════════════════════════════════════════════════
#  CEO INTERVIEW — Post-Game Competency Assessment
# ═════════════════════════════════════════════════════════════════

def _is_interview_allowed(latest: dict) -> bool:
    """Determine if the CEO interview is available for this session.
    Post-game (round > 10): always available.
    Pre-game: requires explicit ceo_interview_enabled flag or god-mode toggle."""
    from admin_shared import _god_mode_settings
    flags = latest.get("global_state", {}).get("active_event_flags", {})
    round_number = latest.get("round_number", 1)
    game_is_done = round_number > 10 or bool(flags.get("profile"))
    if game_is_done:
        return True
    # Pre-game: explicit per-cohort flag or god-mode toggle required
    return flags.get("ceo_interview_enabled", _god_mode_settings.get("ceo_interview_enabled", False))


@router.get("/{session_id}/ceo-interview/questions", summary="Get CEO interview questions")
async def get_interview_questions_endpoint(session_id: str):
    """Returns the interview questions for the post-game CEO assessment.
    Auto-enabled after game completion. Can also be enabled pre-game via facilitator settings."""
    from admin_shared import _god_mode_settings

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    if not _is_interview_allowed(latest):
        raise HTTPException(403, "CEO Interview is not enabled for this cohort. Enable via God Mode or facilitator settings.")

    flags = latest.get("global_state", {}).get("active_event_flags", {})

    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")

    # Per-cohort voice gender override
    voice_gender = flags.get(
        "ceo_interview_voice_gender",
        _god_mode_settings.get("ceo_interview_voice_gender", "female"),
    )

    from ceo_interview import get_interview_questions, get_ceo_persona, DIMENSIONS
    persona = get_ceo_persona(voice_gender)
    questions = get_interview_questions(
        ending_pathway=ending_pathway,
        question_count=_god_mode_settings.get("ceo_interview_question_count", 5),
        include_pathway_question=_god_mode_settings.get("ceo_interview_pathway_question", True),
    )

    return {
        "session_id": session_id,
        "questions": questions,
        "persona": persona,
        "dimensions": DIMENSIONS,
        "ending_pathway": ending_pathway,
    }


@router.post("/{session_id}/ceo-interview/assess", summary="Submit interview responses for assessment")
async def submit_interview_responses(session_id: str, body: dict):
    """Submit player responses for CEO interview assessment.
    Returns scored dimensions (spider diagram data) + narrative feedback."""
    from admin_shared import _god_mode_settings

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    if not _is_interview_allowed(latest):
        raise HTTPException(403, "CEO Interview is not enabled.")

    responses = body.get("responses", [])
    if not responses:
        raise HTTPException(400, "No responses provided")

    gs = latest.get("global_state", {})
    bus = latest.get("bu_states", [])
    flags = gs.get("active_event_flags", {})
    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")

    from ceo_interview import (
        get_interview_questions, calc_data_scores, blend_scores,
        generate_fallback_feedback, generate_score_rationale,
        get_ceo_persona, DIMENSIONS,
    )
    voice_gender = _god_mode_settings.get("ceo_interview_voice_gender", "female")
    persona = get_ceo_persona(voice_gender)

    questions = get_interview_questions(
        ending_pathway=ending_pathway,
        question_count=_god_mode_settings.get("ceo_interview_question_count", 5),
    )

    # Build the extra dict from R10 grand finale results
    # (should be in active_event_flags after commit)
    extra = {
        "regenerative_multiple": flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)),
        "terminal_value": flags.get("terminal_value", gs.get("terminal_value", 0)),
        "profile_title": flags.get("profile_title", gs.get("profile_title", "Unknown")),
    }

    # Step 1: Calculate data-derived scores
    data_scores = calc_data_scores(extra, gs, bus, flags)

    # Step 2: Try LLM-based response scoring, fall back to data-only
    response_scores = {}
    llm_feedback = None
    try:
        # TODO: Integrate with actual LLM API (GPT-4o / Claude)
        # For now, use data scores as both halves (with slight randomisation)
        import random
        for dim_id in data_scores:
            # Simulate response analysis: slight variance around data score
            base = data_scores[dim_id]
            noise = random.uniform(-1.0, 1.0)
            response_scores[dim_id] = round(min(10, max(1, base + noise)), 1)
    except Exception as e:
        print(f"[ceo-interview] LLM scoring failed: {e}")
        response_scores = dict(data_scores)

    # Step 3: Blend scores
    final_scores = blend_scores(data_scores, response_scores)

    # Step 4: Generate score rationale (per-dimension explanations)
    score_rationale = generate_score_rationale(data_scores, extra, gs, bus, flags)

    # Step 5: Generate narrative feedback
    feedback = llm_feedback or generate_fallback_feedback(final_scores, extra)

    # Step 6: Persist the assessment in session flags
    try:
        flags["ceo_interview_completed"] = True
        flags["ceo_interview_scores"] = final_scores
        flags["ceo_interview_data_scores"] = data_scores
        flags["ceo_interview_response_scores"] = response_scores
        flags["ceo_interview_score_rationale"] = score_rationale
        gs["active_event_flags"] = flags
        await db.update_latest_global_state(session_id, gs, bus)
    except Exception as e:
        print(f"[ceo-interview] Failed to persist assessment: {e}")

    return {
        "session_id": session_id,
        "dimensions": DIMENSIONS,
        "final_scores": final_scores,
        "data_scores": data_scores,
        "response_scores": response_scores,
        "score_rationale": score_rationale,
        "feedback": feedback,
        "persona": persona,
    }


@router.get("/{session_id}/ceo-interview/results", summary="Get stored interview results")
async def get_interview_results(session_id: str):
    """Retrieve previously completed CEO interview results."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    flags = latest.get("global_state", {}).get("active_event_flags", {})
    if not flags.get("ceo_interview_completed"):
        raise HTTPException(404, "No CEO interview results found for this session")

    from ceo_interview import get_ceo_persona, DIMENSIONS, generate_fallback_feedback, generate_score_rationale
    from admin_shared import _god_mode_settings as _gms
    voice_gender = _gms.get("ceo_interview_voice_gender", "female")
    persona = get_ceo_persona(voice_gender)

    final_scores = flags.get("ceo_interview_scores", {})
    extra = {
        "regenerative_multiple": flags.get("regenerative_multiple", 1.0),
        "terminal_value": flags.get("terminal_value", 0),
        "profile_title": flags.get("profile_title", "Unknown"),
    }

    # Retrieve or regenerate score rationale
    score_rationale = flags.get("ceo_interview_score_rationale")
    if not score_rationale:
        gs = latest.get("global_state", {})
        bus = latest.get("bu_states", [])
        data_scores = flags.get("ceo_interview_data_scores", {})
        score_rationale = generate_score_rationale(data_scores, extra, gs, bus, flags)

    return {
        "session_id": session_id,
        "dimensions": DIMENSIONS,
        "final_scores": final_scores,
        "data_scores": flags.get("ceo_interview_data_scores", {}),
        "response_scores": flags.get("ceo_interview_response_scores", {}),
        "score_rationale": score_rationale,
        "feedback": generate_fallback_feedback(final_scores, extra),
        "persona": persona,
        "completed": True,
    }


@router.post("/{session_id}/ceo-interview/tts", summary="Synthesize CEO voice audio")
async def synthesize_ceo_voice(session_id: str, body: dict):
    """Synthesize speech for a CEO interview text segment.
    
    Body: { "text": "...", "voice_id": "..." (optional) }
    Returns: { "audio_b64": "..." } — base64-encoded MP3
    """
    from admin_shared import _god_mode_settings
    tts_latest = await db.fetch_latest_state(session_id)
    if not tts_latest:
        raise HTTPException(404, "Session not found")
    if not _is_interview_allowed(tts_latest):
        raise HTTPException(403, "CEO Interview is not enabled.")

    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided")

    # Resolve voice from god-mode settings if not explicitly provided
    voice_id = body.get("voice_id")
    if not voice_id:
        from ceo_interview import get_ceo_persona
        voice_gender = _god_mode_settings.get("ceo_interview_voice_gender", "female")
        persona = get_ceo_persona(voice_gender)
        voice_id = persona.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM")

    from elevenlabs_tts import synthesize_speech
    audio_b64 = await synthesize_speech(text=text, voice_id=voice_id)

    if audio_b64 is None:
        raise HTTPException(503, "Voice synthesis unavailable. Check ElevenLabs API key.")

    return {
        "audio_b64": audio_b64,
        "voice_id": voice_id,
        "text_length": len(text),
    }


@router.get("/elevenlabs/status", summary="Check ElevenLabs API status")
async def elevenlabs_status():
    """Check if ElevenLabs API is available and return subscription info."""
    from elevenlabs_tts import check_api_status
    return await check_api_status()


# ─────────────────────────────────────────────────────────────────
# ENGAGEMENT 7.3: Industry Benchmarks
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/benchmarks", summary="ESG Industry Benchmarks comparison")
async def get_industry_benchmarks(session_id: str):
    """Compare simulation metrics against real FTSE 100 ESG benchmarks."""
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from benchmarks import get_benchmarks
    return get_benchmarks(current["bu_states"], current["global_state"])


# ─────────────────────────────────────────────────────────────────
# ENGAGEMENT 7.5: Peer Decision Reveal
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/peer-stats/{round_number}", summary="Aggregate peer decision stats")
async def get_peer_stats(session_id: str, round_number: int):
    """
    After all players commit a round, reveal aggregate statistics:
    choice distribution and average investment ratio.
    Only available for completed rounds.
    """
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find parent cohort
    parent_id = session_info.get("parent_cohort_id") or session_id
    children = await db.get_child_sessions(parent_id)
    if not children:
        return {"available": False, "reason": "No peer sessions found"}

    # Check all players have committed this round
    all_committed = True
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state and child_state.get("round_number", 1) <= round_number:
            all_committed = False
            break

    if not all_committed:
        return {"available": False, "reason": "Not all peers have committed this round yet"}

    # Aggregate decision data from logs
    decision_log = await db.get_decision_log(parent_id)
    round_decisions = [d for d in decision_log if d.get("round_number") == round_number]

    if not round_decisions:
        return {"available": False, "reason": "No decisions found for this round"}

    # Choice distribution
    choice_counts: dict[str, int] = {}
    total_capex = 0.0
    total_investment_ratio = 0.0
    decision_count = 0

    for dec in round_decisions:
        choice = dec.get("choice_selected", "")
        if choice:
            choice_counts[choice] = choice_counts.get(choice, 0) + 1
        total_capex += dec.get("capex_allocated", 0)
        total_investment_ratio += dec.get("investment_ratio", 0) if hasattr(dec, 'get') else 0
        decision_count += 1

    total_choices = sum(choice_counts.values()) or 1
    choice_distribution = {
        k: round(v / total_choices * 100, 1)
        for k, v in choice_counts.items()
    }

    return {
        "available": True,
        "round_number": round_number,
        "peer_count": len(children),
        "choice_distribution": choice_distribution,
        "most_popular_choice": max(choice_counts, key=choice_counts.get) if choice_counts else None,
        "avg_capex": round(total_capex / max(decision_count, 1), 2),
        "avg_investment_ratio": round(total_investment_ratio / max(decision_count, 1), 4),
        "total_decisions_logged": decision_count,
        "note": "Anonymised aggregate — individual player decisions are not revealed.",
    }


# ─────────────────────────────────────────────────────────────────
# ITEM 5: Cohort Pace Lock
# ─────────────────────────────────────────────────────────────────

@router.put("/{session_id}/pace-lock", summary="Set cohort pace lock")
async def set_pace_lock(session_id: str, body: dict):
    """Set the maximum round players can advance to. Facilitator control."""
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    max_round = body.get("max_round")
    if max_round is not None:
        if not isinstance(max_round, int) or max_round < 1 or max_round > 10:
            raise HTTPException(status_code=400, detail="max_round must be 1-10")
    session_info["max_round"] = max_round
    return {"session_id": session_id, "max_round": max_round}


# ─────────────────────────────────────────────────────────────────
# ITEM 19: Round Timer
# ─────────────────────────────────────────────────────────────────

@router.put("/{session_id}/round-timer", summary="Set round deadline")
async def set_round_timer(session_id: str, body: dict):
    """Set a deadline (Unix timestamp) for the current round. Auto-locks on expiry."""
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    deadline = body.get("deadline")  # Unix timestamp or null to clear
    session_info["round_deadline"] = deadline
    return {"session_id": session_id, "round_deadline": deadline}


# ─────────────────────────────────────────────────────────────────
# ITEM 24: Facilitator Commit Notifications
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/commit-notifications", summary="Get recent commit notifications")
async def get_commit_notifications(session_id: str):
    """Return recent player commit notifications for the facilitator dashboard."""
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    notifications = session_info.get("commit_notifications", [])
    return {
        "session_id": session_id,
        "notifications": notifications[-20:],  # Last 20
        "total": len(notifications),
    }


# ═══════════════════════════════════════════════════════════════
#  NEW ENGINE ENDPOINTS
#  API surface for the improvement modules implemented in Batch 1-3.
# ═══════════════════════════════════════════════════════════════

# ── SI-4: TCFD Scenario Analysis ──────────────────────────────

@router.get(
    "/{session_id}/tcfd-scenarios",
    summary="Run TCFD climate scenario analysis on current portfolio",
)
async def get_tcfd_scenarios(session_id: str, scenario_id: str = None):
    """
    Run TCFD-aligned climate scenario analysis.
    If scenario_id is provided, run that single scenario.
    Otherwise, run all three and return a comparison matrix.
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    bio_state = gs.get("biodiversity_state")

    from tcfd_scenarios import run_scenario_analysis, get_scenario_comparison

    if scenario_id:
        result = run_scenario_analysis(scenario_id, bus, gs, bio_state)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    else:
        return get_scenario_comparison(bus, gs, bio_state)


# ── SE-1: Board Governance — Vote on Resolution ──────────────

@router.post(
    "/{session_id}/board-vote",
    summary="Submit a board vote on a shareholder resolution",
)
async def board_vote(session_id: str, body: dict):
    """
    Vote on a pending shareholder resolution.
    Body: { "resolution_id": "...", "recommendation": "support" | "oppose" }
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    board = gs.get("board_governance")
    if not board:
        raise HTTPException(status_code=400, detail="Board governance not initialised")

    resolution_id = body.get("resolution_id")
    recommendation = body.get("recommendation", "support")

    from board_governance import simulate_board_vote, SHAREHOLDER_RESOLUTIONS

    resolution = next((r for r in SHAREHOLDER_RESOLUTIONS if r["id"] == resolution_id), None)
    if not resolution:
        raise HTTPException(status_code=404, detail=f"Resolution '{resolution_id}' not found")

    result = simulate_board_vote(board, resolution, recommendation, gs)

    # Apply impacts if passed
    if result["passed"]:
        impacts = result.get("impact", {})
        if "reputation" in impacts:
            gs["group_reputation"] = min(100, round(gs.get("group_reputation", 50) + impacts["reputation"], 2))
        if "esg_linked_compensation_pct" in impacts:
            board["esg_linked_compensation_pct"] = impacts["esg_linked_compensation_pct"]
        if "tnfd_level" in impacts:
            bio = gs.get("biodiversity_state", {})
            bio["tnfd_disclosure_level"] = impacts["tnfd_level"]

        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - result.get("cost", 0), 2)

    # Persist
    gs["board_governance"] = board
    await db.update_latest_global_state(session_id, gs, bus)

    return result


# ── SE-2: Supply Chain — Conduct Audit ────────────────────────

@router.post(
    "/{session_id}/supply-chain-audit",
    summary="Conduct a supply chain due diligence audit",
)
async def supply_chain_audit(session_id: str, body: dict):
    """
    Conduct a supply chain audit.
    Body: { "audit_depth": 1 | 2 | 3 }
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    sc = gs.get("supply_chain")
    if not sc:
        raise HTTPException(status_code=400, detail="Supply chain not initialised")

    audit_depth = body.get("audit_depth", 1)
    if audit_depth not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="audit_depth must be 1, 2, or 3")

    from supply_chain_network import conduct_supply_chain_audit

    result = conduct_supply_chain_audit(sc, audit_depth, gs)
    gs["supply_chain"] = sc
    await db.update_latest_global_state(session_id, gs, bus)

    return result


# ── SI-5: Org Politics — Coalition Check ──────────────────────

@router.post(
    "/{session_id}/coalition-check",
    summary="Check C-suite coalition support for a decision",
)
async def coalition_check(session_id: str, body: dict):
    """
    Check which C-suite members support or oppose a proposed decision.
    Body: { "decision_tags": ["cost_reduction", "science_based_targets"], "estimated_cost": 5000000 }
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    org = gs.get("org_politics")
    if not org:
        raise HTTPException(status_code=400, detail="Org politics not initialised")

    from org_politics import evaluate_csuite_support

    result = evaluate_csuite_support(
        org,
        body.get("decision_tags", []),
        body.get("estimated_cost", 0),
        gs,
    )
    return result


# ── Meadows Leverage Points — Full Session Analysis ──────────

@router.get(
    "/{session_id}/leverage-analysis",
    summary="Meadows leverage points analysis for debrief",
)
async def leverage_analysis(session_id: str):
    """
    Analyse the full session against Meadows' 12 Leverage Points.
    Best used post-game for debrief.
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]

    from meadows_leverage import (
        analyse_session_leverage_points,
        detect_archetypes,
        classify_learning_loop,
    )

    decision_history = gs.get("decision_history", [])
    leverage = analyse_session_leverage_points(decision_history, gs, bus)

    flags = gs.get("active_event_flags", {})
    archetypes = detect_archetypes(gs, bus, flags)

    mental_model_history = gs.get("mental_model_history", [])
    learning_loop = classify_learning_loop(mental_model_history, decision_history)

    return {
        "leverage_analysis": leverage,
        "system_archetypes": archetypes,
        "learning_loop_classification": learning_loop,
        "theory_reference": "Meadows, D. (2008). Thinking in Systems: A Primer.",
    }


# ── SE-8: Dynamic Cases ──────────────────────────────────────

@router.get(
    "/{session_id}/contextual-cases",
    summary="Get context-aware real-world case studies",
)
async def get_contextual_cases(session_id: str, max_cases: int = 3):
    """Return real-world case studies relevant to the player's current state."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    round_number = latest.get("round_number", 1)

    from dynamic_cases import select_contextual_cases

    cases = select_contextual_cases(gs, bus, round_number, max_cases=max_cases)
    return {"cases": cases, "round": round_number}


# ── SE-7: Regulatory Sandbox — Activate Regulation ───────────

@router.post(
    "/{session_id}/regulatory-sandbox/activate",
    summary="Activate a regulatory instrument in sandbox mode",
)
async def activate_regulation(session_id: str, body: dict):
    """
    Activate a regulation in the sandbox.
    Body: { "instrument_id": "carbon_tax", "parameters": {"rate_per_tonne": 75} }
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]

    from regulatory_sandbox import create_sandbox_state, activate_regulation as _activate, REGULATORY_INSTRUMENTS

    if "regulatory_sandbox" not in gs:
        gs["regulatory_sandbox"] = create_sandbox_state()
        gs["regulatory_sandbox"]["sandbox_mode"] = True

    sandbox = gs["regulatory_sandbox"]
    instrument_id = body.get("instrument_id")
    custom_params = body.get("parameters", {})
    round_number = latest.get("round_number", 1)

    result = _activate(sandbox, instrument_id, custom_params, round_number)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    gs["regulatory_sandbox"] = sandbox
    await db.update_latest_global_state(session_id, gs, bus)

    # Audit log — captured in GodModeAuditLog under 🧪 Sandbox filter
    try:
        from admin_router import _audit as _god_audit
        _god_audit(
            "regulatory_sandbox_activated",
            actor="facilitator",
            details={
                "session_id": session_id,
                "instrument_id": instrument_id,
                "parameters": custom_params,
                "round": round_number,
                "complexity_index": result.get("complexity_index"),
                "capture_risk": result.get("capture_risk"),
            },
        )
    except Exception:
        pass  # Non-critical — don't let audit failure break the activation

    return result



@router.get(
    "/{session_id}/regulatory-sandbox/instruments",
    summary="List available regulatory instruments",
)
async def list_instruments(session_id: str):
    """Return all available regulatory instruments and their parameters."""
    from regulatory_sandbox import REGULATORY_INSTRUMENTS
    return {"instruments": REGULATORY_INSTRUMENTS}


@router.get(
    "/{session_id}/regulatory-sandbox/exogenous-events",
    summary="List available exogenous crisis events",
)
async def list_exogenous_events(session_id: str):
    """Return all configurable exogenous events with trigger conditions."""
    from regulatory_sandbox import EXOGENOUS_EVENTS
    latest = await db.fetch_latest_state(session_id)
    sandbox = {}
    if latest:
        sandbox = latest["global_state"].get("regulatory_sandbox", {})
    events_out = []
    for eid, cfg in EXOGENOUS_EVENTS.items():
        fired_key = f"exogenous_{eid}_fired"
        events_out.append({
            "event_id": eid,
            "name": cfg["name"],
            "description": cfg["description"],
            "trigger_rounds": cfg["trigger_rounds"],
            "trigger_conditions": cfg["trigger_conditions"],
            "effects": cfg["effects"],
            "theory": cfg["theory"],
            "icon": cfg["icon"],
            "severity": cfg["severity"],
            "already_fired": sandbox.get(fired_key),
        })
    return {"exogenous_events": events_out}


@router.post(
    "/{session_id}/regulatory-sandbox/trigger-event",
    summary="God Mode: Force-trigger an exogenous crisis event",
)
async def trigger_exogenous(session_id: str, body: dict):
    """
    Facilitator God Mode — manually fire an exogenous event.
    Body: { "event_id": "carbon_minsky_moment" }
    Bypasses trigger conditions. Requires sandbox to be active.
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    round_number = latest.get("round_number", 1)

    from regulatory_sandbox import (
        create_sandbox_state, trigger_exogenous_event,
    )

    if "regulatory_sandbox" not in gs:
        gs["regulatory_sandbox"] = create_sandbox_state()
        gs["regulatory_sandbox"]["sandbox_mode"] = True

    sandbox = gs["regulatory_sandbox"]
    event_id = body.get("event_id")
    events = {}

    result = trigger_exogenous_event(
        event_id, sandbox, gs, bus, events, round_number
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    gs["regulatory_sandbox"] = sandbox
    await db.update_latest_global_state(session_id, gs, bus)

    # Audit log
    try:
        from admin_router import _audit as _god_audit
        _god_audit(
            "exogenous_event_triggered",
            actor="facilitator",
            details={
                "session_id": session_id,
                "event_id": event_id,
                "round": round_number,
                "result": result,
            },
        )
    except Exception:
        pass

    return result


# ── Biodiversity & Balance Sheet Data ─────────────────────────

@router.get(
    "/{session_id}/biodiversity",
    summary="Get biodiversity state and history",
)
async def get_biodiversity(session_id: str):
    """Return the current biodiversity state for the session."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    bio = latest["global_state"].get("biodiversity_state", {})
    return {"biodiversity": bio}


@router.get(
    "/{session_id}/balance-sheet",
    summary="Get balance sheet state and history",
)
async def get_balance_sheet(session_id: str):
    """Return the current balance sheet for the session.
    Auto-initializes from BU states if not yet created by engine tick."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    gs = latest["global_state"]
    bs = gs.get("balance_sheet")
    if not bs or not bs.get("total_assets"):
        # Initialize balance sheet from current BU states so dashboard shows data pre-commit
        try:
            from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
            bus = latest["bu_states"]
            bs = create_initial_balance_sheet(bus)
            # Sync cash from treasury
            bs["current_assets"]["cash_and_equivalents"] = gs.get("corporate_treasury", 0)
            # Run one tick to populate totals
            bs, _ = process_balance_sheet_tick(
                bs, gs, bus,
                {"csf_this_round": 0, "total_capex_allocated": 0, "dividends_paid": 0,
                 "remediation_events": [], "tipping_tier": "none"},
                latest.get("round_number", 1),
            )
            gs["balance_sheet"] = bs
            await db.update_latest_global_state(session_id, gs, bus)
        except Exception:
            bs = {}
    return {"balance_sheet": bs}


@router.get(
    "/{session_id}/board-governance",
    summary="Get board governance state",
)
async def get_board_governance(session_id: str):
    """Return board composition, effectiveness, and governance history."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    board = latest["global_state"].get("board_governance", {})
    return {"board_governance": board}


@router.get(
    "/{session_id}/supply-chain",
    summary="Get supply chain network state",
)
async def get_supply_chain(session_id: str):
    """Return the 3-tier supply chain network state."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    sc = latest["global_state"].get("supply_chain", {})
    return {"supply_chain": sc}


@router.get(
    "/{session_id}/npc-stakeholders",
    summary="Get NPC stakeholder states",
)
async def get_npc_stakeholders(session_id: str):
    """Return all NPC stakeholder satisfaction and actions."""
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    npc = latest["global_state"].get("npc_stakeholders", {})
    return {"npc_stakeholders": npc}



# ── Extended Horizon Mode (SI-3) ────────────────────────────────

@router.post(
    "/{session_id}/extend",
    summary="Activate Extended Horizon Mode (Rounds 11–20)",
)
async def activate_extended_mode(session_id: str):
    """
    Activates Extended Horizon Mode (SI-3).
    Sets extended_horizon_mode=True, clears game_over, and advances
    round_number to 11 so the simulation loop continues seamlessly.
    """
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]

    gs["extended_horizon_mode"] = True
    gs["game_over"] = False
    gs["game_over_reason"] = None

    await db.update_latest_global_state(session_id, gs, bus)

    # Advance to round 11 — reuse the existing advance-round mechanism
    from branching_engine import get_extended_round_config
    r11 = get_extended_round_config(11) or {}
    await db.advance_round(session_id, 11)

    return {
        "ok": True,
        "extended_horizon_mode": True,
        "new_round": 11,
        "round_title": r11.get("title", "Year 5 Q3: Extended Horizon"),
        "round_theme": r11.get("theme", ""),
        "message": "Extended Horizon activated. Rounds 11–20 are now unlocked.",
    }


# ═════════════════════════════════════════════════════════════════
#  PLAYER-FACING ANNOTATIONS — Facilitator notes visible to students
#  Visibility controlled by facilitator via admin toggle.
# ═════════════════════════════════════════════════════════════════

@router.get("/{session_id}/annotations", summary="Get annotations visible to the player")
async def get_player_annotations(session_id: str):
    """Returns annotations for this session that the facilitator has
    marked as visible to students. Respects the session-level visibility toggle."""
    import database_memory as db_mem
    from admin_router import _annotations

    # Find the parent cohort session to check visibility toggle
    sess = db_mem._sessions.get(session_id, {})
    parent_id = sess.get("parent_cohort_id", session_id)
    parent_sess = db_mem._sessions.get(parent_id, sess)

    # Check if facilitator has enabled annotations visibility for students
    if not parent_sess.get("annotations_player_visible", False):
        return {"annotations": []}

    # Get annotations for the parent cohort (not the player sub-session)
    all_annotations = _annotations.get(parent_id, [])

    # Filter to those explicitly marked as visible_to_students (or all if the toggle is on)
    visible = [
        a for a in all_annotations
        if a.get("visible_to_students", True)  # Default to visible when toggle is on
    ]

    return {"annotations": visible}

