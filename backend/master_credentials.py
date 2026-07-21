"""
master_credentials.py — runtime-changeable master password.

Precedence: the God-Mode override file (bcrypt hash, survives restarts)
supersedes the MASTER_PASSWORD env/config fallback. The file never holds
plaintext. Every master-bypass comparison in the app goes through
verify_master_password(), so a change takes effect immediately for
god_mode logins, facilitator master-bypass logins, password-change
bypasses, role-change verification, and player master unlocks.
"""

from __future__ import annotations

import hmac
import json
from datetime import datetime, timezone
from pathlib import Path

from config import MASTER_PASSWORD, PLAYER_MASTER_PASSWORD
from password_hashing import hash_password, verify_password

# QA-2026-07-16 #3: moved into the shared durable data dir (MURESSONS_DATA_DIR,
# default <repo>/db). NOTE the legacy location was backend/db/ -- NOT repo db/ --
# so an existing override file is migrated across on first resolve.
from runtime_paths import data_file as _data_file
_LEGACY_OVERRIDE = Path(__file__).parent / "db" / "master_password.json"
_OVERRIDE_FILE = _data_file("master_password.json", legacy=_LEGACY_OVERRIDE)


def _load_override_hash() -> str | None:
    try:
        data = json.loads(_OVERRIDE_FILE.read_text(encoding="utf-8"))
        return data.get("hash") or None
    except Exception:
        return None


def master_override_active() -> bool:
    return _load_override_hash() is not None


def verify_master_password(candidate: str) -> bool:
    """True when `candidate` is the CURRENT master password."""
    if not candidate:
        return False
    override = _load_override_hash()
    if override:
        try:
            return verify_password(candidate, override)
        except Exception:
            return False
    return bool(MASTER_PASSWORD) and hmac.compare_digest(candidate, MASTER_PASSWORD)


def verify_player_master_password(candidate: str) -> bool:
    """P6: player master-unlock. Uses PLAYER_MASTER_PASSWORD — a secret SEPARATE
    from the admin break-glass MASTER_PASSWORD — so a leak of one credential
    cannot span both realms. Disabled (returns False) unless
    PLAYER_MASTER_PASSWORD is explicitly configured; it does NOT fall back to
    MASTER_PASSWORD."""
    if not candidate or not PLAYER_MASTER_PASSWORD:
        return False
    return hmac.compare_digest(candidate, PLAYER_MASTER_PASSWORD)


def set_master_password(new_plain: str, changed_by: str = "god_mode") -> None:
    """Persist a new master password (bcrypt hash only)."""
    _OVERRIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _OVERRIDE_FILE.write_text(
        json.dumps(
            {
                "hash": hash_password(new_plain),
                "changed_by": changed_by,
                "changed_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=1,
        ),
        encoding="utf-8",
    )


def clear_master_password_override() -> None:
    """Revert to the env/config MASTER_PASSWORD."""
    try:
        _OVERRIDE_FILE.unlink()
    except FileNotFoundError:
        pass
