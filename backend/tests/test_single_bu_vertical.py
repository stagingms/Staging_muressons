"""
Single-BU vertical anomaly — regression tests.

Bug: a cohort configured as Single Business Unit with a substitute vertical
(e.g. 'retail_fmcg') gave players the full 4-BU conglomerate, because the
vertical id never matched a seed slot bu_id and the filter fell through
silently. Fix: create_session resolves the owning slot via SLOT_FIT_MAP and,
per design decision, the player's one BU carries the VERTICAL's profile
(consistent with 4-BU substitution via build_bu_states).
"""
import asyncio
import pytest

import database_memory as dbm


def _create(name, **kw):
    return asyncio.run(dbm.create_session(name, "FAC-TEST", **kw))


def test_single_bu_vertical_gets_exactly_one_vertical_bu():
    """The reported anomaly: single_bu + retail_fmcg must yield 1 BU, and it
    must be the retail_fmcg vertical profile — not 4 BUs, not consumer_goods."""
    res = _create(
        "VertCohort-A",
        simulation_mode="single_bu",
        industry_vertical="retail_fmcg",
        assigned_bu="consumer_goods",  # slot id, as normalised by /start
    )
    bus = res["business_units"]
    assert len(bus) == 1, f"expected 1 BU, got {len(bus)}"
    assert bus[0]["bu_id"] == "retail_fmcg"
    # Session record must agree with bu_states
    sess = dbm._sessions[res["session_id"]]
    assert sess["assigned_bu"] == "retail_fmcg"
    assert sess["simulation_mode"] == "single_bu"


def test_single_bu_legacy_vertical_assigned_bu():
    """Legacy cohorts stored the raw vertical id in assigned_bu (pre-fix).
    They must also resolve to the single vertical BU."""
    res = _create(
        "VertCohort-B",
        simulation_mode="single_bu",
        industry_vertical="retail_fmcg",
        assigned_bu="retail_fmcg",  # raw vertical id, no slot normalisation
    )
    bus = res["business_units"]
    assert len(bus) == 1
    assert bus[0]["bu_id"] == "retail_fmcg"


def test_single_bu_default_slot_unchanged():
    """Single-BU with a native slot (no substitute) keeps the default profile."""
    res = _create(
        "VertCohort-C",
        simulation_mode="single_bu",
        industry_vertical="pharma",
        assigned_bu="pharma",
    )
    bus = res["business_units"]
    assert len(bus) == 1
    assert bus[0]["bu_id"] == "pharma"


def test_conglomerate_still_four_bus():
    """No assigned_bu → full conglomerate, exactly as before."""
    res = _create("VertCohort-D")
    assert len(res["business_units"]) == 4


def test_single_bu_unknown_id_never_grants_conglomerate():
    """Unknown ids fall back to a single BU (final guard), never 4."""
    res = _create(
        "VertCohort-E",
        simulation_mode="single_bu",
        industry_vertical="not_a_real_vertical",
        assigned_bu="not_a_real_vertical",
    )
    assert len(res["business_units"]) == 1


def test_vertical_bu_has_engine_required_fields():
    """The substituted vertical BU must carry every field the engine and the
    bu_states serializer consume from seed BUs."""
    res = _create(
        "VertCohort-F",
        simulation_mode="single_bu",
        industry_vertical="oil_gas",
        assigned_bu="pharma",
    )
    bu = res["business_units"][0]
    assert bu["bu_id"] == "oil_gas"
    for field in (
        "revenue_base", "opex_base", "carbon_intensity", "water_dependency",
        "natural_capital_debt", "social_license_score", "governance_risk_score",
        "reputation_score", "staff_burnout_index",
    ):
        assert field in bu, f"vertical BU missing engine field: {field}"
