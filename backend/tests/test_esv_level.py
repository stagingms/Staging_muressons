"""N4 (EVAL_AuditResponse 2026-09-10, action 10) — ecosystem-services value is
a LEVEL of the current ecology, not a per-round growth rate.

Before: calc_ecosystem_services_value multiplied LAST ROUND's value by the
composite factor (≈1.12 at the starting state), so ESV went $8.0M → $26.9M
over ten rounds with nothing changing, and a single EHI drop turned the
composite into a <1 growth rate that shrank the value — and charged
"Nature's Invoice" — every round after (six invoices, $473K, for one event).

Now: value = ESV_BASE × composite(this round's ecology). Unchanged ecology
→ unchanged value; one fall in the level → one invoice proportional to it;
a state written by the old rule is re-levelled once without an invoice.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import biodiversity_engine  # noqa: E402
from biodiversity_engine import (  # noqa: E402
    calc_ecosystem_services_value, create_initial_biodiversity_state, process_biodiversity_tick,
)
from bu_profiles import build_bu_states  # noqa: E402

ESV_BASE = getattr(biodiversity_engine, "ESV_BASE", 8_000_000.0)   # absent before N4 — keeps the pre-fix run meaningful


def _bus(ci: float = 40.0) -> list[dict]:
    bus = build_bu_states()
    for b in bus:
        b["carbon_intensity"] = ci          # ≤ 50: no climate stress on EHI
    return bus


def _gs() -> dict:
    return {"corporate_treasury": 50_000_000.0, "active_event_flags": {}}


def _run(state, gs, bus, ncd_by_round: dict[int, float] | None = None, rounds: int = 10):
    out = []
    for r in range(1, rounds + 1):
        state, diag = process_biodiversity_tick(
            state, gs, bus, {"natural_capital_debt_delta": (ncd_by_round or {}).get(r, 0.0)}, r)
        out.append((copy.deepcopy(state), diag))
    return out


def test_unchanged_ecology_gives_an_unchanged_value_for_ten_rounds():
    """habitat_integrity 0.5 and carbon intensity ≤ 50 hold EHI exactly
    constant (IMP-01 levers all zero), so nothing ecological moves."""
    state = create_initial_biodiversity_state()
    state["habitat_integrity"] = 0.5
    state["ecosystem_services_value"], _ = calc_ecosystem_services_value(      # the level at THIS ecology
        ESV_BASE, state["ecosystem_health_index"], state["pollinator_health"],
        state["water_stress_index"], state["habitat_integrity"])
    ticks = _run(state, _gs(), _bus())
    ehis = {round(s["ecosystem_health_index"], 6) for s, _ in ticks}
    values = {s["ecosystem_services_value"] for s, _ in ticks}
    assert len(ehis) == 1, ehis
    assert len(values) == 1, values                       # was: ten different, rising ~12 %/round
    assert all(d.get("nature_replacement_cost") is None for _, d in ticks)


def test_the_value_is_base_times_this_rounds_composite_not_last_rounds_value_times_it():
    """Two sessions that arrive at the same ecology by different paths carry
    the same value — a level has no memory. Under the old rule the value
    depended on every previous round's composite."""
    a = create_initial_biodiversity_state()
    b = create_initial_biodiversity_state()
    b["ecosystem_services_value"] = 3 * ESV_BASE      # any history at all
    ta = _run(a, _gs(), _bus(), rounds=3)
    tb = _run(b, _gs(), _bus(), rounds=3)
    assert ta[-1][0]["ecosystem_health_index"] == tb[-1][0]["ecosystem_health_index"]
    assert ta[-1][0]["ecosystem_services_value"] == tb[-1][0]["ecosystem_services_value"]
    # and the value is the documented formula
    s, d = ta[-1]
    v, _ = calc_ecosystem_services_value(0.0, s["ecosystem_health_index"], s["pollinator_health"],
                                         s["water_stress_index"], s["habitat_integrity"])
    assert s["ecosystem_services_value"] == v
    assert d["ecosystem_services"]["new_value"] == v


