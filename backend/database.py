"""
Muressons Global Command — Async Database Service
Wraps asyncpg for all persistence operations.
"""

from __future__ import annotations
import json
import uuid
from typing import Any, Optional

import asyncpg

from config import DATABASE_URL, DB_MIN_CONNECTIONS, DB_MAX_CONNECTIONS


# ── Connection Pool ─────────────────────────────────────────────

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_MIN_CONNECTIONS,
            max_size=DB_MAX_CONNECTIONS,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Seed Data ───────────────────────────────────────────────────

def _load_seed() -> dict:
    """Load the Round 1 seed JSON (relative to the backend directory)."""
    import pathlib
    seed_path = pathlib.Path(__file__).resolve().parent.parent / "db" / "seed_round1.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Session Operations ──────────────────────────────────────────

async def create_session(
    cohort_name: str, 
    facilitator_id: str, 
    allowed_overrides: list[str] = None, 
    allowed_swipes: list[str] = None,
    loan_interest_rate: float = 0.12,
    player_id: str = None,
    parent_cohort_id: str = None,
) -> dict:
    """
    Create a new session, insert the Round 1 global state and all BU
    states from the seed JSON.  Returns a dict ready for the API response.
    """
    allowed_overrides = allowed_overrides or []
    allowed_swipes = allowed_swipes or []
    pool = await get_pool()
    seed = _load_seed()

    session_id = str(uuid.uuid4())
    global_state_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Session row
            await conn.execute(
                """
                INSERT INTO sessions (session_id, cohort_name, facilitator_id)
                VALUES ($1, $2, $3)
                """,
                uuid.UUID(session_id),
                cohort_name,
                facilitator_id,
            )
            
            # (Note: In a true DB migration, we would run ALTER TABLE sessions ADD COLUMN allowed_overrides JSONB, etc.
            # But the user might be using memory DB. We'll store it by updating session row if columns exist, but 
            # for now, we leave the schema alone to avoid dropping existing DBs. We will rely on memory cache or separate store if needed.)

            gs = seed["global_state"]

            # 2. Global round state — Round 1
            await conn.execute(
                """
                INSERT INTO global_round_states
                    (state_id, session_id, round_number,
                     corporate_treasury, group_reputation,
                     synergy_multiplier, cost_of_capital,
                     active_event_flags)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                uuid.UUID(global_state_id),
                uuid.UUID(session_id),
                1,
                gs["corporate_treasury_usd"],
                gs["group_reputation_score"],
                gs["group_synergy_multiplier"],
                gs["cost_of_capital_rate"],
                json.dumps({
                    **gs.get("active_event_flags", {}),
                    "loan_interest_rate": loan_interest_rate
                }),
            )

            # 3. BU round states
            for bu in seed["business_units"]:
                await conn.execute(
                    """
                    INSERT INTO bu_round_states
                        (global_state_id, bu_id,
                         revenue_base, opex_base,
                         natural_capital_debt, social_license_score,
                         reputation_score, governance_risk_score,
                         water_dependency, carbon_intensity,
                         risk_factors)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    uuid.UUID(global_state_id),
                    bu["bu_id"],
                    bu["revenue_base"],
                    bu["opex_base"],
                    bu.get("natural_capital_debt", 0),
                    bu.get("social_license_score", 50),
                    bu.get("reputation_score", 50),
                    bu.get("governance_risk_score", 0),
                    bu.get("water_dependency", 0),
                    bu.get("carbon_intensity", 0),
                    json.dumps(bu.get("risk_factors", {})),
                )

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
        },
        "business_units": seed["business_units"],
    }


# ── Fetch Operations ───────────────────────────────────────────

async def get_session_info(session_id: str) -> Optional[dict]:
    """Return basic session metadata by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT session_id, cohort_name, facilitator_id FROM sessions WHERE session_id = $1",
            uuid.UUID(session_id),
        )
        if row is None:
            return None
        return {
            "session_id": str(row["session_id"]),
            "cohort_name": row["cohort_name"],
            "facilitator_id": row["facilitator_id"],
        }

async def fetch_session_by_cohort(cohort_name: str) -> Optional[dict]:
    """Look up an existing session by cohort_name and return its latest state."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT session_id
            FROM sessions
            WHERE cohort_name = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            cohort_name
        )
        if row is None:
            return None
            
        # Manually tack on session_id so the router can use it
        state = await fetch_latest_state(str(row["session_id"]))
        if state:
            state["session_id"] = str(row["session_id"])
        return state


