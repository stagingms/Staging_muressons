"""
Bulk facilitator delete — POST /api/admin/facilitators/bulk-delete.

Batch counterpart of DELETE /facilitators/{fac_id}. Verifies:
  - RBAC: super_admin level required (project_admin and anonymous are refused);
  - soft delete stamps deleted_at + cascades, and is idempotent (already_deleted);
  - hard delete removes records from the registry (second pass → not_found);
  - unknown IDs are reported per-ID (not_found) without aborting the batch;
  - a super admin cannot delete their own account mid-batch (skipped_self);
  - input validation: empty list and oversize batch → 400.
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


def _create(gm_cookies, name, role="facilitator"):
    r = client.post(
        "/api/admin/facilitators",
        json={"name": name, "role": role},
        cookies=gm_cookies,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return body["facilitator_id"], body.get("one_time_password")


def _bulk_delete(cookies, ids, hard=False):
    return client.post(
        "/api/admin/facilitators/bulk-delete",
        json={"facilitator_ids": ids, "hard": hard},
        cookies=cookies,
    )


# ── RBAC ─────────────────────────────────────────────────────────────────────

def test_anonymous_is_refused():
    r = client.post(
        "/api/admin/facilitators/bulk-delete",
        json={"facilitator_ids": ["FAC-001"]},
    )
    # BUG-2026-07-18: anonymous (no/dead cookie) is now 401 "Session expired",
    # not a role-based 403 — see _reject_anonymous in admin_router.
    assert r.status_code == 401, r.text


def test_project_admin_is_refused():
    # project_admin (level 0, provisioning-only) must never reach a
    # super-admin destructive endpoint.
    pa = _cookies(_PA)
    r = _bulk_delete(pa, ["FAC-001"])
    assert r.status_code == 403, r.text


# ── Input validation ─────────────────────────────────────────────────────────

def test_empty_list_is_rejected():
    gm = _cookies(_GOD)
    assert _bulk_delete(gm, []).status_code == 400
    assert _bulk_delete(gm, ["", "   "]).status_code == 400


def test_oversize_batch_is_rejected():
    gm = _cookies(_GOD)
    r = _bulk_delete(gm, [f"FAC-X{i}" for i in range(201)])
    assert r.status_code == 400, r.text


# ── Soft delete (default) ────────────────────────────────────────────────────

def test_bulk_soft_delete_and_idempotency():
    gm = _cookies(_GOD)
    ids = [_create(gm, f"BulkSoft{i}")[0] for i in range(3)]

    r = _bulk_delete(gm, ids + ["FAC-DOES-NOT-EXIST"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["hard"] is False
    assert body["deleted"] == 3
    assert body["status"] == "partial"  # one not_found in the batch
    by_id = {e["facilitator_id"]: e for e in body["results"]}
    for fid in ids:
        assert by_id[fid]["status"] == "deleted"
    assert by_id["FAC-DOES-NOT-EXIST"]["status"] == "not_found"

    # Soft-deleted accounts can no longer log in (registry lookup skips
    # deleted_at) and a second soft pass reports already_deleted.
    r2 = _bulk_delete(gm, ids)
    assert r2.status_code == 200, r2.text
    assert all(e["status"] == "already_deleted" for e in r2.json()["results"])
    assert r2.json()["deleted"] == 0


def test_duplicate_ids_are_deduped():
    gm = _cookies(_GOD)
    fid, _ = _create(gm, "BulkDup")
    r = _bulk_delete(gm, [fid, fid, f"  {fid}  "])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["requested"] == 1
    assert body["deleted"] == 1


# ── Hard delete ──────────────────────────────────────────────────────────────

def test_bulk_hard_delete_removes_registry_records():
    gm = _cookies(_GOD)
    ids = [_create(gm, f"BulkHard{i}")[0] for i in range(2)]

    r = _bulk_delete(gm, ids, hard=True)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["hard"] is True
    assert body["deleted"] == 2
    assert body["status"] == "completed"

    # Records are gone from the registry entirely → second pass not_found.
    r2 = _bulk_delete(gm, ids, hard=True)
    assert r2.status_code == 200
    assert all(e["status"] == "not_found" for e in r2.json()["results"])


# ── Self-protection ──────────────────────────────────────────────────────────

def test_caller_cannot_bulk_delete_own_account():
    gm = _cookies(_GOD)
    admin_id, admin_pw = _create(gm, "BulkSelfAdmin", role="super_admin")
    victim_id, _ = _create(gm, "BulkSelfVictim")

    admin_cookies = _cookies({"facilitator_id": admin_id, "password": admin_pw})
    r = _bulk_delete(admin_cookies, [admin_id, victim_id])
    assert r.status_code == 200, r.text
    body = r.json()
    by_id = {e["facilitator_id"]: e for e in body["results"]}
    assert by_id[admin_id]["status"] == "skipped_self"
    assert by_id[victim_id]["status"] == "deleted"
    assert body["deleted"] == 1

    # The caller's session must still be valid afterwards (token not bumped).
    r_list = client.get("/api/admin/facilitators", cookies=admin_cookies)
    assert r_list.status_code == 200, r_list.text
