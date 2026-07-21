"""
Workstream E tests — governance & audit.

I5: high-impact config writes under the god_mode break-glass identity must carry
a 'reason' for the audit trail; named super_admins are unaffected.
"""
import pytest
from fastapi import HTTPException

import admin_router


class _DummyReq:
    """Stand-in for a Request — the gate resolves the role via get_fac_role,
    which we monkeypatch, so the object itself is never inspected."""


def test_god_mode_write_without_reason_is_rejected(monkeypatch):
    monkeypatch.setattr(admin_router, "get_fac_role", lambda req: "god_mode")
    with pytest.raises(HTTPException) as exc:
        admin_router._require_god_mode_reason(_DummyReq(), None)
    assert exc.value.status_code == 422


def test_god_mode_write_with_blank_reason_is_rejected(monkeypatch):
    monkeypatch.setattr(admin_router, "get_fac_role", lambda req: "god_mode")
    with pytest.raises(HTTPException):
        admin_router._require_god_mode_reason(_DummyReq(), "   ")


def test_god_mode_write_with_reason_is_allowed(monkeypatch):
    monkeypatch.setattr(admin_router, "get_fac_role", lambda req: "god_mode")
    role = admin_router._require_god_mode_reason(_DummyReq(), "Raise carbon fee for advanced cohort")
    assert role == "god_mode"


def test_super_admin_does_not_need_a_reason(monkeypatch):
    monkeypatch.setattr(admin_router, "get_fac_role", lambda req: "super_admin")
    assert admin_router._require_god_mode_reason(_DummyReq(), None) == "super_admin"


def test_named_facilitator_roles_are_unaffected(monkeypatch):
    for role in ("lead_facilitator", "facilitator", "project_admin"):
        monkeypatch.setattr(admin_router, "get_fac_role", lambda req, r=role: r)
        assert admin_router._require_god_mode_reason(_DummyReq(), None) == role