async def fetch_latest_state(session_id: str) -> Optional[dict]:
    """
    Return the latest round's global state + BU states for a session.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        grs = await conn.fetchrow(
            """
            SELECT state_id, round_number, corporate_treasury,
                   group_reputation, synergy_multiplier, cost_of_capital,
                   active_event_flags
            FROM global_round_states
            WHERE session_id = $1
            ORDER BY round_number DESC
            LIMIT 1
            """,
            uuid.UUID(session_id),
        )
        if grs is None:
            return None

        bus = await conn.fetch(
            """
            SELECT bu_id, revenue_base, opex_base,
                   natural_capital_debt, social_license_score,
                   reputation_score, governance_risk_score,
                   water_dependency, carbon_intensity,
                   risk_factors
            FROM bu_round_states
            WHERE global_state_id = $1
            ORDER BY bu_id
            """,
            grs["state_id"],
        )

        return {
            "state_id": str(grs["state_id"]),
            "round_number": grs["round_number"],
            "global_state": {
                "corporate_treasury": float(grs["corporate_treasury"]),
                "group_reputation": float(grs["group_reputation"]),
                "synergy_multiplier": float(grs["synergy_multiplier"]),
                "cost_of_capital": float(grs["cost_of_capital"]),
                "active_event_flags": grs["active_event_flags"] or {},
            },
            "bu_states": [
                {
                    "bu_id": row["bu_id"],
                    "revenue_base": float(row["revenue_base"]),
                    "opex_base": float(row["opex_base"]),
                    "natural_capital_debt": float(row["natural_capital_debt"]),
                    "social_license_score": float(row["social_license_score"]),
                    "reputation_score": float(row["reputation_score"]),
                    "governance_risk_score": float(row["governance_risk_score"]),
                    "water_dependency": float(row["water_dependency"]),
                    "carbon_intensity": float(row["carbon_intensity"]),
                    "risk_factors": row["risk_factors"] or {},
                }
                for row in bus
            ],
        }


async def fetch_round_history(session_id: str) -> list[dict]:
    """
    Return all rounds for a session (for the dashboard history).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rounds = await conn.fetch(
            """
            SELECT state_id, round_number, corporate_treasury,
                   group_reputation, synergy_multiplier, cost_of_capital,
                   active_event_flags
            FROM global_round_states
            WHERE session_id = $1
            ORDER BY round_number
            """,
            uuid.UUID(session_id),
        )

        history = []
        for grs in rounds:
            bus = await conn.fetch(
                """
                SELECT bu_id, revenue_base, opex_base,
                       natural_capital_debt, social_license_score,
                       reputation_score, governance_risk_score,
                       water_dependency, carbon_intensity,
                       risk_factors
                FROM bu_round_states
                WHERE global_state_id = $1
                ORDER BY bu_id
                """,
                grs["state_id"],
            )
            history.append({
                "round_number": grs["round_number"],
                "global_state": {
                    "corporate_treasury": float(grs["corporate_treasury"]),
                    "group_reputation": float(grs["group_reputation"]),
                    "synergy_multiplier": float(grs["synergy_multiplier"]),
                    "cost_of_capital": float(grs["cost_of_capital"]),
                    "active_event_flags": grs["active_event_flags"] or {},
                },
                "business_units": [
                    {
                        "bu_id": row["bu_id"],
                        "revenue_base": float(row["revenue_base"]),
                        "opex_base": float(row["opex_base"]),
                        "natural_capital_debt": float(row["natural_capital_debt"]),
                        "social_license_score": float(row["social_license_score"]),
                        "reputation_score": float(row["reputation_score"]),
                        "governance_risk_score": float(row["governance_risk_score"]),
                        "water_dependency": float(row["water_dependency"]),
                        "carbon_intensity": float(row["carbon_intensity"]),
                        "risk_factors": row["risk_factors"] or {},
                    }
                    for row in bus
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
    pool = await get_pool()
    global_state_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Global state
            await conn.execute(
                """
                INSERT INTO global_round_states
                    (state_id, session_id, round_number,
                     corporate_treasury, group_reputation,
                     synergy_multiplier, cost_of_capital,
                     active_event_flags)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                uuid.UUID(global_state_id),
                uuid.UUID(session_id),
                round_number,
                global_state["corporate_treasury"],
                global_state["group_reputation"],
                global_state["synergy_multiplier"],
                global_state.get("cost_of_capital", 0.05),
                json.dumps(global_state.get("active_event_flags", {})),
            )

            # BU states
            for bu in bu_states:
                await conn.execute(
                    """
                    INSERT INTO bu_round_states
                        (global_state_id, bu_id,
                         revenue_base, opex_base,
                         natural_capital_debt, social_license_score,
                         reputation_score, governance_risk_score,
                         water_dependency, carbon_intensity,
                         risk_factors)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    uuid.UUID(global_state_id),
                    bu["bu_id"],
                    bu["revenue_base"],
                    bu["opex_base"],
                    bu.get("natural_capital_debt", 0),
                    bu.get("social_license_score", 50),
                    bu.get("reputation_score", 50),
                    bu.get("governance_risk_score", 0),
                    bu.get("water_dependency", 0),
                    bu.get("carbon_intensity", 0),
                    json.dumps(bu.get("risk_factors", {})),
                )

            # Decision audit log
            for dec in decisions:
                await conn.execute(
                    """
                    INSERT INTO decision_audit_log
                        (session_id, round_number, bu_id,
                         decision_node_id, choice_selected,
                         capex_allocated, time_to_decision_seconds,
                         team_consensus)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    uuid.UUID(session_id),
                    round_number,
                    dec.get("bu_id"),
                    dec.get("decision_node_id", ""),
                    dec.get("choice_selected", ""),
                    dec.get("capex_allocated", 0),
                    dec.get("time_to_decision_seconds", 0),
                    dec.get("team_consensus", "majority"),
                )

    return global_state_id


# ── Admin / God Mode Operations ───────────────────────────────

async def fetch_all_sessions() -> list[dict]:
    """Return all sessions with basic metadata for the admin leaderboard."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, cohort_name, facilitator_id, start_time
            FROM sessions
            ORDER BY start_time DESC
            """
        )
        return [
            {
                "session_id": str(row["session_id"]),
                "cohort_name": row["cohort_name"],
                "facilitator_id": row["facilitator_id"],
                "start_time": row["start_time"].isoformat() if row["start_time"] else None,
            }
            for row in rows
        ]


async def update_latest_global_state(
    session_id: str,
    global_state: dict,
    bu_states: list[dict],
) -> None:
    """
    Update the LATEST round's global and BU states in place.
    Used by God Mode overrides that mutate the current round
    without advancing to a new round.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Find the latest state_id
        grs = await conn.fetchrow(
            """
            SELECT state_id FROM global_round_states
            WHERE session_id = $1
            ORDER BY round_number DESC LIMIT 1
            """,
            uuid.UUID(session_id),
        )
        if grs is None:
            return

        state_id = grs["state_id"]

        async with conn.transaction():
            # Update global state
            await conn.execute(
                """
                UPDATE global_round_states SET
                    corporate_treasury = $2,
                    group_reputation = $3,
                    synergy_multiplier = $4,
                    cost_of_capital = $5,
                    active_event_flags = $6
                WHERE state_id = $1
                """,
                state_id,
                global_state["corporate_treasury"],
                global_state["group_reputation"],
                global_state["synergy_multiplier"],
                global_state.get("cost_of_capital", 0.05),
                json.dumps(global_state.get("active_event_flags", {})),
            )

            # Update BU states
            for bu in bu_states:
                await conn.execute(
                    """
                    UPDATE bu_round_states SET
                        revenue_base = $3,
                        opex_base = $4,
                        natural_capital_debt = $5,
                        social_license_score = $6,
                        reputation_score = $7,
                        governance_risk_score = $8,
                        water_dependency = $9,
                        carbon_intensity = $10,
                        risk_factors = $11
                    WHERE global_state_id = $1 AND bu_id = $2
                    """,
                    state_id,
                    bu["bu_id"],
                    bu["revenue_base"],
                    bu["opex_base"],
                    bu.get("natural_capital_debt", 0),
                    bu.get("social_license_score", 50),
                    bu.get("reputation_score", 50),
                    bu.get("governance_risk_score", 0),
                    bu.get("water_dependency", 0),
                    bu.get("carbon_intensity", 0),
                    json.dumps(bu.get("risk_factors", {})),
                )


# ── Undo / Rollback Operations ────────────────────────────────

async def undo_latest_round(session_id: str) -> dict:
    """
    Delete the latest round's global state, BU states, and audit log
    entries for a session. Temporarily disables immutability triggers.
    Returns {"success": True, "deleted_round": N, "new_current_round": N-1}
    or {"success": False, "reason": "..."}.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Find the latest round
        latest = await conn.fetchrow(
            """
            SELECT state_id, round_number
            FROM global_round_states
            WHERE session_id = $1
            ORDER BY round_number DESC
            LIMIT 1
            """,
            uuid.UUID(session_id),
        )
        if latest is None:
            return {"success": False, "reason": "Session has no round data"}

        if latest["round_number"] <= 1:
            return {"success": False, "reason": "Cannot undo Round 1 (initial state)"}

        deleted_round = latest["round_number"]
        state_id = latest["state_id"]

        async with conn.transaction():
            # Temporarily disable immutability triggers
            await conn.execute("ALTER TABLE decision_audit_log DISABLE TRIGGER trg_immutable_decision_audit_log")
            await conn.execute("ALTER TABLE bu_round_states DISABLE TRIGGER trg_immutable_bu_round_states")
            await conn.execute("ALTER TABLE global_round_states DISABLE TRIGGER trg_immutable_global_round_states")

            try:
                # Delete audit log entries for this round
                await conn.execute(
                    "DELETE FROM decision_audit_log WHERE session_id = $1 AND round_number = $2",
                    uuid.UUID(session_id), deleted_round,
                )
                # Delete BU states (cascades from global state via FK, but explicit is safer)
                await conn.execute(
                    "DELETE FROM bu_round_states WHERE global_state_id = $1",
                    state_id,
                )
                # Delete global round state
                await conn.execute(
                    "DELETE FROM global_round_states WHERE state_id = $1",
                    state_id,
                )
            finally:
                # Re-enable immutability triggers
                await conn.execute("ALTER TABLE global_round_states ENABLE TRIGGER trg_immutable_global_round_states")
                await conn.execute("ALTER TABLE bu_round_states ENABLE TRIGGER trg_immutable_bu_round_states")
                await conn.execute("ALTER TABLE decision_audit_log ENABLE TRIGGER trg_immutable_decision_audit_log")

    return {
        "success": True,
        "deleted_round": deleted_round,
        "new_current_round": deleted_round - 1,
    }

