"""
turnaround_engine.py — Post-completion Turnaround arc (P3).

A self-contained, fixed 4-round crisis-recovery arc offered AFTER a run has
completed its 10 rounds (see PLAN_Turnaround_Module_Implementation.md §4-6). It
deliberately does NOT reuse the main round commit pipeline: a normal run stays
complete at R10, its canonical result is immutable, and the arc only ever
appends `turnaround_amended_report`.

Flow:
  enter_arc()  -> Crisis phase, +$3M bailout.
  apply_commit(choice) x up to 4 -> applies a recovery lever, then runs the
    engine.detect_distress progression (crisis -> stabilisation -> recovery ->
    exit). Graduation (reach exit) lifts the M_R clamp and adds the +0.10
    premium; running out of rounds clamps M_R at the last phase cap.
  abort_arc() -> discard the arc, canonical result untouched.

Scoring note (P3 simplification, flagged for calibration): the team makes only
financial-recovery decisions during the arc, so the underlying ESG M_R is not
recomputed. The amended M_R = canonical base M_R, clamped at the phase cap while
in the arc, +0.10 on graduation. This is faithful to how the mid-sim arc's
mr_cap already works. Full ESG re-valuation can replace _finalize() later.
"""

from __future__ import annotations

from config import (
    TURNAROUND_ARC_MAX_ROUNDS,
    TURNAROUND_ARC_ENTRY_BAILOUT,
    TURNAROUND_EXIT_MR_BONUS,
    TURNAROUND_CRISIS_MR_CAP,
    TURNAROUND_STAB_MR_CAP,
    TURNAROUND_RECOVERY_MR_CAP,
)
from engine import detect_distress


# ── Recovery-round content (mirrors branching_engine.EXTENDED_ROUNDS shape) ──
# Each round offers three levers: A = disciplined/safe, B = balanced,
# C = aggressive growth bet (bigger treasury swing, larger reputation cost).
# Deltas are PLACEHOLDER calibration — they let the §2 gates be cleared from the
# distressed floor but should be play-tested (see PLAN §11 gate-calibration risk).
TURNAROUND_ROUNDS: dict[int, dict] = {
    1: {
        "title": "T1 — Triage", "phase_hint": "crisis",
        "crisis": "Creditors demand an immediate survival plan. Rebuild trust or bank cash?",
        "options": {
            "option_a": {"label": "A", "title": "Rebuild Trust First",
                         "impacts": {"treasury": 6_000_000, "reputation": 10}},
            "option_b": {"label": "B", "title": "Balanced Triage",
                         "impacts": {"treasury": 9_000_000, "reputation": 6}},
            "option_c": {"label": "C", "title": "Cash Grab",
                         "impacts": {"treasury": 14_000_000, "reputation": -4}},
        },
    },
    2: {
        "title": "T2 — Stabilise", "phase_hint": "stabilisation",
        "crisis": "The plan is approved. Convert goodwill into a durable recovery.",
        "options": {
            "option_a": {"label": "A", "title": "Reinforce Credibility",
                         "impacts": {"treasury": 8_000_000, "reputation": 20}},
            "option_b": {"label": "B", "title": "Balanced Recovery",
                         "impacts": {"treasury": 11_000_000, "reputation": 16}},
            "option_c": {"label": "C", "title": "Aggressive Expansion",
                         "impacts": {"treasury": 16_000_000, "reputation": 8}},
        },
    },
    3: {
        "title": "T3 — Rebuild", "phase_hint": "recovery",
        "crisis": "Credit rating upgraded. Push for the exit conditions.",
        "options": {
            "option_a": {"label": "A", "title": "Cement Reputation",
                         "impacts": {"treasury": 10_000_000, "reputation": 14}},
            "option_b": {"label": "B", "title": "Balanced Scale-Up",
                         "impacts": {"treasury": 14_000_000, "reputation": 11}},
            "option_c": {"label": "C", "title": "Market Blitz",
                         "impacts": {"treasury": 20_000_000, "reputation": 7}},
        },
    },
    4: {
        "title": "T4 — Prove the Comeback", "phase_hint": "recovery",
        "crisis": "Final round. Clear the exit gate to complete the turnaround.",
        "options": {
            "option_a": {"label": "A", "title": "Cement the Recovery",
                         "impacts": {"treasury": 10_000_000, "reputation": 14}},
            "option_b": {"label": "B", "title": "Balanced Finish",
                         "impacts": {"treasury": 14_000_000, "reputation": 11}},
            "option_c": {"label": "C", "title": "Bold Final Play",
                         "impacts": {"treasury": 20_000_000, "reputation": 7}},
        },
    },
}


_PHASE_MR_CAP = {
    "crisis": TURNAROUND_CRISIS_MR_CAP,
    "stabilisation": TURNAROUND_STAB_MR_CAP,
    "recovery": TURNAROUND_RECOVERY_MR_CAP,
    "exit": None,
}


def get_turnaround_round_config(n: int):
    """Return the config for turnaround round n (1..max), or None."""
    return TURNAROUND_ROUNDS.get(n)


def _flags(gs: dict) -> dict:
    return gs.setdefault("active_event_flags", {})


