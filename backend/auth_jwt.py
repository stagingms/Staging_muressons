"""
Muressons — JWT Authentication Module
MED-013/014: Replace header-only + localStorage auth with signed JWT tokens
delivered via HttpOnly, Secure, SameSite=Strict cookies.

Architecture:
- Login endpoints issue a signed JWT stored in an HttpOnly cookie.
- The JWT carries: facilitator_id, role, issued-at, expires-at.
- All admin requests validate the cookie (the X-Facilitator-Id header fallback
  was removed in C-1 — the JWT cookie is the sole trusted auth path).
- Tokens expire after JWT_EXPIRY_HOURS and must be refreshed via /auth/refresh.

Setup:
  pip install PyJWT
  Set JWT_SECRET env var to a strong random string (openssl rand -hex 32).
  Set JWT_EXPIRY_HOURS env var (default: 2 hours; use 8 for full-day workshops).
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

# F-22 (2026-08-04): PyJWT, not python-jose.
#
# python-jose drags in `ecdsa` and pins `pyasn1<0.5.0`. Between them those two
# accounted for 6 of the 16 advisories pip-audit reported, and `ecdsa` has NO
# fixed release at all — the pin meant pyasn1 could never be patched while jose
# was present. PyJWT signs HS256 through `cryptography` and needs neither.
#
# The swap is behaviour-preserving: same HS256, same secret, same claims, so
# tokens issued by the jose build stay valid and NOBODY IS LOGGED OUT by the
# upgrade. Only two API details differ, both handled below:
#   * the error base is `PyJWTError` rather than `JWTError`;
#   * PyJWT verifies `exp` by default — which is what we already wanted
#     everywhere except the god_mode recovery path, and that one passes
#     options={"verify_exp": False} exactly as before.
try:
    import jwt as _pyjwt
    from jwt import PyJWTError as _JWTError
    _JWT_LIB_AVAILABLE = True
except ImportError:
    _JWT_LIB_AVAILABLE = False

from fastapi import Cookie, HTTPException, Request, Response, status

# ── Config ─────────────────────────────────────────────────────────────────
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM: str = "HS256"
# LOW-005: Default reduced from 8 h → 2 h to limit the blast-radius of a
# stolen token.  H-4 (registry cross-check) already invalidates deactivated
# accounts on every request, so the practical impact of a shorter expiry is
# mainly for undetected credential theft.
# For workshops that run longer than 2 hours set JWT_EXPIRY_HOURS=8 (or higher)
# in your environment file before starting the server.
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "2"))
COOKIE_NAME: str = "mur_session"

# LOW-001 / BUG-2026-07-18: When JWT_SECRET is not configured, the secret used
# to be per-process ephemeral — every backend restart silently invalidated all
# facilitator cookies. The dashboard (rendered from client state) still LOOKED
# logged in, so the first symptom was a confusing guard error on the next
# privileged call (e.g. "Registry-admin access required" for god_mode).
# Fix: auto-generate ONCE and persist to the durable data dir
# (runtime_paths.data_file — same volume as facilitator_registry.json), so
# sessions survive restarts. The file is gitignored (db/*.json is not matched;
# we use a dedicated pattern) and written 0600. Setting JWT_SECRET explicitly
# still takes precedence and skips the file entirely.
if not JWT_SECRET:
    import logging as _log
    _auth_logger = _log.getLogger("muressons.auth")
    try:
        from runtime_paths import data_file as _data_file
        _secret_path = str(_data_file("jwt_secret.key"))
        try:
            with open(_secret_path, "r", encoding="utf-8") as _fh:
                _stored = _fh.read().strip()
        except FileNotFoundError:
            _stored = ""
        if len(_stored) >= 32:
            JWT_SECRET = _stored
        else:
            JWT_SECRET = secrets.token_hex(32)
            _dirname = os.path.dirname(_secret_path)
            if _dirname:
                os.makedirs(_dirname, exist_ok=True)
            _fd = os.open(_secret_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(_fd, "w", encoding="utf-8") as _fh:
                _fh.write(JWT_SECRET)
            _auth_logger.warning(
                "[AUTH] JWT_SECRET not set — generated one and persisted it to "
                f"{_secret_path} so sessions survive restarts. For production, "
                "prefer an explicit JWT_SECRET env var (openssl rand -hex 32)."
            )
    except Exception as _exc:
        # Persistence unavailable (read-only fs, etc.) — fall back to the old
        # ephemeral behaviour rather than refusing to start.
        JWT_SECRET = JWT_SECRET or secrets.token_hex(32)
        _auth_logger.error(
            "\n"
            "╔══════════════════════════════════════════════════╗\n"
            "║  SECURITY — JWT_SECRET is not configured and     ║\n"
            "║  could not be persisted (%s).                    ║\n"
            "║  • All facilitator sessions lost on restart      ║\n"
            "║  • Set JWT_SECRET env var (32 bytes minimum):    ║\n"
            "║    openssl rand -hex 32                          ║\n"
            "╚══════════════════════════════════════════════════╝" % _exc
        )


def _jwt_available() -> bool:
    return _JWT_LIB_AVAILABLE and bool(JWT_SECRET)


def create_facilitator_token(
    facilitator_id: str,
    role: str,
    token_version: int = 0,
    *,
    master_bypass: bool = False,
) -> str:
    """Issue a signed JWT for a facilitator session.

    SEC-1: ALL accounts — including god_mode — now receive a normal
    JWT_EXPIRY_HOURS TTL. The previous 100-year god_mode token meant a single
    leaked super-admin cookie was usable effectively forever. For long
    workshops set JWT_EXPIRY_HOURS=8 (or higher) in the environment.

    The token carries a `ver` (token_version) claim. Incrementing the stored
    version for an account (admin_shared.bump_token_version) invalidates every
    outstanding token for that account on the next request — the revocation
    kill-switch that god_mode in particular previously lacked.

    F-22 (launch audit 2026-09-01): `master_bypass=True` stamps an `mb` claim
    on tokens minted from a MASTER_PASSWORD login. The login response already
    suppresses `must_change_password` for those logins (admin impersonation is
    not the facilitator's first-login flow); the claim lets the server-side
    enforcement in `admin_router.get_fac_role` make the same exemption. It is
    signed, so a client cannot grant it to itself.
    """
    if not _JWT_LIB_AVAILABLE:
        raise RuntimeError("PyJWT is not installed. Run: pip install PyJWT")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": facilitator_id,
        "role": role,
        "ver": int(token_version),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    if master_bypass:
        payload["mb"] = True
    return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_facilitator_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    if not _JWT_LIB_AVAILABLE:
        raise HTTPException(status_code=500, detail="JWT library not available")
    try:
        payload = _pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except _JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired session token: {exc}",
        )


def cookie_secure_enabled() -> bool:
    """SEC-2: Resolve the session-cookie ``Secure`` flag independently of DEBUG.

    Precedence:
      1. Explicit ``COOKIE_SECURE`` env var — ``true/1/yes`` → True,
         ``false/0/no`` → False.
      2. Unset → fall back to the historical behaviour: Secure everywhere
         except local development (``DEBUG=true``).

    Rationale: previously the Secure flag was ``not DEBUG``. That coupled a
    verbose-logging switch to a transport-security control, so leaving
    ``DEBUG=true`` on a deployed box silently sent auth cookies over plaintext
    HTTP. Decoupling forces an operator to opt OUT of Secure explicitly
    (``COOKIE_SECURE=false``, e.g. for an HTTP-only LAN workshop) instead of
    getting the insecure behaviour as a side effect of DEBUG.
    """
    raw = os.getenv("COOKIE_SECURE", "").strip().lower()
    if raw in ("true", "1", "yes"):
        return True
    if raw in ("false", "0", "no"):
        return False
    return os.getenv("DEBUG", "false").lower() != "true"


def set_session_cookie(response: Response, token: str, facilitator_id: str = "") -> None:
    """Attach the JWT as an HttpOnly, Secure, SameSite=Strict cookie.

    LOW-001 / CSRF defence:
    SameSite=Strict prevents the browser from sending this cookie on any
    cross-site navigation, which is the primary CSRF defence.  This protection
    became effective once C-3 added `credentials: 'include'` to the login
    fetch, causing the browser to actually store the cookie.

    Layered defence-in-depth:
      • SameSite=Strict — blocks cross-site cookie transmission (primary)
      • HttpOnly         — blocks XSS-based token extraction
      • Secure           — cookie only sent over HTTPS in production
      • path=/api        — scope-limited; not sent to player/public routes
      • CORS allowlist   — rejects cross-origin preflight from unknown origins
    No additional CSRF token is required while SameSite=Strict is active and
    the CORS allowlist does not include attacker-controlled origins.

    SEC-1: the cookie max_age now matches JWT_EXPIRY_HOURS for ALL accounts,
    including god_mode (no more 100-year cookie).

    SEC-2: the Secure flag is resolved via cookie_secure_enabled() (COOKIE_SECURE
    env, falling back to `not DEBUG`) rather than being tied directly to DEBUG.
    A stray DEBUG=true in a deployed environment therefore no longer silently
    downgrades the auth cookie to plaintext HTTP.
    """
    is_secure = cookie_secure_enabled()
    cookie_max_age = JWT_EXPIRY_HOURS * 3600
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_secure,     # HTTPS-only unless explicitly relaxed (SEC-2)
        samesite="strict",
        max_age=cookie_max_age,
        path="/api",
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie (logout)."""
    response.delete_cookie(key=COOKIE_NAME, path="/api")


def _decode_token_ignore_expiry(token: str) -> dict:
    """Decode a JWT without checking the expiry claim.

    Used ONLY for god_mode recovery: the token signature is still fully
    verified so the god_mode identity cannot be forged.  Expiry is the only
    check relaxed, and only when the sub claim is 'god_mode'.
    """
    if not _JWT_LIB_AVAILABLE:
        raise HTTPException(status_code=500, detail="JWT library not available")
    try:
        payload = _pyjwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token (signature check failed): {exc}",
        )


