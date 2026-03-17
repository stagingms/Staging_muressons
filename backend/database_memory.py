"""
Muressons Global Command — In-Memory Database Service
Drop-in replacement for database.py when PostgreSQL is unavailable.
Stores all state in Python dicts; data resets on server restart.
"""

from __future__ import annotations
import copy
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


# ── Seed Data ───────────────────────────────────────────────────

def _load_seed() -> dict:
    """Load the Round 1 seed JSON (relative to the backend directory)."""
    import pathlib
    seed_path = pathlib.Path(__file__).resolve().parent.parent / "db" / "seed_round1.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── In-Memory Stores ────────────────────────────────────────────

_sessions: dict[str, dict] = {}
_global_states: dict[str, list[dict]] = {}      # session_id → [round_states]
_bu_states: dict[str, dict[int, list[dict]]] = {} # session_id → {round_num → [bu_dicts]}
_decision_log: list[dict] = []


# ── Pool stubs (no-ops for compatibility) ───────────────────────

async def get_pool():
    return None

async def close_pool():
    pass


# ── Session Operations ──────────────────────────────────────────

async def create_session(
    cohort_name: str, 
    facilitator_id: Optional[str] = None,
    loan_interest_rate: float = 0.12,
    player_id: Optional[str] = None,
    parent_cohort_id: Optional[str] = None,
    decision_paradigm: str = "legacy_abc",
) -> dict:
    """
    Create a new session and seed Round 1 state.
    Returns a dict ready for the API response.
    """
    # Prevent duplicate cohort names for top-level sessions
    if not parent_cohort_id:
        for existing in _sessions.values():
            if (existing["cohort_name"].strip().lower() == cohort_name.strip().lower()
                    and not existing.get("parent_cohort_id")):
                raise ValueError(f"A cohort named '{cohort_name}' already exists.")

    seed = _load_seed()
    session_id = str(uuid.uuid4())
    global_state_id = str(uuid.uuid4())

    gs = seed["global_state"]

    _sessions[session_id] = {
        "session_id": session_id,
        "cohort_name": cohort_name,
        "facilitator_id": facilitator_id,
        "start_time": datetime.now(timezone.utc),
        "is_public": False,
        "allowed_player_ids": [],
        "player_id": player_id,
        "parent_cohort_id": parent_cohort_id,
        "decision_paradigm": decision_paradigm,
    }

    bus = seed["business_units"]
    n = len(bus) or 1
    baseline_ebitda = round(sum(b["revenue_base"] - b["opex_base"] for b in bus), 2)
    baseline_tco2e = round(sum(b.get("carbon_intensity", 0) * b["revenue_base"] / 1_000_000 for b in bus))
    avg_sl = sum(b.get("social_license_score", 50) for b in bus) / n
    avg_ci = sum(b.get("carbon_intensity", 50) for b in bus) / n
    avg_gr = sum(b.get("governance_risk_score", 20) for b in bus) / n
    baseline_vrio = {
        "value": round(max(0, min(100, avg_sl)), 1),
        "rarity": round(max(0, min(100, 100 - avg_ci)), 1),
        "imitability": round(max(0, min(100, gs["group_synergy_multiplier"] * 100)), 1),
        "organization": round(max(0, min(100, 100 - avg_gr)), 1),
    }

    global_state = {
        "state_id": global_state_id,
        "session_id": session_id,
        "round_number": 1,
        "corporate_treasury": gs["corporate_treasury_usd"],
        "group_reputation": gs["group_reputation_score"],
        "synergy_multiplier": gs["group_synergy_multiplier"],
        "cost_of_capital": gs["cost_of_capital_rate"],
        "active_event_flags": {
            **gs.get("active_event_flags", {}),
            "loan_interest_rate": loan_interest_rate
        },
        "bonus_score": 0,
        "historical_ebitda": baseline_ebitda,
        "tco2e_emissions": baseline_tco2e,
        "vrio_capabilities": baseline_vrio,
    }

    _global_states[session_id] = [global_state]
    _bu_states[session_id] = {1: copy.deepcopy(bus)}

    return {
        "session_id": session_id,
        "round_number": 1,
        "global_state": {
            "corporate_treasury": gs["corporate_treasury_usd"],
            "group_reputation": gs["group_reputation_score"],
            "synergy_multiplier": gs["group_synergy_multiplier"],
            "cost_of_capital": gs["cost_of_capital_rate"],
            "active_event_flags": {
                **gs.get("active_event_flags", {}),
                "loan_interest_rate": loan_interest_rate
            },
            "historical_ebitda": baseline_ebitda,
            "tco2e_emissions": baseline_tco2e,
            "vrio_capabilities": baseline_vrio,
        },
        "business_units": seed["business_units"],
    }


