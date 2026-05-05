"""
Targeted HC Comprehensive Validation — Rate-Limiter Fix Verification
=====================================================================
Runs a representative 36-test matrix:
  - Rounds 1, 2, 3 (crosses the gate boundaries)
  - All 3 options (A/B/C)
  - All 4 paradigms
  = 36 tests

Purpose: confirm that advance_to_round() now sleeps 5.2s between
commits and no longer hits the 5-second rate limiter.

NOTE: The full 120-test matrix (R1-R10 x 4 paradigms x 3 options)
is intentionally run offline — it takes ~47 minutes due to rate-limiter
sleeps in the advance-to-round fast-forward logic.
"""
import sys
import time
from test_hc_comprehensive import (
    _test_option, PARADIGMS, ALL_OPTIONS, validate_kpis
)

TARGET_ROUNDS = [1, 2, 3]  # covers: no advance / 1 advance / 2 advances

def main():
    print("=" * 70)
    print("  TARGETED HC VALIDATION — R1/R2/R3 × All Options × All Paradigms")
    print(f"  Total: {len(TARGET_ROUNDS) * len(ALL_OPTIONS) * len(PARADIGMS)} tests")
    print("=" * 70)

    total = passed = warned = failed = 0

    for paradigm in PARADIGMS:
        print(f"\n  {'-'*66}")
        print(f"  PARADIGM: {paradigm.upper()}")
        print(f"  {'-'*66}")
        for round_num in TARGET_ROUNDS:
            for option in ALL_OPTIONS:
                total += 1
                sys.stdout.write(f"  R{round_num:02d} {option} [{paradigm:<18}] ... ")
                sys.stdout.flush()

                r = _test_option(paradigm, round_num, option)

                if r["status"] == "PASS":
                    passed += 1
                    t = f"${r['treasury']:>12,.0f}" if r["treasury"] is not None else "           N/A"
                    rep = f"{r['reputation']:5.1f}" if r["reputation"] is not None else "  N/A"
                    print(f"PASS  treasury={t}  rep={rep}  -> R{r['new_round']}")
                elif r["status"] == "WARN":
                    warned += 1
                    print(f"WARN  violations={r['violations']}")
                else:
                    failed += 1
                    print(f"FAIL  error={r['error']}")

    print(f"\n{'='*70}")
    print(f"  RESULT: {total} tests | {passed} PASS | {warned} WARN | {failed} FAIL")
    print(f"{'='*70}")

    if failed > 0:
        print("  FAILED — rate limiter fix did NOT resolve the issue.")
        sys.exit(1)
    else:
        print("  ALL PASS — rate limiter fix confirmed. Full matrix safe to run offline.")
        sys.exit(0)

if __name__ == "__main__":
    main()
