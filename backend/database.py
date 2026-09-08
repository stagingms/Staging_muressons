"""
Muressons Global Corporation — Async Database Service
Wraps asyncpg for all persistence operations.
"""

from __future__ import annotations
import asyncio
import json
import uuid
from typing import Any, Optional
from datetime import datetime, timezone

import asyncpg
from fastapi import HTTPException

from config import (DATABASE_URL, DB_MIN_CONNECTIONS, DB_MAX_CONNECTIONS,
                    DB_ACQUIRE_TIMEOUT_SECONDS, DB_COMMAND_TIMEOUT_SECONDS,
                    SIM_INITIAL_BUDGET, SIM_ROUNDS)

# ── Sync session cache: SHARED with the memory backend ──────────────────────
# BUG-2026-07-31: router.py reads `db._sessions` in several fallbacks (e.g.
# player-login's "survives server restart" registry-miss scan). In memory mode
# `database` is aliased to database_memory, which has `_sessions`; under
# Postgres this module had NO such attribute, so the exact code written to
# recover after a restart raised AttributeError → 500 "unable to login" for
# any player missing from the in-process registry. This module already
# MAINTAINS database_memory._sessions as its synchronous cache (init_pool
# pre-populates it from the sessions table; every write updates it) — it just
# never exposed it. Re-export the SAME dict so every `db._sessions` callsite
# reads one truth in both modes. (database_memory does not import this module,
# so no cycle; its import already happens at init_pool under Postgres.)
from database_memory import _sessions  # noqa: F401  (parity re-export)


# ── JSON serialization parity with the memory store ─────────────────────────
# BUG-2026-07-20: the memory store's snapshot serializer tolerates datetimes
# and dataclass instances (database_memory._datetime_serializer), but this
# module used bare json.dumps. So an engine object leaking into
# active_event_flags (e.g. CIDeltaResult at scope3-weighted rounds) persisted
# fine locally and 500'd ONLY on Postgres: "Failed to persist round: Object of
# type CIDeltaResult is not JSON serializable" — stalling the cohort at round 7.
# The leak itself is fixed at the source (engine.apply_ci_delta_in_place), but
# the two stores must degrade IDENTICALLY when the next leak happens, so every
# state dump here now uses the same tolerant default.

def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    import dataclasses as _dc
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        return _dc.asdict(obj)
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _dumps(obj) -> str:
    return json.dumps(obj, default=_json_default)


async def _allow_immutable_purge(conn) -> None:
    """Transaction-local bypass of the append-only immutability guard, for the
    admin purge/reset/undo paths that legitimately delete historical round rows.

    MUST be called INSIDE an open transaction. `SET LOCAL` scopes the flag to
    THIS transaction only — it auto-resets on COMMIT/ROLLBACK, so it never
    leaks to another pooled connection and never leaves the guard disabled
    platform-wide.

    This replaces `ALTER TABLE ... DISABLE TRIGGER`, which was wrong three ways
    (launch-audit follow-up 2026-09-02 — undeletable cohorts / delete-500):
      1. It required TABLE OWNERSHIP. If the app's runtime role wasn't the
         owner (e.g. after a PITR restore reassigned ownership) the ALTER
         raised `must be owner of table`.
      2. It took a table-level lock that conflicts with concurrent turn
         commits writing those same tables, so under live load it could block
         and then time out.
      3. Worst: the ALTER ran inside the delete transaction, so ANY failure
         (either of the above) poisoned the transaction. The `except: pass`
         around it swallowed the real error, and the very next DELETE then
         raised `current transaction is aborted, commands ignored ...`, which
         was NOT caught — the request 500'd and the cohort survived the
         rollback. `SET LOCAL` on a namespaced custom GUC needs no ownership,
         no superuser and no lock, and cannot fail this way.

    The guard (fn_immutable_guard) checks `current_setting('muressons.allow_purge')`
    and, when it is 'on', allows the UPDATE/DELETE; the flag is set nowhere
    else, so ordinary writes are still rejected exactly as before.
    """
    await conn.execute("SET LOCAL muressons.allow_purge = 'on'")


