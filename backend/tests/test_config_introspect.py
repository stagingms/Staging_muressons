"""config_introspect — "what is the engine ACTUALLY running right now?"

WHY THIS MODULE EXISTS AT ALL
    Muressons has three tuning surfaces (Excel importer, god-mode sliders, edit
    the JSON + redeploy) and they fail in three different ways. Until this
    endpoint, "did my change take effect?" could only be answered by changing a
    parameter and watching the numbers move — and the engine's non-determinism
    makes that observation unreliable. So a knob that silently did nothing was
    indistinguishable from a knob that did something small.

WHAT THESE TESTS PIN
    1. The report never raises, whatever state the process is in. It is read by
       an admin page; an introspection bug must not take that page down.
    2. Secrets are never returned, even though the route is super-admin only.
    3. The stale-binding detector actually detects. This is the load-bearing
       test: `from config import X` binds a VALUE, so importlib.reload(config)
       leaves consumers on the old number while the upload reports success.
       Test 3 simulates exactly that and asserts we catch it.
    4. The fingerprint is stable across calls and moves when a value moves —
       the property that makes it worth stamping on a run (#27).
    5. The route is super-admin guarded.
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import config  # noqa: E402
import config_introspect as ci  # noqa: E402
import round_logic  # noqa: E402  (a consumer that does `from config import ...`)


# ── 1. Shape and robustness ──────────────────────────────────────────────────

def test_report_is_well_formed_and_does_not_raise():
    r = ci.live_config_report()
    for key in ("fingerprint", "constant_count", "healthy", "problems",
                "summary", "file_vs_process", "stale_bindings",
                "god_mode_shadowing", "inert_tunables"):
        assert key in r, f"missing {key}"
    assert r["constant_count"] > 50, "config surface looks implausibly small"
    assert isinstance(r["problems"], list)
    assert r.get("check_errors") is None, f"a check blew up: {r.get('check_errors')}"


def test_values_can_be_omitted():
    assert "constants" not in ci.live_config_report(include_values=False)
    assert "constants" in ci.live_config_report(include_values=True)


# ── 2. Redaction ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "MASTER_PASSWORD", "JWT_SECRET", "DATABASE_URL", "LLM_API_KEY",
    "PROJECT_ADMIN_PASSWORD", "PLAYER_MASTER_PASSWORD",
])
def test_secretish_names_are_redacted(name):
    assert ci._is_secret(name), f"{name} must be treated as a secret"


def test_no_secret_value_appears_in_the_report():
    constants = ci.live_config_report()["constants"]
    for name, value in constants.items():
        if ci._is_secret(name):
            assert value == "«redacted»", f"{name} leaked into the report"


# ── 3. The load-bearing test: stale bindings ─────────────────────────────────

def test_stale_binding_detector_catches_a_partial_hot_reload():
    """Reproduce the Excel-upload failure mode exactly.

    admin_router's config upload calls importlib.reload(config), which rebinds
    names inside config's namespace. Modules that did `from config import X`
    keep the OLD value, so the process runs a mixture — and the endpoint returns
    {"reload": "complete"}. Nothing else in the system can see this.
    """
    original = config.SIM_ROUNDS
    assert round_logic.SIM_ROUNDS == original, "fixture assumption broken"
    try:
        config.SIM_ROUNDS = original + 2          # what a reload does
        found = ci.check_stale_bindings(config)   # round_logic still holds the old value
        assert any(f["module"] == "round_logic" and f["constant"] == "SIM_ROUNDS"
                   for f in found), (
            "the stale-binding detector missed a mixed-config process — this is "
            "the whole reason the module exists"
        )
        problems = ci.live_config_report()["problems"]
        assert any(p["kind"] == "stale_binding" for p in problems)
        assert ci.live_config_report()["healthy"] is False
    finally:
        config.SIM_ROUNDS = original

    assert not any(f["constant"] == "SIM_ROUNDS" for f in ci.check_stale_bindings(config))


def test_a_clean_process_reports_no_stale_bindings():
    """At boot, before any hot-reload, every consumer agrees with config."""
    assert ci.check_stale_bindings(config) == []


# ── 4. Fingerprint ───────────────────────────────────────────────────────────

def test_fingerprint_is_stable_and_sensitive():
    first = ci.live_config_report(include_values=False)["fingerprint"]
    assert first == ci.live_config_report(include_values=False)["fingerprint"]

    original = config.SIM_ROUNDS
    try:
        config.SIM_ROUNDS = original + 1
        assert ci.live_config_report(include_values=False)["fingerprint"] != first
    finally:
        config.SIM_ROUNDS = original
    assert ci.live_config_report(include_values=False)["fingerprint"] == first


# ── 5. file-vs-process ───────────────────────────────────────────────────────

def test_file_ahead_of_process_is_detected():
    """An upload (or a hand edit) that the process has not picked up."""
    loaded = config.SIMULATION_CONFIG
    try:
        # Pretend the process loaded something different from what is on disk.
        config.SIMULATION_CONFIG = {"simulation_settings": {"rounds": 99}}
        state = ci.check_file_ahead_of_process(config)
        assert state["status"] in ("file_ahead_of_process", "missing", "unreadable")
        if state["status"] == "file_ahead_of_process":
            assert state["differing_count"] > 0
            assert "NOT IN EFFECT" in state["message"]
    finally:
        config.SIMULATION_CONFIG = loaded

    assert ci.check_file_ahead_of_process(config)["status"] in ("in_sync", "missing")


# ── 6. The route is guarded ──────────────────────────────────────────────────

def test_route_requires_super_admin():
    route = next(
        r for r in ci.config_introspect_router.routes
        if getattr(r, "path", None) == "/api/admin/config/live"
    )
    dep_names = [
        getattr(d.call, "__name__", "")
        for d in route.dependant.dependencies
    ]
    assert "require_super_admin" in dep_names, (
        "config/live enumerates every engine constant — it must stay super-admin only"
    )
