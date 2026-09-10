"""Five-paradigm cohort smoke — the standing regression gate for the 2026-09-04 audit remediation.

WHY THIS EXISTS
    test_full_run_e2e.py plays a SOLO legacy_abc game. Nothing in the suite plays a
    COHORT game (cohort seed, NPC engines, difficulty tier, facilitator-issued
    player) on every paradigm in ``config.VALID_DECISION_PARADIGMS``. The audit
    found a paradigm (``brsr_ngrbc``) that reaches round 10 without ever running
    its own post-tick path (VAL-06), which no collected test could see because no
    test created a brsr cohort. (That defect is pinned by its own test when WP-27
    lands; this file only guarantees every paradigm completes.)

WHAT IT PINS
    For each (paradigm, difficulty_tier): a facilitator creates the cohort, mints a
    player, the player joins and commits ten rounds through the real router.
    Every commit is 201, the engine reports no failures, the finale writes the
    terminal keys, and the headline numbers are finite. For multi_toggles every
    pillar area receives a choice (an omitted area silently inherits the legacy
    proxy option's flags — FLAG-2).

    All three difficulty tiers (G06, audit 2026-09-09: the Wave 0 gate ran
    advanced and expert only).

    N1 (EVAL_AuditResponse 2026-09-10, action 5): a second game per pillar
    paradigm posts THE CLIENT'S payload shape — choice_selected '' plus
    pillar_decisions drawn from that paradigm's own pillar config — and asserts
    that paradigm's own flags appear. The canonical-option shape above cannot
    see a paradigm whose pillars are dropped on the floor, which is how the
    BRSR edition shipped unplayable from the cockpit.

WHAT IT DOES NOT PIN
    Model correctness (the golden traces do that) or the exact values.
"""

from __future__ import annotations

import asyncio
import math
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

import config  # noqa: E402
from main import app  # noqa: E402
from router import _commit_timestamps  # noqa: E402
from pillar_configs import get_pillar_config  # noqa: E402
from side_tracks.brsr_ngrbc.configs import BRSR_PILLAR_OPTIONS  # noqa: E402

_ROUNDS = config.SIM_ROUNDS
_TIERS = ("foundation", "advanced", "expert")


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            import database as _active_db
            if getattr(_active_db, "_pool", None) is not None:
                loop.run_until_complete(_active_db.close_pool())
        except Exception:  # noqa: BLE001 — teardown only
            pass
        loop.close()


def _client():
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _pillar_decisions(round_number: int, paradigm: str = "multi_toggles") -> dict:
    """First option of EVERY area — so no area is omitted (FLAG-2) — from the
    paradigm's OWN pillar config."""
    if paradigm == "brsr_ngrbc":
        cfg = BRSR_PILLAR_OPTIONS.get(round_number) or {}
    else:
        cfg = get_pillar_config(round_number) or {}
    out = {}
    for area, spec in (cfg.get("areas") or {}).items():
        options = list((spec.get("options") or {}).keys())
        if options:
            out[area] = options[0]
    return out


def _pillar_flags(round_number: int, paradigm: str) -> set:
    cfg = BRSR_PILLAR_OPTIONS.get(round_number) if paradigm == "brsr_ngrbc" else get_pillar_config(round_number)
    return {f for a in (cfg or {}).get("areas", {}).values()
            for o in a.get("options", {}).values() for f in o.get("flags_set", [])}


_PILLAR_PARADIGMS = ("multi_toggles", "brsr_ngrbc")


async def play_cohort(ac, paradigm: str, tier: str, rounds: int = _ROUNDS, client_shape: bool = False):
    """Facilitator creates the cohort; one player joins and plays every round.
    client_shape=True posts what the cockpit posts in pillar mode (N1).
    Returns (cohort_sid, player_sid, per-round commit responses)."""
    r = await ac.post("/api/admin/facilitators/login",
                      json={"facilitator_id": "god_mode",
                            "password": os.environ["MASTER_PASSWORD"]})
    assert r.status_code == 200, f"god_mode login: {r.status_code} {r.text[:200]}"

    r = await ac.post("/api/simulations/start",
                      json={"cohort_name": f"smoke-{paradigm}-{tier}{'-client' if client_shape else ''}",
                            "decision_paradigm": paradigm,
                            "difficulty_tier": tier})
    assert r.status_code == 201, f"start: {r.status_code} {r.text[:300]}"
    cohort_sid = r.json()["session_id"]

    r = await ac.post(f"/api/admin/{cohort_sid}/generate-player")
    assert r.status_code == 200, f"generate-player: {r.status_code} {r.text[:300]}"
    pid, pw = r.json()["player_id"], r.json()["password"]
    r = await ac.post(f"/api/simulations/public/sessions/{cohort_sid}/join",
                      json={"player_id": pid, "password": pw, "player_name": "Smoke"})
    assert r.status_code == 200, f"join: {r.status_code} {r.text[:300]}"
    sid = r.json()["session_id"]

    dash = await ac.get(f"/api/simulations/{sid}/dashboard")
    assert dash.status_code == 200, dash.text[:300]
    bus = dash.json()["business_units"]
    assert bus, "a new session has no business units"

    responses = []
    for rnd in range(1, rounds + 1):
        _commit_timestamps.pop(sid, None)   # clear the 5 s cooldown, as test_full_run_e2e does
        decision = {"investment_ratio": 0.4, "capex_allocated": 500_000,
                    "choice_selected": "option_a"}
        if client_shape and paradigm in _PILLAR_PARADIGMS:
            decision["choice_selected"] = ""                      # page.js in pillar mode
            decision["pillar_decisions"] = _pillar_decisions(rnd, paradigm)
        elif paradigm == "multi_toggles":
            decision["pillar_decisions"] = _pillar_decisions(rnd)
        payload = {
            "decisions": [{"bu_id": b["bu_id"], **decision} for b in bus],
            "force_override_cfo": True,
            "expected_round": rnd,
        }
        res = await ac.post(f"/api/simulations/{sid}/commit-turn", json=payload)
        assert res.status_code == 201, (
            f"{paradigm}/{tier} round {rnd}: {res.status_code} {res.text[:400]}"
        )
        body = res.json()
        failures = (body.get("events") or {}).get("engine_failures") or []
        assert not failures, f"{paradigm}/{tier} round {rnd} engine_failures: {failures}"
        responses.append(body)
        bus = body.get("business_units") or bus
    return cohort_sid, sid, responses


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


