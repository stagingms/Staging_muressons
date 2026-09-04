"""Audit F-02: every debrief card and every dashboard history item must carry
the decision that was MADE in the round it is labelled with.

The decision log files a commit under the round it was made in (AUDIT-1,
2026-08-02). Two readers still used the pre-AUDIT-1 offset: the facilitator's
Round Debrief (admin_router.get_debrief read decisions_by_round[rn] for a card
labelled rn-1) and router._choices_by_game_round (out[tag-1]). Both put the
NEXT round's decision under each round's heading — with the right deltas
beside it, so the wrong decision looked explained. This test plays three
rounds with three different options and checks both readers.
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
from main import app  # noqa: E402

_PATH = ["option_a", "option_c", "option_b"]   # canonical choices for R1, R2, R3


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _display_key(sid, canonical, rnd):
    import database_memory as dm
    from option_shuffle import get_shuffle_mapping
    seed = (dm._sessions.get(sid) or {}).get("shuffle_seed")
    if not seed:
        return canonical
    return get_shuffle_mapping(seed, rnd)["canonical_to_display"].get(canonical, canonical)


async def _setup_and_play(ac):
    r = await ac.post("/api/admin/facilitators/login",
                      json={"facilitator_id": "god_mode", "password": os.environ["MASTER_PASSWORD"]})
    assert r.status_code == 200, r.text[:200]
    r = await ac.post("/api/simulations/start",
                      json={"cohort_name": "attribution", "decision_paradigm": "legacy_abc"})
    assert r.status_code == 201, r.text[:300]
    cohort = r.json()["session_id"]
    r = await ac.post(f"/api/admin/{cohort}/generate-player")
    assert r.status_code == 200, r.text[:300]
    pid, pw = r.json()["player_id"], r.json()["password"]
    r = await ac.post(f"/api/simulations/public/sessions/{cohort}/join",
                      json={"player_id": pid, "password": pw, "player_name": "A"})
    assert r.status_code == 200, r.text[:300]
    sid = r.json()["session_id"]
    for rnd, canonical in enumerate(_PATH, start=1):
        dash = await ac.get(f"/api/simulations/{sid}/dashboard")
        bus = dash.json()["business_units"]
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_000_000,
                           "choice_selected": _display_key(sid, canonical, rnd)} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
    return cohort, sid


def _client():
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_debrief_cards_carry_the_decision_made_in_that_round():
    async def go():
        async with _client() as ac:
            cohort, sid = await _setup_and_play(ac)
            r = await ac.get(f"/api/admin/{sid}/debrief")
            assert r.status_code == 200, r.text[:300]
            return r.json()
    body = _run(go())
    cards = {c["round_number"]: c for c in body["rounds"]}
    # Three commits produce history rows 2..4 -> cards for decision rounds 1..3.
    assert sorted(cards) == [1, 2, 3], sorted(cards)
    for rnd, canonical in enumerate(_PATH, start=1):
        assert cards[rnd]["choice_selected"] == canonical, (
            f"card R{rnd} says {cards[rnd]['choice_selected']!r}, the team chose {canonical!r}")


def test_dashboard_history_items_carry_the_decision_made_in_that_round():
    async def go():
        async with _client() as ac:
            cohort, sid = await _setup_and_play(ac)
            r = await ac.get(f"/api/simulations/{sid}/dashboard")
            assert r.status_code == 200, r.text[:300]
            return r.json()
    body = _run(go())
    by_round = {h["round_number"]: h.get("choice_selected") for h in body["history"]}
    for rnd, canonical in enumerate(_PATH, start=1):
        assert by_round.get(rnd) == canonical, (
            f"history[{rnd}].choice_selected is {by_round.get(rnd)!r}, expected {canonical!r}")
    # The row for the round about to be played (4) carries no decision yet.
    assert not by_round.get(4)
