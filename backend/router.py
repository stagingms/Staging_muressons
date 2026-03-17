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
from admin_router import set_session_interventions, SessionInterventionsRequest, check_hidden_resource_triggers, auto_inject_scheduled_interventions
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player ID not found. Please check with your facilitator."
        )

    # Validate password ("321" is master override)
    stored_pw = player_record.get("password", "")
    if stored_pw and req.password != "321" and req.password != stored_pw:
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
            if req.password != "321" and req.password != player_record["password"]:
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
        result = await db.create_session(
            body.cohort_name, 
            body.facilitator_id, 
            loan_interest_rate=body.loan_interest_rate,
            decision_paradigm=getattr(body, 'decision_paradigm', 'legacy_abc'),
        )
        
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
    valid_bu_ids = {"pharma", "electronics", "consumer_goods", "software"}
    submitted_bu_ids = [d["bu_id"] for d in decisions_raw]

    # VULN-005: Reject duplicate BU IDs
    if len(submitted_bu_ids) != len(set(submitted_bu_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate BU IDs in decisions. Each BU must appear exactly once.",
        )

    # VULN-009: Require all 4 BUs
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
    )

    new_round = tick_result["global_state"]["round_number"]
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

    # ── FINAL REPORT: Generate game-over summary after Round 10 ──
    if current_round == 10:
        treasury = new_global.get("corporate_treasury", 0)
        reputation = new_global.get("group_reputation", 50)
        synergy = new_global.get("synergy_multiplier", 1.0)
        ebitda = new_global.get("historical_ebitda", 0)

        # Carbon tonnage and carbon tax
        carbon_tonnage = sum(
            bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000
            for bu in new_bus
        )
        carbon_tax_per_ton = 250  # EU ETS projected 2050
        carbon_cost = round(carbon_tonnage * carbon_tax_per_ton, 2)

        # Regenerative Multiple breakdown
        avg_sl = sum(bu.get("social_license_score", 50) for bu in new_bus) / max(len(new_bus), 1)
        avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in new_bus) / max(len(new_bus), 1)

        base_mr = 1.0
        synergy_bonus = round(max(0, (synergy - 1.0) * 3), 2)
        resilience_bonus = round(max(0, (avg_sl - 50) / 50) * 0.5, 2)
        truth_premium = 0  # From stakeholder map accuracy — future enhancement
        instability_discount = round(-min(1.0, avg_ncd / 5_000_000) * 0.8, 2)

        regenerative_multiple = round(base_mr + synergy_bonus + resilience_bonus + truth_premium + instability_discount, 2)
        regenerative_multiple = max(0.5, min(3.0, regenerative_multiple))

        # Terminal value
        exit_multiple = round(8 + regenerative_multiple * 3, 1)
        terminal_value = round(ebitda * exit_multiple, 2)

        # Profile classification
        if regenerative_multiple >= 2.0 and avg_sl >= 65:
            profile = "regenerative_pioneer"
            profile_title = "The Regenerative Pioneer"
            profile_description = (
                "A transformational corporation that has embedded sustainability into its DNA. "
                "Investors see outsized long-term returns with minimal tail risk."
            )
        elif regenerative_multiple >= 1.5:
            profile = "strategic_integrator"
            profile_title = "The Strategic Integrator"
            profile_description = (
                "A corporation that has strategically woven ESG into operations. "
                "Strong risk management and growing competitive advantages."
            )
        elif regenerative_multiple >= 1.0:
            profile = "derisked_safe_haven"
            profile_title = "The De-risked Safe-Haven"
            profile_description = (
                "A resilient corporation that avoided the worst tail risks. "
                "Investors value the predictability, but innovation is stalling."
            )
        else:
            profile = "stranded_asset"
            profile_title = "The Stranded Asset"
            profile_description = (
                "A corporation weighed down by unmanaged ESG risks. "
                "Regulatory penalties and reputational damage erode long-term value."
            )

        # Synergy score (0-200 scale)
        synergy_score = round(synergy * 100, 1)

        # R10 choice (from decisions)
        r10_choice = decisions_raw[0].get("choice_selected", "option_b") if decisions_raw else "option_b"

        # Inject final report into events
        events["ebitda_2050"] = round(ebitda, 2)
        events["carbon_tonnage_group"] = round(carbon_tonnage, 1)
        events["carbon_cost"] = carbon_cost
        events["carbon_tax_per_ton"] = carbon_tax_per_ton
        events["regenerative_multiple"] = regenerative_multiple
        events["mr_breakdown"] = {
            "base": base_mr,
            "synergy_bonus": synergy_bonus,
            "resilience_bonus": resilience_bonus,
            "truth_premium": truth_premium,
            "instability_discount": instability_discount,
        }
        events["terminal_value"] = terminal_value
        events["exit_multiple"] = exit_multiple
        events["final_treasury"] = round(treasury, 2)
        events["profile"] = profile
        events["profile_title"] = profile_title
        events["profile_description"] = profile_description
        events["synergy_score"] = synergy_score
        events["avg_social_license"] = round(avg_sl, 1)
        events["r10_choice"] = r10_choice

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
async def get_round_config_endpoint(round_number: int):
    """
    Returns the crisis definition, decision options, special rules,
    and UI constraints for a round.
    Used by the frontend to populate the DecisionModal.
    """
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
    decision_paradigm: str  # 'legacy_abc' or 'multi_toggles'

@router.put(
    "/{session_id}/paradigm",
    summary="Update the decision paradigm for a session",
)
async def update_session_paradigm(session_id: str, body: UpdateParadigmRequest):
    """Set the decision paradigm for a session. Propagates to child player sessions."""
    if body.decision_paradigm not in ("legacy_abc", "multi_toggles"):
        raise HTTPException(status_code=400, detail="Invalid paradigm. Must be 'legacy_abc' or 'multi_toggles'.")

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
        from database_memory import _sessions
        for sid, sdata in _sessions.items():
            if sdata.get("parent_cohort_id") == session_id:
                sdata["decision_paradigm"] = body.decision_paradigm
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

    # Add allocation to treasury
    global_state["corporate_treasury"] += allocated_budget
    global_state["materiality_budget_allocated"] = list(q1_submission) # Save the funded issues directly
    
    # Store BU context if applicable
    if body.bu_id:
        global_state["materiality_bu_id"] = body.bu_id

    # Persist the updated treasury back to the database for this round
    await db.update_latest_global_state(session_id, global_state, bu_states)

    return MaterialitySubmissionResponse(
        allocated_budget=allocated_budget,
        corporate_treasury=global_state["corporate_treasury"],
        message="Materiality Matrix accepted. Funding allocated based on accuracy."
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
    from admin_router import _resource_library, _session_resource_state

    # Get current round
    latest = await db.fetch_latest_state(session_id)
    current_round = latest["round_number"] if latest else 1

    # Also check parent cohort for unlocked resources
    session_info = await db.get_session_info(session_id)
    parent_id = session_info.get("parent_cohort_id") if session_info else None

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

    return {
        "current_round": current_round,
        "new_this_round": new_this_round,
        "archive": archive,
        "total_unlocked": len(new_this_round) + len(archive),
    }
