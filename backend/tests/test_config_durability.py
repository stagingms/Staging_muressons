"""3.1 — tunable config lives on the volume, and still has values when it doesn't.

WHAT THIS PINS
    `simulation_config.json` and `decision_overrides.json` are the two files a
    facilitator actually edits between runs — through the Excel importer, the
    god-mode sliders, or the decision-override editor. Until 3.1 they lived in
    the container IMAGE. On Railway that filesystem is ephemeral, so every
    tuning change survived until the next deploy and then reverted, while the
    upload endpoint went on answering {"reload": "complete"}.

    The failure mode that makes this worth a test file of its own is the FIX's
    failure mode, not the bug's. Routing config through the ordinary
    `data_file()` helper would have looked correct and been much worse: the
    test suite sets MURESSONS_DATA_DIR to a temp dir AND
    MURESSONS_NO_LEGACY_MIGRATION=1, so the file would resolve to a path that
    does not exist, config.py would fall through to a hardcoded default for
    every economic parameter, and the entire suite — golden traces included —
    would have quietly started measuring a different simulation. Nothing would
    have failed to tell us.

    So the property under test is not "the path moved". It is: THE VALUES NEVER
    DISAPPEAR, on any of the three deployments this code runs in.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
_REPO_ROOT = _BACKEND_DIR.parent

import runtime_paths  # noqa: E402


@pytest.fixture
def config_loaded_under(monkeypatch):
    """Reload config + config_excel with a chosen data dir, then put them back.

    Needed because CONFIG_PATH and JSON_PATH are import-time constants, and two
    existing modules (test_effective_settings_parent_walk.py:31 and
    test_extended_horizon.py:32) assign os.environ["MURESSONS_DATA_DIR"]
    DIRECTLY at import and never restore it. Whichever of those imports first
    wins for the rest of the process, so any assertion comparing an import-time
    path against the live data dir is order-dependent through no fault of its
    own — the same shape of defect as the shared cookie jar in conftest.py.

    Rather than assert against a moving environment, this pins one and reloads.
    Teardown restores the original value AND reloads again, so this fixture
    does not itself become the next module that leaks.
    """
    import importlib
    import config as _config
    import config_excel as _config_excel

    original = os.environ.get("MURESSONS_DATA_DIR")

    def _load(data_dir):
        monkeypatch.setenv("MURESSONS_DATA_DIR", str(data_dir))
        return importlib.reload(_config), importlib.reload(_config_excel)

    yield _load

    if original is None:
        os.environ.pop("MURESSONS_DATA_DIR", None)
    else:
        os.environ["MURESSONS_DATA_DIR"] = original
    importlib.reload(_config)
    importlib.reload(_config_excel)


# ── 1. The values survive, which is the whole point ────────────────────────

def test_the_committed_config_is_still_what_the_engine_reads():
    """The regression that would have been invisible. If this fails, every
    economic constant has silently fallen back to its hardcoded default."""
    import config
    shipped = json.loads((_REPO_ROOT / "simulation_config.json").read_text(encoding="utf-8"))
    assert config.SIMULATION_CONFIG, (
        "SIMULATION_CONFIG is empty — config.py found no file and every "
        "parameter is now a hardcoded default. This is the exact silent "
        "failure 3.1's design note warns about."
    )
    assert config.SIMULATION_CONFIG == shipped, (
        "the loaded configuration differs from the committed one"
    )


def test_a_named_constant_matches_the_committed_file():
    """Belt and braces: SIMULATION_CONFIG could match while a typed constant
    was computed from something else."""
    import config
    shipped = json.loads((_REPO_ROOT / "simulation_config.json").read_text(encoding="utf-8"))
    rounds = shipped.get("simulation_settings", {}).get("rounds")
    if rounds is not None:
        assert config.SIM_ROUNDS == int(rounds)


# ── 2. It resolves into the durable directory ──────────────────────────────

def test_config_resolves_inside_the_data_dir(tmp_path, config_loaded_under):
    """The actual 3.1 change: with a volume configured, config lives ON it and
    not in the image, so a redeploy cannot revert a facilitator's tuning."""
    cfg, _ = config_loaded_under(tmp_path)
    assert Path(cfg.CONFIG_PATH).parent.resolve() == tmp_path.resolve()
    assert _REPO_ROOT.resolve() not in Path(cfg.CONFIG_PATH).resolve().parents, (
        "config still resolves inside the image — a redeploy would revert it"
    )
    assert cfg.SIMULATION_CONFIG, "seeded path loaded an empty configuration"