# ── Connection Pool ─────────────────────────────────────────────

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_MIN_CONNECTIONS,
            max_size=DB_MAX_CONNECTIONS,
            # PERF-AUDIT-2026-07-29: bound query execution too. An acquire
            # timeout only helps if connections are actually returned; a query
            # that hangs would otherwise pin one for the rest of the class.
            command_timeout=DB_COMMAND_TIMEOUT_SECONDS,
        )
        # ── Auto-schema: create tables if they don't exist ──────────
        # Railway's managed Postgres does NOT auto-run init.sql.
        # This block is idempotent — safe on both fresh and existing DBs.
        async with _pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
            # Extensions are best-effort: gen_random_uuid() is BUILT IN since
            # Postgres 13, so the schema no longer depends on uuid-ossp. Some
            # managed/minimal Postgres builds (and the CI/pgserver instances the
            # parity suite runs on) do not ship the extension control files, and
            # a hard failure here used to abort the whole auto-schema.
            for _ext in ('"uuid-ossp"', '"pgcrypto"'):
                try:
                    await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {_ext};")
                except Exception:
                    pass  # optional — schema uses gen_random_uuid() (built-in)
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE consensus_level AS ENUM (
                        'unanimous','majority','split','facilitator_override'
                    );
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cohort_name         VARCHAR(120)    NOT NULL,
                    facilitator_id      VARCHAR(80)     NOT NULL,
                    start_time          TIMESTAMPTZ     NOT NULL DEFAULT now(),
                    end_time            TIMESTAMPTZ,
                    final_terminal_value            NUMERIC(18,2),
                    final_regenerative_multiple     NUMERIC(8,4),
                    metadata            JSONB           DEFAULT '{}'::jsonb,
                    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_cohort ON sessions (cohort_name);
                CREATE INDEX IF NOT EXISTS idx_sessions_start  ON sessions (start_time);

                CREATE TABLE IF NOT EXISTS global_round_states (
                    state_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id          UUID            NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    round_number        SMALLINT        NOT NULL CHECK (round_number BETWEEN 1 AND 10),
                    corporate_treasury  NUMERIC(18,2)   NOT NULL,
                    group_reputation    NUMERIC(6,2)    NOT NULL,
                    synergy_multiplier  NUMERIC(6,4)    NOT NULL DEFAULT 1.0,
                    cost_of_capital     NUMERIC(6,4)    NOT NULL DEFAULT 0.05,
                    active_event_flags  JSONB           NOT NULL DEFAULT '{}',
                    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
                    CONSTRAINT uq_session_round UNIQUE (session_id, round_number)
                );
                CREATE INDEX IF NOT EXISTS idx_grs_session    ON global_round_states (session_id);
                CREATE INDEX IF NOT EXISTS idx_grs_round      ON global_round_states (round_number);

                CREATE TABLE IF NOT EXISTS bu_round_states (
                    bu_state_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    global_state_id         UUID            NOT NULL REFERENCES global_round_states(state_id) ON DELETE CASCADE,
                    bu_id                   VARCHAR(40)     NOT NULL,
                    revenue_base            NUMERIC(18,2)   NOT NULL,
                    opex_base               NUMERIC(18,2)   NOT NULL,
                    natural_capital_debt    NUMERIC(12,2)   NOT NULL DEFAULT 0,
                    social_license_score    NUMERIC(6,2)    NOT NULL DEFAULT 50,
                    reputation_score        NUMERIC(6,2)    NOT NULL DEFAULT 50,
                    governance_risk_score   NUMERIC(6,2)    NOT NULL DEFAULT 0,
                    water_dependency        NUMERIC(6,2)    DEFAULT 0,
                    carbon_intensity        NUMERIC(6,2)    DEFAULT 0,
                    risk_factors            JSONB           NOT NULL DEFAULT '{}',
                    created_at              TIMESTAMPTZ     NOT NULL DEFAULT now(),
                    CONSTRAINT uq_bu_per_round UNIQUE (global_state_id, bu_id)
                );
                CREATE INDEX IF NOT EXISTS idx_bu_global_state ON bu_round_states (global_state_id);
                CREATE INDEX IF NOT EXISTS idx_bu_bu_id        ON bu_round_states (bu_id);

                CREATE TABLE IF NOT EXISTS decision_audit_log (
                    log_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id              UUID            NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    round_number            SMALLINT        NOT NULL CHECK (round_number BETWEEN 1 AND 10),
                    bu_id                   VARCHAR(40),
                    decision_node_id        VARCHAR(120)    NOT NULL,
                    choice_selected         VARCHAR(200)    NOT NULL,
                    capex_allocated         NUMERIC(18,2)   DEFAULT 0,
                    time_to_decision_seconds INTEGER        DEFAULT 0,
                    team_consensus          consensus_level NULL DEFAULT NULL,   -- TEAM-3: NULL = not recorded
                    metadata                JSONB           DEFAULT '{}',
                    created_at              TIMESTAMPTZ     NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_dal_session ON decision_audit_log (session_id);
                CREATE INDEX IF NOT EXISTS idx_dal_round   ON decision_audit_log (round_number);
                CREATE INDEX IF NOT EXISTS idx_dal_node    ON decision_audit_log (decision_node_id);
            """)
            # Immutability triggers (idempotent — DROP IF EXISTS + CREATE)
            #
            # BUG-2026-07-20: the original guard blocked EVERY update, but the
            # app legitimately mutates the CURRENT round in place — materiality
            # budget allocation, CEO-Interview config, panel fees and God-Mode
            # overrides all write to the latest global_round_states row via
            # update_latest_global_state(). On Postgres that raised
            # "Immutability violation: UPDATE on table global_round_states",
            # surfaced to the operator as a generic 500 (CEO-Interview save
            # failed; the double-materiality matrix could not be submitted).
            # In-memory mode has no triggers, so the bug was Postgres-only and
            # invisible in local dev.
            #
            # The design intent is "HISTORICAL rounds are append-only" — the
            # round still being played is not historical. The guard now allows
            # UPDATE on the CURRENT (max round_number) row for a session, while
            # still rejecting updates to completed rounds and ALL deletes (the
            # reset/delete admin paths disable the trigger explicitly, so they
            # are unaffected). decision_audit_log stays strictly append-only.
            await conn.execute("""
                CREATE OR REPLACE FUNCTION fn_immutable_guard()
                RETURNS TRIGGER AS $f$
                DECLARE
                    v_is_current boolean := false;
                BEGIN
                    -- Admin purge/reset/undo paths set a transaction-local flag
                    -- (SET LOCAL muressons.allow_purge = 'on') instead of the old
                    -- ALTER TABLE ... DISABLE TRIGGER dance, which needed table
                    -- ownership, took a lock that blocked live commits, and
                    -- poisoned the delete transaction when it failed (the
                    -- undeletable-cohort / delete-500 bug, 2026-09-02). The flag
                    -- is set nowhere but those paths, so ordinary writes are
                    -- still guarded exactly as before.
                    IF current_setting('muressons.allow_purge', true) = 'on' THEN
                        RETURN COALESCE(NEW, OLD);
                    END IF;

                    IF TG_OP = 'DELETE' THEN
                        RAISE EXCEPTION
                            'Immutability violation: DELETE on "%" is not allowed. '
                            'Historical round data is append-only.', TG_TABLE_NAME;
                    END IF;

                    IF TG_TABLE_NAME = 'global_round_states' THEN
                        SELECT OLD.round_number = MAX(round_number)
                          FROM global_round_states
                          WHERE session_id = OLD.session_id
                          INTO v_is_current;
                    ELSIF TG_TABLE_NAME = 'bu_round_states' THEN
                        SELECT g.round_number = (
                                 SELECT MAX(round_number) FROM global_round_states
                                 WHERE session_id = g.session_id)
                          FROM global_round_states g
                          WHERE g.state_id = OLD.global_state_id
                          INTO v_is_current;
                    ELSE
                        -- decision_audit_log and anything else: strictly append-only.
                        v_is_current := false;
                    END IF;

                    IF v_is_current THEN
                        RETURN NEW;  -- current round is mutable
                    END IF;

                    RAISE EXCEPTION
                        'Immutability violation: UPDATE on historical round data in "%" '
                        'is not allowed. Only the current round may be modified.',
                        TG_TABLE_NAME;
                END;
                $f$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS trg_immutable_global_round_states ON global_round_states;
                CREATE TRIGGER trg_immutable_global_round_states
                    BEFORE UPDATE OR DELETE ON global_round_states
                    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

                DROP TRIGGER IF EXISTS trg_immutable_bu_round_states ON bu_round_states;
                CREATE TRIGGER trg_immutable_bu_round_states
                    BEFORE UPDATE OR DELETE ON bu_round_states
                    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

                DROP TRIGGER IF EXISTS trg_immutable_decision_audit_log ON decision_audit_log;
                CREATE TRIGGER trg_immutable_decision_audit_log
                    BEFORE UPDATE OR DELETE ON decision_audit_log
                    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();
            """)
            print("[POSTGRES] Auto-schema: tables, indexes, and immutability triggers verified.")

        # Ensure metadata column exists (for DBs created by older init.sql without it)
        async with _pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
            await conn.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;")
            # F-28 (launch audit 2026-09-01): parent_cohort_id and player_id live
            # in the JSONB. Sibling lookups (leaderboard, peer trends, pacing
            # round probe, shockwave, cohort undo) used to fetch EVERY session on
            # the platform and filter in Python — work that grew with platform
            # history, not cohort size. Expression indexes let the store answer
            # "children of cohort X" / "session of player P" directly; the write
            # path is untouched (no dual-write, no backfill).
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_parent_cohort "
                "ON sessions ((metadata->>'parent_cohort_id'));")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_player_id "
                "ON sessions ((metadata->>'player_id'));")

        # ── TEAM-3 (UX audit #7, 2026-08-02): team_consensus becomes nullable ──
        # The client used to hardcode 'majority' on every commit, so the audit
        # log asserted a consensus nobody recorded. The driver now answers in the
        # review modal, but rounds committed before this shipped — and every
        # server auto-commit — have no answer, and that must be distinguishable
        # from a real 'majority'.
        #
        # Idempotent and forward-only, matching the metadata pattern above:
        #   • add 'not_recorded' to the enum if missing
        #   • drop the NOT NULL and the 'majority' default
        # Existing rows are NOT rewritten — backfilling them to 'not_recorded'
        # would be a guess about history, and these rows sit behind an
        # immutability trigger. Old rows keep 'majority'; new ones tell the truth.
        async with _pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
            try:
                await conn.execute(
                    "ALTER TYPE consensus_level ADD VALUE IF NOT EXISTS 'not_recorded';"
                )
            except Exception as _enum_exc:
                print(f"[POSTGRES] consensus_level enum extend skipped (non-fatal): {_enum_exc}")
            try:
                await conn.execute(
                    "ALTER TABLE decision_audit_log ALTER COLUMN team_consensus DROP NOT NULL;"
                )
                await conn.execute(
                    "ALTER TABLE decision_audit_log ALTER COLUMN team_consensus DROP DEFAULT;"
                )
                print("[POSTGRES] TEAM-3: team_consensus is nullable (NULL = not recorded).")
            except Exception as _tc_exc:
                print(f"[POSTGRES] team_consensus nullability migration skipped (non-fatal): {_tc_exc}")
        
        # Populate database_memory._sessions from DB for synchronous access parity
        try:
            from database_memory import _sessions
            async with _pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
                rows = await conn.fetch("SELECT session_id, cohort_name, facilitator_id, start_time, metadata FROM sessions")
                for row in rows:
                    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                    _sessions[str(row["session_id"])] = {
                        "session_id": str(row["session_id"]),
                        "cohort_name": row["cohort_name"],
                        "facilitator_id": row["facilitator_id"],
                        "start_time": row["start_time"],
                        **metadata
                    }
        except Exception as e:
            print(f"[POSTGRES] Failed to pre-populate in-memory session cache: {e}")

    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── SEC-5: Cross-process commit serialization (advisory locks) ──
# The per-session asyncio.Lock in router.py only serializes within a single
# process. Once the app runs with >1 worker/instance, two simultaneous commits
# for the same session can land on different workers and both proceed,
# corrupting round state. A Postgres session-level advisory lock provides the
# missing cross-process mutual exclusion. We use the *try* variant so callers
# fast-fail with HTTP 409 on contention (matching the existing asyncio
# fast-fail) rather than blocking and piling up connections.

async def acquire_advisory_lock(session_id: str):
    """Try to take a cross-process advisory lock for this session.

    Returns the held asyncpg connection on success (caller MUST later pass it
    to release_advisory_lock). Returns None if the lock is already held by
    another process — the caller should treat that as a 409 conflict.

    PERF-AUDIT-2026-07-29: this connection is held for the WHOLE commit while
    the commit's own queries acquire further connections from the same pool.
    That makes each in-flight commit cost ~2 connections, so a cohort larger
    than pool_size/2 committing together exhausted the pool — and because
    `pool.acquire()` had no timeout, the requests waited on each other
    FOREVER rather than erroring. Measured on real Postgres: 12 simultaneous
    commits with the old default pool of 10 never returned; the same 12 with a
    pool of 40 finished in 0.4s. That is precisely the moment a class commits
    a round together, so it had to be fixed on both axes:
      * the default pool now exceeds the 20-player roster ceiling (config.py);
      * and this acquire times out, so an exhausted pool surfaces as a clean
        error the facilitator can see instead of a silent hang.
    """
    pool = await get_pool()
    try:
        conn = await pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database connection pool exhausted — too many simultaneous "
                "commits. Retry in a moment; if this persists, raise "
                "DB_MAX_CONNECTIONS above the cohort roster size."
            ),
        )
    try:
        # hashtext() maps the session_id to a stable int4 key, identical across
        # processes (unlike Python's randomized hash()).
        got = await conn.fetchval("SELECT pg_try_advisory_lock(hashtext($1))", session_id)
        if not got:
            await pool.release(conn)
            return None
        return conn
    except Exception:
        # On any error acquiring the lock, don't leak the connection.
        try:
            await pool.release(conn)
        except Exception:
            pass
        raise


async def release_advisory_lock(conn, session_id: str) -> None:
    """Release the advisory lock held on `conn` and return it to the pool."""
    if conn is None:
        return
    try:
        await conn.fetchval("SELECT pg_advisory_unlock(hashtext($1))", session_id)
    finally:
        try:
            await get_pool_release(conn)
        except Exception:
            pass


async def get_pool_release(conn) -> None:
    """Release a connection back to the pool (small indirection for testability)."""
    pool = await get_pool()
    await pool.release(conn)


# ── Seed Data ───────────────────────────────────────────────────

def _load_seed(industry: str = "generic") -> dict:
    """Load the Round 1 seed JSON from the db folder."""
    import pathlib
    filename = "seed_healthcare.json" if industry == "healthcare" else "seed_round1.json"
    seed_path = pathlib.Path(__file__).resolve().parent.parent / "db" / filename
    with open(seed_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ── Session Operations ──────────────────────────────────────────

async def update_session_metadata(session_id: str, updates: dict) -> bool:
    """Public API: update the metadata dict for a session. Both backends implement this."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        row = await conn.fetchrow(
            "SELECT metadata FROM sessions WHERE session_id = $1",
            uuid.UUID(session_id),
        )
        if row is None:
            return False
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        metadata.update(updates)
        await conn.execute(
            "UPDATE sessions SET metadata = $2 WHERE session_id = $1",
            uuid.UUID(session_id),
            _dumps(metadata),
        )
        # Update memory cache too
        from database_memory import _sessions
        if session_id in _sessions:
            _sessions[session_id].update(updates)
        return True

