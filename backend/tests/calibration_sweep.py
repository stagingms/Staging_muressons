"""The Phase 5 calibration sweep — the driver behind docs/verification/phase5_recalibration.md.

Not a test, and deliberately not named like one: it is a measurement instrument
that takes minutes, and the assertions it justifies live in test_calibration.py.
It sits in tests/ next to the two harnesses it drives, the same way
golden_matrix_harness.py and stress_harness.py do.

    python3 tests/calibration_sweep.py sweep   <seed> <n> [swans]   # append pairs
    python3 tests/calibration_sweep.py summary [file]               # §2 §4.1 §4.3 §4.4
    python3 tests/calibration_sweep.py ceilings [file]              # §4.2
    python3 tests/calibration_sweep.py isolate [n] [seed]           # §3, with controls
    python3 tests/calibration_sweep.py compare <before> <after>     # §5.2
    python3 tests/calibration_sweep.py surface [n] [seed]           # §8.1

`sweep` APPENDS JSONL, one line per paired game, so a shell timeout or a killed
run costs only the games it had not written yet. 550 pairs take about 42 seconds.
The published figures are 3,300 pairs per regime: seeds 1-3 with black swans off
and 11-13 with them on.
"""
from __future__ import annotations

import json
import logging
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_HERE))

os.environ.setdefault("USE_MEMORY_DB", "true")

DEFAULT_OUT = _BACKEND / "tests" / ".calibration_sweep.jsonl"


def _quiet():
    """The engine logs a line per round at INFO and a dual-form warning per run.
    A 3,300-game sweep with that on is unreadable and measurably slower."""
    logging.disable(logging.CRITICAL)


# ── collection ────────────────────────────────────────────────────────────
def cmd_sweep(argv: list[str]) -> None:
    import time
    _quiet()
    seed = int(argv[0])
    n = int(argv[1])
    swans = len(argv) > 2 and argv[2] == "swans"
    out = Path(argv[3]) if len(argv) > 3 else DEFAULT_OUT

    import stress_harness as S
    t0, written = time.time(), 0
    with open(out, "a", encoding="utf-8") as fh:
        for spec in S.sample_specs(n, seed, swans):
            a = S.run(spec, "2026.09")
            b = S.run(spec, "2026.10")
            fh.write(json.dumps({"09": asdict(a), "10": asdict(b)}) + "\n")
            written += 1
    print(f"seed={seed} n={n} swans={swans} -> {written} pairs "
          f"in {time.time() - t0:.1f}s  ({out})")


def _load(path: str | Path | None) -> list[dict]:
    p = Path(path) if path else DEFAULT_OUT
    if not p.exists():
        sys.exit(f"no sweep file at {p} — run `calibration_sweep.py sweep` first")
    return [json.loads(line) for line in p.open(encoding="utf-8")]