def test_every_consumer_agrees_on_one_path():
    """Four modules resolve decision_overrides.json independently. If they ever
    disagree, a saved override is written to one file and read from another —
    which reads to the facilitator as 'the setting did not save'."""
    import round_configs, pillar_configs, healthcare_configs
    paths = {
        "round_configs": Path(round_configs.OVERRIDES_FILE).resolve(),
        "pillar_configs": Path(pillar_configs.OVERRIDES_FILE).resolve(),
        "healthcare_configs": Path(healthcare_configs.OVERRIDES_FILE).resolve(),
    }
    assert len(set(paths.values())) == 1, f"consumers disagree: {paths}"


def test_the_importer_writes_where_config_reads(tmp_path, config_loaded_under):
    """config_excel.JSON_PATH is where an Excel import LANDS; config.CONFIG_PATH
    is where the engine READS. If those differ, an import reports success and
    changes nothing — which is how the uploader came to be untrustworthy in the
    first place."""
    cfg, excel = config_loaded_under(tmp_path)
    assert Path(excel.JSON_PATH).resolve() == Path(cfg.CONFIG_PATH).resolve()


# ── 3. Seeding, which is what makes the absent-file case safe ──────────────

def test_an_empty_volume_is_seeded_from_the_image(tmp_path, monkeypatch):
    """A brand-new Railway volume is empty. The first boot must populate it
    from the committed copy rather than run with no configuration."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MURESSONS_NO_LEGACY_MIGRATION", "1")   # set by conftest; must not matter here
    target = runtime_paths.config_file("simulation_config.json")
    assert target.exists(), "an empty data dir was not seeded — config would be missing"
    assert Path(target).parent.resolve() == tmp_path.resolve()
    assert json.loads(target.read_text(encoding="utf-8")) == json.loads(
        (_REPO_ROOT / "simulation_config.json").read_text(encoding="utf-8")
    )


def test_seeding_does_not_clobber_a_facilitators_edit(tmp_path, monkeypatch):
    """The second boot must NOT re-seed. If it did, every redeploy would revert
    tuning exactly as before — the bug wearing the fix's clothes."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    first = runtime_paths.config_file("simulation_config.json")
    first.write_text(json.dumps({"simulation_settings": {"rounds": 4}}), encoding="utf-8")
    second = runtime_paths.config_file("simulation_config.json")
    assert json.loads(second.read_text(encoding="utf-8"))["simulation_settings"]["rounds"] == 4, (
        "the edit was overwritten by re-seeding"
    )


def test_config_file_ignores_no_legacy_migration_and_says_why(tmp_path, monkeypatch):
    """data_file() honours that flag; config_file() must not. Asserted rather
    than left to a comment, because the difference is the whole design."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MURESSONS_NO_LEGACY_MIGRATION", "1")
    assert not runtime_paths.data_file("some_pure_runtime_state.json").exists()
    assert runtime_paths.config_file("decision_overrides.json").exists()


def test_an_unwritable_data_dir_falls_back_to_real_values(monkeypatch):
    """A misconfigured mount must degrade to read-only-but-correct, never to
    an empty config. This is a live-run property: a facilitator with a broken
    volume should get their simulation, not a differently-parameterised one."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", "/proc/definitely-not-writable")
    resolved = runtime_paths.config_file("simulation_config.json")
    assert resolved.exists(), "fell back to a non-existent path"
    assert json.loads(resolved.read_text(encoding="utf-8")), "fell back to an empty config"
