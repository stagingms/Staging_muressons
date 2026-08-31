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
import re

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
ALLOWLISTED_UNAPPLIED: dict[str, str] = {
    # C-6, design ruling 2026-08-31: divest_all stays in config but inert —
    # its intended mechanics were never specified and must not be inferred
    # from the name. Its live siblings (synergy_wipe, the -12 SLO, the +8
    # NCD, treasury, revenue_delta) carry the Divest ending. Remove this
    # entry the moment a design lands and a consumer is written.
    "divest_all": "pending design ruling — deliberately unconsumed",
}


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


# ═════════════════════════════════════════════════════════════════
#  Test 2 — no impact is applied twice (and none is applied zero times)
#  Direct post_tick execution against synthetic state: the resulting delta
#  must equal the configured value EXACTLY — not double, not zero.
# ═════════════════════════════════════════════════════════════════

def _mk_bus():
    return [{"bu_id": b, "revenue_base": 10_000_000.0, "opex_base": 7_000_000.0,
             "carbon_intensity": 50.0, "social_license_score": 50.0,
             "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
             "water_dependency": 30.0, "staff_burnout_index": 10.0,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def _mk_gs(rnd):
    return {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
            "green_transition_fund": 0.0, "synergy_multiplier": 1.0,
            "round_number": rnd, "active_event_flags": {},
            "workforce_readiness": 50.0, "climate_resilience": 0.5,
            "session_id": "", "cost_of_capital": 0.08}


def _run_post_tick(rnd, choice, prev_flags=None):
    import random
    from round_logic import post_tick
    random.seed(20260831)
    gs, bus = _mk_gs(rnd), _mk_bus()
    decs = [{"choice_selected": choice, "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(rnd, gs, bus, decs, {}, prev_flags or {})
    return gs, bus, extra

# Rounds whose treasury moves by more than the option cost by design
# (R5: stochastic cyclone damage; R9: strike engine on Option A).
_TREASURY_NOISY_ROUNDS = {5, 9}
# Rounds that DEFER their NCD delta into pending_capex_projects.
_NCD_DEFERRED_ROUNDS = {5, 8}


def _all_round_options():
    from round_configs import get_round_options
    out = []
    for r in range(1, 11):
        for k, v in (get_round_options(r) or {}).items():
            if isinstance(v, dict):
                out.append((r, k, v.get("impacts") or {}))
    return out


@pytest.mark.parametrize("rnd,choice,imp", [
    pytest.param(r, c, i, id=f"r{r}-{c}") for r, c, i in _all_round_options()])
def test_configured_delta_is_applied_exactly_once(rnd, choice, imp):
    gs, bus, extra = _run_post_tick(rnd, choice)

    # Social licence: exact single application on every BU (start 50, all
    # shipped deltas are within the 0..100 clamp from there). R8's designed
    # severe-drop mechanic additionally hits its configured target BUs.
    slo_cfg = imp.get("social_license_delta", imp.get("social_license", 0)) or 0
    severe_targets, severe_amt = set(), 0
    if imp.get("social_license_severe_drop") and extra.get("social_license_severe_drop_applied"):
        severe_targets = set(imp.get("social_license_drop_targets", []))
        severe_amt = imp.get("social_license_drop_amount", -25)
    for bu in bus:
        expected = 50.0 + slo_cfg + (severe_amt if bu["bu_id"] in severe_targets else 0)
        expected = max(0.0, min(100.0, expected))
        assert bu["social_license_score"] == pytest.approx(expected), (
            f"R{rnd} {choice} {bu['bu_id']}: SLO moved "
            f"{bu['social_license_score'] - 50.0}, expected {expected - 50.0}")

    # Natural capital debt: exact single application (start 50 avoids the
    # 0-floor), except where the round defers it into a pending project.
    ncd_cfg = imp.get("natural_capital_debt_delta", 0) or 0
    if rnd in _NCD_DEFERRED_ROUNDS:
        for bu in bus:
            assert bu["natural_capital_debt"] == pytest.approx(50.0), (
                f"R{rnd} {choice}: deferred NCD must not also apply immediately")
        if ncd_cfg:
            assert any(p.get("type") == "ncd_drop" and p.get("amount") == ncd_cfg
                       for p in gs.get("pending_capex_projects", []))
    else:
        for bu in bus:
            assert bu["natural_capital_debt"] == pytest.approx(50.0 + ncd_cfg), (
                f"R{rnd} {choice}: NCD moved {bu['natural_capital_debt'] - 50.0}, "
                f"config says {ncd_cfg}")

    # Treasury: exact single application where the round has no designed
    # extra treasury mechanics on top of the option cost.
    if rnd not in _TREASURY_NOISY_ROUNDS:
        tre_cfg = imp.get("treasury", 0) or 0
        assert gs["corporate_treasury"] == pytest.approx(100_000_000.0 + tre_cfg), (
            f"R{rnd} {choice}: treasury moved "
            f"{gs['corporate_treasury'] - 100_000_000.0}, config says {tre_cfg}")


# ═════════════════════════════════════════════════════════════════
#  Test 3 — one spelling per concept across the whole config surface
# ═════════════════════════════════════════════════════════════════

_CONFIG_FILES = ("round_configs.py", "healthcare_configs.py",
                 "pillar_configs.py", "ending_pathways.py")


@pytest.mark.parametrize("retired,canonical", [
    ('"social_license":', "social_license_delta"),
    ('"reputation_delta":', "reputation"),
])
def test_retired_impact_spellings_are_gone_from_configs(retired, canonical):
    offenders = []
    for fn in _CONFIG_FILES:
        path = os.path.join(_BACKEND_DIR, fn)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8", errors="replace").read()
        if retired in src:
            offenders.append(fn)
    assert not offenders, (
        f"config files still use the retired spelling {retired} — "
        f"use {canonical!r}: {offenders}")


# ═════════════════════════════════════════════════════════════════
#  Test 4 — every flag read via `in all_flags` has a writer
# ═════════════════════════════════════════════════════════════════

# Flags written by data-driven or dynamic writers a textual scan can't see.
# The 2026-08 audit confirmed each of these live end-to-end; extend ONLY
# with a verified writer path.
DYNAMIC_WRITERS = {
    "materiality_aligned": "F-1 single-writer loop in _post_r2_materiality (flags[f] = f == tier)",
    "materiality_partial": "F-1 single-writer loop in _post_r2_materiality (flags[f] = f == tier)",
    "materiality_ignored": "F-1 single-writer loop in _post_r2_materiality (flags[f] = f == tier)",
    "planet_expendable": "shadow_board_audit REJECTION_FLAGS data-driven writer (end-to-end tested)",
    "shareholder_alienated": "shadow_board_audit REJECTION_FLAGS data-driven writer (end-to-end tested)",
    "governance_fragility": "shadow_board_audit REJECTION_FLAGS data-driven writer (end-to-end tested)",
}

_READER_FILES = ("round_logic.py", "impact_engine.py", "ending_pathways.py",
                 "engine.py", "router.py", "admin_router.py")


def _flag_reads():
    reads = {}
    for fn in _READER_FILES:
        src = open(os.path.join(_BACKEND_DIR, fn), encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'["\'](\w+)["\'] (?:in|not in) all_flags', src):
            reads.setdefault(m.group(1), set()).add(fn)
    return reads


def _writer_corpus():
    import glob as _glob
    files = [p for p in _glob.glob(os.path.join(_BACKEND_DIR, "*.py"))
             + _glob.glob(os.path.join(_BACKEND_DIR, "side_tracks", "*", "*.py"))
             if "test" not in os.path.basename(p)]
    return "".join(open(p, encoding="utf-8", errors="replace").read() for p in files)


def test_every_read_flag_has_a_writer():
    reads = _flag_reads()
    corpus = _writer_corpus()
    dead = []
    for name in sorted(reads):
        if name in DYNAMIC_WRITERS:
            continue
        written = (
            re.search(r'flags_set[^\]]*["\']' + re.escape(name) + r'["\']', corpus, re.S)
            or re.search(r'\[["\']' + re.escape(name) + r'["\']\]\s*=', corpus)
            or re.search(r'["\']' + re.escape(name) + r'["\']\s*:\s*True', corpus)
        )
        if not written:
            dead.append((name, sorted(reads[name])))
    assert not dead, (
        "flags read via `in all_flags` that no code path or config ever "
        f"writes (B-1/B-2 class): {dead}")


# ═════════════════════════════════════════════════════════════════
#  Test 5 — every special_rules key is read, or allow-listed with a reason
# ═════════════════════════════════════════════════════════════════

DESCRIPTIVE_SPECIAL_RULES: dict[str, str] = {
    # empty — B-4 wired all four previously-inert switches into the code
    # that implements them. Add entries ONLY for keys that are genuinely
    # documentation, with the reason.
}


def test_every_special_rules_key_is_read():
    import glob as _glob
    from round_configs import get_round_config
    keys = set()
    for r in range(1, 11):
        keys |= set((get_round_config(r) or {}).get("special_rules", {}))
    files = [p for p in _glob.glob(os.path.join(_BACKEND_DIR, "*.py"))
             + _glob.glob(os.path.join(_BACKEND_DIR, "side_tracks", "*", "*.py"))
             if "test" not in os.path.basename(p)]
    src = "".join(open(p, encoding="utf-8", errors="replace").read() for p in files)
    dead = [k for k in sorted(keys)
            if k not in DESCRIPTIVE_SPECIAL_RULES
            and src.count(f'"{k}"') + src.count(f"'{k}'") <= 1]
    assert not dead, (
        f"special_rules keys that look like switches but are never read: {dead}")


# ═════════════════════════════════════════════════════════════════
#  Test 6 — no flag is both config-declared and boolean-written
#  (generalises the Round 2 dual-form guard)
# ═════════════════════════════════════════════════════════════════

DUAL_FORM_ALLOWLIST = {
    # B-5: declared in R6 Option A's pillar flags_set AND boolean-written at
    # the same condition in _post_r6_ai_bias. The two writers agree today;
    # this entry documents the dual form so any NEW one fails the test.
    "ai_monetised": "R6 Option A: config flags_set and boolean write fire under the same condition",
    # Found by this test (2026-08-31): the supply-chain side track declares
    # supply_chain_fragile in a crisis option's flags_set AND boolean-writes
    # it from the data bridge when final visibility < 50 — two writers with
    # DIFFERENT conditions, so a team can end up carrying both
    # supply_chain_resilient and supply_chain_fragile. No core code reads the
    # flag today, which is why this is an allow-list entry and not a fix;
    # flagged for the side-track design owner.
    "supply_chain_fragile": "disagreeing dual writers in the supply-chain side track — pending design ruling",
}


def test_no_flag_is_both_config_declared_and_boolean_written():
    corpus = _writer_corpus()
    declared = set(re.findall(
        r'flags_set["\']?\s*[:=]\s*\[([^\]]*)\]', corpus))
    declared_names = set()
    for group in declared:
        declared_names |= set(re.findall(r'["\'](\w+)["\']', group))
    bool_written = set(re.findall(
        r'active_event_flags[^\n]*\[["\'](\w+)["\']\]\s*=\s*(?:True|False|bool\()', corpus))
    bool_written |= set(re.findall(
        r'\bflags\[["\'](\w+)["\']\]\s*=\s*(?:True|False|bool\()', corpus))
    dual = (declared_names & bool_written) - set(DUAL_FORM_ALLOWLIST)
    assert not dual, (
        f"flags in BOTH a config flags_set and a boolean write — unretirable "
        f"via _collect_all_flags union (F-2 class): {sorted(dual)}")


# ═════════════════════════════════════════════════════════════════
#  Test 7 — SLO reachability: the Instability Discount is steerable
#  A team taking the most licence-positive option every round must finish
#  above the 75 average; the most licence-negative path must finish below.
#  This is the property C-1 destroyed (the max path forfeited +23 points).
# ═════════════════════════════════════════════════════════════════

def _play_full_game(mode):
    import random
    import sys as _sys
    _sys.path.insert(0, os.path.join(_BACKEND_DIR, "tests"))
    from test_r2_materiality_audit import (_start, _commit, _submit, _bus_latest,
                                           Q1_IDS, Q2_IDS, Q3_IDS)
    from round_configs import get_round_options
    import database_memory as dbm

    def slo_of(opt):
        i = opt.get("impacts") or {}
        return i.get("social_license_delta", i.get("social_license", 0)) or 0

    def picker(rnd):
        opts = {k: v for k, v in get_round_options(rnd).items() if isinstance(v, dict)}
        f = max if mode == "max" else min
        return f(opts, key=lambda k: slo_of(opts[k]))

    random.seed(20260831 if mode == "max" else 20260832)
    sid, bus = _start()
    for rnd in range(1, 11):
        if rnd == 2:
            assert _submit(sid, Q1_IDS, Q2_IDS, Q3_IDS).status_code == 200
        # capex 3M keeps the avg investment ratio above the 15% greenwash
        # threshold — otherwise the greenwash scandal (-7.5/round) dominates
        # SLO and the test measures the wrong mechanic.
        _commit(sid, bus, rnd, picker(rnd), capex=3_000_000)
    flags = dict(dbm._global_states[sid][-1].get("active_event_flags") or {})
    bl = _bus_latest(sid)
    avg = sum(b["social_license_score"] for b in bl) / len(bl)
    return avg, flags


def test_instability_discount_is_steerable():
    avg_max, flags_max = _play_full_game("max")
    assert avg_max > 75, (
        f"licence-maximising team finished at avg SLO {avg_max:.1f} — the "
        f"75 threshold is unreachable, the Instability Discount is not steerable")
    assert not flags_max.get("instability_discount_applied"), (
        "licence-maximising team must not take the -0.40 Instability Discount")

    avg_min, flags_min = _play_full_game("min")
    assert avg_min < 75, (
        f"licence-minimising team finished at avg SLO {avg_min:.1f} — "
        f"negative-licence consequences are not landing")
    assert flags_min.get("instability_discount_applied"), (
        "licence-minimising team must take the -0.40 Instability Discount")
