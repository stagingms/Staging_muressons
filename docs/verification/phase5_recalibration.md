# Phase 5 — recalibrate and cut over

Repo: `muressons-sim`, branch `fix/audit-remediation-wave3-20260906`, on top of the
Phase 0–4 work. Date: 2026-09-08.

Phase 5 of `Muressons_Dead_Flag_Remediation_Plan.docx` §6: *"Run the Monte Carlo
stress harness under both rule sets. Re-derive the M_R ceilings, the clamp and the
archetype thresholds. Re-execute the affected register rows. Reissue the affected
manuscript passages. Exit condition: a published delta report, a new default
rules_version, and a register with no row still stamped against the old commit."*

| Exit condition | Status |
|---|---|
| A published delta report | **MET** — this document; 3,300 paired games per regime |
| A new default `rules_version` | **MET** — `rules.CURRENT_VERSION = "2026.10"`, verified end to end (§6) |
| A register with no row still stamped against the old commit | **NOT MET** — the twelve rows Phase 5 could have moved are re-executed and three changed; the remaining 87 are triaged, enumerated and open (§9) |

**The headline is not the one the plan expected.** The plan assumed the revival
would move the grading surface enough to need the ceilings, the clamp and the
archetype thresholds re-derived. Measured over 3,300 paired games per regime, two
of those three need nothing, and the ceilings needed correcting for a reason that
has nothing to do with the revival — they were indexed on the wrong dimension and
were equally wrong under the old rule set. The one quantity that genuinely had to
be recalibrated is the one the plan does not mention: **supply-chain transparency,
a 0–100 score that was constant at 40.0 in every one of 3,300 baseline games.**

---

## 0. What Phase 5 changed

| File | Status | What it is |
|---|---|---|
| `backend/tests/stress_harness.py` | new | the Monte Carlo sampler: `RunSpec` sampling, paired execution, `Outcome`, `describe`, `relative_delta` |
| `backend/tests/test_calibration.py` | new, 14 tests | pins the knob layer, the once-only cadence, the recalibrated SCT distribution, and the three constants that did **not** move |
| `backend/tests/test_finale_record_is_storage.py` | new, 13 tests | the defect in §5.2 and its behavioural consequence |
| `backend/rules.py` | extended | `Knob`, `KNOBS`, `RuleSet.calibration`, `rule_value`, `UnknownKnob`; **`CURRENT_VERSION` cut over to `2026.10`** |
| `backend/flag_utils.py` | extended | `FINALE_INPUTS_KEY`, `FINALE_INPUTS_LEGACY_KEY`, `finale_inputs_of` |
| `backend/systemic_risk_engine.py` | modified | the entropy knob and the once-only boost cadence |
| `backend/terminal_valuation.py` | modified | `PATHWAY_MR_HEADROOM`, `max_achievable_mr_for` |
| `backend/round_logic.py` · `router.py` | modified | the finale re-run record moved out of the flag namespace |
| `backend/tests/calibration_sweep.py` | new | the driver behind every figure in this document — sweep, summary, ceilings, isolate, compare |
| `backend/tests/register_check.py` | new | triages the claims register's 99 rows against the current tree (§9) |
| `backend/round_logic.py` (F-2 guard) | modified | a per-run `print` became a log record; the durable signal was always the `dual_form_flags_detected` event key |
| `backend/tests/golden_matrix_harness.py` | refactored | `RunSpec` / `_spec_for` / `drive(spec=…)`, so one driver serves both the covering array and the sampler |
| `backend/tests/golden/matrix/` · `matrix_2026_10/` | rebaselined | one key, at one round, on four paths (§7) |
| `backend/tests/test_rules.py` · `test_option_matrix_golden.py` | modified | the cut-over pins; the matrix flag count 94 → 93 |
| `backend/tests/test_flag_reachability.py` | modified | `_UNREACHABLE_CONSUMERS` re-keyed on the read's SOURCE TEXT instead of its line number (§8) |

Full suite after Phase 5: **2,920 passed, 15 skipped, 0 failed.**

---

## 1. The instrument, and why the covering array could not be it

Phase 0–4 are anchored on a seven-path covering array (`tests/golden/matrix`). It
is the right instrument for *"did the engine move?"* — it is deterministic, it
pins every graded quantity at every round, and a one-cent change fails it. It is
the wrong instrument for *"where should this threshold sit?"*, and Phase 5 began
by getting that wrong: reading seven paths, all seven of which showed an
unchanged M_R, I inferred that M_R was unchanged. It is not. Seven points cannot
describe a distribution, and every one of the seven happened to sit away from the
thresholds in question.