# ── §2, §4.1, §4.3, §4.4 ──────────────────────────────────────────────────
def cmd_summary(argv: list[str]) -> None:
    import stress_harness as S
    rows = _load(argv[0] if argv else None)
    fails = sum(1 for r in rows if r["09"]["failed"] or r["10"]["failed"])
    print(f"pairs: {len(rows)}  failures: {fails}")

    for regime, keep in (("swans OFF", False), ("swans ON", True)):
        sub = [r for r in rows if bool(r["09"]["swans"]) is keep]
        if not sub:
            continue
        print(f"\n===== {regime}  (n={len(sub)}) =====")
        for field in ("mr", "terminal_value", "exit_multiple", "wacc",
                      "sct", "sdg_index", "m_sdg"):
            a = S.describe([r["09"][field] for r in sub])
            b = S.describe([r["10"][field] for r in sub])
            print("  %-15s 09 p05/p50/p95 = %12.4f %12.4f %12.4f   10 = %12.4f %12.4f %12.4f"
                  % (field, a["p05"], a["p50"], a["p95"], b["p05"], b["p50"], b["p95"]))
        d_mr = [r["10"]["mr"] - r["09"]["mr"] for r in sub]
        d_tv = [S.relative_delta(r["09"]["terminal_value"], r["10"]["terminal_value"])
                for r in sub]
        q = S.describe(d_mr)
        print("  paired dM_R      : mean %+0.4f  p05 %+0.4f  p50 %+0.4f  p95 %+0.4f  worst %+0.4f"
              % (st.mean(d_mr), q["p05"], q["p50"], q["p95"], min(d_mr)))
        q = S.describe(d_tv)
        print("  paired dTV (rel) : mean %+0.2f%%  p05 %+0.2f%%  p50 %+0.2f%%  p95 %+0.2f%%"
              % (st.mean(d_tv) * 100, q["p05"] * 100, q["p50"] * 100, q["p95"] * 100))
        moved = sum(1 for r in sub if r["09"]["archetype"] != r["10"]["archetype"])
        print("  archetype changed: %d/%d (%.1f%%)" % (moved, len(sub), moved / len(sub) * 100))
        for arm in ("09", "10"):
            c = Counter(r[arm]["archetype"] for r in sub)
            print("    2026.%s: %s" % (arm, dict(c.most_common())))
        for label, key in (("ceiling", "mr_ceiling_clamped"), ("floor", "mr_floor_clamped")):
            print("  M_R %-7s clamped 09/10: %d / %d"
                  % (label, sum(r["09"][key] for r in sub), sum(r["10"][key] for r in sub)))
        print("  SCT at 0   09/10: %d / %d"
              % (sum(1 for r in sub if r["09"]["sct"] <= 0),
                 sum(1 for r in sub if r["10"]["sct"] <= 0)))
        print("  SCT at 100 09/10: %d / %d"
              % (sum(1 for r in sub if r["09"]["sct"] >= 100),
                 sum(1 for r in sub if r["10"]["sct"] >= 100)))

    v = sorted(r["10"]["sct"] for r in rows)
    n = len(v)
    print("\n2026.10 SCT over %d games: min %.1f  max %.1f  mean %.2f" % (n, v[0], v[-1], st.mean(v)))
    print("  deciles:", [round(v[int(q * n / 10)], 1) for q in range(1, 10)])
    for lo, hi in ((0, 0), (1, 10), (11, 25), (26, 50), (51, 75), (76, 100)):
        c = sum(1 for x in v if lo <= x <= hi)
        print("  [%3d,%3d] %5d  %5.1f%%" % (lo, hi, c, c / n * 100))


# ── §4.2 ──────────────────────────────────────────────────────────────────
def cmd_ceilings(argv: list[str]) -> None:
    import terminal_valuation as TV
    rows = _load(argv[0] if argv else None)
    print("PUBLISHED CEILINGS  :", TV.MR_PUBLISHED_CEILINGS)
    print("PATHWAY_MR_HEADROOM :", TV.PATHWAY_MR_HEADROOM)
    print("global clamp        : [%s, %s]\n" % (TV.MR_FLOOR, TV.MR_CEILING))
    for arm in ("09", "10"):
        by = defaultdict(list)
        for r in rows:
            by[r[arm]["pathway"]].append(r[arm]["mr_raw"])
        print(f"-- rules 2026.{arm} — max PRE-CLAMP M_R observed, by pathway --")
        for pw in sorted(by):
            v = sorted(by[pw])
            allowed = TV.max_achievable_mr_for({"ending_pathway": pw})
            over = sum(1 for x in v if x > allowed + 1e-9)
            print("   %-22s n=%4d  max=%6.4f  p95=%6.4f  headroom=%.2f  allowed=%6.4f  over=%d"
                  % (pw, len(v), v[-1], v[int(.95 * len(v))],
                     TV.PATHWAY_MR_HEADROOM.get(pw, 0.0), allowed, over))
        pub = sum(1 for r in rows if r[arm]["mr"] > TV.MR_PUBLISHED_CEILINGS["base"] + 1e-9)
        jt = sum(1 for r in rows if r[arm]["mr"] > TV.MR_PUBLISHED_CEILINGS["jt_scaled"] + 1e-9)
        new = sum(1 for r in rows
                  if r[arm]["mr"] > TV.max_achievable_mr_for(
                      {"ending_pathway": r[arm]["pathway"]}) + 1e-9)
        print("   above published 1.93: %d/%d   above 2.02: %d   above the corrected ceiling: %d\n"
              % (pub, len(rows), jt, new))
    for arm in ("09", "10"):
        c = sum(1 for r in rows if r[arm]["mr_ceiling_clamped"])
        f = sum(1 for r in rows if r[arm]["mr_floor_clamped"])
        print("2026.%s clamp: ceiling %d/%d (%.2f%%)   floor %d/%d (%.2f%%)"
              % (arm, c, len(rows), c / len(rows) * 100, f, len(rows), f / len(rows) * 100))


