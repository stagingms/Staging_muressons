"""F-4 proper (v3/S5): POST /api/admin/facilitators/bulk-upload/preview —
parse-only Excel preview so the .xlsx path gets the review step CSV always had.

Covers: (a) the route exists and is registry-admin gated (401/403 unauth, not
404 — a distinct path was chosen precisely so older backends 404 and the
frontend falls back instead of accidentally creating accounts); (b) preview
parses valid + invalid rows and creates NOTHING; (c) preview and create agree
on the same file (shared parser).
"""
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from main import app
from admin_router import _facilitator_registry, require_registry_admin, _persist_facilitators

client = TestClient(app)


def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


SHEET = [
    ["name", "email", "programme", "max_cohorts"],
    ["Prof. Preview One", "one@test.local", "MBA 2026", 2],
    ["", "orphan@test.local", "row without a name", 1],   # -> row error
    ["Dr. Preview Two", "two@test.local", "", ""],
]


def test_preview_route_exists_and_is_gated():
    r = client.post(
        "/api/admin/facilitators/bulk-upload/preview",
        files={"file": ("f.xlsx", _xlsx(SHEET), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code in (401, 403), (
        f"expected auth rejection, got {r.status_code} — 404 would mean the route is missing"
    )


def test_preview_parses_and_creates_nothing():
    app.dependency_overrides[require_registry_admin] = lambda: None
    try:
        before = len(_facilitator_registry)
        r = client.post(
            "/api/admin/facilitators/bulk-upload/preview",
            files={"file": ("f.xlsx", _xlsx(SHEET), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["dry_run"] is True
        assert d["total_valid"] == 2 and d["total_errors"] == 1
        assert [row["name"] for row in d["rows"]] == ["Prof. Preview One", "Dr. Preview Two"]
        assert d["rows"][0]["max_cohorts"] == 2
        assert d["rows"][1]["max_cohorts"] == 3          # blank -> default 3
        assert d["errors"][0]["row"] == 3                 # sheet row number
        assert len(_facilitator_registry) == before       # NOTHING created
    finally:
        app.dependency_overrides.pop(require_registry_admin, None)


def test_preview_and_create_agree_on_the_same_file():
    app.dependency_overrides[require_registry_admin] = lambda: None
    try:
        before_ids = {f["facilitator_id"] for f in _facilitator_registry}
        pv = client.post(
            "/api/admin/facilitators/bulk-upload/preview",
            files={"file": ("f.xlsx", _xlsx(SHEET), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        ).json()
        cr = client.post(
            "/api/admin/facilitators/bulk-upload",
            files={"file": ("f.xlsx", _xlsx(SHEET), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        ).json()
        # Same parser => same verdicts, row for row.
        assert cr["total_created"] == pv["total_valid"]
        assert cr["total_errors"] == pv["total_errors"]
        assert [c["name"] for c in cr["created"]] == [r["name"] for r in pv["rows"]]
        assert cr["errors"] == pv["errors"]
        # Clean up the accounts this test created (test isolation) — and
        # persist the cleaned registry so the on-disk file isn't polluted
        # (the create endpoint persisted the additions).
        new_ids = {f["facilitator_id"] for f in _facilitator_registry} - before_ids
        _facilitator_registry[:] = [f for f in _facilitator_registry if f["facilitator_id"] not in new_ids]
        _persist_facilitators()
    finally:
        app.dependency_overrides.pop(require_registry_admin, None)