def get_facilitator_from_request(request: Request) -> Optional[str]:
    """
    MED-013/014: Extract facilitator_id from the signed JWT cookie only.

    C-1 security fix: the X-Facilitator-Id header fallback has been removed.
    Accepting an un-signed header as identity proof allowed any caller to
    impersonate any facilitator (including super_admin) without credentials.
    The signed JWT cookie is the only trusted auth path for HTTP endpoints.

    SEC-1: the previous god_mode "honour expired token" special-case has been
    removed. Expired tokens are now rejected for ALL accounts, god_mode
    included. Recovery of a locked-out god_mode account is done by resetting
    its credentials/token-version out of band, not by an immortal token.

    Returns None if no valid (unexpired, correctly-signed) cookie is present.
    """
    cookie_token = request.cookies.get(COOKIE_NAME, "")
    if cookie_token and _jwt_available():
        try:
            payload = decode_facilitator_token(cookie_token)
            return payload.get("sub")
        except HTTPException:
            # Expired or invalid signature → no identity. No exceptions.
            return None
    return None



# ── Player HTTP token (F-22, launch audit 2026-09-01) ─────────────────────────
# Players used to be identified by the bare X-Player-Id header, which anyone
# holding a team's session UUID and player id could forge. Login now mints a
# signed, session-scoped bearer token; _assert_player_owns_session refuses an
# owned session unless the request carries one (or a facilitator cookie).
# Players have no refresh flow, so the TTL defaults to a full teaching day.
PLAYER_TOKEN_TTL_HOURS: int = int(os.getenv("PLAYER_TOKEN_TTL_HOURS", "12"))
PLAYER_TOKEN_HEADER = "X-Player-Token"


