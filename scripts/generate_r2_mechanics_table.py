#!/usr/bin/env python3
"""Generate the Round 2 mechanics tables in SIMULATION_CONTEXT.md.

The R2 audit (2026-08) found the hand-maintained Round 2 documentation stating
a 90% threshold, a $2M treasury bonus and a flat Option-A premium that did not
exist in the engine (F-4 and friends). This generator builds the tables from
the same sources the tests pin — round_configs for the option economics and
tests/test_r2_materiality_audit.TIER_EXPECTATIONS for the nine-way tier grid —
so the doc can only drift if the tests drift with it (and a test compares the
doc block against this generator's output).

Usage:
    python3 scripts/generate_r2_mechanics_table.py           # print the block
    python3 scripts/generate_r2_mechanics_table.py --write   # splice into SIMULATION_CONTEXT.md
"""

import importlib.util
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
sys.path.insert(0, _BACKEND)

BEGIN = "<!-- BEGIN GENERATED: R2-MECHANICS (scripts/generate_r2_mechanics_table.py — do not edit by hand) -->"
END = "<!-- END GENERATED: R2-MECHANICS -->"

# Pinned elsewhere: +0.10/+0.05/0 in terminal_valuation.calculate_mr and
# round_logic (test_mr_ceilings_unchanged); the Green Bond modulation in
# round_logic._post_r3_scope3 (§5.2 decision: symmetric half-discount).
TIER_MR = {"materiality_aligned": "+0.10", "materiality_partial": "+0.05",
           "materiality_ignored": "0"}
TIER_R3 = {"materiality_aligned": "−$500K Green Bond discount",
           "materiality_partial": "−$250K Green Bond discount",
           "materiality_ignored": "+$1M Green Bond risk premium"}


def _tier_expectations():
    path = os.path.join(_BACKEND, "tests", "test_r2_materiality_audit.py")
    spec = importlib.util.spec_from_file_location("_r2_audit_fixtures", path)
    mod = importlib.util.module_from_spec(spec)
    # The test module imports app machinery; keep that import side-effect-free
    # for doc generation by reusing the already-importable backend modules.
    os.environ.setdefault("USE_MEMORY_DB", "true")
    spec.loader.exec_module(mod)
    return mod.TIER_EXPECTATIONS


def _money(v):
    if not v:
        return "$0"
    sign = "−" if v < 0 else "+"
    a = abs(v)
    return f"{sign}${a/1e6:g}M" if a >= 1_000_000 else f"{sign}${a/1e3:g}K"


def build_block() -> str:
    from round_configs import get_round_options
    opts = get_round_options(2)

    lines = [BEGIN, ""]
    lines.append("**Options** (economics from `round_configs.py`; `revenue_delta` is per business unit):")
    lines.append("")
    lines.append("| Option | Title | Treasury | Revenue Δ/BU | Reputation | Governance posture |")
    lines.append("|---|---|---|---|---|---|")
    posture = {
        "option_a": "Board-committee oversight — eligible for `materiality_aligned`",
        "option_b": "Strategic exceptions — eligible for `materiality_partial`",
        "option_c": "ESRS 1 §1.51 breach — always `materiality_ignored`; 40% fund clawback",
    }
    for key in ("option_a", "option_b", "option_c"):
        o = opts[key]
        imp = o.get("impacts", {})
        lines.append(
            f"| {o.get('label', key[-1].upper())} | {o.get('title', '')} | "
            f"{_money(imp.get('treasury', 0))} | {_money(imp.get('revenue_delta', 0))} | "
            f"{imp.get('reputation', 0):+d} | {posture[key]} |"
        )

    lines.append("")
    lines.append("**Governance premium — tiered** (accuracy is full-quadrant matrix accuracy; "
                 "exactly one flag is written, by `round_logic._post_r2_materiality`):")
    lines.append("")
    lines.append("| Matrix accuracy | Option | Flag | M_R at R10 | R3 Green Bond effect |")
    lines.append("|---|---|---|---|---|")
    band_label = {"lt80": "< 80%", "eq80": "= 80%", "gt80": "> 80%"}
    for choice, band, flag in _tier_expectations():
        lines.append(
            f"| {band_label[band]} | {choice.replace('option_', '').upper()} | "
            f"`{flag}` | {TIER_MR[flag]} | {TIER_R3[flag]} |"
        )
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main():
    block = build_block()
    if "--write" not in sys.argv:
        print(block)
        return
    doc_path = os.path.join(_ROOT, "SIMULATION_CONTEXT.md")
    with open(doc_path, encoding="utf-8") as f:
        doc = f.read()
    start, end = doc.find(BEGIN), doc.find(END)
    if start == -1 or end == -1:
        raise SystemExit("markers not found in SIMULATION_CONTEXT.md — add them first")
    doc = doc[:start] + block + doc[end + len(END):]
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"wrote generated block into {doc_path}")


if __name__ == "__main__":
    main()
