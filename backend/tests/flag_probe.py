"""Muressons — the flag read probe (Phase 3 of the dead-flag remediation).

WHY A PROBE AND NOT A SWEEP
    tests/test_flag_sweep.py asks whether a flag's NAME appears in the source. It
    is the second generation of that question — the test it replaced was "green
    while blind" for three reasons — and it is green while blind for a fourth,
    because a name is not a value. systemic_risk_engine.py:71 contains the literal
    "supply_chain_disruption_risk": -10.0 on a non-comment line in backend
    non-test code, so the sweep marks the flag READ. The value has never once
    flowed. There is an unbounded supply of ways for a name to appear without a
    value arriving, so the invariant has to move from "is the name referenced?" to
    "does a value flow from writer to reader?". That is a runtime question.

WHY THE PROBE IS NOT WIRED TO flags.FlagSet
    The remediation plan sketched the probe as a hook on FlagSet.has(). Phase 1
    deliberately did NOT migrate any consumer onto FlagSet, because migrating a
    raw read to the flattened reader turns a dead mechanic ON, and a behaviour
    change belongs in the reviewed phase, not the scaffolding phase. Nothing in
    the engine constructs a FlagSet, so a probe on FlagSet would observe exactly
    nothing and every LIVE assertion would fail. The exit condition for this phase
    is that the test fails for the flags Appendix B names AND FOR NOTHING ELSE, so
    the probe has to observe the code as it stands. It instruments the containers
    the current consumers actually read.

TWO CHANNELS, BECAUSE ONE IS NOT ENOUGH
    1. THE READ PROBE (observe) — recording containers on the four boundaries the
       flag namespace crosses:

         active_event_flags   installed by golden_matrix_harness.MatrixHooks at
                              the four points the driver hands the namespace on.
                              Catches every inline `flags.get(F)` / `F in flags`,
                              which is where shapes A and C live.
         ctx.events           installed by replacing engine.TickContext with a
                              factory that wraps the events bag. Catches shape B,
                              the _SDG_FLAG_BONUSES registry reading a dict that
                              is empty by construction.
         collect_all_flags    the returned set is a recording set, so `F in
                              all_flags` — how every CORRECT consumer reads — is
                              attributed.
         calculate_mr(flags)  the terminal boundary, coerced at the call.

       It records reads, truthy reads, and the file:line of each, so a dead flag
       comes back diagnosed: READ_NEVER_TRUE means a consumer exists and the
       storage format hides it (REVIVE); NOT_READ means no consumer exists at all
       (RETIRE). Appendix B's triage was done by hand; this derives it.

    2. THE DIFFERENTIAL (differential) — the verdict. Re-run a path with one flag
       scrubbed out of existence and diff the whole trace. Nothing differs => the
       flag moved nothing, whatever the reads looked like.

       The differential exists because the read probe has a blind spot it cannot
       close from the inside. Consumers that iterate the namespace in bulk —
       stakeholder_sentiment builds `{f.lower() for f in flags_set}` and
       intersects rule sets against it — never perform a keyed read, so no
       container can attribute the flag. Appendix B calls carbon_deferred,
       deny_and_deflect and quiet_patch LIVE ON SENTIMENT ALONE. A keyed-read-only
       probe would report all three dead, which is precisely the false alarm the
       exit condition forbids. The differential is shape-agnostic and catches
       them. The bulk census (Observation.bulk) enumerates the blind spot rather
       than leaving it implied.

WHY SCRUBBING IS SOUND
    rng_util.event_seed hashes only flags["stochastic_seed"], never the dict, and
    each event draws from its own named stream — so removing a flag cannot shift
    another mechanic's rolls. Verified: the matrix makes zero bare global draws.

    The scrub is airtight rather than staged. A hook that filtered the namespace
    only at the driver's handover points would leave a window inside post_tick,
    between _apply_option_flags writing r{N}_flags and the next handover, in which
    a same-round consumer would still see the flag — and a missed window produces
    a FALSE DEAD, the one error class this phase cannot tolerate. So the scrub is
    a property of the container: a ScrubbingDict lies about the flag on every read
    including .items(), so collect_all_flags cannot find it either, and it filters
    the flag out of any list value under a key collect_all_flags would expand.
    Filtered list values are returned as copies; that is safe because the only
    in-place list mutation anywhere in the tick is on custom_black_swans and
    engine_failures, neither of which is a flag list.

OBSERVATION MUST NOT PERTURB
    A probe that changes the run cannot describe it. The recording containers only
    record; test_flag_reachability asserts that a probed matrix reproduces the
    golden fixtures byte for byte.
"""

