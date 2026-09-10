"""F06(b) / N3 — the commit_results table on REAL PostgreSQL (the store the
class runs on): round-trip through the JSONB column, upsert on re-commit
after an undo, undo cleanup, cohort-delete cascade.

Gated like tests/test_postgres_parity.py (PG_PARITY=1, USE_MEMORY_DB=false,
reachable DATABASE_URL).
"""
from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/muressons")


def _pg_reachable() -> bool:
    if "host=/" in DATABASE_URL:
        return True
    try:
        p = urlparse(DATABASE_URL)
        with socket.create_connection((p.hostname or "localhost", p.port or 5432), timeout=2):
            return True
    except OSError:
        return False


_OPTED_IN = os.environ.get("PG_PARITY", "").strip() in ("1", "true", "yes") or bool(os.environ.get("CI"))
pytestmark = pytest.mark.skipif(
    not (_OPTED_IN and _pg_reachable()),
    reason="Postgres commit-result suite: set PG_PARITY=1, USE_MEMORY_DB=false and a reachable DATABASE_URL.",
)

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

import main  # noqa: E402
from tests.test_draft_round_bound import _cohort, _commit, _login, _player  # noqa: E402
from tests.test_draft_round_bound_pg import _run_pg  # noqa: E402


@pytest.fixture(autouse=True)
def _real_store():
    assert main.db.__name__ == "database"


def test_commit_results_round_trip_undo_and_cascade_on_postgres(monkeypatch):
    async def go():
        import database as db
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "PGr")
            r1 = await _commit(ac, sid, h)
            r2 = await _commit(ac, sid, h)
            assert r1.status_code == 201 and r2.status_code == 201
            got2 = await ac.get(f"/api/simulations/{sid}/commit-result/2", headers=h)
            kept2 = got2.json()
            undo = await db.undo_latest_round(sid)
            gone2 = await ac.get(f"/api/simulations/{sid}/commit-result/2", headers=h)
            # re-commit round 2: the row is replaced, not duplicated
            r2b = await _commit(ac, sid, h)
            got2b = await ac.get(f"/api/simulations/{sid}/commit-result/2", headers=h)
            # a hard session delete removes its stored results too
            deleted = await db.delete_session(sid, hard=True)   # the store-level delete the admin cascade calls per session
            left = await db.fetch_commit_result(sid, 1)
            return r2.json(), kept2, undo, gone2.status_code, r2b.status_code, got2b.json(), deleted, left
    resp2, kept2, undo, gone2, r2b, kept2b, deleted, left = _run_pg(go())
    assert kept2["round_committed"] == 2 and kept2["new_round_number"] == 3
    assert kept2["global_state"]["corporate_treasury"] == resp2["global_state"]["corporate_treasury"]
    assert undo.get("success") is True and gone2 == 404
    assert r2b == 201 and kept2b["round_committed"] == 2
    if deleted is not None:
        assert left is None, "commit_results must cascade with the session"
