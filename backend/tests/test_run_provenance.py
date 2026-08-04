"""4.7 — a finished run records what produced it.

WHAT WAS MISSING
    Three things decide the numbers a cohort sees:

        the SEED    — which stochastic events were dealt (4.2)
        the CONFIG  — the tunable constants in force at the time
        the CODE    — the engine that combined them

    A completed session recorded none of them. Two cohorts run a month apart,
    with a config change in between, were indistinguishable in the database:
    same shape, same fields, silently different rules. Nobody could say which
    had been graded under which regime, and no later analysis could recover it,
    because the information was never written down.

    That is the difference between a result you can defend to a paying
    executive and one you can only assert.

THE TRAP THIS GUARDS
    Provenance that disagrees with reality is WORSE than no provenance — it is
    confidently wrong. The seed recorded in metadata and the seed the engine
    actually rolls with come from one resolver for exactly this reason, and
    test_recorded_seed_matches_the_seed_actually_used pins it.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from config_introspect import run_provenance  # noqa: E402
from rng_util import derive_cohort_seed  # noqa: E402


def _unique(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            import database as _db
            if getattr(_db, "_pool", None) is not None:
                loop.run_until_complete(_db.close_pool())
        except Exception:
            pass
        loop.close()


# ── 1. The stamp itself ────────────────────────────────────────────────────

def test_provenance_carries_seed_config_and_code():
    p = run_provenance("mur-abc123")
    assert p["stochastic_seed"] == "mur-abc123"
    assert p["config_fingerprint"].startswith("sha256:")
    assert p["code_version"]           # "unknown" is honest; "" is a bug
    assert p["stamped_at_utc"].endswith("+00:00"), "timestamps must be UTC-explicit"
    assert p["schema"] == 1, "bump deliberately — readers key off this"


def test_provenance_never_raises():
    """Evidence, not control flow. A run must not fail to START because a
    fingerprint could not be computed."""
    import config_introspect
    original = config_introspect._fingerprint
    config_introspect._fingerprint = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        p = run_provenance("mur-x")
        assert p["config_fingerprint"] == "unavailable"
        assert "boom" in p.get("config_fingerprint_error", "")
        assert p["stochastic_seed"] == "mur-x", "the rest of the stamp survives"
    finally:
        config_introspect._fingerprint = original


def test_the_fingerprint_moves_when_config_moves():
    """If it did not, stamping it would be theatre."""
    import config as config_mod
    from config_introspect import _fingerprint, _public_constants
    before = _fingerprint(_public_constants(config_mod))
    key = next(k for k, v in _public_constants(config_mod).items() if isinstance(v, (int, float)))
    original = getattr(config_mod, key)
    try:
        setattr(config_mod, key, original + 1)
        assert _fingerprint(_public_constants(config_mod)) != before
    finally:
        setattr(config_mod, key, original)


# ── 2. It is actually attached to a run ────────────────────────────────────

def test_a_new_session_carries_provenance():
    import database as db
    out = _run(db.create_session(cohort_name=_unique("PROV"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")
    info = _run(db.get_session_info(sid))
    prov = (info or {}).get("run_provenance") or {}
    assert prov, (
        "a new session records nothing about what produced it — the pre-4.7 state"
    )
    assert prov.get("config_fingerprint")
    assert prov.get("stochastic_seed")


def test_recorded_seed_matches_the_seed_actually_used():
    """THE assertion. Provenance that disagrees with the live state is worse
    than none: it would let someone 'reproduce' a run with the wrong seed and
    believe the mismatch was the engine's fault."""
    import database as db
    out = _run(db.create_session(cohort_name=_unique("PROV-match"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")

    info = _run(db.get_session_info(sid))
    recorded = ((info or {}).get("run_provenance") or {}).get("stochastic_seed")

    state = _run(db.fetch_latest_state(sid))
    live = (state["global_state"].get("active_event_flags") or {}).get("stochastic_seed")

    assert recorded and live, f"recorded={recorded!r} live={live!r}"
    assert recorded == live, (
        f"provenance claims seed {recorded!r} but the engine rolls with {live!r} — "
        "a reader replaying this run would reproduce the wrong simulation"
    )
    assert recorded == derive_cohort_seed(sid)


def test_every_team_in_a_cohort_records_the_same_seed():
    """The cohort-level property, at the provenance layer this time."""
    import database as db
    parent = _run(db.create_session(cohort_name=_unique("PROV-cohort"), facilitator_id="god_mode"))
    pid = parent.get("session_id") or parent.get("id")
    seeds = set()
    for n in (1, 2):
        child = _run(db.create_session(
            cohort_name=_unique(f"PROV-cohort-t{n}"), facilitator_id="god_mode",
            parent_cohort_id=pid, player_id=f"MUR-10{n}"))
        cid = child.get("session_id") or child.get("id")
        info = _run(db.get_session_info(cid))
        seeds.add(((info or {}).get("run_provenance") or {}).get("stochastic_seed"))
    assert seeds == {derive_cohort_seed(pid)}, seeds