from __future__ import annotations

import copy
import os
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import golden_matrix_harness as H          # noqa: E402
import engine                              # noqa: E402
import flag_utils                          # noqa: E402
import round_logic                         # noqa: E402
import terminal_valuation                  # noqa: E402
from flags.registry import REGISTRY        # noqa: E402

# Only registered names are recorded. The namespace carries ~130 event keys that
# are state, not flags (capex_loan_balance, macro_rate_environment …); recording
# every one of them would bury the signal and cost frame introspection on reads
# that answer no question this module asks.
FLAG_NAMES = frozenset(REGISTRY)

CH_AEF = "active_event_flags"
CH_EVENTS = "events"
CH_COLLECTED = "collect_all_flags"
CH_MR = "calculate_mr.flags"

# Reads made BY the namespace machinery itself, not by a consumer of it.
# flag_utils.collect_all_flags carries a hard-coded fallback list at :49-54 that
# tests four names as top-level keys; that is the reader doing its job, and
# counting it as a consumer read would make electronics_blindspot look consumed.
_READER_FILES = frozenset({"flag_utils.py", "flagset.py"})
# The probe's and the harness's own plumbing. Anything attributed here is the
# scaffolding copying dicts around, never a finding.
_PLUMBING_FILES = frozenset({"flag_probe.py", "golden_matrix_harness.py", "copy.py"})

# Verdicts
TRUE_READ = "TRUE_READ"                 # a keyed read returned truthy
READ_NEVER_TRUE = "READ_NEVER_TRUE"     # read, never truthy, and it WAS written
NOT_READ = "NOT_READ"                   # no consumer performed a keyed read
NOT_WRITTEN = "NOT_WRITTEN"             # the matrix never raises it — no verdict


@dataclass(frozen=True)
class Site:
    channel: str
    file: str
    line: int
    kind: str                            # get | in | sub

    def __str__(self) -> str:
        return f"{self.file}:{self.line} ({self.kind}, via {self.channel})"


@dataclass(frozen=True)
class BulkSite:
    channel: str
    file: str
    line: int
    op: str                              # items | keys | iter | values

    def __str__(self) -> str:
        return f"{self.file}:{self.line} .{self.op}() on {self.channel}"


@dataclass
class FlagReads:
    reads: int = 0
    true_reads: int = 0
    sites: Counter = field(default_factory=Counter)
    true_sites: Counter = field(default_factory=Counter)


def _caller_site(depth: int) -> tuple[str, int]:
    f = sys._getframe(depth)
    return os.path.basename(f.f_code.co_filename), f.f_lineno


class _Sink:
    """Where the recording containers write. A module-level instance would break
    the moment two runs overlapped, and copy.deepcopy of a container must not
    deep-copy the log, so the containers close over a sink instance instead of
    holding one as an attribute."""

    def __init__(self) -> None:
        self.keyed: dict[str, FlagReads] = defaultdict(FlagReads)
        self.internal: Counter = Counter()
        self.bulk: Counter = Counter()

    def record(self, channel: str, kind: str, flag: str, hit: bool, depth: int) -> None:
        file, line = _caller_site(depth + 1)
        if file in _PLUMBING_FILES:
            return
        site = Site(channel, file, line, kind)
        if file in _READER_FILES:
            self.internal[site] += 1
            return
        rec = self.keyed[flag]
        rec.reads += 1
        rec.sites[site] += 1
        if hit:
            rec.true_reads += 1
            rec.true_sites[site] += 1

    def record_bulk(self, channel: str, op: str, depth: int) -> None:
        file, line = _caller_site(depth + 1)
        if file in _PLUMBING_FILES:
            return
        self.bulk[BulkSite(channel, file, line, op)] += 1


