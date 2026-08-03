"""4.1 — both storage backends hand the engine the same BU order.

THE DEFECT
    engine.py resolves the micro-strike target by INDEXING the business-unit
    list. The two backends returned that list in different orders:

        database_memory  ->  pharma, electronics, consumer_goods, software
        database (PG)    ->  consumer_goods, electronics, pharma, software

    Postgres sorts ORDER BY bu_id (alphabetical); the memory store returns
    creation order (slot order). So micro_strike_bu_idx == 0 struck pharma in
    every test ever run, and consumer_goods in production. Two of four draws
    hit a different company in the deployment than in the suite validating it.

    Nothing failed. Both backends were internally consistent; they simply
    disagreed with each other, and only one of them was ever tested.

WHAT CHANGED, AND THE BEHAVIOUR RISK
    Slot order is now canonical, so PRODUCTION behaviour moves: a run committed
    before this change does not replay identically on Postgres. That was a
    deliberate choice — slot order is what build_bu_states() creates, what the
    UI renders and what the Excel importer writes; alphabetical was an accident
    of one ORDER BY clause. No graded run had been scored when this landed.

    The memory backend is unaffected: creation order already WAS slot order, so
    the golden traces do not move. That asymmetry is the proof the right order
    was chosen — the tested behaviour is the one that survived.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from bu_profiles import (  # noqa: E402
    DEFAULT_SLOTS, canonical_bu_order, sort_bu_states_canonically,
)


def _states(*bu_ids):
    return [{"bu_id": b, "opex_base": 1000.0} for b in bu_ids]


def _ids(states):
    return [s["bu_id"] for s in states]


# ── 1. The ordering contract ───────────────────────────────────────────────

def test_alphabetical_input_comes_back_in_slot_order():
    """Exactly what Postgres hands us today."""
    pg_order = _states("consumer_goods", "electronics", "pharma", "software")
    assert _ids(sort_bu_states_canonically(pg_order)) == DEFAULT_SLOTS


def test_slot_ordered_input_is_left_alone():
    """Exactly what the memory store hands us. Must be a no-op, or the golden
    traces would move and the memory backend would be the one that changed."""
    mem_order = _states(*DEFAULT_SLOTS)
    assert _ids(sort_bu_states_canonically(mem_order)) == DEFAULT_SLOTS


def test_the_two_backends_now_agree():
    """The property the whole change exists for, stated directly."""
    pg = sort_bu_states_canonically(_states("consumer_goods", "electronics", "pharma", "software"))
    mem = sort_bu_states_canonically(_states(*DEFAULT_SLOTS))
    assert _ids(pg) == _ids(mem)


def test_ordering_is_total_and_stable_for_unknown_units():
    """A vertical no longer in the slot map must not make the order arbitrary —
    it sorts last, deterministically, rather than wherever the input put it."""
    mixed = _states("software", "zz_retired_unit", "pharma", "aa_retired_unit")
    out = _ids(sort_bu_states_canonically(mixed))
    assert out[:2] == ["pharma", "software"]
    assert out[2:] == ["aa_retired_unit", "zz_retired_unit"]


# ── 2. Substitution: the case that rules out ordering by bu_id ─────────────

def test_a_substituted_vertical_keeps_its_slot_position():
    """The reason 'just sort by bu_id' is wrong.

    A cohort running oil & gas has bu_id 'oil_gas' sitting in the 'pharma'
    slot. Alphabetically it would land second; by slot it must stay FIRST,
    because the slot is what the UI, the config and the engine all address.
    """
    gs = {"bu_substitutions": {"pharma": "oil_gas"}}
    stored = _states("consumer_goods", "electronics", "oil_gas", "software")
    assert _ids(sort_bu_states_canonically(stored, gs)) == [
        "oil_gas", "electronics", "consumer_goods", "software"
    ]


def test_the_canonical_order_follows_the_substitution_map():
    gs_subs = {"pharma": "oil_gas", "software": "technology"}
    assert canonical_bu_order(gs_subs) == [
        "oil_gas", "electronics", "consumer_goods", "technology"
    ]
    assert canonical_bu_order({}) == DEFAULT_SLOTS


def test_no_schema_change_was_needed():
    """Guards the design: the order is derived from data already persisted
    (global_state['bu_substitutions']). If someone later makes this depend on a
    new column, existing cohorts silently lose their ordering on read."""
    import inspect
    src = inspect.getsource(sort_bu_states_canonically)
    assert "bu_substitutions" in src
    assert "slot_index" not in src, "ordering now depends on a column old rows do not have"


# ── 3. The consumer that made it matter ────────────────────────────────────

def test_the_micro_strike_resolves_through_the_canonical_order():
    """engine.py must not index the raw list. If this regresses, the strike
    silently goes back to depending on which database you happen to be on."""
    src = (_BACKEND_DIR / "engine.py").read_text(encoding="utf-8")
    # Anchor on the APPLICATION site, not the generator that draws the index —
    # "micro_strike_triggered" appears in both, and the first hit is the draw.
    anchor = 'if macro_noise["micro_strike_triggered"]'
    assert src.count(anchor) == 1, "the micro-strike application site moved or multiplied"
    idx = src.index(anchor)
    window = src[idx:idx + 1200]
    assert "sort_bu_states_canonically" in window, (
        "the micro-strike no longer resolves through the canonical order"
    )


@pytest.mark.parametrize("draw,expected", list(enumerate(DEFAULT_SLOTS)))
def test_each_draw_maps_to_one_named_business_unit(draw, expected):
    """Pins the mapping itself, so a future reorder of DEFAULT_SLOTS is a
    visible, deliberate change to who gets struck rather than a silent one."""
    ordered = sort_bu_states_canonically(
        _states("consumer_goods", "electronics", "pharma", "software"))
    assert ordered[draw % len(ordered)]["bu_id"] == expected
