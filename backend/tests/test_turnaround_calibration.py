"""
Turnaround Module — calibration regression (playtest properties).

Pins the balance of the T1-T4 recovery levers (PLAN §11 gate-calibration risk) so
future delta changes can't silently make graduation trivial or impossible:

  * disciplined (reputation-forward) play graduates reliably,
  * a treasury-only "growth bet" that ignores the trust gate never graduates,
  * graduation is achievable but not trivial across all decision sequences,
  * opening by rebuilding trust (A) beats opening with a cash grab (C).

Exhaustive over 3^4 sequences × a grid of distressed entry states (~1,900 plays,
sub-second).
"""

import itertools
import statistics
import turnaround_engine as te

CHOICES = ["option_a", "option_b", "option_c"]
ENTRIES = [(t, rep) for t in (-5_000_000, -2_000_000, -500_000, 0)
                    for rep in (10, 15, 18, 22, 26, 29)]
ALL_SEQS = list(itertools.product(CHOICES, repeat=4))


def _play(entry_t, entry_rep, seq):
    gs = {"corporate_treasury": entry_t, "group_reputation": entry_rep,
          "game_over": True, "round_number": 10,
          "final_report_canonical": {"regenerative_multiple": 0.7},
          "active_event_flags": {}}
    te.enter_arc(gs, [])
    for ch in seq:
        r = te.apply_commit(gs, [], ch)
        if r["arc_complete"]:
            return bool(r["graduated"])
    return False


def test_disciplined_play_graduates_everywhere():
    assert all(_play(t, rep, ("option_a",) * 4) for (t, rep) in ENTRIES)


def test_treasury_only_never_graduates():
    assert not any(_play(t, rep, ("option_c",) * 4) for (t, rep) in ENTRIES)


def test_graduation_achievable_but_not_trivial():
    results = [_play(t, rep, seq) for (t, rep) in ENTRIES for seq in ALL_SEQS]
    rate = statistics.mean(results)
    assert 0.35 <= rate <= 0.80, f"overall graduation rate {rate:.1%} out of band"


def test_rebuild_trust_beats_cash_grab_first_move():
    first_a = statistics.mean(
        _play(t, rep, seq) for (t, rep) in ENTRIES for seq in ALL_SEQS if seq[0] == "option_a")
    first_c = statistics.mean(
        _play(t, rep, seq) for (t, rep) in ENTRIES for seq in ALL_SEQS if seq[0] == "option_c")
    assert first_a > first_c + 0.25, f"A={first_a:.1%} not clearly above C={first_c:.1%}"
