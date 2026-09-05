"""
Muressons Global Corporation — API Router
Simulation endpoints: start, dashboard, commit-turn, round-config.
"""

from __future__ import annotations

import logging as _logging
_log = _logging.getLogger("muressons.router")  # QA-2026-07-16 #16: structured, request-correlated

import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
import copy
import os as _os

import database as db
import materiality_db as mat_db
from engine import process_tick
from round_logic import pre_tick, post_tick, run_new_engines, base_crisis_severity_for_round
from round_configs import get_round_config, get_round_crisis
from pillar_configs import get_pillar_config, aggregate_pillar_decisions, translate_pillars_to_legacy_choice
from config import MASTER_PASSWORD
# CFG-05 (audit 2026-09-04, WP-25): the CSF pool constants and the imitation
# decay default are read off the config MODULE at call time, not bound here
# at import — the Excel upload's hot reload rebinds names inside config only,
# so a `from config import X` copy kept the old value while the response said
# "reload: complete" (the engine ran 0.05 after an upload of 0.07).
import config as _cfg
from master_credentials import verify_master_password, verify_player_master_password
from admin_router import set_session_interventions, SessionInterventionsRequest, auto_inject_scheduled_interventions, require_facilitator, _check_rate_limit, _assert_player_or_facilitator_can_view
from password_hashing import verify_password as _verify_pw, hash_password as _hash_pw, maybe_upgrade_password as _maybe_upgrade_pw
from password_hashing import verify_password_async as _verify_pw_async, hash_password_async as _hash_pw_async, maybe_upgrade_password_async as _maybe_upgrade_pw_async  # F-30
from admin_resources import check_hidden_resource_triggers
from admin_shared import check_and_increment_cohort_count, is_practice_mode, _session_journey_responses
from option_shuffle import shuffle_options_for_display, deshuffle_choice, strip_canonical_metadata
from models import (
    BUStateOut,
    CommitTurnRequest,
    CommitTurnResponse,
    DashboardResponse,
    GlobalStateOut,
    JourneyResponseRequest,
    RoundSnapshot,
    StartSessionRequest,
    StartSessionResponse,
    MaterialitySubmissionRequest,
    MaterialitySubmissionResponse,
    SaveDecisionsRequest,
)
from round2_csrd import (
    CSRD_ISSUES, ROUND_2_DEFAULT_CONFIG, ASSURANCE_LABELS,
    ESRS_MAT_THRESHOLD, correct_quadrant_v2,
)

router = APIRouter(prefix="/api/simulations", tags=["Simulations"])

# BU display names
_BU_NAMES = {
    "pharma": "Muressons Pharma",
    "electronics": "Muressons Electronics",
    "consumer_goods": "Muressons Consumer Goods",
    "software": "Muressons Software",
    "hospitals": "Hospitals & Acute Care",
    "clinics": "Primary Care Clinics",
    "specialised_care": "Specialised Care Centers",
    "telehealth": "Digital Health / Telehealth",
    # UN SDG Edition regions
    "sub_saharan_corridor": "Sub-Saharan Corridor",
    "south_asia_subcontinent": "South Asia Subcontinent",
    "southeast_asia_hub": "South-East Asia Hub",
    "latin_america_basin": "Latin America Basin",
    "northern_transition_zone": "Northern Transition Zone",
    # Industry Verticals
    "oil_gas": "Muressons Oil & Gas",
    "banking_financial_services": "Muressons Banking & Financial Services",
    "retail_fmcg": "Muressons Retail/FMCG",
    "agriculture": "Muressons Agriculture",
    "technology": "Muressons Technology",
}

# ═══════════════════════════════════════════════════════════════════════════════
# VERTICAL_SLOT_MAP — maps every industry vertical ID to its owning seed slot.
# Used by /simulations/start, join_session, and session-info to derive the
# correct assigned_bu (always a seed slot ID: pharma|electronics|consumer_goods|software).
#
# Mirror of frontend VERTICAL_CATALOG in frontend/app/lib/verticalCatalog.js
# and backend SLOT_FIT_MAP in bu_profiles.py. Add new verticals to all three.
# ═══════════════════════════════════════════════════════════════════════════════
VERTICAL_SLOT_MAP: dict[str, str] = {
    # pharma slot
    "pharma": "pharma", "oil_gas": "pharma", "chemical": "pharma",
    "cosmetics": "pharma", "food_beverage": "pharma", "power_utilities": "pharma",
    # electronics slot
    "electronics": "electronics", "semiconductor": "electronics",
    "medical_devices": "electronics", "automotive": "electronics", "telecom": "electronics",
    # consumer_goods slot
    "consumer_goods": "consumer_goods", "retail_fmcg": "consumer_goods",
    "agriculture": "consumer_goods",
    # software slot
    "software": "software", "technology": "software",
    "banking_financial_services": "software",
}


def _bu_out(bu: dict) -> BUStateOut:
    """Map a raw BU dict to the Pydantic output model."""
    # Prefer bu_label (set by build_bu_states for verticals), then _BU_NAMES, then raw ID
    display_name = bu.get("bu_label") or _BU_NAMES.get(bu["bu_id"], bu["bu_id"])
    return BUStateOut(
        bu_id=bu["bu_id"],
        name=display_name,
        revenue_base=bu["revenue_base"],
        opex_base=bu["opex_base"],
        natural_capital_debt=bu.get("natural_capital_debt", 0),
        social_license_score=bu.get("social_license_score", 50),
        reputation_score=bu.get("reputation_score", 50),
        governance_risk_score=bu.get("governance_risk_score", 0),
        water_dependency=bu.get("water_dependency", 0),
        carbon_intensity=bu.get("carbon_intensity", 0),
        staff_burnout_index=bu.get("staff_burnout_index", 0),
        bed_capacity_utilization=bu.get("bed_capacity_utilization", 0),
        patient_outcomes_score=bu.get("patient_outcomes_score", 0),
        risk_factors=bu.get("risk_factors", {}),
    )


# ─────────────────────────────────────────────────────────────────
# PUBLIC SESSIONS: Fetch and Join
# ─────────────────────────────────────────────────────────────────

_session_players = {}

# ── RB-1 (UX audit §7.3): _session_players is process-local and was only ever
# rebuilt inside join_session, so after a backend restart every consumer
# (_cohort_commit_progress, _auto_commit_laggards, _cohort_advance_status)
# silently iterated an empty roster — the X/Y committed badge vanished and
# Force Advance "succeeded" while advancing nobody. rebuild_session_players()
# reconstructs the cohort→players map from the durable store via the parity
# API (fetch_all_sessions_raw works in BOTH memory and Postgres modes — never
# touches a store's private dicts), and only fills cohorts whose entry is
# missing/empty so it can never clobber live in-process state. Called once at
# startup (main.py lifespan) and as a throttled lazy self-heal from the
# consumers above.
import time as _rb_time
_roster_rebuild_last: float = 0.0
_ROSTER_REBUILD_MIN_INTERVAL_S = 30.0


async def rebuild_session_players(force: bool = False) -> int:
    """Rebuild _session_players from persisted sub-sessions. Returns the number
    of player entries restored. Throttled to one attempt per 30s unless forced
    (startup) so an empty-but-legitimate cohort can't turn every dashboard poll
    into a full session scan."""
    global _roster_rebuild_last
    now = _rb_time.monotonic()
    if not force and (now - _roster_rebuild_last) < _ROSTER_REBUILD_MIN_INTERVAL_S:
        return 0
    _roster_rebuild_last = now
    try:
        # A whole-platform scan is legitimate HERE: this rebuilds the roster map
        # for every cohort after a restart, throttled to once per 30 s.
        sessions = await db.fetch_all_sessions_raw()
    except Exception as exc:
        _log.warning(f"[ROSTER-REBUILD] fetch_all_sessions_raw failed: {exc}")
        return 0
    rebuilt: dict = {}
    for s in sessions:
        parent = s.get("parent_cohort_id")
        pid = s.get("player_id")
        sid = s.get("session_id")
        if parent and pid and sid:
            rebuilt.setdefault(parent, []).append(
                {"player_id": pid, "player_session_id": sid}
            )
    restored = 0
    for parent, players in rebuilt.items():
        if not _session_players.get(parent):
            _session_players[parent] = players
            restored += len(players)
    if restored:
        _log.info(f"[ROSTER-REBUILD] restored {restored} player entr(ies) "
                  f"across {len(rebuilt)} cohort(s)")
    return restored


# F-19: per-process tally of engine-module failures (exposed by /api/health so
# a monitor can alarm on a run where analytics silently stopped updating).
_ENGINE_FAILURE_COUNTER: dict = {"total": 0, "last": None}

# ── ITEM 4: Per-session commit rate limiter ──
_commit_timestamps = {}

# ── FIX-QA-003: Per-session async lock to prevent race conditions ──
# When two players in the same session submit simultaneously, the lock
# ensures they are serialized and the second commit sees the first's state.
import asyncio as _asyncio
_commit_locks = {}

def _get_commit_lock(session_id: str) -> _asyncio.Lock:
    """Get or create a per-session asyncio lock for commit serialization."""
    if session_id not in _commit_locks:
        _commit_locks[session_id] = _asyncio.Lock()
    return _commit_locks[session_id]


# F-28 (launch audit 2026-09-01): both maps grew for the life of the process —
# one entry per session that ever committed, never removed. A cooldown stamp
# is meaningless after 5 s and an idle lock after an hour, so prune them
# opportunistically (at most once a minute, on a commit).
_COMMIT_MAP_PRUNE_INTERVAL_S = 60.0
_COMMIT_MAP_IDLE_S = 3600.0
_commit_maps_last_prune = 0.0


def _prune_commit_maps(now: float) -> None:
    global _commit_maps_last_prune
    if now - _commit_maps_last_prune < _COMMIT_MAP_PRUNE_INTERVAL_S:
        return
    _commit_maps_last_prune = now
    stale = [sid for sid, ts in _commit_timestamps.items() if now - ts > _COMMIT_MAP_IDLE_S]
    for sid in stale:
        _commit_timestamps.pop(sid, None)
        lock = _commit_locks.get(sid)
        if lock is not None and not lock.locked():
            _commit_locks.pop(sid, None)


# ── F-26 (launch audit 2026-09-01): process-wide commit gate ──────────────
# The per-session lock above serialises commits for ONE team. Nothing bounded
# how many DIFFERENT teams could be mid-commit at once, and each of those holds
# a pooled connection (advisory lock) while its queries take a second one. At
# DB_MAX_CONNECTIONS concurrent commits the pool is fully held by advisory
# connections and every commit waits for a second connection nobody can free:
# on real Postgres 40 simultaneous R1 commits produced 0 successes. See
# config.COMMIT_MAX_IN_FLIGHT for the sizing rule.
#
# One semaphore per event loop: asyncio primitives bind to the loop that first
# makes them wait, and the test-suite's module-level TestClients run each
# request on a fresh loop.
_commit_gates: dict[int, _asyncio.Semaphore] = {}


def _commit_gate() -> _asyncio.Semaphore:
    from config import COMMIT_MAX_IN_FLIGHT
    loop = _asyncio.get_running_loop()
    gate = _commit_gates.get(id(loop))
    if gate is None:
        gate = _asyncio.Semaphore(COMMIT_MAX_IN_FLIGHT)
        # keep the map from growing with dead loops (tests create thousands)
        if len(_commit_gates) > 64:
            _commit_gates.clear()
        _commit_gates[id(loop)] = gate
    return gate


async def _enter_commit_gate() -> _asyncio.Semaphore:
    """Wait for a commit slot; 503 (retryable) if the queue is deeper than the
    configured patience. Returns the gate so the caller can release it."""
    from config import COMMIT_QUEUE_TIMEOUT_SECONDS
    gate = _commit_gate()
    try:
        await _asyncio.wait_for(gate.acquire(), timeout=COMMIT_QUEUE_TIMEOUT_SECONDS)
    except _asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "commit_queue_full",
                "message": "The server is processing a burst of commits. Your decisions "
                           "were not lost — please submit again in a moment.",
            },
            headers={"Retry-After": "5"},
        )
    return gate


# ═══════════════════════════════════════════════════════════════════════════
#  TEAM SEATS (UX audit #7, revised 2026-08-02 after client correction)
#
#  A team is REAL: up to 6 people, but exactly ONE of them drives.
#
#    • DRIVER   — holds the team's player credential (MUR-004). Unchanged: one
#                 session, one company, full read/write. The credential IS the
#                 driver seat, so handing over to another team member is just
#                 signing in as MUR-004 on their laptop.
#    • OBSERVER — holds the team's shared VIEW CODE (MUR-004-VIEW). Resolves to
#                 the SAME session and sees the same live board, but every
#                 mutating endpoint refuses it.
#
#  Architecture note: this adds NO new session, NO new game state and NO engine
#  change. An observer is a read-only identity pointed at an existing session,
#  which is why the whole feature is additive over a validated engine.
#
#  Security posture is FAIL-CLOSED: _assert_player_owns_session (used by all 28
#  player routes) rejects observers by default. A route must opt in with
#  allow_observer=True to be readable by a team's watchers — so any route added
#  later is driver-only until someone deliberately opens it.
# ═══════════════════════════════════════════════════════════════════════════

VIEW_CODE_SUFFIX = "-VIEW"


def _is_view_code(player_id: str) -> bool:
    return bool(player_id) and player_id.strip().upper().endswith(VIEW_CODE_SUFFIX)


def driver_id_for_view_code(view_code: str) -> str:
    """MUR-004-VIEW -> MUR-004. Pure string op; callers still verify that the
    driver record exists AND that the code matches the one actually issued."""
    vc = (view_code or "").strip().upper()
    return vc[: -len(VIEW_CODE_SUFFIX)] if vc.endswith(VIEW_CODE_SUFFIX) else vc


async def _assert_player_owns_session(request: Request, session_id: str, allow_observer: bool = False) -> None:
    """Bind the caller to the session it is acting on (SEC-3 / audit #9 / F-22).

    Rules:
      • Session has NO owner (solo / self-paced, player_id unset) → allowed. The
        high-entropy session UUID is the bearer; there is no other player to
        protect against.
      • A valid PLAYER TOKEN (Authorization: Bearer … or X-Player-Token, minted
        at /player-login) is the player credential. It must be scoped to THIS
        session; an observer token is admitted only where allow_observer=True.
      • A valid facilitator JWT cookie (console / observer) is admitted.
      • Anything else is refused. In particular a bare X-Player-Id header no
        longer identifies anyone (F-22, launch audit 2026-09-01): it was a
        plain, forgeable string, so whoever learned a team's session UUID and
        player id could read AND commit for that team. Such requests get a
        401 with code "player_token_required" so the client can re-login.
    """
    sess = await db.get_session_info(session_id)
    if not sess:
        return  # Session-not-found is handled by the caller.
    session_owner = sess.get("player_id", "")
    if not session_owner:
        return  # Unowned (solo) session — nothing to bind against.

    # 1. Player token (the credential) scoped to THIS session.
    try:
        from auth_jwt import get_player_from_request, get_facilitator_from_request
        tok = get_player_from_request(request)
        fac_id = get_facilitator_from_request(request)
    except Exception:
        tok, fac_id = None, None
    if tok and tok.get("session_id") == str(session_id):
        if tok.get("observer") and not allow_observer:
            # TEAM-1: observers may only read routes that opted in; every
            # mutation refuses. Fail-closed by default.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are signed in as a team observer. Only your team's driver can change or commit decisions.",
            )
        # F-22: a driver still on the id-derived initial password may READ
        # (the cockpit needs the board to render the forced change-password
        # modal) but may not play until the password is personal.
        if not tok.get("observer") and request.method.upper() not in ("GET", "HEAD", "OPTIONS") \
                and await _player_must_change_password(tok.get("player_id", ""), sess):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "password_change_required",
                    "message": "Set a personal password before playing — the initial one is only for signing in.",
                },
            )
        return

    # 2. Authenticated facilitator (console / observer) — no player token needed,
    #    but ONLY for a cohort they own / observe (F-21): any facilitator cookie
    #    used to be admitted, so a facilitator could read and commit for a team
    #    in someone else's cohort through the player routes. Checked before a
    #    mismatched player token so a facilitator whose browser still holds a
    #    player token from an earlier sign-in is not locked out of the console.
    if fac_id:
        from admin_router import _assert_session_visible, _assert_session_ownership
        if request.method.upper() in ("GET", "HEAD", "OPTIONS"):
            await _assert_session_visible(request, session_id)
        else:
            await _assert_session_ownership(request, session_id)
        return

    if tok:
        # Valid token, wrong session.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player is not the owner of this session.",
        )

    # 3. Legacy header-only client, or anonymous UUID-only caller.
    player_id_header = request.headers.get("X-Player-Id", "").strip()
    if player_id_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "player_token_required",
                "message": "Your sign-in has expired or this client is out of date. Please sign in again.",
            },
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing player credential: this session belongs to a registered player.",
    )


async def _player_must_change_password(player_id: str, sess: dict | None) -> bool:
    """True while the player's live credential is still the id-derived default.
    Reads the in-process registry first, then the cohort roster (durable in
    both stores) so a fresh worker gives the same answer."""
    if not player_id:
        return False
    try:
        from admin_shared import _player_registry
        rec = next((p for p in _player_registry if p.get("player_id") == player_id), None)
        if rec is not None:
            return bool(rec.get("must_change_password", False))
    except Exception:
        pass
    parent = (sess or {}).get("parent_cohort_id")
    roster_holder = sess or {}
    if parent:
        try:
            roster_holder = (await db.get_session_info(parent)) or {}
        except Exception:
            roster_holder = {}
    for rp in (roster_holder.get("registered_players") or []):
        if rp.get("player_id") == player_id:
            return bool(rp.get("must_change_password", False))
    return False


async def _cohort_sibling_rounds(parent: str) -> tuple[list[dict], list[int]]:
    """F-27: the latest round of every team in a cohort, in ONE store call.
    Returns (siblings, rounds). Both the commit badge and the free-advance
    status need this; the dashboard poll computes it once and hands it to both
    (they used to each issue one query per sibling)."""
    siblings = _session_players.get(parent, [])
    if not siblings:
        # RB-1 lazy self-heal: after a restart the roster map is empty even
        # though this IS a cohort sub-session (parent_cohort_id is set).
        # Rebuild from the durable store (throttled) before concluding solo.
        await rebuild_session_players()
        siblings = _session_players.get(parent, [])
    if not siblings:
        return [], []
    sids = [s.get("player_session_id") for s in siblings if s.get("player_session_id")]
    _batched = getattr(db, "fetch_latest_rounds", None)
    if _batched is not None:
        latest = await _batched(sids)
        rounds = [latest[sid] for sid in sids if sid in latest]
    else:  # pragma: no cover — store without the batched helper
        rounds = []
        for sid in sids:
            r = await db.fetch_latest_round(sid)
            if r is not None:
                rounds.append(r)
    return siblings, rounds


async def _cohort_commit_progress(session_info, rounds: list[int] | None = None,
                                  siblings: list[dict] | None = None):
    """MP-01 live badge: "X of Y teams committed the latest round" for a cohort
    sub-session. Returns (committed_count, team_count), or (None, None) for solo /
    non-cohort / before siblings are registered.

    'committed' = teams whose latest round equals the furthest round ANY team in
    the cohort has reached, so every team sees the same tally and it ticks up as
    teams catch up (then resets when the first team advances again). The
    sibling rounds may be passed in by a caller that already fetched them."""
    parent = (session_info or {}).get("parent_cohort_id")
    if not parent:
        return None, None
    if rounds is None or siblings is None:
        siblings, rounds = await _cohort_sibling_rounds(parent)
    if not siblings or not rounds:
        return None, None
    target = max(rounds)
    committed = sum(1 for r in rounds if r >= target)
    return committed, len(siblings)


# ═══════════════════════════════════════════════════════════════════════════
#  FREE-ADVANCE AUTO-RELEASE (facilitator timeout / force-advance)
#
#  In "free" pacing the cohort still holds a "waiting for other teams" barrier
#  until every team commits — one absent team deadlocks everyone. When the
#  facilitator sets free_advance_timeout_seconds (or presses Force Advance), the
#  barrier releases after the deadline and any straggler is auto-committed using
#  its saved decisions, so the whole cohort advances together and stays in sync.
#  Everything below is a no-op unless a positive timeout / force flag is set, so
#  solo play and legacy wait-for-all cohorts are completely unaffected.
# ═══════════════════════════════════════════════════════════════════════════

async def _run_commit_locked(session_id: str, body):
    """Lock-safe internal commit (no SEC binding) — mirrors the commit_turn HTTP
    wrapper so auto-commit / force-advance runs through the EXACT same engine
    path a real player commit does. Returns the response, or None if a real
    commit is already in flight (we defer to it)."""
    commit_lock = _get_commit_lock(session_id)
    if commit_lock.locked():
        return None
    await commit_lock.acquire()
    advisory = None
    gate = None
    try:
        gate = await _enter_commit_gate()  # F-26: bound in-flight commits per worker
        advisory = await db.acquire_advisory_lock(session_id)
        if advisory is None:
            return None
        return await _commit_turn_impl(session_id, body, commit_lock)
    finally:
        if advisory is not None:
            await db.release_advisory_lock(advisory, session_id)
        if gate is not None:
            gate.release()
        if commit_lock.locked():
            commit_lock.release()


def _auto_commit_request(global_state: dict, bu_states: list, round_number: int,
                         shuffle_seed=None, paradigm: str = "legacy_abc"):
    """Build a CommitTurnRequest from a team's SAVED decisions (a near-no-op
    roll-forward when nothing was saved). The engine recomputes investment_ratio
    from capex/csf_pool, so we only need a valid capex (>= $1) per BU.

    F-33 (launch audit 2026-09-01): the request is fed through the same commit
    path as a real player submission, which DESHUFFLES `choice_selected` as a
    displayed key. A saved draft IS a displayed key, so that is right for it —
    but the literal default "option_b" is a CANONICAL key, and deshuffling it
    handed the straggler whichever canonical option sat in display slot B that
    round (a random option), while the disclosure told the student "Option B".
    The default is now expressed in the session's display space, so it always
    deshuffles back to canonical option_b."""
    from models import CommitTurnRequest, BUDecision
    saved = (global_state or {}).get("saved_allocations") or {}
    choice = (global_state or {}).get("saved_decision_choice")
    if not choice:
        choice = "option_b"
        if shuffle_seed is not None and paradigm == "legacy_abc":
            try:
                from option_shuffle import get_shuffle_mapping
                choice = get_shuffle_mapping(shuffle_seed, round_number)["canonical_to_display"].get("option_b", "option_b")
            except Exception:
                choice = "option_b"
    treasury = (global_state or {}).get("corporate_treasury", 0) or 0
    csf_pool = max(treasury * 0.20, 5_000_000)
    decisions = []
    for bu in (bu_states or []):
        bu_id = bu.get("bu_id")
        if not bu_id:
            continue
        alloc = saved.get(bu_id, 0) or 0
        capex = max(1.0, float(alloc))
        inv = min(capex / csf_pool, 1.0) if csf_pool > 0 else 0.0
        decisions.append(BUDecision(
            bu_id=bu_id, investment_ratio=inv, capex_allocated=capex,
            choice_selected=choice, decision_node_id=f"round_{round_number}_{bu_id}",
            time_to_decision_seconds=0,
            # TEAM-3 (UX audit #7): an auto-commit is the canonical "no team
            # answered" case — recording 'majority' here was the fiction.
            team_consensus="not_recorded", pillar_decisions=None,
        ))
    return CommitTurnRequest(dividends_paid=0.0, decisions=decisions)  # engine params are server-derived (F-07)


async def _auto_commit_laggards(parent_cohort_id: str, target_round: int) -> int:
    """Auto-commit every team in the cohort still behind target_round using its
    saved decisions. Best-effort and idempotent: a team already at/after the
    target, or one mid-commit, is skipped; a lost race is turned into a harmless
    409 by the uq_session_round guard. Returns the count advanced."""
    siblings = _session_players.get(parent_cohort_id, [])
    if not siblings:
        # RB-1 lazy self-heal (see rebuild_session_players): without this,
        # Force Advance after a backend restart reports success and advances
        # nobody because the process-local roster map is empty.
        await rebuild_session_players()
        siblings = _session_players.get(parent_cohort_id, [])
    advanced = 0
    for s in siblings:
        sid = s.get("player_session_id")
        if not sid:
            continue
        try:
            latest = await db.fetch_latest_round(sid)
            if latest is None or latest >= target_round:
                continue
            state = await db.fetch_latest_state(sid)
            if not state:
                continue
            # AC-1 (UX audit §7.8): remember whether a saved draft existed so the
            # disclosure below can tell the player exactly what was submitted.
            _gs = state.get("global_state") or {}
            had_draft = bool(_gs.get("saved_allocations") or _gs.get("saved_decision_choice"))
            _sinfo = await db.get_session_info(sid) or {}
            body = _auto_commit_request(state["global_state"], state["bu_states"], latest,
                                        shuffle_seed=_sinfo.get("shuffle_seed"),
                                        paradigm=_sinfo.get("decision_paradigm", "legacy_abc"))
            # OPS-1 (WP-17): a server-initiated commit for a team that has not
            # committed this round is not a double-submit — the 5-s cooldown
            # guards the client's button, not the facilitator's timer.
            _commit_timestamps.pop(sid, None)
            if await _run_commit_locked(sid, body) is not None:
                advanced += 1
                # AC-1: stamp a persistent disclosure onto the new round's flags.
                # Metadata only — written AFTER the engine ran, never read by it.
                try:
                    newest = await db.fetch_latest_state(sid)
                    if newest:
                        ng = newest["global_state"]
                        nflags = ng.get("active_event_flags") or {}
                        nflags["auto_committed"] = True
                        nflags["auto_committed_source"] = "draft" if had_draft else "default"
                        nflags["auto_committed_reason"] = (
                            "Facilitator advance / timeout — committed from your saved draft"
                            if had_draft else
                            "Facilitator advance / timeout — committed with defaults (Option B, $1 per business unit)"
                        )
                        ng["active_event_flags"] = nflags
                        await db.update_latest_global_state(sid, ng, newest["bu_states"])
                except Exception as _ac_exc:
                    _log.warning(f"[FREE-ADVANCE] disclosure stamp failed for {sid}: {_ac_exc}")
        except Exception as exc:
            _log.warning(f"[FREE-ADVANCE] auto-commit failed for {sid}: {exc}")
    return advanced


async def _cohort_advance_status(session_info, committed=None, teams=None,
                                 rounds: list[int] | None = None):
    """Compute the free-advance barrier state for a cohort sub-session and
    ENFORCE the deadline (auto-commit stragglers once it lapses or a force flag
    is set). Returns {deadline_at, unblocked, committed} or None for
    solo/non-cohort. Safe to call on every dashboard read: it only writes when a
    positive timeout has actually lapsed (or Force Advance was pressed).
    `rounds` (the siblings' latest rounds) may be supplied by a caller that
    already fetched them (F-27)."""
    from datetime import datetime, timezone, timedelta
    from admin_shared import _get_pacing
    parent = (session_info or {}).get("parent_cohort_id")
    if not parent:
        return None
    if rounds is None:
        _sibs, rounds = await _cohort_sibling_rounds(parent)
        if committed is None or teams is None:
            committed, teams = await _cohort_commit_progress(session_info, rounds=rounds, siblings=_sibs)
    elif committed is None or teams is None:
        committed, teams = await _cohort_commit_progress(session_info, rounds=rounds,
                                                         siblings=_session_players.get(parent, []))
    if teams is None:
        return None
    if not rounds:
        return None
    max_r, min_r = max(rounds), min(rounds)
    in_sync = (min_r == max_r)

    pacing = _get_pacing(parent)

    # FACILITATOR-PACED ADVANCE: under manual/timed pacing the wait-for-all-teams
    # barrier does not apply at all. Each team commits whenever it is ready (its
    # values are saved and its state advances), and the NEXT round's commit is
    # gated by is_round_unlocked against the facilitator's pacing — the round
    # advances when the timer fires or the facilitator unlocks it manually. No
    # auto-commit of stragglers here: a team that skipped a round simply catches
    # up at its own pace inside the unlocked window.
    if pacing.get("mode") != "free":
        return {
            "deadline_at": pacing.get("next_unlock_at"),
            "unblocked": True,
            "committed": committed,
            "teams": teams,
        }

    timeout = int(pacing.get("free_advance_timeout_seconds", 0) or 0)
    forced = bool(pacing.get("_fa_force"))
    now = datetime.now(timezone.utc)
    deadline_iso = None
    unblocked = in_sync

    if pacing.get("mode") == "free" and timeout > 0:
        # Fixed per-round budget: arm the deadline when a round OPENS for the
        # cohort (the active round = the slowest team's round, min_r). Arming at
        # round-open — not at first-commit — means the countdown reflects the
        # whole round's time budget, so the barrier that appears after the first
        # commit shows the REMAINING time, not a fresh full clock.
        if pacing.get("_fa_round") != min_r or not pacing.get("_fa_deadline_at"):
            pacing["_fa_round"] = min_r
            pacing["_fa_deadline_at"] = (now + timedelta(seconds=timeout)).isoformat()
        deadline_iso = pacing["_fa_deadline_at"]
        # Only the barrier (someone is behind) can be released by the timeout.
        if not in_sync:
            try:
                if now >= datetime.fromisoformat(deadline_iso):
                    unblocked = True
            except Exception:
                unblocked = True

    if forced:
        unblocked = True

    if unblocked and not in_sync:
        await _auto_commit_laggards(parent, max_r)
        pacing["_fa_round"] = None
        pacing["_fa_deadline_at"] = None
        pacing["_fa_force"] = False
        committed, teams = await _cohort_commit_progress(session_info)

    return {"deadline_at": deadline_iso, "unblocked": bool(unblocked), "committed": committed, "teams": teams}


@router.get("/public/sessions", summary="List active public sessions")
async def get_active_sessions():
    """
    Returns a list of all active public sessions (cohorts) that have less than 5 players.
    """
    rows = await db.get_active_public_sessions()
    
    available = []
    for row in rows:
        sid = str(row["session_id"])
        players = _session_players.get(sid, [])
        if len(players) < 5:
            available.append({
                "session_id": sid,
                "cohort_name": row["cohort_name"],
                "player_count": len(players)
            })
    return {"sessions": available}

class SetUsernameRequest(BaseModel):
    user_id: str
    role: str
    username: str

@router.post("/set-username", summary="Set unique username")
async def set_username(request: Request, req: SetUsernameRequest):
    from admin_shared import (
        _player_registry, _facilitator_registry, _persist_facilitators,
        _virtual_account_profiles, is_virtual_facilitator, set_virtual_username,
    )
    import database_memory

    # F-24 (launch audit 2026-09-01): this was fully unauthenticated — anyone
    # could rename any player or facilitator and probe which ids exist. A player
    # may rename only the identity their token carries; a facilitator only their
    # own account (admins may rename anyone).
    from auth_jwt import get_player_from_request, get_facilitator_from_request
    _tok = get_player_from_request(request)
    _fac_caller = get_facilitator_from_request(request)
    if req.role == "player":
        _tok_pid = (_tok or {}).get("player_id", "")
        _tok_sid = (_tok or {}).get("session_id", "")
        # (Local alias: `db` is re-imported as a function local further down,
        # so the module-level name is shadowed and unbound at this point.)
        import database as _db_su
        if _tok and (_tok_pid == req.user_id or _tok_sid == req.user_id):
            pass  # the player renames itself
        elif _fac_caller:
            # A facilitator may rename players only in cohorts it can see
            # (owner / co-facilitator / admin) — not every player on the platform.
            from admin_router import _assert_session_visible as _asv
            _target_cohort = None
            _rec = next((p for p in _player_registry if p.get("player_id") == req.user_id), None)
            if _rec:
                _target_cohort = _rec.get("session_id")
            if not _target_cohort:
                _sess = await _db_su.get_session_info(req.user_id)
                if _sess:
                    _target_cohort = _sess.get("parent_cohort_id") or req.user_id
                else:
                    for _sid, _s in database_memory._sessions.items():
                        if _s.get("player_id") == req.user_id:
                            _target_cohort = _s.get("parent_cohort_id") or _sid
                            break
            if _target_cohort:
                await _asv(request, _target_cohort)
        else:
            # Solo sessions have no owner and no token: the session UUID itself
            # is the bearer, exactly as on every other solo route.
            _solo = await _db_su.get_session_info(req.user_id)
            if not (_solo and not _solo.get("player_id")):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail={"code": "player_token_required", "message": "Sign in to change your team name."})
    elif req.role == "facilitator":
        if not _fac_caller:
            raise HTTPException(status_code=401, detail="Facilitator authentication required")
        if _fac_caller != req.user_id and _fac_caller != "god_mode":
            from admin_shared import get_role as _get_role, is_admin_role as _is_admin
            _caller_rec = next((f for f in _facilitator_registry if f.get("facilitator_id") == _fac_caller), None)
            if not (_caller_rec and _is_admin(_get_role(_caller_rec))):
                raise HTTPException(status_code=403, detail="You can only rename your own account.")

    username_lower = req.username.strip().lower()
    if not username_lower:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    for p in _player_registry:
        if p.get("username", "").strip().lower() == username_lower and p.get("player_id") != req.user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")
    for f in _facilitator_registry:
        if f.get("username", "").strip().lower() == username_lower and f["facilitator_id"] != req.user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")
    # Virtual break-glass accounts (god_mode / facilitator / project_admin) hold
    # their usernames in the virtual-profile store, not the registry — include
    # them in the global uniqueness sweep.
    for vid, vprof in _virtual_account_profiles.items():
        if (vprof.get("username", "").strip().lower() == username_lower
                and vid != req.user_id):
            raise HTTPException(status_code=400, detail="Username already taken.")

    if req.role == "player":
        import database as db
        player = next((p for p in _player_registry if p.get("player_id") == req.user_id), None)
        
        target_session_id = None
        if not player:
            # Try direct session ID (frontend sends sessionId when localStorage lacks playerId)
            sess = db._sessions.get(req.user_id)
            if sess:
                # Auto-bridge Solo Sessions (which lack player_id) by treating the session UUID as the player context
                assigned_pid = sess.get("player_id") or f"solo-{req.user_id[:8]}"
                player = {"player_id": assigned_pid, "session_id": req.user_id}
                target_session_id = req.user_id
            
            # Fallback to searching by player string ID explicitly
            if not player:
                for sid, s in db._sessions.items():
                    if s.get("player_id") == req.user_id:
                        player = {"player_id": req.user_id, "session_id": s.get("parent_cohort_id")}
                        target_session_id = sid
                        break
                    
        if not player:
            raise HTTPException(status_code=404, detail="Player not found.")
            
        player["username"] = req.username.strip()
        
        session_id = player.get("session_id") or target_session_id
        if session_id:
            cohort = await db.get_session_info(session_id)
            if cohort:
                reg = cohort.get("registered_players", [])
                changed = False
                for p_rec in reg:
                    if p_rec["player_id"] == req.user_id:
                        p_rec["username"] = req.username.strip()
                        changed = True
                # Fix #6: persist the mutated roster through the db interface
                # (durable under Postgres, not just the memory mirror + snapshot).
                if changed:
                    await db.update_session_metadata(session_id, {"registered_players": reg})

            # Update all active sessions owned by this player (discover via the
            # mirror cache, write durably per session through the db interface).
            for sid, sess in list(database_memory._sessions.items()):
                if sess.get("player_id") == req.user_id:
                    await db.update_session_metadata(sid, {
                        "player_name": req.username.strip(),
                        "cohort_name": f"Player ({req.username.strip()})",
                    })
    elif req.role == "facilitator":
        # Virtual accounts (god_mode / facilitator / project_admin) are NOT
        # registry rows by design — their mutable profile state lives in the
        # dedicated virtual-profile store. Registry facilitators are unchanged.
        if is_virtual_facilitator(req.user_id):
            set_virtual_username(req.user_id, req.username)
        else:
            fac = next((f for f in _facilitator_registry if f["facilitator_id"] == req.user_id), None)
            if not fac:
                raise HTTPException(status_code=404, detail="Facilitator not found.")
            fac["username"] = req.username.strip()
            _persist_facilitators()
    else:
        raise HTTPException(status_code=400, detail="Invalid role.")
        
    return {"status": "success", "username": req.username.strip()}

class JoinSessionRequest(BaseModel):
    player_id: str
    password: str = ""  # Password from player induction
    player_name: str = ""  # Display name for the player
    join_code: str = ""  # Cohort join code (required only when the cohort sets one)
    consent: bool = False  # Data-processing consent (required only when the cohort demands it)

class PlayerLoginRequest(BaseModel):
    player_id: str
    password: str = ""

