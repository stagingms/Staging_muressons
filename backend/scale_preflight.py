"""
scale_preflight.py — decide how many web workers are SAFE to run (audit #7).

Multi-worker only became safe once live-run coordination state was externalized
to a shared store (audit #5: coordination_store on Postgres). On the in-memory
store, EVERYTHING — sessions, scores, pacing, freeze, rate-limit buckets — lives
in per-process dicts, so a second worker would split-brain the classroom. This
module is the single gate that refuses to fan out unless the durable, shared
Postgres backend is in use.

Used by docker-start.sh:  python -m scale_preflight  → prints the safe worker
count on stdout (and any warnings on stderr), which the entrypoint feeds to
gunicorn's -w.

Precedence for "are we on the shared Postgres backend?":
  • USE_MEMORY_DB=true            → in-memory  → force 1 worker.
  • ALLOW_MEMORY_DB_IN_PROD=true  → intentional non-durable prod → force 1.
  • DEBUG=true                    → local dev (memory allowed) → force 1.
  • otherwise                     → Postgres   → honour WEB_CONCURRENCY.

main.py still enforces the durability guard at import time (SEC-2), so a worker
that somehow boots on memory in prod hard-fails anyway; this module makes the
failure mode a clear "clamped to 1 worker" instead of silent split-brain.
"""

from __future__ import annotations

import os
from typing import Mapping


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in ("true", "1", "yes")


def is_shared_backend(env: Mapping[str, str]) -> bool:
    """True only when the durable, cross-worker Postgres backend is in use."""
    if _truthy(env.get("USE_MEMORY_DB")):
        return False
    if _truthy(env.get("ALLOW_MEMORY_DB_IN_PROD")):
        return False
    if _truthy(env.get("DEBUG")):
        return False
    return True


def safe_worker_count(env: Mapping[str, str]) -> tuple[int, list[str]]:
    """Return (workers, warnings).

    Honours WEB_CONCURRENCY (default 1) but clamps to 1 whenever the backend is
    not the shared Postgres store, because per-process state cannot be split
    across workers safely.
    """
    warnings: list[str] = []
    try:
        requested = int(env.get("WEB_CONCURRENCY", "1") or "1")
    except ValueError:
        requested = 1
        warnings.append("WEB_CONCURRENCY was not an integer; defaulting to 1.")
    if requested < 1:
        requested = 1

    if requested > 1 and not is_shared_backend(env):
        warnings.append(
            f"WEB_CONCURRENCY={requested} but the shared Postgres backend is NOT "
            "active (memory/offline/DEBUG mode). Per-process state (sessions, "
            "pacing, freeze, rate limits) cannot be split across workers — "
            "forcing 1 worker. Set USE_MEMORY_DB=false + a reachable DATABASE_URL "
            "(and DEBUG=false) to scale out."
        )
        return 1, warnings

    return requested, warnings


def main() -> None:
    workers, warnings = safe_worker_count(os.environ)
    import sys
    for w in warnings:
        print(f"[scale] WARNING: {w}", file=sys.stderr)
    # stdout carries ONLY the number so the shell can capture it cleanly.
    print(workers)


if __name__ == "__main__":
    main()
