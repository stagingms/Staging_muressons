"""The projector, the God-Mode leaderboard and the grading CSV rank on the
AWARDED terminal value — audit 2026-09-04 F-14 / SEAM-13 · WP-13.

GET /api/admin/leaderboard computed `treasury + (rev − opex) × synergy × 5`
for every row and never read flags.terminal_value, so a completed game was
ranked on a projection that disagreed with the value on every player screen
(served −$426M / −$82M / $122M against awarded $0 / $59.6M / $279.9M), sign
flips included. The rows carried no price_per_share, so the Trading Floor's
IPO delta never rendered.
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


async def _game(ac, rounds):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "Board", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    for rnd in range(1, rounds + 1):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                           "choice_selected": "option_b"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        bus = r.json().get("business_units") or bus
    dash = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
    return sid, dash


async def _board(ac):
    import master_credentials
    master_credentials.MASTER_PASSWORD = "test-master-pw"
    master_credentials._load_override_hash = lambda: None
    r = await ac.post("/api/admin/facilitators/login",
                      json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert r.status_code == 200, r.text[:200]
    r = await ac.get("/api/admin/leaderboard")
    assert r.status_code == 200, r.text[:200]
    return {row["session_id"]: row for row in r.json()["leaderboard"]}


@pytest.fixture(scope="module")
def played():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            done_sid, done = await _game(ac, 10)
            mid_sid, mid = await _game(ac, 4)
            rows = await _board(ac)
            return done_sid, done, mid_sid, mid, rows
    return _run(go())


def test_a_completed_game_is_ranked_on_the_awarded_terminal_value(played):
    done_sid, done, _, _, rows = played
    flags = done["global_state"]["active_event_flags"]
    assert flags.get("terminal_value") is not None, "precondition: the finale stamped a terminal value"
    row = rows[done_sid]
    assert row["terminal_value"] == pytest.approx(flags["terminal_value"], abs=0.01), \
        f"leaderboard serves {row['terminal_value']} while the team was awarded {flags['terminal_value']}"
    assert row["terminal_value_source"] == "awarded"
    # the equity bridge and profile ride along for the Trading Floor / CSV
    assert row["price_per_share"] == pytest.approx(flags["price_per_share"], abs=0.0001)
    assert row["equity_value"] == pytest.approx(flags["equity_value"], abs=0.01)
    assert row["regenerative_multiple"] == pytest.approx(flags["regenerative_multiple"], abs=1e-6)
    assert row["archetype"] == flags.get("profile_title")
    # and the awarded figure is what the other admin surface says too
    proxy = done["global_state"]["corporate_treasury"] + sum(
        b["revenue_base"] - b["opex_base"] for b in done["business_units"]) * done["global_state"]["synergy_multiplier"] * 5
    assert row["terminal_value"] != pytest.approx(proxy, abs=1.0) or flags["terminal_value"] == pytest.approx(proxy, abs=1.0)


def test_a_mid_game_row_is_labelled_a_projection(played):
    _, _, mid_sid, mid, rows = played
    row = rows[mid_sid]
    assert row["terminal_value_source"] == "projection"
    gs, bus = mid["global_state"], mid["business_units"]
    proxy = round(gs["corporate_treasury"] + sum(b["revenue_base"] - b["opex_base"] for b in bus) * gs["synergy_multiplier"] * 5, 2)
    assert row["terminal_value"] == pytest.approx(proxy, abs=0.01)
    assert row["price_per_share"] is None and row["equity_value"] is None


def test_the_row_never_reads_the_proxy_when_the_finale_has_run():
    """Source pin on the handler."""
    import inspect
    import admin_router
    src = inspect.getsource(admin_router.get_leaderboard)
    i = src.index("terminal_value_source")
    assert '.get("terminal_value")' in src[:i + 400]
    assert '"terminal_value_source": terminal_value_source' in src
