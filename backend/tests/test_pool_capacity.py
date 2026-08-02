"""The connection pool must be able to seat a full cohort committing at once.

PERF-AUDIT-2026-07-29. The worst failure found in the whole audit, because it
fires at the exact moment a class is most exposed: everyone commits the round
together.

`acquire_advisory_lock` takes a pool connection and HOLDS it for the duration
of the commit, while the commit's own queries acquire further connections from
the same pool. Each in-flight commit therefore costs roughly two connections.
With the old default `DB_MAX_CONNECTIONS=10`, a cohort bigger than ~5 could
consume every connection holding locks, leaving nothing for the queries those
locks were taken for. Classic pool-exhaustion deadlock.

And because `pool.acquire()` was called with no timeout, it did not degrade —
it waited forever. Measured against real Postgres:

    12 simultaneous commits, pool = 10  ->  never returned
    12 simultaneous commits, pool = 40  ->  0.4s, all 201
    20 simultaneous commits, pool = 40  ->  0.5s, all 201

Two independent fixes, because either alone still fails:
  * pool sized above 2 x the roster ceiling (this file pins that arithmetic);
  * every acquire bounded by a timeout, so exhaustion becomes a visible 503
    instead of a class-wide hang (verified: pool=2 with 8 committers now
    errors in ~2s rather than hanging).

These are cheap arithmetic assertions on purpose. A real 20-player deadlock
test would take minutes and hang CI when it regressed — which is exactly the
symptom it is meant to report.
"""
import importlib
import os


def _reload_config(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import config
    return importlib.reload(config)


def test_default_pool_seats_a_full_cohort_committing_together():
    """The invariant: pool >= 2 x max roster, plus headroom."""
    import config
    from player_capacity import MAX_PLAYERS_CEILING

    needed = 2 * MAX_PLAYERS_CEILING
    assert config.DB_MAX_CONNECTIONS >= needed, (
        f"DB_MAX_CONNECTIONS={config.DB_MAX_CONNECTIONS} cannot seat "
        f"{MAX_PLAYERS_CEILING} students committing simultaneously: each "
        f"in-flight commit holds ~2 connections (advisory lock + queries), so "
        f"at least {needed} are required. Below this the pool deadlocks."
    )


def test_every_acquire_is_bounded_by_a_timeout():
    """An unbounded acquire turns a capacity problem into a hang. Pin that no
    call site drifts back to the bare form."""
    import pathlib
    import re
    src = (pathlib.Path(__file__).resolve().parents[1] / "database.py").read_text(encoding="utf-8")
    # Match the CALL SYNTAX, not the bare token. database.py's own docstrings
    # quote `pool.acquire()` while explaining this very bug, and a tripwire
    # that trips on its own prose is worse than no tripwire. Real call sites
    # are always `async with <x>pool.acquire() as ...` or `await <x>pool.acquire()`;
    # prose never is.
    CALL = re.compile(r"(async with|await)\s+_?pool\.acquire\(\s*\)")
    offenders = [
        (i + 1, ln.strip())
        for i, ln in enumerate(src.split("\n"))
        if CALL.search(ln)
    ]
    assert not offenders, (
        "bare pool.acquire() will wait forever when the pool is exhausted; use "
        "pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS). Offending lines: "
        + "; ".join(f"{n}: {t}" for n, t in offenders)
    )
    assert "DB_ACQUIRE_TIMEOUT_SECONDS" in src


def test_timeouts_are_configured_and_sane():
    import config
    assert 0 < config.DB_ACQUIRE_TIMEOUT_SECONDS <= 60, \
        "acquire timeout must be positive and short enough to surface during a class"
    assert 0 < config.DB_COMMAND_TIMEOUT_SECONDS <= 120, \
        "command timeout must bound a stuck query without killing a slow legitimate one"


def test_pool_size_is_still_env_overridable(monkeypatch):
    """Operators must be able to tune this per deployment — the pool is PER
    WORKER, so raising WEB_CONCURRENCY multiplies it against the server's
    max_connections."""
    cfg = _reload_config(monkeypatch, DB_MAX_CONNECTIONS="77")
    try:
        assert cfg.DB_MAX_CONNECTIONS == 77
    finally:
        monkeypatch.delenv("DB_MAX_CONNECTIONS", raising=False)
        importlib.reload(cfg)


def test_advisory_lock_holds_a_connection_for_the_whole_commit():
    """Documents WHY the 2x factor exists. If this ever stops being true the
    arithmetic above can relax — but it must be a deliberate change."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "database.py").read_text(encoding="utf-8")
    i = src.index("async def acquire_advisory_lock")
    body = src[i:i + 3000]
    assert "return conn" in body, (
        "acquire_advisory_lock no longer hands its connection to the caller — "
        "re-derive the pool sizing factor in this file"
    )
