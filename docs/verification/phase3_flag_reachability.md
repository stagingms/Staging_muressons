# Phase 3 — the read probe, the covering array and the reachability test

Repo: `muressons-sim`, branch `fix/audit-remediation-wave3-20260906`, against
`0ad1246` plus the Phase 0–2 scaffolding. Date: 2026-09-08.

Phase 3 of `Muressons_Dead_Flag_Remediation_Plan.docx`: *"Build the read probe,
the covering-array harness and the bidirectional reachability test … Exit
condition: the test fails for exactly the flags Appendix B names, and for nothing
else. That symmetry is the acceptance criterion."*

---

## 0. What was built, and the one design decision that mattered

| File | Status | What it is |
|---|---|---|
| `backend/tests/golden_matrix_harness.py` | rewritten | The production commit sequence, seven paths, one driver |
| `backend/tests/flag_probe.py` | new | Read probe (4 channels) + differential reachability engine |
| `backend/tests/test_flag_reachability.py` | new | 63 tests: forward, reverse, symmetry, diagnosis, fault injection |
| `backend/tests/test_option_matrix_golden.py` | extended | 16 → 29 tests; fixtures rebaselined |
| `backend/tests/golden/matrix/*.json` | rebaselined + 3 new | 7 fixtures |
| `backend/flags/registry.py` | 1 entry corrected | `hard_engineering` LIVE → DEAD_DEFECT |
| `backend/tests/test_flags_package.py` | 2 ratchets updated | 18/11 → 17/12, with the reason |

**The decision.** The plan sketched the probe as a hook on `FlagSet.has()`. That
could not work, and the reason is worth recording rather than quietly routing
around. Phase 1 deliberately did **not** migrate any consumer onto `FlagSet` —
migrating a raw read to the flattened reader turns a dead mechanic ON, and a
behaviour change belongs in the reviewed phase, not the scaffolding phase. So
nothing in the engine constructs a `FlagSet`, and a probe hooked to it would
observe exactly nothing: every LIVE assertion would fail. "Fails for everything"
is not "fails for exactly the 22", so the exit condition itself rules that design
out. The probe instruments the containers the current consumers actually read.

---

## 1. The harness was not driving production, and it mattered

Phase 0 shipped the matrix with `pre_tick`, the FLAG-3 `flags_set` attach and the
session-config stamps omitted, and said so in its docstring. Phase 3 made those
omissions load-bearing: **a consumer the harness never executes is
indistinguishable from a consumer that cannot fire**, and that is the one
distinction the probe exists to draw. Seven steps were added. Each was measured
before it was adopted.

| Step | Router line | What it hid |
|---|---|---|
| `pre_tick` + server-derived crisis severity | `:2894`, `:2906` | `round_logic._pre_r4_contagion` is the ONLY reader of `electronics_blindspot` and `deferred_audit`. Both looked dead. |
| attach the option's `flags_set` to the decision | `:2946-2960` | Measured on all_c without it: `apply_decision_sentiment` moved **0 stakeholders in all ten rounds**. With it, `carbon_deferred` moves 1 at R3, `deny_and_deflect` 2 at R4, `quiet_patch` 2 at R6 — Appendix B's three "LIVE (sentiment only)" flags. The harness was reproducing inside the test suite the very bug FLAG-3 fixed in production. |
| stamp `difficulty_tier` and the `_systemic_toggles` bag | `:2963`, `:2977-2988` | The bag is what `systemic_risk_engine.systemic_toggle_on` reads. Building it wrong (all-True instead of letting `pedagogical_overrides` win) turned black swans back on and moved all_c by ~103M — caught by measurement, not by inspection. |
| `_forward_persistent_flags` | `:3121` | The seven session keys the post-tick engines read. |
| `events.update(post_events)` | `:3141` | **Everything the R10 finale computes.** `post_tick` returns its extra events and Phase 0 discarded the return value, so the finale ran and then vanished. |
| `events.update(new_engine_events)` | `:3174` | The engines' own event record. |
| `restamp_finale_valuation` | `:3182-3186` | Audit F-08 / SEAM-05: re-runs the finale's valuation on the CLOSING state. |

**Consequence of the last three.** The fixtures had been pinning
`terminal_snapshot`'s own reconstruction of M_R rather than the engine's. The
reconstruction is materially wrong: on all_c it computes 1.07 against the
engine's 0.92; on distress_c it grades a `fragile_giant` where the engine grades
a `stranded_relic`. The trace now records both, and the "KNOWN LIMITATION" about
the fixed exit multiple is closed for the finale numbers.

### The rebaseline is attributable, not asserted

`drive(production_steps=False)` drops exactly those steps and holds crisis
severity at the financial oracle's flat 20.0. In that mode the harness reproduces
the Phase 0 fixtures **byte for byte on all four original paths**, and
`test_harness_reproduces_the_financial_oracle_when_read_its_way` still reproduces
`golden/financial_trace.json`. So the whole fixture delta belongs to steps the
module can name. Held by
`test_oracle_compatibility_mode_drops_exactly_the_named_steps`, which also
asserts the load-bearing part: the four original paths gain 33 flags and lose 6,
and **none of the 39 is a decision flag** — the covering array still means what
its name says.

