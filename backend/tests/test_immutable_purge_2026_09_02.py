"""Append-only guard: admin purge/reset must not use ALTER TABLE … DISABLE TRIGGER.

Root cause of the undeletable-cohort / delete-500 (launch-audit follow-up
2026-09-02): the hard-delete, reset and undo paths disabled the immutability
triggers with `ALTER TABLE … DISABLE TRIGGER` *inside* the delete transaction.
That statement (a) needs table ownership, (b) takes a lock that conflicts with
concurrent turn commits, and (c) — the actual failure — poisoned the whole
transaction whenever it failed. The `except: pass` around it swallowed the real
error ("must be owner of table …"), and the very next DELETE then raised
`current transaction is aborted, commands ignored until end of transaction
block`, which was NOT caught: the request 500'd and the cohort survived the
rollback. It never reproduced in local dev because the dev role owns the tables.

The fix: the guard `fn_immutable_guard` honours a transaction-local flag
(`SET LOCAL muressons.allow_purge = 'on'`, via db._allow_immutable_purge) set
only by those admin paths. No ownership, no lock, no way to poison the txn.

Two layers of test:
  * SOURCE TRIPWIRES (always run) — pin that the anti-pattern is gone and the
    flag mechanism is wired on both sides (guard + every purge caller).
  * LIVE POSTGRES (skipped unless a real PG is reachable, e.g. probe/ptpg.sh) —
    prove the real delete path works, that the purge succeeds even for a
    NON-OWNER role (the prod precondition), and that immutability is still
    enforced for ordinary writes.
"""
import os
import re
import socket
import uuid
from urllib.parse import urlparse

import pytest

import database  # noqa: E402  (module under test)

_DB_SRC = os.path.join(os.path.dirname(database.__file__), "database.py")
with open(_DB_SRC, encoding="utf-8") as _f:
    _SRC = _f.read()


# ── SOURCE TRIPWIRES (no database required) ──────────────────────────────────

def test_no_disable_trigger_statements_remain():
    """The ALTER TABLE … DISABLE/ENABLE TRIGGER anti-pattern must not come back.

    Match only executed SQL (inside a quote), so the explanatory comments that
    mention the old approach by name don't trip the wire."""
    executed = re.findall(r"""["'][^"'\n]*(?:DISABLE|ENABLE)\s+TRIGGER[^"'\n]*["']""", _SRC)
    assert not executed, f"purge paths must not toggle triggers via ALTER TABLE; found {executed}"


def test_guard_honours_the_transaction_local_flag():
    """fn_immutable_guard must allow the operation when muressons.allow_purge is on."""
    assert "current_setting('muressons.allow_purge', true) = 'on'" in _SRC, \
        "the immutability guard no longer checks the allow_purge bypass flag"
    # The bypass must sit BEFORE the DELETE-always RAISE, or a delete never reaches it.
    guard = _SRC[_SRC.index("fn_immutable_guard"):]
    bypass_at = guard.index("muressons.allow_purge")
    delete_raise_at = guard.index("TG_OP = 'DELETE'")
    assert bypass_at < delete_raise_at, "allow_purge bypass must precede the DELETE guard"


def test_every_purge_path_sets_the_flag_not_a_trigger_toggle():
    """delete_session (hard), reset_session_to_round1 and the round-undo path all
    route through the single helper, so none can silently drift back."""
    assert "async def _allow_immutable_purge(conn)" in _SRC
    assert "SET LOCAL muressons.allow_purge = 'on'" in _SRC
    # exactly the three purge/reset/undo call sites use the helper
    assert _SRC.count("await _allow_immutable_purge(conn)") == 3, \
        "expected the helper at all three purge sites (delete hard, reset, undo)"


# ── LIVE POSTGRES ────────────────────────────────────────────────────────────

_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/muressons"
)


def _pg_reachable() -> bool:
    try:
        p = urlparse(_DATABASE_URL)
        with socket.create_connection((p.hostname or "localhost", p.port or 5432), timeout=1.5):
            return True
    except Exception:
        return False


pg = pytest.mark.skipif(not _pg_reachable(),
                        reason=f"no reachable Postgres at {_DATABASE_URL} (run via probe/ptpg.sh)")


async def _seed_cohort(conn) -> str:
    """A cohort with two rounds of *historical* (immutable) round rows."""
    sid = uuid.uuid4()
    await conn.execute(
        "INSERT INTO sessions(session_id,cohort_name,facilitator_id) VALUES($1,'ZZ_purge_test','god_mode')", sid)
    for rnd in (1, 2):
        stid = uuid.uuid4()
        await conn.execute(
            "INSERT INTO global_round_states(state_id,session_id,round_number,corporate_treasury,"
            "group_reputation,synergy_multiplier,cost_of_capital,active_event_flags) "
            "VALUES($1,$2,$3,100,50,1.0,0.1,'{}'::jsonb)", stid, sid, rnd)
        await conn.execute(
            "INSERT INTO bu_round_states(global_state_id,bu_id,revenue_base,opex_base,natural_capital_debt,"
            "social_license_score,reputation_score,governance_risk_score,water_dependency,carbon_intensity,"
            "risk_factors) VALUES($1,'bu_a',10,5,0,50,50,0,0,0,'{}'::jsonb)", stid)
        await conn.execute(
            "INSERT INTO decision_audit_log(session_id,round_number,decision_node_id,choice_selected,"
            "capex_allocated) VALUES($1,$2,'node','option_a',0)", sid, rnd)
    return str(sid)


