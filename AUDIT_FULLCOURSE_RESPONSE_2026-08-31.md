# Full-Course Impact Audit — Response & Repair Report
**Date:** 2026-08-31 · **Branch:** `fix/full-course-impact-audit` (off `fix/r2-materiality-audit`, 8 commits)
**Scope:** Rounds 1, 3–10, terminal valuation, ending pathways — companion to the Round 2 repair of the same date.
**Shipping constraint honoured:** behavioural branch only; never apply to a mid-course cohort.

---

## 1. Reproductions (§5)

| Repro | Result |
|---|---|
| §5.1 coverage check | **Matched exactly.** Generic set = the five listed keys; unapplied = `divest_all` [10], `natural_capital_debt_delta` [2,4,10], `social_license_delta` [1,2,3,7,10], `treasury` [2]. Round 10 (not 8) confirmed for C-1, as the audit's corrected draft states. |
| §5.3 special_rules | **Matched exactly.** 14 keys, 4 dead, same names. |
| §5.2 just-transition grep | **Partially matched — two deviations.** (a) The grep also hits `npc_stakeholders.py` (a satisfaction-driver id) and `regulatory_sandbox.py` (a sandbox instrument id) — neither writes the flag namespace, so the *dead-flag* substance holds. (b) More materially: line 2786 sits inside `_post_r10_grand_finale`, so `choice in ("option_a","option_c")` tested the **Round 10** choice — the old code passed *Resist & Integrate* and *Divest* and failed *Spin-off*. The audit's claim that it "passes Immediate Closure and fails Managed Transition" was wrong about which round's choice is read; the incoherence with the +0.12 `managed_transition` bonus was real either way. The fix was designed against the actual behaviour. |
| Baseline | R2 regression suite green before any change (40 tests — the doc says 38; it has grown). |

## 2. Design rulings taken (with the design owner, this session)

