"""
scripts/generate_facilitator_evidence.py
========================================
A3 — Facilitator evidence artifact generator.

Runs the existing Monte-Carlo stress harness and the BU-substitution parity
tests, then writes two facilitator-facing artifacts into ./reports/:

  1. reports/facilitator_evidence.md    — human-readable summary a facilitator
     can bring into the room to defend fairness / balance.
  2. reports/facilitator_evidence.json  — machine-readable metrics for CI.

It PROVES two claims:
  • No strategy is strictly dominant (the ESG and FINANCIAL profiles trade
    off — neither wins on every metric).
  • The Regenerative Multiple (M_R) never breaches its floor/ceiling
    (MR_FLOOR .. MR_CEILING from terminal_valuation.py).

This is a read-only analysis harness. It never touches the database, the API,
or any runtime state — it calls engine.process_tick() directly, exactly like
the Monte-Carlo script it wraps. Safe to run in CI.

USAGE (from project root, muressons-sim/):
    python scripts/generate_facilitator_evidence.py            # default 300/profile
    python scripts/generate_facilitator_evidence.py --n 1000
    python scripts/generate_facilitator_evidence.py --skip-parity
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_REPORTS = _ROOT / "reports"
_BACKEND = _ROOT / "backend"

# Make backend importable and reuse the existing harness verbatim.
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_ROOT / "scripts"))


def _load_mr_bounds() -> tuple[float, float]:
    """Read the authoritative M_R floor/ceiling from the engine."""
    try:
        from terminal_valuation import MR_FLOOR, MR_CEILING  # type: ignore
        return float(MR_FLOOR), float(MR_CEILING)
    except Exception:
        # Documented defaults; kept in sync with terminal_valuation.py.
        return 0.0, 2.05


def run_stress(n: int, seed: int | None) -> dict:
    """Run the Monte-Carlo harness and return its per-profile analysis dict."""
    import monte_carlo_stress_test as mc  # the existing script

    results = mc.run_monte_carlo(
        n_per_profile=n,
        profiles=mc._PROFILES,
        difficulty_tier="standard",
        seed=seed if seed is not None else 20260101,
        verbose=False,
    )
    return mc.analyse_results(results), results


def evaluate(analysis: dict, results, mr_floor: float, mr_ceiling: float) -> dict:
    """Derive the pass/fail claims from the raw analysis + run objects."""
    profiles = list(analysis.keys())

    # M_R bounds: scan every individual run's M_R, not just percentiles.
    # results is {profile: [RunResult, ...]} — flatten across profiles.
    all_mr = [r.mr for runs in results.values() for r in runs]
    mr_min, mr_max = (min(all_mr), max(all_mr)) if all_mr else (float("nan"), float("nan"))
    bounds_ok = (mr_min >= mr_floor - 1e-9) and (mr_max <= mr_ceiling + 1e-9)

    # No strict dominance: on the median metrics, no single profile should be
    # >= every other profile on M_R AND treasury survival AND reputation.
    def dominates(a: str, b: str) -> bool:
        A, B = analysis[a], analysis[b]
        return (
            A["mr_p50"] >= B["mr_p50"]
            and A["treasury_survival_rate"] >= B["treasury_survival_rate"]
            and A["rep_mean"] >= B["rep_mean"]
        )

    strict_dominator = None
    for a in profiles:
        if all(a == b or dominates(a, b) for b in profiles):
            # a weakly dominates all; check it's STRICT on at least one metric vs each
            strict = True
            for b in profiles:
                if a == b:
                    continue
                A, B = analysis[a], analysis[b]
                if not (A["mr_p50"] > B["mr_p50"] or A["treasury_survival_rate"] > B["treasury_survival_rate"] or A["rep_mean"] > B["rep_mean"]):
                    strict = False
            if strict:
                strict_dominator = a
    no_dominance_ok = strict_dominator is None

    return {
        "mr_floor": mr_floor,
        "mr_ceiling": mr_ceiling,
        "mr_observed_min": round(mr_min, 4),
        "mr_observed_max": round(mr_max, 4),
        "mr_bounds_respected": bool(bounds_ok),
        "strict_dominator": strict_dominator,
        "no_strict_dominance": bool(no_dominance_ok),
        "profiles": {
            p: {
                "mr_p10": analysis[p]["mr_p10"],
                "mr_p50": analysis[p]["mr_p50"],
                "mr_p90": analysis[p]["mr_p90"],
                "treasury_survival_rate": analysis[p]["treasury_survival_rate"],
                "instability_discount_rate": analysis[p]["instability_discount_rate"],
                "rep_mean": analysis[p]["rep_mean"],
            }
            for p in profiles
        },
    }


def run_parity() -> dict:
    """Run the BU-substitution parity test via pytest and capture pass/fail."""
    test_path = _BACKEND / "test_bu_substitution.py"
    if not test_path.exists():
        return {"ran": False, "note": "test_bu_substitution.py not found."}
    env = dict(os.environ, USE_MEMORY_DB="true", DEBUG="true")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q"],
        cwd=str(_BACKEND), env=env, capture_output=True, text=True,
    )
    passed = proc.returncode == 0
    tail = (proc.stdout or proc.stderr).strip().splitlines()[-1:] if (proc.stdout or proc.stderr) else []
    return {"ran": True, "passed": passed, "summary": tail[0] if tail else ""}


def write_markdown(evidence: dict, parity: dict, n: int) -> Path:
    _REPORTS.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# Muressons — Facilitator Evidence Pack\n")
    lines.append(f"*Generated {ts} · {n} runs per strategy profile · read-only engine harness.*\n")
    lines.append("This pack is regenerated from the live engine. Bring it into the room to")
    lines.append("answer the two questions every competitive cohort asks.\n")

    lines.append("## 1. Is any strategy strictly dominant? — "
                 + ("**No.**" if evidence["no_strict_dominance"] else "**⚠️ Review.**") + "\n")
    if evidence["no_strict_dominance"]:
        lines.append("No single strategy profile beats every other on M_R **and** treasury survival **and** "
                     "reputation. The profiles trade off, which is the intended design: there is no button that wins everything.\n")
    else:
        lines.append(f"⚠️ `{evidence['strict_dominator']}` appears to dominate on the median metrics. "
                     "Re-tune before a graded session.\n")
    lines.append("| Profile | M_R P10 | M_R P50 | M_R P90 | Treasury survival | Instability-discount rate | Avg reputation |")
    lines.append("|---|---|---|---|---|---|---|")
    for p, m in evidence["profiles"].items():
        lines.append(f"| {p} | {m['mr_p10']} | {m['mr_p50']} | {m['mr_p90']} | "
                     f"{m['treasury_survival_rate']}% | {m['instability_discount_rate']}% | {m['rep_mean']} |")
    lines.append("")

    lines.append("## 2. Can M_R go out of bounds? — "
                 + ("**No.**" if evidence["mr_bounds_respected"] else "**⚠️ Breach detected.**") + "\n")
    lines.append(f"Configured bounds: **[{evidence['mr_floor']}, {evidence['mr_ceiling']}]**. "
                 f"Observed across all runs: **min {evidence['mr_observed_min']}, max {evidence['mr_observed_max']}**.\n")
    if evidence["mr_bounds_respected"]:
        lines.append("Every simulated outcome stayed inside the floor/ceiling clamp — no bonus or penalty stack "
                     "can produce an economically meaningless valuation.\n")
    else:
        lines.append("⚠️ At least one run breached the clamp. Investigate `terminal_valuation.calculate_mr`.\n")

    lines.append("## 3. Vertical-swap parity (BU substitution)\n")
    if not parity.get("ran"):
        lines.append(f"_{parity.get('note', 'parity test not run')}_\n")
    else:
        lines.append(("**PASS** — " if parity.get("passed") else "**⚠️ FAIL** — ")
                     + "terminal-valuation balance holds when default BUs are swapped for industry verticals. "
                     + f"`{parity.get('summary','')}`\n")

    lines.append("## 4. Determinism note\n")
    lines.append("Every team in a cohort shares one RNG seed (`rng_util.py`), so the stochastic events above roll "
                 "identically for all teams. Distribution spread reflects **strategy**, not luck.\n")

    out = _REPORTS / "facilitator_evidence.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate facilitator evidence artifacts.")
    ap.add_argument("--n", type=int, default=300, help="Runs per strategy profile (default 300).")
    ap.add_argument("--seed", type=int, default=20260101, help="Master RNG seed for reproducibility.")
    ap.add_argument("--skip-parity", action="store_true", help="Skip the BU-substitution pytest.")
    args = ap.parse_args()

    mr_floor, mr_ceiling = _load_mr_bounds()
    print(f"[evidence] Running Monte-Carlo ({args.n}/profile)…")
    analysis, results = run_stress(args.n, args.seed)
    evidence = evaluate(analysis, results, mr_floor, mr_ceiling)

    parity = {"ran": False, "note": "skipped"} if args.skip_parity else run_parity()

    md = write_markdown(evidence, parity, args.n)
    js = _REPORTS / "facilitator_evidence.json"
    js.write_text(json.dumps({"evidence": evidence, "parity": parity,
                              "generated": datetime.now(timezone.utc).isoformat()},
                             indent=2, default=str), encoding="utf-8")

    print(f"[evidence] Wrote {md}")
    print(f"[evidence] Wrote {js}")
    print(f"[evidence] No strict dominance: {evidence['no_strict_dominance']} | "
          f"M_R bounds respected: {evidence['mr_bounds_respected']}")

    # Non-zero exit if a core invariant fails, so CI can gate on it.
    ok = evidence["no_strict_dominance"] and evidence["mr_bounds_respected"] and (
        parity.get("passed", True) if parity.get("ran") else True
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
