"""Per-cohort pedagogy toggles must reach the player (BUG-2026-07-20).

Reported: "Real-World Case Cards is enabled but not visible in the sim."

The card was fully built — content for all 10 rounds, a working unguarded
endpoint, a RealWorldCard component, and a `pedToggles.real_world_cards_enabled`
gate at the results stage. It could still never appear, because of TWO stacked
defects between the facilitator's switch and the player's screen:

  1. STORAGE SPLIT — PUT /cohort/{id}/pedagogical-settings writes to
     session["pedagogical_overrides"], a different store from cohort_settings,
     which is what get_effective_settings (and therefore GET /global-settings)
     reads. The cohort value was saved and then ignored.

  2. MISSING SCOPE — ExecutiveCockpit fetched /global-settings with NO
     session_id, so even a correct backend would have handed it platform
     defaults.

Both had to be wrong for the symptom; fixing either alone leaves it broken.
These tests cover the backend half (the frontend half is pinned by
__tests__/pedagogy-strip.test.js and the source itself).
"""
import os
import pathlib
import tempfile

import pytest

PEDAGOGY_KEYS = [
    "real_world_cards_enabled",
    "round_recap_enabled",
    "debrief_protocol_enabled",
    "strategy_memo_enabled",
    "confidence_calibration_enabled",
]


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="pedcohort_")
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


def _cohort(client, name):
    r = client.post("/api/simulations/start",
                    json={"cohort_name": name, "facilitator_id": "god_mode"})
    assert r.status_code in (200, 201), r.text
    return str(r.json()["session_id"])


def test_cohort_pedagogy_toggle_reaches_global_settings(client):
    """The exact reported path: enable the card for a cohort, then read what
    the player's cockpit reads."""
    sid = _cohort(client, "PedEffective")
    r = client.put(f"/api/admin/cohort/{sid}/pedagogical-settings",
                   json={"real_world_cards_enabled": True})
    assert r.status_code == 200, r.text

    eff = client.get(f"/api/admin/global-settings?session_id={sid}").json()
    assert eff["real_world_cards_enabled"] is True, (
        "the cohort's pedagogy override never reached /global-settings — the "
        "player's Real-World Case Card can never render"
    )


@pytest.mark.parametrize("key", PEDAGOGY_KEYS)
def test_every_pedagogy_toggle_is_cohort_effective(client, key):
    """Not just the reported one: the whole family flows through the same
    split store, so all of them were affected."""
    sid = _cohort(client, f"Ped-{key}")
    client.put(f"/api/admin/cohort/{sid}/pedagogical-settings", json={key: True})
    eff = client.get(f"/api/admin/global-settings?session_id={sid}").json()
    assert eff.get(key) is True, f"{key} is not cohort-effective"


def test_one_cohorts_override_does_not_leak_to_another(client):
    sid_on = _cohort(client, "PedOn")
    sid_off = _cohort(client, "PedOff")
    client.put(f"/api/admin/cohort/{sid_on}/pedagogical-settings",
               json={"real_world_cards_enabled": True})

    on = client.get(f"/api/admin/global-settings?session_id={sid_on}").json()
    off = client.get(f"/api/admin/global-settings?session_id={sid_off}").json()
    glob = client.get("/api/admin/global-settings").json()

    assert on["real_world_cards_enabled"] is True
    assert off["real_world_cards_enabled"] is False, "override leaked to another cohort"
    assert glob["real_world_cards_enabled"] is False, "override leaked into the platform default"


def test_case_card_content_and_endpoint_exist(client):
    """Guards the other half of the feature: a toggle that reaches the player
    is useless if the card endpoint has no content for the round."""
    for rnd in (1, 5, 10):
        r = client.get(f"/api/admin/pedagogical/real-world-parallels/{rnd}")
        assert r.status_code == 200, r.text
        card = r.json().get("parallel")
        assert card and card.get("title"), f"no case card for round {rnd}"
        for field in ("brief", "simulation_parallel", "outcome", "key_lesson"):
            assert card.get(field), f"round {rnd} card missing {field}"


def test_cockpit_requests_cohort_scoped_settings():
    """Frontend half, pinned at source: a bare /global-settings fetch in the
    cockpit reintroduces defect #2 and nothing else would catch it."""
    repo = pathlib.Path(__file__).resolve().parents[2]
    src = (repo / "frontend" / "app" / "components" / "ExecutiveCockpit.js").read_text(encoding="utf-8")
    i = src.index("setPedToggles")
    block = src[max(0, i - 900):i + 200]
    assert "session_id=" in block, (
        "ExecutiveCockpit fetches /global-settings without a session_id — "
        "per-cohort pedagogy toggles will be ignored for players"
    )