# Keep private alias for any legacy internal callers during transition
_update_session_metadata = update_session_metadata


async def create_session(
    cohort_name: str, 
    facilitator_id: Optional[str] = None,
    loan_interest_rate: float = 0.12,
    player_id: Optional[str] = None,
    parent_cohort_id: Optional[str] = None,
    decision_paradigm: str = "legacy_abc",
    currency_symbol: str = "$",
    scenario_preset: Optional[str] = None,
    experience_level: Optional[str] = None,
    difficulty_tier: Optional[str] = None,
    created_by: Optional[str] = None,
    created_when: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    assigned_bu: Optional[str] = None,
    region_id: Optional[str] = None,
    simulation_mode: Optional[str] = None,
    industry_vertical: Optional[str] = None,
    rules_version: Optional[str] = None,
) -> dict:
    """
    Create a new session, insert the Round 1 global state and all BU
    states from the seed JSON. Returns a dict ready for the API response.
    """
    # Prevent duplicate cohort names for top-level sessions
    if not parent_cohort_id:
        pool = await get_pool()
        async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
            rows = await conn.fetch(
                "SELECT session_id, metadata FROM sessions WHERE LOWER(TRIM(cohort_name)) = LOWER(TRIM($1))",
                cohort_name
            )
            for r in rows:
                meta = json.loads(r["metadata"]) if r["metadata"] else {}
                if not meta.get("parent_cohort_id"):
                    raise ValueError(f"A cohort named '{cohort_name}' already exists.")

    if decision_paradigm == "brsr_ngrbc" and currency_symbol == "$":
        currency_symbol = "₹"

    # Determine seed based on paradigm
    from admin_shared import _god_mode_settings
    from rules import CURRENT_VERSION as _CURRENT_RULES_VERSION
    _PARADIGM_INDUSTRY_MAP = {"healthcare": "healthcare"}
    industry = _PARADIGM_INDUSTRY_MAP.get(decision_paradigm, _god_mode_settings.get("industry", "generic"))
    seed = _load_seed(industry=industry)

    session_id = str(uuid.uuid4())
    global_state_id = str(uuid.uuid4())
    gs = seed["global_state"]
    bus = seed["business_units"]

    # If paradigm is un_sdg, dynamically inject non-zero baselines (50.0) for SDG clusters
    if decision_paradigm == "un_sdg":
        for bu in bus:
            for cluster in ["basic_needs", "human_capital", "sustainable_growth", "planet", "governance", "partnerships"]:
                if cluster not in bu:
                    bu[cluster] = 50.0

    # Calculate baseline metrics
    n = len(bus) or 1

    # Single-BU mode: restrict bu_states to only the assigned BU.
    # Mirrors database_memory.create_session — see comments there.
    if assigned_bu:
        _slot = assigned_bu
        _vertical = (industry_vertical or "").strip()
        try:
            from bu_profiles import SLOT_FIT_MAP, BU_PROFILES, build_bu_states
            _seed_ids = {b.get("bu_id") for b in bus}
            if _slot not in _seed_ids:
                _vertical = _vertical or _slot
                _slot = next(
                    (s for s, vs in SLOT_FIT_MAP.items() if _slot == s or _slot in vs),
                    _slot,
                )
            if (
                simulation_mode == "single_bu"
                and _vertical
                and _vertical != _slot
                and _vertical in BU_PROFILES
            ):
                filtered = [b for b in build_bu_states({_slot: _vertical})
                            if b.get("bu_id") == _vertical]
            else:
                filtered = [b for b in bus if b.get("bu_id") == _slot]
        except Exception:
            filtered = [b for b in bus if b.get("bu_id") == assigned_bu]
        if filtered:
            bus = filtered
            assigned_bu = filtered[0].get("bu_id", assigned_bu)
        elif simulation_mode == "single_bu":
            bus = [bus[0]] if bus else bus
            if bus:
                assigned_bu = bus[0].get("bu_id", assigned_bu)
        # else conglomerate mode with unknown bu_id — fall through with all BUs (defensive)

    # ── Single-BU mode: scale treasury proportionally ──
    # When running with 1 BU out of N total, divide treasury by N so the
    # player doesn't start with a disproportionately large cash cushion.
    _treasury_val = SIM_INITIAL_BUDGET
    if assigned_bu:
        total_bus_in_seed = len(seed.get("business_units", []))
        if total_bus_in_seed > 1:
            _treasury_val = round(_treasury_val / total_bus_in_seed, 2)


    # Recalculate after possible BU filtering
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

    # Generate a friendly short code for top-level cohort sessions
    from database_memory import _generate_short_code
    short_code = _generate_short_code() if not parent_cohort_id else None

    # Anti-gaming option shuffle seed
    from option_shuffle import generate_shuffle_seed
    _shuffle_seed = generate_shuffle_seed()

    # Metadata to store in database sessions.metadata
    from config_introspect import run_provenance as _run_provenance
    from rng_util import resolve_or_derive_seed as _resolve_or_derive_seed

    metadata = {
        "short_code": short_code,
        "is_public": False,
        "allowed_player_ids": [],
        "player_id": player_id,
        "parent_cohort_id": parent_cohort_id,
        "decision_paradigm": decision_paradigm,
        "currency_symbol": currency_symbol,
        "scenario_preset": scenario_preset,
        "experience_level": experience_level,
        "difficulty_tier": difficulty_tier or "advanced",
        # Phase 4 (dead-flag remediation): the rule set this session is
        # pinned to for its whole life. Sessions created before this key
        # existed have no value and resolve to rules.DEFAULT_RULES_VERSION,
        # which IS the semantics they were played under.
        "rules_version": rules_version or _CURRENT_RULES_VERSION,
        "created_by": created_by,
        "created_when": created_when,
        "start_date": start_date,
        "end_date": end_date,
        "shuffle_seed": _shuffle_seed,
        "assigned_bu": assigned_bu or "",
        "region_id": region_id or "",
        "simulation_mode": simulation_mode or "",
        "industry_vertical": industry_vertical or "",
        # 4.7 (2026-08-03): stamp what produced this run, at the moment it is
        # true. Seed + config fingerprint + code version are the three things
        # that decide the numbers a cohort sees; a finished session recorded
        # none of them, so two runs a month apart with a config change between
        # them were indistinguishable in the database. Computed from the SAME
        # resolver the engine's seed comes from, so provenance cannot claim a
        # seed the run did not use.
        "run_provenance": _run_provenance(
            _resolve_or_derive_seed(gs.get("active_event_flags"),
                                    parent_cohort_id or session_id)),
    }

    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        async with conn.transaction():
            # 1. Session row
            await conn.execute(
                """
                INSERT INTO sessions (session_id, cohort_name, facilitator_id, metadata)
                VALUES ($1, $2, $3, $4)
                """,
                uuid.UUID(session_id),
                cohort_name,
                facilitator_id or "admin",
                _dumps(metadata),
            )
            
            # Prepare global state flags
            flags = {
                **gs.get("active_event_flags", {}),
                "loan_interest_rate": loan_interest_rate,
                "bonus_score": 0,
                "historical_ebitda": baseline_ebitda,
                "tco2e_emissions": baseline_tco2e,
                "vrio_capabilities": baseline_vrio,
                "green_transition_fund": 0.0,
                "tipping_point_active": False,
                "pending_capex_projects": [],
                "inflation_index": 0.025,
                "competitor_ebitda": baseline_ebitda,
                # PARITY (2026-07-31, gap #4): the memory backend seeds these
                # two at creation — with a comment explaining that the engine
                # only ever sees global_state, so stakeholder/materiality
                # resolution reads industry x region FROM THE FLAGS. This twin
                # was never updated, so under Postgres every cohort resolved
                # with no vertical and no region: admin-uploaded vertical and
                # regional Excel configs (stakeholders AND materiality) were
                # silently invisible during play, while the same cohort in
                # memory mode showed them. Empty strings are ignored by the
                # resolvers, exactly as in database_memory.create_session.
                "industry_vertical": industry_vertical or "",
                "region_id": region_id or "",
            }

            # 4.2 (2026-08-03): every cohort gets a stochastic seed, always.
            # `rng_seed` was a cohort setting defaulting to "" — and empty means
            # event_rng() returns a SYSTEM-seeded Random, so a facilitator who
            # never opened the advanced settings ran an unrepeatable, unrecorded
            # simulation and was told nothing. Reproducibility was an unticked
            # checkbox. Derived from the parent cohort id so all twenty teams
            # share one stream (GAME-4); never overwrites an explicit seed.
            from rng_util import ensure_cohort_seed
            ensure_cohort_seed(flags, parent_cohort_id or session_id)

            # C2: seed effective climate inputs (global + per-cohort override)
            # into active_event_flags so the engine sees resolved values.
            try:
                from admin_shared import seed_effective_flags
                seed_effective_flags(session_id, flags)
            except Exception:
                pass

            if decision_paradigm == "brsr_ngrbc":
                from brsr_controller import init_brsr_state
                init_brsr_state(flags, bus, {})

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
                _treasury_val,
                gs["group_reputation_score"],
                gs["group_synergy_multiplier"],
                gs["cost_of_capital_rate"],
                _dumps(flags),
            )

            # 3. BU round states
            for bu in bus:
                explicit_columns = {
                    "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                    "social_license_score", "reputation_score", "governance_risk_score",
                    "water_dependency", "carbon_intensity"
                }
                rf = dict(bu.get("risk_factors", {}))
                for k, v in bu.items():
                    if k not in explicit_columns and k != "risk_factors":
                        rf[k] = v

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
                    _dumps(rf),
                )

    # Populate cache in database_memory._sessions
    from database_memory import _sessions
    _sessions[session_id] = {
        "session_id": session_id,
        "cohort_name": cohort_name,
        "facilitator_id": facilitator_id,
        "start_time": datetime.now(timezone.utc),
        **metadata
    }

    res_gs = {
        "corporate_treasury": _treasury_val,
        "group_reputation": gs["group_reputation_score"],
        "synergy_multiplier": gs["group_synergy_multiplier"],
        "cost_of_capital": gs["cost_of_capital_rate"],
        "active_event_flags": flags,
    }
    for k, v in flags.items():
        if k not in res_gs:
            res_gs[k] = v

    return {
        "session_id": session_id,
        "round_number": 1,
        "global_state": res_gs,
        "business_units": bus,
    }


