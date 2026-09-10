"""F06(b) / N3 (AUDIT_Engines_Flow_Classroom50_20260909, P1) — the commit
response is kept, per round, and can be fetched back. Decision D6: all ten
rounds.

Before: CommitTurnResponse.events existed only in the HTTP response. A
participant whose response was lost retried, got 409 stale_round, and the
client re-synced to the next round with commitResults=null — the round's
results screen was gone for good (audit probe STALE_COMMIT_RECOVERY
commitResults:null), because nothing could rebuild it.

Now: _commit_turn_impl stores the compact response under the round
COMMITTED (both stores; PG table commit_results), GET
/{sid}/commit-result/{round} serves it to the owner / observer / facilitator,
an undo drops the undone round's copy, a cohort delete cascades.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
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
from tests.test_draft_round_bound import _cohort, _commit, _dash, _login, _player, _run  # noqa: E402


def test_every_committed_round_can_be_fetched_back_and_matches_the_response(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamR")
            responses = []
            for rnd in range(1, 11):
                r = await _commit(ac, sid, h)
                assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:200]}"
                responses.append(r.json())
            stored = []
            for rnd in range(1, 11):
                g = await ac.get(f"/api/simulations/{sid}/commit-result/{rnd}", headers=h)
                assert g.status_code == 200, f"R{rnd}: {g.status_code} {g.text[:200]}"
                stored.append(g.json())
            missing = await ac.get(f"/api/simulations/{sid}/commit-result/11", headers=h)
            # a client with neither the facilitator cookie nor the player token
            async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as anon_client:
                anon = await anon_client.get(f"/api/simulations/{sid}/commit-result/3")
            return responses, stored, missing, anon
    responses, stored, missing, anon = _run(go())
    for rnd, (resp, kept) in enumerate(zip(responses, stored), start=1):
        assert kept["round_committed"] == rnd
        assert kept["new_round_number"] == resp["new_round_number"]
        assert kept["global_state"]["corporate_treasury"] == resp["global_state"]["corporate_treasury"]
        assert [b["bu_id"] for b in kept["business_units"]] == [b["bu_id"] for b in resp["business_units"]]
        # the events the results screen renders are all there; the audit-log copy is not duplicated
        kept_keys = set(kept["events"])
        resp_keys = set(resp["events"]) - {"decisions_raw"}
        assert resp_keys <= kept_keys, resp_keys - kept_keys
        assert "decisions_raw" not in kept["events"]
    assert stored[9]["events"].get("profile"), "the R10 finale is stored with its profile"
    assert missing.status_code == 404
    assert anon.status_code in (401, 403)


def test_undo_drops_the_undone_rounds_result(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamU")
            assert (await _commit(ac, sid, h)).status_code == 201
            assert (await _commit(ac, sid, h)).status_code == 201
            before = await ac.get(f"/api/simulations/{sid}/commit-result/2", headers=h)
            res = await _router.db.undo_latest_round(sid)     # the store-level undo the admin route calls
            after2 = await ac.get(f"/api/simulations/{sid}/commit-result/2", headers=h)
            after1 = await ac.get(f"/api/simulations/{sid}/commit-result/1", headers=h)
            return before.status_code, res, after2.status_code, after1.status_code
    before, res, after2, after1 = _run(go())
    assert before == 200 and res.get("success") is True and res.get("deleted_round") == 3
    assert after2 == 404, "the undone round's stored result must go with the round"
    assert after1 == 200


def test_the_store_survives_a_snapshot_round_trip():
    import database_memory as dm
    sid = f"snap-{int(time.time() * 1000)}"
    _run(dm.save_commit_result(sid, 4, {"round_committed": 4, "new_round_number": 5, "events": {"x": 1},
                                        "global_state": {}, "business_units": []}))
    dm._write_snapshot_now()
    dm._commit_results.clear()
    assert _run(dm.fetch_commit_result(sid, 4)) is None
    dm._load_from_disk()
    got = _run(dm.fetch_commit_result(sid, 4))
    assert got and got["events"] == {"x": 1} and got["new_round_number"] == 5
    dm._commit_results.pop(sid, None)


def test_results_live_in_a_journal_not_the_snapshot_and_a_drop_survives_a_reload():
    """The snapshot is rewritten in full on every _persist(); carrying every
    round's response there made each write cost O(all results). Results go
    to an append-only journal instead: the snapshot never mentions them, a
    later save for the same round wins, a tombstone written by undo / delete
    still holds after a reload, and a torn line is skipped, not fatal."""
    import json
    import database_memory as dm
    sid = f"jrn-{int(time.time() * 1000)}"
    _run(dm.save_commit_result(sid, 1, {"round_committed": 1, "new_round_number": 2, "events": {"v": 1},
                                        "global_state": {}, "business_units": []}))
    _run(dm.save_commit_result(sid, 2, {"round_committed": 2, "new_round_number": 3, "events": {"v": 1},
                                        "global_state": {}, "business_units": []}))
    _run(dm.save_commit_result(sid, 2, {"round_committed": 2, "new_round_number": 3, "events": {"v": 2},
                                        "global_state": {}, "business_units": []}))
    dm._write_snapshot_now()
    assert "commit_results" not in json.loads(dm._SNAPSHOT_PATH.read_text(encoding="utf-8"))
    dm._drop_commit_results(sid, 2)                     # what undo does
    with open(dm._COMMIT_RESULTS_PATH, "a", encoding="utf-8") as fh:
        fh.write('{"session_id": "torn", "round_number": 1, "payl')   # an interrupted write
    dm._commit_results.clear()
    dm._load_from_disk()
    assert _run(dm.fetch_commit_result(sid, 1))["events"] == {"v": 1}
    assert _run(dm.fetch_commit_result(sid, 2)) is None, "the tombstone must hold across a reload"
    # a whole-session drop (hard delete / reset) also holds
    _run(dm.save_commit_result(sid, 3, {"round_committed": 3, "new_round_number": 4, "events": {},
                                        "global_state": {}, "business_units": []}))
    dm._drop_commit_results(sid)
    dm._commit_results.clear()
    dm._load_from_disk()
    assert _run(dm.fetch_commit_result(sid, 1)) is None and _run(dm.fetch_commit_result(sid, 3)) is None


def test_a_store_failure_never_fails_the_commit(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamS")

            async def _boom(*a, **k):
                raise RuntimeError("disk full")
            monkeypatch.setattr(_router.db, "save_commit_result", _boom)
            r = await _commit(ac, sid, h)
            monkeypatch.undo()
            d = await _dash(ac, sid, h)
            return r, d
    r, d = _run(go())
    assert r.status_code == 201, r.text[:200]
    assert d["current_round"] == 2


def test_init_sql_declares_the_table_the_boot_schema_creates():
    """db/init.sql and the auto-schema in database.get_pool must agree, or a
    DB built from the script and one built at boot diverge (the two-copy
    convention pinned by test_team_consensus_nullable / test_doc_drift)."""
    import re
    init_sql = (_BACKEND_DIR.parent / "db" / "init.sql").read_text(encoding="utf-8", errors="ignore")
    pg = (_BACKEND_DIR / "database.py").read_text(encoding="utf-8", errors="ignore")

    def columns(src: str, table_stmt: str) -> list[str]:
        m = re.search(table_stmt + r"\s*\((.*?)\n\s*\);", src, re.S)
        assert m, f"{table_stmt} not found"
        return [re.sub(r"\s+", " ", ln.strip().rstrip(",")) for ln in m.group(1).splitlines() if ln.strip()]

    assert columns(init_sql, r"CREATE TABLE commit_results") == columns(pg, r"CREATE TABLE IF NOT EXISTS commit_results")
    # a cache of a response, deliberately outside the append-only guard
    assert "ON commit_results" not in init_sql
