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
  pip install python-jose[cryptography]
  Set JWT_SECRET env var to a strong random string (openssl rand -hex 32).
  Set JWT_EXPIRY_HOURS env var (default: 2 hours; use 8 for full-day workshops).
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from jose import JWTError, jwt as _jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False

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

# LOW-001: Loud startup notice when JWT_SECRET is not configured.
# In production (DEBUG != true) this logs at ERROR level so it surfaces in
# monitoring. The server still starts to avoid hard-failing running workshops,
# but all JWT sessions will be invalidated on every restart.
if not JWT_SECRET:
    import logging as _log
    _auth_logger = _log.getLogger("muressons.auth")
    _is_prod = os.getenv("DEBUG", "false").lower() != "true"
    if _is_prod:
        _auth_logger.error(
            "\n"
            "╔══════════════════════════════════════════════════╗\n"
            "║  SECURITY — JWT_SECRET is not configured!        ║\n"
            "║  • All facilitator sessions lost on restart      ║\n"
            "║  • Set JWT_SECRET env var (32 bytes minimum):    ║\n"
            "║    openssl rand -hex 32                          ║\n"
            "╚══════════════════════════════════════════════════╝"
        )
    else:
        _auth_logger.warning(
            "[AUTH] JWT_SECRET not set — ephemeral secret in use. "
            "Sessions will be lost on server restart. "
            "This is acceptable for local development only."
        )
    # Generate a per-process ephemeral secret so the rest of the auth
    # pipeline keeps working; tokens issued with it are invalidated on restart.
    JWT_SECRET = secrets.token_hex(32)


def _jwt_available() -> bool:
    return _JOSE_AVAILABLE and bool(JWT_SECRET)


def create_facilitator_token(facilitator_id: str, role: str, token_version: int = 0) -> str:
    """Issue a signed JWT for a facilitator session.

    SEC-1: ALL accounts — including god_mode — now receive a normal
    JWT_EXPIRY_HOURS TTL. The previous 100-year god_mode token meant a single
    leaked super-admin cookie was usable effectively forever. For long
    workshops set JWT_EXPIRY_HOURS=8 (or higher) in the environment.

    The token carries a `ver` (token_version) claim. Incrementing the stored
    version for an account (admin_shared.bump_token_version) invalidates every
    outstanding token for that account on the next request — the revocation
    kill-switch that god_mode in particular previously lacked.
    """
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is not installed. Run: pip install python-jose[cryptography]")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": facilitator_id,
        "role": role,
        "ver": int(token_version),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return _jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_facilitator_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    if not _JOSE_AVAILABLE:
        raise HTTPException(status_code=500, detail="JWT library not available")
    try:
        payload = _jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired session token: {exc}",
        )


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
    """
    is_prod = not os.getenv("DEBUG", "false").lower() == "true"
    cookie_max_age = JWT_EXPIRY_HOURS * 3600
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_prod,       # HTTPS-only in production
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
    if not _JOSE_AVAILABLE:
        raise HTTPException(status_code=500, detail="JWT library not available")
    try:
        payload = _jose_jwt.decode(
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




def create_player_ws_ticket(session_id: str, player_id: str = "", ttl_hours=None) -> str:
    if not _jwt_available():
        return ""
    hours = int(ttl_hours if ttl_hours is not None else JWT_EXPIRY_HOURS)
    now = datetime.now(timezone.utc)
    payload = {"sid": session_id, "pid": player_id, "typ": "ws",
               "iat": now, "exp": now + timedelta(hours=hours)}
    return _jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_player_ws_ticket(token: str, session_id: str) -> bool:
    if not token or not _jwt_available():
        return False
    try:
        payload = _jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return False
    return payload.get("typ") == "ws" and payload.get("sid") == session_id