# ── Fetch Operations ───────────────────────────────────────────

async def get_session_info(session_id: str) -> Optional[dict]:
    """Return basic session metadata by ID."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        row = await conn.fetchrow(
            "SELECT session_id, cohort_name, facilitator_id, start_time, metadata FROM sessions WHERE session_id = $1",
            uuid.UUID(session_id),
        )
        if row is None:
            return None
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        res = {
            "session_id": str(row["session_id"]),
            "cohort_name": row["cohort_name"],
            "facilitator_id": row["facilitator_id"],
            "start_time": row["start_time"],
        }
        res.update(metadata)
        return res


def resolve_cohort_id_sync(session_id: str) -> str:
    """Map ANY session id to the cohort that owns its settings — synchronously.

    Parity API. A player who joins a cohort gets their OWN sub-session, and
    that id is what every player-side request carries. Per-cohort settings live
    on the PARENT, so a gate evaluated with the child id silently resolves to
    the platform default. That is how Stakeholder Negotiation Rooms stayed
    403 "not enabled for this cohort" after the facilitator had enabled them.

    Sync on purpose: the callers (get_effective_settings and the gates built on
    it) are synchronous, and making them async would ripple through most of the
    admin surface. Both backends read the same synchronous session cache, which
    database.py maintains under Postgres precisely for this kind of access.

    Returns the parent cohort id when `session_id` is a sub-session, otherwise
    `session_id` unchanged (including for unknown ids — callers fall back to
    the global view rather than failing closed).
    """
    # `database_memory._sessions` is NOT the memory store here: under Postgres
    # it is the synchronous access-parity cache this module fills at pool init
    # and refreshes on every session create/metadata update (see get_pool and
    # update_session_metadata). Reading it is the sanctioned sync path; the
    # async truth is get_session_info().
    try:
        from database_memory import _sessions
        rec = _sessions.get(session_id) or {}
        return rec.get("parent_cohort_id") or session_id
    except Exception:
        return session_id


async def fetch_session_by_cohort(cohort_name: str) -> Optional[dict]:
    """Look up an existing session by cohort_name and return its latest state."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        row = await conn.fetchrow(
            """
            SELECT session_id
            FROM sessions
            WHERE LOWER(TRIM(cohort_name)) = LOWER(TRIM($1))
            ORDER BY created_at DESC
            LIMIT 1
            """,
            cohort_name
        )
        if row is None:
            return None
            
        state = await fetch_latest_state(str(row["session_id"]))
        if state:
            state["session_id"] = str(row["session_id"])
        return state


async def resolve_join_code(code: str) -> Optional[str]:
    """Resolve a short join code to a session_id. Returns None if not found.

    PARITY (2026-07-31 audit): this accessor existed only in the memory
    backend, so the short-code join path (`/public/join/{code}`) raised
    AttributeError → 500 under Postgres — a student joining by code in a
    production classroom crashed. Postgres stores short_code in the session
    metadata (create_session writes it), which is mirrored into the shared
    session cache; scan that, falling back to a direct metadata query so the
    answer does not depend on cache warmth.
    """
    wanted = (code or "").strip().upper()
    if not wanted:
        return None
    try:
        for sid, sess in list(_sessions.items()):
            if (sess.get("short_code") or "").upper() == wanted:
                return sid
    except Exception:
        pass
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch("SELECT session_id, metadata FROM sessions")
        for row in rows:
            try:
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
            except (TypeError, ValueError):
                continue
            if (meta.get("short_code") or "").upper() == wanted:
                return str(row["session_id"])
    return None