@router.post("/player-login", summary="Player login — auto-resolves cohort from Player ID")
async def player_login(request: Request, req: PlayerLoginRequest):
    """
    Simplified player login: only Player ID + Password required.
    Looks up the player's cohort from the registry and joins/re-joins automatically.
    Returns the player's session info so the frontend can resume where they left off.
    """
    # HIGH-009 + QA-2026-07-16 #7: rate-limit player login. Key the tight
    # brute-force cap by player_id so a NATed classroom (many players, one public
    # IP) is not locked out at "everyone log in now"; keep a generous per-IP
    # ceiling so a single machine still can't stuff unlimited accounts.
    _check_rate_limit(request, "player_login", identity=getattr(req, "player_id", None))
    _check_rate_limit(request, "player_login")

    from admin_shared import _player_registry

    # TEAM-1 (UX audit #7): a team's OBSERVERS sign in with the shared view code
    # (MUR-004-VIEW). Resolve it to the driver's record so they land on the same
    # session, then mark the response is_observer so the client renders
    # read-only and every mutating route refuses them server-side.
    _requested_id = (req.player_id or "").strip()
    _as_observer = _is_view_code(_requested_id)
    _lookup_id = driver_id_for_view_code(_requested_id) if _as_observer else _requested_id

    # Find the player in the registry. F-40 (launch audit 2026-09-01): ids
    # issued before the platform-wide uniqueness fix may exist in MORE than one
    # cohort. Collect every candidate and, when there are several, pick the one
    # whose password verifies instead of blindly taking the first — otherwise a
    # team could be signed into another cohort's game, or told its password is
    # wrong because a stranger's record came first.
    _candidates = [p for p in _player_registry if p.get("player_id") == _lookup_id]

    if not _candidates:
        import database as db
        for sid, sess in db._sessions.items():
            # Check player's own sub-session
            if sess.get("player_id") == _lookup_id:
                _candidates.append({"player_id": _lookup_id, "session_id": sess.get("parent_cohort_id")})
                continue
            # Check pre-generated players in registered_players (survives server restart)
            _found_here = False
            for rp in sess.get("registered_players", []):
                if rp.get("player_id") == _lookup_id:
                    _candidates.append(rp)
                    _found_here = True
                    # Re-hydrate into _player_registry so future logins are fast
                    from admin_shared import _player_registry as _reg
                    if not any(p.get("player_id") == _lookup_id and p.get("session_id") == rp.get("session_id") for p in _reg):
                        _reg.append(rp)
                    break
            if _found_here:
                continue
            # allowed_player_ids: player was pre-generated via generate-player endpoint.
            # Their actual password is stored in _player_registry (added by generate_player_id).
            # Fall back to an empty stored_pw so the password check below handles it.
            if _lookup_id in sess.get("allowed_player_ids", []):
                _candidates.append({"player_id": _lookup_id, "session_id": sid, "password": ""})

    player_record = _candidates[0] if _candidates else None
    if len(_candidates) > 1 and not verify_player_master_password(req.password):
        _verified = []
        for c in _candidates:
            if c.get("password") and await _verify_pw_async(req.password, c["password"]):  # F-30: off-loop bcrypt
                _verified.append(c)
        if len(_verified) == 1:
            player_record = _verified[0]
        elif not _verified:
            # No candidate matches: fall through to the normal "Incorrect
            # password" path against the first record (unchanged behaviour).
            player_record = _candidates[0]
        else:
            # Same id AND same (default) password in several cohorts: refusing
            # is the only safe answer — logging in would be a coin toss between
            # two teams' games. The facilitator re-issues one of the ids.
            _log.error(f"[F-40] player id {_lookup_id} is ambiguous across "
                       f"{len(_verified)} cohorts — refusing login")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "player_id_ambiguous",
                        "message": "This player id exists in more than one cohort. "
                                   "Ask your facilitator to issue a fresh id."},
            )

    if not player_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player ID not found. Please check with your facilitator."
        )

    # LOW-003: Use bcrypt-aware verify (falls back to plaintext for legacy records)
    stored_pw = player_record.get("password", "")
    # P6: player unlock uses the SEPARATE player master secret, not the admin one.
    master_ok = verify_player_master_password(req.password)
    # SEC: An empty stored password must never *bypass* a real one. If this
    # record's password is blank (e.g. the `allowed_player_ids` fallback path),
    # cross-check the authoritative registry so a placeholder can't skip a
    # password that actually exists. Genuinely passwordless players (blank
    # everywhere) keep their intended ID-only join flow unchanged.
    if not stored_pw and not master_ok:
        try:
            from admin_shared import _player_registry as _reg
            real_pw = next(
                (p.get("password", "") for p in _reg if p.get("player_id") == _lookup_id),
                "",
            )
            if real_pw:
                stored_pw = real_pw
        except Exception:
            pass
    if stored_pw and not master_ok and not await _verify_pw_async(req.password, stored_pw):  # F-30
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect password."
        )
    # Auto-upgrade plaintext player passwords to bcrypt on successful login
    if stored_pw and not master_ok:
        upgraded = await _maybe_upgrade_pw_async(req.password, stored_pw)
        if upgraded:
            player_record["password"] = upgraded

    # Get the cohort session_id
    cohort_session_id = player_record.get("session_id", "")
    if not cohort_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player not assigned to any cohort yet. Ask your facilitator to assign you."
        )

    # TEAM-1: an observer authenticates against the team's VIEW CODE password,
    # never the driver's. Checked here (before the join delegation) so a wrong
    # view code can never fall through to the driver's credential path.
    if _as_observer:
        _vc_issued = (player_record.get("team_view_code") or "").upper()
        _vc_hash = player_record.get("team_view_password") or ""
        if not _vc_issued or _vc_issued != _requested_id.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No observer seat is open for this team. Ask your facilitator for the team's view code.",
            )
        if _vc_hash and not await _verify_pw_async(req.password, _vc_hash):  # F-30
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect view-code password.")

    # Delegate to the existing join logic. Observers join with the DRIVER's id
    # so they attach to the team's existing session rather than minting one —
    # an observer never creates game state.
    join_req = JoinSessionRequest(
        player_id=_lookup_id,
        password=req.password,
        player_name=player_record.get("name", ""),
    )
    join_result = await _join_session_impl(cohort_session_id, join_req,
                                           bypass_password=_as_observer)

    # Fetch current round so frontend can resume
    player_sid = join_result.get("session_id") if isinstance(join_result, dict) else join_result["session_id"]
    current_round = 1
    try:
        latest = await db.fetch_latest_state(player_sid)
        if latest:
            current_round = latest["round_number"]
    except Exception:
        pass

    # SEC/HIGH-001: mint a signed, session-scoped ws ticket so the player push
    # channel no longer treats the raw session_id as a credential. Best-effort:
    # if JWT is unavailable the ticket is "" and the client degrades to polling.
    ws_ticket = ""
    player_token = ""
    try:
        from auth_jwt import create_player_ws_ticket, create_player_token
        ws_ticket = create_player_ws_ticket(player_sid, _requested_id)
        # F-22: the HTTP credential. Observers get a token flagged observer so
        # every mutating route (and every read that did not opt in) refuses it.
        player_token = create_player_token(player_sid, _requested_id, observer=_as_observer)
    except Exception:
        ws_ticket = ""
        player_token = ""

    return {
        "status": join_result.get("status", "joined") if isinstance(join_result, dict) else "joined",
        "session_id": player_sid,
        "cohort_session_id": cohort_session_id,
        "cohort_name": player_record.get("cohort_name", ""),
        "player_name": player_record.get("name", ""),
        "username": player_record.get("username", ""),
        "current_round": current_round,
        "ws_ticket": ws_ticket,
        # F-22: signed, session-scoped bearer token; the client sends it as
        # `Authorization: Bearer …` on every player request.
        "player_token": player_token,
        # TEAM-1: the client renders a read-only cockpit when this is true. The
        # server does not rely on it — every mutation is refused independently.
        "is_observer": _as_observer,
        "player_id": _requested_id,
        "team_driver_id": _lookup_id if _as_observer else None,
        # Signal the frontend to force a password change on first login
        # (never for an observer — the view code is a shared, rotatable token).
        "must_change_password": (not _as_observer) and bool(player_record.get("must_change_password", False)),
    }


async def _join_session_impl(session_id: str, req: JoinSessionRequest, *,
                             bypass_password: bool = False):
    """
    Registers a player into a cohort by creating an independent session for them.
    Each player gets their own game state starting at Round 1.
    Maximum 5 players per cohort.
    """
    # Validate player ID against the cohort session
    is_valid = await db.validate_player_id(session_id, req.player_id)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Player ID for this session.")

    # Validate password against player registry
    # Pre-initialise to None so it's always in scope below for assigned_bu lookup.
    player_record = None
    try:
        from admin_shared import _player_registry
        # F-40: prefer the record that belongs to THIS cohort — a legacy id
        # colliding across cohorts must not be checked against a stranger's hash.
        player_record = next((p for p in _player_registry
                              if p.get("player_id") == req.player_id
                              and p.get("session_id") == session_id), None)
        if player_record is None:
            player_record = next((p for p in _player_registry if p.get("player_id") == req.player_id), None)
        # QA-2026-07-16 #4: after a restart (or on another worker) the per-process
        # _player_registry may be empty, but the bcrypt credential is durable in
        # the cohort session's registered_players metadata. Fall back to it so the
        # password check is NEVER silently skipped (fail-closed) — previously a
        # missing registry entry meant "if player_record and ..." was false and
        # the player_id alone logged in.
        if not player_record:
            _cohort = await db.get_session_info(session_id)
            for rp in (_cohort or {}).get("registered_players", []):
                if rp.get("player_id") == req.player_id:
                    player_record = rp
                    break
        if player_record and player_record.get("password") and not bypass_password:
            # LOW-003: bcrypt-aware comparison
            # P6: player unlock uses the SEPARATE player master secret.
            # `bypass_password` is keyword-only and this function has NO route, so
            # it is reachable ONLY from player_login, which sets it after verifying
            # a team view code against team_view_password. It cannot come from the
            # wire in any form — see the note on join_session below.
            master_ok = verify_player_master_password(req.password)
            if not master_ok and not await _verify_pw_async(req.password, player_record["password"]):  # F-30
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password.")
    except ImportError:
        pass  # admin_router not available, skip password check

    players = _session_players.get(session_id, [])

    # Rebuild _session_players from sub-sessions if it's empty
    # (happens after server restart — sub-sessions still exist in _sessions)
    if not players:
        try:
            from database_memory import _sessions as all_sessions
            for sid, sdata in all_sessions.items():
                if sdata.get("parent_cohort_id") == session_id and sdata.get("player_id"):
                    players.append({
                        "player_id": sdata["player_id"],
                        "player_session_id": sid,
                    })
            if players:
                _session_players[session_id] = players
        except ImportError:
            pass

    # Check if this player already joined — return their existing session
    for p in players:
        if p.get("player_id") == req.player_id:
            return {
                "status": "rejoined",
                "session_id": p["player_session_id"],
                "player_count": len(players),
                "player_token": _mint_player_token(p["player_session_id"], req.player_id, bypass_password),
            }

    # ── MEDIUM-tier join-policy enforcement (new joins only — rejoin above is
    # always allowed so a policy change never locks out an existing player) ──
    try:
        from admin_shared import get_effective_settings as _ges
        _join_eff = _ges(session_id)
    except Exception:
        _join_eff = {}

    # Join code: enforced only when the facilitator explicitly set one AND the
    # cohort's join_method is "code" — unconfigured cohorts behave exactly as
    # before (fail-open). Comparison is trimmed + case-insensitive.
    _cfg_code = str(_join_eff.get("join_code", "") or "").strip()
    if _cfg_code and _join_eff.get("join_method", "code") == "code":
        if (req.join_code or "").strip().upper() != _cfg_code.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This cohort requires a join code. Ask your facilitator for it.",
            )

    # Consent capture (LOW-tier compliance): when the cohort requires it, a new
    # join must carry consent=true; the acceptance timestamp is recorded on the
    # player's session below. Unconfigured cohorts skip this entirely.
    _consent_required = bool(_join_eff.get("consent_required", False))
    if _consent_required and not req.consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(_join_eff.get("consent_text", "").strip()
                    or "This cohort requires your consent to data processing before joining."),
        )

    # Late-join policy: "closed" blocks all new joins; "before_round_2" blocks
    # once any team in the cohort has advanced past Round 1. "anytime" = legacy.
    _late_policy = _join_eff.get("late_join_policy", "anytime")
    if _late_policy == "closed":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This cohort is closed to new joins. Contact your facilitator.",
        )
    if _late_policy == "before_round_2":
        try:
            _max_round = 1
            for _child in await db.get_child_sessions(session_id):
                _cl = await db.fetch_latest_state(_child["session_id"])
                if _cl:
                    _max_round = max(_max_round, int(_cl.get("round_number", 1) or 1))
            if _max_round > 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This cohort no longer accepts new joins — the simulation is past Round 1.",
                )
        except HTTPException:
            raise
        except Exception:
            pass  # fail-open: a state-read hiccup never blocks a legitimate join

    # Roster cap: honour the cohort's configured team_count / max_players.
    # Unconfigured ⇒ the platform default (20, the ceiling — raised from the
    # legacy 5 on 2026-07-31 so a forgotten setting can't bounce students).
    try:
        from admin_shared import resolve_roster_cap as _rrc
        _roster_cap = _rrc(session_id)
    except Exception:
        _roster_cap = 20
    if len(players) >= _roster_cap:
        raise HTTPException(
            status_code=400,
            detail=f"Cohort has reached its roster cap of {_roster_cap} player(s).",
        )

    # Fetch parent cohort info for naming and mode inheritance
    cohort_info = await db.get_session_info(session_id)
    cohort_name = cohort_info["cohort_name"] if cohort_info else "Unknown"

    # Inherit simulation mode from the parent cohort so player sub-sessions
    # reflect whether this cohort runs as single-BU or full conglomerate.
    _cohort_sim_mode = cohort_info.get("simulation_mode", "") if cohort_info else ""
    _cohort_industry = cohort_info.get("industry_vertical", "") if cohort_info else ""

    # Resolve the player's individual assigned_bu:
    #   Priority 1 — per-player registry entry set by the facilitator at induction time
    #                 (e.g. 'pharma', 'electronics', 'consumer_goods', 'software').
    #   Priority 2 — cohort-level assigned_bu (used only when the whole cohort runs
    #                 as a single entity, e.g. god-mode global single-BU deployment).
    # player_record was already fetched above for password validation.
    _player_assigned_bu = ""
    _player_industry = ""
    _player_region = ""
    try:
        if player_record is None:
            from admin_shared import _player_registry as _reg
            player_record = next((p for p in _reg if p.get("player_id") == req.player_id), None)
        if player_record:
            _player_assigned_bu = player_record.get("assigned_bu", "") or ""
            _player_industry = player_record.get("industry_vertical", "") or ""
            _player_region = player_record.get("region_id", "") or ""
    except Exception:
        pass

    _cohort_assigned_bu = cohort_info.get("assigned_bu", "") if cohort_info else ""
    _cohort_region = cohort_info.get("region_id", "") if cohort_info else ""
    _effective_assigned_bu = _player_assigned_bu or _cohort_assigned_bu or None

    # The player's OWN company, in a single-business cohort where each player
    # runs one. The vertical decides the BU's profile (stats, label, icon) and
    # the slot only decides which seed position it occupies, so a per-player
    # vertical is what actually makes two players' businesses differ —
    # create_session already builds the single BU from (slot, vertical); it was
    # simply never handed the player's own vertical, only the cohort's, so every
    # player in a single-business cohort ran the same company no matter what the
    # roster said. The cohort's value remains the fallback: a player with no
    # vertical of their own (a bare generated id, or a pre-existing roster) keeps
    # exactly the behaviour they had.
    _effective_industry = _cohort_industry
    _effective_region = _cohort_region
    if _cohort_sim_mode == "single_bu":
        _effective_industry = _player_industry or _cohort_industry
        _effective_region = _player_region or _cohort_region
        if _player_industry:
            # Keep the slot congruent with the vertical actually being built,
            # rather than trusting a stored slot that may predate a roster edit.
            _effective_assigned_bu = VERTICAL_SLOT_MAP.get(_player_industry, _player_industry)

    # Single-BU fallback (mirrors session-info Fallback 3): cohorts created
    # before the per-session assigned_bu write carry only industry_vertical —
    # derive the scope from it so a joining player never silently lands in the
    # 4-BU conglomerate. create_session resolves vertical ids itself, so the
    # raw industry_vertical is a valid value to pass here.
    if not _effective_assigned_bu and _cohort_sim_mode == "single_bu" and _effective_industry:
        _effective_assigned_bu = VERTICAL_SLOT_MAP.get(_effective_industry, _effective_industry)

    # Create an independent session for this player
    player_session = await db.create_session(
        cohort_name=cohort_name,
        facilitator_id=cohort_info.get("facilitator_id") if cohort_info else None,
        player_id=req.player_id,
        parent_cohort_id=session_id,
        decision_paradigm=cohort_info.get("decision_paradigm", "legacy_abc") if cohort_info else "legacy_abc",
        currency_symbol=cohort_info.get("currency_symbol", "$") if cohort_info else "$",
        simulation_mode=_cohort_sim_mode or None,
        industry_vertical=_effective_industry or None,
        region_id=_effective_region or None,
        assigned_bu=_effective_assigned_bu,
    )

    player_sid = str(player_session["session_id"])

    # ENDING PATHWAY INHERITANCE (2026-07-31, found by the 5-endings drill):
    # /start writes the cohort's chosen (or 'random'-resolved) pathway onto the
    # COHORT's round flags, but this child-session create never received it —
    # memory seeded the child from the GLOBAL default and Postgres seeded
    # nothing — so every player played activist_ultimatum no matter what the
    # facilitator picked. Copy the cohort's resolved flag onto the child, the
    # same write /start uses. Fail-open: a missing flag leaves the child on
    # the default exactly as before.
    try:
        _cohort_latest = await db.fetch_latest_state(session_id)
        _cohort_ep = ((_cohort_latest or {}).get("global_state", {})
                      .get("active_event_flags", {}) or {}).get("ending_pathway")
        if _cohort_ep:
            # 'random' on the cohort is intent, not a pathway: each player
            # draws their OWN concrete ending here, so one cohort's debrief
            # compares several finales. A named pathway copies verbatim.
            if _cohort_ep == "random":
                from ending_pathways import resolve_pathway as _resolve_ep
                _cohort_ep = _resolve_ep("random")
            _child_latest = await db.fetch_latest_state(player_sid)
            if _child_latest:
                _cgs = _child_latest["global_state"]
                if (_cgs.get("active_event_flags", {}) or {}).get("ending_pathway") != _cohort_ep:
                    # BOTH locations: the memory round also carries a TOP-LEVEL
                    # ending_pathway, and the persist repack prefers top-level
                    # keys — writing only the flag was silently overwritten by
                    # the stale top-level value (verified step-by-step).
                    _cgs["ending_pathway"] = _cohort_ep
                    _cgs.setdefault("active_event_flags", {})["ending_pathway"] = _cohort_ep
                    await db.update_latest_global_state(player_sid, _cgs, _child_latest["bu_states"])
    except Exception:
        pass  # never block a join over pathway bookkeeping

    # Consent capture (LOW-tier compliance): record the acceptance + timestamp
    # on the player's session so it is auditable and survives restarts.
    if _consent_required:
        try:
            from datetime import datetime as _dt, timezone as _tz
            import database_memory as _dm_consent
            _psess = _dm_consent._sessions.get(player_sid)
            if _psess is not None:
                _psess["consent_given_at"] = _dt.now(_tz.utc).isoformat()
        except Exception:
            pass

    # Track the mapping
    players.append({"player_id": req.player_id, "player_session_id": player_sid})
    _session_players[session_id] = players

    # Update the player registry with the name so it shows in facilitator view
    try:
        from admin_shared import _player_registry
        player_record = next((p for p in _player_registry if p.get("player_id") == req.player_id), None)
        if player_record:
            if req.player_name:
                player_record["name"] = req.player_name
            player_record["session_id"] = session_id
            player_record["status"] = "joined"
        elif req.player_name:
            # Player not in registry yet (edge case), add them
            from datetime import datetime, timezone
            _player_registry.append({
                "player_id": req.player_id,
                "name": req.player_name,
                "email": "",
                "assigned_bu": "",
                "session_id": session_id,
                "password": req.password,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "joined",
            })
        
        # Also update session-level registered_players so name persists
        parent_sess = await db.get_session_info(session_id)
        if parent_sess:
            rp = parent_sess.get("registered_players", [])
            for p in rp:
                if p.get("player_id") == req.player_id:
                    if req.player_name:
                        p["name"] = req.player_name
                    p["status"] = "joined"
                    break
            else:
                # Player not found in session's registered_players, add
                if req.player_name:
                    rp.append({
                        "player_id": req.player_id,
                        "name": req.player_name,
                        "email": "",
                        "assigned_bu": "",
                        "session_id": session_id,
                        "password": req.password,
                        "created_at": datetime.now(timezone.utc).isoformat() if 'datetime' in dir() else "",
                        "status": "joined",
                    })
            parent_sess["registered_players"] = rp
    except ImportError:
        pass

    return {
        "status": "joined",
        "session_id": player_sid,
        "player_count": len(players),
        "player_token": _mint_player_token(player_sid, req.player_id, bypass_password),
    }


def _mint_player_token(player_sid: str, player_id: str, observer: bool) -> str:
    """F-22: best-effort token mint for the join paths (empty when JWT is unavailable)."""
    try:
        from auth_jwt import create_player_token
        return create_player_token(player_sid, player_id, observer=bool(observer))
    except Exception:
        return ""


@router.post("/public/sessions/{session_id}/join", summary="Join an active session")
async def join_session(session_id: str, req: JoinSessionRequest):
    """Public join endpoint. Thin wrapper: the password check is NEVER skippable
    from the wire.

    SEC-2026-08-02: this used to be the implementation itself, with a
    `_bypass_password: bool = False` parameter. FastAPI binds a non-path,
    non-Pydantic scalar with a default as a QUERY parameter (a leading
    underscore is not filtered), so `?_bypass_password=true` skipped the bcrypt
    check for anyone who knew a player id. The bypass now lives on a private
    keyword-only argument of `_join_session_impl`, which has no route and
    therefore no wire representation. Do NOT add parameters to this signature:
    anything added here becomes part of the public API surface.
    """
    return await _join_session_impl(session_id, req, bypass_password=False)


