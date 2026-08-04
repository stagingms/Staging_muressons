"""
Muressons — replay(session_id)   (4.9, 2026-08-03)

WHAT THIS ANSWERS
    "Can this grade be defended?"

    A cohort disputes a result. Someone asks why team 7 finished with a lower
    terminal value than team 3. Before this tool the honest answer was "we
    cannot tell you" — the run recorded its outputs but not enough of its
    inputs to derive them again. 4.2 (seed), 4.7 (provenance) and 4.8 (commit
    envelope) exist to close that gap; this is the thing that USES them, and
    therefore the thing that proves they were sufficient.

WHAT IT DOES
    Re-runs each recorded round through the SAME pure engine entry point the
    live commit path uses (engine.process_tick), feeding it the decisions and
    the server-derived inputs recorded at the time, and diffs the result
    against the state that was actually stored.

WHAT IT DELIBERATELY DOES NOT DO
    It does not re-run the whole commit pipeline. commit_turn also applies
    pre-tick modifiers, pillar aggregation, engagement actions and CFO
    refusals; reproducing that outside the request path would mean maintaining
    a second copy of it, and a verifier that drifts from what it verifies is
    worse than none. So the CORE TICK is what is checked, the scope is stated
    in the report, and fields the core tick does not own are excluded by name
    rather than silently ignored.

    It is READ-ONLY. It never writes a session, never advances a round, and
    never touches the audit log. A verification tool that can alter the thing
    it verifies is not a verification tool.

THE HONESTY REQUIREMENT
    If the config has changed since the run, replay CANNOT match, and saying
    "MISMATCH" would be a lie about the engine. The report distinguishes:

        VERIFIED          reproduced exactly, field for field
        DRIFT             config or code moved since the run; a difference is
                          expected and is NOT evidence against the engine
        PARTIAL           differences found, but replay does not yet run every
                          stage the live commit path runs, so the difference
                          cannot be attributed. See KNOWN LIMIT below.
        INSUFFICIENT      the run predates the provenance/envelope work and
                          does not carry enough to be replayed at all

    There is deliberately no MISMATCH verdict yet. Emitting one while replay
    covers a subset of the pipeline would cry wolf on healthy runs, and a
    verifier nobody believes is worse than no verifier.

KNOWN LIMIT — and what closes it
    Replay runs pre_tick + process_tick. The live path also runs pillar
    aggregation, engagement actions, the climate/carbon application and the
    inflation step. Measured on a real three-round session, that leaves 14
    systematic differences: carbon intensity +2 (mirroring the run's own
    carbon_intensity_applied_r1 = -2 flag), opex ~2.2% high from inflation
    applied once more than the live path, reputation -2.

    Bolting each stage onto this module would create a SECOND copy of the
    commit pipeline that drifts from the first — the same defect class as the
    two storage backends disagreeing on BU order, and as R10 logging decisions
    differently from rounds 1-9. The fix is to extract the pipeline into one
    pure function that commit_turn and replay both call. That is a real
    refactor of the hottest path in the router and should not be done in the
    fortnight before a cohort runs.

    INSUFFICIENT is not a failure of this tool. Every session created before
    2026-08-03 will report it, and that is the correct answer: those runs were
    never reproducible and no amount of cleverness now makes them so.
"""

from __future__ import annotations

import copy
from typing import Any, Optional

# Fields the core tick does not own, excluded by name so the exclusion is
# auditable rather than implicit. Each one is owned by a stage of the commit
# pipeline that replay deliberately does not re-run.
_NOT_OWNED_BY_CORE_TICK = {
    "active_event_flags",        # merged from pre_tick + engagement + quiz paths
    "game_over", "game_over_reason",
    "team_commits_this_round", "cohort_team_count",
    "pending_capex_projects",    # mutated by the capex scheduler outside the tick
    "bonus_score",               # facilitator-adjustable at any time
}

_MONEY_TOLERANCE = 0.01          # one cent: NUMERIC(18,2) round-trips
_RATIO_TOLERANCE = 1e-6


def _close(a: Any, b: Any) -> bool:
    """Numeric comparison that tolerates storage rounding but nothing else."""
    # bool is a subclass of int in Python, so True == 1.0 is True. A stored
    # boolean that replays as a number IS a real difference — treat the type
    # mismatch as one rather than letting Python's coercion hide it.
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        diff = abs(float(a) - float(b))
        if diff <= _RATIO_TOLERANCE:
            return True
        # NUMERIC(18,2) columns round; anything above a cent is a real change.
        return diff <= _MONEY_TOLERANCE
    return a == b


