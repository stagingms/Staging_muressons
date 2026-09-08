# Phase 4 — triage, revival behind versioned rules, and the rulings

Repo: `muressons-sim`, branch `fix/audit-remediation-wave3-20260906`, on top of the
Phase 0–3 work. Date: 2026-09-08.

Phase 4 of `Muressons_Dead_Flag_Remediation_Plan.docx`: *"Apply §4. Revivals go
behind RuleSet switches, default OFF, so Phase 0 fixtures keep passing. Retire the
vestigial flags. Write the rulings. Fix the four stale comments. Exit condition:
probe green under 2026.09 with switches off, and green under 2026.10 with them
on."*

Both halves of the exit condition hold. **The compatibility guarantee is measured,
not asserted: under 2026.09 all seven matrix paths are byte-identical to the
pre-Phase-4 fixtures**, the only difference being one observability key the probe
needed (`sdg_index`).

---

## 0. What was built

| File | Status | What it is |
|---|---|---|
| `backend/rules.py` | new | `rules_version`, six named switches, the reader, the fallback rules |
| `backend/tests/test_rules.py` | new | 16 tests, mostly about the fallback paths |
| `backend/tests/golden/matrix_2026_10/` | new | 7 fixtures pinning the revived semantics |
| `systemic_risk_engine.py` · `engine.py` · `round_logic.py` · `npc_stakeholders.py` · `autonomous_agents.py` · `ceo_interview.py` · `biodiversity_engine.py` · two side tracks | modified | one rule-gated read each |
| `router.py` · `database.py` · `database_memory.py` | modified | stamp and persist the version |
| `flags/registry.py` | schema + rulings | `DEPRECATED`, `removes_at`, `revived_in`; 8 rulings written |
| `round_configs.py` · `terminal_valuation.py` | comments | the four stale comments §4.4 names, plus a fifth |

`rules.py` enforces two rules on itself, and both are the lesson of the defect it
remediates. **An unknown version resolves to the baseline, never to "everything
on"** — a session pinned to a version this build does not know must not be
silently re-graded, and it must not raise either, because a classroom is sitting
in front of it. **An unknown switch raises.** `systemic_risk_engine.py:80` guessed
a key name, guessed wrong, returned falsy for a year and passed every test; a
rules layer that repeated that mistake would be an unusually poor joke.

---

## 1. Verification changed §4 materially, in five places

Every claim in §4 was re-read against HEAD before any code moved. Five did not
survive.

**1. The SDG revivals move no graded number.** §5.1 says the two SDG bonuses "move
the SDG index, which moves M_SDG, which multiplies terminal value directly". They
do not. `calc_sdg_impact` returns `sdg_index`, whose only consumers are one event
key and a narrative line (`engine.py:4534`). M_SDG comes from
`terminal_valuation.calculate_sdg_multiplier`, which reads a **different
quantity** — `sdg_impact_score`, written only by the Corporate SDG side track
(`side_tracks/corporate_sdg/track.py:310`). The two have never been connected.
The revival changes the report a team is shown, and nothing else. That removes it
from Phase 5's recalibration scope entirely.

**2. The fog-of-war revival is not a revival.** Appendix B §B.13 records the
`deep_audit_completed` read at `engine.py:4369` as hiding a "Fog-of-War exemption
in R1-R2 (±10% noise on NCD / SLO / governance)". There is no such mechanic:
`ctx.events["fog_noise"]` is computed and **never read** — not by the backend, and
not by the frontend, where the only references are a key in a "don't render raw"
list and two unrelated tunables. `fog_of_war_active` drives one banner in
`EngineEventsPanel.js`. So the flag's exemption gates a UI banner and the
generation of three numbers that are then discarded. "Reviving" it would mean
implementing a mechanic that was never written, which is not remediation. Recorded
as a correction to Appendix B; no switch, no code change.

**3. `divest_all` does not belong in the flag registry.** §4.2 says its inert
ruling "belongs in the registry as DEPRECATED, not in a test allow-list". It is
not a flag: it is an **impacts key** (`round_configs.py:787`), so the flag registry
has no jurisdiction over it and `tests/test_engine_invariants.py`'s allow-list is
the correct home. Recorded in `divest`'s ruling.

**4. There is a fifth defect shape, and it is the worst one.**
`biodiversity_engine.py:442` reads

