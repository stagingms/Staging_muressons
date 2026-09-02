"""ESG rubric fixes: blend clamping, new BRSR innovation keys, RBAC after the
facilitator-dashboard move, and ramped mr_breakdown reporting."""
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}
_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}

def _cookies(creds):
    r = client.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return r.cookies

def test_only_super_admin_edits_the_platform_rubric():
    """F-24 (launch audit 2026-09-01): the rubric is platform-wide, so a base
    facilitator may READ it (to explain the scoring) but not rewrite it for
    every other cohort; project_admin sees neither."""
    gm = _cookies(_GOD)
    r = client.post("/api/admin/facilitators", json={"name": "EsgFix", "role": "facilitator"}, cookies=gm)
    fid, pw = r.json()["facilitator_id"], r.json()["one_time_password"]
    from conftest import rotate_facilitator_password  # F-22: initial password → personal
    pw = rotate_facilitator_password(client, fid, pw)
    fc = _cookies({"facilitator_id": fid, "password": pw})
    from admin_shared import get_allowed_tabs
    assert "esg_weights" not in get_allowed_tabs({"role": "facilitator"})
    assert "esg_weights" not in get_allowed_tabs({"role": "project_admin"})
    assert "*" in get_allowed_tabs({"role": "super_admin"})
    assert client.get("/api/admin/esg-profile-weights", cookies=fc).status_code == 200
    assert client.post("/api/admin/esg-profile-weights", json={"weights": {}}, cookies=fc).status_code == 403
    assert client.post("/api/admin/esg-profile-weights", json={"weights": {}}, cookies=gm).status_code == 200
    pa = _cookies(_PA)
    assert client.post("/api/admin/esg-profile-weights", json={"weights": {}}, cookies=pa).status_code == 403

def test_blend_weights_clamped_and_new_brsr_keys_accepted():
    gm = _cookies(_GOD)
    r = client.post("/api/admin/esg-profile-weights", json={"weights": {
        "governance": {"reputation_blend": 5},
        "social_impact": {"social_license_blend": -2},
        "innovation": {"brsr_steward": 45, "brsr_laggard": 10},
    }}, cookies=gm)
    assert r.status_code == 200, r.text
    w = r.json()["esg_profile_weights"]
    assert w["governance"]["reputation_blend"] == 1.0
    assert w["social_impact"]["social_license_blend"] == 0.0
    assert w["innovation"]["brsr_steward"] == 45
    assert w["innovation"]["brsr_laggard"] == 10
    client.post("/api/admin/esg-profile-weights/reset", cookies=gm)

def test_backend_frontend_default_weights_in_sync():
    """The frontend keeps a mirrored copy of DEFAULT_ESG_WEIGHTS; drift check."""
    import json, re, pathlib
    from admin_shared import DEFAULT_ESG_WEIGHTS
    js = pathlib.Path(__file__).resolve().parents[2] / "frontend/app/components/ESGLeadershipProfile.js"
    if not js.exists():
        import pytest; pytest.skip("frontend not present in this checkout")
    src = js.read_text(encoding="utf-8")
    for dim, sigs in DEFAULT_ESG_WEIGHTS.items():
        for k in sigs:
            assert re.search(rf"\b{k}\s*:", src), f"frontend missing {dim}.{k}"

def test_mr_breakdown_reports_ramped_values():
    """round_logic._mrb contract: numeric extras (ramped) pass through; boolean
    extras fall back to nominal; missing -> 0."""
    import inspect, round_logic, re
    src = inspect.getsource(round_logic)
    assert 'def _mrb(' in src
    # the nominal-only pattern must be gone
    assert '0.30 if extra.get("mr_climate_leader_bonus") else 0' not in src
    assert '_mrb("mr_stranded_asset_penalty", -0.40)' in src
    assert '_mrb("mr_social_collapse_penalty", -0.50)' in src
