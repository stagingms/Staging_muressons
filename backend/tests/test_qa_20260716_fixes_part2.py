"""
QA-2026-07-16 regression tests for review fixes #4-#7.

#4 — Player credentials are persisted durably; join fails closed (a registered
     player with a hash must pass the password check, never skip it).
#5 — Tripwire: every admin_router endpoint that mutates _god_mode_settings must
     publish via mark_godmode_dirty() (else it is lost on restart / split-brain).
#6 — is_round_unlocked is time-aware: a scheduled/timed unlock whose wall-clock
     time has passed opens the round even when the in-process timer is gone.
#7 — player_login rate limit is keyed by player_id (per-account), with a
     generous per-IP ceiling so a NATed classroom is not locked out.
"""

import ast
import pathlib
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}  # test-only (conftest env)


def _cookies():
    r = client.post("/api/admin/facilitators/login", json=_GOD)
    assert r.status_code == 200, r.text
    return r.cookies


# ── Fix #5: god-mode publish tripwire ────────────────────────────────────────

def test_every_godmode_mutation_publishes():
    """Any function that assigns to _god_mode_settings[...] must also call
    mark_godmode_dirty(), or the change is lost on restart and diverges across
    workers (audit §1.2). This mirrors the repo's other drift tripwires."""
    src = (pathlib.Path(__file__).resolve().parent.parent / "admin_router.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    def assigns_godmode(node):
        for n in ast.walk(node):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                            and t.value.id == "_god_mode_settings"):
                        return True
        return False

    def calls_mark(node):
        return any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "mark_godmode_dirty"
            for n in ast.walk(node)
        )

    missing = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and assigns_godmode(node) and not calls_mark(node)
    ]
    assert not missing, f"god-mode mutation without mark_godmode_dirty(): {missing}"


# ── Fix #6: time-aware pacing ────────────────────────────────────────────────

def test_scheduled_unlock_is_time_aware_after_timer_loss():
    import admin_shared
    sid = "qa716-pacing-sched"
    p = admin_shared._get_pacing(sid)
    p["mode"] = "scheduled"
    p["unlocked_round"] = 1              # in-process counter (timer never fired)
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    p["schedule"] = [None, past, future]  # round 2 due, round 3 not yet
    p["next_unlock_at"] = None
    p["_timer_tasks"] = []               # simulate restart: no live timers

    assert admin_shared.is_round_unlocked(sid, 1) is True
    assert admin_shared.is_round_unlocked(sid, 2) is True    # past schedule → open
    assert admin_shared.is_round_unlocked(sid, 3) is False   # future schedule → closed


def test_single_shot_unlock_is_time_aware():
    import admin_shared
    sid = "qa716-pacing-single"
    p = admin_shared._get_pacing(sid)
    p["mode"] = "timed"
    p["unlocked_round"] = 2
    p["schedule"] = []
    p["next_unlock_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert admin_shared.is_round_unlocked(sid, 3) is True     # pending unlock is due
    p["next_unlock_at"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert admin_shared.is_round_unlocked(sid, 3) is False    # not due yet


def test_free_mode_still_always_unlocked():
    import admin_shared
    sid = "qa716-pacing-free"
    p = admin_shared._get_pacing(sid)
    p["mode"] = "free"
    assert admin_shared.is_round_unlocked(sid, 10) is True


# ── Fix #7: login rate limit keyed by player_id ──────────────────────────────

class _FakeReq:
    def __init__(self, ip):
        self.client = type("C", (), {"host": ip})()
        self.headers = {}


def _reset_rl():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def test_login_limit_is_per_player_not_per_ip():
    import rate_limit
    _reset_rl()
    req = _FakeReq("203.0.113.9")   # one shared classroom IP
    # 10 attempts against one account are allowed, the 11th trips.
    for _ in range(10):
        rate_limit._check_rate_limit(req, "player_login", identity="MUR-AAA")
    with pytest.raises(HTTPException) as ei:
        rate_limit._check_rate_limit(req, "player_login", identity="MUR-AAA")
    assert ei.value.status_code == 429
    # A DIFFERENT player from the SAME IP is unaffected (not cross-locked).
    rate_limit._check_rate_limit(req, "player_login", identity="MUR-BBB")


def test_login_per_ip_ceiling_is_classroom_generous():
    import rate_limit
    _reset_rl()
    req = _FakeReq("203.0.113.10")
    # Without an identity, player_login uses the high per-IP ceiling (>10), so a
    # NATed room of distinct logins is not locked out at the old 10/min cap.
    for _ in range(50):
        rate_limit._check_rate_limit(req, "player_login")  # must not raise


# ── Fix #4: durable credentials + fail-closed join ───────────────────────────

def _make_cohort():
    return client.post(
        "/api/simulations/start", json={"cohort_name": "QA716-P4"}, cookies=_cookies()
    ).json()["session_id"]


def test_generated_player_survives_registry_wipe_and_join_fails_closed():
    import admin_shared
    cohort = _make_cohort()
    gen = client.post(f"/api/admin/{cohort}/generate-player", cookies=_cookies()).json()
    pid, pw = gen["player_id"], gen["password"]

    # Simulate a restart / other worker: the per-process registry is empty, so
    # the join must resolve the credential from durable registered_players.
    admin_shared._player_registry.clear()
    r_bad = client.post(
        f"/api/simulations/public/sessions/{cohort}/join",
        json={"player_id": pid, "password": "definitely-wrong", "player_name": "X"},
    )
    assert r_bad.status_code == 403, r_bad.text   # fail-closed, NOT skipped

    admin_shared._player_registry.clear()
    r_ok = client.post(
        f"/api/simulations/public/sessions/{cohort}/join",
        json={"player_id": pid, "password": pw, "player_name": "X"},
    )
    assert r_ok.status_code == 200, r_ok.text
