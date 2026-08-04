"""config_introspect.py — "what is the engine ACTUALLY running right now?"

WHY THIS EXISTS
    Muressons has three tuning surfaces and they fail in three different ways:

      1. Excel importer  -> writes simulation_config.json into the IMAGE, so any
         later redeploy silently reverts it; and its hot-reload only reloads 5
         modules, leaving every `from config import X` consumer bound to the OLD
         value. It reports {"reload": "complete"} either way.
      2. God-mode sliders -> _engine_tunables forwards only 2 of its 24 values;
         the rest are write-only and the endpoint still returns {"changed": ...}.
      3. Edit the JSON + redeploy -> the only path that fully works.

    So "did my change take effect?" has, until now, been answerable only by
    changing a parameter and watching the numbers move — which is exactly the
    observation the engine's non-determinism makes unreliable.

    This module answers it directly, by reading the values the RUNNING PROCESS
    is actually using, not by re-reading the file.

WHAT IT CHECKS (in order of how often it will save you)
    A. file_ahead_of_process  simulation_config.json on disk differs from what
                              this process loaded at import -> your edit/upload
                              has NOT taken effect; restart or redeploy.
    B. stale_binding          a consumer module's copy of a constant differs
                              from config's -> a partial hot-reload left this
                              process running a MIXTURE of old and new values.
                              This is the one that is invisible by every other
                              means.
    C. shadowed_by_god_mode   a runtime override wins over the config constant,
                              so the configured value is dead.
    D. inert_tunable          an _engine_tunables knob that reaches nothing.

    Plus a fingerprint over the live values, so a run can be stamped with the
    configuration that produced it.

DESIGN NOTES
    * Read-only. Imports nothing at module scope that isn't already loaded, does
      no I/O except one read of simulation_config.json, and never mutates state.
    * Nothing is hardcoded per-constant. Checks B and C are derived by
      introspection, so a constant added tomorrow is covered without edits here.
    * Secrets are redacted by name pattern before anything is returned.
    * Every check is individually wrapped: an introspection bug must never be
      able to take down an admin page.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Never return the value of anything whose name looks like a credential, even
# though this endpoint is super-admin only. Defence in depth: this module's
# whole job is to print configuration, so the redaction list is the safety rail.
_SECRET_TOKENS = (
    "SECRET", "PASSWORD", "TOKEN", "KEY", "CREDENTIAL", "DSN",
    "DATABASE_URL", "API_KEY", "SALT", "PRIVATE",
)

_SCALAR = (int, float, str, bool)


def _is_secret(name: str) -> bool:
    upper = name.upper()
    return any(tok in upper for tok in _SECRET_TOKENS)


def _redact(name: str, value: Any) -> Any:
    return "«redacted»" if _is_secret(name) else value


def _public_constants(config_mod) -> dict[str, Any]:
    """Every UPPER_CASE scalar on the config module — the engine's tunable surface."""
    out = {}
    for name in dir(config_mod):
        if not name.isupper() or name.startswith("_"):
            continue
        try:
            value = getattr(config_mod, name)
        except Exception:
            continue
        if isinstance(value, _SCALAR):
            out[name] = value
    return out


def _backend_modules():
    """Loaded modules that live in this backend package (skip stdlib / site-packages)."""
    backend_dir = str(Path(__file__).resolve().parent)
    for mod_name, mod in list(sys.modules.items()):
        if mod is None or mod_name in ("config", "config_introspect"):
            continue
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        try:
            if str(Path(f).resolve().parent) == backend_dir:
                yield mod_name, mod
        except Exception:
            continue


# ── A. Is the file on disk ahead of the process? ─────────────────────────────

