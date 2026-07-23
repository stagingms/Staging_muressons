"""Postgres parity — run the flows that actually broke, on the store that runs
in production.

WHY THIS FILE EXISTS (2026-07-20)
---------------------------------
Every other test in this suite runs on the in-memory store
(conftest: USE_MEMORY_DB=true). Railway runs PostgreSQL. That gap shipped a
sequence of Postgres-only production failures that 1,485 green tests could not
see, because the defect lived in the half of the storage layer the suite never
executes:

  * fn_immutable_guard blocked ALL updates to global_round_states, so saving
    the CEO-Interview config and submitting the Double-Materiality matrix both
    500'd in production — while passing every memory-mode test and every local
    manual check. (Memory mode has no triggers.)
  * Endpoint code that writes through database_memory._sessions + _persist()
    "succeeds" under Postgres but never reaches the database.

This file re-runs those exact flows over real HTTP against a real PostgreSQL.
It is the deploy gate: ci.yml runs it in a `backend-postgres` job against a
postgres:16 service container, and Railway's "Wait for CI" holds the deploy
until it is green.

SKIP BEHAVIOUR
--------------
Requires a reachable Postgres. Locally it is SKIPPED unless you opt in:

    docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=muressons postgres:16
    PG_PARITY=1 python -m pytest tests/test_postgres_parity.py -q

Skipping (rather than failing) keeps the ordinary memory-mode developer loop
green; CI is where this must always run.
"""
import os
import socket
import pathlib
import tempfile
from urllib.parse import urlparse

import pytest

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/muressons"
)


def _pg_reachable() -> bool:
    if "host=/" in DATABASE_URL:
        return True  # unix-socket DSN (local pgserver) — no TCP probe possible
    try:
        p = urlparse(DATABASE_URL)
        with socket.create_connection((p.hostname or "localhost", p.port or 5432), timeout=2):
            return True
    except OSError:
        return False


_OPTED_IN = os.environ.get("PG_PARITY", "").strip() in ("1", "true", "yes") or bool(
    os.environ.get("CI")
)

pytestmark = pytest.mark.skipif(
    not (_OPTED_IN and _pg_reachable()),
    reason="Postgres parity suite: set PG_PARITY=1 with a reachable Postgres "
           "(runs unconditionally in CI). See module docstring.",
)


@pytest.fixture(scope="module")
def client():
    """A TestClient wired to REAL Postgres — the production configuration."""
    os.environ["USE_MEMORY_DB"] = "false"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["DEBUG"] = "true"
    os.environ.setdefault("MASTER_PASSWORD", "sim2026@iim")
    d = tempfile.mkdtemp(prefix="pg_parity_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")

    from fastapi.testclient import TestClient
    import main

    # The availability probe may race the service container; the URL decides.
    assert main.db.__name__ == "database", (
        "App selected the MEMORY store despite USE_MEMORY_DB=false — the parity "
        "suite would silently test the wrong database. Is Postgres reachable at "
        f"{DATABASE_URL}?"
    )
    with TestClient(main.app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode",
                         "password": os.environ["MASTER_PASSWORD"]})
        assert r.status_code == 200, r.text
        yield c


@pytest.fixture()
def cohort(client):
    r = client.post("/api/simulations/start",
                    json={"cohort_name": f"PGParity-{os.urandom(3).hex()}",
                          "facilitator_id": "god_mode"})
    assert r.status_code in (200, 201), r.text
    return str(r.json()["session_id"])


# ── The regressions this file exists to catch ───────────────────────────────

def test_ceo_interview_config_saves_on_postgres(client, cohort):
    """THE trigger bug. Failed only on Postgres: fn_immutable_guard rejected the
    UPDATE on global_round_states and the operator saw a generic 500."""
    r = client.put(f"/api/admin/sessions/{cohort}/ceo-interview",
                   json={"ceo_interview_enabled": True,
                         "ceo_interview_voice_gender": "male"})
    assert r.status_code == 200, r.text
    assert r.json()["ceo_interview_enabled"] is True

    # And the write actually LANDED — read it back through the db, not a cache.
    r2 = client.put(f"/api/admin/sessions/{cohort}/ceo-interview", json={})
    assert r2.status_code == 200
    assert r2.json()["ceo_interview_enabled"] is True


