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


def test_round_state_with_engine_objects_persists_on_postgres(client, cohort):
    """The round-7 stall (BUG-2026-07-20): a CIDeltaResult dataclass leaked
    into active_event_flags and Postgres json.dumps refused it — 'Failed to
    persist round'. The leak is fixed at the source, but the store must also
    DEGRADE like the memory store does (serialize the dataclass) so the next
    leaked object slows nobody's classroom."""
    import asyncio
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class LeakedProbe:
        applied_deltas: dict
        new_carbon_intensities: dict

    import database as db

    async def check():
        latest = await db.fetch_latest_state(cohort)
        gs = latest["global_state"]
        gs.setdefault("active_event_flags", {})["parity_leak_probe"] = LeakedProbe(
            {"pharma": -1.5}, {"pharma": 48.5})
        # This exact write raised on Postgres before the tolerant serializer.
        await db.update_latest_global_state(cohort, gs, latest["bu_states"])
        back = await db.fetch_latest_state(cohort)
        probe = back["global_state"]["active_event_flags"]["parity_leak_probe"]
        assert probe["applied_deltas"]["pharma"] == -1.5
        if db._pool is not None:
            await db._pool.close()

    # The app's pool is bound to the TestClient's event loop; running db calls
    # here needs a pool on THIS loop. Swap in a fresh one, restore after.
    saved_pool = db._pool
    db._pool = None
    try:
        asyncio.new_event_loop().run_until_complete(check())
    finally:
        db._pool = saved_pool


def test_generated_player_can_log_in_on_postgres(client, cohort):
    """Credential durability: the QA-2026-07-16 #4 class of bug (hash lived in
    one process's dict) is only observable on the Postgres path."""
    g = client.post(f"/api/admin/{cohort}/generate-player")
    assert g.status_code == 200, g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    r = client.post("/api/simulations/player-login",
                    json={"player_id": pid, "password": pw})
    assert r.status_code == 200, r.text


# ── Launch audit 2026-09-01 (F-20/F-21/F-22) — the authorization boundary on
# the production store. Ownership is resolved through db.get_session_info and
# the roster through sessions.metadata JSONB, so a memory-mode green run says
# nothing about these paths under Postgres.

def _rotate(client, fid, otp):
    from conftest import rotate_facilitator_password
    return rotate_facilitator_password(client, fid, otp)


def _god_cookies(client):
    r = client.post("/api/admin/facilitators/login",
                    json={"facilitator_id": "god_mode", "password": os.environ["MASTER_PASSWORD"]})
    assert r.status_code == 200, r.text
    return r.cookies


def test_player_token_and_first_login_gate_on_postgres(client, cohort):
    gm = _god_cookies(client)
    g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": "PG Team"}, cookies=gm)
    assert g.status_code == 200, g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": pw})
    assert lr.status_code == 200, lr.text
    team, token = lr.json()["session_id"], lr.json()["player_token"]
    assert token
    H = {"Authorization": f"Bearer {token}"}

    # The module client's jar carries god_mode's cookie; these checks need an
    # anonymous caller. Clear it and re-login at the end (re-setting the saved
    # values by hand would store them under a different domain/path and the
    # jar would then send TWO mur_session cookies).
    client.cookies.clear()
    try:
        assert client.get(f"/api/simulations/{team}/dashboard", headers=H).status_code == 200
        bare = client.get(f"/api/simulations/{team}/dashboard", headers={"X-Player-Id": pid})
        assert bare.status_code == 401 and bare.json()["detail"]["code"] == "player_token_required"
        assert client.get(f"/api/simulations/{team}/dashboard").status_code == 403
        assert client.get(f"/api/simulations/{team}/final-report").status_code == 403

        dash = client.get(f"/api/simulations/{team}/dashboard", headers=H).json()
        payload = {"decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1, "choice_selected": "option_b"}
                                 for b in dash["business_units"]],
                   "expected_round": dash["current_round"]}
        from router import _commit_timestamps
        _commit_timestamps.pop(team, None)
        blocked = client.post(f"/api/simulations/{team}/commit-turn", json=payload, headers=H)
        assert blocked.status_code == 403 and blocked.json()["detail"]["code"] == "password_change_required"
        assert client.post("/api/simulations/change-password",
                           json={"player_id": pid, "old_password": pw, "new_password": "personal-pg-1"}).status_code == 200
        _commit_timestamps.pop(team, None)
        ok = client.post(f"/api/simulations/{team}/commit-turn", json=payload, headers=H)
        assert ok.status_code == 201, ok.text
        # the rotated flag LANDED in the JSONB roster — a fresh login says so
        lr2 = client.post("/api/simulations/player-login", json={"player_id": pid, "password": "personal-pg-1"})
        assert lr2.status_code == 200 and lr2.json().get("must_change_password") is False
    finally:
        _god_cookies(client)


