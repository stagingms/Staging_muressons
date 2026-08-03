"""Phase 0 — the run-day fixes, 2026-08-02.

Each test below pins one defect that could have shown up in front of a cohort.
They are grouped by the plan item that produced them.

  0.1  pacing gating          -> covered by tests/test_pacing_gated_modes.py
  0.4  cohort-pulse guard     -> §A here
  0.7  R10 committed once     -> §B here
  0.9  Force Advance survives -> §C here
  0.10 deploy_preflight runs  -> §D here
  0.12 multi-worker opt-in    -> §E here
"""

import asyncio
import inspect
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
_REPO = _BACKEND_DIR.parent

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

import admin_router  # noqa: E402
import admin_shared  # noqa: E402
import database_memory as db  # noqa: E402
import scale_preflight  # noqa: E402
from main import app  # noqa: E402
from router import _commit_timestamps  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _solo_session():
    transport = ASGITransport(app=app)

    async def _setup():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/api/simulations/solo-start",
                              json={"player_name": "PHASE0", "decision_paradigm": "legacy_abc"})
            sid = r.json()["session_id"]
            dash = await ac.get(f"/api/simulations/{sid}/dashboard")
            return sid, dash.json()["business_units"]

    return _run(_setup())


# ══ §A · 0.4 — cohort-pulse was unguarded and leaked the player credential ══

def _route(path, method="GET"):
    for r in admin_router.admin_router.routes:
        if getattr(r, "path", None) == path and method in getattr(r, "methods", ()):
            return r
    raise AssertionError(f"{method} {path} not found")


def test_cohort_pulse_has_a_role_guard():
    """It had NO Depends at all, and returned every team's session_id AND
    player_id — which together ARE the player REST credential (router.py binds
    a caller to a session by string-comparing the X-Player-Id header). Cohort
    ids are reachable from the unrate-limited public join-code lookup."""
    deps = [getattr(d.call, "__name__", "") for d in
            _route("/api/admin/cohort-pulse/{cohort_id}").dependant.dependencies]
    assert any(name.startswith("require_") for name in deps), (
        f"cohort-pulse has no role guard (dependencies: {deps})"
    )


def test_cohort_pulse_enforces_cohort_ownership():
    src = inspect.getsource(admin_router.get_cohort_pulse)
    assert "_assert_session_ownership" in src, (
        "a role guard alone lets any facilitator read any other cohort's board"
    )


def test_cohort_pulse_does_not_return_player_ids():
    src = inspect.getsource(admin_router.get_cohort_pulse)
    assert '"player_id": sess.get("player_id")' not in src, (
        "player_id is half the player REST credential and CohortPulse.js never "
        "used it — do not put it back"
    )


# ══ §B · 0.7 — round 10 is committed exactly once ═══════════════════════════

def test_game_over_blocks_a_further_commit():
    """R10 persists in place, so there is no uq_session_round to violate and the
    '> 10' gate never trips — a second POST re-ran process_tick over resolved
    terminal state and compounded treasury, emissions and terminal valuation."""
    sid, bus = _solo_session()

    state = _run(db.fetch_latest_state(sid))
    gs = dict(state["global_state"])
    gs["game_over"] = True
    gs["game_over_reason"] = "simulation_complete_r10"
    _run(db.update_latest_global_state(session_id=sid, global_state=gs,
                                       bu_states=state["bu_states"]))

    _commit_timestamps[sid] = 0.0
    payload = {
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.5,
                       "capex_allocated": 1_000_000, "choice_selected": "option_a"}
                      for b in bus],
        "force_override_cfo": True,
        "expected_round": 1,
    }
    transport = ASGITransport(app=app)

    async def _post():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.post(f"/api/simulations/{sid}/commit-turn", json=payload)

    r = _run(_post())
    assert r.status_code == 409, f"a completed run accepted another commit ({r.status_code})"
    assert "already completed" in str(r.json().get("detail", "")).lower()


def test_r10_persist_branch_sets_game_over():
    import router
    src = inspect.getsource(router._commit_turn_impl)
    assert 'new_global["game_over"] = True' in src, (
        "the normal R10 finale must set game_over — completion was previously "
        "only ever INFERRED as `rn >= 10`, in three separate places"
    )


