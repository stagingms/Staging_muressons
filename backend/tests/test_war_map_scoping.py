"""War-map scoping — the map must match the game stage (BUG-2026-07-20).

Facilitator report: a Round-2 classroom's operations map showed stakeholders
"on strike" / "hostile". Agent escalation requires CONSECUTIVE bad rounds
(dormant → watching → agitated → hostile → triggered), so a Round-2 cohort
cannot produce those states from its own data.

Cause: /api/admin/war-map aggregated EVERY player session on the platform —
the facilitator filter was optional and the projector never sent it — and each
stakeholder pin shows the WORST stage across the aggregate. One old or test
cohort with a triggered agent poisoned every classroom's projector.

Contract now: the endpoint aggregates exactly ONE cohort — ?session_id=
selects it explicitly, otherwise the caller's most recently started cohort —
and reports which cohort it scoped to, so the header can prove it to the room.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="warmap_")
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


def _cohort_with_player(client, name):
    s = client.post("/api/simulations/start",
                    json={"cohort_name": name, "facilitator_id": "god_mode"})
    assert s.status_code in (200, 201), s.text
    sid = str(s.json()["session_id"])
    g = client.post(f"/api/admin/{sid}/generate-player")
    assert g.status_code == 200, g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": pid, "password": pw})
    assert j.status_code == 200, j.text
    # NOTE: the join response's session_id is the PARENT cohort id, not the
    # player's child session — resolve the child through the store.
    import database_memory as db
    child = next(s for s, v in db._sessions.items()
                 if v.get("parent_cohort_id") == sid)
    return sid, child


def _poison_with_triggered_agent(session_id):
    """Plant a fully escalated agent — the state a Round-2 cohort cannot reach."""
    import asyncio
    import database_memory as db

    async def poison():
        latest = await db.fetch_latest_state(session_id)
        gs = latest["global_state"]
        gs["autonomous_agents"] = {"agents": {
            "the_community_activist": {"escalation_stage": "triggered", "tolerance": 3},
        }}
        await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(poison())
    finally:
        loop.close()


def _scenario(client):
    """Built fresh INSIDE each test — the suite's autouse clear_memory_db
    fixture wipes _sessions before every test, so ids cannot be cached across
    tests (a cached id points at a session that no longer exists)."""
    old_parent, old_child = _cohort_with_player(client, "WarMap-Old")
    _poison_with_triggered_agent(old_child)
    new_parent, new_child = _cohort_with_player(client, "WarMap-New")
    return dict(old_parent=old_parent, old_child=old_child,
                new_parent=new_parent, new_child=new_child)


def test_fresh_cohort_does_not_inherit_another_cohorts_escalation(client):
    """The reported bug, end to end: an OLD cohort has a triggered agent; the
    NEW (default-selected) cohort's map must stay dormant."""
    sc = _scenario(client)
    r = client.get("/api/admin/war-map")
    assert r.status_code == 200, r.text
    body = r.json()

    # Default scope = most recently started cohort, and it says which.
    assert body["cohort_session_id"] == sc["new_parent"], body
    assert body["cohort_name"] == "WarMap-New"
    assert body["team_count"] == 1, (
        f"team_count must be the selected cohort's own (1), got {body['team_count']} "
        "— a platform-wide count would include the other cohort"
    )

    stages = {s["agent_id"]: s["stage"] for s in body["stakeholders"]}
    assert stages.get("the_community_activist", "dormant") == "dormant", (
        "the old cohort's triggered agent leaked into the new cohort's map — "
        "this is exactly the 'on strike at Round 2' report"
    )
    assert all(v == "dormant" for v in stages.values())


def test_explicit_session_id_selects_that_cohort(client):
    """The poisoned cohort's OWN map must still show its escalation — scoping
    hides other cohorts, it must not sanitise the selected one."""
    sc = _scenario(client)
    r = client.get(f"/api/admin/war-map?session_id={sc['old_parent']}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cohort_session_id"] == sc["old_parent"]
    assert body["team_count"] == 1
    stages = {s["agent_id"]: s["stage"] for s in body["stakeholders"]}
    assert stages.get("the_community_activist") == "triggered", (
        "explicit selection must SHOW the selected cohort's escalation, "
        f"got stages={stages}"
    )