def check_file_ahead_of_process(config_mod) -> dict:
    """The single most useful answer: did my edit/upload actually take effect?"""
    path = getattr(config_mod, "CONFIG_PATH", None)
    loaded = getattr(config_mod, "SIMULATION_CONFIG", None)
    if path is None or loaded is None:
        return {"status": "unknown", "reason": "config module has no CONFIG_PATH/SIMULATION_CONFIG"}
    path = Path(path)
    if not path.exists():
        return {
            "status": "missing",
            "path": str(path),
            "message": (
                "simulation_config.json does not exist. EVERY economic parameter is "
                "silently running on its hardcoded default (config.py catches the load "
                "error and leaves SIMULATION_CONFIG empty)."
            ),
        }
    try:
        on_disk = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": "unreadable",
            "path": str(path),
            "message": (
                f"simulation_config.json cannot be parsed ({exc}). If this process "
                "restarts now, every economic parameter reverts to its hardcoded default."
            ),
        }
    if on_disk == loaded:
        return {"status": "in_sync", "path": str(path)}

    def _leaves(d, prefix=""):
        out = {}
        for k, v in (d or {}).items():
            key = f"{prefix}{k}"
            if isinstance(v, dict):
                out.update(_leaves(v, key + "."))
            else:
                out[key] = v
        return out

    disk_leaves, proc_leaves = _leaves(on_disk), _leaves(loaded)
    differing = sorted(
        set(disk_leaves) | set(proc_leaves),
        key=str,
    )
    diffs = [
        {"key": k, "in_file": disk_leaves.get(k, "«absent»"), "in_process": proc_leaves.get(k, "«absent»")}
        for k in differing
        if disk_leaves.get(k, "«absent»") != proc_leaves.get(k, "«absent»")
    ]
    return {
        "status": "file_ahead_of_process",
        "path": str(path),
        "differing_count": len(diffs),
        "differences": diffs[:100],
        "message": (
            f"simulation_config.json on disk differs from what this process loaded "
            f"({len(diffs)} value(s)). THESE CHANGES ARE NOT IN EFFECT. Restart the "
            "backend (or redeploy) to pick them up. Note that on Railway the file "
            "lives in the image, so an uploaded config is also lost on the next "
            "redeploy — see remediation #37."
        ),
    }


# ── B. Stale consumer bindings (the partial hot-reload detector) ─────────────

def check_stale_bindings(config_mod) -> list[dict]:
    """`from config import X` binds a VALUE, not a reference.

    importlib.reload(config) rebinds the name inside config's namespace only, so
    every module that imported the constant by value keeps the old one. That is
    how an upload can report success while the engine runs the previous number.
    """
    findings = []
    constants = _public_constants(config_mod)
    for mod_name, mod in _backend_modules():
        for name, config_value in constants.items():
            if not hasattr(mod, name):
                continue
            try:
                mod_value = getattr(mod, name)
            except Exception:
                continue
            if not isinstance(mod_value, _SCALAR):
                continue
            if mod_value != config_value:
                findings.append({
                    "constant": name,
                    "module": mod_name,
                    "module_value": _redact(name, mod_value),
                    "config_value": _redact(name, config_value),
                    "message": (
                        f"{mod_name}.{name} is stale: it holds {mod_value!r} while "
                        f"config.{name} is {config_value!r}. This process is running a "
                        "MIXTURE of old and new configuration — a partial hot-reload. "
                        "Restart the backend to converge."
                    ),
                })
    return sorted(findings, key=lambda f: (f["constant"], f["module"]))


# ── C. Runtime overrides that beat the configured value ──────────────────────

