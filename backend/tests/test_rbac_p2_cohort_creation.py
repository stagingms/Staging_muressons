"""RBAC P2 / R2 — ONE server-side rule for who may create a cohort. 2026-08-01.

THE CONTRADICTION (audit F2)
----------------------------
One capability had THREE answers:
  * dashboard button   -> a per-profile permission that enforced nothing
  * Registry-tab button-> the role string (`role !== 'facilitator'`)
  * POST /simulations/start -> NEITHER; any authenticated facilitator with
    quota could create a cohort, including through a direct API call that both
    UI surfaces appeared to forbid.

Now `admin_shared.may_create_cohort(role)` is the only place the question is
answered: /start enforces it, and both UI surfaces render its result
(`may_create_cohorts`, returned by login and auth/refresh).

TWO REAL BUGS FIXED ALONGSIDE
-----------------------------
1. The `allow_facilitator_cohort_creation` switch was enforced inside
   check_and_increment_cohort_count against the TARGET facilitator, not the
   ACTOR — wrong identity whenever a registry admin created a cohort on
   someone else's behalf.
2. That same check demanded super_admin, so switching it off silently blocked
   LEAD FACILITATORS — the people who actually run workshops.

DEFAULT IS UNCHANGED: `allow_facilitator_cohort_creation` stays True, so base
facilitators keep the access the server has always granted them. Turning it
off is now the supported way to make cohort creation lead-and-above only.
"""
import pytest


# ── the policy helper ──────────────────────────────────────────────────────

@pytest.fixture
def switch():
    """Set/restore allow_facilitator_cohort_creation without leaking state."""
    from admin_shared import _god_mode_settings
    had = "allow_facilitator_cohort_creation" in _god_mode_settings
    old = _god_mode_settings.get("allow_facilitator_cohort_creation")

    def _set(value):
        _god_mode_settings["allow_facilitator_cohort_creation"] = value

    yield _set
    if had:
        _god_mode_settings["allow_facilitator_cohort_creation"] = old
    else:
        _god_mode_settings.pop("allow_facilitator_cohort_creation", None)


@pytest.mark.parametrize("role", ["god_mode", "super_admin", "admin",
                                  "lead_facilitator", "project_admin"])
def test_privileged_roles_may_always_create(role, switch):
    from admin_shared import may_create_cohort
    switch(False)   # even with the switch off
    allowed, _ = may_create_cohort(role)
    assert allowed is True, f"{role} must always be able to create cohorts"


def test_base_facilitator_follows_the_platform_switch(switch):
    from admin_shared import may_create_cohort
    switch(True)
    assert may_create_cohort("facilitator")[0] is True
    switch(False)
    allowed, reason = may_create_cohort("facilitator")
    assert allowed is False
    assert "lead facilitators" in reason.lower(), reason


def test_default_preserves_existing_access(switch):
    """An unconfigured platform must not silently lock base facilitators out."""
    from admin_shared import _god_mode_settings, may_create_cohort
    _god_mode_settings.pop("allow_facilitator_cohort_creation", None)
    assert may_create_cohort("facilitator")[0] is True


def test_anonymous_is_refused():
    from admin_shared import may_create_cohort
    for role in ("anonymous", "", None):
        allowed, reason = may_create_cohort(role)
        assert allowed is False and reason


# ── the server actually enforces it ────────────────────────────────────────

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


def _make_facilitator(client, role):
    """god_mode provisions a real registry facilitator of the given role."""
    assert _login(client, "god_mode").status_code == 200
    r = client.post("/api/admin/facilitators", json={"name": f"P2 {role}", "role": role})
    assert r.status_code == 200, r.text
    body = r.json()
    fid = (body.get("facilitator") or {}).get("facilitator_id") or body.get("facilitator_id")
    client.cookies.clear()
    return fid


def test_base_facilitator_is_refused_by_the_api_when_the_switch_is_off(client, switch):
    """The hole this closes: the UI hid the button, the API allowed it anyway."""
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "facilitator")
    assert _login(client, fid, default_facilitator_password(fid)).status_code == 200

    switch(False)
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "P2-Denied", "facilitator_id": fid})
    assert r.status_code == 403, r.text
    assert "lead facilitators" in r.json()["detail"].lower()
    # …and nothing was created
    from database_memory import _sessions
    assert not any(s.get("cohort_name") == "P2-Denied" for s in _sessions.values())


