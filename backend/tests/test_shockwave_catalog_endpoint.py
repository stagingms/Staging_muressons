"""G-3 proper (v3/S5): GET /api/admin/shockwave/events — the engine's crisis
catalog served as a single source of truth for the Shockwave console.

Covers: (a) the route exists and is auth-gated (an unauthenticated caller is
rejected, NOT 404 — which would mean the path got shadowed by a dynamic
/{cohort_id} route or was removed); (b) an authenticated facilitator receives
exactly the _SHOCKWAVE_EVENTS entries, ids and impact numbers intact.
"""
from fastapi.testclient import TestClient
from main import app
from admin_router import _SHOCKWAVE_EVENTS

client = TestClient(app)


def test_catalog_route_exists_and_is_gated():
    r = client.get("/api/admin/shockwave/events")
    assert r.status_code in (401, 403), (
        f"expected auth rejection, got {r.status_code} — 404 would mean the "
        f"route is missing or shadowed by a dynamic /{{cohort_id}} route"
    )


def test_catalog_matches_engine_for_authenticated_facilitator():
    # Self-provision a facilitator via god_mode rather than depending on live
    # registry data (FAC-001's password is operator-owned and changes in real
    # deployments; one-time passwords are randomised per QA-2026-07-16 #11).
    gm = client.post(
        "/api/admin/facilitators/login",
        json={"facilitator_id": "god_mode", "password": "sim2026@iim"},
    )
    assert gm.status_code == 200, gm.text
    created = client.post(
        "/api/admin/facilitators",
        json={"name": "Shockwave Probe", "role": "facilitator"},
        cookies=gm.cookies,
    )
    assert created.status_code in (200, 201), created.text
    body = created.json()
    login = client.post(
        "/api/admin/facilitators/login",
        json={"facilitator_id": body["facilitator_id"],
              "password": body["one_time_password"]},
    )
    assert login.status_code == 200, login.text

    r = client.get("/api/admin/shockwave/events", cookies=login.cookies)
    assert r.status_code == 200, r.text
    events = {e["id"]: e for e in r.json()["events"]}

    assert set(events.keys()) == set(_SHOCKWAVE_EVENTS.keys())
    for eid, ev in _SHOCKWAVE_EVENTS.items():
        assert events[eid]["financial_impact"] == ev["financial_impact"]
        assert events[eid]["reputation_impact"] == ev["reputation_impact"]
        assert events[eid]["title"] == ev["title"]