def test_cross_cohort_facilitator_is_refused_on_postgres(client, cohort):
    gm = _god_cookies(client)
    r = client.post("/api/admin/facilitators", json={"name": "PG Other", "role": "facilitator"}, cookies=gm)
    assert r.status_code in (200, 201), r.text
    fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
    pw = _rotate(client, fid, otp)   # leaves the jar holding fid's session
    ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies
    client.cookies.clear()
    try:
        _assert_cross_cohort_refused(client, ck, fid, cohort, gm)
    finally:
        _god_cookies(client)          # later fixtures expect god_mode in the jar


def _assert_cross_cohort_refused(client, ck, fid, cohort, gm):
    rows = client.get("/api/admin/sessions", cookies=ck).json()["sessions"]
    assert cohort not in {s["session_id"] for s in rows}, "F-20: god_mode's cohort leaked to an unrelated facilitator"
    assert client.get(f"/api/admin/{cohort}/player-sessions", cookies=ck).status_code == 403
    assert client.get(f"/api/admin/sessions/{cohort}/pacing", cookies=ck).status_code == 403
    assert client.put(f"/api/admin/cohort/{cohort}/pacing",
                      json={"pacing_mode": "manual", "max_unlocked_round": 1}, cookies=ck).status_code == 403
    assert client.post(f"/api/admin/{cohort}/generate-player",
                       json={"player_name": "Intruder"}, cookies=ck).status_code == 403
    assert client.patch(f"/api/admin/sessions/{cohort}/metadata",
                        json={"cohort_name": "Hijacked", "facilitator_id": fid}, cookies=ck).status_code == 403
    # the session list never carries roster credentials, owned or not
    for s in client.get("/api/admin/sessions", cookies=gm).json()["sessions"]:
        for p in s.get("registered_players", []) or []:
            assert "password" not in p


def test_extra_bu_keys_survive_a_round_trip_on_postgres(client, cohort):
    """F-15 parity anchor: the Postgres store packs non-column BU keys into
    risk_factors and unpacks them on read; the memory store now does the same
    pass-through. Pin the production side so the two cannot drift apart again."""
    import asyncio, uuid
    import database as db

    async def check():
        sid = str(uuid.uuid4())
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO sessions (session_id, cohort_name, facilitator_id, metadata) "
                "VALUES ($1, $2, $3, $4::jsonb)",
                uuid.UUID(sid), "F15", "god_mode", "{}")
        gs = {"round_number": 1, "corporate_treasury": 1.0, "group_reputation": 50.0,
              "synergy_multiplier": 0.3, "cost_of_capital": 0.05, "active_event_flags": {}}
        bus = [{"bu_id": "pharma", "revenue_base": 1.0, "opex_base": 1.0, "natural_capital_debt": 0.0,
                "social_license_score": 50.0, "reputation_score": 50.0, "governance_risk_score": 20.0,
                "water_dependency": 30.0, "carbon_intensity": 30.0, "staff_burnout_index": 10.0,
                "risk_factors": {}, "scope_1_ci": 12.5, "supplier_defection_active": True}]
        await db.insert_next_round(sid, 1, gs, bus, [])
        latest = await db.fetch_latest_state(sid)
        if db._pool is not None:
            await db._pool.close()
        return latest

    saved_pool = db._pool
    db._pool = None
    try:
        latest = asyncio.new_event_loop().run_until_complete(check())
    finally:
        db._pool = saved_pool
    bu = (latest.get("bu_states") or latest.get("business_units"))[0]
    assert bu["scope_1_ci"] == 12.5
    assert bu["supplier_defection_active"] is True