def test_base_facilitator_may_create_when_the_switch_is_on(client, switch):
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "facilitator")
    assert _login(client, fid, default_facilitator_password(fid)).status_code == 200
    switch(True)
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "P2-Allowed", "facilitator_id": fid})
    assert r.status_code == 201, r.text


def test_lead_facilitator_is_never_blocked_by_the_switch(client, switch):
    """REGRESSION: the old check demanded super_admin when the switch was off,
    silently locking out the very role that runs workshops."""
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "lead_facilitator")
    assert _login(client, fid, default_facilitator_password(fid)).status_code == 200
    switch(False)
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "P2-Lead", "facilitator_id": fid})
    assert r.status_code == 201, r.text


def test_resuming_an_existing_cohort_is_not_gated(client, switch):
    """The rule guards bringing a cohort INTO EXISTENCE, never resuming one —
    otherwise flipping the switch would strand a running workshop."""
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "facilitator")
    assert _login(client, fid, default_facilitator_password(fid)).status_code == 200
    switch(True)
    first = client.post("/api/simulations/start",
                        json={"cohort_name": "P2-Resume", "facilitator_id": fid})
    assert first.status_code == 201
    sid = str(first.json()["session_id"])

    switch(False)   # policy tightens mid-workshop
    again = client.post("/api/simulations/start",
                        json={"cohort_name": "P2-Resume", "facilitator_id": fid})
    # The endpoint declares 201 for every successful return, resume included —
    # the property that matters is that it was NOT refused and handed back the
    # SAME cohort rather than creating a second one.
    assert again.status_code != 403, "resume was blocked by the create policy"
    assert again.status_code < 400, again.text
    assert str(again.json()["session_id"]) == sid, "resume created a new cohort"


def test_login_publishes_the_answer_for_the_ui(client, switch):
    """Both buttons render this field; without it they would guess again."""
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "facilitator")
    switch(False)
    r = _login(client, fid, default_facilitator_password(fid))
    assert r.status_code == 200
    assert r.json()["may_create_cohorts"] is False
    switch(True)
    r2 = _login(client, fid, default_facilitator_password(fid))
    assert r2.json()["may_create_cohorts"] is True


def test_quota_denial_is_reported_distinctly_from_policy_denial(client, switch):
    """The old code answered a policy refusal with 'reached the maximum cohort
    limit', sending an administrator to look at the wrong setting."""
    from default_credentials import default_facilitator_password
    fid = _make_facilitator(client, "facilitator")
    assert _login(client, fid, default_facilitator_password(fid)).status_code == 200
    switch(False)
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "P2-Msg", "facilitator_id": fid})
    assert "maximum cohort limit" not in r.json()["detail"].lower()


# ── tripwire: the rule stays in ONE place ──────────────────────────────────

def test_start_endpoint_delegates_to_the_shared_policy():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "router.py").read_text(encoding="utf-8")
    i = src.index("async def start_simulation")
    body = src[i:i + 4000]
    assert "may_create_cohort(caller_role)" in body, \
        "/start must delegate to the shared policy, not re-implement a rule"


def test_the_quota_counter_no_longer_re_implements_policy():
    import inspect
    from admin_shared import check_and_increment_cohort_count
    src = inspect.getsource(check_and_increment_cohort_count)
    code = "\n".join(l for l in src.split("\n") if not l.strip().startswith("#"))
    assert "allow_facilitator_cohort_creation" not in code, \
        "policy leaked back into the quota counter — two rules again"


def test_both_ui_surfaces_read_the_server_answer():
    import pathlib
    page = (pathlib.Path(__file__).resolve().parents[2]
            / "frontend" / "app" / "admin" / "facilitator" / "page.js").read_text(encoding="utf-8")
    # exactly the two create-cohort gates, both on may_create_cohorts
    assert page.count("authData.may_create_cohorts !== undefined") == 2, \
        "a create-cohort button is still deciding for itself"