def create_player_token(session_id: str, player_id: str, *, observer: bool = False,
                        ttl_hours: int | None = None) -> str:
    """Signed bearer token binding a player (or team observer) to ONE session."""
    if not _jwt_available():
        return ""
    hours = int(ttl_hours if ttl_hours is not None else max(PLAYER_TOKEN_TTL_HOURS, JWT_EXPIRY_HOURS))
    now = datetime.now(timezone.utc)
    payload = {"sid": str(session_id), "pid": str(player_id or ""), "typ": "player",
               "obs": bool(observer), "iat": now, "exp": now + timedelta(hours=hours)}
    return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_player_token(token: str) -> Optional[dict]:
    """Return {"session_id", "player_id", "observer"} for a valid player token, else None."""
    if not token or not _jwt_available():
        return None
    try:
        payload = _pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
    if payload.get("typ") != "player":
        return None
    return {"session_id": str(payload.get("sid") or ""), "player_id": str(payload.get("pid") or ""),
            "observer": bool(payload.get("obs", False))}


def get_player_from_request(request: Request) -> Optional[dict]:
    """Player identity from `Authorization: Bearer <token>` or X-Player-Token."""
    raw = ""
    auth = request.headers.get("Authorization", "") or ""
    if auth.lower().startswith("bearer "):
        raw = auth[7:].strip()
    if not raw:
        raw = (request.headers.get(PLAYER_TOKEN_HEADER, "") or "").strip()
    return verify_player_token(raw) if raw else None


def create_player_ws_ticket(session_id: str, player_id: str = "", ttl_hours=None) -> str:
    if not _jwt_available():
        return ""
    hours = int(ttl_hours if ttl_hours is not None else JWT_EXPIRY_HOURS)
    now = datetime.now(timezone.utc)
    payload = {"sid": session_id, "pid": player_id, "typ": "ws",
               "iat": now, "exp": now + timedelta(hours=hours)}
    return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_player_ws_ticket(token: str, session_id: str) -> bool:
    if not token or not _jwt_available():
        return False
    try:
        payload = _pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return False
    return payload.get("typ") == "ws" and payload.get("sid") == session_id
