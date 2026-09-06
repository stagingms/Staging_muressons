"""
Muressons Global Corporation - Admin Analytics Sub-Router (ARCH-002)
Extracted from admin_router.py to reduce monolith size.

Contains:
  - Analytics Visibility settings (God Mode + per-cohort)
  - Platform-wide Analytics (decision heatmap, trajectories, convergence, learning)
  - Player-scoped Analytics (per-session KPI deep-dive)
  - Glossary CRUD
  - 8 API endpoints
"""
from __future__ import annotations

import math
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel

import database as db
import database_memory
from admin_shared import _god_mode_settings, _get_session_paradigm, _facilitator_registry, get_role

analytics_router = APIRouter(prefix="/api/admin", tags=["Admin - Analytics"])


def _get_fac_role(request: Request):
    """C6: delegate to the SINGLE canonical resolver in admin_router so the
    god_mode (level 4) and project_admin virtual accounts, token-version
    revocation, and immediate registry re-validation all behave identically
    here. This module previously carried a stale copy whose token-role
    allow-list ("super_admin","admin","facilitator") silently dropped god_mode
    once it became a distinct tier — de-duplicated to prevent that class of
    drift entirely."""
    from admin_router import get_fac_role as _canonical_get_fac_role
    return _canonical_get_fac_role(request)


def _require_super_admin(role: str = Depends(_get_fac_role)):
    # C6: level-based so god_mode (4) and the admin alias are admitted, not just
    # the literal 'super_admin' string.
    from admin_shared import is_admin_role
    if not is_admin_role(role):
        raise HTTPException(status_code=403, detail='Super Admin required')

def _require_facilitator(role: str = Depends(_get_fac_role)):
    """Allow any authenticated facilitator (any role). Blocks anonymous requests."""
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Facilitator authentication required')


async def _assert_session_visible(request: Request, session_id: str) -> None:
    """F-21: delegate to the canonical read-side tenancy guard (lazy import —
    admin_router imports this module's router at load time)."""
    from admin_router import _assert_session_visible as _canonical
    await _canonical(request, session_id)


