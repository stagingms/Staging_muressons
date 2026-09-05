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


# ── 7. CFG-02/03 (audit 2026-09-04, WP-20): clamps, image vs volume, honesty ─

def test_pristine_install_is_healthy_and_inert_tunables_are_advisories():
    """CFG-03: 16 inert god-mode tunables are true of a pristine install. Listed
    as problems they kept `healthy` false forever, so the panel's warning was
    permanently on and a real problem read like the noise."""
    r = ci.live_config_report(include_values=False)
    assert r["clamped_values"] == [], "the committed config must not trip a clamp"
    assert r["image_vs_volume"]["status"] in ("in_sync", "same_file"), r["image_vs_volume"]
    assert r["healthy"] is True
    assert all(p["kind"] != "inert_tunable" for p in r["problems"])
    assert any(a["kind"] == "inert_tunable" for a in r["advisories"])
    assert "no value was clamped" in r["summary"]


def test_a_clamp_is_a_high_severity_problem(monkeypatch):
    monkeypatch.setattr(config, "CONFIG_CLAMPS", [
        {"key": "engine_parameters.regulatory_ratchet.baseline", "configured": 10.0, "using": 20.0,
         "reason": "is at or below the pre-F-10 value 10.0 (seed teams are fined in round 1)"},
    ], raising=False)
    r = ci.live_config_report(include_values=False)
    assert r["healthy"] is False
    clamp = next(p for p in r["problems"] if p["kind"] == "clamped_value")
    assert clamp["severity"] == "high"
    assert clamp["key"] == "engine_parameters.regulatory_ratchet.baseline"
    assert clamp["configured"] == 10.0 and clamp["using"] == 20.0
    assert "NOT what the engine uses" in clamp["message"]


def test_volume_drift_from_the_image_is_reported_with_its_keys(monkeypatch):
    """A volume seeded by an earlier build keeps its values forever — even the
    ones no clamp guards (e.g. terminal_valuation.shares_outstanding)."""
    import copy
    drifted = copy.deepcopy(config.SIMULATION_CONFIG)
    drifted.setdefault("terminal_valuation", {})["shares_outstanding"] = 100_000_000
    drifted.setdefault("engine_parameters", {}).setdefault("regulatory_ratchet", {})["baseline"] = 15.0
    monkeypatch.setattr(config, "SIMULATION_CONFIG", drifted)
    # make the volume path distinct from the image so the diff is not "same_file"
    monkeypatch.setattr(config, "CONFIG_PATH", Path("/data/simulation_config.json"), raising=False)
    state = ci.check_image_vs_volume(config)
    assert state["status"] == "differs", state
    keys = {d["key"] for d in state["differences"]}
    assert keys == {"terminal_valuation.shares_outstanding", "engine_parameters.regulatory_ratchet.baseline"}
    r = ci.live_config_report(include_values=False)
    prob = next(p for p in r["problems"] if p["kind"] == "image_vs_volume")
    assert prob["severity"] == "medium" and set(prob["keys"]) == keys
    assert r["healthy"] is False


def test_stale_volume_end_to_end_in_a_fresh_process(tmp_path):
    """The real thing: a data volume carrying pre-F-10 values, loaded by a
    fresh interpreter — config.py clamps, the ledger fills, /config/live
    reports it as high-severity, `healthy` is false. The audit's probe
    (cfg/probe_config_live.py case b) found `in_sync`, 0 stale bindings and
    healthy:false for the WRONG reason (inert tunables) on exactly this volume."""
    import json
    import subprocess
    image = json.loads((_BACKEND_DIR.parent / "simulation_config.json").read_text(encoding="utf-8"))
    stale = json.loads(json.dumps(image))
    stale["engine_parameters"]["regulatory_ratchet"]["baseline"] = 10.0
    stale["engine_parameters"]["imitation_decay"]["default_rate"] = 0.1
    (tmp_path / "simulation_config.json").write_text(json.dumps(stale), encoding="utf-8")
    env = {**os.environ, "MURESSONS_DATA_DIR": str(tmp_path), "USE_MEMORY_DB": "true",
           "MURESSONS_NO_LEGACY_MIGRATION": "1", "PYTHONPATH": str(_BACKEND_DIR)}
    code = (
        "import json, config, config_introspect as ci\n"
        "r = ci.live_config_report(include_values=True)\n"
        "print('JSON' + json.dumps({'clamps': config.CONFIG_CLAMPS, 'healthy': r['healthy'],"
        " 'problems': [(p['severity'], p['kind'], p.get('key')) for p in r['problems']],"
        " 'ivv': r['image_vs_volume']['status'], 'live_baseline': r['constants']['REG_RATCHET_BASELINE'],"
        " 'live_imit': r['constants']['DEFAULT_IMITATION_DECAY_RATE']}))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                         timeout=120, cwd=str(_BACKEND_DIR))
    line = next((l for l in out.stdout.splitlines() if l.startswith("JSON")), None)
    assert line, f"no report line:\nSTDOUT:{out.stdout[-1500:]}\nSTDERR:{out.stderr[-1500:]}"
    rep = json.loads(line[4:])
    assert [c["key"] for c in rep["clamps"]] == [
        "engine_parameters.regulatory_ratchet.baseline", "engine_parameters.imitation_decay.default_rate"]
    assert rep["live_baseline"] == 20.0 and rep["live_imit"] == 0.05
    assert rep["healthy"] is False and rep["ivv"] == "differs"
    kinds = [(s, k) for s, k, _ in rep["problems"]]
    assert kinds.count(("high", "clamped_value")) == 2
    assert ("medium", "image_vs_volume") in kinds
    assert all(k != "inert_tunable" for _, k in kinds)
    # and the deploy log line the runbook tells the operator to look for
    assert "[CONFIG] WARNING: engine_parameters.regulatory_ratchet.baseline=10.0" in out.stdout


def test_file_ahead_message_no_longer_claims_the_file_lives_in_the_image():
    """CFG-09/CFG-03: the upload lands on the data volume (admin_router writes
    to runtime_paths.config_file) and survives a redeploy; the old sentence
    said the opposite."""
    import inspect
    src = inspect.getsource(ci.check_file_ahead_of_process)
    assert "lives in the image" not in src
    assert "data volume" in src
