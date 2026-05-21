"""
Muressons — JWT Authentication Module
MED-013/014: Replace header-only + localStorage auth with signed JWT tokens
delivered via HttpOnly, Secure, SameSite=Strict cookies.

Architecture:
- Login endpoints issue a signed JWT stored in an HttpOnly cookie.
- The JWT carries: facilitator_id, role, issued-at, expires-at.
- All admin requests validate the cookie (falling back to X-Facilitator-Id
  header for backward compatibility during the migration window).
- Tokens expire after JWT_EXPIRY_HOURS and must be refreshed via /auth/refresh.

Setup:
  pip install python-jose[cryptography]
  Set JWT_SECRET env var to a strong random string (openssl rand -hex 32).
  Set JWT_EXPIRY_HOURS env var (default: 8 hours).
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
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "8"))
COOKIE_NAME: str = "mur_session"

# Warn on startup if no secret is configured
if not JWT_SECRET:
    import logging
    logging.warning(
        "[AUTH] JWT_SECRET is not set. JWT authentication is disabled — "
        "falling back to X-Facilitator-Id header. Set JWT_SECRET in production."
    )
    # Generate an ephemeral secret for this process (tokens invalidated on restart)
    JWT_SECRET = secrets.token_hex(32)


def _jwt_available() -> bool:
    return _JOSE_AVAILABLE and bool(JWT_SECRET)


def create_facilitator_token(facilitator_id: str, role: str) -> str:
    """Issue a signed JWT for a facilitator session."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is not installed. Run: pip install python-jose[cryptography]")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": facilitator_id,
        "role": role,
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


def set_session_cookie(response: Response, token: str) -> None:
    """Attach the JWT as an HttpOnly, Secure, SameSite=Strict cookie."""
    is_prod = not os.getenv("DEBUG", "false").lower() == "true"
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_prod,       # HTTPS-only in production
        samesite="strict",
        max_age=JWT_EXPIRY_HOURS * 3600,
        path="/api/admin",
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie (logout)."""
    response.delete_cookie(key=COOKIE_NAME, path="/api/admin")


def get_facilitator_from_request(request: Request) -> Optional[str]:
    """
    MED-013/014: Extract facilitator_id from:
    1. JWT cookie (preferred — HttpOnly, not accessible to JS)
    2. X-Facilitator-Id header (backward-compat fallback)

    Returns None if neither is present or valid.
    """
    # ── 1. Try JWT cookie ──────────────────────────────────────────
    cookie_token = request.cookies.get(COOKIE_NAME, "")
    if cookie_token and _jwt_available():
        try:
            payload = decode_facilitator_token(cookie_token)
            return payload.get("sub")
        except HTTPException:
            pass  # Invalid token

    # ── 2. Fallback to X-Facilitator-Id header (backward-compat) ─────
    header_val = request.headers.get("x-facilitator-id", "").strip()
    return header_val or None


