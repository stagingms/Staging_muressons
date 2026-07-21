"""
session_reaper.py — idle-session + in-process lock GC (audit #10).

Two unbounded-growth problems the audit flagged:
  • the per-session coordination dicts in router (_commit_locks,
    _commit_timestamps, _session_players) are never cleaned, so they grow for the
    whole process lifetime — a slow leak under a long-running server that creates
    many (especially solo) sessions, and
  • expired solo/self-paced sessions linger in the in-memory store forever.

This reaper runs periodically from the FastAPI lifespan and:
  • reaps SOLO sessions whose end_date has passed (memory backend only — cohort
    sessions are preserved for debrief and, under Postgres, are the DB's to
    manage), and
  • GCs the ancillary in-process dicts for any session no longer live — in BOTH
    backends, since those dicts are per-process regardless of store. A lock that
    is currently held is skipped so an in-flight commit is never disturbed.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date
from typing import Optional

REAP_INTERVAL_SECONDS: float = float(os.getenv("SESSION_REAP_INTERVAL_SECONDS", "1800"))  # 30 min

_reaper_task: Optional[asyncio.Task] = None


def _memory_backend_active() -> bool:
    try:
        import coordination_store as cs
        return not cs.is_shared()
    except Exception:
        return True


def _expired_solo_ids(sessions: dict, today: date) -> list[str]:
    out = []
    for sid, s in list(sessions.items()):
        if not s.get("is_solo"):
            continue
        end = s.get("end_date")
        if not end:
            continue
        try:
            if date.fromisoformat(str(end)) < today:
                out.append(sid)
        except (ValueError, TypeError):
            continue
    return out


def _retention_expired_cohort_ids(sessions: dict, today: date) -> list[str]:
    """LOW-tier data retention: cohorts whose configured retention window has
    elapsed — end_date + data_retention_days < today.

    Deliberately opt-in per cohort (data_retention_days > 0 must be SET; the
    global default of 0 keeps the legacy keep-forever behaviour) and requires an
    end_date, so an open-ended cohort is never reaped. Returns the cohort ids;
    the caller also removes their player sub-sessions."""
    from datetime import timedelta
    out = []
    for sid, s in list(sessions.items()):
        if s.get("parent_cohort_id") or s.get("is_solo"):
            continue  # cohort roots only (children reaped with their parent)
        end = s.get("end_date")
        if not end:
            continue
        try:
            from admin_shared import get_effective_settings
            days = int(get_effective_settings(sid).get("data_retention_days", 0) or 0)
        except Exception:
            days = 0
        if days <= 0:
            continue
        try:
            if date.fromisoformat(str(end)) + timedelta(days=days) < today:
                out.append(sid)
        except (ValueError, TypeError):
            continue
    return out


def reap_once(today: Optional[date] = None) -> dict:
    """Run one reap pass. Returns a summary dict (also handy for tests)."""
    today = today or date.today()
    summary = {"sessions_reaped": 0, "locks_gc": 0, "timestamps_gc": 0, "players_gc": 0, "pacing_gc": 0}
    # QA-2026-07-16 #14: session_ids whose pacing was GC'd, so the async loop can
    # also drop their SHARED coordination rows (Postgres). reap_once itself stays
    # synchronous (used directly in tests); the shared delete is best-effort.
    summary["_pacing_deleted_ids"] = []

    import database_memory as dm

    # 1) Reap expired solo sessions (memory backend only).
    if _memory_backend_active():
        for sid in _expired_solo_ids(dm._sessions, today):
            dm._sessions.pop(sid, None)
            getattr(dm, "_global_states", {}).pop(sid, None)
            getattr(dm, "_bu_states", {}).pop(sid, None)
            summary["sessions_reaped"] += 1

        # 1b) LOW-tier data retention: reap cohorts whose configured retention
        # window (end_date + data_retention_days) has elapsed — including their
        # player sub-sessions and cohort-settings overlay. Opt-in per cohort;
        # the default (0) keeps cohorts forever exactly as before.
        summary["retention_cohorts_reaped"] = 0
        for cid in _retention_expired_cohort_ids(dm._sessions, today):
            child_ids = [sid for sid, s in list(dm._sessions.items())
                         if s.get("parent_cohort_id") == cid]
            for sid in [cid] + child_ids:
                dm._sessions.pop(sid, None)
                getattr(dm, "_global_states", {}).pop(sid, None)
                getattr(dm, "_bu_states", {}).pop(sid, None)
                summary["sessions_reaped"] += 1
            summary["retention_cohorts_reaped"] += 1
            try:
                import admin_shared
                admin_shared.cohort_settings.pop(cid, None)
                admin_shared.persist_cohort_state()  # durable removal on the volume
            except Exception:
                pass

    live = set(dm._sessions.keys())

    # 2) GC ancillary in-process dicts for any non-live session (both backends).
    try:
        import router
        # Commit locks — never GC a lock that is currently held.
        for k in list(router._commit_locks.keys()):
            if k in live:
                continue
            lock = router._commit_locks.get(k)
            if lock is not None and lock.locked():
                continue
            router._commit_locks.pop(k, None)
            summary["locks_gc"] += 1
        for k in list(router._commit_timestamps.keys()):
            if k not in live:
                router._commit_timestamps.pop(k, None)
                summary["timestamps_gc"] += 1
        for k in list(router._session_players.keys()):
            if k not in live:
                router._session_players.pop(k, None)
                summary["players_gc"] += 1
    except Exception:
        pass

    # 3) GC pacing entries for non-live sessions (per-process; the durable copy,
    #    if any, lives in the coordination store).
    try:
        import admin_shared
        for k in list(admin_shared._round_pacing.keys()):
            if k not in live:
                admin_shared._round_pacing.pop(k, None)
                summary["pacing_gc"] += 1
                summary["_pacing_deleted_ids"].append(k)
    except Exception:
        pass

    if summary["sessions_reaped"]:
        try:
            dm._persist()
        except Exception:
            pass
    return summary


async def _reaper_loop() -> None:  # pragma: no cover - timing loop
    while True:
        try:
            await asyncio.sleep(REAP_INTERVAL_SECONDS)
            summary = reap_once()
            # QA-2026-07-16 #14: drop the shared coordination rows for reaped
            # sessions (no-op in memory mode).
            try:
                import coordination_store as _cs
                for _sid in summary.get("_pacing_deleted_ids", []):
                    await _cs.delete_pacing(_sid)
            except Exception:
                pass
            if any(v for k, v in summary.items() if k != "_pacing_deleted_ids"):
                import logging
                logging.getLogger("muressons.reaper").info(
                    "reap: %s", ", ".join(f"{k}={v}" for k, v in summary.items() if v)
                )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            import logging
            logging.getLogger("muressons.reaper").warning("reap pass failed: %s", exc)


async def start_reaper() -> None:
    global _reaper_task
    if _reaper_task is None or _reaper_task.done():
        _reaper_task = asyncio.create_task(_reaper_loop())


async def stop_reaper() -> None:
    global _reaper_task
    if _reaper_task is not None:
        _reaper_task.cancel()
        try:
            await _reaper_task
        except Exception:
            pass
        _reaper_task = None
