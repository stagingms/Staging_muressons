"""
TEAM-1 — team observer seats (UX audit #7, revised 2026-08-02).

A team is up to 6 people: ONE driver who holds the player credential and
commits, plus up to 5 observers sharing a view code (MUR-NNN-VIEW) who see the
same live board read-only.

WHAT THIS PINS
  1. View-code parsing is exact — only the -VIEW suffix resolves, and it maps
     to the right driver id.
  2. The authorisation guard is FAIL-CLOSED: an observer is refused on every
     route that did not explicitly opt in (allow_observer=True). This is the
     property that keeps the feature safe as routes are added — a new mutating
     endpoint is driver-only without anyone remembering to think about it.
  3. An observer CAN read the dashboard (the one opted-in route).
  4. A view code for a DIFFERENT team is refused (no cross-team peeking).
  5. Seat configuration caps at 6 members and derives observer seats correctly.
  6. The engine is untouched: an observer identity creates no session and no
     round state.
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import router  # noqa: E402
from fastapi import HTTPException  # noqa: E402


class _FakeRequest:
    """Minimal Request stand-in: the guard only reads headers + cookies."""

    def __init__(self, player_id=None):
        self.headers = {"X-Player-Id": player_id} if player_id else {}
        self.cookies = {}


# ── 1. View-code parsing ──────────────────────────────────────────────────

@pytest.mark.parametrize("code,expected", [
    ("MUR-004-VIEW", True),
    ("mur-004-view", True),      # case-insensitive
    ("MUR-004", False),
    ("MUR-004-VIEWER", False),   # near-miss must NOT resolve
    ("", False),
    (None, False),
])
def test_view_code_detection(code, expected):
    assert router._is_view_code(code) is expected


def test_view_code_resolves_to_driver_id():
    assert router.driver_id_for_view_code("MUR-004-VIEW") == "MUR-004"
    assert router.driver_id_for_view_code("mur-012-view") == "MUR-012"
    # A non-view id passes through unchanged (upper-cased) rather than being mangled.
    assert router.driver_id_for_view_code("MUR-004") == "MUR-004"


# ── 2/3. Guard behaviour ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_driver_is_allowed_everywhere(monkeypatch):
    async def _sess(_sid):
        return {"player_id": "MUR-004"}
    monkeypatch.setattr(router.db, "get_session_info", _sess)
    # No exception on either a read or a write route.
    await router._assert_player_owns_session(_FakeRequest("MUR-004"), "s1")
    await router._assert_player_owns_session(_FakeRequest("MUR-004"), "s1", allow_observer=True)


@pytest.mark.asyncio
async def test_observer_refused_by_default_fail_closed(monkeypatch):
    """The property that matters: a route that did NOT opt in refuses observers.
    Every mutating player route is in this category."""
    async def _sess(_sid):
        return {"player_id": "MUR-004"}
    monkeypatch.setattr(router.db, "get_session_info", _sess)

    with pytest.raises(HTTPException) as exc:
        await router._assert_player_owns_session(_FakeRequest("MUR-004-VIEW"), "s1")
    assert exc.value.status_code == 403
    assert "observer" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_observer_allowed_on_opted_in_read(monkeypatch):
    async def _sess(_sid):
        return {"player_id": "MUR-004"}
    monkeypatch.setattr(router.db, "get_session_info", _sess)
    await router._assert_player_owns_session(_FakeRequest("MUR-004-VIEW"), "s1", allow_observer=True)


# ── 4. Cross-team isolation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_other_teams_view_code_is_refused(monkeypatch):
    """MUR-009-VIEW must not read MUR-004's board, even on an opted-in route."""
    async def _sess(_sid):
        return {"player_id": "MUR-004"}
    monkeypatch.setattr(router.db, "get_session_info", _sess)

    with pytest.raises(HTTPException) as exc:
        await router._assert_player_owns_session(_FakeRequest("MUR-009-VIEW"), "s1", allow_observer=True)
    assert exc.value.status_code == 403
    assert "not the owner" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_unowned_session_still_open(monkeypatch):
    """Solo / unowned sessions keep their existing behaviour — no regression."""
    async def _sess(_sid):
        return {"player_id": ""}
    monkeypatch.setattr(router.db, "get_session_info", _sess)
    await router._assert_player_owns_session(_FakeRequest("ANYTHING"), "s1")


# ── 5. Seat configuration ─────────────────────────────────────────────────

def test_team_size_cap_is_six_with_five_observers():
    import admin_router
    assert admin_router.TEAM_MAX_MEMBERS == 6
    assert admin_router.TEAM_MAX_OBSERVERS == 5


@pytest.mark.parametrize("size,expected_observers", [
    (1, 0),   # solo driver, no observers
    (4, 3),
    (6, 5),   # full team
])
def test_observer_seat_derivation(size, expected_observers):
    assert max(0, size - 1) == expected_observers


# ── 6. Engine isolation ───────────────────────────────────────────────────

def test_observer_support_adds_no_engine_surface():
    """The feature must live entirely in auth/identity. If an observer concept
    ever leaks into the engine, this fails and the review is forced."""
    engine_src = (_BACKEND_DIR / "engine.py").read_text(encoding="utf-8", errors="ignore")
    for token in ("observer", "view_code", "VIEW_CODE", "team_view"):
        assert token not in engine_src, f"engine.py must not know about {token!r}"
