"""Audit F-04 (RNG-1): the cohort seed must reach the post-tick engines.

engine._assemble_global_state sets new_global["active_event_flags"] to the
round's EVENTS dict; the stored flags — where rng_util.ensure_cohort_seed put
``stochastic_seed`` at creation — were merged in only after run_new_engines.
So npc_stakeholders.process_npc_tick read ``stochastic_seed`` as None and the
regulator's $5-25M enforcement fine fell through to ``random.uniform``: three
teams with byte-identical decisions were fined $24.4M / $7.4M / $15.4M in the
same round (audit probe rng/probe_diverge.py). The same gap starved
balance_sheet.py of ``loan_interest_rate`` / ``ending_pathway`` and
round_logic of ``difficulty_tier``.

router._forward_persistent_flags now carries those keys into the post-tick
state. These tests pin (1) the keys are present when post_tick runs, (2) the
unseeded RNG path in npc_stakeholders is never taken during a commit, and
(3) two identical teams in one cohort produce identical state.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

import router as _router  # noqa: E402
import npc_stakeholders  # noqa: E402
from main import app  # noqa: E402

# Per-team bookkeeping that legitimately differs between two identical teams:
# cohort counters, and the raw decisions as SENT (option keys are in each
# session's own shuffled display space; commit_turn deshuffles them).
_VOLATILE = {"cohort_team_count", "team_commits_this_round", "decisions_raw"}


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _client():
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(ac):
    r = await ac.post("/api/admin/facilitators/login",
                      json={"facilitator_id": "god_mode",
                            "password": os.environ["MASTER_PASSWORD"]})
    assert r.status_code == 200, r.text[:200]


async def _cohort(ac, name, **extra):
    body = {"cohort_name": name, "decision_paradigm": "legacy_abc"}
    body.update(extra)
    r = await ac.post("/api/simulations/start", json=body)
    assert r.status_code == 201, r.text[:300]
    return r.json()["session_id"]


async def _player(ac, cohort_sid, name):
    r = await ac.post(f"/api/admin/{cohort_sid}/generate-player")
    assert r.status_code == 200, r.text[:300]
    pid, pw = r.json()["player_id"], r.json()["password"]
    r = await ac.post(f"/api/simulations/public/sessions/{cohort_sid}/join",
                      json={"player_id": pid, "password": pw, "player_name": name})
    assert r.status_code == 200, r.text[:300]
    return r.json()["session_id"]


def _display_key(sid: str, canonical: str, rnd: int) -> str:
    """The option letter this session DISPLAYS for a canonical option this round.
    Options are shuffled per session (option_shuffle); commit_turn deshuffles
    the displayed key back to canonical. Two teams sending the literal
    "option_b" would therefore be choosing DIFFERENT options."""
    import database_memory as dm
    from option_shuffle import get_shuffle_mapping
    seed = (dm._sessions.get(sid) or {}).get("shuffle_seed")
    if not seed:
        return canonical
    return get_shuffle_mapping(seed, rnd)["canonical_to_display"].get(canonical, canonical)


async def _commit(ac, sid, rnd, choice="option_b", capex=2_000_000):
    dash = await ac.get(f"/api/simulations/{sid}/dashboard")
    bus = dash.json()["business_units"]
    sent = _display_key(sid, choice, rnd)
    _router._commit_timestamps.pop(sid, None)
    r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3,
                       "capex_allocated": capex, "choice_selected": sent} for b in bus],
        "force_override_cfo": True,
        "expected_round": rnd,
    })
    assert r.status_code == 201, f"R{rnd} {sid}: {r.status_code} {r.text[:300]}"
    return r.json()


def _strip(d):
    """Diff-able view of a global_state: drop the per-cohort counters."""
    out = dict(d)
    flags = dict(out.get("active_event_flags") or {})
    for k in _VOLATILE:
        out.pop(k, None)
        flags.pop(k, None)
    out["active_event_flags"] = flags
    return out


# ── 1. Unit: the forwarder fills only what is missing ─────────────────────

def test_forwarder_fills_missing_keys_and_never_overrides_the_tick():
    stored = {"stochastic_seed": "mur-abc", "loan_interest_rate": 0.09,
              "ending_pathway": "hostile_takeover", "difficulty_tier": "expert",
              "industry_vertical": "", "region_id": None, "r1_flags": ["x"]}
    new_global = {"active_event_flags": {"difficulty_tier": "advanced", "cbam_surcharge_applied": 1.0}}
    _router._forward_persistent_flags({"active_event_flags": stored}, new_global)
    flags = new_global["active_event_flags"]
    assert flags["stochastic_seed"] == "mur-abc"
    assert flags["loan_interest_rate"] == 0.09
    assert flags["ending_pathway"] == "hostile_takeover"
    assert flags["difficulty_tier"] == "advanced"          # the tick's value wins
    assert "industry_vertical" not in flags                 # empty string not forwarded
    assert "region_id" not in flags                         # None not forwarded
    assert "r1_flags" not in flags                          # history is NOT forwarded here
    assert flags["cbam_surcharge_applied"] == 1.0


# ── 2. Integration: the keys are present when post_tick runs ──────────────

def test_post_tick_sees_the_seed_the_loan_rate_and_the_pathway(monkeypatch):
    seen = []
    real_post_tick = _router.post_tick

    def spy(**kw):
        seen.append(dict(kw["global_state"].get("active_event_flags") or {}))
        return real_post_tick(**kw)

    monkeypatch.setattr(_router, "post_tick", spy)

    async def go():
        async with _client() as ac:
            await _login(ac)
            cohort = await _cohort(ac, "seed-fwd", ending_pathway="hostile_takeover")
            sid = await _player(ac, cohort, "A")
            before = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
            before_flags = before["global_state"]["active_event_flags"]
            await _commit(ac, sid, 1)
            return before_flags

    stored = _run(go())
    assert seen, "post_tick was not called"
    at_post_tick = seen[0]
    assert stored.get("stochastic_seed"), "the child session carries no cohort seed"
    assert at_post_tick.get("stochastic_seed") == stored["stochastic_seed"]
    # Inherited from the cohort at join (router.join_session) — must survive into post_tick,
    # where balance_sheet.py reads it for stranded-asset exposure.
    assert stored.get("ending_pathway") == "hostile_takeover"
    assert at_post_tick.get("ending_pathway") == "hostile_takeover"
    assert at_post_tick.get("loan_interest_rate") == stored.get("loan_interest_rate")


# ── 3. The unseeded RNG path in npc_stakeholders is never taken ───────────

def test_no_commit_ever_reaches_the_unseeded_fine_draw(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("npc_stakeholders fell through to random.uniform — seed missing")
    monkeypatch.setattr(npc_stakeholders.random, "uniform", forbidden)

    async def go():
        async with _client() as ac:
            await _login(ac)
            cohort = await _cohort(ac, "no-unseeded")
            sid = await _player(ac, cohort, "A")
            for rnd in range(1, 6):
                await _commit(ac, sid, rnd)
    _run(go())


# ── 4. Identical decisions → identical state for two teams in one cohort ─

def test_two_identical_teams_in_one_cohort_get_identical_state():
    async def go():
        async with _client() as ac:
            await _login(ac)
            cohort = await _cohort(ac, "twins")
            a = await _player(ac, cohort, "A")
            b = await _player(ac, cohort, "B")
            states = []
            for rnd in range(1, 6):
                ra = await _commit(ac, a, rnd)
                rb = await _commit(ac, b, rnd)
                states.append((_strip(ra["global_state"]), _strip(rb["global_state"])))
            return states
    for rnd, (ga, gb) in enumerate(_run(go()), start=1):
        assert ga == gb, f"round {rnd}: identical teams diverged"
        assert ga["corporate_treasury"] == gb["corporate_treasury"]
