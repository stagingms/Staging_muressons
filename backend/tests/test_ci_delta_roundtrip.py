"""CI-delta application and serialization — the round-7 stall (BUG-2026-07-20).

Two coupled defects in one line, at BOTH call sites of the pure helper
engine.apply_ci_delta_to_bus (round_logic option impacts and side-track
impacts):

  1. The pure function's new_carbon_intensities was never written back, so
     option-driven CI deltas were silently DROPPED whenever the real engine
     imported (the test-context fallback shim mutates, masking this).
  2. The raw CIDeltaResult dataclass was stored into active_event_flags.
     The memory store's serializer tolerates dataclasses; Postgres json.dumps
     did not → "Failed to persist round: Object of type CIDeltaResult is not
     JSON serializable" at scope3_weighted rounds (R3/R7). Cohorts stalled.

These tests pin the wrapper's contract, both call sites, and the store-parity
serializer, so neither half can regress silently.
"""
import json
import pathlib
import re

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1]


# ── The wrapper contract ────────────────────────────────────────────────────

def _bus():
    return [
        {"bu_id": "pharma", "carbon_intensity": 50.0},
        {"bu_id": "electronics", "carbon_intensity": 80.0},
        {"bu_id": "oil_gas", "carbon_intensity": 120.0},
    ]


def test_in_place_wrapper_actually_applies_the_delta():
    """Defect #1: with the pure helper called bare, every one of these values
    stayed unchanged and the option's climate consequence never happened."""
    from engine import apply_ci_delta_in_place
    bus = _bus()
    before = {b["bu_id"]: b["carbon_intensity"] for b in bus}
    applied = apply_ci_delta_in_place(bus, -10, routing="uniform")
    for b in bus:
        assert b["carbon_intensity"] == before[b["bu_id"]] - 10, \
            f"{b['bu_id']}: delta was not applied to the BU state"
    assert applied == {"pharma": -10, "electronics": -10, "oil_gas": -10}


def test_in_place_wrapper_scope3_weighting_differs_per_bu():
    from engine import apply_ci_delta_in_place
    bus = _bus()
    applied = apply_ci_delta_in_place(bus, -10, routing="scope3_weighted")
    # Scope3-heavy electronics must benefit more than scope1-heavy oil_gas.
    assert applied["electronics"] < applied["oil_gas"] < 0
    for b in bus:
        assert b["carbon_intensity"] < {"pharma": 50, "electronics": 80, "oil_gas": 120}[b["bu_id"]]


def test_in_place_wrapper_returns_json_safe_plain_dict():
    """Defect #2: the bare helper's return value was stored in flags. The
    wrapper must return something a bare json.dumps accepts."""
    from engine import apply_ci_delta_in_place
    applied = apply_ci_delta_in_place(_bus(), -10, routing="scope3_weighted")
    assert type(applied) is dict
    json.dumps(applied)  # must not raise — this exact call failed in production


def test_pure_helper_is_still_pure():
    """The wrapper must not have compromised the original contract — other
    callers may rely on purity."""
    from engine import apply_ci_delta_to_bus
    bus = _bus()
    before = [dict(b) for b in bus]
    result = apply_ci_delta_to_bus(bus, -10, routing="uniform")
    assert bus == before, "apply_ci_delta_to_bus mutated its input"
    assert result.new_carbon_intensities["pharma"] == 40.0


# ── Call-site pins (source-level: a revert is invisible at runtime because
#    the fallback shim masks it) ─────────────────────────────────────────────

def test_round_logic_uses_the_in_place_wrapper():
    src = (BACKEND / "round_logic.py").read_text(encoding="utf-8")
    assert "from engine import apply_ci_delta_in_place" in src, \
        "round_logic must import the IN-PLACE wrapper, not the pure helper"


def test_side_tracks_use_the_in_place_wrapper():
    src = (BACKEND / "side_tracks" / "base_track.py").read_text(encoding="utf-8")
    assert "apply_ci_delta_in_place" in src
    assert not re.search(r"=\s*apply_ci_delta_to_bus\(", src), \
        "base_track stores the PURE helper's dataclass return into flags again"


# ── Store-parity serialization ──────────────────────────────────────────────

def test_postgres_dumps_matches_memory_store_tolerance():
    """database._dumps must accept everything database_memory's serializer
    accepts, or the same leak persists locally and 500s only on Railway."""
    from datetime import datetime
    from dataclasses import dataclass
    # conftest aliases sys.modules["database"] to the MEMORY store; load the
    # real Postgres module from its file so we test the actual code under test.
    import importlib.util
    spec = importlib.util.spec_from_file_location("database_real", BACKEND / "database.py")
    _real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_real)
    _dumps = _real._dumps

    @dataclass(frozen=True)
    class Probe:
        applied_deltas: dict
        new_carbon_intensities: dict

    flags = {
        "carbon_intensity_by_bu_r7": Probe({"pharma": -1.5}, {"pharma": 48.5}),
        "stamp": datetime(2026, 7, 20, 12, 0, 0),
        "ids": {"a", "b"},
    }
    out = json.loads(_dumps(flags))
    assert out["carbon_intensity_by_bu_r7"]["applied_deltas"]["pharma"] == -1.5
    assert out["stamp"].startswith("2026-07-20")
    assert out["ids"] == ["a", "b"]


def test_every_state_dump_in_database_py_uses_the_tolerant_serializer():
    """A future json.dumps( added to database.py reintroduces the divergence."""
    src = (BACKEND / "database.py").read_text(encoding="utf-8")
    bare = [
        ln for ln in src.splitlines()
        if "json.dumps(" in ln and "_json_default" not in ln and not ln.strip().startswith("#")
    ]
    assert not bare, f"bare json.dumps in database.py — use _dumps: {bare}"
