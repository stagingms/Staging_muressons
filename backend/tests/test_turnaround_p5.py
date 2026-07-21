"""
Turnaround Module — P5: leaderboard/analytics labelling.

Pins PLAN §8: the canonical R10 result stays the AUTHORITATIVE leaderboard
figure; a session that ran the arc gets a separate, clearly-labelled annotation
(authoritative=False) that never overwrites the completed-run M_R.
"""

import turnaround_engine as te


def _canonical_gs(base_mr=0.7):
    return {
        "corporate_treasury": -2_000_000, "group_reputation": 18,
        "game_over": True, "round_number": 10,
        "final_report_canonical": {"regenerative_multiple": base_mr},
        # The R10 valuation writes the authoritative M_R here:
        "active_event_flags": {"regenerative_multiple": base_mr, "profile_title": "The Stranded Relic"},
        "regenerative_multiple": base_mr,
    }


def test_annotation_none_when_no_arc():
    assert te.leaderboard_annotation(_canonical_gs()) is None


def test_annotation_none_while_open():
    gs = _canonical_gs()
    te.enter_arc(gs, [])                       # status -> open
    assert te.leaderboard_annotation(gs) is None


def test_annotation_graduated_is_labelled_non_authoritative():
    gs = _canonical_gs(base_mr=0.7)
    te.enter_arc(gs, [])
    for _ in range(4):
        if te.apply_commit(gs, [], "option_a")["arc_complete"]:
            break
    ann = te.leaderboard_annotation(gs)
    assert ann["status"] == "graduated" and ann["graduated"] is True
    assert ann["authoritative"] is False
    assert ann["amended_regenerative_multiple"] == 0.8
    assert ann["base_regenerative_multiple"] == 0.7


def test_annotation_aborted():
    gs = _canonical_gs()
    te.enter_arc(gs, [])
    te.abort_arc(gs)
    ann = te.leaderboard_annotation(gs)
    assert ann == {"status": "aborted", "authoritative": False}


def test_canonical_mr_untouched_by_arc():
    # The authoritative leaderboard M_R (active_event_flags.regenerative_multiple)
    # and the canonical snapshot must be identical before and after the arc.
    gs = _canonical_gs(base_mr=0.7)
    before_flag_mr = gs["active_event_flags"]["regenerative_multiple"]
    before_canon = dict(gs["final_report_canonical"])
    te.enter_arc(gs, [])
    for _ in range(4):
        if te.apply_commit(gs, [], "option_a")["arc_complete"]:
            break
    assert gs["active_event_flags"]["regenerative_multiple"] == before_flag_mr
    assert gs["regenerative_multiple"] == before_flag_mr
    assert gs["final_report_canonical"] == before_canon