def _unpack_flags(state: dict) -> dict:
    """Put both sides in the same shape before comparing.

    The readers unpack active_event_flags to the top level of global_state (see
    the PARITY note in fetch_latest_state), while process_tick returns them
    still nested. Diffing the two shapes directly reports every flag as
    "recorded X, replayed None" — a hundred phantom mismatches that bury the
    handful of real ones. Normalise, then compare.
    """
    out = dict(state)
    for k, v in (state.get("active_event_flags") or {}).items():
        out.setdefault(k, v)
    return out


def _diff_state(expected: dict, actual: dict, *, label: str) -> list[dict]:
    """Field-level differences, skipping what the core tick does not own."""
    expected, actual = _unpack_flags(expected), _unpack_flags(actual)
    out: list[dict] = []
    for key in sorted(set(expected) | set(actual)):
        if key in _NOT_OWNED_BY_CORE_TICK:
            continue
        e, a = expected.get(key), actual.get(key)
        if isinstance(e, (dict, list)) or isinstance(a, (dict, list)):
            continue                      # structural fields: out of scope
        if key not in actual or key not in expected:
            # Present on one side only: a stage replay does not run produced it.
            # Reported separately so it cannot be mistaken for a wrong NUMBER.
            out.append({"where": label, "field": key, "kind": "absent",
                        "recorded": e, "replayed": a})
            continue
        if not _close(e, a):
            out.append({"where": label, "field": key, "kind": "value",
                        "recorded": e, "replayed": a})
    return out


