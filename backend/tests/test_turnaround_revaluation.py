"""
Turnaround Module — full ESG re-valuation on completion.

The arc re-runs the terminal_valuation engine with the final M_R and the
recovered cash position (never mutating final_report_canonical):
  * graduation lifts the survival clamp (+0.10) and lets the archetype climb;
  * expiry keeps the clamp and stays 'turnaround_manager';
  * terminal value scales with the final M_R; recovered cash flows to equity.
"""

import turnaround_engine as te

BUS = [
    {"revenue_base": 18_000_000, "opex_base": 12_000_000, "carbon_intensity": 35},
    {"revenue_base": 16_500_000, "opex_base": 11_500_000, "carbon_intensity": 72},
]


def _gs(base_mr=0.7):
    return {
        "corporate_treasury": -2_000_000, "group_reputation": 18,
        "game_over": True, "round_number": 10,
        "final_report_canonical": {"regenerative_multiple": base_mr},
        "active_event_flags": {
            "regenerative_multiple": base_mr, "net_debt": 5_000_000,
            "exit_multiple_applied": 12.0, "carbon_tax_per_ton": 250,
        },
    }


def _run(seq, base_mr=0.7):
    gs = _gs(base_mr)
    te.enter_arc(gs, BUS)
    for ch in seq:
        if te.apply_commit(gs, BUS, ch)["arc_complete"]:
            break
    return gs


def test_graduation_revalues_and_climbs():
    gs = _run(["option_a"] * 4)
    rep = gs["turnaround_amended_report"]
    assert rep["graduated"] is True and rep["revalued"] is True
    assert rep["regenerative_multiple"] == 0.8
    assert rep["archetype"] != "stranded_relic"       # climbed (reward)
    assert rep["terminal_value"] and rep["terminal_value"] > 0
    assert rep["price_per_share"] is not None
    assert rep["cash_recovered"] > 0                  # recovery lifted cash
    # Canonical untouched.
    assert gs["final_report_canonical"] == {"regenerative_multiple": 0.7}
    assert gs["active_event_flags"]["regenerative_multiple"] == 0.7


def test_expiry_stays_turnaround_manager():
    gs = _run(["option_c"] * 4)
    rep = gs["turnaround_amended_report"]
    assert rep["graduated"] is False
    assert rep["archetype"] == "turnaround_manager"   # clamp held
    assert rep["revalued"] is True


def test_terminal_value_scales_with_final_mr():
    # A higher base M_R (still < 0.8) yields a higher graduated terminal value.
    tv_low = _run(["option_a"] * 4, base_mr=0.60)["turnaround_amended_report"]["terminal_value"]
    tv_high = _run(["option_a"] * 4, base_mr=0.79)["turnaround_amended_report"]["terminal_value"]
    assert tv_high > tv_low


def test_revaluation_gracefully_skipped_without_bus():
    gs = _gs()
    te.enter_arc(gs, [])
    for _ in range(4):
        if te.apply_commit(gs, [], "option_a")["arc_complete"]:
            break
    rep = gs["turnaround_amended_report"]
    assert rep["revalued"] is False           # no BU data → M_R still amended
    assert rep["regenerative_multiple"] == 0.8
