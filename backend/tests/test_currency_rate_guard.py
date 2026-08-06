"""The stored conversion factor cannot be a value that breaks the product.

WHY A SERVER-SIDE GUARD WHEN THE CLIENT ALREADY HAS ONE
    The client refuses a bad rate, but the client is not where it is STORED.
    A zero persisted on the session renders every treasury, allocation and
    option cost as 0 for that cohort, on every screen, with nothing in any log
    — and it reads as an engine failure rather than a config one. A negative
    inverts every figure and, because several surfaces colour by sign, every
    good/bad colour with it.

SCOPE
    This is presentation. The engine keeps computing in engine units; the rate
    is applied at the frontend's format boundary. Nothing here touches
    simulation logic.
"""
import os

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")

import admin_router  # noqa: E402


def _model():
    """The settings model that carries currency_rate, found by field rather
    than by name so a rename does not silently skip this whole file."""
    import pydantic
    for obj in vars(admin_router).values():
        if isinstance(obj, type) and issubclass(obj, pydantic.BaseModel):
            fields = getattr(obj, "model_fields", None) or getattr(obj, "__fields__", {})
            if "currency_rate" in fields:
                return obj
    raise AssertionError("no settings model carries currency_rate")


M = _model()


@pytest.mark.parametrize("bad", [0, 0.0, -1, -83.0])
def test_zero_and_negative_are_refused(bad):
    assert M(currency_rate=bad).currency_rate is None


def test_absent_stays_absent_rather_than_becoming_one():
    # "Not configured" and "a rate of exactly one" are different states. The
    # client leaves the previous value alone for the first and resets for the
    # second; collapsing them here would remove that distinction.
    assert M().currency_rate is None
    assert M(currency_rate=None).currency_rate is None


def test_a_real_rate_survives_unchanged():
    assert M(currency_rate=83).currency_rate == pytest.approx(83.0)
    assert M(currency_rate=1).currency_rate == pytest.approx(1.0)
    assert M(currency_rate=0.011).currency_rate == pytest.approx(0.011)


def test_the_bounds_are_wide_on_purpose():
    """A facilitator may want a round 100x factor to make arithmetic legible.

    This is a teaching parameter, not a market rate, so the guard only stops
    values that break the product — not values that look unusual.
    """
    assert M(currency_rate=100).currency_rate == pytest.approx(100.0)
    assert M(currency_rate=1_000_000).currency_rate == pytest.approx(1_000_000.0)


def test_it_is_editable_from_the_cohort_editor():
    """The field being on the model is not enough — a separate allowlist
    decides what the edit form may actually save, and it has silently dropped
    fields before (the stakeholder/materiality pack IDs)."""
    import inspect
    src = inspect.getsource(admin_router)
    assert '"currency_rate"' in src.split("EDITABLE = {")[1].split("}")[0]
