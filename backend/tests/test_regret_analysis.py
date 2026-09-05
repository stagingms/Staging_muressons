"""Audit F-06 (SEAM-04): "The Road Not Taken" must compare like with like.

The shadow ticks run process_tick only; the baseline they were diffed against
was new_global AFTER post_tick, run_new_engines and board pressure. Every
alternative therefore "would have yielded" exactly the round's post-tick
deductions — identical for both alternatives, to the cent, in 9 of 10 rounds
of the audit's probe run (R4: both +$30,022,303.52; R9: both +$21,933,383.74).
The shadow now runs process_tick + post_tick (the option's own effects live in
post_tick) and is diffed against the actual state at the same point.
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


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _play(ac, rounds):
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "Regret", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    out = []
    for rnd in range(1, rounds + 1):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3,
                           "capex_allocated": 2_000_000, "choice_selected": "option_a"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        body = r.json()
        out.append(body)
        bus = body.get("business_units") or bus
    return out


def test_alternatives_are_not_the_post_tick_gap_in_disguise():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play(ac, 4)
    bodies = _run(go())
    seen_regret = 0
    for rnd, body in enumerate(bodies, start=1):
        ev = body.get("events") or {}
        regret = ev.get("decision_regret")
        if not regret:
            continue
        seen_regret += 1
        assert regret.get("scope") == "engine_and_round_effects"
        alts = regret["alternatives"]
        assert len(alts) == 2, alts
        deltas = [a["treasury_delta"] for a in alts.values()]
        # WP-22: the two alternatives can LEGITIMATELY carry the same delta —
        # R2's option_b and option_c both cost $0 against option_a's $2.5M, so
        # when the canonical primary is option_a (the display order is shuffled
        # per session) both read +2.5M, which is also the round's post-tick gap
        # once nothing else in run_new_engines moves treasury. The heuristic
        # below only passed on that case while the biodiversity invoice (F-19a)
        # was still charging every round; skip it when the config itself
        # prices the two alternatives identically.
        from round_configs import get_round_config
        _opts = (get_round_config(rnd) or {}).get("options", {})
        _primary = ({"option_a", "option_b", "option_c"} - set(alts)).pop()
        _expected = {k: (_opts.get(k, {}).get("impacts", {}).get("treasury", 0)
                         - _opts.get(_primary, {}).get("impacts", {}).get("treasury", 0)) for k in alts}
        if len(set(_expected.values())) == 1:
            continue
        # The symptom: both alternatives equal to (engine final treasury - persisted treasury).
        wf_final = (ev.get("consequence_waterfall") or {}).get("final_treasury")
        persisted = body["global_state"]["corporate_treasury"]
        if wf_final is not None:
            gap = round(float(wf_final) - float(persisted), 2)
            if abs(gap) > 1.0:
                assert not all(abs(d - gap) < 0.01 for d in deltas), (
                    f"R{rnd}: both alternatives equal the post-tick gap {gap} — pipeline artifact")
    assert seen_regret >= 3, "decision_regret was not produced"


def test_round_one_alternatives_differ_from_each_other():
    """R1 options carry different costs (A $0 scan, B $3M audit, C), applied in
    post_tick — so the two counterfactuals cannot be identical."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play(ac, 1)
    body = _run(go())[0]
    regret = (body.get("events") or {}).get("decision_regret")
    assert regret, "no decision_regret in the R1 response"
    deltas = {k: v["treasury_delta"] for k, v in regret["alternatives"].items()}
    assert len(set(deltas.values())) == 2, f"alternatives identical: {deltas}"
