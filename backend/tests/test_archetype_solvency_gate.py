"""AR-A — terminal archetype solvency gate + reveal-key mapping.

Pins the two behaviours that stop an insolvent company being crowned a
flattering archetype, and that route the real profile to the reveal screen's
UPPERCASE ARCHETYPE_MATRIX key (which was previously never set, so every player
fell back to SAFE_HAVEN).
"""

from round_logic import (
    solvency_gated_profile,
    terminal_archetype_key,
    match_custom_archetype,
)


def test_negative_dmav_blocks_every_flattering_label():
    # AR-B: strong-ESG failures become the Hollow Idealist; mediocre-ESG
    # failures become the Stranded Relic. Either way, no flattering label.
    assert solvency_gated_profile("regenerative_titan", -464_550_000.0) == "hollow_idealist"
    assert solvency_gated_profile("derisked_safe_haven", -464_550_000.0) == "hollow_idealist"
    assert solvency_gated_profile("fragile_giant", -464_550_000.0) == "stranded_relic"


def test_zero_dmav_counts_as_value_destroyed():
    assert solvency_gated_profile("fragile_giant", 0.0) == "stranded_relic"
    assert solvency_gated_profile("regenerative_titan", 0.0) == "hollow_idealist"


def test_positive_dmav_keeps_the_earned_label():
    assert solvency_gated_profile("derisked_safe_haven", 50_000_000.0) == "derisked_safe_haven"
    assert solvency_gated_profile("regenerative_titan", 1.0) == "regenerative_titan"
    assert solvency_gated_profile("fragile_giant", 1.0) == "fragile_giant"


def test_stranded_relic_is_never_promoted_or_altered():
    assert solvency_gated_profile("stranded_relic", -5.0) == "stranded_relic"
    assert solvency_gated_profile("stranded_relic", 5.0) == "stranded_relic"


def test_pragmatic_operator_is_the_solvent_low_mr_floor():
    # AR-B: solvent low-M_R keeps its earned "Pragmatic Operator" label; only
    # value destruction demotes it to the Stranded Relic floor.
    assert solvency_gated_profile("pragmatic_operator", 50_000_000.0) == "pragmatic_operator"
    assert solvency_gated_profile("pragmatic_operator", -1.0) == "stranded_relic"
    assert solvency_gated_profile("pragmatic_operator", 0.0) == "stranded_relic"
    assert terminal_archetype_key("pragmatic_operator", 0.5) == "PRAGMATIC_OPERATOR"


def test_screenshot_case_maps_to_stranded_relic():
    # Round-10 screenshot: M_R 1.0, treasury -$464.55M, negligible NCD.
    mr = 1.0
    final_treasury = -464_550_000.0
    total_ncd = 145.0
    dmav = final_treasury * mr - total_ncd
    # M_R 1.0 lands on "fragile_giant" in the ladder; the gate must downgrade it.
    gated = solvency_gated_profile("fragile_giant", dmav)
    assert gated == "stranded_relic"
    assert terminal_archetype_key(gated, mr) == "STRANDED_RELIC"


def test_reveal_key_mapping_for_defaults():
    assert terminal_archetype_key("regenerative_titan", 1.9) == "REGENERATIVE_TITAN"
    assert terminal_archetype_key("derisked_safe_haven", 1.3) == "SAFE_HAVEN"
    assert terminal_archetype_key("fragile_giant", 1.0) == "FRAGILE_GIANT"
    assert terminal_archetype_key("stranded_relic", 0.4) == "STRANDED_RELIC"
    assert terminal_archetype_key("hollow_idealist", 1.4) == "HOLLOW_IDEALIST"


def test_hollow_idealist_is_a_strong_esg_bankruptcy():
    # A high-M_R company that still destroyed value keeps an honest — but
    # distinct — label, and maps to its own reveal theme.
    gated = solvency_gated_profile("regenerative_titan", -10_000_000.0)
    assert gated == "hollow_idealist"
    assert terminal_archetype_key(gated, 1.85) == "HOLLOW_IDEALIST"


def test_reveal_key_falls_back_by_mr_tier_for_custom_profiles():
    assert terminal_archetype_key("some_custom_key", 1.85) == "REGENERATIVE_TITAN"
    assert terminal_archetype_key("some_custom_key", 1.25) == "SAFE_HAVEN"
    assert terminal_archetype_key("some_custom_key", 0.9) == "FRAGILE_GIANT"
    assert terminal_archetype_key("some_custom_key", 0.5) == "STRANDED_RELIC"


# ── AR-C: custom-archetype matcher with the solvency axis ──────────────────
_CUSTOMS = [
    {"key": "titan", "mr_threshold": 1.8, "requires_solvent": True},
    {"key": "haven", "mr_threshold": 1.2, "requires_solvent": True},
    {"key": "relic", "mr_threshold": 0.0, "requires_solvent": False},
]


def test_custom_matcher_awards_top_tier_when_solvent():
    assert match_custom_archetype(_CUSTOMS, 1.9, solvent=True)["key"] == "titan"
    assert match_custom_archetype(_CUSTOMS, 1.3, solvent=True)["key"] == "haven"


def test_custom_matcher_insolvent_skips_solvency_gated_and_falls_to_failure():
    # High M_R but insolvent cannot win the solvency-gated titan.
    assert match_custom_archetype(_CUSTOMS, 1.9, solvent=False)["key"] == "relic"


def test_custom_matcher_non_gated_is_unaffected_by_solvency():
    customs = [{"key": "leader", "mr_threshold": 1.0, "requires_solvent": False}]
    assert match_custom_archetype(customs, 1.5, solvent=False)["key"] == "leader"
    assert match_custom_archetype(customs, 1.5, solvent=True)["key"] == "leader"


def test_custom_matcher_empty_returns_none():
    assert match_custom_archetype([], 1.0, solvent=True) is None


def test_custom_matcher_all_gated_insolvent_falls_to_lowest_tier():
    gated_only = [
        {"key": "titan", "mr_threshold": 1.8, "requires_solvent": True},
        {"key": "haven", "mr_threshold": 1.2, "requires_solvent": True},
    ]
    assert match_custom_archetype(gated_only, 1.9, solvent=False)["key"] == "haven"
