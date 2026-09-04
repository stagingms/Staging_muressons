"""
Muressons Global Corporation — Debrief Narrative Router
"The debrief writes itself" — UX audit §9 / item #12.

Facilitator-only, STRICTLY READ-ONLY aggregation endpoint that turns a
cohort's raw round history into the skeleton of a spoken debrief: a final
ranking, the round where the field split, each player's biggest turning
point, their pre-commit predictions paired against what actually happened,
and any auto-committed (unplayed) rounds flagged for grading.

Design notes:
- Engine untouched. No writes anywhere — every read goes through the
  parity API (db.fetch_all_sessions_raw / db.fetch_round_history), the
  same path get_cohort_pulse uses, so it behaves identically under
  Postgres and the in-memory store.
- Guarded like every other live-run surface: require_sim_manager
  (project_admin excluded) + _assert_session_ownership (H-3).
- Included by main.py as `debrief_narrative_router`; admin_router is
  imported before this module there, so the module-level guard import
  is safe.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Depends, HTTPException

import database as db  # main.py injects the selected backend into sys.modules["database"]
from admin_router import require_sim_manager, _assert_session_ownership

debrief_narrative_router = APIRouter(prefix="/api/admin", tags=["Admin — Debrief Narrative"])

# Treasury moves in the tens of millions while reputation moves in single
# points; normalise treasury deltas by $10M so the two are comparable when
# picking a player's single biggest turning point.
_TREASURY_SCALE = 10_000_000


def _series_from_history(history: list[dict]) -> list[dict]:
    """Flatten round history into a sorted per-round series of the three KPIs."""
    series = []
    for item in history:
        gs = item.get("global_state", {}) or {}
        # Audit F-03: `or 50` turned a reputation of 0.0 (a reachable state —
        # the engine clamps at 0) into 50, and the turning-point picker then
        # reported a "+23 up" swing for a team whose reputation had collapsed.
        # Only a MISSING value defaults.
        _rep = gs.get("group_reputation")
        series.append({
            "round": item.get("round_number", 1),
            "treasury": float(gs.get("corporate_treasury", 0) or 0),
            "reputation": float(50.0 if _rep is None else _rep),
            "synergy": float(gs.get("synergy_multiplier", 1.0) or 1.0),
            "auto_committed": bool((gs.get("active_event_flags") or {}).get("auto_committed")),
        })
    series.sort(key=lambda s: s["round"])
    return series


def _turning_point(series: list[dict]) -> dict | None:
    """Round with the largest scale-normalized round-over-round KPI swing."""
    best = None  # (normalized_magnitude, round, metric, delta)
    for prev, cur in zip(series, series[1:]):
        t_delta = cur["treasury"] - prev["treasury"]
        r_delta = cur["reputation"] - prev["reputation"]
        for metric, delta, magnitude in (
            ("treasury", t_delta, abs(t_delta) / _TREASURY_SCALE),
            ("reputation", r_delta, abs(r_delta)),
        ):
            if best is None or magnitude > best[0]:
                best = (magnitude, cur["round"], metric, delta)
    if best is None:
        return None
    return {
        "round": best[1],
        "metric": best[2],
        "delta": best[3],
        "direction": "up" if best[3] >= 0 else "down",
    }


def _predicted_vs_actual(predictions: dict, by_round: dict[int, dict]) -> list[dict]:
    """Pair each prediction with the KPI deltas of the round it predicted."""
    pairs = []
    for key, text in sorted(predictions.items(), key=lambda kv: str(kv[0])):
        try:
            r = int(key)
        except (TypeError, ValueError):
            continue
        cur, prev = by_round.get(r), by_round.get(r - 1)
        if cur and prev:
            actual = {
                "treasury_delta": cur["treasury"] - prev["treasury"],
                "reputation_delta": cur["reputation"] - prev["reputation"],
            }
        else:
            actual = {"treasury_delta": None, "reputation_delta": None}
        pairs.append({"round": r, "prediction": text, "actual": actual})
    return pairs


@debrief_narrative_router.get(
    "/debrief-narrative/{cohort_id}",
    summary="Read-only debrief narrative aggregation for a cohort",
)
async def get_debrief_narrative(
    cohort_id: str,
    request: Request,
    _guard: None = Depends(require_sim_manager),
):
    """Aggregate a cohort's round history into facilitator-readable debrief
    building blocks. READ-ONLY — no session, metadata, or engine writes."""
    await _assert_session_ownership(request, cohort_id)

    sessions = await db.fetch_all_sessions_raw()
    by_sid = {s.get("session_id"): s for s in sessions}
    if cohort_id not in by_sid:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")

    cohort_sess = by_sid[cohort_id]
    player_sessions = [
        s for s in sessions
        if s.get("parent_cohort_id") == cohort_id and s.get("player_id")
    ]

    try:
        players = []
        treasury_by_round: dict[int, list[tuple[float, str]]] = {}
        max_round = 0
        players_with_predictions = 0

        for sess in player_sessions:
            sid = sess["session_id"]
            name = sess.get("player_name") or sess.get("player_id") or sid[:10]
            history = await db.fetch_round_history(sid)
            series = _series_from_history(history)
            by_round = {s["round"]: s for s in series}

            for s in series:
                max_round = max(max_round, s["round"])
                treasury_by_round.setdefault(s["round"], []).append((s["treasury"], name))

            predictions = sess.get("round_predictions") or {}
            if not isinstance(predictions, dict):
                predictions = {}
            if predictions:
                players_with_predictions += 1

            final = series[-1] if series else None
            players.append({
                "session_id": sid,
                "name": name,
                "trajectory": [
                    {"round": s["round"], "treasury": s["treasury"], "reputation": s["reputation"]}
                    for s in series
                ],
                "turning_point": _turning_point(series),
                "auto_committed_rounds": [s["round"] for s in series if s["auto_committed"]],
                "predictions": predictions,
                "predicted_vs_actual": _predicted_vs_actual(predictions, by_round),
                "final": {
                    "round": final["round"],
                    "treasury": final["treasury"],
                    "reputation": final["reputation"],
                    "synergy": final["synergy"],
                } if final else None,
            })

        # Divergence: round (seen by ≥2 players) with max treasury variance.
        divergence = None
        best_var = -1.0
        for rnd, entries in treasury_by_round.items():
            if len(entries) < 2:
                continue
            vals = [t for t, _ in entries]
            mean = sum(vals) / len(vals)
            var = sum((v - mean) ** 2 for v in vals) / len(vals)
            if var > best_var:
                best_var = var
                leader = max(entries, key=lambda e: e[0])
                laggard = min(entries, key=lambda e: e[0])
                divergence = {
                    "round": rnd,
                    "treasury_spread": leader[0] - laggard[0],
                    "leader": leader[1],
                    "laggard": laggard[1],
                }

        ranking = sorted(
            (
                {
                    "name": p["name"],
                    "treasury": p["final"]["treasury"] if p["final"] else 0,
                    "reputation": p["final"]["reputation"] if p["final"] else 0,
                }
                for p in players
            ),
            key=lambda r: r["treasury"],
            reverse=True,
        )

        return {
            "cohort_id": cohort_id,
            "cohort_name": cohort_sess.get("cohort_name") or cohort_id[:10],
            "generated_over_rounds": max_round,
            "players": players,
            "divergence_round": divergence,
            "ranking": ranking,
            "prediction_coverage": {
                "players_with_predictions": players_with_predictions,
                "total_players": len(players),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # defensive: aggregation must never 500 opaquely
        raise HTTPException(
            status_code=500,
            detail=f"Debrief narrative aggregation failed for cohort '{cohort_id}': {exc}",
        )