@router.get(
    "/public/join/{join_code}",
    summary="Resolve a short join code to session ID",
)
async def resolve_join_code_endpoint(join_code: str):
    """Resolve a 6-character join code to the full session UUID."""
    session_id = await db.resolve_join_code(join_code)
    if not session_id:
        raise HTTPException(status_code=404, detail=f"Join code '{join_code}' not found")
    return {"session_id": session_id, "join_code": join_code.upper()}


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/start
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new simulation session",
)
async def start_simulation(body: StartSessionRequest, request: Request):
    """
    Creates a new session (or resumes an existing one matching the cohort_name),
    seeds Round 1 from the baseline JSON, and returns the game state.
    """
    # ── C2 fix: authenticate cohort creation & pin ownership ──────────────
    # Previously this endpoint had NO auth guard and trusted the client-supplied
    # facilitator_id, so any anonymous caller could create cohorts or spoof a
    # real facilitator's id to exhaust their cohort quota / mis-attribute a
    # cohort. We now require an authenticated facilitator and resolve the owning
    # facilitator_id from the verified JWT identity — never from the raw body.
    #
    # Only registry-level admins (super_admin / god_mode / project_admin) may
    # create a cohort on behalf of ANOTHER facilitator (e.g. seeding a
    # newly-provisioned facilitator's first cohort). Any other role is pinned to
    # its own id; a body value naming a different facilitator is rejected so it
    # cannot be used to spoof or burn someone else's quota.
    #
    # Unauthenticated self-paced play is unaffected: it has its own dedicated
    # endpoint, /solo-start, which is intentionally ungated.
    from admin_router import get_fac_role
    from auth_jwt import get_facilitator_from_request

    caller_id = get_facilitator_from_request(request)
    caller_role = get_fac_role(request)
    if caller_role == "anonymous" or not caller_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Facilitator authentication required to create a cohort.",
        )

    _REGISTRY_ADMIN_ROLES = {"god_mode", "super_admin", "admin", "project_admin"}
    _requested_fac_id = (body.facilitator_id or "").strip()
    if (
        _requested_fac_id
        and _requested_fac_id != caller_id
        and caller_role not in _REGISTRY_ADMIN_ROLES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only create cohorts under your own facilitator id.",
        )
    # Trust the JWT identity for quota + ownership. An explicit target id is
    # honoured only for registry admins; everyone else is forced to their own.
    body.facilitator_id = (
        _requested_fac_id
        if (_requested_fac_id and caller_role in _REGISTRY_ADMIN_ROLES)
        else caller_id
    )

    try:
        # 1. Look for existing session to allow resuming mid-round decisions
        existing_state = await db.fetch_session_by_cohort(body.cohort_name)
        if existing_state:
            return StartSessionResponse(
                session_id=existing_state["session_id"],
                round_number=existing_state["round_number"],
                global_state=GlobalStateOut(**existing_state["global_state"]),
                business_units=[_bu_out(bu) for bu in existing_state["bu_states"]],
            )

        # 1b. RBAC-R2 (2026-08-01): the ONE server-side rule for who may create
        # a cohort. Deliberately placed AFTER the resume branch above — an
        # existing cohort must stay resumable by whoever already owns it; only
        # bringing a NEW cohort into existence is a privileged action. Until
        # now this endpoint enforced no role rule at all, so a base facilitator
        # could create a cohort through a direct API call that both UI surfaces
        # appeared to forbid. Both surfaces now render this same answer.
        from admin_shared import may_create_cohort
        _may_create, _deny_reason = may_create_cohort(caller_role)
        if not _may_create:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_deny_reason,
            )

        # 2. No session found, create a new one
        # I4 (Workstream D): inherit omitted provisioning values (climate branch
        # + single-BU scope) from the global default so a super_admin's
        # Switchboard setting seeds NEW cohorts. Explicit request values win;
        # existing cohorts are untouched.
        _raw_paradigm = getattr(body, 'decision_paradigm', None)
        _raw_sim_mode = getattr(body, 'simulation_mode', None)
        _raw_vertical = getattr(body, 'industry_vertical', None)
        try:
            from admin_shared import inherited_provisioning_defaults
            _raw_paradigm, _raw_sim_mode, _raw_vertical = inherited_provisioning_defaults(
                decision_paradigm=_raw_paradigm,
                simulation_mode=_raw_sim_mode,
                industry_vertical=_raw_vertical,
            )
        except Exception:
            pass  # Non-critical — fall back to per-field defaults below.

        # 2a. Validate decision paradigm before doing anything.
        # Set lives in config.VALID_DECISION_PARADIGMS so the bulk-upload
        # template's dropdown offers exactly what this check accepts.
        _req_paradigm = _raw_paradigm or 'legacy_abc'
        from config import VALID_DECISION_PARADIGMS as _VALID_PARADIGMS
        if _req_paradigm not in _VALID_PARADIGMS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid decision_paradigm '{_req_paradigm}'. Valid values: {sorted(_VALID_PARADIGMS)}"
            )

        # 2b. Check facilitator cohort limit
        if not await check_and_increment_cohort_count(body.facilitator_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Facilitator '{body.facilitator_id}' has reached the maximum cohort limit.",
            )

        # Resolve assigned_bu for single_bu mode.
        # Uses the module-level VERTICAL_SLOT_MAP to convert a substitute vertical
        # (e.g. 'oil_gas') to its owning seed slot ('pharma').
        _sim_mode = _raw_sim_mode or 'conglomerate'
        _industry_vertical = _raw_vertical
        # assigned_bu = the slot id (always one of the 4 seed BU ids); falls back to
        # the vertical itself for forward-compat when a new vertical is added before
        # the map is updated.
        _assigned_bu = (
            VERTICAL_SLOT_MAP.get(_industry_vertical, _industry_vertical)
            if _sim_mode == 'single_bu' and _industry_vertical
            else None
        )

        result = await db.create_session(
            body.cohort_name,
            body.facilitator_id,
            loan_interest_rate=body.loan_interest_rate,
            decision_paradigm=_req_paradigm,
            currency_symbol=getattr(body, 'currency_symbol', '$') or '$',
            scenario_preset=getattr(body, 'scenario_preset', None),
            experience_level=getattr(body, 'experience_level', None),
            difficulty_tier=getattr(body, 'difficulty_tier', None),
            created_by=getattr(body, 'created_by', None),
            created_when=getattr(body, 'created_when', None),
            start_date=getattr(body, 'start_date', None),
            end_date=getattr(body, 'end_date', None),
            simulation_mode=_sim_mode,
            industry_vertical=_industry_vertical,
            assigned_bu=_assigned_bu,
            region_id=getattr(body, 'region_id', None),
        )

        # 2b-ii. Persist the packs chosen at setup onto the session record —
        # the one place BOTH backends carry, and where the scope-hydration
        # helper reads them back for resolution during play. These ids were
        # previously discarded twice over: absent from StartSessionRequest
        # (Pydantic dropped them) and filtered out of the metadata PATCH's
        # EDITABLE set — the pack dropdowns were decorative end-to-end.
        _packs = {k: getattr(body, k) for k in ("stakeholder_pack_id", "materiality_pack_id")
                  if (getattr(body, k, None) or "").strip()}
        if _packs:
            try:
                await db.update_session_metadata(str(result["session_id"]), _packs)
            except Exception:
                pass  # cohort creation must not fail over pack bookkeeping

        # 2c. Persist decision_paradigm on the facilitator record
        #     so GET /facilitators always returns it (fixes paradigm disappearing on poll)
        try:
            from admin_shared import _facilitator_registry, _persist_facilitators
            fac_rec = next((f for f in _facilitator_registry if f["facilitator_id"] == body.facilitator_id), None)
            if fac_rec:
                fac_rec["decision_paradigm"] = _req_paradigm
                _persist_facilitators()
        except Exception:
            pass  # Non-critical

        # 3. Store allowed interventions natively for this session
        overrides = body.allowed_overrides or []
        swipes = body.allowed_swipes or []
        await set_session_interventions(str(result["session_id"]), SessionInterventionsRequest(
            allowed_overrides=overrides,
            allowed_swipes=swipes
        ))

        # 4. Apply ending pathway to the session's initial state
        _ending_pathway = getattr(body, 'ending_pathway', None)
        if _ending_pathway:
            try:
                # 'random' is stored UNRESOLVED on the cohort: it is intent,
                # not a pathway. Each player's join draws their own concrete
                # ending (see the inheritance block in join_session), so one
                # classroom sees several endings — the pedagogical point of
                # random. Named pathways still copy through verbatim. The
                # cohort session itself is never played to round 10, so a
                # literal 'random' on the cohort row is display-only
                # ("Random — resolved per player").
                # Write directly to the session's active_event_flags
                gs = result["global_state"]
                gs.setdefault("active_event_flags", {})["ending_pathway"] = _ending_pathway
                await db.update_latest_global_state(
                    str(result["session_id"]), gs, result["business_units"]
                )
                _log.info(f"[session-start] Ending pathway set to '{_ending_pathway}' for {result['session_id']}")
            except Exception as exc:
                _log.warning(f"[WARN] Failed to set ending pathway: {exc}")
        
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve),
        )
    except HTTPException:
        raise  # Re-raise 403 (cohort limit) etc. as-is
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {exc}",
        )

    return StartSessionResponse(
        session_id=str(result["session_id"]),
        round_number=1,
        global_state=GlobalStateOut(**result["global_state"]),
        business_units=[_bu_out(bu) for bu in result["business_units"]],
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/solo-start
# Creates a self-contained solo/demo session for self-paced study.
# Bypasses facilitator gating and auto-seeds all 10 round configs.
# ─────────────────────────────────────────────────────────────────

class SoloStartRequest(BaseModel):
    player_name: str = "Solo Player"
    decision_paradigm: str = "legacy_abc"
    currency_symbol: str = "$"

@router.post(
    "/solo-start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a self-contained solo/demo session (no facilitator required)",
)
async def solo_start_simulation(body: SoloStartRequest):
    """
    Creates a fully self-contained solo session for self-paced learners.

    Key differences from /start:
    - No facilitator_id required — bypasses all facilitator gating.
    - No cohort-count limit check.
    - All 10 rounds are pre-unlocked (free pacing).
    - Round options are auto-seeded so the Strategic Options panel is never empty.
    - Session is tagged is_solo=True and expires in 24 hours.
    """
    from datetime import date, timedelta

    # Solo mode is a PLATFORM switch a lead_facilitator / super_admin enables
    # per workshop (PATCH /api/admin/solo-mode). The login screen hides its
    # button when off, but this endpoint is public and unauthenticated, so the
    # server must refuse too — a hidden button is never the only line of
    # defence (V-B/V-C precedent). DEFAULT OFF (2026-08-01): an unconfigured
    # platform has NO solo access, and this fails CLOSED — an absent key or a
    # settings-store error both deny, because solo is now opt-in, not opt-out.
    try:
        from admin_shared import _god_mode_settings as _gms
        _solo_enabled = _gms.get("solo_mode_enabled", False) is True
    except Exception:
        _solo_enabled = False
    if not _solo_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo sessions are not enabled. Ask your lead facilitator or administrator to turn them on.",
        )

    _req_paradigm = (body.decision_paradigm or "legacy_abc").strip()
    # C5: derive from the canonical set instead of a drifting inline copy.
    # Solo mode additionally accepts un_sdg (solo-only experience); COHORT
    # creation does not, and the cohort form must offer only the config set.
    from config import VALID_DECISION_PARADIGMS as _CFG_PARADIGMS
    _VALID_PARADIGMS = set(_CFG_PARADIGMS) | {"un_sdg"}
    if _req_paradigm not in _VALID_PARADIGMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid decision_paradigm '{_req_paradigm}'. Valid: {sorted(_VALID_PARADIGMS)}",
        )

    # Use a unique name so duplicate-name guard doesn't block repeated solo starts
    import uuid as _uuid
    cohort_name = f"Solo — {body.player_name} ({_uuid.uuid4().hex[:6].upper()})"
    end_date_str = (date.today() + timedelta(days=1)).isoformat()

    try:
        result = await db.create_session(
            cohort_name=cohort_name,
            facilitator_id=None,          # No facilitator required
            loan_interest_rate=0.12,
            player_id=None,
            parent_cohort_id=None,
            decision_paradigm=_req_paradigm,
            currency_symbol=body.currency_symbol or "$",
            end_date=end_date_str,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create solo session: {exc}",
        )

    session_id = str(result["session_id"])

    # ── Tag session as solo + set free-play pacing (all rounds unlocked) ──
    # Fix #6: route session mutations through the db interface. Under Postgres
    # these land in the durable `metadata` JSONB column (and the mirror cache);
    # the old path wrote only to the database_memory dict + snapshot and was lost
    # on a Postgres restart. In memory mode the effect is identical.
    await db.update_session_metadata(session_id, {
        "is_solo": True,
        "pacing_mode": "free_play",
        "player_name": body.player_name,
    })
    sess = await db.get_session_info(session_id)

    # ── Pre-unlock all rounds for this solo session ──
    from admin_shared import _round_pacing, mark_pacing_dirty
    _round_pacing[session_id] = {
        "mode": "free",
        "unlocked_round": 999,
        "interval_seconds": 0,
        "next_unlock_at": None,
        "schedule": [],
        "_timer_tasks": [],
        "_timer_task": None,
        "set_by": None,
    }
    # Fix #5: publish the pacing policy so it survives a restart and is shared
    # across workers (no-op beyond a local snapshot in memory mode).
    mark_pacing_dirty(session_id)

    # ── Pre-seed round configs so the Strategic Options panel is never empty ──
    # We fetch all 10 rounds and store them on the session for the frontend
    # to retrieve via GET /api/simulations/{session_id}/solo-round-configs
    try:
        all_round_configs = {}
        # audit #15: single dispatch point instead of an inline if/elif chain.
        from paradigm_registry import round_config_for
        for rnum in range(1, 11):
            rcfg = round_config_for(_req_paradigm, rnum)
            if rcfg:
                # Apply option shuffle for solo sessions too
                _solo_options = rcfg.get("options", {})
                if sess and _req_paradigm in ("legacy_abc", "advanced_climate"):
                    _solo_seed = sess.get("shuffle_seed")
                    if _solo_seed:
                        _solo_options = shuffle_options_for_display(_solo_options, _solo_seed, rnum)
                        _solo_options = strip_canonical_metadata(_solo_options)
                all_round_configs[str(rnum)] = {
                    "round_number": rnum,
                    "title": rcfg.get("title"),
                    "theme": rcfg.get("theme"),
                    "crisis": rcfg.get("crisis"),
                    "options": _solo_options,
                    "special_rules": rcfg.get("special_rules", {}),
                    "paradigm": _req_paradigm,
                }
        if all_round_configs:
            await db.update_session_metadata(session_id, {"_solo_round_configs": all_round_configs})
    except Exception as rc_exc:
        _log.warning(f"[WARN] solo-start: failed to pre-seed round configs: {rc_exc}")

    _log.info(f"[solo-start] Created solo session {session_id} for '{body.player_name}' paradigm={_req_paradigm}")

    return StartSessionResponse(
        session_id=session_id,
        round_number=1,
        global_state=GlobalStateOut(**result["global_state"]),
        business_units=[_bu_out(bu) for bu in result["business_units"]],
    )


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/solo-round-configs
# Returns all pre-seeded round configs for a solo session
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/solo-round-configs",
    summary="Get all pre-seeded round configs for a solo session",
)
async def get_solo_round_configs(session_id: str, request: Request):
    """
    Returns all 10 rounds' option sets pre-seeded at solo session creation.
    Used by the player cockpit to populate DecisionModal without extra fetches.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    import database_memory as _dm
    sess = _dm._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if not sess.get("is_solo"):
        raise HTTPException(status_code=400, detail="Not a solo session")
    return {
        "session_id": session_id,
        "round_configs": sess.get("_solo_round_configs", {}),
        "is_solo": True,
    }



# Returns per-session metadata: currency_symbol, scenario_preset, paradigm
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/session-info", summary="Get session metadata (currency, preset, paradigm)")
async def get_session_info(session_id: str, request: Request):
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    session = await db.get_session_info(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If this is a player sub-session, also pull parent cohort's settings
    parent_id = session.get("parent_cohort_id")
    parent_currency = None
    parent_rate = None
    if parent_id:
        parent = await db.get_session_info(parent_id)
        if parent:
            parent_currency = parent.get("currency_symbol", "$")
            parent_rate = parent.get("currency_rate")

    # Read ending pathway from the session's latest state
    ending_pathway = "activist_ultimatum"
    try:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            ending_pathway = latest.get("global_state", {}).get(
                "active_event_flags", {}
            ).get("ending_pathway", "activist_ultimatum")
    except Exception:
        pass

    # MEDIUM-tier time & scheduling: effective cohort timezone (cohort-settings
    # layer) + the per-round decision timer (existing pedagogical toggles, which
    # live on the session/parent as pedagogical_overrides). Fail-open throughout.
    _time_eff = {}
    _timer_cfg = {}
    try:
        from admin_shared import get_effective_settings as _ges
        _time_eff = _ges(parent_id or session_id)
    except Exception:
        _time_eff = {}
    try:
        from pedagogical_engine import get_pedagogical_toggles as _gpt
        _ped_src = (parent if parent_id and parent else session) or {}
        _timer_cfg = _gpt(_ped_src.get("pedagogical_overrides") or {})
    except Exception:
        _timer_cfg = {}

    # Resolve simulation_mode, assigned_bu, and industry_vertical.
    # For player sub-sessions these fields live directly on the session;
    # for legacy sessions created before this fix, we apply a two-stage
    # fallback: (1) parent cohort metadata, (2) _player_registry entry.
    _sim_mode      = session.get("simulation_mode", "") or ""
    _assigned_bu   = session.get("assigned_bu", "") or ""
    _industry_vert = session.get("industry_vertical", "") or ""

    # Fallback 1 — parent cohort's fields (for sessions missing their own values)
    if parent_id and parent and not _sim_mode:
        _sim_mode      = parent.get("simulation_mode", "") or ""
        _industry_vert = parent.get("industry_vertical", "") or _industry_vert
    if parent_id and parent and not _assigned_bu:
        _assigned_bu = parent.get("assigned_bu", "") or ""

    # Fallback 2 — per-player registry entry (authoritative source for per-player BU
    # assignments; set by the facilitator during induction).  This covers both legacy
    # sub-sessions (created before assigned_bu was written at join time) and any future
    # cases where the registry entry is the only source of truth.
    #
    # The registry is also consulted for industry_vertical, and there it OUTRANKS
    # the cohort's value rather than merely filling a gap: in single-business mode
    # the cohort's vertical is the default for players who chose none, so a
    # sub-session inheriting the cohort's vertical (Fallback 1) would report the
    # wrong company for a player who has their own. Only the player's own value
    # can be right about which business this player runs.
    # NOTE on assigned_bu vs industry_vertical, because conflating them is easy
    # and the failure is silent: the SESSION's assigned_bu is the bu_id actually
    # present in bu_states, which for a substituted vertical IS the vertical id
    # (create_session sets it from filtered[0]["bu_id"]), not the seed slot. So a
    # session that already carries assigned_bu is authoritative and is never
    # overwritten here — recomputing it as a slot would make the cockpit address a
    # BU that does not exist in its own state.
    _player_id = session.get("player_id", "")
    if _player_id and (not _assigned_bu or _sim_mode == "single_bu"):
        try:
            from admin_shared import _player_registry as _reg
            _prec = next((p for p in _reg if p.get("player_id") == _player_id), None)
            if _prec:
                _prec_vertical = _prec.get("industry_vertical") or ""
                if _sim_mode == "single_bu" and _prec_vertical:
                    _industry_vert = _prec_vertical
                if not _assigned_bu:
                    # Prefer the player's own vertical over their stored slot: the
                    # vertical is what create_session would have scoped them to.
                    _assigned_bu = (_prec_vertical if _sim_mode == "single_bu" and _prec_vertical
                                    else (_prec.get("assigned_bu", "") or ""))
        except Exception:
            pass

    # Fallback 3 — single_bu mode: industry_vertical IS the BU.
    # If simulation_mode is 'single_bu' but assigned_bu is still unresolved
    # (e.g. cohort was created before the per-session assigned_bu write was added,
    # or the player has no per-player BU entry), derive assigned_bu from the
    # cohort's industry_vertical so the player session always scopes to 1 BU.
    if not _assigned_bu and _sim_mode == "single_bu" and _industry_vert:
        _assigned_bu = VERTICAL_SLOT_MAP.get(_industry_vert, _industry_vert)

    return {
        "session_id": session_id,
        "cohort_name": session.get("cohort_name"),
        "decision_paradigm": session.get("decision_paradigm", "legacy_abc"),
        "currency_symbol": session.get("currency_symbol") or parent_currency or "$",
        "parent_currency_symbol": parent_currency,
        # THE CONVERSION FACTOR, alongside the glyph it belongs to.
        #
        # Before this, a rupee cohort read "Rs 11.0M" for an engine value of
        # 11,000,000 dollars: the symbol was localised and the quantity was
        # not. The frontend applies this once, at the format boundary.
        #
        # NOT applied server-side, and that is the important part. config.py's
        # constants, the covenant thresholds and every tuned ratio are
        # expressed in engine units; multiplying before the engine would
        # silently redefine all of them. This converts PRESENTATION only.
        #
        # Absent reads as None rather than 1.0 so the client can tell "no rate
        # configured" from "a rate of exactly one" - the first should leave the
        # previous value alone, the second is a deliberate reset.
        "currency_rate": session.get("currency_rate") or parent_rate,
        "parent_currency_rate": parent_rate,
        "scenario_preset": session.get("scenario_preset"),
        "experience_level": session.get("experience_level"),
        "difficulty_tier": session.get("difficulty_tier", "advanced"),
        "parent_cohort_id": parent_id,
        "ending_pathway": ending_pathway,
        "pacing_mode": (parent.get("pacing_mode", "free_play") if parent_id and parent else session.get("pacing_mode", "free_play")),
        "simulation_mode":   _sim_mode   or None,
        "assigned_bu":       _assigned_bu or None,
        "industry_vertical": _industry_vert or None,
        # MEDIUM-tier time & scheduling: cohort-local timezone + the effective
        # per-round decision timer (existing pedagogical toggles, surfaced here
        # so the cockpit can render a countdown without an extra fetch).
        "cohort_timezone":        _time_eff.get("cohort_timezone", "") or None,
        "decision_timer_enabled": bool(_timer_cfg.get("decision_timer_enabled", False)),
        "decision_timer_seconds": int(_timer_cfg.get("decision_timer_seconds", 300) or 300),
        # LOW-tier polish: cohort accessibility defaults + white-label branding,
        # so the cockpit can apply both without an extra fetch. All fail-open.
        "accessibility_defaults": _time_eff.get("accessibility_defaults") or {},
        "branding": {
            "institution":   _time_eff.get("branding_institution", "") or None,
            "logo_url":      _time_eff.get("branding_logo_url", "") or None,
            "primary_color": _time_eff.get("branding_primary_color", "") or None,
        },
        "consent_required": bool(_time_eff.get("consent_required", False)),
        "consent_text":     _time_eff.get("consent_text", "") or None,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/export-my-data  (LOW-tier compliance)
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/export-my-data",
    summary="Export this session's data (privacy/compliance)",
)
async def export_my_data(session_id: str, request: Request):
    """Player-facing data export: everything the platform holds about THIS
    session — metadata, per-round states, and this session's decision entries —
    as one JSON document the player can download and keep. SEC-3 bound: only
    the session owner (or a facilitator) can export it."""
    await _assert_player_owns_session(request, session_id)
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    # Session metadata, minus server-internal / credential fields.
    _EXCLUDE = {"password", "bump_token_version", "_solo_round_configs",
                "registered_players", "allowed_player_ids"}
    meta = {k: v for k, v in sess.items() if k not in _EXCLUDE and not k.startswith("_")}

    try:
        # SEAM-08: the closing state rides along as round 11 / is_final so a
        # finished run exports what it ended on, not only what it entered R10 with.
        history = await db.fetch_round_history(session_id, include_final=True)
    except Exception:
        history = []

    from datetime import datetime as _dt, timezone as _tz
    return {
        "export_version": 1,
        "generated_at": _dt.now(_tz.utc).isoformat(),
        "session_id": session_id,
        "session": meta,
        "round_history": history,
        "consent_given_at": sess.get("consent_given_at"),
        "note": "This export contains all simulation data stored for this session.",
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/final-report
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/final-report",
    summary="Get final game report with terminal valuation",
)
async def get_final_report(session_id: str, request: Request):
    """Aggregated final report: terminal valuation, M_R, archetype, ending pathway."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    gs = latest["global_state"]
    # BUGFIX: fetch_latest_state exposes round_number at the top level (as the
    # dashboard uses); the rebuilt global_state sub-dict does not carry it, so
    # gs.get("round_number") always returned 1 and the final report 400ed at
    # the end of every completed game.
    rn = latest.get("round_number", gs.get("round_number", 1))
    flags = gs.get("active_event_flags", {})
    if rn < 10 and not gs.get("game_over"):
        raise HTTPException(status_code=400, detail=f"Game not finished — currently at round {rn}")
    # P2: attach the score-based Turnaround offer (module flag + completion +
    # M_R threshold). Per-facilitator authorisation is applied by the admin
    # eligibility endpoint, not here (this endpoint has no role context).
    from admin_shared import _god_mode_settings as _gms
    from engine import turnaround_offer_for
    _turnaround_offer = turnaround_offer_for(gs, _gms.get("turnaround_module_enabled", False))

    # ── MEDIUM-tier report-access control (server-side, not just UI) ────────
    # "full" (default) = legacy behaviour; "summary" withholds the narrative
    # report bodies but keeps headline numbers; "facilitator_only" returns a
    # locked notice — facilitators still see everything via admin surfaces.
    _report_access = "full"
    try:
        from admin_shared import get_effective_settings as _ges
        _sess_info = await db.get_session_info(session_id)
        _scope_sid = (_sess_info or {}).get("parent_cohort_id") or session_id
        _report_access = _ges(_scope_sid).get("report_access", "full")
    except Exception:
        _report_access = "full"

    if _report_access == "facilitator_only":
        return {
            "session_id": session_id,
            "round_number": rn,
            "locked": True,
            "report_access": "facilitator_only",
            "message": "Your facilitator will share the final report during the debrief.",
            "game_over": gs.get("game_over", False),
        }

    # Per-player quiz score log for the results / archetype card. Scores are a
    # performance metric (not narrative), so they survive the "summary" access
    # tier like the other headline numbers.
    try:
        from quiz_gate import build_quiz_score_log
        _quiz_log = build_quiz_score_log(gs)
    except Exception:
        _quiz_log = None

    _withhold_narrative = (_report_access == "summary")
    return {
        "session_id": session_id,
        "round_number": rn,
        "report_access": _report_access,
        "final_report_canonical": None if _withhold_narrative else gs.get("final_report_canonical"),
        "turnaround_amended_report": None if _withhold_narrative else gs.get("turnaround_amended_report"),
        "turnaround_offer": _turnaround_offer,
        "terminal_valuation": gs.get("terminal_valuation"),
        "regenerative_multiple": gs.get("regenerative_multiple"),
        "archetype": gs.get("archetype"),
        "ending_pathway": flags.get("ending_pathway", "activist_ultimatum"),
        "corporate_treasury": gs.get("corporate_treasury"),
        "group_reputation": gs.get("group_reputation"),
        "synergy_multiplier": gs.get("synergy_multiplier"),
        "consequence_dna_snapshot": flags.get("consequence_dna_snapshot"),
        "quiz_score_log": _quiz_log,
        "game_over": gs.get("game_over", False),
        "game_over_reason": gs.get("game_over_reason"),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/dashboard
# ─────────────────────────────────────────────────────────────────

def _choices_by_game_round(history_raw: list[dict]) -> dict:
    """Map game-round -> primary strategic option (e.g. 'option_a').

    A history row K is the state ENTERING round K (the result of the round-(K-1)
    commit); the decisions attached to it are the ones MADE in round K — both
    stores file a commit's decisions under the round it was made in
    (insert_next_round, AUDIT-1 2026-08-02; round 10 files explicitly at
    current_round). So a decision tagged K belongs to game-round K. This
    function read `tag - 1`, the pre-AUDIT-1 offset, and every dashboard
    history item carried the NEXT round's choice (audit F-02). The per-round
    rN_choice event flags are game-round indexed and fill rounds the log
    misses; the decision log wins when both exist.
    """
    out: dict = {}
    for h in history_raw:
        tag = h.get("round_number", 0)
        for dec in (h.get("decisions") or []):
            ch = dec.get("choice_selected") or ""
            if isinstance(ch, str) and ch.startswith("option_"):
                out[tag] = ch  # decision tagged `tag` == game-round tag
                break
        flags = (h.get("global_state", {}) or {}).get("active_event_flags", {}) or {}
        for k, v in flags.items():
            if isinstance(k, str) and k.endswith("_choice") and isinstance(v, str) and v.startswith("option_"):
                try:
                    gr = int(k[1:k.index("_choice")])
                except (ValueError, IndexError):
                    continue
                out.setdefault(gr, v)
    return out


@router.get(
    "/{session_id}/dashboard",
    response_model=DashboardResponse,
    summary="Retrieve the current dashboard state",
)
async def get_dashboard(session_id: str, request: Request, since_round: int | None = None):
    """
    Returns the latest round state plus history for the session.

    PER-1: pass ?since_round=N to return only history rounds >= N
    (default: full history, unchanged).
    """
    # SEC-3: bind the caller to the session. Consistent with save_decisions
    # and the other player routes (MED-003-008): when an X-Player-Id header is
    # present it must match the session owner, else 403. Facilitators/observers
    # (JWT auth, no X-Player-Id) are unaffected, and clients that omit the
    # header keep the UUID-as-bearer behaviour.
    # TEAM-1: allow_observer=True — a team's watchers (MUR-004-VIEW) read the
    # SAME board as their driver. This is the ONLY player route opened to them;
    # every other route stays driver-only by default (fail-closed).
    await _assert_player_owns_session(request, session_id, allow_observer=True)

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # PER-1 / F-27: optional bound on the history payload. Default (None)
    # returns the full history, so existing clients are unaffected; the cockpit
    # poller passes ?since_round=<highest round it holds> and receives only the
    # newest round(s) — the filter now runs in the store (SQL), not here.
    history_raw = await db.fetch_round_history(session_id, since_round=since_round)

    _choice_by_round = _choices_by_game_round(history_raw)
    history = [
        RoundSnapshot(
            round_number=h["round_number"],
            global_state=GlobalStateOut(**_slim_history_global_state(h["global_state"])),
            business_units=[_bu_out(bu) for bu in h["business_units"]],
            choice_selected=_choice_by_round.get(h["round_number"], ""),
        )
        for h in history_raw
    ]

    # MP-01 live refresh: recompute the multiplayer 'X/Y teams committed' badge
    # on every read so all teams see it update as others commit (cohort sub-sessions
    # only; solo sessions short-circuit in the helper and pay nothing).
    _si = await db.get_session_info(session_id)
    # F-27: one batched sibling scan feeds both the commit badge and the
    # free-advance status (was 2 × one query per sibling, on every poll).
    _sib_rounds = None
    _sibs = None
    if (_si or {}).get("parent_cohort_id"):
        _sibs, _sib_rounds = await _cohort_sibling_rounds(_si["parent_cohort_id"])
    _committed, _teams = await _cohort_commit_progress(_si, rounds=_sib_rounds, siblings=_sibs)
    if _teams is not None:
        latest["global_state"]["team_commits_this_round"] = _committed
        latest["global_state"]["cohort_team_count"] = _teams
        # Free-advance auto-release: surface the deadline + release flag, and
        # enforce the timeout (auto-commit stragglers) when it lapses. No-op
        # unless the facilitator set a positive free_advance_timeout_seconds
        # (or pressed Force Advance).
        try:
            _adv = await _cohort_advance_status(_si, _committed, _teams, rounds=_sib_rounds)
            if _adv is not None:
                latest["global_state"]["cohort_advance_deadline"] = _adv.get("deadline_at")
                latest["global_state"]["cohort_advance_unblocked"] = _adv.get("unblocked", False)
                if _adv.get("committed") is not None:
                    latest["global_state"]["team_commits_this_round"] = _adv["committed"]
        except Exception as _exc:
            _log.warning(f"[FREE-ADVANCE] status/enforce failed: {_exc}")
        # FACILITATOR-PACED ADVANCE: tell the cockpit whether the CURRENT round
        # is commit-locked by the cohort's pacing, and when it opens — so the
        # player sees "round opens at …" instead of a raw 403 at commit time.
        try:
            from admin_shared import _get_pacing as _gp, is_round_unlocked as _iru
            _pace_parent = (_si or {}).get("parent_cohort_id") or session_id
            _pp = _gp(_pace_parent)
            latest["global_state"]["cohort_pacing_mode"] = _pp.get("mode", "free")
            latest["global_state"]["cohort_round_locked"] = not _iru(_pace_parent, latest["round_number"])
            latest["global_state"]["cohort_next_unlock_at"] = _pp.get("next_unlock_at")
        except Exception:
            pass

    # MANDATORY-QUIZ GATE: surface whether this round's quiz must be taken before
    # the player can commit. Runs for ALL player sessions (solo + cohort); the
    # resolver fails open, so it can never wedge a round. The cockpit reads
    # global_state.quiz_gate exactly like cohort_round_locked.
    try:
        from quiz_gate import quiz_gate_status
        _qparent = (_si or {}).get("parent_cohort_id")
        latest["global_state"]["quiz_gate"] = quiz_gate_status(
            session_id, latest["round_number"], latest["global_state"], _qparent
        )
    except Exception:
        pass

    return DashboardResponse(
        session_id=session_id,
        current_round=latest["round_number"],
        global_state=GlobalStateOut(**_slim_latest_global_state(latest["global_state"])),
        business_units=[_bu_out(bu) for bu in latest["bu_states"]],
        history=history,
    )


# F-27: keys of active_event_flags that are engine-internal state, not
# something the cockpit renders. `_prev_global_states` is the momentum window
# (a rolling copy of previous global states — ~25 KB by R10) and
# `consequence_dna_snapshot` (~19 KB) is served by its own endpoint and is
# read by the Balanced Scorecard from the LATEST state only. Stripping them
# from the response never touches what is persisted; the store dicts are not
# mutated (new dicts are built).
_DASHBOARD_FLAGS_STRIP_ALWAYS = frozenset({"_prev_global_states"})
_DASHBOARD_FLAGS_STRIP_HISTORY = _DASHBOARD_FLAGS_STRIP_ALWAYS | frozenset({"consequence_dna_snapshot"})


def _slim_flags(gs: dict, strip: frozenset) -> dict:
    flags = gs.get("active_event_flags")
    if not isinstance(flags, dict) or not any(k in flags for k in strip):
        return gs
    out = dict(gs)
    out["active_event_flags"] = {k: v for k, v in flags.items() if k not in strip}
    return out


def _slim_latest_global_state(gs: dict) -> dict:
    return _slim_flags(gs, _DASHBOARD_FLAGS_STRIP_ALWAYS)


def _slim_history_global_state(gs: dict) -> dict:
    return _slim_flags(gs, _DASHBOARD_FLAGS_STRIP_HISTORY)


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/commit-turn
# ─────────────────────────────────────────────────────────────────

# Session-level configuration stamped on active_event_flags at creation
# (database_memory.create_session / database.create_session) and read back by
# post-tick engines. Forwarded into the post-tick state by
# _forward_persistent_flags — see the F-04 note in commit_turn.
_PERSISTENT_FLAG_KEYS = (
    "stochastic_seed",       # rng_util.ensure_cohort_seed — every seeded draw
    "loan_interest_rate",    # balance_sheet revolver pricing
    "ending_pathway",        # balance_sheet stranded-asset exposure; finale
    "difficulty_tier",       # round_logic covenant ratio (get_difficulty_config)
    "industry_vertical",     # stakeholder_map resolution
    "region_id",
)


def _forward_persistent_flags(current_global: dict, new_global: dict) -> None:
    """Copy the session-level keys from the STORED flags into the post-tick
    state's flags without overriding anything the tick just produced."""
    stored = current_global.get("active_event_flags") or {}
    target = new_global.setdefault("active_event_flags", {})
    for key in _PERSISTENT_FLAG_KEYS:
        value = stored.get(key)
        if value not in (None, "") and key not in target:
            target[key] = value


@router.post(
    "/{session_id}/commit-turn",
    response_model=CommitTurnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Commit decisions and advance to the next round",
)
async def commit_turn(session_id: str, body: CommitTurnRequest, request: Request):
    """Lock-safe wrapper: serializes commits per session in-process (asyncio)
    AND cross-process (Postgres advisory lock), then delegates and guarantees
    both locks are released on every exit path."""
    # SEC-3: bind the caller to the session before doing any work (and before
    # taking any lock), so a party holding only the session UUID cannot advance
    # another team's round. Enforced when X-Player-Id is present; facilitators
    # (JWT, no header) and header-less clients are unaffected.
    await _assert_player_owns_session(request, session_id)

    # CON-2: in-process deterministic fast-fail. asyncio.Lock has no
    # try-acquire, but acquire() on a FREE lock completes without yielding to
    # the event loop, so the locked()-check and acquire() below run atomically
    # with respect to other coroutines in this worker. A concurrent commit for
    # the same session therefore gets a deterministic 409 here instead of
    # silently queueing behind the in-flight one.
    commit_lock = _get_commit_lock(session_id)
    if commit_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another commit is in progress for this session. Please wait.",
        )
    await commit_lock.acquire()

    # CON-1: cross-process serialization. The asyncio lock only covers THIS
    # worker; with >1 uvicorn worker/instance two commits for the same session
    # can land on different workers and both proceed. A Postgres
    # try-advisory-lock (SEC-5) supplies the missing mutual exclusion and also
    # closes the round-10 lost-update window (the R10 in-place update path has
    # no uq_session_round guard). In single-process / in-memory mode this is a
    # no-op sentinel, so classroom/offline runs are unaffected.
    advisory = None
    gate = None
    try:
        # F-26: wait for a commit slot BEFORE taking the advisory connection, so
        # the number of connections pinned by in-flight commits is bounded and
        # every admitted commit can always obtain the second connection its
        # queries need. Excess commits queue in arrival order (503 only after
        # COMMIT_QUEUE_TIMEOUT_SECONDS); the per-session lock above still makes
        # a second commit for the SAME team fail fast with 409.
        gate = await _enter_commit_gate()
        advisory = await db.acquire_advisory_lock(session_id)
        if advisory is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another commit is in progress for this session (cross-process). Please wait.",
            )
        _commit_result = await _commit_turn_impl(session_id, body, commit_lock)
        # LOW-tier webhooks: notify the cohort's configured endpoint that a round
        # was committed (and whether the game just ended). Fire-and-forget —
        # scheduling can never raise or delay the player's response.
        try:
            from webhook_util import fire_webhook
            _sess_meta = await db.get_session_info(session_id)
            _parent_cid = (_sess_meta or {}).get("parent_cohort_id")
            _new_rn = getattr(_commit_result, "new_round_number", None)
            # The run is R1–R10; reaching R10 is the finale (the R10 commit is an
            # in-place update, so new_round_number never exceeds 10).
            _game_over = bool(_new_rn is not None and _new_rn >= 10)
            fire_webhook(
                "game_over" if _game_over else "round_committed",
                session_id, _parent_cid,
                payload={"round_number": _new_rn, "game_over": _game_over},
            )
        except Exception:
            pass
        return _commit_result
    finally:
        # CON-1: always hand the advisory lock / pooled connection back.
        if advisory is not None:
            await db.release_advisory_lock(advisory, session_id)
        if gate is not None:
            gate.release()  # F-26
        # FIX-RC-002: Guarantee in-process lock release on ANY exit path.
        # (_commit_turn_impl releases it early on some short-circuits; the
        # locked() guard makes a second release here a harmless no-op.)
        if commit_lock.locked():
            commit_lock.release()


