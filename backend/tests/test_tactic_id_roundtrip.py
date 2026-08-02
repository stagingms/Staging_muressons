"""Engagement-tactic ids must survive an Excel export → reimport round-trip.

THE DEFECT (C4 in the failure-mode register)
--------------------------------------------
_encode_tactic wrote ``Label|correct|Rationale`` — no id — and _parse_tactic
regenerated the id as a slug of the label. A tactic shipped as
``id: "meet_privately", label: "Meet privately with the CEO"`` therefore came
back from a round-trip as ``meet_privately_with_the_ceo``: every reference
keyed to the original id (correct-tactic scoring, history) silently stopped
matching. The failure needed no error anywhere — the config imported cleanly.

The fix appends the id as an optional 4th field. Old 3-field files must keep
parsing byte-for-byte as before (slug fallback), because facilitators hold
exports made before the fix.
"""
import pytest

from stakeholder_config_excel import _encode_tactic, _parse_tactic


def test_id_survives_encode_parse_roundtrip():
    t = {"id": "meet_privately", "label": "Meet privately with the CEO",
         "correct": True, "rationale": "Builds trust."}
    got = _parse_tactic(_encode_tactic(t))
    assert got["id"] == "meet_privately"
    assert got["label"] == t["label"]
    assert got["correct"] is True
    assert got["rationale"] == "Builds trust."


def test_the_original_defect_shape_is_dead():
    """The exact mangling that was reported: id != slug(label)."""
    t = {"id": "meet_privately", "label": "Meet privately with the CEO",
         "correct": False, "rationale": "x"}
    got = _parse_tactic(_encode_tactic(t))
    assert got["id"] != "meet_privately_with_the_ceo"


def test_legacy_three_field_string_still_parses_with_slug_fallback():
    got = _parse_tactic("Meet privately with the CEO|true|Builds trust.")
    assert got["id"] == "meet_privately_with_the_ceo"
    assert got["correct"] is True
    assert got["rationale"] == "Builds trust."


def test_rationale_containing_a_pipe_is_not_eaten_as_an_id():
    """A pipe inside prose must not be misread as the id delimiter. The final
    segment here is not slug-shaped (spaces, capitals), so it stays rationale."""
    got = _parse_tactic("Lobby|false|Risky: press|board may object")
    assert got["id"] == "lobby"
    assert got["rationale"] == "Risky: press|board may object"


def test_tactic_without_id_encodes_as_legacy_three_fields():
    s = _encode_tactic({"label": "Lobby", "correct": False, "rationale": "r"})
    assert s == "Lobby|false|r"


@pytest.mark.parametrize("bad", ["", None, "only-label", "a|b"])
def test_unparseable_inputs_still_return_none(bad):
    assert _parse_tactic(bad) is None
