"""F01 / F04 (audit AUDIT_Engines_Flow_Classroom50_20260909, P0 / P1).

F01 — `save-decisions` read the latest round, mutated the whole global_state
and wrote it back through update_latest_global_state, which re-resolved
"latest" at write time. An autosave (2 s after any slider change, and on
tab-hide) whose read preceded a commit's INSERT and whose write followed it
replaced the NEW round's treasury / reputation / BU economics with the OLD
round's — round advanced, money rolled back, save reported success. A second
tab's late save was stamped with the new round and hydrated it with the old
draft.

Contract now:
  * every draft names its round (`expected_round`); any other round → 409
    stale_draft, and the draft lands nowhere;
  * a draft sent while this session's commit lock is held → 409
    commit_in_progress (the commit clears drafts anyway);
  * the write is db.update_draft_fields: draft keys only, bound to that
    round's row; update_latest_global_state is never called by the save path.

F04 — the pillar selections are part of the draft: saved, restored under the
same saved_round guard, and carried by the Force-Advance auto-commit.

These tests drive the real ASGI app on the memory store. The barrier test
reproduces the audit's schedule deterministically: the save's read completes,
a commit inserts the next round, then the save's write runs.
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


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _login(ac, mp):
    import master_credentials
    mp.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    mp.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    r = await ac.post("/api/admin/facilitators/login",
                      json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert r.status_code == 200, r.text[:200]


async def _player(ac, cid, name):
    import rate_limit
    rate_limit._rate_buckets.clear()
    r = await ac.post(f"/api/admin/{cid}/generate-player")
    pid, pw = r.json()["player_id"], r.json()["password"]
    r = await ac.post(f"/api/simulations/public/sessions/{cid}/join",
                      json={"player_id": pid, "password": pw, "player_name": name})
    assert r.status_code == 200, r.text[:200]
    r = await ac.post("/api/simulations/change-password",
                      json={"player_id": pid, "old_password": pw, "new_password": name + "#2026pw"})
    assert r.status_code == 200, r.text[:200]
    rate_limit._rate_buckets.clear()
    r = await ac.post("/api/simulations/player-login", json={"player_id": pid, "password": name + "#2026pw"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["session_id"], pid, {"Authorization": f"Bearer {r.json()['player_token']}", "X-Player-Id": pid}


async def _dash(ac, sid, hdr):
    r = await ac.get(f"/api/simulations/{sid}/dashboard", headers=hdr)
    assert r.status_code == 200, r.text[:200]
    return r.json()


async def _commit(ac, sid, hdr, choice="option_a", pillars=None):
    _router._commit_timestamps.pop(sid, None)
    d = await _dash(ac, sid, hdr)
    decs = []
    for b in d["business_units"]:
        dec = {"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 500_000,
               "choice_selected": choice}
        if pillars is not None:
            dec["pillar_decisions"] = pillars
        decs.append(dec)
    body = {"decisions": decs, "dividends_paid": 0.0, "force_override_cfo": True,
            "expected_round": d["current_round"]}
    return await ac.post(f"/api/simulations/{sid}/commit-turn", json=body, headers=hdr)


async def _cohort(ac, paradigm="legacy_abc"):
    r = await ac.post("/api/simulations/start",
                      json={"cohort_name": f"F01-{paradigm}-{int(time.time() * 1000)}",
                            "decision_paradigm": paradigm})
    assert r.status_code in (200, 201), r.text[:200]
    return r.json()["session_id"]


_ECONOMIC_GLOBAL = ("corporate_treasury", "group_reputation", "synergy_multiplier", "cost_of_capital")
_ECONOMIC_BU = ("revenue_base", "opex_base", "natural_capital_debt", "social_license_score",
                "reputation_score", "governance_risk_score", "carbon_intensity")


def _econ(d):
    gs = d["global_state"]
    return ({k: gs.get(k) for k in _ECONOMIC_GLOBAL},
            {b["bu_id"]: {k: b.get(k) for k in _ECONOMIC_BU} for b in d["business_units"]})


# ── the contract ─────────────────────────────────────────────────────────────

def test_a_draft_must_name_its_round(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamA")
            no_round = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                                     json={"allocations": {"pharma": 1_000_000}, "decision_choice": "option_a"})
            wrong = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                                  json={"allocations": {"pharma": 1_000_000}, "decision_choice": "option_a",
                                        "expected_round": 2})
            right = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                                  json={"allocations": {"pharma": 1_000_000}, "decision_choice": "option_a",
                                        "expected_round": 1})
            d = await _dash(ac, sid, h)
            return no_round, wrong, right, d
    no_round, wrong, right, d = _run(go())
    assert no_round.status_code == 409 and no_round.json()["detail"]["code"] == "expected_round_required"
    assert wrong.status_code == 409 and wrong.json()["detail"]["code"] == "stale_draft"
    assert wrong.json()["detail"]["current_round"] == 1
    assert right.status_code == 200, right.text[:200]
    gs = d["global_state"]
    assert gs["saved_allocations"] == {"pharma": 1_000_000}
    assert gs["saved_decision_choice"] == "option_a"
    assert gs["saved_round"] == 1


def test_the_save_path_never_writes_economic_state(monkeypatch):
    """The whole point of F01: the save must not go through the
    read-modify-write helper. Make that helper explode and save anyway."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamB")
            before = _econ(await _dash(ac, sid, h))

            async def _boom(*a, **k):
                raise AssertionError("save-decisions must not call update_latest_global_state")
            monkeypatch.setattr(_router.db, "update_latest_global_state", _boom)
            r = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                              json={"allocations": {"pharma": 2_000_000}, "decision_choice": "option_b",
                                    "expected_round": 1})
            monkeypatch.undo()
            after = await _dash(ac, sid, h)
            return r, before, _econ(after), after["global_state"]
    r, before, after, gs = _run(go())
    assert r.status_code == 200, r.text[:200]
    assert after == before
    assert gs["saved_allocations"] == {"pharma": 2_000_000} and gs["saved_round"] == 1


