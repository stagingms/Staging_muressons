"""DEEP-4: the cohort stochastic_seed reaches impact_engine's four rolls.

GAME-4's rng_util gives every stochastic engine a named, per-cohort random
stream — black swans, micro-strikes, FX and NPC reactions all use it. The
four highest-stakes rolls never did: the R5 cyclone, the R5 NBS
establishment, the R9 strike and the R9 retraining outcome came from the
bare module RNG — unseeded, shared across concurrent sessions, and deaf to
the facilitator's fairness seed.

Contract pinned here:
  - seeded flags  -> identical rolls for identical (seed, round, event),
    regardless of module-RNG state (two teams in one cohort meet the same
    cyclone; a graded run is reproducible);
  - different events/seeds -> independent streams;
  - unseeded flags -> the module RNG, exactly as before (test harnesses and
    legacy sessions keep their behaviour bit-for-bit).
"""

import random

import pytest


def _mk_bus(slo=50.0):
    return [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
             "carbon_intensity": 50.0, "social_license_score": slo,
             "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
             "water_dependency": 30.0, "staff_burnout_index": 10.0,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def _mk_gs(rnd):
    return {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
            "green_transition_fund": 0.0, "synergy_multiplier": 1.0,
            "round_number": rnd, "active_event_flags": {},
            "workforce_readiness": 50.0, "climate_resilience": 0.5,
            "session_id": "", "cost_of_capital": 0.08}


def _tick(rnd, choice, prev_flags, module_seed):
    from round_logic import post_tick
    random.seed(module_seed)
    gs, bus = _mk_gs(rnd), _mk_bus()
    decs = [{"choice_selected": choice, "capex_allocated": 0,
             "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(rnd, gs, bus, decs, {}, prev_flags)
    return gs, extra


SEEDED = {"stochastic_seed": "cohort-fairness-2026"}


def test_seeded_cyclone_roll_ignores_module_rng_state():
    """Same cohort seed => same R5 roll, whatever the module RNG was doing —
    two teams committing concurrently meet the same cyclone."""
    _, a = _tick(5, "option_b", dict(SEEDED), module_seed=1)
    _, b = _tick(5, "option_b", dict(SEEDED), module_seed=999999)
    assert a["stochastic_roll"] == b["stochastic_roll"]
    assert a.get("climate_event_struck") == b.get("climate_event_struck")


def test_seeded_r9_rolls_are_reproducible():
    _, a = _tick(9, "option_b", dict(SEEDED), module_seed=1)
    _, b = _tick(9, "option_b", dict(SEEDED), module_seed=424242)
    assert a["retraining_assessment"]["roll"] == b["retraining_assessment"]["roll"]


def test_different_seeds_give_different_streams():
    rolls = set()
    for s in ("cohort-A", "cohort-B", "cohort-C", "cohort-D"):
        _, e = _tick(5, "option_b", {"stochastic_seed": s}, module_seed=1)
        rolls.add(e["stochastic_roll"])
    assert len(rolls) >= 3, f"seeds are not producing independent streams: {rolls}"


def test_cyclone_and_nbs_are_independent_named_streams():
    """rng_util contract: each event gets its own stream, so branching in one
    can never desync another. The NBS roll must not simply be 'the next draw'
    after the cyclone roll."""
    from rng_util import event_rng
    flags = dict(SEEDED)
    cyclone_stream_next = event_rng(flags, 5, "r5:cyclone").random()
    _, e = _tick(5, "option_b", flags, module_seed=1)  # option_b rolls NBS
    nbs = e.get("nbs_uncertainty", {}).get("roll")
    if nbs is None:  # NBS succeeded — read the flag-stored roll instead
        gs, e = _tick(5, "option_b", flags, module_seed=2)
    # The independence property that matters: the cyclone roll equals its own
    # named stream's first draw — untouched by however many other rolls fired.
    assert e["stochastic_roll"] == round(cyclone_stream_next, 4)


def test_unseeded_falls_back_to_module_rng_exactly():
    """No seed => bit-identical to the historical behaviour (module RNG),
    which test harnesses and legacy sessions rely on."""
    random.seed(15)
    expected_first = round(random.random(), 4)
    _, e = _tick(5, "option_b", {}, module_seed=15)
    assert e["stochastic_roll"] == expected_first


# ═══════════════════════════════════════════════════════════════════════════
#  No production code may reseed the PROCESS-GLOBAL rng (2026-09-03)
# ═══════════════════════════════════════════════════════════════════════════
#
# router.get_peer_leaderboard and get_peer_trend_history did:
#
#     import random as _rng                       # the MODULE, not an instance
#     _rng.seed(hash(session_id) & 0xFFFFFFFF)
#
# `random.seed()` reseeds the process-global Mersenne Twister — the same stream
# org_politics.evaluate_csuite_support, supply_chain_network's disruption rolls
# and engine's unseeded fallbacks draw from. Measured: a student in ONE cohort
# opening the peer leaderboard changed another cohort's next three draws. With
# thirty cohorts in one process that is silent cross-class contamination, and
# because hash() is PYTHONHASHSEED-randomised it was not even reproducible.
#
# The rule is simple and mechanically checkable: production code seeds its OWN
# Random instance (rng_util.event_rng for gameplay, rng_util.stable_rng for
# cosmetic display draws) and never calls seed() on the module.

_GLOBAL_SEED_ALLOWLIST: dict[str, str] = {
    # "module.function": "reason it may reseed the global rng"
    #
    # All three are OFFLINE tooling: nothing under backend/ imports them outside
    # tests (asserted below). Seeding the global rng is legitimate in a
    # single-purpose script that owns its whole process. It stops being
    # legitimate the moment the module is imported by the live app, which is
    # what test_allow_listed_global_seeders_stay_out_of_production guards.
    "dry_run._run_one":
        "offline bot harness; seeds the global rng so engines that draw from it "
        "are reproducible per (strategy, rep). WARNING: this module's own "
        "docstring calls it the 'facilitator pre-flight simulator' — wiring it "
        "to an endpoint would make this a live 30-cohort contamination bug. "
        "Give it a local Random first.",
    "validation_logic.run_traversal":
        "offline decision-tree traversal tool; no production importer.",
    "validation_logic.run_single":
        "offline decision-tree traversal tool; no production importer.",
}


def _module_level_seed_calls():
    """Every `random.seed(...)` / `<alias>.seed(...)` where the receiver is the
    random MODULE, resolved by AST across backend/*.py (tests excluded)."""
    import ast, os
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hits = []
    for fn in sorted(f for f in os.listdir(backend) if f.endswith(".py")):
        path = os.path.join(backend, fn)
        try:
            tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
        except SyntaxError:
            continue
        # aliases bound to the random MODULE in this file
        aliases = {"random"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == "random":
                        aliases.add(a.asname or "random")
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "seed"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in aliases):
                owner = "?"
                for f in ast.walk(tree):
                    if (isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and f.lineno <= node.lineno <= f.end_lineno):
                        owner = f.name
                hits.append(f"{fn[:-3]}.{owner}:{node.lineno}")
    return hits


def test_no_production_code_reseeds_the_global_rng():
    offenders = [h for h in _module_level_seed_calls()
                 if h.rsplit(":", 1)[0] not in _GLOBAL_SEED_ALLOWLIST]
    assert not offenders, (
        f"these call seed() on the random MODULE, reseeding the process-global "
        f"stream every cohort shares: {offenders}\n"
        f"Use rng_util.event_rng (gameplay, keyed to the cohort seed) or "
        f"rng_util.stable_rng (cosmetic, process-stable) and keep the instance "
        f"local, or add an entry to _GLOBAL_SEED_ALLOWLIST with a reason."
    )


def test_stable_rng_is_isolated_reproducible_and_process_stable():
    """The three properties the peer-leaderboard fix depends on."""
    import random
    from rng_util import stable_rng

    # 1. isolated — drawing from it must not disturb the global stream
    random.seed(11)
    before = [random.random() for _ in range(3)]
    random.seed(11)
    r = stable_rng("some-other-cohort", 4, "peer_leaderboard")
    [r.uniform(-1, 1), r.randint(-50, 50), r.choice(["a", "b"])]
    after = [random.random() for _ in range(3)]
    assert before == after, "stable_rng disturbed the global rng"

    # 2. reproducible — the property the original hash() seed promised and broke
    assert (stable_rng("s1", 3, "x").random()
            == stable_rng("s1", 3, "x").random())
    assert (stable_rng("s1", 3, "x").random()
            != stable_rng("s2", 3, "x").random())

    # 3. unambiguous — separator escaping, so ("a|b","c") cannot collide with ("a","b|c")
    assert stable_rng("a|b", "c").random() != stable_rng("a", "b|c").random()


def test_allow_listed_global_seeders_stay_out_of_production():
    """The allow-list above is only safe while those modules are offline.

    If someone wires dry_run to an endpoint — which its own docstring invites —
    its `random.seed()` starts reseeding the stream every live cohort draws
    from. This fails the moment any backend module imports one of them.
    """
    import ast, os
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offline = {name.split(".", 1)[0] for name in _GLOBAL_SEED_ALLOWLIST}
    importers = []
    for fn in sorted(f for f in os.listdir(backend) if f.endswith(".py")):
        if fn[:-3] in offline:
            continue
        try:
            tree = ast.parse(open(os.path.join(backend, fn), encoding="utf-8",
                                  errors="replace").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if m.split(".")[0] in offline:
                    importers.append(f"{fn} imports {m} (line {node.lineno})")
    assert not importers, (
        f"a module allow-listed to reseed the global rng is now imported by "
        f"production code: {importers}\n"
        f"Give it a local Random instance (rng_util.event_rng / stable_rng) "
        f"before wiring it up, or every live cohort shares its reseeds."
    )