```
audit_active = "deep_audit" in str(events.get("active_event_flags", {}))
```

— string containment over the **repr of a nested dictionary**, against a name no
configuration declares (the flag is `deep_audit_completed`). Shapes A–D always
return False, so their mechanic is simply absent. **This one fails open.**
Measured on the deep-audit paths it is True at exactly three rounds, for three
different reasons, and False in between:

| Round | Why it matched |
|---|---|
| R1 | the repr of the `r1_flags` **list**, `"['deep_audit_completed']"` |
| R4 | the **key** `deep_audit_protected` — a pre_tick pre_event, a different flag |
| R10 | inside the stringified `finale_inputs` blob |

Turning the switch on therefore also turns the species-risk gate **off** at R4 and
R10. It is a behaviour change in both directions, which is why it is versioned
like the rest rather than fixed outright.

**5. The transparency response reaches further than the terminal.** The switch's
first blast-radius note said "nature premium → WACC → exit multiple → terminal
value". Measured on `all_c`, it also moves the in-game economy: WACC rises
0.0666 → 0.0684, and by R6 a **different escalation fires** — 2026.09 takes an NPC
enforcement fine of −6,844,448 where 2026.10 takes an autonomous-agent event of
−8,374,695 — carrying OPEX up about 22% and the debrief ESG index from 57.49 to
39.60. Cost of capital is not a leaf. Phase 5 must not scope its recalibration to
the terminal decomposition alone. The declaration in `rules.SWITCHES` was corrected
to say so.

---

## 2. The six switches

All default OFF. `rules.CURRENT_VERSION` stays at the baseline: Phase 4 wires the
mechanics, Phase 5 decides whether to enable them, and a test fails the moment
that line moves without the recalibration behind it.

| Switch | Shape | What it moves | Graded? |
|---|---|---|---|
| `sct_flag_boosts_live` | C | six option flags reach the Supply Chain Transparency score | **Yes, and widely** — see §1.5 |
| `sdg_flag_bonuses_live` | B | SDG 1 / 12 / 16 bonuses reach the SDG Impact Report | No — report only |
| `hard_engineering_pulse_revert_live` | D | the R5 +3 carbon-intensity construction pulse is reversed at R7 | Yes |
| `npc_betrayal_reads_option_flags` | C ×2 | `deny_and_deflect` triggers the NPC / agent trust scar | Only when the facilitator's `stakeholder_memory_enabled` toggle is also on — it defaults off, so this switch alone does nothing |
| `debrief_reads_option_flags` | A | CEO-interview `ethical_reasoning` and its citations; two side-track seeds | Debrief and side tracks |
| `biodiversity_audit_gate_reads_flags` | E | the species-risk audit gate stops matching substrings | Yes, in both directions |

Two details worth keeping.

The 2026.09 branch of the transparency reader is a **per-flag membership test on
the dict**, not a precomputed set. Collapsing it would be behaviourally identical
and would make the defect invisible to `tests/flag_probe.py` — which is the only
thing that can tell anyone it is still broken. The first attempt did collapse it,
and the Phase 3 reachability test caught the lost observability immediately.

The SDG revival also feeds the round's **own** decision flags into the report.
`_apply_option_flags` does not write `r{N}_flags` until post_tick, so a report
computed in the tick would have shown a team an SDG 12 score that ignored the
Circular Redesign they had just taken and only caught up a round later. The
decision already carries its option's flags for exactly this reason
(`router.py:2946-2960`, FLAG-3), and the stakeholder-sentiment bridge reads them
the same way.

---

## 3. The exit condition

`tests/test_flag_reachability.py` now runs the whole probe under both rule sets.

- Under **2026.09** every switch is off and every flag Phase 4 revives still reads
  dead — `test_the_baseline_rule_set_revives_nothing`. That is what lets a past
  cohort's score stand.
- Under **2026.10** exactly five flags come back, and exactly the five declared:
  `supply_chain_disruption_risk`, `remediation_active`, `epr_program` (all three
  from the transparency read), `circular_redesign` (via the SDG report — its +5
  transparency is absorbed by the clamp on every path that raises it) and
  `hard_engineering`. Nothing else moves, and nothing is lost —
  `test_the_revived_rule_set_revives_exactly_the_declared_set`.