# ── §3 ────────────────────────────────────────────────────────────────────
def cmd_isolate(argv: list[str]) -> None:
    _quiet()
    n = int(argv[0]) if argv else 120
    seed = int(argv[1]) if len(argv) > 1 else 7
    import rules as R
    import stress_harness as S

    specs = S.sample_specs(n, seed)
    base = [S.run(sp, "2026.09") for sp in specs]
    OFF = {k: False for k in R.SWITCHES}
    C09 = dict(R.RULE_SETS["2026.09"].calibration)
    C10 = dict(R.RULE_SETS["2026.10"].calibration)

    def arm(tag, switches, calibration):
        version = "_iso_" + tag
        R.RULE_SETS[version] = R.RuleSet(version=version, note="isolation arm",
                                         switches=switches, calibration=calibration)
        try:
            return [S.run(sp, version) for sp in specs]
        finally:
            R.RULE_SETS.pop(version, None)

    def row(label, outs):
        d = [o.mr - b.mr for b, o in zip(base, outs)]
        dtv = [S.relative_delta(b.terminal_value, o.terminal_value)
               for b, o in zip(base, outs)]
        print("%-48s %+8.4f %+8.4f %+8.2f %6d"
              % (label, st.mean(d), min(d), st.mean(dtv) * 100,
                 sum(1 for x in d if x < -0.05)))

    print("%-48s %8s %8s %8s %6s" % ("arm", "meanDMR", "worst", "meanDTV%", "n<-.05"))
    # The two controls are the point: every isolated arm carries the 2026.10
    # knob, so a switch's OWN effect is its deviation from the knob-only row.
    row("CONTROL: all switches OFF, 2026.09 calibration", arm("c09", OFF, C09))
    row("KNOB ONLY: all switches OFF, 2026.10 knob", arm("c10", OFF, C10))
    for sw in sorted(R.SWITCHES):
        row(sw, arm(sw, {**OFF, sw: True}, C10))
    row("ALL (2026.10)", [S.run(sp, "2026.10") for sp in specs])


# ── §5.2 ──────────────────────────────────────────────────────────────────
def cmd_compare(argv: list[str]) -> None:
    import stress_harness as S
    if len(argv) < 2:
        sys.exit("compare needs two sweep files: <before> <after>")
    before, after = _load(argv[0]), _load(argv[1])
    if len(before) != len(after):
        sys.exit(f"sweeps are different sizes ({len(before)} vs {len(after)}); "
                 "they must be the same seeds in the same order to be paired")
    mismatch = sum(1 for b, a in zip(before, after)
                   if (b["09"]["label"], b["09"]["pathway"])
                   != (a["09"]["label"], a["09"]["pathway"]))
    print(f"pairs: {len(after)}  spec mismatches: {mismatch}")
    for regime, keep in (("swans OFF", False), ("swans ON", True)):
        B = [r for r in before if bool(r["09"]["swans"]) is keep]
        A = [r for r in after if bool(r["09"]["swans"]) is keep]
        if not A:
            continue
        print(f"\n===== {regime} (n={len(A)}) =====")
        print("  2026.09 arm identical:  M_R %s   TV %s   archetype %s" % (
            [r["09"]["mr"] for r in B] == [r["09"]["mr"] for r in A],
            [r["09"]["terminal_value"] for r in B] == [r["09"]["terminal_value"] for r in A],
            [r["09"]["archetype"] for r in B] == [r["09"]["archetype"] for r in A]))
        for label, rows in (("pre ", B), ("post", A)):
            d = [r["10"]["mr"] - r["09"]["mr"] for r in rows]
            tv = [S.relative_delta(r["09"]["terminal_value"], r["10"]["terminal_value"])
                  for r in rows]
            moved = sum(1 for r in rows if r["09"]["archetype"] != r["10"]["archetype"])
            print("  %s : meanDM_R %+0.4f  worst %+0.4f  n<-.05 %4d  meanDTV %+0.2f%%  "
                  "p05DTV %+0.2f%%  archetype moved %4d (%.1f%%)"
                  % (label, st.mean(d), min(d), sum(1 for x in d if x < -0.05),
                     st.mean(tv) * 100, S.describe(tv)["p05"] * 100,
                     moved, moved / len(rows) * 100))


