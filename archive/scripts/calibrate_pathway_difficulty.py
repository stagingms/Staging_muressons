"""
scripts/calibrate_pathway_difficulty.py
========================================
GAME-3 — Empirically calibrate the cross-pathway leaderboard difficulty
coefficients used by terminal_valuation.normalize_mr_for_leaderboard().

WHY
---
Teams play one of five ending pathways, and the pathways are not equally hard:
the same strategy yields different M_R distributions per pathway. To rank teams
fairly on a shared leaderboard we multiply each team's raw M_R by a per-pathway
coefficient. Those coefficients were previously hand-set (1.00–1.20). After the
GAME-2 (M_R ramps) and GAME-4 (seeded RNG) changes, the distributions shifted,
so the coefficients must be re-derived from data.

METHOD
------
For each pathway, run every strategy profile (RANDOM / FINANCIAL / ESG_OPTIMISED)
for N seeded iterations through the real engine (engine.process_tick), collect
the pathway-adjusted M_R, and take the pooled median. The coefficient is:

    coefficient[pathway] = median(M_R | activist_ultimatum) / median(M_R | pathway)

so the *median strategy* scores identically on every pathway after
normalisation. activist_ultimatum is the 1.00 reference by construction.

The result is written back into simulation_config.json under
terminal_valuation.pathway_difficulty, and a timestamped report is saved under
reports/. terminal_valuation/config.py read this key on next startup.

USAGE
-----
    # From the project root (muressons-sim/):
    python scripts/calibrate_pathway_difficulty.py            # N=200 (default)
    python scripts/calibrate_pathway_difficulty.py --n 500
    python scripts/calibrate_pathway_difficulty.py --dry-run  # print, do not write

NOTE
----
Must be run in a full environment where the backend package imports cleanly
(it drives the real engine). Re-run after any scoring change and after the
first live pilot, when real cohort score distributions are available.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Make the backend package importable ──────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

from monte_carlo_stress_test import run_single_simulation  # noqa: E402

_CONFIG_PATH = _ROOT / "simulation_config.json"
_REPORTS_DIR = _ROOT / "reports"

_PATHWAYS = [
    "activist_ultimatum",   # reference (coefficient pinned to 1.00)
    "climate_black_swan",
    "stakeholder_revolt",
    "hostile_takeover",
    "regulatory_shutdown",
]
_PROFILES = ["RANDOM", "FINANCIAL", "ESG_OPTIMISED"]
_REFERENCE = "activist_ultimatum"


def collect_mr(pathway: str, n: int, base_seed: int = 0) -> list[float]:
    """Pooled M_R samples across all profiles for one pathway."""
    samples: list[float] = []
    for profile in _PROFILES:
        for i in range(n):
            # Deterministic, distinct seed per (pathway, profile, i) so runs are
            # reproducible and every pathway sees a comparable spread of luck.
            seed = hash((base_seed, pathway, profile, i)) & 0xFFFFFFFF
            rng = random.Random(seed)
            try:
                result = run_single_simulation(profile, rng, ending_pathway=pathway)
                samples.append(result.mr)
            except Exception as exc:
                print(f"  [WARN] run failed ({pathway}/{profile}/{i}): {exc}")
    return samples


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibrate pathway difficulty coefficients (GAME-3).")
    ap.add_argument("--n", type=int, default=200, help="iterations per (pathway, profile)")
    ap.add_argument("--dry-run", action="store_true", help="print results without writing config")
    args = ap.parse_args()

    print(f"GAME-3 pathway difficulty calibration — {args.n} iters × {len(_PROFILES)} profiles per pathway\n")

    medians: dict[str, float] = {}
    spreads: dict[str, dict] = {}
    for pathway in _PATHWAYS:
        samples = collect_mr(pathway, args.n)
        if not samples:
            print(f"  {pathway}: NO SAMPLES — aborting.")
            return 1
        med = statistics.median(samples)
        medians[pathway] = med
        spreads[pathway] = {
            "n": len(samples),
            "median": round(med, 4),
            "p10": round(statistics.quantiles(samples, n=10)[0], 4),
            "p90": round(statistics.quantiles(samples, n=10)[8], 4),
            "mean": round(statistics.fmean(samples), 4),
        }
        print(f"  {pathway:<22} median M_R={med:.4f}  (n={len(samples)})")

    ref_median = medians[_REFERENCE]
    if ref_median <= 0:
        print("Reference median M_R is non-positive — cannot calibrate.")
        return 1

    coefficients = {
        pw: round(ref_median / med, 4) if med > 0 else 1.0
        for pw, med in medians.items()
    }
    coefficients[_REFERENCE] = 1.00  # pin the reference exactly

    print("\nCalibrated coefficients (= median_ref / median_pathway):")
    for pw, c in coefficients.items():
        print(f"  {pw:<22} {c:.4f}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "coefficient = median(M_R, activist_ultimatum) / median(M_R, pathway); pooled across RANDOM/FINANCIAL/ESG_OPTIMISED profiles",
        "iterations_per_pathway_per_profile": args.n,
        "profiles": _PROFILES,
        "per_pathway": spreads,
        "coefficients": coefficients,
    }

    if args.dry_run:
        print("\n[dry-run] Config not modified.")
        return 0

    # ── Write coefficients back into simulation_config.json ──
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg.setdefault("terminal_valuation", {})["pathway_difficulty"] = coefficients
    cfg["terminal_valuation"]["_pathway_difficulty_calibrated_at"] = report["generated_at"]
    with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"\n✅ Wrote coefficients to {_CONFIG_PATH}")

    _REPORTS_DIR.mkdir(exist_ok=True)
    report_path = _REPORTS_DIR / f"pathway_difficulty_calibration_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"📄 Report saved to {report_path}")
    print("\nRestart the backend (or reload config) for the new coefficients to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
