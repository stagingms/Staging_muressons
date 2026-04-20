"""
Muressons Global Command — API Router
Simulation endpoints: start, dashboard, commit-turn, round-config.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

import database as db
import materiality_db as mat_db
from engine import process_tick
from round_logic import pre_tick, post_tick
from round_configs import get_round_config, get_round_crisis
from pillar_configs import get_pillar_config, aggregate_pillar_decisions, translate_pillars_to_legacy_choice
from config import MASTER_PASSWORD
from admin_router import set_session_interventions, SessionInterventionsRequest, check_hidden_resource_triggers, auto_inject_scheduled_interventions, check_and_increment_cohort_count, is_practice_mode
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

_session_players: dict[str, list[dict]] = {}

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
    from admin_router import _player_registry, _facilitator_registry, _persist_facilitators
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
    from admin_router import _player_registry

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
        from admin_router import _player_registry
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
    )

    player_sid = str(player_session["session_id"])

    # Track the mapping
    players.append({"player_id": req.player_id, "player_session_id": player_sid})
    _session_players[session_id] = players

    # Update the player registry with the name so it shows in facilitator view
    try:
        from admin_router import _player_registry
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
        )
        
        # 2c. Persist decision_paradigm on the facilitator record
        #     so GET /facilitators always returns it (fixes paradigm disappearing on poll)
        try:
            from admin_router import _facilitator_registry, _persist_facilitators
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
    # ── Fetch current state ──────────────────────────────────
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    current_round = current["round_number"]
    if current_round > 10:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already completed all 10 rounds.",
        )

    # ── Round pacing gate ────────────────────────────────────
    from admin_router import is_round_unlocked
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

    # ── Run the tick engine ──────────────────────────────────
    tick_result = process_tick(
        current_global=current_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        dividends_paid=body.dividends_paid,
        crisis_severity=effective_crisis,
        imitation_decay_rate=body.imitation_decay_rate,
        decision_paradigm=paradigm,
    )

    new_round = tick_result["global_state"]["round_number"]
    # ── CAP: After Round 10, do NOT advance to Round 11 ──
    if current_round == 10:
        new_round = 10
        tick_result["global_state"]["round_number"] = 10
    new_global = tick_result["global_state"]
    new_bus = tick_result["bu_states"]
    events = tick_result["events"]

    # Merge pre-tick events
    events.update(pre_result.get("pre_events", {}))

    # ── PILLAR MODE: Apply aggregated impacts ────────────────
    if pillar_aggregation:
        agg_impacts = pillar_aggregation.get("impacts", {})
        agg_cost = pillar_aggregation.get("total_cost", 0)

        # Apply treasury cost from pillar selections
        if agg_cost != 0:
            new_global["corporate_treasury"] = round(new_global["corporate_treasury"] + agg_cost, 2)
            events["pillar_cost_applied"] = agg_cost

        # Apply reputation delta
        rep_delta = agg_impacts.get("reputation", 0)
        if rep_delta != 0:
            new_global["group_reputation"] = max(0, min(100, round(new_global["group_reputation"] + rep_delta, 2)))

        # Apply NCD delta across all BUs
        ncd_delta = agg_impacts.get("natural_capital_debt_delta", 0)
        if ncd_delta != 0:
            for bu in new_bus:
                bu["natural_capital_debt"] = max(0, round(bu.get("natural_capital_debt", 0) + ncd_delta, 2))

        # Apply carbon intensity delta across all BUs
        ci_delta = agg_impacts.get("carbon_intensity_delta", 0)
        if ci_delta != 0:
            for bu in new_bus:
                bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))

        # Apply social license delta across all BUs
        sl_delta = agg_impacts.get("social_license_delta", 0)
        if sl_delta != 0:
            for bu in new_bus:
                bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))

        # Apply governance risk delta across all BUs
        gov_delta = agg_impacts.get("governance_risk_delta", 0)
        if gov_delta != 0:
            for bu in new_bus:
                bu["governance_risk_score"] = max(0, min(100, round(bu.get("governance_risk_score", 0) + gov_delta, 2)))

        # Apply water dependency delta across all BUs
        wd_delta = agg_impacts.get("water_dependency_delta", 0)
        if wd_delta != 0:
            for bu in new_bus:
                bu["water_dependency"] = max(0, round(bu.get("water_dependency", 0) + wd_delta, 2))

        # Store pillar metadata in events
        events["decision_paradigm"] = "multi_toggles"
        events["pillar_selections"] = pillar_aggregation.get("per_area", {})
        events["pillar_flags"] = pillar_aggregation.get("flags_set", [])

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

    # ── PRACTICE MODE: Reset after Round 2 ────────────────────
    # Check if this session or its parent is in practice mode
    practice_session_id = session_id
    if session_info and session_info.get("parent_cohort_id"):
        practice_session_id = session_info["parent_cohort_id"]

    if is_practice_mode(practice_session_id) and current_round >= 2:
        # Reset the cohort session and all child sessions back to Round 1
        await db.reset_session_to_round1(practice_session_id)
        # Disable practice mode after reset
        from admin_router import _practice_mode
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

    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration for round {round_number}.",
        )

    # Build UI constraints from options for frontend gating
    ui_constraints = {}
    for opt_key, opt_val in cfg.get("options", {}).items():
        if opt_val.get("ui_constraint"):
            ui_constraints[opt_key] = opt_val["ui_constraint"]

    return {
        "round_number": round_number,
        "title": cfg.get("title"),
        "theme": cfg.get("theme"),
        "crisis": cfg.get("crisis"),
        "options": cfg.get("options"),
        "special_rules": cfg.get("special_rules", {}),
        "ui_constraints": ui_constraints,
        "paradigm": paradigm or "legacy_abc",
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
    Returns the 4-area strategic pillar options for a round.
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
    3. Deducts consultant fee if used.
    4. Validates CFO Rule: NO non-material (Q2/Q3/Q4) issues allowed in Q1 Top Right.
    5. Calculates M_acc (valid Q1 issues placed correctly / Total True Q1).
    6. Allocates budget based on accuracy.
    7. Persists the new treasury state.
    """
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    bu_states = current["bu_states"]
    
    # Load dynamic Materiality Config
    # Priority: 1) BU-specific dict (if bu_id), 2) Cohort sandbox, 3) Global
    if body.bu_id:
        # Strategic Pillars mode: load BU-specific dictionary
        # Check for cohort-specific BU override first
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
    consultant_fee = mat_config.get("consultant_fee_usd", 1500000)
    
    # Pre-compute the target Q1 (High Fin + High Impact)
    q1_target_issue_ids = set()
    for issue in all_issues:
        if issue["financial_impact"] == "high" and issue["societal_impact"] == "high":
            q1_target_issue_ids.add(issue["id"])

    # Provide a fallback total budget for R2
    from round2_csrd import ROUND_2_DEFAULT_CONFIG
    total_budget = ROUND_2_DEFAULT_CONFIG["round_2_config"]["total_materiality_budget"]

    # Deduct Consultant Fee if used
    if body.consultant_used:
        global_state["corporate_treasury"] -= consultant_fee

    # CFO Override Validation (Strict)
    q1_submission = set(body.matrix_submission.quadrant_1_top_right)
    invalid_q1_issues = q1_submission - q1_target_issue_ids
    
    if invalid_q1_issues:
        if body.force_override_cfo:
            # Executive override used: penalize treasury further or reputation!
            global_state["group_reputation"] = max(0, global_state.get("group_reputation", 50) - 10)
            # Proceed with accurate counting ignoring invalid
        else:
            # User requested funding for an issue that shouldn't get it
            raise HTTPException(
                status_code=400,
                detail="Your matrix is fundamentally flawed. You have requested CapEx for non-material or low-impact issues. My office will NOT approve this capital allocation. Fix your Quadrant 1 logic and submit again."
            )

    # Accuracy Scoring & Capital Release
    if not q1_target_issue_ids:
        m_acc = 1.0
    else:
        correct_q1_count = len(q1_submission.intersection(q1_target_issue_ids))
        m_acc = correct_q1_count / len(q1_target_issue_ids)

    allocated_budget = int(total_budget * m_acc)

    # ── Full-Quadrant Accuracy Bonus ──────────────────────────────
    # Compute how many of ALL placed issues are in their correct quadrant.
    # Award 1000 bonus_score if accuracy >= 80%.
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

    full_accuracy = (correct_placed / total_placed) if total_placed > 0 else 0
    accuracy_bonus = 0
    if full_accuracy >= 0.80:
        accuracy_bonus = 1000
        global_state["bonus_score"] = global_state.get("bonus_score", 0) + accuracy_bonus

    global_state["materiality_full_accuracy"] = round(full_accuracy * 100, 1)

    # Add allocation to treasury
    global_state["corporate_treasury"] += allocated_budget
    global_state["materiality_budget_allocated"] = list(q1_submission) # Save the funded issues directly
    
    # Store BU context if applicable
    if body.bu_id:
        global_state["materiality_bu_id"] = body.bu_id

    # Unlock the module gate
    global_state["csrd_completed"] = True 

    # Persist the updated treasury back to the database for this round
    await db.update_latest_global_state(session_id, global_state, bu_states)

    return MaterialitySubmissionResponse(
        allocated_budget=allocated_budget,
        corporate_treasury=global_state["corporate_treasury"],
        message=f"Materiality Matrix accepted. Accuracy: {round(full_accuracy*100)}%.{' +1000 bonus points!' if accuracy_bonus else ''} Funding allocated based on Q1 accuracy."
    )