`backend/tests/stress_harness.py` samples instead. It drives the *same*
production sequence as the golden harness — `drive()` is shared, not
reimplemented — over randomised decision paths, ending pathways, investment
ratios and capex levels, and runs each sampled game **twice, once under each rule
set, from the same seed**, so every comparison is paired and the sampling noise
cancels exactly.

```
PATHWAYS      activist_ultimatum · climate_black_swan · stakeholder_revolt
              hostile_takeover · regulatory_shutdown
INVEST_LEVELS 0.1  0.3  0.5  0.7  0.9
CAPEX_LEVELS  0  250k  500k  1M  2M
regimes       black swans off (seeds 1–3) · on (seeds 11–13)
n             550 games per seed  →  3,300 pairs per regime, 6,600 games total
failures      0
```

`run()` records a failure rather than swallowing it, so a crashed game cannot
silently leave the sample and flatter the result. Every figure below is from
`~/audit_scratch/p5/sweep.jsonl`; §10 says how to regenerate it.

**The harness self-checks.** An arm with every switch off and the baseline
calibration reproduces the 2026.09 arm exactly — mean ΔM_R +0.0000, mean ΔTV
+0.00% — so a non-zero reading in any other arm is the arm, not the instrument.

---

## 2. The headline measurement

3,300 paired games per regime. Δ is 2026.10 minus 2026.09 on the same seed.

| | swans OFF (n=1650) | swans ON (n=1650) |
|---|---|---|
| M_R, 2026.09 p05 / p50 / p95 | 0.1500 / 1.1226 / 1.8800 | 0.1273 / 1.0700 / 1.8700 |
| M_R, 2026.10 p05 / p50 / p95 | 0.1500 / 1.1200 / 1.8800 | 0.1300 / 1.0700 / 1.8700 |
| paired ΔM_R mean / p50 / worst | −0.0088 / +0.0000 / −1.1900 | −0.0072 / +0.0000 / −0.9000 |
| paired ΔTV mean / p05 / p95 | −2.08% / −23.13% / +6.30% | −2.11% / −23.04% / +5.90% |
| archetype changed | 57 / 1650 (3.5%) | 84 / 1650 (5.1%) |
| M_R ceiling clamped, 09 → 10 | 13 → 12 | 15 → 15 |
| M_R floor clamped, 09 → 10 | 40 → 40 | 44 → 43 |
| exit multiple at the 18× cap | 319 → 269 | 298 → 260 |
| exit multiple at the 6× floor | 107 → 107 | 99 → 99 |
| SCT at 0 | 0 → 88 | 0 → 80 |
| SCT at 100 | 0 → 0 | 0 → 0 |

Read that as: **the median game does not move at all.** The mean moves because a
minority of games move a lot, and they move for one reason (§3). The tail is
real and is the thing a facilitator has to be told about: p05 of ΔTV is −23%.

---

## 3. Which switch does what

120 sampled specs (seed 7), each arm run against the same 2026.09 baseline. The
control rows are the point of the table: every isolated arm carries the
recalibrated entropy knob, so **a switch's own effect is its deviation from the
knob-only row (+0.22%), not its absolute figure.**

| arm | mean ΔM_R | worst ΔM_R | mean ΔTV | runs ΔM_R < −0.05 |
|---|---|---|---|---|
| CONTROL — all switches off, 2026.09 calibration | +0.0000 | +0.0000 | +0.00% | 0 |
| KNOB ONLY — all switches off, 2026.10 knob | +0.0000 | +0.0000 | +0.22% | 0 |
| `biodiversity_audit_gate_reads_flags` | +0.0000 | +0.0000 | +0.22% | 0 |
| `debrief_reads_option_flags` | +0.0000 | +0.0000 | +0.22% | 0 |
| `fog_of_war_display_noise` | +0.0000 | +0.0000 | +0.22% | 0 |
| `sdg_flag_bonuses_live` | +0.0000 | +0.0000 | +0.22% | 0 |
| `sdg_single_quantity` | +0.0000 | +0.0000 | +0.26% | 0 |
| `sct_flag_boosts_live` | +0.0000 | +0.0000 | +0.11% | 0 |
| `sct_boosts_apply_once` | +0.0000 | +0.0000 | −0.15% | 0 |
| `hard_engineering_pulse_revert_live` | +0.0058 | +0.0000 | +1.18% | 0 |
| **`npc_betrayal_reads_option_flags`** | **−0.0129** | **−0.4250** | **−1.88%** | **6** |
| ALL (2026.10) | −0.0069 | −0.4250 | −1.00% | 6 |

