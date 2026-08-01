"""Materiality Packs — one double-materiality dictionary per SBU, per region.

Phases 2-4 of bringing the materiality framework to the Stakeholder Pack
standard. Phase 1 (durability) is pinned separately in
test_materiality_durability.py.

WHAT CHANGED
------------
  * Region axis. Materiality had NO region dimension: a grep for "region" in
    materiality_db returned only prose inside issue descriptions. But CSRD in
    Europe and BRSR in India weight the same issue differently, which is much
    of the point of teaching double materiality.
  * Packs. Previously the only way to give a cohort a bespoke dictionary was
    PUT /{session_id}/materiality-dictionary, which copies a whole dictionary
    INTO that cohort's state — no reuse, no single place to fix an error, and
    no way to tell two cohorts were running the same setup.

BACK-COMPATIBILITY IS THE POINT, as with stakeholders. No pack, unknown pack,
a pack missing a slot, or a pack naming a deleted config must all resolve
exactly as before, and never hand a live class an empty matrix. The explicit
per-BU cohort override must still beat a pack — a sandbox edit made for one
class should not be silently overridden by a pack chosen for it.
"""
import io
import os
import pathlib
import tempfile

import pytest

SLOTS = ["pharma", "electronics", "consumer_goods", "software"]


@pytest.fixture
def volume(monkeypatch):
    """A throwaway 'mounted volume'. materiality_db resolves CONFIG_DIR at
    import, so it is repointed explicitly — the same isolation lesson that an
    ad-hoc script taught by overwriting 13 real stakeholder configs."""
    vol = pathlib.Path(tempfile.mkdtemp(prefix="matvol_"))
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(vol))

    import materiality_db
    import materiality_packs
    cfg_dir = vol / "materiality_configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(materiality_db, "CONFIG_DIR", cfg_dir, raising=False)
    monkeypatch.setattr(materiality_db, "BU_CONFIG_FILES",
                        {b: cfg_dir / f"materiality_config_{b}.json"
                         for b in materiality_db.get_bu_ids()}, raising=False)
    materiality_db._cached_bu_configs = {}
    materiality_packs.invalidate_cache()
    yield vol
    materiality_db._cached_bu_configs = {}
    materiality_packs.invalidate_cache()


def _cfg(title: str) -> dict:
    return {
        "consultant_fee_usd": 1_000_000,
        "issues": [{"id": "iss1", "title": title, "category": "environmental",
                    "financial_impact": 50, "nature_of_impact": 50}],
        "interdependencies": [],
    }


# ── Phase 2: region axis ───────────────────────────────────────────────────

def test_regional_config_round_trips(volume):
    import materiality_db as m
    assert m.save_regional_bu_config("pharma", "europe", _cfg("EU pharma")) is True
    got = m.get_regional_bu_config("pharma", "europe")
    assert got["issues"][0]["title"] == "EU pharma"


def test_missing_region_falls_through_to_the_bu_matrix(volume):
    """Returns None — never {} — so the caller uses the plain BU config."""
    import materiality_db as m
    assert m.get_regional_bu_config("pharma", "south_asia") is None
    assert m.resolve_bu_config("pharma", "south_asia") == m.get_bu_config("pharma")


def test_region_wins_over_the_plain_bu_matrix(volume):
    import materiality_db as m
    m.save_regional_bu_config("pharma", "europe", _cfg("EU pharma"))
    assert m.resolve_bu_config("pharma", "europe")["issues"][0]["title"] == "EU pharma"


def test_no_region_argument_behaves_exactly_as_before(volume):
    import materiality_db as m
    assert m.resolve_bu_config("pharma") == m.get_bu_config("pharma")


def test_a_corrupt_regional_file_falls_back_rather_than_raising(volume):
    """A broken file must not take a live class down mid-round."""
    import materiality_db as m
    m._regional_path("pharma", "europe").write_text("{ not json", encoding="utf-8")
    assert m.get_regional_bu_config("pharma", "europe") is None
    assert m.resolve_bu_config("pharma", "europe")


def test_invalid_region_ids_are_refused(volume):
    import materiality_db as m
    for bad in ("Has Space", "sym!bol", ""):
        assert m.save_regional_bu_config("pharma", bad, _cfg("x")) is False


# ── Phase 3: packs ─────────────────────────────────────────────────────────

def test_pack_round_trips_and_is_case_insensitive(volume):
    from materiality_packs import save_pack, get_pack, delete_pack
    assert save_pack("EMEA_2026", "EMEA", "europe", {"pharma": "pharma__europe"})
    assert get_pack("EMEA_2026") is not None
    assert get_pack("emea_2026") is not None      # saved lowercase, read either way
    assert delete_pack("EMEA_2026") is True


def test_unknown_slots_are_dropped(volume):
    from materiality_packs import save_pack, get_pack
    save_pack("p1", "P", "europe", {"pharma": "pharma__europe", "not_a_slot": "x"})
    assert set(get_pack("p1")["bus"]) == {"pharma"}


def test_coverage_reports_missing_slots(volume):
    from materiality_packs import save_pack, pack_coverage
    save_pack("partial", "Partial", "europe", {"pharma": "pharma__europe"})
    cov = pack_coverage("partial")
    assert cov["complete"] is False
    assert set(cov["missing"]) == set(SLOTS) - {"pharma"}


