"""
C3 regression tests -- 'Project Admin never manages runs'.

The project_admin virtual account provisions facilitators + cohorts but must be
blocked from every live-run-management endpoint. These endpoints are guarded by
require_sim_manager (which rejects project_admin); cohort provisioning/config and
read endpoints stay on require_facilitator (which project_admin may use).

Contract:
  * project_admin -> 403 with "project admin" detail on run-management endpoints.
  * project_admin -> allowed (not 401/403) on provisioning + read endpoints.
  * a normal facilitator (lead) is NOT blocked by the project-admin gate.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_PROJECT_ADMIN = {"facilitator_id": "project_admin", "password": "simadmin2026@"}
_LEAD = {"facilitator_id": "FAC-001", "password": "Muressons123"}

# Live-run-management endpoints that project_admin must never reach.
# (method, path, json) -- the guard runs before the handler, so a fake id is fine.
_RUN_ENDPOINTS = [
    ("post", "/api/admin/sessions/FAKE/pacing", {"mode": "manual", "interval_seconds": 0}),
    ("post", "/api/admin/sessions/FAKE/pacing/unlock", {}),
    ("post", "/api/admin/players/register", {"player_name": "X", "team_name": "A"}),
    ("post", "/api/admin/players/induct",
     {"name": "A", "email": "a@b.com", "session_id": "FAKE", "assigned_bu": "pharma"}),
    ("post", "/api/admin/FAKE/inject-message", {}),
    ("post", "/api/admin/FAKE/shockwave", {}),
    ("post", "/api/admin/broadcast", {"title": "t", "body": "b"}),
]

# Provisioning + read endpoints project_admin must still be able to reach.
_ALLOWED_ENDPOINTS = [
    ("get", "/api/admin/facilitators"),                       # require_facilitator (read)
    ("get", "/api/admin/facilitators/bulk-upload/template"),  # require_registry_admin
]


def _cookies(creds):
    r = client.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return r.cookies


def test_project_admin_blocked_on_run_management():
    pac = _cookies(_PROJECT_ADMIN)
    for method, path, body in _RUN_ENDPOINTS:
        r = getattr(client, method)(path, json=body, cookies=pac)
        assert r.status_code == 403, f"{path}: expected 403, got {r.status_code}"
        assert "project admin" in r.json().get("detail", "").lower(), \
            f"{path}: expected project-admin denial, got {r.json()}"


def test_project_admin_allowed_on_provisioning_and_reads():
    pac = _cookies(_PROJECT_ADMIN)
    for method, path in _ALLOWED_ENDPOINTS:
        r = getattr(client, method)(path, cookies=pac)
        assert r.status_code not in (401, 403), \
            f"{path}: project_admin should be allowed, got {r.status_code}"


def test_regular_facilitator_not_blocked_by_project_admin_gate():
    lf = _cookies(_LEAD)
    r = client.post("/api/admin/sessions/FAKE/pacing",
                    json={"mode": "manual", "interval_seconds": 0}, cookies=lf)
    # May hit later validation (any status), but never the project-admin 403.
    if r.status_code == 403:
        assert "project admin" not in r.json().get("detail", "").lower()


def test_project_admin_can_refresh_session():
    # Refresh gap fix: the virtual project_admin account must be able to refresh
    # its JWT (previously 401'd on the registry lookup, forcing a re-login on
    # expiry). god_mode already had this branch; project_admin now does too.
    pac = _cookies(_PROJECT_ADMIN)
    r = client.post("/api/admin/auth/refresh", cookies=pac)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "project_admin"
    assert set(body["allowed_tabs"]) == {"dashboard_home", "facilitator_registry"}
    assert "mur_session" in r.cookies, "refresh should set a fresh session cookie"
    # The refreshed session must remain blocked from run management (C3 intact).
    r2 = client.post("/api/admin/sessions/FAKE/pacing",
                     json={"mode": "manual", "interval_seconds": 0}, cookies=r.cookies)
    assert r2.status_code == 403