def test_r10_decisions_reach_the_audit_log():
    """The R10 branch used to be `for dec in decisions_raw: pass`, under a
    comment claiming insert_next_round logged them — which it cannot, because
    the R10 branch does not call it. The graded finale had no decision record."""
    import router
    src = inspect.getsource(router._commit_turn_impl)
    assert "log_decisions" in src, "R10 decisions are still not being written"

    sid, _ = _solo_session()
    before = len(_run(db.get_decision_log(sid)))
    written = _run(db.log_decisions(session_id=sid, round_number=10, decisions=[
        {"bu_id": "pharma", "choice_selected": "option_c", "capex_allocated": 42,
         "player_id": "MUR-001", "decision_node_id": "r10"},
    ]))
    assert written == 1
    after = _run(db.get_decision_log(sid))
    assert len(after) == before + 1
    assert after[-1]["choice_selected"] == "option_c"


def test_log_decisions_exists_on_both_backends_with_one_signature():
    """The AST parity tripwire enforces this too; assert it here so a divergence
    is named rather than discovered as a Postgres-only 500 in production."""
    import database as pg
    assert inspect.signature(pg.log_decisions) == inspect.signature(db.log_decisions)


# ══ §C · 0.9 — Force Advance is not reverted by the refresher ═══════════════

@pytest.mark.parametrize("key", ["_fa_force", "_fa_round", "_fa_deadline_at"])
def test_free_advance_keys_are_process_local(key):
    """These are a one-shot COMMAND, not replicated policy. Treating them as
    policy meant the 3-second coordination refresher restored the shared row's
    stale _fa_force=False over the facilitator's action — so whether the button
    worked was a race between that refresh and the 5-second player poll."""
    assert key in admin_shared._PACING_LOCAL_FIELDS


def test_the_refresher_cannot_revert_a_force_advance():
    sid = "phase0-force-advance"
    pacing = admin_shared._get_pacing(sid)
    try:
        pacing["_fa_force"] = True
        # Exactly what coordination_store.rehydrate() does on its 3s tick, with
        # a shared row written before the facilitator pressed the button.
        admin_shared.restore_pacing_policy(sid, {"mode": "free", "_fa_force": False})
        assert admin_shared._get_pacing(sid)["_fa_force"] is True, (
            "the refresher reverted Force Advance — the facilitator gets "
            '{"status":"ok"} and nothing happens'
        )
        assert "_fa_force" not in admin_shared.pacing_policy_snapshot(sid)
    finally:
        admin_shared._round_pacing.pop(sid, None)


def test_force_advance_publishes_the_surrounding_policy():
    src = inspect.getsource(admin_router.force_advance_cohort)
    assert "mark_pacing_dirty" in src, (
        "force_advance_cohort was the only pacing mutator that never published"
    )


# ══ §D · 0.10 — the preflight actually runs ═════════════════════════════════

def test_main_invokes_the_deployment_preflight():
    """186 lines of boot checks that `grep run_preflight` found only in a test,
    while PREDEPLOY_CHECKLIST.md told operators to look for output it could
    never produce."""
    src = (_BACKEND_DIR / "main.py").read_text(encoding="utf-8")
    assert "run_preflight" in src and "format_findings" in src


def test_docker_start_invokes_scale_preflight():
    """scale_preflight is reached only via `python -m scale_preflight` in the
    container entrypoint, so no import graph can see it. This tripwire is the
    only thing standing between it and a dead-code sweep."""
    entry = (_REPO / "docker-start.sh").read_text(encoding="utf-8")
    assert "python -m scale_preflight" in entry


# ══ §E · 0.12 — multi-worker is opt-in, not merely Postgres-gated ═══════════

_PG = {"USE_MEMORY_DB": "false", "DEBUG": "false"}


def test_postgres_alone_no_longer_unlocks_multiple_workers():
    workers, warnings = scale_preflight.safe_worker_count({**_PG, "WEB_CONCURRENCY": "4"})
    assert workers == 1, (
        "Postgres is necessary but nowhere near sufficient — ~12 stores are "
        "still per-process (id counters, cohort quota, rate limits, facilitator "
        "notes and assessment data)"
    )
    assert any("MURESSONS_MULTIWORKER_VERIFIED" in w for w in warnings)


def test_explicit_opt_in_is_honoured():
    workers, _ = scale_preflight.safe_worker_count(
        {**_PG, "WEB_CONCURRENCY": "4", "MURESSONS_MULTIWORKER_VERIFIED": "true"})
    assert workers == 4


def test_one_worker_is_always_fine():
    for env in ({}, {"WEB_CONCURRENCY": "1"}, {**_PG, "WEB_CONCURRENCY": "1"}):
        assert scale_preflight.safe_worker_count(env)[0] == 1