def test_each_bu_resolves_its_own_dictionary(volume):
    from materiality_packs import save_pack, config_for_bu
    import materiality_db as m
    for slot in SLOTS:
        m.save_regional_bu_config(slot, "europe", _cfg(f"{slot} EU"))
    save_pack("emea", "EMEA", "europe", {s: f"{s}__europe" for s in SLOTS})

    titles = [config_for_bu("emea", s)["issues"][0]["title"] for s in SLOTS]
    assert titles == [f"{s} EU" for s in SLOTS]
    assert len(set(titles)) == len(SLOTS), "BUs shared a dictionary"


def test_delete_removes_the_pack_only(volume):
    """A pack is an index; deleting it must not delete a matrix."""
    import materiality_db as m
    from materiality_packs import save_pack, delete_pack
    m.save_regional_bu_config("pharma", "europe", _cfg("keep me"))
    save_pack("temp", "T", "europe", {"pharma": "pharma__europe"})
    assert delete_pack("temp") is True
    assert m.get_regional_bu_config("pharma", "europe")["issues"][0]["title"] == "keep me"


# ── back-compatibility: additive or it is a regression ─────────────────────

def test_no_pack_and_unknown_pack_both_fall_through(volume):
    from materiality_packs import config_for_bu
    assert config_for_bu("", "pharma") is None
    assert config_for_bu("does_not_exist", "pharma") is None


def test_pack_missing_a_slot_falls_through_for_that_slot(volume):
    from materiality_packs import save_pack, config_for_bu
    import materiality_db as m
    m.save_regional_bu_config("pharma", "europe", _cfg("EU pharma"))
    save_pack("half", "Half", "europe", {"pharma": "pharma__europe"})
    assert config_for_bu("half", "pharma") is not None
    assert config_for_bu("half", "software") is None   # → caller uses today's chain


def test_pack_naming_a_deleted_regional_config_degrades_to_the_bu_matrix(volume):
    """The failure that would hurt most is an empty matrix in a live class."""
    from materiality_packs import save_pack, config_for_bu
    save_pack("ghost", "Ghost", "europe", {"pharma": "pharma__europe"})
    cfg = config_for_bu("ghost", "pharma")     # no regional file was ever written
    assert cfg is None or cfg.get("issues"), "resolution produced an empty matrix"


def test_pack_naming_an_unknown_bu_returns_none_not_an_exception(volume):
    from materiality_packs import save_pack, config_for_bu
    save_pack("odd", "Odd", "europe", {"pharma": "no_such_bu"})
    assert config_for_bu("odd", "pharma") is None


def test_pack_id_is_a_cohort_setting():
    from admin_shared import COHORT_OVERRIDABLE_KEYS
    assert "materiality_pack_id" in COHORT_OVERRIDABLE_KEYS


def test_explicit_cohort_override_still_beats_a_pack():
    """The per-BU cohort override resolves BEFORE the pack. A sandbox edit made
    for one class must not be silently replaced.

    2026-07-31: the chain moved from router.submit_materiality_matrix into
    materiality_packs.resolve_session_bu_config so the display endpoint
    resolves identically (a player must be SHOWN the dictionary they are
    SCORED on) — the ordering property is now pinned on the helper, and both
    call sites are pinned to actually use it."""
    import inspect
    from materiality_packs import resolve_session_bu_config
    src = inspect.getsource(resolve_session_bu_config)
    # Anchor on the CALL expressions, not bare names — the docstring mentions
    # the function names too and index() would match prose before code.
    i_override = src.index('return global_state[override_key]')
    i_pack = src.index('cfg = config_for_bu(')
    i_bu = src.index('cfg = mat_db.resolve_bu_config(')
    assert i_override < i_pack < i_bu

    router_src = (pathlib.Path(__file__).resolve().parents[1] / "router.py").read_text(encoding="utf-8")
    assert "resolve_session_bu_config(global_state, body.bu_id)" in router_src
    admin_src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    assert "resolve_session_bu_config(_gs, bu_id)" in admin_src


def test_resolve_session_bu_config_behaviour(volume):
    """Behavioural pin of the chain, not just its source order."""
    import materiality_db as m
    from materiality_packs import save_pack, resolve_session_bu_config

    m.save_regional_bu_config("pharma", "europe", _cfg("regional"))
    save_pack("p", "P", "europe", {"pharma": "pharma__europe"})

    # pack wins when set on the session
    gs = {"materiality_pack_id": "p"}
    assert resolve_session_bu_config(gs, "pharma")["issues"][0]["title"] == "regional"

    # explicit cohort override beats the pack
    gs["materiality_dictionary_override_pharma"] = _cfg("sandbox override")
    assert resolve_session_bu_config(gs, "pharma")["issues"][0]["title"] == "sandbox override"

    # region (via flags) without a pack
    gs2 = {"active_event_flags": {"region_id": "europe"}}
    assert resolve_session_bu_config(gs2, "pharma")["issues"][0]["title"] == "regional"

    # nothing configured → plain BU matrix, exactly as before
    gs3 = {}
    assert resolve_session_bu_config(gs3, "pharma") == m.get_bu_config("pharma")
