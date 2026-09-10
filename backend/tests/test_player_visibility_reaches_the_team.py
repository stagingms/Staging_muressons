"""Found by the scripted classroom rehearsal (EVAL action 12, 2026-09-10):
the facilitator's "what the players see" settings never reached a player.

useAnalyticsVisibility read /api/admin/cohort/{id}/analytics-visibility —
console-only since F-21 — got 401 as a participant and failed open, so a
per-cohort player-audience override (hide the boardroom showdown, the
strategy report, a debrief surface) was saved on the console and ignored
on every participant's screen.

Now: GET /api/simulations/{sid}/player-visibility answers the team (driver
or observer) with the PLAYER column resolved exactly as the console
resolves it; the hook falls back to it when the console route refuses.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from httpx import ASGITransport

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

from main import app  # noqa: E402
from tests.test_draft_round_bound import _cohort, _login, _player, _run  # noqa: E402


def test_a_team_reads_the_player_column_the_facilitator_set(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, pid, h = await _player(ac, cid, "TeamV")
            sid2, pid2, h2 = await _player(ac, cid, "TeamW")
            console = await ac.get(f"/api/admin/cohort/{cid}/analytics-visibility")
            before = await ac.get(f"/api/simulations/{sid}/player-visibility", headers=h)
            put = await ac.put(f"/api/admin/cohort/{cid}/analytics-visibility",
                               json={"player": {"boardroom_showdown": False, "student_report_export": False}})
            after = await ac.get(f"/api/simulations/{sid}/player-visibility", headers=h)
            async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as bare:   # no facilitator cookie
                other_team = await bare.get(f"/api/simulations/{sid}/player-visibility", headers=h2)
                anon = await bare.get(f"/api/simulations/{sid}/player-visibility")
                unknown = await bare.get("/api/simulations/00000000-0000-4000-8000-000000000000/player-visibility")
            return console, before, put, after, other_team, anon, unknown
    console, before, put, after, other_team, anon, unknown = _run(go())
    assert console.status_code == 200 and put.status_code == 200, (console.text[:200], put.text[:200])
    assert before.status_code == 200 and before.json()["effective"]["player"]["boardroom_showdown"] is True
    assert after.status_code == 200
    eff = after.json()["effective"]
    assert eff["player"]["boardroom_showdown"] is False and eff["player"]["student_report_export"] is False
    assert "facilitator" not in eff, "the team never sees the console column"
    assert eff["player"] == put.json()["effective"]["player"], "resolved exactly as the console resolves it"
    assert other_team.status_code == 403, other_team.text[:200]
    assert anon.status_code in (401, 403), anon.text[:200]   # refused either way (the guard answers 403 for a cohort with players)
    # a session id that names nothing is 404, not the default column (the G04 sweep found the route
    # answering 200 for a random UUID with no credential — the guard leaves "not found" to the caller)
    assert unknown.status_code == 404, unknown.text[:200]


def test_the_cockpit_hook_falls_back_to_the_team_route():
    src = (_BACKEND_DIR.parent / "frontend" / "app" / "hooks" / "useAnalyticsVisibility.js").read_text(encoding="utf-8")
    assert "/player-visibility" in src and "playerIdHeader()" in src
    assert src.index("analytics-visibility") < src.index("/player-visibility"), "console route first, team route as the fallback"
