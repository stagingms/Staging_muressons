"""Durable cohort-settings store (Railway volume, backend-independent).

Per-cohort settings — pacing, briefing-video URLs, analytics visibility,
templates — previously lived only in-process: memory mode happened to snapshot
them, Postgres mode never persisted them, so a redeploy reset every cohort.
They now write to a dedicated JSON file under MURESSONS_DATA_DIR (the mounted
volume) on every mutation, and rehydrate on boot. Pins:

  1. A settings mutation (via the API) writes the durable file, and a simulated
     restart (clear dicts → _load_cohort_state) restores it — INCLUDING
     briefing-video URLs.
  2. Templates round-trip through the same durable file.
  3. Persistence is independent of the db backend (the store writes its own
     file; it does not rely on database._persist, which Postgres lacks).
"""

import json
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import admin_shared
from admin_shared import cohort_settings, _cohort_templates, _load_cohort_state
from main import app

client = TestClient(app)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _god():
    r = client.post("/api/admin/facilitators/login", json=_GOD)
    assert r.status_code == 200, r.text
    return r.cookies


def _simulate_restart():
    """Drop the in-process state and rehydrate ONLY from the durable file —
    exactly what a fresh process does on boot."""
    cohort_settings.clear()
    _cohort_templates.clear()
    _load_cohort_state()


def test_cohort_settings_survive_restart_via_durable_file():
    gm = _god()
    sid = "cohort-durable-1"
    try:
        # Mutate through the real endpoint (PATCH → mark_cohort_settings_dirty).
        r = client.patch(f"/api/admin/sessions/{sid}/cohort-settings",
                         json={"results_reveal_round": 6, "team_count": 4}, cookies=gm)
        assert r.status_code == 200, r.text

        # The durable file physically exists on the "volume".
        path = admin_shared._cohort_state_path()
        assert os.path.exists(path), "durable cohort-settings file was not written"
        on_disk = json.load(open(path))
        assert on_disk["cohort_settings"][sid]["results_reveal_round"] == 6

        _simulate_restart()
        assert cohort_settings.get(sid, {}).get("results_reveal_round") == 6
        assert cohort_settings.get(sid, {}).get("team_count") == 4
    finally:
        cohort_settings.pop(sid, None)
        admin_shared.persist_cohort_state()


def test_briefing_videos_survive_restart():
    gm = _god()
    sid = "cohort-durable-video"
    try:
        r = client.post(f"/api/admin/sessions/{sid}/briefing-videos",
                        json={"briefing_video_base": "https://cdn.x.edu/b-{round}.mp4",
                              "briefing_videos": {"2": "https://youtu.be/keepme"}},
                        cookies=gm)
        assert r.status_code == 200, r.text

        _simulate_restart()

        # The player-facing read returns the persisted URLs after "restart".
        g = client.get(f"/api/admin/global-settings?session_id={sid}").json()
        assert g["briefing_video_base"] == "https://cdn.x.edu/b-{round}.mp4"
        assert g["briefing_videos"]["2"] == "https://youtu.be/keepme"
    finally:
        cohort_settings.pop(sid, None)
        admin_shared.persist_cohort_state()


def test_templates_survive_restart():
    gm = _god()
    src = "cohort-durable-tplsrc"
    cohort_settings[src] = {"team_count": 9, "quiz_enabled": True}
    admin_shared.persist_cohort_state()
    tid = None
    try:
        r = client.post("/api/admin/cohort-templates",
                        json={"name": "Durable Setup", "source_session_id": src}, cookies=gm)
        assert r.status_code == 200, r.text
        tid = r.json()["template_id"]

        _simulate_restart()
        assert tid in _cohort_templates
        assert _cohort_templates[tid]["settings"]["team_count"] == 9
    finally:
        cohort_settings.pop(src, None)
        if tid:
            _cohort_templates.pop(tid, None)
        admin_shared.persist_cohort_state()