def _recording_dict_class(sink: _Sink, channel: str):
    """A dict that records keyed reads of registered flag names.

    __iter__ is deliberately NOT overridden. CPython's dict constructor and
    dict.update take a fast C path only while tp_iter is dict's own; overriding it
    forces them onto the keys()/__getitem__ protocol, which would attribute every
    `dict(flags)` copy in the engine as a keyed read of every flag it holds. The
    bulk census loses `for k in flags` as a result and keeps .items()/.keys(),
    which is what the real bulk consumers use (flag_utils.py:27, engine.py:4791).
    """

    class _RecordingDict(dict):
        __slots__ = ()

        def get(self, key, default=None):
            value = dict.get(self, key, default)
            if key in FLAG_NAMES:
                sink.record(channel, "get", key, bool(value), 2)
            return value

        def __contains__(self, key):
            present = dict.__contains__(self, key)
            if key in FLAG_NAMES:
                sink.record(channel, "in", key, bool(present), 2)
            return present

        def __getitem__(self, key):
            value = dict.__getitem__(self, key)
            if key in FLAG_NAMES:
                sink.record(channel, "sub", key, bool(value), 2)
            return value

        def items(self):
            sink.record_bulk(channel, "items", 2)
            return dict.items(self)

        def keys(self):
            sink.record_bulk(channel, "keys", 2)
            return dict.keys(self)

        def values(self):
            sink.record_bulk(channel, "values", 2)
            return dict.values(self)

    return _RecordingDict


def _recording_set_class(sink: _Sink):
    class _RecordingSet(set):
        __slots__ = ()

        def __contains__(self, key):
            present = set.__contains__(self, key)
            if key in FLAG_NAMES:
                sink.record(CH_COLLECTED, "in", key, bool(present), 2)
            return present

        def __iter__(self):
            sink.record_bulk(CH_COLLECTED, "iter", 2)
            return set.__iter__(self)

    return _RecordingSet


def _scrubbing_dict_class(victim: str):
    """A dict from which one flag has never existed.

    Hides `victim` as a top-level key on every read path INCLUDING items()/keys()/
    values(), so flag_utils.collect_all_flags cannot see it, and strips it from any
    list value under a key collect_all_flags would expand (`"flag" in key.lower()`).
    Writes are untouched: the engine may set the key, and the next read still will
    not find it. That is what makes the scrub airtight inside post_tick rather than
    only at the driver's handover points.
    """

    def _clean(key, value):
        if isinstance(value, list) and isinstance(key, str) and "flag" in key.lower():
            if any(v == victim for v in value):
                return [v for v in value if v != victim]
        return value

    class _ScrubbingDict(dict):
        __slots__ = ()

        def get(self, key, default=None):
            if key == victim:
                return default
            return _clean(key, dict.get(self, key, default))

        def __contains__(self, key):
            return False if key == victim else dict.__contains__(self, key)

        def __getitem__(self, key):
            if key == victim:
                raise KeyError(key)
            return _clean(key, dict.__getitem__(self, key))

        def __len__(self):
            return dict.__len__(self) - (1 if dict.__contains__(self, victim) else 0)

        def items(self):
            return [(k, _clean(k, v)) for k, v in dict.items(self) if k != victim]

        def keys(self):
            return [k for k in dict.keys(self) if k != victim]

        def values(self):
            return [_clean(k, v) for k, v in dict.items(self) if k != victim]

        def __iter__(self):
            return iter(self.keys())

    return _ScrubbingDict


# ── hooks ───────────────────────────────────────────────────────────────────

class _RecordingHooks(H.MatrixHooks):
    def __init__(self, sink: _Sink):
        self._aef = _recording_dict_class(sink, CH_AEF)
        self._ev = _recording_dict_class(sink, CH_EVENTS)

    def on_flags(self, flags, stage, rnd):
        return flags if isinstance(flags, self._aef) else self._aef(flags)

    def on_events(self, events, rnd):
        return events if isinstance(events, self._ev) else self._ev(events)


class _ScrubHooks(H.MatrixHooks):
    def __init__(self, victim: str):
        self._cls = _scrubbing_dict_class(victim)

    def on_flags(self, flags, stage, rnd):
        return flags if isinstance(flags, self._cls) else self._cls(flags)

    def on_events(self, events, rnd):
        return events if isinstance(events, self._cls) else self._cls(events)


# ── patching ────────────────────────────────────────────────────────────────

