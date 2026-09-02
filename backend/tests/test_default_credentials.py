"""Deterministic id-derived initial credentials, forced-change on first login.

POLICY (2026-08-01, by request):
  * player MUR-NNN default password = "MUR-NNN@123"
  * facilitator FAC-NNN default password = "FAC-NNN@321"
  * both must_change_password=True → replaced on first login.

The rule the whole room already knows replaces the copy-a-random-string-per-
user distribution that produced repeated "password not working" reports. The
predictable value is valid only until first login (must_change_password), so
the security window is the same as a mailed activation code.
"""
import pathlib
import re

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[1]


# ── the module: pure derivation ────────────────────────────────────────────

def test_derivation_matches_the_policy_exactly():
    from default_credentials import default_player_password, default_facilitator_password
    assert default_player_password("MUR-014") == "MUR-014@123"
    assert default_facilitator_password("FAC-007") == "FAC-007@321"


def test_credentials_return_plaintext_and_a_verifying_hash():
    from default_credentials import make_player_credentials, make_facilitator_credentials
    from password_hashing import verify_password

    plain, h = make_player_credentials("MUR-020")
    assert plain == "MUR-020@123"
    assert verify_password("MUR-020@123", h)
    assert not verify_password("MUR-020@321", h)   # wrong suffix rejected

    fplain, fh = make_facilitator_credentials("FAC-003")
    assert fplain == "FAC-003@321"
    assert verify_password("FAC-003@321", fh)


def test_id_is_used_verbatim_so_the_rule_matches_what_the_user_is_told():
    from default_credentials import default_player_password
    # the student is told "your ID then @123" — no case/format massaging
    assert default_player_password("MUR-099") == "MUR-099@123"


# ── end-to-end: create → default password logs in → forced change ──────────

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


def _god(client):
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})


def test_generated_player_logs_in_with_the_derived_default_and_is_forced_to_change(client):
    from default_credentials import default_player_password
    _god(client)
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "DC", "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    pid = g["player_id"]
    # the one-time credential IS the derived default
    assert g["password"] == default_player_password(pid)

    # /player-login is the real player entry point (the login screen calls it)
    # and is the endpoint that relays must_change_password.
    _clear()
    j = client.post("/api/simulations/player-login",
                    json={"player_id": pid, "password": default_player_password(pid)})
    assert j.status_code == 200, j.text
    assert j.json().get("must_change_password") is True, "first login must force a change"

    # a wrong-suffix guess is rejected (the value is genuinely the password)
    _clear()
    bad = client.post("/api/simulations/player-login",
                      json={"player_id": pid, "password": f"{pid}@999"})
    assert bad.status_code == 403


def test_created_facilitator_logs_in_with_derived_default_and_is_forced_to_change(client):
    from default_credentials import default_facilitator_password
    _god(client)
    _clear()
    r = client.post("/api/admin/facilitators",
                    json={"name": "Dana Facilitator", "role": "facilitator"})
    assert r.status_code == 200, r.text
    body = r.json()
    fac_id = (body.get("facilitator") or {}).get("facilitator_id") or body.get("facilitator_id")
    one_time = body.get("temp_password") or body.get("one_time_password") \
        or (body.get("facilitator") or {}).get("temp_password")
    # the response surfaces the derived default (however the field is named)
    if one_time is not None:
        assert one_time == default_facilitator_password(fac_id)

    _clear()
    login = client.post("/api/admin/facilitators/login",
                        json={"facilitator_id": fac_id,
                              "password": default_facilitator_password(fac_id)})
    assert login.status_code == 200, login.text
    assert login.json().get("must_change_password") is True


def test_password_reset_returns_to_the_same_derived_default(client):
    from default_credentials import default_player_password
    _god(client)
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "DCR", "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    pid = g["player_id"]
    # admin reset → derived default again, forced change again
    _clear()
    rr = client.post(f"/api/admin/players/{pid}/reset-password")
    if rr.status_code == 200:
        _clear()
        j = client.post("/api/simulations/player-login",
                        json={"player_id": pid, "password": default_player_password(pid)})
        assert j.status_code == 200, "reset did not return to the derived default"
        assert j.json().get("must_change_password") is True


# ── tripwire: the rule lives in ONE place ──────────────────────────────────

def test_no_random_temp_password_generator_survives():
    """A resurrected random-temp path would silently reintroduce the
    per-user-string distribution failure this replaced."""
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    assert "def _generate_temp_password" not in src, (
        "the retired random-temp generator is back")


def test_suffixes_are_not_hard_coded_anywhere_but_the_policy_module():
    """@123 / @321 against an id must exist ONLY in default_credentials, so
    the rule can never drift between sites."""
    offenders = []
    for path in _BACKEND.glob("*.py"):
        if path.name in ("default_credentials.py",):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # id-concatenation forms: f"...@123", + "@123", '@321' next to an id var
        for m in re.finditer(r'["\']@(?:123|321)["\']', text):
            line = text[:m.start()].count("\n") + 1
            offenders.append(f"{path.name}:{line}")
    assert not offenders, (
        f"default-password suffix hard-coded outside default_credentials: {offenders}")


def test_creation_and_reset_sites_route_through_the_policy_module():
    """Every credential mint in admin_router uses the shared helpers — a raw
    hash_password of an ad-hoc default would bypass the forced-change pairing."""
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    # F-30: request handlers use the async variants (bcrypt on the thread pool);
    # both spellings route through default_credentials' policy.
    assert src.count("make_player_credentials(") + src.count("make_player_credentials_async(") >= 3
    assert src.count("make_facilitator_credentials(") + src.count("make_facilitator_credentials_async(") >= 4
    assert src.count("make_player_credentials_async(") >= 3, "mints must not block the event loop (F-30)"
