"""The typed boundary over the flag namespace (Phase 1 of the flag remediation).

WHAT THIS IS FOR, STATED NARROWLY
    active_event_flags is NOT a flag namespace. Measured across the backend:
    298 read-by-name sites over 136 distinct keys, of which only 47 sites over
    24 keys read a DECLARED FLAG. The other 251 read scalar state
    (regenerative_multiple, caroic, workforce_readiness), session configuration
    (difficulty_tier, region_id, stochastic_seed) or structured sub-objects
    (ceo_interview_scores, esg_adjusted_wacc). This package covers the flag
    subset ONLY and deliberately leaves the rest alone.

WHAT IT DOES NOT DO
    It fixes no bug. Every production caller of calculate_mr already builds a
    collected flag dict — F-15/WP-14 did that work, and mr_flags_from /
    mr_input_from_state are its result. What is missing is enforcement: nothing
    in the type system stops a caller passing the RAW dict instead, and one
    caller already does (tests/test_financial_golden_trace.py, which is why its
    terminal M_R is 1.25 where production computes 1.23).

    So this package makes the existing, already-correct convention impossible to
    violate. Behaviour change belongs in Phase 4, behind a rules version.

THE TWO CONSTRUCTORS ARE THE POINT
    FlagSet.from_state(gs)   the correct reading — expands the rN_flags lists
    FlagSet.legacy_raw(d)    top-level truthy keys only, i.e. today's raw-dict
                             semantics, preserved bit-for-bit

    legacy_raw is not a convenience. It is a MARKER: every call site is a
    known-wrong reader, greppable, countable, and removable one at a time in
    Phase 4 with the golden matrix showing exactly what each one moves. It
    converts an invisible defect class into a finite TODO list.

PHASE 2 — THE REGISTRY SAYS WHAT IT CAN SHOW
    registry.py now carries effect and evidence, and four statuses rather than
    two. The first cut derived LIVE from "absent from flag_taxonomy.py", which
    inherits a textual sweep's blindness: eleven of the sixteen round flags
    Appendix B verified dead were labelled LIVE. They are now DEAD_DEFECT with
    the evidence, the seventeen demonstrably live round flags carry their
    effect, and the hundred whose reachability has not been established are
    UNVERIFIED rather than assumed working. Phase 3's runtime probe exists to
    drive that count down.
"""
from .flagset import FlagSet, UnknownFlag                      # noqa: F401
from .registry import (                                        # noqa: F401
    REGISTRY, FlagSpec, LIVE, DEAD_DEFECT, INERT_BY_DESIGN, UNVERIFIED,
    get, by_status, live, dead, inert, unverified,
)

__all__ = ["FlagSet", "UnknownFlag", "REGISTRY", "FlagSpec",
           "LIVE", "DEAD_DEFECT", "INERT_BY_DESIGN", "UNVERIFIED",
           "get", "by_status", "live", "dead", "inert", "unverified"]