async def _commit_turn_impl(session_id: str, body: CommitTurnRequest, commit_lock):
    """
    Core commit-turn implementation.
    1. Fetches the current round state.
    2. Validates the round is not past simulation cap.
    3. Runs pre-tick hooks (validation, crisis overrides).
    4. Runs the mathematical engine (process_tick).
    5. Runs post-tick hooks (round-specific state mutations).
    6. Persists the new immutable state and audit log.
    7. Returns the next-round state.
    """
    # ── ITEM 4: Per-session rate limiting (5s cooldown) ───────
    import time as _time
    now = _time.time()
    last_commit = _commit_timestamps.get(session_id, 0)
    if now - last_commit < 5.0:
        commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limited. Wait 5 seconds between commits.",
        )
    _commit_timestamps[session_id] = now
    _prune_commit_maps(now)

    # ── Emergency Freeze guard ───────────────────────────────
    # 2026-09-03: this read `_god_mode_settings["system_frozen"]` — the
    # PROCESS-GLOBAL dict — even though `system_frozen` is in
    # COHORT_OVERRIDABLE_KEYS and admin_router explicitly grants a
    # lead_facilitator write access to it for cohorts they own. So a
    # facilitator freezing their own cohort for a discussion got a 200, saw it
    # applied on the settings screen, and their class kept committing; while a
    # super-admin freeze stopped all thirty classes at once. This was the only
    # enforcement point for the flag.
    #
    # EITHER freeze applies. A cohort override must be able to stop its own
    # class, but it must NOT be able to escape a platform-wide maintenance
    # freeze — so this is OR, not "the override wins". get_effective_settings
    # walks a player sub-session up to its parent cohort, which is required
    # here because `session_id` is the player's, not the cohort's.
    from admin_shared import _god_mode_settings as _gms, get_effective_settings as _eff
    _global_frozen = bool(_gms.get("system_frozen", False))
    _cohort_settings_now = _eff(session_id)
    _cohort_frozen = bool(_cohort_settings_now.get("system_frozen", False))
    if _global_frozen or _cohort_frozen:
        commit_lock.release()
        _scope = "System is currently frozen for maintenance" if _global_frozen \
            else "This cohort is currently paused by your facilitator"
        _msg = _cohort_settings_now.get("freeze_message") or ""
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(f"{_scope}. Please wait for your facilitator to resume."
                    + (f" — {_msg}" if _msg else "")),
        )

    # ── Fetch current state ──────────────────────────────────
    current = await db.fetch_latest_state(session_id)
    if current is None:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # ── Cohort end-date lockout ──────────────────────────────
    session_meta = await db.get_session_info(session_id)
    if session_meta:
        end_date_str = session_meta.get("end_date")
        if end_date_str:
            from datetime import date
            try:
                cohort_end = date.fromisoformat(end_date_str)
                if date.today() > cohort_end:
                    if commit_lock.locked(): commit_lock.release()
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"This cohort expired on {end_date_str}. The game is locked and no further rounds can be played.",
                    )
            except ValueError:
                pass  # Malformed date — skip check

    current_round = current["round_number"]
    if current_round > 10:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already completed all 10 rounds.",
        )

    # ── R10-1 (2026-08-02): the finale is committed EXACTLY once ─────────────
    # Round 10 persists in place via update_latest_global_state (there is no
    # round 11 to insert), so the uq_session_round constraint that makes rounds
    # 1-9 idempotent does not exist here — and fetch_latest_state keeps
    # returning round_number == 10, so the "> 10" gate above never trips. A
    # second POST five seconds later therefore re-ran process_tick over
    # already-resolved terminal state and COMPOUNDED treasury, emissions and
    # terminal valuation. The normal finale now sets game_over (see the R10
    # persist branch below) and this gate refuses anything after it.
    #
    # The turnaround arc is unaffected: it commits through its own endpoint
    # rather than this one. (Extended Horizon, which used to clear game_over
    # here, was removed — F-32.)
    if (current.get("global_state") or {}).get("game_over"):
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This simulation has already completed. Its final results are "
                "locked — reload to see the Year-5 report."
            ),
        )

    # ── ITEM 1: Optimistic locking — expected_round guard ────
    # Enforced whenever the client sends it. Deliberately still optional in the
    # model: making it mandatory would 422 any browser tab running a cached
    # bundle, which is a run-day failure mode, and the double-advance this
    # guards against originates in the CLIENT's 429 retry loop — so shipping
    # useSimulation.js's expected_round is what actually closes it. Set
    # REQUIRE_EXPECTED_ROUND=true once the warning below stops appearing.
    expected_round = getattr(body, 'expected_round', None)
    if expected_round is None:
        if _os.getenv("REQUIRE_EXPECTED_ROUND", "").strip().lower() in ("true", "1", "yes"):
            if commit_lock.locked(): commit_lock.release()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expected_round is required. Refresh the page to load the current client.",
            )
        _log.warning(
            "[COMMIT] session=%s round=%s committed WITHOUT expected_round — a stale "
            "client that cannot be protected from the retry double-advance.",
            session_id, current_round,
        )
    elif expected_round != current_round:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_round",
                "expected": expected_round,
                "current": current_round,
                "message": (
                    f"This round has already been committed (you are on round "
                    f"{current_round}). Your decisions were saved — nothing was lost."
                ),
            },
        )

    # ── ITEM 5: Cohort pace lock — max_round enforcement ─────
    session_info_for_pace = await db.get_session_info(session_id)
    parent_id_for_pace = (session_info_for_pace or {}).get("parent_cohort_id")
    pace_session_id = parent_id_for_pace or session_id
    pace_session = await db.get_session_info(pace_session_id)
    max_round = (pace_session or {}).get("max_round")
    if max_round is not None and current_round > max_round:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cohort pace lock: maximum round is {max_round}. Wait for facilitator.",
        )

    # ── Round pacing gate ────────────────────────────────────
    # FACILITATOR-PACED ADVANCE: the gate is evaluated against the PARENT
    # cohort's pacing (pace_session_id), not the player sub-session — the
    # facilitator sets pacing on the cohort, so checking the child (which always
    # has a fresh default "free" policy) silently disabled manual/timed pacing
    # for cohort players. With the parent scope, players commit any unlocked
    # round whenever they're ready (values saved as usual) and the NEXT round
    # opens only when the facilitator's timer fires or they advance it manually.
    from admin_shared import is_round_unlocked
    if not is_round_unlocked(pace_session_id, current_round):
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Round {current_round} is locked. It opens when the facilitator's timer fires or they advance the round.",
        )

    # ── Free-mode barrier, server side (F-18(ii), audit 2026-09-04) ─────
    # In free mode the cohort advances together: the cockpit shows "Waiting
    # for Other Teams" after a commit until every team has committed the
    # round (or the auto-advance timeout lapses / the facilitator forces).
    # That barrier lived in React state only — a reload skipped it and the
    # server accepted round N+1 from a team while a sibling was still on
    # round N. Now the same status the dashboard computes
    # (_cohort_advance_status: timeout, force flag, laggard auto-commit) is
    # consulted here, and a team AHEAD of the slowest sibling is refused
    # with the barrier's own copy while it is not released. A team that is
    # behind (catching up) is never blocked by this.
    if parent_id_for_pace:
        try:
            from admin_shared import _get_pacing as _gp_fa
            _fa_pacing = _gp_fa(parent_id_for_pace)
            if _fa_pacing.get("mode") == "free":
                _fa_sibs, _fa_rounds = await _cohort_sibling_rounds(parent_id_for_pace)
                if _fa_rounds and len(_fa_rounds) > 1 and current_round > min(_fa_rounds):
                    _fa_status = await _cohort_advance_status(session_info_for_pace, rounds=_fa_rounds)
                    if _fa_status is not None and not _fa_status.get("unblocked"):
                        _fa_rounds_after = (await _cohort_sibling_rounds(parent_id_for_pace))[1] or _fa_rounds
                        if current_round > min(_fa_rounds_after):
                            if commit_lock.locked(): commit_lock.release()
                            _behind = sum(1 for r in _fa_rounds_after if r < current_round)
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail={
                                    "code": "waiting_for_teams",
                                    "message": (
                                        f"Waiting for other teams — {_behind} team(s) have not committed round "
                                        f"{current_round - 1} yet. Round {current_round} opens when every team has "
                                        f"committed, when the auto-advance timeout lapses, or when the facilitator advances."
                                    ),
                                    "committed": _fa_status.get("committed"),
                                    "teams": _fa_status.get("teams"),
                                    "deadline_at": _fa_status.get("deadline_at"),
                                },
                            )
        except HTTPException:
            raise
        except Exception as _fa_exc:  # never let the barrier itself break a commit
            _log.warning(f"[FREE-ADVANCE] barrier check failed for {session_id}: {_fa_exc}")

    # ── Mandatory-quiz gate (server-side enforcement) ────────
    # When the cohort marks quizzes mandatory, a round that carries a quiz
    # notebook cannot be committed until the player has taken that round's quiz.
    # The frontend blocks the button too, but this is the authoritative check so
    # a direct POST can't bypass it. Fails OPEN on any resolver error.
    try:
        from quiz_gate import quiz_gate_status
        _qg = quiz_gate_status(session_id, current_round, current["global_state"], parent_id_for_pace)
    except Exception:
        _qg = {"blocked": False}
    if _qg.get("blocked"):
        if commit_lock.locked(): commit_lock.release()
        _qt = _qg.get("required_title") or "this round's quiz"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This cohort requires you to complete {_qt} before committing your decisions for round {current_round}.",
        )

    # ── Side track blocking gate ─────────────────────────────
    blocking_tid, blocking_st = await _get_active_side_track_for_session(session_id)
    if blocking_tid and blocking_st and not blocking_st.get("completed"):
        from side_tracks import get_track as _st_get
        _st_obj = _st_get(blocking_tid)
        _st_name = _st_obj.display_name if _st_obj else blocking_tid
        commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Side track '{_st_name}' is active and must be completed before advancing. Open the Side Tracks panel to continue.",
        )

    # ── Build engine inputs ──────────────────────────────────
    current_global = {
        "round_number": current_round,
        **current["global_state"],
    }
    current_bus = current["bu_states"]
    decisions_raw = [d.model_dump() for d in body.decisions]

    # A negotiation room never outlives the round it was opened in: if the
    # player committed without walking out, auto-close it here so the record
    # resolves (resolution="round_committed") instead of leaking open into the
    # next round. Concessions accepted this meeting were already applied and
    # persisted by /negotiation/accept; this only closes the open room, and it
    # travels through the tick via the active_event_flags "preserve history"
    # merge below. No-op when no room is open.
    try:
        import negotiation as _negotiation
        _negotiation.close_on_commit(current_global, current_round)
    except Exception as _neg_close_exc:
        _log.error("negotiation.close_on_commit failed for %s R%s: %s",
                   session_id, current_round, _neg_close_exc, exc_info=True)

    # ── Determine decision paradigm (fall back to parent cohort) ──
    session_info = await db.get_session_info(session_id)
    paradigm = (session_info or {}).get("decision_paradigm", "legacy_abc")
    if paradigm == "legacy_abc" and session_info and session_info.get("parent_cohort_id"):
        parent_info = await db.get_session_info(session_info["parent_cohort_id"])
        if parent_info:
            paradigm = parent_info.get("decision_paradigm", "legacy_abc")

    # ── Pillar-mode: aggregate multi-toggle decisions ─────────
    pillar_aggregation = None
    if paradigm == "multi_toggles":
        # Extract pillar_decisions from the first decision that has them
        pillar_choices = None
        for d in decisions_raw:
            if d.get("pillar_decisions"):
                pillar_choices = d["pillar_decisions"]
                break

        if pillar_choices:
            pillar_aggregation = aggregate_pillar_decisions(current_round, pillar_choices)

            # Translate to legacy choice for round_logic compatibility
            legacy_choice = translate_pillars_to_legacy_choice(current_round, pillar_choices)
            for d in decisions_raw:
                d["choice_selected"] = legacy_choice
        else:
            # Fallback: no pillar_decisions provided, treat as legacy
            paradigm = "legacy_abc"

    # ── ANTI-GAMING: Deshuffle displayed choice → canonical key ──
    # The frontend sends back option_a/b/c based on the shuffled
    # display order. We reverse-map to the real canonical key here
    # so all downstream logic (engine, round_logic, flags) is unaffected.
    _shuffle_seed = (session_info or {}).get("shuffle_seed")
    if _shuffle_seed and paradigm == "legacy_abc":
        for d in decisions_raw:
            raw_choice = d.get("choice_selected", "")
            if raw_choice:
                d["choice_selected"] = deshuffle_choice(raw_choice, _shuffle_seed, current_round)

    # ── FIX VULN-005/008/009: Input validation ────────────────
    valid_choices = {"option_a", "option_b", "option_c", ""}
    valid_bu_ids = {bu["bu_id"] for bu in current_bus}
    submitted_bu_ids = [d["bu_id"] for d in decisions_raw]

    # VULN-005: Reject duplicate BU IDs
    if len(submitted_bu_ids) != len(set(submitted_bu_ids)):
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate BU IDs in decisions. Each BU must appear exactly once.",
        )

    # VULN-009: Require decisions for all active BUs
    missing = valid_bu_ids - set(submitted_bu_ids)
    if missing:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing decisions for BU(s): {', '.join(sorted(missing))}.",
        )

    # audit #4: Reject UNKNOWN/foreign BU IDs. The "missing" check above ensures
    # every real BU is present; this complements it so a decision for a BU that
    # does not belong to this session cannot slip through to the engine.
    unknown = set(submitted_bu_ids) - valid_bu_ids
    if unknown:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown BU ID(s): {', '.join(sorted(unknown))}.",
        )

    # VULN-008: Validate choice_selected (only for legacy_abc paradigm)
    if paradigm == "legacy_abc":
        for d in decisions_raw:
            choice = d.get("choice_selected", "")
            if choice and choice not in valid_choices:
                if commit_lock.locked(): commit_lock.release()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid choice_selected '{choice}'. Must be option_a, option_b, or option_c.",
                )
        # F-35 (launch audit 2026-09-01): a submission with NO strategic option
        # used to be accepted and silently scored as Option B (the R1 ledger
        # showed a −$3M "Deep Forensic Audit" for a choice of ""). A commit
        # must say which option the team chose.
        if not any((d.get("choice_selected") or "").startswith("option_") for d in decisions_raw):
            if commit_lock.locked(): commit_lock.release()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "choice_required",
                        "message": "No strategic option was selected. Choose Option A, B or C before committing."},
            )

    # VULN-009: Enforce minimum investment of $1 per BU
    for d in decisions_raw:
        if d.get("capex_allocated", 0) < 1:
            if commit_lock.locked(): commit_lock.release()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BU '{d['bu_id']}' must receive a minimum investment of $1.",
            )

    # ── COR-1 / TECH-2: server-side recompute of investment_ratio ──
    # The client-supplied investment_ratio is ADVISORY ONLY. Derive it here
    # from the actual committed spend so a hand-crafted request cannot decouple
    # the ESG reward (gradated SLO/reputation growth + greenwashing detection in
    # engine.process_tick) from real capex -- e.g. investment_ratio=1.0 paired
    # with capex_allocated=$1.
    #
    # Formula mirrors the player cockpit's Corporate Sustainability Fund pool
    # (frontend/app/page.js `csfPool`): csf_pool = max(treasury * 0.20, 5_000_000),
    # investment_ratio = clamp(capex_allocated / csf_pool, 0.0, 1.0). Because the
    # honest client already sends exactly this value, legitimate play is
    # unchanged; only fabricated ratios are corrected.
    _treasury = current_global.get("corporate_treasury", 0) or 0
    _csf_pool = max(_treasury * _cfg.CSF_POOL_TREASURY_FRACTION, _cfg.CSF_POOL_FLOOR)
    for d in decisions_raw:
        _capex = d.get("capex_allocated", 0) or 0
        _ratio = (_capex / _csf_pool) if _csf_pool > 0 else 0.0
        d["investment_ratio"] = max(0.0, min(1.0, _ratio))

    # ── F-07 (launch audit 2026-09-01): engine parameters are SERVER-derived ──
    # crisis_severity, imitation_decay_rate and emergency_credit_used used to be
    # read from the player's request body. The model even documented
    # crisis_severity as "ignored" — it was not (pre_tick only overrode round 4).
    # A client could send crisis_severity=0 for every crisis round, or
    # imitation_decay_rate=0 to freeze synergy decay. The body fields are still
    # accepted for older clients but are ignored (and logged when non-default).
    _server_crisis = base_crisis_severity_for_round(current_round)
    _server_decay = _cfg.DEFAULT_IMITATION_DECAY_RATE   # CFG-05: call-time read
    # The cockpit's rule for the emergency credit line: the 20% CSF allowance
    # has fallen below the $5M floor — computed here from the same numbers.
    _server_emergency = bool((_treasury * _cfg.CSF_POOL_TREASURY_FRACTION) < _cfg.CSF_POOL_FLOOR)
    if (body.crisis_severity not in (0.0, _server_crisis)
            or abs(body.imitation_decay_rate - _server_decay) > 1e-9
            or body.emergency_credit_used != _server_emergency):
        _log.info(f"[F-07] client engine parameters ignored for {session_id} R{current_round}: "
                  f"crisis={body.crisis_severity} decay={body.imitation_decay_rate} "
                  f"emergency={body.emergency_credit_used} -> server "
                  f"crisis={_server_crisis} decay={_server_decay} emergency={_server_emergency}")

    # ── PRE-TICK: Round-specific validation & overrides ───────
    pre_result = pre_tick(
        round_number=current_round,
        current_global=current_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        crisis_severity=_server_crisis,
        force_override_cfo=body.force_override_cfo,
    )

    # Check for validation errors (e.g. R2 CFO gate)
    if "validation_error" in pre_result:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pre_result["validation_error"],
        )

    # Use potentially overridden crisis severity
    effective_crisis = pre_result.get("crisis_severity", _server_crisis)

    # ── Crisis Multiplier KPI: expose severity source for UI display ──
    # Allows the frontend to show a visible "Crisis Multiplier" KPI panel.
    # Base crisis severity for this paradigm is 40 (from round_config special_rules).
    _BASE_CRISIS = 40
    _crisis_multiplier = round(effective_crisis / _BASE_CRISIS, 2) if _BASE_CRISIS else 1.0
    _pre_evts = pre_result.get("pre_events", {})
    if _pre_evts.get("electronics_blindspot_triggered"):
        _crisis_source = "electronics_blindspot"
        _crisis_label = "⚡ DOUBLED — Electronics audit skipped in Round 1"
    elif _pre_evts.get("deferred_audit_penalty") or _pre_evts.get("compliance_gap_triggered"):
        _crisis_source = "deferred_audit"
        _crisis_label = "⚠️ +50% — Audit deferred in Round 1"
    elif effective_crisis != _server_crisis:
        _crisis_source = "history_modifier"
        _crisis_label = f"Modified by earlier decisions: {effective_crisis}"
    else:
        _crisis_source = "baseline"
        _crisis_label = "✅ Baseline — Full audit completed"
    # ── PHASE-1: Inject difficulty tier into engine input ─────
    _session_difficulty = (session_info or {}).get("difficulty_tier", "standard")
    current_global.setdefault("active_event_flags", {})["difficulty_tier"] = _session_difficulty
    # ── Run the tick engine ──────────────────────────────────
    tick_result = process_tick(
        current_global=current_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        dividends_paid=body.dividends_paid,
        crisis_severity=effective_crisis,
        imitation_decay_rate=_server_decay,
        decision_paradigm=paradigm,
        emergency_credit_used=_server_emergency,
    )

    new_round = tick_result["global_state"]["round_number"]
    # ── CAP: After Round 10, do NOT advance to Round 11 ──
    if current_round == 10:
        new_round = 10
        tick_result["global_state"]["round_number"] = 10
    new_global = tick_result["global_state"]
    new_bus = tick_result["bu_states"]
    events = tick_result["events"]

    # ── Crisis Multiplier KPI: expose severity source for UI display ──
    events["crisis_severity_effective"] = effective_crisis
    events["crisis_multiplier"] = _crisis_multiplier
    events["crisis_multiplier_source"] = _crisis_source
    events["crisis_multiplier_label"] = _crisis_label

    # Merge pre-tick events
    events.update(pre_result.get("pre_events", {}))

    # ── PILLAR MODE: Apply aggregated impacts ────────────────
    if pillar_aggregation:
        agg_impacts = pillar_aggregation.get("impacts", {})
        agg_cost = pillar_aggregation.get("total_cost", 0)

        # Apply treasury cost from pillar selections (NOT modified by effectiveness — cost is always owed)
        if agg_cost != 0:
            new_global["corporate_treasury"] = round(new_global["corporate_treasury"] + agg_cost, 2)
        # ALWAYS set the marker in pillar mode, even at zero cost — it is the
        # paradigm signal every post_tick handler (and _apply_common_impacts)
        # branches on. Before 2026-08-31 an all-free pillar selection left it
        # unset and the whole tick ran in legacy mode by accident.
        events["pillar_cost_applied"] = agg_cost

        # ── Workforce Readiness → Pillar Effectiveness ──
        # Low readiness reduces the magnitude of strategic impacts (not costs)
        effectiveness = new_global.get("pillar_effectiveness_modifier", 1.0)
        if effectiveness != 1.0:
            events["pillar_effectiveness_modifier_applied"] = effectiveness

        # Pillar-impact ownership (2026-08-31 design ruling): R1-R9 the
        # router applies the aggregates here — the single impact source in
        # pillar mode. R10 is the exception: the pillar selections map to an
        # A/B/C ending whose full impact set applies in post_tick, so the
        # aggregates are NOT applied on top.
        if current_round != 10:
            _apply_pillar_aggregate_impacts(new_global, new_bus, events, agg_impacts, effectiveness)
        else:
            events["pillar_aggregates_skipped_r10"] = True

        # Store pillar metadata in events
        events["decision_paradigm"] = "multi_toggles"
        events["pillar_selections"] = pillar_aggregation.get("per_area", {})
        events["pillar_flags"] = pillar_aggregation.get("flags_set", [])
        events["pillar_exclusivity_warnings"] = pillar_aggregation.get("exclusivity_warnings", [])
        # Rec 5: Expose aggregate impacts for post-tick handlers to read
        events["pillar_aggregate_impacts"] = agg_impacts

        # Persist pillar flags into active_event_flags
        flag_key = f"r{current_round}_pillar_flags"
        new_global.setdefault("active_event_flags", {})
        new_global["active_event_flags"][flag_key] = pillar_aggregation.get("flags_set", [])
    else:
        # WP-27 (audit 2026-09-04 follow-on): this stamped the literal
        # "legacy_abc" for EVERY non-pillar paradigm, and the label is what
        # round_logic reads back from active_event_flags — so advanced_climate
        # paid the legacy mid-game carbon OPEX on top of its own escalating
        # internal fee (_apply_midgame_carbon_cost's advanced_climate early
        # return never saw "advanced_climate"), the finale's I10 carbon-tax
        # sync to the peak internal fee never fired, and a BRSR run carried a
        # legacy label. `paradigm` is already "legacy_abc" here when a
        # multi_toggles commit fell back to the legacy path (no pillar
        # decisions), so the pillar/legacy distinction is preserved.
        events["decision_paradigm"] = paradigm

    # C2: re-seed effective climate inputs (global + per-cohort override) into
    # the round's active_event_flags before the engine reads them, so a mid-run
    # Switchboard/override change takes effect from this round forward. Seeds
    # base inputs only; round-computed outputs use different keys.
    try:
        from admin_shared import seed_effective_flags
        new_global.setdefault("active_event_flags", {})
        seed_effective_flags(session_id, new_global["active_event_flags"])
    except Exception as _sef_exc:
        # F-36: a failed seed means a Switchboard change silently did not apply
        # to this round. Log it properly and mark the round.
        _log.error(f"[ENGINE-FAILURE] seed_effective_flags failed for {session_id}: {_sef_exc}", exc_info=True)
        events.setdefault("engine_failures", []).append(
            {"engine": "seed_effective_flags", "error": f"{type(_sef_exc).__name__}: {_sef_exc}"[:300]})

    # ── Carry session-level flags into the post-tick state (audit F-04) ──
    # engine._assemble_global_state sets new_global["active_event_flags"] to
    # THIS round's events dict; the stored flags are merged in only after
    # run_new_engines (the "preserve history" merge below). Every post-tick
    # engine that reads session configuration off gs["active_event_flags"]
    # therefore saw nothing: the cohort seed (npc_stakeholders.py — the
    # $5-25M regulator fine fell through to the unseeded global RNG, so two
    # teams with identical decisions diverged by up to ~$17M), the loan rate
    # and ending pathway on the balance sheet, the difficulty tier for the
    # covenant ratio. dry_run.py forwarded the seed since its inception;
    # production never did, which is why the offline balance reports were
    # seeded and the classroom was not. setdefault: nothing the tick produced
    # is overridden.
    _forward_persistent_flags(current_global, new_global)

    # ── POST-TICK: Round-specific state mutations ────────────
    post_events = post_tick(
        round_number=current_round,
        global_state=new_global,
        bu_states=new_bus,
        decisions=decisions_raw,
        events=events,
        previous_flags=current_global.get("active_event_flags", {}),
        # VAL-06 (audit 2026-09-04, WP-27): post_tick's brsr_ngrbc branch —
        # process_brsr_round, the BRSR option flags, finalise_brsr_track and
        # the BRSR finale — is gated on this parameter, which the player
        # commit never passed (the facilitator auto-commit did). A BRSR
        # cohort therefore played the legacy crises with legacy flags and
        # ended on the legacy finale.
        decision_paradigm=paradigm,
    )
    events.update(post_events)

    # Audit F-06: the "Road Not Taken" shadow runs (below) take the chosen
    # option's ALTERNATIVES through process_tick + post_tick — the engine and
    # the round's option effects — and nothing further. Their baseline is
    # therefore the actual state at exactly this point, captured before
    # run_new_engines (NPC fines, agents, balance sheet) and board pressure
    # mutate new_global in place. Diffing the shadow against the fully
    # post-processed state made every alternative "worth" exactly the round's
    # later deductions, identical for both alternatives, to the cent.
    _regret_baseline = {
        "treasury": float(new_global.get("corporate_treasury", 0.0) or 0.0),
        "reputation": float(new_global.get("group_reputation", 50.0) or 0.0),
        "ebitda": float(sum(b["revenue_base"] - b["opex_base"] for b in new_bus)),
    }

    # ── NEW ENGINES: Process all improvement modules ──────────
    # Inject data needed by balance sheet engine (CAPEX & dividends)
    events["decisions_raw"] = decisions_raw
    events["dividends_paid"] = body.dividends_paid
    # SPEC F5 — pass the round's optional engagement action to run_new_engines
    # (acted on only when stakeholder_engagement_enabled is on).
    events["engagement_action"] = body.engagement_action
    try:
        new_engine_events = run_new_engines(
            round_number=current_round,
            global_state=new_global,
            bu_states=new_bus,
            events=events,
        )
        events.update(new_engine_events)
        # Audit F-08 / SEAM-05: the R10 finale ran inside post_tick, BEFORE the
        # engines above applied the round's NPC fines, agent hits and balance
        # sheet. Re-run its valuation stamps on the closing state so
        # final_treasury, group_reputation, net debt / equity / share price,
        # emissions, the solvency-gated profile and the canonical record are
        # the persisted numbers, not a mid-pipeline snapshot.
        if events.get("finale_inputs"):
            from round_logic import restamp_finale_valuation
            restamp_finale_valuation(new_global, new_bus, events,
                                     current_global.get("active_event_flags", {}))
    except Exception as exc:
        # F-19: the batch itself throwing means NO engine ran for this team this
        # round. It must not be a warning nobody reads.
        _log.error(f"[ENGINE-FAILURE] New engines batch failed for {session_id} R{current_round}: {exc}", exc_info=True)
        events.setdefault("engine_failures", []).append(
            {"engine": "run_new_engines (whole batch)", "error": f"{type(exc).__name__}: {exc}"[:300]})

    # ── ENGAGEMENT 7.4: Board Pressure Events (R3, R6, R9) ───
    # SEAM-10 (audit 2026-09-04): this ran AFTER the round was persisted, so
    # the −3 reputation existed only in the commit response — the next
    # dashboard poll put the 3 points back and analytics/debrief never saw
    # the penalty the player was shown. It now runs before persistence.
    if current_round in (3, 6, 9):
        try:
            baseline_ebitda = current_global.get("historical_ebitda", 0)
            current_ebitda = sum(bu["revenue_base"] - bu["opex_base"] for bu in new_bus)
            target_ebitda = baseline_ebitda * 1.05  # 5% improvement target
            if current_ebitda < target_ebitda:
                shortfall_pct = round(((target_ebitda - current_ebitda) / max(target_ebitda, 1)) * 100, 1)
                events["board_pressure"] = {
                    "triggered": True,
                    "target_ebitda": target_ebitda,
                    "actual_ebitda": current_ebitda,
                    "shortfall_pct": shortfall_pct,
                    "message": (
                        f"⚠️ BOARD WARNING: EBITDA (${current_ebitda:,.0f}) is "
                        f"{shortfall_pct}% below the board's target of ${target_ebitda:,.0f}. "
                        f"The Chairman expects a credible improvement plan by next period. "
                        f"Failure to deliver may result in a leadership review."
                    ),
                    "reputation_penalty": -3,
                }
                # Apply reputation penalty
                new_global["group_reputation"] = max(0, round(
                    new_global.get("group_reputation", 50) - 3, 2
                ))
            else:
                events["board_pressure"] = {
                    "triggered": False,
                    "message": "✅ Board satisfied — EBITDA meets or exceeds target.",
                }
        except Exception as exc:
            _log.warning(f"[WARN] Board pressure calculation failed: {exc}")

    # F-19 / F-36 (launch audit 2026-09-01): make engine failures VISIBLE.
    # Every engine in run_new_engines is individually isolated (a failing
    # balance sheet must not block a class), but until now a team could get a
    # round without its stakeholder/balance-sheet update while its siblings
    # did, and nobody was told. The failures are now (a) stamped on the round
    # (`engine_failures`, persisted with the flags, shown by the console),
    # (b) pushed to every facilitator console over the admin WebSocket, and
    # (c) counted per process so a health probe can alarm on them.
    _failures = events.get("engine_failures") or []
    if _failures:
        events["engine_failure_alert"] = {
            "round": current_round,
            "count": len(_failures),
            "engines": [f.get("engine") for f in _failures],
            "message": (f"⚠️ {len(_failures)} engine module(s) failed while processing round "
                        f"{current_round} for this team: {', '.join(f.get('engine', '?') for f in _failures)}. "
                        "The round committed, but the affected analytics/stakeholder state did not update."),
        }
        _ENGINE_FAILURE_COUNTER["total"] += len(_failures)
        _ENGINE_FAILURE_COUNTER["last"] = {"session_id": session_id, "round": current_round,
                                           "engines": events["engine_failure_alert"]["engines"]}
        try:
            from admin_router import manager as _ws_manager
            _sess_meta_ef = await db.get_session_info(session_id)
            await _ws_manager.broadcast_admin({
                "type": "engine_failure",
                "session_id": session_id,
                "cohort_id": (_sess_meta_ef or {}).get("parent_cohort_id") or session_id,
                "round": current_round,
                "engines": events["engine_failure_alert"]["engines"],
                "message": events["engine_failure_alert"]["message"],
            })
        except Exception:
            pass  # the alert is on the round either way

    # ══ REPORTING-TRUTH RESYNC (math audit, 2026-07) ═══════════════════════
    # process_tick derives historical_ebitda / tco2e_emissions / per-BU
    # absolute_emissions inside its FINANCIAL layer, but the BU table keeps
    # mutating afterwards: the engine's operational layer adjusts carbon
    # intensity (green tech −3, cost-cutting +2, austerity scaling, +2%
    # creep) and OPEX (burnout/NCD penalties), the reporting layer applies
    # supplier defection, and this route then applies pillar aggregate
    # deltas, post_tick round mutations, and the new-engines batch. The
    # dashboard was therefore reporting a CO₂ total that did not equal the
    # sum of its own per-BU rows (audited live: 2,387.4 t reported vs
    # 2,265.2 t recomputed from the same response's BUs; EBITDA 9.41M vs
    # 11.35M), and every history/trend point after R1 carried the stale
    # value.
    #
    # Recompute the three DISPLAY metrics from the FINAL BU table so the
    # response and persisted state are self-consistent. Gameplay is
    # untouched: the internal carbon fee and competitor-pressure
    # calculations consumed their mid-pipeline ctx values before this point,
    # and nothing downstream reads these persisted fields as a logic input
    # (terminal valuation recomputes from BU state; the competitor seeding
    # fallback only ever fires on the first commit, where it reads the
    # creation-time baseline, not this value).
    new_global["historical_ebitda"] = round(
        sum((bu.get("revenue_base") or 0) - (bu.get("opex_base") or 0) for bu in new_bus), 2
    )
    new_global["tco2e_emissions"] = round(
        sum((bu.get("carbon_intensity") or 0) * (bu.get("revenue_base") or 0) / 1_000_000 for bu in new_bus), 1
    )
    for bu in new_bus:
        bu["absolute_emissions"] = round(
            (bu.get("carbon_intensity") or 0) * (bu.get("revenue_base") or 0) / 1_000_000, 2
        )

    # Ensure active_event_flags contains everything (preserve history)
    # Merge order: historical flags → post_tick flags (rN_flags) → events
    # FIX: Previously used current_global (input state) as base, which
    # silently dropped flags set by _apply_option_flags in post_tick.
    merged_flags = dict(current_global.get("active_event_flags", {}))
    merged_flags.update(new_global.get("active_event_flags", {}))
    merged_flags.update(events)
    new_global["active_event_flags"] = merged_flags

    # ── CHECK HIDDEN RESOURCE TRIGGERS ───────────────────────
    try:
        triggered = await check_hidden_resource_triggers(
            session_id=session_id,
            round_number=new_round,
            global_state=new_global,
            bu_states=new_bus,
        )
        if triggered:
            events["hidden_resources_unlocked"] = [
                {"id": r["id"], "title": r["title"], "effect": r.get("effect")}
                for r in triggered
            ]
    except Exception as exc:
        # Non-critical — don't block the turn commit; but visible (F-36).
        _log.error(f"[ENGINE-FAILURE] Hidden resource trigger check failed for {session_id}: {exc}", exc_info=True)
        events.setdefault("engine_failures", []).append(
            {"engine": "Hidden resource triggers", "error": f"{type(exc).__name__}: {exc}"[:300]})

    # Clear saved decisions since turn was committed
    if "saved_allocations" in new_global:
        del new_global["saved_allocations"]
    if "saved_decision_choice" in new_global:
        del new_global["saved_decision_choice"]
    if "saved_round" in new_global:
        del new_global["saved_round"]

    # FIX AUDIT-002: Removed duplicate R10 terminal valuation block.
    # The authoritative R10 calculation lives in round_logic.py →
    # _post_r10_grand_finale(), which uses flag-based MR accounting,
    # config-driven exit multiples, and correct carbon tonnage units.
    # The previous block here used a divergent formula (continuous MR,
    # dynamic exit multiple, different profile thresholds) that silently
    # overwrote the round_logic.py values in the events dict.

    # ── Enrich decisions for audit trail ─────────────────────
    # Populate decision_node_id from round config (crisis ID)
    round_cfg = get_round_config(current_round)
    crisis_id = round_cfg.get("crisis", {}).get("id", "") if round_cfg else ""
    crisis_title = round_cfg.get("crisis", {}).get("title", "") if round_cfg else ""
    # Populate player_id from session metadata
    audit_player_id = (session_info or {}).get("player_id") or ""
    for d in decisions_raw:
        if not d.get("decision_node_id"):
            d["decision_node_id"] = crisis_title or crisis_id
        if not d.get("player_id"):
            d["player_id"] = audit_player_id

    # ── Persist ──────────────────────────────────────────────
    # ── R10 SYSTEM FREEZE: Capture DNA snapshot ──────────────
    if current_round == 10:
        try:
            from consequence_dna_api import build_consequence_dna_data
            history_raw = await db.fetch_round_history(session_id)
            history_for_dna = [
                {"round_number": h["round_number"], "global_state": h["global_state"], "decisions": h.get("decisions", [])}
                for h in history_raw
            ]
            dna_snapshot = build_consequence_dna_data(
                session_id=session_id,
                global_state=new_global,
                bu_states=new_bus,
                history=history_for_dna,
            )
            new_global.setdefault("active_event_flags", {})["consequence_dna_snapshot"] = dna_snapshot
        except Exception as exc:
            _log.warning(f"[WARN] Consequence DNA snapshot capture failed: {exc}")

    if current_round == 10:
        # R10-1: mark the run complete BEFORE persisting, so the state that is
        # written already carries the flag the gate above reads. Previously the
        # normal finale never set game_over at all — completion was inferred as
        # `rn >= 10` in three separate places — which is why R10 could be
        # re-committed indefinitely.
        new_global["game_over"] = True
        new_global.setdefault("game_over_reason", "simulation_complete_r10")

    # ── 4.8 (2026-08-03): the commit envelope ──────────────────────────────
    #
    # decision_audit_log has always had a `metadata` JSONB column and NOTHING
    # has ever written to it. Only eight scalar fields survived a commit, so
    # everything else a team submitted was discarded at the moment it stopped
    # being a request object:
    #
    #     pillar_decisions      the {energy, operations, supply_chain,
    #                           offsetting} split — an ENGINE INPUT
    #     investment_ratio      as actually used (recomputed server-side by
    #                           TECH-2/COR-1, so the submitted value is not
    #                           the one that scored)
    #     dividends_paid        moves the treasury
    #     emergency_credit_used takes a loan at +2%
    #     force_override_cfo    overrides a refusal
    #     engagement_action     the F5 dialogic action
    #     player_id             WHO decided (Postgres dropped it; the memory
    #                           backend kept it — a silent parity gap)
    #
    # Every one of those changes the numbers. A round could therefore not be
    # reconstructed from its own audit trail: you could see that a team chose
    # option_b and spent $4M, but not how they split it, whether they took the
    # loan, or whether a CFO refusal was overridden. That is the same class of
    # defect as R10-2 — an audit log that looks complete and is not.
    #
    # Built HERE, after the engine has run, so investment_ratio is the
    # effective value rather than the advisory one the client sent. Repeated on
    # every row rather than normalised into a new table: rows are append-only,
    # capped at 64 per round, and a self-describing row survives a partial
    # export. No migration — the column has been sitting there empty.
    _turn_envelope = {
        "dividends_paid": body.dividends_paid,
        "emergency_credit_used": _server_emergency,     # F-07: server-derived
        "force_override_cfo": body.force_override_cfo,
        "engagement_action": body.engagement_action,
        "imitation_decay_rate": _server_decay,           # F-07: server-derived
        "expected_round": body.expected_round,
        # Found by BUILDING the replay tool (4.9): these two are engine inputs
        # that the CLIENT never sends — the server derives them. Recording only
        # what the client submitted therefore left a replay under-determined:
        # crisis_severity comes from the round config plus pre_tick modifiers
        # (TECH-1 deprecated the client's value outright), and the paradigm is
        # resolved from the session, falling back to the parent cohort. Without
        # them a verifier has to GUESS two inputs and would report spurious
        # mismatches — which is worse than no verifier, because people would
        # stop trusting the real mismatches too.
        "crisis_severity_effective": effective_crisis,
        "decision_paradigm": paradigm,
    }
    _envelope_player_id = (session_info or {}).get("player_id") or ""
    for _dec in decisions_raw:
        _dec["metadata"] = {
            "schema": 1,
            "player_id": _envelope_player_id,
            # Effective, not submitted — see TECH-2/COR-1. The distinction is
            # the whole point: the submitted value never scored anything.
            "investment_ratio": _dec.get("investment_ratio"),
            "pillar_decisions": _dec.get("pillar_decisions"),
            "turn": _turn_envelope,
        }

    try:
        if current_round == 10:
            # R10: Update existing state in-place (don't insert new round 11)
            # SEAM-08 (audit 2026-09-04): the row this overwrites is the state
            # ENTERING round 10 — stash it so history keeps ten entering-states
            # and the analytics/debrief R10 deltas exist (history_semantics).
            from history_semantics import stash_entering_state
            stash_entering_state(new_global, current["global_state"], current["bu_states"])
            await db.update_latest_global_state(
                session_id=session_id,
                global_state=new_global,
                bu_states=new_bus,
            )
            # R10-2 (2026-08-02): actually log them. This loop was `pass` with a
            # comment claiming they were "logged inline by insert_next_round" —
            # but the R10 branch does not CALL insert_next_round, so the graded
            # finale's decisions were never recorded anywhere. A grade you cannot
            # reconstruct is a grade you cannot defend.
            try:
                # AUDIT-1: `current_round`, matching insert_next_round's corrected
                # convention — decisions are filed under the round they were made
                # in. R10 needs an explicit call because its branch persists in
                # place via update_latest_global_state and never reaches
                # insert_next_round, so the finale's decisions were written nowhere.
                await db.log_decisions(
                    session_id=session_id, round_number=current_round, decisions=decisions_raw
                )
            except Exception as _audit_exc:
                _log.error(
                    "[R10] FAILED to write finale decisions to the audit log for "
                    "session=%s: %s", session_id, _audit_exc,
                )
        else:
            await db.insert_next_round(
                session_id=session_id,
                round_number=new_round,
                global_state=new_global,
                bu_states=new_bus,
                decisions=decisions_raw,
            )
    except Exception as exc:
        commit_lock.release()
        # Unique constraint → duplicate round
        if "uq_session_round" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Round {new_round} has already been committed for this session.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist round: {exc}",
        )

    # ── AUTO-INJECT SCHEDULED INTERVENTIONS ───────────────────
    try:
        auto_injected = await auto_inject_scheduled_interventions(
            session_id=session_id,
            new_round=new_round,
        )
        if auto_injected:
            events["auto_injected_messages"] = [
                {"id": m["id"], "title": m["title"], "preset_id": m.get("preset_id")}
                for m in auto_injected
            ]
    except Exception as exc:
        _log.warning(f"[WARN] Auto-inject scheduled interventions failed: {exc}")

    # ── MP-01: Update cohort commit count in globalState ─────────────
    try:
        parent_cohort_id = (session_info or {}).get("parent_cohort_id")
        if parent_cohort_id:
            # MP-01: reuse the shared live helper so the committing team's
            # immediate response matches what every other team will see on their
            # next dashboard poll. Persisted too, as a restart fallback.
            committed_count, total_teams = await _cohort_commit_progress(session_info)
            if total_teams is not None:
                new_global["team_commits_this_round"] = committed_count
                new_global["cohort_team_count"] = total_teams
                await db.update_latest_global_state(session_id, new_global, new_bus)
    except Exception as exc:
        _log.warning(f"[WARN] Cohort commit count update failed: {exc}")

    # ── PRACTICE MODE: Reset after Round 2 ────────────────────
    # Check if this session or its parent is in practice mode
    practice_session_id = session_id
    if session_info and session_info.get("parent_cohort_id"):
        practice_session_id = session_info["parent_cohort_id"]

    if is_practice_mode(practice_session_id) and current_round >= 2:
        # Reset the cohort session and all child sessions back to Round 1
        await db.reset_session_to_round1(practice_session_id)
        # Disable practice mode after reset
        from admin_shared import _practice_mode
        _practice_mode.pop(practice_session_id, None)

        # Notify all players of the practice reset
        from admin_router import manager as ws_manager
        await ws_manager.push_to_session(practice_session_id, {
            "type": "practice_reset",
            "message": "Practice round completed! Session has been reset to Round 1.",
        })

        # Return a special response with practice_reset event
        reset_state = await db.fetch_latest_state(session_id)
        reset_events = {"practice_reset": True, "practice_message": "Practice complete — session reset to Round 1."}
        commit_lock.release()
        return CommitTurnResponse(
            session_id=session_id,
            new_round_number=1,
            global_state=GlobalStateOut(**(reset_state["global_state"] if reset_state else new_global)),
            business_units=[_bu_out(bu) for bu in (reset_state["bu_states"] if reset_state else new_bus)],
            events=reset_events,
        )

    # ── ENGAGEMENT 7.2: CEO Diary ──────────────────────────────
    try:
        from ceo_diary import generate_ceo_diary
        primary_choice = ""
        for d in decisions_raw:
            c = d.get("choice_selected", "")
            if c.startswith("option_"):
                primary_choice = c
                break
        diary_entry = generate_ceo_diary(current_round, primary_choice, events)
        events["ceo_diary"] = diary_entry
    except Exception as exc:
        _log.warning(f"[WARN] CEO Diary generation failed: {exc}")

    # ── ENGAGEMENT 7.1: Decision Regret (Shadow Ticks) ────────
    try:
        from admin_shared import _god_mode_settings
        if _god_mode_settings.get("decision_regret_enabled", True):
            regret_analysis = {}
            all_options = ["option_a", "option_b", "option_c"]
            for alt_option in all_options:
                if alt_option == primary_choice:
                    continue
                # Create shadow decisions with alternative choice
                shadow_decisions = copy.deepcopy(decisions_raw)
                for d in shadow_decisions:
                    d["choice_selected"] = alt_option
                try:
                    import copy as _copy
                    shadow_result = process_tick(
                        current_global=_copy.deepcopy(current_global),
                        current_bus=_copy.deepcopy(current_bus),
                        decisions=shadow_decisions,
                        dividends_paid=body.dividends_paid,
                        crisis_severity=effective_crisis,
                        imitation_decay_rate=_server_decay,
                        decision_paradigm=paradigm,
                        emergency_credit_used=_server_emergency,
                    )
                    shadow_gs = shadow_result["global_state"]
                    shadow_bus = shadow_result["bu_states"]
                    # The option's own effects (treasury, reputation, CI, SLO,
                    # flags) are applied by post_tick, not by the engine tick;
                    # a shadow without it reads 0/0 in most rounds. Same
                    # inputs as the real path, on the deep copies (audit F-06).
                    _forward_persistent_flags(current_global, shadow_gs)
                    shadow_gs_events = shadow_result.get("events") or {}
                    post_tick(
                        round_number=current_round,
                        global_state=shadow_gs,
                        bu_states=shadow_bus,
                        decisions=shadow_decisions,
                        events=shadow_gs_events,
                        previous_flags=_copy.deepcopy(current_global.get("active_event_flags", {})),
                        decision_paradigm=paradigm,
                    )
                    shadow_ebitda = sum(b["revenue_base"] - b["opex_base"] for b in shadow_bus)
                    regret_analysis[alt_option] = {
                        "treasury_delta": round(float(shadow_gs.get("corporate_treasury", 0.0) or 0.0)
                                                - _regret_baseline["treasury"], 2),
                        "reputation_delta": round(float(shadow_gs.get("group_reputation", 50.0) or 0.0)
                                                  - _regret_baseline["reputation"], 2),
                        "ebitda_delta": round(shadow_ebitda - _regret_baseline["ebitda"], 2),
                    }
                except Exception:
                    pass  # Shadow tick failed — skip this option
            if regret_analysis:
                # R10: the synergy gate can replace the chosen option with the
                # fallback (round_logic r10_choice); report what was applied.
                _applied_choice = events.get("r10_choice") if current_round == 10 else None
                events["decision_regret"] = {
                    "your_choice": _applied_choice or primary_choice,
                    "alternatives": regret_analysis,
                    "scope": "engine_and_round_effects",
                    "note": ("What the other options would have produced this round through the engine and "
                             "the round's option effects — before events, fines and stakeholder reactions, "
                             "which land whichever option you choose."),
                }
    except Exception as exc:
        _log.warning(f"[WARN] Decision Regret analysis failed: {exc}")

    # ── ITEM 24: Facilitator commit notification ─────────────
    try:
        parent_cohort_id = (session_info or {}).get("parent_cohort_id")
        if parent_cohort_id:
            import time as _time_notify
            notification = {
                "player_id": (session_info or {}).get("player_id", "unknown"),
                "round": new_round,
                "timestamp": _time_notify.time(),
                "choice": primary_choice,
            }
            parent_sess = await db.get_session_info(parent_cohort_id)
            if parent_sess:
                commit_log = parent_sess.setdefault("commit_notifications", [])
                commit_log.append(notification)
                # Keep only last 100 notifications
                if len(commit_log) > 100:
                    parent_sess["commit_notifications"] = commit_log[-100:]
    except Exception as exc:
        _log.warning(f"[WARN] Facilitator notification failed: {exc}")

    return CommitTurnResponse(
        session_id=session_id,
        new_round_number=new_round,
        global_state=GlobalStateOut(**new_global),
        business_units=[_bu_out(bu) for bu in new_bus],
        events=events,
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/save-decisions
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/save-decisions",
    status_code=status.HTTP_200_OK,
    summary="Save uncommitted UI allocations and decisions mid-round",
)
async def save_decisions(request: Request, session_id: str, body: SaveDecisionsRequest):
    """
    Saves the user's current slider allocations and chosen decision
    to the global_state so they can resume after leaving the page.
    """
    await _assert_player_owns_session(request, session_id)
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found."
        )

    global_state = current["global_state"]
    bu_states = current["bu_states"]

    global_state["saved_allocations"] = body.allocations
    global_state["saved_decision_choice"] = body.decision_choice
    # BUG-2026-07-20: round-stamp the save. Without this, a save carried into
    # the next round (engine snapshot copies saved_* forward before the commit
    # path deletes them) hydrated the NEW round's sliders with the OLD round's
    # allocations — every round started pre-set at last round's values instead
    # of zero. The client only hydrates when saved_round matches its current
    # round, so a stale save can never leak across a round boundary again.
    global_state["saved_round"] = current.get("round_number", global_state.get("round_number"))

    # Update latest state in DB
    await db.update_latest_global_state(session_id, global_state, bu_states)

    return {"status": "success", "message": "Decisions saved successfully."}


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/prediction
# PRED-1 (UX audit §9): persist the player's "Predict Before You Commit" text
# server-side. Previously it was thrown into sessionStorage and lost — the
# aggregated predicted-vs-actual view is the debrief's highest-value artifact.
# Stored in session METADATA (never in round state), so the engine, the golden
# trace and the audit log are untouched.
# ─────────────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    round_number: int
    text: str


@router.post(
    "/{session_id}/prediction",
    status_code=status.HTTP_200_OK,
    summary="Persist the player's pre-commit prediction for a round",
)
async def save_prediction(request: Request, session_id: str, body: PredictionRequest):
    await _assert_player_owns_session(request, session_id)
    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Session {session_id} not found.")
    text = (body.text or "").strip()[:2000]  # bound the payload
    if not text:
        return {"status": "skipped", "message": "Empty prediction not stored."}
    predictions = dict(sess.get("round_predictions") or {})
    predictions[str(int(body.round_number))] = text
    await db.update_session_metadata(session_id, {"round_predictions": predictions})
    return {"status": "success", "round_number": body.round_number}


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/journey-response
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/journey-response",
    status_code=status.HTTP_200_OK,
    summary="Persist a pedagogical journey response (R6/R7/R8) for a player session",
)
async def save_journey_response(request: Request, session_id: str, body: JourneyResponseRequest):
    """
    Stores the player's response from a pedagogical journey panel (R6 revelation,
    R7 budget allocation, R8 stakeholder tribunal) keyed by journey step.
    Data lives in _session_journey_responses[session_id] for the lifetime of the
    process and is readable by the admin debrief view.
    """
    await _assert_player_owns_session(request, session_id)
    if session_id not in _session_journey_responses:
        _session_journey_responses[session_id] = {}
    _session_journey_responses[session_id][body.key] = body.data
    return {"status": "ok", "session_id": session_id, "key": body.key}


