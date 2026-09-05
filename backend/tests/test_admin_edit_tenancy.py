"""Tenancy and persistence of admin edits — audit 2026-09-04 ACC-4, ACC-6, OPS-2, OPS-5, OPS-6 · WP-26.

ACC-4  players/{id}/reset-password had no cohort-ownership check: any
       facilitator could reset (and learn) another cohort's player credential.
ACC-6  Pillar-override edits were written into backend/db/ — inside the image
       (lost on redeploy) and inside the working tree on a dev box — and any
       facilitator could edit the platform-global config.
OPS-2  Cohort-wide undo iterated a set that included the shell (round 1
       forever): 400 before or after the children, and the UI button was
       permanently disabled off the shell's round.
OPS-5  A stakeholder-map resubmission re-applied the penalty/bonus.
OPS-6  A player password reset/change left the old device's token valid.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

from main import app  # noqa: E402
from conftest import rotate_facilitator_password  # noqa: E402
from router import _commit_timestamps  # noqa: E402

client = TestClient(app)
GOD = {"facilitator_id": "god_mode", "password": os.environ.get("MASTER_PASSWORD", "sim2026@iim")}


def _god():
    client.cookies.clear()
    r = client.post("/api/admin/facilitators/login", json=GOD)
    assert r.status_code == 200, r.text
    return r.cookies


def _facilitator(gm, name, role="facilitator"):
    r = client.post("/api/admin/facilitators", json={"name": name, "role": role}, cookies=gm)
    assert r.status_code in (200, 201), r.text
    fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
    pw = rotate_facilitator_password(client, fid, otp)
    client.cookies.clear()
    ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies
    return fid, ck


def _cohort(ck, fid, name):
    r = client.post("/api/simulations/start", json={"cohort_name": name, "facilitator_id": fid}, cookies=ck)
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def _team(ck, cohort, name="Team", personal=False):
    g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": name}, cookies=ck)
    assert g.status_code in (200, 201), g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    client.cookies.clear()
    if personal:   # F-01: a driver must hold a personal password before playing
        r = client.post("/api/simulations/change-password",
                        json={"player_id": pid, "old_password": pw, "new_password": f"{name}#2026pw"})
        assert r.status_code == 200, r.text
        pw = f"{name}#2026pw"
    lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": pw})
    assert lr.status_code == 200, lr.text
    return pid, pw, lr.json()["session_id"], lr.json()["player_token"]


def _hdr(pid, tok):
    return {"Authorization": f"Bearer {tok}", "X-Player-Id": pid}


def _commit(sid, pid, tok, rnd):
    dash = client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, tok)).json()
    _commit_timestamps.pop(sid, None)
    r = client.post(f"/api/simulations/{sid}/commit-turn", headers=_hdr(pid, tok), json={
        "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "investment_ratio": 0.2,
                       "choice_selected": "option_b"} for b in dash["business_units"]],
        "force_override_cfo": True, "expected_round": rnd})
    assert r.status_code == 201, (rnd, r.text[:200])
    return r.json()


# ── ACC-4 ───────────────────────────────────────────────────────────────────

def test_reset_password_is_refused_across_cohorts_and_allowed_within():
    gm = _god()
    fx, ckx = _facilitator(gm, "Owner X")
    fy, cky = _facilitator(gm, "Owner Y")
    cohort_x = _cohort(ckx, fx, "ACC4-X")
    _cohort(cky, fy, "ACC4-Y")
    pid, pw, _sid, _tok = _team(ckx, cohort_x, "Bravo")
    # facilitator Y (owns a different cohort) may not reset X's player
    client.cookies.clear()
    r = client.post(f"/api/admin/players/{pid}/reset-password", cookies=cky)
    assert r.status_code == 403, r.text[:200]
    # the player's live password still works
    client.cookies.clear()
    assert client.post("/api/simulations/player-login", json={"player_id": pid, "password": pw}).status_code == 200
    # the owner may
    client.cookies.clear()
    r = client.post(f"/api/admin/players/{pid}/reset-password", cookies=ckx)
    assert r.status_code == 200, r.text[:200]
    assert r.json()["new_password"]
    # and so may an admin
    client.cookies.clear()
    r = client.post(f"/api/admin/players/{pid}/reset-password", cookies=gm)
    assert r.status_code == 200


# ── OPS-6 ───────────────────────────────────────────────────────────────────

def test_a_reset_signs_the_old_device_out():
    gm = _god()
    fx, ckx = _facilitator(gm, "Owner Z")
    cohort = _cohort(ckx, fx, "OPS6")
    pid, pw, sid, old_tok = _team(ckx, cohort, "Charlie")
    assert client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, old_tok)).status_code == 200
    client.cookies.clear()
    assert client.post(f"/api/admin/players/{pid}/reset-password", cookies=ckx).status_code == 200
    # the token minted before the reset is refused with the re-login code
    client.cookies.clear()
    r = client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, old_tok))
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "player_token_required"


def test_a_self_service_change_keeps_the_same_token_working():
    """F-01's contract stands: the forced first change does not sign the
    driver's own device out — only a facilitator RESET bumps the version."""
    gm = _god()
    fx, ckx = _facilitator(gm, "Owner W")
    cohort = _cohort(ckx, fx, "OPS6b")
    pid, pw, sid, tok = _team(ckx, cohort, "Delta")
    client.cookies.clear()
    r = client.post("/api/simulations/change-password",
                    json={"player_id": pid, "old_password": pw, "new_password": "Delta#2026pw"})
    assert r.status_code == 200, r.text[:200]
    assert client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, tok)).status_code == 200
    # a fresh login after the reset carries the bumped version and works
    client.cookies.clear()
    assert client.post(f"/api/admin/players/{pid}/reset-password", cookies=ckx).status_code == 200
    client.cookies.clear()
    assert client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, tok)).status_code == 401
    newpw = client.post(f"/api/admin/players/{pid}/reset-password", cookies=ckx).json()["new_password"]
    client.cookies.clear()
    lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": newpw})
    assert lr.status_code == 200
    assert client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, lr.json()["player_token"])).status_code == 200


