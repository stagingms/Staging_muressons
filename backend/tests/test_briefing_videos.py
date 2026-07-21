"""Briefing videos — the Read | Watch link on round briefings.

The frontend (RoundBriefing / page.js / AnalyticsControlPanel / cohort modal)
was built against a backend contract that never existed server-side, so every
configured video URL was silently dropped and the briefing link went missing.
Pins the contract:

  1. POST /api/admin/sessions/{sid}/briefing-videos stores the cohort's URL
     pattern + per-round map through settings normalisation.
  2. GET /api/admin/global-settings?session_id=… returns them cohort-effective
     (the exact read the player page performs on mount).
  3. URLs are sanitised: http(s) only — javascript:/data: never reach the
     player's embed iframe; map keys clamp to rounds 1–10.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from admin_shared import cohort_settings, normalize_advanced_cohort_settings as normalize
from main import app

client = TestClient(app)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _god_cookies():
    r = client.post("/api/admin/facilitators/login", json=_GOD)
    assert r.status_code == 200, r.text
    return r.cookies


def test_save_and_read_back_cohort_effective():
    gm = _god_cookies()
    sid = "cohort-briefvid"
    try:
        r = client.post(f"/api/admin/sessions/{sid}/briefing-videos",
                        json={"briefing_video_base": "https://cdn.x.edu/briefing-{round}.mp4",
                              "briefing_videos": {"2": "https://youtu.be/abc123"}},
                        cookies=gm)
        assert r.status_code == 200, r.text
        assert r.json()["briefing_video_base"] == "https://cdn.x.edu/briefing-{round}.mp4"
        assert r.json()["briefing_videos"] == {"2": "https://youtu.be/abc123"}

        # The exact read the player page performs on mount.
        g = client.get(f"/api/admin/global-settings?session_id={sid}").json()
        assert g["briefing_video_base"] == "https://cdn.x.edu/briefing-{round}.mp4"
        assert g["briefing_videos"]["2"] == "https://youtu.be/abc123"

        # Another cohort is unaffected (per-cohort layer, not global).
        g2 = client.get("/api/admin/global-settings?session_id=cohort-other").json()
        assert g2["briefing_video_base"] == ""
        assert g2["briefing_videos"] == {}
    finally:
        cohort_settings.pop(sid, None)


def test_urls_are_sanitised():
    assert normalize({"briefing_video_base": "javascript:alert(1)"})["briefing_video_base"] == ""
    assert normalize({"briefing_video_base": "  https://ok.edu/v-{round}.mp4 "})["briefing_video_base"] == "https://ok.edu/v-{round}.mp4"
    out = normalize({"briefing_videos": {
        "1": "https://youtu.be/ok",
        "11": "https://youtu.be/out-of-range",
        "x": "https://youtu.be/bad-key",
        "3": "data:text/html,evil",
    }})["briefing_videos"]
    assert out == {"1": "https://youtu.be/ok"}


def test_empty_payload_is_rejected_and_partial_accepted():
    gm = _god_cookies()
    sid = "cohort-briefvid-partial"
    try:
        assert client.post(f"/api/admin/sessions/{sid}/briefing-videos",
                           json={}, cookies=gm).status_code == 422
        r = client.post(f"/api/admin/sessions/{sid}/briefing-videos",
                        json={"briefing_video_base": "https://cdn.x.edu/b-{round}.mp4"},
                        cookies=gm)
        assert r.status_code == 200, r.text
        assert r.json()["briefing_videos"] == {}
    finally:
        cohort_settings.pop(sid, None)