async def get_decision_log(session_id: str) -> list[dict]:
    """All decisions for a session and its child player sessions.

    PARITY (2026-07-31 audit): memory-only until now — the decision-journey
    and admin decision views 500'd under Postgres. The data was ALWAYS
    persisted (decision_audit_log, written by insert_next_round); only this
    accessor was missing. Shape mirrors database_memory.get_decision_log:
    entries carry player_id and cohort_name from the owning session, sorted
    by (round, player).
    """
    related: dict[str, dict] = {}
    sess = await get_session_info(session_id)
    if sess:
        related[session_id] = sess
    for child in await get_child_sessions(session_id):
        related[str(child.get("session_id"))] = child

    results: list[dict] = []
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        for sid, meta in related.items():
            try:
                rows = await conn.fetch(
                    """
                    SELECT round_number, bu_id, decision_node_id, choice_selected,
                           capex_allocated, time_to_decision_seconds, team_consensus,
                           metadata
                    FROM decision_audit_log
                    WHERE session_id = $1
                    ORDER BY round_number
                    """,
                    uuid.UUID(sid),
                )
            except (ValueError, asyncpg.PostgresError):
                continue
            for row in rows:
                results.append({
                    "session_id": sid,
                    "round_number": int(row["round_number"]),
                    "bu_id": row["bu_id"],
                    "decision_node_id": row["decision_node_id"],
                    "choice_selected": row["choice_selected"],
                    "capex_allocated": float(row["capex_allocated"] or 0),
                    "player_id": meta.get("player_id") or "unknown",
                    "time_to_decision_seconds": int(row["time_to_decision_seconds"] or 0),
                    # TEAM-3: NULL stays NULL — the debrief must be able to say
                    # "not recorded" instead of reporting a consensus that never
                    # happened.
                    "team_consensus": (str(row["team_consensus"]) if row["team_consensus"] else None),
                    # 4.8: surface the envelope. Writing it and not reading it
                    # would be the same defect in a different place.
                    "metadata": _loads_meta(row["metadata"]),
                    "cohort_name": meta.get("cohort_name", ""),
                })
    results.sort(key=lambda x: (x.get("round_number", 0), x.get("player_id", "")))
    return results


async def get_child_sessions(parent_id: str) -> list[dict]:
    """Return all child sessions for a parent session (facilitator views).
    F-28: an indexed lookup on metadata->>'parent_cohort_id' — the table is no
    longer scanned and filtered in Python."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            "SELECT session_id, cohort_name, facilitator_id, start_time, metadata FROM sessions "
            "WHERE metadata->>'parent_cohort_id' = $1",
            str(parent_id),
        )
        res = []
        for row in rows:
            metadata = _loads_meta(row["metadata"])
            sess = {
                "session_id": str(row["session_id"]),
                "cohort_name": row["cohort_name"],
                "facilitator_id": row["facilitator_id"],
                "start_time": row["start_time"],
            }
            sess.update(metadata)
            res.append(sess)
        return res


async def fetch_child_session_ids(parent_id: str) -> list[str]:
    """F-28: just the ids of a cohort's player sub-sessions (indexed)."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            "SELECT session_id FROM sessions WHERE metadata->>'parent_cohort_id' = $1",
            str(parent_id),
        )
    return [str(r["session_id"]) for r in rows]


async def fetch_latest_state(session_id: str) -> Optional[dict]:
    """Return the latest round's global state + BU states for a session."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
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

        flags = json.loads(grs["active_event_flags"]) if isinstance(grs["active_event_flags"], str) else (grs["active_event_flags"] or {})
        
        global_state = {
            "corporate_treasury": float(grs["corporate_treasury"]),
            "group_reputation": float(grs["group_reputation"]),
            "synergy_multiplier": float(grs["synergy_multiplier"]),
            "cost_of_capital": float(grs["cost_of_capital"]),
            "active_event_flags": flags,
        }
        # Unpack dynamic global state fields from active_event_flags
        explicit_global_columns = {
            "corporate_treasury", "group_reputation", "synergy_multiplier",
            "cost_of_capital", "active_event_flags"
        }
        for k, v in flags.items():
            if k not in explicit_global_columns:
                global_state[k] = v

        bu_states = []
        for row in bus:
            rf = json.loads(row["risk_factors"]) if isinstance(row["risk_factors"], str) else (row["risk_factors"] or {})
            bu_dict = {
                "bu_id": row["bu_id"],
                "revenue_base": float(row["revenue_base"]),
                "opex_base": float(row["opex_base"]),
                "natural_capital_debt": float(row["natural_capital_debt"]),
                "social_license_score": float(row["social_license_score"]),
                "reputation_score": float(row["reputation_score"]),
                "governance_risk_score": float(row["governance_risk_score"]),
                "water_dependency": float(row["water_dependency"]) if row["water_dependency"] is not None else 0.0,
                "carbon_intensity": float(row["carbon_intensity"]) if row["carbon_intensity"] is not None else 0.0,
                "risk_factors": rf,
            }
            # Unpack dynamic BU fields from risk_factors
            explicit_bu_columns = {
                "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                "social_license_score", "reputation_score", "governance_risk_score",
                "water_dependency", "carbon_intensity", "risk_factors"
            }
            for k, v in rf.items():
                if k not in explicit_bu_columns:
                    bu_dict[k] = v
            bu_states.append(bu_dict)

        # 4.1: the SELECT above says ORDER BY bu_id, which is alphabetical and
        # therefore a different order from the memory backend's (slot order).
        # The engine indexes this list positionally, so that difference decided
        # which business unit the micro-strike hit — differently in production
        # than in any test. Re-order canonically here rather than in SQL: the
        # canonical order depends on global_state["bu_substitutions"], which is
        # not available to the query, and doing it in Python keeps ONE
        # definition of the order for both backends.
        from bu_profiles import sort_bu_states_canonically
        bu_states = sort_bu_states_canonically(bu_states, global_state)

        return {
            "state_id": str(grs["state_id"]),
            "round_number": grs["round_number"],
            "global_state": global_state,
            "bu_states": bu_states,
        }


async def fetch_latest_round(session_id: str) -> Optional[int]:
    """PER-2: cheap latest-round lookup -- one indexed scalar query,
    avoiding the fetchrow + BU fetch that fetch_latest_state performs.
    Used for the per-sibling commit-count fan-out."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rn = await conn.fetchval(
            """
            SELECT round_number FROM global_round_states
            WHERE session_id = $1
            ORDER BY round_number DESC
            LIMIT 1
            """,
            uuid.UUID(session_id),
        )
    return int(rn) if rn is not None else None