The eleven flags still dead with every switch on are dead for reasons that survive
the revival, and `test_the_still_dead_flags_are_dead_for_a_reason_that_survives_the_revival`
holds each to its disposition: four ruled DEPRECATED, three INERT_BY_DESIGN, four
live in pillar mode only.

The golden matrix carries a fixture set per rule set, so the revived semantics are
pinned too — an unpinned "new rules" branch would be exactly the unguarded state
this whole exercise is about — and
`test_the_revivals_move_something_and_only_the_right_things` asserts that the two
sets differ only in quantities a switch declares.

---

## 4. The rulings

`FlagSpec` gained two fields and the registry a fifth status.

**`DEPRECATED` + `removes_at`.** Deprecation is not deletion, and the distinction
is the point: dropping a declared flag while cohorts are in flight changes what a
replayed session's `r{N}_flags` contains even when no number moves. Four flags —
`resist_integrate`, `spinoff`, `divest`, `green_bond_active` — are ruled
DEPRECATED with `removes_at="2026.10"`, stay declared, and are held there by
`test_a_deprecated_flag_is_still_declared`. `green_bond_active` carries the note
that retirement is the default disposition and not the only one: moving the Green
Bond's pricing onto the flag named after it would be better design and would make
the Round 3 case teachable, but it is a behaviour change and belongs with the
cut-over. The date forces a decision rather than deferring it.

**`revived_in`.** The five revived flags keep `status=DEAD_DEFECT` and carry
`revived_in="2026.10"`, because while `CURRENT_VERSION` predates the revival the
flag **is** dead for every session anyone is playing. The field is Phase 5's
cut-over filter: it turns "which statuses change when we flip the version" from an
investigation into a query.

**Dated INERT_BY_DESIGN rulings** for `materiality_exceptions`, `ceo_only_signoff`,
`pr_containment` and `turnaround_restructuring`, each superseding the undated
2026-09-01 taxonomy entry and each now confirmed by execution rather than by a name
sweep. `turnaround_restructuring`'s ruling carries a correction: the option's own
description says it "Sets turnaround_restructuring flag, enabling Phase 2
transition", and it enables nothing — `turnaround_engine` keys its phase machine
off `turnaround_phase`, a string state it writes itself, and has never read the
flag.

Registry movements, all reviewed: LIVE 17 (unchanged), DEAD_DEFECT 12 → 9,
INERT_BY_DESIGN 156 → 155, UNVERIFIED 100 (unchanged), DEPRECATED 0 → 4. Total 285.

---

## 5. The stale comments

All four §4.4 names were verified still wrong at HEAD, and a fifth was found in the
same docstring.

| Location | Was | Is |
|---|---|---|
| `round_configs.py:147` | "full_materiality_alignment is a choice marker with no consumer" | consumed at `engine.py:3787`, in `advanced_climate` only — measured NCD forgiveness 1.23 → 1.54 |
| `terminal_valuation.py:155`, `:217` | synergy_unlock set by R7 option_c "Resist & Integrate" | R7 option_c is **Waste-to-Energy Partnership**; Resist & Integrate is R10 option A |
| `terminal_valuation.py:33`, `:398` | "100 million shares" | the config ships **6,500,000** — a 15× error in every per-share figure read from it |
| `round_configs.py:529` | synergy boost "harmonised to match M_R +0.30" | the M_R premium is **+0.15** since STRAT-010; they are different quantities and are not meant to match |
| `terminal_valuation.py:149` (**not in §4.4**) | synergy "boosted +0.35 by R7 option_c Resist & Integrate" | **+0.30**, and by Waste-to-Energy — wrong magnitude *and* wrong option |

---

## 6. State of the suite

Full backend suite, six batches: **2,865 passed, 15 skipped, 0 failed.**
`test_rules.py` 16, `test_flag_reachability.py` 71,
`test_option_matrix_golden.py` 67, `test_flags_package.py` 19.

The AST lint earned its place during this phase: renaming
`all_flags.get("deep_audit")` to the real flag made a **pre-existing** raw read
visible to the detector for the first time — the old name was not registered, so
nothing could see it. It is baselined with that explanation rather than silently
added.

---

## 7. Named follow-up

