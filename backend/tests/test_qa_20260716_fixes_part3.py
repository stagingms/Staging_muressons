"""
QA-2026-07-16 regression tests for review fixes #10, #11, #13, #14.

#10 — ws_fanout is a no-op in memory/single-worker mode; local delivery still works.
#11 — _generate_temp_password returns a RANDOM per-call password (no fixed default).
#13 — sensitive admin GETs now reject anonymous callers.
#14 — coordination_store gains delete()/delete_pacing() (no-op & non-raising in memory)
      and a publish-failure counter; the reaper reports reaped pacing ids.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── #11: random temp passwords ───────────────────────────────────────────────

def test_generate_temp_password_is_random():
    import admin_router
    p1, h1 = admin_router._generate_temp_password()
    p2, h2 = admin_router._generate_temp_password()
    assert p1 != "Muressons123" and p2 != "Muressons123"
    assert p1 != p2                      # random, not a shared default
    assert len(p1) >= 10 and p1.isalnum()
    assert h1 != p1                      # a hash is stored, not the plaintext


# ── #10: ws_fanout no-op in memory, local delivery intact ────────────────────

def test_ws_fanout_is_noop_in_memory():
    import ws_fanout
    ws_fanout.configure("memory")
    assert ws_fanout.is_shared() is False
    # publish must be a safe no-op in memory mode (no PG, no raise)
    asyncio.new_event_loop().run_until_complete(
        ws_fanout.publish("session", "sid-x", {"type": "test"})
    )


def test_ws_manager_local_delivery_unaffected():
    from admin_ws import manager
    # deliver_local to a session with no sockets must not raise (no-op).
    asyncio.new_event_loop().run_until_complete(
        manager.deliver_local("session", "no-such-session", {"type": "x"})
    )
    asyncio.new_event_loop().run_until_complete(
        manager.deliver_local("all", None, {"type": "x"})
    )


# ── #14: coordination_store delete + counter (memory no-op) ──────────────────

def test_coordination_delete_is_noop_in_memory():
    import coordination_store as cs
    cs.configure("memory")
    assert cs.is_shared() is False
    loop = asyncio.new_event_loop()
    # None of these raise; all no-op in memory mode.
    loop.run_until_complete(cs.delete("pacing:whatever"))
    loop.run_until_complete(cs.delete_pacing("sid-1"))
    loop.run_until_complete(cs.delete_session_override("sid-1"))
    assert isinstance(cs.publish_failure_count(), int)


def test_reaper_reports_pacing_deleted_ids():
    import admin_shared
    import session_reaper
    sid = "qa716-reap-14"
    # A pacing entry for a session that is NOT live should be GC'd and reported.
    admin_shared._round_pacing[sid] = {"mode": "free", "unlocked_round": 1}
    summary = session_reaper.reap_once()
    assert "_pacing_deleted_ids" in summary
    assert sid in summary["_pacing_deleted_ids"]
    assert sid not in admin_shared._round_pacing


# ── #13: sensitive admin GETs are guarded ────────────────────────────────────

@pytest.mark.parametrize("path", [
    "/api/admin/god/analytics",
    "/api/admin/some-session/audit-trail",
    "/api/admin/some-session/player-sessions",
    "/api/admin/broadcast/history",
])
def test_sensitive_admin_gets_require_auth(path):
    client.cookies.clear()
    r = client.get(path)
    assert r.status_code in (401, 403), f"{path} -> {r.status_code}: {r.text[:120]}"
