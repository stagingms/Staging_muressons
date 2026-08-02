"""Login must survive a null identity field in the facilitator registry.

THE DEFECT
----------
Production returned 500 on every login, with the correct password, for every
account — including the god_mode break-glass account. The traceback:

    admin_router.facilitator_login
      f.get("name", "").lower() == fac_id_lower
    AttributeError: 'NoneType' object has no attribute 'lower'

`dict.get(key, default)` returns the default only when the key is ABSENT. A key
present with value None returns None, and None.lower() raises. One registry row
with `"name": null` therefore took down authentication entirely.

Three things made it severe rather than annoying:

  1. The registry scan runs BEFORE the master-password branch, so god_mode —
     the documented recovery path for exactly this situation — crashed too.
     There was no way back in through the product.
  2. The poisoned value was persisted to the durable volume, so it survived
     restarts and redeploys. Recovery meant hand-editing JSON on a mounted
     volume.
  3. update_facilitator wrote it: a blind `fac[key] = value` over
     model_dump(exclude_unset=True), so a client PATCHing its whole form with
     an empty name field wrote null straight through.

Hence three layers, each pinned below: the read must not crash, the write must
not create nulls, and an already-poisoned file must heal itself on load.
"""
import json
import pathlib

import pytest


@pytest.fixture
def registry(monkeypatch, tmp_path):
    """Isolate the registry. Never touch the developer's real one — an earlier
    conftest bug deleted a live snapshot by operating on real paths."""
    # MASTER_PASSWORD is captured into a module constant at import, so setenv
    # is too late — patch the resolved value and any override hash.
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    import admin_shared

    monkeypatch.setattr(admin_shared, "_FAC_REGISTRY_PATH",
                        str(tmp_path / "facilitator_registry.json"), raising=False)
    saved = list(admin_shared._facilitator_registry)
    admin_shared._facilitator_registry.clear()
    admin_shared._facilitator_registry.append({
        "facilitator_id": "FAC-001", "name": "Ada", "username": "ada",
        "password": "x", "role": "facilitator", "enabled": True,
    })
    yield admin_shared._facilitator_registry
    admin_shared._facilitator_registry.clear()
    admin_shared._facilitator_registry.extend(saved)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    # raise_server_exceptions=False so a 500 is asserted as a STATUS CODE
    # rather than blowing up the test run — the defect must be observable
    # the way the browser observed it.
    return TestClient(app, raise_server_exceptions=False)


def _login(client, fac_id="god_mode", password="test-master-pw"):
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    return client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": fac_id, "password": password})


# ── Layer 1: the read must not crash ───────────────────────────────────────

@pytest.mark.parametrize("field", ["name", "username", "facilitator_id"])
def test_a_null_identity_field_does_not_500_the_login(registry, client, field):
    registry[0][field] = None
    assert _login(client).status_code != 500


def test_god_mode_still_gets_in_when_the_registry_is_poisoned(registry, client):
    """The whole point of break-glass: it must work when everything else is
    broken. This is what made the outage unrecoverable from the product."""
    registry[0]["name"] = None
    assert _login(client).status_code == 200


def test_every_identity_field_null_at_once(registry, client):
    registry[0].update(name=None, username=None, facilitator_id=None)
    assert _login(client).status_code == 200


def test_a_non_string_identity_field_does_not_crash_either(registry, client):
    """Coercion is by type, not by `is None` — a number from a spreadsheet
    import has no .lower() either."""
    registry[0]["name"] = 12345
    assert _login(client).status_code != 500


# ── the fix must not change behaviour for healthy rows ─────────────────────

def test_lookup_by_each_identity_field_still_works(registry, client):
    """403 (bad password) proves the row was FOUND. A 500 here would mean the
    None-guard silently stopped matching real accounts."""
    for handle in ("FAC-001", "ada", "Ada", "ADA"):
        assert _login(client, handle, "wrong-password").status_code == 403


def test_a_healthy_registry_logs_in_normally(registry, client):
    assert _login(client).status_code == 200


# ── Layer 2: the write must not create nulls ───────────────────────────────

def test_update_cannot_null_an_identity_field(registry, client):
    """An explicit null for name/username/id is ignored, not written."""
    import admin_router
    assert admin_router._IDENTITY_FIELDS == {"facilitator_id", "username", "name"}

    login = _login(client)
    assert login.status_code == 200
    r = client.put("/api/admin/facilitators/FAC-001",
                   json={"name": None, "programme": "MBA"},
                   cookies=login.cookies)
    if r.status_code == 200:
        assert registry[0]["name"] == "Ada", "null was written over a real name"
        assert registry[0]["programme"] == "MBA", "the rest of the update was dropped"
    # Whatever the authz outcome, the registry must remain loginable.
    assert _login(client).status_code == 200


# ── Layer 3: an already-poisoned file heals itself ─────────────────────────

def test_a_registry_file_containing_nulls_heals_on_load(registry, monkeypatch):
    """Blocking the write path does nothing for a volume that ALREADY holds a
    null — without this, recovery means hand-editing JSON on a mounted volume
    mid-class. One redeploy should be enough."""
    import admin_shared
    path = pathlib.Path(admin_shared._FAC_REGISTRY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        [{"facilitator_id": "FAC-009", "name": None, "username": None,
          "role": "facilitator"}]), encoding="utf-8")

    healed = admin_shared._load_facilitator_registry()
    assert healed[0]["name"] == ""
    assert healed[0]["username"] == ""
    # and the healed row is safe to scan
    assert all(isinstance(healed[0][k], str)
               for k in ("facilitator_id", "username", "name"))


# ── tripwire: the shape that caused it ─────────────────────────────────────

def test_no_login_path_calls_lower_on_a_raw_registry_get():
    """`.get("x", "").lower()` is the exact shape of the defect, and it reads as
    safe — which is why it survived review. Unit tests all passed; the row that
    triggered it simply never existed in a fixture. Ban the shape."""
    import re
    src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    offenders = re.findall(r'\.get\(\s*"(?:name|username|facilitator_id)"[^)]*\)\s*\.lower\(\)', src)
    assert not offenders, f"unguarded identity .lower() — use _lc(): {offenders}"

    bracket = re.findall(r'f\[\s*"(?:name|username|facilitator_id)"\s*\]\s*\.lower\(\)', src)
    assert not bracket, f"unguarded identity .lower() on subscript — use _lc(): {bracket}"
