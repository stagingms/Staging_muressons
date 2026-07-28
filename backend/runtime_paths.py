"""
runtime_paths.py — durable location for MUTABLE runtime files (QA-2026-07-16 #3).

WHY THIS EXISTS
---------------
Several pieces of identity/ops state live as flat files under <repo>/db:
facilitator_registry.json (every facilitator account + bcrypt hash),
token_versions.json (session-revocation kill-switch), rate_bans.json,
admin_audit.jsonl, master_password.json (runtime master-password override),
and memory_snapshot.json (in-memory-mode game state).

On Railway the container filesystem is EPHEMERAL and the registry files are
not in git, so every redeploy silently wiped them — all facilitator accounts
created in production vanished and the emergency-fallback account activated.

THE FIX
-------
Set MURESSONS_DATA_DIR to a mounted volume (e.g. a Railway volume at /data)
and every mutable runtime file is read/written there instead. Unset, the
default is <repo>/db — byte-identical to the old behaviour, so local dev and
the test suite are unaffected.

Deliberately NOT routed through here: seed/config files (seed_round1.json,
init.sql, industry configs, upload templates). Those ship in the image under
<repo>/db and must never be hidden by a volume mount — which is also why the
volume should be mounted at its own path (e.g. /data), NOT over /app/db.

MIGRATION
---------
On first use with a fresh data dir, an existing copy of the file in <repo>/db
(or an explicit legacy path) is copied across once, so pointing an already-
running deployment at a new volume carries its current state along.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_REPO_DB_DIR = Path(__file__).resolve().parent.parent / "db"


def data_dir() -> Path:
    """The directory holding mutable runtime files. Created on demand."""
    configured = os.getenv("MURESSONS_DATA_DIR", "").strip()
    d = Path(configured) if configured else _REPO_DB_DIR
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # fall through — callers handle unwritable paths per-file
    return d


def on_railway() -> bool:
    """True when running inside a Railway deployment (their injected env)."""
    return bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))


def storage_status() -> dict:
    """Durability report for the mutable-state directory.

    `durable` is the single flag deployments should alert on: True when the
    data dir is explicitly configured (MURESSONS_DATA_DIR → a mounted volume)
    AND writable, or when we're NOT on an ephemeral platform (local dev /
    docker-compose with a bind mount, where <repo>/db is fine)."""
    configured = bool(os.getenv("MURESSONS_DATA_DIR", "").strip())
    d = data_dir()
    writable = False
    try:
        probe = d / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        writable = True
    except OSError:
        writable = False
    railway = on_railway()
    return {
        "data_dir": str(d),
        "configured": configured,          # MURESSONS_DATA_DIR set
        "writable": writable,
        "on_railway": railway,
        # On Railway the container FS is ephemeral: durable ⇔ volume configured
        # and writable. Off Railway, <repo>/db is as durable as the host disk.
        "durable": (configured and writable) if railway else writable,
    }


def data_file(name: str, legacy: Path | None = None) -> Path:
    """Resolve a mutable runtime file inside data_dir().

    If the target does not exist yet, migrate a legacy copy once — first from
    `legacy` (an old non-standard location, e.g. backend/db/master_password.json),
    then from <repo>/db/<name>. No-op when MURESSONS_DATA_DIR is unset (target
    and repo copy are then the same path).

    Set MURESSONS_NO_LEGACY_MIGRATION=1 to keep a fresh data dir FRESH — the
    file is resolved inside it and nothing is ever copied in. Two uses:

      * The test suite, which must not read (or inherit) the developer's live
        runtime state. Without this, pointing the suite at a temp dir is not
        actually isolation: the first data_file() call copies the real
        memory_snapshot.json / facilitator_registry.json / master_password.json
        straight back in, and the tests run against production data anyway.
      * Pointing an existing deployment at a NEW volume when you want it to
        start clean rather than inherit whatever shipped in the image.
    """
    target = data_dir() / name
    if os.getenv("MURESSONS_NO_LEGACY_MIGRATION", "").strip().lower() in ("1", "true", "yes"):
        return target
    if not target.exists():
        for candidate in (legacy, _REPO_DB_DIR / name):
            if candidate is None:
                continue
            try:
                if candidate.exists() and candidate.resolve() != target.resolve():
                    shutil.copy2(candidate, target)
                    break
            except OSError:
                continue
    return target
