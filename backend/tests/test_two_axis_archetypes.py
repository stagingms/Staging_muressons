"""AR-B — the complete two-axis terminal-archetype model.

Pins the full matrix (M_R x solvency) end-to-end:
  - the editable model (admin_shared.DEFAULT_ARCHETYPES) carries all seven
    archetypes with a coherent second (solvency) axis;
  - the custom-archetype matcher, fed that ladder, reproduces every cell —
    solvent labels for DMAV > 0, failure-band labels for DMAV <= 0;
  - the compute-side label map (terminal_valuation._ARCHETYPES) mirrors the
    two new keys so any lookup resolves.

No M_R math or valuation number is exercised here — only the label mapping.
"""

from admin_shared import DEFAULT_ARCHETYPES
from round_logic import match_custom_archetype
from terminal_valuation import _ARCHETYPES

# The seven archetypes of the two-axis model.
_EXPECTED_KEYS = {
    "regenerative_titan", "derisked_safe_haven", "fragile_giant",
    "pragmatic_operator", "hollow_idealist", "stranded_relic",
    "turnaround_manager",
}


def test_default_model_contains_every_two_axis_archetype():
    keys = {a["key"] for a in DEFAULT_ARCHETYPES}
    assert keys == _EXPECTED_KEYS, f"model drift: {keys ^ _EXPECTED_KEYS}"
    # Every entry declares both axes.
    for a in DEFAULT_ARCHETYPES:
        assert "mr_threshold" in a and "requires_solvent" in a, a["key"]


def test_solvent_axis_is_internally_consistent():
    by_key = {a["key"]: a for a in DEFAULT_ARCHETYPES}
    # Solvent-earned labels gate on solvency…
    for k in ("regenerative_titan", "derisked_safe_haven", "fragile_giant", "pragmatic_operator"):
        assert by_key[k]["requires_solvent"] is True, k
    # …failure-band labels do not (they ARE the insolvent outcomes).
    for k in ("hollow_idealist", "stranded_relic", "turnaround_manager"):
        assert by_key[k]["requires_solvent"] is False, k


def _customs():
    # A facilitator cloning the default ladder into custom_archetypes.
    return [dict(a) for a in DEFAULT_ARCHETYPES]


def test_matcher_reproduces_the_full_matrix():
    customs = _customs()

    def cell(mr, solvent):
        return match_custom_archetype(customs, mr, solvent)["key"]

    # Solvent column (DMAV > 0)
    assert cell(1.9, True) == "regenerative_titan"
    assert cell(1.3, True) == "derisked_safe_haven"
    assert cell(1.0, True) == "fragile_giant"
    assert cell(0.5, True) == "pragmatic_operator"

    # Value-destroyed column (DMAV <= 0) — flattering labels are refused
    assert cell(1.9, False) == "hollow_idealist"      # strong ESG, bankrupt
    assert cell(1.3, False) == "hollow_idealist"      # safe-haven tier, bankrupt
    assert cell(1.0, False) == "stranded_relic"       # fragile tier, bankrupt
    assert cell(0.5, False) == "stranded_relic"       # low M_R, bankrupt


def test_tie_break_order_prefers_solvent_gated_label():
    # At the 1.2 tie, a solvent company must win De-risked Safe-Haven, not the
    # non-gated Hollow Idealist that shares the threshold.
    assert match_custom_archetype(_customs(), 1.25, solvent=True)["key"] == "derisked_safe_haven"


def test_compute_side_label_map_mirrors_new_keys():
    assert _ARCHETYPES["pragmatic_operator"]["title"] == "The Pragmatic Operator"
    assert _ARCHETYPES["hollow_idealist"]["title"] == "The Hollow Idealist"
