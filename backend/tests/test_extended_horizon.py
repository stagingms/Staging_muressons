"""Extended Horizon Mode (rounds 11-20) is RETIRED — F-32, launch audit 2026-09-01.

The feature was dead end-to-end: POST /extend inserted round 11 and cleared
game_over, but the commit path refuses current_round > 10, the Postgres schema
has CHECK (round_number BETWEEN 1 AND 10) and the cockpit treats round > 10 as
game over. Owner ruling 2026-09-02: remove it. These tests pin the retirement —
the route answers 410 for everyone and never touches session state.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="exthorizon_")
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


@pytest.fixture()
def solo(client):
    from admin_shared import _god_mode_settings
    _god_mode_settings["solo_mode_enabled"] = True
    r = client.post("/api/simulations/solo-start", json={"player_name": "EH"})
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def test_extend_is_gone_and_mutates_nothing(client, solo):
    before = client.get(f"/api/simulations/{solo}/dashboard").json()
    r = client.post(f"/api/simulations/{solo}/extend")
    assert r.status_code == 410, r.text
    assert r.json()["detail"]["code"] == "extended_horizon_removed"
    after = client.get(f"/api/simulations/{solo}/dashboard").json()
    assert after["current_round"] == before["current_round"] == 1
    assert not after["global_state"].get("extended_horizon_mode")


def test_extended_round_content_is_gone():
    import branching_engine
    assert not hasattr(branching_engine, "EXTENDED_ROUNDS")
    assert not hasattr(branching_engine, "get_extended_round_config")