@router.get(
    "/{session_id}/journey-responses",
    summary="Retrieve all persisted journey responses for a session",
)
async def get_journey_responses(session_id: str, request: Request):
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    return {"session_id": session_id, "responses": _session_journey_responses.get(session_id, {})}


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/consequence-dna-data
# Consequence DNA Visualizer — full Sankey diagram data model
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/consequence-dna-data",
    summary="Get Consequence DNA Sankey data for the visualizer",
)
async def get_consequence_dna_data(session_id: str, request: Request):
    """
    Returns the complete data model for the Consequence DNA Visualizer:
    decision nodes, causal flags, metric shifts, M_R projections,
    agent conflict/constriction nodes, cascade events, and Senge badges.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    history_raw = await db.fetch_round_history(session_id)
    history = [
        {"round_number": h["round_number"], "global_state": h["global_state"], "decisions": h.get("decisions", [])}
        for h in history_raw
    ]

    from consequence_dna_api import build_consequence_dna_data
    # SEAM-11 (audit 2026-09-04): fetch_latest_state keeps round_number as a
    # sibling key, not inside global_state, so the live graph was built at
    # "round 1" for every session — flags with source_round > 1 dropped,
    # links skipped, ignition impossible — while the R10 snapshot (built from
    # new_global, which carries round_number) was right. Same one-line fix
    # the final report already carries.
    dna_data = build_consequence_dna_data(
        session_id=session_id,
        global_state={**latest["global_state"], "round_number": latest["round_number"]},
        bu_states=latest["bu_states"],
        history=history,
    )
    return dna_data


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/sdg-dashboard
# SDG Alignment Radar — Chief Strategic Orchestrator Dashboard
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/sdg-dashboard",
    summary="Get SDG alignment dashboard data for the radar visualizer",
)
async def get_sdg_dashboard(session_id: str, request: Request):
    """
    Returns the complete SDG dashboard data:
    - Per-BU SDG alignment scores with material SDG details
    - Group-level SDG composite score
    - SDG heatmap (per-SDG normalized scores)
    - Material gap alerts
    - Materiality mapping metadata
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = latest["global_state"]
    bus = latest["bu_states"]
    flags = gs.get("active_event_flags", {})

    # Import the SDG linkage engine
    try:
        from sdg_linkage_engine import calc_group_sdg_score, SDG_BU_MATERIALITY
    except ImportError:
        return {"error": "SDG linkage engine not available", "bu_scores": {}, "group_sdg_score": 0, "sdg_heatmap": {}, "alerts": [], "gap_count": 0}

    # Compute group SDG score
    sdg_result = calc_group_sdg_score(bus, gs)

    # Build per-BU detailed scores
    SDG_ICONS = {3: '💊', 6: '💧', 8: '⚡', 9: '💻', 10: '⚖️', 12: '♻️', 15: '🌿'}
    SDG_COLORS = {3: '#4C9F38', 6: '#26BDE2', 8: '#A21942', 9: '#FD6925', 10: '#DD1367', 12: '#BF8B2E', 15: '#56C02B'}
    BU_LABELS = {'pharma': 'Pharma', 'electronics': 'Electronics', 'consumer_goods': 'Consumer Goods', 'software': 'Software'}

    bu_scores = {}
    all_sdg_scores = {}  # sdg_num -> list of scores for heatmap
    all_gaps = []

    for bu in bus:
        # Use bu_id directly (e.g. "pharma") or fall back to deriving from name
        bu_id = bu.get("bu_id") or bu.get("name", "").lower().replace(" ", "_").replace("muressons_", "")
        mat = SDG_BU_MATERIALITY.get(bu_id, {})
        sdg_entries = mat.get("sdgs", [])
        linkage_rule = mat.get("linkage_rule", "")

        sdg_details = []
        bu_total = 0
        for sdg_entry in sdg_entries:
            # Support both dict-based format {sdg, metric_key, scoring, ...}
            # and legacy int-based format (fall back gracefully)
            if isinstance(sdg_entry, dict):
                sdg_num = sdg_entry["sdg"]
                mk = sdg_entry.get("metric_key")
                scoring = sdg_entry.get("scoring", "higher_is_better")
                icon = sdg_entry.get("icon") or SDG_ICONS.get(sdg_num, "🎯")
                color = SDG_COLORS.get(sdg_num, "#888")
            else:
                sdg_num = sdg_entry
                mk = None
                scoring = "higher_is_better"
                icon = SDG_ICONS.get(sdg_num, "🎯")
                color = SDG_COLORS.get(sdg_num, "#888")

            raw_val = bu.get(mk, 50.0) if mk else 50.0

            # Normalize using scoring direction from engine definition
            if scoring == "lower_is_better":
                normalized = max(0, min(100, 100 - raw_val))
            else:
                normalized = max(0, min(100, raw_val))

            sdg_details.append({
                "sdg": sdg_num,
                "icon": icon,
                "color": color,
                "raw_metric": round(raw_val, 2),
                "metric_key": mk,
                "normalized_score": round(normalized, 1),
            })
            bu_total += normalized

            if sdg_num not in all_sdg_scores:
                all_sdg_scores[sdg_num] = []
            all_sdg_scores[sdg_num].append(normalized)

        bu_avg = bu_total / max(len(sdg_entries), 1)
        bu_color = '#10b981' if bu_avg >= 60 else '#f59e0b' if bu_avg >= 40 else '#ef4444'

        # Detect gaps (SDGs scoring below 40)
        gaps = [
            {"sdg": sd["sdg"], "gap_magnitude": round(40 - sd["normalized_score"], 1)}
            for sd in sdg_details if sd["normalized_score"] < 40
        ]
        all_gaps.extend(gaps)

        bu_scores[bu_id] = {
            "sdg_score": round(bu_avg, 1),
            "color": bu_color,
            "sdg_details": sdg_details,
            "gaps": gaps,
            "linkage_rule": linkage_rule,
        }

    # Build SDG heatmap (average score per SDG across all BUs)
    sdg_heatmap = {}
    for sdg_num, scores in all_sdg_scores.items():
        sdg_heatmap[sdg_num] = round(sum(scores) / len(scores), 1) if scores else 0

    # Build alerts
    alerts = []
    for gap in all_gaps:
        severity = "critical" if gap["gap_magnitude"] > 25 else "warning"
        alerts.append({
            "severity": severity,
            "message": f"SDG {gap['sdg']} is {gap['gap_magnitude']:.0f} points below alignment threshold",
        })

    # Materiality map for UI cross-referencing
    materiality_map = {
        bu_id: {"sdgs": mat.get("sdgs", []), "label": BU_LABELS.get(bu_id, bu_id)}
        for bu_id, mat in SDG_BU_MATERIALITY.items()
    }

    return {
        "session_id": session_id,
        "group_sdg_score": sdg_result.get("group_sdg_score", 0),
        "bu_scores": bu_scores,
        "sdg_heatmap": sdg_heatmap,
        "alerts": alerts,
        "gap_count": len(all_gaps),
        "materiality_map": materiality_map,
        "sdg_track_active": bool(flags.get("sdg_track_completed")),
        "sdg_impact_score": flags.get("sdg_impact_score"),
    }


# ─────────────────────────────────────────────────────────────────
# SHADOW BOARD AUDIT — Round 5 Reflective Middleware
# ─────────────────────────────────────────────────────────────────

class ShadowBoardRejectionRequest(BaseModel):
    rejection_target: str  # 'shareholder' | 'activist' | 'auditor'

@router.get(
    "/{session_id}/shadow-board-audit",
    summary="Get Shadow Board Audit personas and state (R5 middleware)",
)
async def get_shadow_board_audit(session_id: str, request: Request):
    """
    Returns the three Shadow Board personas with their scripts and the
    current audit state for this session. Called when Round 5 briefing
    is dismissed to determine if the audit modal should be shown.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from shadow_board_audit import (
        get_shadow_board_personas,
        get_shadow_board_state,
        check_shadow_board_required,
    )

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = latest["global_state"]
    round_number = latest["round_number"]

    return {
        "session_id": session_id,
        "round_number": round_number,
        "audit_required": check_shadow_board_required(round_number, gs),
        "audit_state": get_shadow_board_state(gs),
        "personas": get_shadow_board_personas(),
    }


@router.post(
    "/{session_id}/shadow-board-audit/reject",
    status_code=status.HTTP_200_OK,
    summary="Submit Shadow Board public rejection (R5 middleware)",
)
async def submit_shadow_board_rejection(
    request: Request, session_id: str, body: ShadowBoardRejectionRequest
):
    """
    Records the player's public rejection of one of the three Shadow Board
    personas. This:
    1. Sets hidden flags evaluated at Round 10 for ending pathway cascades
    2. Adjusts the corresponding stakeholder agent's tolerance (-10)
    3. Classifies the firm's strategic archetype
    4. Returns consequence DNA chain for UI traceability
    """
    await _assert_player_owns_session(request, session_id)
    from shadow_board_audit import process_rejection
    from autonomous_agents import AGENT_PROFILES

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    gs = latest["global_state"]
    bus = latest["bu_states"]

    # Check if already completed
    flags = gs.get("active_event_flags", {})
    if flags.get("shadow_board_completed"):
        return {
            "status": "already_completed",
            "message": "Shadow Board Audit has already been completed for this session.",
            "rejection_target": flags.get("shadow_board_rejection"),
            "archetype": flags.get("shadow_board_archetype"),
        }

    # Validate rejection target
    valid_targets = {"shareholder", "activist", "auditor"}
    if body.rejection_target not in valid_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rejection_target '{body.rejection_target}'. "
                   f"Must be one of: {sorted(valid_targets)}",
        )

    # Load autonomous agent state from global_state
    agent_state = gs.get("autonomous_agents")
    if not agent_state:
        # Try to initialize if missing
        try:
            from autonomous_agents import create_initial_agent_state
            agent_state = create_initial_agent_state()
        except Exception:
            agent_state = None

    # Process the rejection
    result = process_rejection(
        rejection_target=body.rejection_target,
        global_state=gs,
        agent_master_state=agent_state,
    )

    # Persist agent state back
    if agent_state:
        gs["autonomous_agents"] = agent_state

    # Persist updated global state
    await db.update_latest_global_state(session_id, gs, bus)

    _log.info(
        f"[shadow-board] Session {session_id}: "
        f"Rejected '{body.rejection_target}' -> "
        f"flag='{result['hidden_flag']['name']}', "
        f"archetype='{result['strategic_archetype']['archetype']}'"
    )

    return result


# ─────────────────────────────────────────────────────────────────
# Stakeholder Negotiation Rooms — player-facing HTTP over the existing
# deal engine (negotiation.py / llm_negotiator.py). Slice 5.
#
# The engine already exists; these routes wire it and enforce the
# per-facilitator capability gate. The gate is a LIVE read on every call
# (never a snapshot copied onto the room at open time), which is exactly
# what makes a super-admin revoke stop an already-open room mid-game —
# mirroring how resolve_max_players is enforced on read, not trusted from
# a stored value.
# ─────────────────────────────────────────────────────────────────

from admin_shared import facilitator_negotiation_granted as _facilitator_negotiation_granted


async def _require_negotiation_open(session_id: str) -> dict:
    """Raise 403 unless BOTH (a) the cohort's negotiation_rooms_enabled is on
    AND (b) the owning facilitator currently holds the grant. Returns the
    session record on success. Re-read per call so a revoke stops a live room."""
    from admin_shared import get_effective_settings, _facilitator_registry

    sess = await db.get_session_info(session_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")

    if get_effective_settings(session_id).get("negotiation_rooms_enabled") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stakeholder Negotiation Rooms are not enabled for this cohort.",
        )

    owner_id = sess.get("facilitator_id")
    owner = next(
        (f for f in _facilitator_registry
         if f.get("facilitator_id") == owner_id and not f.get("deleted_at")),
        None,
    )
    if owner is not None:
        # Real registry owner: capability is DEFAULT-GRANTED since 2026-09-01
        # (EVAL rec 2) — an absent key means granted; only an explicit False
        # (the revoke path) refuses.
        if not _facilitator_negotiation_granted(owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Stakeholder Negotiation Rooms are not enabled for the owning facilitator's profile.",
            )
    elif owner_id not in ("god_mode", "project_admin", "facilitator"):
        # Unknown, non-virtual owner id — refuse rather than fail open.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stakeholder Negotiation Rooms are not enabled for the owning facilitator's profile.",
        )
    return sess


class NegotiationOpenRequest(BaseModel):
    agent_id: str


class NegotiationSayRequest(BaseModel):
    text: str = ""


@router.post("/{session_id}/negotiation/open", summary="Open a Stakeholder Negotiation Room")
async def open_negotiation_room(request: Request, session_id: str, body: NegotiationOpenRequest):
    """Open a room with a stakeholder agent (only takes the meeting once the
    agent is hostile/triggered — enforced by the engine). Capability-gated."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    import negotiation
    await _require_negotiation_open(session_id)

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    gs, bus, rn = latest["global_state"], latest["bu_states"], latest["round_number"]

    result = negotiation.open_room(gs, bus, rn, body.agent_id)
    if "error" in result:
        # not_hostile / meeting_cap / room_already_open / unknown_agent → 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    await db.update_latest_global_state(session_id, gs, bus)
    return result


@router.post("/{session_id}/negotiation/say", summary="Send a turn in the open negotiation room")
async def say_in_negotiation_room(request: Request, session_id: str, body: NegotiationSayRequest):
    """Record the player's line and get the agent's reply. Uses the LLM when a
    key is configured, else the deterministic scripted persona. Capability-gated
    on every call, so a revoke stops the conversation immediately."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    import negotiation
    await _require_negotiation_open(session_id)

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    gs, bus, rn = latest["global_state"], latest["bu_states"], latest["round_number"]

    # Best-effort LLM flavour; any failure (incl. no API key configured, the
    # common case) falls back to the scripted persona so no-key deployments and
    # every error path play identically. negotiate_turn itself never raises and
    # returns None without a key.
    llm_reply = None
    try:
        import llm_negotiator
        log = negotiation.get_negotiation_log(gs)
        room = log.get("active")
        if room:
            agent_id = room["agent_id"]
            grievances = negotiation.compute_grievances(gs, bus, agent_id)
            menu = negotiation.menu_for_agent(gs, rn, agent_id)
            agent_state = ((gs.get("autonomous_agents") or {}).get("agents") or {}).get(agent_id) or {}
            llm_reply = await llm_negotiator.negotiate_turn(
                room, grievances, menu, agent_state, body.text, rn,
            )
    except Exception:
        llm_reply = None

    result = negotiation.say(gs, bus, rn, body.text, llm_reply=llm_reply)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    await db.update_latest_global_state(session_id, gs, bus)
    return result


class NegotiationAcceptRequest(BaseModel):
    concession_id: str


@router.post("/{session_id}/negotiation/accept", summary="Accept a concession in the open negotiation room")
async def accept_in_negotiation_room(request: Request, session_id: str, body: NegotiationAcceptRequest):
    """Apply ONE whitelisted concession from the agent's live menu — the only
    path that mutates state (treasury, reputation, governance/burnout, promises).
    The frontend (NegotiationRoom.js) has always POSTed here; the route was
    missing, so the Accept button 404'd and a paid-for meeting could never
    conclude in a deal. Same ownership + capability gating as /open and /say,
    re-checked per call so a revoke stops mid-negotiation."""
    await _assert_player_owns_session(request, session_id)
    import negotiation
    await _require_negotiation_open(session_id)

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    gs, bus, rn = latest["global_state"], latest["bu_states"], latest["round_number"]

    result = negotiation.accept_concession(gs, bus, rn, body.concession_id)
    if "error" in result:
        # no_open_room / unknown_concession / not_on_this_agents_menu /
        # one_promised_concession_per_meeting / one_free_action_per_meeting → 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    await db.update_latest_global_state(session_id, gs, bus)
    return result


@router.post("/{session_id}/negotiation/walk-out", summary="Walk out of the open negotiation room")
async def walk_out_of_negotiation_room(request: Request, session_id: str):
    """Close the open room without a (further) deal. Any concessions already
    accepted this meeting stand; walking out with zero deals is recorded as a
    stonewall the agent remembers. The frontend's Walk-out button POSTs here;
    the route was missing, so it 404'd and a room could only ever leak open
    until the round committed."""
    await _assert_player_owns_session(request, session_id)
    import negotiation
    await _require_negotiation_open(session_id)

    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    gs, bus, rn = latest["global_state"], latest["bu_states"], latest["round_number"]

    result = negotiation.walk_out(gs, rn)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    await db.update_latest_global_state(session_id, gs, bus)
    return result


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/round-config/{round_number}
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/round-config/{round_number}",
    summary="Get crisis and options for a specific round",
)
async def get_round_config_endpoint(round_number: int, session_id: str | None = None):
    """
    Returns the crisis definition, decision options, special rules,
    and UI constraints for a round.
    Used by the frontend to populate the DecisionModal.
    
    If session_id is provided, returns paradigm-specific config
    (e.g. SDG or Healthcare) when applicable.
    """
    paradigm = None
    if session_id:
        try:
            state = await db.get_session_info(session_id)
            if state:
                paradigm = state.get("decision_paradigm")
                if (paradigm is None or paradigm == "legacy_abc") and state.get("parent_cohort_id"):
                    parent_state = await db.get_session_info(state["parent_cohort_id"])
                    if parent_state:
                        paradigm = parent_state.get("decision_paradigm")
        except Exception as e:
            _log.warning(f"[WARN] Error fetching session paradigm for round-config: {e}")
            pass

    # Select the correct config based on paradigm
    if paradigm == "un_sdg":
        from sdg_configs import get_sdg_round_config
        cfg = get_sdg_round_config(round_number)
    elif paradigm == "healthcare":
        from healthcare_configs import get_healthcare_round_config
        cfg = get_healthcare_round_config(round_number)
    elif paradigm == "brsr_ngrbc":
        # VAL-06 / WP-27: the BRSR track ships its own ten rounds (crisis,
        # options, pillar map); the cockpit used to be handed the legacy
        # round here while the engine (now) runs the BRSR branch.
        from side_tracks.brsr_ngrbc.configs import get_brsr_round_config
        cfg = get_brsr_round_config(round_number)
    else:
        cfg = get_round_config(round_number)

    # ── Ending Pathway: overlay R10 crisis/options if non-default ──
    ending_pathway = None
    if round_number == 10 and session_id and paradigm not in ("un_sdg", "healthcare", "brsr_ngrbc"):
        try:
            latest = await db.fetch_latest_state(session_id)
            if latest:
                ending_pathway = latest.get("global_state", {}).get(
                    "active_event_flags", {}
                ).get("ending_pathway", "activist_ultimatum")
            if ending_pathway and ending_pathway not in ("activist_ultimatum", ""):
                from ending_pathways import get_pathway_r10_config
                pw_cfg = get_pathway_r10_config(ending_pathway)
                if pw_cfg and cfg:
                    cfg["crisis"] = pw_cfg["crisis"]
                    cfg["options"] = pw_cfg["options"]
                    cfg["special_rules"] = pw_cfg.get("special_rules", cfg.get("special_rules", {}))
        except Exception as e:
            _log.warning(f"[WARN] Error loading pathway R10 config: {e}")

    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration for round {round_number}.",
        )

    # ── ANTI-GAMING: Shuffle option presentation order ────────
    # Randomizes A/B/C labels per session so the letter carries no
    # signal about option quality. Backend logic is unaffected.
    options_out = cfg.get("options", {})
    if session_id and (paradigm or "legacy_abc") in ("legacy_abc", "advanced_climate"):
        try:
            sess_meta = await db.get_session_info(session_id)
            _shuffle_seed = (sess_meta or {}).get("shuffle_seed")
            if _shuffle_seed:
                options_out = shuffle_options_for_display(options_out, _shuffle_seed, round_number)
                options_out = strip_canonical_metadata(options_out)

                # R10 synergy gate: apply disabled state to whichever display
                # position now holds the "Resist & Integrate" option
                if round_number == 10:
                    try:
                        latest_state = await db.fetch_latest_state(session_id)
                        if latest_state:
                            _synergy = latest_state["global_state"].get("synergy_multiplier", 1.0) * 100
                            for opt_key, opt_val in options_out.items():
                                ui_c = opt_val.get("ui_constraints", {})
                                threshold = ui_c.get("require_synergy_above")
                                if threshold is not None and _synergy <= threshold:
                                    opt_val["disabled"] = True
                                    opt_val["disabled_reason"] = (
                                        f"Requires Synergy Score > {threshold} (current: {_synergy:.0f})"
                                    )
                    except Exception as e:
                        _log.warning(f"[WARN] R10 synergy gate check failed: {e}")
        except Exception as e:
            _log.warning(f"[WARN] Option shuffle failed, serving unshuffled: {e}")

    # Build UI constraints from options for frontend gating
    ui_constraints = {}
    for opt_key, opt_val in options_out.items():
        if isinstance(opt_val, dict) and opt_val.get("ui_constraint"):
            ui_constraints[opt_key] = opt_val["ui_constraint"]

    return {
        "round_number": round_number,
        "title": cfg.get("title"),
        "theme": cfg.get("theme"),
        "crisis": cfg.get("crisis"),
        "options": options_out,
        "special_rules": cfg.get("special_rules", {}),
        "ui_constraints": ui_constraints,
        "paradigm": paradigm or "legacy_abc",
        "ending_pathway": ending_pathway,
        "options_shuffled": bool(session_id),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/pillar-config/{round_number}
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/pillar-config/{round_number}",
    summary="Get strategic pillar options for a specific round (multi-toggles mode)",
)
async def get_pillar_config_endpoint(round_number: int):
    """
    Returns the 5-area strategic pillar options for a round.
    Used by the frontend StrategicPillarsWorkspace in multi_toggles mode.
    """
    cfg = get_pillar_config(round_number)
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pillar configuration for round {round_number}.",
        )

    return {
        "round_number": round_number,
        "title": cfg.get("title"),
        "description": cfg.get("description"),
        "areas": cfg.get("areas", {}),
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/paradigm
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/paradigm",
    summary="Get the decision paradigm for a session",
)
async def get_session_paradigm(session_id: str, request: Request):
    """Returns which decision paradigm (legacy_abc or multi_toggles) a session uses.
    Falls back to the parent cohort's paradigm for child player sessions."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found.")
    paradigm = session_info.get("decision_paradigm", "legacy_abc")
    # If this is a child player session, inherit from parent cohort
    if paradigm == "legacy_abc" and session_info.get("parent_cohort_id"):
        parent_info = await db.get_session_info(session_info["parent_cohort_id"])
        if parent_info:
            paradigm = parent_info.get("decision_paradigm", "legacy_abc")
    return {
        "session_id": session_id,
        "decision_paradigm": paradigm,
        "paradigm_locked": bool(session_info.get("paradigm_locked", False)),
    }


# ─────────────────────────────────────────────────────────────────
# PUT /api/simulations/{session_id}/paradigm
# ─────────────────────────────────────────────────────────────────

class UpdateParadigmRequest(BaseModel):
    decision_paradigm: str  # 'legacy_abc', 'multi_toggles', or 'advanced_climate'

@router.put(
    "/{session_id}/paradigm",
    summary="Update the decision paradigm for a session",
)
async def update_session_paradigm(request: Request, session_id: str, body: UpdateParadigmRequest, _guard: None = Depends(require_facilitator)):
    """Set the decision paradigm for a session. Propagates to child player sessions."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    if body.decision_paradigm not in ("legacy_abc", "multi_toggles", "advanced_climate", "healthcare"):
        raise HTTPException(status_code=400, detail="Invalid paradigm. Must be 'legacy_abc', 'multi_toggles', 'advanced_climate', or 'healthcare'.")

    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Once set, the paradigm is locked for this cohort
    if session_info.get("paradigm_locked"):
        raise HTTPException(
            status_code=409,
            detail="Decision paradigm has already been set for this cohort and cannot be changed."
        )

    session_info["decision_paradigm"] = body.decision_paradigm
    session_info["paradigm_locked"] = True

    # Propagate to all child player sessions
    # The healthcare paradigm re-seed rewrites the in-memory BU/global dicts
    # directly. That is a MEMORY-STORE-ONLY operation: under Postgres, round state
    # lives in tables, so these dict writes are a silent no-op. Guard on the active
    # backend and skip under Postgres (a durable Postgres re-seed is a follow-up).
    # NOTE: the former `un_sdg` branch was dead code — un_sdg fails the paradigm
    # validation at the top of this endpoint, so it could never run; dropped.
    try:
        import copy
        from admin_shared import _in_memory_backend_active
        if _in_memory_backend_active():
            # tripwire-allow-block-start
            from database_memory import _sessions, _bu_states, _global_states, _load_seed
            seed = None
            if body.decision_paradigm == "healthcare":
                seed = _load_seed(industry="healthcare")
                _bu_states[session_id] = {1: copy.deepcopy(seed["business_units"])}
                states = _global_states.get(session_id, [])
                if states:
                    states[-1]["corporate_treasury"] = seed["global_state"]["corporate_treasury_usd"]
                    states[-1]["political_capital"] = seed["global_state"].get("political_capital", 50.0)
                    states[-1]["community_trust_score"] = seed["global_state"].get("community_trust_score", 50.0)
                    states[-1]["global_emissions_intensity"] = seed["global_state"].get("global_emissions_intensity", 60.0)

            for sid, sdata in _sessions.items():
                if sdata.get("parent_cohort_id") == session_id:
                    sdata["decision_paradigm"] = body.decision_paradigm
                    if body.decision_paradigm == "healthcare":
                        _bu_states[sid] = {1: copy.deepcopy(seed["business_units"])}
            # tripwire-allow-block-end
    except ImportError:
        pass

    return {
        "status": "success",
        "session_id": session_id,
        "decision_paradigm": body.decision_paradigm,
    }


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/materiality/commission-panel
# ─────────────────────────────────────────────────────────────────

_PANELS_COMMISSIONED_KEY = "materiality_panels_commissioned"


def _commissioned_panels(global_state: dict) -> set:
    """Panel groups this session has commissioned (recorded server-side).

    Stored as a {group: True} dict so the flags pack/unpack round-trip keeps it
    (both stores fold unknown top-level keys into active_event_flags) without
    _collect_flags_from_state reading the group names as active flags — a list
    there would."""
    raw = global_state.get(_PANELS_COMMISSIONED_KEY)
    if raw is None:
        raw = (global_state.get("active_event_flags") or {}).get(_PANELS_COMMISSIONED_KEY)
    if isinstance(raw, dict):
        return {str(g) for g, on in raw.items() if on}
    if isinstance(raw, (list, tuple, set)):
        return {str(g) for g in raw}
    return set()


class PanelCommissionRequest(BaseModel):
    group: str
    bu_id: str | None = None


@router.post(
    "/{session_id}/materiality/commission-panel",
    tags=["Simulation"],
    summary="Commission one stakeholder panel group for the R2 matrix",
)
async def commission_materiality_panel(request: Request, session_id: str, body: PanelCommissionRequest):
    """F-10 / ACC-2 (audit 2026-09-04): the per-group quadrant recommendations
    used to ride along in GET /api/admin/materiality-config for everyone, and
    the `experts` column is always correct — the R2 answer key, free. They are
    now served here, one group per call, to the session's owner, and the
    commission is recorded on the session so the group's fee is charged at
    submission (POST /materiality) even if the client omits it.

    Idempotent: commissioning a group twice returns the same hints and charges
    once. The dictionary resolves through the same chain the matrix displays
    and the submit scores against (bu_id → cohort override → pack → region →
    BU; else cohort sandbox; else global)."""
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    from round2_csrd import ROUND_2_DEFAULT_CONFIG, compute_panel_recommendations
    groups = ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"].get("groups", {})
    if body.group not in groups:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown panel group {body.group!r}; expected one of {sorted(groups)}.",
        )
    gs = latest["global_state"]
    scoped = await _hydrate_scope_from_session(gs, session_id)
    if body.bu_id:
        from materiality_packs import resolve_session_bu_config
        mat_config = resolve_session_bu_config(scoped, body.bu_id)
    elif "materiality_dictionary_override" in scoped:
        mat_config = scoped["materiality_dictionary_override"]
    else:
        mat_config = mat_db.get_current_config()
    recs = compute_panel_recommendations(mat_config.get("issues", []))

    commissioned = _commissioned_panels(gs)
    if body.group not in commissioned:
        commissioned.add(body.group)
        gs[_PANELS_COMMISSIONED_KEY] = {g: True for g in sorted(commissioned)}
        try:
            await db.update_latest_global_state(session_id, gs, latest["bu_states"])
        except Exception as exc:  # never lose the hint over a persistence hiccup
            _log.warning(f"[MATERIALITY] could not record panel commission for {session_id[:8]}: {exc}")
    return {
        "group": body.group,
        "commissioned": sorted(commissioned),
        "fee_usd": groups[body.group].get("fee_usd", 750_000),
        "recommendations": {iid: g.get(body.group) for iid, g in recs.items() if g.get(body.group)},
    }


# POST /api/simulations/{session_id}/materiality
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/materiality",
    response_model=MaterialitySubmissionResponse,
    summary="Submit Double Materiality matrix and receive capital allocation",
)
async def submit_materiality_matrix(request: Request, session_id: str, body: MaterialitySubmissionRequest):
    """
    1. Fetches current state and dynamic materiality config.
    2. If bu_id is provided (Strategic Pillars mode), loads BU-specific dictionary.
    3. Deducts stakeholder panel fee if used (tiered: 1-4 issues=$250K each; 5-8=$500K each).
    4. Validates CFO Rule: NO non-material (Q2/Q3/Q4) issues allowed in Q1 Top Right.
    5. Calculates M_acc (valid Q1 issues placed correctly / Total True Q1).
    6. Applies Option C budget clawback (40%) if materiality_ignored flag is active.
    7. Allocates disclosure_investment_budget for Q2 issues placed correctly.
    8. Persists the new treasury state and emits ESRS debrief card.
    """
    await _assert_player_owns_session(request, session_id)
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    global_state = current["global_state"]
    bu_states = current["bu_states"]

    # FIX BUG-8 (double-materiality "loops twice" ROOT CAUSE): idempotency guard.
    #
    # Two coupled defects made a duplicate submit loop forever:
    #   1. The marker/replay data were stored as TOP-LEVEL global_state keys.
    #      The memory backend persists via an explicit allow-list, so those keys
    #      were silently dropped there (guard never fired → double-deduction),
    #      while Postgres kept them (guard fired). We now store them inside
    #      `active_event_flags`, the one bag that round-trips through BOTH
    #      backends (Postgres packs it dynamically; the memory store persists it
    #      by reference) — so the guard behaves identically everywhere.
    #   2. When the guard DID fire (Postgres/prod), it returned a bare
    #      {"status": "already_submitted", ...} dict missing both required fields
    #      of the strict response_model → FastAPI raised ResponseValidationError
    #      → generic 500 ("An internal server error occurred"). The frontend
    #      surfaced that 500 through the CFO "Force Override" modal, whose
    #      override RE-SUBMITTED → guard again → another 500: the deterministic
    #      loop the player saw. The guard now REPLAYS the committed result as a
    #      schema-valid response, so a duplicate submit is a clean no-op.
    _mat_key = f"materiality_submitted_r{global_state.get('round_number', 2)}"
    if body.bu_id:
        _mat_key += f"_{body.bu_id}"
    _idem_store = (global_state.get("active_event_flags", {}) or {}).get("_materiality_idempotency", {}) or {}
    if _mat_key in _idem_store:
        _rec = _idem_store[_mat_key] or {}
        return MaterialitySubmissionResponse(
            success=True,
            allocated_budget=int(_rec.get("allocated_budget", 0) or 0),
            corporate_treasury=global_state.get("corporate_treasury", 0),
            message="Materiality already submitted this round — showing your committed result.",
            debrief=_rec.get("debrief"),
        )

    # Load dynamic Materiality Config
    # Priority: 1) BU-specific dict (if bu_id), 2) Cohort sandbox, 3) Global
    # Parity gap #4 healing: older Postgres-created rounds carry no
    # region/vertical scope — hydrate from the session record so uploaded
    # regional matrices resolve for existing cohorts too.
    global_state = await _hydrate_scope_from_session(global_state, session_id)
    if body.bu_id:
        # The chain (explicit per-BU cohort override → pack → region → BU
        # matrix) lives in materiality_packs.resolve_session_bu_config so the
        # DISPLAY endpoint resolves IDENTICALLY — the player must be scored
        # against the dictionary they were shown.
        from materiality_packs import resolve_session_bu_config
        mat_config = resolve_session_bu_config(global_state, body.bu_id)
    elif "materiality_dictionary_override" in global_state:
        mat_config = global_state["materiality_dictionary_override"]
    else:
        mat_config = mat_db.get_current_config()

    all_issues = mat_config.get("issues", [])
    from round2_csrd import ROUND_2_DEFAULT_CONFIG
    panel_config = ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"]

    # ── R1 Intelligence Modulation ─────────────────────────────────────────────
    # If electronics_blindspot flag is active (R1A Surface Scan chosen),
    # degrade hover_description for electronics_sensitive issues.
    # The frontend receives this via the issues list — we annotate them here
    # so the materiality config endpoint can surface the degraded descriptions.
    prev_flags = global_state.get("active_event_flags", {})
    has_blindspot = "electronics_blindspot" in _collect_flags_from_state(prev_flags)
    if has_blindspot:
        all_issues = [
            {**issue, "hover_description": issue.get("blindspot_description") or issue["hover_description"]}
            if issue.get("electronics_sensitive")
            else issue
            for issue in all_issues
        ]
        global_state["r1_blindspot_active_in_r2"] = True

    # ── R1 Stakeholder Voice Boost ─────────────────────────────────────────────
    # If player correctly classified a stakeholder in R1 Mendelow matrix,
    # mark that stakeholder's linked issues as "stakeholder_confirmed" so
    # the frontend can show a confirmation badge on those issue chips.
    # FIX C1/C18/C22: Keys match stakeholder_map.py IDs, all 10 mapped.
    stakeholder_accuracy = global_state.get("stakeholder_accuracy", {})
    stakeholder_boosts = set()
    stakeholder_boost_map = {
        "activist_fund": ["shareholder_activism", "executive_compensation"],
        "eu_regulators": ["csrd_compliance", "carbon_disclosure", "scope3_reporting"],
        "local_communities": ["water_scarcity", "plastic_packaging", "philanthropy"],
        "tier3_miners": ["tier3_labor", "living_wage", "conflict_minerals"],
        "factory_employees": ["ai_bias", "employee_volunteering", "just_transition"],
        "syndicate_banks": ["green_bonds", "esg_lending_criteria"],
        "national_gov": ["carbon_tax", "environmental_fines"],
        "cafeteria_vendors": [],
        "gen_public": [],
        "local_media": [],
    }
    for stakeholder_key, issue_ids in stakeholder_boost_map.items():
        # Check if this stakeholder was correctly placed in "Manage Closely" quadrant
        if stakeholder_accuracy.get(stakeholder_key) == "manage_closely":
            stakeholder_boosts.update(issue_ids)
    global_state["stakeholder_boosted_issues"] = list(stakeholder_boosts)

    # Pre-compute the target Q1 (High Fin + High Impact) through the round's
    # single classifier (F-6 follow-up). For every shipped dictionary this is
    # the same string-label rule as before — correct_quadrant_v2 falls back to
    # financial_impact/societal_impact — but capital release and full-quadrant
    # accuracy can no longer drift apart, and issues missing a label no longer
    # raise KeyError.
    q1_target_issue_ids = {
        issue["id"] for issue in all_issues
        if correct_quadrant_v2(issue) == "q1"
    }

    total_budget = ROUND_2_DEFAULT_CONFIG["round_2_config"]["total_materiality_budget"]
    disclosure_budget = ROUND_2_DEFAULT_CONFIG["round_2_config"]["disclosure_investment_budget"]

    # ── Stakeholder Panel Survey Fee — Multi-Group Model ─────────────────────
    # New: each group is commissioned independently at flat $750K each.
    # Legacy single-survey path (consultant_used + panel_issue_count) is still
    # supported for backward compatibility with existing saved sessions.
    from round2_csrd import compute_panel_recommendations
    panel_fee = 0
    # F-10 / ACC-2: a panel commissioned through /materiality/commission-panel
    # is recorded on the session; it is charged whether or not the client
    # lists it (reading the hints, then omitting the group, was free).
    _recorded_panels = _commissioned_panels(global_state)
    _claimed_panels = list(body.panel_groups_commissioned or [])
    _all_panels = _claimed_panels + [g for g in sorted(_recorded_panels) if g not in _claimed_panels]
    if _all_panels:
        group_configs = panel_config.get("groups", {})
        valid_groups = [g for g in _all_panels if g in group_configs]
        panel_fee = sum(
            group_configs[g].get("fee_usd", 750_000) for g in valid_groups
        )
        global_state["corporate_treasury"] -= panel_fee
        global_state["stakeholder_panel_fee_paid"] = panel_fee
        global_state["stakeholder_panel_groups_commissioned"] = valid_groups
        # Tag panel fee as a CSF deduction so InvestmentMatrix can surface it
        global_state["panel_fee_deducted_from_csf"] = panel_fee
    elif body.consultant_used:
        # Legacy path: single tiered survey
        panel_issue_count = max(1, min(8, body.panel_issue_count))
        tier_break = panel_config.get("tier_break", 4)
        base_fee = panel_config.get("base_fee_per_issue_usd", 250_000)
        extended_fee = panel_config.get("extended_fee_per_issue_usd", 500_000)
        if panel_issue_count <= tier_break:
            panel_fee = panel_issue_count * base_fee
        else:
            panel_fee = (tier_break * base_fee) + ((panel_issue_count - tier_break) * extended_fee)
        global_state["corporate_treasury"] -= panel_fee
        global_state["stakeholder_panel_fee_paid"] = panel_fee
        global_state["stakeholder_panel_issues_rated"] = panel_issue_count
        global_state["panel_fee_deducted_from_csf"] = panel_fee

    # ── CFO Override Validation (Strict) ──────────────────────────────────────
    q1_submission = set(body.matrix_submission.quadrant_1_top_right)
    invalid_q1_issues = q1_submission - q1_target_issue_ids

    if invalid_q1_issues:
        if body.force_override_cfo:
            # Executive override: penalize reputation (−10, doubled from −5 to reflect governance gravity)
            global_state["group_reputation"] = max(0, global_state.get("group_reputation", 50) - 10)
            global_state["cfo_override_used_r2"] = True
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "CFO Override: Proposed initiatives include non-material or low-impact issues. "
                    "Budget allocation denied per Double Materiality framework. "
                    "Review your Quadrant 1 classification and resubmit."
                )
            )

    # ── Accuracy Scoring & Capital Release ────────────────────────────────────
    if not q1_target_issue_ids:
        m_acc = 1.0
    else:
        correct_q1_count = len(q1_submission.intersection(q1_target_issue_ids))
        m_acc = correct_q1_count / len(q1_target_issue_ids)

    allocated_budget = int(total_budget * m_acc)

    # ── Option C clawback: NOT applied here (F-1/F-3) ────────────────────────
    # The A/B/C governance choice arrives at end-of-round commit, after this
    # handler has already run, so a submit-time clawback could never fire — and
    # under the old debit semantics it would have REFUNDED the offending team.
    # round_logic._post_r2_materiality applies it against the released fund.
    clawback_applied = 0

    # ── Full-Quadrant Accuracy — one classifier (F-6) ─────────────────────────
    # Scoring uses round2_csrd.correct_quadrant_v2: dual-axis numeric scoring
    # only when all four axis-specific fields are present, otherwise the same
    # string labels that build q1_target_issue_ids. One rule, not two.
    _correct_quadrant_v2 = correct_quadrant_v2

    # Adjacent-quadrant map for ambiguous partial credit
    _ADJACENT_Q = {
        "q1": {"q2", "q3"},  # shares both Q2 (high impact) and Q3 (high financial) borders
        "q2": {"q1", "q4"},
        "q3": {"q1", "q4"},
        "q4": {"q2", "q3"},
    }

    issue_lookup = {i["id"]: i for i in all_issues}
    total_placed = 0.0
    correct_placed = 0.0
    q2_disclosure_correct = 0

    # Build per-issue score breakdown for debrief transparency
    issue_score_breakdown: dict[str, dict] = {}

    for qname in ("q1", "q2", "q3", "q4"):
        submission_attr = {
            "q1": "quadrant_1_top_right",
            "q2": "quadrant_2_top_left",
            "q3": "quadrant_3_bottom_right",
            "q4": "quadrant_4_bottom_left",
        }[qname]
        placed_ids = getattr(body.matrix_submission, submission_attr, [])
        for iid in placed_ids:
            issue = issue_lookup.get(iid)
            if not issue:
                continue  # custom factor — skip accuracy check
            total_placed += 1
            correct_q = _correct_quadrant_v2(issue)
            sev = issue.get("severity_score")
            like = issue.get("likelihood_score")
            mat_product = (sev * like) if sev and like else None

            is_ambiguous = issue.get("is_ambiguous", False)
            if correct_q == qname:
                credit = 1.0
                correct_placed += credit
                if qname == "q2" and issue.get("disclosure_required"):
                    q2_disclosure_correct += 1
            elif is_ambiguous and qname in _ADJACENT_Q.get(correct_q, set()):
                # Partial credit for ambiguous issues placed in adjacent quadrant
                credit = 0.5
                correct_placed += credit
            else:
                credit = 0.0

            # Build transparency record
            issue_score_breakdown[iid] = {
                "title": issue.get("title", iid),
                "esrs_topic": issue.get("esrs_topic"),
                "severity_score": sev,
                "likelihood_score": like,
                "materiality_product": mat_product,
                "threshold": ESRS_MAT_THRESHOLD,
                "correct_quadrant": correct_q,
                "placed_quadrant": qname,
                "credit": credit,
                "is_ambiguous": is_ambiguous,
                "value_chain_scope": issue.get("value_chain_scope"),
                "time_horizon": issue.get("time_horizon"),
            }

    full_accuracy = (correct_placed / total_placed) if total_placed > 0 else 0.0
    # F-4: threshold and bonus come from round config special_rules — the one
    # place the classroom numbers are declared (80% → +1000 leaderboard points;
    # the previously documented 90%/$2M treasury bonus never existed).
    _r2_rules = (get_round_config(2) or {}).get("special_rules", {})
    _acc_threshold = float(_r2_rules.get("accuracy_threshold_pct", 80)) / 100.0
    accuracy_bonus = 0
    if full_accuracy >= _acc_threshold:
        accuracy_bonus = int(_r2_rules.get("accuracy_bonus_points", 1000))
        global_state["bonus_score"] = global_state.get("bonus_score", 0) + accuracy_bonus

    global_state["materiality_full_accuracy"] = round(full_accuracy * 100, 1)
    global_state["materiality_issue_scores"] = issue_score_breakdown

    # ── Q2 Disclosure Investment Budget ───────────────────────────────────────
    # Players who correctly placed Q2 issues receive the disclosure_investment_budget
    # to cover data collection, assurance, and stakeholder engagement costs.
    # This teaches: impact materiality requires disclosure investment, not capex.
    disclosure_allocated = 0
    if q2_disclosure_correct > 0:
        # Pro-rata: each correct Q2 issue unlocks a portion of disclosure budget.
        # Denominator = disclosure-carrying Q2 issues in the ACTIVE dictionary
        # (the old fixed CSRD_ISSUES denominator made full unlock impossible on
        # any other dictionary); CSRD count kept as a safety fallback.
        from round2_csrd import Q2_DISCLOSURE_ISSUES
        active_q2_disclosure = sum(
            1 for i in all_issues
            if i.get("disclosure_required") and _correct_quadrant_v2(i) == "q2"
        )
        max_q2 = max(active_q2_disclosure or len(Q2_DISCLOSURE_ISSUES), 1)
        disclosure_allocated = int(disclosure_budget * min(1.0, q2_disclosure_correct / max_q2))
        global_state["q2_disclosure_budget_unlocked"] = disclosure_allocated
        global_state["q2_disclosure_message"] = (
            f"📋 ESRS Disclosure Budget: {q2_disclosure_correct} Q2 impact-material issues correctly "
            f"identified. ${disclosure_allocated:,} disclosure investment budget credited to your "
            f"ring-fenced materiality fund for data collection, assurance, and stakeholder "
            f"engagement (ESRS S1/S2/E1-E5)."
        )

    # ── F-3: Capital release → ring-fenced materiality fund (§5.1 option a) ──
    # The old behaviour debited treasury by the released amount and nothing
    # ever consumed it: higher accuracy was strictly more expensive and bought
    # nothing the model reads. The release is now real — the amount becomes a
    # restricted balance, spendable only as ESG CapEx on the issues identified
    # (engine.process_tick draws it down before the loan/interest machinery,
    # mirroring the Advanced Climate green fund). Capital for MISSED issues is
    # never released: it is simply unavailable, not returned to treasury —
    # missing an issue means you cannot fund its mitigation.
    fund_balance = float(allocated_budget + disclosure_allocated)
    global_state["materiality_restricted_fund"] = fund_balance
    global_state["materiality_fund_released"] = float(allocated_budget)
    global_state["materiality_budget_allocated"] = list(q1_submission)

    # Store BU context if applicable
    if body.bu_id:
        global_state["materiality_bu_id"] = body.bu_id

    # Unlock the module gate
    global_state["csrd_completed"] = True

    # ── Materiality tier flags — NOT set here (F-2) ───────────────────────────
    # materiality_aligned / materiality_partial / materiality_ignored are owned
    # exclusively by round_logic._post_r2_materiality, which runs at end-of-round
    # commit when the A/B/C governance choice exists. Writing any of them at
    # panel-submit time re-creates the two-writer defect where either path alone
    # granted the +0.10 M_R premium.

    # ── ESRS Debrief Card ─────────────────────────────────────────────────────
    # Post-submission regulatory literacy card explaining the scoring rationale.
    q1_correct_ids = list(q1_submission.intersection(q1_target_issue_ids))
    q1_missed_ids  = list(q1_target_issue_ids - q1_submission)

    # ── ESRS Assurance Readiness Indicator ────────────────────────────────────
    # Synthesise a 1-4 star readiness score from four ESRS governance signals.
    # This teaches students that CSRD assurance depends on process quality, not
    # just which issues they identified.
    _assurance_signals = {
        "q1_recall":         len(q1_correct_ids) >= (len(q1_target_issue_ids) * 0.8),  # ≥80% Q1 recall
        # Provisional: the A/B/C governance choice does not exist until end-of-round
        # commit — _post_r2_materiality finalises this signal (and the star count).
        "governance_board":  True,
        "q2_disclosed":      q2_disclosure_correct > 0,                                 # Impact material issues disclosed
        "ambiguous_handled": any(                                                         # Ambiguous issues placed thoughtfully
            v.get("is_ambiguous") and v.get("credit", 0) >= 0.5
            for v in issue_score_breakdown.values()
        ),
    }
    assurance_stars = sum(_assurance_signals.values())  # 0-4
    assurance_labels = ASSURANCE_LABELS  # shared with round_logic._post_r2_materiality
    assurance_label, assurance_detail = assurance_labels[assurance_stars]

    global_state["r2_esrs_debrief"] = {
        "esrs_reference": "ESRS 1 §1.30-1.51 — Double Materiality Threshold (Severity × Likelihood)",
        "q1_correct":     q1_correct_ids,
        "q1_missed":      q1_missed_ids,
        "scoring_rationale": (
            "Scoring engine: impact materiality and financial materiality are assessed "
            "SEPARATELY (ESRS 1). High on both axes = Q1 (doubly material); high impact "
            f"only = Q2; high financial only = Q3. "
            f"Your Q1 recall: {len(q1_correct_ids)}/{len(q1_target_issue_ids)} issues correctly prioritised "
            f"({round(full_accuracy * 100, 1)}% weighted accuracy including partial credit for ambiguous placements)."
        ),
        "q2_insight": (
            "Q2 issues (High Impact / Low Financial) are not capital-intensive, but "
            "ESRS S1, S2, and E1-E5 require mandatory disclosure. They require "
            "disclosure investment (data collection, assurance) — not silence."
        ),
        "spectrum_note": (
            "The 2×2 matrix is a pedagogical simplification. Real ESRS practice uses "
            "continuous severity (Scale × Scope × Irremediability) × Likelihood scoring "
            "with explicit time-horizon tagging — which the severity badges on each issue chip now reflect."
        ),
        "time_horizon_note": (
            "Time horizons matter: Short-term issues (ST) demand immediate capital allocation; "
            "long-term issues (LT) require transition plan disclosure. Both can be Q1 — but "
            "your ESRS reporting must distinguish them in the materiality table."
        ),
        "full_accuracy_pct":      round(full_accuracy * 100, 1),
        "q2_disclosure_allocated": disclosure_allocated,
        "materiality_fund_released": allocated_budget,
        "materiality_fund_balance":  fund_balance,
        # Finalised by _post_r2_materiality once the governance choice exists.
        "clawback_applied":        clawback_applied,
        # New: per-issue score transparency
        "issue_score_breakdown":   issue_score_breakdown,
        # New: ESRS Assurance Readiness
        "assurance_stars":         assurance_stars,
        "assurance_label":         assurance_label,
        "assurance_detail":        assurance_detail,
        "assurance_signals":       _assurance_signals,
        "esrs_mat_threshold":      12,
    }

    # Finalise the debrief (panel-fee breakdown for the success modal) BEFORE it
    # is snapshotted into the idempotency record and persisted, so a replay
    # returns the identical, complete debrief.
    global_state["r2_esrs_debrief"]["panel_fee_paid"] = panel_fee
    global_state["r2_esrs_debrief"]["panel_groups_commissioned"] = (
        global_state.get("stakeholder_panel_groups_commissioned", [])
    )

    # Idempotency marker + replay bundle live INSIDE active_event_flags (the one
    # bag that round-trips through both backends). A duplicate submit replays
    # this exact result instead of re-deducting or 500-ing. Kept under a single
    # nested dict so it never leaks into flag-name collectors.
    _mat_flags = global_state.setdefault("active_event_flags", {})
    _idem = _mat_flags.setdefault("_materiality_idempotency", {})
    _idem[_mat_key] = {
        "allocated_budget": int(allocated_budget),
        "debrief": global_state["r2_esrs_debrief"],
    }

    # Persist once, after all state (treasury, flags, debrief, marker) is final.
    await db.update_latest_global_state(session_id, global_state, bu_states)

    msg_parts = [f"Materiality Matrix accepted. Accuracy: {round(full_accuracy*100)}%."]
    msg_parts.append(
        f"${allocated_budget:,} released into your ring-fenced materiality fund "
        f"(spendable as ESG CapEx on the issues you identified)."
    )
    if accuracy_bonus:
        msg_parts.append("+1000 bonus points!")
    if disclosure_allocated:
        msg_parts.append(f"Q2 disclosure budget: +${disclosure_allocated:,} credited to the fund.")

    return MaterialitySubmissionResponse(
        success=True,
        allocated_budget=allocated_budget,
        corporate_treasury=global_state["corporate_treasury"],
        message=" ".join(msg_parts),
        debrief=global_state["r2_esrs_debrief"],
    )


def _collect_flags_from_state(flags_dict: dict) -> set:
    """Thin helper to collect flag names from the active_event_flags dict."""
    result = set()
    for key, val in flags_dict.items():
        if isinstance(val, list):
            result.update(str(v) for v in val)
        elif isinstance(val, bool) and val:
            result.add(key)
        elif isinstance(val, str):
            result.add(val)
    return result




# ─────────────────────────────────────────────────────────────────
# Stakeholder Power-Interest Grid (Round 1 Minigame)
# ─────────────────────────────────────────────────────────────────

from stakeholder_map import evaluate_stakeholder_map, get_stakeholder_list, get_master_config, evaluate_stakeholder_map_for_session, get_stakeholders_for_session


async def _hydrate_scope_from_session(global_state: dict, session_id: str) -> dict:
    """Backfill industry_vertical / region_id from the SESSION record when the
    round state lacks them.

    HEALING half of parity gap #4: Postgres create_session did not seed these
    two flags (the memory twin did), so every cohort created under Postgres has
    round rows with no vertical/region scope — and admin-uploaded vertical and
    regional Excel configs (stakeholders AND materiality) silently never
    reached play. Seeding is now fixed for NEW sessions; this backfill makes
    EXISTING cohorts resolve correctly without rewriting their stored rounds.
    The session record has always carried both values in both backends.
    """
    try:
        _SCOPE_KEYS = ("industry_vertical", "region_id", "assigned_bu",
                       "stakeholder_pack_id", "materiality_pack_id")
        need = [k for k in _SCOPE_KEYS
                if not (global_state.get(k)
                        or (global_state.get("active_event_flags") or {}).get(k))]
        if not need:
            return global_state
        sess = await db.get_session_info(session_id) or {}
        # A player's sub-session may not carry cohort-level values (packs are
        # set on the PARENT cohort) — walk up once. get_session_info is a
        # parity API; parent_cohort_id exists in both backends.
        parent = None
        if sess.get("parent_cohort_id"):
            try:
                parent = await db.get_session_info(str(sess["parent_cohort_id"])) or {}
            except Exception:
                parent = None
        # Cohort-settings fallback: pack ids are also COHORT_OVERRIDABLE_KEYS,
        # so a pack applied through the settings fan-out resolves too.
        eff = {}
        try:
            from admin_shared import get_effective_settings
            eff = get_effective_settings(session_id) or {}
        except Exception:
            eff = {}
        for k in need:
            for source in (sess, parent or {}, eff):
                v = source.get(k)
                v = v.strip() if isinstance(v, str) else v
                if v:
                    global_state[k] = v
                    break
    except Exception:
        pass  # resolution falls back to defaults exactly as before
    return global_state


class StakeholderMapSubmission(BaseModel):
    """Player's mapping of stakeholder IDs to quadrant IDs."""
    mapping: dict[str, str]  # {stakeholder_id: quadrant_id}


