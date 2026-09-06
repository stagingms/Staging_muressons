"""RNG-2, RNG-5, RNG-6, RNG-8 (audit 2026-09-04, Wave 3).

RNG-2  The facilitator's rng_seed (wizard "Advanced" box / PATCH cohort-settings)
       was written to the flags only; both stores re-pack the stale top-level
       copy over it on write, so the typed seed never reached the game.
RNG-5  The CEO-interview fallback scorer added process-global ±1.0 noise.
RNG-6  The regulator's message quoted a different random amount than it
       deducted (closed by WP-23's FIN-09; pinned here).
RNG-8  Board vote, coalition check, sandbox whistleblower, the R2 materiality BU
       pick and the supply-chain disruption roll drew from the process-global
       Random. They draw from the cohort's event stream.
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import config  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── RNG-2 ────────────────────────────────────────────────────────────────────

def test_a_patched_seed_reaches_the_live_state_of_the_cohort_and_its_teams():
    import httpx
    from httpx import ASGITransport
    from main import app
    import database as db

    parent = _run(db.create_session(cohort_name=f"RNG2-{uuid.uuid4().hex[:8]}", facilitator_id="god_mode"))
    pid = parent.get("session_id") or parent.get("id")
    child = _run(db.create_session(cohort_name=f"RNG2-team-{uuid.uuid4().hex[:8]}", facilitator_id="god_mode",
                                   player_id="MUR-901", parent_cohort_id=pid))
    cid = child.get("session_id") or child.get("id")

    async def go(seed):
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            login = await ac.post("/api/admin/facilitators/login",
                                  json={"facilitator_id": "god_mode", "password": config.MASTER_PASSWORD})
            assert login.status_code == 200, login.text[:200]
            r = await ac.patch(f"/api/admin/sessions/{pid}/cohort-settings", json={"rng_seed": seed}, cookies=login.cookies)
            assert r.status_code == 200, r.text[:300]
            g = await ac.get(f"/api/admin/sessions/{pid}/cohort-settings", cookies=login.cookies)
            return g.json()

    body = _run(go("class-2026-A"))
    for sid in (pid, cid):
        latest = _run(db.fetch_latest_state(sid))
        assert latest["global_state"]["active_event_flags"]["stochastic_seed"] == "class-2026-A", sid
    assert body["rng_seed"] == "class-2026-A" and body["rng_seed_source"] != "divergent"
    # an explicit blank un-seeds (the wizard no longer sends a blank; a deliberate PATCH may)
    _run(go(""))
    for sid in (pid, cid):
        latest = _run(db.fetch_latest_state(sid))
        assert latest["global_state"]["active_event_flags"].get("stochastic_seed") != "class-2026-A"


# ── RNG-5 ────────────────────────────────────────────────────────────────────

def test_the_ceo_fallback_noise_is_a_stable_per_session_stream():
    import inspect
    import router
    src = inspect.getsource(router)
    seg = src[src.index("# Fallback: noise-based scoring"):][:900]
    assert "random.uniform(-1.0, 1.0)" not in seg
    assert 'stable_rng(session_id, "ceo_interview_fallback", dim_id)' in seg
    from rng_util import stable_rng
    a = [stable_rng("s1", "ceo_interview_fallback", d).uniform(-1, 1) for d in ("x", "y")]
    b = [stable_rng("s1", "ceo_interview_fallback", d).uniform(-1, 1) for d in ("x", "y")]
    c = [stable_rng("s2", "ceo_interview_fallback", d).uniform(-1, 1) for d in ("x", "y")]
    assert a == b and a != c


# ── RNG-6 ────────────────────────────────────────────────────────────────────

def test_the_regulator_quotes_the_amount_it_deducts_seeded_or_not():
    import inspect
    import npc_stakeholders as N
    src = inspect.getsource(N)
    tail = src[src.index('diagnostics["regulatory_fine"] = fine'):][:900]
    assert 'f"€{fine / 1_000_000:.1f}M fine"' in tail          # the message is rewritten with the applied fine


# ── RNG-8 ────────────────────────────────────────────────────────────────────

def test_no_module_level_random_in_the_five_gameplay_draws():
    import inspect
    import board_governance, org_politics, regulatory_sandbox, supply_chain_network, admin_router
    assert "random.random()" not in inspect.getsource(board_governance.simulate_board_vote)
    assert "random.random()" not in inspect.getsource(org_politics.evaluate_csuite_support)
    assert "random.random()" not in inspect.getsource(regulatory_sandbox._evaluate_exogenous_trigger)
    sc = inspect.getsource(supply_chain_network.process_supply_chain_tick)
    assert "random.random()" not in sc and "random.choice(" not in sc and "random.uniform(" not in sc
    ar = inspect.getsource(admin_router)
    seg = ar[ar.index('selected_bu = global_state.get("r2_selected_bu")'):][:1200]
    assert "random.choice(active_bus)" not in seg and '"r2_materiality_bu"' in seg


def test_seeded_sessions_vote_and_coalesce_the_same_way_every_time():
    from board_governance import create_initial_board_state, simulate_board_vote, SHAREHOLDER_RESOLUTIONS
    from org_politics import create_initial_org_politics_state, evaluate_csuite_support
    gs = {"group_reputation": 55.0, "round_number": 4, "active_event_flags": {"stochastic_seed": "rng8"}}
    board = create_initial_board_state()
    res = SHAREHOLDER_RESOLUTIONS[0]
    v1 = simulate_board_vote(board, res, "support", gs)
    v2 = simulate_board_vote(board, res, "support", gs)
    assert [d["voted_for"] for d in v1["vote_details"]] == [d["voted_for"] for d in v2["vote_details"]]
    org = create_initial_org_politics_state()
    c1 = evaluate_csuite_support(org, ["esg", "capex"], 3_000_000, gs)
    c2 = evaluate_csuite_support(org, ["esg", "capex"], 3_000_000, gs)
    assert c1 == c2
