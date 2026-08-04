"""The test-speed knob must never weaken a real deployment (G1).

WHAT G1 ACTUALLY WAS
--------------------
`test_twenty_players_can_actually_join` was deselected as a "full-suite hang".
It was not hanging. bcrypt at the production cost factor costs ~180 ms to hash
AND ~180 ms to verify; that one test performs 40 such operations, and the suite
as a whole performs thousands. It was simply paying for them — ~7 s for that
test locally and several times that on a slower CI runner, on top of an
already-long run. Store size was ruled out first: 10 joins cost the same with
0 sessions in the store as with 71, so it was never quadratic growth.

Dropping the cost to 4 under pytest took that test from 11.9 s to 1.6 s and the
whole suite from ~100 s to ~35 s, and the deselect is gone.

THE RISK THIS FILE GUARDS
-------------------------
A cheap cost factor is exactly the kind of setting that escapes a CI file into
a .env. At cost 4 a leaked registry is trivially crackable. So the override is
honoured ONLY inside a pytest process; anywhere else the floor is
PRODUCTION_ROUNDS regardless of what the environment asks for. That asymmetry
is the whole safety property, and it is what these tests pin.
"""
import sys

import pytest

import password_hashing as ph


def test_tests_run_cheap(monkeypatch):
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    assert ph.bcrypt_rounds() == 4
    assert "pytest" in sys.modules, "precondition: we are inside a test process"


def test_production_ignores_a_weakening_override(monkeypatch):
    """The safety property: outside pytest, 4 is refused and 12 is used."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    monkeypatch.setattr(ph, "_under_pytest", lambda: False)
    assert ph.bcrypt_rounds() == ph.PRODUCTION_ROUNDS


@pytest.mark.parametrize("value", ["1", "3", "0", "-5"])
def test_absurdly_low_values_are_clamped_then_refused(monkeypatch, value):
    monkeypatch.setenv("BCRYPT_ROUNDS", value)
    monkeypatch.setattr(ph, "_under_pytest", lambda: False)
    assert ph.bcrypt_rounds() == ph.PRODUCTION_ROUNDS


def test_a_STRONGER_override_is_honoured_everywhere(monkeypatch):
    """Raising the cost is always allowed — only weakening is gated."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "14")
    monkeypatch.setattr(ph, "_under_pytest", lambda: False)
    assert ph.bcrypt_rounds() == 14


@pytest.mark.parametrize("junk", ["", "   ", "twelve", "12.5", "None"])
def test_unset_or_junk_falls_back_to_production(monkeypatch, junk):
    monkeypatch.setenv("BCRYPT_ROUNDS", junk)
    monkeypatch.setattr(ph, "_under_pytest", lambda: False)
    assert ph.bcrypt_rounds() == ph.PRODUCTION_ROUNDS


def test_the_ceiling_stops_a_denial_of_service_by_config(monkeypatch):
    """cost 31 would take minutes per login and hang the whole platform."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "31")
    assert ph.bcrypt_rounds() == ph._MAX_ROUNDS


# ── the behaviour must be unchanged, only the price ────────────────────────

def test_hashes_still_verify_across_cost_factors(monkeypatch):
    """bcrypt stores the cost INSIDE the hash, so a cost-12 hash minted by
    production still verifies in a cost-4 test process. If that were not true,
    this change would invalidate every stored password."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "12")
    expensive = ph.hash_password("MUR-001@123")
    assert expensive.startswith("$2b$12$")

    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    cheap = ph.hash_password("MUR-001@123")
    assert cheap.startswith("$2b$04$")

    # both directions, both hashes
    assert ph.verify_password("MUR-001@123", expensive) is True
    assert ph.verify_password("MUR-001@123", cheap) is True
    assert ph.verify_password("wrong", expensive) is False
    assert ph.verify_password("wrong", cheap) is False


def test_the_default_is_still_twelve():
    """Nobody should be able to lower the production default by editing a
    constant without this failing."""
    assert ph.PRODUCTION_ROUNDS == 12