def test_a_save_during_a_commit_is_refused(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamC")
            lock = _router._get_commit_lock(sid)
            await lock.acquire()
            try:
                r = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                                  json={"allocations": {"pharma": 1}, "decision_choice": "option_a",
                                        "expected_round": 1})
            finally:
                lock.release()
            d = await _dash(ac, sid, h)
            return r, d["global_state"]
    r, gs = _run(go())
    assert r.status_code == 409 and r.json()["detail"]["code"] == "commit_in_progress"
    assert not gs.get("saved_allocations")


# ── the race, deterministically ──────────────────────────────────────────────

def test_autosave_that_loses_the_race_with_a_commit_changes_nothing(monkeypatch):
    """The audit's schedule (E01): the save reads R1; the commit inserts R2;
    the save writes. Before: R2's economics were replaced by R1's and the
    save said 200. Now: 409 stale_draft, and every economic field of R2 is
    what the commit response said it was."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamD")

            gate = asyncio.Event()          # released by the test after the commit lands
            read_done = asyncio.Event()     # the save has taken its read
            real_fetch = _router.db.fetch_latest_state
            armed = {"on": True}

            async def slow_fetch(session_id):
                state = await real_fetch(session_id)
                if armed["on"] and session_id == sid:
                    armed["on"] = False
                    read_done.set()
                    await gate.wait()       # the commit runs while we hold R1 in hand
                return state
            monkeypatch.setattr(_router.db, "fetch_latest_state", slow_fetch)

            save = asyncio.create_task(ac.post(
                f"/api/simulations/{sid}/save-decisions", headers=h,
                json={"allocations": {"pharma": 4_000_000}, "decision_choice": "option_c",
                      "expected_round": 1}))
            await asyncio.wait_for(read_done.wait(), 10)

            commit = await _commit(ac, sid, h)     # real commit: inserts R2
            assert commit.status_code == 201, commit.text[:300]
            committed = commit.json()
            gate.set()
            save_res = await asyncio.wait_for(save, 10)
            monkeypatch.undo()

            d = await _dash(ac, sid, h)
            return save_res, committed, d
    save_res, committed, d = _run(go())
    assert save_res.status_code == 409, save_res.text[:200]
    assert save_res.json()["detail"]["code"] == "stale_draft"
    assert d["current_round"] == 2
    # R2 is exactly what the commit produced — the save wrote nothing.
    for k in _ECONOMIC_GLOBAL:
        assert d["global_state"][k] == pytest.approx(committed["global_state"][k]), k
    by_id = {b["bu_id"]: b for b in committed["business_units"]}
    for b in d["business_units"]:
        for k in _ECONOMIC_BU:
            assert b.get(k) == pytest.approx(by_id[b["bu_id"]].get(k)), (b["bu_id"], k)
    gs = d["global_state"]
    assert not gs.get("saved_allocations") and gs.get("saved_round") in (None, 0)


def test_a_second_tabs_late_draft_cannot_hydrate_the_next_round(monkeypatch):
    """Deterministic variant: the round has already advanced when the old
    tab saves. The server used to stamp the save with the NEW round."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamE")
            assert (await _commit(ac, sid, h)).status_code == 201
            old_tab = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                                    json={"allocations": {"pharma": 9_000_000}, "decision_choice": "option_c",
                                          "expected_round": 1})
            d = await _dash(ac, sid, h)
            return old_tab, d
    old_tab, d = _run(go())
    assert old_tab.status_code == 409 and old_tab.json()["detail"]["code"] == "stale_draft"
    assert d["current_round"] == 2
    gs = d["global_state"]
    assert not gs.get("saved_allocations"), "the old tab's draft reached round 2"
    assert gs.get("saved_round") != 2