Four switches are exactly the knob-only row: they change what a report or a
display says and touch no graded number, which is what they were designed to do.
`sdg_single_quantity` and `sct_flag_boosts_live` move terminal value by under a
tenth of a point. `hard_engineering_pulse_revert_live` is the only switch that
*raises* M_R, and never lowers it.

**One switch carries the whole grading change**, and it is the one that should:
`npc_betrayal_reads_option_flags` restores the trust scar for a team that denies
and deflects. Before §5.2 was found, this switch measured −0.0392 mean ΔM_R and
−6.96% mean ΔTV; roughly two-thirds of that was a defect, not a mechanic.

`sct_boosts_apply_once` is not orthogonal to `sct_flag_boosts_live` and the table
shows it: −0.15% against a +0.22% control. The 2026.09 reader is not uniformly
blind — `materiality_aligned` is written as a genuine top-level boolean, so it is
visible to the broken reader as well, and it is the one boost that has always
applied. Turning the cadence switch on alone therefore stops *that* boost
repeating. This is stated because the table is otherwise easy to misread.

---

## 4. What needed re-deriving, and what did not

### 4.1 Supply-chain transparency — the one real recalibration

`calc_supply_chain_transparency` is a 0–100 score. Under 2026.09 it took
**exactly one value, 40.0, in all 3,300 games.** Not "rarely moved": one distinct
value. The read that feeds it is the Shape-C defect (`flags.get("flags_set")`,
a key with no writer), so six of its eight boosts had never applied, and the
seventh — `materiality_aligned` — is a top-level boolean that applied in every
round against a −3.0/round entropy. Constant in, constant out.

Turning the boosts on at the old cadence does not fix that; it breaks it the
other way. Each boost re-applying every round makes the score a race to a clamp:

| arm | at 0 | at 100 | clamped | p05 / p50 / p95 |
|---|---|---|---|---|
| 2026.09 baseline | 0.0% | 0.0% | 0.0% | 40.0 / 40.0 / 40.0 |
| boosts live, old cadence (−3.0/round) | 41.5% | 25.5% | **66.9%** | 0 / 15 / 100 |
| boosts live, once-only, −1.0/round | 5.1% | 0.0% | **5.1%** | 0 / 23 / 51 |

Two changes, both derived from the code rather than fitted to the outcome:

**The cadence.** A boost is a one-off event — a completed audit, a deployed
blockchain trace — not a per-round income. `sct_boosts_apply_once` records what
has already been counted in the function's own diagnostic bag, which the engine
already persists and the router already merges back (`engine.py:3707-3708`), so
"have I counted this?" is answerable without new state.

**The entropy knob.** `rules.KNOBS["sct_entropy_per_round"]`: −3.0 under 2026.09,
−1.0 under 2026.10. The band follows arithmetically from the boost table — start
30, positives +56 (20 + 15 + 5 + 8 + 5 + 3), penalties −25 (−10 − 15), decay
10 × entropy:

```
entropy −3.0, once-only :  [30 − 25 − 30, 30 + 56 − 30]  =  [−25,  56]
entropy −1.0, once-only :  [30 − 25 − 10, 30 + 56 − 10]  =  [ −5,  76]
entropy  0.0, once-only :  [30 − 25 −  0, 30 + 56 −  0]  =  [  5,  86]
```

−1.0 keeps decay a real force (−10 over a game, a third of the starting score)
while putting all but the worst outcomes inside the scale. −3.0 with a one-off
cadence would floor-clamp a large share of the population for no pedagogical
reason; 0.0 deletes the decay mechanic the score is named for.

Measured distribution under 2026.10, 3,300 games — min 0.0, max **53.0**, mean
24.05, deciles 5 / 10 / 15 / 20 / 23 / 28 / 31 / 35 / 45:

| band | games | share |
|---|---|---|
| 0 (floor-clamped) | 168 | 5.1% |
| 1–10 | 638 | 19.3% |
| 11–25 | 1086 | 32.9% |
| 26–50 | 1243 | 37.7% |
| 51–75 | 165 | 5.0% |
| 76–100 | 0 | 0.0% |

