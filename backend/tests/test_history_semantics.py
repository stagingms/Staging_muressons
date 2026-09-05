"""History and analytics integrity — audit 2026-09-04 SEAM-08/09/10/11 · WP-19.

SEAM-08 The R10 commit persisted the closing state in place of history row
        10, so the state entering round 10 vanished from every history
        consumer: analytics attributed R9+R10 to "R9" (treasury +14.6M /
        −39 reputation for a real R9 of +3.4M / −8) and R10 had no entry.
SEAM-09 "Predicted vs actual" paired round r's prediction with round r−1's
        outcome (sign flips on reputation).
SEAM-10 The board-pressure −3 reputation was applied AFTER persistence: it
        existed only in the commit response and the next poll put it back.
SEAM-11 The live Consequence-DNA endpoint built every graph at "round 1"
        (round_number is a sibling key of the fetched state, not inside it).
"""
from __future__ import annotations

import asyncio
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

import database as db  # noqa: E402
import router as _router  # noqa: E402
from history_semantics import (  # noqa: E402
    ENTERING_R10_BAG, display_round, entering_rows, produced_by_round, splice_final_state, stash_entering_state,
)
from main import app  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _play(ac, rounds=10, choice="option_b"):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    r = await ac.post("/api/simulations/solo-start", json={"player_name": "Hist", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    commits = []
    for rnd in range(1, rounds + 1):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                           "choice_selected": choice} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        commits.append(r.json())
        bus = commits[-1].get("business_units") or bus
    return sid, commits


# ── the helper ─────────────────────────────────────────────────────────────

def test_splice_restores_row_ten_and_appends_the_final_only_when_asked():
    rows = [{"round_number": k, "global_state": {"corporate_treasury": k * 1e6, "active_event_flags": {}},
             "business_units": [{"bu_id": "pharma", "natural_capital_debt": k}]} for k in range(1, 10)]
    entering = {"corporate_treasury": 10e6, "group_reputation": 60.0, "active_event_flags": {"r9_flags": ["community_fund"]}}
    final = {"corporate_treasury": 12e6, "group_reputation": 55.0, "active_event_flags": {"terminal_value": 5e8, "game_over": True}}
    stash_entering_state(final, entering, [{"bu_id": "pharma", "natural_capital_debt": 10}])
    rows.append({"round_number": 10, "global_state": final, "business_units": [{"bu_id": "pharma", "natural_capital_debt": 12}]})
    ten = splice_final_state(rows)
    assert len(ten) == 10 and ten[-1]["round_number"] == 10
    assert ten[-1]["global_state"]["corporate_treasury"] == 10e6, "row 10 is the ENTERING state"
    assert ten[-1]["global_state"]["r9_flags"] == ["community_fund"]   # non-column flag keys unpacked, as the stores do
    assert ten[-1]["business_units"][0]["natural_capital_debt"] == 10
    eleven = splice_final_state(rows, include_final=True)
    assert len(eleven) == 11 and eleven[-1]["is_final"] is True and eleven[-1]["round_number"] == 11
    assert eleven[-1]["global_state"]["corporate_treasury"] == 12e6
    assert ENTERING_R10_BAG not in eleven[-1]["global_state"]["active_event_flags"]
    # an unfinished game is untouched
    assert splice_final_state(rows[:5], include_final=True) == rows[:5]


def test_consumer_helpers_read_the_convention():
    seed, r7 = {"round_number": 1}, {"round_number": 7}
    final = {"round_number": 11, "is_final": True}
    assert (display_round(seed), display_round(r7), display_round(final)) == (1, 7, 10)
    # row K holds the events of the round-(K-1) commit; the seed holds none; the closing row holds R10's
    assert (produced_by_round(seed), produced_by_round(r7), produced_by_round(final)) == (None, 6, 10)
    assert [h["round_number"] for h in entering_rows([seed, r7, final])] == [1, 7]


# ── through the router ─────────────────────────────────────────────────────

@pytest.fixture
def game():
    # function-scoped: conftest clears the memory store before every test
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            sid, commits = await _play(ac)
            dash = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
            hist10 = await db.fetch_round_history(sid)
            hist11 = await db.fetch_round_history(sid, include_final=True)
            return sid, commits, dash, hist10, hist11
    return _run(go())


def test_after_r10_history_has_ten_entering_states_and_a_final_state(game):
    sid, commits, dash, hist10, hist11 = game
    assert [h["round_number"] for h in hist10] == list(range(1, 11))
    assert [h["round_number"] for h in hist11] == list(range(1, 12)) and hist11[-1]["is_final"] is True
    # row K = the state entering K: row k+1's treasury is commit k's persisted treasury
    for k in range(1, 10):
        assert hist11[k]["global_state"]["corporate_treasury"] == pytest.approx(
            commits[k - 1]["global_state"]["corporate_treasury"], abs=0.01), f"row {k + 1}"
    # row 10 is the state ENTERING round 10 (commit 9's result), not the finale
    assert hist10[9]["global_state"]["corporate_treasury"] == pytest.approx(commits[8]["global_state"]["corporate_treasury"], abs=0.01)
    # the final row is the closing state — what the dashboard shows
    assert hist11[10]["global_state"]["corporate_treasury"] == pytest.approx(dash["global_state"]["corporate_treasury"], abs=0.01)
    assert hist11[10]["global_state"]["corporate_treasury"] == pytest.approx(commits[9]["global_state"]["corporate_treasury"], abs=0.01)
    # the dashboard's own history (the cockpit's) keeps ten rows, now with the real row 10
    assert len(dash["history"]) == 10
    assert dash["history"][9]["global_state"]["corporate_treasury"] == pytest.approx(commits[8]["global_state"]["corporate_treasury"], abs=0.01)
    # latest state: still round 10, game over
    assert dash["current_round"] == 10


def test_analytics_r9_and_r10_deltas_equal_the_commit_time_deltas(game, monkeypatch):
    sid, commits, dash, _, hist11 = game
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            assert (await ac.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", "password": "test-master-pw"})).status_code == 200
            r = await ac.get(f"/api/admin/analytics/player/{sid}")
            assert r.status_code == 200, r.text[:200]
            d = await ac.get(f"/api/admin/{sid}/debrief")
            return r.json(), (d.json() if d.status_code == 200 else None)
    analytics, debrief = _run(go())
    impact = {row["round"]: row for row in analytics["decision_impact"]}
    assert sorted(impact) == list(range(1, 11)), sorted(impact)
    for k in (9, 10):
        entering = hist11[k - 1]["global_state"]
        closing = hist11[k]["global_state"]
        assert impact[k]["treasury_delta"] == pytest.approx(closing["corporate_treasury"] - entering["corporate_treasury"], abs=0.01)
        assert impact[k]["reputation_delta"] == pytest.approx(closing["group_reputation"] - entering["group_reputation"], abs=0.01)
    # R10's delta is the finale's own movement (commit 10 vs commit 9)
    assert impact[10]["treasury_delta"] == pytest.approx(
        commits[9]["global_state"]["corporate_treasury"] - commits[8]["global_state"]["corporate_treasury"], abs=0.01)
    if debrief and debrief.get("rounds"):
        cards = {c.get("round_number") or c.get("round"): c for c in debrief["rounds"]}
        assert 10 in cards, sorted(cards)


def test_prediction_pairs_with_the_round_it_predicted(monkeypatch):
    """A cohort player posts a prediction for round 5, plays round 5; the
    narrative's "predicted vs actual" must carry ROUND 5's deltas."""
    import master_credentials
    import rate_limit
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            assert (await ac.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", "password": "test-master-pw"})).status_code == 200
            r = await ac.post("/api/simulations/start", json={"cohort_name": "SEAM09", "facilitator_id": "god_mode"})
            cid = r.json()["session_id"]
            g = (await ac.post(f"/api/admin/{cid}/generate-player")).json()
            assert (await ac.post(f"/api/simulations/public/sessions/{cid}/join", json={"player_id": g["player_id"], "password": g["password"], "player_name": "Seer"})).status_code == 200
            assert (await ac.post("/api/simulations/change-password", json={"player_id": g["player_id"], "old_password": g["password"], "new_password": "Seer#2026pw"})).status_code == 200
            rate_limit._rate_buckets.clear()
            lg = await ac.post("/api/simulations/player-login", json={"player_id": g["player_id"], "password": "Seer#2026pw"})
            sid = lg.json()["session_id"]
            H = {"Authorization": f"Bearer {lg.json()['player_token']}", "X-Player-Id": g["player_id"]}
            bus = (await ac.get(f"/api/simulations/{sid}/dashboard", headers=H)).json()["business_units"]
            commits = []
            for rnd in range(1, 6):
                if rnd == 5:
                    r = await ac.post(f"/api/simulations/{sid}/prediction", headers=H, json={"round_number": 5, "text": "R5 will hurt"})
                    assert r.status_code in (200, 201), r.text[:200]
                _router._commit_timestamps.pop(sid, None)
                r = await ac.post(f"/api/simulations/{sid}/commit-turn", headers=H, json={
                    "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                                   "choice_selected": "option_b"} for b in bus],
                    "force_override_cfo": True, "expected_round": rnd})
                assert r.status_code == 201, f"R{rnd}: {r.text[:200]}"
                commits.append(r.json())
                bus = commits[-1].get("business_units") or bus
            n = await ac.get(f"/api/admin/debrief-narrative/{cid}")
            assert n.status_code == 200, n.text[:200]
            return sid, commits, n.json()
    sid, commits, narrative = _run(go())
    me = next(p for p in narrative["players"] if p["session_id"] == sid)
    pair = next(p for p in me["predicted_vs_actual"] if p["round"] == 5)
    c4, c5 = commits[3], commits[4]
    assert pair["actual"]["treasury_delta"] == pytest.approx(c5["global_state"]["corporate_treasury"] - c4["global_state"]["corporate_treasury"], abs=0.01)
    assert pair["actual"]["reputation_delta"] == pytest.approx(c5["global_state"]["group_reputation"] - c4["global_state"]["group_reputation"], abs=0.01)


def test_board_pressure_penalty_is_persisted():
    """R3 with EBITDA below the board's target triggers the warning; the −3
    must be in the NEXT dashboard, not only in the commit response."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            sid, commits = await _play(ac, rounds=2)
            # make the board's target unreachable: the baseline is last round's EBITDA stock
            latest = await db.fetch_latest_state(sid)
            gs = latest["global_state"]
            gs["historical_ebitda"] = 10_000_000_000.0
            await db.update_latest_global_state(sid, gs, latest["bu_states"])
            before = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["global_state"]["group_reputation"]
            bus = commits[-1]["business_units"]
            _router._commit_timestamps.pop(sid, None)
            r3 = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
                "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                               "choice_selected": "option_b"} for b in bus],
                "force_override_cfo": True, "expected_round": 3})
            assert r3.status_code == 201, r3.text[:200]
            dash = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
            return r3.json(), dash
    c3, dash = _run(go())
    bp = c3["events"].get("board_pressure") or {}
    assert bp.get("triggered") is True, bp
    assert bp.get("reputation_penalty") == -3
    assert dash["global_state"]["group_reputation"] == pytest.approx(c3["global_state"]["group_reputation"], abs=0.01), \
        "the −3 the player was shown is not in the persisted state"


def test_live_dna_graph_is_built_at_the_session_round():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            sid, _ = await _play(ac, rounds=6)
            r = await ac.get(f"/api/simulations/{sid}/consequence-dna-data")
            assert r.status_code == 200, r.text[:200]
            return r.json()
    dna = _run(go())
    assert dna.get("current_round") == 7, dna.get("current_round")


def test_board_pressure_runs_before_persistence():
    import inspect
    src = inspect.getsource(_router._commit_turn_impl)
    assert src.index("Board Pressure Events") < src.index("if current_round == 10:\n            # R10: Update existing state in-place")


def test_latest_state_consumers_read_the_closing_state(monkeypatch):
    """A finished cohort team: the peer leaderboard, the cohort pulse, the
    session report, the complexity feed and the data export all see what the
    team ENDED on — not the state it entered R10 with, which is what hist[-1]
    became once row 10 stopped being overwritten."""
    import master_credentials
    import rate_limit
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            assert (await ac.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", "password": "test-master-pw"})).status_code == 200
            r = await ac.post("/api/simulations/start", json={"cohort_name": "SEAM08-consumers", "facilitator_id": "god_mode"})
            cid = r.json()["session_id"]
            g = (await ac.post(f"/api/admin/{cid}/generate-player")).json()
            assert (await ac.post(f"/api/simulations/public/sessions/{cid}/join", json={"player_id": g["player_id"], "password": g["password"], "player_name": "Closer"})).status_code == 200
            assert (await ac.post("/api/simulations/change-password", json={"player_id": g["player_id"], "old_password": g["password"], "new_password": "Closer#2026pw"})).status_code == 200
            rate_limit._rate_buckets.clear()
            lg = await ac.post("/api/simulations/player-login", json={"player_id": g["player_id"], "password": "Closer#2026pw"})
            sid = lg.json()["session_id"]
            H = {"Authorization": f"Bearer {lg.json()['player_token']}", "X-Player-Id": g["player_id"]}
            bus = (await ac.get(f"/api/simulations/{sid}/dashboard", headers=H)).json()["business_units"]
            commits = []
            for rnd in range(1, 11):
                _router._commit_timestamps.pop(sid, None)
                r = await ac.post(f"/api/simulations/{sid}/commit-turn", headers=H, json={
                    "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                                   "choice_selected": "option_b"} for b in bus],
                    "force_override_cfo": True, "expected_round": rnd})
                assert r.status_code == 201, f"R{rnd}: {r.text[:200]}"
                commits.append(r.json())
                bus = commits[-1].get("business_units") or bus
            out = {"sid": sid, "cid": cid, "commits": commits}
            out["dash"] = (await ac.get(f"/api/simulations/{sid}/dashboard", headers=H)).json()
            out["peer"] = (await ac.get(f"/api/simulations/{sid}/peer-leaderboard", headers=H)).json()
            out["export"] = (await ac.get(f"/api/simulations/{sid}/export-my-data", headers=H)).json()
            out["pulse"] = (await ac.get(f"/api/admin/cohort-pulse/{cid}")).json()
            out["report"] = (await ac.get(f"/api/admin/session-report/{sid}")).json()
            out["feed"] = (await ac.get(f"/api/admin/complexity-events/{sid}")).json()
            return out
    o = _run(go())
    closing = o["dash"]["global_state"]["corporate_treasury"]
    entering_r10 = o["commits"][8]["global_state"]["corporate_treasury"]
    assert closing == pytest.approx(o["commits"][9]["global_state"]["corporate_treasury"], abs=0.01)
    assert closing != pytest.approx(entering_r10, abs=1.0), "the finale moved the treasury; the probe is meaningful"
    # peer leaderboard: the team ranks on its closing treasury
    me = next(row for row in o["peer"]["leaderboard"] if row["isYou"])
    assert me["treasury"] == pytest.approx(closing, abs=0.01)
    # cohort pulse: current = closing, round 10 / finished, the R10 cell = entering R10, no R11 cell
    team = next(t for t in o["pulse"]["teams"] if t["session_id"] == o["sid"])
    assert team["current"]["treasury"] == pytest.approx(closing, abs=0.01)
    assert team["round"] == 10 and team["finished"] is True and team["committed"] is True
    assert set(map(int, team["history"].keys())) == set(range(1, 11))
    assert team["history"]["10"]["treasury"] == pytest.approx(entering_r10, abs=0.01)   # JSON keys are strings
    # session report: ten entering rows + the closing row, flagged
    rh = o["report"]["round_history"]
    assert [x["round"] for x in rh] == list(range(1, 12)) and rh[-1]["is_final"] is True
    assert rh[-1]["treasury"] == pytest.approx(closing, abs=0.01)
    assert rh[9]["treasury"] == pytest.approx(entering_r10, abs=0.01)
    # complexity feed: labelled by the round whose commit produced the events, 1..10 — never 0 or 11
    rounds_seen = [f["round"] for f in o["feed"]["feed"]]
    assert rounds_seen and all(1 <= r <= 10 for r in rounds_seen), rounds_seen
    assert all(e["round"] == f["round"] for f in o["feed"]["feed"] for e in f["events"])
    # export: everything stored — the ten entering states and the closing state
    ex = o["export"]["round_history"]
    assert [x["round_number"] for x in ex] == list(range(1, 12)) and ex[-1]["is_final"] is True
