"""Virtual-account usernames (god_mode / facilitator / project_admin).

The three break-glass accounts are virtual — env-password logins with no
facilitator-registry row. The first-login "choose a callsign" flow previously
404'd for them ("Facilitator not found": set-username only knew the registry)
and, because login rebuilds the virtual account dict from scratch, the screen
re-appeared on every login. Pins:

  1. project_admin (and god_mode) can save a username via /set-username.
  2. The saved username is hydrated into subsequent login AND refresh
     responses, so the first-login flow doesn't re-trigger.
  3. Uniqueness is global: a registry facilitator can't take a virtual
     account's username, nor the reverse.
  4. Registry facilitators are unchanged; unknown non-virtual ids still 404.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from admin_shared import _virtual_account_profiles, _persist_virtual_profiles
from main import app

client = TestClient(app)

_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}
_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _set_username(user_id, username, cookies=None):
    # F-24 (launch audit 2026-09-01): /set-username now requires the caller to be
    # signed in — a facilitator may rename itself, admins/god_mode anyone.
    if cookies is None:
        cookies = client.post("/api/admin/facilitators/login", json=_GOD).cookies
    return client.post("/api/simulations/set-username",
                       json={"user_id": user_id, "role": "facilitator", "username": username},
                       cookies=cookies)


def _clear_virtual(*ids):
    for vid in ids:
        _virtual_account_profiles.pop(vid, None)
    _persist_virtual_profiles()


def test_project_admin_can_set_and_keep_username():
    _clear_virtual("project_admin")
    try:
        login = client.post("/api/admin/facilitators/login", json=_PA)
        assert login.status_code == 200, login.text
        assert login.json()["username"] == ""  # first login: no callsign yet

        r = _set_username("project_admin", "Admin", cookies=login.cookies)
        assert r.status_code == 200, r.text
        assert r.json()["username"] == "Admin"

        # Re-login: the callsign survives (previously rebuilt empty each time).
        login2 = client.post("/api/admin/facilitators/login", json=_PA)
        assert login2.status_code == 200
        assert login2.json()["username"] == "Admin"

        # And the refresh path carries it too.
        refreshed = client.post("/api/admin/auth/refresh", cookies=login2.cookies)
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()["username"] == "Admin"
    finally:
        _clear_virtual("project_admin")


def test_god_mode_username_roundtrips_through_login():
    _clear_virtual("god_mode")
    try:
        r = _set_username("god_mode", "Overseer")
        assert r.status_code == 200, r.text
        login = client.post("/api/admin/facilitators/login", json=_GOD)
        assert login.status_code == 200
        assert login.json()["username"] == "Overseer"
    finally:
        _clear_virtual("god_mode")


def test_username_uniqueness_spans_registry_and_virtual_accounts():
    # Unique-per-run names: the registry persists to a real file, so a fixed
    # username from a previous run would collide with itself.
    import uuid
    from admin_shared import _facilitator_registry, _persist_facilitators
    tag = uuid.uuid4().hex[:8]
    virt_name = f"Callisto-{tag}"
    reg_name = f"RegistryFal-{tag}"
    _clear_virtual("project_admin")
    fid = None
    try:
        assert _set_username("project_admin", virt_name).status_code == 200

        # A registry facilitator cannot take the virtual account's name…
        gm = client.post("/api/admin/facilitators/login", json=_GOD)
        created = client.post("/api/admin/facilitators",
                              json={"name": "VU Probe", "role": "facilitator"},
                              cookies=gm.cookies)
        assert created.status_code in (200, 201), created.text
        fid = created.json()["facilitator_id"]
        clash = _set_username(fid, virt_name.lower())  # case-insensitive
        assert clash.status_code == 400
        assert "taken" in clash.json()["detail"].lower()

        # …and the registry facilitator's own name works, then blocks project_admin.
        assert _set_username(fid, reg_name).status_code == 200
        clash2 = _set_username("project_admin", reg_name.lower())
        assert clash2.status_code == 400
    finally:
        _clear_virtual("project_admin")
        if fid:  # drop the probe account's username so nothing persists
            probe = next((f for f in _facilitator_registry if f["facilitator_id"] == fid), None)
            if probe is not None:
                probe.pop("username", None)
                _persist_facilitators()


def test_unknown_non_virtual_facilitator_still_404s():
    r = _set_username("FAC-DOES-NOT-EXIST", "Ghost")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_set_username_requires_facilitator_auth_and_self_scope():
    """F-24: anonymous callers are refused; a plain facilitator may rename only
    itself (the endpoint used to be fully unauthenticated — anyone could rename
    any account and probe which ids exist)."""
    anon = client.post("/api/simulations/set-username",
                       json={"user_id": "god_mode", "role": "facilitator", "username": "Pwned"})
    assert anon.status_code == 401
    gm = client.post("/api/admin/facilitators/login", json=_GOD).cookies
    created = client.post("/api/admin/facilitators", json={"name": "F24 Probe", "role": "facilitator"}, cookies=gm)
    assert created.status_code in (200, 201), created.text
    fid, otp = created.json()["facilitator_id"], created.json()["one_time_password"]
    from tests.conftest import rotate_facilitator_password
    pw = rotate_facilitator_password(client, fid, otp)
    fac_ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies
    other = client.post("/api/simulations/set-username",
                        json={"user_id": "god_mode", "role": "facilitator", "username": "Pwned"}, cookies=fac_ck)
    assert other.status_code == 403, other.text
    own = client.post("/api/simulations/set-username",
                      json={"user_id": fid, "role": "facilitator", "username": f"Own-{fid}"}, cookies=fac_ck)
    assert own.status_code == 200, own.text
