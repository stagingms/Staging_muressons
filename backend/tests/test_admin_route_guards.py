"""Admin route authorisation — a ratchet, not a wish.

THE PROBLEM THIS PINS
    Muressons gets the ROLE dimension right. `CLAUDE.md` documents one role
    ladder, `require_sim_manager` vs `require_facilitator` is applied
    thoughtfully, and a drift tripwire keeps the ladder in sync with the UI.

    The TENANT dimension — *which cohort* — was never systematised. As of
    2026-08-02, of 286 admin routes, **69 have no role guard at all** and **68
    session-scoped routes never call `_assert_session_ownership`**. That is how
    `GET /cohort-pulse/{cohort_id}` came to return every team's session_id and
    player_id to an unauthenticated caller, and how `/{session_id}/debrief`,
    `/{session_id}/peer-evaluations`, `/{session_id}/bonuses` and
    `/annotations/{session_id}` were serving student PII and assessment data
    with no check of any kind.

WHY A RATCHET AND NOT A FIX
    Fixing 137 route-guard gaps in one commit, five days before a live cohort,
    with no golden coverage of the admin surface, would be reckless — a wrongly
    tightened guard locks a facilitator out mid-workshop, which is the failure
    mode this whole review exists to prevent.

    So: the CURRENT counts are recorded below as ceilings. They may only go
    DOWN. A new unguarded route fails immediately; the backlog is visible,
    countable and shrinking instead of invisible and growing. This is the same
    shape as `frontend/__tests__/design-token-drift.test.js`, for the same
    reason.

HOW TO USE IT
    Fixing a route: add the guard, run this file, lower the ceiling in the same
    commit. The failure message tells you the new number. Do NOT raise a ceiling
    to make this pass — that is the one edit that defeats the entire mechanism.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

_ROUTER_FILES = (
    "admin_router.py", "admin_teleprompter.py", "admin_resources.py",
    "admin_analytics.py", "admin_god_controls.py", "admin_debrief_narrative.py",
    "config_introspect.py",
)
_HTTP = ("get", "post", "put", "patch", "delete", "websocket")

# Routes that are correctly reachable without a role dependency. Each entry
# needs a reason; "it seemed fine" is not one.
_INTENTIONALLY_PUBLIC = {
    # The credential exchange itself — a guard here would be a bootstrap paradox.
    "POST /facilitators/login",
    # Clearing your own cookie must work even with an expired or invalid token.
    "POST /auth/logout",
    # WebSockets authenticate INSIDE the handler: /ws/admin verifies the JWT and
    # /ws/session/{id} verifies a signed player ticket. FastAPI's Depends does
    # not run the same way for websocket routes, so the check is inline.
    "WEBSOCKET /ws/admin",
    "WEBSOCKET /ws/session/{session_id}",
}

# ── THE RATCHET ────────────────────────────────────────────────────────────
# Measured 2026-08-02. LOWER THESE as routes are fixed. Never raise them.
_MAX_UNGUARDED = 65     # routes with no Depends(require_*), excluding the public set
_MAX_UNTENANTED = 68    # session/cohort-scoped routes with no _assert_session_ownership

# Routes fixed on 2026-08-02 because they served PII or assessment data with no
# check whatsoever. Named individually so a future refactor cannot quietly undo
# them inside the ratchet's slack.
_MUST_STAY_GUARDED = {
    "get_debrief", "list_bonuses", "list_peer_evaluations",
    "get_annotations", "get_session_messages", "get_cohort_pulse",
}


def _routes():
    """(file, lineno, 'METHOD /path', func_name, arg_src, body_src) per route."""
    out = []
    for fname in _ROUTER_FILES:
        path = _BACKEND_DIR / fname
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decs = [d for d in node.decorator_list
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr in _HTTP]
            if not decs:
                continue
            dec = decs[0]
            route = (dec.args[0].value
                     if dec.args and isinstance(dec.args[0], ast.Constant) else "?")
            out.append((fname, node.lineno, f"{dec.func.attr.upper()} {route}",
                        node.name, ast.unparse(node.args), ast.unparse(node)))
    return out


def _unguarded():
    return [r for r in _routes()
            if "Depends(require_" not in r[4] and r[2] not in _INTENTIONALLY_PUBLIC]


def _untenanted():
    return [r for r in _routes()
            if ("{session_id}" in r[2] or "{cohort_id}" in r[2])
            and "_assert_session_ownership" not in r[5]]


def _fmt(rows):
    return "\n".join(f"    {r[2]:<58} {r[0]}:{r[1]}" for r in sorted(rows, key=lambda x: x[2]))


# ── 1. The ratchet ─────────────────────────────────────────────────────────

def test_unguarded_admin_routes_do_not_increase():
    rows = _unguarded()
    assert len(rows) <= _MAX_UNGUARDED, (
        f"{len(rows)} admin routes have no role guard; the ceiling is "
        f"{_MAX_UNGUARDED}.\n\nA route with no Depends(require_*) is reachable by "
        "anyone who can reach the server.\n\n" + _fmt(rows) +
        "\n\nAdd `_guard: None = Depends(require_sim_manager)` (live-run) or "
        "`require_facilitator` (provisioning). Do NOT raise the ceiling."
    )


def test_session_scoped_routes_without_ownership_do_not_increase():
    rows = _untenanted()
    assert len(rows) <= _MAX_UNTENANTED, (
        f"{len(rows)} session/cohort-scoped routes never check ownership; the "
        f"ceiling is {_MAX_UNTENANTED}.\n\nA role guard answers 'may this person "
        "operate a run?'. It does NOT answer 'may they operate THIS run?' — "
        "without the ownership check any facilitator reaches any cohort.\n\n"
        + _fmt(rows) +
        "\n\nAdd `request: Request` and `await _assert_session_ownership(request, "
        "session_id)` as the first statement. Do NOT raise the ceiling."
    )


def test_the_ratchet_is_actually_tight():
    """A ceiling far above the real number silently permits regressions.

    Keeps the ceilings honest: if the count drops well below a ceiling because
    someone did good work, this nags them to bank it by lowering the number.
    """
    slack_guard = _MAX_UNGUARDED - len(_unguarded())
    slack_tenant = _MAX_UNTENANTED - len(_untenanted())
    assert slack_guard <= 3, (
        f"{slack_guard} routes of slack in the guard ceiling — lower "
        f"_MAX_UNGUARDED to {len(_unguarded())} and bank the progress."
    )
    assert slack_tenant <= 3, (
        f"{slack_tenant} routes of slack in the tenancy ceiling — lower "
        f"_MAX_UNTENANTED to {len(_untenanted())} and bank the progress."
    )


# ── 2. The routes that must never regress ──────────────────────────────────

@pytest.mark.parametrize("func_name", sorted(_MUST_STAY_GUARDED))
def test_pii_routes_keep_their_guard_and_their_tenancy(func_name):
    """These five served student PII or assessment data with no check at all,
    and one served the player REST credential. They are named, not counted."""
    match = [r for r in _routes() if r[3] == func_name]
    assert match, f"{func_name} not found — was it renamed? Update this test WITH the rename."
    _, _, route, _, args, body = match[0]
    assert "Depends(require_" in args, f"{route} ({func_name}) lost its role guard"
    assert "_assert_session_ownership" in body, (
        f"{route} ({func_name}) lost its ownership check — any facilitator can now "
        "read any cohort's copy of this data"
    )


def test_cohort_pulse_does_not_return_the_player_credential():
    """Belt and braces with test_phase0_run_day_fixes: session_id + player_id is
    the player REST credential, and this endpoint used to hand out both."""
    src = (_BACKEND_DIR / "admin_router.py").read_text(encoding="utf-8")
    start = src.index("async def get_cohort_pulse")
    body = src[start:start + 8000]
    assert '"player_id": sess.get("player_id")' not in body


# ── 3. Make the numbers visible even on a green run ────────────────────────

def test_report_current_debt(capsys):
    """Not an assertion — a printout. `pytest -s` shows how much is left."""
    with capsys.disabled():
        print(f"\n[route-guard debt] unguarded={len(_unguarded())}/{_MAX_UNGUARDED}  "
              f"untenanted={len(_untenanted())}/{_MAX_UNTENANTED}  "
              f"(of {len(_routes())} admin routes)")