async def _counts(conn, sid):
    return (
        await conn.fetchval("SELECT count(*) FROM sessions WHERE session_id=$1", uuid.UUID(sid)),
        await conn.fetchval("SELECT count(*) FROM global_round_states WHERE session_id=$1", uuid.UUID(sid)),
        await conn.fetchval("SELECT count(*) FROM decision_audit_log WHERE session_id=$1", uuid.UUID(sid)),
    )


async def _purge(conn, sid):
    await conn.execute("DELETE FROM decision_audit_log WHERE session_id=$1", uuid.UUID(sid))
    await conn.execute("DELETE FROM bu_round_states WHERE global_state_id IN "
                       "(SELECT state_id FROM global_round_states WHERE session_id=$1)", uuid.UUID(sid))
    await conn.execute("DELETE FROM global_round_states WHERE session_id=$1", uuid.UUID(sid))
    await conn.execute("DELETE FROM sessions WHERE session_id=$1", uuid.UUID(sid))


@pg
@pytest.mark.asyncio(loop_scope="module")
async def test_real_hard_delete_removes_a_cohort_with_history():
    """The actual production path: db.delete_session(hard=True) on a cohort that
    has committed (immutable) round rows must remove everything and return True."""
    pool = await database.get_pool()   # (re)installs the new fn_immutable_guard
    async with pool.acquire() as conn:
        sid = await _seed_cohort(conn)
        assert await _counts(conn, sid) == (1, 2, 2)
    ok = await database.delete_session(sid, hard=True)
    assert ok is True
    async with pool.acquire() as conn:
        assert await _counts(conn, sid) == (0, 0, 0)


@pg
@pytest.mark.asyncio(loop_scope="module")
async def test_purge_succeeds_for_a_non_owner_role_and_guard_still_holds():
    """The prod precondition, reproduced: a role that CANNOT `ALTER TABLE …
    DISABLE TRIGGER` (non-owner) must still be able to purge via the flag, and a
    write WITHOUT the flag must still be rejected by the immutability guard."""
    import asyncpg
    pool = await database.get_pool()
    async with pool.acquire() as owner:
        await owner.execute("DROP ROLE IF EXISTS app_purge_test")
        await owner.execute("CREATE ROLE app_purge_test NOSUPERUSER NOCREATEDB LOGIN PASSWORD 'x'")
        await owner.execute("GRANT USAGE ON SCHEMA public TO app_purge_test")
        await owner.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO app_purge_test")
    try:
        p = urlparse(_DATABASE_URL)
        r = await asyncpg.connect(user="app_purge_test", password="x",
                                  host=p.hostname or "localhost", port=p.port or 5432,
                                  database=(p.path or "/muressons").lstrip("/"))
        try:
            async with pool.acquire() as owner:
                # (a) non-owner CAN purge with the flag
                sid = await _seed_cohort(owner)
                async with r.transaction():
                    await r.execute("SET LOCAL muressons.allow_purge = 'on'")
                    await _purge(r, sid)
                assert await _counts(owner, sid) == (0, 0, 0), "flagged purge should delete as non-owner"

                # (b) the OLD ALTER … DISABLE TRIGGER, as this non-owner, would have
                #     poisoned the txn — assert that precondition really holds here,
                #     so (a) is a meaningful proof and not a role with hidden powers.
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await r.execute("ALTER TABLE decision_audit_log DISABLE TRIGGER trg_immutable_decision_audit_log")

                # (c) without the flag, immutability is STILL enforced
                sid2 = await _seed_cohort(owner)
                with pytest.raises(Exception) as ei:
                    await r.execute("DELETE FROM decision_audit_log WHERE session_id=$1", uuid.UUID(sid2))
                assert "Immutability violation" in str(ei.value)

                # cleanup sid2 via the flag
                async with owner.transaction():
                    await owner.execute("SET LOCAL muressons.allow_purge = 'on'")
                    await _purge(owner, sid2)
        finally:
            await r.close()
    finally:
        async with pool.acquire() as owner:
            await owner.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_purge_test")
            await owner.execute("REVOKE USAGE ON SCHEMA public FROM app_purge_test")
            await owner.execute("DROP ROLE IF EXISTS app_purge_test")