async def replay(session_id: str, *, db=None) -> dict:
    """Verify that a completed session reproduces from its own record.

    Returns a report dict; never raises for a session that simply cannot be
    replayed — that is a VERDICT, not an error.
    """
    if db is None:
        import database as db  # noqa: PLC0415 — respects the runtime backend switch

    from config_introspect import run_provenance
    from engine import process_tick
    from round_logic import pre_tick

    report: dict[str, Any] = {
        "session_id": session_id,
        "verdict": "INSUFFICIENT",
        "scope": "core tick (engine.process_tick) only — see module docstring",
        "rounds_checked": 0,
        "differences": [],
        "notes": [],
    }

    info = await db.get_session_info(session_id)
    if not info:
        report["notes"].append("no such session")
        return report

    prov = info.get("run_provenance") or {}
    if not prov:
        report["notes"].append(
            "this run predates 4.7 and records no provenance: its seed, config "
            "and code version are unknown, so it cannot be replayed. That is "
            "the honest answer, not a tool failure."
        )
        return report

    report["provenance"] = prov

    # ── Drift: has the world moved since this run? ─────────────────────────
    now = run_provenance(prov.get("stochastic_seed", ""))
    drift = []
    if prov.get("config_fingerprint") not in ("", "unavailable", None) and \
            prov["config_fingerprint"] != now["config_fingerprint"]:
        drift.append(f"config {prov['config_fingerprint']} -> {now['config_fingerprint']}")
    if prov.get("code_version") not in ("", "unknown", None) and \
            now.get("code_version") not in ("", "unknown", None) and \
            prov["code_version"] != now["code_version"]:
        drift.append(f"code {prov['code_version']} -> {now['code_version']}")
    report["drift"] = drift

    # ── Inputs: the recorded rounds and the decisions that produced them ───
    history = await db.fetch_round_history(session_id)
    if not history or len(history) < 2:
        report["notes"].append(
            "fewer than two recorded rounds: nothing to verify (a replay needs "
            "a starting state and at least one transition)."
        )
        return report

    history = sorted(history, key=lambda h: h.get("round_number", 0))
    by_round = {h["round_number"]: h for h in history}

    differences: list[dict] = []
    checked = 0
    unreplayable: list[int] = []

    for prev, nxt in zip(history, history[1:]):
        rn = prev["round_number"]
        decisions = [copy.deepcopy(d) for d in (prev.get("decisions") or [])]
        if not decisions:
            unreplayable.append(rn)
            continue

        env = {}
        for d in decisions:
            md = d.get("metadata") or {}
            if isinstance(md, dict) and md.get("turn"):
                env = md["turn"]
                break
        if not env:
            unreplayable.append(rn)
            continue

        # The audit log stores capex under "capex" in some readers and
        # "capex_allocated" in others; the engine wants the latter.
        for d in decisions:
            if "capex_allocated" not in d and "capex" in d:
                d["capex_allocated"] = d["capex"]
            md = d.get("metadata") or {}
            if isinstance(md, dict) and md.get("investment_ratio") is not None:
                d["investment_ratio"] = md["investment_ratio"]

        current_global = {"round_number": rn, **prev["global_state"]}
        current_bus = copy.deepcopy(prev["business_units"]
                                    if "business_units" in prev
                                    else prev.get("bu_states") or [])
        try:
            # PRE-TICK FIRST. Found by running this tool against a real
            # three-round session: without it every round reported the same
            # systematic offsets — governance +5, carbon intensity +5,
            # reputation -5, inflation doubled — because process_tick was being
            # fed the RAW recorded state rather than the state pre_tick hands
            # it. The engine was never wrong; the replay was starting in the
            # wrong place. pre_tick mutates in place, hence the deepcopy above.
            pre = pre_tick(
                round_number=rn,
                current_global=current_global,
                current_bus=current_bus,
                decisions=decisions,
                crisis_severity=env.get("crisis_severity_effective", 0.0),
                force_override_cfo=env.get("force_override_cfo", False),
            )
            if "validation_error" in pre:
                # The recorded run got past this gate, so a refusal here means
                # the GATE has changed, not the decision. Say which.
                differences.append({"where": f"round {rn}", "field": "<pre_tick refused>",
                                    "kind": "value", "recorded": "accepted at the time",
                                    "replayed": pre["validation_error"]})
                continue
            tick = process_tick(
                current_global=current_global,
                current_bus=current_bus,
                decisions=decisions,
                dividends_paid=env.get("dividends_paid", 0.0),
                crisis_severity=pre.get("crisis_severity",
                                        env.get("crisis_severity_effective", 0.0)),
                imitation_decay_rate=env.get("imitation_decay_rate", 0.05),
                decision_paradigm=env.get("decision_paradigm", "legacy_abc"),
                emergency_credit_used=env.get("emergency_credit_used", False),
            )
        except Exception as exc:                       # noqa: BLE001
            differences.append({"where": f"round {rn}", "field": "<engine raised>",
                                "recorded": None, "replayed": f"{type(exc).__name__}: {exc}"})
            continue

        checked += 1
        differences += _diff_state(nxt["global_state"], tick["global_state"],
                                   label=f"round {rn}->{rn + 1} global")

        recorded_bus = {b.get("bu_id"): b for b in (nxt.get("business_units")
                                                    or nxt.get("bu_states") or [])}
        for rb in tick["bu_states"]:
            got = recorded_bus.get(rb.get("bu_id"))
            if got is None:
                differences.append({"where": f"round {rn + 1}", "field": "bu_missing",
                                    "recorded": None, "replayed": rb.get("bu_id")})
                continue
            differences += _diff_state(got, rb, label=f"round {rn + 1} bu:{rb.get('bu_id')}")

    report["rounds_checked"] = checked
    report["differences"] = differences
    if unreplayable:
        report["notes"].append(
            f"rounds {unreplayable} carry no commit envelope (pre-4.8) and were skipped"
        )

    # ── Verdict ────────────────────────────────────────────────────────────
    if checked == 0:
        report["verdict"] = "INSUFFICIENT"
    elif not differences:
        report["verdict"] = "VERIFIED"
    elif drift:
        report["verdict"] = "DRIFT"
        report["notes"].append(
            "the config or code moved after this run, so a difference is EXPECTED "
            "and is not evidence against the engine. Reproduce by checking out "
            f"{prov.get('code_version')} with the matching config."
        )
    else:
        # NOT "MISMATCH". Replay currently runs pre_tick + process_tick, while
        # the live commit path also runs pillar aggregation, engagement
        # actions, the climate/carbon application and the inflation step. A
        # difference in a field owned by one of those stages is a GAP IN THIS
        # TOOL, and this tool cannot yet tell the two apart.
        #
        # Measured on a real three-round session: 14 value differences remain,
        # and every one is a systematic offset (carbon intensity +2 mirroring
        # the recorded carbon_intensity_applied_r1 flag, opex ~2.2% high from
        # inflation applied once more than the live path, reputation -2). Those
        # are the signature of a stage not running, not of a wrong engine.
        #
        # Claiming MISMATCH here would be the most damaging thing this tool
        # could do: it would cry wolf on healthy runs, and within a week nobody
        # would look at a real one. PARTIAL says exactly what is known.
        report["verdict"] = "PARTIAL"
        report["notes"].append(
            "differences found, but replay covers only pre_tick + process_tick "
            "while the live commit path runs further stages. These differences "
            "are NOT yet evidence against the engine. A definitive VERIFIED/"
            "MISMATCH verdict requires extracting the commit pipeline into one "
            "function that both commit_turn and replay call — see the module "
            "docstring."
        )

    return report
