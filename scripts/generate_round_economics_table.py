#!/usr/bin/env python3
"""Generate the canonical R1-R10 option-economics table in SIMULATION_CONTEXT.md.

W3 (2026-09-01). The per-round sections of SIMULATION_CONTEXT keep their
curated prose and "Key Effect" summaries, but the NUMBERS in them kept
drifting (the W3 sweep caught R9-A claiming a 75% strike chance against a
shipped 0.50 override, and R7-C's synergy boost misquoted as +0.35). This
generator emits one complete, uniform economics table for every core-game
option straight from round_configs, spliced between sentinels — the same
pattern scripts/generate_r2_mechanics_table.py established for Round 2.
tests/test_round_doc_parity.py compares the doc block against this output
AND cross-checks the hand-written per-round tables' treasury figures.

Usage:
    python3 scripts/generate_round_economics_table.py           # print
    python3 scripts/generate_round_economics_table.py --write   # splice
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
sys.path.insert(0, _BACKEND)
os.environ.setdefault("USE_MEMORY_DB", "true")

BEGIN = "<!-- BEGIN GENERATED: ROUND-ECONOMICS (scripts/generate_round_economics_table.py — do not edit by hand) -->"
END = "<!-- END GENERATED: ROUND-ECONOMICS -->"

_DELTA_COLS = [
    ("carbon_intensity_delta", "CI"),
    ("natural_capital_debt_delta", "NCD"),
    ("social_license_delta", "SLO"),
    ("governance_risk", "Gov"),
    ("reputation", "Rep"),
]


def _money(v) -> str:
    if not v:
        return "$0"
    sign = "−" if v < 0 else "+"
    a = abs(v)
    return f"{sign}${a/1e6:g}M" if a >= 1_000_000 else f"{sign}${a/1e3:g}K"


def _num(v) -> str:
    if not v:
        return ""
    return f"{v:+g}"


def build_block() -> str:
    from round_configs import get_round_config

    lines = [BEGIN, ""]
    lines.append("### Canonical Option Economics (generated from `round_configs.py`)")
    lines.append("")
    lines.append("The single source of truth for core-game option numbers. The per-round")
    lines.append("sections above summarise mechanics; when a figure here and a figure there")
    lines.append("disagree, THIS table is the one the engine runs. `Rev Δ/BU` applies per")
    lines.append("business unit; deltas are omitted when zero.")
    lines.append("")
    lines.append("| R | Opt | Title | Treasury | Rev Δ/BU | Rep | CI | NCD | SLO | Gov | Flags set |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for rnd in range(1, 11):
        cfg = get_round_config(rnd) or {}
        for key in ("option_a", "option_b", "option_c"):
            opt = (cfg.get("options") or {}).get(key)
            if not opt:
                continue
            imp = opt.get("impacts", {}) or {}
            flags = ", ".join(f"`{f}`" for f in (opt.get("flags_set") or [])) or ""
            cells = [
                str(rnd), key[-1].upper(), str(opt.get("title", opt.get("label", ""))),
                _money(imp.get("treasury", 0)), _money(imp.get("revenue_delta", 0)),
                _num(imp.get("reputation", 0)),
                _num(imp.get("carbon_intensity_delta", 0)),
                _num(imp.get("natural_capital_debt_delta", 0)),
                _num(imp.get("social_license_delta", imp.get("social_license", 0))),
                _num(imp.get("governance_risk", 0)),
                flags,
            ]
            lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def write() -> None:
    path = os.path.join(_ROOT, "SIMULATION_CONTEXT.md")
    with open(path, encoding="utf-8") as f:
        doc = f.read()
    block = build_block()
    if BEGIN in doc:
        pre = doc[:doc.index(BEGIN)]
        post = doc[doc.index(END) + len(END):]
        doc = pre + block + post
    else:
        anchor = "## 5. Decision Pillars (Multi-Toggle Paradigm)"
        assert anchor in doc, "splice anchor missing"
        doc = doc.replace(anchor, block + "\n\n---\n\n" + anchor)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(doc)
    print(f"spliced {len(block.splitlines())} lines into SIMULATION_CONTEXT.md")


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
    else:
        print(build_block())
