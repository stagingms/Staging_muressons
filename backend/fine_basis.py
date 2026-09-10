"""fine_basis — one applicator for the cash effects of stakeholder events.

F07 / N5 (AUDIT_Engines_Flow_Classroom50_20260909; EVAL_AuditResponse action 7,
decision D3 2026-09-10).

Two applicators (autonomous_agents Phase 3 and the NPC-cascade block in
round_logic.run_new_engines) computed a "percentage fine" as
    hit = corporate_treasury × |pct|;  treasury -= hit
so a team already in emergency credit (treasury < 0) was CREDITED cash by a
regulatory shutdown order — the −$10M team ended at −$9.6M — while the
narrative said "Fine: 4% of annual revenue". The black-swan and sandbox
applicators shared the sign bug.

Decision D3: a fine that names revenue is charged on annual revenue
(2 × Σ revenue_base — two six-month rounds, the WP-23 convention the NPC
regulator already uses); investor / journalist events act through cost of
capital and reputation, not cash; any remaining "% of treasury" shock is
charged on max(0, treasury) — a shock can empty a till, never fill one.

Effect keys understood here
    revenue_pct_fine   fraction of ANNUAL revenue, charged as cash (>= 0)
    treasury_pct_hit   fraction of the POSITIVE treasury balance (sign ignored)
    treasury_flat_hit  a fixed cash amount (sign ignored, always a charge)
"""
from __future__ import annotations

from typing import Any


def annual_revenue(bus: list[dict] | None) -> float:
    """Annual revenue = two six-month rounds of Σ revenue_base (WP-23)."""
    return round(2.0 * sum(float((b or {}).get("revenue_base", 0) or 0) for b in (bus or [])), 2)


def apply_cash_effects(effects: dict | None, gs: dict, bus: list[dict] | None) -> dict[str, float]:
    """Apply the cash effects in `effects` to gs["corporate_treasury"].

    Returns the amounts actually charged, keyed by effect — every value is
    >= 0, and a charge only ever LOWERS the treasury. Keys that are absent or
    zero produce no entry.
    """
    effects = effects or {}
    applied: dict[str, float] = {}
    treasury = float(gs.get("corporate_treasury", 0) or 0)

    fine_pct = float(effects.get("revenue_pct_fine", 0) or 0)
    if fine_pct:
        fine = round(abs(fine_pct) * annual_revenue(bus), 2)
        if fine > 0:
            treasury = round(treasury - fine, 2)
            applied["revenue_pct_fine"] = fine

    hit_pct = float(effects.get("treasury_pct_hit", 0) or 0)
    if hit_pct:
        hit = round(max(0.0, treasury) * abs(hit_pct), 2)
        if hit > 0:
            treasury = round(treasury - hit, 2)
            applied["treasury_pct_hit"] = hit

    flat = float(effects.get("treasury_flat_hit", 0) or 0)
    if flat:
        charge = round(abs(flat), 2)
        treasury = round(treasury - charge, 2)
        applied["treasury_flat_hit"] = charge

    if applied:
        gs["corporate_treasury"] = treasury
    return applied


def total_charged(applied: dict[str, float]) -> float:
    return round(sum(applied.values()), 2)


__all__: list[str] = ["annual_revenue", "apply_cash_effects", "total_charged"]
