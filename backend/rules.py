"""Muressons — versioned rule sets.

WHY THIS EXISTS
    Cohorts are in flight and past cohorts have published results. A change that
    silently alters scoring invalidates both: a team that scored 1.23 last term
    cannot be told they now score 1.31 because a mechanic that never ran was
    switched on. The standard answer applies — version the rules, pin each
    session to a version, and express every behavioural change as a NAMED SWITCH
    rather than as an edit to the calculation.

    So `2026.09` is not "the old rules". It is the semantics every session played
    under up to and including commit 0ad1246, and it is the default for every
    session record that does not say otherwise — which is all of them, since
    nothing wrote a version before this module existed. A 2026.09 session must
    replay bit-identically after any change here, and that is a test
    (tests/test_rules.py, tests/test_option_matrix_golden.py) rather than a hope.

WHAT A SWITCH IS FOR
    Each switch turns on ONE mechanic that was designed, written into the engine,
    and never ran because a reader and a writer disagreed about the shape of the
    flag namespace (see docs/verification/appendixB_flags.md §B.0 and the
    dead-flag remediation plan §1.2). The switch does not implement the mechanic;
    the mechanic is already there. The switch decides whether the reader is
    allowed to see what the writer wrote.

    That is deliberate. A revival is not a new feature and should not read like
    one: the diff at each site is the read, and the switch is what keeps the
    change out of a session that did not opt into it.

THE TWO RULES THIS MODULE ENFORCES ON ITSELF
    1. An UNKNOWN VERSION resolves to the default and never to "everything on".
       A typo in a session record, or a session written by a future build and
       replayed by an older one, must not silently re-grade a cohort. It is not
       an exception either — a stored bad value must not brick a session that a
       classroom is sitting in front of — so it degrades to the safe version and
       says so in the log.
    2. An UNKNOWN SWITCH RAISES. `rule_on(gs, "sct_flag_boosts_liv")` dies at the
       first call rather than returning False forever. This is the same lesson as
       the defect this whole exercise is about: systemic_risk_engine.py:80 guessed
       a key name, guessed wrong, returned falsy for a year and passed every test.
       A rules layer that repeats that mistake would be an unusually poor joke.

HOW A VERSION REACHES THE ENGINE
    router.commit_turn stamps it onto the flag bag the engine reads
    (`active_event_flags["_rules_version"]`), from the session record's
    `rules_version` metadata key — exactly as it already stamps difficulty_tier
    and the `_systemic_toggles` bag. The key is underscore-prefixed so
    flag_utils.collect_all_flags never reads a setting as a decision flag, and it
    is in router._PERSISTENT_FLAG_KEYS so the post-tick engines see it too.

    Direct callers that have no router — the golden harnesses, dry_run.py — set
    it in `pedagogical_overrides`, which is the same fallback
    systemic_risk_engine.systemic_toggle_on offers for the same reason.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping

log = logging.getLogger(__name__)

# The key on active_event_flags. Underscore-prefixed: a setting is not a decision
# flag, and collect_all_flags skips keys starting with "_" (flag_utils.py:30).
RULES_FLAG = "_rules_version"

# The semantics every existing session played under. Never change this value —
# change the default a NEW session is created with instead (see CURRENT_VERSION).
DEFAULT_RULES_VERSION = "2026.09"

# What database_memory.create_session / database.create_session stamp on a new
# session. Phase 4 wired the mechanics and left them off; Phase 5 measured them
# and cut over on 2026-09-08. The evidence is in
# docs/verification/phase5_recalibration.md — 3,300 paired Monte Carlo games per
# regime, every one played twice, once under each rule set:
#
#   * M_R moves in 5.2% of games and by a median of 0.0000; mean -0.008.
#   * Terminal value moves by -2.1% on the mean, p05 -23%, p95 +6%.
#   * The archetype changes in 3.5% of games (5.1% with black swans on) and the
#     population split moves by under 1.1 points in every band, so the
#     archetype thresholds are NOT re-derived.
#   * The 2.05 clamp binds in 0.85% of games under 2026.09 and 0.82% under
#     2026.10, so the clamp is NOT re-derived.
#   * Supply-chain transparency was constant at 40.0 in all 3,300 baseline
#     games — the score existed and never moved. Live, at the old per-round
#     cadence, it clamped in 66.9% of games; with the once-only cadence and the
#     recalibrated entropy knob it clamps in 5.1%. That is the one quantity the
#     recalibration actually had to re-derive.
#
# This value governs NEW sessions only. An existing record keeps the version it
# was stamped with, and a record written before the flag existed resolves to the
# baseline — router.commit_turn:3029 stamps `session_info["rules_version"] or
# DEFAULT_RULES_VERSION` and never consults this constant, which is the whole
# compatibility guarantee. tests/test_rules.py pins both halves.
CURRENT_VERSION = "2026.10"


@dataclass(frozen=True)
class Switch:
    """One revived mechanic, with the site it lives at and what it moves.

    `blast_radius` is not decoration. Phase 5 has to re-derive the M_R ceilings,
    the 2.05 clamp and the archetype thresholds, and the input to that work is
    which switches touch graded numbers and which touch a report.
    """
    name: str
    site: str
    shape: str
    effect: str
    blast_radius: str


SWITCHES: dict[str, Switch] = {
    "sct_flag_boosts_live": Switch(
        name="sct_flag_boosts_live",
        site="systemic_risk_engine.py:calc_supply_chain_transparency",
        shape="C — guessed key name: `flags.get(\"flags_set\")` has no writer",
        effect="deep_audit_completed +20, blockchain_traceability +15, "
               "supply_chain_disruption_risk -10, deny_and_deflect -15, "
               "remediation_active +8, circular_redesign +5, epr_program +3 on the "
               "0-100 Supply Chain Transparency score",
        blast_radius="GRADED, AND WIDER THAN THE TERMINAL. Transparency is the "
                     "transparency term of the nature premium in "
                     "calc_esg_adjusted_wacc (engine.py:3692-3696), so it sets the "
                     "cost of capital — and the cost of capital is not a leaf. It "
                     "sets the Gordon exit multiple and so terminal value, and it "
                     "also moves the in-game economy underneath the stakeholder "
                     "engines. MEASURED on all_c: with the switch on, transparency "
                     "collapses, WACC rises 0.0666 -> 0.0684, and by R6 a DIFFERENT "
                     "escalation fires — 2026.09 takes an NPC enforcement fine of "
                     "-6,844,448 where 2026.10 takes an autonomous-agent event of "
                     "-8,374,695 — carrying OPEX up about 22% and the debrief ESG "
                     "index from 57.49 to 39.60. Do not scope Phase 5's "
                     "recalibration to the terminal decomposition alone. "
                     "Separately: the score reaches a clamp on both the uniform-A "
                     "path (floors at 0 by R6) and the legacy path (ceilings at 100 "
                     "by R5), so it is not calibrated for boosts of up to +20 against "
                     "-3/round entropy in the first place.",
    ),
    "sdg_flag_bonuses_live": Switch(
        name="sdg_flag_bonuses_live",
        site="engine.py:calc_sdg_impact call site (:4457)",
        shape="B — wrong source dict: the bonuses read ctx.events, empty at :5055",
        effect="SDG 1 +10 (community_fund), SDG 16 +15 (ethical_ai_overhaul), "
               "SDG 12 +15 (circular_redesign) on the per-goal weighted scores, "
               "before the sdg_index aggregate",
        blast_radius="REPORT ONLY, and this corrects the remediation plan §5.1, which "
                     "says these revivals move M_SDG and so terminal value. They do "
                     "not. calc_sdg_impact returns `sdg_index`; M_SDG is computed by "
                     "terminal_valuation.calculate_sdg_multiplier from a DIFFERENT "
                     "quantity, `sdg_impact_score`, written only by the Corporate SDG "
                     "side track (side_tracks/corporate_sdg/track.py:310). The two "
                     "have never been connected. Nothing graded moves.",
    ),
    "hard_engineering_pulse_revert_live": Switch(
        name="hard_engineering_pulse_revert_live",
        site="round_logic.py:_revert_r5_hard_engineering_pulse (:3509-3534)",
        shape="D — wrong generation of the container: the post-tick flag bag holds "
              "this round's events, not the history",
        effect="carbon_intensity -3.0 on every BU, once, at R7 — reversing the +3 "
               "construction pulse R5 option A applied",
        blast_radius="GRADED. Carbon intensity feeds absolute emissions, the mid-game "
                     "carbon cost, the average CI that sets the WACC carbon term, and "
                     "the R10 climate bonuses on the climate pathway.",
    ),
    "npc_betrayal_reads_option_flags": Switch(
        name="npc_betrayal_reads_option_flags",
        site="npc_stakeholders.detect_betrayal (:50) and the identical copy in "
             "autonomous_agents.detect_betrayal (:880)",
        shape="C — the same guessed `flags_set` key, duplicated in two modules",
        effect="deny_and_deflect (and the other betrayal flags, when option-held) "
               "trigger the NPC / agent trust scar",
        blast_radius="GRADED. CORRECTED 2026-09-08 after measurement: an earlier "
                     "note here said both call sites sit behind a facilitator toggle "
                     "that defaults OFF, so the switch would do nothing until someone "
                     "turned it on. That is wrong. `stakeholder_memory_enabled` "
                     "defaults ON — pedagogical_engine.py:719 sets it True and "
                     "get_pedagogical_toggles merges those defaults, so the "
                     "`.get(..., False)` fallbacks at round_logic.py:1059 and :1236 "
                     "only fire if the toggle machinery throws. Measured on the golden "
                     "matrix, memory_enabled is True in every round of every path. "
                     "(npc_stakeholders.py:26 and :662 still say it defaults off; both "
                     "are stale and are corrected in the same pass.) So this switch "
                     "moves the escalation surface on ALL SEVEN paths and cascades "
                     "into money on two of them. It would have looked inert on four "
                     "paths without the escalation identities added to the matrix "
                     "snapshot, which is what that block is for.",
    ),
    "debrief_reads_option_flags": Switch(
        name="debrief_reads_option_flags",
        site="ceo_interview.py:191,:310,:811 and the two side-track seed reads "
             "(side_tracks/supply_chain/track.py:102, "
             "side_tracks/ethics_sustainability/track.py:95)",
        shape="A — top-level key tests against list-held flags",
        effect="CEO-interview ethical_reasoning +2.5 / +2.0 / +1.0 and its citations; "
               "the supply-chain track's _sc_deep_audit_done bridge value; the ethics "
               "track's ethical_governance seed +10",
        blast_radius="DEBRIEF AND SIDE TRACKS. Nothing in the main ten-round "
                     "simulation reads these; they shape what a team is told "
                     "afterwards and what a side track starts from.",
    ),
    "sct_boosts_apply_once": Switch(
        name="sct_boosts_apply_once",
        site="systemic_risk_engine.calc_supply_chain_transparency",
        shape="not a defect shape — a calibration error the revival exposed",
        effect="A transparency boost applies ONCE, on the round its flag is first "
               "held, instead of being re-applied every round for the rest of the "
               "game.",
        blast_radius="GRADED, and it is the correction that makes "
                     "sct_flag_boosts_live usable. The function applies its whole "
                     "boost table every round. That is harmless for the +5 the one "
                     "working flag carries — measured, it moves the score from 24 "
                     "to 40 over eight rounds — and it is not harmless for a +20 or "
                     "a -15: at that cadence a completed deep audit is a team "
                     "commissioning the same audit ten times. Measured over 3,300 "
                     "sampled games with the boosts live at the old cadence, 67% of "
                     "runs end pinned at a clamp. Applying each boost once, on "
                     "first sight of its flag, is what the magnitudes were written "
                     "for; the previously-applied set is read back from the diag "
                     "the engine already persists.",
    ),
    "sdg_single_quantity": Switch(
        name="sdg_single_quantity",
        site="engine.calc_sdg_impact (the fold) and round_logic.py:507, :3165 "
             "(which quantity M_SDG is computed from)",
        shape="not one of the five — two quantities that were never connected",
        effect="There is ONE SDG number. The Corporate SDG side track's "
               "sdg_impact_score is folded into calc_sdg_impact's sdg_index at "
               "config.SDG_TRACK_WEIGHT per point, and M_SDG is computed from the "
               "index against config.SDG_INDEX_NEUTRAL instead of from the track "
               "score against zero.",
        blast_radius="GRADED, AND THE NAIVE VERSION OF THIS IS A TRAP. M_SDG "
                     "multiplies terminal value directly (round_logic.py:513, "
                     ":3166). The index is ~73.5 for a team that has done nothing — "
                     "measured identical on six of the seven matrix paths at R1 — so "
                     "feeding it to the old zero-anchored formula would multiply "
                     "EVERY session's terminal value by about 1.22, including every "
                     "session already played and debriefed. The neutral point is what "
                     "makes the change safe, and it is why this is one switch and not "
                     "a one-line wire. PROVISIONAL CALIBRATION: at the inherited "
                     "coefficient of 0.25 the achievable range is M_SDG 0.930..1.047 "
                     "against the old lever's 0.97..1.26, so the SDG dimension carries "
                     "LESS authority than it did, not more. Phase 5 decides whether "
                     "that is right and moves config.SDG_MULTIPLIER_COEFF if not.",
    ),
    "fog_of_war_display_noise": Switch(
        name="fog_of_war_display_noise",
        site="engine.py:4368-4384 (the noise) and router._bu_out (where it lands)",
        shape="not one of the five — a mechanic that was specified in configuration "
              "and never implemented",
        effect="Fog of War becomes real: the ±noise engine.py has always computed "
               "and discarded is applied to natural_capital_debt, "
               "social_license_score and governance_risk_score IN THE PLAYER'S VIEW "
               "ONLY, for the configured number of opening rounds, and completing "
               "the R1 deep forensic audit exempts a team from it. The window and "
               "the amplitude come from the facilitator tunables fog_of_war_rounds "
               "and fog_noise_range instead of the hardcoded 2 rounds and ±0.10.",
        blast_radius="NOT GRADED, BY CONSTRUCTION. The perturbation is applied at "
                     "the serialisation boundary (router._bu_out), never to stored "
                     "state, so no engine reads a fogged number and no score moves — "
                     "which is why this needs no recalibration even though it is the "
                     "most visible change in the set. It IS applied to the history "
                     "endpoint as well as the dashboard, because a fog a player can "
                     "defeat by opening a different tab is not a fog. Facilitator "
                     "and admin views are unaffected: they do not go through _bu_out. "
                     "Note that Draft 1.0 of the remediation plan listed the "
                     "fog-of-war exemption as a REVIVAL of deep_audit_completed. It "
                     "was not — fog_noise was computed and read by nothing, and the "
                     "two tunables carry CFG-08's inert ruling — so this switch "
                     "implements a specified mechanic rather than repairing a broken "
                     "read.",
    ),
    "biodiversity_audit_gate_reads_flags": Switch(
        name="biodiversity_audit_gate_reads_flags",
        site="biodiversity_engine.py:442",
        shape="E — string containment over the repr of a nested dict, against a name "
              "no configuration declares",
        effect="the species-risk audit mitigation gates on deep_audit_completed "
               "actually being held, instead of on the substring \"deep_audit\" "
               "appearing anywhere in `str(active_event_flags)`",
        blast_radius="DIAGNOSTIC, BUT IT FAILS OPEN. Corrected 2026-09-08: an "
                     "earlier note called this GRADED. It is not — the gate feeds "
                     "`species_risk_score`, which has NO consumer outside "
                     "biodiversity_engine itself. The stakeholder engines that do read "
                     "biodiversity_state take `water_stress_index` and "
                     "`tnfd_disclosure_level` (npc_stakeholders.py:469-473, "
                     "autonomous_agents.py:408), not species risk, and measured on the "
                     "golden matrix this switch alone moves nothing the fixtures "
                     "record. What remains true, and is the reason it is versioned at "
                     "all: shapes A-D always return False, so their mechanic is simply "
                     "absent, while this one returns True on "
                     "unrelated grounds: measured on the deep-audit paths it fires at "
                     "R1 (matching the repr of the r1_flags LIST), R4 (matching the KEY "
                     "`deep_audit_protected`, a different flag entirely) and R10 "
                     "(matching inside the stringified `_finale_inputs` blob), and is "
                     "False in between. Turning the switch ON therefore also turns the "
                     "gate OFF at R4 and R10, which is a behaviour change in both "
                     "directions and is why it is versioned like the rest.",
    ),
}


@dataclass(frozen=True)
class Knob:
    """One CALIBRATED NUMBER, versioned like a switch.

    Phase 5 exists because reviving a mechanic changes what a score means, and
    the answer to that is to recalibrate. But a calibration constant is a global:
    changing config.SCT_ENTROPY_PER_ROUND re-grades every session ever played,
    including the ones the whole 2026.09 rule set exists to protect. So a rule set
    has to carry its NUMBERS as well as its switches, or the compatibility
    guarantee only covers half the surface.

    `rationale` is required and is the measurement the value came from. A
    calibration constant with no recorded derivation is a number somebody liked.
    """
    name: str
    site: str
    meaning: str
    rationale: str


KNOBS: dict[str, Knob] = {
    "sct_entropy_per_round": Knob(
        name="sct_entropy_per_round",
        site="systemic_risk_engine.calc_supply_chain_transparency",
        meaning="Natural entropy applied to the 0-100 Supply Chain Transparency "
                "score every round, before any flag boost.",
        rationale="-3.0 is the value the function shipped with, and under 2026.09 "
                  "it is nearly invisible because no flag boost has ever applied: "
                  "measured across 3,300 sampled games the score is CONSTANT at "
                  "40.0 in every single run, moved only by materiality_aligned's "
                  "+5, the one boost whose flag is a genuine top-level boolean. "
                  "Turn the other seven on at -3.0/round and the score becomes "
                  "bimodal: 41.5% of games end pinned at 0 and 25.5% at 100, so "
                  "two thirds of teams get a score that cannot move. -1.0 is "
                  "derived in docs/verification/phase5_recalibration.md: over ten "
                  "rounds it costs a passive team 10 points of a 30-point opening "
                  "position instead of all 30, which is what leaves room for the "
                  "boosts to mean anything.",
    ),
}


@dataclass(frozen=True)
class RuleSet:
    version: str
    note: str
    switches: Mapping[str, bool]
    calibration: Mapping[str, float] = field(default_factory=dict)


RULE_SETS: dict[str, RuleSet] = {
    "2026.09": RuleSet(
        version="2026.09",
        note="Semantics as played up to commit 0ad1246. Every revival off. This is "
             "what an unversioned session record means, and it must never change.",
        switches={name: False for name in SWITCHES},
        calibration={"sct_entropy_per_round": -3.0},
    ),
    "2026.10": RuleSet(
        version="2026.10",
        note="Every mechanic Appendix B found designed-but-never-run, switched on. "
             "NOT a default: Phase 5 owns the recalibration (the M_R ceilings, the "
             "2.05 clamp and the archetype thresholds were all derived against an "
             "engine in which these did not fire) and the cut-over.",
        switches={name: True for name in SWITCHES},
        calibration={"sct_entropy_per_round": -1.0},
    ),
}


class UnknownSwitch(KeyError):
    """A switch name no rule set declares. Raised rather than defaulted — see the
    module docstring, rule 2."""


def _flags_of(state: Any) -> Mapping:
    """The flag bag, whether a global_state or a bare flags dict was passed.

    Several consumers only ever receive the flag dict —
    calc_supply_chain_transparency takes `flags`, not `gs` — so the reader has to
    accept both. Same accommodation, for the same reason, as
    systemic_risk_engine.systemic_toggle_on.
    """
    if not isinstance(state, dict):
        return {}
    inner = state.get("active_event_flags")
    return inner if isinstance(inner, dict) else state


def resolve_version(state: Any) -> str:
    """The rules version in force for this state.

    active_event_flags["_rules_version"] (stamped at commit) → the same key on a
    bare flags dict → pedagogical_overrides["rules_version"] (direct callers) →
    the default. An unrecognised value degrades to the default and is logged; it
    is never treated as an opt-in.
    """
    flags = _flags_of(state)
    version = flags.get(RULES_FLAG)
    if version in (None, ""):
        ped = state.get("pedagogical_overrides") if isinstance(state, dict) else None
        if isinstance(ped, dict):
            version = ped.get("rules_version")
    if version in (None, ""):
        return DEFAULT_RULES_VERSION
    version = str(version)
    if version not in RULE_SETS:
        log.warning(
            "[rules] unknown rules_version %r; falling back to %s. A session pinned "
            "to a version this build does not know must not be re-graded under a "
            "newer rule set.", version, DEFAULT_RULES_VERSION,
        )
        return DEFAULT_RULES_VERSION
    return version


def ruleset_for(state: Any) -> RuleSet:
    return RULE_SETS[resolve_version(state)]


def rule_on(state: Any, switch: str) -> bool:
    """Is this mechanic enabled for this state?

    Raises UnknownSwitch on a name no rule set declares. That is the point: the
    defect this module exists to remediate is a reader that guessed a key name,
    guessed wrong and returned falsy forever without anything noticing.
    """
    if switch not in SWITCHES:
        raise UnknownSwitch(
            f"{switch!r} is not a declared rule switch. Declared: "
            f"{sorted(SWITCHES)}"
        )
    return bool(ruleset_for(state).switches[switch])


class UnknownKnob(KeyError):
    """A calibration key no rule set declares. Raised, not defaulted — same
    discipline as UnknownSwitch, and for the same reason."""


def rule_value(state: Any, knob: str) -> float:
    """The calibrated number in force for this state.

    Resolution is the switch resolution: the rule set the state names, and the
    baseline for anything unrecognised. A knob missing from a rule set is a
    programming error rather than a session's problem, so it raises here rather
    than silently taking another version's value.
    """
    if knob not in KNOBS:
        raise UnknownKnob(
            f"{knob!r} is not a declared calibration knob. Declared: {sorted(KNOBS)}")
    ruleset = ruleset_for(state)
    if knob not in ruleset.calibration:
        raise UnknownKnob(
            f"rule set {ruleset.version} declares no value for {knob!r}")
    return float(ruleset.calibration[knob])


def stamp(flags: dict, version: str | None) -> dict:
    """Write the version onto a flag bag, as router.commit_turn does. Returns the
    same dict so it can be used inline. A None or empty version stamps the
    default rather than leaving the key absent, so a persisted round always
    records which rules produced it."""
    if isinstance(flags, dict):
        flags[RULES_FLAG] = str(version) if version else DEFAULT_RULES_VERSION
    return flags