def is_active(gs: dict) -> bool:
    return bool(gs.get("turnaround_mode"))


def enter_arc(gs: dict, bus: list | None = None) -> dict:
    """Deliberately enter the arc at Crisis and apply the entry bailout. Assumes
    the caller has already checked eligibility + permission."""
    flags = _flags(gs)
    distress = detect_distress(
        gs.get("corporate_treasury", 0), gs.get("group_reputation", 0),
        round_number=99, current_phase="none", deliberate_entry=True,
    )
    gs["turnaround_entry_treasury"] = gs.get("corporate_treasury", 0)  # for re-valuation
    gs["turnaround_mode"] = True
    gs["turnaround_round"] = 1
    gs["game_over"] = False            # arc in progress; re-set True on finalize
    gs["game_over_reason"] = None
    flags["turnaround_phase"] = "crisis"
    flags["turnaround_status"] = "open"
    gs["corporate_treasury"] = round(
        gs.get("corporate_treasury", 0) + distress["bailout_amount"], 2)
    return {
        "turnaround_round": 1,
        "phase": "crisis",
        "bailout_applied": distress["bailout_amount"],
        "config": get_turnaround_round_config(1),
        "message": distress["message"],
    }


def apply_commit(gs: dict, bus: list | None, choice: str) -> dict:
    """Apply one recovery round's chosen lever, run the phase progression, and
    advance / terminate the arc. Returns a result dict for the API layer."""
    if not is_active(gs):
        raise ValueError("Session is not in turnaround mode")
    flags = _flags(gs)
    t_round = int(gs.get("turnaround_round", 1))
    cfg = TURNAROUND_ROUNDS.get(t_round)
    if not cfg:
        raise ValueError(f"No turnaround round {t_round}")
    opt = cfg["options"].get(choice)
    if not opt:
        raise ValueError(f"Invalid choice {choice!r}")

    # Apply the lever's financial impact.
    imp = opt["impacts"]
    gs["corporate_treasury"] = round(
        gs.get("corporate_treasury", 0) + imp.get("treasury", 0), 2)
    gs["group_reputation"] = max(0.0, min(
        100.0, gs.get("group_reputation", 0) + imp.get("reputation", 0)))

    phase = flags.get("turnaround_phase", "crisis")
    distress = detect_distress(
        gs["corporate_treasury"], gs["group_reputation"],
        round_number=99, already_in_survival=True, current_phase=phase,
    )
    new_phase = distress.get("turnaround_phase", phase)
    flags["turnaround_phase"] = new_phase

    graduated = new_phase == "exit"
    last_round = t_round >= TURNAROUND_ARC_MAX_ROUNDS

    result = {
        "turnaround_round": t_round,
        "choice": choice,
        "phase": new_phase,
        "phase_transition": bool(distress.get("phase_transition")),
        "treasury": gs["corporate_treasury"],
        "reputation": gs["group_reputation"],
        "graduated": graduated,
        "arc_complete": graduated or last_round,
        "message": distress.get("message"),
    }

    if graduated:
        flags["turnaround_graduated"] = True
        _finalize(gs, bus, graduated=True)
    elif last_round:
        flags["turnaround_final_mr_cap"] = _PHASE_MR_CAP.get(new_phase)
        _finalize(gs, bus, graduated=False)
    else:
        gs["turnaround_round"] = t_round + 1
        result["config"] = get_turnaround_round_config(t_round + 1)

    if result["arc_complete"]:
        result["amended_report"] = gs.get("turnaround_amended_report")
    return result


