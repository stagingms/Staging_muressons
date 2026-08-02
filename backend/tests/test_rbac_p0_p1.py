"""RBAC audit remediation — P0 (F3, F4, F5) and P1 (F1). 2026-08-01.

P0
--
F3  The facilitator-list endpoint decided admin-ness with
    `caller_role == "super_admin"`, which silently dropped the documented
    level-3 `admin` ALIAS (treated as a non-admin, so it saw only its own
    record) and admitted god_mode by ID rather than role. Now is_admin_role.
F4  POST /facilitators/batch was an unused super_admin-only duplicate of
    POST /facilitators/bulk (require_registry_admin). Divergent authz on one
    action is a hazard; the duplicate is deleted.
F5  assignable_roles_for documents WHY project_admin (level 0) may grant
    lead_facilitator/facilitator: its level ranks RUN authority, not
    provisioning authority.

P1 (F1)
-------
The per-facilitator `permissions` dict (can_undo_rounds, can_create_cohorts,
…) was authored at creation, editable in the Registry and returned at login —
and NO authorization decision ever read it. Capability is granted by ROLE. An
authority control that looks authoritative and silently is not is worse than
no control, so it is removed everywhere. These tests pin it gone and pin the
role-based reality it was pretending to describe.
"""
import pathlib
import re

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
_FRONTEND = _BACKEND.parent / "frontend"


# ── F1: the inert permissions dict is gone ─────────────────────────────────

def test_no_facilitator_record_is_created_with_a_permissions_dict():
    """The four creation sites (single / bulk-upload / bulk / — batch deleted)
    must not author the dict any more."""
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    # No literal capability keys survive anywhere in the router.
    for key in ("can_undo_rounds", "can_override_decisions", "can_modify_materiality",
                "can_manage_auto_pause", "can_create_cohorts", "can_enable_side_tracks"):
        assert f'"{key}"' not in src, f"{key} is still authored in admin_router"


def test_login_and_profile_responses_no_longer_return_permissions():
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    assert '"permissions": fac.get("permissions", {})' not in src
    assert '"permissions": {},' not in src


def test_update_endpoint_drops_a_stale_permissions_field_without_persisting():
    """An older client may still POST `permissions`; the request must succeed
    (no 422) and the field must never be written."""
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    i = src.index("async def update_facilitator(")
    body = src[i:i + 2500]
    assert 'if key == "permissions":' in body
    branch = body[body.index('if key == "permissions":'):]
    # the branch must skip the field; window is generous because the rationale
    # comment sits between the condition and the `continue`.
    assert "continue" in branch[:900]
    assert 'fac["permissions"]' not in body, "the update path still persists permissions"


def test_frontend_permission_grid_and_toggle_are_gone():
    fm = (_FRONTEND / "app" / "components" / "FacilitatorManager.js").read_text(encoding="utf-8")
    # The RENDERED label (a JSX <label>…Admin Permissions</label>) must be gone.
    # The RBAC-F1 tombstone comments legitimately name it, so match the markup,
    # not the bare phrase.
    assert not re.search(r">\s*Admin Permissions\s*<", fm), "the permission grid is still rendered"
    assert "updatePermission" not in fm
    assert "toggleCohortCreationPermission(" not in fm.replace(
        "// RBAC-F1: toggleCohortCreationPermission removed", "")
    # No LIVE use of the capability keys. Comments may still name them (the
    # tombstones explain the removal), so strip comment blocks before scanning
    # rather than pattern-matching prose line by line.
    code = re.sub(r"/\*.*?\*/", "", fm, flags=re.S)          # /* … */ and {/* … */}
    code = "\n".join(l for l in code.split("\n") if not l.lstrip().startswith("//"))
    for key in ("can_undo_rounds", "can_create_cohorts", "can_enable_side_tracks",
                "can_override_decisions", "can_modify_materiality", "can_manage_auto_pause"):
        assert key not in code, f"live use of {key} survives in FacilitatorManager.js"


def test_dashboard_create_gate_no_longer_reads_the_permission():
    page = (_FRONTEND / "app" / "admin" / "facilitator" / "page.js").read_text(encoding="utf-8")
    assert "permissions?.can_create_cohorts" not in page
    assert "data.permissions" not in page


# ── F3: admin classification is level-based ────────────────────────────────

