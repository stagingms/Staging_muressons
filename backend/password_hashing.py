"""
Muressons — Password Hashing Utility
LOW-003: Replace plaintext password storage with bcrypt hashing.

Uses the bcrypt library directly (no passlib dependency needed).
Fails hard at import time if bcrypt is not installed — the server
will not start without it, preventing silent plaintext fallback.

Migration strategy (zero-downtime):
  - New passwords are always hashed.
  - On login, if the stored value does NOT start with "$2b$" (bcrypt prefix),
    the comparison is done in plaintext and the password is re-hashed on success.
  - After all existing facilitators have logged in once, all passwords will
    be hashed automatically.
"""

from __future__ import annotations

try:
    import bcrypt as _bcrypt
    # Public flag: True when bcrypt is available.
    # The module already raises RuntimeError on import if bcrypt is missing,
    # so this constant will always be True when the module loads successfully.
    # Exported so tests can introspect availability (e.g. pytest.skip guards).
    _BCRYPT_AVAILABLE: bool = True
except ImportError:
    raise RuntimeError(
        "[AUTH] bcrypt is not installed. "
        "Run: pip install bcrypt\n"
        "The server will not start without bcrypt — plaintext password "
        "storage is not permitted."
    )


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using bcrypt (cost factor 12)."""
    pw_bytes = plaintext.encode("utf-8")
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def _is_hashed(value: str) -> bool:
    """True if value looks like a bcrypt hash."""
    return value.startswith("$2b$") or value.startswith("$2a$")


def verify_password(plaintext: str, stored: str) -> bool:
    """Verify a plaintext password against a stored value.

    Handles both:
    - Bcrypt hash: constant-time verification
    - Legacy plaintext: direct comparison (covers records created before
      bcrypt was enforced; auto-upgraded to a hash on next successful login)
    """
    if not stored:
        return False
    if _is_hashed(stored):
        try:
            return _bcrypt.checkpw(plaintext.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # Legacy plaintext — compared only during the migration window
    # H-1 security fix: use constant-time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(plaintext, stored)


def maybe_upgrade_password(plaintext: str, stored: str) -> str | None:
    """If the stored value is plaintext and login succeeded, return a new bcrypt hash.
    Returns None if the password is already hashed."""
    if _is_hashed(stored):
        return None  # Already hashed
    return hash_password(plaintext)