@router.get(
    "/stakeholder-map/stakeholders",
    tags=["Simulation"],
    summary="Get stakeholder list for the drag-and-drop bank",
)
async def get_stakeholders(session_id: str = None):
    """Returns the stakeholder bank. If session_id is provided and has
    BU substitutions, returns the vertical-specific stakeholder set."""
    if session_id:
        latest = await db.fetch_latest_state(session_id)
        if latest:
            gs = await _hydrate_scope_from_session(latest["global_state"], session_id)
            stakeholders = get_stakeholders_for_session(gs)
            return {"stakeholders": [
                {
                    "id": s["id"], "name": s["name"], "icon": s["icon"],
                    "description": s["description"],
                    "intel_dossier": s.get("intel_dossier", []),
                }
                for s in stakeholders
            ]}
    return {"stakeholders": get_stakeholder_list()}


@router.post(
    "/{session_id}/stakeholder-map",
    tags=["Simulation"],
    summary="Submit stakeholder power-interest grid mapping",
)
async def submit_stakeholder_map(request: Request, session_id: str, body: StakeholderMapSubmission):
    await _assert_player_owns_session(request, session_id)
    # Evaluate against master (C4: graduated scoring, C12: treasury penalty)
    # Session-aware: uses vertical stakeholders if BU substitutions are active
    latest_for_eval = await db.fetch_latest_state(session_id)
    if latest_for_eval:
        # Scoring must see the SAME scoped stakeholder set the bank displayed —
        # scoring against the default set while the player placed an uploaded
        # vertical set would mark correct placements wrong.
        result = evaluate_stakeholder_map_for_session(
            body.mapping,
            await _hydrate_scope_from_session(latest_for_eval["global_state"], session_id),
        )
    else:
        result = evaluate_stakeholder_map(body.mapping)

    latest = await db.fetch_latest_state(session_id)
    if latest:
        gs = latest["global_state"]
        gs["bonus_score"] = gs.get("bonus_score", 0) + result["points_awarded"]
        gs["stakeholder_map_completed"] = True
        gs["stakeholder_map_accuracy"] = result["accuracy_percentage"]
        # C18: Persist per-stakeholder accuracy for R2 Voice Boost
        gs["stakeholder_accuracy"] = body.mapping  # {stakeholder_id: quadrant_id}
        # C12: Treasury penalty for poor analysis (<60%)
        if result.get("treasury_penalty", 0) != 0:
            gs["corporate_treasury"] = gs.get("corporate_treasury", 0) + result["treasury_penalty"]
            gs["stakeholder_penalty_applied"] = result["treasury_penalty"]
        # C4: Reputation penalty for failing (<80%)
        if result.get("reputation_penalty", 0) != 0:
            gs["group_reputation"] = max(0, gs.get("group_reputation", 50) + result["reputation_penalty"])
        await db.update_latest_global_state(session_id, gs, latest["bu_states"])

    return {
        "accuracy_percentage": result["accuracy_percentage"],
        "passed": result["passed"],
        "points_awarded": result["points_awarded"],
        "correct_count": result["correct_count"],
        "total_count": result["total_count"],
        "details": result["details"],
        "master_mapping": result["master_mapping"],
        "treasury_penalty": result.get("treasury_penalty", 0),
        "reputation_penalty": result.get("reputation_penalty", 0),
        "scoring_tier": result.get("scoring_tier", ""),
        "urgency_debrief": result.get("urgency_debrief", []),
        "engagement_tactics": result.get("engagement_tactics", []),
    }


@router.get(
    "/stakeholder-map/master",
    tags=["Admin"],
    summary="God Mode: Get full master stakeholder config",
)
async def get_stakeholder_master(_g: None = Depends(require_facilitator)):
    # F-10 (audit 2026-09-04): the R1 answer key (each stakeholder's
    # correct_quadrant and per-tactic correct flags) — facilitators only.
    return get_master_config()


# ─────────────────────────────────────────────────────────────────
# Player Password Change
# ─────────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    player_id: str
    old_password: str
    new_password: str

@router.post(
    "/change-password",
    tags=["Simulation"],
    summary="Allow a player to change their password",
)
async def change_password(request: Request, body: ChangePasswordRequest):
    # F-24 (launch audit 2026-09-01): this path verified the old password with NO
    # rate limit, so it was an unthrottled brute-force oracle that bypassed the
    # login limiter. Same per-identity + per-IP policy as /player-login.
    _check_rate_limit(request, "player_login", identity=body.player_id)
    _check_rate_limit(request, "player_login")
    try:
        from admin_shared import _player_registry
    except ImportError:
        raise HTTPException(500, "Player registry not available")

    player = next((p for p in _player_registry if p.get("player_id") == body.player_id), None)
    if not player:
        raise HTTPException(404, "Player ID not found")

    if not await _verify_pw_async(body.old_password, player.get("password", "")):  # F-30
        raise HTTPException(403, "Current password is incorrect")

    if len(body.new_password.strip()) < 8:
        raise HTTPException(400, "New password must be at least 8 characters")

    player["password"] = await _hash_pw_async(body.new_password.strip())  # F-30
    # Clear the forced-change flag now that the player has set a personal password
    player["must_change_password"] = False
    # The player owns their password now — the revealable temp credential must
    # stop existing on the registry record too (the registered_players copy is
    # cleared below). Otherwise it would keep surfacing on facilitator roster reads.
    player.pop("plaintext_password", None)
    player.pop("temp_password", None)

    # Persist the cleared flag to session metadata so it survives server restarts
    try:
        import database as _db
        session_id = player.get("session_id", "")
        if session_id:
            sess = await _db.get_session_info(session_id)
            if sess:
                for rp in sess.get("registered_players", []):
                    if rp.get("player_id") == body.player_id:
                        rp["must_change_password"] = False
                        rp["password"] = player["password"]
                        # The player owns their password now — the generated
                        # temp credential must stop existing anywhere (it would
                        # otherwise keep surfacing on facilitator roster reads).
                        rp.pop("plaintext_password", None)
                        rp.pop("temp_password", None)
                        break
                # PARITY (2026-07-31 audit): this called _db._persist(), which
                # exists only in the memory backend. Under Postgres the
                # AttributeError was swallowed by the except below, so the
                # scrubbed temp credential was never written to the sessions
                # table — after a restart the PLAINTEXT temp password
                # re-surfaced on facilitator roster reads even though the
                # player had replaced it. update_session_metadata persists in
                # BOTH backends (and the memory version snapshots internally).
                await _db.update_session_metadata(
                    session_id, {"registered_players": sess.get("registered_players", [])}
                )
    except Exception:
        pass  # Non-critical — in-memory flag is already cleared

    return {"status": "success", "message": "Password updated successfully"}


# ─────────────────────────────────────────────────────────────────
# POST /api/simulations/{session_id}/learning-bonus  — Award points
# ─────────────────────────────────────────────────────────────────

class LearningBonusRequest(BaseModel):
    activity_type: str  # "podcast_complete" | "quiz_complete"
    notebook_id: str
    score_percent: int = 0  # Only for quiz_complete

