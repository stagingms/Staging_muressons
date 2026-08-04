"""4.2 — every cohort is seeded, and the same seed replays the same simulation.

WHAT WAS WRONG
    `rng_seed` has been a cohort setting since GAME-4, defaulting to "". Empty
    means unseeded, and rng_util.event_rng() answers an unseeded flags dict with
    a SYSTEM-seeded Random. So unless a facilitator opened the advanced settings
    and typed something, every black swan, micro-strike and NPC reaction a team
    met was unrepeatable and unrecorded — and nothing said so. The feature was
    built, correct, documented, and off.

    That is not a missing feature; it is a grading exposure. If a team disputes
    a result, "we cannot reconstruct which events you were dealt" is not an
    answer you want to give a paying executive.

WHAT THIS PINS
    1. A session created today HAS a seed. No setting, no ceremony.
    2. Every team in a cohort has the SAME seed — the property the whole
       mechanism exists for. Ranking must reflect strategy, not who got the
       kinder dice.
    3. An explicit seed always wins, so the override still works.
    4. Identical seeds produce identical rolls, and different seeds do not.
       Asserted on the real rng_util streams rather than assumed.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import rng_util  # noqa: E402
from rng_util import derive_cohort_seed, ensure_cohort_seed, event_rng  # noqa: E402


def _unique(name: str) -> str:
    """Cohort names are UNIQUE for top-level sessions, and Postgres keeps rows
    between runs. A fixed name passes once and then fails forever on a real
    database — which is precisely the kind of memory-mode-only assumption this
    whole Postgres job exists to catch.
    """
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


# ── 1. Derivation ──────────────────────────────────────────────────────────

def test_the_seed_is_stable_for_a_given_cohort():
    """A pure function of the cohort id, so it can be recomputed if the flag is
    ever lost — and so reading it tells you which run it belongs to."""
    assert derive_cohort_seed("abc-123") == derive_cohort_seed("abc-123")


def test_different_cohorts_get_different_seeds():
    assert derive_cohort_seed("abc-123") != derive_cohort_seed("abc-124")


def test_an_explicit_seed_is_never_overwritten():
    """The override path. A facilitator replaying last month's run types that
    run's seed; auto-generation must not stamp over it."""
    flags = {"stochastic_seed": "facilitator-chose-this"}
    assert ensure_cohort_seed(flags, "any-cohort") == "facilitator-chose-this"
    assert flags["stochastic_seed"] == "facilitator-chose-this"


def test_an_empty_seed_counts_as_absent():
    """"" is what the cohort setting defaults to. It must be treated as unset,
    not as a seed whose text happens to be empty."""
    flags = {"stochastic_seed": ""}
    seed = ensure_cohort_seed(flags, "cohort-x")
    assert seed and seed == derive_cohort_seed("cohort-x")


# ── 2. The property the seed exists for ────────────────────────────────────

def test_the_same_seed_deals_the_same_events():
    """If this fails the seed is decorative."""
    a = {"stochastic_seed": "mur-fixed"}
    b = {"stochastic_seed": "mur-fixed"}
    for event in ("blackswan:ransomware", "micro_strike", "npc:regulator"):
        for rnd in (1, 5, 10):
            assert [event_rng(a, rnd, event).random() for _ in range(5)] == \
                   [event_rng(b, rnd, event).random() for _ in range(5)]


def test_different_seeds_deal_different_events():
    a, b = {"stochastic_seed": "mur-aaa"}, {"stochastic_seed": "mur-bbb"}
    assert [event_rng(a, 1, "blackswan:ransomware").random() for _ in range(5)] != \
           [event_rng(b, 1, "blackswan:ransomware").random() for _ in range(5)]


def test_an_unseeded_dict_is_still_non_deterministic():
    """Pins the fallback rather than assuming it. This is what EVERY cohort got
    before 4.2 — kept working, so a legacy session still runs."""
    draws = [event_rng({}, 1, "blackswan:ransomware").random() for _ in range(6)]
    assert len(set(draws)) > 1


# ── 3. End to end: a real session carries a seed ───────────────────────────

def test_a_newly_created_session_has_a_seed():
    """The whole point: no setting, no ceremony, no unticked checkbox."""
    import database as db
    out = _run(db.create_session(cohort_name=_unique("SEEDTEST-solo"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")
    state = _run(db.fetch_latest_state(sid))
    flags = state["global_state"].get("active_event_flags") or {}
    assert flags.get("stochastic_seed"), (
        "a new session has no stochastic_seed — its events are unrepeatable "
        "and unrecorded, which is exactly the pre-4.2 behaviour"
    )


def test_every_team_in_a_cohort_shares_one_seed():
    """GAME-4's actual requirement. Twenty teams meeting different black swans
    means the leaderboard ranks luck; this is the assertion that forbids it."""
    import database as db
    parent = _run(db.create_session(cohort_name=_unique("SEEDTEST-cohort"), facilitator_id="god_mode"))
    pid = parent.get("session_id") or parent.get("id")
    kids = []
    for n in (1, 2, 3):
        child = _run(db.create_session(
            cohort_name=_unique(f"SEEDTEST-cohort-team{n}"), facilitator_id="god_mode",
            parent_cohort_id=pid, player_id=f"MUR-00{n}"))
        kids.append(child.get("session_id") or child.get("id"))

    def _seed_of(sid):
        st = _run(db.fetch_latest_state(sid))
        return (st["global_state"].get("active_event_flags") or {}).get("stochastic_seed")

    seeds = {sid: _seed_of(sid) for sid in kids}
    assert all(seeds.values()), f"a team session has no seed: {seeds}"
    assert len(set(seeds.values())) == 1, (
        f"teams in one cohort got different seeds: {seeds}. Their black swans, "
        "micro-strikes and NPC reactions differ, so the leaderboard is ranking "
        "luck rather than strategy."
    )
    assert set(seeds.values()) == {derive_cohort_seed(pid)}, (
        "team seeds are not derived from the parent cohort id"
    )


# ── 4. Display: the facilitator can see the seed they are running ──────────

def test_the_settings_endpoint_reports_the_live_seed():
    """The 'display it' half of 4.2.

    rng_seed lives in the SETTINGS override layer; the seed a run actually uses
    lives in the game state's active_event_flags. Auto-seeding writes the
    second, so an endpoint that reads only the first shows an empty box for a
    run that IS reproducible — telling the facilitator the opposite of the
    truth at the moment it matters most.
    """
    import httpx
    from httpx import ASGITransport
    from main import app
    import database as db

    out = _run(db.create_session(cohort_name=_unique("SEEDTEST-display"),
                                 facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")

    async def go():
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            login = await ac.post("/api/admin/facilitators/login",
                                  json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
            assert login.status_code == 200, login.text[:200]
            return await ac.get(f"/api/admin/sessions/{sid}/cohort-settings",
                                cookies=login.cookies)

    r = _run(go())
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("rng_seed"), (
        "the settings endpoint reports no seed for a seeded run — a facilitator "
        "reading this would believe the run is not reproducible"
    )
    assert body["rng_seed"] == derive_cohort_seed(sid)
    assert body.get("rng_seed_source") == "auto", body.get("rng_seed_source")
    assert body.get("reproducible") is True
    assert body["effective"]["rng_seed"] == body["rng_seed"], (
        "the merged 'effective' view still shows the empty override"
    )