### Paths: 4 → 7, distinct flags 53 → 94

- `distress_c` — server-derived crisis severity moved all_c from −19,379,984 to
  +29,611,117, and the whole distress cascade went with it (`survival_mode`,
  `cfo_austerity_active`, `dividends_clamped`, `dividend_ratchet_triggered`,
  `distress_detected`, `phase_transition`, all previously seen only on all_c at
  R9–R10). Keeping the decision paths in the normal operating band is right — the
  financial oracle's own calibration note argues it — so the cascade moved to a
  directed case on the spend profile that note measured as insolvent by round 4.
- `adaptation` and `regulatory` — the **ending pathway is session configuration**
  (`round_logic.py:721`, `:2653`), not a decision. Four of the five M_R pathway
  calculators therefore ran for no path at all, and the flags they read looked
  dead for a reason that had nothing to do with the flags. `adaptation` is also
  the only path that takes R3 option_a *with* R5 option_b, which §B.14.1's
  Adaptation Premium requires and no uniform path can hold at once.

---

## 2. The probe: two channels, because one is not enough

**The differential is the verdict.** Scrub a flag out of existence, re-run the
paths that raise it, diff the whole trace. Shape-agnostic, and it is the only
thing that can see the sentiment consumers, which iterate the namespace in bulk
and perform no keyed read at all. A keyed-read probe alone would report
`carbon_deferred`, `quiet_patch` and `deny_and_deflect` dead — the exact false
alarm the exit condition forbids.

Scrubbing is sound because `rng_util.event_seed` hashes only
`flags["stochastic_seed"]`, never the dict, and every event draws from its own
named stream; removing a flag cannot shift another mechanic's rolls. It is
airtight rather than staged: a `ScrubbingDict` lies about the flag on every read
including `.items()`, so `collect_all_flags` cannot find it either, and a config
patch stops the option layer writing it at all. A missed window would produce a
**false dead**, the one error class this phase cannot tolerate, so the
differential *raises* rather than reports when a scrubbed flag is still visible.

**The read probe is the diagnosis.** Recording containers on four boundaries —
`active_event_flags`, `ctx.events`, `collect_all_flags`'s returned set, and
`calculate_mr`'s flags argument — recording every keyed read of a registered flag
name with its `file:line` and whether it returned truthy. That is what separates
`READ_NEVER_TRUE` (a consumer exists and the storage format hides it → REVIVE)
from `NOT_READ` (no consumer at all → RETIRE or INERT). Appendix B's §4 triage
was done by hand; this derives it.

The probe is observation-only, and that is asserted: every instrumented path
reproduces its fixture exactly. It is not hypothetical care — the first version
wrapped `new_global["active_event_flags"]` and the events bag as two objects.
Production makes them **one** (`engine.py:4472`, `:4905`), and de-aliasing them
moved `group_reputation` 58 → 63 at R2 on every path.

A **bulk census** enumerates the blind spot rather than leaving it implied: every
site that iterates the namespace instead of asking it a keyed question.

---

## 3. The result

The probe reaches its verdicts by execution and reproduces Appendix B
independently — **30 of 32** in-matrix round flags agreed on the first complete
run, and the two disagreements are both real findings rather than probe error.

| Verdict | Count | Flags |
|---|---|---|
| LIVE, confirmed by keyed read | 10 | `ai_monetised`, `community_fund`, `deferred_audit`, `early_decarboniser`, `electronics_blindspot`, `electronics_water_priority`, `ethical_ai_overhaul`, `insurance_only`, `managed_transition`, `synergy_unlock` |
| LIVE, confirmed only by the differential | 5 | `carbon_deferred`, `deep_audit_completed`, `deny_and_deflect`, `nature_based_resilience`, `quiet_patch` — the bulk-consumed and pathway-conditional ones |
| DEAD, `READ_NEVER_TRUE` → **REVIVE** | 5 | `supply_chain_disruption_risk`, `remediation_active`, `epr_program`, `circular_redesign`, `hard_engineering` |
| DEAD, `NOT_READ` → RETIRE / INERT / PILLAR | 11 | `materiality_exceptions`, `ceo_only_signoff`, `green_bond_active`, `pr_containment`, `waste_to_energy`, `water_efficiency_all`, `desalination_built`, `immediate_closure`, `resist_integrate`, `spinoff`, `divest` |
| SCOPED to another paradigm | 1 | `full_materiality_alignment` |

Four defect shapes were observed at their exact lines, each read many times and
never once truthy, and each is now pinned by a test that fails when it is fixed:

| Site | Shape | Flags hidden |
|---|---|---|
| `engine.py:4369` | A — container mismatch | `deep_audit_completed` |
| `engine.py:2122` | B — wrong source dict | `circular_redesign`, `community_fund`, `ethical_ai_overhaul` |
| `systemic_risk_engine.py:80` | C — guessed key name | `deep_audit_completed`, `supply_chain_disruption_risk`, `deny_and_deflect`, `remediation_active`, `circular_redesign`, `epr_program` |
| `round_logic.py:3523` | **D — wrong generation** (new) | `hard_engineering` |

