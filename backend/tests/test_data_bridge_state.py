"""
tests/test_data_bridge_state.py
================================
Contract tests for the Data Bridge Delta vs Override enforcement.

Tests verify that apply_side_track_results():
  1. Never mutates the original state dict (pure-function guarantee).
  2. Applies kpi_deltas (additive) FIRST.
  3. Applies kpi_overrides (absolute assignment) SECOND, overwriting delta
     results ONLY for fields that are explicitly set (not None).
  4. Leaves unrelated state keys completely untouched.
  5. Correctly handles flag merging and removal in the same atomic call.
  6. Clamps all written KPIs to their engine-defined bounds.
  7. Raises TypeError on invalid payload type.
"""

import copy
import pytest

# ── Imports from the Data Bridge public API ───────────────────────────────────
# All three types are re-exported from base_track for consumer convenience.
from side_tracks.base_track import DataBridgeOutput, KPIDeltas, KPIOverrides

# ── The engine function under test ───────────────────────────────────────────
from engine import apply_side_track_results


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def base_state() -> dict:
    """A representative main-sim global_state snapshot."""
    return {
        "corporate_treasury":   50_000_000.0,
        "group_reputation":     65.0,
        "avg_carbon_intensity": 48.0,
        "avg_governance_risk":  22.0,
        "avg_social_license":   70.0,
        "total_ncd":            5_000_000.0,
        "synergy_multiplier":   1.05,
        "active_event_flags": {
            "ethics_track_completed": True,
            "existing_flag":          "keep_me",
        },
    }


@pytest.fixture()
def delta_only_payload() -> DataBridgeOutput:
    """Payload that only contains additive deltas; no overrides."""
    return DataBridgeOutput(
        kpi_deltas=KPIDeltas(treasury_delta=-2_000_000.0, reputation_delta=3.0),
    )


@pytest.fixture()
def override_only_payload() -> DataBridgeOutput:
    """Payload that only sets absolute overrides; no deltas."""
    return DataBridgeOutput(
        kpi_overrides=KPIOverrides(group_reputation=50.0),
    )


@pytest.fixture()
def mixed_payload() -> DataBridgeOutput:
    """The canonical contract payload: treasury delta + reputation override."""
    return DataBridgeOutput(
        kpi_deltas=KPIDeltas(treasury_delta=-2_000_000.0),
        kpi_overrides=KPIOverrides(group_reputation=50.0),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT TEST (the primary specification from the task)
# ═══════════════════════════════════════════════════════════════════════════════

def test_data_bridge_separates_deltas_and_overrides(base_state):
    """
    Core contract: delta is additive math; override is an absolute assignment.
    Both can coexist in one payload without interfering with each other.
    """
    initial_state = {
        "corporate_treasury": 50_000_000.0,
        "group_reputation":   65.0,
    }

    payload = DataBridgeOutput(
        kpi_deltas=KPIDeltas(treasury_delta=-2_000_000.0),
        kpi_overrides=KPIOverrides(group_reputation=50.0),
    )

    new_state = apply_side_track_results(initial_state, payload, apply_flags=False)

    assert new_state["corporate_treasury"] == 48_000_000.0, (
        "Delta failed to do math: expected 50M - 2M = 48M."
    )
    assert new_state["group_reputation"] == 50.0, (
        "Override failed to reset absolute value: expected exactly 50.0 "
        "(not 65.0 + some delta)."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PURE-FUNCTION GUARANTEE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_original_state_is_never_mutated(base_state, mixed_payload):
    """apply_side_track_results must return a COPY, not mutate the input."""
    original_copy = copy.deepcopy(base_state)
    apply_side_track_results(base_state, mixed_payload)
    assert base_state == original_copy, (
        "Original state dict was mutated. apply_side_track_results must be a pure function."
    )


def test_return_is_different_object(base_state, mixed_payload):
    """The returned dict must be a different object, not the same reference."""
    new_state = apply_side_track_results(base_state, mixed_payload)
    assert new_state is not base_state, (
        "apply_side_track_results returned the same dict object — must return a copy."
    )


def test_unrelated_keys_preserved(base_state, mixed_payload):
    """Keys not in any KPI map must survive unchanged in the output."""
    new_state = apply_side_track_results(base_state, mixed_payload)
    assert new_state["synergy_multiplier"] == base_state["synergy_multiplier"]
    assert new_state["avg_governance_risk"] == base_state["avg_governance_risk"]
    assert new_state["total_ncd"] == base_state["total_ncd"]


# ═══════════════════════════════════════════════════════════════════════════════
#  DELTA SEMANTICS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_delta_is_additive_positive(base_state):
    """A positive reputation_delta ADDS to the existing reputation."""
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(reputation_delta=10.0))
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["group_reputation"] == pytest.approx(75.0)


def test_delta_is_additive_negative(base_state):
    """A negative treasury_delta SUBTRACTS from the existing treasury."""
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(treasury_delta=-5_000_000.0))
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["corporate_treasury"] == pytest.approx(45_000_000.0)


