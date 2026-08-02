"""
dry_run.py — Facilitator pre-flight simulator ("fly the cohort before the class does").

Plays N bot strategies through the REAL engine pipeline (pre_tick →
process_tick → post_tick → run_new_engines — the same call chain as
commit-turn) headlessly, from the cohort's CURRENT state to round 10, and
returns a difficulty report: bankruptcy risk, per-round KPI medians, which
crises actually bite, stakeholder escalations, and config warnings.

Design constraints:
  • Pure & side-effect free: operates on deepcopies; NOTHING is persisted.
    The real cohort is untouched (verified by the state-untouched test).
  • Deterministic per (strategy, rep): each rep pins both entropy channels the
    engine uses — the global `random` module and the GAME-4 `stochastic_seed`
    event_rng streams (same technique as the stakeholder golden oracle).
  • Bot choices are DATA-DRIVEN: options are scored from their configured
    impacts, so bots keep working when a facilitator re-tunes round configs.
"""

from __future__ import annotations

import copy
import random
import statistics
from typing import Any, Optional

from engine import process_tick
from round_logic import pre_tick, post_tick, run_new_engines
from round_configs import get_round_options, get_round_crisis
from config import CSF_POOL_TREASURY_FRACTION, CSF_POOL_FLOOR

# ── Bot strategies ───────────────────────────────────────────────────────────
# capex_frac: share of the CSF pool the bot deploys each round (None = chaotic
# rng draw). dividends: paid per round after R1. scorer: how options are ranked.
STRATEGIES: dict[str, dict] = {
    "aggressive_green": {"label": "🌱 Aggressive Green", "capex_frac": 0.8, "dividends": 0,        "scorer": "green"},
    "extractive":       {"label": "🏭 Extractive",       "capex_frac": 0.05, "dividends": 1_000_000, "scorer": "profit"},
    "balanced":         {"label": "⚖️ Balanced",         "capex_frac": 0.35, "dividends": 500_000,  "scorer": "balanced"},
    "chaotic":          {"label": "🎲 Chaotic",          "capex_frac": None, "dividends": None,     "scorer": "random"},
}


def _option_scores(impacts: dict) -> tuple[float, float]:
    """(profit_score, green_score) for one option's configured impacts."""
    profit = (impacts.get("treasury", 0) or 0) / 1e6 + 2 * (impacts.get("revenue_delta", 0) or 0) / 1e6
    green = (
        (impacts.get("reputation_delta", 0) or 0)
        + (impacts.get("social_license_delta", 0) or 0)
        - (impacts.get("carbon_intensity_delta", 0) or 0)
        - (impacts.get("governance_risk_delta", 0) or 0)
        - (impacts.get("natural_capital_debt_delta", 0) or 0) / 10.0
    )
    return profit, green


def _pick_choice(round_number: int, scorer: str, rng: random.Random) -> str:
    opts = get_round_options(round_number) or {}
    keys = sorted(k for k in opts if k.startswith("option_"))
    if not keys:
        return "option_b"
    if scorer == "random":
        return rng.choice(keys)
    best_key, best_val = keys[0], float("-inf")
    for k in keys:
        profit, green = _option_scores((opts[k] or {}).get("impacts", {}) or {})
        val = {"profit": profit, "green": green, "balanced": profit + green}[scorer]
        if val > best_val:
            best_key, best_val = k, val
    return best_key


def _decisions(round_number: int, bus: list[dict], treasury: float,
               strategy: dict, rng: random.Random) -> list[dict]:
    """Build a production-shaped decision list for this round.

    decision_node_id uses the dynamically-whitelisted `round_{n}_{bu}` form so
    the R2 CFO materiality gate treats bot capex as materially justified —
    bots do not play the materiality mini-game; the report notes this.
    """
    choice = _pick_choice(round_number, strategy["scorer"], rng)
    csf_pool = max((treasury or 0) * CSF_POOL_TREASURY_FRACTION, CSF_POOL_FLOOR)
    frac = strategy["capex_frac"]
    if frac is None:
        frac = rng.uniform(0.0, 0.9)
    per_bu = max(1.0, (frac * csf_pool) / max(1, len(bus)))
    decs = []
    for bu in bus:
        capex = round(per_bu, 2)
        decs.append({
            "bu_id": bu["bu_id"],
            "decision_node_id": f"round_{round_number}_{bu['bu_id']}",
            "choice_selected": choice,
            "capex_allocated": capex,
            "investment_ratio": max(0.0, min(1.0, capex / csf_pool if csf_pool else 0.0)),
            "time_to_decision_seconds": 30,
            "team_consensus": "majority",
        })
    return decs


_NPC_STAGE_ORDER = {"dormant": 0, "watchful": 1, "watching": 1, "concerned": 2,
                    "critical": 3, "agitated": 3, "investigation": 3,
                    "hostile": 4, "triggered": 5}


def _worst_npc_stage(gs: dict) -> int:
    worst = 0
    for nd in ((gs.get("npc_stakeholders") or {}).get("npcs") or {}).values():
        worst = max(worst, _NPC_STAGE_ORDER.get(str(nd.get("escalation_level", "")).lower(), 0))
    return worst