@contextmanager
def _recording_patches(sink: _Sink):
    """Wrap the three read boundaries the driver's hooks cannot reach.

    collect_all_flags is patched in two places: flag_utils (which every
    function-local `from flag_utils import collect_all_flags` re-resolves at call
    time — engine.py:3786, engine.py:3950, black_swan_registry.py:627,
    terminal_valuation.py:712) and round_logic._collect_all_flags, the one
    module-level alias, whose binding is independent.
    """
    rec_set = _recording_set_class(sink)
    rec_mr = _recording_dict_class(sink, CH_MR)
    rec_ev = _recording_dict_class(sink, CH_EVENTS)

    orig_caf = flag_utils.collect_all_flags
    orig_rl_caf = round_logic._collect_all_flags
    orig_mr = terminal_valuation.calculate_mr
    orig_tc = engine.TickContext

    def caf(flags_dict):
        return rec_set(orig_caf(flags_dict))

    def calculate_mr(flags, *args, **kwargs):
        if isinstance(flags, dict) and not isinstance(flags, rec_mr):
            flags = rec_mr(flags)
        return orig_mr(flags, *args, **kwargs)

    def tick_context(*args, **kwargs):
        ctx = orig_tc(*args, **kwargs)
        if isinstance(ctx.events, dict) and not isinstance(ctx.events, rec_ev):
            ctx.events = rec_ev(ctx.events)
        return ctx

    flag_utils.collect_all_flags = caf
    round_logic._collect_all_flags = caf
    terminal_valuation.calculate_mr = calculate_mr
    engine.TickContext = tick_context
    try:
        yield
    finally:
        flag_utils.collect_all_flags = orig_caf
        round_logic._collect_all_flags = orig_rl_caf
        terminal_valuation.calculate_mr = orig_mr
        engine.TickContext = orig_tc


@contextmanager
def _scrub_patches(victim: str):
    """Remove one flag from the OPTION CONFIG as well as from the namespace.

    round_logic._apply_option_flags re-fetches the options itself
    (round_logic.py:3765) rather than using whatever the caller attached, so
    filtering the harness's copy alone would leave the write intact. Patching the
    fetch covers both that write and the router's flags_set attach, and leaves
    every other field of the option — cost, impacts, description — untouched:
    the counterfactual is "this option no longer sets this flag", not "this option
    no longer exists".
    """
    orig_fetch = round_logic._fetch_options_for_industry

    def fetch(round_number, bus, decision_paradigm=None):
        opts = orig_fetch(round_number, bus, decision_paradigm=decision_paradigm)
        if not isinstance(opts, dict):
            return opts
        out = {}
        for key, opt in opts.items():
            flags = (opt or {}).get("flags_set") if isinstance(opt, dict) else None
            if isinstance(flags, list) and victim in flags:
                opt = dict(opt)
                opt["flags_set"] = [f for f in flags if f != victim]
            out[key] = opt
        return out

    round_logic._fetch_options_for_industry = fetch
    _h_orig = H._fetch_options
    H._fetch_options = fetch
    try:
        yield
    finally:
        round_logic._fetch_options_for_industry = orig_fetch
        H._fetch_options = _h_orig


# ── the observation ─────────────────────────────────────────────────────────

@dataclass
class Observation:
    keyed: dict
    internal: Counter
    bulk: Counter
    writes: dict                      # flag -> {path_name: sorted rounds}
    traces: dict                      # path_name -> trace

    # -- queries --------------------------------------------------------
    def written(self, flag: str) -> bool:
        return bool(self.writes.get(flag))

    def reads(self, flag: str) -> int:
        return self.keyed[flag].reads if flag in self.keyed else 0

    def true_reads(self, flag: str) -> int:
        return self.keyed[flag].true_reads if flag in self.keyed else 0

    def sites(self, flag: str) -> list[Site]:
        return sorted(self.keyed[flag].sites, key=str) if flag in self.keyed else []

    def true_site_list(self, flag: str) -> list[Site]:
        return sorted(self.keyed[flag].true_sites, key=str) if flag in self.keyed else []

    def verdict(self, flag: str) -> str:
        if self.true_reads(flag) > 0:
            return TRUE_READ
        if not self.written(flag):
            return NOT_WRITTEN
        return READ_NEVER_TRUE if self.reads(flag) > 0 else NOT_READ

    def explain(self, flag: str) -> str:
        v = self.verdict(flag)
        where = self.writes.get(flag) or {}
        head = (f"{flag}: {v} — {self.reads(flag)} keyed read(s), "
                f"{self.true_reads(flag)} truthy; written on "
                f"{', '.join(f'{p} R{r}' for p, rs in sorted(where.items()) for r in rs[:1]) or 'no path'}")
        lines = [head]
        for site in self.sites(flag):
            n = self.keyed[flag].sites[site]
            t = self.keyed[flag].true_sites.get(site, 0)
            lines.append(f"    {site}  x{n}, truthy {t}")
        return "\n".join(lines)