def test_current_round_state_is_mutable_history_is_not(client, cohort):
    """The guard's contract after the fix: the round in play accepts writes;
    completed rounds and deletes are rejected.

    Uses its OWN asyncpg connection: the app's pool is bound to the TestClient's
    event loop, and the HTTP tests above already prove the app-path write. This
    test pins the TRIGGER's behaviour at the SQL level, where the bug lived.
    """
    import asyncio
    import uuid as _uuid
    import asyncpg

    async def check():
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            sid = _uuid.UUID(cohort)
            # current round (1): UPDATE must be ALLOWED — the pre-fix guard
            # rejected exactly this and broke CEO config + materiality.
            await conn.execute(
                "UPDATE global_round_states SET group_reputation = group_reputation "
                "WHERE session_id = $1 AND round_number = 1", sid)

            # fabricate round 2 so round 1 becomes historical
            row = await conn.fetchrow(
                "SELECT corporate_treasury, group_reputation FROM global_round_states "
                "WHERE session_id = $1 AND round_number = 1", sid)
            await conn.execute(
                """INSERT INTO global_round_states
                   (session_id, round_number, corporate_treasury, group_reputation,
                    synergy_multiplier, cost_of_capital, active_event_flags)
                   VALUES ($1, 2, $2, $3, 1.0, 0.05, '{}')""",
                sid, row["corporate_treasury"], row["group_reputation"])

            with pytest.raises(asyncpg.PostgresError):
                await conn.execute(
                    "UPDATE global_round_states SET group_reputation = 99 "
                    "WHERE session_id = $1 AND round_number = 1", sid)

            with pytest.raises(asyncpg.PostgresError):
                await conn.execute(
                    "DELETE FROM global_round_states WHERE session_id = $1", sid)
        finally:
            await conn.close()

    asyncio.new_event_loop().run_until_complete(check())


def test_materiality_matrix_submits_on_postgres(client, cohort):
    """The player-facing casualty of the same trigger: 'cannot get past the
    Double Materiality Matrix of Round 2'."""
    import materiality_db as m
    issues = m.get_current_config()["issues"]
    q1 = [i["id"] for i in issues
          if i["financial_impact"] == "high" and i["societal_impact"] == "high"]
    rest = [i["id"] for i in issues if i["id"] not in q1]
    r = client.post(f"/api/simulations/{cohort}/materiality", json={
        "consultant_used": False,
        "matrix_submission": {
            "quadrant_1_top_right": q1,
            "quadrant_2_top_left": rest[:2],
            "quadrant_3_bottom_right": rest[2:4],
            "quadrant_4_bottom_left": rest[4:],
        },
        "force_override_cfo": False,
    })
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True

    # Idempotency guard must REPLAY, not 500 (the historical loop bug).
    r2 = client.post(f"/api/simulations/{cohort}/materiality", json={
        "consultant_used": False,
        "matrix_submission": {"quadrant_1_top_right": q1,
                              "quadrant_2_top_left": rest[:2],
                              "quadrant_3_bottom_right": rest[2:4],
                              "quadrant_4_bottom_left": rest[4:]},
        "force_override_cfo": False,
    })
    assert r2.status_code == 200, "duplicate submit must replay, never 500"


def test_cohort_settings_persist_through_postgres(client, cohort):
    """Cohort overrides (roster cap, briefing videos) must round-trip when the
    backing store is Postgres — these are exactly the writes that a
    database_memory._sessions shortcut loses."""
    r = client.patch(f"/api/admin/sessions/{cohort}/cohort-settings",
                     json={"max_players": 12})
    assert r.status_code == 200, r.text

    r = client.post(f"/api/admin/sessions/{cohort}/briefing-videos",
                    json={"briefing_video_base": "https://cdn.example.edu/b-{round}.mp4"})
    assert r.status_code == 200, r.text

    eff = client.get(f"/api/admin/global-settings?session_id={cohort}").json()
    assert eff["briefing_video_base"] == "https://cdn.example.edu/b-{round}.mp4"

    lb = client.get("/api/admin/leaderboard").json()["leaderboard"]
    row = next(s for s in lb if s["session_id"] == cohort)
    assert row["max_players"] == 12


def test_generated_player_can_log_in_on_postgres(client, cohort):
    """Credential durability: the QA-2026-07-16 #4 class of bug (hash lived in
    one process's dict) is only observable on the Postgres path."""
    g = client.post(f"/api/admin/{cohort}/generate-player")
    assert g.status_code == 200, g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    r = client.post("/api/simulations/player-login",
                    json={"player_id": pid, "password": pw})
    assert r.status_code == 200, r.text