# ─────────────────────────────────────────────────────────────────
# Stakeholder Power-Interest Grid (Round 1 Minigame)
# ─────────────────────────────────────────────────────────────────

from stakeholder_map import evaluate_stakeholder_map, get_stakeholder_list, get_master_config


class StakeholderMapSubmission(BaseModel):
    """Player's mapping of stakeholder IDs to quadrant IDs."""
    mapping: dict[str, str]  # {stakeholder_id: quadrant_id}


@router.get(
    "/stakeholder-map/stakeholders",
    tags=["Simulation"],
    summary="Get stakeholder list for the drag-and-drop bank",
)
async def get_stakeholders():
    return {"stakeholders": get_stakeholder_list()}


@router.post(
    "/{session_id}/stakeholder-map",
    tags=["Simulation"],
    summary="Submit stakeholder power-interest grid mapping",
)
async def submit_stakeholder_map(session_id: str, body: StakeholderMapSubmission):
    # Evaluate against master
    result = evaluate_stakeholder_map(body.mapping)

    # If passed, award bonus_score
    if result["passed"]:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            gs = latest["global_state"]
            gs["bonus_score"] = gs.get("bonus_score", 0) + result["points_awarded"]
            gs["stakeholder_map_completed"] = True
            gs["stakeholder_map_accuracy"] = result["accuracy_percentage"]
            await db.update_latest_global_state(session_id, gs, latest["bu_states"])
    else:
        # Even on fail, mark as completed so player can proceed
        latest = await db.fetch_latest_state(session_id)
        if latest:
            gs = latest["global_state"]
            gs["stakeholder_map_completed"] = True
            gs["stakeholder_map_accuracy"] = result["accuracy_percentage"]
            await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    return {
        "accuracy_percentage": result["accuracy_percentage"],
        "passed": result["passed"],
        "points_awarded": result["points_awarded"],
        "correct_count": result["correct_count"],
        "total_count": result["total_count"],
        "details": result["details"],
        "master_mapping": result["master_mapping"],
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
        from admin_router import _player_registry
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
    from admin_router import _notebooklm_notebooks, _quiz_difficulty

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
    from admin_router import _resource_library, _session_resource_state, _notebooklm_notebooks, _quiz_enabled

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
    For solo/demo sessions, returns empty list.
    """
    # Get session info to find parent cohort
    session_info = await db.get_session_info(session_id)
    if not session_info:
        return {"leaderboard": [], "message": "Session not found"}

    parent_id = session_info.get("parent_cohort_id")
    if not parent_id:
        # Solo session — no peers
        return {"leaderboard": [], "message": "Solo session — no peers to compare"}

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

