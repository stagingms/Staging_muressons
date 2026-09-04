"""Applying pacing MID-RUN must clamp to the round the class is actually on.

THE DEFECT (PACING-2, 2026-08-04)
---------------------------------
Reported: "it did not work even when I reapplied". PACING-1 had fixed the
raise-only ceiling, and its tests passed — but the clamp was being fed the
wrong number.

`_gated_ceiling()` clamps the free-play sentinel down to "the round the cohort
is on", and read that from `fetch_latest_round(session_id)` where session_id is
the COHORT id. A cohort id names the SHELL session; every gameplay row belongs
to a player SUB-session. The shell therefore sits at round 1 forever. With two
teams on round 4, the lookup answered 1, so switching to Manual set the ceiling
to 1 and locked the round the class was mid-way through.

WHY PACING-1'S TESTS MISSED IT
------------------------------
Every one of them applied pacing at round 1, where the wrong answer (the shell's
round, 1) and the right answer (the current round, 1) are the same number. The
bug was undetectable by construction. Each test below therefore plays SEVERAL
rounds first — that is the whole point of the file, and why it is separate from
test_pacing_gated_modes.py.
"""
import pytest

BUS = ["pharma", "electronics", "consumer_goods", "software"]


@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _clear():
    import rate_limit
    import router as rmod
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    getattr(rmod, "_commit_timestamps", {}).clear()


@pytest.fixture
def cohort(client):
    _clear()
    assert client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": "god_mode", "password": "test-master-pw"}
                       ).status_code == 200
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "MidRun", "facilitator_id": "god_mode"})
    assert r.status_code == 201, r.text
    return str(r.json()["session_id"])


def _join(client, sid):
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    return str(j["session_id"]), {"X-Player-Id": g["player_id"]}


def _commit(client, psid, headers, rnd):
    _clear()
    return client.post(f"/api/simulations/{psid}/commit-turn", headers=headers,
                       json={"decisions": [{"bu_id": b, "capex_allocated": 1_000_000,
                                            "choice_selected": "option_a",
                                            "investment_ratio": 0.2} for b in BUS],
                             "dividends_paid": 0, "expected_round": rnd})


def _play(client, team, upto):
    """Commit rounds 1..upto for one team, leaving it ON round upto+1."""
    psid, headers = team
    for rnd in range(1, upto + 1):
        r = _commit(client, psid, headers, rnd)
        assert r.status_code == 201, (rnd, r.status_code, r.text[:150])


# ── the reported bug ───────────────────────────────────────────────────────

def test_applying_manual_midrun_does_not_lock_the_round_in_progress(client, cohort):
    """THE bug: ceiling clamped to 1 while the class was on round 4."""
    from admin_shared import _get_pacing, is_round_unlocked

    a, b = _join(client, cohort), _join(client, cohort)
    _play(client, a, 3)
    _play(client, b, 3)           # both teams are now ON round 4

    assert client.post(f"/api/admin/sessions/{cohort}/pacing",
                       json={"mode": "manual"}).status_code == 200

    ceiling = _get_pacing(cohort)["unlocked_round"]
    assert ceiling == 4, f"ceiling clamped to {ceiling} — the class is on round 4"
    assert is_round_unlocked(cohort, 4) is True, "the round in progress must stay playable"
    assert is_round_unlocked(cohort, 5) is False, "the NEXT round must wait"


def test_the_class_can_still_commit_the_round_it_is_in(client, cohort):
    """The user-visible half: a real team, mid-run, is not frozen out."""
    a = _join(client, cohort)
    _play(client, a, 3)
    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})

    assert _commit(client, a[0], a[1], 4).status_code == 201, \
        "applying pacing mid-run locked the round the team was already playing"

    blocked = _commit(client, a[0], a[1], 5)
    assert blocked.status_code == 403
    assert "locked" in blocked.json()["detail"].lower()

    assert client.post(f"/api/admin/sessions/{cohort}/pacing/unlock").status_code == 200
    assert _commit(client, a[0], a[1], 5).status_code == 201


@pytest.mark.parametrize("mode", ["manual", "timed"])
def test_both_gated_modes_clamp_to_the_live_round(client, cohort, mode):
    from admin_shared import _get_pacing
    a = _join(client, cohort)
    _play(client, a, 5)                     # on round 6
    body = {"mode": mode}
    if mode == "timed":
        body["interval_seconds"] = 300
    assert client.post(f"/api/admin/sessions/{cohort}/pacing", json=body).status_code == 200
    assert _get_pacing(cohort)["unlocked_round"] == 6


# ── teams out of sync ──────────────────────────────────────────────────────

def test_the_ceiling_follows_the_leading_team_not_the_trailing_one(client, cohort):
    """MAX, not MIN.

    A min would lock the leaders out of the round they are already in. Max
    keeps the leaders playing and lets the straggler catch up inside the
    unlocked window — the documented free-advance behaviour.
    """
    from admin_shared import _get_pacing

    fast, slow = _join(client, cohort), _join(client, cohort)
    _play(client, fast, 5)          # on round 6
    _play(client, slow, 2)          # on round 3

    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"})
    assert _get_pacing(cohort)["unlocked_round"] == 6

    # the leader keeps playing…
    assert _commit(client, fast[0], fast[1], 6).status_code == 201
    # …and the straggler can still catch up rather than being frozen
    assert _commit(client, slow[0], slow[1], 3).status_code == 201
    assert _commit(client, slow[0], slow[1], 4).status_code == 201


# ── the helper's own contract ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_cohort_current_round_aggregates_children(client, cohort):
    """The shell's own round is NOT the cohort's round — the defect in one line."""
    import database as db
    from admin_router import _cohort_current_round

    a = _join(client, cohort)
    _play(client, a, 3)

    assert await db.fetch_latest_round(cohort) == 1, \
        "precondition: the cohort SHELL still reads round 1"
    assert await _cohort_current_round(cohort) == 4, \
        "the helper must aggregate the player sub-sessions"


@pytest.mark.anyio
async def test_cohort_current_round_floors_at_one(client, cohort):
    """An empty roster (or an unknown id) must never produce 0 or None —
    a ceiling of 0 would lock round 1 and freeze a cohort before it starts."""
    from admin_router import _cohort_current_round
    assert await _cohort_current_round(cohort) == 1
    assert await _cohort_current_round("no-such-session") == 1


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ── tripwire on the shape that caused it ───────────────────────────────────

def test_set_pacing_never_reads_the_cohort_shells_own_round():
    """`fetch_latest_round(session_id)` inside the pacing handler is the bug.

    It answers with the SHELL's round (always 1), which is exactly what made
    the clamp lock a live class. The cohort's round must come from the helper
    that aggregates children.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    # The clamp lives in `_apply_pacing` (audit 2026-09-04 F-18: shared by
    # POST /sessions/{id}/pacing and the cohort wizard's PUT); `set_pacing`
    # must delegate to it rather than grow its own copy.
    i = src.index("async def _apply_pacing(session_id")
    j = src.index("async def set_pacing")
    block = src[i:j]
    # strip comments so the explanation above the fix cannot satisfy the pin
    code = "\n".join(l for l in block.split("\n") if not l.lstrip().startswith("#"))
    assert "fetch_latest_round(session_id)" not in code, \
        "the pacing handler is reading the cohort shell's round again — it is always 1"
    assert "_cohort_current_round(session_id)" in code
    handler = src[j:j + 1500]
    assert "await _apply_pacing(session_id, body)" in handler
    assert "fetch_latest_round(" not in handler