def _run_one(initial_global: dict, initial_bus: list[dict], strategy_id: str,
             seed: int, end_round: int, paradigm: str, ped_overrides: dict,
             difficulty_tier: str) -> dict:
    """One seeded bot playthrough. Returns the per-round trajectory + events."""
    strategy = STRATEGIES[strategy_id]
    rng = random.Random(seed)
    random.seed(seed)  # engines that roll on the bare global random module

    gs = copy.deepcopy(initial_global)
    bus = copy.deepcopy(initial_bus)
    gs.setdefault("active_event_flags", {})["stochastic_seed"] = f"dryrun-{strategy_id}-{seed}"
    gs["active_event_flags"]["difficulty_tier"] = difficulty_tier

    start_round = int(gs.get("round_number", 1) or 1)
    rounds_out = []
    bankrupt_round = None
    escalation_peak = 0

    for rnd in range(start_round, end_round + 1):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(ped_overrides)
        dividends = strategy["dividends"]
        if dividends is None:
            dividends = rng.choice([0, 500_000, 1_500_000])
        if rnd == 1:
            dividends = 0
        decs = _decisions(rnd, bus, gs.get("corporate_treasury", 0), strategy, rng)

        prev_treasury = gs.get("corporate_treasury", 0) or 0
        prev_rep = gs.get("group_reputation", 0) or 0

        # ── Production call chain (see _commit_turn_impl) ──
        pre = pre_tick(round_number=rnd, current_global=gs, current_bus=bus,
                       decisions=decs, crisis_severity=40.0, force_override_cfo=False)
        if "validation_error" in pre:
            # A gate refused the bot's plan (e.g. an industry-specific rule):
            # degrade to zero-capex and retry once, as a cautious human would.
            for d in decs:
                d["capex_allocated"] = 1.0
                d["investment_ratio"] = 0.0
            pre = pre_tick(round_number=rnd, current_global=gs, current_bus=bus,
                           decisions=decs, crisis_severity=40.0, force_override_cfo=True)
        severity = pre.get("crisis_severity", 40.0)

        tick = process_tick(
            current_global=gs, current_bus=bus, decisions=decs,
            dividends_paid=dividends, crisis_severity=severity,
            imitation_decay_rate=0.05, decision_paradigm=paradigm,
        )
        new_gs, new_bus, events = tick["global_state"], tick["bu_states"], tick["events"]
        events.update(pre.get("pre_events", {}))
        new_gs.setdefault("active_event_flags", {})["stochastic_seed"] = gs["active_event_flags"]["stochastic_seed"]
        new_gs["active_event_flags"]["difficulty_tier"] = difficulty_tier
        try:
            post_tick(round_number=rnd, global_state=new_gs, bu_states=new_bus,
                      decisions=decs, events=events,
                      previous_flags=gs.get("active_event_flags", {}),
                      decision_paradigm=paradigm)
        except Exception:
            pass
        events["decisions_raw"] = decs
        events["dividends_paid"] = dividends
        new_gs["pedagogical_overrides"] = dict(ped_overrides)
        try:
            run_new_engines(round_number=rnd, global_state=new_gs,
                            bu_states=new_bus, events=events)
        except Exception:
            pass

        treasury = new_gs.get("corporate_treasury", 0) or 0
        rep = new_gs.get("group_reputation", 0) or 0
        if bankrupt_round is None and treasury < 0:
            bankrupt_round = rnd
        stage = _worst_npc_stage(new_gs)
        escalation_peak = max(escalation_peak, stage)
        rounds_out.append({
            "round": rnd,
            "treasury": round(treasury, 2),
            "treasury_delta": round(treasury - prev_treasury, 2),
            "reputation": round(rep, 2),
            "reputation_delta": round(rep - prev_rep, 2),
            "min_slo": round(min((b.get("social_license_score", 50) or 0) for b in new_bus), 2),
            "npc_stage": stage,
        })
        gs, bus = new_gs, new_bus

    return {
        "rounds": rounds_out,
        "bankrupt_round": bankrupt_round,
        "escalation_peak": escalation_peak,
        "final_treasury": rounds_out[-1]["treasury"] if rounds_out else None,
        "final_reputation": rounds_out[-1]["reputation"] if rounds_out else None,
    }


def _median(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 2) if vals else None


