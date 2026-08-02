"""
QA-2026-07-16 regression tests for review fixes #10, #11, #13, #14.

#10 — ws_fanout is a no-op in memory/single-worker mode; local delivery still works.
#11 — SUPERSEDED 2026-08-01: initial passwords are now DETERMINISTIC and
      id-derived (default_credentials: player MUR-NNN@123 / facilitator
      FAC-NNN@321), not random. The forced-change-on-first-login guarantee
      is unchanged and is now pinned in test_default_credentials.py.
#13 — sensitive admin GETs now reject anonymous callers.
#14 — coordination_store gains delete()/delete_pacing() (no-op & non-raising in memory)
      and a publish-failure counter; the reaper reports reaped pacing ids.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── #11 (superseded): initial passwords are deterministic + id-derived ───────

def test_initial_passwords_are_deterministic_and_id_derived():
    """Replaces the old 'random temp password' pin. The value is the id plus a
    fixed suffix, differs by realm, and only the hash is stored. Forced-change
    behaviour is covered in test_default_credentials.py."""
    from default_credentials import make_player_credentials, make_facilitator_credentials
    pp, ph = make_player_credentials("MUR-042")
    fp, fh = make_facilitator_credentials("FAC-042")
    assert pp == "MUR-042@123"
    assert fp == "FAC-042@321"
    assert ph != pp and fh != fp          # a hash is stored, not the plaintext
    # the retired random generator must stay gone
    import admin_router
    assert not hasattr(admin_router, "_generate_temp_password")


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
