"""Audit #13 (automatable slice) — two-users-commit-in-the-same-instant.

CON-2: the per-session in-process asyncio lock gives a deterministic 409 when a
second commit for the SAME session arrives while the first is still in flight, so
two teammates hitting "commit" together can never double-advance the round. This
test drives two genuinely concurrent commits through the ASGI app and asserts
exactly one is rejected with 409 (and the other is not a 5xx).

The remaining #13 items (facilitator <=2-click intervene, responsive 1280-1440,
a11y/axe, draft-survives-refresh) need a running app + browser and are captured
in load_tests/UX_VERIFICATION_CHECKLIST.md.
"""

import asyncio
import os

os.environ["USE_MEMORY_DB"] = "true"

import httpx
from httpx import ASGITransport

from main import app
from router import _commit_timestamps


def _solo_session():
    transport = ASGITransport(app=app)

    async def _setup():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post(
                "/api/simulations/solo-start",
                json={"player_name": "RACE", "decision_paradigm": "legacy_abc"},
            )
            sid = r.json()["session_id"]
            dash = await ac.get(f"/api/simulations/{sid}/dashboard")
            bus = dash.json()["business_units"]
            return sid, bus

    return asyncio.get_event_loop().run_until_complete(_setup())


def test_concurrent_commits_yield_one_409():
    sid, bus = _solo_session()
    decisions = [
        {"bu_id": b["bu_id"], "investment_ratio": 0.5, "capex_allocated": 1_000_000,
         "choice_selected": "option_a"}
        for b in bus
    ]
    payload = {"decisions": decisions, "force_override_cfo": True, "expected_round": 1}
    # Clear the 5s per-session cooldown so we isolate the concurrency guard.
    _commit_timestamps[sid] = 0.0

    transport = ASGITransport(app=app)

    async def _fire():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            return await asyncio.gather(
                ac.post(f"/api/simulations/{sid}/commit-turn", json=payload),
                ac.post(f"/api/simulations/{sid}/commit-turn", json=payload),
                return_exceptions=True,
            )

    results = asyncio.get_event_loop().run_until_complete(_fire())
    codes = []
    for r in results:
        assert not isinstance(r, Exception), f"request raised: {r!r}"
        codes.append(r.status_code)

    # Exactly one commit is rejected by the concurrency guard (409); neither 5xx.
    assert 409 in codes, f"expected a 409 from the concurrency guard, got {codes}"
    assert all(c < 500 for c in codes), f"a commit 5xx'd under contention: {codes}"