# ── OPS-5 ───────────────────────────────────────────────────────────────────

def test_stakeholder_map_resubmission_replaces_the_outcome_and_a_third_is_locked():
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    client.cookies.clear()
    r = client.post("/api/simulations/solo-start", json={"player_name": "Mapper", "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]
    ids = [s["id"] for s in client.get("/api/simulations/stakeholder-map/stakeholders").json()["stakeholders"]]
    wrong = {i: "low_low" for i in ids}
    t0 = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]["corporate_treasury"]
    r1 = client.post(f"/api/simulations/{sid}/stakeholder-map", json={"mapping": wrong}).json()
    g1 = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    assert r1["treasury_penalty"] < 0
    assert g1["corporate_treasury"] == pytest.approx(t0 + r1["treasury_penalty"], abs=0.01)
    # the one re-attempt the modal offers: the penalty is not charged twice
    r2 = client.post(f"/api/simulations/{sid}/stakeholder-map", json={"mapping": wrong}).json()
    g2 = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    assert g2["corporate_treasury"] == pytest.approx(t0 + r2["treasury_penalty"], abs=0.01)
    assert g2["bonus_score"] == r2["points_awarded"]
    # a third submission is refused and changes nothing
    r3 = client.post(f"/api/simulations/{sid}/stakeholder-map", json={"mapping": wrong})
    assert r3.status_code == 409
    assert r3.json()["detail"]["code"] == "stakeholder_map_locked"
    g3 = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    assert g3["corporate_treasury"] == pytest.approx(g2["corporate_treasury"], abs=0.01)


# ── OPS-2 ───────────────────────────────────────────────────────────────────

def test_cohort_wide_undo_rolls_every_team_back_and_reports_it():
    gm = _god()
    fx, ckx = _facilitator(gm, "Owner U", role="lead_facilitator")
    cohort = _cohort(ckx, fx, "OPS2")
    client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"}, cookies=ckx)
    for _ in range(4):
        client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", cookies=ckx)
    a = _team(ckx, cohort, "Alpha", personal=True)
    b = _team(ckx, cohort, "Beta", personal=True)
    for rnd in (1, 2, 3):
        _commit(a[2], a[0], a[3], rnd)
    for rnd in (1, 2):
        _commit(b[2], b[0], b[3], rnd)
    # A is on round 4, B on round 3; the shell sits at round 1
    client.cookies.clear()
    r = client.post(f"/api/admin/{cohort}/undo-round?cohort_wide=true&target_round=2", cookies=ckx)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body["cohort_wide"] is True
    assert body["teams_rolled_back"] == {a[2]: 2, b[2]: 2}
    assert body["new_current_round"] == 2
    for sid, pid, tok in ((a[2], a[0], a[3]), (b[2], b[0], b[3])):
        assert client.get(f"/api/simulations/{sid}/dashboard", headers=_hdr(pid, tok)).json()["current_round"] == 2
    # a second rollback to the same round: nothing to do, said so, not a shell error
    client.cookies.clear()
    r = client.post(f"/api/admin/{cohort}/undo-round?cohort_wide=true&target_round=2", cookies=ckx)
    assert r.status_code == 400
    assert "already at" in r.json()["detail"]


# ── ACC-6 ───────────────────────────────────────────────────────────────────

def test_pillar_override_edits_go_to_the_data_dir_and_need_super_admin(tmp_path, monkeypatch):
    import pillar_configs, runtime_paths
    monkeypatch.setattr(runtime_paths, "data_dir", lambda: tmp_path)
    repo_copy = pillar_configs._OVERRIDES_DB_DIR / "pillar_overrides_pharma.json"
    before = repo_copy.read_bytes() if repo_copy.exists() else None
    # first read seeds the volume copy from the image copy
    data = pillar_configs._load_pillar_overrides("pharma")
    assert (tmp_path / "pillar_overrides_pharma.json").exists()
    data.setdefault("custom_areas", []).append({"key": "wp26_probe", "label": "WP-26 probe"})
    pillar_configs._save_pillar_overrides("pharma", data)
    # the edit landed on the volume, not in the image / working tree
    assert "wp26_probe" in (tmp_path / "pillar_overrides_pharma.json").read_text(encoding="utf-8")
    assert (repo_copy.read_bytes() if repo_copy.exists() else None) == before
    # writes are super-admin only; reads stay open to facilitators
    gm = _god()
    fx, ckx = _facilitator(gm, "Owner P", role="lead_facilitator")
    client.cookies.clear()
    assert client.get("/api/admin/pillar-config/pharma", cookies=ckx).status_code == 200
    r = client.put("/api/admin/pillar-config/pharma/order", json={"order": []}, cookies=ckx)
    assert r.status_code == 403, r.text[:200]