@router.post(
    "/{session_id}/learning-bonus",
    summary="Award bonus points for completing podcast or quiz",
)
async def award_learning_bonus(request: Request, session_id: str, body: LearningBonusRequest):
    """
    Awards bonus points:
    - podcast_complete: 1000 pts (one-time only)
    - quiz_complete: 60-80% = 1500, 80-90% = 2000, 90-100% = 3000
      Retakes allowed — only the *incremental* improvement is awarded.
    Tracks attempt count so frontend can reveal answers after attempt 2.
    """
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    gs = latest["global_state"]
    bu_states = latest["bu_states"]

    awarded_key = "learning_bonuses_awarded"
    awarded = gs.get(awarded_key, {})
    claim_key = f"{body.activity_type}_{body.notebook_id}"

    def _quiz_points(pct: int) -> int:
        if pct >= 90: return 3000
        if pct >= 80: return 2000
        if pct >= 60: return 1500
        return 0

    # ── Podcast: one-time 1000 pts ─────────────────────────────
    if body.activity_type == "podcast_complete":
        if claim_key in awarded:
            return {
                "status": "already_claimed",
                "points_awarded": 0,
                "bonus_score": gs.get("bonus_score", 0),
                "message": "Podcast bonus already claimed.",
                "attempt": awarded[claim_key].get("attempt", 1),
            }
        points = 1000
        gs["bonus_score"] = gs.get("bonus_score", 0) + points
        awarded[claim_key] = {"points": points, "attempt": 1}
        gs[awarded_key] = awarded
        await db.update_latest_global_state(session_id, gs, bu_states)
        return {
            "status": "success",
            "points_awarded": points,
            "bonus_score": gs["bonus_score"],
            "message": f"+{points} bonus points!",
            "attempt": 1,
        }

    # ── Quiz: max 2 attempts, higher score kept ────────────────
    new_points = _quiz_points(body.score_percent)
    prev = awarded.get(claim_key, {})
    prev_points = prev.get("points", 0)
    prev_attempt = prev.get("attempt", 0)
    current_attempt = prev_attempt + 1

    # Quiz policy from the cohort's effective settings (fail-safe to legacy).
    try:
        from admin_shared import get_effective_settings as _ges
        _qeff = _ges(session_id)
        MAX_QUIZ_ATTEMPTS = int(_qeff.get("quiz_max_attempts", 2) or 2)
        _quiz_pass = int(_qeff.get("quiz_pass_threshold", 70) or 70)
        _quiz_graded = bool(_qeff.get("quiz_graded", False))
    except Exception:
        MAX_QUIZ_ATTEMPTS, _quiz_pass, _quiz_graded = 2, 70, False

    if prev_attempt >= MAX_QUIZ_ATTEMPTS:
        return {
            "status": "max_attempts_reached",
            "points_awarded": 0,
            "total_earned": prev_points,
            "bonus_score": gs.get("bonus_score", 0),
            "message": f"Maximum {MAX_QUIZ_ATTEMPTS} attempts reached. Your best score: {prev.get('best_score_percent', 0)}% ({prev_points} pts).",
            "attempt": prev_attempt,
            "max_attempts": MAX_QUIZ_ATTEMPTS,
            "passed": prev.get("best_score_percent", 0) >= _quiz_pass,
            "pass_threshold": _quiz_pass,
            "graded": _quiz_graded,
            "show_answers": True,
        }

    incremental = max(0, new_points - prev_points)

    if incremental > 0:
        gs["bonus_score"] = gs.get("bonus_score", 0) + incremental

    awarded[claim_key] = {
        "points": max(new_points, prev_points),
        "score_percent": body.score_percent,
        "attempt": current_attempt,
        "best_score_percent": max(body.score_percent, prev.get("best_score_percent", 0)),
    }
    gs[awarded_key] = awarded
    await db.update_latest_global_state(session_id, gs, bu_states)

    attempts_remaining = MAX_QUIZ_ATTEMPTS - current_attempt

    if incremental > 0:
        msg = f"+{incremental} bonus points! (improved from {prev_points} → {max(new_points, prev_points)})"
    elif new_points > 0:
        msg = f"Score: {body.score_percent}% — already at best tier ({prev_points} pts)."
    else:
        msg = "Score below 60% — no bonus this time."

    if attempts_remaining > 0:
        msg += f" {attempts_remaining} retake{'s' if attempts_remaining > 1 else ''} remaining."
    else:
        msg += " No more retakes available."

    return {
        "status": "success",
        "points_awarded": incremental,
        "total_earned": max(new_points, prev_points),
        "bonus_score": gs.get("bonus_score", 0),
        "message": msg,
        "attempt": current_attempt,
        "max_attempts": MAX_QUIZ_ATTEMPTS,
        "attempts_remaining": attempts_remaining,
        "passed": max(body.score_percent, prev.get("best_score_percent", 0)) >= _quiz_pass,
        "pass_threshold": _quiz_pass,
        "graded": _quiz_graded,
        "show_answers": current_attempt >= MAX_QUIZ_ATTEMPTS,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/quiz/{notebook_id}  — Generate random quiz
# ─────────────────────────────────────────────────────────────────

import random as _random

@router.get(
    "/quiz/{notebook_id}",
    summary="Get 10 random quiz questions for a notebook, filtered by difficulty",
)
async def get_quiz_questions(notebook_id: str):
    """
    Returns 10 randomly selected questions from the notebook's question bank.
    Questions are filtered by the facilitator's current difficulty setting.
    Falls back to all difficulties if not enough at the target level.
    Question and option order are shuffled for each request.
    """
    from admin_resources import _notebooklm_notebooks, _quiz_difficulty

    nb = next((n for n in _notebooklm_notebooks if n["id"] == notebook_id), None)
    if not nb:
        raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found.")

    all_questions = nb.get("quiz_questions", [])
    if not all_questions:
        raise HTTPException(status_code=404, detail="No quiz questions available for this notebook.")

    # Filter by difficulty
    filtered = [q for q in all_questions if q.get("difficulty") == _quiz_difficulty]

    # Fallback: if fewer than 10 at target difficulty, supplement from other levels
    if len(filtered) < 10:
        remaining = [q for q in all_questions if q not in filtered]
        _random.shuffle(remaining)
        filtered.extend(remaining[:10 - len(filtered)])

    # Select 10 random questions
    _random.shuffle(filtered)
    selected = filtered[:10]

    # Shuffle option order for each question (adjusting correct index)
    result = []
    for q in selected:
        options = list(q["options"])
        correct_text = options[q["correct"]]
        _random.shuffle(options)
        new_correct = options.index(correct_text)
        result.append({
            "question": q["question"],
            "options": options,
            "correct": new_correct,
            "explanation": q["explanation"],
            "difficulty": q.get("difficulty", "medium"),
        })

    return {
        "notebook_id": notebook_id,
        "difficulty": _quiz_difficulty,
        "question_count": len(result),
        "questions": result,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/resources  — Player-facing
# ─────────────────────────────────────────────────────────────────


@router.get(
    "/{session_id}/resources",
    summary="Get unlocked resources for a player session",
)
async def get_player_resources(session_id: str, request: Request):
    """
    Returns resources available to the player:
    1. Standard resources whose facilitator_default_round <= current round (auto-available)
    2. Explicitly unlocked resources (facilitator-unlocked or hidden resources unlocked by triggers)
    Splits them into 'new_this_round' and 'archive'.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from admin_resources import _resource_library, _session_resource_state, _notebooklm_notebooks, _quiz_enabled

    # Get current round
    latest = await db.fetch_latest_state(session_id)
    current_round = latest["round_number"] if latest else 1

    # Also check parent cohort for unlocked resources
    session_info = await db.get_session_info(session_id)
    parent_id = session_info.get("parent_cohort_id") if session_info else None

    # Quiz enabled check — check session and parent cohort
    quiz_enabled = _quiz_enabled.get(session_id, True)
    if parent_id:
        quiz_enabled = _quiz_enabled.get(parent_id, quiz_enabled)

    unlocked = _session_resource_state.get(session_id, [])
    if parent_id:
        unlocked = unlocked + _session_resource_state.get(parent_id, [])
    unlocked_ids = {u["resource_id"]: u for u in unlocked}

    seen_ids = set()
    new_this_round = []
    archive = []

    for res in _resource_library:
        rid = res["id"]
        if rid in seen_ids:
            continue

        visibility = res.get("visibility", "Standard")
        default_round = res.get("facilitator_default_round")

        # Explicitly unlocked resources (hidden or manual)
        if rid in unlocked_ids:
            seen_ids.add(rid)
            unlock_info = unlocked_ids[rid]
            enriched = {
                **res,
                "unlocked_at_round": unlock_info["unlocked_at_round"],
                "unlocked_at_time": unlock_info["unlocked_at_time"],
                "is_strategic_drop": unlock_info.get("is_strategic_drop", False),
                "trigger": unlock_info.get("trigger", "manual"),
            }
            if unlock_info["unlocked_at_round"] == current_round:
                new_this_round.append(enriched)
            else:
                archive.append(enriched)
            continue

        # Standard resources auto-available at their designated round
        if visibility == "Standard" and default_round is not None and default_round <= current_round:
            seen_ids.add(rid)
            enriched = {
                **res,
                "unlocked_at_round": default_round,
                "unlocked_at_time": None,
                "is_strategic_drop": False,
                "trigger": "auto_round",
            }
            if default_round == current_round:
                new_this_round.append(enriched)
            else:
                archive.append(enriched)

    # Filter NotebookLM notebooks available for current round
    notebooklm_available = [
        nb for nb in _notebooklm_notebooks
        if nb.get("target_round", 1) <= current_round
    ]

    return {
        "current_round": current_round,
        "new_this_round": new_this_round,
        "archive": archive,
        "total_unlocked": len(new_this_round) + len(archive),
        "notebooklm_notebooks": notebooklm_available,
        "quiz_enabled": quiz_enabled,
    }


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/peer-leaderboard
# ─────────────────────────────────────────────────────────────────

TEAM_NAMES = [
    "Team Alpha", "Team Bravo", "Team Charlie", "Team Delta",
    "Team Echo", "Team Foxtrot", "Team Golf", "Team Hotel",
    "Team India", "Team Juliet", "Team Kilo", "Team Lima",
]

@router.get(
    "/{session_id}/peer-leaderboard",
    summary="Get anonymized peer leaderboard for a player session",
)
async def get_peer_leaderboard(session_id: str, request: Request):
    """
    Returns an anonymized leaderboard of all players in the same cohort.
    The requesting player is highlighted with isYou=True.
    For solo/demo sessions, generates AI benchmark players for comparison.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    # Get session info to find parent cohort
    session_info = await db.get_session_info(session_id)
    if not session_info:
        return {"leaderboard": [], "message": "Session not found"}

    parent_id = session_info.get("parent_cohort_id")

    # Result-visibility policy (fail-open). reveal_round gates the whole ranking
    # until a set round; redact_peers forces anonymised team names for everyone
    # but the requester. Read from the cohort's effective settings; any failure
    # leaves both off (current behaviour).
    _reveal_round = 0
    _redact_peers = False
    try:
        from admin_shared import get_effective_settings as _ges
        _pol = _ges(parent_id or session_id)
        _reveal_round = int(_pol.get("results_reveal_round", 0) or 0)
        _redact_peers = bool(_pol.get("redact_peer_identities", False))
    except Exception:
        pass

    # ── Solo session: Generate AI benchmark players ──────────────
    if not parent_id:
        latest = await db.fetch_latest_state(session_id)
        if not latest:
            return {"leaderboard": [], "message": "No simulation data yet"}
        gs = latest["global_state"]
        player_treasury = float(gs.get("corporate_treasury", 25_000_000))
        player_rep = float(gs.get("group_reputation", 50))
        player_round = latest.get("round_number", gs.get("round_number", 1))  # BUGFIX: top-level round_number
        player_carbon = int(gs.get("tco2e_emissions", 0))
        player_synergy = float(gs.get("synergy_multiplier", 1.0))
        player_bonus = gs.get("bonus_score", 0)
        player_name = session_info.get("player_name", "Your Team") if session_info else "Your Team"

        # An INSTANCE, not the module. `import random as _rng; _rng.seed(...)`
        # reseeded the PROCESS-GLOBAL rng that org_politics, supply_chain_network
        # and engine's unseeded fallbacks draw from, so one cohort opening this
        # page changed another cohort's board votes and supplier rolls. The old
        # hash() seed was PYTHONHASHSEED-randomised too, so the "consistent
        # across refreshes" below was never true across a restart. It is now.
        from rng_util import stable_rng
        _rng = stable_rng(session_id, player_round, "peer_leaderboard")

        # Generate 3 AI benchmark players with varied strategies
        ai_profiles = [
            {"name": "🤖 AI Strategist (Balanced)", "treasury_mult": 1.08, "rep_mult": 0.95, "carbon_mult": 0.85, "synergy_mult": 1.05},
            {"name": "🤖 AI Optimizer (Growth)", "treasury_mult": 1.20, "rep_mult": 0.80, "carbon_mult": 1.15, "synergy_mult": 0.90},
            {"name": "🤖 AI Guardian (ESG)", "treasury_mult": 0.85, "rep_mult": 1.15, "carbon_mult": 0.70, "synergy_mult": 1.10},
        ]

        leaderboard = []
        # Add player first
        leaderboard.append({
            "rank": 0,
            "name": player_name or "Your Team",
            "treasury": player_treasury,
            "reputation": player_rep,
            "co2": player_carbon,
            "bonus_score": player_bonus,
            "trend": "→",
            "isYou": True,
        })

        for prof in ai_profiles:
            noise_t = _rng.uniform(-0.05, 0.05)
            noise_r = _rng.uniform(-3, 3)
            ai_treasury = round(player_treasury * prof["treasury_mult"] + noise_t * player_treasury, 2)
            ai_rep = round(min(100, max(5, player_rep * prof["rep_mult"] + noise_r)), 1)
            ai_carbon = max(0, int(player_carbon * prof["carbon_mult"] + _rng.randint(-50, 50)))
            ai_bonus = max(0, player_bonus + _rng.randint(-500, 500))

            leaderboard.append({
                "rank": 0,
                "name": prof["name"],
                "treasury": ai_treasury,
                "reputation": ai_rep,
                "co2": ai_carbon,
                "bonus_score": ai_bonus,
                "trend": _rng.choice(["↑", "→", "↓"]),
                "isYou": False,
                "isAI": True,
            })

        # Sort by treasury descending and assign ranks
        leaderboard.sort(key=lambda x: x["treasury"], reverse=True)
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return {"leaderboard": leaderboard, "ai_benchmark": True}

    # ── Multiplayer: Real peer leaderboard ──────────────────────
    # Find all sibling sessions (same parent)
    # Parity API: read siblings + round history via db.* (works under Postgres;
    # a direct _sessions / _global_states read returns {} there).
    # F-28: indexed child lookup instead of scanning every session on the platform.
    all_sessions = await db.get_child_sessions(parent_id)

    siblings = []
    for sess in all_sessions:
        sid = sess.get("session_id")
        if sess.get("parent_cohort_id") == parent_id:
            # SEAM-08 (audit 2026-09-04): hist[-1] is the team's CURRENT state
            # only with the closing row included — without it a finished team
            # ranks on the state it entered R10 with (the row R10 overwrote
            # before; now restored). hist[-2] is then one round back, always.
            hist = await db.fetch_round_history(sid, include_final=True)
            if hist:
                from history_semantics import display_round as _display_round
                gs = hist[-1].get("global_state", {})
                prev_treasury = (
                    float(hist[-2].get("global_state", {}).get("corporate_treasury", 0))
                    if len(hist) >= 2 else None
                )
                siblings.append({
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "treasury": float(gs.get("corporate_treasury", 0)),
                    "reputation": float(gs.get("group_reputation", 50)),
                    "carbon": int(gs.get("tco2e_emissions", 0)),
                    "bonus_score": gs.get("bonus_score", 0),
                    "round_number": _display_round(hist[-1]),
                    "finished": bool(hist[-1].get("is_final")),
                    "synergy": float(gs.get("synergy_multiplier", 1.0)),
                    "stakeholder_accuracy": gs.get("stakeholder_map_accuracy", None),  # C21
                    "_prev_treasury": prev_treasury,
                })

    # Sort by treasury descending
    siblings.sort(key=lambda x: x["treasury"], reverse=True)

    # Reveal-schedule: withhold the whole ranking until the configured round.
    if _reveal_round:
        my_round = next((s["round_number"] for s in siblings if s["session_id"] == session_id), 1)
        if my_round < _reveal_round:
            return {
                "leaderboard": [],
                "locked": True,
                "reveal_round": _reveal_round,
                "message": f"Peer rankings unlock at round {_reveal_round}.",
            }

    # Anonymize and mark current player
    leaderboard = []
    for i, s in enumerate(siblings):
        team_name = TEAM_NAMES[i] if i < len(TEAM_NAMES) else f"Team {i + 1}"
        is_you = s["session_id"] == session_id

        # Determine trend based on round number (prev-round treasury precomputed
        # from fetch_round_history above, so no second store read is needed).
        trend = "→"
        if s["round_number"] > 1 and s.get("_prev_treasury") is not None:
            prev_treasury = s["_prev_treasury"]
            if s["treasury"] > prev_treasury:
                trend = "↑"
            elif s["treasury"] < prev_treasury:
                trend = "↓"

        entry = {
            "rank": i + 1,
            # Redaction forces the anonymous team label for every peer but the
            # requester; off (default) keeps the real player name when present.
            "name": (
                (s.get("player_name") or "Your Team") if is_you
                else (team_name if _redact_peers else (s.get("player_name") or team_name))
            ),
            "treasury": s["treasury"],
            "reputation": s["reputation"],
            "co2": s["carbon"],
            "bonus_score": s["bonus_score"],
            "trend": trend,
            "isYou": is_you,
        }
        leaderboard.append(entry)

    return {"leaderboard": leaderboard}


# ─────────────────────────────────────────────────────────────────
# GET /api/simulations/{session_id}/peer-trend-history
# Returns averaged round-by-round metrics for all cohort peers.
# Used by the Trends tab to overlay "Cohort Average" lines on charts.
# ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/peer-trend-history",
    summary="Get averaged round-by-round peer metrics for cohort comparison",
)
async def get_peer_trend_history(session_id: str, request: Request):
    """
    Returns averaged round-by-round performance metrics for all sibling
    sessions in the same cohort.  Each round entry contains:
      - avgCI, tco2e, ebitda, rep (averages across all peers)
      - peerCount (how many peers contributed data for that round)

    For solo sessions, generates synthetic AI benchmark trend lines.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        return {"available": False, "reason": "Session not found", "rounds": []}

    parent_id = session_info.get("parent_cohort_id")

    # Resolve cohort siblings FIRST, because a cohort that happens to have only
    # ONE team needs exactly the same fallback as a solo run.
    # BUG-2026-07-20: the AI benchmark was gated on `not parent_id`, so a
    # single-team cohort fell through to the multiplayer branch, found no
    # siblings and returned available=False. The "Cohort Trends" toggle then
    # flipped but drew nothing — reported as "the toggle does not work". A
    # one-team cohort is the normal case when piloting or running a small
    # class, so it must still get a comparison line.
    sibling_ids = []
    _sess_by_id = {}
    if parent_id:
        _all_sessions = await db.get_child_sessions(parent_id)   # F-28: indexed
        _sess_by_id = {s.get("session_id"): s for s in _all_sessions}
        sibling_ids = [
            s["session_id"] for s in _all_sessions
            if s.get("parent_cohort_id") == parent_id and s.get("session_id") != session_id
        ]

    # ── Solo OR single-team cohort: synthetic AI benchmarks ───────
    # NOTE: AI benchmarks use INDEPENDENT absolute trajectories, NOT
    # perturbations of the player's own data. This ensures the peer
    # comparison line is meaningfully different from the player's path.
    if not parent_id or not sibling_ids:
        latest = await db.fetch_latest_state(session_id)
        if not latest:
            return {"available": False, "reason": "No simulation data yet", "rounds": []}

        own_history = await db.fetch_round_history(session_id)
        if not own_history:
            return {"available": False, "reason": "No history available", "rounds": []}

        # Instance, not the module — see get_peer_leaderboard above.
        from rng_util import stable_rng
        _rng = stable_rng(session_id, "peer_trend_history")

        # ── Independent AI archetype trajectories ──────────────────
        # Each profile defines absolute base values and per-round deltas
        # representing genuinely different strategic approaches.
        #
        # Base values match the simulation's initial conditions:
        #   CI ~45, EBITDA ~$19.2M, Rep ~50, tCO2e ~180
        EBITDA_BASE = 19_200_000
        CI_BASE = 45.0
        REP_BASE = 50.0
        TCO2E_BASE = 180.0
        IPO_PRICE_REF = 50.0  # For stock price calculation

        ai_profiles = [
            {
                "name": "Balanced",
                "ci_delta": -1.5,        # gradual decarbonisation
                "ebitda_growth": 0.03,    # steady 3% growth/round
                "rep_delta": 1.5,         # slow reputation build
                "tco2e_delta": -8,        # moderate emission cuts
                "synergy_base": 1.02,
            },
            {
                "name": "Growth",
                "ci_delta": 1.0,          # carbon increases (profit focus)
                "ebitda_growth": 0.08,    # aggressive 8% growth/round
                "rep_delta": -2.0,        # reputation erosion
                "tco2e_delta": 12,        # emissions rise
                "synergy_base": 0.95,
            },
            {
                "name": "ESG",
                "ci_delta": -3.0,         # aggressive decarbonisation
                "ebitda_growth": -0.02,   # EBITDA shrinks (heavy green CAPEX)
                "rep_delta": 3.0,         # strong reputation gain
                "tco2e_delta": -18,       # deep emission cuts
                "synergy_base": 1.10,
            },
        ]

        rounds_out = []
        for snap in own_history:
            rn = snap.get("round_number", 0)
            if rn < 1 or rn > 10:
                continue

            # Generate each profile's absolute value at this round
            ci_vals, tco2e_vals, ebitda_vals, rep_vals, stock_vals = [], [], [], [], []
            for prof in ai_profiles:
                r = rn - 1  # 0-indexed round offset

                ci = max(5, CI_BASE + prof["ci_delta"] * r + _rng.uniform(-1.5, 1.5))
                tco2e = max(0, TCO2E_BASE + prof["tco2e_delta"] * r + _rng.uniform(-15, 15))
                ebitda = EBITDA_BASE * ((1 + prof["ebitda_growth"]) ** r) + _rng.uniform(-1_500_000, 1_500_000)
                rep = min(100, max(5, REP_BASE + prof["rep_delta"] * r + _rng.uniform(-2, 2)))

                ci_vals.append(ci)
                tco2e_vals.append(tco2e)
                ebitda_vals.append(ebitda)
                rep_vals.append(rep)

                # Stock price: IPO * (EBITDA/Baseline) * sentiment
                synergy_boost = prof["synergy_base"] - 1.0
                ncd_penalty = 5.0 / 100  # assume moderate NCD ~5
                rep_penalty = (100 - rep) / 200
                sentiment = max(0.1, 1.0 + synergy_boost - ncd_penalty - rep_penalty)
                stock_price = IPO_PRICE_REF * (max(0, ebitda) / EBITDA_BASE) * sentiment
                stock_vals.append(max(1.0, stock_price))

            avg_ci = sum(ci_vals) / len(ci_vals)
            avg_tco2e = sum(tco2e_vals) / len(tco2e_vals)
            avg_ebitda = sum(ebitda_vals) / len(ebitda_vals)
            avg_rep = sum(rep_vals) / len(rep_vals)
            avg_stock = sum(stock_vals) / len(stock_vals)

            peer_details = []
            for i, prof in enumerate(ai_profiles):
                peer_details.append({
                    "id": f"ai_{i}",
                    "name": prof["name"],
                    "ci": ci_vals[i],
                    "tco2e": tco2e_vals[i],
                    "ebitda": ebitda_vals[i],
                    "rep": rep_vals[i],
                    "stock": stock_vals[i]
                })

            rounds_out.append({
                "round": rn,
                "avgCI": round(avg_ci, 2),
                "tco2e": round(avg_tco2e, 1),
                "ebitda": round(avg_ebitda, 2),
                "rep": round(avg_rep, 1),
                "peerStockPrice": round(avg_stock, 2),
                "peerCount": 3,
                "peers": peer_details,
            })

        return {"available": True, "ai_benchmark": True, "peerCount": 3, "rounds": rounds_out}

    # ── Multiplayer: Real peer averages ──────────────────────────
    # sibling_ids resolved above. (Historical note: this branch once imported
    # `_round_states` — a name that has NEVER existed in the store — so it
    # always raised ImportError and silently returned "unavailable".)

    # Aggregate per-round metrics from all siblings
    round_accum = {}  # round_num → {ci: [], tco2e: [], ebitda: [], rep: [], peers: []}
    for sid in sibling_ids:
        peer_history = await db.fetch_round_history(sid)
        if not peer_history:
            continue
        for snap in peer_history:
            rn = snap.get("round_number", 0)
            if rn < 1 or rn > 10:
                continue
            gs = snap.get("global_state", {})
            bu_arr = snap.get("business_units", snap.get("bu_states", []))
            ci = sum(b.get("carbon_intensity", 0) for b in bu_arr) / max(len(bu_arr), 1)
            tco2e = gs.get("tco2e_emissions", 0)
            ebitda = gs.get("historical_ebitda", 0)
            rep = gs.get("group_reputation", 50)

            # Compute peer stock price
            _ipo = 50.0
            _baseline_ebitda = 19_200_000
            _synergy_boost = 0.0  # assume baseline synergy for peers
            _ncd_penalty = 5.0 / 100
            _rep_penalty = (100 - rep) / 200
            _sentiment = max(0.1, 1.0 + _synergy_boost - _ncd_penalty - _rep_penalty)
            _stock = max(1.0, _ipo * (max(0, ebitda) / _baseline_ebitda) * _sentiment)

            if rn not in round_accum:
                round_accum[rn] = {"ci": [], "tco2e": [], "ebitda": [], "rep": [], "peers": []}
            round_accum[rn]["ci"].append(ci)
            round_accum[rn]["tco2e"].append(tco2e)
            round_accum[rn]["ebitda"].append(ebitda)
            round_accum[rn]["rep"].append(rep)
            
            # Use cohort name or short code if available, fallback to Team X.
            # BUG-2026-07-20: this read `_sessions` — an UNDEFINED NAME (pyflakes
            # flags it). Every 2+ team cohort raised NameError here, so the real
            # peer-average branch never returned; combined with single-team
            # cohorts short-circuiting to "unavailable", the Cohort Trends
            # toggle drew nothing for ANY cohort. Use the parity-API map built
            # above so this works on Postgres as well as in memory mode.
            sess_info = _sess_by_id.get(sid, {}) or {}
            p_name = sess_info.get("cohort_name") or f"Team {sid[:4]}"
            round_accum[rn]["peers"].append({
                "id": sid,
                "name": p_name,
                "ci": ci,
                "tco2e": tco2e,
                "ebitda": ebitda,
                "rep": rep,
                "stock": _stock
            })

    rounds_out = []
    for rn in sorted(round_accum.keys()):
        acc = round_accum[rn]
        n = len(acc["ci"])
        avg_ebitda = sum(acc["ebitda"]) / n
        avg_rep = sum(acc["rep"]) / n

        # Compute peer stock price from averaged metrics
        # Same formula as stockValuationEngine: IPO * (EBITDA/Baseline) * sentiment
        _ipo = 50.0
        _baseline_ebitda = 19_200_000
        _synergy_boost = 0.0  # assume baseline synergy for peers
        _ncd_penalty = 5.0 / 100
        _rep_penalty = (100 - avg_rep) / 200
        _sentiment = max(0.1, 1.0 + _synergy_boost - _ncd_penalty - _rep_penalty)
        _stock = max(1.0, _ipo * (max(0, avg_ebitda) / _baseline_ebitda) * _sentiment)

        rounds_out.append({
            "round": rn,
            "avgCI": round(sum(acc["ci"]) / n, 2),
            "tco2e": round(sum(acc["tco2e"]) / n, 1),
            "ebitda": round(avg_ebitda, 2),
            "rep": round(avg_rep, 1),
            "peerStockPrice": round(_stock, 2),
            "peerCount": n,
            "peers": acc["peers"],
        })

    return {"available": True, "ai_benchmark": False, "peerCount": len(sibling_ids), "rounds": rounds_out}


# ═════════════════════════════════════════════════════════════════
#  SIDE TRACK ENDPOINTS (Player-Facing)
#  Sequential model: main sim pauses while side track is active.
#  Full process_tick() engine used for side track rounds.
# ═════════════════════════════════════════════════════════════════

async def _get_active_side_track_for_session(session_id: str) -> tuple[str | None, dict | None]:
    """
    Check if a session (or its parent cohort) has an active, incomplete side track.
    Returns (track_id, track_state) if a side track is blocking main sim progression,
    or (None, None) if no side track is active.
    """
    from database_memory import _sessions
    sess = _sessions.get(session_id)
    if not sess:
        return None, None

    # Keep a reference to the player session before resolving to cohort
    player_sess = sess

    # Check parent cohort if this is a player sub-session
    parent_id = sess.get("parent_cohort_id")
    if parent_id:
        parent = _sessions.get(parent_id)
        if parent:
            sess = parent

    active_tracks = sess.get("active_side_tracks", [])
    if not active_tracks:
        return None, None

    # Player-level states take priority (commit writes completed=True here),
    # fall back to cohort-level states for tracks not yet touched by this player
    states = player_sess.get("side_track_states") or sess.get("side_track_states", {})
    timing = sess.get("side_track_timing", {})

    # Get current main sim round (parity API — works under Postgres; a direct
    # _global_states read returns {} there).
    _rn = await db.fetch_latest_round(session_id)
    current_main_round = _rn if _rn is not None else 1

    for tid in active_tracks:
        st = states.get(tid, {})
        if st.get("completed"):
            continue

        # Check timing: has the unlock round been reached?
        track_timing = timing.get(tid, {})
        unlock_after = track_timing.get("unlock_after_round", 0)
        if current_main_round <= unlock_after:
            continue

        # This track is active, unlocked, and not completed — it blocks main sim
        if st.get("current_round", 0) > 0 or current_main_round > unlock_after:
            return tid, st

    return None, None


@router.get("/{session_id}/side-tracks", summary="Get active side tracks for this session")
async def get_session_side_tracks(session_id: str, request: Request):
    """
    Returns all side tracks assigned to this session (via cohort),
    their current progress, and whether the main sim is blocked.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from database_memory import _sessions

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Resolve parent cohort for player sub-sessions
    parent_id = session.get("parent_cohort_id")
    cohort = _sessions.get(parent_id) if parent_id else session
    if not cohort:
        cohort = session

    active_tracks = cohort.get("active_side_tracks", [])
    timing = cohort.get("side_track_timing", {})

    # Use player-level side track states if they exist, otherwise cohort level
    states = session.get("side_track_states") or cohort.get("side_track_states", {})

    # Get current main sim round
    latest = await db.fetch_latest_state(session_id)
    current_main_round = latest["round_number"] if latest else 1

    from side_tracks import get_track
    tracks_out = []
    blocking_track_id = None

    for tid in active_tracks:
        track = get_track(tid)
        if not track:
            continue

        st = states.get(tid, {})
        track_timing = timing.get(tid, {})
        unlock_after = track_timing.get("unlock_after_round", 0)
        is_unlocked = current_main_round > unlock_after
        is_completed = st.get("completed", False)
        current_track_round = st.get("current_round", 0)

        # Determine if this track is blocking
        is_blocking = is_unlocked and not is_completed and current_track_round >= 0
        if is_blocking and not blocking_track_id:
            blocking_track_id = tid

        # Get round config for current or preview round
        round_config = None
        if not is_completed:
            # Return current round config, or round 1 preview if not started yet
            config_round = current_track_round if current_track_round > 0 else 1
            round_config = track.get_round_config(config_round)

        tracks_out.append({
            "track_id": tid,
            "display_name": track.display_name,
            "description": track.description,
            "icon": track.icon,
            "num_rounds": track.num_rounds,
            "current_round": current_track_round,
            "completed": is_completed,
            "is_unlocked": is_unlocked,
            "is_blocking": is_blocking,
            "unlock_after_round": unlock_after,
            "scoring_dimensions": track.scoring_dimensions,
            "track_state": st.get("state", {}),
            "round_config": round_config,
        })

    return {
        "session_id": session_id,
        "side_tracks": tracks_out,
        "main_sim_blocked": blocking_track_id is not None,
        "blocking_track_id": blocking_track_id,
        "current_main_round": current_main_round,
    }


class SideTrackCommitRequest(BaseModel):
    decisions: list[dict]
    crisis_severity: float = 40.0
    dividends_paid: float = 0.0
    imitation_decay_rate: float = 0.05


@router.post("/{session_id}/side-tracks/{track_id}/commit", summary="Commit a side track round")
async def commit_side_track_turn(request: Request, session_id: str, track_id: str, body: SideTrackCommitRequest):
    """
    Processes one round of a side track using the FULL process_tick() engine.

    Flow:
      1. Resolve cohort & validate track is active/unlocked
      2. If round 0 (not started), seed from main state via data bridge
      3. Run pre_tick → process_tick → post_tick
      4. Persist track state
      5. If final round, write back to main sim via data bridge
      6. Return new track state
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    from database_memory import _sessions, _persist
    from side_tracks import get_track
    import copy

    # Resolve session & cohort
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    parent_id = session.get("parent_cohort_id")
    cohort = _sessions.get(parent_id) if parent_id else session
    if not cohort:
        cohort = session

    # Validate track
    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Side track '{track_id}' not found")

    active = cohort.get("active_side_tracks", [])
    if track_id not in active:
        raise HTTPException(status_code=403, detail=f"Side track '{track_id}' not assigned to this cohort")

    # Get or create player-level track states
    if "side_track_states" not in session:
        session["side_track_states"] = copy.deepcopy(cohort.get("side_track_states", {}))
    
    states = session["side_track_states"]
    if track_id not in states:
        states[track_id] = {
            "current_round": 0,
            "completed": False,
            "state": {},
            "bu_states": [],
            "round_history": [],
            "accumulated_flags": [],
        }

    track_data = states[track_id]
    if track_data.get("completed"):
        raise HTTPException(status_code=409, detail=f"Side track '{track_id}' already completed")

    # Check timing: is this track unlocked?
    timing = cohort.get("side_track_timing", {})
    track_timing = timing.get(track_id, {})
    unlock_after = track_timing.get("unlock_after_round", 0)

    latest_main = await db.fetch_latest_state(session_id)
    current_main_round = latest_main["round_number"] if latest_main else 1
    if current_main_round <= unlock_after:
        raise HTTPException(
            status_code=403,
            detail=f"Side track '{track_id}' unlocks after main Round {unlock_after}. Currently on Round {current_main_round}."
        )

    current_track_round = track_data.get("current_round", 0)

    # ── SEED: If round 0, initialize from main state ─────────
    if current_track_round == 0:
        main_global = latest_main["global_state"] if latest_main else {}
        main_bus = latest_main["bu_states"] if latest_main else []

        # Collect completed track states for cross-track dependencies
        completed_tracks = {}
        for tid, tst in states.items():
            if tst.get("completed") and tid != track_id:
                completed_tracks[tid] = tst.get("state", {})

        seed_state = track.seed_from_main_state(main_global, main_bus, completed_tracks)
        # Convert DataBridgeInput to plain dict for mutable storage
        # (seed_from_main_state returns a frozen Pydantic model)
        track_data["state"] = seed_state.to_seed_dict() if hasattr(seed_state, 'to_seed_dict') else seed_state
        track_data["bu_states"] = copy.deepcopy(main_bus)
        current_track_round = 1
        track_data["current_round"] = 1

    # ── BUILD ENGINE INPUTS ──────────────────────────────────
    track_global = {
        "round_number": current_track_round,
        "corporate_treasury": track_data["state"].get("inherited_treasury", 50_000_000),
        "group_reputation": track_data["state"].get("inherited_reputation", 50.0),
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "active_event_flags": {
            f"side_track_{track_id}": True,
            **{f: True for f in track_data.get("accumulated_flags", [])},
        },
        "bonus_score": 0,
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "vrio_capabilities": {},
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "pending_capex_projects": [],
        "inflation_index": 0.025,
        "competitor_ebitda": 0,
    }

    # Merge persisted treasury/reputation if track has progressed past R1
    if current_track_round > 1:
        track_global["corporate_treasury"] = track_data["state"].get(
            "current_treasury", track_global["corporate_treasury"]
        )
        track_global["group_reputation"] = track_data["state"].get(
            "current_reputation", track_global["group_reputation"]
        )

    current_bus = copy.deepcopy(track_data.get("bu_states", []))
    decisions_raw = [d if isinstance(d, dict) else d.model_dump() for d in body.decisions]

    # ── PRE-TICK ─────────────────────────────────────────────
    # F-07: side tracks take their crisis severity from the track definition
    # (its pre_tick may override); the client value is ignored.
    _track_base_crisis = float(getattr(track, "base_crisis_severity", 0.0) or 0.0)
    pre_result = track.pre_tick(
        round_number=current_track_round,
        track_state=track_data["state"],
        bus=current_bus,
        decisions=decisions_raw,
        crisis_severity=_track_base_crisis,
    )
    effective_crisis = pre_result.get("crisis_severity", _track_base_crisis)
    pre_events = pre_result.get("pre_events", {})

    # ── PROCESS TICK (Full 8-formula engine) ──────────────────
    # Determine paradigm from session (side tracks use the same paradigm)
    session_info = await db.get_session_info(session_id)
    paradigm = (session_info or {}).get("decision_paradigm", "legacy_abc")

    tick_result = process_tick(
        current_global=track_global,
        current_bus=current_bus,
        decisions=decisions_raw,
        dividends_paid=body.dividends_paid,
        crisis_severity=effective_crisis,
        imitation_decay_rate=_cfg.DEFAULT_IMITATION_DECAY_RATE,  # F-07 / CFG-05: call-time read
        decision_paradigm=paradigm,
    )

    new_global = tick_result["global_state"]
    new_bus = tick_result["bu_states"]
    events = tick_result["events"]
    events.update(pre_events)

    # ── POST-TICK (Track-specific) ───────────────────────────
    post_events = track.post_tick(
        round_number=current_track_round,
        global_state=new_global,
        bu_states=new_bus,
        decisions=decisions_raw,
        events=events,
        extra_events={},
        previous_flags={"accumulated_flags": track_data.get("accumulated_flags", [])},
    )
    events.update(post_events)

    # ── UPDATE TRACK STATE ───────────────────────────────────
    # Accumulate flags from the chosen option
    choice = track._get_primary_choice(decisions_raw)
    round_opts = track.get_round_options(current_track_round)
    opt = round_opts.get(choice, {})
    new_flags = opt.get("flags_set", [])
    track_data["accumulated_flags"] = list(
        set(track_data.get("accumulated_flags", []) + new_flags)
    )

    # Update custom track metrics from events
    for key, val in events.items():
        prefix = f"st_{track_id}_custom_"
        if key.startswith(prefix):
            metric_name = key[len(prefix):]
            if isinstance(val, (int, float)):
                current_val = track_data["state"].get(metric_name, 0)
                track_data["state"][metric_name] = round(current_val + val, 2)
            else:
                track_data["state"][metric_name] = val

    # Persist treasury & reputation
    track_data["state"]["current_treasury"] = new_global["corporate_treasury"]
    track_data["state"]["current_reputation"] = new_global["group_reputation"]

    # Store round snapshot in history
    track_data["round_history"].append({
        "round_number": current_track_round,
        "choice": choice,
        "events": events,
        "treasury_after": new_global["corporate_treasury"],
        "reputation_after": new_global["group_reputation"],
        "track_state_snapshot": copy.deepcopy(track_data["state"]),
    })

    track_data["bu_states"] = copy.deepcopy(new_bus)

    # ── CHECK COMPLETION ─────────────────────────────────────
    is_final = current_track_round >= track.num_rounds
    if is_final:
        track_data["completed"] = True
        track_data["current_round"] = current_track_round

        # Calculate final score
        score = track.calculate_score(track_data["state"])
        track_data["final_score"] = score

        # DATA BRIDGE (WRITE): merge flags/KPI deltas into main sim
        # Uses engine.apply_side_track_results() for proper typed handling
        # of DataBridgeOutput (flags, KPI deltas, KPI overrides, clamping).
        main_state = await db.fetch_latest_state(session_id)
        if main_state:
            write_back = track.write_back_to_main(track_data["state"], main_state["global_state"])
            from engine import apply_side_track_results
            main_gs = apply_side_track_results(main_state["global_state"], write_back)
            await db.update_latest_global_state(
                session_id=session_id,
                global_state=main_gs,
                bu_states=main_state["bu_states"],
            )
            events["write_back_flags"] = write_back.flags_to_set
            events["side_track_completed"] = True
            events["side_track_score"] = score
    else:
        track_data["current_round"] = current_track_round + 1

    _persist()

    # ── BUILD RESPONSE ───────────────────────────────────────
    # Get next round config if not completed
    next_round_config = None
    if not is_final:
        next_round_config = track.get_round_config(current_track_round + 1)

    return {
        "session_id": session_id,
        "track_id": track_id,
        "round_completed": current_track_round,
        "next_round": None if is_final else current_track_round + 1,
        "is_final": is_final,
        "track_state": track_data["state"],
        "accumulated_flags": track_data["accumulated_flags"],
        "events": events,
        "next_round_config": next_round_config,
        "final_score": track_data.get("final_score"),
        "global_state": {
            "corporate_treasury": new_global["corporate_treasury"],
            "group_reputation": new_global["group_reputation"],
        },
    }


@router.get("/{session_id}/side-tracks/{track_id}/history", summary="Get side track round history")
async def get_side_track_history(session_id: str, request: Request, track_id: str):
    """Returns the round-by-round history for a specific side track."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from database_memory import _sessions

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    states = session.get("side_track_states", {})
    track_data = states.get(track_id)
    if not track_data:
        # Try parent cohort
        parent_id = session.get("parent_cohort_id")
        if parent_id:
            parent = _sessions.get(parent_id)
            if parent:
                states = parent.get("side_track_states", {})
                track_data = states.get(track_id)

    if not track_data:
        raise HTTPException(status_code=404, detail=f"No data for side track '{track_id}'")

    return {
        "session_id": session_id,
        "track_id": track_id,
        "current_round": track_data.get("current_round", 0),
        "completed": track_data.get("completed", False),
        "round_history": track_data.get("round_history", []),
        "final_score": track_data.get("final_score"),
        "accumulated_flags": track_data.get("accumulated_flags", []),
    }


@router.get("/{session_id}/side-tracks/{track_id}/leaderboard", summary="Side track leaderboard")
async def get_side_track_leaderboard(session_id: str, request: Request, track_id: str):
    """
    Returns the separate leaderboard for a side track across all players in the cohort.
    Scores are independent of the main simulation leaderboard.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from database_memory import _sessions
    from side_tracks import get_track

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Side track '{track_id}' not found")

    # Find parent cohort
    parent_id = session.get("parent_cohort_id")
    if not parent_id:
        parent_id = session_id  # Solo session

    # Collect all sibling sessions
    entries = []
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_id or sid == parent_id:
            st = sess.get("side_track_states", {}).get(track_id)
            if st and st.get("current_round", 0) > 0:
                score = st.get("final_score") or track.calculate_score(st.get("state", {}))
                entries.append({
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "total_score": score.get("total_score", 0),
                    "grade": score.get("grade", "?"),
                    "archetype": score.get("archetype", {}).get("title", ""),
                    "completed": st.get("completed", False),
                    "rounds_done": st.get("current_round", 0),
                    "num_rounds": track.num_rounds,
                    "is_you": sid == session_id,
                })

    entries.sort(key=lambda e: -e["total_score"])
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return {
        "track_id": track_id,
        "display_name": track.display_name,
        "leaderboard": entries,
    }


@router.get("/{session_id}/side-tracks/aggregate-leaderboard", summary="Cross-track aggregated leaderboard")
async def get_aggregate_side_track_leaderboard(session_id: str, request: Request):
    """
    Returns an aggregated leaderboard across ALL completed side tracks.
    Each player gets a composite score (average of completed track scores)
    plus per-track breakdowns. Useful for facilitator debrief dashboards.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from database_memory import _sessions
    from side_tracks import get_all_tracks

    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    all_tracks = get_all_tracks()
    parent_id = session.get("parent_cohort_id") or session_id

    # Collect all sibling sessions
    player_data: dict = {}  # session_id → {name, tracks: {track_id: score_dict}}
    for sid, sess in _sessions.items():
        if sess.get("parent_cohort_id") == parent_id or sid == parent_id:
            st_states = sess.get("side_track_states", {})
            if not st_states:
                continue

            tracks_done = {}
            for tid, track_obj in all_tracks.items():
                st = st_states.get(tid)
                if st and st.get("current_round", 0) > 0:
                    score = st.get("final_score") or track_obj.calculate_score(st.get("state", {}))
                    tracks_done[tid] = {
                        "total_score": score.get("total_score", 0),
                        "grade": score.get("grade", "?"),
                        "archetype": score.get("archetype", {}).get("title", ""),
                        "completed": st.get("completed", False),
                        "rounds_done": st.get("current_round", 0),
                        "num_rounds": track_obj.num_rounds,
                        "mr_bonus": score.get("total_score", 0),
                    }

            if tracks_done:
                player_data[sid] = {
                    "session_id": sid,
                    "player_id": sess.get("player_id", ""),
                    "player_name": sess.get("player_name", ""),
                    "tracks": tracks_done,
                    "is_you": sid == session_id,
                }

    # Calculate composite scores
    entries = []
    for sid, pd in player_data.items():
        track_scores = [t["total_score"] for t in pd["tracks"].values()]
        composite = round(sum(track_scores) / len(track_scores), 1) if track_scores else 0

        # Grade the composite
        if composite >= 85: grade = "A+"
        elif composite >= 75: grade = "A"
        elif composite >= 65: grade = "B"
        elif composite >= 50: grade = "C"
        elif composite >= 35: grade = "D"
        else: grade = "F"

        entries.append({
            "session_id": pd["session_id"],
            "player_id": pd["player_id"],
            "player_name": pd["player_name"],
            "composite_score": composite,
            "composite_grade": grade,
            "tracks_completed": sum(1 for t in pd["tracks"].values() if t["completed"]),
            "tracks_started": len(pd["tracks"]),
            "tracks_available": len(all_tracks),
            "track_details": pd["tracks"],
            "is_you": pd["is_you"],
        })

    entries.sort(key=lambda e: -e["composite_score"])
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return {
        "available_tracks": [
            {"track_id": tid, "display_name": t.display_name, "icon": t.icon, "num_rounds": t.num_rounds}
            for tid, t in all_tracks.items()
        ],
        "aggregate_leaderboard": entries,
    }


# ═════════════════════════════════════════════════════════════════
#  CEO INTERVIEW — Post-Game Competency Assessment
# ═════════════════════════════════════════════════════════════════

def _is_interview_allowed(latest: dict) -> bool:
    """Determine if the CEO interview is available for this session.
    Post-game (round > 10): always available.
    Pre-game: requires explicit ceo_interview_enabled flag or god-mode toggle."""
    from admin_shared import _god_mode_settings
    flags = latest.get("global_state", {}).get("active_event_flags", {})
    round_number = latest.get("round_number", 1)
    game_is_done = round_number > 10 or bool(flags.get("profile"))
    if game_is_done:
        return True
    # Pre-game: explicit per-cohort flag or god-mode toggle required
    return flags.get("ceo_interview_enabled", _god_mode_settings.get("ceo_interview_enabled", False))


@router.get("/{session_id}/ceo-interview/questions", summary="Get CEO interview questions")
async def get_interview_questions_endpoint(session_id: str, request: Request):
    """Returns the interview questions for the post-game CEO assessment.
    Auto-enabled after game completion. Can also be enabled pre-game via facilitator settings."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from admin_shared import _god_mode_settings

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    if not _is_interview_allowed(latest):
        raise HTTPException(403, "CEO Interview is not enabled for this cohort. Enable via God Mode or facilitator settings.")

    flags = latest.get("global_state", {}).get("active_event_flags", {})

    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")

    # Per-cohort voice gender override
    voice_gender = flags.get(
        "ceo_interview_voice_gender",
        _god_mode_settings.get("ceo_interview_voice_gender", "female"),
    )

    from ceo_interview import get_interview_questions, get_ceo_persona, DIMENSIONS
    persona = get_ceo_persona(voice_gender)
    questions = get_interview_questions(
        ending_pathway=ending_pathway,
        question_count=_god_mode_settings.get("ceo_interview_question_count", 5),
        include_pathway_question=_god_mode_settings.get("ceo_interview_pathway_question", True),
    )

    return {
        "session_id": session_id,
        "questions": questions,
        "persona": persona,
        "dimensions": DIMENSIONS,
        "ending_pathway": ending_pathway,
    }


@router.post("/{session_id}/ceo-interview/assess", summary="Submit interview responses for assessment")
async def submit_interview_responses(request: Request, session_id: str, body: dict):
    """Submit player responses for CEO interview assessment.
    Returns scored dimensions (spider diagram data) + narrative feedback."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    from admin_shared import _god_mode_settings

    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    if not _is_interview_allowed(latest):
        raise HTTPException(403, "CEO Interview is not enabled.")

    responses = body.get("responses", [])
    if not responses:
        raise HTTPException(400, "No responses provided")
    # Guard against LLM abuse: cap response count and individual response length
    if len(responses) > 20:
        raise HTTPException(400, "Too many responses (max 20).")
    for r in responses:
        if isinstance(r, dict):
            ans = r.get("answer", r.get("response", ""))
            if isinstance(ans, str) and len(ans) > 3000:
                raise HTTPException(400, "Response too long (max 3000 characters per answer).")

    gs = latest.get("global_state", {})
    bus = latest.get("bu_states", [])
    flags = gs.get("active_event_flags", {})
    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")

    from ceo_interview import (
        get_interview_questions, calc_data_scores, blend_scores,
        generate_fallback_feedback, generate_score_rationale,
        get_ceo_persona, DIMENSIONS,
        score_responses_with_llm, calc_trajectory_modifiers,
        generate_evidence_citations, store_peer_scores,
        calc_peer_benchmarks, calc_calibration_gaps,
    )
    voice_gender = _god_mode_settings.get("ceo_interview_voice_gender", "female")
    persona = get_ceo_persona(voice_gender)

    questions = get_interview_questions(
        ending_pathway=ending_pathway,
        question_count=_god_mode_settings.get("ceo_interview_question_count", 5),
    )

    # Build the extra dict from R10 grand finale results
    extra = {
        "regenerative_multiple": flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)),
        "terminal_value": flags.get("terminal_value", gs.get("terminal_value", 0)),
        "profile_title": flags.get("profile_title", gs.get("profile_title", "Unknown")),
    }

    # Step 1: Calculate data-derived scores
    data_scores = calc_data_scores(extra, gs, bus, flags)

    # Step 1b: Apply trajectory modifiers (Improvement 2)
    round_history = await db.fetch_round_history(session_id)
    decision_log = await db.get_decision_log(session_id)
    trajectory = calc_trajectory_modifiers(round_history, decision_log)
    trajectory_adjusted_data = dict(data_scores)
    for dim_id, traj in trajectory.items():
        if dim_id in trajectory_adjusted_data:
            trajectory_adjusted_data[dim_id] = round(
                min(10, max(1, trajectory_adjusted_data[dim_id] * traj["modifier"])), 1
            )

    # Step 2: LLM-based response scoring (Improvement 1)
    response_scores = {}
    llm_feedback = None
    llm_used = False
    try:
        llm_result = await score_responses_with_llm(
            questions, responses, data_scores, extra
        )
        if llm_result and "dimension_scores" in llm_result:
            response_scores = {
                k: round(min(10, max(1, float(v))), 1)
                for k, v in llm_result["dimension_scores"].items()
            }
            llm_feedback = {
                "feedback_paragraphs": llm_result.get("feedback_paragraphs", []),
                "key_strengths": llm_result.get("key_strengths", []),
                "growth_areas": llm_result.get("growth_areas", []),
            }
            llm_used = True
            _log.info(f"[ceo-interview] LLM scoring successful via API")
    except Exception as e:
        _log.warning(f"[ceo-interview] LLM scoring failed: {e}")

    if not response_scores:
        # Fallback: noise-based scoring
        import random
        for dim_id in data_scores:
            base = data_scores[dim_id]
            noise = random.uniform(-1.0, 1.0)
            response_scores[dim_id] = round(min(10, max(1, base + noise)), 1)

    # Step 3: Blend scores (using trajectory-adjusted data scores)
    final_scores = blend_scores(trajectory_adjusted_data, response_scores)

    # Step 4: Generate score rationale
    score_rationale = generate_score_rationale(trajectory_adjusted_data, extra, gs, bus, flags)

    # Step 5: Generate evidence citations (Improvement 3)
    evidence_citations = generate_evidence_citations(decision_log, round_history, data_scores)

    # Step 6: Generate narrative feedback
    feedback = llm_feedback or generate_fallback_feedback(final_scores, extra)

    # Step 7: Self-assessment calibration (Improvement 5)
    self_assessment = flags.get("ceo_interview_self_assessment", {})
    calibration = calc_calibration_gaps(self_assessment, final_scores)

    # Step 8: Peer benchmarking (Improvement 4)
    parent_id = (await db.get_session_info(session_id) or {}).get("parent_cohort_id", session_id)
    store_peer_scores(parent_id, final_scores)
    peer_benchmarks = calc_peer_benchmarks(parent_id, final_scores)

    # Step 9: Persist the assessment in session flags
    try:
        flags["ceo_interview_completed"] = True
        flags["ceo_interview_scores"] = final_scores
        flags["ceo_interview_data_scores"] = trajectory_adjusted_data
        flags["ceo_interview_raw_data_scores"] = data_scores
        flags["ceo_interview_response_scores"] = response_scores
        flags["ceo_interview_score_rationale"] = score_rationale
        flags["ceo_interview_trajectory"] = trajectory
        flags["ceo_interview_evidence"] = evidence_citations
        flags["ceo_interview_llm_used"] = llm_used
        gs["active_event_flags"] = flags
        await db.update_latest_global_state(session_id, gs, bus)
    except Exception as e:
        _log.warning(f"[ceo-interview] Failed to persist assessment: {e}")

    return {
        "session_id": session_id,
        "dimensions": DIMENSIONS,
        "final_scores": final_scores,
        "data_scores": trajectory_adjusted_data,
        "raw_data_scores": data_scores,
        "response_scores": response_scores,
        "score_rationale": score_rationale,
        "trajectory": trajectory,
        "evidence_citations": evidence_citations,
        "calibration": calibration,
        "peer_benchmarks": peer_benchmarks,
        "feedback": feedback,
        "persona": persona,
        "llm_used": llm_used,
    }


