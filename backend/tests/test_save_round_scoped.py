"""Mid-round save-state is ROUND-SCOPED (BUG-2026-07-20).

Player report: "for every round advance the investment tab must be placed at
zero" — i.e. it wasn't. Each new round opened with the PREVIOUS round's slider
allocation (e.g. 60% of pool) already applied.

Mechanism: /save-decisions stores saved_allocations for the mid-round resume
case. The engine's next-round snapshot copies saved_* forward, and although the
commit path deletes them, any carry path that survives (or a stale client
globalState) re-hydrated the new round's sliders, because the client's only
guard was "allocations currently empty" — which is precisely the state right
after a round advance.

Contract now: every save is stamped with saved_round; the client hydrates ONLY
when saved_round equals the round being played. These tests pin the server
stamp, its round-trip through the store, and the client guard (source-level,
since jest cannot run in this sandbox's CI-of-record for the page component).
"""
import os
import pathlib
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="save_scope_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
        assert r.status_code == 200, r.text
        yield c


def test_save_decisions_stamps_the_current_round(client):
    s = client.post("/api/simulations/start",
                    json={"cohort_name": "SaveScope", "facilitator_id": "god_mode"})
    sid = str(s.json()["session_id"])

    r = client.post(f"/api/simulations/{sid}/save-decisions", json={
        "allocations": {"pharma": 3_000_000},
        "decision_choice": "option_b",
    })
    assert r.status_code == 200, r.text

    # The stamp must round-trip through the store with the save itself.
    import asyncio
    import database_memory as db

    async def read():
        return await db.fetch_latest_state(sid)
    loop = asyncio.new_event_loop()
    try:
        latest = loop.run_until_complete(read())
    finally:
        loop.close()
    gs = latest["global_state"]
    assert gs.get("saved_allocations") == {"pharma": 3_000_000}
    assert gs.get("saved_round") == latest["round_number"], (
        "saved_round must equal the round the save was made in — without it the "
        "client cannot tell a resume-save from a stale carry-over"
    )


def test_client_hydration_is_gated_on_saved_round():
    """Source pin on page.js: the hydration effect must check saved_round
    against the current round for BOTH allocations and decision choice. An
    unconditional hydration is exactly the every-round-starts-at-60% bug."""
    src = (REPO / "frontend" / "app" / "page.js").read_text(encoding="utf-8")
    start = src.index("Save State Hydration")
    effect = src[start:start + 2200]
    assert "saved_round === roundNumber" in effect, \
        "hydration must be round-scoped (saved_round === roundNumber)"
    # Both hydrations sit behind the guard variable.
    guard_var = effect.index("savedForThisRound")
    assert effect.count("savedForThisRound") >= 3, \
        "both allocations and decision-choice hydration must use the round guard"
    # roundNumber must be a dependency, or the guard evaluates stale values.
    deps = effect[effect.index("}, [", guard_var):]
    assert "roundNumber" in deps.split("]")[0]


def test_commit_path_clears_the_stamp_with_the_save():
    """The commit cleanup deletes saved_allocations/saved_decision_choice; the
    stamp must go with them or a later save-less round could false-match."""
    src = (REPO / "backend" / "router.py").read_text(encoding="utf-8")
    i = src.index("Clear saved decisions since turn was committed")
    block = src[i:i + 500]
    for key in ("saved_allocations", "saved_decision_choice", "saved_round"):
        assert f'del new_global["{key}"]' in block, f"commit must clear {key}"
