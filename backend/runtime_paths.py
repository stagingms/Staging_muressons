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

Deliberately NOT routed through here: pure SEED files (seed_round1.json,
init.sql, industry configs, upload templates). Those ship in the image under
<repo>/db and must never be hidden by a volume mount — which is also why the
volume should be mounted at its own path (e.g. /data), NOT over /app/db.

TUNABLE CONFIG IS DIFFERENT — see config_file() (3.1, 2026-08-03).
simulation_config.json and decision_overrides.json are BOTH seeded AND mutable:
they ship in the image with sane defaults, and the Excel importer, the god-mode
sliders and the decision-override editor all WRITE to them at runtime. Held in
the image they behaved like the facilitator registry did before this module
existed — every tuning change a facilitator made was silently reverted by the
next redeploy, while the upload endpoint still answered {"reload":"complete"}.
They need the durable directory, but with different absent-file semantics from
data_file(); config_file() implements those.

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


# A6 (pre-class register): a FULL volume is invisible to every check we had.
# `writable` probes with a 2-byte file, which still succeeds with kilobytes
# left, so /health would report a healthy, durable volume right up to the
# moment a pack upload or a registry write fails mid-class. These thresholds
# make the last stretch observable BEFORE it bites. Percentage alone is wrong
# on a large disk (10% of 100 GB is plenty) and bytes alone are wrong on a
# small volume, so `low_space` trips on whichever is more alarming.
LOW_SPACE_PCT = 10.0            # warn under 10% free…
LOW_SPACE_BYTES = 100 * 1024 * 1024   # …or under 100 MB, whichever hits first


def disk_free(path) -> dict:
    """Free/total bytes for the filesystem holding `path`.

    Returns `{}` when the platform refuses to answer (some sandboxes and
    read-only mounts do). Callers must treat an absent reading as UNKNOWN,
    never as healthy — see `low_space` below, which stays False when we
    genuinely do not know, so this can never invent an alarm.
    """
    try:
        usage = shutil.disk_usage(str(path))
    except (OSError, ValueError):
        return {}
    pct = (usage.free / usage.total * 100.0) if usage.total else 0.0
    return {
        "free_bytes": int(usage.free),
        "total_bytes": int(usage.total),
        "free_pct": round(pct, 1),
    }


def storage_status() -> dict:
    """Durability report for the mutable-state directory.

    `durable` is the single flag deployments should alert on: True when the
    data dir is explicitly configured (MURESSONS_DATA_DIR → a mounted volume)
    AND writable, or when we're NOT on an ephemeral platform (local dev /
    docker-compose with a bind mount, where <repo>/db is fine).

    `low_space` is the second flag worth alerting on (A6): the volume can be
    configured, writable and durable and still be one upload from full."""
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

    space = disk_free(d)
    # Unknown free space is NOT low space. A missing reading must not page
    # anyone at 03:00, and must not mask a real shortage either — the absent
    # free_* keys are the signal that the probe failed.
    low_space = bool(
        space
        and (space["free_pct"] < LOW_SPACE_PCT
             or space["free_bytes"] < LOW_SPACE_BYTES)
    )

    return {
        "data_dir": str(d),
        "configured": configured,          # MURESSONS_DATA_DIR set
        "writable": writable,
        "on_railway": railway,
        # On Railway the container FS is ephemeral: durable ⇔ volume configured
        # and writable. Off Railway, <repo>/db is as durable as the host disk.
        "durable": (configured and writable) if railway else writable,
        "low_space": low_space,
        **space,
    }


