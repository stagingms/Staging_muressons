"""SIMULATION_CONTEXT's core-round numbers cannot drift from round_configs.

W3 completion (2026-09-01). Two layers:

  1. The generated Canonical Option Economics block must match the generator's
     current output (same contract as the R2 mechanics block) — a config
     change fails this test until the block is regenerated with
     scripts/generate_round_economics_table.py --write.

  2. The hand-written per-round tables in §4 keep their curated prose, but
     every treasury figure a row states is parsed and checked against the
     option's config treasury. That is the column that drifts most
     dangerously (it is the number teams budget around).
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("USE_MEMORY_DB", "true")

ROOT = BACKEND.parent
DOC = ROOT / "SIMULATION_CONTEXT.md"


def _generator():
    gen_path = ROOT / "scripts" / "generate_round_economics_table.py"
    spec = importlib.util.spec_from_file_location("_gen_round_econ", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canonical_economics_block_matches_generator():
    mod = _generator()
    block = mod.build_block()
    doc = DOC.read_text(encoding="utf-8")
    assert mod.BEGIN in doc, "generated block missing from SIMULATION_CONTEXT.md"
    assert block in doc, (
        "SIMULATION_CONTEXT.md Canonical Option Economics block is stale — "
        "regenerate with scripts/generate_round_economics_table.py --write"
    )


def _money_to_float(tok: str) -> float:
    sign = -1.0 if tok.lstrip().startswith(("−", "-")) else 1.0
    m = re.search(r"\$([\d.]+)\s*([MK]?)", tok)
    assert m, tok
    v = float(m.group(1)) * {"M": 1e6, "K": 1e3, "": 1.0}[m.group(2)]
    return sign * v


def test_handwritten_round_tables_state_config_treasury():
    """Parse §4's per-round tables: any row '| A | Title | ±$xM | ...' must
    state the option's config treasury. Rows whose third cell is not a bare
    money figure are skipped (they carry prose, which layer 1 backstops)."""
    from round_configs import get_round_config

    doc = DOC.read_text(encoding="utf-8")
    gen = _generator()
    body = doc[: doc.index(gen.BEGIN)]  # hand-written sections only

    current_round = None
    failures = []
    checked = 0
    for line in body.splitlines():
        h = re.match(r"### Round (\d+) ", line)
        if h:
            current_round = int(h.group(1))
            continue
        if current_round is None:
            continue
        row = re.match(r"\|\s*([ABC])\s*\|([^|]*)\|\s*([^|]*)\|", line)
        if not row:
            continue
        cell = row.group(3).strip()
        if not re.fullmatch(r"[−+-]?\$[\d.]+[MK]?", cell):
            continue  # prose or composite cell — not a bare money figure
        cfg = get_round_config(current_round) or {}
        opt = (cfg.get("options") or {}).get(f"option_{row.group(1).lower()}")
        if not opt:
            continue
        expected = float((opt.get("impacts") or {}).get("treasury", 0) or 0)
        stated = _money_to_float(cell)
        checked += 1
        if abs(stated - expected) > 0.5:
            failures.append(
                f"R{current_round} option {row.group(1)}: doc states {cell}, "
                f"config treasury is {expected:,.0f}"
            )
    assert checked >= 15, f"parser only matched {checked} rows — doc format changed?"
    assert not failures, "hand-written treasury figures drifted:\n  " + "\n  ".join(failures)


# ── W4.2: the model card exists, is cited, and states the shipped values ───

def test_model_card_exists_and_is_cited():
    card = ROOT / "MODEL_CARD.md"
    assert card.exists(), "MODEL_CARD.md missing (roadmap W4.2 definition of done)"
    assert "MODEL_CARD.md" in DOC.read_text(encoding="utf-8"), \
        "SIMULATION_CONTEXT no longer cites the model card"


def test_model_card_states_current_config_values():
    """The card's shipped-value column must track config — same discipline as
    the glossary. Checked coarsely: the current value's rendering must appear."""
    from config import (
        FINANCIAL_SHADOW_CARBON_PRICE, FINANCIAL_DEFAULT_LOAN_RATE,
        FINANCIAL_FREE_CSF_PCT, NCD_INTEREST_COEFFICIENT,
        TV_EXIT_MULTIPLE_FLOOR, TV_EXIT_MULTIPLE_CEILING,
        CYCLONE_PROB_BASE, PHYSICAL_VAR_DAMAGE_BASE,
        GREENWASH_INVESTMENT_THRESHOLD,
    )
    card = (ROOT / "MODEL_CARD.md").read_text(encoding="utf-8")
    for needle in (
        f"${FINANCIAL_SHADOW_CARBON_PRICE:g}/t",
        f"{FINANCIAL_DEFAULT_LOAN_RATE * 100:g}%",
        f"{FINANCIAL_FREE_CSF_PCT * 100:g}% of treasury",
        f"{TV_EXIT_MULTIPLE_FLOOR:g}–{TV_EXIT_MULTIPLE_CEILING:g}×",
        f"{CYCLONE_PROB_BASE * 100:g}% probability",
        f"${PHYSICAL_VAR_DAMAGE_BASE / 1e6:g}M base damage",
        f"{GREENWASH_INVESTMENT_THRESHOLD * 100:g}% avg investment",
    ):
        assert needle in card, f"MODEL_CARD.md no longer states the shipped value: {needle!r}"
    assert f"+1bp per NCD unit" in card and NCD_INTEREST_COEFFICIENT == 0.0001, \
        "NCD coefficient changed — update MODEL_CARD.md §2.3 and this test"
