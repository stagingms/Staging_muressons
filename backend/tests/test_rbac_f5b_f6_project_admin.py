"""RBAC F5b + F6 — the project_admin model, pinned as decisions. 2026-08-01.

Both findings were resolved as "the code is right, the description was wrong".
Documentation rots, so the DECISIONS are pinned behaviourally here: if someone
later "tidies up" by removing registry project_admins or by widening the roster
guard, these fail and point at the reasoning.

F5b — project_admin exists in TWO legitimate forms:
      * VIRTUAL  — PROJECT_ADMIN_PASSWORD break-glass (shared secret, no
                   individual accountability, disabled when the env var is unset)
      * REGISTRY — a normal FAC-NNN account with role project_admin, assignable
                   by a super_admin; preferred for a named programme admin
                   because it is per-person, auditable and revocable.
      Both behave identically at every guard.

F6  — cohort SHELL vs cohort ROSTER is a deliberate seam: project_admin may
      create a cohort but not mint player ids, because a player id is a
      live-run credential.
"""
import pytest


@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _clear():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def _login(client, fac_id, pw="test-master-pw"):
    _clear()
    return client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": fac_id, "password": pw})


def _personalise(client, fid, default_pw):
    """F-22 (launch audit 2026-09-01): the id-derived initial password may only be
    used to set a personal one; every other admin call is refused until then."""
    from conftest import rotate_facilitator_password
    _clear()
    rotate_facilitator_password(client, fid, default_pw)


@pytest.fixture
def registry_project_admin(client):
    """A NAMED project_admin in the registry — the preferred form (F5b)."""
    assert _login(client, "god_mode").status_code == 200
    r = client.post("/api/admin/facilitators",
                    json={"name": "Programme Admin", "role": "project_admin"})
    assert r.status_code == 200, r.text
    body = r.json()
    fid = (body.get("facilitator") or {}).get("facilitator_id") or body.get("facilitator_id")
    client.cookies.clear()
    return fid


# ── F5b: the registry form is real and must stay assignable ────────────────

def test_project_admin_is_assignable_to_a_registry_account():
    """If someone removes this believing project_admin is 'virtual only', a
    named programme administrator becomes impossible and the only way to hold
    the role is the shared env password."""
    from admin_shared import _ASSIGNABLE_ROLES
    assert "project_admin" in _ASSIGNABLE_ROLES


def test_a_registry_project_admin_logs_in_with_the_project_admin_role(client, registry_project_admin):
    from default_credentials import default_facilitator_password
    fid = registry_project_admin
    r = _login(client, fid, default_facilitator_password(fid))
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "project_admin"
    # and gets the provisioning tab set, not a facilitator's
    assert set(r.json()["allowed_tabs"]) == {"dashboard_home", "facilitator_registry"}


def test_both_forms_are_treated_identically_by_the_guards(client, registry_project_admin):
    """The registry form must not be a second-class citizen: same provisioning
    powers, same run exclusion."""
    from default_credentials import default_facilitator_password
    from admin_shared import may_create_cohort
    fid = registry_project_admin
    _personalise(client, fid, default_facilitator_password(fid))
    # provisioning: may create facilitators…
    made = client.post("/api/admin/facilitators", json={"name": "Made By PA", "role": "facilitator"})
    assert made.status_code == 200, made.text
    # …and cohorts
    assert may_create_cohort("project_admin")[0] is True


def test_project_admin_cannot_mint_another_project_admin_or_an_admin(client, registry_project_admin):
    """Containment: the delegation must not spread or reach admin tiers."""
    from admin_shared import assignable_roles_for
    granted = assignable_roles_for("project_admin")
    assert granted == {"lead_facilitator", "facilitator"}
    assert "project_admin" not in granted
    assert "super_admin" not in granted and "god_mode" not in granted


def test_the_provisioning_trust_model_is_documented():
    """F5b: provisioning implies impersonation (whoever creates an account
    learns its initial credential). That is accepted deliberately — if the
    explanation disappears, the next reader will mistake it for a hole."""
    import inspect
    from admin_shared import assignable_roles_for
    doc = (inspect.getdoc(assignable_roles_for) or "").lower()
    assert "rbac-f5b" in doc
    # the three substantive parts of the explanation, not one magic word:
    # the mechanism, why it is tolerable, and how to tighten it.
    assert "initial credential" in doc, "the escalation mechanism is unexplained"
    assert "must_change_password" in doc, "the mitigation is unexplained"
    assert "facilitator" in doc, "the way to narrow the grant is unexplained"


# ── F6: the shell / roster seam ────────────────────────────────────────────

def test_project_admin_creates_the_shell_but_cannot_mint_players(client, registry_project_admin):
    """THE seam, end to end: cohort yes, roster no."""
    from default_credentials import default_facilitator_password
    fid = registry_project_admin
    _personalise(client, fid, default_facilitator_password(fid))

    made = client.post("/api/simulations/start",
                       json={"cohort_name": "F6-Shell", "facilitator_id": fid})
    assert made.status_code == 201, made.text
    sid = str(made.json()["session_id"])

    _clear()
    gp = client.post(f"/api/admin/{sid}/generate-player")
    assert gp.status_code == 403, "project_admin must not mint live-run credentials"
    detail = gp.json()["detail"].lower()
    assert "provision" in detail and "run" in detail, \
        f"the refusal must explain the seam, got: {detail}"


def test_a_real_facilitator_can_populate_that_same_cohort(client, registry_project_admin):
    """The seam must not strand the cohort — the running facilitator completes it."""
    from default_credentials import default_facilitator_password
    fid = registry_project_admin
    _personalise(client, fid, default_facilitator_password(fid))
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "F6-Handover", "facilitator_id": fid}
                          ).json()["session_id"])
    client.cookies.clear()
    assert _login(client, "god_mode").status_code == 200
    _clear()
    gp = client.post(f"/api/admin/{sid}/generate-player")
    assert gp.status_code == 200, gp.text
    assert gp.json()["player_id"].startswith("MUR-")


def test_the_seam_is_explained_where_it_is_enforced():
    """A 403 the operator only meets after clicking is not an explanation."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    i = src.index("async def generate_player_id(")
    doc = src[i:i + 1400]
    assert "RBAC-F6" in doc, "the seam rationale vanished from the endpoint"
    assert "not-yet-started" in doc, "the sanctioned way to widen it is undocumented"


def test_the_ui_warns_the_project_admin_before_the_403():
    import pathlib
    modal = (pathlib.Path(__file__).resolve().parents[2] / "frontend" / "app"
             / "components" / "CreateCohortModal.js").read_text(encoding="utf-8")
    assert "isProjectAdmin &&" in modal
    assert "player IDs are generated by the" in modal, \
        "the hand-over note is gone; project_admin is back to discovering the seam via a 403"
