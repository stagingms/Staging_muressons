"""
Muressons Global Command - Admin Analytics Sub-Router (ARCH-002)
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

from fastapi import APIRouter, Body
from pydantic import BaseModel

import database as db
from admin_shared import _god_mode_settings, _get_session_paradigm

analytics_router = APIRouter(prefix="/api/admin", tags=["Admin - Analytics"])

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  GOD MODE â€” Platform Analytics (#15)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  ANALYTICS VISIBILITY â€” God Mode controls what facilitators/players see
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_analytics_visibility: dict = {
    "facilitator": {
        "decision_heatmap": True,
        "time_to_decision": True,
        "cohort_comparison": True,
        "convergence_analysis": True,
        "learning_outcomes": True,
        "risk_exposure": True,
        "materiality_matrix": True,
        "technical_reference": True,
    },
    "player": {
        "peer_benchmarking": True,
        "decision_impact": True,
        "what_if_simulator": False,
    }
}


@analytics_router.get("/god/analytics-visibility", summary="Get analytics visibility settings")
async def get_analytics_visibility():
    return _analytics_visibility


@analytics_router.put("/god/analytics-visibility", summary="Update analytics visibility settings")
async def set_analytics_visibility(body: dict = Body(...)):
    for role in ("facilitator", "player"):
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    _analytics_visibility[role][key] = bool(val)
    return _analytics_visibility


# â”€â”€ Per-Cohort Analytics Visibility â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Stored on session dict as session["analytics_visibility"] = {facilitator: {...}, player: {...}}
# Global defaults apply when a cohort has no overrides.

def resolve_analytics_visibility(session_id: str) -> dict:
    """Merge global defaults with per-cohort overrides. Cohort overrides win."""
    import copy as _copy
    merged = _copy.deepcopy(_analytics_visibility)
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
async def get_cohort_analytics_visibility(session_id: str):
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    cohort_overrides = sess.get("analytics_visibility")
    return {
        "global_defaults": _analytics_visibility,
        "cohort_overrides": cohort_overrides,
        "effective": resolve_analytics_visibility(session_id),
    }


@analytics_router.put("/cohort/{session_id}/analytics-visibility", summary="Set per-cohort analytics visibility overrides")
async def set_cohort_analytics_visibility(session_id: str, body: dict = Body(...)):
    sess = database_memory._sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    overrides = sess.setdefault("analytics_visibility", {"facilitator": {}, "player": {}})
    for role in ("facilitator", "player"):
        if role in body:
            for key, val in body[role].items():
                if key in _analytics_visibility.get(role, {}):
                    overrides.setdefault(role, {})[key] = bool(val)
    sess["analytics_visibility"] = overrides
    database_memory._persist()
    return {
        "cohort_overrides": overrides,
        "effective": resolve_analytics_visibility(session_id),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  PLATFORM-WIDE ANALYTICS (God Mode + Facilitator)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@analytics_router.get("/god/analytics", summary="Platform-wide analytics")
async def get_platform_analytics():
    """
    Compute all analytics from _global_states, _bu_states, _decision_log.
    Returns decision heatmap, time-to-decision, cohort trajectories,
    convergence, learning outcomes, and risk exposure.
    """
    import math
    from collections import defaultdict

    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states = getattr(db, '_bu_states', {})
    decision_log = getattr(db, '_decision_log', [])

    # â”€â”€ Summary counts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    cohort_sessions = {sid: s for sid, s in all_sessions.items() if not s.get("parent_cohort_id")}
    player_sessions = {sid: s for sid, s in all_sessions.items() if s.get("parent_cohort_id")}

    # â”€â”€ 1. Decision Heatmap: choice distribution per round â”€â”€â”€â”€
    decision_heatmap = defaultdict(lambda: defaultdict(int))
    for d in decision_log:
        rn = d.get("round_number", 0)
        choice = d.get("choice_selected", "")
        if choice:
            decision_heatmap[f"R{rn}"][choice] += 1

    # â”€â”€ 2. Time-to-Decision: per round timing stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ 3. Cohort Trajectories: KPI over rounds per cohort â”€â”€â”€â”€
    cohort_trajectories = {}
    for sid, sess in cohort_sessions.items():
        cname = sess.get("cohort_name", sid[:12])
        rounds = global_states.get(sid, [])
        trajectory = []
        for grs in rounds:
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

    # â”€â”€ 4. Convergence Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ 5. Learning Outcomes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    badges_awarded = defaultdict(int)
    total_student_bonuses = 0
    for sid_bonuses in _student_bonuses.values():
        for b in sid_bonuses:
            total_student_bonuses += 1
            bk = b.get("badge_key", "")
            if bk:
                badges_awarded[bk] += 1

    # â”€â”€ 6. Risk Exposure: per cohort risk trends â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            avg_carbon = round(sum(b.get("carbon_intensity", 0) for b in bus) / n, 2)
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
async def get_player_analytics(session_id: str):
    """
    Compute peer benchmarking, decision impact attribution, and
    what-if counterfactual analysis for a specific player session.
    """
    all_sessions = getattr(db, '_sessions', {})
    global_states = getattr(db, '_global_states', {})
    bu_states = getattr(db, '_bu_states', {})
    decision_log = getattr(db, '_decision_log', [])

    sess = all_sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    player_rounds = global_states.get(session_id, [])
    if not player_rounds:
        raise HTTPException(404, "No round data for this session")

    latest = player_rounds[-1]
    player_treasury = float(latest.get("corporate_treasury", 0))
    player_reputation = float(latest.get("group_reputation", 50))
    player_synergy = float(latest.get("synergy_multiplier", 1.0))

    # â”€â”€ 1. Peer Benchmarking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ 2. Decision Impact Attribution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        choice = round_decs[0].get("choice_selected", "â€”") if round_decs else "â€”"
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
            "narrative": " â€” ".join(parts) if parts else "Minimal change this round",
        })

    # â”€â”€ 3. What-If Simulator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    return {
        "peer_benchmarking": peer_benchmarking,
        "decision_impact": decision_impact,
        "what_if": what_if,
        "visibility": _analytics_visibility.get("player", {}),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# â”€â”€ Glossary CRUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_glossary_terms: list = [
    {"id": "ebitda", "term": "EBITDA", "definition": "Earnings Before Interest, Taxes, Depreciation, and Amortization â€” measures operational profitability.", "tags": ["finance", "profitability", "earnings"], "weblink": ""},
    {"id": "csf_pool", "term": "CSF Pool", "definition": "Capital Sustainability Fund â€” 20% of corporate treasury available for ESG investment allocation.", "tags": ["finance", "investment", "treasury", "esg"], "weblink": ""},
    {"id": "vrio", "term": "VRIO Radar", "definition": "Strategic resource analysis: Value, Rarity, Imitability, Organization â€” measures competitive advantage.", "tags": ["strategy", "competitive advantage", "resources"], "weblink": ""},
    {"id": "ncd", "term": "Natural Capital Debt", "definition": "Accumulated environmental liability from unsustainable resource extraction or pollution.", "tags": ["environment", "liability", "sustainability", "esg"], "weblink": ""},
    {"id": "social_license", "term": "Social License Score", "definition": "Community and stakeholder approval level for business operations (0-100 scale).", "tags": ["social", "stakeholder", "reputation", "esg"], "weblink": ""},
    {"id": "synergy", "term": "Synergy Multiplier", "definition": "Cross-BU collaboration bonus applied to combined strategic outcomes.", "tags": ["strategy", "collaboration", "business unit"], "weblink": ""},
    {"id": "cost_of_capital", "term": "Cost of Capital", "definition": "Rate of return required by investors â€” affects treasury deductions each round.", "tags": ["finance", "treasury", "investors"], "weblink": ""},
    {"id": "governance_risk", "term": "Governance Risk", "definition": "Risk from poor corporate governance â€” regulatory fines, board conflicts, compliance failures.", "tags": ["governance", "risk", "compliance", "esg"], "weblink": ""},
    {"id": "carbon_intensity", "term": "Carbon Intensity", "definition": "COâ‚‚ emissions per unit of revenue â€” lower is better for ESG compliance.", "tags": ["environment", "emissions", "carbon", "esg"], "weblink": ""},
    {"id": "water_dependency", "term": "Water Dependency", "definition": "Business unit reliance on water resources â€” higher means greater exposure to water stress crises.", "tags": ["environment", "resources", "risk"], "weblink": ""},
    {"id": "double_materiality", "term": "Double Materiality", "definition": "EU CSRD requirement: assess both impact OF the company on environment AND impact of environment ON the company.", "tags": ["governance", "csrd", "regulation", "esg"], "weblink": ""},
    {"id": "scope3", "term": "Scope 3 Emissions", "definition": "Indirect emissions from supply chain, transportation, and product lifecycle â€” hardest to measure and control.", "tags": ["environment", "emissions", "supply chain", "carbon"], "weblink": ""},
    {"id": "stakeholder_map", "term": "Stakeholder Map", "definition": "Mendelow's Matrix classifying stakeholders by Power (influence) and Interest (engagement level).", "tags": ["strategy", "stakeholder", "governance"], "weblink": ""},
    {"id": "treasury", "term": "Treasury", "definition": "Corporate cash reserves â€” main financial health indicator. Depleted by investments, crises, and operating costs.", "tags": ["finance", "cash", "investment"], "weblink": ""},
    {"id": "reputation", "term": "Reputation Score", "definition": "Public perception of the company (0-100) â€” influences customer loyalty, talent retention, and regulatory leniency.", "tags": ["social", "reputation", "brand"], "weblink": ""},
    {"id": "brand_equity", "term": "Brand Equity", "definition": "Intangible asset value from brand recognition and loyalty â€” built through reputation and stakeholder trust.", "tags": ["social", "reputation", "brand", "strategy"], "weblink": ""},
    {"id": "strategic_pillars", "term": "Strategic Pillars", "definition": "Decision paradigm where players choose specific actions across multiple ESG categories (Energy, Operations, Supply Chain, Offsetting).", "tags": ["strategy", "decisions", "esg"], "weblink": ""},
    {"id": "cfo_override", "term": "CFO Override", "definition": "Emergency mechanism to bypass materiality gate â€” incurs a reputation penalty.", "tags": ["governance", "finance", "risk"], "weblink": ""},
    {"id": "round_pacing", "term": "Round Pacing", "definition": "Facilitator-controlled timing mode: Self-paced (players advance freely), Timed (automatic countdown), or Manual (facilitator unlocks).", "tags": ["system", "facilitator", "timing"], "weblink": ""},
    {"id": "bu", "term": "Business Unit (BU)", "definition": "One of four Muressons divisions: Pharma, Electronics, Consumer Goods, Software â€” each with unique risk profiles.", "tags": ["strategy", "organization", "business unit"], "weblink": ""},
    {"id": "esg", "term": "ESG", "definition": "Environmental, Social, and Governance â€” three pillars for measuring corporate sustainability and ethical impact.", "tags": ["esg", "sustainability", "environment", "social", "governance"], "weblink": ""},
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
async def upsert_glossary_term(item: GlossaryItem):
    global _glossary_terms
    # Auto-generate ID if empty
    term_id = item.id or item.term.lower().replace(" ", "_").replace("(", "").replace(")", "")
    entry = item.dict()
    entry["id"] = term_id
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    _glossary_terms.append(entry)
    return entry


@analytics_router.delete("/glossary/{term_id}", summary="Delete a glossary term")
async def delete_glossary_term(term_id: str):
    global _glossary_terms
    _glossary_terms = [t for t in _glossary_terms if t["id"] != term_id]
    return {"status": "deleted", "term_id": term_id}

