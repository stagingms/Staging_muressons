"""FIN-06 hygiene (found while rebaselining the golden matrix for the
2026-09-10 audit response) — the engine waterfall marks say what moved the
treasury, and only for THIS round.

1. run_new_engines wrote `_treasury_moves` only when some engine moved the
   treasury. The router pops the key before the flags are stored, so the
   player's waterfall was never affected — but any driver that keeps the
   engines' extra on the flags (the golden harness) forwarded the previous
   round's list through every quiet round, and the fixtures showed the same
   charge "again" in the rounds after it. The list is now written every
   round, empty when nothing moved.
2. The balance-sheet step moves the treasury for two reasons — the revolver
   interest on negative cash swept to short-term debt, and the covenant
   surcharge — and the single mark around the step labelled both
   "Balance sheet (short-term debt interest)". The step is itemised from the
   engine's own diagnostics: "Balance sheet — short-term debt interest",
   "Balance sheet — covenant surcharge", remainder under "Balance sheet".
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_BACKEND_DIR / "tests"))
os.environ.setdefault("USE_MEMORY_DB", "true")

import golden_matrix_harness as H  # noqa: E402


@pytest.fixture(scope="module")
def distress():
    return H.run_path("distress_c", rules_version="2026.09")


@pytest.fixture(scope="module")
def all_a():
    return H.run_path("all_a", rules_version="2026.09")


def _moves(rec):
    return rec["escalations"]["treasury_moves"]


def test_a_quiet_round_carries_an_empty_list_not_last_rounds(all_a, distress):
    """all_a: Nature's Invoice fires at R5 and nothing moves in R6 (N4's
    commit measured this from the treasury column). distress_c: the R4 NPC
    fine used to reappear at R5 and the R7 one at R8."""
    a5, a6 = all_a[4], all_a[5]
    assert any(l.startswith("Biodiversity") for l, _ in _moves(a5))
    assert _moves(a6) == [], _moves(a6)
    assert a6["global"]["corporate_treasury"] == pytest.approx(
        a5["global"]["corporate_treasury"] + (a6["global"]["corporate_treasury"] - a5["global"]["corporate_treasury"]))
    d4, d5, d7, d8 = distress[3], distress[4], distress[6], distress[7]
    assert any(l.startswith("NPC") for l, _ in _moves(d4)) and any(l.startswith("NPC") for l, _ in _moves(d7))
    assert not any(l.startswith("NPC") for l, _ in _moves(d5))
    assert _moves(d8) == [], _moves(d8)


def test_the_covenant_surcharge_is_named_as_what_it_is(distress):
    """distress_c breaches its covenant at R9 (D1) and R10; the round's move
    is the surcharge, labelled so, equal to what the engine says it charged."""
    for idx in (8, 9):
        rec = distress[idx]
        bs = [(l, a) for l, a in _moves(rec) if l.startswith("Balance sheet")]
        assert bs, (rec["round"], _moves(rec))
        labels = {l for l, _ in bs}
        assert "Balance sheet — covenant surcharge" in labels, labels
        assert not any("short-term debt interest" in l and "(" in l for l in labels), labels
        assert all(a < 0 for _, a in bs)


def test_no_unattributed_balance_sheet_movement_on_the_covering_paths():
    """Whatever the statement moved is explained by its two named items;
    the generic 'Balance sheet' remainder never appears on the seven paths."""
    for name in sorted(H.PATHS):
        for rec in H.run_path(name, rules_version="2026.09")[:-1]:
            for label, _ in _moves(rec):
                assert label != "Balance sheet", (name, rec["round"], _moves(rec))
                assert not label.startswith("Balance sheet (")


def test_the_itemised_labels_reach_the_players_waterfall():
    """The bridge lists the engine moves by their labels — so a covenant
    surcharge is a "covenant surcharge" line in the cockpit's waterfall."""
    from waterfall_bridge import bridge_waterfall
    events = {"consequence_waterfall": {"entries": [], "initial_treasury": 10.0},
              "_treasury_moves": [{"engine": "Balance sheet — covenant surcharge", "delta": -3.0},
                                  {"engine": "Balance sheet — short-term debt interest", "delta": -1.0}]}
    bridge_waterfall(events, after_tick=10.0, after_pillar=10.0, after_post_tick=10.0, after_engines=6.0, stored=6.0)
    labels = [e["label"] for e in events["consequence_waterfall"]["entries"]]
    assert "Balance sheet — covenant surcharge" in labels and "Balance sheet — short-term debt interest" in labels
    assert "Other engine movements" not in labels
