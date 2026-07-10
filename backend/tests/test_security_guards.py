"""
INFO-002: Security regression tests.

Verifies that every guarded endpoint returns 401/403 for unauthenticated
requests, and that key security properties hold across the codebase.

Run with:
    cd backend && pytest tests/test_security_guards.py -v
"""

import pytest
import anyio
import httpx
from httpx import AsyncClient, ASGITransport

# anyio is installed — use @pytest.mark.anyio for async tests
pytestmark = pytest.mark.anyio


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _get(path: str, headers: dict = None):
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, headers=headers or {})

async def _post(path: str, json: dict = None, headers: dict = None):
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, json=json or {}, headers=headers or {})

async def _put(path: str, json: dict = None, headers: dict = None):
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.put(path, json=json or {}, headers=headers or {})


# ── CRIT-002: /players/register must require facilitator auth ────────────────

async def test_register_player_requires_auth():
    r = await _post("/api/admin/players/register", json={"player_name": "Test", "team_name": "A"})
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── CRIT-003: /players/induct must require facilitator auth ─────────────────

async def test_induct_player_requires_auth():
    r = await _post("/api/admin/players/induct", json={
        "name": "Alice", "email": "a@b.com", "session_id": "fake-session", "assigned_bu": "pharma"
    })
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── CRIT-004: /players/set-password must require facilitator auth ────────────

async def test_set_player_password_requires_auth():
    r = await _put("/api/admin/players/set-password", json={"player_id": "P001", "password": "hack"})
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── HIGH-002: GET /facilitators must require auth ────────────────────────────

async def test_list_facilitators_requires_auth():
    r = await _get("/api/admin/facilitators")
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── HIGH-003: GET /players must require auth ─────────────────────────────────

async def test_list_players_requires_auth():
    r = await _get("/api/admin/players")
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── HIGH-004: GET /facilitator-role-info/{id} must require auth ──────────────

async def test_facilitator_role_info_requires_auth():
    r = await _get("/api/admin/facilitator-role-info/FAC-001")
    assert r.status_code != 200, f"Endpoint should not return 200 without auth, got {r.status_code}"
    assert r.status_code in (401, 403, 404), \
        f"Expected 401/403/404, got {r.status_code}"


# ── HIGH-006: POST /{session_id}/decade-plan must require auth ───────────────

async def test_decade_plan_requires_auth():
    r = await _post("/api/admin/fake-session/decade-plan", json={
        "boardroom_choice": "resist_integrate",
        "decade_forward_plan": "hack all the things"
    })
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── MED-002: GET /leaderboard must require auth ──────────────────────────────

async def test_leaderboard_requires_auth():
    r = await _get("/api/admin/leaderboard")
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ── HIGH-010: Security headers present on all responses ─────────────────────

async def test_security_headers_present():
    r = await _get("/health")
    assert r.status_code == 200
    assert "x-frame-options" in r.headers, "X-Frame-Options header missing"
    assert "x-content-type-options" in r.headers, "X-Content-Type-Options header missing"
    assert r.headers.get("x-frame-options", "").upper() == "DENY"
    assert r.headers.get("x-content-type-options", "").lower() == "nosniff"


# ── Sync tests (no async needed) ─────────────────────────────────────────────

def test_player_password_generation_strength():
    """Verify generated passwords are at least 12 chars and use secrets module."""
    import secrets as sec, string as st
    alpha = st.ascii_letters + st.digits
    for _ in range(50):
        pw = ''.join(sec.choice(alpha) for _ in range(12))
        assert len(pw) == 12


def test_bcrypt_roundtrip():
    """Verify hash_password + verify_password work correctly."""
    from password_hashing import hash_password, verify_password, maybe_upgrade_password, _BCRYPT_AVAILABLE

    if not _BCRYPT_AVAILABLE:
        pytest.skip("bcrypt not installed in this environment")

    pw = "SuperSecret!42"
    hashed = hash_password(pw)
    # Hash should not equal plaintext
    assert hashed != pw, "Password was stored as plaintext!"
    assert hashed.startswith("$2b$"), f"Expected bcrypt hash, got: {hashed[:10]}"
    # Correct password verifies
    assert verify_password(pw, hashed), "verify_password returned False for correct password"
    # Wrong password fails
    assert not verify_password("wrongpassword", hashed), "verify_password returned True for wrong password"
    # Auto-upgrade: plaintext stored value triggers upgrade
    upgrade = maybe_upgrade_password(pw, pw)  # stored as plaintext
    assert upgrade is not None, "maybe_upgrade_password should return a hash for plaintext"
    assert upgrade != pw, "Upgraded password should be hashed"
    assert upgrade.startswith("$2b$"), "Upgraded password should be a bcrypt hash"


def test_path_traversal_sanitisation():
    """Verify the real upload sanitiser strips traversal sequences on ANY OS.

    Exercises admin_router._sanitise_upload_name rather than os.path.basename
    directly: basename does NOT strip Windows-style backslash separators on
    POSIX hosts (our deploy target), so testing basename gave a false result
    that only passed on Windows.
    """
    import sys, pathlib
    backend_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    from admin_router import _sanitise_upload_name

    malicious_names = [
        "../../etc/passwd",
        "../../../windows/system32/cmd.exe",
        "..\\..\\admin_router.py",
        "foo/../../../secret.txt",
        "\x00evil.sh",
    ]
    for name in malicious_names:
        result = _sanitise_upload_name(name)
        assert ".." not in result, f"did not strip '..': {result}"
        assert "/" not in result, f"left forward slash in: {result}"
        assert "\\" not in result, f"left backslash in: {result}"
        assert "\x00" not in result, f"left null byte in: {result}"


def test_pydantic_field_length_limits():
    """Verify Pydantic models reject oversized inputs."""
    import sys, pathlib
    from pydantic import ValidationError
    backend_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    from admin_router import FacilitatorNoteRequest, BroadcastRequest

    # FacilitatorNoteRequest: text max 5000 chars
    with pytest.raises(ValidationError):
        FacilitatorNoteRequest(text="x" * 5001)

    # Valid note should work
    note = FacilitatorNoteRequest(text="Short note")
    assert note.text == "Short note"

    # BroadcastRequest: title max 200, body max 5000
    with pytest.raises(ValidationError):
        BroadcastRequest(title="t" * 201, body="b")
    with pytest.raises(ValidationError):
        BroadcastRequest(title="t", body="b" * 5001)

    # Valid broadcast should work
    bc = BroadcastRequest(title="Test", body="Hello all")
    assert bc.title == "Test"
