"""Unit tests for the B5 teachable-moment detector (pure logic, no DB)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from teachable_moments import derive_teachable_moments, _is_adverse


def test_adverse_classification():
    assert _is_adverse("BLOCKS +0.20 Resilience M_R bonus") is True
    assert _is_adverse("Doubles crisis severity to 80") is True
    assert _is_adverse("Triggers greenwash if inv<15%") is True
    # Protective effects are NOT adverse
    assert _is_adverse("Prevents supply chain scandal") is False
    assert _is_adverse("+0.10 M_R Governance bonus") is False


def test_fires_when_majority_converge_on_adverse_flag():
    # 3 of 4 teams took insurance_only (an adverse, BLOCKS-a-bonus flag)
    teams = [
        ["insurance_only", "materiality_aligned"],
        ["insurance_only"],
        ["insurance_only"],
        ["early_decarboniser"],
    ]
    notes = derive_teachable_moments(teams, threshold_ratio=0.5)
    flags = {n["flag"] for n in notes}
    assert "insurance_only" in flags
    note = next(n for n in notes if n["flag"] == "insurance_only")
    assert note["count"] == 3 and note["total"] == 4
    assert "Pause and discuss" in note["message"]


def test_does_not_fire_below_threshold():
    teams = [["insurance_only"], ["early_decarboniser"], ["materiality_aligned"], ["deep_audit_completed"]]
    notes = derive_teachable_moments(teams, threshold_ratio=0.5)
    assert all(n["flag"] != "insurance_only" for n in notes)


def test_ignores_protective_and_beneficial_flags():
    # All teams aligned materiality (a BONUS) — should never be a teachable moment
    teams = [["materiality_aligned"]] * 4
    notes = derive_teachable_moments(teams, threshold_ratio=0.5)
    assert notes == []


def test_min_teams_guard():
    assert derive_teachable_moments([["insurance_only"]], min_teams=2) == []
