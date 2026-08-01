"""Cohort scope (industry x region) must reach play — in BOTH storage modes.

THE DEFECT (reported: "stakeholder and CSRD excel files uploaded in god mode
are not correctly reflecting during play in the relevant cohorts")
------------------------------------------------------------------------------
Stakeholder and materiality resolution read the session's industry_vertical
and region_id FROM THE ROUND STATE (the engine only ever sees global_state).
database_memory.create_session seeds both into round-1 active_event_flags —
with a comment saying exactly why. The Postgres twin was never given that
edit, so under production Postgres every cohort's round rows carried no
scope: resolution found no vertical and no region, fell through to the
DEFAULT stakeholder set and the GLOBAL materiality dictionary, and every
admin-uploaded vertical/regional Excel config was silently invisible in play
— while the same cohort in memory mode showed them. Parity gap #4 (after
get_effective_settings, the God-Mode counters, and db._sessions).

Two halves pinned here:
  * SEEDING — both backends' create_session seed the two keys (source-shape
    tripwire on both files, behavioural check in memory mode).
  * HEALING — rounds created BEFORE the fix have no scope; the read paths
    hydrate it from the session record, which has always carried both values.
"""
import pathlib
import re

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[1]


# ── seeding: the shape that allowed the gap ────────────────────────────────

@pytest.mark.parametrize("fname", ["database_memory.py", "database.py"])
def test_create_session_seeds_scope_into_flags(fname):
    """Both create_session functions must put industry_vertical AND region_id
    into the round-1 flags. The gap existed because only one twin did."""
    src = (_BACKEND / fname).read_text(encoding="utf-8")
    i = src.index("async def create_session")
    j = src.index("async def", i + 10)
    body = src[i:j]
    assert re.search(r'"industry_vertical":\s*industry_vertical or ""', body), fname
    assert re.search(r'"region_id":\s*region_id or ""', body), fname


@pytest.mark.asyncio
async def test_memory_create_session_seeds_scope_behaviourally():
    import database_memory as dbm
    sess = await dbm.create_session(
        cohort_name="ScopeSeed-XYZ", facilitator_id="god_mode",
        industry_vertical="banking_financial_services", region_id="south_asia",
    )
    sid = str(sess["session_id"])
    try:
        latest = await dbm.fetch_latest_state(sid)
        flags = latest["global_state"]["active_event_flags"]
        assert flags.get("industry_vertical") == "banking_financial_services"
        assert flags.get("region_id") == "south_asia"
    finally:
        dbm._sessions.pop(sid, None)
        dbm._global_states.pop(sid, None)
        dbm._bu_states.pop(sid, None)


# ── healing: pre-fix rounds hydrate from the session record ────────────────

@pytest.mark.asyncio
async def test_hydration_backfills_scope_from_the_session_record():
    """Simulate a Postgres-era session: round flags carry NO scope, but the
    session record does. The hydration helper must backfill both keys."""
    import database_memory as dbm
    from router import _hydrate_scope_from_session

    sess = await dbm.create_session(
        cohort_name="ScopeHeal-XYZ", facilitator_id="god_mode",
        industry_vertical="oil_gas", region_id="europe",
    )
    sid = str(sess["session_id"])
    try:
        latest = await dbm.fetch_latest_state(sid)
        gs = latest["global_state"]
        # strip the seeded scope — the pre-fix Postgres shape
        gs.pop("industry_vertical", None)
        gs.pop("region_id", None)
        gs.get("active_event_flags", {}).pop("industry_vertical", None)
        gs.get("active_event_flags", {}).pop("region_id", None)

        healed = await _hydrate_scope_from_session(gs, sid)
        assert healed.get("industry_vertical") == "oil_gas"
        assert healed.get("region_id") == "europe"
    finally:
        dbm._sessions.pop(sid, None)
        dbm._global_states.pop(sid, None)
        dbm._bu_states.pop(sid, None)


@pytest.mark.asyncio
async def test_hydration_never_overwrites_scope_already_on_the_round():
    """A round that HAS scope keeps it — the session record is a fallback,
    not an override (a round's stored scope is the historical truth)."""
    import database_memory as dbm
    from router import _hydrate_scope_from_session

    sess = await dbm.create_session(
        cohort_name="ScopeKeep-XYZ", facilitator_id="god_mode",
        industry_vertical="technology", region_id="north_america",
    )
    sid = str(sess["session_id"])
    try:
        latest = await dbm.fetch_latest_state(sid)
        gs = latest["global_state"]
        healed = await _hydrate_scope_from_session(gs, sid)
        assert (healed.get("industry_vertical")
                or healed["active_event_flags"].get("industry_vertical")) == "technology"
    finally:
        dbm._sessions.pop(sid, None)
        dbm._global_states.pop(sid, None)
        dbm._bu_states.pop(sid, None)


@pytest.mark.asyncio
async def test_hydration_is_a_noop_for_scopeless_cohorts():
    import database_memory as dbm
    from router import _hydrate_scope_from_session

    sess = await dbm.create_session(cohort_name="NoScope-XYZ", facilitator_id="god_mode")
    sid = str(sess["session_id"])
    try:
        latest = await dbm.fetch_latest_state(sid)
        gs = latest["global_state"]
        healed = await _hydrate_scope_from_session(gs, sid)
        assert not healed.get("industry_vertical")
        assert not healed.get("region_id")
    finally:
        dbm._sessions.pop(sid, None)
        dbm._global_states.pop(sid, None)
        dbm._bu_states.pop(sid, None)


# ── the read paths actually use the hydration ──────────────────────────────

def test_all_three_read_boundaries_hydrate():
    """The stakeholder bank GET, the stakeholder-map scoring POST, and the
    materiality submit must each hydrate before resolving — a boundary that
    skips it re-opens the gap for pre-fix cohorts."""
    src = (_BACKEND / "router.py").read_text(encoding="utf-8")
    calls = src.count("_hydrate_scope_from_session(")
    # 1 definition + 3 router call sites (admin_router adds a 4th elsewhere)
    assert calls >= 4, f"expected the helper plus >=3 call sites, found {calls - 1} calls"
    admin_src = (_BACKEND / "admin_router.py").read_text(encoding="utf-8")
    assert "_hydrate_scope_from_session" in admin_src, (
        "the session-scoped materiality display endpoint must hydrate too")
