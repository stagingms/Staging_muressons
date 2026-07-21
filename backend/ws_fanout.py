"""
ws_fanout.py — cross-worker WebSocket delivery (QA-2026-07-16 #10).

WHY
---
The ConnectionManager in admin_ws holds player/admin sockets in PROCESS memory.
With more than one uvicorn worker (the ~500-user target), a broadcast/freeze push
sent from the worker that handled the facilitator's request reaches only the
sockets that happen to live on THAT worker; players pinned to other workers catch
up only via the 5-15s REST polling fallback (audit §1.4).

This module fans a push out to the OTHER workers using Postgres LISTEN/NOTIFY, so
every worker delivers the message to its own local sockets in near real time.

SAFETY / SCOPE
--------------
* No-op unless Postgres is the active backend AND a listener is running — so in
  single-worker / in-memory mode (today's default) ConnectionManager behaves
  EXACTLY as before: local delivery only, byte-identical. The new path activates
  only under the multi-worker Postgres deployment, which is gated behind the
  staging soak test (audit #10 / DEPLOYMENT_CHECKLIST §"#10").
* Every message is tagged with this process's worker id; a worker ignores its own
  NOTIFYs (it already delivered locally) so there is no double-send or loop.
* Postgres NOTIFY payloads are capped (~8000 bytes). Oversized messages skip the
  fan-out and rely on the polling fallback, rather than erroring.
* Any failure degrades to local-only delivery; the real-time path never raises.

VERIFICATION NOTE
-----------------
The memory-mode no-op path is unit-tested. The live LISTEN/NOTIFY path needs a
multi-worker Postgres soak (audit #10) before enabling WEB_CONCURRENCY>1.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Awaitable, Callable, Optional

_log = logging.getLogger("muressons.ws_fanout")

_CHANNEL = "muressons_ws"
_MAX_PAYLOAD = 7500  # Postgres NOTIFY hard limit is 8000 bytes; stay under it.
_WORKER_ID = uuid.uuid4().hex  # unique per process/worker

_backend: Optional[str] = None
_pg_pool_getter = None
_listen_conn = None
_listen_task = None
# Called on receipt of a REMOTE message: (kind, session_id, message) -> awaitable.
_local_deliver: Optional[Callable[[str, Optional[str], dict], Awaitable[None]]] = None


def configure(backend: str, pg_pool_getter=None, local_deliver=None) -> None:
    """Wire the fan-out to the selected DB backend and the manager's local-only
    delivery callback. Mirrors coordination_store.configure()."""
    global _backend, _pg_pool_getter, _local_deliver
    _backend = "postgres" if backend == "postgres" else "memory"
    _pg_pool_getter = pg_pool_getter
    if local_deliver is not None:
        _local_deliver = local_deliver


def is_shared() -> bool:
    return _backend == "postgres"


async def _pool():
    if _pg_pool_getter is None:
        return None
    try:
        return await _pg_pool_getter()
    except Exception:
        return None


async def publish(kind: str, session_id: Optional[str], message: dict) -> None:
    """Fan a locally-delivered push out to other workers. No-op unless a shared
    Postgres backend is active. Never raises into the real-time path."""
    if not is_shared():
        return
    pool = await _pool()
    if pool is None:
        return
    try:
        envelope = json.dumps({
            "w": _WORKER_ID,
            "kind": kind,
            "sid": session_id,
            "msg": message,
        }, default=str)
        if len(envelope.encode("utf-8")) > _MAX_PAYLOAD:
            # Too big for NOTIFY — local delivery already happened; other workers
            # pick it up via the polling fallback.
            return
        async with pool.acquire() as conn:
            await conn.execute("SELECT pg_notify($1, $2)", _CHANNEL, envelope)
    except Exception as exc:  # pragma: no cover - requires live PG
        _log.warning("publish(%s) failed (non-fatal): %s", kind, exc)


async def _on_notify(_conn, _pid, _channel, payload) -> None:  # pragma: no cover - live PG
    try:
        data = json.loads(payload)
    except Exception:
        return
    if data.get("w") == _WORKER_ID:
        return  # our own message — already delivered locally
    if _local_deliver is None:
        return
    try:
        await _local_deliver(data.get("kind", ""), data.get("sid"), data.get("msg") or {})
    except Exception as exc:
        _log.warning("local delivery of remote push failed: %s", exc)


async def start_listener() -> None:
    """Start LISTENing for cross-worker pushes (Postgres only)."""
    global _listen_conn, _listen_task
    if not is_shared():
        return
    pool = await _pool()
    if pool is None:
        return
    try:
        _listen_conn = await pool.acquire()
        await _listen_conn.add_listener(_CHANNEL, _on_notify)
        _log.info("ws_fanout listening on channel %s (worker %s)", _CHANNEL, _WORKER_ID[:8])
    except Exception as exc:  # pragma: no cover - requires live PG
        _log.warning("ws_fanout listener start failed (degrading to local-only): %s", exc)
        _listen_conn = None


async def stop_listener() -> None:
    global _listen_conn
    if _listen_conn is not None:
        try:
            await _listen_conn.remove_listener(_CHANNEL, _on_notify)
        except Exception:
            pass
        try:
            pool = await _pool()
            if pool is not None:
                await pool.release(_listen_conn)
        except Exception:
            pass
        _listen_conn = None