async def fetch_latest_rounds(session_ids: list[str]) -> dict[str, int]:
    """F-27: latest round for MANY sessions in ONE indexed query. The dashboard
    poll used to issue fetch_latest_round once per sibling, twice (commit badge
    and free-advance status) — 10 round-trips per poll for a 5-team cohort."""
    ids = []
    for sid in session_ids:
        try:
            ids.append(uuid.UUID(str(sid)))
        except (ValueError, TypeError, AttributeError):
            continue
    if not ids:
        return {}
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, MAX(round_number) AS rn
            FROM global_round_states
            WHERE session_id = ANY($1::uuid[])
            GROUP BY session_id
            """,
            ids,
        )
    return {str(r["session_id"]): int(r["rn"]) for r in rows if r["rn"] is not None}


async def fetch_round_history(session_id: str, since_round: int | None = None, include_final: bool = False) -> list[dict]:
    """Return the rounds of a session (for the dashboard history), oldest first.

    F-27 (launch audit 2026-09-01): two changes for the 5-second dashboard poll.
      * `since_round` is pushed into SQL (rounds >= N) instead of fetching the
        whole game and filtering in Python — the poller only ever needs the
        newest round or two.
      * The BU rows and decision rows for ALL selected rounds are fetched in
        one query each (`= ANY($1)`), so a dashboard costs 3 round-trips
        regardless of how many rounds have been played, not 1 + 2×rounds
        (21 at R10, ×150 teams polling).
    """
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        _sid = uuid.UUID(session_id)
        if since_round is None:
            rounds = await conn.fetch(
                """
                SELECT state_id, round_number, corporate_treasury,
                       group_reputation, synergy_multiplier, cost_of_capital,
                       active_event_flags
                FROM global_round_states
                WHERE session_id = $1
                ORDER BY round_number
                """,
                _sid,
            )
        else:
            rounds = await conn.fetch(
                """
                SELECT state_id, round_number, corporate_treasury,
                       group_reputation, synergy_multiplier, cost_of_capital,
                       active_event_flags
                FROM global_round_states
                WHERE session_id = $1 AND round_number >= $2
                ORDER BY round_number
                """,
                _sid, int(since_round),
            )
        if not rounds:
            return []

        state_ids = [grs["state_id"] for grs in rounds]
        min_round = min(int(grs["round_number"]) for grs in rounds)
        bu_rows = await conn.fetch(
            """
            SELECT global_state_id, bu_id, revenue_base, opex_base,
                   natural_capital_debt, social_license_score,
                   reputation_score, governance_risk_score,
                   water_dependency, carbon_intensity,
                   risk_factors
            FROM bu_round_states
            WHERE global_state_id = ANY($1::uuid[])
            ORDER BY bu_id
            """,
            state_ids,
        )
        dec_rows = await conn.fetch(
            """
            SELECT round_number, bu_id, decision_node_id, choice_selected, capex_allocated,
                   time_to_decision_seconds, team_consensus, metadata
            FROM decision_audit_log
            WHERE session_id = $1 AND round_number >= $2
            """,
            _sid, min_round,
        )
        bus_by_state: dict = {}
        for row in bu_rows:
            bus_by_state.setdefault(row["global_state_id"], []).append(row)
        decs_by_round: dict = {}
        for row in dec_rows:
            decs_by_round.setdefault(int(row["round_number"]), []).append(row)

        history = []
        for grs in rounds:
            bus = bus_by_state.get(grs["state_id"], [])
            decs = decs_by_round.get(int(grs["round_number"]), [])

            flags = json.loads(grs["active_event_flags"]) if isinstance(grs["active_event_flags"], str) else (grs["active_event_flags"] or {})
            global_state = {
                "corporate_treasury": float(grs["corporate_treasury"]),
                "group_reputation": float(grs["group_reputation"]),
                "synergy_multiplier": float(grs["synergy_multiplier"]),
                "cost_of_capital": float(grs["cost_of_capital"]),
                "active_event_flags": flags,
            }
            explicit_global_columns = {
                "corporate_treasury", "group_reputation", "synergy_multiplier",
                "cost_of_capital", "active_event_flags"
            }
            for k, v in flags.items():
                if k not in explicit_global_columns:
                    global_state[k] = v

            bu_states = []
            for row in bus:
                rf = json.loads(row["risk_factors"]) if isinstance(row["risk_factors"], str) else (row["risk_factors"] or {})
                bu_dict = {
                    "bu_id": row["bu_id"],
                    "revenue_base": float(row["revenue_base"]),
                    "opex_base": float(row["opex_base"]),
                    "natural_capital_debt": float(row["natural_capital_debt"]),
                    "social_license_score": float(row["social_license_score"]),
                    "reputation_score": float(row["reputation_score"]),
                    "governance_risk_score": float(row["governance_risk_score"]),
                    "water_dependency": float(row["water_dependency"]) if row["water_dependency"] is not None else 0.0,
                    "carbon_intensity": float(row["carbon_intensity"]) if row["carbon_intensity"] is not None else 0.0,
                    "risk_factors": rf,
                }
                explicit_bu_columns = {
                    "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                    "social_license_score", "reputation_score", "governance_risk_score",
                    "water_dependency", "carbon_intensity", "risk_factors"
                }
                for k, v in rf.items():
                    if k not in explicit_bu_columns:
                        bu_dict[k] = v
                bu_states.append(bu_dict)

            history.append({
                "round_number": grs["round_number"],
                "global_state": global_state,
                "business_units": bu_states,
                "decisions": [
                    {
                        "bu_id": row["bu_id"],
                        "decision_node_id": row["decision_node_id"],
                        "choice_selected": row["choice_selected"],
                        "capex": float(row["capex_allocated"] or 0),
                        "time_to_decision_seconds": row["time_to_decision_seconds"],
                        "team_consensus": row["team_consensus"],
                    }
                    for row in decs
                ],
            })
        # SEAM-08 (audit 2026-09-04): parity with database_memory — row K = the
        # state entering K, R10 included; the closing state as round 11 /
        # is_final only when asked.
        from history_semantics import splice_final_state
        return splice_final_state(history, include_final=include_final)


# ── Insert Next-Round State ────────────────────────────────────

async def insert_next_round(
    session_id: str,
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    decisions: list[dict],
) -> str:
    """Persist the new round state and audit log entries. Returns the new global_state_id."""
    pool = await get_pool()
    global_state_id = str(uuid.uuid4())

    # Put extra global fields into active_event_flags
    flags = dict(global_state.get("active_event_flags", {}))
    explicit_global_columns = {
        "state_id", "session_id", "round_number", "corporate_treasury",
        "group_reputation", "synergy_multiplier", "cost_of_capital",
        "active_event_flags"
    }
    for k, v in global_state.items():
        if k not in explicit_global_columns:
            flags[k] = v

    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
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
                _dumps(flags),
            )

            # BU states
            for bu in bu_states:
                explicit_columns = {
                    "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                    "social_license_score", "reputation_score", "governance_risk_score",
                    "water_dependency", "carbon_intensity"
                }
                rf = dict(bu.get("risk_factors", {}))
                for k, v in bu.items():
                    if k not in explicit_columns and k != "risk_factors":
                        rf[k] = v

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
                    _dumps(rf),
                )

            # AUDIT-1 (2026-08-02): decisions are filed under the round they were
            # MADE in, which is `round_number - 1`.
            #
            # This used to pass `round_number` — the round the commit CREATED.
            # The effect was that a team's round-3 choices were stored as round 4,
            # every set was one round late, and round 1 had no rows at all. Any
            # debrief, grade reconstruction or replay reading decision_audit_log
            # therefore attributed each team's decisions to the wrong round, and
            # showed nothing for the opening round. Found by
            # tests/test_full_run_e2e.py, which is the first test that ever
            # played a full game and then looked at the log.
            #
            # Safe at every call site: all three pass new_round = decision_round
            # + 1 (router.py commit-turn, admin_router.py auto-commit), and the
            # Extended Horizon insert passes decisions=[] so the arithmetic never
            # applies there.
            #
            # NOT backfilled. decision_audit_log is append-only behind an
            # immutability trigger, and rewriting recorded history to match a
            # later opinion is worse than a documented discontinuity: runs
            # committed before this change carry the old offset. No score has
            # been graded from them yet, which is the window that makes this a
            # clean break rather than a migration.
            _decisions_round = max(1, round_number - 1)
            for dec in decisions:
                await conn.execute(
                    """
                    INSERT INTO decision_audit_log
                        (session_id, round_number, bu_id,
                         decision_node_id, choice_selected,
                         capex_allocated, time_to_decision_seconds,
                         team_consensus, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    uuid.UUID(session_id),
                    _decisions_round,
                    dec.get("bu_id"),
                    dec.get("decision_node_id", ""),
                    dec.get("choice_selected", ""),
                    dec.get("capex_allocated", 0),
                    dec.get("time_to_decision_seconds", 0),
                    # TEAM-3: no coercion. A missing value means the team did
                    # not record how it decided; write NULL and say so, rather
                    # than inventing 'majority'.
                    dec.get("team_consensus") or None,
                    # 4.8: persist the commit envelope. The column has always
                    # existed and was never written, so pillar_decisions,
                    # dividends, emergency credit, the CFO override and the
                    # engagement action — all engine inputs — were discarded.
                    _dumps(dec.get("metadata") or {}),
                )

    return global_state_id


async def log_decisions(session_id: str, round_number: int, decisions: list[dict]) -> int:
    """Append decisions to the audit trail WITHOUT advancing the round.

    R10-2 (2026-08-02): rounds 1-9 log their decisions as part of
    insert_next_round, but round 10 persists in place via
    update_latest_global_state and never calls it — so the graded finale's
    decisions were written nowhere. commit-turn now calls this for R10.

    Mirrors insert_next_round's decision write EXACTLY, including TEAM-3's
    no-coercion rule on team_consensus. Append-only, and safe under the Postgres
    immutability triggers, which block UPDATE and DELETE on decision_audit_log
    but permit INSERT. Returns the number of rows written.
    """
    if not decisions:
        return 0
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        async with conn.transaction():
            for dec in decisions:
                await conn.execute(
                    """
                    INSERT INTO decision_audit_log
                        (session_id, round_number, bu_id,
                         decision_node_id, choice_selected,
                         capex_allocated, time_to_decision_seconds,
                         team_consensus, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    uuid.UUID(session_id),
                    round_number,
                    dec.get("bu_id"),
                    dec.get("decision_node_id", ""),
                    dec.get("choice_selected", ""),
                    dec.get("capex_allocated", 0),
                    dec.get("time_to_decision_seconds", 0),
                    # TEAM-3: no coercion — NULL means "not recorded".
                    dec.get("team_consensus") or None,
                    # 4.8: persist the commit envelope. The column has always
                    # existed and was never written, so pillar_decisions,
                    # dividends, emergency credit, the CFO override and the
                    # engagement action — all engine inputs — were discarded.
                    _dumps(dec.get("metadata") or {}),
                )
    return len(decisions)


# ── Admin / God Mode Operations ───────────────────────────────

async def count_sessions() -> dict:
    """Mode-agnostic live session counts (Postgres). player_id / parent_cohort_id
    live inside the sessions.metadata JSON, so we read that and classify each row."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch("SELECT metadata FROM sessions")
    cohorts = players = 0
    for row in rows:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        if meta.get("deleted_at"):
            continue
        if meta.get("player_id"):
            players += 1
        else:
            cohorts += 1
    return {"cohorts": cohorts, "players": players}


async def fetch_all_sessions() -> list[dict]:
    """Return all sessions with basic metadata for the admin leaderboard."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, cohort_name, facilitator_id, start_time, metadata
            FROM sessions
            ORDER BY start_time DESC
            """
        )
        res = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            sess_dict = {
                "session_id": str(row["session_id"]),
                "cohort_name": row["cohort_name"],
                "facilitator_id": row["facilitator_id"],
                "start_time": row["start_time"].isoformat() if row["start_time"] else None,
            }
            sess_dict.update(metadata)
            res.append(sess_dict)
        return res


