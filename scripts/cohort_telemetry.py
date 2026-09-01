#!/usr/bin/env python3
"""Cohort telemetry — intended pedagogy vs realized experience (roadmap W4.3).

One command after each cohort: reads the stored round history of every team
session and reports what the cohort ACTUALLY experienced — share of teams
earning each M_R component, archetype and terminal-value distribution,
greenwash-scandal / black-swan / strike incidence, insolvency rate and first
bankruptcy round — the empirical side of the calibration loop. Read it next
to BALANCE_REPORT_BASELINE.md (what scripted strategies achieve) and
MODEL_CARD.md (what each parameter intends): a component no real team earns,
or a bankruptcy rate matching the bots', is a calibration finding.

Usage:
    python3 scripts/cohort_telemetry.py                  # all cohorts, print
    python3 scripts/cohort_telemetry.py --cohort NAME    # one cohort (name or id prefix)
    python3 scripts/cohort_telemetry.py --write          # also write COHORT_TELEMETRY_LATEST.md

Works on both backends: in-memory (USE_MEMORY_DB=true) and Postgres.
The report may contain team names — it is written locally and is NOT meant
to be committed.
"""

import asyncio
import os
import statistics
import sys
from collections import Counter

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
sys.path.insert(0, _BACKEND)

# The documented calculate_mr component set (same list as the balance report).
KNOWN_COMPONENTS = [
    "materiality_governance", "synergy_bonus", "resilience_bonus",
    "truth_premium", "community_champion_bonus", "just_transition_bonus",
    "workforce_bonus", "wellbeing_bonus", "instability_discount",
]


# ── pure aggregation (unit-tested in tests/test_cohort_telemetry.py) ───────

def summarize_team(history: list[dict]) -> dict | None:
    """Reduce one session's stored round history to its telemetry facts.

    history entries: {"round_number", "global_state", "business_units", "decisions"}.
    Returns None for sessions that never advanced past round 1 (lobbies).
    """
    if not history or len(history) < 2:
        return None
    last = history[-1]
    gs = last.get("global_state") or {}
    flags = gs.get("active_event_flags") or {}
    breakdown = dict(flags.get("mr_breakdown") or {})
    components = sorted(
        k for k, v in breakdown.items()
        if k not in ("base",) and not k.startswith("max_") and v
    )
    greenwash_rounds = sum(
        1 for h in history
        if ((h.get("global_state") or {}).get("active_event_flags") or {}).get("greenwashing_scandal") is True
    )
    black_swan_rounds = sum(
        1 for h in history
        if ((h.get("global_state") or {}).get("active_event_flags") or {}).get("black_swan_events")
    )
    bankrupt_round = None
    for h in history:
        t = (h.get("global_state") or {}).get("corporate_treasury")
        if t is not None and t < 0:
            bankrupt_round = h.get("round_number")
            break
    tv = flags.get("terminal_value")
    mr = flags.get("regenerative_multiple")
    return {
        "rounds_played": int(last.get("round_number") or len(history)),
        "final_treasury": gs.get("corporate_treasury"),
        "terminal_value": float(tv) if tv is not None else None,
        "mr": float(mr) if mr is not None else None,
        "archetype": flags.get("archetype") or None,
        "components": components,
        "greenwash_rounds": greenwash_rounds,
        "black_swan_rounds": black_swan_rounds,
        "bankrupt_round": bankrupt_round,
        "strike": bool(flags.get("strike_occurred")),
    }


def aggregate_cohort(teams: dict[str, dict]) -> dict:
    """Cohort-level aggregates over {team_name: summarize_team(...)}."""
    finished = {n: t for n, t in teams.items() if t and t["rounds_played"] >= 10}
    n_all, n_fin = len(teams), len(finished)
    comp_counts = Counter()
    for t in finished.values():
        for c in t["components"]:
            comp_counts[c] += 1
    tvs = [t["terminal_value"] for t in finished.values() if t["terminal_value"] is not None]
    mrs = [t["mr"] for t in finished.values() if t["mr"] is not None]
    return {
        "teams": n_all,
        "finished": n_fin,
        "component_share": {
            c: (comp_counts.get(c, 0), n_fin) for c in sorted(set(KNOWN_COMPONENTS) | set(comp_counts))
        },
        "archetypes": Counter(t["archetype"] for t in finished.values() if t["archetype"]),
        "tv_median": statistics.median(tvs) if tvs else None,
        "tv_range": (min(tvs), max(tvs)) if tvs else None,
        "mr_median": statistics.median(mrs) if mrs else None,
        "bankrupt": sum(1 for t in teams.values() if t and t["bankrupt_round"]),
        "greenwash_any": sum(1 for t in teams.values() if t and t["greenwash_rounds"]),
        "strike_any": sum(1 for t in finished.values() if t["strike"]),
    }