- **Phase 5 owns the cut-over**, and its scope is now smaller and better measured
  than the plan assumed: the SDG revivals need no recalibration at all, and the
  transparency revival needs more than the terminal decomposition. The measured
  inputs are in `rules.SWITCHES[...].blast_radius` and in the two fixture sets.
- **Supply-chain transparency is not calibrated for its own boosts.** With the
  switch on it runs `27, 24, 21, 8, 3, 0, 0, 0, 0, 0` on the uniform-A path and
  `27, 44, 61, 78, 100, …` on the legacy path: a 0–100 score with −3/round entropy
  and boosts up to +20 reaches a clamp either way. Recalibration is part of the
  revival, not a follow-up to it.
- **`collect_all_flags` silently drops a boolean whose key contains "flag"**
  (`flag_utils.py:36-40` routes any such key down the list/string branch). No
  declared or registered flag name contains the substring today — checked — so
  nothing is affected, but a future flag named `red_flag_raised` would be
  invisible as a top-level boolean.
- **The pillar and healthcare paradigms remain out of the probe's scope**, so the
  four pillar-only flags are still ruled by inspection rather than by execution.
- **The `deep_audit_completed` side-track and CEO-interview revivals are not
  probe-verified**, because the matrix drives neither. Each has a direct test
  instead, and that difference is stated rather than smoothed over.

---

# Addendum — resolving the five findings (2026-09-08)

§1 recorded five claims in the plan that verification falsified. All five are now
resolved. Two were design decisions, taken; three were mechanical. Resolving them
falsified two more of my own claims, both caught by a test written in the same
pass — which is the point of writing it.

## A. The SDG quantities are unified — `sdg_single_quantity`

The simulation carried two SDG numbers that had never been connected: `sdg_index`
(0–100, recomputed every round from BU metrics across all 17 goals, and graded
nothing) and `sdg_impact_score` (−11..105, written only by the Corporate SDG side
track, and the sole input to M_SDG). For any cohort that did not play the optional
track, M_SDG was 1.0 and the whole SDG dimension was inert — while a full SDG
report sat beside it doing nothing.

Under 2026.10 there is one quantity. The side track folds into the index at
`config.SDG_TRACK_WEIGHT` per point — additive, after the aggregate, clamped to the
0–100 the index already lives in, so a track-less session's index is untouched.
M_SDG is then computed from the index against a **neutral point**:

```
M_SDG = 1 + (sdg_index − SDG_INDEX_NEUTRAL) / 100 × SDG_MULTIPLIER_COEFF
```

The neutral point is the whole safety argument. The index is ~73.5 for a team that
has done nothing — measured identical on six of the seven matrix paths at R1 — so
feeding it to the old zero-anchored formula would multiply **every** session's
terminal value by about 1.22, retroactively, for standing still. A missing SDG
report falls back to the neutral rather than to zero for the same reason: it must
read as "no opinion", not as M_SDG 0.82.

`calculate_sdg_multiplier` is one formula with two inputs, and which input it gets
is the versioned decision. With `neutral=0` it is bit-identical to the function it
replaced, asserted digit by digit. The Consequence-DNA projection was switched in
the same pass, because showing a team an M_SDG derived from a number the finale
does not use is the F-15 Mirror Debrief bug in a new place.

Measured effect at the finale, all switches on: high-SDG paths gain ~4.6–5.1% of
terminal value, low-SDG paths lose ~1.3%. The dimension discriminates for the
first time.

**Provisional calibration, and it is provisional.** The coefficient is left at the
0.25 the original design chose, so the only thing that changes is what it applies
to. Over the measured index range that gives M_SDG 0.930..1.047 against the old
side-track lever's 0.97..1.26 — the SDG dimension now carries *less* authority,
not more. That may well be right for a score every team has rather than an optional
deep dive, but it is a calibration judgement and Phase 5 owns it;
`test_the_authority_of_the_lever_is_recorded_for_phase_5` makes moving the
coefficient a deliberate act.

## B. Fog of War is implemented, display-only — `fog_of_war_display_noise`

The engine computed `fog_noise` every round of the opening window and nothing read
it. Intent had been recorded, though, which is why this is an implementation and
not an invention: `fog_of_war_rounds` and `fog_noise_range` are facilitator
tunables with per-scenario presets of 1, 3, 4 and 5 rounds, while the engine
hardcoded 2 rounds and ±0.10. Both already carried CFG-08's inert ruling.

