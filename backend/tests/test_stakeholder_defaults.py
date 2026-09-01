"""Stakeholder realism waves + negotiation rooms are ON by default.

EVAL_Stakeholder_SLO_2026-09-01 recommendations 1+2 (owner ruling): the
accumulative stakeholder model (F1 trust stock, F2 continuous SLO feedback,
F3 coalitions, F4 uncertain thresholds/patience clock, F5 promises) and the
negotiation surface ship enabled, so the next cohort meets stakeholders with
memory and has the designed exits. Per-cohort overrides and the explicit
facilitator revoke path both keep working; F6 (intel UI rail) stays opt-in.
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))
os.environ.setdefault("USE_MEMORY_DB", "true")

WAVES_ON = (
    "stakeholder_memory_enabled",
    "stakeholder_slo_feedback_enabled",
    "stakeholder_engagement_enabled",
    "stakeholder_coalitions_enabled",
    "stakeholder_uncertainty_enabled",
)


def test_wave_toggles_default_on_and_intel_stays_opt_in():
    from pedagogical_engine import get_pedagogical_toggles
    t = get_pedagogical_toggles(None)
    for key in WAVES_ON:
        assert t[key] is True, f"{key} must default ON (EVAL rec 1/2)"
    assert t["stakeholder_intel_ui_enabled"] is False, "F6 rail stays opt-in"


def test_wave_toggles_remain_cohort_overridable():
    from pedagogical_engine import get_pedagogical_toggles
    t = get_pedagogical_toggles({"stakeholder_memory_enabled": False})
    assert t["stakeholder_memory_enabled"] is False
    assert t["stakeholder_slo_feedback_enabled"] is True


def test_negotiation_rooms_default_enabled_for_cohorts():
    from admin_shared import get_effective_settings
    assert get_effective_settings(None).get("negotiation_rooms_enabled") is True


def test_facilitator_capability_defaults_granted_but_revocable():
    """Absent key = granted (the new platform default); explicit False = the
    revoke path, still refused."""
    from router import _facilitator_negotiation_granted
    assert _facilitator_negotiation_granted({}) is True
    assert _facilitator_negotiation_granted({"negotiation_rooms_enabled": True}) is True
    assert _facilitator_negotiation_granted({"negotiation_rooms_enabled": False}) is False


def test_default_pipeline_runs_the_accumulative_model():
    """End to end: a dry-run round under DEFAULT toggles must initialise the
    F1 trust stock on the named NPCs — the observable that memory is live."""
    import dry_run
    import test_universal_math_engine as UME
    dry_run._EXTRA_STRATEGIES["waves_probe"] = {
        "label": "waves_probe", "capex_frac": 0.10, "dividends": 0,
        "scorer": "balanced", "choice_map": {r: "option_b" for r in range(1, 11)},
    }
    bus = UME.BU_COMPOSITION_FACTORIES["DEFAULT_4_BU"]()
    gs = UME.make_global_state(paradigm="legacy_abc")
    out = dry_run._run_one(copy.deepcopy(gs), copy.deepcopy(bus), "waves_probe",
                           seed=7, end_round=2, paradigm="legacy_abc",
                           ped_overrides={}, difficulty_tier="standard")
    assert out["rounds"], "dry run produced no rounds"
    # the run mutates its own deep copies; re-run capturing state via a fresh
    # global: easiest observable is on the returned trajectory's final gs —
    # _run_one does not return gs, so assert through a direct post_tick probe:
    from round_logic import run_new_engines
    gs2 = UME.make_global_state(paradigm="legacy_abc")
    bus2 = UME.BU_COMPOSITION_FACTORIES["DEFAULT_4_BU"]()
    events: dict = {}
    run_new_engines(round_number=1, global_state=gs2, bu_states=bus2, events=events)
    npcs = (gs2.get("npc_stakeholders") or {}).get("npcs") or {}
    assert npcs, "NPC engine did not run under default toggles"
    assert all(st.get("trust_initialised") for st in npcs.values()), (
        "F1 trust stock not initialised — stakeholder memory is not live by default")