async def fetch_all_sessions_raw() -> list[dict]:
    """ALL session records, INCLUDING per-player sub-sessions and shells.

    Parity API (Railway audit §1.1) — the Postgres sessions query already
    returns every row (child relationships live in metadata), so this simply
    reuses it under the parity name the memory store also implements. Aggregate
    endpoints must call this instead of touching a store's private dicts."""
    return await fetch_all_sessions()


def _loads_meta(raw) -> dict:
    """asyncpg hands JSONB back as str on some driver/codec combinations and as
    dict on others. 4.8 readers must not have to care, and must never explode on
    a legacy row whose metadata is NULL or was written before the column was
    used."""
    if not raw:
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:      # noqa: BLE001 — a malformed audit row is not fatal
        return {}


async def fetch_all_decisions() -> list[dict]:
    """Every decision-audit row across all sessions (analytics aggregates).
    Parity API — mirrors database_memory.fetch_all_decisions."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, round_number, bu_id, decision_node_id,
                   choice_selected, capex_allocated, time_to_decision_seconds,
                   team_consensus, metadata
            FROM decision_audit_log
            ORDER BY round_number
            """
        )
        return [
            {
                "session_id": str(r["session_id"]),
                "round_number": r["round_number"],
                "bu_id": r["bu_id"],
                "decision_node_id": r["decision_node_id"],
                "choice_selected": r["choice_selected"],
                "capex_allocated": float(r["capex_allocated"] or 0),
                "time_to_decision_seconds": r["time_to_decision_seconds"],
                "team_consensus": r["team_consensus"],
                # 4.8: the envelope — pillar splits, dividends, CFO override.
                "metadata": _loads_meta(r["metadata"]),
            }
            for r in rows
        ]


async def update_latest_global_state(
    session_id: str,
    global_state: dict,
    bu_states: list[dict],
) -> None:
    """Update the LATEST round's global and BU states in place."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
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

        flags = dict(global_state.get("active_event_flags", {}))
        explicit_global_columns = {
            "state_id", "session_id", "round_number", "corporate_treasury",
            "group_reputation", "synergy_multiplier", "cost_of_capital",
            "active_event_flags"
        }
        for k, v in global_state.items():
            if k not in explicit_global_columns:
                flags[k] = v

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
                _dumps(flags),
            )

            # Update BU states
            for bu in bu_states:
                explicit_columns = {
                    "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                    "social_license_score", "reputation_score", "governance_risk_score",
                    "water_dependency", "carbon_intensity"
                }
                rf = dict(bu.get("risk_factors", {}))
                for k, v in bu.items():
                    if k not in explicit_columns and k != "risk_factors":
                        rf[k] = v

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
                    _dumps(rf),
                )


# ── Undo / Rollback Operations ────────────────────────────────

async def undo_latest_round(session_id: str) -> dict:
    """Delete the latest round's state and restore the previous round."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
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
            # Transaction-local bypass of the append-only guard for this undo
            # (see _allow_immutable_purge) — replaces ALTER TABLE ... DISABLE
            # TRIGGER, which needed ownership, took a lock, and poisoned the
            # transaction on failure.
            await _allow_immutable_purge(conn)

            await conn.execute(
                "DELETE FROM decision_audit_log WHERE session_id = $1 AND round_number = $2",
                uuid.UUID(session_id), deleted_round,
            )
            await conn.execute(
                "DELETE FROM bu_round_states WHERE global_state_id = $1",
                state_id,
            )
            await conn.execute(
                "DELETE FROM global_round_states WHERE state_id = $1",
                state_id,
            )

    return {
        "success": True,
        "deleted_round": deleted_round,
        "new_current_round": deleted_round - 1,
    }


# ── Additional Player/Session CRUD for PostgreSQL ─────────────

async def validate_player_id(session_id: str, player_id: str) -> bool:
    """Validate if a player ID is allowed for a session."""
    info = await get_session_info(session_id)
    if not info:
        return False
    return player_id in info.get("allowed_player_ids", [])


async def set_session_public(session_id: str, is_public: bool) -> bool:
    """Set the visibility of a session (public or private)."""
    return await _update_session_metadata(session_id, {"is_public": is_public})


# F-40 (launch audit 2026-09-01, found while running the fixes on Postgres):
# player ids were only unique WITHIN a cohort. `MUR-XXX` (17,576 values; now
# four letters = 456,976, see config.PLAYER_ID_RANDOM_LETTERS) was
# drawn per cohort and the bulk/induct paths used an in-process counter that
# restarts at MUR-001 on every deploy — so two cohorts on one platform could and
# did hold the same id. Login resolves a player id GLOBALLY, and the default
# password is derived from the id, so the second team to sign in with a
# colliding id landed in the first team's game (or was told its password was
# wrong once that team had personalised theirs). Every mint now checks the
# whole platform, deleted cohorts included, so an id is never reissued.
_PLAYER_ID_IN_USE_SQL = """
    SELECT 1 FROM sessions
    WHERE metadata->>'player_id' = $1
       OR (metadata->'allowed_player_ids') ? $1
       OR (metadata->'registered_players') @> jsonb_build_array(jsonb_build_object('player_id', $1::text))
    LIMIT 1
"""


async def player_id_in_use(player_id: str) -> bool:
    """True if ANY session on the platform (any cohort, any sub-session, deleted
    or not) has issued or is using this player id."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        row = await conn.fetchrow(_PLAYER_ID_IN_USE_SQL, str(player_id))
    return row is not None


async def list_all_player_ids() -> set[str]:
    """Every player id ever issued on the platform (see player_id_in_use)."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch("SELECT metadata FROM sessions")
    out: set[str] = set()
    for row in rows:
        meta = _loads_meta(row["metadata"])
        if meta.get("player_id"):
            out.add(str(meta["player_id"]))
        for pid in meta.get("allowed_player_ids") or []:
            out.add(str(pid))
        for rp in meta.get("registered_players") or []:
            if isinstance(rp, dict) and rp.get("player_id"):
                out.add(str(rp["player_id"]))
    return out


_PLAYER_ID_MINT_ATTEMPTS = 2000



def _player_id_in_registry(player_id: str) -> bool:
    """Wave 3 hygiene: the credential registry (admin_shared._player_registry) can
    hold a record whose session no longer exists; minting that id again would
    make change-password / login find the stale record first."""
    try:
        from admin_shared import _player_registry
    except Exception:  # pragma: no cover — registry unavailable at import time
        return False
    return any(isinstance(p, dict) and p.get("player_id") == player_id for p in _player_registry)

async def generate_player_id(session_id: str) -> Optional[str]:
    """Generate and register a player ID for the session that is unique across
    the WHOLE platform (F-40), not just within this cohort."""
    import random
    import string
    info = await get_session_info(session_id)
    if not info:
        return None
    allowed = info.get("allowed_player_ids", [])
    from config import PLAYER_ID_RANDOM_LETTERS
    _sysrand = random.SystemRandom()   # Wave 3 hygiene: OS entropy, not the seedable process-global Random
    for _ in range(_PLAYER_ID_MINT_ATTEMPTS):
        letters = ''.join(_sysrand.choices(string.ascii_uppercase, k=PLAYER_ID_RANDOM_LETTERS))
        pid = f"MUR-{letters}"
        if pid in allowed:
            continue
        if not await player_id_in_use(pid) and not _player_id_in_registry(pid):
            break
    else:  # pragma: no cover — id space effectively exhausted
        raise RuntimeError("Could not allocate a platform-unique player id; raise PLAYER_ID_RANDOM_LETTERS.")
    allowed.append(pid)
    await _update_session_metadata(session_id, {"allowed_player_ids": allowed})
    return pid


