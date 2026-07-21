"""
QA-2026-07-16 regression tests for review fixes #1–#3.

#1 — No committed break-glass defaults: config.py must not contain the burned
     literals, and an empty MASTER_PASSWORD must disable the bypass.
#2 — The three formerly-unguarded POSTs (peer-evaluations, brsr/decide,
     mod4-crisis-choices) reject anonymous callers.
#3 — runtime_paths honours MURESSONS_DATA_DIR and migrates legacy copies.
"""

import asyncio
import importlib
import json
import pathlib

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_GOD_MODE_CREDS = {"facilitator_id": "god_mode", "password": "sim2026@iim"}  # test-only (conftest env)


def _facilitator_cookies():
    resp = client.post("/api/admin/facilitators/login", json=_GOD_MODE_CREDS)
    assert resp.status_code == 200, f"god_mode login failed: {resp.text}"
    return resp.cookies


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _new_player_session(cohort_name: str):
    import database as db
    cohort = client.post(
        "/api/simulations/start", json={"cohort_name": cohort_name},
        cookies=_facilitator_cookies(),
    ).json()["session_id"]
    pid = _run(db.generate_player_id(cohort))
    sub = client.post(
        f"/api/simulations/public/sessions/{cohort}/join",
        json={"player_id": pid, "password": "", "player_name": "Owner"},
    ).json()["session_id"]
    return cohort, pid, sub


# ── Fix #1: no committed break-glass defaults ────────────────────────────────

def test_config_source_has_no_burned_default_passwords():
    """Tripwire: the burned literals must never reappear in config.py."""
    src = (pathlib.Path(__file__).resolve().parent.parent / "config.py").read_text(encoding="utf-8")
    assert "sim2026@iim" not in src
    assert "simadmin2026@" not in src


def test_empty_master_password_disables_bypass(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "")
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None)
    assert master_credentials.verify_master_password("") is False
    assert master_credentials.verify_master_password("anything") is False


# ── Fix #2: formerly-unguarded POSTs reject anonymous callers ────────────────

def test_peer_evaluation_post_requires_facilitator():
    client.cookies.clear()
    r = client.post(
        "/api/admin/some-session/peer-evaluations",
        json={"evaluator_name": "Mallory", "target_name": "Alice",
              "contribution": 5, "communication": 5, "leadership": 5, "comment": ""},
    )
    assert r.status_code in (401, 403), r.text


def test_brsr_decide_requires_facilitator():
    client.cookies.clear()
    r = client.post(
        "/api/admin/some-session/brsr/decide",
        json={"brsr_round": 1, "choice": "option_a", "god_mode_override": True},
    )
    assert r.status_code in (401, 403), r.text


def test_mod4_crisis_choices_bound_to_session_owner():
    """Owned session: wrong X-Player-Id and anonymous callers are rejected;
    the real owner passes the ownership gate."""
    cohort, pid, sub = _new_player_session("QA716-Mod4")
    client.cookies.clear()

    body = {"choices": {"bu_legacy": "eat"}, "effective_fee": 95}

    r_wrong = client.post(f"/api/admin/sessions/{sub}/mod4-crisis-choices",
                          json=body, headers={"X-Player-Id": "MUR-EVIL"})
    assert r_wrong.status_code == 403

    r_anon = client.post(f"/api/admin/sessions/{sub}/mod4-crisis-choices", json=body)
    assert r_anon.status_code == 403

    # Real owner clears the OWNERSHIP gate (later validation may still reject
    # the payload, but never with the ownership message).
    r_owner = client.post(f"/api/admin/sessions/{sub}/mod4-crisis-choices",
                          json=body, headers={"X-Player-Id": pid})
    if r_owner.status_code == 403:
        assert "owner" not in r_owner.json().get("detail", "").lower()


def test_mod4_crisis_choices_solo_session_still_open():
    """Solo sessions have no owner — the UUID stays the bearer (unchanged)."""
    sub = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "QA716-Solo", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    client.cookies.clear()
    r = client.post(f"/api/admin/sessions/{sub}/mod4-crisis-choices",
                    json={"choices": {"bu_legacy": "eat"}, "effective_fee": 95})
    # Must not be blocked by the ownership gate (any non-403 outcome is fine;
    # a 403 would mean solo play broke).
    assert r.status_code != 403, r.text


# ── Fix #3: durable data dir ─────────────────────────────────────────────────

def test_runtime_paths_honours_data_dir_and_migrates(tmp_path, monkeypatch):
    import runtime_paths

    # Default (unset) → repo db/
    monkeypatch.delenv("MURESSONS_DATA_DIR", raising=False)
    assert runtime_paths.data_dir() == runtime_paths._REPO_DB_DIR

    # Configured → the volume path, created on demand.
    vol = tmp_path / "vol"
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(vol))
    assert runtime_paths.data_dir() == vol
    assert vol.is_dir()

    # Migration: a legacy copy is carried across on first resolve.
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps({"marker": 1}), encoding="utf-8")
    target = runtime_paths.data_file("qa716_migrated.json", legacy=legacy)
    assert target == vol / "qa716_migrated.json"
    assert json.loads(target.read_text(encoding="utf-8")) == {"marker": 1}

    # Second resolve does not re-copy / overwrite.
    target.write_text(json.dumps({"marker": 2}), encoding="utf-8")
    again = runtime_paths.data_file("qa716_migrated.json", legacy=legacy)
    assert json.loads(again.read_text(encoding="utf-8")) == {"marker": 2}
