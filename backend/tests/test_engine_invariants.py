"""Engine-wide invariants from the full-course impact audit (2026-08-31).

Test 1 here is the acceptance criterion for C-1, C-2, C-5 and C-6: every
impact key an option config promises is applied by some code path — either
generically by _apply_common_impacts or by the round's own post-tick handler,
with handler ownership resolved by AST (never by line number).

Before the fixes this fails on exactly four keys:
  social_license_delta        unapplied in R1, R2, R3, R7, R10   (C-1)
  natural_capital_debt_delta  unapplied in R2, R4, R10           (C-2)
  treasury                    unapplied in R2                    (C-5)
  divest_all                  unapplied in R10                   (C-6)
"""

import ast
import os

import pytest

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HANDLER_ROUND = {
    "_post_r1_foundations": 1, "_post_r2_materiality": 2, "_post_r3_scope3": 3,
    "_post_r4_contagion": 4, "_post_r5_climate": 5, "_post_r6_ai_bias": 6,
    "_post_r7_circularity": 7, "_post_r8_blue_stress": 8,
    "_post_r9_just_transition": 9, "_post_r10_grand_finale": 10,
}

# Keys an option may declare that are deliberately NOT consumed by any
# handler.  Every entry needs a reason; an empty dict is the healthy state.
ALLOWLISTED_UNAPPLIED: dict[str, str] = {}


def _handler_sources() -> dict[str, str]:
    """Source text of every post-tick handler plus the generic applier,
    resolved by AST function boundaries (a function's own lines only)."""
    src_of: dict[str, str] = {}
    for fn in ("round_logic.py", "impact_engine.py"):
        path = os.path.join(_BACKEND_DIR, fn)
        txt = open(path, encoding="utf-8", errors="replace").read()
        lines = txt.split("\n")
        for node in ast.walk(ast.parse(txt)):
            if isinstance(node, ast.FunctionDef) and (
                    node.name in HANDLER_ROUND or node.name == "_apply_common_impacts"):
                src_of[node.name] = "\n".join(lines[node.lineno - 1:node.end_lineno])
    return src_of


def _impact_key_usage() -> dict[str, set[int]]:
    from round_configs import get_round_options
    use: dict[str, set[int]] = {}
    for r in range(1, 11):
        for k, v in (get_round_options(r) or {}).items():
            if not isinstance(v, dict):
                continue
            for ik, iv in (v.get("impacts") or {}).items():
                if iv:
                    use.setdefault(ik, set()).add(r)
    return use


def _referenced(key: str, source: str) -> bool:
    return f'"{key}"' in source or f"'{key}'" in source


_SRC = _handler_sources()
_GENERIC_SRC = _SRC.get("_apply_common_impacts", "")
_USE = _impact_key_usage()
_HANDLER_BY_ROUND = {r: n for n, r in HANDLER_ROUND.items()}


@pytest.mark.parametrize("key", sorted(_USE))
def test_every_impact_key_is_applied_in_every_round_that_uses_it(key):
    if key in ALLOWLISTED_UNAPPLIED:
        pytest.skip(f"allow-listed as deliberately unapplied: {ALLOWLISTED_UNAPPLIED[key]}")
    if _referenced(key, _GENERIC_SRC):
        return  # applied generically for all rounds
    unapplied = [
        r for r in sorted(_USE[key])
        if not _referenced(key, _SRC.get(_HANDLER_BY_ROUND[r], ""))
    ]
    assert not unapplied, (
        f"impact key '{key}' is configured in rounds {sorted(_USE[key])} but "
        f"neither _apply_common_impacts nor the handlers of rounds {unapplied} "
        f"ever reference it — those options silently do nothing for this key"
    )


def test_all_ten_handlers_exist():
    missing = [n for n in HANDLER_ROUND if n not in _SRC]
    assert not missing, f"handlers not found by AST walk: {missing}"