Under 2026.10 the noise is applied at the **serialisation boundary**
(`router._bu_out`), never to stored state. No engine reads a fogged number and no
score moves, which is why the most visible change in the whole phase needs no
recalibration at all. `test_the_stored_state_is_never_fogged` is that property and
is the one test in the module that must never be relaxed.

Three consequences follow from doing it there. The tunables are read, so four
scenario presets stop meaning nothing. The shape-A exemption read is fixed, so the
R1 Deep Forensic Audit finally buys something: measured, a team that takes it is
fogged at R1 and clear from R2, while a team that skips it is fogged for the full
configured window. And it is applied to the **history endpoint** as well as the
dashboard — a fog a player can defeat by opening a different tab is not a fog —
while facilitator and admin views, which do not go through `_bu_out`, keep the true
numbers.

## C, D, E. The three mechanical fixes

**A shape-E lint** (`tests/test_no_stringified_flag_reads.py`). The pattern is
invisible to both existing guards — to the textual sweep because the name it tests
is not a declared flag, and to the read probe because a substring test over a
string consults no container. The sweep found four sites in the whole backend, one
of them the known instance and three legitimate, so the ban is cheap; a test also
holds that premise, so if the allow-list ever needs to grow, someone has to argue
for the instrument rather than quietly widen it.

**The escalation identities are pinned** in the matrix snapshot. The transparency
cascade's cash effect was already recorded; which escalation fired was not, so a
swap for another of similar cost would have moved no fixture. Identifiers only —
`npc_id:action` and `agent_id:stage` — never the narrative text, which would churn
seven fixtures on every copy edit. It immediately earned its keep: see the first
correction below.

**The plan is reissued as Draft 1.1**, with a §0 listing the five corrected claims
and §1.2 rewritten from three defect shapes to five.

## Two more of my own claims, falsified by the separability test

`test_each_switch_can_be_assessed_on_its_own` turns each switch on alone and
measures which paths move. It exists so Phase 5 can cost each mechanic separately.
It found two errors in this document's own §2 table on its first run.

**`npc_betrayal_reads_option_flags` is graded, not conditional.** I recorded that
both call sites sit behind `stakeholder_memory_enabled`, "which defaults off, so
this switch does nothing until a cohort turns that toggle on". The toggle defaults
**on**: `pedagogical_engine.py:719` sets it True and `get_pedagogical_toggles`
merges those defaults, so the `.get(..., False)` fallbacks at `round_logic.py:1059`
and `:1236` only fire if the toggle machinery throws. Measured, `memory_enabled` is
True in every round of every matrix path, and the switch moves the escalation
surface on all seven and cascades into money on two. `npc_stakeholders.py:26` and
`:662` still said "defaults OFF" — a sixth stale comment, corrected in the same
pass.

Note that this switch would have looked **inert on four of seven paths** without
the escalation identities added an hour earlier.

**`biodiversity_audit_gate_reads_flags` is diagnostic, not graded.** I called it
"GRADED, AND THIS ONE FAILS OPEN". The failing-open half stands and is why it is
versioned at all. The graded half does not: the gate feeds `species_risk_score`,
which has no consumer outside `biodiversity_engine` itself. The stakeholder engines
that do read `biodiversity_state` take `water_stress_index` and
`tnfd_disclosure_level`, not species risk.

## A detector that went blind, and why that is the dangerous failure

Renaming a flag bag to a local `_fog_flags` removed a read from
`test_no_new_raw_flag_reads.py`'s view, and the lint reported it as a baselined
read that was **gone — good**. It was not gone; the detector could no longer see
it, and its silence was indistinguishable from success. `_FLAG_VARS` was widened
(and `main_flags` added while there, which surfaced two pre-existing side-track
reads that are now on the ledger with that explanation). A guard that goes quiet
when a variable is renamed is worse than no guard, and this is the third time in
four phases that a guard's blind spot has been the actual finding.

## State

Seven switches, all off in the baseline. Full backend suite: **2,890 passed, 15
skipped, 0 failed.** New modules: `test_fog_of_war_display.py` (9),
`test_sdg_single_quantity.py` (9), `test_no_stringified_flag_reads.py` (4).

Still named for Phase 5, unchanged: the SDG coefficient, the transparency score's
clamps, the pillar and healthcare paradigms, and the cut-over itself.