# ── data access ────────────────────────────────────────────────────────────

def _db():
    if os.getenv("USE_MEMORY_DB", "").lower() in ("true", "1", "yes"):
        import database_memory as db
    else:
        import database as db
    return db


async def _collect(cohort_filter: str | None):
    db = _db()
    sessions = await db.fetch_all_sessions()
    by_id = {s["session_id"]: s for s in sessions}

    def root_of(s):
        seen = set()
        while s.get("parent_cohort_id") and s["parent_cohort_id"] in by_id and s["session_id"] not in seen:
            seen.add(s["session_id"])
            s = by_id[s["parent_cohort_id"]]
        return s

    cohorts: dict[str, dict[str, dict]] = {}
    for s in sessions:
        root = root_of(s)
        root_key = f"{root.get('cohort_name') or 'unnamed'} ({root['session_id'][:8]})"
        if cohort_filter and cohort_filter.lower() not in root_key.lower() \
                and not root["session_id"].startswith(cohort_filter):
            continue
        history = await db.fetch_round_history(s["session_id"])
        summary = summarize_team(history)
        if summary:
            name = s.get("cohort_name") or s["session_id"][:8]
            cohorts.setdefault(root_key, {})[f"{name} ({s['session_id'][:8]})"] = summary
    return cohorts


# ── rendering ──────────────────────────────────────────────────────────────

def _m(v):
    return "n/a" if v is None else f"${v/1e6:,.1f}M"


def render(cohorts: dict) -> str:
    lines = ["# Cohort Telemetry Report", ""]
    lines.append("Realized experience per cohort — read against BALANCE_REPORT_BASELINE.md")
    lines.append("(scripted-strategy expectations) and MODEL_CARD.md (parameter intent).")
    lines.append("Contains team names: local artifact, do not commit.")
    lines.append("")
    if not cohorts:
        lines.append("No played sessions found (nothing with 2+ rounds of history).")
        return "\n".join(lines)
    for cname, teams in sorted(cohorts.items()):
        agg = aggregate_cohort(teams)
        lines.append(f"## {cname} — {agg['teams']} played session(s), {agg['finished']} reached R10")
        lines.append("")
        lines.append("| Team | Rounds | Terminal Value | M_R | Archetype | Bankrupt | Greenwash rounds | Black-swan rounds |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for tname, t in sorted(teams.items()):
            mr_s = f"{t['mr']:.2f}" if t["mr"] is not None else "n/a"
            lines.append(
                f"| {tname} | {t['rounds_played']} | {_m(t['terminal_value'])} | {mr_s} | "
                f"{t['archetype'] or 'n/a'} | {'R' + str(t['bankrupt_round']) if t['bankrupt_round'] else '—'} | "
                f"{t['greenwash_rounds']} | {t['black_swan_rounds']} |"
            )
        lines.append("")
        if agg["finished"]:
            lines.append(f"Median TV {_m(agg['tv_median'])} (range {_m(agg['tv_range'][0])} … {_m(agg['tv_range'][1])}); "
                         f"median M_R {agg['mr_median']:.2f}; archetypes: "
                         + ", ".join(f"{k}×{v}" for k, v in agg["archetypes"].most_common()))
            lines.append("")
            lines.append("### M_R component attainment (teams reaching R10)")
            lines.append("")
            lines.append("| Component | Teams | Share |")
            lines.append("|---|---|---|")
            for c, (n, d) in agg["component_share"].items():
                share = f"{n/d:.0%}" if d else "n/a"
                mark = " ⚠ never earned" if n == 0 else ""
                lines.append(f"| {c} | {n}/{d} | {share}{mark} |")
            lines.append("")
        lines.append(f"Incidence: bankruptcy {agg['bankrupt']}/{agg['teams']} teams; "
                     f"greenwash scandal (any round) {agg['greenwash_any']}/{agg['teams']}; "
                     f"strike {agg['strike_any']}/{max(agg['finished'],1)} finishers.")
        lines.append("")
    return "\n".join(lines)


async def main():
    cohort = None
    if "--cohort" in sys.argv:
        cohort = sys.argv[sys.argv.index("--cohort") + 1]
    cohorts = await _collect(cohort)
    report = render(cohorts)
    print(report)
    if "--write" in sys.argv:
        out = os.path.join(_ROOT, "COHORT_TELEMETRY_LATEST.md")
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(report + "\n")
        print(f"\n[written] {out}")


if __name__ == "__main__":
    asyncio.run(main())
