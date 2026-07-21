"""
P1 / C1 regression -- role assignment is caller-scoped. A caller may never grant
a role above its own tier; project_admin may grant only lead/facilitator; and the
virtual god_mode tier is never assignable to a registry facilitator.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}
_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}


def _cookies(creds):
    r = client.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return r.cookies


def test_project_admin_can_only_grant_lead_and_facilitator():
    pa = _cookies(_PA)
    assert client.post("/api/admin/facilitators", json={"name": "E1", "role": "super_admin"}, cookies=pa).status_code == 403
    assert client.post("/api/admin/facilitators", json={"name": "E2", "role": "god_mode"}, cookies=pa).status_code == 403
    assert client.post("/api/admin/facilitators", json={"name": "E3", "role": "project_admin"}, cookies=pa).status_code == 403
    assert client.post("/api/admin/facilitators", json={"name": "OK1", "role": "facilitator"}, cookies=pa).status_code == 200
    assert client.post("/api/admin/facilitators", json={"name": "OK2", "role": "lead_facilitator"}, cookies=pa).status_code == 200


def test_god_mode_is_never_assignable():
    gm = _cookies(_GOD)
    # create a target facilitator to mutate
    created = client.post("/api/admin/facilitators", json={"name": "Target", "role": "facilitator"}, cookies=gm)
    assert created.status_code == 200, created.text
    fid = created.json()["facilitator_id"]
    creds = {"god_mode_fac_id": "god_mode", "god_mode_password": "sim2026@iim"}
    # god_mode caller may NOT assign the god_mode tier...
    r_god = client.put(f"/api/admin/facilitators/{fid}/role", json={"role": "god_mode", **creds}, cookies=gm)
    assert r_god.status_code == 403, r_god.text
    # ...but CAN assign super_admin (within its scope).
    r_super = client.put(f"/api/admin/facilitators/{fid}/role", json={"role": "super_admin", **creds}, cookies=gm)
    assert r_super.status_code == 200, r_super.text
    # generic update endpoint is also closed to the god_mode tier.
    r_generic = client.put(f"/api/admin/facilitators/{fid}", json={"role": "god_mode"}, cookies=gm)
    assert r_generic.status_code in (400, 403), r_generic.text