def test_facilitator_list_uses_is_admin_role_not_a_string_compare():
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    i = src.index("is_admin_caller =")
    line = src[i:src.index("\n", i)]
    assert "is_admin_role(caller_role)" in line, line
    assert 'caller_role == "super_admin"' not in line, "string compare drops the `admin` alias"
    assert 'caller_id == "god_mode"' not in line, "god_mode must be admitted by ROLE, not id"


@pytest.mark.parametrize("role,expected", [
    ("god_mode", True), ("super_admin", True), ("admin", True),
    ("lead_facilitator", False), ("facilitator", False), ("project_admin", False),
])
def test_is_admin_role_covers_the_alias_and_god_mode(role, expected):
    from admin_shared import is_admin_role
    assert is_admin_role(role) is expected


# ── F4: one facilitator-creation authz rule ────────────────────────────────

def test_the_duplicate_batch_create_endpoint_is_deleted():
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    assert '@admin_router.post("/facilitators/batch"' not in src
    assert "async def batch_create_facilitators" not in src


def test_all_surviving_facilitator_creation_paths_share_one_guard():
    """Every remaining creation endpoint is require_registry_admin — so
    'who may create facilitators' has exactly one answer."""
    src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    for route in ('"/facilitators"', '"/facilitators/bulk"', '"/facilitators/bulk-upload"'):
        i = src.index(f"@admin_router.post({route}")
        decl = src[i:src.index("):", i)]
        assert "require_registry_admin" in decl, f"{route} uses a different guard"


# ── F5: the project_admin exception is documented ──────────────────────────

def test_project_admin_grant_exception_is_explained_and_bounded():
    import inspect
    from admin_shared import assignable_roles_for
    doc = inspect.getdoc(assignable_roles_for) or ""
    assert "RBAC-F5a" in doc, "the level-0 vs grants-leads tension is undocumented"
    granted = assignable_roles_for("project_admin")
    assert granted == {"lead_facilitator", "facilitator"}
    assert "super_admin" not in granted and "god_mode" not in granted


# ── the ladder itself is unchanged by this work ────────────────────────────

def test_role_ladder_is_untouched():
    from admin_shared import ROLE_HIERARCHY
    assert ROLE_HIERARCHY["god_mode"] == 4
    assert ROLE_HIERARCHY["super_admin"] == ROLE_HIERARCHY["admin"] == 3
    assert ROLE_HIERARCHY["lead_facilitator"] == 2
    assert ROLE_HIERARCHY["facilitator"] == 1
    assert ROLE_HIERARCHY["project_admin"] == 0


def test_god_mode_is_never_assignable_by_anyone():
    from admin_shared import assignable_roles_for, ROLE_HIERARCHY
    for role in ROLE_HIERARCHY:
        assert "god_mode" not in assignable_roles_for(role)


# ── F7: "no session" is 401, "wrong role" is 403 — on EVERY guard ──────────

def test_every_role_guard_distinguishes_no_session_from_wrong_role():
    """RBAC-F7 (2026-08-01), found by probing the live deploy: two guards
    answered an anonymous caller with 403 ("Lead Facilitator or higher
    required"), so an EXPIRED COOKIE read as a role refusal and sent the user
    to inspect their permissions instead of signing in again. The codebase had
    already adopted the 401/403 split (BUG-2026-07-18) — two guards just never
    got it. Pin it for all of them so the next guard added inherits the rule."""
    import inspect
    import admin_router

    for name in ("require_super_admin", "require_lead_facilitator",
                 "require_facilitator", "require_registry_admin",
                 "require_sim_manager"):
        src = inspect.getsource(getattr(admin_router, name))
        assert "role == 'anonymous'" in src or 'role == "anonymous"' in src, \
            f"{name} does not special-case an absent session"
        anon_branch = src[src.index("anonymous"):]
        assert "401" in anon_branch[:300], \
            f"{name} answers an unauthenticated caller with something other than 401"


@pytest.mark.parametrize("method,path", [
    ("patch", "/api/admin/solo-mode"),          # require_lead_facilitator
    ("get", "/api/admin/solo-mode"),            # require_lead_facilitator
    ("post", "/api/admin/facilitators/bulk"),   # require_registry_admin
])
def test_anonymous_callers_get_401_not_403(method, path):
    from fastapi.testclient import TestClient
    from main import app
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    client = TestClient(app, raise_server_exceptions=False)
    r = getattr(client, method)(path, json={}) if method != "get" else client.get(path)
    assert r.status_code == 401, (
        f"{method.upper()} {path} returned {r.status_code} to an anonymous caller — "
        "an expired session must read as 'sign in again', not a role refusal")