**Supply-chain transparency is not a display KPI.** This is the part of §4.1 that
matters most and it was nearly missed. The score is an input to the ESG-adjusted
WACC through the nature premium:

```
nature_premium = max(0, biodiversity_dependency × (1 − supply_chain_transparency/100) × 0.02)
```

`systemic_risk_engine.py:37`. With the score frozen at 40.0, `(1 − SCT/100)` was a
fixed 0.60 for every team in every game. With it live and recalibrated the mean is
0.76, so the premium rises, WACC rises, and the Gordon-growth exit multiple falls.
Measured over 3,300 paired games: mean ΔSCT −15.95, mean ΔWACC **+0.00168**. The
nature premium alone predicts **+0.00173** from the seed's mean water dependency
(0.5425) — essentially all of it. Exit multiples sitting at the 18× cap fall from
617 to 529, a 14% drop.

So the SCT recalibration is the one place in this remediation where a "soft" score
reaches the valuation without passing through M_R, and it is why the terminal-value
distribution moves on paths where M_R does not. Register row M-085 is extended
accordingly.

**A residual, stated rather than buried:** the theoretical maximum is 76 and the
observed maximum over 3,300 games is 53, because the positive flags come from
mutually exclusive option branches and no path can hold all six. The top ~45
points of a 0–100 scale are unreachable. That is a property of the boost table,
not of the knob, and correcting it means changing what the boosts are worth —
a content decision outside Phase 5's remit. It is logged in §9.

### 4.2 The published M_R ceilings — indexed on the wrong dimension

`MR_PUBLISHED_CEILINGS` is keyed on the decision paradigm (`base` 1.93,
`jt_scaled` 2.02, `brsr` 1.98). Measurement says the binding dimension is the
**ending pathway**: four of the five pathways run an M_R calculator whose bonuses
sit outside the 1.93 base sum. Analytic maxima, read off the positive terms in
`ending_pathways.py` and confirmed against the function boundaries at :546, :625,
:669 and :731:

| pathway | analytic headroom | components | max pre-clamp M_R observed | n |
|---|---|---|---|---|
| `activist_ultimatum` | +0.00 | no calculator — the platform default | 1.5800 | 651 |
| `hostile_takeover` | +0.60 | 0.25 integration + 0.20 fortress + 0.15 shareholder | 1.7800 | 674 |
| `climate_black_swan` | +0.65 | 0.30 leader + 0.20 adaptation + 0.15 transition | **2.2300** | 626 |
| `stakeholder_revolt` | +0.65 | 0.35 regeneration + 0.15 employee + 0.15 community | **2.0800** | 679 |
| `regulatory_shutdown` | +0.65 | 0.30 exemplar + 0.20 transparency + 0.15 compliance | 1.9300 | 670 |

**99 of 3,300 games scored above the "maximum" the facilitator panel published**
under 2026.09 (90 under 2026.10); 46 scored above even the 2.02 figure. This was
never a revival effect — it was equally wrong before Phase 4 — and it is not
cosmetic: `admin_router` divides a cohort's M_R by this number to report
`mr_efficiency_pct`, so a climate-pathway cohort could be shown an efficiency
above 100%.

`terminal_valuation.max_achievable_mr_for()` now returns
`min(MR_CEILING, base + PATHWAY_MR_HEADROOM[pathway])`. Against it, **zero of
3,300 games exceed their ceiling under either rule set.** The `min` matters: a
ceiling a team cannot reach because the 2.05 clamp stops them first is not a
ceiling, it is a fiction with a decimal point.

This change is **not versioned**, deliberately. It moves no player's score. It
corrects a number the panel reports and the debrief publishes, and versioning it
would preserve a mistake rather than a semantics.

### 4.3 The 2.05 clamp — NOT re-derived

| | ceiling clamped | floor clamped |
|---|---|---|
| 2026.09 | 28 / 3300 (0.85%) | 84 / 3300 (2.55%) |
| 2026.10 | 27 / 3300 (0.82%) | 83 / 3300 (2.52%) |

The clamp binds in under one game in a hundred and the revival moves that by
0.03 points. A clamp that rare is doing what a clamp is for — catching the
outlier — and there is no measurement here that would justify moving it. It
stays at `[0.0, 2.05]`, pinned by `test_calibration.py`.