_PARAMS = [
    pytest.param(p, t, id=f"{p}-{t}")
    for p in sorted(config.VALID_DECISION_PARADIGMS)
    for t in _TIERS
]


@pytest.mark.parametrize("paradigm,tier", _PARAMS)
def test_a_cohort_game_completes_on_every_paradigm(paradigm, tier):
    async def go():
        async with _client() as ac:
            cohort_sid, sid, responses = await play_cohort(ac, paradigm, tier)
            final = await ac.get(f"/api/simulations/{sid}/dashboard")
            return cohort_sid, sid, responses, final
    _cohort, _sid, responses, final = _run(go())

    assert len(responses) == _ROUNDS
    if paradigm == "multi_toggles":
        # Pillar aggregation ran on our per-area choices (the router tags the
        # events "multi_toggles" only when pillar_decisions were supplied).
        ev1 = responses[0].get("events") or {}
        assert ev1.get("decision_paradigm") == "multi_toggles", ev1.get("decision_paradigm")
        assert ev1.get("pillar_selections"), "no pillar selections recorded"

    assert final.status_code == 200, final.text[:300]
    body = final.json()
    gs = body["global_state"]
    flags = gs.get("active_event_flags") or {}

    for key in ("corporate_treasury", "group_reputation", "synergy_multiplier", "tco2e_emissions"):
        assert _finite(gs.get(key)), f"{paradigm}/{tier}: {key} not finite: {gs.get(key)!r}"
    for key in ("terminal_value", "regenerative_multiple", "terminal_ebitda", "profile"):
        assert key in flags, f"{paradigm}/{tier}: finale did not write {key}"
    assert _finite(flags["terminal_value"]) and _finite(flags["regenerative_multiple"])
    assert 0.0 <= flags["regenerative_multiple"] <= 2.05
    assert body["current_round"] == _ROUNDS


@pytest.mark.parametrize("paradigm", _PILLAR_PARADIGMS)
def test_a_pillar_paradigm_played_through_the_clients_shape_raises_its_own_flags(paradigm):
    """N1: choice_selected '' + pillar_decisions from the paradigm's own
    config, ten rounds; every commit is labelled with the paradigm, carries
    pillar selections for every area, and the round's pillar flags are drawn
    from THAT paradigm's options. Before action 5 a brsr_ngrbc game in this
    shape committed '' into the BRSR track and raised no BRSR flag at all."""
    async def go():
        async with _client() as ac:
            cohort_sid, sid, responses = await play_cohort(ac, paradigm, "advanced", client_shape=True)
            final = await ac.get(f"/api/simulations/{sid}/dashboard")
            return responses, final
    responses, final = _run(go())
    assert len(responses) == _ROUNDS
    for rnd, body in enumerate(responses, start=1):
        ev = body.get("events") or {}
        assert ev.get("decision_paradigm") == paradigm, (rnd, ev.get("decision_paradigm"))
        assert set(ev.get("pillar_selections") or {}) == set(_pillar_decisions(rnd, paradigm)), rnd
        flags = set(ev.get("pillar_flags") or [])
        assert flags and flags <= _pillar_flags(rnd, paradigm), (rnd, flags)
    aef = final.json()["global_state"]["active_event_flags"]
    assert set(aef.get("r1_pillar_flags") or []) <= _pillar_flags(1, paradigm)
    if paradigm == "brsr_ngrbc":
        assert aef.get("brsr_track_completed") is True
        rc = (aef.get("_brsr_track_state") or {}).get("round_choices") or {}
        assert len(rc) == _ROUNDS and all(v in ("option_a", "option_b", "option_c") for v in rc.values())
