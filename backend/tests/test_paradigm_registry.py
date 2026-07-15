"""Audit #15 — paradigm registry dispatch.

Pins that the registry returns the SAME config each paradigm's own provider
returns, so replacing the inline if/elif chains is behaviour-preserving.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

import paradigm_registry as pr
from round_configs import get_round_config


def test_valid_paradigms_cover_the_known_set():
    assert pr.VALID_PARADIGMS == {
        "legacy_abc", "advanced_climate", "un_sdg", "healthcare", "multi_toggles",
    }


def test_legacy_matches_get_round_config():
    for rnum in range(1, 11):
        assert pr.round_config_for("legacy_abc", rnum) == get_round_config(rnum)


def test_advanced_climate_uses_legacy_config():
    for rnum in (1, 5, 10):
        assert pr.round_config_for("advanced_climate", rnum) == get_round_config(rnum)


def test_unknown_and_blank_paradigm_fall_back_to_legacy():
    assert pr.round_config_for("nonsense", 1) == get_round_config(1)
    assert pr.round_config_for("", 1) == get_round_config(1)
    assert pr.round_config_for(None, 1) == get_round_config(1)


def test_sdg_matches_sdg_provider():
    from sdg_configs import get_sdg_round_config
    for rnum in (1, 6, 10):
        assert pr.round_config_for("un_sdg", rnum) == get_sdg_round_config(rnum)


def test_healthcare_matches_healthcare_provider():
    from healthcare_configs import get_healthcare_round_config
    for rnum in (1, 6, 10):
        assert pr.round_config_for("healthcare", rnum) == get_healthcare_round_config(rnum)


def test_pillar_falls_back_to_legacy_when_no_override():
    from pillar_configs import get_pillar_config
    for rnum in range(1, 11):
        expected = get_pillar_config(rnum) or get_round_config(rnum)
        assert pr.round_config_for("multi_toggles", rnum) == expected