### The two corrections to Appendix B

1. **`hard_engineering` is DEAD, not LIVE** (§B.6, §B.16 #14). Its only consumer,
   `_revert_r5_hard_engineering_pulse`, reads the post-tick flag bag, which holds
   this round's events plus seven session keys — never `r5_flags`. Every other
   flattened reader in `round_logic.py` uses `previous_flags`; `:3522` is the
   single exception, and that asymmetry is the proof. Measured at R7 on all_a the
   function sees `['greenwashing_checked', 'technology_lockin_penalty']` and the
   +3 carbon-intensity construction pulse is permanent — the exact defect
   FLAG-8 / WP-23 believed it had fixed, which swapped the reader and left the
   container wrong. Verified without the probe by
   `test_hard_engineering_reads_the_wrong_generation_of_the_flag_bag`.
   `impact_engine.py:93` takes the R5 resilience factor from the option's
   **impacts**, keyed by choice, so there is no second consumer to fall back on.
   The Phase 2 registry entry has been corrected in the same pass.

2. **`full_materiality_alignment` is live in `advanced_climate` only** (§B.16 #4).
   `engine.py:3763` opens `if ctx.decision_paradigm == "advanced_climate":` and
   the consumer is inside it at `:3787`. §B.3 names the paradigm; the summary row
   did not, which is what made the flat "LIVE" misleading. Declared SCOPED rather
   than dead, and the declaration is checked rather than asserted:
   `test_the_paradigm_scoped_flag_is_live_behind_its_gate` runs the same tick
   under both paradigms and measures NCD forgiveness 1.23 → 1.54 with the flag
   under `advanced_climate`, unchanged under `legacy_abc`.

### The exit condition

`test_the_naive_assertion_fails_for_exactly_the_dead_set` applies the rule a
correct engine would satisfy — every flag a round declares must change something
— and asserts the failure set equals the specification's dead set exactly. One
too many is a false alarm and the probe cannot gate a fix; one too few is a blind
spot and it cannot find one. It passes.

### Fault injection — the correctness test for the probe

Repairing the single membership test at `systemic_risk_engine.py:80` (shape C)
revives **exactly** the three flags whose only consumer is that line —
`supply_chain_disruption_risk`, `remediation_active`, `epr_program` — and
disturbs no other verdict in either direction. A probe that cannot tell a fix
from no fix would make every verdict above worthless.

### A calibration finding that Phase 5 needs

With shape C repaired, supply-chain transparency runs
`27, 24, 21, 8, 3, 0, 0, 0, 0, 0` on all_a and
`27, 44, 61, 78, 100, 100, 100, 100, 100, 100` on legacy_mixed. It is a 0–100
score with −3/round entropy and boosts up to +20, and **it is not calibrated for
those boosts to apply**: the uniform-A path floors by R6 and the legacy path
ceilings by R5. `circular_redesign`'s +5 changes nothing for that reason alone,
which is why it does not appear in the revival set above. §5 of the plan argues
that reviving these flags changes every score because transparency feeds the
nature premium, WACC and the exit multiple; this is the number behind that
argument, and it says recalibration is part of the revival rather than a
follow-up to it.

---

## 4. State of the suite

Full backend suite, five batches: **2,815 passed, 15 skipped, 0 failed.**
`tests/test_flag_reachability.py` 63 passed; `tests/test_option_matrix_golden.py`
29 passed; `tests/test_flags_package.py` 15 passed.

Only one tracked file has been modified across Phases 0–3
(`backend/tests/test_flag_sweep.py`, +7/−1 from Phase 2). Everything else is new.

## 5. Named follow-up, not silently half-done

- **Pillar and healthcare paradigms.** The matrix is `legacy_abc` only. The five
  case-(iii) flags (`circular_redesign`, `waste_to_energy`, `water_efficiency_all`,
  `desalination_built`, `immediate_closure`) are live in pillar mode and dead
  here; they are ruled PILLAR in the expectation table and not asserted for
  pillar. Driving `aggregate_pillar_decisions` +
  `_apply_pillar_aggregate_impacts` is a bounded addition — the R10 option keys
  match — and it is the natural next widening.
- **The registry's `scope` field means "declared in", not "applies in".** Plan
  §3.2 specified the latter. The probe now carries the paradigm dimension in its
  report instead; reconciling the field belongs with the Phase 4 migration.
- **Appendix B's arithmetic.** §B.13's table now lists eight locations; the plan's
  §1 says "six live consumers that cannot fire", and the "22 findings" figure is
  16 + 6. The counts should be reconciled in one pass rather than drifting.
- **`terminal_snapshot`'s reconstruction** is retained only for the reader
  divergence test and the financial-oracle comparison. It uses the fixed exit
  multiple and passes neither `hr_investment_rounds` nor `pathway_bonuses`; the
  fixtures now carry the engine's own finale alongside it, and the reconstruction
  should be retired once those two tests are re-based.
