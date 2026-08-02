"""deploy_preflight.py — say it at BOOT, not three hours into a workshop.

Every check here corresponds to a misconfiguration that has actually been hit,
and whose symptom appeared far away from its cause:

  * A rotated master_password.json shipped in the image and migrated onto the
    volume, so MASTER_PASSWORD "did not work" with no explanation anywhere.
  * MURESSONS_DATA_DIR pointed at a path with no volume behind it, so the
    facilitator registry was wiped by the next redeploy.
  * TRUSTED_PROXY_IPS left at localhost behind a PaaS edge, so every client
    shared one rate-limit bucket and one bad password 429'd the whole cohort.

These are WARNINGS, not fatals. main.py already fails hard on the two things
that make a deployment unsafe (no JWT_SECRET, insecure cookies). The checks
here describe situations that are legitimate in some deployments — a single
laptop workshop genuinely has no proxy — so refusing to boot would be wrong.
The goal is that the information exists at the moment it is cheap to act on.

Pure and side-effect free: returns findings, prints nothing. main.py decides
whether to show them, which keeps this unit-testable without capturing stdout.
"""
from __future__ import annotations

import os
from pathlib import Path

# The mutable runtime files. Mirrored by .dockerignore and pinned by
# tests/test_deploy_image_hygiene.py — add a file here and the tripwire fails
# until .dockerignore excludes it too.
RUNTIME_STATE_FILES = (
    "facilitator_registry.json",
    "memory_snapshot.json",
    "memory_snapshot.bak",
    "master_password.json",
    "token_versions.json",
    "rate_bans.json",
    "admin_audit.jsonl",
    "jwt_secret.key",
)


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("true", "1", "yes")


def check_master_password_override(data_dir: Path, legacy: Path | None = None) -> str | None:
    """The single most confusing failure mode in this codebase.

    verify_master_password() consults master_password.json FIRST and only falls
    back to the env var when absent. A file that arrived via the image (or a
    rotation performed months ago) therefore silently wins, and the operator
    sees nothing but "Invalid facilitator ID or password".
    """
    if not os.getenv("MASTER_PASSWORD", "").strip():
        return None  # nothing to conflict with
    for candidate in (data_dir / "master_password.json", legacy):
        if candidate and candidate.exists():
            return (
                f"MASTER_PASSWORD is set, but a rotated override exists at {candidate}. "
                "The override WINS — your MASTER_PASSWORD value will NOT log in. "
                "Delete that file to fall back to the environment value, or sign in "
                "with the rotated password."
            )
    return None


def check_data_dir_is_durable(data_dir: Path) -> str | None:
    """MURESSONS_DATA_DIR only helps if a volume is actually mounted there.

    Cannot detect a mount portably, so this checks the thing that is both
    observable and diagnostic: in production the directory should be OUTSIDE
    the image (a bare path like /data), and it must be writable.
    """
    configured = os.getenv("MURESSONS_DATA_DIR", "").strip()
    if _truthy("DEBUG"):
        return None
    if not configured:
        return (
            "MURESSONS_DATA_DIR is not set, so mutable state lives in the image at "
            "<repo>/db. On an ephemeral filesystem EVERY redeploy wipes the "
            "facilitator registry. Set it to a mounted volume path (e.g. /data)."
        )
    try:
        import tempfile
        p = Path(configured)
        p.mkdir(parents=True, exist_ok=True)
        # A NamedTemporaryFile cleans itself up even if this process is killed
        # mid-check. An earlier version wrote a fixed ".write_probe" and
        # unlinked it, which littered the data directory on any filesystem
        # where the write succeeds but the unlink does not.
        with tempfile.NamedTemporaryFile(dir=p, prefix=".preflight_", suffix=".tmp"):
            pass
    except OSError as exc:
        return f"MURESSONS_DATA_DIR={configured} is not writable ({exc}). State cannot persist."
    return None


def check_stale_state_in_data_dir(data_dir: Path) -> str | None:
    """State on the volume BEFORE the first request is state that came from
    somewhere else — almost always a developer's laptop via the image."""
    if _truthy("DEBUG"):
        return None
    found = [n for n in RUNTIME_STATE_FILES if (data_dir / n).exists()]
    # A registry alone is normal on a redeploy (the volume persists it). The
    # signal worth reporting is the master-password override, which should
    # never arrive by accident.
    if "master_password.json" in found:
        return (
            f"master_password.json is present in {data_dir}. If this deployment is "
            "new, it was shipped in the image — check .dockerignore. It overrides "
            "MASTER_PASSWORD."
        )
    return None


def check_proxy_trust() -> str | None:
    """Behind a PaaS edge with an untrusted proxy list, rate limiting degrades
    from per-client to per-deployment without any error."""
    if _truthy("DEBUG"):
        return None
    raw = os.getenv("TRUSTED_PROXY_IPS", "").strip()
    if not raw:
        return (
            "TRUSTED_PROXY_IPS is unset (defaults to localhost only). Behind a "
            "platform edge proxy, X-Forwarded-For is then ignored and every client "
            "shares ONE rate-limit bucket — a single mistyped password can lock out "
            "the whole cohort. Add the platform's edge range, e.g. "
            "127.0.0.1,::1,10.0.0.0/8,100.64.0.0/10"
        )
    entries = [e.strip() for e in raw.split(",") if e.strip()]
    if all(e in ("127.0.0.1", "::1", "localhost") for e in entries):
        return (
            "TRUSTED_PROXY_IPS lists only localhost. If this deployment sits behind a "
            "load balancer, proxy headers are ignored and all clients collapse into "
            "one rate-limit bucket. Add the platform's edge range (CIDR is supported)."
        )
    return None


def check_player_master_unset() -> str | None:
    """PLAYER_MASTER_PASSWORD is a skeleton key to any student account."""
    if _truthy("DEBUG"):
        return None
    if os.getenv("PLAYER_MASTER_PASSWORD", "").strip():
        return (
            "PLAYER_MASTER_PASSWORD is set in production. It unlocks ANY player "
            "account without their password. Unset it unless you are mid-recovery."
        )
    return None


def run_preflight(data_dir: Path | None = None, legacy_master: Path | None = None) -> list[str]:
    """Return every finding, worst-first. Empty list == clean."""
    if data_dir is None:
        from runtime_paths import data_dir as _dd
        data_dir = _dd()
    findings = []
    for check in (
        lambda: check_master_password_override(data_dir, legacy_master),
        lambda: check_stale_state_in_data_dir(data_dir),
        lambda: check_data_dir_is_durable(data_dir),
        lambda: check_proxy_trust(),
        lambda: check_player_master_unset(),
    ):
        try:
            result = check()
        except Exception as exc:  # a preflight must never prevent a boot
            result = f"preflight check failed to run: {exc}"
        if result:
            findings.append(result)
    return findings


def format_findings(findings: list[str]) -> str:
    if not findings:
        return "[preflight] Deployment configuration looks correct."
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║  DEPLOYMENT PREFLIGHT — review before running a workshop     ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    for i, f in enumerate(findings, 1):
        lines.append(f"  {i}. {f}")
    lines.append("")
    return "\n".join(lines)