### 4.4 The archetype thresholds — NOT re-derived

Population split over all 6,600 games:

| archetype | 2026.09 | 2026.10 | move |
|---|---|---|---|
| SAFE_HAVEN | 34.5% | 34.0% | −0.5 |
| FRAGILE_GIANT | 24.4% | 23.8% | −0.6 |
| PRAGMATIC_OPERATOR | 20.2% | 20.2% | 0.0 |
| STRANDED_RELIC | 11.2% | 12.5% | +1.3 |
| REGENERATIVE_TITAN | 8.5% | 7.9% | −0.6 |
| HOLLOW_IDEALIST | 1.2% | 1.6% | +0.4 |

No band moves by more than 1.3 points, and the direction is coherent: slightly
fewer flattering labels, slightly more stranded relics, because one restored
mechanic penalises a specific evasive choice. `_THRESHOLDS` stays at
`{regenerative_titan: 1.8, derisked_safe_haven: 1.2, fragile_giant: 0.8}`,
pinned by `test_calibration.py`.

---

## 5. Two defects the measurement found

### 5.1 A method error in the measurement itself

The first sweep reconstructed pre-clamp M_R by summing `mr_breakdown`. That
double-counts: the pathway calculators write both their individual components
*and* the `pathway_mr_delta` total into the same dict, so on adaptation paths
`adaptation_premium + carbon_transition + climate_leader` were added twice. The
reconstruction reported the 2.05 clamp binding in 14% of games. The engine's own
stamps (`round_logic.py:493-494`, `:3129-3130`) say 0.8%.

Recorded because the correction is the finding: **read the engine's stamp, do not
recompute the engine's arithmetic in the instrument.** `stress_harness.Outcome`
now takes `mr_raw`, `mr_ceiling_clamped` and `mr_floor_clamped` straight from
`active_event_flags`, and all 3,300 pairs were re-swept.

### 5.2 The R10 finale's re-run record was living in the flag namespace

**A sixth defect shape, and the only one found by measurement rather than by
reading.** Appendix B §B.13 names five. This is a sixth: *a storage record parked
in the flag namespace, harvested as flags.*

`_stamp_finale_valuation` must be re-runnable on the closing state (audit F-08 /
SEAM-05) — the finale runs inside `post_tick`, before the round's NPC fines,
agent hits and R10 balance sheet land, so `router.commit_turn` re-runs its
valuation afterwards. To make that replay exact, the R10 handler records the
inputs it resolved. That record carries `all_flags` — a snapshot of every flag in
force at R10 — and `special`, the pathway's config dict. It was written under a
bare key on `active_event_flags`, which **is** the flag namespace, and
`flag_utils.collect_all_flags` recurses into any nested dict whose key is not
underscore-prefixed and harvests every list under a key containing "flag".

Measured on path `all_c` under 2026.10, attributing each detection to the exact
container it came from:

```
fire 1  R2   via 'materiality_ignored'   -> ['materiality_ignored']      (set at R2)
fire 2  R4   via 'r4_flags'              -> ['deny_and_deflect']         (set at R4)
        R4   via 'flags_set_r4'          -> ['deny_and_deflect']
fire 3  R10  via 'finale_inputs'         -> ['deny_and_deflect', 'materiality_ignored']
```

One R4 decision, two trust scars. The third fire was not a cadence bug in the
betrayal mechanic — the mechanic fires exactly once per flag, in the round the
flag is set — it was a storage key that did not follow the namespace's own
convention. The record also contributed `is_healthcare`, `brsr` and every boolean
inside the pathway config as flag names, and in the closing bag it resurrected
flags the round had already cleared (`insolvency_warning`, `phase_transition`,
`micro_strike_triggered`, `distress_detected`, `reflection_required`).

**The fix is the convention the file already states.** `flag_utils.py:30-35`
records, for `_materiality_idempotency`, that an underscore prefix marks a
private state bag as storage, because recursing into them "polluted the flag
namespace with names no writer ever intended as flags." The record now follows
it: `FINALE_INPUTS_KEY = "_finale_inputs"`. `finale_inputs_of()` reads the legacy
key as well and is never written, so a session persisted before this change still
restamps.