- **C-6 `divest_all`** → *leave inert, flag for design.* No mechanics invented; allow-listed in `test_engine_invariants.py` with the reason, marked in `round_configs.py`. Its live siblings (synergy_wipe, treasury, revenue_delta, −12 SLO, +8 NCD — the last two now landing via C-1/C-2) carry the Divest ending.
- **B-1 just transition** → *align with the R9 M_R view.* `just_transition_passed` = R9 `managed_transition` OR `community_fund`; Immediate Closure fails. Dead-flag reads and the R10-choice condition removed. Works in both paradigms (pillar flags carry the same names).
- **B-2 `scope_3_transparency`** → the audit's premise was wrong: **no** R6 pillar mentions Scope 3 transparency (nearest candidates: R2's "Supply Chain Transparency" pillar area; R3, the Scope 3 round). Follow-up ruling: *R3 ≥80% Scope 3 data completeness* (Option A's Direct Supplier Audit) writes the flag.
- **C-3 velocity amplifier** → *persistent escalation.* Extracted to `_apply_social_media_velocity`, called from `post_tick` for R4+; multiplier escalates 1.1× (R4) → 1.7× (R10), active only while group reputation < 60. This is a behavioural change to R5–R10 for low-reputation teams; ceiling teams (rep ≥ 60) are untouched, and the golden trace rebaseline absorbs it.

## 3. Before / after — C-1 + C-5 together

**R2 option treasury** (the authoritative isolated deltas, by direct `post_tick` execution; the `option_treasury_applied_r2` event marks the charge):

| Option | Old charge | New charge | Clawback |
|---|---|---|---|
| A Full Materiality Alignment | $0 | **−$2,500,000** | — |
| B Strategic Exceptions | $0 | $0 | — |
| C CEO-Only Sign-Off | $0 | $0 | −$6,000,000 (unchanged) |

Full-session closing treasuries (TestClient, seed 4242, capex $3M/BU): A $63.67M→$62.15M, B $64.80M→$59.63M, C $64.38M→$61.15M. Cross-option comparison of these carries ±$1–3M of per-session market-seeding noise, which is why the isolated deltas above are the acceptance numbers. Option A no longer strictly dominates Option B.

**Round-10 social licence** (licence-maximising vs licence-minimising team, full 10-round games, capex $3M/BU to keep the investment ratio above the 15% greenwashing threshold):

| Team | Old avg SLO | New avg SLO | Crosses 75? | Instability Discount |
|---|---|---|---|---|
| Licence-max | 99.25 | 95.0 | yes → yes | never applied |
| Licence-min | 2.16 | 0.0 | no → no | applied both |

Two honest nuances the audit's severity framing needs: (a) with a competent capex posture, an all-max team already cleared 75 pre-fix — R6/R8/R9's applied positives plus NPC/stakeholder feedback carried it; C-1's practical bite is per-round fidelity (every one of the 14 dead promises now lands — verified exactly, all 30 round×option combinations apply the configured delta exactly once) and teams near the 75 boundary. (b) With low per-BU capex, the **greenwashing engine** (−7.5/−15 SLO per round below a 15% average investment ratio) dominates every other SLO mechanic and drives all teams toward 0 — worth knowing for classroom calibration; it is why the harness pins capex.

## 4. Ceilings

`test_mr_ceilings_unchanged` green throughout and at HEAD: **1.93 / 2.02** (with JT scaling), partial tier 1.88. No fix moved a ceiling.

## 5. Beyond the audit's list — found during this work

1. **R9 retraining clawback could never fire** (same dead-read class as B-3): ITEM 20 reads `extra["reputation_applied_r9"]`, which nothing wrote. Fixed as part of C-4 — the R9 handler now stamps it, so failed retraining genuinely claws back 30% of the R9 reputation gain. *Behavioural.*
2. **`supply_chain_fragile` is dual-form with disagreeing writers** (caught by the new generalised dual-form guard, test 6): declared in a supply-chain side-track crisis option's `flags_set` AND boolean-written by the track's data bridge on final visibility < 50. A team can end up carrying both `supply_chain_resilient` and `supply_chain_fragile`. No core code reads it today, so it is allow-listed with the reason and left for the side-track owner — not silently "fixed".
3. **Pillar-mode generic-applier leak — reported, deliberately NOT fixed.** `_apply_common_impacts` also runs in pillar mode, where the router has already applied the pillar aggregates AND `choice_selected` holds a *translated* legacy option — so that option's `reputation`, `revenue_delta`, `governance_risk_delta` and (except in R3, which guards it) `carbon_intensity_delta` are applied **on top of** the pillar aggregates. Same defect class as C-1, inverted: double instead of never. The new SLO/NCD appliers carry an explicit pillar-mode check so they do not extend the leak; repairing the four existing keys changes pillar-cohort difficulty and deserves its own measured, cohort-boundary change.
4. **Pre-existing failures at the branch base** (verified identical at `ff2b3ab`): `test_team_seats` ×5, `test_scope_seeding_parity` ×4, `test_ci_delta_roundtrip`, `test_player_login_parity`. Untouched. Full suite otherwise: **2136 passed**. Two order-dependent flakes observed (a sec3 dashboard test under full-suite ordering; `test_option_c_reduces_position…` once lost its $6M clawback signal to cross-session market noise) — both pass in isolation, both pre-existing infrastructure quirks.
5. **DB round-trip:** every new state key (`scope_3_transparency`, `retraining_succeeded`, `retraining_roll`) lives inside `active_event_flags`, which both backends already persist wholesale; no new top-level global-state keys were added. Test 7 exercises the memory backend end-to-end.

## 6. Where this response corrects the audit

- **B-1** as written misidentified whose choice line 2786 reads (Round 10's, not Round 9's) and understated the flag-name reuse elsewhere (§1). The finding survives; the description didn't.
- **B-2**'s premise (an R6 pillar "literally 'Scope 3 transparency'") does not exist in the shipped configs; resolved by follow-up ruling.
- **C-1/C-2's prescribed fix is insufficient for Round 10.** The generic applier runs *after* the round handler, but R10's handler itself computes the Instability Discount (closing SLO) and the DMAV solvency gate (closing NCD). Applied generically, Divest's −12 SLO and +8 NCD would land after the numbers that are supposed to feel them. R10 therefore applies both **in-handler** (after the synergy gate, before M_R), guarded so the generic applier skips it — the coverage test is satisfied either way, but only this ordering makes the terminal round's consequences real.

## 7. Tests shipped (`backend/tests/test_engine_invariants.py`)

1. Every impact key applied (AST-resolved handler ownership) — failed pre-fix on exactly the four §5.1 keys; the acceptance criterion. 2. Exact-single-application via direct `post_tick` (30 combos; deferral and severe-drop mechanics modelled). 3. Retired spellings absent from all config files. 4. Every `in all_flags` read has a writer (dynamic writers documented). 5. Every special_rules key is read (allow-list empty after B-4). 6. Generalised dual-form guard (extends the R2 F-2 guard; already earned its keep — see §5.2). 7. SLO steerability: licence-max crosses 75, licence-min doesn't — the property C-1 destroyed.

## 8. Housekeeping

- Financial golden trace rebaselined in-branch (first divergence is exactly R2A's −3 NCD and −$2.5M landing); committed with the JSON diff as its test instructs.
- `SIMULATION_CONTEXT.md` updated (repairs changelog; B-2 earn-condition; C-6 inert note).
- The pre-existing uncommitted WIP on `fix/r2-materiality-audit` (DEPLOYMENT_CHECKLIST.md, backend/main.py, test_disk_space_health.py) was preserved through a stash round-trip; its content is intact but its staged-vs-unstaged split collapsed to unstaged — re-stage before committing it.
- A stale `.git/index.lock` was removed (with permission) to unblock git on this machine.

---

## 9. Follow-up branch: `fix/pillar-impact-ownership` (same day)

Resolves §5.3 of this report (the pillar-mode leak), on its own branch off
`fix/full-course-impact-audit`, with its own acceptance tests committed red first.

**Measured pre-fix:** every translated legacy option's `reputation`, `revenue_delta`,
`carbon_intensity_delta` and `governance_risk_delta` stacked on top of the router's
pillar aggregates in ALL ten rounds (full leak map in the red-test commit message);
no never-apply gap exists on the pillar surface — every key the pillar options
declare is router-aggregated or handler-read.

**Design rulings (this session):** R1–R9, the router is the single applier of option
impacts in pillar mode — the legacy translation is flags/bookkeeping only. R10 is the
exception: the pillar selections map to an A/B/C ending whose FULL impact set is the
single source (its SLO/NCD now land in pillar mode for the first time), and the
router skips applying R10 pillar aggregates on top.

**Changes:** `_apply_common_impacts` bypasses entirely in pillar mode for R1–R9;
the R10 handler's SLO/NCD pillar guards are lifted; the router's aggregate
application is extracted to `_apply_pillar_aggregate_impacts` (unit-testable) and
gated off for R10. Edge fix: `pillar_cost_applied` is set even for an all-zero-cost
pillar selection — previously such a commit lost its paradigm marker and the whole
tick ran as legacy by accident.

**Before/after (same pillar policy, same seed, 10 rounds):** closing treasury
+$53.6M → −$137.5M; terminal value +$65.7M → −$214.1M; M_R 1.58 both. The leak was
financing pillar cohorts by roughly $190M of terminal value under this policy.
Ship strictly at a cohort boundary, and treat the numbers as a REBALANCING INPUT:

**Design gap exposed (needs the design owner):** pillar options declare no revenue
impacts anywhere — post-fix, pillar mode has NO decision-driven revenue lever; the
leaked legacy `revenue_delta` was accidentally load-bearing for pillar-cohort
revenue growth. Either pillar options should gain deliberate revenue impacts (added
to the router aggregation list), or pillar-mode balance should be retuned around
costs/CI/SLO only. Until that ruling, pillar cohorts on this branch will find the
course markedly harder than the last thirty cohorts did.

**Verification:** 31/31 pillar-ownership acceptance tests green; invariants + R2
suites green (99 passed); full suite 2167 passed with only the same 11 pre-existing
base failures; M_R ceilings untouched (legacy path unchanged; ceilings test green).

### §9 addendum — revenue lever implemented (same day)

The design gap is closed: SPEC_Pillar_Revenue_Impacts v2 (evidence-rated values)
is wired in — 68 `revenue_delta` values in pillar_configs.py (R1–R9; R10 none, by
ruling), an effectiveness-scaled flat-per-BU revenue block applied last in
`router._apply_pillar_aggregate_impacts`, and four new invariants (R10 carries no
revenue config; all values inside the ±$400K realism band with the three deliberate
extremes pinned; aggregation→application lands exactly once; helper scaling).
Validation, same policy/seed: closing treasury +$13.8M and terminal value +$61.1M —
within 7% of the leaky engine's +$65.7M terminal value, restoring comparable cohort
difficulty through designed levers. Full suite: 2169 passed; failures confined to
the same four pre-existing files. Cohort-boundary shipping unchanged.