def check_god_mode_shadowing(config_mod) -> list[dict]:
    """_god_mode_settings values that the engine reads INSTEAD of the constant.

    Matched by name: OVERRUN_DEFAULT_PROBABILITY <-> overrun_probability, etc.
    Derived rather than hardcoded so a new override is caught automatically.
    """
    try:
        from admin_shared import _god_mode_settings
    except Exception:
        return []
    constants = _public_constants(config_mod)
    norm_const = {n.lower().replace("default_", "").replace("_", ""): n for n in constants}
    findings = []
    for key, override in (_god_mode_settings or {}).items():
        if not isinstance(override, _SCALAR):
            continue
        const_name = norm_const.get(str(key).lower().replace("_", ""))
        if not const_name:
            continue
        configured = constants[const_name]
        findings.append({
            "override_key": key,
            "constant": const_name,
            "live_value": _redact(key, override),
            "configured_value": _redact(const_name, configured),
            "differs": override != configured,
            "message": (
                f"_god_mode_settings['{key}'] = {override!r} is what the engine reads; "
                f"config.{const_name} = {configured!r} is dead at runtime. This override "
                "is process-global (shared by every concurrent cohort), is read MID-TICK, "
                "and is not recorded in any run's history."
            ),
        })
    return sorted(findings, key=lambda f: f["override_key"])


# ── D. Knobs that reach nothing ──────────────────────────────────────────────

def check_inert_tunables() -> list[dict]:
    """_engine_tunables keys with no downstream consumer.

    Heuristic, and labelled as one: a key is reported inert when it is neither
    forwarded to _god_mode_settings nor present as a config constant. As of
    2026-08 that is 22 of 24 (only overrun_probability / overrun_severity are
    forwarded), which is why the god-mode sliders mostly do nothing.
    """
    try:
        from admin_router import _engine_tunables
    except Exception:
        return []
    try:
        from admin_shared import _god_mode_settings
    except Exception:
        _god_mode_settings = {}
    try:
        import config as _cfg
        const_norm = {n.lower().replace("_", "") for n in _public_constants(_cfg)}
    except Exception:
        const_norm = set()

    findings = []
    for key, value in (_engine_tunables or {}).items():
        norm = str(key).lower().replace("_", "")
        forwarded = key in (_god_mode_settings or {})
        has_constant = norm in const_norm or ("default" + norm) in const_norm
        if not forwarded and not has_constant:
            findings.append({
                "tunable": key,
                "value": value,
                "message": (
                    f"_engine_tunables['{key}'] is not forwarded to _god_mode_settings "
                    "and has no matching config constant. Editing it in the god-mode "
                    "panel returns success and changes nothing. (Heuristic — confirm "
                    "with a grep before deleting.)"
                ),
            })
    return findings


# ── Assembly ─────────────────────────────────────────────────────────────────