**Not versioned, and the evidence is unusually strong.** Re-running the entire
3,300-pair sweep before and after the move: **the 2026.09 arm is bit-identical —
M_R, terminal value and archetype, all 3,300 games, both regimes.** Across the
golden matrix the only 2026.09 movement is the diagnostic `flags` listing at R10
on four paths; every graded quantity — global, score, bus, escalations, the
finale stamps, the terminal reconstruction — is unchanged. M_R recomputed from
the closing bag through `mr_input_from_state` is identical on all seven paths,
and the `carbon_deferred` and `deep_audit_completed` gates are unchanged. The
2026.09 Shape-E branch (`"deep_audit" in str(flags)`) still matches at R10,
because `str()` does not honour the private prefix — bug-for-bug preservation
intact, verified.

What the move was worth, on the same 3,300 paired games:

| | before | after |
|---|---|---|
| mean ΔM_R (swans off / on) | −0.0240 / −0.0217 | **−0.0088 / −0.0072** |
| games with ΔM_R < −0.05 | 192 / 180 | **90 / 80** |
| mean ΔTV | −5.10% / −5.19% | **−2.08% / −2.11%** |
| p05 ΔTV | −34.07% / −33.76% | **−23.13% / −23.04%** |
| archetype changed | 6.8% / 7.4% | **3.5% / 5.1%** |

Roughly half of what looked like the cost of the revival was this defect.

---

## 6. The cut-over

`rules.CURRENT_VERSION` moves from `DEFAULT_RULES_VERSION` to `"2026.10"`. It
governs **new sessions only**, and the compatibility guarantee does not depend on
it: `router.commit_turn:3029` stamps `session_info["rules_version"] or
DEFAULT_RULES_VERSION` and never consults `CURRENT_VERSION`, so a record written
before the flag existed resolves to the baseline whatever the build defaults to.

Verified end to end against a real `create_session`, not asserted:

```
new session rules_version       : 2026.10
resolves to                     : 2026.10
switches ON for a new session   : biodiversity_audit_gate_reads_flags,
                                  debrief_reads_option_flags, fog_of_war_display_noise,
                                  hard_engineering_pulse_revert_live,
                                  npc_betrayal_reads_option_flags, sct_boosts_apply_once,
                                  sct_flag_boosts_live, sdg_flag_bonuses_live,
                                  sdg_single_quantity
sct_entropy_per_round           : -1.0

unstamped legacy record resolves: 2026.09
switches ON for it              : none
sct_entropy_per_round           : -3.0
```

Three tests hold the cut-over (`tests/test_rules.py`):
`test_new_sessions_are_created_on_the_revived_rule_set` pins the value and that
`DEFAULT_RULES_VERSION` is still the 2026.09 compatibility floor;
`test_the_cut_over_did_not_re_grade_a_single_existing_session` pins the four
resolution paths, the unknown-version degradation, and that the router's fallback
is still the constant; `test_an_existing_session_replays_bit_identically_after_the_cut_over`
replays all seven covering paths pinned to 2026.09 against the fixtures and
asserts no switch reads ON for a 2026.09-stamped bag.

---

## 7. Fixture movement, and the rebaseline

Every `(round, key)` that moved, per path, per rule set:

| path | 2026.09 | 2026.10 |
|---|---|---|
| `all_a` | — | R10.escalations |
| `all_b` | — | R10.escalations |
| `all_c` | R10.flags | R10.escalations, R10.flags, R10.global, terminal.finale |
| `legacy_mixed` | — | R10.escalations |
| `distress_c` | R10.flags | R10.escalations, R10.flags |
| `adaptation` | R10.flags | R10.bus, R10.escalations, R10.flags, R10.global, R10.score, terminal.finale, terminal.terminal |
| `regulatory` | R10.flags | R10.escalations, R10.flags |

Under 2026.09 the *only* moving key is `flags`, the harness's own recording of
`sorted(collect_all_flags(aef))` — the listing of what a correct reader sees. It
loses exactly the six names §5.2 identifies. Under 2026.10, escalations move on
every path because the R10 phantom betrayal is gone, and the numbers move on the
paths whose history contained a betrayal flag.

`_MATRIX_DISTINCT_FLAGS` drops 94 → 93. The name that left is
`exit_multiple_ci_haircut`, and it was never a flag: it is a key in the
adaptation pathway's `special` config (`ending_pathways.py:172`) and
`round_logic.py:3082` stamps it as a float. It was visible only through the
record. No other name moved on any path under either rule set.