@router.get("/{session_id}/ceo-interview/results", summary="Get stored interview results")
async def get_interview_results(session_id: str, request: Request):
    """Retrieve previously completed CEO interview results with all enrichment data."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    flags = latest.get("global_state", {}).get("active_event_flags", {})
    if not flags.get("ceo_interview_completed"):
        raise HTTPException(404, "No CEO interview results found for this session")

    from ceo_interview import (
        get_ceo_persona, DIMENSIONS, generate_fallback_feedback,
        generate_score_rationale, calc_peer_benchmarks, calc_calibration_gaps,
    )
    from admin_shared import _god_mode_settings as _gms
    voice_gender = _gms.get("ceo_interview_voice_gender", "female")
    persona = get_ceo_persona(voice_gender)

    final_scores = flags.get("ceo_interview_scores", {})
    extra = {
        "regenerative_multiple": flags.get("regenerative_multiple", 1.0),
        "terminal_value": flags.get("terminal_value", 0),
        "profile_title": flags.get("profile_title", "Unknown"),
    }

    # Retrieve or regenerate score rationale
    score_rationale = flags.get("ceo_interview_score_rationale")
    if not score_rationale:
        gs = latest.get("global_state", {})
        bus = latest.get("bu_states", [])
        data_scores = flags.get("ceo_interview_data_scores", {})
        score_rationale = generate_score_rationale(data_scores, extra, gs, bus, flags)

    # Re-calc calibration if self-assessment exists
    self_assessment = flags.get("ceo_interview_self_assessment", {})
    calibration = calc_calibration_gaps(self_assessment, final_scores)

    # Re-calc peer benchmarks
    parent_id = (await db.get_session_info(session_id) or {}).get("parent_cohort_id", session_id)
    peer_benchmarks = calc_peer_benchmarks(parent_id, final_scores)

    return {
        "session_id": session_id,
        "dimensions": DIMENSIONS,
        "final_scores": final_scores,
        "data_scores": flags.get("ceo_interview_data_scores", {}),
        "raw_data_scores": flags.get("ceo_interview_raw_data_scores", {}),
        "response_scores": flags.get("ceo_interview_response_scores", {}),
        "score_rationale": score_rationale,
        "trajectory": flags.get("ceo_interview_trajectory", {}),
        "evidence_citations": flags.get("ceo_interview_evidence", {}),
        "calibration": calibration,
        "peer_benchmarks": peer_benchmarks,
        "feedback": generate_fallback_feedback(final_scores, extra),
        "persona": persona,
        "llm_used": flags.get("ceo_interview_llm_used", False),
        "completed": True,
    }


@router.post("/{session_id}/ceo-interview/self-assessment", summary="Submit self-assessment ratings")
async def submit_self_assessment(request: Request, session_id: str, body: dict):
    """Store player's self-rated dimension scores before the interview.

    Body: { "ratings": { "strategic_thinking": 7.0, ... } }
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    ratings = body.get("ratings", {})
    if not ratings:
        raise HTTPException(400, "Missing ratings object")

    gs = latest.get("global_state", {})
    bus = latest.get("bu_states", [])
    flags = gs.get("active_event_flags", {})
    flags["ceo_interview_self_assessment"] = ratings
    gs["active_event_flags"] = flags
    await db.update_latest_global_state(session_id, gs, bus)
    return {"status": "ok", "stored_dimensions": list(ratings.keys())}


@router.post("/{session_id}/ceo-interview/adaptive-questions", summary="Get personalised interview questions")
async def get_adaptive_questions(request: Request, session_id: str):
    """Generate interview questions tailored to the player's weak dimensions.

    Requires data scores to have been pre-calculated (calls calc_data_scores internally).
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    gs = latest.get("global_state", {})
    bus = latest.get("bu_states", [])
    flags = gs.get("active_event_flags", {})
    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")

    from ceo_interview import calc_data_scores, generate_adaptive_questions, get_ceo_persona
    from admin_shared import _god_mode_settings
    extra = {
        "regenerative_multiple": flags.get("regenerative_multiple", gs.get("regenerative_multiple", 1.0)),
        "terminal_value": flags.get("terminal_value", gs.get("terminal_value", 0)),
        "profile_title": flags.get("profile_title", gs.get("profile_title", "Unknown")),
    }
    data_scores = calc_data_scores(extra, gs, bus, flags)
    questions = generate_adaptive_questions(
        data_scores, ending_pathway,
        _god_mode_settings.get("ceo_interview_question_count", 5),
    )
    voice_gender = _god_mode_settings.get("ceo_interview_voice_gender", "female")
    return {
        "questions": questions,
        "data_scores_preview": data_scores,
        "persona": get_ceo_persona(voice_gender),
    }


@router.post("/{session_id}/ceo-interview/what-if", summary="Counterfactual 'What-If' analysis")
async def what_if_analysis(request: Request, session_id: str, body: dict):
    """Run a lightweight counterfactual scenario.

    Body: { "round": 5, "dimension": "stakeholder_empathy", "scenario": "What if I had invested in community fund earlier?" }
    Returns estimated score deltas.
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    target_round = body.get("round", 5)
    dimension = body.get("dimension", "")
    scenario_text = body.get("scenario", "")

    gs = latest.get("global_state", {})
    flags = gs.get("active_event_flags", {})
    final_scores = flags.get("ceo_interview_scores", {})

    # Simplified counterfactual model — estimates impact of earlier ethical/strategic decisions
    counterfactual = {}
    for dim_id, current_score in final_scores.items():
        # The earlier the intervention, the bigger the potential impact
        round_bonus = max(0, (10 - target_round) * 0.15)
        projected = min(10, current_score + round_bonus) if dim_id == dimension else current_score
        counterfactual[dim_id] = round(projected, 1)

    delta = {
        dim_id: round(counterfactual.get(dim_id, 0) - final_scores.get(dim_id, 0), 1)
        for dim_id in final_scores
    }

    return {
        "original_scores": final_scores,
        "counterfactual_scores": counterfactual,
        "deltas": delta,
        "target_round": target_round,
        "target_dimension": dimension,
        "insight": f"Had you acted on '{dimension.replace('_', ' ')}' in Round {target_round} instead of later, "
                   f"your score could have improved by approximately +{delta.get(dimension, 0):.1f} points. "
                   f"Earlier interventions compound through the remaining rounds.",
    }


@router.post("/{session_id}/ceo-interview/tts", summary="Synthesize CEO voice audio")
async def synthesize_ceo_voice(request: Request, session_id: str, body: dict):
    """Synthesize speech for a CEO interview text segment.
    
    Body: { "text": "...", "voice_id": "..." (optional) }
    Returns: { "audio_b64": "..." } — base64-encoded MP3
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    from admin_shared import _god_mode_settings
    tts_latest = await db.fetch_latest_state(session_id)
    if not tts_latest:
        raise HTTPException(404, "Session not found")
    if not _is_interview_allowed(tts_latest):
        raise HTTPException(403, "CEO Interview is not enabled.")

    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided")
    if len(text) > 2000:
        raise HTTPException(400, "Text too long (max 2000 characters).")

    # Resolve voice from god-mode settings if not explicitly provided
    voice_id = body.get("voice_id")
    if not voice_id:
        from ceo_interview import get_ceo_persona
        voice_gender = _god_mode_settings.get("ceo_interview_voice_gender", "female")
        persona = get_ceo_persona(voice_gender)
        voice_id = persona.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM")

    from elevenlabs_tts import synthesize_speech
    audio_b64 = await synthesize_speech(text=text, voice_id=voice_id)

    if audio_b64 is None:
        raise HTTPException(503, "Voice synthesis unavailable. Check ElevenLabs API key.")

    return {
        "audio_b64": audio_b64,
        "voice_id": voice_id,
        "text_length": len(text),
    }


@router.get("/elevenlabs/status", summary="Check ElevenLabs API status")
async def elevenlabs_status():
    """Check if ElevenLabs API is available and return subscription info."""
    from elevenlabs_tts import check_api_status
    return await check_api_status()


# ─────────────────────────────────────────────────────────────────
# ENGAGEMENT 7.3: Industry Benchmarks
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/benchmarks", summary="ESG Industry Benchmarks comparison")
async def get_industry_benchmarks(session_id: str, request: Request):
    """Compare simulation metrics against real FTSE 100 ESG benchmarks."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    current = await db.fetch_latest_state(session_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from benchmarks import get_benchmarks
    return get_benchmarks(current["bu_states"], current["global_state"])


# ─────────────────────────────────────────────────────────────────
# ENGAGEMENT 7.5: Peer Decision Reveal
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/peer-stats/{round_number}", summary="Aggregate peer decision stats")
async def get_peer_stats(session_id: str, request: Request, round_number: int):
    """
    After all players commit a round, reveal aggregate statistics:
    choice distribution and average investment ratio.
    Only available for completed rounds.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find parent cohort
    parent_id = session_info.get("parent_cohort_id") or session_id
    children = await db.get_child_sessions(parent_id)
    if not children:
        return {"available": False, "reason": "No peer sessions found"}

    # Check all players have committed this round
    all_committed = True
    for child in children:
        child_state = await db.fetch_latest_state(child["session_id"])
        if child_state and child_state.get("round_number", 1) <= round_number:
            all_committed = False
            break

    if not all_committed:
        return {"available": False, "reason": "Not all peers have committed this round yet"}

    # Aggregate decision data from logs
    decision_log = await db.get_decision_log(parent_id)
    round_decisions = [d for d in decision_log if d.get("round_number") == round_number]

    if not round_decisions:
        return {"available": False, "reason": "No decisions found for this round"}

    # Choice distribution
    choice_counts: dict[str, int] = {}
    total_capex = 0.0
    total_investment_ratio = 0.0
    decision_count = 0

    for dec in round_decisions:
        choice = dec.get("choice_selected", "")
        if choice:
            choice_counts[choice] = choice_counts.get(choice, 0) + 1
        total_capex += dec.get("capex_allocated", 0)
        total_investment_ratio += dec.get("investment_ratio", 0) if hasattr(dec, 'get') else 0
        decision_count += 1

    total_choices = sum(choice_counts.values()) or 1
    choice_distribution = {
        k: round(v / total_choices * 100, 1)
        for k, v in choice_counts.items()
    }

    return {
        "available": True,
        "round_number": round_number,
        "peer_count": len(children),
        "choice_distribution": choice_distribution,
        "most_popular_choice": max(choice_counts, key=choice_counts.get) if choice_counts else None,
        "avg_capex": round(total_capex / max(decision_count, 1), 2),
        "avg_investment_ratio": round(total_investment_ratio / max(decision_count, 1), 4),
        "total_decisions_logged": decision_count,
        "note": "Anonymised aggregate — individual player decisions are not revealed.",
    }


# ─────────────────────────────────────────────────────────────────
# ITEM 5: Cohort Pace Lock
# ─────────────────────────────────────────────────────────────────

@router.put("/{session_id}/pace-lock", summary="Set cohort pace lock")
async def set_pace_lock(request: Request, session_id: str, body: dict, _guard: None = Depends(require_facilitator)):
    """Set the maximum round players can advance to. Facilitator control."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    max_round = body.get("max_round")
    if max_round is not None:
        if not isinstance(max_round, int) or max_round < 1 or max_round > 10:
            raise HTTPException(status_code=400, detail="max_round must be 1-10")
    session_info["max_round"] = max_round
    return {"session_id": session_id, "max_round": max_round}


# ─────────────────────────────────────────────────────────────────
# ITEM 19: Round Timer
# ─────────────────────────────────────────────────────────────────

@router.put("/{session_id}/round-timer", summary="Set round deadline")
async def set_round_timer(request: Request, session_id: str, body: dict, _guard: None = Depends(require_facilitator)):
    """Set a deadline (Unix timestamp) for the current round. Auto-locks on expiry."""
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    deadline = body.get("deadline")  # Unix timestamp or null to clear
    session_info["round_deadline"] = deadline
    return {"session_id": session_id, "round_deadline": deadline}


# ─────────────────────────────────────────────────────────────────
# ITEM 24: Facilitator Commit Notifications
# ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/commit-notifications", summary="Get recent commit notifications")
async def get_commit_notifications(session_id: str, request: Request):
    """Return recent player commit notifications for the facilitator dashboard."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    session_info = await db.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    notifications = session_info.get("commit_notifications", [])
    return {
        "session_id": session_id,
        "notifications": notifications[-20:],  # Last 20
        "total": len(notifications),
    }


# ═══════════════════════════════════════════════════════════════
#  NEW ENGINE ENDPOINTS
#  API surface for the improvement modules implemented in Batch 1-3.
# ═══════════════════════════════════════════════════════════════

# ── SI-4: TCFD Scenario Analysis ──────────────────────────────

@router.get(
    "/{session_id}/tcfd-scenarios",
    summary="Run TCFD climate scenario analysis on current portfolio",
)
async def get_tcfd_scenarios(session_id: str, request: Request, scenario_id: str = None):
    """
    Run TCFD-aligned climate scenario analysis.
    If scenario_id is provided, run that single scenario.
    Otherwise, run all three and return a comparison matrix.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    bio_state = gs.get("biodiversity_state")

    from tcfd_scenarios import run_scenario_analysis, get_scenario_comparison

    if scenario_id:
        result = run_scenario_analysis(scenario_id, bus, gs, bio_state)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    else:
        return get_scenario_comparison(bus, gs, bio_state)


# ── SE-1: Board Governance — Vote on Resolution ──────────────

@router.post(
    "/{session_id}/board-vote",
    summary="Submit a board vote on a shareholder resolution",
)
async def board_vote(request: Request, session_id: str, body: dict):
    """
    Vote on a pending shareholder resolution.
    Body: { "resolution_id": "...", "recommendation": "support" | "oppose" }
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    board = gs.get("board_governance")
    if not board:
        raise HTTPException(status_code=400, detail="Board governance not initialised")

    resolution_id = body.get("resolution_id")
    recommendation = body.get("recommendation", "support")

    from board_governance import simulate_board_vote, SHAREHOLDER_RESOLUTIONS

    resolution = next((r for r in SHAREHOLDER_RESOLUTIONS if r["id"] == resolution_id), None)
    if not resolution:
        raise HTTPException(status_code=404, detail=f"Resolution '{resolution_id}' not found")

    result = simulate_board_vote(board, resolution, recommendation, gs)

    # Apply impacts if passed
    if result["passed"]:
        impacts = result.get("impact", {})
        if "reputation" in impacts:
            gs["group_reputation"] = min(100, round(gs.get("group_reputation", 50) + impacts["reputation"], 2))
        if "esg_linked_compensation_pct" in impacts:
            board["esg_linked_compensation_pct"] = impacts["esg_linked_compensation_pct"]
        if "tnfd_level" in impacts:
            bio = gs.get("biodiversity_state", {})
            bio["tnfd_disclosure_level"] = impacts["tnfd_level"]

        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - result.get("cost", 0), 2)

    # Persist
    gs["board_governance"] = board
    await db.update_latest_global_state(session_id, gs, bus)

    return result


# ── SE-2: Supply Chain — Conduct Audit ────────────────────────

@router.post(
    "/{session_id}/supply-chain-audit",
    summary="Conduct a supply chain due diligence audit",
)
async def supply_chain_audit(request: Request, session_id: str, body: dict):
    """
    Conduct a supply chain audit.
    Body: { "audit_depth": 1 | 2 | 3 }
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    sc = gs.get("supply_chain")
    if not sc:
        raise HTTPException(status_code=400, detail="Supply chain not initialised")

    audit_depth = body.get("audit_depth", 1)
    if audit_depth not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="audit_depth must be 1, 2, or 3")

    from supply_chain_network import conduct_supply_chain_audit

    result = conduct_supply_chain_audit(sc, audit_depth, gs)
    gs["supply_chain"] = sc
    await db.update_latest_global_state(session_id, gs, bus)

    return result


# ── SI-5: Org Politics — Coalition Check ──────────────────────

@router.post(
    "/{session_id}/coalition-check",
    summary="Check C-suite coalition support for a decision",
)
async def coalition_check(request: Request, session_id: str, body: dict):
    """
    Check which C-suite members support or oppose a proposed decision.
    Body: { "decision_tags": ["cost_reduction", "science_based_targets"], "estimated_cost": 5000000 }
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    org = gs.get("org_politics")
    if not org:
        raise HTTPException(status_code=400, detail="Org politics not initialised")

    from org_politics import evaluate_csuite_support

    result = evaluate_csuite_support(
        org,
        body.get("decision_tags", []),
        body.get("estimated_cost", 0),
        gs,
    )
    return result


# ── Meadows Leverage Points — Full Session Analysis ──────────

@router.get(
    "/{session_id}/leverage-analysis",
    summary="Meadows leverage points analysis for debrief",
)
async def leverage_analysis(session_id: str, request: Request):
    """
    Analyse the full session against Meadows' 12 Leverage Points.
    Best used post-game for debrief.
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]

    from meadows_leverage import (
        analyse_session_leverage_points,
        detect_archetypes,
        classify_learning_loop,
    )

    decision_history = gs.get("decision_history", [])
    leverage = analyse_session_leverage_points(decision_history, gs, bus)

    flags = gs.get("active_event_flags", {})
    archetypes = detect_archetypes(gs, bus, flags)

    mental_model_history = gs.get("mental_model_history", [])
    learning_loop = classify_learning_loop(mental_model_history, decision_history)

    return {
        "leverage_analysis": leverage,
        "system_archetypes": archetypes,
        "learning_loop_classification": learning_loop,
        "theory_reference": "Meadows, D. (2008). Thinking in Systems: A Primer.",
    }


# ── SE-8: Dynamic Cases ──────────────────────────────────────

@router.get(
    "/{session_id}/contextual-cases",
    summary="Get context-aware real-world case studies",
)
async def get_contextual_cases(session_id: str, request: Request, max_cases: int = 3):
    """Return real-world case studies relevant to the player's current state."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    round_number = latest.get("round_number", 1)

    from dynamic_cases import select_contextual_cases

    cases = select_contextual_cases(gs, bus, round_number, max_cases=max_cases)
    return {"cases": cases, "round": round_number}


# ── SE-7: Regulatory Sandbox — Activate Regulation ───────────

@router.post(
    "/{session_id}/regulatory-sandbox/activate",
    summary="Activate a regulatory instrument in sandbox mode",
)
async def activate_regulation(request: Request, session_id: str, body: dict):
    """
    Activate a regulation in the sandbox.
    Body: { "instrument_id": "carbon_tax", "parameters": {"rate_per_tonne": 75} }
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]

    from regulatory_sandbox import create_sandbox_state, activate_regulation as _activate, REGULATORY_INSTRUMENTS

    if "regulatory_sandbox" not in gs:
        gs["regulatory_sandbox"] = create_sandbox_state()
        gs["regulatory_sandbox"]["sandbox_mode"] = True

    sandbox = gs["regulatory_sandbox"]
    instrument_id = body.get("instrument_id")
    custom_params = body.get("parameters", {})
    round_number = latest.get("round_number", 1)

    result = _activate(sandbox, instrument_id, custom_params, round_number)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    gs["regulatory_sandbox"] = sandbox
    await db.update_latest_global_state(session_id, gs, bus)

    # Audit log — captured in GodModeAuditLog under 🧪 Sandbox filter
    try:
        from admin_router import _audit as _god_audit
        _god_audit(
            "regulatory_sandbox_activated",
            actor="facilitator",
            details={
                "session_id": session_id,
                "instrument_id": instrument_id,
                "parameters": custom_params,
                "round": round_number,
                "complexity_index": result.get("complexity_index"),
                "capture_risk": result.get("capture_risk"),
            },
        )
    except Exception:
        pass  # Non-critical — don't let audit failure break the activation

    return result



@router.get(
    "/{session_id}/regulatory-sandbox/instruments",
    summary="List available regulatory instruments",
)
async def list_instruments(session_id: str, request: Request):
    """Return all available regulatory instruments and their parameters."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from regulatory_sandbox import REGULATORY_INSTRUMENTS
    return {"instruments": REGULATORY_INSTRUMENTS}


@router.get(
    "/{session_id}/regulatory-sandbox/exogenous-events",
    summary="List available exogenous crisis events",
)
async def list_exogenous_events(session_id: str, request: Request):
    """Return all configurable exogenous events with trigger conditions."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    from regulatory_sandbox import EXOGENOUS_EVENTS
    latest = await db.fetch_latest_state(session_id)
    sandbox = {}
    if latest:
        sandbox = latest["global_state"].get("regulatory_sandbox", {})
    events_out = []
    for eid, cfg in EXOGENOUS_EVENTS.items():
        fired_key = f"exogenous_{eid}_fired"
        events_out.append({
            "event_id": eid,
            "name": cfg["name"],
            "description": cfg["description"],
            "trigger_rounds": cfg["trigger_rounds"],
            "trigger_conditions": cfg["trigger_conditions"],
            "effects": cfg["effects"],
            "theory": cfg["theory"],
            "icon": cfg["icon"],
            "severity": cfg["severity"],
            "already_fired": sandbox.get(fired_key),
        })
    return {"exogenous_events": events_out}


@router.post(
    "/{session_id}/regulatory-sandbox/trigger-event",
    summary="God Mode: Force-trigger an exogenous crisis event",
)
async def trigger_exogenous(request: Request, session_id: str, body: dict, _guard: None = Depends(require_facilitator)):
    """
    Facilitator God Mode — manually fire an exogenous event.
    Body: { "event_id": "carbon_minsky_moment" }
    Bypasses trigger conditions. Requires sandbox to be active.
    """
    # SEC-AUDIT-2026-07-29: bind the caller to this session. These handlers
    # previously took no `request`, so NO ownership check could run and any
    # anonymous caller holding a session id could mutate another team's run
    # (proven: board-vote moved a victim's group_reputation and treasury).
    await _assert_player_owns_session(request, session_id)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")

    gs = latest["global_state"]
    bus = latest["bu_states"]
    round_number = latest.get("round_number", 1)

    from regulatory_sandbox import (
        create_sandbox_state, trigger_exogenous_event,
    )

    if "regulatory_sandbox" not in gs:
        gs["regulatory_sandbox"] = create_sandbox_state()
        gs["regulatory_sandbox"]["sandbox_mode"] = True

    sandbox = gs["regulatory_sandbox"]
    event_id = body.get("event_id")
    events = {}

    result = trigger_exogenous_event(
        event_id, sandbox, gs, bus, events, round_number
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    gs["regulatory_sandbox"] = sandbox
    await db.update_latest_global_state(session_id, gs, bus)

    # Audit log
    try:
        from admin_router import _audit as _god_audit
        _god_audit(
            "exogenous_event_triggered",
            actor="facilitator",
            details={
                "session_id": session_id,
                "event_id": event_id,
                "round": round_number,
                "result": result,
            },
        )
    except Exception:
        pass

    return result


# ── Biodiversity & Balance Sheet Data ─────────────────────────

@router.get(
    "/{session_id}/biodiversity",
    summary="Get biodiversity state and history",
)
async def get_biodiversity(session_id: str, request: Request):
    """Return the current biodiversity state for the session."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    bio = latest["global_state"].get("biodiversity_state", {})
    return {"biodiversity": bio}


@router.get(
    "/{session_id}/balance-sheet",
    summary="Get balance sheet state and history",
)
async def get_balance_sheet(session_id: str, request: Request):
    """Return the current balance sheet for the session.
    Auto-initializes from BU states if not yet created by engine tick."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    gs = latest["global_state"]
    bs = gs.get("balance_sheet")
    if not bs or not bs.get("total_assets"):
        # Initialize balance sheet from current BU states so dashboard shows data pre-commit
        try:
            from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
            bus = latest["bu_states"]
            bs = create_initial_balance_sheet(bus)
            # Sync cash from treasury
            bs["current_assets"]["cash_and_equivalents"] = gs.get("corporate_treasury", 0)
            # Run one tick to populate totals
            bs, _ = process_balance_sheet_tick(
                bs, gs, bus,
                {"csf_this_round": 0, "total_capex_allocated": 0, "dividends_paid": 0,
                 "remediation_events": [], "tipping_tier": "none"},
                latest.get("round_number", 1),
            )
            gs["balance_sheet"] = bs
            await db.update_latest_global_state(session_id, gs, bus)
        except Exception:
            bs = {}
    return {"balance_sheet": bs}


@router.get(
    "/{session_id}/board-governance",
    summary="Get board governance state",
)
async def get_board_governance(session_id: str, request: Request):
    """Return board composition, effectiveness, and governance history."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    board = latest["global_state"].get("board_governance", {})
    return {"board_governance": board}


@router.get(
    "/{session_id}/supply-chain",
    summary="Get supply chain network state",
)
async def get_supply_chain(session_id: str, request: Request):
    """Return the 3-tier supply chain network state."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    sc = latest["global_state"].get("supply_chain", {})
    return {"supply_chain": sc}


@router.get(
    "/{session_id}/npc-stakeholders",
    summary="Get NPC stakeholder states",
)
async def get_npc_stakeholders(session_id: str, request: Request):
    """Return all NPC stakeholder satisfaction and actions."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Session not found")
    npc = latest["global_state"].get("npc_stakeholders", {})
    return {"npc_stakeholders": npc}



# ── Extended Horizon Mode — RETIRED (F-32, launch audit 2026-09-01) ──────
# Rounds 11–20 were dead end-to-end: this endpoint inserted round 11 and
# cleared game_over, but _commit_turn_impl refuses current_round > 10, the
# Postgres schema has CHECK (round_number BETWEEN 1 AND 10), and the cockpit
# treats current_round > 10 as game over — so activation produced a session
# nobody could play (409 on the memory store, 500 on Postgres). Owner ruling
# 2026-09-02: remove rather than build out. The route answers 410 so a stale
# client gets a clear message instead of a half-mutated run.

@router.post(
    "/{session_id}/extend",
    summary="Retired: Extended Horizon Mode (rounds 11–20) has been removed",
    status_code=status.HTTP_410_GONE,
)
async def activate_extended_mode(request: Request, session_id: str):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={"code": "extended_horizon_removed",
                "message": "Extended Horizon (rounds 11–20) has been removed. The simulation is ten rounds."},
    )


# ═════════════════════════════════════════════════════════════════
#  PLAYER-FACING ANNOTATIONS — Facilitator notes visible to students
#  Visibility controlled by facilitator via admin toggle.
# ═════════════════════════════════════════════════════════════════

@router.get("/{session_id}/annotations", summary="Get annotations visible to the player")
async def get_player_annotations(session_id: str, request: Request):
    """Returns annotations for this session that the facilitator has
    marked as visible to students. Respects the session-level visibility toggle."""
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    import database_memory as db_mem
    from admin_router import _annotations

    # Find the parent cohort session to check visibility toggle
    sess = db_mem._sessions.get(session_id, {})
    parent_id = sess.get("parent_cohort_id", session_id)
    parent_sess = db_mem._sessions.get(parent_id, sess)

    # Check if facilitator has enabled annotations visibility for students
    if not parent_sess.get("annotations_player_visible", False):
        return {"annotations": []}

    # Get annotations for the parent cohort (not the player sub-session)
    all_annotations = _annotations.get(parent_id, [])

    # Filter to those explicitly marked as visible_to_students (or all if the toggle is on)
    visible = [
        a for a in all_annotations
        if a.get("visible_to_students", True)  # Default to visible when toggle is on
    ]

    return {"annotations": visible}


# ═════════════════════════════════════════════════════════════════
#  WOW-5E: FRONT PAGE — LLM-ENHANCED NEWSPAPER GENERATION
# ═════════════════════════════════════════════════════════════════

# Deterministic fallback templates (same as FrontPageReveal.js)
_FP_TEMPLATES = {
    "titan": {
        "headline": "MURESSONS CROWNED SUSTAINABILITY LEADER OF THE DECADE",
        "subhead": "Regenerative strategy compounds into a {tv}M valuation as the board's five-year bet pays off",
        "quote": "A textbook case that decarbonisation and value creation are the same story.",
    },
    "safe": {
        "headline": "MURESSONS DELIVERS STEADY, DE-RISKED RETURNS",
        "subhead": "A pragmatic five years leaves the group well-capitalised at {tv}M with room to push further",
        "quote": "Solid, defensible, and unspectacular — exactly what nervous boards asked for.",
    },
    "fragile": {
        "headline": "QUESTIONS MOUNT OVER MURESSONS' RESILIENCE",
        "subhead": "A {tv}M valuation masks a fragile {mr}× multiple as deferred costs come due",
        "quote": "The bill for short-termism arrives late, larger, and with fewer options.",
    },
    "relic": {
        "headline": "MURESSONS FACES STRANDED-ASSET RECKONING",
        "subhead": "Five years of extraction leave a {mr}× multiple and a valuation under pressure at {tv}M",
        "quote": "A cautionary tale of value destroyed one deferred decision at a time.",
    },
}


def _fp_band(mr: float) -> str:
    if mr >= 1.8:
        return "titan"
    if mr >= 1.2:
        return "safe"
    if mr >= 0.8:
        return "fragile"
    return "relic"


@router.get(
    "/{session_id}/front-page",
    summary="WOW-5E: Generate newspaper front page copy (LLM-enhanced with deterministic fallback)",
)
async def get_front_page(session_id: str, request: Request):
    """
    Returns headline, subhead, and quote for the Year-5 front page.

    If LLM_API_KEY is set → calls the LLM for creative, game-state-aware copy.
    If LLM_API_KEY is unset, call times out, or response is malformed →
    falls back to deterministic per-archetype templates (always works).
    """
    await _assert_player_owns_session(request, session_id, allow_observer=True)  # F-22/F-23 (launch audit 2026-09-01)
    latest = await db.fetch_latest_state(session_id)
    if not latest:
        raise HTTPException(404, "Session not found")

    gs = latest["global_state"]
    flags = gs.get("active_event_flags", {})
    mr = float(flags.get("regenerative_multiple", 0) or 0)
    tv_raw = float(flags.get("terminal_value", 0) or 0)
    tv = f"${tv_raw / 1_000_000:.1f}"
    mr_str = f"{mr:.2f}"
    band = _fp_band(mr)

    # Deterministic fallback
    tpl = _FP_TEMPLATES.get(band, _FP_TEMPLATES["fragile"])
    fallback = {
        "headline": tpl["headline"],
        "subhead": tpl["subhead"].format(tv=tv, mr=mr_str),
        "quote": tpl["quote"],
        "source": "deterministic",
        "band": band,
        "mr": mr_str,
        "terminal_value": tv,
    }

    # ── Try LLM enhancement ──
    try:
        from config import LLM_API_KEY, LLM_PROVIDER, LLM_MODEL
    except ImportError:
        return fallback

    if not LLM_API_KEY:
        return fallback

    # Build context for LLM
    archetype = flags.get("shadow_board_archetype", band)
    share_price = flags.get("price_per_share", "—")
    rep = gs.get("group_reputation", 50)
    notable_flags_list = [
        k for k in flags
        if k not in ("terminal_value", "regenerative_multiple", "price_per_share",
                      "shadow_board_completed", "shadow_board_archetype", "shadow_board_rejection",
                      "sdg_impact_score")
        and flags[k] is True
    ]

    prompt = (
        f"You are a senior financial journalist at The Muressons Times.\n"
        f"Write a Year-5 front page for a company with these results:\n"
        f"- Regenerative Multiple (M_R): {mr_str}× (band: {band})\n"
        f"- Terminal Value: {tv}\n"
        f"- Share Price: ${share_price}\n"
        f"- Reputation: {rep}/100\n"
        f"- Archetype: {archetype}\n"
        f"- Notable achievements: {', '.join(notable_flags_list[:8]) if notable_flags_list else 'none'}\n\n"
        f"Return a JSON object with exactly these keys:\n"
        f"  headline: a punchy ALL-CAPS newspaper headline (max 12 words)\n"
        f"  subhead: an italic subheadline (max 25 words)\n"
        f"  quote: a fictional analyst quote (max 20 words)\n\n"
        f"Respond ONLY with the JSON object, no markdown fences."
    )

    try:
        import httpx
        import json as _json

        if LLM_PROVIDER == "anthropic":
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": LLM_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL or "claude-sonnet-4-20250514",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                body = res.json()
                text = body.get("content", [{}])[0].get("text", "")
        else:  # openai
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL or "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"},
                    },
                )
                body = res.json()
                text = body["choices"][0]["message"]["content"]

        # Parse + validate
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = _json.loads(text)

        # Validate required keys
        if not all(k in result for k in ("headline", "subhead", "quote")):
            _log.warning(f"[WOW-5E] LLM response missing keys, falling back: {result}")
            return fallback

        return {
            "headline": str(result["headline"])[:200],
            "subhead": str(result["subhead"])[:300],
            "quote": str(result["quote"])[:200],
            "source": "llm",
            "band": band,
            "mr": mr_str,
            "terminal_value": tv,
        }
    except Exception as e:
        _log.warning(f"[WOW-5E] LLM front-page error, using deterministic fallback: {e}")
        return fallback


def _apply_pillar_aggregate_impacts(
    new_global: dict, new_bus: list, events: dict,
    agg_impacts: dict, effectiveness: float,
) -> None:
    """Apply the aggregated pillar impacts (R1-R9 pillar-mode single source).

    Moved verbatim out of commit_turn (2026-08-31, fix/pillar-impact-
    ownership) so the application — and the R10 skip at the call site — is
    directly unit-testable. Reputation lands on the group; the per-BU deltas
    are distributed proportionally to revenue weight; all strategic impacts
    scale by workforce effectiveness (costs never do).
    """
    rep_delta = round(agg_impacts.get("reputation", 0) * effectiveness, 2)
    if rep_delta != 0:
        new_global["group_reputation"] = max(0, min(100, round(new_global["group_reputation"] + rep_delta, 2)))

    total_revenue = sum(bu.get("revenue_base", 0) for bu in new_bus)
    num_bus = len(new_bus)

    def _get_weight(bu_data: dict) -> float:
        if total_revenue <= 0 or num_bus == 0:
            return 1.0 / max(1, num_bus)
        return bu_data.get("revenue_base", 0) / total_revenue

    ncd_delta = round(agg_impacts.get("natural_capital_debt_delta", 0) * effectiveness, 2)
    if ncd_delta != 0:
        for bu in new_bus:
            proportional_ncd = ncd_delta * _get_weight(bu) * num_bus
            bu["natural_capital_debt"] = max(0, round(bu.get("natural_capital_debt", 0) + proportional_ncd, 2))

    ci_delta = round(agg_impacts.get("carbon_intensity_delta", 0) * effectiveness, 2)
    if ci_delta != 0:
        for bu in new_bus:
            proportional_ci = ci_delta * _get_weight(bu) * num_bus
            bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + proportional_ci, 2))

    sl_delta = round(agg_impacts.get("social_license_delta", 0) * effectiveness, 2)
    if sl_delta != 0:
        for bu in new_bus:
            proportional_sl = sl_delta * _get_weight(bu) * num_bus
            bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + proportional_sl, 2)))

    gov_delta = round(agg_impacts.get("governance_risk_delta", 0) * effectiveness, 2)
    if gov_delta != 0:
        for bu in new_bus:
            proportional_gov = gov_delta * _get_weight(bu) * num_bus
            bu["governance_risk_score"] = max(0, min(100, round(bu.get("governance_risk_score", 0) + proportional_gov, 2)))

    wd_delta = round(agg_impacts.get("water_dependency_delta", 0) * effectiveness, 2)
    if wd_delta != 0:
        for bu in new_bus:
            proportional_wd = wd_delta * _get_weight(bu) * num_bus
            bu["water_dependency"] = max(0, round(bu.get("water_dependency", 0) + proportional_wd, 2))

    burnout_delta = agg_impacts.get("burnout_delta", 0)
    if burnout_delta != 0:
        for bu in new_bus:
            current_bo = bu.get("staff_burnout_index", 0.0)
            bu["staff_burnout_index"] = max(0.0, min(100.0, round(current_bo + burnout_delta, 2)))
        events["pillar_burnout_delta_applied"] = burnout_delta

    # Revenue delta (SPEC_Pillar_Revenue_Impacts v2, 2026-08-31): flat per BU
    # like the legacy convention, scaled by effectiveness, floored at 0.
    # Applied LAST so the revenue-weighted deltas above keep the round's
    # incoming revenue distribution as their basis. This is the deliberate
    # replacement for the revenue the pre-fix leak was accidentally
    # providing pillar cohorts.
    rev_delta = round(agg_impacts.get("revenue_delta", 0) * effectiveness, 2)
    if rev_delta != 0:
        for bu in new_bus:
            bu["revenue_base"] = max(0, round(bu.get("revenue_base", 0) + rev_delta, 2))
        events["pillar_revenue_delta_applied"] = rev_delta