def run_dry_run(initial_global: dict, initial_bus: list[dict], *,
                settings: Optional[dict] = None,
                strategies: Optional[list[str]] = None,
                n_reps: int = 3, end_round: int = 10,
                paradigm: str = "legacy_abc",
                difficulty_tier: str = "standard") -> dict:
    """Full pre-flight report. Pure: inputs are deepcopied, nothing persisted."""
    settings = settings or {}
    strategies = [s for s in (strategies or list(STRATEGIES)) if s in STRATEGIES]
    n_reps = max(1, min(5, int(n_reps)))
    ped_overrides = {k: v for k, v in settings.items()
                     if isinstance(k, str) and k.endswith("_enabled") or k == "difficulty_tier"}
    start_round = int(initial_global.get("round_number", 1) or 1)

    per_strategy: dict[str, Any] = {}
    for sid in strategies:
        runs = [
            _run_one(initial_global, initial_bus, sid, seed=90_000 + i * 7 + hash(sid) % 1000,
                     end_round=end_round, paradigm=paradigm,
                     ped_overrides=ped_overrides, difficulty_tier=difficulty_tier)
            for i in range(n_reps)
        ]
        rounds_axis = list(range(start_round, end_round + 1))
        per_strategy[sid] = {
            "label": STRATEGIES[sid]["label"],
            "reps": n_reps,
            "bankruptcy_risk": round(sum(1 for r in runs if r["bankrupt_round"] is not None) / len(runs), 2),
            "first_bankrupt_round": _median([r["bankrupt_round"] for r in runs]),
            "final_treasury_median": _median([r["final_treasury"] for r in runs]),
            "final_reputation_median": _median([r["final_reputation"] for r in runs]),
            "escalation_peak": max(r["escalation_peak"] for r in runs),
            "treasury_by_round": [
                _median([run["rounds"][i]["treasury"] for run in runs if i < len(run["rounds"])])
                for i in range(len(rounds_axis))
            ],
            "reputation_by_round": [
                _median([run["rounds"][i]["reputation"] for run in runs if i < len(run["rounds"])])
                for i in range(len(rounds_axis))
            ],
            "min_slo": _median([min((r["min_slo"] for r in run["rounds"]), default=None) for run in runs]),
            "_runs": runs,  # kept for crisis-bite aggregation; stripped below
        }

    # ── Crisis bite: median KPI deltas in each scripted SHOCK round ──
    # Railway audit §3.3: get_round_crisis() also returns entries for the
    # decision-gate rounds (R1 "ESG Audit Decision", R2 "Double Materiality
    # Matrix") — listing those as "crises" with positive deltas was noise
    # that undermined the report. Only true exogenous shocks belong here.
    _SHOCK_ROUNDS = {3, 4, 5, 6, 8, 9, 10}
    crisis_bite = []
    for rnd in range(start_round, end_round + 1):
        if rnd not in _SHOCK_ROUNDS:
            continue
        crisis = None
        try:
            crisis = get_round_crisis(rnd)
        except Exception:
            pass
        if not crisis:
            continue
        t_deltas, r_deltas = [], []
        for s in per_strategy.values():
            for run in s["_runs"]:
                for row in run["rounds"]:
                    if row["round"] == rnd:
                        t_deltas.append(row["treasury_delta"])
                        r_deltas.append(row["reputation_delta"])
        crisis_bite.append({
            "round": rnd,
            "name": crisis.get("name") or crisis.get("title") or f"Round {rnd} crisis",
            "median_treasury_delta": _median(t_deltas),
            "median_reputation_delta": _median(r_deltas),
        })
    for s in per_strategy.values():
        s.pop("_runs", None)

    # ── Warnings & difficulty grade ──
    warnings = []
    g = per_strategy.get("aggressive_green")
    e = per_strategy.get("extractive")
    if e and e["bankruptcy_risk"] == 0 and (e["final_reputation_median"] or 0) >= 40:
        warnings.append("Extractive play survives comfortably with acceptable reputation — "
                        "consider raising market hostility or the carbon fee if you want ESG neglect to hurt.")
    if g and g["bankruptcy_risk"] >= 0.5:
        warnings.append("The green strategy goes bankrupt in most runs — treasury may be too tight "
                        "for sustainability investment to be viable. Consider a higher starting treasury.")
    survivors = sum(1 for s in per_strategy.values() if s["bankruptcy_risk"] < 0.5)
    if survivors == 0:
        warnings.append("Every strategy tends to bankrupt — this configuration is likely too punishing for a first-time cohort.")
    finals = [s["final_reputation_median"] for s in per_strategy.values() if s["final_reputation_median"] is not None]
    if len(finals) >= 2 and (max(finals) - min(finals)) < 5:
        warnings.append("Final reputation barely differs across opposed strategies — outcomes may feel "
                        "insensitive to student choices. Check that ESG-relevant toggles are on.")
    if not warnings:
        warnings.append("No red flags: opposed strategies produce distinct, survivable-but-consequential trajectories.")

    grade = ("forgiving" if survivors == len(per_strategy) and e and e["bankruptcy_risk"] == 0
             else "brutal" if survivors == 0
             else "punishing" if survivors <= max(1, len(per_strategy) // 2)
             else "balanced")

    return {
        "start_round": start_round,
        "end_round": end_round,
        "rounds_axis": list(range(start_round, end_round + 1)),
        "n_reps": n_reps,
        "strategies": per_strategy,
        "crisis_bite": crisis_bite,
        "warnings": warnings,
        "difficulty_grade": grade,
        "notes": [
            "Bots do not play the Double Materiality mini-game; their Round-2 capex is treated as materially justified.",
            "Each strategy runs multiple seeded repetitions; figures are medians across repetitions.",
            "The dry run is fully isolated — your cohort's real state is never touched.",
        ],
    }