# ── §8.1 — the affected surface ───────────────────────────────────────────
def cmd_surface(argv):
    """Which named quantities actually differ between the rule sets.

    Not "which switches exist", and not "which claims mention a switch" — every
    scalar key in the closing global state, flag bag and (aggregated) business
    units, compared across paired games. A quantity that never differs across the
    sample is one a claim can quote without a version caveat; one that does is a
    register and manuscript surface whether or not any switch is named near it.

    This exists because the first pass at re-executing the claims register found
    the affected rows by searching claim TEXT for the names of switched
    mechanics, which can only find rows that happen to use those words. The
    supply-chain transparency score, for instance, feeds the ESG-adjusted WACC
    through the nature premium, so it moves the exit multiple, terminal value,
    treasury, EBITDA and opex for teams whose claims mention none of it.
    """
    _quiet()
    n = int(argv[0]) if argv else 150
    seed = int(argv[1]) if len(argv) > 1 else 21
    import golden_matrix_harness as H
    import stress_harness as S

    def closing(spec, version):
        _trace, gs, bus = H.drive(spec=spec, rules_version=version)
        flat = {}
        for k, v in (gs or {}).items():
            if k != "active_event_flags" and (v is None or isinstance(v, (int, float, str, bool))):
                flat[f"global.{k}"] = v
        for k, v in (gs.get("active_event_flags") or {}).items():
            if v is None or isinstance(v, (int, float, str, bool)):
                flat[f"flags.{k}"] = v
        for bu in bus or []:
            for k, v in bu.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    flat[f"bu.{k}"] = flat.get(f"bu.{k}", 0) + v
        return flat

    differs, only_one, seen = Counter(), Counter(), Counter()
    for spec in S.sample_specs(n, seed):
        a, b = closing(spec, "2026.09"), closing(spec, "2026.10")
        for k in set(a) | set(b):
            seen[k] += 1
            if k not in a or k not in b:
                only_one[k] += 1
            elif a[k] != b[k]:
                differs[k] += 1

    affected = set(differs) | set(only_one)
    print(f"{n} paired games; {len(seen)} distinct scalar keys observed")
    print(f"  differ in value     : {len(differs)}")
    print(f"  present under one   : {len(only_one)}")
    print(f"  AFFECTED (union)    : {len(affected)}")
    print(f"  never differ        : {len(seen) - len(affected)}\n")
    print("AFFECTED — a claim quoting one of these needs a rule-set caveat:")
    for k, c in differs.most_common():
        print(f"   {c:4d}/{seen[k]:<4d}  {k}")
    print("\nPRESENT UNDER ONE RULE SET ONLY:")
    for k, c in only_one.most_common():
        print(f"   {c:4d}/{seen[k]:<4d}  {k}")
    if "--safe" in argv:
        print(f"\nNOT OBSERVED TO DIFFER in {n} paired games "
              "(evidence of invariance, not proof):")
        for k in sorted(set(seen) - affected):
            print(f"   {k}")


_COMMANDS = {"sweep": cmd_sweep, "summary": cmd_summary, "ceilings": cmd_ceilings,
             "isolate": cmd_isolate, "compare": cmd_compare,
             "surface": cmd_surface}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in _COMMANDS:
        sys.exit(__doc__)
    os.chdir(_BACKEND)
    _COMMANDS[sys.argv[1]](sys.argv[2:])
