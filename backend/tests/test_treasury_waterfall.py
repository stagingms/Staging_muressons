"""Treasury waterfall — measure the gap before claiming a conservation law.

WHAT I SET OUT TO DO, AND WHY I DIDN'T
    Remediation #10 said: `test_universal_math_engine.py`'s INV-1 "Conservation
    of Treasury" is a tautology — it asserts `ledger.treasury_end ==
    next_ledger.treasury_start`, and `run_deterministic_simulation` assigns
    those equal by construction, so the branch is unreachable. The proposed fix
    was to assert the real waterfall instead:

        treasury_end == treasury_start + csf - capex - interest + side_track

    So I measured it before asserting it. It does not hold, and not by a little:

        DEFAULT_4_BU             legacy_abc        max |residual|        9,619,862
        DEFAULT_4_BU             multi_toggles     max |residual|      656,628,336
        SINGLE_BU_PHARMA         legacy_abc        max |residual|        2,000,000
        SINGLE_BU_PHARMA         multi_toggles     max |residual|        2,728,071
        VERTICAL_OIL_AND_GAS_SUB legacy_abc        max |residual|       14,117,483
        VERTICAL_OIL_AND_GAS_SUB multi_toggles     max |residual|      602,922,486

    A $656M unexplained movement in a simulation that opens with $50M of
    treasury is not a rounding question. `RoundLedger` records six terms; the
    engine moves treasury through considerably more than six paths — carbon
    fees, green-fund transfers, fines, black-swan costs, board resolutions, the
    balance-sheet tick, NPC penalties. None of them are in the ledger, so none
    of them are in anybody's mental model of where the money goes either.

    Asserting `residual == 0` would therefore have replaced an invariant that
    cannot fail with one that always does. So this file does the honest thing:
    it MEASURES the unexplained movement, REPORTS it, and RATCHETS it. As terms
    are added to the ledger the ceiling comes down, and when it reaches zero the
    engine has a real conservation law — at which point replace this with the
    equality and delete the ratchet.

THE LEAD, CLAIMED (2026-08-31)
    `SINGLE_BU_PHARMA / legacy_abc`'s residual of exactly 2,000,000.00 was the
    predicted case of "a term never applied": CapEx principal is by design not
    a treasury outflow (interest-only financing above the free-CSF allowance —
    see _residual). Removing the term from the expected-waterfall zeroed that
    case's residual outright. The remaining residuals were then hunted down
    term by term — see below.

THE CONSERVATION LAW, ACHIEVED (2026-09-01)
    Eight terms explain every dollar, every round, in all six compositions:

        + csf                        engine's own Gross Profit waterfall entry
        + option_treasury            post-tick option charges/gains (signed)
        - loan_interest              CapEx financing (interest-only, principal
        - emergency_credit_interest    never debits treasury — the claimed lead)
        - negative_treasury_interest
        - regulatory_ratchet_fine    events["regulatory_ratchet"]["fine"]
        - black_swan_treasury_hit    black_swan_diagnostics.total_treasury_drain
        - cbam_surcharge             cbam_surcharge_applied
        - loss_damage_levy           loss_damage_levy_applied
        + deferred_revenue_collected revenue_generation_completed
        + treasury_floor_clamp       treasury_floor_clamp_applied (insolvency
        + side_track_treasury_delta    floor forgives losses below the floor)

    residual == 0 (< $0.01) is asserted unconditionally for every case and
    every round: the ratchet this file promised is retired, replaced by the
    equality it was ratcheting toward.

THE ENTROPY SOURCE, FOUND (2026-09-01)
    The runner's nondeterminism was never PYTHONHASHSEED. process_tick returns
    a REBUILT active_event_flags that drops the cohort stochastic_seed;
    production survives because router.commit_turn merges the old flags back in
    as the base, but this harness fed the engine its own raw output, so from R2
    onward every event_rng() call fell back to a SYSTEM-seeded random.Random()
    — entropy random.seed() cannot reach. Black swans then fired differently
    per process (and their treasury hits were an untracked ledger term, which
    is why the residuals both moved and refused to close). Re-stamping the seed
    each round in the runner (exactly what dry_run.py:164 already did) made all
    six fingerprints bit-identical across processes; the strict xfail below
    became a passing pin.

WHY THIS MATTERS BEYOND TIDINESS
    A characterization test (the financial golden trace) tells you the numbers
    did not change. A conservation law tells you the numbers are POSSIBLE. They
    catch different bugs: the golden pins behaviour including any leak, so a
    leak that has always been there stays invisible to it forever. This is the
    only test in the suite that could ever find one.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import test_universal_math_engine as UME  # noqa: E402  (reuses its runner + ledger)

_ROUNDS = 10

# Cross-process pins, captured 2026-09-01 after the seed re-stamp fix (three
# fresh processes agreed bit-for-bit). A change here means the simulation's
# numbers changed — intended (rebaseline deliberately, in its own commit) or
# not (a regression this file exists to catch).
# Rebaselined 2026-09-01 for the ratchet-economy repair (calibration ruling
# A+B+C, CALIBRATION_DIAGNOSIS_2026-09-01.md): flow penalties no longer
# compound into the BU base and revenue gains inflation pass-through, so every
# trajectory deliberately changed. Verified bit-identical across two fresh
# processes before pinning.
# Rebaselined 2026-09-01 (launch audit F-01/F-02): the contagion sigmoid is
# normalised so severity 0 no longer shaves ~5.9 reputation points per tick, and
# water_dependency is passed to the ESG-WACC as the 0-1 fraction it expects
# (WACC was pinned at the 20% cap). Only the two multi_toggles trajectories
# moved — legacy_abc treasury never touches either quantity (NCD interest is a
# BU stock, not a treasury flow). Bit-identical across two fresh processes.
# Rebaselined 2026-09-02 (launch audit phase 3: F-04/F-04b, F-05, F-06, F-08,
# F-09, F-10, F-13). Every trajectory moved, deliberately: CapEx now debits
# treasury (allowance tranche in cash, excess as an amortising term loan);
# the per-round synergy OPEX reduction is capped; four more flow penalties
# became transients AND, with F-04b, every transient recorded after gross
# profit is banked now charges treasury this round (before, the talent
# premium, NCD penalty, defection and squeeze reached no cash at all —
# multi_toggles and legacy_abc had converged to the same fingerprint). Bit-
# identical across two fresh processes before pinning.
_EXPECTED_RUNNER_FINGERPRINTS = {
    # WP-23 (audit 2026-09-04, 2026-09-05): re-pinned after three deliberate
    # numbers changes — the regulator's enforcement fine is capped by tier and
    # 4% of turnover (FIN-09), a black swan's revenue/OPEX percentages are
    # flows for the event's duration instead of permanent base erosion
    # (IMP-05), and TARGETED swan effects (revenue_pct_reduction_targeted /
    # opex_pct_increase_targeted — the embargo, the water crisis) now apply:
    # they were dropped from impacts_applied before, so those events were
    # inert. Bit-identical across two interpreters under PYTHONHASHSEED=1
    # and 12345 before pinning. Unmoved cases are the ones no swan fires in.
    # C-1 (owner calibration ruling, 2026-09-05): the greenwash bar is the
    # TEAM'S share of the CSF pool (Σ per-BU ratios), not their average. This
    # runner gives every BU 10 % of the pool: a four-BU team therefore put 40 %
    # of the pool behind each claim and was still a greenwasher on every full
    # and moderate claim from R4 (average 10 % < 15 % / 10.05 %). Only the
    # multi-BU compositions move (+2.28M … +2.85M treasury by R10 — the SLO
    # penalty's brand/talent terms); the SINGLE_BU pins are byte-identical,
    # and legacy_abc / healthcare now fingerprint IDENTICALLY to brsr_ngrbc,
    # which is never greenwash-checked on this runner — i.e. that penalty was
    # the whole difference. Bit-identical under PYTHONHASHSEED=1 and 12345.
    ("DEFAULT_4_BU", "advanced_climate"): "c039fef396bfd7a2",
    ("DEFAULT_4_BU", "brsr_ngrbc"): "020d13667d5e6d5d",
    ("DEFAULT_4_BU", "healthcare"): "020d13667d5e6d5d",
    ("DEFAULT_4_BU", "legacy_abc"): "020d13667d5e6d5d",
    ("DEFAULT_4_BU", "multi_toggles"): "8ed5dc35b55ae0b2",
    ("SINGLE_BU_PHARMA", "advanced_climate"): "f8b44913c6fec8fa",
    ("SINGLE_BU_PHARMA", "brsr_ngrbc"): "c039cbbb9198437b",
    ("SINGLE_BU_PHARMA", "healthcare"): "c039cbbb9198437b",
    ("SINGLE_BU_PHARMA", "legacy_abc"): "c039cbbb9198437b",
    ("SINGLE_BU_PHARMA", "multi_toggles"): "93273de34e6b5177",
    ("VERTICAL_OIL_AND_GAS_SUB", "advanced_climate"): "d1f5895bd742fec9",
    ("VERTICAL_OIL_AND_GAS_SUB", "brsr_ngrbc"): "643d2b27f1dd4637",
    ("VERTICAL_OIL_AND_GAS_SUB", "healthcare"): "643d2b27f1dd4637",
    ("VERTICAL_OIL_AND_GAS_SUB", "legacy_abc"): "643d2b27f1dd4637",
    ("VERTICAL_OIL_AND_GAS_SUB", "multi_toggles"): "738085d5f2a14b37",
}

# Audit 2026-09-04 (WP-12 harness debt): `un_sdg` is not a paradigm the
# platform accepts (create_session rejects it) and `brsr_ngrbc` — which it
# does — was missing, so the law was a statement about a paradigm nobody can
# play and silent on one anybody can. The list now derives from
# config.VALID_DECISION_PARADIGMS; the brsr_ngrbc pins were computed twice in
# separate interpreters under different PYTHONHASHSEEDs before being pinned.
#
# WORTH KNOWING, and not a defect this commit fixes: `brsr_ngrbc` and `healthcare`
# fingerprint IDENTICALLY to `legacy_abc` on all three compositions. Their
# distinct mechanics are not in the financial layer this runner exercises —
# healthcare's own BU composition (hospitals/clinics) is not in
# BU_COMPOSITION_FACTORIES at all, so it runs on the generic four. These pins
# therefore prove those paradigms are STABLE, not that they are DISTINCT. A
# separate harness is needed to cover what actually differs about them.

# B-5 (2026-09-03): the law used to run on legacy_abc and multi_toggles only,
# while paradigm_registry declares five. Running its own _residual over the
# other three found advanced_climate breaking it by $1,813,896 over ten rounds
# (worst round -$253,141.94) through the unledgered internal carbon fee. Every
# DECLARED paradigm is covered now, so a paradigm-gated treasury path cannot
# hide behind a case list again.
from config import VALID_DECISION_PARADIGMS as _VALID_PARADIGMS  # noqa: E402
_PARADIGMS = sorted(_VALID_PARADIGMS)
assert set(_PARADIGMS) == {"legacy_abc", "multi_toggles", "advanced_climate", "healthcare", "brsr_ngrbc"}, _PARADIGMS
_CASES = [
    (comp, par)
    for comp in ("DEFAULT_4_BU", "SINGLE_BU_PHARMA", "VERTICAL_OIL_AND_GAS_SUB")
    for par in _PARADIGMS
]


def _residual(ledger) -> float:
    """Treasury movement the ledger cannot explain, for one round.

    Positive: treasury ended HIGHER than the recorded terms allow — money
    arrived from a path nobody is tracking. Negative: money left through one.
    """
    # DEEP-8 lead CLAIMED (2026-08-31): `- ledger.total_capex` used to sit in
    # this formula because CapEx principal was, by design, not a treasury
    # outflow — `new_treasury = base + csf − interest`.
    # F-05 (launch audit 2026-09-01) changed the design: the allowance tranche
    # (≤ FREE_CSF_PCT × treasury) is paid in cash this round and the excess is
    # a term loan repaid over the remaining rounds, so two evented terms join
    # the law — capex_equity_funded and capex_loan_repayment. total_capex
    # itself is still not a term (the loan-funded part is cash-neutral when
    # drawn); the new terms are exactly what the engine debits.
    expected = (
        ledger.treasury_start
        + ledger.csf
        - ledger.capex_equity_funded       # F-05: cash-funded CapEx tranche
        - ledger.capex_loan_repayment      # F-05: scheduled term-loan principal
        + ledger.post_csf_flows            # F-04b (2026-09-02): flow penalties assessed
                                           # after CSF was banked (talent premium, NCD
                                           # OPEX, defection, squeeze), signed, evented
        + ledger.option_treasury           # DEEP-8 term 2 (2026-08-31): post-tick
                                           # option charges/gains, signed — the
                                           # second exact-valued residual claimed
                                           # (R2A's -\$2.5M after the C-5 repair)
        - ledger.loan_interest
        - ledger.emergency_credit_interest
        - ledger.negative_treasury_interest
        + ledger.side_track_treasury_delta
        # DEEP-8 terms 3-6 (2026-08-31): direct engine debits/credits, each
        # read from its own event. The Regulatory Ratchet fine was the silent
        # exact-valued residual (\$2.5M / \$3.75M at R1); CBAM (R3/R7), the
        # Loss & Damage levy (tipping tiers) and deferred revenue collection
        # (pending projects) are its evented siblings.
        - ledger.regulatory_ratchet_fine
        - ledger.black_swan_treasury_hit   # DEEP-8 term 7 (2026-09-01): black-swan
                                              # direct debits (whistleblower/ransomware/
                                              # pandemic...), from black_swan_diagnostics
        + ledger.treasury_floor_clamp      # DEEP-8 term 8 (2026-09-01): losses the
                                              # insolvency floor absorbed (creditors stop
                                              # extending at FINANCIAL_TREASURY_FLOOR +
                                              # 200M x ESG investment ratio)
        - ledger.cbam_surcharge
        - ledger.loss_damage_levy
        + ledger.deferred_revenue_collected
        # B-5 (2026-09-03): four direct treasury movements that had no term
        # here. The law closed at $0.00 on legacy_abc and multi_toggles only
        # because those two paradigms never trigger them — it was a statement
        # about two paradigms, not about the engine. The internal carbon fee is
        # gated on advanced_climate and broke the law by $1,813,896 over ten
        # rounds the moment the law was run against it.
        - ledger.internal_carbon_fee
        - ledger.carbon_offset_purchase
        - ledger.carbon_retribution_levy
        + ledger.emergency_bailout
    )
    return ledger.treasury_end - expected


def _run(composition: str, paradigm: str):
    matrix = UME.MatrixConfig(
        decision_paradigm=paradigm, bu_composition=composition, side_track_payload=None
    )
    ledgers, _final_gs, _ = UME.run_deterministic_simulation(matrix, num_rounds=_ROUNDS)
    return ledgers


# ── 1. Properties that are unconditionally true ────────────────────────────

@pytest.mark.parametrize("composition,paradigm", _CASES)
def test_treasury_stays_a_finite_number(composition, paradigm):
    """The one thing INV-1 already got right, kept and made reachable. NaN or
    inf here means a divide-by-zero or overflow reached the money path, and
    every downstream number — EBITDA, M_R, terminal value — is meaningless."""
    for ledger in _run(composition, paradigm):
        assert math.isfinite(ledger.treasury_start), f"round {ledger.round_number} start not finite"
        assert math.isfinite(ledger.treasury_end), f"round {ledger.round_number} end not finite"


@pytest.mark.parametrize("composition,paradigm", _CASES)
def test_every_recorded_ledger_term_is_finite(composition, paradigm):
    for ledger in _run(composition, paradigm):
        for term in ("csf", "total_capex", "option_treasury", "regulatory_ratchet_fine",
                     "black_swan_treasury_hit", "treasury_floor_clamp",
                     "cbam_surcharge", "loss_damage_levy", "deferred_revenue_collected",
                     "loan_interest", "emergency_credit_interest",
                     "negative_treasury_interest", "side_track_treasury_delta"):
            value = getattr(ledger, term)
            assert math.isfinite(value), f"round {ledger.round_number}: {term} is {value}"


@pytest.mark.parametrize("composition,paradigm", _CASES)
def test_treasury_conservation_law(composition, paradigm):
    """residual == 0, to the cent, per round, for EVERY case (2026-09-01).

    The equality INV-1 claimed and could not reach: treasury_end must equal
    treasury_start plus the recorded ledger terms — see _residual for the full
    eight-term waterfall. A failure here means a treasury path was added to the
    engine without a ledger term (or an existing one stopped being evented):
    add the term, don't widen the tolerance.
    """
    for ledger in _run(composition, paradigm):
        r = _residual(ledger)
        assert math.isfinite(r)
        assert abs(r) < 0.01, (
            f"conservation law broken: R{ledger.round_number} residual {r:,.2f} — "
            f"a treasury path was added without a ledger term")


# ── 2. Cross-process determinism, pinned ──────────────────────────────────

@pytest.mark.parametrize("composition,paradigm", _CASES)
def test_the_deterministic_runner_is_actually_deterministic(composition, paradigm):
    """Once the most valuable failing assertion in this file; now a pin.

    Root cause (2026-09-01, module docstring "THE ENTROPY SOURCE, FOUND"):
    process_tick drops the cohort stochastic_seed from active_event_flags, so
    from R2 onward event_rng() fell back to a system-seeded random.Random() —
    entropy neither random.seed() nor PYTHONHASHSEED could explain or control.
    The runner now re-stamps the seed each round (as router.commit_turn's flag
    merge does in production and dry_run.py:164 does in its own harness), and
    these fingerprints are bit-identical across processes.

    This compares against a COMMITTED baseline, so it is the cross-process
    guarantee that matters: every invariant in test_universal_math_engine.py
    runs on this runner, and until this passed they were evaluating a different
    simulation on every run. A mismatch means the simulation's numbers changed:
    rebaseline deliberately in its own commit, or find the regression.
    """
    import hashlib
    ledgers = _run(composition, paradigm)
    payload = "|".join(f"{l.round_number}:{l.treasury_end:.4f}:{_residual(l):.4f}" for l in ledgers)
    fingerprint = hashlib.sha256(payload.encode()).hexdigest()[:16]
    expected = _EXPECTED_RUNNER_FINGERPRINTS[(composition, paradigm)]
    assert fingerprint == expected, (
        f"the runner produced a different simulation than the committed baseline.\n"
        f"  expected {expected}\n  got      {fingerprint}\n"
        "Either a deliberate numbers change (rebaseline in its own commit) or a "
        "regression — including the seed-drop regression this test was born from."
    )


# ── 4. Make the debt visible on a green run ────────────────────────────────

def test_report_unexplained_treasury(capsys):
    """Not an assertion — a printout. `pytest -s` shows the size of the gap.

    Stable run to run since the seed re-stamp fix, and all zeros since the
    conservation law closed — kept as the quickest human-readable check that it
    still holds.
    """
    with capsys.disabled():
        print("\n[treasury waterfall] unexplained movement, worst round per case:")
        for composition, paradigm in _CASES:
            worst = max(abs(_residual(l)) for l in _run(composition, paradigm))
            print(f"    {composition:<26} {paradigm:<14} ${worst:>16,.2f}")
        print("    conservation law holds: every value above should be $0.00 "
              "(asserted per round by test_treasury_conservation_law).")