def test_dashboard_history_batched_queries_and_since_round_on_postgres(client, cohort):
    """F-27: fetch_round_history now runs 3 queries with `= ANY(...)` instead of
    1 + 2×rounds, and pushes since_round into SQL. Pin the shape of what comes
    back on the production store: every round, its BUs, its decisions."""
    gm = _god_cookies(client)
    g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": "Hist"}, cookies=gm)
    pid, pw = g.json()["player_id"], g.json()["password"]
    import rate_limit as _rl
    _rl._rate_buckets.clear(); _rl._persistent_bans.clear()   # earlier tests spent the per-IP login budget
    lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": pw})
    assert lr.status_code == 200, lr.text
    team, token = lr.json()["session_id"], lr.json()["player_token"]
    assert client.post("/api/simulations/change-password",
                       json={"player_id": pid, "old_password": pw, "new_password": "hist-pass-1"}).status_code == 200
    H = {"Authorization": f"Bearer {token}"}
    from router import _commit_timestamps
    bus = client.get(f"/api/simulations/{team}/dashboard", headers=H).json()["business_units"]
    for rnd in (1, 2, 3):
        _commit_timestamps.pop(team, None)
        r = client.post(f"/api/simulations/{team}/commit-turn", headers=H, json={
            "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1, "choice_selected": "option_b"} for b in bus],
            "expected_round": rnd})
        assert r.status_code == 201, r.text
        bus = r.json()["business_units"]

    full = client.get(f"/api/simulations/{team}/dashboard", headers=H)
    assert full.status_code == 200 and full.headers.get("content-encoding") == "gzip"
    body = full.json()
    assert body["current_round"] == 4
    assert [h["round_number"] for h in body["history"]] == [1, 2, 3, 4]
    for h in body["history"]:
        assert len(h["business_units"]) == len(bus)
        assert "_prev_global_states" not in h["global_state"]["active_event_flags"]
    # decisions were joined to their rounds (the batched decision query). The
    # value is the CANONICAL option after de-shuffling, so only its shape is pinned.
    for h in body["history"][:3]:
        assert h["choice_selected"] in ("option_a", "option_b", "option_c"), h["choice_selected"]
    part = client.get(f"/api/simulations/{team}/dashboard?since_round=3", headers=H).json()
    assert [h["round_number"] for h in part["history"]] == [3, 4]
    assert part["global_state"]["corporate_treasury"] == body["global_state"]["corporate_treasury"]

    import asyncio
    import database as db

    async def check():
        pool = await db.get_pool()
        try:
            latest = await db.fetch_latest_rounds([team, cohort])
            hist = await db.fetch_round_history(team, since_round=4)
            return latest, hist
        finally:
            await pool.close()

    saved_pool = db._pool
    db._pool = None
    try:
        latest, hist = asyncio.new_event_loop().run_until_complete(check())
    finally:
        db._pool = saved_pool
    assert latest.get(team) == 4
    assert [h["round_number"] for h in hist] == [4]


def test_player_ids_are_unique_across_cohorts_on_postgres(client, cohort, monkeypatch):
    """F-40 on the production store: the platform-wide check is a JSONB query
    over sessions.metadata — pin it against real Postgres."""
    import random
    import admin_router
    import database as db
    gm = _god_cookies(client)
    other = client.post("/api/simulations/start",
                        json={"cohort_name": f"PGUniq-{os.urandom(3).hex()}", "facilitator_id": "god_mode"},
                        cookies=gm).json()["session_id"]
    g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": "A1"}, cookies=gm)
    assert g.status_code == 200, g.text
    taken = g.json()["player_id"]
    letters = list(taken.split("-", 1)[1])
    draws = iter([letters] * 4)
    real_choices = random.choices

    def rigged(population, k=4, **kw):
        try:
            return next(draws)
        except StopIteration:
            return real_choices(population, k=k, **kw)
    monkeypatch.setattr(random, "choices", rigged)
    g2 = client.post(f"/api/admin/{other}/generate-player", json={"player_name": "B1"}, cookies=gm)
    assert g2.status_code == 200, g2.text
    assert g2.json()["player_id"] != taken

    # sequential path after a simulated redeploy
    r1 = client.post("/api/admin/players/induct",
                     json={"session_id": cohort, "name": "Seq1", "email": "", "programme": "", "assigned_bu": ""},
                     cookies=gm)
    assert r1.status_code == 200, r1.text
    admin_router._next_player_id = 1
    admin_router._next_player_id_seeded = False
    r2 = client.post("/api/admin/players/induct",
                     json={"session_id": other, "name": "Seq2", "email": "", "programme": "", "assigned_bu": ""},
                     cookies=gm)
    assert r2.status_code == 200, r2.text
    assert r2.json()["player_id"] != r1.json()["player_id"]

    import asyncio

    async def check():
        pool = await db.get_pool()
        try:
            return (await db.player_id_in_use(taken),
                    await db.player_id_in_use(r1.json()["player_id"]),
                    await db.player_id_in_use("MUR-NOPE"))
        finally:
            await pool.close()

    saved_pool = db._pool
    db._pool = None
    try:
        a, b, c = asyncio.new_event_loop().run_until_complete(check())
    finally:
        db._pool = saved_pool
    assert (a, b, c) == (True, True, False)