def observe(path_names=None, rules_version=None) -> Observation:
    """Run the matrix under instrumentation and report what each flag's readers
    actually saw, under one rule set."""
    names = list(path_names or H.PATHS)
    version = rules_version or H.DEFAULT_RULES_VERSION
    sink = _Sink()
    writes: dict = defaultdict(lambda: defaultdict(list))
    traces: dict = {}
    hooks = _RecordingHooks(sink)
    with _recording_patches(sink):
        for name in names:
            trace, gs, bus = H.drive(name, hooks=hooks, rules_version=version)
            H.terminal_snapshot(gs, bus, production_path=True)
            traces[name] = trace
            for rec in trace:
                for flag in rec.get("flags", ()):
                    if flag in FLAG_NAMES:
                        writes[flag][name].append(rec["round"])
    return Observation(
        keyed=dict(sink.keyed),
        internal=sink.internal,
        bulk=sink.bulk,
        writes={f: {p: sorted(rs) for p, rs in d.items()} for f, d in writes.items()},
        traces=traces,
    )


# ── the differential ────────────────────────────────────────────────────────

@dataclass
class Difference:
    flag: str
    path: str
    moved: bool
    first_diff: str = ""


def _baseline_traces(path_names, rules_version=None) -> dict:
    version = rules_version or H.DEFAULT_RULES_VERSION
    return {name: H.run_path(name, rules_version=version) for name in path_names}


def _without(trace: list, victim: str) -> list:
    """The baseline trace as it would read if the flag's own NAME were absent.

    The snapshot records the collected flag set, so a scrubbed run always differs
    from its baseline by at least the scrubbed flag itself. That difference is the
    scrub working, not the flag doing anything, and comparing raw traces would
    report every flag in the game LIVE — measured, all 32. Removing the victim
    name and nothing else leaves the real question: did any OTHER recorded
    quantity move? Derived flags stay in, because a flag that causes
    electronics_blindspot_triggered has done something.
    """
    out = []
    for rec in trace:
        if "flags" in rec and victim in rec["flags"]:
            rec = dict(rec)
            rec["flags"] = [f for f in rec["flags"] if f != victim]
        out.append(rec)
    return out


def differential(flags, path_names=None, baselines=None,
                 _hooks_override=None, rules_version=None) -> dict:
    """For each flag, re-run every path that raises it with the flag scrubbed out
    of existence, and report whether the trace moved.

    Only the paths that actually raise the flag are re-run — every round flag is
    raised by exactly one (round, option), so this is one or two runs per flag
    rather than the full matrix.

    The scrub has TWO mechanisms and needs both. The config patch stops the option
    layer writing the flag into r{N}_flags; the ScrubbingDict hides it from every
    read. Neither alone is sufficient: ai_monetised is ALSO written as a top-level
    boolean at round_logic.py:2430, keyed off the CHOICE rather than the flag, so
    the config patch cannot remove it — and a same-round consumer would see a flag
    the container scrub had not yet been installed to hide. `_hooks_override` is a
    test seam that runs the scrub with the container mechanism replaced, so
    tests/test_flag_reachability can prove the guard below fires instead of
    reporting a false DEAD. It has no production use.
    """
    names = list(path_names or H.PATHS)
    version = rules_version or H.DEFAULT_RULES_VERSION
    base = baselines if baselines is not None else _baseline_traces(names, version)
    raises: dict = defaultdict(list)
    for name in names:
        for rec in base[name]:
            for flag in rec.get("flags", ()):
                if flag in flags and name not in raises[flag]:
                    raises[flag].append(name)

    out: dict = {}
    for flag in flags:
        results = []
        for name in raises.get(flag, []):
            hooks = _hooks_override() if _hooks_override else _ScrubHooks(flag)
            with _scrub_patches(flag):
                scrubbed = H.run_path(name, hooks=hooks, rules_version=version)
            # The scrub is only meaningful if it worked. A flag still visible in
            # the scrubbed trace would make "nothing moved" meaningless.
            still_there = [rec["round"] for rec in scrubbed
                           if flag in rec.get("flags", ())]
            if still_there:
                raise AssertionError(
                    f"scrub of '{flag}' on path '{name}' failed: the flag is still "
                    f"visible at rounds {still_there}. The differential verdict "
                    f"would be meaningless, so this is raised rather than reported."
                )
            reference = _without(base[name], flag)
            moved = scrubbed != reference
            results.append(Difference(
                flag=flag, path=name, moved=moved,
                first_diff="" if not moved else H.first_diff(reference, scrubbed),
            ))
        out[flag] = results
    return out


def moved_anywhere(results: list) -> bool:
    return any(r.moved for r in results)
