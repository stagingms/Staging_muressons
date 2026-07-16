"""
coordination_store.py — shared live-run coordination state (audit Fix #5).

WHY THIS EXISTS
---------------
The live-run coordination state that a facilitator manipulates during a session
— round pacing / unlock, the God-Mode "system frozen" flag, per-session commit
timestamps — used to live ONLY in per-process Python dicts in admin_shared /
router. That has two failure modes the audit flagged:

  1. Restart/redeploy loss: Railway deploys on push and restarts the container,
     dropping every dict → a live cohort's pacing/freeze state vanishes mid
     session (audit §1.1).
  2. Multi-worker split-brain: to serve ~500 concurrent users the app must run
     more than one uvicorn worker/replica (audit §1.2). Each worker holds its
     OWN copy of those dicts, so a facilitator's unlock/freeze lands on one
     worker and players pinned to other workers never see it.

This module externalizes that state to the durable store so it survives
restarts AND is shared across workers.

DESIGN
------
* Backend is chosen at import time to mirror main.py's DB selection:
    - PostgreSQL available  → a `coordination_state (key TEXT PK, value JSONB)`
      table is authoritative and shared across workers.
    - In-memory / offline   → this module is a thin no-op; durability is instead
      provided by database_memory's existing JSON snapshot (which now also
      snapshots pacing + god-mode settings). Single-process, so no sharing is
      needed and behaviour is byte-identical to before.
* The hot path (`is_round_unlocked`, freeze checks) is SYNCHRONOUS, so we never
  block it on a DB round-trip. Instead:
    - writes publish immediately to Postgres (async, best-effort), and
    - a background refresher (started from the FastAPI lifespan in PG mode)
      pulls the table into the in-process caches every REFRESH_SECONDS.
  Cross-worker propagation is therefore eventually-consistent with a bounded
  staleness window of REFRESH_SECONDS (default 3s). Facilitator actions on the
  SAME worker are always immediate.

VERIFICATION NOTE
-----------------
The in-memory path is exercised by the test suite. The PostgreSQL path requires
a live multi-worker + Postgres soak test before enabling >1 worker in
production — see audit item #8. Functions that only matter under Postgres are
marked accordingly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

# Bounded staleness window for cross-worker propagation (seconds).
REFRESH_SECONDS: float = float(os.getenv("COORDINATION_REFRESH_SECONDS", "3"))

_log = logging.getLogger("muressons.coordination")

# QA-2026-07-16 #14: publish/read failures were swallowed with a bare print, so a
# Postgres blip silently left pacing/freeze process-local with no operator signal.
# Count them and log at WARNING so a live incident is visible; expose the counter
# for a health probe.
_publish_failures: int = 0


def publish_failure_count() -> int:
    return _publish_failures

# Resolved lazily on first use to avoid import cycles with main.py / database.
_pg_pool_getter = None          # callable returning an asyncpg pool (PG mode)
_backend: Optional[str] = None  # "postgres" | "memory" | None(uninitialised)
_refresher_task: Optional[asyncio.Task] = None

_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS coordination_state (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


# ── Backend resolution ──────────────────────────────────────────────────────
def configure(backend: str, pg_pool_getter=None) -> None:
    """Called once from main.py after it has selected the DB module.

    backend: "postgres" enables the shared table; anything else → memory no-op.
    pg_pool_getter: zero-arg async callable returning the asyncpg pool.
    """
    global _backend, _pg_pool_getter
    _backend = "postgres" if backend == "postgres" else "memory"
    _pg_pool_getter = pg_pool_getter


def is_shared() -> bool:
    """True when a cross-worker shared backend (Postgres) is active."""
    return _backend == "postgres"


async def _pool():
    if _pg_pool_getter is None:
        return None
    try:
        return await _pg_pool_getter()
    except Exception:
        return None


# ── Schema ──────────────────────────────────────────────────────────────────
async def init_schema() -> None:
    """Create the coordination table (PG mode only). Idempotent, safe to call
    on every boot. No-op in memory mode."""
    if not is_shared():
        return
    pool = await _pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(_TABLE_DDL)
    except Exception as exc:  # pragma: no cover - requires live PG
        print(f"[coordination] init_schema failed (non-fatal): {exc}")


# ── Low-level KV ────────────────────────────────────────────────────────────
async def put(key: str, value: Any) -> None:
    """Upsert a JSON-serialisable value under key. No-op in memory mode
    (durability there rides the database_memory snapshot)."""
    if not is_shared():
        return
    pool = await _pool()
    if pool is None:
        return
    try:
        payload = json.dumps(value, default=str)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO coordination_state(key, value, updated_at)
                VALUES($1, $2::jsonb, now())
                ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value, updated_at = now()
                """,
                key, payload,
            )
    except Exception as exc:  # pragma: no cover - requires live PG
        global _publish_failures
        _publish_failures += 1
        _log.warning("put(%s) failed (non-fatal, total failures=%d): %s", key, _publish_failures, exc)


