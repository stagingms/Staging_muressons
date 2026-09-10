"""
Muressons Global Corporation — In-Memory Database Service
Drop-in replacement for database.py when PostgreSQL is unavailable.
Stores all state in Python dicts with automatic JSON file persistence.
Data survives server restarts via snapshot file.
"""

from __future__ import annotations
import copy
import json
import uuid
import pathlib
import threading
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
from config import SIM_INITIAL_BUDGET, SIM_ROUNDS



# ── Persistence Config ──────────────────────────────────────────

# QA-2026-07-16 #3: snapshot lives in the durable data dir (MURESSONS_DATA_DIR,
# default <repo>/db -- unchanged locally) so an intentional memory-mode run on a
# volume survives a redeploy.
from runtime_paths import data_file as _data_file
_SNAPSHOT_PATH = _data_file("memory_snapshot.json")
# RES-1: rolling one-generation backup of the last-known-good snapshot.
_BACKUP_PATH = _SNAPSHOT_PATH.with_suffix(".bak")
_save_lock = threading.Lock()
_async_write_lock = asyncio.Lock()


# ── Seed Data ───────────────────────────────────────────────────

def _load_seed(industry: str = "generic") -> dict:
    """Load the Round 1 seed JSON depending on selected industry.

    LOW-004: The industry parameter is validated against an explicit allowlist
    before any file path is constructed.  Any unrecognised value silently
    normalises to "generic" so callers never cause path-traversal by passing
    untrusted strings such as "../../../etc/passwd".
    """
    # Explicit allowlist — add new industries here as seed files are created.
    _ALLOWED = {"healthcare": "seed_healthcare.json"}
    _DEFAULT = "seed_round1.json"

    if industry not in _ALLOWED and industry != "generic":
        import logging as _logging
        _logging.getLogger("muressons.db").warning(
            "[SEED] Unknown industry %r — falling back to generic seed.", industry
        )

    filename = _ALLOWED.get(industry, _DEFAULT)
    seed_path = pathlib.Path(__file__).resolve().parent.parent / "db" / filename
    with open(seed_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ── In-Memory Stores ────────────────────────────────────────────

_sessions = {}
_global_states = {}      # session_id → [round_states]
_bu_states = {} # session_id → {round_num → [bu_dicts]}
_decision_log = []


# ── Persistence Helpers ─────────────────────────────────────────

def _datetime_serializer(obj):
    """JSON serializer for datetime objects and dataclass instances.

    Extended to handle frozen dataclasses (e.g. engine.CIDeltaResult) which
    appear in _global_states after process_tick runs.  They don't need to
    round-trip from disk — converting to a plain dict on save is sufficient
    since the engine recomputes them fresh each tick.
    """
    if isinstance(obj, datetime):
        return {"__datetime__": obj.isoformat()}
    import dataclasses as _dc
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        return _dc.asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _datetime_deserializer(obj):
    """JSON object hook to restore datetime objects."""
    if "__datetime__" in obj:
        return datetime.fromisoformat(obj["__datetime__"])
    return obj


# F-15: the BU keys fetch_latest_state / fetch_round_history serialise
# explicitly. Every OTHER key on a stored BU dict is passed through verbatim,
# mirroring database.py's risk_factors pack/unpack, so the two stores expose
# the same BU shape to the engine.
_BU_EXPLICIT_READ_KEYS: frozenset[str] = frozenset({
    "bu_id", "revenue_base", "opex_base", "natural_capital_debt",
    "social_license_score", "reputation_score", "governance_risk_score",
    "water_dependency", "carbon_intensity", "staff_burnout_index",
    "bed_capacity_utilization", "patient_outcomes_score", "basic_needs",
    "human_capital", "sustainable_growth", "planet", "governance",
    "partnerships", "population", "migration_pressure",
    "institutional_leakage_multiplier", "sanitation_miracle_bonus",
    "risk_factors",
})


# ── F-29 (launch audit 2026-09-01): debounced, off-loop snapshot writes ──────
# _persist() used to serialise the ENTIRE store to JSON and write it to disk,
# synchronously on the event loop, on every one of its 13 call sites — a
# 40-team memory-mode workshop measured ~1 commit/s because each commit paid
# for several full snapshots. Now a call marks the store dirty and schedules
# ONE write after a quiet window (MURESSONS_SNAPSHOT_DEBOUNCE_MS, default 500;
# 0 = immediate, which the test suite uses). The JSON is still encoded on the
# loop (the dicts are only ever mutated there, so no concurrent-mutation
# hazard), but the file write happens in a worker thread. flush_snapshot()
# forces a write (called at shutdown).
import os as _os

_SNAPSHOT_DEBOUNCE_S = max(0.0, float(_os.getenv("MURESSONS_SNAPSHOT_DEBOUNCE_MS", "500")) / 1000.0)
_snapshot_dirty = False
_snapshot_timer = None          # asyncio.TimerHandle while a write is scheduled
_snapshot_stats = {"requested": 0, "written": 0}


def _persist():
    """Request a snapshot. Coalesced: many calls inside the debounce window
    produce one write. Falls back to an immediate write when there is no
    running event loop (sync callers, tests) or the debounce is 0."""
    global _snapshot_dirty, _snapshot_timer
    _snapshot_stats["requested"] += 1
    _snapshot_dirty = True
    if _SNAPSHOT_DEBOUNCE_S <= 0:
        _write_snapshot_now()
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        _write_snapshot_now()
        return
    if _snapshot_timer is not None:
        return                      # a write is already scheduled — coalesce
    _snapshot_timer = loop.call_later(_SNAPSHOT_DEBOUNCE_S, _scheduled_snapshot_write)


def _scheduled_snapshot_write() -> None:
    global _snapshot_timer
    _snapshot_timer = None
    if _snapshot_dirty:
        _write_snapshot_now()


def flush_snapshot() -> None:
    """Write immediately if anything is pending (shutdown / tests)."""
    global _snapshot_timer
    if _snapshot_timer is not None:
        try:
            _snapshot_timer.cancel()
        except Exception:
            pass
        _snapshot_timer = None
    if _snapshot_dirty:
        _write_snapshot_now()


def _write_snapshot_now():
    """Save all in-memory stores to disk as a JSON snapshot."""
    global _snapshot_dirty
    _snapshot_dirty = False
    _snapshot_stats["written"] += 1
    with _save_lock:
        try:
            # FIX BUG-6: Copy-on-write snapshot — prevent dict mutation during iteration
            sessions_snap = dict(_sessions)
            gs_snap = {k: list(v) for k, v in dict(_global_states).items()}
            bu_serializable = {}
            for sid, rounds in dict(_bu_states).items():
                bu_serializable[sid] = {str(rn): list(bus) for rn, bus in dict(rounds).items()}
            dl_snap = list(_decision_log)

            import admin_shared
            # Fix #5: pacing policy + God-Mode settings are live-run coordination
            # state; snapshot them so a restart/redeploy does not drop a cohort's
            # unlock/freeze state (audit §1.1). Pacing is stored via the JSON-safe
            # helper that strips per-process asyncio timer handles.
            try:
                _round_pacing_snap = admin_shared.all_pacing_policies()
                _godmode_snap = admin_shared.godmode_settings_snapshot()
            except Exception:
                _round_pacing_snap, _godmode_snap = {}, {}
            # MEDIUM-tier: per-cohort overrides + settings templates are setup
            # state a facilitator invested real time in — snapshot them so a
            # restart doesn't silently revert cohorts to global defaults.
            try:
                _cohort_settings_snap = {sid: dict(o) for sid, o in dict(admin_shared.cohort_settings).items()}
                _cohort_templates_snap = admin_shared.cohort_templates_snapshot()
            except Exception:
                _cohort_settings_snap, _cohort_templates_snap = {}, {}
            snapshot = {
                "sessions": sessions_snap,
                "global_states": gs_snap,
                "bu_states": bu_serializable,
                "decision_log": dl_snap,
                "cohort_marketplaces": getattr(admin_shared, "_cohort_marketplaces", {}),
                "round_pacing": _round_pacing_snap,
                "god_mode_settings": _godmode_snap,
                "cohort_settings": _cohort_settings_snap,
                "cohort_templates": _cohort_templates_snap,
            }
            _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            # Encode on the calling thread (state is consistent here); the disk
            # work below is handed to a worker thread when a loop is running.
            payload = json.dumps(snapshot, default=_datetime_serializer, ensure_ascii=False).encode("utf-8")

            def _write_to_disk(_payload=payload):
                tmp_path = _SNAPSHOT_PATH.with_suffix(".tmp")
                with open(tmp_path, "wb") as f:
                    f.write(_payload)
                # RES-1: rotate the current last-known-good snapshot into a rolling
                # backup BEFORE overwriting it, so a future unreadable primary can be
                # recovered from _BACKUP_PATH instead of silently losing all state.
                try:
                    if _SNAPSHOT_PATH.exists():
                        import shutil
                        shutil.copy2(_SNAPSHOT_PATH, _BACKUP_PATH)
                except Exception as _bak_err:
                    print(f"[persistence] Backup rotation skipped: {_bak_err}")
                import time
                for _ in range(5):
                    try:
                        tmp_path.replace(_SNAPSHOT_PATH)  # atomic rename
                        break
                    except OSError:
                        time.sleep(0.05)

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None and _SNAPSHOT_DEBOUNCE_S > 0:
                def _bg():
                    try:
                        _write_to_disk()
                    except Exception as exc:  # report from the worker thread too
                        try:
                            from admin_shared import record_persistence_failure
                            record_persistence_failure("memory_snapshot", exc, str(_SNAPSHOT_PATH))
                        except Exception:
                            print(f"[persistence] Failed to save snapshot: {exc}")
                loop.run_in_executor(None, _bg)
            else:
                _write_to_disk()
        except Exception as e:
            try:
                from admin_shared import record_persistence_failure
                record_persistence_failure("memory_snapshot", e, str(_SNAPSHOT_PATH))
            except Exception:  # pragma: no cover — admin_shared not importable
                print(f"[persistence] Failed to save snapshot: {e}")


def _apply_snapshot(snapshot: dict) -> int:
    """Populate the in-memory stores from a parsed snapshot dict.

    Builds everything into locals first and commits to the module globals only
    at the end, so a malformed snapshot can never leave a half-applied state.
    Returns the number of top-level cohorts restored."""
    sessions = snapshot.get("sessions", {})
    global_states = snapshot.get("global_states", {})
    decision_log = snapshot.get("decision_log", [])
    raw_bu = snapshot.get("bu_states", {})
    bu_states = {}
    for sid, rounds in raw_bu.items():
        bu_states[sid] = {int(rn): bus for rn, bus in rounds.items()}

    global _sessions, _global_states, _bu_states, _decision_log
    _sessions = sessions
    _global_states = global_states
    _decision_log = decision_log
    _bu_states.clear()
    _bu_states.update(bu_states)

    # Restore cohort_marketplaces (best-effort -- never fail the whole restore).
    try:
        import admin_shared
        admin_shared._cohort_marketplaces.clear()
        admin_shared._cohort_marketplaces.update(snapshot.get("cohort_marketplaces", {}))
        admin_shared._shared_marketplace = admin_shared._cohort_marketplaces.setdefault("default", {
            "carbon_credit_pool": {
                "total_available": 500,
                "price_per_credit": 50_000,
                "purchased": {},
                "price_history": [50_000],
            },
            "green_talent_pool": {
                "total_available": 100,
                "cost_per_hire": 200_000,
                "hired": {},
                "cost_history": [200_000],
            },
        })
    except Exception as e:
        print(f"[persistence] Failed to restore marketplace: {e}")

    # Fix #5: restore live-run coordination state (pacing + God-Mode settings)
    # so a restart keeps a cohort's unlock/freeze state. Best-effort — never
    # fail the whole restore over coordination state.
    try:
        import admin_shared
        gm = snapshot.get("god_mode_settings")
        if isinstance(gm, dict):
            admin_shared.restore_godmode_settings(gm)
        pacing_map = snapshot.get("round_pacing")
        if isinstance(pacing_map, dict):
            for _sid, _policy in pacing_map.items():
                admin_shared.restore_pacing_policy(_sid, _policy)
        # MEDIUM-tier: restore per-cohort overrides + settings templates.
        cs = snapshot.get("cohort_settings")
        if isinstance(cs, dict):
            for _sid, _ov in cs.items():
                if isinstance(_ov, dict):
                    admin_shared.cohort_settings.setdefault(_sid, {}).update(_ov)
        admin_shared.restore_cohort_templates(snapshot.get("cohort_templates") or {})
    except Exception as e:
        print(f"[persistence] Failed to restore pacing/god-mode state: {e}")

    _cleanup_expired_records()
    return len([s for s in _sessions.values() if not s.get("parent_cohort_id")])


def _read_snapshot(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read(), object_hook=_datetime_deserializer)


def _quarantine_corrupt(path):
    """Move an unreadable snapshot aside so it is preserved for inspection and
    never re-loaded. Returns the quarantine path, or None on failure."""
    try:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = path.with_name(f"{path.stem}.corrupt-{ts}{path.suffix}")
        path.rename(dest)
        return dest
    except Exception as e:
        print(f"[persistence] Could not quarantine corrupt snapshot: {e}")
        return None


def _load_from_disk():
    """Restore the in-memory stores from disk.

    RES-1: a corrupt/unreadable primary snapshot must NEVER cause a silent empty
    boot. On failure we log loudly, quarantine the bad file, and try the rolling
    backup (_BACKUP_PATH) before -- as a last resort -- starting empty with an
    unmissable notice."""
    main = _SNAPSHOT_PATH
    bak = _BACKUP_PATH
    quarantined = None

    if main.exists():
        try:
            n = _apply_snapshot(_read_snapshot(main))
            print(f"[persistence] Restored {n} cohort(s) from snapshot.")
            return
        except Exception as e:
            print(
                "\n============================================================\n"
                "  RES-1 -- PRIMARY SNAPSHOT UNREADABLE.\n"
                "  Saved session state could not be loaded; attempting recovery\n"
                "  from the rolling backup before starting empty.\n"
                "============================================================\n"
                f"[persistence] Load error: {e}"
            )
            quarantined = _quarantine_corrupt(main)
    elif not bak.exists():
        return  # No snapshot at all -- normal first run / fresh start.

    if bak.exists():
        try:
            n = _apply_snapshot(_read_snapshot(bak))
            msg = f"[persistence] RECOVERED {n} cohort(s) from the BACKUP snapshot after the primary was unusable"
            if quarantined:
                msg += f" (corrupt primary quarantined at {quarantined.name})"
            print(msg + ".")
            return
        except Exception as e2:
            print(f"[persistence] Backup snapshot ALSO unreadable: {e2}")

    # Last resort: start empty, but NEVER silently.
    global _sessions, _global_states, _decision_log
    _sessions = {}
    _global_states = {}
    _decision_log = []
    _bu_states.clear()
    print(
        "\n============================================================\n"
        "  RES-1 -- STARTING WITH EMPTY STATE.\n"
        "  No usable snapshot or backup was found. Any prior data has\n"
        "  been PRESERVED (not overwritten).\n"
        "============================================================"
        + (f"\n[persistence] Corrupt snapshot preserved at: {quarantined}" if quarantined else "")
    )

from datetime import timedelta
def _cleanup_expired_records():
    """Hard delete records that were soft-deleted more than 7 days ago."""
    global _sessions, _global_states, _bu_states, _decision_log
    now = datetime.now(timezone.utc)
    expired_sids = []
    
    for sid, sess in list(_sessions.items()):
        deleted_at_str = sess.get("deleted_at")
        if deleted_at_str:
            try:
                deleted_at = datetime.fromisoformat(deleted_at_str)
                if now - deleted_at > timedelta(days=7):
                    expired_sids.append(sid)
            except Exception:
                pass
                
    for sid in expired_sids:
        _sessions.pop(sid, None)
        _global_states.pop(sid, None)
        _bu_states.pop(sid, None)
        
    if expired_sids:
        _decision_log = [d for d in _decision_log if d.get("session_id") not in expired_sids]
        print(f"[persistence] Hard deleted {len(expired_sids)} expired sessions.")

# ── Short Join Codes ─────────────────────────────────────────────
_join_codes = {}  # join_code → session_id

def _generate_join_code() -> str:
    """Generate a unique 6-char uppercase alphanumeric join code."""
    import random, string
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in _join_codes:
            return code

async def resolve_join_code(code: str) -> Optional[str]:
    """Resolve a short join code to a session_id. Returns None if not found."""
    return _join_codes.get(code.upper())

# ── Auto-load on import ────────────────────────────────────────
_load_from_disk()


# ── Pool stubs (no-ops for compatibility) ───────────────────────

async def get_pool():
    return None

async def close_pool():
    pass


# ── SEC-5: Advisory-lock stubs (memory mode is single-process) ──
# In-memory mode runs in a single process, where router.py's asyncio.Lock
# already provides full serialization. These return a sentinel so the
# composite lock's acquire path always "succeeds" without a DB round-trip.
_MEMORY_LOCK_SENTINEL = object()


async def acquire_advisory_lock(session_id: str):
    """No-op cross-process lock for memory mode (always acquires)."""
    return _MEMORY_LOCK_SENTINEL


async def release_advisory_lock(conn, session_id: str) -> None:
    """No-op release for memory mode."""
    return None


# ── Session Short Code Generator ───────────────────────────────

import random as _random
import string as _string

def _generate_short_code() -> str:
    """Generate a unique human-friendly session identifier like SIM-A3K7."""
    existing_codes = {s.get("short_code") for s in list(_sessions.values())}
    for _ in range(1000):
        code = "SIM-" + "".join(_random.choices(_string.ascii_uppercase + _string.digits, k=4))
        if code not in existing_codes:
            return code
    # Fallback: extend to 6 chars
    return "SIM-" + "".join(_random.choices(_string.ascii_uppercase + _string.digits, k=6))


# ── Session Operations ──────────────────────────────────────────

async def create_session(
    cohort_name: str, 
    facilitator_id: Optional[str] = None,
    loan_interest_rate: float = 0.12,
    player_id: Optional[str] = None,
    parent_cohort_id: Optional[str] = None,
    decision_paradigm: str = "legacy_abc",
    currency_symbol: str = "$",
    scenario_preset: Optional[str] = None,
    experience_level: Optional[str] = None,
    difficulty_tier: Optional[str] = None,
    created_by: Optional[str] = None,
    created_when: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    assigned_bu: Optional[str] = None,
    region_id: Optional[str] = None,
    simulation_mode: Optional[str] = None,
    industry_vertical: Optional[str] = None,
    rules_version: Optional[str] = None,
) -> dict:
    """
    Create a new session and seed Round 1 state.
    Returns a dict ready for the API response.
    """
    # Prevent duplicate cohort names for top-level sessions
    if not parent_cohort_id:
        for existing in list(_sessions.values()):
            if (existing["cohort_name"].strip().lower() == cohort_name.strip().lower()
                    and not existing.get("parent_cohort_id")):
                raise ValueError(f"A cohort named '{cohort_name}' already exists.")

    if decision_paradigm == "brsr_ngrbc" and currency_symbol == "$":
        currency_symbol = "₹"

    from admin_shared import _god_mode_settings
    from rules import CURRENT_VERSION as _CURRENT_RULES_VERSION
    # Determine industry/seed based on the requested decision paradigm.
    # Paradigm-specific seeds take priority over the global god-mode industry setting.
    _PARADIGM_INDUSTRY_MAP = {"healthcare": "healthcare"}
    industry = _PARADIGM_INDUSTRY_MAP.get(decision_paradigm, _god_mode_settings.get("industry", "generic"))
    seed = _load_seed(industry=industry)
    session_id = str(uuid.uuid4())
    global_state_id = str(uuid.uuid4())

    gs = seed["global_state"]

    # Generate a friendly short code for top-level cohort sessions
    short_code = _generate_short_code() if not parent_cohort_id else None

    # ── Anti-gaming: generate per-session option shuffle seed ──
    from option_shuffle import generate_shuffle_seed
    _shuffle_seed = generate_shuffle_seed()

    from config_introspect import run_provenance as _run_provenance
    from rng_util import resolve_or_derive_seed as _resolve_or_derive_seed

    _sessions[session_id] = {
        "session_id": session_id,
        "short_code": short_code,
        "cohort_name": cohort_name,
        "facilitator_id": facilitator_id,
        "start_time": datetime.now(timezone.utc),
        "is_public": False,
        "allowed_player_ids": [],
        "player_id": player_id,
        "parent_cohort_id": parent_cohort_id,
        "decision_paradigm": decision_paradigm,
        "currency_symbol": currency_symbol,
        "scenario_preset": scenario_preset,
        "experience_level": experience_level,
        "difficulty_tier": difficulty_tier or "advanced",
        # Phase 4 (dead-flag remediation): the rule set this session is
        # pinned to for its whole life. Sessions created before this key
        # existed have no value and resolve to rules.DEFAULT_RULES_VERSION,
        # which IS the semantics they were played under.
        "rules_version": rules_version or _CURRENT_RULES_VERSION,
        "created_by": created_by,
        "created_when": created_when,
        "start_date": start_date,
        "end_date": end_date,
        "shuffle_seed": _shuffle_seed,
        "assigned_bu": assigned_bu or "",
        "region_id": region_id or "",
        "simulation_mode": simulation_mode or "",
        "industry_vertical": industry_vertical or "",
        # 4.7 (2026-08-03): stamp what produced this run, at the moment it is
        # true. Seed + config fingerprint + code version are the three things
        # that decide the numbers a cohort sees; a finished session recorded
        # none of them, so two runs a month apart with a config change between
        # them were indistinguishable in the database. Computed from the SAME
        # resolver the engine's seed comes from, so provenance cannot claim a
        # seed the run did not use.
        "run_provenance": _run_provenance(
            _resolve_or_derive_seed(gs.get("active_event_flags"),
                                    parent_cohort_id or session_id)),
    }

    bus = copy.deepcopy(seed["business_units"])
    if assigned_bu:
        # Resolve the seed slot and (optional) substitute vertical this session
        # scopes to. assigned_bu is normally a seed slot id (normalised via
        # VERTICAL_SLOT_MAP at the API layer), but legacy cohorts may still
        # carry a raw vertical id (e.g. 'retail_fmcg').
        _slot = assigned_bu
        _vertical = (industry_vertical or "").strip()
        try:
            from bu_profiles import SLOT_FIT_MAP, BU_PROFILES, build_bu_states
            _seed_ids = {b.get("bu_id") for b in bus}
            if _slot not in _seed_ids:
                # Legacy path: assigned_bu is itself a vertical id — derive its
                # owning slot from the single source of truth (SLOT_FIT_MAP).
                _vertical = _vertical or _slot
                _slot = next(
                    (s for s, vs in SLOT_FIT_MAP.items() if _slot == s or _slot in vs),
                    _slot,
                )
            if (
                simulation_mode == "single_bu"
                and _vertical
                and _vertical != _slot
                and _vertical in BU_PROFILES
            ):
                # Single-BU with a substitute vertical: the player's one BU
                # carries the VERTICAL's profile (stats/label/icon) — consistent
                # with how 4-BU substitution applies vertical profiles via
                # build_bu_states. Previously the vertical id silently failed
                # the seed-slot filter and the player received the full 4-BU
                # conglomerate (the reported anomaly).
                filtered = [b for b in build_bu_states({_slot: _vertical})
                            if b.get("bu_id") == _vertical]
            else:
                filtered = [b for b in bus if b.get("bu_id") == _slot]
        except Exception:
            # Defensive: profile resolution must never break session creation.
            filtered = [b for b in bus if b.get("bu_id") == assigned_bu]
        if filtered:
            bus = filtered
            # Record the bu_id the session ACTUALLY scopes to, so allocation
            # validation, briefing labels, and child-session inheritance all
            # agree with bu_states (vertical id when substituted, else slot).
            assigned_bu = filtered[0].get("bu_id", assigned_bu)
        elif simulation_mode == "single_bu":
            # Final guard for unknown ids: 1 BU is always better than silently
            # granting the full conglomerate in single-BU mode.
            bus = [bus[0]] if bus else bus
            if bus:
                assigned_bu = bus[0].get("bu_id", assigned_bu)
        # The session record was written above with the raw value — sync it to
        # the effective scope id resolved here.
        _sessions[session_id]["assigned_bu"] = assigned_bu or ""
    if decision_paradigm == "un_sdg":
        for bu in bus:
            for cluster in ["basic_needs", "human_capital", "sustainable_growth", "planet", "governance", "partnerships"]:
                if cluster not in bu:
                    bu[cluster] = 50.0
    n = len(bus) or 1
    baseline_ebitda = round(sum(b["revenue_base"] - b["opex_base"] for b in bus), 2)
    baseline_tco2e = round(sum(b.get("carbon_intensity", 0) * b["revenue_base"] / 1_000_000 for b in bus))
    avg_sl = sum(b.get("social_license_score", 50) for b in bus) / n
    avg_ci = sum(b.get("carbon_intensity", 50) for b in bus) / n
    avg_gr = sum(b.get("governance_risk_score", 20) for b in bus) / n
    baseline_vrio = {
        "value": round(max(0, min(100, avg_sl)), 1),
        "rarity": round(max(0, min(100, 100 - avg_ci)), 1),
        "imitability": round(max(0, min(100, gs["group_synergy_multiplier"] * 100)), 1),
        "organization": round(max(0, min(100, 100 - avg_gr)), 1),
    }

    from admin_shared import _god_mode_settings
    treasury = _god_mode_settings.get("corporate_treasury_start", SIM_INITIAL_BUDGET)
    reputation = _god_mode_settings.get("group_reputation_start", gs["group_reputation_score"])
    synergy = _god_mode_settings.get("synergy_multiplier_start", gs["group_synergy_multiplier"])
    coc = _god_mode_settings.get("cost_of_capital_start", gs["cost_of_capital_rate"])
    loan_interest_rate = _god_mode_settings.get("loan_interest_rate_start", loan_interest_rate)
    green_fund = _god_mode_settings.get("green_transition_fund_start", 0.0)


    # ── Single-BU mode: scale treasury proportionally ──
    # When running with 1 BU out of N total, divide treasury by N ONLY when
    # the treasury is the default full-group seed amount (SIM_INITIAL_BUDGET).
    # If the facilitator has explicitly set corporate_treasury_start to a custom
    # value, that value is already their intended per-BU amount — do NOT divide
    # it again (which would produce a nonsensically small starting balance).
    if assigned_bu:
        treasury_was_explicitly_set = "corporate_treasury_start" in _god_mode_settings
        if not treasury_was_explicitly_set:
            # Using the default seed budget — scale it down proportionally
            total_bus_in_seed = len(seed.get("business_units", []))
            if total_bus_in_seed > 1:
                treasury = round(treasury / total_bus_in_seed, 2)
                green_fund = round(green_fund / total_bus_in_seed, 2)

    # ── Resolve ending pathway for this session ──
    from ending_pathways import resolve_pathway
    default_pathway = _god_mode_settings.get("default_ending_pathway", "activist_ultimatum")
    ending_pathway = resolve_pathway(default_pathway)

    global_state = {
        "state_id": global_state_id,
        "session_id": session_id,
        "round_number": 1,
        "corporate_treasury": treasury,
        "group_reputation": reputation,
        "synergy_multiplier": synergy,
        "cost_of_capital": coc,
        "active_event_flags": {
            **gs.get("active_event_flags", {}),
            "loan_interest_rate": loan_interest_rate,
            "ending_pathway": ending_pathway,
            # Industry + region are declared at cohort setup and live on the
            # session record, but the engine only ever sees global_state. Seed
            # them here so stakeholder_map can resolve industry x region
            # stakeholder maps; empty strings are ignored by the resolver.
            "industry_vertical": industry_vertical or "",
            "region_id": region_id or "",
        },
        "bonus_score": 0,
        "historical_ebitda": baseline_ebitda,
        "tco2e_emissions": baseline_tco2e,
        "vrio_capabilities": baseline_vrio,
        "green_transition_fund": green_fund,
        "tipping_point_active": False,
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "competitor_ebitda": round(sum(b["revenue_base"] - b["opex_base"] for b in bus), 2),
        # SDG Edition metrics (zeroed for non-SDG paradigms)
        "political_capital": gs.get("political_capital", 50.0),
        "community_trust_score": gs.get("community_trust_score", 50.0),
        "global_emissions_intensity": gs.get("global_emissions_intensity", 0.0),
    }

    # C2: seed effective climate inputs (global defaults + any per-cohort
    # override) into active_event_flags so the engine — which reads these keys
    # off the session — sees the resolved values from round 1.
    # 4.2: same stamp as the Postgres backend, from the same helper, so the two
    # stores cannot drift on which seed a cohort gets. Derived from the parent
    # cohort id so every team in the cohort rolls identically (GAME-4).
    from rng_util import ensure_cohort_seed
    ensure_cohort_seed(global_state["active_event_flags"], parent_cohort_id or session_id)

    try:
        from admin_shared import seed_effective_flags
        seed_effective_flags(session_id, global_state["active_event_flags"])
    except Exception:
        pass

    if decision_paradigm == "brsr_ngrbc":
        from brsr_controller import init_brsr_state
        init_brsr_state(global_state["active_event_flags"], bus, {})

    _global_states[session_id] = [global_state]
    _bu_states[session_id] = {1: copy.deepcopy(bus)}

    # REC-2: Generate and store short join code for top-level sessions
    if not parent_cohort_id:
        join_code = _generate_join_code()
        _sessions[session_id]["join_code"] = join_code
        _join_codes[join_code] = session_id

    _persist()

    res_global = {
        "corporate_treasury": treasury,
        "group_reputation": reputation,
        "synergy_multiplier": synergy,
        "cost_of_capital": coc,
        "active_event_flags": global_state["active_event_flags"],
        "historical_ebitda": baseline_ebitda,
        "tco2e_emissions": baseline_tco2e,
        "vrio_capabilities": baseline_vrio,
        "green_transition_fund": green_fund,
        "tipping_point_active": False,
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "competitor_ebitda": baseline_ebitda,
    }
    if decision_paradigm == "brsr_ngrbc":
        res_global["_brsr_track_state"] = global_state["active_event_flags"]["_brsr_track_state"]

    return {
        "session_id": session_id,
        "round_number": 1,
        "global_state": res_global,
        "business_units": bus,
    }


# ── Fetch Operations ───────────────────────────────────────────

async def get_session_info(session_id: str) -> Optional[dict]:
    """Return basic session metadata by ID."""
    return _sessions.get(session_id)


def resolve_cohort_id_sync(session_id: str) -> str:
    """Map ANY session id to the cohort that owns its settings — synchronously.

    Parity API. A player who joins a cohort gets their OWN sub-session, and
    that id is what every player-side request carries. Per-cohort settings live
    on the PARENT, so a gate evaluated with the child id silently resolves to
    the platform default. That is how Stakeholder Negotiation Rooms stayed
    403 "not enabled for this cohort" after the facilitator had enabled them.

    Sync on purpose: the callers (get_effective_settings and the gates built on
    it) are synchronous, and making them async would ripple through most of the
    admin surface. Both backends read the same synchronous session cache, which
    database.py maintains under Postgres precisely for this kind of access.

    Returns the parent cohort id when `session_id` is a sub-session, otherwise
    `session_id` unchanged (including for unknown ids — callers fall back to
    the global view rather than failing closed).
    """
    rec = _sessions.get(session_id) or {}
    return rec.get("parent_cohort_id") or session_id


async def fetch_all_sessions_raw() -> list[dict]:
    """ALL session records, INCLUDING per-player sub-sessions and shells.

    Parity API (Railway audit §1.1): fetch_all_sessions() filters to top-level
    cohorts for the leaderboard, which made endpoints that need child sessions
    (situation room, cohort pulse, analytics scoping) reach into the private
    `_sessions` dict — a read that silently returns {} under Postgres. Use
    THIS for aggregate reads; never touch the store directly.

    The store key is authoritative for session_id: legacy/minimal records
    (and some test fixtures) omit the field from the record body."""
    return [{**s, "session_id": s.get("session_id", k)} for k, s in _sessions.items()]


async def fetch_all_decisions() -> list[dict]:
    """Every decision-log row across all sessions (analytics aggregates).
    Parity API — mirrors database.fetch_all_decisions."""
    return [dict(d) for d in _decision_log]

async def fetch_session_by_cohort(cohort_name: str) -> Optional[dict]:
    """Look up an existing session by cohort_name and return its latest state.
    Only matches top-level sessions (not per-player clones)."""
    matching_sessions = [
        s for s in list(_sessions.values())
        if s["cohort_name"] == cohort_name and not s.get("parent_cohort_id")
    ]
    if not matching_sessions:
        return None
        
    latest_session = sorted(
        matching_sessions,
        key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True
    )[0]
    
    session_id = latest_session["session_id"]
    state = await fetch_latest_state(session_id)
    if state:
        state["session_id"] = session_id
    return state


async def get_active_public_sessions() -> list[dict]:
    """Return all top-level sessions (exclude per-player sub-sessions) that are not deleted."""
    active = [s for s in list(_sessions.values()) if not s.get("parent_cohort_id") and not s.get("deleted_at")]
    # Sort by start_time descending
    active.sort(key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return active

async def validate_player_id(session_id: str, player_id: str) -> bool:
    session = _sessions.get(session_id)
    if not session: return False
    return player_id in session.get("allowed_player_ids", [])

async def set_session_public(session_id: str, is_public: bool) -> bool:
    session = _sessions.get(session_id)
    if not session: return False
    session["is_public"] = is_public
    _persist()
    return True

async def update_session_metadata(session_id: str, updates: dict) -> bool:
    """Public API: update editable metadata fields on a session.
    Parallel to database.py's update_session_metadata — both backends must implement this.
    Updates the in-memory store in-place and persists to disk snapshot.
    """
    session = _sessions.get(session_id)
    if session is None:
        return False
    session.update(updates)
    _persist()
    return True



def _player_id_in_registry(player_id: str) -> bool:
    """Wave 3 hygiene: the credential registry (admin_shared._player_registry) can
    hold a record whose session no longer exists; minting that id again would
    make change-password / login find the stale record first."""
    try:
        from admin_shared import _player_registry
    except Exception:  # pragma: no cover — registry unavailable at import time
        return False
    return any(isinstance(p, dict) and p.get("player_id") == player_id for p in _player_registry)

def _player_id_in_use_sync(player_id: str) -> bool:
    for sess in list(_sessions.values()):
        if sess.get("player_id") == player_id:
            return True
        if player_id in (sess.get("allowed_player_ids") or []):
            return True
        for rp in sess.get("registered_players") or []:
            if isinstance(rp, dict) and rp.get("player_id") == player_id:
                return True
    return False


async def player_id_in_use(player_id: str) -> bool:
    """F-40: parity with database.player_id_in_use — any session, any cohort."""
    return _player_id_in_use_sync(str(player_id))


async def list_all_player_ids() -> set[str]:
    out: set[str] = set()
    for sess in list(_sessions.values()):
        if sess.get("player_id"):
            out.add(str(sess["player_id"]))
        for pid in sess.get("allowed_player_ids") or []:
            out.add(str(pid))
        for rp in sess.get("registered_players") or []:
            if isinstance(rp, dict) and rp.get("player_id"):
                out.add(str(rp["player_id"]))
    return out


async def generate_player_id(session_id: str) -> Optional[str]:
    """F-40: the id is unique across the whole platform, not just this cohort."""
    import random
    import string
    session = _sessions.get(session_id)
    if not session: return None
    
    allowed = session.setdefault("allowed_player_ids", [])
    from config import PLAYER_ID_RANDOM_LETTERS
    # Wave 3 hygiene (found by an order-dependent test failure): the letters came
    # from the process-global Random, which dry_run / validation_logic seed and
    # the test harness restores per test — so ids REPEATED across tests, and the
    # uniqueness scan did not look at the credential registry, which can hold a
    # record whose session is gone. OS entropy, and the registry is checked too.
    _sysrand = random.SystemRandom()
    for _ in range(2000):
        letters = ''.join(_sysrand.choices(string.ascii_uppercase, k=PLAYER_ID_RANDOM_LETTERS))
        pid = f"MUR-{letters}"
        if pid not in allowed and not _player_id_in_use_sync(pid) and not _player_id_in_registry(pid):
            break
    else:  # pragma: no cover
        raise RuntimeError("Could not allocate a platform-unique player id; raise PLAYER_ID_RANDOM_LETTERS.")
            
    allowed.append(pid)
    _persist()
    return pid


async def fetch_latest_state(session_id: str) -> Optional[dict]:
    """
    Return the latest round's global state + BU states for a session.
    """
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return None

    grs = rounds[-1]
    rn = grs.get("round_number", 1)
    bus = _bu_states.get(session_id, {}).get(rn, [])
    # 4.1: apply the SAME canonical ordering as the Postgres backend. Creation
    # order already equals slot order here, so this is a no-op for every
    # unsubstituted cohort — it is present so that the two stores share one
    # definition of the order rather than agreeing by coincidence.
    from bu_profiles import sort_bu_states_canonically
    bus = sort_bu_states_canonically(list(bus), grs.get("active_event_flags") or grs)

    # Defensive .get()s: legacy/minimal rows (and test fixtures) may omit
    # bookkeeping fields like state_id — a read API should degrade, not raise.
    out = {
        "state_id": grs.get("state_id"),
        "round_number": rn,
        "global_state": {
            "corporate_treasury": float(grs.get("corporate_treasury", 0) or 0),
            "group_reputation": float(grs.get("group_reputation", 50) or 0),
            "synergy_multiplier": float(grs.get("synergy_multiplier", 1.0) or 0),
            "cost_of_capital": float(grs.get("cost_of_capital", 0.05) or 0),
            "active_event_flags": grs.get("active_event_flags") or {},
            # MP-01: surface the multiplayer commit counts (see update_latest_global_state).
            "team_commits_this_round": grs.get("team_commits_this_round"),
            "cohort_team_count": grs.get("cohort_team_count"),
            "bonus_score": grs.get("bonus_score", 0),
            "historical_ebitda": float(grs.get("historical_ebitda", 0)),
            "tco2e_emissions": int(grs.get("tco2e_emissions", 0)),
            "vrio_capabilities": grs.get("vrio_capabilities") or {},
            "stakeholder_map_completed": grs.get("stakeholder_map_completed", False),
            "stakeholder_map_accuracy": grs.get("stakeholder_map_accuracy", 0),
            "learning_bonuses_awarded": grs.get("learning_bonuses_awarded", {}),
            "saved_allocations": grs.get("saved_allocations"),
            "saved_decision_choice": grs.get("saved_decision_choice"),
            "saved_round": grs.get("saved_round"),
            "saved_pillar_decisions": grs.get("saved_pillar_decisions"),   # F04
            "materiality_budget_allocated": grs.get("materiality_budget_allocated"),
            "materiality_bu_id": grs.get("materiality_bu_id"),
            "csrd_completed": grs.get("csrd_completed", False),
            "green_transition_fund": float(grs.get("green_transition_fund", 0.0)),
            "tipping_point_active": grs.get("tipping_point_active", False),
            "pending_capex_projects": grs.get("pending_capex_projects", []),
            "inflation_index": float(grs.get("inflation_index", 0.025)),
            "competitor_ebitda": float(grs.get("competitor_ebitda", 0.0)),
            # SDG Edition metrics
            "political_capital": float(grs.get("political_capital", 50.0)),
            "community_trust_score": float(grs.get("community_trust_score", 50.0)),
            "global_emissions_intensity": float(grs.get("global_emissions_intensity", 0.0)),
            # BU Substitution state (vertical industry selection)
            "bu_substitutions": grs.get("bu_substitutions", {}),
            # Autonomous stakeholder agent state
            "autonomous_agents": grs.get("autonomous_agents"),
            # Live stakeholder summary for the dashboard. Falls back to the
            # active_event_flags copy for rows persisted before the
            # agent_summary column existed.
            "agent_summary": grs.get("agent_summary")
                or (grs.get("active_event_flags") or {}).get("agent_summary"),
        },
        "bu_states": [
            {
                "bu_id": bu["bu_id"],
                "revenue_base": float(bu["revenue_base"]),
                "opex_base": float(bu["opex_base"]),
                "natural_capital_debt": float(bu.get("natural_capital_debt", 0)),
                "social_license_score": float(bu.get("social_license_score", 50)),
                "reputation_score": float(bu.get("reputation_score", 50)),
                "governance_risk_score": float(bu.get("governance_risk_score", 0)),
                "water_dependency": float(bu.get("water_dependency", 0)),
                "carbon_intensity": float(bu.get("carbon_intensity", 0)),
                "staff_burnout_index": float(bu.get("staff_burnout_index", 0)),
                "bed_capacity_utilization": float(bu.get("bed_capacity_utilization", 0)),
                "patient_outcomes_score": float(bu.get("patient_outcomes_score", 0)),
                # SDG cluster scores (UN SDG Edition)
                "basic_needs": float(bu.get("basic_needs", 0)),
                "human_capital": float(bu.get("human_capital", 0)),
                "sustainable_growth": float(bu.get("sustainable_growth", 0)),
                "planet": float(bu.get("planet", 0)),
                "governance": float(bu.get("governance", 0)),
                "partnerships": float(bu.get("partnerships", 0)),
                "population": int(bu.get("population", 0)),
                "migration_pressure": float(bu.get("migration_pressure", 0)),
                "institutional_leakage_multiplier": float(bu.get("institutional_leakage_multiplier", 1.0)),
                "sanitation_miracle_bonus": float(bu.get("sanitation_miracle_bonus", 1.0)),
                "risk_factors": bu.get("risk_factors") or {},
                # F-15 (launch audit 2026-09-01): PARITY with database.py. Postgres
                # packs every engine-written BU key it has no column for into
                # risk_factors and unpacks it on read, so fields such as
                # scope_1_ci / scope_2_ci / scope_3_ci, absolute_emissions,
                # supplier_defection_active and green_premium_squeeze survive
                # the round boundary in production. This store silently
                # dropped them, so mechanics that read them next round (the
                # CBAM levy) fired ONLY in production and never in any test.
                **{k: v for k, v in bu.items() if k not in _BU_EXPLICIT_READ_KEYS},
            }
            for bu in bus
        ],
    }
    # PARITY with database.py (Postgres): unpack non-column keys from
    # active_event_flags to top level so engine ledgers (balance_sheet,
    # board_governance, supply_chain, …) are readable exactly as under
    # Postgres. Explicit values above always win.
    for _k, _v in (grs.get("active_event_flags") or {}).items():
        if _k not in out["global_state"]:
            out["global_state"][_k] = _v
    return out


async def fetch_latest_round(session_id: str) -> Optional[int]:
    """PER-2: cheap latest-round lookup -- returns only the round number,
    without assembling the full global + BU state that fetch_latest_state
    builds. Used for the per-sibling commit-count fan-out."""
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return None
    rn = rounds[-1].get("round_number")
    return int(rn) if rn is not None else None


async def fetch_latest_rounds(session_ids: list[str]) -> dict[str, int]:
    """F-27: latest round for MANY sessions in one call (the cohort sibling
    scan the dashboard poll performs). Sessions with no rounds are omitted."""
    out: dict[str, int] = {}
    for sid in session_ids:
        rounds = _global_states.get(sid, [])
        if rounds and rounds[-1].get("round_number") is not None:
            out[sid] = int(rounds[-1]["round_number"])
    return out


async def fetch_round_history(session_id: str, since_round: int | None = None, include_final: bool = False) -> list[dict]:
    """
    Return the rounds of a session (for the dashboard history), oldest first.
    F-27: `since_round` keeps only rounds >= N — same contract as database.py.
    """
    rounds = _global_states.get(session_id, [])
    history = []
    for grs in rounds:
        rn = grs.get("round_number", 1)
        if since_round is not None and rn < since_round:
            continue
        bus = _bu_states.get(session_id, {}).get(rn, [])
        # Defensive .get()s — legacy/minimal rows and test fixtures may omit
        # fields; a read API should degrade to defaults, not raise.
        history.append({
            "round_number": rn,
            "global_state": {
                "corporate_treasury": float(grs.get("corporate_treasury", 0) or 0),
                "group_reputation": float(grs.get("group_reputation", 50) or 0),
                "synergy_multiplier": float(grs.get("synergy_multiplier", 1.0) or 0),
                "cost_of_capital": float(grs.get("cost_of_capital", 0.05) or 0),
                "active_event_flags": grs.get("active_event_flags") or {},
                "bonus_score": grs.get("bonus_score", 0),
                "historical_ebitda": float(grs.get("historical_ebitda", 0)),
                "tco2e_emissions": int(grs.get("tco2e_emissions", 0)),
                "vrio_capabilities": grs.get("vrio_capabilities") or {},
                "green_transition_fund": float(grs.get("green_transition_fund", 0.0)),
                "tipping_point_active": grs.get("tipping_point_active", False),
                "pending_capex_projects": grs.get("pending_capex_projects", []),
                # SDG Edition metrics
                "political_capital": float(grs.get("political_capital", 50.0)),
                "community_trust_score": float(grs.get("community_trust_score", 50.0)),
                "global_emissions_intensity": float(grs.get("global_emissions_intensity", 0.0)),
            },
            "business_units": [
                {
                    "bu_id": bu["bu_id"],
                    "revenue_base": float(bu["revenue_base"]),
                    "opex_base": float(bu["opex_base"]),
                    "natural_capital_debt": float(bu.get("natural_capital_debt", 0)),
                    "social_license_score": float(bu.get("social_license_score", 50)),
                    "reputation_score": float(bu.get("reputation_score", 50)),
                    "governance_risk_score": float(bu.get("governance_risk_score", 0)),
                    "water_dependency": float(bu.get("water_dependency", 0)),
                    "carbon_intensity": float(bu.get("carbon_intensity", 0)),
                    "risk_factors": bu.get("risk_factors") or {},
                    # F-15: same parity rule as fetch_latest_state.
                    **{k: v for k, v in bu.items() if k not in _BU_EXPLICIT_READ_KEYS},
                }
                for bu in bus
            ],
            # Parity with the Postgres backend (database.fetch_round_history):
            # attach the round's per-BU decisions so downstream consumers
            # (RoundSnapshot.choice_selected enrichment, consequence-DNA) can
            # read choice_selected in memory mode too. Sourced from _decision_log.
            "decisions": [
                {
                    "bu_id": dec.get("bu_id"),
                    "decision_node_id": dec.get("decision_node_id", ""),
                    "choice_selected": dec.get("choice_selected", ""),
                    "capex": float(dec.get("capex_allocated", 0) or 0),
                    "time_to_decision_seconds": dec.get("time_to_decision_seconds", 0),
                    # TEAM-3 (UX audit #7): no coercion — NULL/None means the team
                    # did not record how it decided. Parity with database.py.
                    "team_consensus": dec.get("team_consensus") or None,
                    # 4.8: parity with the Postgres reader.
                    "metadata": dec.get("metadata") or {},
                }
                for dec in _decision_log
                if dec.get("session_id") == session_id and dec.get("round_number") == rn
            ],
        })
    # PARITY with database.py (Postgres): unpack non-column flag keys to
    # top level per round (explicit values win) — see fetch_latest_state.
    for h in history:
        gs_out = h["global_state"]
        for _k, _v in (gs_out.get("active_event_flags") or {}).items():
            if _k not in gs_out:
                gs_out[_k] = _v
    # SEAM-08 (audit 2026-09-04): row K = state entering K, R10 included; the
    # closing state is appended as round 11 / is_final only when asked.
    from history_semantics import splice_final_state
    return splice_final_state(history, include_final=include_final)


# ── Insert Next-Round State ────────────────────────────────────

async def insert_next_round(
    session_id: str,
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
    decisions: list[dict],
) -> str:
    """
    Persist the new round state and audit log entries.
    Returns the new global_state_id.
    """
    global_state_id = str(uuid.uuid4())

    state_entry = {
        "state_id": global_state_id,
        "session_id": session_id,
        "round_number": round_number,
        "corporate_treasury": global_state["corporate_treasury"],
        "group_reputation": global_state["group_reputation"],
        "synergy_multiplier": global_state.get("synergy_multiplier", 1.0),
        "cost_of_capital": global_state.get("cost_of_capital", 0.05),
        "active_event_flags": global_state.get("active_event_flags", {}),
        "bonus_score": global_state.get("bonus_score", 0),
        "historical_ebitda": global_state.get("historical_ebitda", 0),
        "tco2e_emissions": global_state.get("tco2e_emissions", 0),
        "vrio_capabilities": global_state.get("vrio_capabilities", {}),
        "stakeholder_map_completed": global_state.get("stakeholder_map_completed", False),
        "stakeholder_map_accuracy": global_state.get("stakeholder_map_accuracy", 0),
        "learning_bonuses_awarded": global_state.get("learning_bonuses_awarded", {}),
        "saved_allocations": global_state.get("saved_allocations"),
        "saved_decision_choice": global_state.get("saved_decision_choice"),
        "saved_round": global_state.get("saved_round"),
        "saved_pillar_decisions": global_state.get("saved_pillar_decisions"),   # F04
        "materiality_budget_allocated": global_state.get("materiality_budget_allocated"),
        "materiality_bu_id": global_state.get("materiality_bu_id"),
        "csrd_completed": global_state.get("csrd_completed", False),
        "green_transition_fund": global_state.get("green_transition_fund", 0.0),
        "tipping_point_active": global_state.get("tipping_point_active", False),
        "pending_capex_projects": global_state.get("pending_capex_projects", []),
        "inflation_index": global_state.get("inflation_index", 0.025),
        "competitor_ebitda": global_state.get("competitor_ebitda", 0.0),
        # SDG Edition metrics
        "political_capital": global_state.get("political_capital", 50.0),
        "community_trust_score": global_state.get("community_trust_score", 50.0),
        "global_emissions_intensity": global_state.get("global_emissions_intensity", 0.0),
        # BU Substitution state (vertical industry selection)
        "bu_substitutions": global_state.get("bu_substitutions", {}),
        # Autonomous stakeholder agent state
        "autonomous_agents": global_state.get("autonomous_agents"),
        # Frontend-ready stakeholder summary (round_logic writes it top-level so
        # the LIVE dashboard reflects escalation every round; without this column
        # it was silently dropped here and the cockpit fell back to stale
        # post-commit events).
        "agent_summary": global_state.get("agent_summary"),
    }

    # PARITY with database.py (Postgres): pack every global_state key the
    # explicit schema above doesn't store into active_event_flags. Without
    # this, engine ledgers written top-level (balance_sheet, board_governance,
    # supply_chain, …) were silently dropped in memory mode — e.g. the
    # Year-by-Year balance sheet lost its accumulated history and rebuilt a
    # fresh one-round statement on every read.
    _packed_flags = dict(state_entry.get("active_event_flags") or {})
    for _k, _v in global_state.items():
        if _k not in state_entry and _k != "active_event_flags":
            _packed_flags[_k] = _v
    state_entry["active_event_flags"] = _packed_flags

    if session_id not in _global_states:
        _global_states[session_id] = []
    _global_states[session_id].append(state_entry)

    if session_id not in _bu_states:
        _bu_states[session_id] = {}
    _bu_states[session_id][round_number] = copy.deepcopy(bu_states)

    # AUDIT-1 (2026-08-02): decisions are filed under the round they were MADE
    # in, which is `round_number - 1`.
    #
    # This used to use `round_number` — the round the commit CREATED. A team's
    # round-3 choices were stored as round 4, every set was one round late, and
    # round 1 had no rows at all, so any debrief, grade reconstruction or replay
    # reading the log attributed decisions to the wrong round. Found by
    # tests/test_full_run_e2e.py — the first test that ever played a full game
    # and then looked at the log.
    #
    # Safe at every call site: all three pass new_round = decision_round + 1,
    # and the Extended Horizon insert passes decisions=[] so it never applies.
    #
    # NOT backfilled — runs committed before this change carry the old offset.
    # No score has been graded from them yet, which is the window that makes
    # this a clean break rather than a data migration.
    _decisions_round = max(1, round_number - 1)
    for dec in decisions:
        _decision_log.append({
            "session_id": session_id,
            "round_number": _decisions_round,
            "bu_id": dec.get("bu_id"),
            "decision_node_id": dec.get("decision_node_id", ""),
            "choice_selected": dec.get("choice_selected", ""),
            "capex_allocated": dec.get("capex_allocated", 0),
            "player_id": dec.get("player_id", ""),
            "time_to_decision_seconds": dec.get("time_to_decision_seconds", 0),
            # TEAM-3 (UX audit #7): no coercion — NULL/None means the team
            # did not record how it decided. Parity with database.py.
            "team_consensus": dec.get("team_consensus") or None,
            # 4.8: parity with the Postgres metadata column — same envelope,
            # same key, so a reader need not know which store it came from.
            "metadata": dec.get("metadata") or {},
        })

    # H-4 fix: Cap decision log to prevent unbounded memory growth
    _MAX_DECISION_LOG = 50_000
    if len(_decision_log) > _MAX_DECISION_LOG:
        del _decision_log[:_MAX_DECISION_LOG // 10]

    _persist()
    return global_state_id


async def log_decisions(session_id: str, round_number: int, decisions: list[dict]) -> int:
    """Append decisions to the audit trail WITHOUT advancing the round.

    R10-2 (2026-08-02): rounds 1-9 log their decisions as part of
    insert_next_round, but round 10 persists in place via
    update_latest_global_state and never calls it — so the graded finale's
    decisions were written nowhere. commit-turn now calls this for R10.

    Mirrors insert_next_round's decision write EXACTLY, including TEAM-3's
    no-coercion rule on team_consensus. Append-only, and safe under the Postgres
    immutability triggers, which block UPDATE and DELETE on decision_audit_log
    but permit INSERT. Returns the number of rows written.
    """
    if not decisions:
        return 0
    for dec in decisions:
        _decision_log.append({
            "session_id": session_id,
            "round_number": round_number,
            "bu_id": dec.get("bu_id"),
            "decision_node_id": dec.get("decision_node_id", ""),
            "choice_selected": dec.get("choice_selected", ""),
            "capex_allocated": dec.get("capex_allocated", 0),
            "player_id": dec.get("player_id", ""),
            "time_to_decision_seconds": dec.get("time_to_decision_seconds", 0),
            # TEAM-3: no coercion — None means "not recorded". Parity with database.py.
            "team_consensus": dec.get("team_consensus") or None,
            # 4.8: parity with the Postgres metadata column — same envelope,
            # same key, so a reader need not know which store it came from.
            "metadata": dec.get("metadata") or {},
        })
    _persist()
    return len(decisions)


async def get_decision_log(session_id: str) -> list[dict]:
    """
    Return all decisions for a session and its child player sessions.
    Includes player_id from the child session metadata.
    """
    # Collect all relevant session IDs (parent + children)
    related_ids = {session_id}
    for sid, sess in list(_sessions.items()):
        if sess.get("parent_cohort_id") == session_id:
            related_ids.add(sid)

    results = []
    for entry in _decision_log:
        if entry.get("session_id") in related_ids:
            # Prefer player_id from the decision entry itself (set during commit-turn),
            # fall back to session metadata
            sess = _sessions.get(entry["session_id"], {})
            player_id = entry.get("player_id") or sess.get("player_id") or "unknown"
            results.append({
                **entry,
                "player_id": player_id,
                "cohort_name": sess.get("cohort_name", ""),
            })

    # Sort by round, then player
    results.sort(key=lambda x: (x.get("round_number", 0), x.get("player_id", "")))
    return results



# ── Admin / God Mode Operations ───────────────────────────────

async def count_sessions() -> dict:
    """Mode-agnostic live session counts for the God Mode overview.
    Counts non-deleted cohorts (no player_id) and players (player_id set).
    Mirrors database.count_sessions so the God Mode status works in BOTH
    the in-memory and Postgres backends."""
    cohorts = players = 0
    for sdata in _sessions.values():
        if sdata.get("deleted_at"):
            continue
        if sdata.get("player_id"):
            players += 1
        else:
            cohorts += 1
    return {"cohorts": cohorts, "players": players}


async def fetch_all_sessions() -> list[dict]:
    """Return only top-level cohort sessions for the admin leaderboard (excludes per-player sub-sessions)."""
    # Back-fill short codes for sessions that predate this feature
    for s in list(_sessions.values()):
        if not s.get("short_code") and not s.get("parent_cohort_id"):
            s["short_code"] = _generate_short_code()

    return [
        {
            "session_id": s["session_id"],
            "short_code": s.get("short_code"),
            "cohort_name": s["cohort_name"],
            "facilitator_id": s["facilitator_id"],
            "start_time": s["start_time"].isoformat() if hasattr(s.get("start_time"), "isoformat") else s.get("start_time"),
            "is_public": s.get("is_public", False),
            "allowed_player_ids": s.get("allowed_player_ids", []),
            "player_id": s.get("player_id"),
            "parent_cohort_id": s.get("parent_cohort_id"),
            "registered_players": s.get("registered_players", []),
            "decision_paradigm": s.get("decision_paradigm", "legacy_abc"),
            "currency_symbol": s.get("currency_symbol", "$"),
            "scenario_preset": s.get("scenario_preset"),
            "experience_level": s.get("experience_level"),
            "difficulty_tier": s.get("difficulty_tier", "advanced"),
            "created_by": s.get("created_by"),
            "created_when": s.get("created_when"),
            "deleted_at": s.get("deleted_at"),
            "pedagogical_overrides": s.get("pedagogical_overrides", {}),
            "ceo_interview_enabled": s.get("ceo_interview_enabled", False),
            "ceo_interview_voice_gender": s.get("ceo_interview_voice_gender", "female"),
            "side_tracks": s.get("side_tracks", []),
            "start_date": s.get("start_date"),
            "end_date": s.get("end_date"),
            "pacing_mode": s.get("pacing_mode", "free_play"),
            "max_unlocked_round": s.get("max_unlocked_round", SIM_ROUNDS),
            "simulation_mode": s.get("simulation_mode", ""),
            "industry_vertical": s.get("industry_vertical", ""),
            "region_id": s.get("region_id", ""),
        }
        for s in sorted(
            list(_sessions.values()),
            key=lambda x: x.get("start_time", datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        ) if not s.get("deleted_at")
    ]


async def get_child_sessions(parent_id: str) -> list[dict]:
    """Return all child player sessions for a given parent cohort session.
    Parity with database.get_child_sessions: the full session record."""
    children = []
    for sid, sess in list(_sessions.items()):
        if sess.get("parent_cohort_id") == parent_id:
            rec = dict(sess)
            rec.setdefault("session_id", sid)
            rec.setdefault("player_id", sess.get("player_id", "unknown"))
            rec.setdefault("cohort_name", sess.get("cohort_name", ""))
            rec["parent_cohort_id"] = parent_id
            children.append(rec)
    return children


async def fetch_child_session_ids(parent_id: str) -> list[str]:
    """F-28 parity: ids of a cohort's player sub-sessions."""
    return [sid for sid, sess in list(_sessions.items()) if sess.get("parent_cohort_id") == parent_id]


async def update_latest_global_state(
    session_id: str,
    global_state: dict,
    bu_states: list[dict],
) -> None:
    """
    Update the LATEST round's global and BU states in place.
    Used by God Mode overrides.
    """
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return

    latest = rounds[-1]
    latest["corporate_treasury"] = global_state["corporate_treasury"]
    latest["group_reputation"] = global_state["group_reputation"]
    latest["synergy_multiplier"] = global_state.get("synergy_multiplier", 1.0)
    latest["cost_of_capital"] = global_state.get("cost_of_capital", 0.05)
    latest["active_event_flags"] = global_state.get("active_event_flags", {})
    # MP-01: persist the multiplayer commit counts so the cockpit "X/Y teams
    # committed" badge renders. Postgres carries these via its dynamic
    # active_event_flags pack/unpack; the memory store uses an explicit
    # allow-list, so they are listed here or they get silently dropped.
    latest["team_commits_this_round"] = global_state.get("team_commits_this_round", latest.get("team_commits_this_round", 0))
    latest["cohort_team_count"] = global_state.get("cohort_team_count", latest.get("cohort_team_count", 0))
    # Persist bonus/learning fields that were previously being dropped
    latest["bonus_score"] = global_state.get("bonus_score", latest.get("bonus_score", 0))
    latest["historical_ebitda"] = global_state.get("historical_ebitda", latest.get("historical_ebitda", 0))
    latest["tco2e_emissions"] = global_state.get("tco2e_emissions", latest.get("tco2e_emissions", 0))
    latest["vrio_capabilities"] = global_state.get("vrio_capabilities", latest.get("vrio_capabilities", {}))
    latest["stakeholder_map_completed"] = global_state.get("stakeholder_map_completed", latest.get("stakeholder_map_completed", False))
    latest["stakeholder_map_accuracy"] = global_state.get("stakeholder_map_accuracy", latest.get("stakeholder_map_accuracy", 0))
    latest["learning_bonuses_awarded"] = global_state.get("learning_bonuses_awarded", latest.get("learning_bonuses_awarded", {}))
    latest["saved_allocations"] = global_state.get("saved_allocations")
    latest["saved_decision_choice"] = global_state.get("saved_decision_choice")
    latest["saved_round"] = global_state.get("saved_round")
    latest["saved_pillar_decisions"] = global_state.get("saved_pillar_decisions")   # F04
    latest["materiality_budget_allocated"] = global_state.get("materiality_budget_allocated")
    latest["materiality_bu_id"] = global_state.get("materiality_bu_id")
    latest["csrd_completed"] = global_state.get("csrd_completed", latest.get("csrd_completed", False))
    latest["green_transition_fund"] = global_state.get("green_transition_fund", latest.get("green_transition_fund", 0.0))
    latest["tipping_point_active"] = global_state.get("tipping_point_active", latest.get("tipping_point_active", False))
    latest["pending_capex_projects"] = global_state.get("pending_capex_projects", latest.get("pending_capex_projects", []))
    latest["inflation_index"] = global_state.get("inflation_index", latest.get("inflation_index", 0.025))
    latest["competitor_ebitda"] = global_state.get("competitor_ebitda", latest.get("competitor_ebitda", 0.0))
    # SDG Edition metrics
    latest["political_capital"] = global_state.get("political_capital", latest.get("political_capital", 50.0))
    latest["community_trust_score"] = global_state.get("community_trust_score", latest.get("community_trust_score", 50.0))
    latest["global_emissions_intensity"] = global_state.get("global_emissions_intensity", latest.get("global_emissions_intensity", 0.0))
    # BU Substitution state (vertical industry selection)
    latest["bu_substitutions"] = global_state.get("bu_substitutions", latest.get("bu_substitutions", {}))
    # Autonomous stakeholder agent state
    latest["autonomous_agents"] = global_state.get("autonomous_agents", latest.get("autonomous_agents"))
    latest["agent_summary"] = global_state.get("agent_summary", latest.get("agent_summary"))
    # PARITY with database.py (Postgres): pack extra top-level keys back into
    # active_event_flags so ledgers modified via fetch→update round-trips
    # (balance_sheet, board_governance, …) are not silently dropped.
    _packed = dict(latest.get("active_event_flags") or {})
    for _k, _v in global_state.items():
        if _k not in latest and _k != "active_event_flags":
            _packed[_k] = _v
    latest["active_event_flags"] = _packed

    rn = latest["round_number"]
    if session_id in _bu_states:
        _bu_states[session_id][rn] = copy.deepcopy(bu_states)
    _persist()


class StaleStateError(Exception):
    """Parity with database.StaleStateError (F01, audit 2026-09-09)."""


async def update_draft_fields(session_id: str, round_number: int, draft: dict) -> bool:
    """F01 (audit 2026-09-09) — parity with database.update_draft_fields.

    Write the mid-round draft keys onto the row for EXACTLY `round_number`,
    and only if that row is still the session's latest. Touches no economic
    field. Returns False (caller answers 409) when the session has moved on —
    the draft belonged to the round that just closed and must not hydrate the
    next one.
    """
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return False
    latest = rounds[-1]
    if int(latest.get("round_number", 0) or 0) != int(round_number):
        return False
    for k, v in (draft or {}).items():
        latest[k] = copy.deepcopy(v)
    # Parity with the Postgres row, where the draft lives in the JSONB flags
    # column (the dynamic-field pack in database.update_latest_global_state).
    flags = latest.get("active_event_flags")
    if isinstance(flags, dict):
        for k, v in (draft or {}).items():
            flags[k] = copy.deepcopy(v)
    _persist()
    return True


# ── Reset / Delete Operations ─────────────────────────────────

async def fetch_sessions_by_facilitator(facilitator_id: str) -> list[dict]:
    """Return all top-level sessions owned by the given facilitator.

    Mirrors database.fetch_sessions_by_facilitator so the cascade-delete
    path in delete_facilitator works identically in memory-DB mode.
    Both active and soft-deleted sessions are included so that a hard
    facilitator delete can permanently erase everything.
    """
    result = []
    for sid, sess in list(_sessions.items()):
        if sess.get("facilitator_id") != facilitator_id:
            continue
        # Skip child player sessions — those are handled by _cascade_delete_session
        if sess.get("parent_cohort_id"):
            continue
        result.append({
            "session_id": sid,
            "cohort_name": sess.get("cohort_name", ""),
            "facilitator_id": sess.get("facilitator_id", facilitator_id),
            "start_time": sess.get("start_time"),
        })
    # Return newest first, matching the PostgreSQL ORDER BY start_time DESC
    result.sort(key=lambda s: s.get("start_time") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return result


async def delete_session(session_id: str, hard: bool = False) -> bool:
    """Delete a single session and all its state. Returns True if found."""
    found = session_id in _sessions
    if not found:
        return False
        
    if hard:
        _sessions.pop(session_id, None)
        _global_states.pop(session_id, None)
        _bu_states.pop(session_id, None)
        global _decision_log
        _decision_log = [d for d in _decision_log if d.get("session_id") != session_id]
    else:
        _sessions[session_id]["deleted_at"] = datetime.now(timezone.utc).isoformat()
        
    _persist()
    return True


async def delete_all_sessions(hard: bool = False) -> int:
    """Delete ALL sessions. Returns the count of sessions deleted."""
    count = len(_sessions)
    if hard:
        _sessions.clear()
        _global_states.clear()
        _bu_states.clear()
        global _decision_log
        _decision_log = []
    else:
        now_str = datetime.now(timezone.utc).isoformat()
        for sess in list(_sessions.values()):
            if not sess.get("deleted_at"):
                sess["deleted_at"] = now_str
                
    _persist()
    return count


# ── Decade Forward Plan ──────────────────────────────────────

async def save_decade_plan(session_id: str, boardroom_choice: str, decade_plan: str) -> bool:
    """Save the boardroom choice and decade forward plan into the session."""
    sess = _sessions.get(session_id)
    if not sess:
        return False
    sess["boardroom_choice"] = boardroom_choice
    sess["decade_forward_plan"] = decade_plan
    _persist()
    return True


async def get_decade_plan(session_id: str) -> Optional[dict]:
    """Retrieve the decade forward plan for a session."""
    sess = _sessions.get(session_id)
    if not sess:
        return None
    return {
        "boardroom_choice": sess.get("boardroom_choice"),
        "decade_forward_plan": sess.get("decade_forward_plan"),
    }


# ── Practice Mode Reset ──────────────────────────────────────

async def reset_session_to_round1(session_id: str) -> bool:
    """
    Reset a session (and all its child player sessions) back to Round 1 seed state.
    Preserves session metadata (cohort name, facilitator, players, etc.).
    Used by practice mode after Round 2.
    """
    global _decision_log
    sess = _sessions.get(session_id)
    if not sess:
        return False

    seed = _load_seed()
    gs = seed["global_state"]
    bus = seed["business_units"]

    # Rebuild baseline metrics from seed
    n = len(bus) or 1
    baseline_ebitda = round(sum(b["revenue_base"] - b["opex_base"] for b in bus), 2)
    baseline_tco2e = round(sum(b.get("carbon_intensity", 0) * b["revenue_base"] / 1_000_000 for b in bus))
    avg_sl = sum(b.get("social_license_score", 50) for b in bus) / n
    avg_ci = sum(b.get("carbon_intensity", 50) for b in bus) / n
    avg_gr = sum(b.get("governance_risk_score", 20) for b in bus) / n
    baseline_vrio = {
        "value": round(max(0, min(100, avg_sl)), 1),
        "rarity": round(max(0, min(100, 100 - avg_ci)), 1),
        "imitability": round(max(0, min(100, gs["group_synergy_multiplier"] * 100)), 1),
        "organization": round(max(0, min(100, 100 - avg_gr)), 1),
    }

    # Get loan interest rate from existing state if available
    old_states = _global_states.get(session_id, [])
    loan_rate = 0.12
    if old_states:
        from config import FINANCIAL_DEFAULT_LOAN_RATE as _dlr   # FIN-11
        loan_rate = old_states[0].get("active_event_flags", {}).get("loan_interest_rate", _dlr)

    new_state_id = str(uuid.uuid4())
    global_state = {
        "state_id": new_state_id,
        "session_id": session_id,
        "round_number": 1,
        "corporate_treasury": gs["corporate_treasury_usd"],
        "group_reputation": gs["group_reputation_score"],
        "synergy_multiplier": gs["group_synergy_multiplier"],
        "cost_of_capital": gs["cost_of_capital_rate"],
        "active_event_flags": {
            **gs.get("active_event_flags", {}),
            "loan_interest_rate": loan_rate,
        },
        "bonus_score": 0,
        "historical_ebitda": baseline_ebitda,
        "tco2e_emissions": baseline_tco2e,
        "vrio_capabilities": baseline_vrio,
        "green_transition_fund": 0.0,
        "tipping_point_active": False,
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "competitor_ebitda": baseline_ebitda,
    }

    # Reset this session's state
    _global_states[session_id] = [global_state]
    _bu_states[session_id] = {1: copy.deepcopy(bus)}

    # Remove decision log entries for this session
    _decision_log = [d for d in _decision_log if d.get("session_id") != session_id]

    # Also reset all child player sessions
    child_ids = [
        sid for sid, s in list(_sessions.items())
        if s.get("parent_cohort_id") == session_id
    ]
    for child_id in child_ids:
        child_state_id = str(uuid.uuid4())
        child_global = {**global_state, "state_id": child_state_id, "session_id": child_id}
        _global_states[child_id] = [child_global]
        _bu_states[child_id] = {1: copy.deepcopy(bus)}
        _decision_log = [d for d in _decision_log if d.get("session_id") != child_id]

    _persist()
    return True


# ── Undo / Rollback Operations ────────────────────────────────

async def undo_latest_round(session_id: str) -> dict:
    """
    Delete the latest round's global state, BU states, and audit log
    entries for a session. Returns structured result.
    """
    global _decision_log
    rounds = _global_states.get(session_id, [])
    if not rounds:
        return {"success": False, "reason": "Session has no round data"}

    latest = rounds[-1]
    deleted_round = latest["round_number"]

    if deleted_round <= 1:
        return {"success": False, "reason": "Cannot undo Round 1 (initial state)"}

    # Remove the latest global state entry
    rounds.pop()

    # Remove BU states for that round
    if session_id in _bu_states:
        _bu_states[session_id].pop(deleted_round, None)

    # Remove decision log entries for that round
    _decision_log = [
        d for d in _decision_log
        if not (d.get("session_id") == session_id and d.get("round_number") == deleted_round)
    ]

    _persist()
    return {
        "success": True,
        "deleted_round": deleted_round,
        "new_current_round": deleted_round - 1,
    }