def test_the_default_start_no_longer_triples_over_a_game():
    ticks = _run(create_initial_biodiversity_state(), _gs(), _bus())
    first, last = ticks[0][0]["ecosystem_services_value"], ticks[-1][0]["ecosystem_services_value"]
    # EHI drifts +0.25/round at habitat 0.55 (an IMP-01 lever), i.e. ≈ +2 % over the game — not ×3
    assert 1.0 < last / first < 1.05, (first, last)


def test_the_starting_value_is_the_level_at_the_starting_ecology():
    s = create_initial_biodiversity_state()
    v, _ = calc_ecosystem_services_value(ESV_BASE, s["ecosystem_health_index"], s["pollinator_health"],
                                         s["water_stress_index"], s["habitat_integrity"])
    assert s["ecosystem_services_value"] == v != ESV_BASE


def test_one_fall_in_the_level_is_invoiced_once_and_in_proportion():
    gs = _gs()
    ticks = _run(create_initial_biodiversity_state(), gs, _bus(), ncd_by_round={5: 40.0})
    invoices = [(r + 1, d["nature_replacement_cost"]) for r, (_, d) in enumerate(ticks)
                if d.get("nature_replacement_cost") is not None]
    assert [r for r, _ in invoices] == [5], invoices          # was: rounds 5..10, six invoices
    s4, s5 = ticks[3][0], ticks[4][0]
    fall = round(s4["ecosystem_services_value"] - s5["ecosystem_services_value"], 2)
    assert fall > 0
    expected = round(fall * s5["biodiversity_dependency_score"] * 0.3, 2)
    assert invoices[0][1] == pytest.approx(expected)
    assert gs["corporate_treasury"] == pytest.approx(50_000_000.0 - expected)
    # the level stays where the ecology left it — it neither recovers nor keeps sinking on its own
    assert ticks[5][0]["ecosystem_services_value"] < ticks[3][0]["ecosystem_services_value"]
    assert ticks[9][0]["ecosystem_services_value"] == pytest.approx(ticks[5][0]["ecosystem_services_value"], rel=0.02)


def test_a_state_written_by_the_old_rule_is_relevelled_once_without_an_invoice():
    """In-flight sessions carry a compounded value and the old `_prev_esv`
    marker. The first tick under the new rule brings the value to the level
    and must not charge the team for the difference — nothing happened to
    the ecology. The marker is dropped so the next tick is ordinary."""
    legacy = create_initial_biodiversity_state()
    legacy["ecosystem_services_value"] = 26_904_382.0
    legacy["_prev_esv"] = 26_904_382.0
    gs = _gs()
    s, d = process_biodiversity_tick(legacy, gs, _bus(), {"natural_capital_debt_delta": 0.0}, 6)
    assert s["ecosystem_services_value"] < 10_000_000 and "_prev_esv" not in s
    assert d.get("nature_replacement_cost") is None and gs["corporate_treasury"] == 50_000_000.0
    assert d["esv_relevelled_from_legacy"]["previous_value"] == 26_904_382.0
    # the round after: a genuine fall IS invoiced again
    s2, d2 = process_biodiversity_tick(s, gs, _bus(), {"natural_capital_debt_delta": 40.0}, 7)
    assert d2.get("nature_replacement_cost", 0) > 0 and "esv_relevelled_from_legacy" not in d2


def test_the_engine_never_writes_the_growth_rate_marker_again():
    s, _ = process_biodiversity_tick(create_initial_biodiversity_state(), _gs(), _bus(),
                                     {"natural_capital_debt_delta": 0.0}, 1)
    assert "_prev_esv" not in s
    src = (_BACKEND_DIR / "biodiversity_engine.py").read_text(encoding="utf-8")
    assert "new_value = round(current_value * composite" not in src
    assert "new_value = round(base_value * composite" in src