async def get(key: str) -> Optional[Any]:
    if not is_shared():
        return None
    pool = await _pool()
    if pool is None:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM coordination_state WHERE key = $1", key
            )
        if row is None:
            return None
        val = row["value"]
        return json.loads(val) if isinstance(val, (str, bytes)) else val
    except Exception as exc:  # pragma: no cover - requires live PG
        print(f"[coordination] get({key}) failed (non-fatal): {exc}")
        return None


async def get_prefix(prefix: str) -> dict[str, Any]:
    """Return {key: value} for every key starting with prefix (PG mode)."""
    if not is_shared():
        return {}
    pool = await _pool()
    if pool is None:
        return {}
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key, value FROM coordination_state WHERE key LIKE $1",
                prefix + "%",
            )
        out: dict[str, Any] = {}
        for r in rows:
            v = r["value"]
            out[r["key"]] = json.loads(v) if isinstance(v, (str, bytes)) else v
        return out
    except Exception as exc:  # pragma: no cover - requires live PG
        print(f"[coordination] get_prefix({prefix}) failed (non-fatal): {exc}")
        return {}


async def delete(key: str) -> None:
    """QA-2026-07-16 #14: remove a key so rows for dead sessions do not accumulate
    forever (rehydrate only ever merges, so a key removed centrally would
    otherwise linger in every worker's cache too). No-op in memory mode."""
    if not is_shared():
        return
    pool = await _pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM coordination_state WHERE key = $1", key)
    except Exception as exc:  # pragma: no cover - requires live PG
        global _publish_failures
        _publish_failures += 1
        _log.warning("delete(%s) failed (non-fatal): %s", key, exc)


# ── Typed helpers (keys namespaced) ─────────────────────────────────────────
_PACING_PREFIX = "pacing:"
_GODMODE_KEY = "godmode:settings"
_OVERRIDE_PREFIX = "session_override:"


async def publish_pacing(session_id: str, policy: dict) -> None:
    await put(_PACING_PREFIX + session_id, policy)


async def delete_pacing(session_id: str) -> None:
    """QA-2026-07-16 #14: drop a dead session's shared pacing row (reaper / hard-delete)."""
    await delete(_PACING_PREFIX + session_id)


async def delete_session_override(session_id: str) -> None:
    await delete(_OVERRIDE_PREFIX + session_id)


async def publish_godmode_settings(settings: dict) -> None:
    await put(_GODMODE_KEY, settings)


async def publish_session_override(session_id: str, fields: dict) -> None:
    """Non-column session fields (is_solo, pacing_mode, _solo_round_configs,
    annotation/pulse visibility, side-track config, …) that the Postgres session
    table has no dedicated column for. Merged back into the mirror cache on
    load so they survive restart under Postgres."""
    existing = (await get(_OVERRIDE_PREFIX + session_id)) or {}
    existing.update(fields)
    await put(_OVERRIDE_PREFIX + session_id, existing)


async def load_session_override(session_id: str) -> dict:
    return (await get(_OVERRIDE_PREFIX + session_id)) or {}


# ── Rehydrate + background refresh ──────────────────────────────────────────
async def rehydrate() -> None:
    """Pull shared coordination state into the in-process admin_shared caches.

    In PG mode this is called at startup (so a freshly (re)started worker sees
    the cohort's current pacing/freeze) and repeatedly by the background
    refresher (so workers converge). In memory mode it is a no-op — the
    database_memory snapshot restore already repopulates the dicts.
    """
    if not is_shared():
        return
    try:
        import admin_shared
    except Exception:
        return

    # God-mode settings (global, single row).
    gm = await get(_GODMODE_KEY)
    if isinstance(gm, dict):
        admin_shared.restore_godmode_settings(gm)

    # Per-session pacing policy.
    pacing_rows = await get_prefix(_PACING_PREFIX)
    for key, policy in pacing_rows.items():
        sid = key[len(_PACING_PREFIX):]
        if isinstance(policy, dict):
            admin_shared.restore_pacing_policy(sid, policy)


async def _refresher_loop() -> None:  # pragma: no cover - requires live PG
    while True:
        try:
            await asyncio.sleep(REFRESH_SECONDS)
            await rehydrate()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[coordination] refresher iteration failed: {exc}")


async def start_background_refresh() -> None:
    """Start the periodic cross-worker refresh (PG mode only)."""
    global _refresher_task
    if not is_shared():
        return
    if _refresher_task is None or _refresher_task.done():
        _refresher_task = asyncio.create_task(_refresher_loop())


async def stop_background_refresh() -> None:
    global _refresher_task
    if _refresher_task is not None:
        _refresher_task.cancel()
        try:
            await _refresher_task
        except Exception:
            pass
        _refresher_task = None