async def _assert_session_ownership(request: Request, session_id: str) -> None:
    """F-21: delegate to the canonical write-side tenancy guard."""
    from admin_router import _assert_session_ownership as _canonical
    await _canonical(request, session_id)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  GOD MODE — Platform Analytics (#15)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  ANALYTICS VISIBILITY — God Mode controls what facilitators/players see
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# NOTE: this dict is the authoritative catalog + default state. The setter
# endpoints reject any key not present here, so it must stay in sync with the
# frontend FACILITATOR_ANALYTICS / PLAYER_ANALYTICS arrays in
# CreateCohortModal.js (add a key in both, same commit). Values are the default
# visibility; per-cohort overrides layer on top via resolve_analytics_visibility.
_analytics_visibility: dict = {
    "facilitator": {
        # ── Core analytics (shipped) ──
        "decision_heatmap": True,
        "time_to_decision": True,
        "cohort_comparison": True,
        "convergence_analysis": True,
        "learning_outcomes": True,
        "risk_exposure": True,
        # Calibration analytics (Predict-Before-Commit confidence vs accuracy).
        # Railway audit §4.3 follow-up: the frontend toggle existed but this
        # key was missing here, and the setters silently DROP unknown keys —
        # so the toggle could never persist. Keys must stay in sync with
        # frontend/app/config/analyticsRegistry.js (add in both, same commit).
        "calibration_analytics": True,
        "materiality_matrix": True,
        "technical_reference": True,
        # ── Live cohort monitoring ──
        "cohort_pulse": True,          # live KPI heatmap + per-team commit status
        # VIS-1 (UX audit #16a, 2026-08-02): eleven further keys used to live
        # here — leaderboard_matrix, session_health, engine_event_feed,
        # consequence_dna, decision_timeline, stakeholder_map, audit_trail,
        # shadow_board_audit, sdg_alignment, tcfd_dashboard, peer_evaluation.
        # They rendered a toggle in cohort setup and gated NOTHING: no surface
        # read them, so flipping one changed nothing a facilitator could see.
        # Removed together with their frontend entries in
        # analyticsRegistry.js::EXTENDED_VISIBILITY_CARDS (same commit, per this
        # file's own sync rule). Re-add a key ONLY alongside its consumer.
    },
    "player": {
        # ── Core analytics (shipped) ──
        "peer_benchmarking": True,
        "decision_impact": True,
        "what_if_simulator": False,
        # ── Performance & history ──
        "kpi_dashboard": True,         # personal KPI cockpit
        "decision_history": True,      # own past decisions & rationale
        "consequence_timeline": True,  # unfolding consequences over rounds
        "stock_performance": True,     # share-price / valuation chart
        "balanced_scorecard": False,   # sustainability balanced scorecard
        # ── Risk & strategy lenses ──
        "risk_radar": True,            # multi-axis risk radar
        "esg_leadership": False,       # ESG leadership profile
        "competitor_intel": False,     # rival intelligence cards
        # ── Reports & engagement ──
        "annual_report": True,         # narrative annual report
        "achievement_badges": True,    # gamified milestone badges
        "regret_meter": False,         # counterfactual regret meter
        "glossary": True,              # in-game technical glossary
        # ── Right-hand context rail (2026-07-20) ──
        # The rail's four tabs are player-facing surfaces like any other panel,
        # but were never in this catalog — so a facilitator could not turn them
        # off for a cohort. The Decisions tab renders DecisionHistory and is
        # gated by the existing `decision_history` key rather than a duplicate.
        "rail_mailbox": True,          # 📬 Executive Mailbox tab
        "rail_engines": True,          # 🌎 Engine widgets tab
        "rail_climate": True,          # 🌡️ TCFD climate-scenario tab
        "market_reality_feed": True,   # 📡 live market/consequence feed
        # ── 2026-07-30: player-facing surfaces that had NO cohort switch ──
        # Everything below was rendered unconditionally (or behind a round
        # number / engine toggle / its own legacy flag), so a facilitator could
        # not tailor the cockpit for an introductory vs an executive cohort.
        #
        # All default TRUE: adding a switch must not change what any existing
        # cohort sees. The switch is a VETO that composes with the pre-existing
        # gate — turning it on cannot make a Round-9 panel appear in Round 2.
        #
        # Keys mirror frontend/app/config/playerVisibilityRegistry.js; the
        # setters below DROP unknown keys, so a key missing here can never
        # persist. Kept in step by
        # backend/tests/test_player_visibility_catalog.py.
        # End of game & debrief
        "boardroom_showdown": True,           # Boardroom Moment / Showdown
        "archetype_reveal": True,             # Archetype Reveal
        "mirror_debrief": True,               # Mirror Debrief
        "rewind_ribbon": True,                # Rewind Ribbon
        "mr_ladder_reveal": True,             # M_R Ladder Reveal
        "archetype_card": True,               # Shareable Archetype Card
        "three_key_insights": True,           # 3 Key Insights
        "calibration_report": True,           # Calibration Report
        "ceo_interview": True,                # CEO Interview & Assessment
        "student_report_export": True,        # Student Report Export
        "front_page_reveal": True,            # Front Page Reveal
        "side_track_results": True,           # Side Track Results
        # Valuation & causal analytics
        "consequence_dna": True,              # Consequence DNA
        "consequence_dna_sankey": True,       # Consequence DNA Sankey
        "esg_constellation_3d": True,         # 3D ESG Constellation
        "terminal_valuation_calc": True,      # Terminal Valuation Estimator
        "synergy_tracker": True,              # Synergy Multiplier Tracker
        "ebitda_waterfall": True,             # EBITDA Waterfall
        "balance_sheet_modal": True,          # Balance Sheet & Covenants
        "consequence_replay": True,           # Consequence Replay
        "benchmarks_panel": True,             # FTSE 100 ESG Benchmarks
        "living_planet_globe": True,          # Living Planet Globe
        # Prediction & reflection
        "prediction_prompts": True,             # Predict Before You Commit
        "prediction_comparison": True,        # Prediction vs Reality
        "quick_reflection_box": True,         # Quick Reflection box
        "reflective_prompt": True,            # Reflective Nudge card
        # Narrative & stakeholders
        "briefing_video": True,          # Briefing: Watch (video) — the Read | Watch choice
        "briefing_theory_card": True,         # Briefing: Academic Framework
        "briefing_stakeholder_voices": True,  # Briefing: Stakeholder Voices
        "briefing_midgame_valuation": True,   # Briefing: Mid-Game Valuation
        "briefing_butterfly_hints": True,     # Briefing: Butterfly Hints
        "briefing_last_round_recap": True,    # Briefing: Last Round Recap
        "ceo_diary": True,                    # CEO Diary
        "round_retrospect": True,             # What Happened This Round / Road Not Taken
        "stakeholder_agent_panel": True,      # Autonomous Stakeholder Agents
        "market_intel_cards": True,           # Market News & Rating Actions
        "player_annotations": True,           # Facilitator Annotations
        "flag_dependency_warnings": True,     # Flag Dependency Warnings
        # Help & reference
        "ai_advisor": True,                   # AI Strategic Advisor
        "podcast_player": True,               # Boardroom Briefing Podcast
        "learning_hub": True,                 # Learning Hub notebooks
        "resources_sidebar": True,            # Resources Library
        "detailed_option_descriptions": True, # Detailed Option Descriptions
        # Dock & ambient
        "dock_sdg_radar": True,               # Dock: SDG Alignment Radar
        "decision_pressure_timer": True,      # Decision Pressure Timer
    },
}


@analytics_router.get("/god/analytics-visibility", summary="Get analytics visibility settings")
async def get_analytics_visibility():
    return _analytics_visibility


@analytics_router.put("/god/analytics-visibility", summary="Update analytics visibility settings")
async def set_analytics_visibility(body: dict = Body(...), _guard: None = Depends(_require_super_admin)):
    for role in ("facilitator", "player"):
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    _analytics_visibility[role][key] = bool(val)
    return _analytics_visibility


# ── Per-Cohort Analytics Visibility ─────────────────────────────
# Stored on session dict as session["analytics_visibility"] = {facilitator: {...}, player: {...}}
# Global defaults apply when a cohort has no overrides.

def resolve_analytics_visibility(session_id: str, facilitator_id: str | None = None) -> dict:
    """Merge visibility layers, most specific last:

        global defaults
          → per-FACILITATOR profile (admin-set on the registry record;
            facilitator column only — an account-level baseline)
          → per-cohort overrides (admin-set for the facilitator column,
            facilitator-set for the player column)

    facilitator_id is the VIEWING facilitator (the caller), so the same cohort
    can render differently for two facilitators with different profiles.
    """
    import copy as _copy
    merged = _copy.deepcopy(_analytics_visibility)

    # Layer 2: per-facilitator profile (facilitator column only).
    if facilitator_id:
        fac = next((f for f in _facilitator_registry
                    if f.get("facilitator_id") == facilitator_id and not f.get("deleted_at")), None)
        profile = (fac or {}).get("analytics_visibility") or {}
        for key, val in (profile.get("facilitator") or {}).items():
            if key in merged.get("facilitator", {}):
                merged["facilitator"][key] = bool(val)

    sess = database_memory._sessions.get(session_id)
    if not sess:
        return merged
    # Walk up to parent cohort if this is a player sub-session
    if sess.get("parent_cohort_id"):
        parent = database_memory._sessions.get(sess["parent_cohort_id"])
        if parent:
            sess = parent
    cohort_vis = sess.get("analytics_visibility")
    if cohort_vis:
        for role in ("facilitator", "player"):
            if role in cohort_vis:
                for key, val in cohort_vis[role].items():
                    if key in merged.get(role, {}):
                        merged[role][key] = bool(val)
    return merged


@analytics_router.get("/cohort/{session_id}/analytics-visibility", summary="Get per-cohort analytics visibility")
async def get_cohort_analytics_visibility(session_id: str, request: Request, _guard: None = Depends(_require_facilitator)):
    # F-21 (launch audit 2026-09-01): console-only read (AnalyticsControlPanel);
    # _assert_session_visible passes anonymous callers through by design (it
    # assumes a role guard ran first), so the guard is required here.
    await _assert_session_visible(request, session_id)
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    cohort_overrides = sess.get("analytics_visibility")
    # Per-facilitator profiles apply to the VIEWER: resolve with the caller's
    # facilitator identity (None for players/anonymous — profile layer skipped).
    from auth_jwt import get_facilitator_from_request
    caller_fac_id = get_facilitator_from_request(request)
    return {
        "global_defaults": _analytics_visibility,
        "cohort_overrides": cohort_overrides,
        "effective": resolve_analytics_visibility(session_id, facilitator_id=caller_fac_id),
    }


@analytics_router.put("/cohort/{session_id}/analytics-visibility", summary="Set per-cohort analytics visibility overrides")
async def set_cohort_analytics_visibility(session_id: str, request: Request, body: dict = Body(...),
                                          caller_role: str = Depends(_get_fac_role),
                                          _guard: None = Depends(_require_facilitator)):
    await _assert_session_ownership(request, session_id)  # F-21 (launch audit 2026-09-01)
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    # Governance: the FACILITATOR-dashboard column is admin-owned. A facilitator
    # must not grant themselves panels an admin turned off, so non-admin callers
    # may only set the player block; any facilitator block they send is ignored
    # (reported back, not an error, so older clients keep working).
    from admin_shared import is_admin_role
    editable_roles = ("facilitator", "player") if is_admin_role(caller_role) else ("player",)
    ignored_roles = [r for r in ("facilitator", "player") if r in body and r not in editable_roles]
    overrides = sess.setdefault("analytics_visibility", {"facilitator": {}, "player": {}})
    for role in editable_roles:
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    overrides.setdefault(role, {})[key] = bool(val)
    sess["analytics_visibility"] = overrides
    database_memory._persist()
    return {
        "cohort_overrides": overrides,
        "ignored_admin_only_roles": ignored_roles,
        "effective": resolve_analytics_visibility(session_id),
    }


# ── Per-FACILITATOR visibility profile (admin-owned) ──────────────────────────
# An account-level baseline for the facilitator-dashboard column, set from the
# god-mode Facilitator Registry. Layered between global defaults and per-cohort
# overrides by resolve_analytics_visibility.

@analytics_router.get("/god/facilitators/{facilitator_id}/analytics-visibility",
                      summary="Get a facilitator's visibility profile")
async def get_facilitator_visibility_profile(facilitator_id: str,
                                             _guard: None = Depends(_require_super_admin)):
    fac = next((f for f in _facilitator_registry
                if f.get("facilitator_id") == facilitator_id and not f.get("deleted_at")), None)
    if not fac:
        raise HTTPException(status_code=404, detail="Facilitator not found")
    profile = fac.get("analytics_visibility") or {}
    return {
        "facilitator_id": facilitator_id,
        "profile": {"facilitator": profile.get("facilitator", {})},
        "global_defaults": {"facilitator": _analytics_visibility.get("facilitator", {})},
    }


@analytics_router.put("/god/facilitators/{facilitator_id}/analytics-visibility",
                      summary="Set a facilitator's visibility profile")
async def set_facilitator_visibility_profile(facilitator_id: str, body: dict = Body(...),
                                             _guard: None = Depends(_require_super_admin)):
    """Body: {"facilitator": {panel_key: bool, ...}} — replaces the profile.
    An empty dict clears it (back to global defaults). Facilitator column only;
    the player column is cohort-level pedagogy, not an account property."""
    fac = next((f for f in _facilitator_registry
                if f.get("facilitator_id") == facilitator_id and not f.get("deleted_at")), None)
    if not fac:
        raise HTTPException(status_code=404, detail="Facilitator not found")
    incoming = body.get("facilitator") or {}
    catalog = _analytics_visibility.get("facilitator", {})
    cleaned = {k: bool(v) for k, v in incoming.items() if k in catalog}
    if cleaned:
        fac["analytics_visibility"] = {"facilitator": cleaned}
    else:
        fac.pop("analytics_visibility", None)   # empty ⇒ profile cleared
    from admin_shared import _persist_facilitators
    _persist_facilitators()
    return {
        "facilitator_id": facilitator_id,
        "profile": {"facilitator": cleaned},
        "cleared": not cleaned,
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  PLATFORM-WIDE ANALYTICS (God Mode + Facilitator)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@analytics_router.get("/god/analytics", summary="Platform-wide analytics")
async def get_platform_analytics(request: Request,
                                 caller_role: str = Depends(_get_fac_role),
                                 _guard: None = Depends(_require_facilitator)):
    """
    Compute all analytics from _global_states, _bu_states, _decision_log.
    Returns decision heatmap, time-to-decision, cohort trajectories,
    convergence, learning outcomes, and risk exposure.

    BUGFIX (Cohort Analytics 'Failed to load analytics'): QA-2026-07-16 #13
    guarded this super_admin-only, which 403'd the facilitator dashboard's
    Cohort Analytics tab — its primary consumer. The QA intent (block
    ANONYMOUS access to facilitator/admin-only data) is preserved by
    _require_facilitator; the data-exposure concern is handled by SCOPING:
    non-admin callers see only their own cohorts (and their child player
    sessions), while super_admin/god_mode keep the whole platform.
    """
    import math
    from collections import defaultdict

    # Railway audit §1.1: build memory-shaped views via the parity db API so
    # this works identically under Postgres (the old getattr reads silently
    # returned {} there). Shapes match the memory store exactly:
    #   global_states[sid] = list of per-round dicts (fields at top level),
    #   bu_states[sid]     = {round_number: [bu dicts]}.
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}
    global_states: dict = {}
    bu_states: dict = {}
    for _sid in all_sessions:
        # SEAM-08 (audit 2026-09-04): the closing row rides along (round 11,
        # is_final) so rounds[-1] is a finished run's final state — learning
        # bonuses, flags — not the state it entered R10 with; the per-round
        # trajectory below keeps to the ten entering states.
        _hist = await db.fetch_round_history(_sid, include_final=True)
        global_states[_sid] = [
            {**h["global_state"], "round_number": h.get("round_number", 1), "is_final": bool(h.get("is_final"))}
            for h in _hist
        ]
        bu_states[_sid] = {h.get("round_number", 1): h.get("business_units") or [] for h in _hist}
    decision_log = await db.fetch_all_decisions()

    from admin_shared import is_admin_role
    if not is_admin_role(caller_role):
        from auth_jwt import get_facilitator_from_request
        caller_fid = get_facilitator_from_request(request)
        own = {sid for sid, s in all_sessions.items() if s.get("facilitator_id") == caller_fid}
        own |= {sid for sid, s in all_sessions.items() if s.get("parent_cohort_id") in own}
        all_sessions = {sid: s for sid, s in all_sessions.items() if sid in own}
        global_states = {sid: v for sid, v in global_states.items() if sid in own}
        bu_states = {sid: v for sid, v in bu_states.items() if sid in own}
        decision_log = [d for d in decision_log if d.get("session_id") in own]

    # ── Summary counts ────────────────────────────────────────
    cohort_sessions = {sid: s for sid, s in all_sessions.items() if not s.get("parent_cohort_id")}
    player_sessions = {sid: s for sid, s in all_sessions.items() if s.get("parent_cohort_id")}

    # ── 1. Decision Heatmap: choice distribution per round ────
    decision_heatmap = defaultdict(lambda: defaultdict(int))
    for d in decision_log:
        rn = d.get("round_number", 0)
        choice = d.get("choice_selected", "")
        if choice:
            decision_heatmap[f"R{rn}"][choice] += 1

    # ── 2. Time-to-Decision: per round timing stats ───────────
    time_by_round = defaultdict(list)
    for d in decision_log:
        rn = d.get("round_number", 0)
        ttd = d.get("time_to_decision_seconds", 0)
        if ttd > 0:
            time_by_round[f"R{rn}"].append(ttd)

    time_to_decision = {}
    for rkey, times in sorted(time_by_round.items()):
        st = sorted(times)
        n = len(st)
        median = st[n // 2] if n % 2 == 1 else round((st[n // 2 - 1] + st[n // 2]) / 2, 1)
        time_to_decision[rkey] = {
            "avg_seconds": round(sum(st) / n, 1),
            "median_seconds": median,
            "min": st[0],
            "max": st[-1],
            "count": n,
        }

    # ── 3. Cohort Trajectories: KPI over rounds per cohort ────
    cohort_trajectories = {}
    for sid, sess in cohort_sessions.items():
        cname = sess.get("cohort_name", sid[:12])
        rounds = global_states.get(sid, [])
        trajectory = []
        for grs in rounds:
            if grs.get("is_final"):
                continue   # SEAM-08: the closing state is not an "R11" point
            rn = grs.get("round_number", 1)
            bus = bu_states.get(sid, {}).get(rn, [])
            avg_sl = sum(b.get("social_license_score", 50) for b in bus) / max(len(bus), 1)
            trajectory.append({
                "round": rn,
                "treasury": round(float(grs.get("corporate_treasury", 0)) / 1_000_000, 2),
                "reputation": round(float(grs.get("group_reputation", 50)), 1),
                "synergy": round(float(grs.get("synergy_multiplier", 1.0)), 3),
                "ebitda": round(float(grs.get("historical_ebitda", 0)) / 1_000_000, 2),
            })
        cohort_trajectories[cname] = trajectory

    # ── 4. Convergence Analysis ───────────────────────────────
    # Measure strategy similarity: CapEx StdDev and choice entropy per round
    capex_by_round = defaultdict(list)
    choices_by_round = defaultdict(list)
    for d in decision_log:
        rn = d.get("round_number", 0)
        capex_by_round[f"R{rn}"].append(d.get("capex_allocated", 0))
        ch = d.get("choice_selected", "")
        if ch:
            choices_by_round[f"R{rn}"].append(ch)

    capex_std_by_round = {}
    for rkey, vals in sorted(capex_by_round.items()):
        if len(vals) > 1:
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            capex_std_by_round[rkey] = round(math.sqrt(variance), 0)
        else:
            capex_std_by_round[rkey] = 0

    choice_entropy_by_round = {}
    for rkey, choices in sorted(choices_by_round.items()):
        n = len(choices)
        if n == 0:
            choice_entropy_by_round[rkey] = 0
            continue
        freq = defaultdict(int)
        for c in choices:
            freq[c] += 1
        entropy = 0
        for count in freq.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)
        choice_entropy_by_round[rkey] = round(entropy, 3)

    # Convergence index: 0 = everyone same, 1 = maximum diversity
    all_entropies = list(choice_entropy_by_round.values())
    max_entropy = math.log2(3) if all_entropies else 1  # 3 choices max
    convergence_index = round(
        1 - (sum(all_entropies) / max(len(all_entropies), 1) / max_entropy), 3
    ) if all_entropies else 0.5

    # ── 5. Learning Outcomes ──────────────────────────────────
    total_bonuses = 0
    bonuses_breakdown = defaultdict(int)
    for sid, rounds in global_states.items():
        if not rounds:
            continue
        latest = rounds[-1]
        lb = latest.get("learning_bonuses_awarded", {})
        if isinstance(lb, dict):
            for category, val in lb.items():
                if isinstance(val, (int, float)):
                    total_bonuses += val
                    bonuses_breakdown[category] += 1

    # Student bonus awards
    try:
        import admin_router as _ar
        _student_bonuses = getattr(_ar, '_student_bonuses', {})
    except Exception:
        _student_bonuses = {}
    badges_awarded = defaultdict(int)
    total_student_bonuses = 0
    for sid_bonuses in _student_bonuses.values():
        for b in sid_bonuses:
            total_student_bonuses += 1
            bk = b.get("badge_key", "")
            if bk:
                badges_awarded[bk] += 1

    # ── 6. Risk Exposure: per cohort risk trends ──────────────
    risk_exposure = {}
    for sid, sess in cohort_sessions.items():
        cname = sess.get("cohort_name", sid[:12])
        rounds_data = global_states.get(sid, [])
        risk_trend = []
        for grs in rounds_data:
            rn = grs.get("round_number", 1)
            bus = bu_states.get(sid, {}).get(rn, [])
            if not bus:
                continue
            n = len(bus)
            from engine import calc_revenue_weighted_avg_ci as _rw_ci
            avg_carbon = round(_rw_ci(bus), 2)   # SEAM-15: tCO₂e per $M revenue, revenue-weighted
            avg_ncd = round(sum(b.get("natural_capital_debt", 0) for b in bus) / n, 2)
            avg_sl = round(sum(b.get("social_license_score", 50) for b in bus) / n, 2)
            avg_gov = round(sum(b.get("governance_risk_score", 0) for b in bus) / n, 2)
            risk_trend.append({
                "round": rn,
                "avg_carbon_intensity": avg_carbon,
                "avg_natural_capital_debt": avg_ncd,
                "avg_social_license": avg_sl,
                "avg_governance_risk": avg_gov,
            })
        risk_exposure[cname] = risk_trend

    return {
        "total_cohorts": len(cohort_sessions),
        "total_players": len(player_sessions),
        "total_facilitators": len(_facilitator_registry),
        "total_decisions": len(decision_log),
        "decision_heatmap": {k: dict(v) for k, v in sorted(decision_heatmap.items())},
        "time_to_decision": dict(sorted(time_to_decision.items())),
        "cohort_trajectories": cohort_trajectories,
        "convergence": {
            "capex_std_by_round": capex_std_by_round,
            "choice_entropy_by_round": choice_entropy_by_round,
            "convergence_index": convergence_index,
        },
        "learning_outcomes": {
            "learning_bonuses_total": total_bonuses,
            "bonuses_by_category": dict(bonuses_breakdown),
            "badges_awarded": dict(badges_awarded),
            "student_bonus_count": total_student_bonuses,
        },
        "risk_exposure": risk_exposure,
        "visibility": _analytics_visibility,
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  PLAYER-SCOPED ANALYTICS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@analytics_router.get("/analytics/player/{session_id}", summary="Player-scoped analytics")
async def get_player_analytics(session_id: str, request: Request):
    """
    Compute peer benchmarking, decision impact attribution, and
    what-if counterfactual analysis for a specific player session.

    Guard (audit finding B — was fully unauthenticated): facilitators always
    pass; player callers are bound to their own session with the same SEC-3
    semantics as router._assert_player_owns_session — an unowned (solo)
    session admits its UUID bearer, an owned session requires a matching
    X-Player-Id, and holding a leaked session id alone is not enough.
    """
    # Railway audit §1.1: memory-shaped views via the parity db API (the old
    # getattr reads silently returned {} under Postgres, 404ing every player).
    all_sessions = {s["session_id"]: s for s in await db.fetch_all_sessions_raw()}
    global_states: dict = {}
    bu_states: dict = {}
    for _sid in all_sessions:
        # SEAM-08: entering-states 1..10 plus the closing state, so R9 and R10 deltas are real
        _hist = await db.fetch_round_history(_sid, include_final=True)
        global_states[_sid] = [
            {**h["global_state"], "round_number": h.get("round_number", 1)} for h in _hist
        ]
        bu_states[_sid] = {h.get("round_number", 1): h.get("business_units") or [] for h in _hist}
    decision_log = await db.fetch_all_decisions()

    sess = all_sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    # F-11 (audit 2026-09-04): this was a plaintext X-Player-Id compare — a
    # forgeable header, not the signed player token every router.py player
    # route requires — and any facilitator passed with no tenancy check. A
    # player is now bound by the same rule as the cockpit's own routes (a
    # token scoped to THIS session; observers may read); a facilitator must be
    # able to observe the cohort the session belongs to.
    if _get_fac_role(request) == 'anonymous':
        from router import _assert_player_owns_session
        await _assert_player_owns_session(request, session_id, allow_observer=True)
    else:
        from admin_router import _assert_session_visible
        await _assert_session_visible(request, session_id)

    player_rounds = global_states.get(session_id, [])
    if not player_rounds:
        raise HTTPException(404, "No round data for this session")

    latest = player_rounds[-1]
    player_treasury = float(latest.get("corporate_treasury", 0))
    player_reputation = float(latest.get("group_reputation", 50))
    player_synergy = float(latest.get("synergy_multiplier", 1.0))

    # ── 1. Peer Benchmarking ──────────────────────────────────
    # Compute percentiles across all sessions at the same round
    player_round = latest.get("round_number", 1)
    all_treasuries = []
    all_reputations = []
    all_synergies = []

    for sid, rounds in global_states.items():
        if not rounds:
            continue
        # Find the state at the same round number
        for grs in rounds:
            if grs.get("round_number") == player_round:
                all_treasuries.append(float(grs.get("corporate_treasury", 0)))
                all_reputations.append(float(grs.get("group_reputation", 50)))
                all_synergies.append(float(grs.get("synergy_multiplier", 1.0)))
                break

    def percentile(value, population):
        if not population:
            return 50
        below = sum(1 for v in population if v < value)
        return round(below / len(population) * 100, 1)

    cohort_avg_treasury = round(sum(all_treasuries) / max(len(all_treasuries), 1), 2)
    cohort_avg_reputation = round(sum(all_reputations) / max(len(all_reputations), 1), 1)

    peer_benchmarking = {
        "treasury_percentile": percentile(player_treasury, all_treasuries),
        "reputation_percentile": percentile(player_reputation, all_reputations),
        "synergy_percentile": percentile(player_synergy, all_synergies),
        "player_count": len(all_treasuries),
        "cohort_avg": {
            "treasury": cohort_avg_treasury,
            "reputation": cohort_avg_reputation,
        },
        "player": {
            "treasury": round(player_treasury, 2),
            "reputation": round(player_reputation, 1),
            "synergy": round(player_synergy, 3),
        },
    }

    # ── 2. Decision Impact Attribution ────────────────────────
    # For each round, show the KPI deltas caused by the player's choice
    decision_impact = []
    player_decisions = [
        d for d in decision_log if d.get("session_id") == session_id
    ]
    # Group by round
    from collections import defaultdict
    dec_by_round = defaultdict(list)
    for d in player_decisions:
        dec_by_round[d.get("round_number", 0)].append(d)

    for i in range(1, len(player_rounds)):
        prev = player_rounds[i - 1]
        curr = player_rounds[i]
        rn = prev.get("round_number", i)
        treasury_delta = float(curr.get("corporate_treasury", 0)) - float(prev.get("corporate_treasury", 0))
        reputation_delta = float(curr.get("group_reputation", 50)) - float(prev.get("group_reputation", 50))
        synergy_delta = float(curr.get("synergy_multiplier", 1.0)) - float(prev.get("synergy_multiplier", 1.0))

        round_decs = dec_by_round.get(rn, []) or dec_by_round.get(curr.get("round_number", 0), [])
        choice = round_decs[0].get("choice_selected", "—") if round_decs else "—"
        total_capex = sum(d.get("capex_allocated", 0) for d in round_decs)

        # Generate narrative
        parts = []
        if treasury_delta > 0:
            parts.append(f"Treasury grew by ${abs(treasury_delta/1_000_000):.1f}M")
        elif treasury_delta < 0:
            parts.append(f"Treasury fell by ${abs(treasury_delta/1_000_000):.1f}M")
        if reputation_delta > 0:
            parts.append(f"reputation rose {reputation_delta:.1f} pts")
        elif reputation_delta < 0:
            parts.append(f"reputation dropped {abs(reputation_delta):.1f} pts")

        decision_impact.append({
            "round": rn,
            "choice": choice,
            "total_capex": round(total_capex, 0),
            "treasury_delta": round(treasury_delta, 2),
            "reputation_delta": round(reputation_delta, 2),
            "synergy_delta": round(synergy_delta, 4),
            "narrative": " — ".join(parts) if parts else "Minimal change this round",
        })

    # ── 3. What-If Simulator ──────────────────────────────────
    # Simple counterfactual: show what the average player chose at each
    # round and compare KPI trajectory
    what_if = []
    # Gather avg choice per round across all sessions
    from collections import Counter
    choices_per_round = defaultdict(list)
    for d in decision_log:
        ch = d.get("choice_selected", "")
        if ch:
            choices_per_round[d.get("round_number", 0)].append(ch)

    for impact in decision_impact:
        rn = impact["round"]
        player_choice = impact["choice"]
        round_choices = choices_per_round.get(rn, [])
        if not round_choices:
            continue
        counter = Counter(round_choices)
        most_popular = counter.most_common(1)[0][0] if counter else player_choice

        if most_popular != player_choice:
            # Find avg KPI delta for sessions that chose the popular option
            pop_deltas_t = []
            pop_deltas_r = []
            for sid, rounds in global_states.items():
                if sid == session_id:
                    continue
                sid_decs = [d for d in decision_log if d.get("session_id") == sid and d.get("round_number") == rn]
                sid_choice = sid_decs[0].get("choice_selected", "") if sid_decs else ""
                if sid_choice == most_popular and len(rounds) > rn:
                    for idx in range(len(rounds) - 1):
                        if rounds[idx].get("round_number") == rn:
                            dt = float(rounds[idx + 1].get("corporate_treasury", 0)) - float(rounds[idx].get("corporate_treasury", 0))
                            dr = float(rounds[idx + 1].get("group_reputation", 50)) - float(rounds[idx].get("group_reputation", 50))
                            pop_deltas_t.append(dt)
                            pop_deltas_r.append(dr)
                            break

            if pop_deltas_t:
                avg_t = sum(pop_deltas_t) / len(pop_deltas_t)
                avg_r = sum(pop_deltas_r) / len(pop_deltas_r)
                what_if.append({
                    "round": rn,
                    "actual_choice": player_choice,
                    "alternative": most_popular,
                    "alternative_popularity": f"{counter[most_popular]}/{len(round_choices)}",
                    "projected_treasury_diff": round(avg_t - impact["treasury_delta"], 2),
                    "projected_reputation_diff": round(avg_r - impact["reputation_delta"], 2),
                })

    # BUG-2026-07-20: this used to hand back _analytics_visibility["player"] —
    # the GLOBAL defaults — so PlayerAnalytics' tab gating ignored per-cohort
    # overrides entirely. A facilitator who switched Peer Benchmarking off for
    # their cohort still saw the tab, because only the platform default was
    # consulted. resolve_analytics_visibility layers cohort overrides on top
    # (and walks a player sub-session up to its parent cohort).
    try:
        _vis = resolve_analytics_visibility(session_id).get("player", {})
    except Exception:
        _vis = _analytics_visibility.get("player", {})  # fail-open to defaults
    return {
        "peer_benchmarking": peer_benchmarking,
        "decision_impact": decision_impact,
        "what_if": what_if,
        "visibility": _vis,
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ── Glossary CRUD ─────────────────────────────────────────────
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# DEEP-7 (2026-08-31): the strike numbers in the glossary are interpolated
# from the shipped R9 config so documentation cannot drift from the engine
# again (the previous hand-written entries claimed 75% and printed a formula
# that existed nowhere in the code).
from round_configs import get_round_config as _grc
_STRIKE_PCT = int(float((_grc(9) or {}).get("special_rules", {})
                        .get("strike_probability_override", 0.50)) * 100)

# W3 (2026-09-01): every load-bearing number below is interpolated from the
# same constants the engine runs on, so a config change updates the glossary
# and drift is structurally impossible. tests/test_glossary_parity.py guards
# the wiring. Hand-written figures that remain are framework/history facts
# (CSRD counts, citation years) or paradigm-config values without a global
# constant.
from config import (
    FINANCIAL_FREE_CSF_PCT, FINANCIAL_DEFAULT_LOAN_RATE,
    FINANCIAL_SHADOW_CARBON_PRICE,
    OVERRUN_CAPEX_THRESHOLD, OVERRUN_DEFAULT_PROBABILITY, OVERRUN_DEFAULT_SEVERITY,
    IMPLEMENTATION_LAG_INV_THRESHOLD,
    DIVIDEND_CUT_THRESHOLD, DIVIDEND_CUT_REP_PENALTY,
    NCD_INTEREST_COEFFICIENT,
    SYNERGY_DAMPENING_FACTOR,
    TECH_DEBT_ROUNDS_THRESHOLD, TECH_DEBT_PENALTY_RATE,
    BRAINDRAIN_REPUTATION_THRESHOLD,
    BURNOUT_OPEX_THRESHOLD,
    CYCLONE_PROB_BASE, PHYSICAL_VAR_DAMAGE_BASE,
    GREENWASH_INVESTMENT_THRESHOLD, GREENWASH_SLO_PENALTY,
    GREENWASH_MODERATE_PENALTY_SCALE,
    TURNAROUND_CRISIS_ENTRY_TREASURY, TURNAROUND_CRISIS_ENTRY_REP,
    TURNAROUND_CRISIS_BAILOUT,
    TV_EXIT_MULTIPLE_FLOOR, TV_EXIT_MULTIPLE_CEILING,
)
from terminal_valuation import MR_FLOOR, MR_CEILING
from engine import _MACRO_RATE_CYCLES

def _pct(x: float) -> str:
    v = x * 100
    return f"{v:g}"

def _musd(x: float) -> str:
    return "$0" if x == 0 else f"${x/1e6:g}M"

def _macro_cycle_text() -> str:
    """Render _MACRO_RATE_CYCLES as grouped ranges, e.g. 'R1-2 -1%'."""
    items = sorted(_MACRO_RATE_CYCLES.items())
    groups, start, prev_r, prev_v = [], None, None, None
    for r, v in items:
        if prev_v is None or v != prev_v or r != prev_r + 1:
            if prev_v is not None:
                groups.append((start, prev_r, prev_v))
            start = r
        prev_r, prev_v = r, v
    groups.append((start, prev_r, prev_v))
    parts = []
    for a, b, v in groups:
        rng = f"R{a}" if a == b else f"R{a}-{b}"
        parts.append(f"{rng} {'+' if v > 0 else ''}{_pct(v)}%" if v else f"{rng} neutral")
    return ", ".join(parts)

_MACRO_TEXT = _macro_cycle_text()

# R7 Waste-to-Energy synergy-multiplier boost, read from the shipped config
# (the hand-written glossary claimed +0.35; the config ships 0.3).
_R7C_SYNERGY_BOOST = float(((_grc(7) or {}).get("options", {}).get("option_c", {})
                            .get("impacts", {}).get("synergy_multiplier_boost", 0.0)))

_glossary_terms: list = [
    # -- Financial Metrics --
    {"id": "ebitda", "term": "EBITDA", "definition": "Earnings Before Interest, Taxes, Depreciation, and Amortization. The primary operational profitability metric. At R10, EBITDA is carbon-adjusted by deducting total carbon tonnage x carbon tax ($250/tonne).", "tags": ["finance", "profitability", "earnings", "valuation"], "weblink": "https://www.investopedia.com/terms/e/ebitda.asp"},
    {"id": "csf_pool", "term": "Corporate Strategic Fund (CSF)", "definition": "The master liquidity pool: CSF = Sum(Revenue_i - OPEX_i) - Dividends. If total CAPEX exceeds " + _pct(FINANCIAL_FREE_CSF_PCT) + "% of treasury, the excess is drawn as a term loan at " + _pct(FINANCIAL_DEFAULT_LOAN_RATE) + "% interest on the opening balance, repaid straight-line from treasury over the rounds that remain (all of it by round 10) and carried on the balance sheet. The primary resource constraint for all investment decisions.", "tags": ["finance", "investment", "treasury", "capital"], "weblink": ""},
    {"id": "treasury", "term": "Treasury", "definition": "Corporate cash reserves. Treasury below " + _musd(TURNAROUND_CRISIS_ENTRY_TREASURY) + " with reputation below " + f"{TURNAROUND_CRISIS_ENTRY_REP:g}" + " triggers the Turnaround pathway (crisis bailout " + _musd(TURNAROUND_CRISIS_BAILOUT) + "). Depleted by investments, crises, loan interest, and operating costs.", "tags": ["finance", "cash", "investment", "liquidity"], "weblink": ""},
    {"id": "terminal_value", "term": "Terminal Value (TV)", "definition": "Simulated market capitalisation at end of the 5-year cycle. TV = (Terminal_EBITDA + Green_Fund) x Exit_Multiple (WACC-coupled, " + f"{TV_EXIT_MULTIPLE_FLOOR:g}" + "-" + f"{TV_EXIT_MULTIPLE_CEILING:g}" + "x, 12x at baseline WACC) x Regenerative_Multiple (M_R). Represents what an ESG-informed institutional investor would pay.", "tags": ["finance", "valuation", "exit", "strategy"], "weblink": "https://www.investopedia.com/terms/t/terminalvalue.asp"},
    {"id": "capex", "term": "CAPEX (Capital Expenditure)", "definition": "One-time investment per BU per round from the CSF pool. CAPEX > " + _pct(IMPLEMENTATION_LAG_INV_THRESHOLD) + "% of BU revenue triggers a 1-round implementation lag. CAPEX > " + _musd(OVERRUN_CAPEX_THRESHOLD) + " has a " + _pct(OVERRUN_DEFAULT_PROBABILITY) + "% chance of +" + _pct(OVERRUN_DEFAULT_SEVERITY) + "% cost overrun.", "tags": ["finance", "investment", "capital", "expenditure"], "weblink": "https://www.investopedia.com/terms/c/capitalexpenditure.asp"},
    {"id": "opex", "term": "OPEX (Operating Expenditure)", "definition": "Ongoing BU operational costs. Reduced by the Synergy Engine (sqrt(ratio) x " + f"{SYNERGY_DAMPENING_FACTOR:g}" + " x synergy_multiplier). Increased by inflation (default 5%/round, macro noise adds/removes a fraction), burnout, brain-drain, and technical debt.", "tags": ["finance", "operations", "costs", "expenditure"], "weblink": "https://www.investopedia.com/terms/o/operating_expense.asp"},
    {"id": "cost_of_capital", "term": "Cost of Capital", "definition": "Investor-required rate of return. Follows macro cycles: " + _MACRO_TEXT + ". Higher rates penalise late-stage treasury recovery.", "tags": ["finance", "treasury", "investors", "interest"], "weblink": "https://www.investopedia.com/terms/c/costofcapital.asp"},
    {"id": "green_fund", "term": "Green Transition Fund (GTF)", "definition": "Ring-fenced capital reserve from early-round ESG decisions, analogous to a green bond issuance (ICMA framework). Drawn down first before corporate treasury for R7-R9 sustainable transition costs.", "tags": ["finance", "green bond", "sustainability", "investment"], "weblink": "https://www.icmagroup.org/sustainable-finance/the-principles-guidelines-and-handbooks/green-bond-principles-gbp/"},
    {"id": "dividend_ratchet", "term": "Dividend Ratchet", "definition": "Board pressure: cutting dividends by more than " + _pct(1 - DIVIDEND_CUT_THRESHOLD) + "% vs. last round triggers -" + f"{DIVIDEND_CUT_REP_PENALTY:g}" + " reputation. Models real-world investor expectations for distribution consistency.", "tags": ["finance", "governance", "dividends", "board"], "weblink": ""},
    # -- Sustainability & ESG --
    {"id": "esg", "term": "ESG", "definition": "Environmental, Social, and Governance. Three pillars for measuring corporate sustainability and ethical impact. First defined by the UN Principles for Responsible Investment (2006).", "tags": ["esg", "sustainability", "environment", "social", "governance"], "weblink": "https://www.unpri.org/about-us/what-are-the-principles-for-responsible-investment"},
    {"id": "ncd", "term": "Natural Capital Debt (NCD)", "definition": "BU-level environmental liability. Interest rate = Base_Rate + NCD x " + f"{NCD_INTEREST_COEFFICIENT:g}" + ", compounds each round. At NCD=5,200 with a 5% base rate the effective rate is " + _pct(0.05 + 5200 * NCD_INTEREST_COEFFICIENT) + "%. Models planetary boundaries as financial risk.", "tags": ["environment", "liability", "sustainability", "natural capital"], "weblink": "https://naturalcapitalcoalition.org/natural-capital-protocol/"},
    {"id": "social_license", "term": "Social License to Operate (SLO)", "definition": "BU-level score [0-100] quantifying community and worker acceptance (Thomson & Boutilier, 2011). Average SLO below 75 draws the -0.40 M_R Instability Discount, phased in across a 5-point band below the threshold (no cliff). Below 50 creates R9 strike risk (" + str(_STRIKE_PCT) + "% base, burnout can add up to +20pts).", "tags": ["social", "stakeholder", "community", "legitimacy"], "weblink": "https://socialicense.com/definition.html"},
    {"id": "carbon_intensity", "term": "Carbon Intensity", "definition": "BU-level metric (tCO2-e per $M revenue). Scope 3 supply chain footprint is 4x direct emissions. Carbon tonnage at R10 is taxed at $" + f"{FINANCIAL_SHADOW_CARBON_PRICE:g}" + "/tonne (climate pathway: $750/tonne).", "tags": ["environment", "emissions", "carbon", "climate"], "weblink": "https://www.ghgprotocol.org/sites/default/files/standards/ghg-protocol-revised.pdf"},
    {"id": "scope3", "term": "Scope 3 Emissions", "definition": "Indirect value chain emissions (upstream suppliers, downstream customers). Typically 4x direct emissions per GHG Protocol. R3 decisions directly shape Scope 3 trajectory.", "tags": ["environment", "emissions", "supply chain", "carbon"], "weblink": "https://www.ghgprotocol.org/standards/scope-3-standard"},
    {"id": "governance_risk", "term": "Governance Risk", "definition": "Score [0-100] reflecting corporate governance quality. High values reduce cash efficiency (revenue x (1 - gov_risk/500)). Feeds supply chain contagion and R9 strike probability.", "tags": ["governance", "risk", "compliance", "board"], "weblink": "https://www.oecd.org/corporate/principles-corporate-governance/"},
    {"id": "water_dependency", "term": "Water Dependency Index", "definition": "BU-level [0-1] score for operational freshwater reliance. Modified exclusively in R8 (Blue Stress). Pharma baseline: 0.85. Maps to TCFD physical climate risk exposures.", "tags": ["environment", "water", "physical risk", "tcfd"], "weblink": "https://www.wri.org/aqueduct"},
    {"id": "burnout", "term": "Staff Burnout", "definition": "Global workforce burnout score [0-100]. Positive HR actions reduce it (typically -16 to -30); overtime pushes add +24 to +30; no HR action adds +6/round natural drift. OPEX penalty rises quadratically above " + f"{BURNOUT_OPEX_THRESHOLD:g}" + ". WHO ICD-11 recognised (2019).", "tags": ["social", "workforce", "hr", "talent"], "weblink": "https://www.who.int/news/item/28-05-2019-burn-out-an-occupational-phenomenon-international-classification-of-diseases"},
    {"id": "workforce_readiness", "term": "Workforce Readiness", "definition": "Global competence score [0-100, starts 50]. High HR: +8, Medium: +4, None: -5 per round. Below 40: pillar effectiveness -20%. Above 75: +0.10 M_R bonus, phased in across a 5-point band.", "tags": ["social", "workforce", "hr", "competence", "learning"], "weblink": ""},
    {"id": "reputation", "term": "Group Reputation", "definition": "Composite [0-100] stakeholder perception score. The Contagion Engine propagates single-BU damage to the group. Below 65 triggers Talent Brain-Drain on Software BU.", "tags": ["social", "reputation", "brand", "contagion"], "weblink": ""},
    {"id": "brand_equity", "term": "Brand Equity", "definition": "Intangible asset value from brand recognition and loyalty. Operationalised via Keller's Customer-Based Brand Equity model (Journal of Marketing, 1993).", "tags": ["social", "reputation", "brand", "strategy"], "weblink": "https://doi.org/10.2307/1252054"},
    # -- Simulation Engines --
    {"id": "contagion_engine", "term": "Contagion Engine", "definition": "Sigmoid-based reputational damage propagation: Group_Rep = AVG(BU_Rep) - 50 x sigmoid((severity-30)/15). If electronics_blindspot active, R4 severity doubles (40 to 80). Models systemic risk cascades.", "tags": ["engine", "reputation", "crisis", "sigmoid", "contagion"], "weblink": ""},
    {"id": "synergy_engine", "term": "Synergy Engine", "definition": "Diminishing-returns OPEX reduction: effective_ratio = sqrt(ratio) x 0.7; New_OPEX = Old_OPEX x (1 - effective_ratio x synergy_mult). R7C Waste-to-Energy adds +" + f"{_R7C_SYNERGY_BOOST:g}" + " to the synergy multiplier.", "tags": ["engine", "synergy", "opex", "investment", "efficiency"], "weblink": ""},
    {"id": "synergy_multiplier", "term": "Synergy Multiplier", "definition": "Factor [0.5-2.0+] amplifying CAPEX effectiveness. Decays 5%/round via VRIO. R7-C boosts +" + f"{_R7C_SYNERGY_BOOST:g}" + ". At R10, synergy x 100 must exceed 80 to unlock Resist & Integrate option.", "tags": ["strategy", "synergy", "efficiency", "competitive advantage"], "weblink": ""},
    {"id": "brain_drain", "term": "Talent Brain-Drain", "definition": "OPEX inflation for Software/Telehealth BU when Group Rep < " + f"{BRAINDRAIN_REPUTATION_THRESHOLD:g}" + ". Penalty = 1 + max(0, (65-Rep)/100) x 1.5 + burnout_adj. Models ESG-driven employee exodus.", "tags": ["engine", "talent", "opex", "reputation", "hr"], "weblink": ""},
    {"id": "entropy", "term": "Natural Decay (Entropy)", "definition": "BUs with zero CAPEX lose 2% reputation and 2% SLO per round. Over 5 rounds: Rep 80 decays to 72.3. Models organisational entropy.", "tags": ["engine", "decay", "neglect", "reputation", "slo"], "weblink": ""},
    {"id": "technical_debt", "term": "Technical Debt", "definition": "" + _pct(TECH_DEBT_PENALTY_RATE) + "% OPEX penalty for BUs with zero investment for " + str(TECH_DEBT_ROUNDS_THRESHOLD) + "+ consecutive rounds. Combined with Natural Decay and Brain-Drain, creates a spiralling neglect cascade.", "tags": ["engine", "penalty", "neglect", "opex", "debt"], "weblink": ""},
    {"id": "greenwashing_engine", "term": "Greenwashing Engine", "definition": "Detects green rhetoric without investment. Options tagged green_claim: full in config are checked against a " + _pct(GREENWASH_INVESTMENT_THRESHOLD) + "% share-of-CSF-pool threshold (the team's total allocation, C-1 2026-09-05) (SLO penalty -" + f"{GREENWASH_SLO_PENALTY:g}" + " per BU on failure); moderate claims face a lower bar and " + _pct(GREENWASH_MODERATE_PENALTY_SCALE) + "% of the penalty. Untagged options are never greenwash-checked. Models regulatory risk from ESG misrepresentation.", "tags": ["engine", "greenwashing", "social license", "regulation"], "weblink": "https://www.esma.europa.eu/press-news/esma-news/esma-proposes-rules-use-esg-and-sustainability-terms-funds-names"},
    {"id": "strike_engine", "term": "Strike Probability Engine", "definition": "R9 stochastic event: if average SLO < 50, base strike probability is " + str(_STRIKE_PCT) + "%; average burnout above 50 adds up to +20 points (capped at 95%). A strike zeroes ALL BU revenue for the round (minimum penalty: the larger of $1M or 5% of treasury).", "tags": ["engine", "strike", "workforce", "social license", "stochastic"], "weblink": ""},
    {"id": "stochastic_climate", "term": "Stochastic Climate Event (R5)", "definition": "Category-4 cyclone with " + _pct(CYCLONE_PROB_BASE) + "% probability. Base damage " + _musd(PHYSICAL_VAR_DAMAGE_BASE) + ". R5-A Hard Engineering: 85% reduction (2-round delay). R5-B Nature-Based: 60%. R5-C Insurance: no reduction, blocks M_R resilience bonus.", "tags": ["engine", "climate", "physical risk", "stochastic", "tcfd"], "weblink": "https://www.fsb-tcfd.org/recommendations/"},
    {"id": "implementation_lag", "term": "Implementation Lag", "definition": "Investments > 10% of BU revenue are DEFERRED 1 round. Pay NOW, benefit NEXT round. Models real-world capital project J-curve payoff profiles.", "tags": ["engine", "investment", "timing", "capex", "delay"], "weblink": ""},
    {"id": "pending_capex", "term": "Pending CAPEX Projects", "definition": "Infrastructure investments maturing over subsequent rounds. Stored with rounds_remaining counter. R5-A Hard Engineering purchases resilience in R7, not R5.", "tags": ["engine", "capex", "infrastructure", "delayed returns"], "weblink": ""},
    # -- Scoring & Archetypes --
    {"id": "mr", "term": "Regenerative Multiple (M_R)", "definition": "Risk-adjusted valuation modifier, clamped to [" + f"{MR_FLOOR:g}" + ", " + f"{MR_CEILING:g}" + "]. Base 1.0 + bonuses: Synergy +0.15 (reduced from +0.30 - the OPEX benefit already compounds through EBITDA), Resilience +0.20, Truth +0.15, Community +0.18 (Just-Transition scaled), Governance +0.10, Workforce +0.10, Wellbeing +0.05. Penalty: Instability -0.40. Threshold bonuses/penalties phase in across a 5-point band (no cliff edges).", "tags": ["scoring", "valuation", "sustainability", "multiplier"], "weblink": ""},
    {"id": "instability_discount", "term": "Instability Discount", "definition": "A -0.40 penalty on M_R when average SLO < 75, phased in across a 5-point band below the threshold (no cliff edge). The single most damaging scoring penalty, equivalent to losing ~$180M in terminal value. Models activist investor impairment pricing (cf. Danone 2021).", "tags": ["scoring", "penalty", "social license", "risk"], "weblink": ""},
    {"id": "archetypes", "term": "Corporate Archetypes", "definition": "Terminal strategy profiles based on M_R: Regenerative Titan (>=1.80, cf. Orsted), De-risked Safe-Haven (>=1.20), Fragile Giant (>=0.80), Stranded Relic (<0.80, cf. post-dieselgate VW).", "tags": ["scoring", "archetype", "profile", "classification"], "weblink": ""},
    # -- Frameworks & Regulation --
    {"id": "double_materiality", "term": "Double Materiality", "definition": "EU CSRD requirement (Article 19a): assess both Financial Materiality (risks to company) and Impact Materiality (company's impact on society/environment). Doubly-material issues are mandatory first-priority.", "tags": ["governance", "csrd", "regulation", "materiality"], "weblink": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464"},
    {"id": "csrd", "term": "CSRD", "definition": "Corporate Sustainability Reporting Directive. EU directive mandating double materiality assessments for ~50,000 companies from 2025. The R2 minigame operationalises CSRD through a 6-issue materiality exercise.", "tags": ["regulation", "governance", "reporting", "eu"], "weblink": "https://finance.ec.europa.eu/capital-markets-union-and-financial-markets/company-reporting-and-auditing/company-reporting/corporate-sustainability-reporting_en"},
    {"id": "tcfd", "term": "TCFD", "definition": "Task Force on Climate-related Financial Disclosures. Framework for disclosing climate risks across Governance, Strategy, Risk Management, Metrics/Targets. The R5 stochastic event models TCFD physical risk scenario analysis.", "tags": ["regulation", "climate", "disclosure", "risk"], "weblink": "https://www.fsb-tcfd.org/recommendations/"},
    {"id": "sbti", "term": "SBTi", "definition": "Science Based Targets initiative. Framework for emissions reduction aligned with Paris Agreement. R3 decisions on Scope 3 emissions map to SBTi near-term vs. long-term pathways.", "tags": ["regulation", "climate", "targets", "emissions"], "weblink": "https://sciencebasedtargets.org/"},
    {"id": "stakeholder_map", "term": "Mendelow's Stakeholder Matrix", "definition": "2x2 Power-Interest grid classifying stakeholders by influence and engagement. R1 minigame: drag 10 stakeholders. 80%+ accuracy earns reputation bonus. Mendelow, A.L. (1991).", "tags": ["strategy", "stakeholder", "governance", "framework"], "weblink": ""},
    {"id": "vrio", "term": "VRIO Framework", "definition": "Value, Rarity, Inimitability, Organisation. Strategic resource analysis per Barney (1991). Implemented as synergy decay: synergy_mult x (1-0.05) per round. Models competitive advantage erosion.", "tags": ["strategy", "competitive advantage", "resources", "rbt"], "weblink": "https://doi.org/10.1177/014920639101700108"},
    # -- Simulation Mechanics --
    {"id": "flags", "term": "Flag Dependencies", "definition": "Persistent boolean state variables encoding past decisions into future engines. Key: electronics_blindspot (R1->R4 severity doubler), ethical_ai_overhaul (R6->M_R +0.15), synergy_unlock (R7->M_R +0.15, STRAT-010).", "tags": ["mechanics", "flags", "path dependence", "decisions"], "weblink": ""},
    {"id": "bu", "term": "Business Unit (BU)", "definition": "One of four Muressons divisions: Pharma ($18M), Electronics ($16.5M, highest carbon 72), Consumer Goods ($10.5M), Software ($8.5M). Alternative verticals: Banking, Agriculture, Oil & Gas, Retail, Tech.", "tags": ["strategy", "organization", "business unit"], "weblink": ""},
    {"id": "strategic_pillars", "term": "Strategic Pillars Paradigm", "definition": "Advanced decision paradigm (multi_toggles) where players configure choices across 5 strategic areas (Energy, Operations, Supply Chain, Offsetting, HR) instead of single A/B/C.", "tags": ["strategy", "decisions", "paradigm", "pillars"], "weblink": ""},
    {"id": "cfo_override", "term": "CFO Override", "definition": "Emergency mechanism bypassing the R2 materiality gate for non-Quadrant-1 issues. Incurs -5 Group Reputation. Models tension between financial expedience and governance compliance.", "tags": ["governance", "finance", "risk", "override"], "weblink": ""},
    {"id": "round_pacing", "term": "Round Pacing", "definition": "Facilitator-controlled timing: Free Play (players advance freely) or Facilitator-Gated (facilitator unlocks each round). Enables synchronised classroom or self-paced individual experiences.", "tags": ["system", "facilitator", "timing", "classroom"], "weblink": ""},
    {"id": "just_transition", "term": "Just Transition", "definition": "ILO/UN framework ensuring the sustainability shift does not leave workers behind. R9: Closure (strike risk) vs. Managed Transition ($12M) vs. Community Fund ($20M, +0.18 M_R). Paris Agreement Art. 4.", "tags": ["social", "workforce", "transition", "community"], "weblink": "https://www.ilo.org/global/topics/green-jobs/WCMS_432859/lang--en/index.htm"},
    {"id": "circular_economy", "term": "Circular Economy", "definition": "Economic model eliminating waste through lifecycle redesign. R7 operationalises via Industrial Symbiosis (Option C: Waste-to-Energy), boosting the synergy multiplier +" + f"{_R7C_SYNERGY_BOOST:g}" + " and earning +0.15 M_R (STRAT-010: the operational benefit already compounds through EBITDA).", "tags": ["environment", "circularity", "waste", "strategy"], "weblink": "https://ellenmacarthurfoundation.org/topics/circular-economy-introduction/overview"},
    {"id": "ai_ethics", "term": "AI Ethics & Algorithmic Bias", "definition": "R6 crisis: algorithmic bias in recruitment AI. Option B (Ethical AI Overhaul, -$8M) earns Truth Premium (+0.15 M_R). Option C (Monetise) triggers EU AI Act costs. Models the EU AI Act (2024).", "tags": ["governance", "ai", "ethics", "regulation", "bias"], "weblink": "https://artificialintelligenceact.eu/"},
    {"id": "dynamic_capabilities", "term": "Dynamic Capabilities", "definition": "Teece (1997): ability to integrate, build, and reconfigure competencies to address changing environments. Modelled via synergy multiplier and VRIO decay. Continuous reinvestment required.", "tags": ["strategy", "theory", "competitive advantage", "capabilities"], "weblink": "https://doi.org/10.1002/(SICI)1097-0266(199708)18:7<509::AID-SMJ882>3.0.CO;2-Z"},
    {"id": "caroic", "term": "CAROIC (Carbon-Adjusted Return on Invested Capital)", "definition": "CAROIC = EBITDA × (1 − Tax Rate) / (Invested Capital + Carbon Tonnage × Shadow Carbon Price). Extends traditional ROIC by adding a shadow carbon cost to the denominator, penalising carbon-intensive firms. Grade scale: A+ (≥25%), A (≥15%), B (≥10%), C (≥5%), D (≥0%), F (<0%). Displayed per-round on both player and facilitator dashboards.", "tags": ["finance", "carbon", "esg", "sustainability", "roic", "metric"], "weblink": ""},
]


class GlossaryItem(BaseModel):
    id: str = ""
    term: str
    definition: str
    tags: list = []
    weblink: str = ""


@analytics_router.get("/glossary", summary="Get all glossary terms")
async def get_glossary():
    return {"terms": _glossary_terms}


@analytics_router.post("/glossary", summary="Add or update a glossary term")
async def upsert_glossary_term(item: GlossaryItem, _guard: None = Depends(_require_super_admin)):
    global _glossary_terms
    # Auto-generate ID if empty
    term_id = item.id or item.term.lower().replace(" ", "_").replace("(", "").replace(")", "")
    entry = item.dict()
    entry["id"] = term_id
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    _glossary_terms.append(entry)
    return entry


@analytics_router.delete("/glossary/{term_id}", summary="Delete a glossary term")
async def delete_glossary_term(term_id: str, _guard: None = Depends(_require_super_admin)):
    global _glossary_terms
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    return {"status": "deleted", "term_id": term_id}


# ═════════════════════════════════════════════════════════════════
#  COHORT DIVERSITY — Industry × Region heatmap (Phase 5)
# ═════════════════════════════════════════════════════════════════

def get_cohort_diversity(cohort_id: str) -> dict:
    """
    Compute the Industry Vertical × Region distribution of players in a cohort.

    Returns a dict with:
      - heatmap:       { vertical: { region: count } }
      - players_by_cell: { "vertical__region": [player_id, ...] }
      - by_vertical / by_region summary counts
    """
    from admin_shared import _player_registry
    from collections import defaultdict

    players = [
        p for p in _player_registry
        if p.get("cohort_id") == cohort_id or p.get("session_id") == cohort_id
    ]

    heatmap: dict = defaultdict(lambda: defaultdict(list))
    by_vertical: dict = defaultdict(int)
    by_region: dict = defaultdict(int)

    for p in players:
        vertical = p.get("assigned_bu") or p.get("industry_vertical") or "unassigned"
        region = p.get("region_id") or "unassigned"
        pid = p.get("player_id", "?")
        heatmap[vertical][region].append(pid)
        by_vertical[vertical] += 1
        by_region[region] += 1

    heatmap_counts = {
        v: {r: len(plist) for r, plist in regions.items()}
        for v, regions in heatmap.items()
    }
    players_by_cell = {
        f"{v}__{r}": plist
        for v, regions in heatmap.items()
        for r, plist in regions.items()
    }

    return {
        "cohort_id": cohort_id,
        "total_players": len(players),
        "heatmap": heatmap_counts,
        "players_by_cell": players_by_cell,
        "by_vertical": dict(by_vertical),
        "by_region": dict(by_region),
    }


@analytics_router.get(
    "/{session_id}/cohort-diversity",
    summary="Get Industry × Region player distribution for a cohort",
)
async def get_cohort_diversity_endpoint(
    session_id: str,
    request: Request,
    _guard: None = Depends(_require_facilitator),
):
    """Return cohort diversity heatmap — Industry Vertical × Region player counts."""
    await _assert_session_visible(request, session_id)  # F-21 (launch audit 2026-09-01)
    return get_cohort_diversity(session_id)


@analytics_router.get(
    "/{session_id}/teachable-moments",
    summary="Facilitator prompts when a cohort converges on an adverse decision flag",
)
async def get_teachable_moments_endpoint(
    session_id: str,
    request: Request,
    _guard: None = Depends(_require_facilitator),
):
    await _assert_session_visible(request, session_id)  # F-21 (launch audit 2026-09-01)
    """B5: read-only detector — surfaces a prompt when >= half a cohort's teams
    share a flag the dependency graph marks as adverse (doubles a crisis, BLOCKS
    a bonus, triggers a penalty). Players are unaffected."""
    from teachable_moments import compute_cohort_teachable_moments
    return await compute_cohort_teachable_moments(session_id)