Both fixture directories were rebaselined with `MURESSONS_REBASELINE_MATRIX=1`
in the same change as the code, which is what the harness's own instructions ask
for.

---

## 8. What Phase 5 did NOT do, and why

* **The 2.05 clamp and the archetype thresholds are unchanged.** §4.3 and §4.4.
  The plan anticipated re-deriving them; the measurement says not to. Changing a
  threshold that 6,600 games say is correctly placed would be motion, not work.
* **No new switch for the betrayal cadence.** The investigation that opened this
  phase's last stretch assumed one was needed. It was not: the mechanic fires
  once per flag per round it is set, and §5.2 was the whole of the anomaly.
  Adding `npc_betrayal_scar_applies_once` would have versioned a defect that had
  already been fixed at its source.
* **The SCT boost table is unchanged**, so the top of that 0–100 scale stays
  unreachable (§4.1). Widening it is a content decision.

One thing Phase 5 did do that the plan does not mention. `_UNREACHABLE_CONSUMERS`
in `test_flag_reachability.py` was keyed on `(file, line number)`, and its stated
requirement is that a MOVE must not break it while a CHANGE must — which is
exactly backwards for a line number. `round_logic`'s anchor churned
3523 → 3567 → 3596 → 3598 → 3607 across Phases 3–5: five edits, none of them
describing a change to the read, each one an invitation to make a red test green
by editing a number. It is now keyed on the stripped SOURCE TEXT of the read, the
way `test_no_stringified_flag_reads.py` already keys its allow-list, with a new
test asserting each anchor matches exactly one line in its file. The four
anchored reads are unchanged.

---

## 9. The affected surface, and the third exit condition

### 9.1 How wide the cut-over actually reaches

The first pass at scoping the register work found the affected rows by searching
claim TEXT for the names of the switched mechanics. That can only find rows that
happen to use those words, and the register says so. Two better instruments were
built to close the gap, and the second is the one that matters.

**By code location.** `tests/register_check.py --versioned` finds the fifteen
`rule_on` / `rule_value` sites in the backend, resolves every quoted fragment in
the register to its CURRENT line (the citations are stamped against `0ad1246`, so
the numbers in the document cannot be tested directly), and reports which rows
cite code inside a rule-gated function. Result: **one row, M-068**, already
re-executed. Wording cannot evade this check — but it only catches rows citing
the gate itself, and M-020 and M-085 are version-dependent because the values
flowing INTO them changed, not because their function is gated.

**By measurement.** `tests/calibration_sweep.py surface` settles it without
enumerating anything: it compares every scalar key in the closing global state,
flag bag and aggregated business units, across paired games. Over 150 pairs, of
**440 distinct quantities**:

| | count |
|---|---|
| differ in value at least once | 142 |
| present under one rule set only | 45 |
| **affected (union)** | **169** |
| not observed to differ | 271 |

The top of the differing list is the causal chain, in order:
`sdg_impact_score` and `sdg_multiplier` (150/150), `supply_chain_transparency`
(147/150), then `terminal_value`, `equity_value`, `price_per_share`,
`ev_over_revenue`, `price_to_book`, `cost_of_capital`,
`exit_multiple_wacc_used` — and from there into `corporate_treasury`,
`total_opex`, `terminal_ebitda`, `historical_ebitda`, `tco2e_emissions`,
`carbon_cost`, `ncd_liability_usd` and the per-BU `opex_base`,
`revenue_base`, `carbon_intensity` and `absolute_emissions`. The keys present
under 2026.10 only are the revived mechanics themselves —
`hard_engineering_pulse_reverted` and its two message keys, in 52 of 52 games
where the R5 pulse was taken.

**So the honest rule for the register and the manuscript is not "does this claim
name a switch".** It is: *does this claim quote a quantity on the affected list?*
Because supply-chain transparency feeds the ESG-adjusted WACC through the nature
premium, and the betrayal scar feeds reputation and opex, the cut-over reaches
about 38% of the model's closing state — including numbers whose claims mention
none of it.

One caveat stated plainly: 150 paired games is a sample. A quantity that never
differed is evidence of invariance, not proof, and the tool prints the sample
size alongside every count for that reason.

### 9.2 The third exit condition — partly met, precisely scoped

*"A register with no row still stamped against the old commit"* is **not met**,
and `docs/verification/register_reexec.md` now says so in its own words rather
than by omission. What Phase 5 did do:

* Built `backend/tests/register_check.py`, which matches every
  `backend/file.py:LINE` citation in the register's 99 rows against a
  whitespace-normalised view of the current file. Result: **18 EXACT, 45 MOVED
  (code moved beneath the citation, the claim did not), 34 needing a human
  re-read, 2 section headers.**
* Identified the twelve rows whose CLAIM names a quantity, flag or mechanic Phase
  5 moved, and re-executed all twelve by hand against both rule sets. Three
  changed: **M-020** (M_SDG is now version-dependent), **M-068** (the betrayal
  scar — and one of its findings was wrong at the old commit too: the register
  argued `materiality_ignored` could not reach the scar, and measurement says it
  always has, because the events bag and `active_event_flags` are one object),
  **M-085** (the nature premium's SCT input stopped being a constant).
* Measured the affected surface exhaustively (§9.1) rather than by enumerating
  switches, so the register has a checkable rule instead of a word search.
* Recorded, in the register itself, that **every row is now potentially two
  claims** — one per rule set — which is a change to the register's contract, not
  a refresh of it.

The 45 drifted citations are deliberately NOT rewritten mechanically. A generated
edit to 45 rows of a verification document is exactly the kind of change that
should be reviewed line by line, and the checker reproduces the list on demand.

Passages and rows still open, including the ones this phase added:

| item | what changed | status |
|---|---|---|
| 45 register rows with drifted citations | line numbers only; the claims stand | ENUMERATED, not rewritten |
| 34 register rows with a citation that no longer resolves | real drift from Phases 0–4, plus checker false positives | NEEDS RE-READ |
| Rows describing a switched mechanic without naming it | the twelve were found by claim text; that sweep can miss | OPEN |
| Refuted row 12 — the NCD → WACC chain (Part 2 entries 2 and 17) | pre-existing, unaffected by Phase 5 | OUTSTANDING |
| Share count: code `TV_SHARES_OUTSTANDING = 6_500_000` vs the book's 100,000,000 | per-share figures in Ch 14 / Ch 18 are off by ~15× | PRINT BLOCKER |
| R5 cyclone: fires when the roll is **below** 0.75, i.e. 75% of the time; documented as 25% | documentation contradicts the code | PRINT BLOCKER |
| Student Manual: synergy "decays 2%/round"; the engine uses 5% | documentation contradicts the code | OUTSTANDING |
| Published M_R ceilings quoted in the manuscript as 1.93 / 2.02 / 1.98 | §4.2 — the pathway headroom must be quoted alongside, or the figures read as maxima they are not | NEW, from this phase |
| Supply-chain transparency described as a moving score | §4.1 — it was constant at 40.0 for every session graded under 2026.09 | NEW, from this phase |
| Any passage quoting an M_R efficiency percentage | §4.2 — the denominator changed | NEW, from this phase |

---

## 10. Reproducing this

Everything below runs from `backend/`. The sampler is
`tests/stress_harness.py`; the driver that produced every figure in this document
is `tests/calibration_sweep.py`, which is in the repo for that reason. It is not
a test and is not collected as one.

```
# the covering array, both rule sets
python3 -m pytest tests/test_option_matrix_golden.py -q

# the calibration pins, the cut-over pins, and the §5.2 regression
python3 -m pytest tests/test_calibration.py tests/test_finale_record_is_storage.py \
                 tests/test_rules.py -q

# the sweep: ~42 s per 550 pairs, append-only, so a killed run costs only the
# games it had not written yet. 3,300 pairs per regime.
for s in 1 2 3;    do python3 tests/calibration_sweep.py sweep $s 550 noswans; done
for s in 11 12 13; do python3 tests/calibration_sweep.py sweep $s 550 swans;   done

python3 tests/calibration_sweep.py summary    # §2, §4.1, §4.3, §4.4
python3 tests/calibration_sweep.py ceilings   # §4.2
python3 tests/calibration_sweep.py isolate    # §3, including both control arms
python3 tests/calibration_sweep.py compare <before.jsonl> <after.jsonl>   # §5.2
```

The sweep writes `tests/.calibration_sweep.jsonl` (~4 MB), which is gitignored:
it is evidence, not source, and it regenerates in about four minutes. `compare`
takes two such files and requires the same seeds in the same order — it checks
that and refuses otherwise, because an unpaired comparison of two Monte Carlo
samples would report sampling noise as an effect.