def _fingerprint(constants: dict[str, Any]) -> str:
    """Stable hash over the LIVE values. Stamp this on a run (#27) and a future
    reader can tell whether the configuration has moved since."""
    payload = json.dumps(
        {k: v for k, v in sorted(constants.items()) if not _is_secret(k)},
        sort_keys=True, default=str,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def live_config_report(include_values: bool = True) -> dict:
    """The whole picture. Never raises: every check is individually guarded."""
    import config as config_mod

    constants = _public_constants(config_mod)
    report: dict[str, Any] = {
        "fingerprint": _fingerprint(constants),
        "constant_count": len(constants),
    }

    def _run(name, fn, default):
        try:
            return fn()
        except Exception as exc:  # pragma: no cover - defensive
            report.setdefault("check_errors", []).append(f"{name}: {exc}")
            return default

    file_state = _run("file_vs_process", lambda: check_file_ahead_of_process(config_mod),
                      {"status": "unknown"})
    stale = _run("stale_bindings", lambda: check_stale_bindings(config_mod), [])
    shadowed = _run("god_mode_shadowing", lambda: check_god_mode_shadowing(config_mod), [])
    inert = _run("inert_tunables", check_inert_tunables, [])

    report["file_vs_process"] = file_state
    report["stale_bindings"] = stale
    report["god_mode_shadowing"] = shadowed
    report["inert_tunables"] = inert

    problems = []
    if file_state.get("status") not in ("in_sync", "unknown"):
        problems.append({"severity": "high", "kind": file_state["status"],
                         "message": file_state.get("message", "")})
    for f in stale:
        problems.append({"severity": "high", "kind": "stale_binding", "message": f["message"]})
    for f in shadowed:
        if f["differs"]:
            problems.append({"severity": "medium", "kind": "shadowed_by_god_mode",
                             "message": f["message"]})
    for f in inert:
        problems.append({"severity": "low", "kind": "inert_tunable", "message": f["message"]})

    report["healthy"] = not problems
    report["problems"] = problems
    report["summary"] = (
        "Configuration is coherent: the file, this process and every consumer module agree."
        if not problems else
        f"{len(problems)} configuration problem(s). The engine is NOT necessarily running "
        "the values you last set — see 'problems'."
    )
    if include_values:
        report["constants"] = {k: _redact(k, v) for k, v in sorted(constants.items())}
    return report


# ── HTTP surface ─────────────────────────────────────────────────────────────
# Sub-router, following the ARCH-002 pattern used by admin_teleprompter /
# admin_resources / admin_analytics / admin_god_controls. main.py mounts this
# AFTER admin_router, so the guard import below cannot cycle.

from fastapi import APIRouter, Depends  # noqa: E402
from admin_router import require_super_admin  # noqa: E402

config_introspect_router = APIRouter(prefix="/api/admin", tags=["Admin — Config"])


@config_introspect_router.get(
    "/config/live",
    summary="What configuration is this process ACTUALLY running?",
)
async def get_live_config(
    values: bool = True,
    _guard: None = Depends(require_super_admin),
):
    """Super-admin only: reports engine constants and, more importantly, every
    way the running process disagrees with what you think you configured.

    Read `problems` first — it is empty when the file, the process and every
    consumer module agree. `fingerprint` is a stable hash of the live values,
    suitable for stamping onto a run so a future reader can tell whether the
    configuration has moved since.
    """
    return live_config_report(include_values=values)


def run_provenance(stochastic_seed: str = "") -> dict:
    """What a completed run needs to carry to be reconstructible (4.7).

    A result is only defensible if you can say what produced it. Three things
    decide the numbers a cohort sees:

        the SEED       — which stochastic events were dealt (4.2)
        the CONFIG     — the tunable constants in force at the time
        the CODE       — the engine that combined them

    Until now a finished session recorded none of them. Two cohorts run a month
    apart, with a config change in between, were indistinguishable in the
    database: same shape, same fields, silently different rules. Nobody could
    tell you which one had been graded under which regime, and no amount of
    later analysis could recover it — the information was never written down.

    Stamped at creation because that is when it is true. Stamping at the END
    would record the config as it stood after any mid-run edits, which is
    precisely the case a reader would want flagged.

    Never raises: provenance is evidence, not control flow. A run must not fail
    to start because a fingerprint could not be computed — it records
    "unavailable" and carries on, which is still more than it recorded before.
    """
    import os
    import subprocess
    from datetime import datetime, timezone

    prov: dict[str, Any] = {
        "schema": 1,
        "stamped_at_utc": datetime.now(timezone.utc).isoformat(),
        "stochastic_seed": stochastic_seed or "",
    }

    try:
        import config as config_mod
        prov["config_fingerprint"] = _fingerprint(_public_constants(config_mod))
    except Exception as exc:            # noqa: BLE001
        prov["config_fingerprint"] = "unavailable"
        prov["config_fingerprint_error"] = str(exc)[:200]

    # Code version: the deploy stamps it, or git knows, or we admit we do not.
    code_version = (os.getenv("RAILWAY_GIT_COMMIT_SHA")
                    or os.getenv("GIT_COMMIT_SHA")
                    or os.getenv("SOURCE_VERSION") or "")
    if not code_version:
        try:
            code_version = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=2,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            ).stdout.strip()
        except Exception:               # noqa: BLE001
            code_version = ""
    prov["code_version"] = code_version or "unknown"

    return prov