async def get_active_public_sessions() -> list[dict]:
    """Return all active public top-level sessions."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            "SELECT session_id, cohort_name, facilitator_id, start_time, metadata FROM sessions"
        )
        res = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            if metadata.get("is_public") and not metadata.get("parent_cohort_id"):
                sess = {
                    "session_id": str(row["session_id"]),
                    "cohort_name": row["cohort_name"],
                    "facilitator_id": row["facilitator_id"],
                    "start_time": row["start_time"],
                }
                sess.update(metadata)
                res.append(sess)
        return res


async def delete_session(session_id: str, hard: bool = False) -> bool:
    """Delete a single session. Soft-deletes unless hard=True.

    Soft delete (hard=False): marks the session with deleted_at in metadata.
    Hard delete (hard=True): permanently removes all rows from the DB.
      - Explicitly cascades child tables (decision_audit_log, bu_round_states,
        global_round_states) with immutability triggers temporarily disabled,
        matching the pattern used in reset_session_to_round1().
      - Then removes the sessions row itself.
    """
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        row = await conn.fetchrow("SELECT session_id FROM sessions WHERE session_id = $1", uuid.UUID(session_id))
        if row is None:
            return False
        if hard:
            async with conn.transaction():
                # Allow this transaction to delete historical round rows past the
                # append-only guard. Transaction-local flag (see
                # _allow_immutable_purge) — NOT ALTER TABLE ... DISABLE TRIGGER,
                # whose failure used to poison this transaction and 500 the
                # delete while the cohort survived (2026-09-02).
                await _allow_immutable_purge(conn)

                # Cascade: child game-state rows first, then the session itself
                await conn.execute(
                    "DELETE FROM decision_audit_log WHERE session_id = $1",
                    uuid.UUID(session_id),
                )
                await conn.execute(
                    """
                    DELETE FROM bu_round_states
                    WHERE global_state_id IN (
                        SELECT state_id FROM global_round_states WHERE session_id = $1
                    )
                    """,
                    uuid.UUID(session_id),
                )
                await conn.execute(
                    "DELETE FROM global_round_states WHERE session_id = $1",
                    uuid.UUID(session_id),
                )
                await conn.execute(
                    "DELETE FROM sessions WHERE session_id = $1",
                    uuid.UUID(session_id),
                )

            # Evict from in-memory cache
            from database_memory import _sessions
            _sessions.pop(session_id, None)
        else:
            # Soft delete: stamp deleted_at in metadata only
            now_str = datetime.now(timezone.utc).isoformat()
            await _update_session_metadata(session_id, {"deleted_at": now_str})
        return True


async def delete_all_sessions(hard: bool = False) -> int:
    """Delete all sessions. Soft-deletes unless hard=True."""
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch("SELECT session_id FROM sessions")
        count = len(rows)
        if hard:
            await conn.execute("DELETE FROM sessions")
            from database_memory import _sessions
            _sessions.clear()
        else:
            now_str = datetime.now(timezone.utc).isoformat()
            for row in rows:
                sid = str(row["session_id"])
                await _update_session_metadata(sid, {"deleted_at": now_str})
        return count


async def save_decade_plan(session_id: str, boardroom_choice: str, decade_plan: str) -> bool:
    """Save the boardroom choice and decade forward plan for a session."""
    return await _update_session_metadata(session_id, {
        "boardroom_choice": boardroom_choice,
        "decade_forward_plan": decade_plan
    })


async def get_decade_plan(session_id: str) -> Optional[dict]:
    """Retrieve the decade forward plan for a session."""
    info = await get_session_info(session_id)
    if not info:
        return None
    return {
        "boardroom_choice": info.get("boardroom_choice"),
        "decade_forward_plan": info.get("decade_forward_plan"),
    }


async def reset_session_to_round1(session_id: str) -> bool:
    """
    Reset a session (and all its child player sessions) back to Round 1 seed state.
    Preserves session metadata (cohort name, facilitator, players, etc.).
    """
    pool = await get_pool()
    info = await get_session_info(session_id)
    if not info:
        return False
    
    # Determine seed based on paradigm
    paradigm = info.get("decision_paradigm", "legacy_abc")
    industry = "healthcare" if paradigm == "healthcare" else "generic"
    seed = _load_seed(industry=industry)
    gs = seed["global_state"]
    bus = seed["business_units"]

    # Rebuild baseline metrics from seed
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

    loan_rate = 0.12
    # Get loan interest rate from latest state if available
    latest = await fetch_latest_state(session_id)
    if latest:
        from config import FINANCIAL_DEFAULT_LOAN_RATE as _dlr   # FIN-11
        loan_rate = latest.get("global_state", {}).get("active_event_flags", {}).get("loan_interest_rate", _dlr)

    global_state_id = str(uuid.uuid4())
    
    # SDG values dynamic injection for reset
    if paradigm == "un_sdg":
        for bu in bus:
            for cluster in ["basic_needs", "human_capital", "sustainable_growth", "planet", "governance", "partnerships"]:
                if cluster not in bu:
                    bu[cluster] = 50.0

    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        async with conn.transaction():
            # Delete old states for this session (cascades or explicit).
            # Transaction-local bypass of the append-only guard (see
            # _allow_immutable_purge) — replaces ALTER TABLE ... DISABLE TRIGGER.
            await _allow_immutable_purge(conn)

            try:
                # 1. Delete audit log entries
                await conn.execute("DELETE FROM decision_audit_log WHERE session_id = $1", uuid.UUID(session_id))
                # 2. Delete BU round states
                await conn.execute(
                    """
                    DELETE FROM bu_round_states 
                    WHERE global_state_id IN (SELECT state_id FROM global_round_states WHERE session_id = $1)
                    """,
                    uuid.UUID(session_id),
                )
                # 3. Delete global round states
                await conn.execute("DELETE FROM global_round_states WHERE session_id = $1", uuid.UUID(session_id))
                
                # 4. Insert Round 1 global state
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
                    _dumps({
                        **gs.get("active_event_flags", {}),
                        "loan_interest_rate": loan_rate,
                        "bonus_score": 0,
                        "historical_ebitda": baseline_ebitda,
                        "tco2e_emissions": baseline_tco2e,
                        "vrio_capabilities": baseline_vrio,
                        "green_transition_fund": 0.0,
                        "tipping_point_active": False,
                        "pending_capex_projects": [],
                        "inflation_index": 0.025,
                        "competitor_ebitda": baseline_ebitda,
                    }),
                )
                
                # 5. Insert BU states
                for bu in bus:
                    explicit_columns = {
                        "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
                        "social_license_score", "reputation_score", "governance_risk_score",
                        "water_dependency", "carbon_intensity"
                    }
                    rf = dict(bu.get("risk_factors", {}))
                    for k, v in bu.items():
                        if k not in explicit_columns and k != "risk_factors":
                            rf[k] = v
                            
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
                        _dumps(rf),
                    )
            finally:
                # Nothing to re-enable: SET LOCAL muressons.allow_purge is
                # scoped to this transaction and resets automatically on
                # COMMIT/ROLLBACK. (The old code re-enabled the triggers it had
                # disabled table-wide here.)
                pass

    # Also reset child player sessions
    child_sessions = await get_child_sessions(session_id)
    for child in child_sessions:
        await reset_session_to_round1(child["session_id"])
        
    return True


async def fetch_sessions_by_facilitator(facilitator_id: str) -> list[dict]:
    """Return all top-level sessions (no parent_cohort_id) owned by a facilitator.

    Used by the cascade-delete path when a facilitator account is removed so
    every cohort they own is cleaned up together with the account.  Both
    soft-deleted and active sessions are included so that a hard facilitator
    delete can permanently erase everything, and a soft delete can mark them.
    """
    pool = await get_pool()
    async with pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS) as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, cohort_name, facilitator_id, start_time, metadata
            FROM sessions
            WHERE facilitator_id = $1
            ORDER BY start_time DESC
            """,
            facilitator_id,
        )
        res = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            # Only return top-level cohorts — child player sessions are handled
            # inside _cascade_delete_session via get_child_sessions()
            if metadata.get("parent_cohort_id"):
                continue
            sess = {
                "session_id": str(row["session_id"]),
                "cohort_name": row["cohort_name"],
                "facilitator_id": row["facilitator_id"],
                "start_time": row["start_time"],
            }
            sess.update(metadata)
            res.append(sess)
        return res


def flush_snapshot() -> None:
    """Backend-parity no-op (F-29). The memory store debounces its JSON
    snapshot and flushes it at shutdown; Postgres commits every write as it
    happens, so there is nothing pending to flush. Present so `db.flush_snapshot()`
    is callable on either backend (test_backend_parity_surface)."""
    return None
