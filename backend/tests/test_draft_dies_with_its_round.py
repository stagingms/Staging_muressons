"""Found by the PostgreSQL burst drill (EVAL action 11, 2026-09-10): a
committed round's draft was forwarded onto the next round.

The draft keys (saved_allocations, saved_decision_choice, saved_round,
saved_pillar_decisions) live in active_event_flags — on Postgres that is
where the dynamic fields are packed, and the memory store mirrors it. The
commit deleted them from the new round's TOP-LEVEL state and then built
the new round's flags by merging the previous round's flags in, so the
persisted R(n+1) row carried R(n)'s draft while the commit RESPONSE did
not. Inert for the cockpit (hydration is guarded by saved_round), but:

  * the facilitator console's has_saved_draft showed a draft for every team
    that had saved one the round before;
  * _auto_commit_request read saved_allocations / saved_decision_choice /
    saved_pillar_decisions with no round check, so a Force Advance on a team
    that had not touched the new round committed LAST round's draft —
    allocations, option and pillar selections — as this round's decisions,
    instead of the disclosed near-no-op roll-forward.

Now: the commit strips the draft keys from the new round's flags as well,
and the auto-commit uses a draft only when its saved_round is the round
being committed.
"""
from __future__ import annotations

import os
import sys
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

_DRAFT_KEYS = ("saved_allocations", "saved_decision_choice", "saved_round", "saved_pillar_decisions")


async def _save(ac, sid, h, rnd, pillars=None):
    body = {"allocations": {"pharma": 4_000_000.0}, "decision_choice": "option_c", "expected_round": rnd}
    if pillars is not None:
        body["pillar_decisions"] = pillars
    r = await ac.post(f"/api/simulations/{sid}/save-decisions", json=body, headers=h)
    assert r.status_code == 200, r.text[:200]


def test_a_committed_rounds_draft_is_not_on_the_next_rounds_row(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamD")
            await _save(ac, sid, h, 1)
            before = await _dash(ac, sid, h)
            assert before["global_state"]["saved_round"] == 1
            res = await _commit(ac, sid, h)
            assert res.status_code == 201, res.text[:200]
            after = await _dash(ac, sid, h)
            state = await _router.db.fetch_latest_state(sid)
            return res.json(), after, state
    resp, after, state = _run(go())
    assert after["current_round"] == 2
    for k in _DRAFT_KEYS:
        assert not resp["global_state"].get(k), k
        assert not after["global_state"].get(k), (k, after["global_state"].get(k))
        assert k not in (state["global_state"].get("active_event_flags") or {}), k


def test_the_facilitator_console_does_not_show_last_rounds_draft(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, pid, h = await _player(ac, cid, "TeamE")
            await _save(ac, sid, h, 1)
            r1 = await ac.get(f"/api/admin/cohort-pulse/{cid}")
            assert (await _commit(ac, sid, h)).status_code == 201
            r2 = await ac.get(f"/api/admin/cohort-pulse/{cid}")
            return sid, r1, r2
    sid, r1, r2 = _run(go())
    assert r1.status_code == 200, r1.text[:200]

    def _flag(r):
        row = next((t for t in r.json().get("teams", []) if t.get("session_id") == sid), None)
        assert row is not None, r.json()
        return row.get("has_saved_draft")
    assert _flag(r1) is True
    assert _flag(r2) is False, "the console showed R1's draft as an R2 draft"


def test_force_advance_after_a_commit_does_not_replay_last_rounds_pillars(monkeypatch):
    """The consequential case: a pillar-mode team saved pillars in R1 and
    committed; in R2 it saved nothing. A Force Advance must take the D2
    fallback for R2 — not commit R1's pillar selections again."""
    from pillar_configs import get_pillar_config
    cfg = get_pillar_config(1)
    pillars_r1 = {area: list(spec["options"])[0] for area, spec in cfg["areas"].items()}

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sid, _, h = await _player(ac, cid, "TeamF")
            await _save(ac, sid, h, 1, pillars=pillars_r1)
            r = await _commit(ac, sid, h, choice="", pillars=pillars_r1)
            assert r.status_code == 201, r.text[:200]
            assert r.json()["events"]["decision_paradigm"] == "multi_toggles"
            # R2: nothing saved. The facilitator force-advances the cohort to R3.
            advanced = await _router._auto_commit_laggards(cid, 3)
            d = await _dash(ac, sid, h)
            return advanced, d
    advanced, d = _run(go())
    assert advanced == 1
    assert d["current_round"] == 3
    flags = d["global_state"]["active_event_flags"]
    assert flags.get("auto_committed") is True
    assert flags.get("auto_committed_source") == "legacy_fallback", flags.get("auto_committed_source")
    assert not flags.get("r2_pillar_flags"), "R1's pillar selections were replayed as R2's decisions"


def test_the_auto_commit_request_ignores_a_draft_from_another_round():
    gs = {"saved_allocations": {"pharma": 9.0}, "saved_decision_choice": "option_c",
          "saved_pillar_decisions": {"energy": "x"}, "saved_round": 1}
    bus = [{"bu_id": "pharma", "revenue_base": 1.0}]
    body = _router._auto_commit_request(gs, bus, 2, paradigm="multi_toggles")
    assert all(d.pillar_decisions is None for d in body.decisions)
    assert all(d.choice_selected != "option_c" for d in body.decisions)
    assert all(d.capex_allocated == 1.0 for d in body.decisions)          # the near-no-op roll-forward
    body_same_round = _router._auto_commit_request(gs, bus, 1, paradigm="multi_toggles")
    assert all(d.pillar_decisions == {"energy": "x"} for d in body_same_round.decisions)
    assert all(d.capex_allocated == 9.0 for d in body_same_round.decisions)