# ── Fetch Operations ───────────────────────────────────────────

async def get_session_info(session_id: str) -> Optional[dict]:
    """Return basic session metadata by ID."""
    return _sessions.get(session_id)

async def fetch_session_by_cohort(cohort_name: str) -> Optional[dict]:
    """Look up an existing session by cohort_name and return its latest state.
    Only matches top-level sessions (not per-player clones)."""
    matching_sessions = [
        s for s in _sessions.values()
        if s["cohort_name"] == cohort_name and not s.get("parent_cohort_id")
    ]
    if not matching_sessions:
        return None
        
    latest_session = sorted(
        matching_sessions,
        key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True
    )[0]
    
    session_id = latest_session["session_id"]
    state = await fetch_latest_state(session_id)
    if state:
        state["session_id"] = session_id
    return state


async def get_active_public_sessions() -> list[dict]:
    """Return all top-level sessions (exclude per-player sub-sessions)."""
    active = [s for s in _sessions.values() if not s.get("parent_cohort_id")]
    # Sort by start_time descending
    active.sort(key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return active

async def validate_player_id(session_id: str, player_id: str) -> bool:
    session = _sessions.get(session_id)
    if not session: return False
    return player_id in session.get("allowed_player_ids", [])

async def set_session_public(session_id: str, is_public: bool) -> bool:
    session = _sessions.get(session_id)
    if not session: return False
    session["is_public"] = is_public
    return True

async def generate_player_id(session_id: str) -> Optional[str]:
    import random
    import string
    session = _sessions.get(session_id)
    if not session: return None
    
    allowed = session.setdefault("allowed_player_ids", [])
    while True:
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        pid = f"MUR-{letters}"
        if pid not in allowed:
            break
            
    allowed.append(pid)
    return pid


async def fetch_latest_state(session_id: str) -> Optional[dict]:
    """
    Return the latest round's global state + BU states for a session.
    """
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return None

    grs = rounds[-1]
    rn = grs["round_number"]
    bus = _bu_states.get(session_id, {}).get(rn, [])

    return {
        "state_id": grs["state_id"],
        "round_number": rn,
        "global_state": {
            "corporate_treasury": float(grs["corporate_treasury"]),
            "group_reputation": float(grs["group_reputation"]),
            "synergy_multiplier": float(grs["synergy_multiplier"]),
            "cost_of_capital": float(grs["cost_of_capital"]),
            "active_event_flags": grs.get("active_event_flags") or {},
            "historical_ebitda": float(grs.get("historical_ebitda", 0)),
            "tco2e_emissions": int(grs.get("tco2e_emissions", 0)),
            "vrio_capabilities": grs.get("vrio_capabilities") or {},
        },
        "bu_states": [
            {
                "bu_id": bu["bu_id"],
                "revenue_base": float(bu["revenue_base"]),
                "opex_base": float(bu["opex_base"]),
                "natural_capital_debt": float(bu.get("natural_capital_debt", 0)),
                "social_license_score": float(bu.get("social_license_score", 50)),
                "reputation_score": float(bu.get("reputation_score", 50)),
                "governance_risk_score": float(bu.get("governance_risk_score", 0)),
                "water_dependency": float(bu.get("water_dependency", 0)),
                "carbon_intensity": float(bu.get("carbon_intensity", 0)),
                "risk_factors": bu.get("risk_factors") or {},
            }
            for bu in bus
        ],
    }


async def fetch_round_history(session_id: str) -> list[dict]:
    """
    Return all rounds for a session (for the dashboard history).
    """
    rounds = _global_states.get(session_id, [])
    history = []
    for grs in rounds:
        rn = grs["round_number"]
        bus = _bu_states.get(session_id, {}).get(rn, [])
        history.append({
            "round_number": rn,
            "global_state": {
                "corporate_treasury": float(grs["corporate_treasury"]),
                "group_reputation": float(grs["group_reputation"]),
                "synergy_multiplier": float(grs["synergy_multiplier"]),
                "cost_of_capital": float(grs["cost_of_capital"]),
                "active_event_flags": grs.get("active_event_flags") or {},
                "historical_ebitda": float(grs.get("historical_ebitda", 0)),
                "tco2e_emissions": int(grs.get("tco2e_emissions", 0)),
                "vrio_capabilities": grs.get("vrio_capabilities") or {},
            },
            "business_units": [
                {
                    "bu_id": bu["bu_id"],
                    "revenue_base": float(bu["revenue_base"]),
                    "opex_base": float(bu["opex_base"]),
                    "natural_capital_debt": float(bu.get("natural_capital_debt", 0)),
                    "social_license_score": float(bu.get("social_license_score", 50)),
                    "reputation_score": float(bu.get("reputation_score", 50)),
                    "governance_risk_score": float(bu.get("governance_risk_score", 0)),
                    "water_dependency": float(bu.get("water_dependency", 0)),
                    "carbon_intensity": float(bu.get("carbon_intensity", 0)),
                    "risk_factors": bu.get("risk_factors") or {},
                }
                for bu in bus
            ],
        })
    return history


# ── Insert Next-Round State ────────────────────────────────────

async def insert_next_round(
    session_id: str,
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    decisions: list[dict],
) -> str:
    """
    Persist the new round state and audit log entries.
    Returns the new global_state_id.
    """
    global_state_id = str(uuid.uuid4())

    state_entry = {
        "state_id": global_state_id,
        "session_id": session_id,
        "round_number": round_number,
        "corporate_treasury": global_state["corporate_treasury"],
        "group_reputation": global_state["group_reputation"],
        "synergy_multiplier": global_state.get("synergy_multiplier", 1.0),
        "cost_of_capital": global_state.get("cost_of_capital", 0.05),
        "active_event_flags": global_state.get("active_event_flags", {}),
        "historical_ebitda": global_state.get("historical_ebitda", 0),
        "tco2e_emissions": global_state.get("tco2e_emissions", 0),
        "vrio_capabilities": global_state.get("vrio_capabilities", {}),
    }

    if session_id not in _global_states:
        _global_states[session_id] = []
    _global_states[session_id].append(state_entry)

    if session_id not in _bu_states:
        _bu_states[session_id] = {}
    _bu_states[session_id][round_number] = copy.deepcopy(bu_states)

    for dec in decisions:
        _decision_log.append({
            "session_id": session_id,
            "round_number": round_number,
            "bu_id": dec.get("bu_id"),
            "decision_node_id": dec.get("decision_node_id", ""),
            "choice_selected": dec.get("choice_selected", ""),
            "capex_allocated": dec.get("capex_allocated", 0),
            "player_id": dec.get("player_id", ""),
            "time_to_decision_seconds": dec.get("time_to_decision_seconds", 0),
            "team_consensus": dec.get("team_consensus", "majority"),
        })

    return global_state_id


async def get_decision_log(session_id: str) -> list[dict]:
    """
    Return all decisions for a session and its child player sessions.
    Includes player_id from the child session metadata.
    """
    # Collect all relevant session IDs (parent + children)
    related_ids = {session_id}
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == session_id:
            related_ids.add(sid)

    results = []
    for entry in _decision_log:
        if entry.get("session_id") in related_ids:
            # Prefer player_id from the decision entry itself (set during commit-turn),
            # fall back to session metadata
            sess = _sessions.get(entry["session_id"], {})
            player_id = entry.get("player_id") or sess.get("player_id") or "unknown"
            results.append({
                **entry,
                "player_id": player_id,
                "cohort_name": sess.get("cohort_name", ""),
            })

    # Sort by round, then player
    results.sort(key=lambda x: (x.get("round_number", 0), x.get("player_id", "")))
    return results


async def get_child_sessions(session_id: str) -> list[dict]:
    """Return all child player sessions under a parent cohort session."""
    children = []
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == session_id:
            children.append({
                "session_id": sid,
                "player_id": sess.get("player_id", ""),
                "cohort_name": sess.get("cohort_name", ""),
                "parent_cohort_id": session_id,
            })
    return children


# ── Admin / God Mode Operations ───────────────────────────────

async def fetch_all_sessions() -> list[dict]:
    """Return only top-level cohort sessions for the admin leaderboard (excludes per-player sub-sessions)."""
    return [
        {
            "session_id": s["session_id"],
            "cohort_name": s["cohort_name"],
            "facilitator_id": s["facilitator_id"],
            "start_time": s["start_time"].isoformat() if s.get("start_time") else None,
            "is_public": s.get("is_public", False),
            "allowed_player_ids": s.get("allowed_player_ids", []),
            "player_id": s.get("player_id"),
            "parent_cohort_id": s.get("parent_cohort_id"),
            "registered_players": s.get("registered_players", []),
        }
        for s in sorted(
            _sessions.values(),
            key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )
        if not s.get("parent_cohort_id")  # Only top-level cohorts
    ]


async def get_child_sessions(parent_session_id: str) -> list[dict]:
    """Return all child player sessions for a given parent cohort session."""
    children = []
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_session_id:
            children.append({
                "session_id": sid,
                "player_id": sess.get("player_id", "unknown"),
                "cohort_name": sess.get("cohort_name", ""),
                "parent_cohort_id": parent_session_id,
            })
    return children


async def update_latest_global_state(
    session_id: str,
    global_state: dict,
    bu_states: list[dict],
) -> None:
    """
    Update the LATEST round's global and BU states in place.
    Used by God Mode overrides.
    """
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return

    latest = rounds[-1]
    latest["corporate_treasury"] = global_state["corporate_treasury"]
    latest["group_reputation"] = global_state["group_reputation"]
    latest["synergy_multiplier"] = global_state.get("synergy_multiplier", 1.0)
    latest["cost_of_capital"] = global_state.get("cost_of_capital", 0.05)
    latest["active_event_flags"] = global_state.get("active_event_flags", {})

    rn = latest["round_number"]
    if session_id in _bu_states:
        _bu_states[session_id][rn] = copy.deepcopy(bu_states)


# ── Reset / Delete Operations ─────────────────────────────────

async def delete_session(session_id: str) -> bool:
    """Delete a single session and all its state. Returns True if found."""
    found = session_id in _sessions
    _sessions.pop(session_id, None)
    _global_states.pop(session_id, None)
    _bu_states.pop(session_id, None)
    # Remove decisions for this session
    global _decision_log
    _decision_log = [d for d in _decision_log if d.get("session_id") != session_id]
    return found


async def delete_all_sessions() -> int:
    """Delete ALL sessions. Returns the count of sessions deleted."""
    count = len(_sessions)
    _sessions.clear()
    _global_states.clear()
    _bu_states.clear()
    global _decision_log
    _decision_log = []
    return count


# ── Decade Forward Plan ──────────────────────────────────────

async def save_decade_plan(session_id: str, boardroom_choice: str, decade_plan: str) -> bool:
    """Save the boardroom choice and decade forward plan into the session."""
    sess = _sessions.get(session_id)
    if not sess:
        return False
    sess["boardroom_choice"] = boardroom_choice
    sess["decade_forward_plan"] = decade_plan
    return True


async def get_decade_plan(session_id: str) -> Optional[dict]:
    """Retrieve the decade forward plan for a session."""
    sess = _sessions.get(session_id)
    if not sess:
        return None
    return {
        "boardroom_choice": sess.get("boardroom_choice"),
        "decade_forward_plan": sess.get("decade_forward_plan"),
    }