def test_zero_delta_is_no_op(base_state):
    """A zero delta must not change the state value."""
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(treasury_delta=0.0))
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["corporate_treasury"] == base_state["corporate_treasury"]


def test_multiple_deltas_all_applied(base_state):
    """Multiple delta fields in one payload are all applied independently."""
    payload = DataBridgeOutput(
        kpi_deltas=KPIDeltas(
            treasury_delta=-1_000_000.0,
            reputation_delta=-5.0,
            carbon_intensity_delta=-3.0,
        )
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["corporate_treasury"]   == pytest.approx(49_000_000.0)
    assert new_state["group_reputation"]     == pytest.approx(60.0)
    assert new_state["avg_carbon_intensity"] == pytest.approx(45.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  OVERRIDE SEMANTICS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_override_sets_absolute_value(base_state):
    """An override must set the exact value regardless of the current state."""
    payload = DataBridgeOutput(
        kpi_overrides=KPIOverrides(group_reputation=30.0)
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["group_reputation"] == 30.0


def test_none_override_does_not_touch_state(base_state):
    """An override field left as None must not alter the state key."""
    payload = DataBridgeOutput(
        kpi_overrides=KPIOverrides(group_reputation=None)   # explicitly None
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["group_reputation"] == base_state["group_reputation"]


def test_override_wins_over_delta_for_same_key(base_state):
    """
    CRITICAL: When a delta and override target the same state key,
    the override must WIN because it is applied SECOND.

    Base reputation: 65.0
    Delta:    +10.0  → intermediate = 75.0
    Override: 40.0   → final        = 40.0  (override wins)
    """
    payload = DataBridgeOutput(
        kpi_deltas=KPIDeltas(reputation_delta=10.0),
        kpi_overrides=KPIOverrides(group_reputation=40.0),
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["group_reputation"] == 40.0, (
        "Override must WIN when both delta and override target the same key. "
        "The override (applied SECOND) must overwrite the delta result."
    )


def test_override_does_not_affect_unrelated_delta_key(base_state):
    """
    An override on reputation must not change a treasury delta applied in Step 1.
    Step 1: treasury -= 2M → 48M
    Step 2: reputation = 50  (override, different key)
    Result: both must be correct simultaneously.
    """
    payload = DataBridgeOutput(
        kpi_deltas=KPIDeltas(treasury_delta=-2_000_000.0),
        kpi_overrides=KPIOverrides(group_reputation=50.0),
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["corporate_treasury"] == pytest.approx(48_000_000.0)
    assert new_state["group_reputation"]   == 50.0


# ═══════════════════════════════════════════════════════════════════════════════
#  BOUNDS-CLAMPING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_reputation_delta_clamped_at_100(base_state):
    """Reputation must never exceed 100 even after a large positive delta.
    
    KPIDeltas.reputation_delta is bounded [-100, +100] by Pydantic.
    We use a state where reputation is already at 90 + delta=100 → would be 190
    without the engine clamp, but must be 100.0.
    """
    high_rep_state = dict(base_state, group_reputation=90.0)
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(reputation_delta=100.0))
    new_state = apply_side_track_results(high_rep_state, payload, apply_flags=False)
    assert new_state["group_reputation"] <= 100.0


def test_reputation_delta_clamped_at_0(base_state):
    """Reputation must never go below 0 even after a large negative delta.
    
    KPIDeltas.reputation_delta is bounded [-100, +100] by Pydantic.
    We use a state where reputation is 5 and apply -100 delta → would be -95
    without the engine clamp, but must be 0.0.
    """
    low_rep_state = dict(base_state, group_reputation=5.0)
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(reputation_delta=-100.0))
    new_state = apply_side_track_results(low_rep_state, payload, apply_flags=False)
    assert new_state["group_reputation"] >= 0.0


def test_carbon_intensity_clamped_at_0(base_state):
    """Carbon intensity must never go below 0."""
    payload = DataBridgeOutput(kpi_deltas=KPIDeltas(carbon_intensity_delta=-9999.0))
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["avg_carbon_intensity"] >= 0.0


# ═══════════════════════════════════════════════════════════════════════════════
#  FLAG MERGING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_flags_to_set_merged_correctly(base_state):
    """flags_to_set values must appear in active_event_flags of the new state."""
    payload = DataBridgeOutput(
        flags_to_set={"brsr_track_completed": True, "brsr_grade": "A"},
        kpi_deltas=KPIDeltas(treasury_delta=-500_000.0),
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    assert new_state["active_event_flags"]["brsr_track_completed"] is True
    assert new_state["active_event_flags"]["brsr_grade"] == "A"


def test_existing_flags_preserved_after_merge(base_state):
    """Flags that existed before write-back must survive the merge."""
    payload = DataBridgeOutput(
        flags_to_set={"brsr_track_completed": True},
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    assert new_state["active_event_flags"]["existing_flag"] == "keep_me"


def test_flags_to_remove_deleted(base_state):
    """flags_to_remove entries must be removed from active_event_flags."""
    payload = DataBridgeOutput(
        flags_to_remove=["ethics_track_completed"],
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    assert "ethics_track_completed" not in new_state["active_event_flags"]


def test_flags_skipped_when_apply_flags_false(base_state):
    """With apply_flags=False, flags_to_set must not enter the new state."""
    payload = DataBridgeOutput(
        flags_to_set={"brsr_track_completed": True},
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert "brsr_track_completed" not in new_state.get("active_event_flags", {})


def test_flag_remove_is_idempotent(base_state):
    """Removing a flag that doesn't exist must not raise a KeyError.
    
    flags_to_remove keys must match a registered prefix (same as flags_to_set).
    We use 'ethics_track_completed' (registered: ethics_ prefix) and
    'ethics_nonexistent_xyz' (registered prefix, but key doesn't exist in state).
    """
    payload = DataBridgeOutput(
        flags_to_remove=["ethics_track_completed", "ethics_nonexistent_xyz"],
    )
    # Must complete without exception
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    assert "ethics_track_completed" not in new_state["active_event_flags"]


# ═══════════════════════════════════════════════════════════════════════════════
#  TYPE SAFETY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_invalid_payload_raises_type_error(base_state):
    """Passing a raw dict as payload must raise TypeError immediately."""
    with pytest.raises(TypeError, match="DataBridgeOutput"):
        apply_side_track_results(base_state, {"kpi_deltas": {}})


def test_empty_payload_is_a_clean_copy(base_state):
    """A fully-default DataBridgeOutput must produce a clean copy with no changes."""
    payload = DataBridgeOutput()
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    # All numeric KPIs unchanged
    assert new_state["corporate_treasury"] == base_state["corporate_treasury"]
    assert new_state["group_reputation"]   == base_state["group_reputation"]
    # Must be a copy, not same object
    assert new_state is not base_state


def test_kpi_overrides_rejects_out_of_bounds_reputation():
    """KPIOverrides must reject a reputation value > 100 at model construction time."""
    with pytest.raises(Exception):   # Pydantic ValidationError
        KPIOverrides(group_reputation=150.0)


def test_kpi_overrides_rejects_negative_reputation():
    """KPIOverrides must reject a negative reputation value at model construction time."""
    with pytest.raises(Exception):
        KPIOverrides(group_reputation=-5.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  CATASTROPHIC-SCENARIO REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_treasury_not_zeroed_by_override_with_no_override_set(base_state):
    """
    REGRESSION: A side track that only sets a reputation override must NOT
    accidentally zero the treasury (which was the risk with the old
    _pending_kpi_deltas / raw dict merge pattern).
    """
    payload = DataBridgeOutput(
        kpi_overrides=KPIOverrides(group_reputation=72.0),
        # No treasury field touched at all
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=False)
    assert new_state["corporate_treasury"] == base_state["corporate_treasury"], (
        "Treasury was wiped! A reputation-only override must never touch treasury."
    )


def test_large_treasury_delta_preserved_through_multi_field_payload(base_state):
    """
    Multi-field payloads must not cause field values to bleed between keys.
    treasury_delta=-2M should NOT affect reputation; reputation override=30
    should NOT affect treasury.
    """
    payload = DataBridgeOutput(
        kpi_deltas=KPIDeltas(treasury_delta=-2_000_000.0),
        kpi_overrides=KPIOverrides(group_reputation=30.0),
        flags_to_set={"ethics_track_completed": True},
    )
    new_state = apply_side_track_results(base_state, payload, apply_flags=True)
    assert new_state["corporate_treasury"] == pytest.approx(48_000_000.0), "Delta bled into wrong field"
    assert new_state["group_reputation"]   == 30.0,                        "Override bled into wrong field"
    assert new_state["avg_governance_risk"] == base_state["avg_governance_risk"], "Untouched field changed"