def data_subdir(name: str, legacy: Path | None = None) -> Path:
    """Resolve a mutable runtime SUBDIRECTORY inside data_dir(), migrating an
    existing copy from <repo>/db/<name> once.

    DURABILITY-2026-07-30: stakeholder_db wrote uploaded stakeholder configs to
    <repo>/db/stakeholder_configs — inside the IMAGE, not the mounted volume.
    On Railway the container filesystem is ephemeral, so every stakeholder
    matrix a super-admin uploaded was silently discarded on the next deploy.
    The same class of bug this module was created to fix for the facilitator
    registry; the config DIRECTORY was simply never migrated with it.

    Directories need their own helper because data_file() migrates a single
    file. Migration is one-shot and non-destructive: files already present in
    the target win, and the legacy copy is left untouched so a rollback still
    finds it.

    `legacy` overrides where the one-time migration reads from, for state that
    never lived under <repo>/db. materiality_db keeps its JSON in backend/db —
    a second, separate in-image location — so it must name that path explicitly
    or the migration would silently find nothing and the volume would start
    empty, resetting every matrix to the shipped defaults.

    Honours MURESSONS_NO_LEGACY_MIGRATION for the same reason data_file() does
    — the test suite must not inherit the developer's real configs.
    """
    target = data_dir() / name
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return target

    if os.getenv("MURESSONS_NO_LEGACY_MIGRATION", "").strip().lower() in ("1", "true", "yes"):
        return target

    legacy_dir = legacy if legacy is not None else (_REPO_DB_DIR / name)
    try:
        if legacy_dir.is_dir() and legacy_dir.resolve() != target.resolve():
            for src in legacy_dir.glob("*.json"):
                dest = target / src.name
                if not dest.exists():
                    shutil.copy2(src, dest)
    except OSError:
        pass
    return target


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


# ── Tunable config: seeded in the image, mutated at runtime ────────────────

_REPO_ROOT   = Path(__file__).resolve().parent.parent
_BACKEND_DIR = Path(__file__).resolve().parent

# name → the VERSION-CONTROLLED copy that ships inside the image. Both are
# tracked in git, so seeding from them is deterministic and identical for every
# developer, CI run and deployment.
_CONFIG_IMAGE_DEFAULTS: dict[str, Path] = {
    "simulation_config.json":  _REPO_ROOT / "simulation_config.json",
    "decision_overrides.json": _BACKEND_DIR / "decision_overrides.json",
}


def config_file(name: str) -> Path:
    """Resolve a TUNABLE CONFIG file in the durable data dir, seeding it once
    from the copy that ships in the image.

    HOW THIS DIFFERS FROM data_file(), AND WHY IT HAS TO
    ----------------------------------------------------
    data_file() honours MURESSONS_NO_LEGACY_MIGRATION, which means "start this
    data dir EMPTY and never inherit state from elsewhere". That is exactly
    right for the facilitator registry, the rate-ban list and the memory
    snapshot: an empty registry is a clean registry, and the test suite must
    never read the developer's real accounts.

    It is exactly WRONG for config. An absent simulation_config.json does not
    mean "no configuration" — config.py falls through to a hardcoded default
    for every economic parameter in the model, so the engine keeps running and
    quietly computes different numbers. `tests/conftest.py` sets both
    MURESSONS_DATA_DIR (a temp dir) and MURESSONS_NO_LEGACY_MIGRATION=1, so
    routing CONFIG_PATH through data_file() would have made every test in the
    suite run against defaults rather than the committed configuration — the
    golden traces included, silently, with nothing failing to say so.

    So config_file() ALWAYS seeds from the in-image default when the durable
    copy is absent. There is no "clean" state to protect here: the shipped file
    IS the clean state, and it is in git.

    Writes go to the returned path, so the first runtime edit lands on the
    volume and every subsequent read sees it. If the data dir cannot be written
    (misconfigured mount), the in-image path is returned instead — read-only,
    but with the correct values, which beats an empty config every time.
    """
    default = _CONFIG_IMAGE_DEFAULTS.get(name)
    target = data_dir() / name
    if target.exists():
        return target
    if default is None or not default.exists():
        return target          # nothing to seed from; caller handles absence
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default, target)
        return target
    except OSError:
        return default         # unwritable volume — correct values, read-only
