"""Player login must survive a registry miss — in BOTH storage modes.

THE DEFECT (reported: "unable to login", 500 on the player login screen)
------------------------------------------------------------------------
player_login's registry-miss fallback — the comment on it literally says
"survives server restart" — reads `db._sessions`:

    import database as db
    for sid, sess in db._sessions.items():   # AttributeError under Postgres

In memory mode `database` is aliased to database_memory, which has
`_sessions`, so every local test passed. Under Postgres, database.py had no
module-level `_sessions` (it maintains database_memory._sessions internally
as its sync cache but never exposed it) → AttributeError → 500 for exactly
the situation the fallback was written for: a player generated before the
last redeploy whose record was not in the in-process registry.

The fix re-exports the SAME dict from database.py, so `db._sessions` reads
one truth in both modes. The identity assert below is the tripwire: if the
re-export ever becomes a copy (or is removed), it fails before production
does. Same memory/Postgres parity gap as get_effective_settings and the
God-Mode counters before it — third strike for this shape.

Also pinned: a malformed registry row (missing player_id) must not take
login down for everyone — `p["player_id"]` subscripts became .get(), the
same crash class as the facilitator null-identity outage.
"""
import pytest


def test_db_sessions_is_the_same_dict_in_both_backends():
    """THE tripwire. database._sessions must BE database_memory._sessions —
    not equal, identical — because database.py's writers update the
    database_memory dict and readers go through `db._sessions`.

    Loaded from FILE, not `import database`: in memory mode main.py aliases
    sys.modules["database"] to database_memory, which made the naive form of
    this assert pass with the fix REMOVED (caught by mutation-testing it).
    The Postgres process imports the real file, so the real file is what
    must carry the attribute."""
    import importlib.util
    import pathlib
    import database_memory

    path = pathlib.Path(__file__).resolve().parents[1] / "database.py"
    spec = importlib.util.spec_from_file_location("_real_database_py", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "_sessions"), (
        "database.py lost its _sessions re-export — player-login's registry-miss "
        "fallback 500s under Postgres again")
    assert mod._sessions is database_memory._sessions


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
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def _mk_player(client):
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "PLP", "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    return sid, g


def _login(client, pid, pw):
    _clear()
    return client.post("/api/simulations/player-login",
                       json={"player_id": pid, "password": pw})


def test_login_works_when_the_registry_has_the_player(client):
    _sid, g = _mk_player(client)
    assert _login(client, g["player_id"], g["password"]).status_code == 200


def test_login_survives_a_registry_miss_via_the_session_scan(client):
    """The exact restart scenario: the in-process registry has lost the
    player, but the session store still knows them. Before the fix this path
    500'd under Postgres; it must 2xx/4xx — never 5xx — in every mode."""
    from admin_shared import _player_registry
    _sid, g = _mk_player(client)
    saved = list(_player_registry)
    try:
        _player_registry.clear()   # simulate the post-redeploy cold registry
        r = _login(client, g["player_id"], g["password"])
        assert r.status_code < 500, f"fallback path crashed: {r.status_code} {r.text[:120]}"
        assert r.status_code == 200, f"player known to the session store was refused: {r.text[:120]}"
    finally:
        _player_registry.clear()
        _player_registry.extend(saved)


def test_a_malformed_registry_row_does_not_break_everyone(client):
    """One row without player_id used to KeyError the scan — the same class
    as the facilitator null-identity outage (one bad row, all logins down)."""
    from admin_shared import _player_registry
    _sid, g = _mk_player(client)
    _player_registry.insert(0, {"name": "row with no id"})
    try:
        r = _login(client, g["player_id"], g["password"])
        assert r.status_code == 200, f"{r.status_code} {r.text[:120]}"
    finally:
        _player_registry[:] = [p for p in _player_registry if p.get("player_id")]


def test_unknown_player_still_gets_a_clean_403(client):
    r = _login(client, "MUR-NOPE", "x")
    assert r.status_code == 403
    assert "not found" in r.json()["detail"].lower()