def _finalize(gs: dict, bus: list | None, graduated: bool) -> dict:
    """Re-value the company at the end of the arc (P: full ESG re-valuation).

    The arc changed only the financial position (treasury/reputation) and, on
    graduation, lifts the survival M_R clamp and adds the +0.10 premium — the BU
    operating state and ESG flags are untouched, so the base ESG M_R from the
    canonical R10 snapshot is still authoritative. We recompute terminal value,
    equity and price/share with the final M_R and the recovered cash position via
    the same terminal_valuation engine the R10 result used. final_report_canonical
    is never mutated; the result is written to turnaround_amended_report."""
    from terminal_valuation import calculate_terminal_value, determine_archetype
    from config import FINANCIAL_SHADOW_CARBON_PRICE

    flags = _flags(gs)
    canon = gs.get("final_report_canonical") or {}
    base_mr = canon.get(
        "regenerative_multiple",
        flags.get("regenerative_multiple", gs.get("regenerative_multiple", 0.6)))
    try:
        base_mr = float(base_mr)
    except (TypeError, ValueError):
        base_mr = 0.6

    if graduated:
        # Clamp lifted + premium; archetype may legitimately climb (the reward).
        mr_final = round(base_mr + TURNAROUND_EXIT_MR_BONUS, 3)
        survival = False
        premium = TURNAROUND_EXIT_MR_BONUS
        status = "graduated"
    else:
        cap = flags.get("turnaround_final_mr_cap")
        cap = TURNAROUND_CRISIS_MR_CAP if cap is None else float(cap)
        mr_final = round(min(base_mr, cap), 3)
        survival = True
        premium = 0.0
        status = "expired"

    # Recovered cash improves the net-debt position relative to R10.
    entry_treasury = float(gs.get("turnaround_entry_treasury", 0.0) or 0.0)
    cash_recovered = round(float(gs.get("corporate_treasury", 0.0) or 0.0) - entry_treasury, 2)
    r10_net_debt = float(flags.get("net_debt", 0.0) or 0.0)
    net_debt_new = round(r10_net_debt - cash_recovered, 2)

    exit_mult = float(flags.get("exit_multiple_applied", 12.0) or 12.0)
    carbon_tax = float(flags.get("carbon_tax_per_ton", FINANCIAL_SHADOW_CARBON_PRICE) or FINANCIAL_SHADOW_CARBON_PRICE)
    green_fund = float(gs.get("green_transition_fund", 0.0) or 0.0)
    sdg = float(gs.get("sdg_impact_score", 0.0) or 0.0)

    reval = None
    if bus:
        try:
            reval = calculate_terminal_value(
                bus, mr_final, carbon_tax_per_ton=carbon_tax,
                exit_multiple=exit_mult, green_fund_balance=green_fund,
                sdg_impact_score=sdg, net_debt=net_debt_new)
        except Exception:
            reval = None

    arch = determine_archetype(mr_final, survival_mode=survival)

    report = {
        "regenerative_multiple": mr_final,
        "base_regenerative_multiple": round(base_mr, 3),
        "graduated": graduated,
        "archetype": arch.get("key", "turnaround_manager"),
        "archetype_title": arch.get("title"),
        "final_phase": flags.get("turnaround_phase"),
        "turnaround_premium": premium,
        "recovered_treasury": gs.get("corporate_treasury"),
        "recovered_reputation": gs.get("group_reputation"),
        "cash_recovered": cash_recovered,
        "rounds_used": gs.get("turnaround_round"),
        "revalued": bool(reval),
        "source": "turnaround_arc",
    }
    if reval:
        report.update({
            "terminal_value": reval.get("terminal_value"),
            "equity_value": reval.get("equity_value"),
            "price_per_share": reval.get("price_per_share"),
            "terminal_ebitda": reval.get("terminal_ebitda"),
            "net_debt": reval.get("net_debt"),
        })

    gs["turnaround_amended_report"] = report
    flags["turnaround_status"] = status
    gs["turnaround_mode"] = False
    gs["game_over"] = True
    gs["game_over_reason"] = ("turnaround_complete" if graduated else "turnaround_expired")
    return report

def abort_arc(gs: dict, bus: list | None = None) -> dict:
    """Cancel an in-flight arc and restore the completed (R10) state. The
    canonical snapshot was never touched, so nothing needs rebuilding."""
    flags = _flags(gs)
    gs["turnaround_mode"] = False
    gs["turnaround_round"] = 0
    gs["game_over"] = True
    gs["game_over_reason"] = "completed"
    for k in ("turnaround_phase", "turnaround_final_mr_cap", "turnaround_graduated"):
        flags.pop(k, None)
    flags["turnaround_status"] = "aborted"
    gs.pop("turnaround_amended_report", None)
    gs.pop("turnaround_entry_treasury", None)
    return {"status": "aborted", "canonical": gs.get("final_report_canonical")}


def arc_state(gs: dict) -> dict:
    """Serialisable current arc state for the facilitator console / player belt."""
    flags = gs.get("active_event_flags", {})
    t_round = int(gs.get("turnaround_round", 0) or 0)
    return {
        "active": is_active(gs),
        "status": flags.get("turnaround_status", "none"),
        "phase": flags.get("turnaround_phase", "none"),
        "turnaround_round": t_round,
        "max_rounds": TURNAROUND_ARC_MAX_ROUNDS,
        "treasury": gs.get("corporate_treasury"),
        "reputation": gs.get("group_reputation"),
        "config": get_turnaround_round_config(t_round) if is_active(gs) else None,
        "amended_report": gs.get("turnaround_amended_report"),
    }


def leaderboard_annotation(gs: dict):
    """Labelled, NON-authoritative leaderboard/report annotation for a session
    that ran the arc, or None if it never did (PLAN §8). The canonical R10 M_R
    stays the authoritative leaderboard figure — this is purely additive, and
    every payload is flagged authoritative=False so a graduated arc can never be
    mistaken for the completed-run score."""
    flags = gs.get("active_event_flags", {}) or {}
    status = flags.get("turnaround_status")
    if not status or status in ("none", "open"):
        return None                      # never ran, or still in flight
    if status == "aborted":
        return {"status": "aborted", "authoritative": False}
    rep = gs.get("turnaround_amended_report") or {}
    return {
        "status": status,                                    # graduated | expired
        "graduated": rep.get("graduated"),
        "amended_regenerative_multiple": rep.get("regenerative_multiple"),
        "base_regenerative_multiple": rep.get("base_regenerative_multiple"),
        "turnaround_premium": rep.get("turnaround_premium"),
        "final_phase": rep.get("final_phase"),
        "rounds_used": rep.get("rounds_used"),
        "authoritative": False,
    }