# ── F04: pillars are part of the draft ───────────────────────────────────────

_PILLARS_R1 = {"energy": "renewable_ppa", "operations": "lean_process",
               "supply_chain": "audit_suppliers"}


def test_pillar_selections_survive_a_reload(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sid, _, h = await _player(ac, cid, "TeamF")
            r = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                              json={"allocations": {"pharma": 1_500_000}, "decision_choice": None,
                                    "pillar_decisions": _PILLARS_R1, "expected_round": 1})
            d = await _dash(ac, sid, h)     # what a reload fetches
            return r, d
    r, d = _run(go())
    assert r.status_code == 200, r.text[:200]
    gs = d["global_state"]
    assert gs["saved_pillar_decisions"] == _PILLARS_R1
    assert gs["saved_round"] == 1


def test_force_advance_commits_the_saved_pillars_exactly_once(monkeypatch):
    """The auto-commit used to send pillar_decisions=None, which downgraded a
    pillar-mode straggler to legacy_abc + Option B. With a saved pillar
    draft it now commits those pillars, in pillar mode."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sidA, _, hA = await _player(ac, cid, "TeamG")
            sidB, _, hB = await _player(ac, cid, "TeamH")
            r = await ac.post(f"/api/simulations/{sidB}/save-decisions", headers=hB,
                              json={"allocations": {"pharma": 1_500_000}, "decision_choice": None,
                                    "pillar_decisions": _PILLARS_R1, "expected_round": 1})
            assert r.status_code == 200, r.text[:200]
            assert (await _commit(ac, sidA, hA, choice="", pillars=_PILLARS_R1)).status_code == 201
            advanced = await _router._auto_commit_laggards(cid, 2)
            dB = await _dash(ac, sidB, hB)
            return advanced, dB
    advanced, dB = _run(go())
    assert advanced == 1
    assert dB["current_round"] == 2
    flags = dB["global_state"]["active_event_flags"]
    assert flags.get("auto_committed") is True
    assert flags.get("auto_committed_source") == "draft"
    # committed in pillar mode with the saved selections, not the legacy fallback
    assert flags.get("decision_paradigm") == "multi_toggles"
    assert set(flags.get("r1_pillar_flags") or []) >= {"renewable_ppa_signed", "lean_process", "deep_audit_completed"}
    # the draft is cleared with the commit — round 2 starts clean
    assert not dB["global_state"].get("saved_pillar_decisions")


def test_force_advance_without_a_pillar_draft_discloses_the_legacy_fallback(monkeypatch):
    """D2 (2026-09-10): keep the legacy fallback for a pillar team with no
    draft — and say so, in pillar terms."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sidA, _, hA = await _player(ac, cid, "TeamI")
            sidB, _, hB = await _player(ac, cid, "TeamJ")
            assert (await _commit(ac, sidA, hA, choice="", pillars=_PILLARS_R1)).status_code == 201
            advanced = await _router._auto_commit_laggards(cid, 2)
            dB = await _dash(ac, sidB, hB)
            return advanced, dB
    advanced, dB = _run(go())
    assert advanced == 1 and dB["current_round"] == 2
    flags = dB["global_state"]["active_event_flags"]
    assert flags.get("auto_committed_source") == "legacy_fallback"
    assert "legacy option path" in (flags.get("auto_committed_reason") or "")
    assert flags.get("decision_paradigm") == "legacy_abc"
